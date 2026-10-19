#!/usr/bin/env python3
"""Build prototype fonts (CFF OTF / WOFF / WOFF2 per weight) from specimen/glyphs.json and fill the
self-contained type tester. Needs a virtualenv; everything else in this skill is stdlib only.

Setup (once, from the project root):
    python3 -m venv .venv && .venv/bin/pip install fonttools skia-pathops brotli

Rebuild (re-runnable; reads specimen/glyphs.json, overwrites its outputs):
    .venv/bin/python scripts/build_font.py --root <project>
    .venv/bin/python scripts/build_font.py --root <project> --screenshot   # also renders tester.html with headless Chrome

Inputs
    <root>/specimen/glyphs.json   produced by glyphs.py (read only, never written here)
    <root>/font.json, docs/PRD.md family, weights, vendor id (see project.py); optional font.json
                                  "metrics": {"ascender": 950, "descender": -250}
    tester_template.html          next to this script; {{...}} placeholders are filled

Outputs
    <root>/fonts/<Family>-<Weight>.otf / .woff / .woff2 (woff2 only if brotli is importable)
    <root>/specimen/tester.html   one self-contained page with every WOFF embedded

How the outlines are made
    Every glyph in glyphs.json is a list of elements in font units, y up:
      {d, w, cut?}  a stroked skeleton (SVG path data: M L A Z), butt caps, miter joins; `cut`
                    rectangles are removed from the stroked result
      {c:[cx,cy,r]} a filled circle
      {d, f:true}   a filled path
    The skeleton is parsed with fontTools' SVG path parser (elliptical arcs become cubic Beziers)
    into a skia-pathops Path, stroked with Skia's own stroker (the same code Chrome uses to draw the
    SVG specimen), and the pieces are combined with boolean ops: union of strokes, minus the cut
    rectangles, plus circles (4-cubic approximation) and filled paths. The result is simplified
    with consistent winding (outer contours counter-clockwise, PostScript convention) and written
    as CFF Type 2 charstrings.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_project, add_root_arg, slug  # noqa: E402

try:
    import pathops
    from fontTools.fontBuilder import FontBuilder
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.roundingPen import RoundingPen
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    from fontTools.svgLib.path import parse_path
    from fontTools.misc.timeTools import timestampNow
    from fontTools.ttLib import TTFont
except ImportError as exc:  # pragma: no cover
    sys.exit("%s\nrun this with the project venv: python3 -m venv .venv && "
             ".venv/bin/pip install fonttools skia-pathops brotli && .venv/bin/python scripts/build_font.py --root ." % exc)

TEMPLATE = Path(__file__).resolve().parent / "tester_template.html"

VERSION = "0.1"
VERSION_STRING = "Version 0.1;prototype"
UPM = 1000
LINE_GAP = 0
# The specimen page strokes with stroke-miterlimit="10"; use the same so the font matches it.
MITER_LIMIT = 10.0
KAPPA = 0.5522847498307936

NAME_TO_CHAR = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "period": ".", "comma": ",", "colon": ":", "hyphen": "-",
    "exclam": "!", "question": "?", "space": " ",
}

LICENSE_TEXT = ("Prototype build; not yet licensed for redistribution. See the project's PRD "
                "(technical requirements and open questions) for the intended licence.")
LICENSE_URL = "https://openfontlicense.org"


# --------------------------------------------------------------------------- outlines

def svg_to_path(d: str) -> pathops.Path:
    """Parse SVG path data (M L H V A C Q Z) into a pathops Path; arcs become cubics."""
    path = pathops.Path()
    parse_path(d, path.getPen(allow_open_paths=True))
    return path


def rect_path(x0: float, y0: float, x1: float, y1: float) -> pathops.Path:
    p = pathops.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y0)
    p.lineTo(x1, y1)
    p.lineTo(x0, y1)
    p.close()
    return p


def circle_path(cx: float, cy: float, r: float) -> pathops.Path:
    k = KAPPA * r
    p = pathops.Path()
    p.moveTo(cx + r, cy)
    p.cubicTo(cx + r, cy + k, cx + k, cy + r, cx, cy + r)
    p.cubicTo(cx - k, cy + r, cx - r, cy + k, cx - r, cy)
    p.cubicTo(cx - r, cy - k, cx - k, cy - r, cx, cy - r)
    p.cubicTo(cx + k, cy - r, cx + r, cy - k, cx + r, cy)
    p.close()
    return p


def stroke_element(el: dict) -> pathops.Path:
    skeleton = svg_to_path(el["d"])
    skeleton.stroke(float(el["w"]), pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, MITER_LIMIT)
    # The stroker's output is a nonzero-fill shape that may overlap itself; flatten that first.
    skeleton.simplify(fix_winding=True, clockwise=False)
    result = skeleton
    for x0, y0, x1, y1 in el.get("cut", ()):
        result = pathops.op(result, rect_path(x0, y0, x1, y1), pathops.PathOp.DIFFERENCE,
                            fix_winding=True, clockwise=False)
    return result


def build_outline(elements: list[dict]) -> pathops.Path:
    result = pathops.Path()
    for el in elements:
        if "c" in el:
            piece = circle_path(*el["c"])
        elif el.get("f"):
            piece = svg_to_path(el["d"])
        else:
            piece = stroke_element(el)
        result = pathops.op(result, piece, pathops.PathOp.UNION, fix_winding=True, clockwise=False)
    result.simplify(fix_winding=True, clockwise=False)
    return result


def signed_area(points) -> float:
    a = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def check_winding(name: str, path: pathops.Path) -> list[str]:
    """Outer contour must be counter-clockwise (positive area, y up); the sum must be positive."""
    problems = []
    areas = []
    for contour in path.contours:
        pts = [pt for seg in contour.segments for pt in (seg[1] if len(seg) > 1 else ())]
        if len(pts) >= 3:
            areas.append(signed_area(pts))
    if not areas:
        return problems
    if sum(areas) <= 0:
        problems.append(f"{name}: net signed area {sum(areas):.0f} is not positive (fill would invert)")
    biggest = max(areas, key=abs)
    if biggest < 0:
        problems.append(f"{name}: largest contour is clockwise (would render as a hole)")
    return problems


# --------------------------------------------------------------------------- font assembly

def codepoint_for(name: str) -> int | None:
    if len(name) == 1 and name.isascii() and name.isalpha():
        return ord(name)
    ch = NAME_TO_CHAR.get(name)
    return ord(ch) if ch else None


def build_weight(proj: dict, style: str, data: dict, order: list[str], charmap: dict,
                 metrics: dict) -> tuple[TTFont, list[str], dict]:
    family = proj["family"]
    css = proj["css_weights"][style]
    glyphs = data["glyphs"]
    glyph_order = [".notdef"] + [n for n in order if n in glyphs]
    missing = [n for n in order if n not in glyphs]
    if missing:
        print(f"  warning: {style} has no data for {missing}", file=sys.stderr)

    inverse_charmap = {v: k for k, v in charmap.items()}
    cmap = {}
    for name in glyph_order[1:]:
        if "." in name:
            continue  # alternates (a.ss01) are reached through features only
        if name in inverse_charmap:
            cmap[ord(inverse_charmap[name])] = name
        else:
            cp = codepoint_for(name)
            if cp is not None:
                cmap[cp] = name

    charstrings, hmetrics, warnings = {}, {}, []
    for name in glyph_order:
        if name == ".notdef":
            adv, outline = 500, pathops.Path()
        else:
            adv = int(round(glyphs[name]["adv"]))
            outline = build_outline(glyphs[name]["el"])
            warnings += check_winding(f"{style}/{name}", outline)
        t2pen = T2CharStringPen(adv, None)
        bpen = BoundsPen(None)
        outline.draw(RoundingPen(t2pen))
        outline.draw(RoundingPen(bpen))
        charstrings[name] = t2pen.getCharString()
        lsb = int(round(bpen.bounds[0])) if bpen.bounds else 0
        hmetrics[name] = (adv, lsb)

    ps_family = "".join(ch for ch in family if ch.isalnum())
    ps_name = f"{ps_family}-{style}"
    is_bold = style == "Bold"
    is_regular = style == "Regular"
    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(ps_name, {
        "FullName": f"{family} {style}",
        "FamilyName": family,
        "Weight": style,
        "version": VERSION,
        "Notice": LICENSE_TEXT,
    }, charstrings, {})
    fb.setupHorizontalMetrics(hmetrics)
    asc, desc = metrics["ascender"], metrics["descender"]
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=LINE_GAP)
    names = {
        "copyright": f"Copyright the {family} project authors. Prototype.",
        "familyName": family if (is_bold or is_regular) else f"{family} {style}",
        "styleName": "Bold" if is_bold else "Regular",
        "uniqueFontIdentifier": f"{VERSION};{proj['vendor'].strip()};{ps_name}",
        "fullName": f"{family} {style}",
        "version": VERSION_STRING,
        "psName": ps_name,
        "typographicFamily": family,
        "typographicSubfamily": style,
        "licenseDescription": LICENSE_TEXT,
        "licenseInfoURL": LICENSE_URL,
        "description": "Prototype: sample glyph set only, built from stroke skeletons.",
    }
    fb.setupNameTable(names)
    fs_selection = 0x80  # USE_TYPO_METRICS
    fs_selection |= 0x20 if is_bold else 0x40  # BOLD / REGULAR
    fb.setupOS2(
        version=4,
        usWeightClass=css,
        usWidthClass=5,
        fsType=0,
        fsSelection=fs_selection,
        achVendID=proj["vendor"],
        sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=LINE_GAP,
        usWinAscent=asc, usWinDescent=-desc,
        sCapHeight=metrics["cap"], sxHeight=metrics["xh"],
        yStrikeoutPosition=int(metrics["xh"] * 0.6), yStrikeoutSize=100,
    )
    fb.setupPost(underlinePosition=-120, underlineThickness=100)
    now = timestampNow()
    fb.setupHead(fontRevision=float(VERSION), macStyle=0x1 if is_bold else 0, created=now, modified=now)

    # every "<base>.ss01" glyph whose base exists becomes a ss01 substitution
    alts = [(n[: -len(".ss01")], n) for n in glyph_order if n.endswith(".ss01") and n[: -len(".ss01")] in glyph_order]
    if alts:
        subs = "".join(f"                sub {b} by {a};\n" for b, a in alts)
        addOpenTypeFeaturesFromString(fb.font, f"""
            languagesystem DFLT dflt;
            languagesystem latn dflt;
            feature ss01 {{
                featureNames {{ name "Stylistic set 1"; }};
{subs}            }} ss01;
        """)
    return fb.font, warnings, cmap


def write_outputs(font: TTFont, fonts_dir: Path, family: str, style: str) -> dict[str, Path]:
    fonts_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    base = fonts_dir / f"{''.join(ch for ch in family if ch.isalnum())}-{style}"
    font.flavor = None
    font.save(base.with_suffix(".otf"))
    out["otf"] = base.with_suffix(".otf")
    font.flavor = "woff"
    font.save(base.with_suffix(".woff"))
    out["woff"] = base.with_suffix(".woff")
    try:
        import brotli  # noqa: F401
    except ImportError:
        print("  brotli not installed; skipping .woff2", file=sys.stderr)
    else:
        font.flavor = "woff2"
        font.save(base.with_suffix(".woff2"))
        out["woff2"] = base.with_suffix(".woff2")
    font.flavor = None
    return out


def validate(path: Path, expected_glyphs: int, has_ss01: bool, codepoints: set[int], asc: int) -> None:
    font = TTFont(path)
    order = font.getGlyphOrder()
    assert len(order) == expected_glyphs, f"{path.name}: {len(order)} glyphs, expected {expected_glyphs}"
    glyph_set = font.getGlyphSet()
    for name in order:
        pen = RecordingPen()
        glyph_set[name].draw(pen)  # raises on a broken charstring
    if has_ss01:
        assert "GSUB" in font and any(
            fr.FeatureTag == "ss01" for fr in font["GSUB"].table.FeatureList.FeatureRecord
        ), f"{path.name}: ss01 feature missing"
    assert font["OS/2"].fsSelection & 0x80, f"{path.name}: USE_TYPO_METRICS not set"
    assert font["hhea"].ascent == asc and font["OS/2"].sTypoAscender == asc
    cmap = font.getBestCmap()
    for cp in codepoints:
        assert cp in cmap, f"{path.name}: U+{cp:04X} not mapped"
    font.close()


# --------------------------------------------------------------------------- tester page

def unicode_ranges(codepoints: set[int]) -> str:
    cps = sorted(codepoints)
    ranges, start, prev = [], None, None
    for cp in cps + [None]:
        if start is None:
            start = prev = cp
            continue
        if cp is not None and cp == prev + 1:
            prev = cp
            continue
        ranges.append("U+%04X" % start if start == prev else "U+%04X-%04X" % (start, prev))
        start = prev = cp
    return ", ".join(ranges)


def write_tester(proj: dict, woffs: dict[str, Path], outputs: dict[str, dict[str, Path]],
                 codepoints: set[int], metrics: dict, has_ss01: bool) -> None:
    family = proj["family"]
    styles = list(proj["weights"])
    css = proj["css_weights"]
    urange = unicode_ranges(codepoints)
    faces = []
    for s in styles:
        b64 = base64.b64encode(woffs[s].read_bytes()).decode("ascii")
        faces.append('@font-face {\n  font-family: "%s"; font-style: normal; font-weight: %d; font-display: block;\n'
                     '  src: url(data:font/woff;base64,%s) format("woff");\n  unicode-range: %s;\n}'
                     % (family, css[s], b64, urange))
    buttons = "\n".join('        <button type="button" id="w%d" data-weight="%d" aria-pressed="false">%s %d</button>'
                        % (css[s], css[s], html.escape(s), css[s]) for s in styles)
    rows = "\n".join('      <div class="row"><span class="label">%s %d · stem %d</span><p class="sample fixed" '
                     'style="font-weight: %d">The quick brown fox jumps over the lazy dog 0123456789</p></div>'
                     % (html.escape(s), css[s], proj["weights"][s], css[s]) for s in styles)
    ss01_row = ""
    if has_ss01:
        spans = " ".join('<span style="font-weight:%d">Hamburgefonstiv</span>' % css[s] for s in styles)
        ss01_row = ('      <div class="row"><span class="label">ss01 · all weights</span>'
                    '<p class="sample fixed" style="font-feature-settings: \'ss01\'">%s</p></div>' % spans)
    chars = "".join(chr(cp) for cp in sorted(codepoints) if cp != 32)
    letters = "".join(c for c in chars if c.isalpha())
    digits = "".join(c for c in chars if c.isdigit())
    others = " ".join(c for c in chars if not c.isalnum())
    sample = " ".join(x for x in (letters[: len(letters) // 2] if letters[: len(letters) // 2].isupper() else letters,
                                  letters[len(letters) // 2:] if letters[: len(letters) // 2].isupper() else "",
                                  digits, others) if x)
    files = ", ".join("<code>fonts/%s</code>" % html.escape(outputs[s]["otf"].name) for s in styles) + \
            " plus <code>.woff</code>" + (" and <code>.woff2</code>" if "woff2" in outputs[styles[0]] else "") + " of each"
    metrics_line = "%d upm · ascender %d · descender %d · line gap 0 · cap %d · x-height %d · USE_TYPO_METRICS" % (
        UPM, metrics["ascender"], metrics["descender"], metrics["cap"], metrics["xh"])
    page = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{FAMILY}}": html.escape(family),
        "{{FAMILY_JSON}}": json.dumps(family),
        "{{FONT_FACES}}": "\n".join(faces),
        "{{WEIGHT_BUTTONS}}": buttons,
        "{{WEIGHT_ROWS}}": rows,
        "{{SS01_ROW}}": ss01_row,
        "{{SAMPLE_CHARS}}": html.escape(sample),
        "{{SAMPLE_CHARS_LABEL}}": html.escape("letters %s, digits %s, punctuation %s" % (letters, digits, others)),
        "{{FONT_FILES}}": files,
        "{{METRICS}}": metrics_line,
        "{{WEIGHTS_JSON}}": json.dumps([css[s] for s in styles]),
        "{{DEFAULT_CSS}}": str(css[proj["default"]]),
        "{{STORE}}": json.dumps(slug(family) + "-tester-v1"),
        "{{WEIGHT_COUNT}}": str(len(styles)),
        "{{WEIGHT_SUMMARY}}": html.escape(", ".join("%s %d" % (s, css[s]) for s in styles)),
    }
    for k, v in repl.items():
        page = page.replace(k, v)
    assert "{{" not in page, "template placeholder left unfilled: %s" % page[page.index("{{"):page.index("{{") + 30]
    Path(proj["tester"]).parent.mkdir(parents=True, exist_ok=True)
    Path(proj["tester"]).write_text(page, encoding="utf-8")


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = add_root_arg(argparse.ArgumentParser(description=__doc__.strip().splitlines()[0]))
    ap.add_argument("--screenshot", action="store_true", help="render tester.html with headless Chrome")
    ap.add_argument("--screenshot-dir", type=Path, default=None, help="default: <root>/fonts/screenshots")
    args = ap.parse_args()
    proj = load_project(args.root)
    glyphs_json = Path(proj["glyphs_json"])
    if not glyphs_json.exists():
        sys.exit(f"no {glyphs_json}: run glyphs.py --root {proj['root']} first")

    data = json.loads(glyphs_json.read_text(encoding="utf-8"))
    order, charmap = data["order"], data.get("charmap", {})
    if "space" not in order:
        order = ["space"] + order
    m = data.get("metrics", {})
    metrics = {"cap": m.get("cap", 700), "xh": m.get("xh", 510),
               "ascender": proj["vmetrics"]["ascender"], "descender": proj["vmetrics"]["descender"]}

    woffs, outputs, all_warnings, codepoints = {}, {}, [], set()
    has_ss01 = False
    for style in proj["weights"]:
        weight_data = data["weights"].get(style)
        if weight_data is None:
            print(f"error: weight {style} missing from glyphs.json", file=sys.stderr)
            return 1
        print(f"{style} (stem {weight_data.get('stem')})")
        font, warnings, cmap = build_weight(proj, style, weight_data, order, charmap, metrics)
        all_warnings += warnings
        codepoints = set(cmap)
        has_ss01 = any(n.endswith(".ss01") for n in font.getGlyphOrder())
        outputs[style] = write_outputs(font, Path(proj["fonts_dir"]), proj["family"], style)
        n_glyphs = len(font.getGlyphOrder())
        for kind, p in outputs[style].items():
            validate(p, n_glyphs, has_ss01, codepoints, metrics["ascender"])
            print(f"  {p.relative_to(proj['root'])}  {p.stat().st_size:,} bytes  ({n_glyphs} glyphs, ok)")
        woffs[style] = outputs[style]["woff"]
    for style in data["weights"]:
        if style not in proj["weights"]:
            print(f"skipping weight {style}: in glyphs.json but not in the project config", file=sys.stderr)

    write_tester(proj, woffs, outputs, codepoints, metrics, has_ss01)
    tester = Path(proj["tester"])
    print(f"{tester.relative_to(proj['root'])}  {tester.stat().st_size:,} bytes")

    if all_warnings:
        print("\nOutline warnings:")
        for w in all_warnings:
            print("  " + w)
    if args.screenshot:
        from screenshot import shoot
        out_dir = args.screenshot_dir or Path(proj["fonts_dir"]) / "screenshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        for width, height in ((1280, 1400), (400, 3000)):
            print("  screenshot", shoot(tester, out_dir / f"tester-{width}.png", width, height, wrap=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
