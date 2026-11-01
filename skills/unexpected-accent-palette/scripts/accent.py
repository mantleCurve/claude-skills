#!/usr/bin/env python3
"""Two base colours + one unexpected accent: analyse, suggest, tokenise, preview, measure.

Colour maths (stdlib only, Python 3.9+):
  * sRGB <-> OKLab/OKLCH with Bjorn Ottosson's matrices (https://bottosson.github.io/posts/oklab/)
  * WCAG 2.x relative luminance and contrast ratio (never rounded before comparing)
  * out-of-gamut OKLCH colours are brought into sRGB by reducing chroma at fixed L and hue
  * colour-vision simulation with the Machado et al. (2009) severity-1.0 matrices

Roles: BASE1 = Mood (dominant background), BASE2 = Support, ACCENT = the one surprise.

Subcommands: analyze, suggest, tokens, preview, coverage. Run with -h for each.
Exit codes: 0 ok (PASS/NOTE/WARN), 1 a FAIL check, 2 usage or environment error.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- thresholds
NEUTRAL_C = 0.03          # OKLCH chroma below this: hue is meaningless, treat as neutral
NEUTRAL_C_EDGE = 0.06     # ...and below this when L < 0.15 or L > 0.97 (chroma is invisible near black/white)
HUE_PASS = 90.0           # accent hue this far from every chromatic base: PASS
HUE_FAIL = 45.0           # closer than this: same hue family, FAIL
ACCENT_C_FAIL = 0.07      # accent chroma below this is a neutral, not an accent
ACCENT_C_GOOD = 0.12      # accent chroma at or above this is "high chroma"
TEXT_MIN = 4.5            # WCAG 1.4.3 normal text
UI_MIN = 3.0              # WCAG 1.4.11 non-text / 1.4.3 large text
SEMANTIC_NEAR = 30.0      # accent hue within this of a status hue: collision
EXTRA_SAME_FAMILY = 25.0  # --extra colour within this of a palette hue counts as its tint/shade
CVD_NEAR = 0.10           # OKLab distance under simulated CVD below this: hard to tell apart

SEMANTIC = {  # role: (default hue, allowed hue band) in OKLCH degrees
    "danger": (27.0, (15.0, 40.0)),
    "warning": (70.0, (58.0, 90.0)),
    "success": (150.0, (138.0, 168.0)),
}

STATUS_ORDER = {"PASS": 0, "NOTE": 1, "WARN": 2, "FAIL": 3}


class ColourError(ValueError):
    pass


# ---------------------------------------------------------------- parsing / formatting
def parse_hex(text: str) -> tuple:
    s = str(text).strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in s):
        raise ColourError(f"not a hex colour: {text!r} (use #abc, abc, #aabbcc or aabbcc)")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb) -> str:
    return "#%02X%02X%02X" % tuple(int(c) for c in rgb)


def hex_arg(text: str) -> str:
    """argparse type: validate and normalise to #RRGGBB."""
    try:
        return to_hex(parse_hex(text))
    except ColourError as exc:
        raise argparse.ArgumentTypeError(str(exc))


# ---------------------------------------------------------------- sRGB <-> OKLab / OKLCH
def srgb_to_linear(c8: float) -> float:
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    c = min(max(c, 0.0), 1.0)
    v = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return v * 255.0


def _cbrt(x: float) -> float:
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


def linear_to_oklab(r: float, g: float, b: float) -> tuple:
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = _cbrt(l), _cbrt(m), _cbrt(s)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def oklab_to_linear(L: float, a: float, b: float) -> tuple:
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def rgb_to_oklab(rgb) -> tuple:
    return linear_to_oklab(*(srgb_to_linear(c) for c in rgb))


def oklab_to_rgb(L: float, a: float, b: float) -> tuple:
    return tuple(int(round(linear_to_srgb(c))) for c in oklab_to_linear(L, a, b))


def rgb_to_oklch(rgb) -> tuple:
    L, a, b = rgb_to_oklab(rgb)
    C = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a)) % 360.0
    return L, C, h


def _lch_to_lab(L: float, C: float, h: float) -> tuple:
    hr = math.radians(h)
    return L, C * math.cos(hr), C * math.sin(hr)


def in_gamut(L: float, C: float, h: float, eps: float = 1e-6) -> bool:
    return all(-eps <= c <= 1 + eps for c in oklab_to_linear(*_lch_to_lab(L, C, h)))


def max_chroma(L: float, h: float, cap: float = 0.4) -> float:
    if L <= 0.0 or L >= 1.0:
        return 0.0
    lo, hi = 0.0, cap
    if in_gamut(L, hi, h):
        return hi
    for _ in range(32):
        mid = (lo + hi) / 2
        if in_gamut(L, mid, h):
            lo = mid
        else:
            hi = mid
    return lo


def oklch_to_rgb(L: float, C: float, h: float) -> tuple:
    """Return (rgb, clipped). Out-of-gamut colours keep L and hue and lose chroma."""
    L = min(max(L, 0.0), 1.0)
    C = max(C, 0.0)
    clipped = False
    if not in_gamut(L, C, h):
        C = max_chroma(L, h, cap=C)
        clipped = True
    return oklab_to_rgb(*_lch_to_lab(L, C, h)), clipped


def oklch_hex(L: float, C: float, h: float) -> str:
    return to_hex(oklch_to_rgb(L, C, h)[0])


def delta_e(rgb1, rgb2) -> float:
    a, b = rgb_to_oklab(rgb1), rgb_to_oklab(rgb2)
    return math.dist(a, b)


def mix_oklab(rgb1, rgb2, t: float) -> tuple:
    """t=0 -> rgb1, t=1 -> rgb2, interpolated in OKLab."""
    a, b = rgb_to_oklab(rgb1), rgb_to_oklab(rgb2)
    return oklab_to_rgb(*(x + (y - x) * t for x, y in zip(a, b)))


# ---------------------------------------------------------------- WCAG
def luminance(rgb) -> float:
    r, g, b = (srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(rgb1, rgb2) -> float:
    y1, y2 = luminance(rgb1), luminance(rgb2)
    hi, lo = max(y1, y2), min(y1, y2)
    return (hi + 0.05) / (lo + 0.05)


def r2(x: float) -> float:
    """Truncate (never round up) so a printed 4.50 is never a 4.499 that fails."""
    return math.floor(x * 100 + 1e-9) / 100


def fmt_ratio(x: float) -> str:
    return "%.2f:1" % r2(x)


# ---------------------------------------------------------------- colour vision deficiency
CVD = {
    "deuteranopia": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
    "protanopia": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
}


def simulate_cvd(rgb, kind: str) -> tuple:
    lin = [srgb_to_linear(c) for c in rgb]
    out = [sum(row[i] * lin[i] for i in range(3)) for row in CVD[kind]]
    return tuple(int(round(linear_to_srgb(c))) for c in out)


# ---------------------------------------------------------------- hue vocabulary
HUE_NAMES = [  # (start degree, name) in OKLCH hue; sorted
    (0, "pink"), (12, "red"), (35, "red-orange"), (52, "orange"), (75, "amber"), (95, "yellow"),
    (115, "lime"), (135, "green"), (155, "sea green"), (175, "teal"), (205, "sky"), (235, "blue"),
    (272, "indigo"), (292, "violet"), (315, "magenta"), (345, "pink"),
]


def hue_name(rgb) -> str:
    L, C, h = rgb_to_oklch(rgb)
    name = HUE_NAMES[0][1]
    for start, label in HUE_NAMES:
        if h >= start:
            name = label
    if neutral_lc(L, C):
        base = "white" if L > 0.93 else "black" if L < 0.2 else "grey"
        return base if C < 0.012 else "%s-tinted %s" % (name, base)
    if L >= 0.82:
        return "light " + name
    if L <= 0.45:
        return "deep " + name
    return name


def neutral_lc(L: float, C: float) -> bool:
    return C < NEUTRAL_C or (C < NEUTRAL_C_EDGE and (L < 0.15 or L > 0.97))


def hue_dist(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360.0
    return min(d, 360.0 - d)


def temperature(rgb) -> str:
    L, C, h = rgb_to_oklch(rgb)
    if neutral_lc(L, C):
        return "neutral"
    if h >= 330 or h < 110:
        return "warm"
    if 135 <= h < 300:
        return "cool"
    return "transitional"


def flips(t1: str, t2: str) -> bool:
    return {t1, t2} == {"warm", "cool"}


def is_chromatic(rgb) -> bool:
    L, C, _h = rgb_to_oklch(rgb)
    return not neutral_lc(L, C)


# ---------------------------------------------------------------- checks
def check(cid: str, status: str, message: str) -> dict:
    return {"id": cid, "status": status, "message": message}


def worst(statuses) -> str:
    statuses = list(statuses) or ["PASS"]
    return max(statuses, key=lambda s: STATUS_ORDER[s])


def base_relation(b1, b2) -> str:
    c1, c2 = is_chromatic(b1), is_chromatic(b2)
    if not c1 and not c2:
        return "neutral pair"
    if c1 != c2:
        return "one hue + a neutral"
    d = hue_dist(rgb_to_oklch(b1)[2], rgb_to_oklch(b2)[2])
    if d < 30:
        return "one hue family (tint/shade pair, %d deg apart)" % round(d)
    return "two hue families (%d deg apart)" % round(d)


def best_text_on(fill, candidates=None) -> tuple:
    cands = candidates or [(255, 255, 255), (0, 0, 0)]
    best = max(cands, key=lambda c: contrast(c, fill))
    return best, contrast(best, fill)


def semantic_collisions(acc) -> list:
    L, C, h = rgb_to_oklch(acc)
    if C < ACCENT_C_FAIL:
        return []
    hits = []
    for role, (hue, _band) in SEMANTIC.items():
        d = hue_dist(h, hue)
        if d < SEMANTIC_NEAR:
            hits.append((role, d))
    return hits


def analyze(b1h: str, b2h: str, acch: str = None, extras=()) -> dict:
    b1, b2 = parse_hex(b1h), parse_hex(b2h)
    acc = parse_hex(acch) if acch else None
    named = [("Mood (BASE1)", b1), ("Support (BASE2)", b2)]
    if acc:
        named.append(("Accent", acc))
    colours = []
    for role, rgb in named:
        L, C, h = rgb_to_oklch(rgb)
        colours.append({
            "role": role, "hex": to_hex(rgb), "name": hue_name(rgb),
            "oklch": [round(L, 4), round(C, 4), round(h, 1)],
            "neutral": neutral_lc(L, C), "temperature": temperature(rgb),
        })
    refs = [("BASE1", b1), ("BASE2", b2)] + ([("ACCENT", acc)] if acc else []) + \
        [("#FFFFFF", (255, 255, 255)), ("#000000", (0, 0, 0))]
    matrix = {a: {b: r2(contrast(x, y)) for b, y in refs} for a, x in refs}
    checks = []
    rel = base_relation(b1, b2)
    checks.append(check("base-relation", "NOTE", "Base pair: %s." % rel))
    pair = contrast(b1, b2)
    if pair >= TEXT_MIN:
        checks.append(check("base-text", "PASS",
                            "BASE2 on BASE1 is %s: usable for text either way round." % fmt_ratio(pair)))
    elif pair >= UI_MIN:
        checks.append(check("base-text", "WARN",
                            "BASE2 on BASE1 is %s: large text (>=24px, or >=18.66px bold) only; body text "
                            "uses a derived neutral (see `tokens`)." % fmt_ratio(pair)))
    else:
        checks.append(check("base-text", "WARN",
                            "BASE2 on BASE1 is %s: not for any text; keep both as fills and use derived "
                            "neutral text (see `tokens`)." % fmt_ratio(pair)))

    result = {"colours": colours, "contrast": matrix, "checks": checks, "hue_distances": {}}
    if not acc:
        checks.append(check("accent", "NOTE", "No accent given: run `suggest BASE1 BASE2`."))
        result["verdict"] = worst(c["status"] for c in checks)
        return result

    La, Ca, ha = rgb_to_oklch(acc)
    ta = temperature(acc)
    # -- hue distance per chromatic base
    hue_statuses, parts = [], []
    for label, rgb in (("BASE1", b1), ("BASE2", b2)):
        L, C, h = rgb_to_oklch(rgb)
        if neutral_lc(L, C):
            parts.append("%s near-neutral (C %.3f), hue ignored" % (label, C))
            result["hue_distances"][label] = None
            continue
        d = hue_dist(ha, h)
        result["hue_distances"][label] = round(d, 1)
        flip = flips(ta, temperature(rgb))
        if d >= HUE_PASS:
            st = "PASS"
        elif d >= HUE_FAIL:
            st = "PASS" if flip else "WARN"
        else:
            st = "FAIL"
        hue_statuses.append(st)
        parts.append("%d deg from %s%s" % (round(d), label, " with a warm/cool flip" if flip and d < HUE_PASS else ""))
    hs = worst(hue_statuses) if hue_statuses else "PASS"
    msg = "Accent hue: " + "; ".join(parts) + ". "
    if hs == "PASS":
        msg += "It reads as a different colour, not a tint of the base."
    elif hs == "WARN":
        msg += ("Under %d deg without a temperature flip: the accent relies on lightness/chroma to stand out. "
                "Prefer a hue >= %d deg away." % (HUE_PASS, HUE_PASS))
    else:
        msg += ("Under %d deg: this is the base hue again (a tint/shade), so nothing surprises. Pick a hue "
                ">= %d deg away (run `suggest`)." % (HUE_FAIL, HUE_PASS))
    if not hue_statuses:
        msg = "Both bases are near-neutral, so any chromatic hue is far from them."
    checks.append(check("hue-distance", hs, msg))

    # -- chroma
    base_cs = [rgb_to_oklch(x)[1] for x in (b1, b2)]
    top = max(base_cs)
    if Ca < ACCENT_C_FAIL:
        checks.append(check("chroma", "FAIL", "Accent chroma %.3f is effectively neutral; an accent needs "
                                              ">= %.2f to pop." % (Ca, ACCENT_C_GOOD)))
    elif Ca >= top + 0.02:
        checks.append(check("chroma", "PASS", "Accent chroma %.3f is above both bases (max %.3f)." % (Ca, top)))
    elif Ca >= ACCENT_C_GOOD:
        checks.append(check("chroma", "NOTE",
                            "Accent chroma %.3f is high, but a base is as or more saturated (%.3f); the accent "
                            "pops through hue and lightness instead. Keep that base off the CTA and small "
                            "focal points." % (Ca, top)))
    else:
        checks.append(check("chroma", "WARN", "Accent chroma %.3f is modest and not above the bases (%.3f); "
                                              "raise it toward the gamut edge." % (Ca, top)))

    # -- temperature
    temps = [temperature(x) for x in (b1, b2) if is_chromatic(x)]
    pair_t = "neutral" if not temps else temps[0] if len(set(temps)) == 1 else "mixed"
    if pair_t == "neutral":
        checks.append(check("temperature", "NOTE", "Neutral base pair: any chromatic accent is a flip."))
    elif pair_t == "mixed":
        checks.append(check("temperature", "NOTE", "Base pair spans warm and cool; a flip is not defined. "
                                                   "Accent is %s." % ta))
    elif flips(pair_t, ta):
        checks.append(check("temperature", "PASS", "Temperature flip: %s base pair, %s accent." % (pair_t, ta)))
    else:
        checks.append(check("temperature", "NOTE", "No temperature flip (%s pair, %s accent); hue distance "
                                                   "has to carry the surprise." % (pair_t, ta)))

    # -- fills, text, focus
    fill = contrast(acc, b1)
    fill2 = contrast(acc, b2)
    if fill >= UI_MIN:
        checks.append(check("accent-fill", "PASS",
                            "Accent vs Mood background %s (>= 3:1): works as a button fill, focus ring, chart "
                            "mark or icon. Vs Support: %s." % (fmt_ratio(fill), fmt_ratio(fill2))))
    else:
        checks.append(check("accent-fill", "WARN",
                            "Accent vs Mood background is %s (< 3:1). A labelled button is still fine if its "
                            "text passes on the fill, but icon-only controls, focus rings and chart marks on "
                            "BASE1 need the lightness-adjusted accent from `tokens`. Vs Support: %s."
                            % (fmt_ratio(fill), fmt_ratio(fill2))))
    cands = [(255, 255, 255), (0, 0, 0), b1, b2]
    best, ratio = best_text_on(acc, cands)
    result["text_on_accent"] = {"hex": to_hex(best), "ratio": r2(ratio)}
    checks.append(check("text-on-accent", "PASS" if ratio >= TEXT_MIN else "FAIL",
                        "Best label colour on the accent: %s at %s (needs >= 4.5:1)." % (to_hex(best), fmt_ratio(ratio))))
    as_text = []
    for label, rgb in (("BASE1", b1), ("BASE2", b2)):
        r = contrast(acc, rgb)
        use = "body text" if r >= TEXT_MIN else "large text only" if r >= UI_MIN else "never as text"
        as_text.append("on %s %s (%s)" % (label, fmt_ratio(r), use))
    checks.append(check("accent-as-text", "NOTE", "Accent as text: " + "; ".join(as_text) + "."))

    # -- semantic colours
    hits = semantic_collisions(acc)
    if hits:
        desc = ", ".join("%s (%d deg)" % (r, round(d)) for r, d in hits)
        checks.append(check("semantic", "WARN",
                            "Accent hue is close to status colour %s. Shift the status hue (`tokens` does) and "
                            "always pair status colour with an icon and text." % desc))
    else:
        checks.append(check("semantic", "PASS", "Accent hue is clear of the error/warning/success hues."))

    # -- colour vision deficiency
    weak = []
    for kind in CVD:
        a2 = simulate_cvd(acc, kind)
        for label, rgb in (("BASE1", b1), ("BASE2", b2)):
            d = delta_e(a2, simulate_cvd(rgb, kind))
            if d < CVD_NEAR:
                weak.append("%s vs %s under %s (dE %.3f)" % ("accent", label, kind, d))
    if weak:
        checks.append(check("colour-vision", "WARN",
                            "Accent is hard to tell from the base for some viewers: " + "; ".join(weak) +
                            ". Never signal with colour alone: keep labels, icons, weight or underline."))
    else:
        checks.append(check("colour-vision", "PASS",
                            "Accent stays distinct from both bases under simulated deuteranopia and protanopia."))

    # -- extra colours present in the design
    for xh in extras:
        x = parse_hex(xh)
        Lx, Cx, hx = rgb_to_oklch(x)
        if neutral_lc(Lx, Cx):
            checks.append(check("extra", "PASS", "%s is a neutral: fine." % to_hex(x)))
            continue
        fam = [lab for lab, rgb in (("BASE1", b1), ("BASE2", b2), ("ACCENT", acc))
               if is_chromatic(rgb) and hue_dist(hx, rgb_to_oklch(rgb)[2]) < EXTRA_SAME_FAMILY]
        sem = [r for r, (hue, _b) in SEMANTIC.items() if hue_dist(hx, hue) < 15]
        if fam:
            checks.append(check("extra", "PASS", "%s is a tint/shade of %s: fine." % (to_hex(x), fam[0])))
        elif sem:
            checks.append(check("extra", "NOTE", "%s looks like a %s status colour: keep it for status only, "
                                                 "quieter than the accent, with icon + text." % (to_hex(x), sem[0])))
        else:
            checks.append(check("extra", "FAIL",
                                "%s (%s) is a new hue that competes with the accent. Exactly one accent hue: "
                                "replace it with a tint of a base or of the accent." % (to_hex(x), hue_name(x))))
    result["verdict"] = worst(c["status"] for c in checks)
    return result


def print_analysis(res: dict) -> None:
    print("Colours (OKLCH L C h)")
    for c in res["colours"]:
        L, C, h = c["oklch"]
        hue = "  -  " if c["neutral"] else "%5.1f" % h
        print("  %-16s %s  L %.3f  C %.3f  h %s  %-14s %s" % (c["role"], c["hex"], L, C, hue, c["name"], c["temperature"]))
    if res["hue_distances"]:
        print("Hue distance from accent: " + ", ".join(
            "%s %s" % (k, "n/a (neutral)" if v is None else "%.1f deg" % v) for k, v in res["hue_distances"].items()))
    print("Contrast matrix (WCAG 2.x)")
    keys = list(res["contrast"].keys())
    print("  %-9s" % "" + "".join("%10s" % k for k in keys))
    for a in keys:
        print("  %-9s" % a + "".join("%10s" % ("-" if a == b else "%.2f" % res["contrast"][a][b]) for b in keys))
    if "text_on_accent" in res:
        t = res["text_on_accent"]
        print("Best text colour on accent: %s (%s)" % (t["hex"], fmt_ratio(t["ratio"])))
    print("Checks")
    for c in res["checks"]:
        print("  [%s] %-15s %s" % (c["status"], c["id"], c["message"]))
    print("Verdict: %s" % res["verdict"])


# ---------------------------------------------------------------- surfaces / modes
def tint_hue(b1, b2) -> tuple:
    """Hue and a small chroma for neutrals, taken from the most chromatic base."""
    cands = sorted((rgb_to_oklch(x) for x in (b1, b2)), key=lambda t: -t[1])
    L, C, h = cands[0]
    return h, (0.0 if C < 0.01 else min(0.02, C * 0.25))


def auto_mode(bg) -> str:
    return "light" if contrast((0, 0, 0), bg) >= contrast((255, 255, 255), bg) else "dark"


def surface_for(b1, b2, mode: str) -> tuple:
    """Return (background rgb, mode, note). auto -> BASE1 as the page."""
    h, c = tint_hue(b1, b2)
    if mode == "auto":
        return b1, auto_mode(b1), "BASE1 is the page background (%s mode by text contrast)." % auto_mode(b1)
    bases = sorted((b1, b2), key=lambda x: rgb_to_oklch(x)[0])
    if mode == "light":
        if rgb_to_oklch(bases[1])[0] >= 0.9:
            return bases[1], "light", "Lighter base %s is the light-mode background." % to_hex(bases[1])
        bg = oklch_to_rgb(0.985, min(c, 0.008), h)[0]
        return bg, "light", "Neither base is light enough; derived light background %s from the base hue." % to_hex(bg)
    if rgb_to_oklch(bases[0])[0] <= 0.40:
        return bases[0], "dark", "Darker base %s is the dark-mode background." % to_hex(bases[0])
    bg = oklch_to_rgb(0.18, c, h)[0]
    return bg, "dark", "Neither base is dark enough; derived dark background %s from the base hue." % to_hex(bg)


def push_contrast(rgb, against, target: float, direction: int = 0, step: float = 0.005) -> tuple:
    """Move rgb's OKLCH lightness (hue kept, chroma kept where gamut allows) until
    contrast(rgb, against) >= target. direction 0 = whichever way gets there with the smaller move.
    Returns (rgb, delta_L) or (None, None) if impossible."""
    L, C, h = rgb_to_oklch(rgb)
    if contrast(rgb, against) >= target:
        return rgb, 0.0
    best = None
    for d in ((-1, 1) if direction == 0 else (direction,)):
        k = 1
        while True:
            Ln = L + d * step * k
            if Ln < 0 or Ln > 1:
                break
            cand = oklch_to_rgb(Ln, C, h)[0]
            if contrast(cand, against) >= target:
                if best is None or abs(Ln - L) < abs(best[1]):
                    best = (cand, Ln - L)
                break
            k += 1
    return best if best else (None, None)


# ---------------------------------------------------------------- suggest
def cusp_lightness(h: float) -> float:
    """Lightness at which hue h reaches its maximum sRGB chroma."""
    return max((i / 100.0 for i in range(5, 100)), key=lambda L: max_chroma(L, h))


def suggest(b1h: str, b2h: str, count: int = 6, mode: str = "auto") -> dict:
    b1, b2 = parse_hex(b1h), parse_hex(b2h)
    bg, used_mode, bg_note = surface_for(b1, b2, mode)
    chroma_bases = [(lab, rgb, rgb_to_oklch(rgb)) for lab, rgb in (("BASE1", b1), ("BASE2", b2)) if is_chromatic(rgb)]
    temps = sorted({temperature(rgb) for _l, rgb, _o in chroma_bases})
    pair_t = "neutral" if not temps else temps[0] if len(temps) == 1 else "mixed"
    top_base_c = max([o[1] for _l, _r, o in chroma_bases] or [0.0])
    cands = []
    for hue10 in range(0, 3600, 50):
        h = hue10 / 10.0
        best = None
        for i in range(0, 121):
            L = 0.35 + i * 0.005
            C = max_chroma(L, h, cap=0.32)
            rgb = oklch_to_rgb(L, C, h)[0]
            fc = contrast(rgb, bg)
            if fc < UI_MIN:
                continue
            Lr, Cr, hr = rgb_to_oklch(rgb)
            key = (round(Cr, 3), fc)
            if best is None or key > best[0]:
                best = (key, rgb)
        if best is None:
            continue
        rgb = best[1]
        L, C, hh = rgb_to_oklch(rgb)
        fc = contrast(rgb, bg)
        dists = [(lab, hue_dist(hh, o[2])) for lab, _r, o in chroma_bases]
        dmin = min([d for _l, d in dists] or [180.0])
        t = temperature(rgb)
        temp_s = 1.0 if (pair_t in ("warm", "cool") and flips(pair_t, t)) else 0.5 if pair_t in ("neutral", "mixed") or t == "transitional" else 0.0
        sem = min(hue_dist(hh, SEMANTIC["danger"][0]), hue_dist(hh, SEMANTIC["success"][0]))
        # Darkened yellows/ambers/limes read as olive or brown, not as a bright surprise.
        muddy = 45.0 <= hh <= 135.0 and cusp_lightness(hh) - L > 0.12
        score = (0.35 * min(dmin, 120.0) / 120.0
                 + 0.25 * (0.7 * min(C / 0.24, 1.0) + 0.3 * (1.0 if C >= top_base_c else C / top_base_c))
                 + 0.15 * temp_s
                 + 0.10 * max(0.0, min((fc - UI_MIN) / 1.5, 1.0))
                 + 0.15 * min(sem / 40.0, 1.0))
        if muddy:
            score *= 0.75
        txt, tr = best_text_on(rgb)
        reasons = []
        if chroma_bases:
            near_lab = min(dists, key=lambda t: t[1])[0]
            reasons.append("%d deg from %s%s" % (round(dmin), near_lab, " (nearer base)" if len(dists) > 1 else ""))
        else:
            reasons.append("neutral bases: any hue is distant")
        if pair_t in ("warm", "cool") and flips(pair_t, t):
            reasons.append("%s vs %s pair" % (t, pair_t))
        reasons.append("C %.2f%s" % (C, " > bases" if C >= top_base_c + 0.02 else ""))
        if muddy:
            reasons.append("darkened to pass 3:1, reads olive/brown")
        if sem < SEMANTIC_NEAR:
            near = "error red" if hue_dist(hh, SEMANTIC["danger"][0]) < SEMANTIC_NEAR else "success green"
            reasons.append("close to %s: shift status hue" % near)
        cands.append({
            "hex": to_hex(rgb), "name": hue_name(rgb), "oklch": [round(L, 3), round(C, 3), round(hh, 1)],
            "hue_distance": round(dmin, 1), "fill_contrast": r2(fc), "text": to_hex(txt),
            "text_contrast": r2(tr), "temperature": t, "score": round(score, 3),
            "eligible": dmin >= HUE_PASS, "reasons": reasons,
        })
    cands.sort(key=lambda c: (not c["eligible"], -c["score"], c["oklch"][2]))
    picked = []
    for c in cands:
        if all(hue_dist(c["oklch"][2], p["oklch"][2]) >= 20 for p in picked):
            picked.append(c)
        if len(picked) >= count:
            break
    return {"background": to_hex(bg), "mode": used_mode, "background_note": bg_note,
            "base_temperature": pair_t, "candidates": picked}


def print_suggest(res: dict) -> None:
    print("Background for the fill check: %s (%s mode). %s" % (res["background"], res["mode"], res["background_note"]))
    print("Base pair temperature: %s. Candidates are max chroma in sRGB at a lightness giving >= 3:1 on the background."
          % res["base_temperature"])
    print("  #  hex      hue label      OKLCH (L C h)          dHue  fill   label text       score  reasons")
    for i, c in enumerate(res["candidates"], 1):
        L, C, h = c["oklch"]
        print("  %d  %s  %-14s %.3f %.3f %5.1f   %5.1f  %-6s %s %-7s %.3f  %s%s" % (
            i, c["hex"], c["name"], L, C, h, c["hue_distance"], "%.2f" % c["fill_contrast"], c["text"],
            "%.2f" % c["text_contrast"], c["score"], "; ".join(c["reasons"]),
            "" if c["eligible"] else "  [below 90 deg]"))


# ---------------------------------------------------------------- tokens
def build_tokens(b1h: str, b2h: str, acch: str, mode: str = "auto") -> dict:
    b1, b2, acc0 = parse_hex(b1h), parse_hex(b2h), parse_hex(acch)
    bg, mode, bg_note = surface_for(b1, b2, mode)
    th, tc = tint_hue(b1, b2)
    notes = [bg_note]
    pairs = []  # (fg token, bg token, ratio, minimum)
    T = {}

    def put(name, rgb, role):
        T[name] = {"hex": to_hex(rgb), "rgb": rgb, "role": role}

    def ensure(name, against_name, target, direction=0, label=None):
        rgb, against = T[name]["rgb"], T[against_name]["rgb"]
        new, dl = push_contrast(rgb, against, target, direction)
        if new is None:
            new = best_text_on(against)[0]
            notes.append("%s could not reach %.1f:1 by lightness; fell back to %s." % (name, target, to_hex(new)))
        elif dl:
            notes.append("%s lightness %+.3f (%s -> %s) to reach %.1f:1 on %s." % (
                name, dl, T[name]["hex"], to_hex(new), target, against_name))
        T[name]["rgb"], T[name]["hex"] = new, to_hex(new)

    put("mood", b1, "Mood: dominant base, unchanged")
    put("support", b2, "Support: second base, unchanged")
    put("surface", bg, "page background")
    Lb = rgb_to_oklch(bg)[0]
    raised_L = (min(1.0, Lb + 0.04) if Lb < 0.99 else Lb - 0.025) if mode == "light" else Lb + 0.05
    put("surface-raised", oklch_to_rgb(raised_L, rgb_to_oklch(bg)[1] * 0.8, rgb_to_oklch(bg)[2])[0], "cards, panels")
    dark_text = oklch_to_rgb(0.22, min(tc * 1.5, 0.03), th)[0]
    light_text = oklch_to_rgb(0.975, min(tc, 0.01), th)[0]
    put("text", dark_text if mode == "light" else light_text, "body text")
    put("text-muted", oklch_to_rgb(0.45 if mode == "light" else 0.76, min(tc * 1.5, 0.03), th)[0], "secondary text")
    away = -1 if mode == "light" else 1
    for name in ("text", "text-muted"):
        for surf in ("surface", "surface-raised"):
            ensure(name, surf, TEXT_MIN, away)
    put("border", oklch_to_rgb(Lb + 0.10 * away, min(tc, 0.015), th)[0], "decorative dividers (no contrast need)")
    put("border-strong", T["border"]["rgb"], "input borders and boundaries that identify a control (>= 3:1)")
    ensure("border-strong", "surface", UI_MIN, away)
    brand = max((b1, b2), key=lambda x: rgb_to_oklch(x)[1])
    put("brand-text", brand, "most chromatic base as link/heading text (not the CTA)")
    ensure("brand-text", "surface", TEXT_MIN)
    ensure("brand-text", "surface-raised", TEXT_MIN)

    # accent: same hue, lightness only as far as needed for >= 3:1 on the surface
    put("accent", acc0, "Accent: primary CTA, focal point, one highlight")
    ensure("accent", "surface", UI_MIN)
    acc = T["accent"]["rgb"]
    La, Ca, ha = rgb_to_oklch(acc)
    on = max([T["text"]["rgb"] if mode == "light" else dark_text, light_text, (0, 0, 0), (255, 255, 255)],
             key=lambda c: (contrast(c, acc) >= TEXT_MIN, c not in ((0, 0, 0), (255, 255, 255)), contrast(c, acc)))
    put("on-accent", on, "label text on accent fills")
    ensure("on-accent", "accent", TEXT_MIN)
    # States: move away from the page first (stronger fill), as long as the label keeps 4.5:1;
    # otherwise move the way that raises label contrast.
    on_rgb = T["on-accent"]["rgb"]
    d_bg = -1 if mode == "light" else 1
    d_label = 1 if luminance(on_rgb) < luminance(acc) else -1
    plan = None
    for d, steps in ((d_bg, (0.05, 0.10)), (d_bg, (0.03, 0.06)), (d_label, (0.05, 0.10))):
        states = [oklch_to_rgb(La + d * k, Ca, ha)[0] for k in steps]
        if all(contrast(x, on_rgb) >= TEXT_MIN for x in states):
            plan = states
            break
    put("accent-hover", plan[0], "hover state")
    put("accent-active", plan[1], "pressed state")
    for st in ("accent-hover", "accent-active"):
        if contrast(T[st]["rgb"], bg) < UI_MIN:
            notes.append("%s is %s on the surface (< 3:1); acceptable for a transient state of a labelled "
                         "button, not for its only boundary." % (st, fmt_ratio(contrast(T[st]["rgb"], bg))))
    put("accent-soft", mix_oklab(bg, acc, 0.16), "badge / selection background tint")
    put("accent-soft-text", acc, "text on accent-soft (badge label)")
    ensure("accent-soft-text", "accent-soft", TEXT_MIN)
    put("focus-ring", acc, "2px focus outline with 2px offset")
    dis = mix_oklab(bg, acc, 0.35)
    Ld, Cd, hd = rgb_to_oklch(dis)
    put("accent-disabled", oklch_to_rgb(Ld, Cd * 0.4, hd)[0], "disabled fill (WCAG exempt; pair with cursor/aria)")
    put("on-accent-disabled", T["text-muted"]["rgb"], "disabled label (exempt)")

    # semantic status colours: quieter than the accent and away from its hue
    for role, (hue, (lo, hi)) in SEMANTIC.items():
        h = hue
        if hue_dist(ha, hue) < SEMANTIC_NEAR and Ca >= ACCENT_C_FAIL:
            h = max((lo, hi), key=lambda x: hue_dist(ha, x))
            notes.append("%s hue moved %d -> %d deg to separate it from the accent (%d deg apart now)%s." % (
                role, hue, h, round(hue_dist(ha, h)),
                "; still close, so status must rely on icon + text" if hue_dist(ha, h) < SEMANTIC_NEAR else ""))
        Ls = 0.52 if mode == "light" else 0.78
        put(role, oklch_to_rgb(Ls, min(0.14, Ca * 0.85), h)[0], "%s status text/icon (always with icon + text)" % role)
        ensure(role, "surface", TEXT_MIN)

    if T["accent"]["hex"] != to_hex(acc0):
        notes.append("Use the adjusted accent in %s mode; the hue is unchanged." % mode)
    for fg, bgn, need in (("text", "surface", TEXT_MIN), ("text", "surface-raised", TEXT_MIN),
                          ("text-muted", "surface", TEXT_MIN), ("text-muted", "surface-raised", TEXT_MIN),
                          ("brand-text", "surface", TEXT_MIN), ("brand-text", "surface-raised", TEXT_MIN), ("on-accent", "accent", TEXT_MIN),
                          ("on-accent", "accent-hover", TEXT_MIN), ("on-accent", "accent-active", TEXT_MIN),
                          ("accent-soft-text", "accent-soft", TEXT_MIN), ("danger", "surface", TEXT_MIN),
                          ("warning", "surface", TEXT_MIN), ("success", "surface", TEXT_MIN),
                          ("accent", "surface", UI_MIN), ("focus-ring", "surface", UI_MIN),
                          ("border-strong", "surface", UI_MIN)):
        r = contrast(T[fg]["rgb"], T[bgn]["rgb"])
        pairs.append({"fg": fg, "bg": bgn, "ratio": r2(r), "min": need, "ok": r >= need})
    for v in T.values():
        v.pop("rgb", None)
    return {"mode": mode, "tokens": T, "contrast": pairs, "notes": notes}


def render_tokens(res: dict, fmt: str, selector: str = ":root") -> str:
    T = res["tokens"]
    if fmt == "json":
        return json.dumps(res, indent=2)
    head = ["unexpected-accent-palette tokens (%s mode), contrast computed by accent.py:" % res["mode"]]
    for p in res["contrast"]:
        head.append("  %-16s on %-14s %-8s (>= %.1f) %s" % (p["fg"], p["bg"], fmt_ratio(p["ratio"]), p["min"],
                                                          "ok" if p["ok"] else "FAIL"))
    if res["notes"]:
        head.append("Notes:")
        head += ["  - " + n for n in res["notes"]]
    comment = "/*\n" + "\n".join(" * " + line for line in head) + "\n */\n"
    width = max(len(k) for k in T) + 10
    lines = ["  %s %s; /* %s */" % (("--color-%s:" % k).ljust(width), v["hex"], v["role"]) for k, v in T.items()]
    if fmt == "tailwind":
        return comment + "/* Tailwind v4: utilities like bg-accent, text-on-accent, ring-focus-ring */\n@theme {\n" + \
            "\n".join(lines) + "\n}\n"
    return comment + "%s {\n" % selector + "\n".join(lines) + "\n}\n"


# ---------------------------------------------------------------- preview
def build_preview(b1h: str, b2h: str, acch: str) -> str:
    tk = build_tokens(b1h, b2h, acch, "auto")
    T = {k: v["hex"] for k, v in tk["tokens"].items()}
    an = analyze(b1h, b2h, acch)
    b1, b2 = parse_hex(b1h), parse_hex(b2h)
    surf = parse_hex(T["surface"])
    # base-only version: the CTA and highlights fall back to the Support colour
    sup = b2
    if contrast(sup, surf) < 1.5:
        sup = push_contrast(sup, surf, UI_MIN)[0] or sup
    on_sup = best_text_on(sup)[0]
    sup_word = b2 if contrast(b2, surf) >= UI_MIN else (push_contrast(b2, surf, UI_MIN)[0] or parse_hex(T["text"]))
    raised = parse_hex(T["surface-raised"])

    def bar_tints(colour):
        return [to_hex(mix_oklab(raised, colour, t)) for t in (0.28, 0.36, 0.32, 0.46, 0.40, 0.52)]

    # The non-highlighted bars are base tints. If Support and the surface are far apart in hue,
    # blending them makes mud, so use tints of the neutral text colour instead.
    sl, sc = rgb_to_oklch(surf), rgb_to_oklch(sup)
    clash = not neutral_lc(sl[0], sl[1]) and not neutral_lc(sc[0], sc[1]) and hue_dist(sl[2], sc[2]) > 60
    sup_bars = bar_tints(parse_hex(T["text"]) if clash else sup)
    # Soft glow of the Support hue; on light pages a light tint, so it never turns into a grey smudge.
    Ls, Cs, hs = rgb_to_oklch(b2)
    glow = to_hex(oklch_to_rgb(0.80, max(Cs, 0.10), hs)[0]) if tk["mode"] == "light" and not neutral_lc(Ls, Cs) else to_hex(b2)
    glow_op = "0" if clash else "0.45" if tk["mode"] == "light" else "0.30"

    def panel(with_accent: bool) -> str:
        acc = T["accent"] if with_accent else to_hex(sup)
        on = T["on-accent"] if with_accent else to_hex(on_sup)
        word = T["accent"] if with_accent else to_hex(sup_word)
        badge_bg = T["accent-soft"] if with_accent else T["surface-raised"]
        badge_fg = T["accent-soft-text"] if with_accent else T["text-muted"]
        hi_bar = T["accent"] if with_accent else to_hex(sup)
        cards = [("Base 1 · Mood", to_hex(b1), hue_name(b1)), ("Base 2 · Support", to_hex(b2), hue_name(b2))]
        if with_accent:
            cards.append(("Accent", acch.upper(), hue_name(parse_hex(acch))))
        sw = "".join(
            '<div class="sw"><span class="chip" style="background:%s"></span><span><b>%s</b><i>%s · %s</i></span></div>'
            % (hx, html.escape(role), hx, html.escape(nm)) for role, hx, nm in cards)
        heights = [38, 52, 46, 64, 58, 88]
        bars = "".join(
            '<div class="bar" style="height:%d%%;background:%s">%s</div>'
            % (hgt, hi_bar if i == 5 else sup_bars[i],
               '<em style="color:%s">+38%%</em>' % (word if with_accent else T["text"]) if i == 5 else "")
            for i, hgt in enumerate(heights))
        title = "With accent" if with_accent else "Base pair only"
        return f"""
<section class="panel" aria-label="{title}" style="--bg:{T['surface']};--raised:{T['surface-raised']};--text:{T['text']};--muted:{T['text-muted']};--border:{T['border']};--strong:{T['border-strong']};--support:{to_hex(b2)};--glow:{glow};--glow-op:{glow_op};--acc:{acc};--on:{on};--focus:{T['focus-ring'] if with_accent else T['border-strong']};--hover:{T['accent-hover'] if with_accent else to_hex(sup)}">
  <div class="tag">{title}</div>
  <div class="glow"></div>
  <div class="swatches">{sw}</div>
  <nav><span class="logo"><span class="mark"></span>Northwind</span>
    <span class="links"><a>Product</a><a>Pricing</a><a>Docs</a><a>Sign in</a></span></nav>
  <div class="hero">
    <span class="badge" style="background:{badge_bg};color:{badge_fg}">New · Release 2.4</span>
    <h2>Launch pages people <span style="color:{word}">remember</span>.</h2>
    <p>Two colours set the mood. One unexpected colour tells visitors exactly where to click.</p>
    <div class="ctas"><a class="btn" href="#">Start free trial</a><a class="ghost" href="#">See a demo</a></div>
  </div>
  <figure class="chart"><figcaption><span>Weekly sign-ups</span><span class="muted">last 6 weeks</span></figcaption>
    <div class="bars">{bars}</div></figure>
</section>"""

    rendered = "" if T["accent"] == acch.upper() else " (lightness-adjusted to %s for 3:1 on this surface)" % T["accent"]
    rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>≥ %.1f</td><td class=\"%s\">%s</td></tr>"
        % (p["fg"], p["bg"], fmt_ratio(p["ratio"]), p["min"], "ok" if p["ok"] else "bad", "pass" if p["ok"] else "FAIL")
        for p in tk["contrast"])
    checks = "".join("<li><b class=\"%s\">%s</b> %s</li>" % (c["status"].lower(), c["status"], html.escape(c["message"]))
                     for c in an["checks"])
    notes = "".join("<li>%s</li>" % html.escape(n) for n in tk["notes"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accent preview · {to_hex(b1)} + {to_hex(b2)} + {acch.upper()}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#E9E9EC;color:#17181C;font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}}
header.page{{max-width:1360px;margin:0 auto;padding:28px 28px 6px}}
header.page h1{{font-size:20px;margin:0 0 2px;letter-spacing:-.01em}}
header.page p{{margin:0;color:#55585F}}
.grid{{max-width:1360px;margin:0 auto;padding:18px 28px;display:grid;grid-template-columns:1fr 1fr;gap:24px}}
@media (max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
.panel{{position:relative;overflow:hidden;background:var(--bg);color:var(--text);border-radius:20px;min-height:600px;padding:22px 30px 30px;box-shadow:0 1px 2px rgba(0,0,0,.06),0 12px 40px rgba(0,0,0,.12)}}
.tag{{position:absolute;left:30px;bottom:14px;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.glow{{position:absolute;width:520px;height:520px;right:-180px;top:120px;border-radius:50%;background:radial-gradient(closest-side,var(--glow),transparent);opacity:var(--glow-op);pointer-events:none}}
nav{{position:relative;display:flex;align-items:center;gap:28px;font-size:14px}}
.logo{{display:flex;align-items:center;gap:9px;font-weight:700;letter-spacing:-.01em}}
.mark{{width:22px;height:22px;border-radius:7px;background:var(--support);box-shadow:inset 0 0 0 2px rgba(255,255,255,.18)}}
.links{{display:flex;gap:20px;color:var(--muted)}}
.links a{{cursor:pointer}}
.swatches{{position:absolute;top:66px;right:22px;display:flex;flex-direction:column;gap:6px;z-index:2}}
.sw{{display:flex;align-items:center;gap:10px;background:#FFFFFF;color:#17181C;border-radius:12px;padding:6px 12px 6px 6px;min-width:176px;box-shadow:0 6px 18px rgba(0,0,0,.18)}}
.sw .chip{{width:30px;height:30px;border-radius:8px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.08)}}
.sw b{{display:block;font-size:12px;line-height:1.2}}
.sw i{{display:block;font-style:normal;font-size:11px;color:#5A5D66;font-variant-numeric:tabular-nums}}
.hero{{position:relative;max-width:470px;margin-top:150px}}
.badge{{display:inline-block;font-size:12px;font-weight:600;padding:5px 11px;border-radius:999px}}
h2{{font-size:46px;line-height:1.04;letter-spacing:-.03em;margin:16px 0 14px;font-weight:800}}
.hero p{{color:var(--muted);font-size:16px;margin:0 0 24px;max-width:380px}}
.ctas{{display:flex;gap:12px;align-items:center}}
.btn{{background:var(--acc);color:var(--on);text-decoration:none;font-weight:700;padding:12px 20px;border-radius:12px;font-size:15px}}
.btn:hover{{background:var(--hover)}}
.btn:focus-visible,.ghost:focus-visible{{outline:2px solid var(--focus);outline-offset:2px}}
.ghost{{color:var(--text);text-decoration:none;font-weight:600;padding:11px 18px;border-radius:12px;border:1px solid var(--strong)}}
.chart{{position:relative;margin:44px 0 18px;max-width:420px;background:var(--raised);border:1px solid var(--border);border-radius:16px;padding:16px 18px}}
.chart figcaption{{display:flex;justify-content:space-between;font-size:13px;font-weight:600}}
.muted{{color:var(--muted);font-weight:500}}
.bars{{display:flex;align-items:flex-end;gap:12px;height:120px;margin-top:12px}}
.bar{{flex:1;border-radius:6px 6px 3px 3px;position:relative}}
.bar em{{position:absolute;top:-20px;left:50%;transform:translateX(-50%);font-style:normal;font-size:12px;font-weight:700;white-space:nowrap}}
.report{{max-width:1360px;margin:0 auto;padding:4px 28px 40px;display:grid;grid-template-columns:1fr 1fr;gap:24px}}
@media (max-width:1100px){{.report{{grid-template-columns:1fr}}}}
.card{{background:#FFFFFF;border-radius:16px;padding:18px 20px;box-shadow:0 1px 2px rgba(0,0,0,.05)}}
.card h3{{margin:0 0 10px;font-size:14px}}
table{{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}}
td,th{{text-align:left;padding:5px 8px;border-bottom:1px solid #ECECEF}}
th{{color:#55585F;font-weight:600}}
.ok,.pass{{color:#11672F;font-weight:700}} .bad,.fail{{color:#A3122A;font-weight:700}}
.warn{{color:#8A4B00;font-weight:700}} .note{{color:#44505F;font-weight:700}}
ul{{margin:0;padding-left:18px;font-size:13px}} li{{margin:4px 0}}
</style></head><body>
<header class="page"><h1>Base pair vs base pair + one unexpected accent</h1>
<p>Mood {to_hex(b1)} · Support {to_hex(b2)} · Accent {acch.upper()}{rendered} · {tk['mode']} mode. The accent appears on the CTA, one headline word, the badge and one bar only.</p></header>
<main class="grid">{panel(False)}{panel(True)}</main>
<section class="report">
<div class="card"><h3>Contrast (WCAG 2.x, computed by accent.py)</h3>
<table><thead><tr><th>Foreground</th><th>Background</th><th>Ratio</th><th>Needs</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="card"><h3>Checks</h3><ul>{checks}</ul><h3 style="margin-top:14px">Token notes</h3><ul>{notes}</ul></div>
</section></body></html>
"""


# ---------------------------------------------------------------- coverage
def decode_image(path: str, size: int) -> list:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH; install it (e.g. `brew install ffmpeg`) to use `coverage`.")
    if not os.path.isfile(path):
        raise RuntimeError("image not found: %s" % path)
    cmd = [exe, "-v", "error", "-i", path, "-frames:v", "1", "-vf", "scale=%d:%d:flags=neighbor" % (size, size),
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.run(cmd, capture_output=True)
    need = size * size * 3
    if proc.returncode or len(proc.stdout) < need:
        raise RuntimeError("ffmpeg could not decode %s: %s" % (path, proc.stderr.decode(errors="replace").strip()[:300]))
    data = proc.stdout[:need]
    return [tuple(data[i:i + 3]) for i in range(0, need, 3)]


def coverage(image: str, acch: str, tolerance: float = 0.08, size: int = 256) -> dict:
    acc = parse_hex(acch)
    target = rgb_to_oklab(acc)
    pixels = decode_image(image, size)
    cache, hits = {}, 0
    for p in pixels:
        m = cache.get(p)
        if m is None:
            m = math.dist(rgb_to_oklab(p), target) <= tolerance
            cache[p] = m
        hits += m
    pct = 100.0 * hits / len(pixels)
    if hits == 0:
        status, msg = "WARN", "Accent not found: it is missing, or rendered off-token (check the hex or raise --tolerance)."
    elif pct > 30.0:
        status, msg = "FAIL", "Accent covers %.1f%%: it has become a base colour, not an accent." % pct
    elif pct > 15.0:
        status, msg = "WARN", "Accent covers %.1f%% (> 15%%): sprawl. Pull it back to the CTA and one focal point." % pct
    else:
        status = "PASS"
        msg = "Accent covers %.2f%% of the view%s." % (
            pct, " (guideline 3-10%; a single CTA can be lower)" if pct < 3 or pct > 10 else ", inside the 3-10% guideline")
    return {"image": image, "accent": to_hex(acc), "tolerance": tolerance, "sampled_pixels": len(pixels),
            "accent_pixels": hits, "percent": round(pct, 3), "status": status, "message": msg}


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="accent.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("analyze", help="OKLCH, hue distances, contrast matrix and checks")
    p.add_argument("base1", type=hex_arg, help="Mood: dominant base (page background)")
    p.add_argument("base2", type=hex_arg, help="Support: second base")
    p.add_argument("accent", type=hex_arg, nargs="?", help="the accent to test (optional)")
    p.add_argument("--extra", type=hex_arg, nargs="+", default=[], metavar="HEX",
                   help="other colours in the design; flags any second accent hue")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("suggest", help="ranked accent candidates for a base pair")
    p.add_argument("base1", type=hex_arg)
    p.add_argument("base2", type=hex_arg)
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--mode", choices=["light", "dark", "auto"], default="auto",
                   help="auto: BASE1 is the background; light/dark: lighter/darker base or a derived surface")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("tokens", help="design tokens with verified contrast")
    p.add_argument("base1", type=hex_arg)
    p.add_argument("base2", type=hex_arg)
    p.add_argument("accent", type=hex_arg)
    p.add_argument("--format", choices=["css", "tailwind", "json"], default="css")
    p.add_argument("--mode", choices=["light", "dark", "auto"], default="auto")
    p.add_argument("--selector", default=":root", help="CSS selector for --format css, e.g. '[data-theme=dark]'")

    p = sub.add_parser("preview", help="self-contained HTML: base pair vs base pair + accent")
    p.add_argument("base1", type=hex_arg)
    p.add_argument("base2", type=hex_arg)
    p.add_argument("accent", type=hex_arg)
    p.add_argument("-o", "--output", required=True)

    p = sub.add_parser("coverage", help="share of a screenshot within OKLab tolerance of the accent")
    p.add_argument("image")
    p.add_argument("accent", type=hex_arg)
    p.add_argument("--tolerance", type=float, default=0.08, help="OKLab distance (default 0.08)")
    p.add_argument("--size", type=int, default=256, help="downsample to SIZE x SIZE before counting")
    p.add_argument("--json", action="store_true")

    a = ap.parse_args(argv)
    if a.cmd == "analyze":
        res = analyze(a.base1, a.base2, a.accent, a.extra)
        print(json.dumps(res, indent=2)) if a.json else print_analysis(res)
        return 1 if res["verdict"] == "FAIL" else 0
    if a.cmd == "suggest":
        if a.count < 1:
            ap.error("--count must be >= 1")
        res = suggest(a.base1, a.base2, a.count, a.mode)
        print(json.dumps(res, indent=2)) if a.json else print_suggest(res)
        return 0
    if a.cmd == "tokens":
        res = build_tokens(a.base1, a.base2, a.accent, a.mode)
        sys.stdout.write(render_tokens(res, a.format, a.selector))
        return 0 if all(p["ok"] for p in res["contrast"]) else 1
    if a.cmd == "preview":
        out = os.path.abspath(a.output)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(build_preview(a.base1, a.base2, a.accent))
        print("wrote %s" % out)
        return 0
    if a.cmd == "coverage":
        if not 0 < a.tolerance < 1 or a.size < 16:
            ap.error("--tolerance must be in (0, 1) and --size >= 16")
        try:
            res = coverage(a.image, a.accent, a.tolerance, a.size)
        except RuntimeError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        if a.json:
            print(json.dumps(res, indent=2))
        else:
            print("%s: %d of %d sampled pixels within dE %.3f of %s = %.2f%%" % (
                res["image"], res["accent_pixels"], res["sampled_pixels"], res["tolerance"], res["accent"], res["percent"]))
            print("[%s] %s" % (res["status"], res["message"]))
        return 1 if res["status"] == "FAIL" else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
