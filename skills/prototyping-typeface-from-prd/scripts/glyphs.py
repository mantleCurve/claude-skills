#!/usr/bin/env python3
"""Sample-glyph generator: stroke skeletons on a 1000 UPM grid -> specimen/glyphs.json. Stdlib only.

    python3 glyphs.py --root <project>     (default root: the current directory)

Copy this file into the project (tools/glyphs.py) and edit it there: the metrics block mirrors
PRD section 8 and every @glyph recipe is the design. The family name and the weight stems come
from <root>/font.json or <root>/docs/PRD.md (see project.py / font.example.json in the skill);
the recipes interpolate on the stem between the lightest, default and boldest weights.

Defines sample glyphs as stroke skeletons (y up, baseline 0) and emits SVG path data per weight.

Output: specimen/glyphs.json
  { "family": "...", "metrics": {...}, "order": [...], "charmap": {...}, "weights": {
    "<Weight>": { "stem": 108, "css": 500, "glyphs": { "<name>": { "adv": 560, "el": [
        {"d": "M ... A ...", "w": 108, "cut": [[x0,y0,x1,y1], ...]},   # stroked path
        {"d": "M ... L ... Z", "f": 1},                                 # filled polygon
        {"c": [cx, cy, r]}                                              # filled dot
  ] } } } }

"cut" lists rectangles (font units) that are removed from the stroke. The renderer
implements them as an even-odd clip-path so arc terminals get true vertical or
horizontal flat cuts.

Every x coordinate is designed in default-weight width space and scaled by a per-weight
width factor (lightest 0.97, default 1.00, boldest 1.03) when serialised, following the
PRD's "widths grow with weight by no more than 6 percent". Filled polygons (z Z 1 7)
are computed directly in the scaled space so their stem widths and mitres stay exact;
fill_poly() stores them pre-divided by the factor.
"""

import argparse
import json
import math
import os
import re
import sys

# ---------------------------------------------------------------- project config
CSS_WEIGHTS = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500,
               "SemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900}
DEFAULT_WEIGHTS = {"Light": 62, "Medium": 108, "Bold": 158}


def load_project(root):
    """family + weights from <root>/font.json, else docs/PRD.md (H1 and the weights table), else
    the defaults. Mirrors project.py in the skill; duplicated so this file stands alone once it
    is copied into a project."""
    root = os.path.abspath(root)
    cfg = {}
    fj = os.path.join(root, "font.json")
    if os.path.exists(fj):
        with open(fj, encoding="utf-8") as f:
            cfg = json.load(f)
    family, weights = cfg.get("family"), cfg.get("weights")
    prd_path = os.path.join(root, "docs", "PRD.md")
    if os.path.exists(prd_path) and not (family and weights):
        text = open(prd_path, encoding="utf-8").read()
        m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
        if m and not family:
            family = re.split(r"\s+[—–-]\s+", m.group(1))[0].strip()
        sec = re.search(r"^##\s+\d*\.?\s*Weights and axes\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if sec and not weights:
            rows = [[c.strip() for c in ln.strip().strip("|").split("|")]
                    for ln in sec.group(1).splitlines() if ln.strip().startswith("|")]
            if rows:
                col = next((i for i, h in enumerate(rows[0]) if "stem" in h.lower()), None)
                found = {}
                for r in rows[1:]:
                    name = re.sub(r"\s*\(.*\)\s*", "", r[0]).strip()
                    if col is not None and name in CSS_WEIGHTS and len(r) > col and re.sub(r"[^\d]", "", r[col]):
                        found[name] = int(re.sub(r"[^\d]", "", r[col]))
                weights = found or None
    weights = dict(sorted((weights or DEFAULT_WEIGHTS).items(), key=lambda kv: kv[1]))
    bad = [w for w in weights if w not in CSS_WEIGHTS]
    if bad:
        sys.exit("weights must use standard style names %s; got %s" % (list(CSS_WEIGHTS), bad))
    names = list(weights)
    default = cfg.get("default") or ("Medium" if "Medium" in weights else names[len(names) // 2])
    return {"root": root, "family": family or "Untitled", "weights": weights, "default": default}

# ---------------------------------------------------------------- metrics (PRD 8)
UPM = 1000
CAP = 700
XH = 510
ASC = 750
DESC = -230
TH = 650
OVER = 12
LC_W, LC_H, LC_CY = 480, 534, 255        # lowercase bowl outer box
UC_W, UC_H, UC_CY = 660, 724, 350        # capital ellipse outer box
SB_S, SB_R = 70, 40                      # default sidebearings straight / round
SPACE = 240
RATIO = LC_H / LC_W                      # 1.1125, the ellipse family ratio

# Weight stems: lightest / default / boldest, set from the project config by configure().
# Recipes interpolate on these (lerp_w, width_factor), so the PRD's weights table drives them.
S_LIGHT, S_MED, S_BOLD = 62, 108, 158
WEIGHTS = [("Light", 62), ("Medium", 108), ("Bold", 158)]


def configure(weights, default):
    """weights: {name: stem} sorted by stem; default: the design-origin weight name."""
    global S_LIGHT, S_MED, S_BOLD, WEIGHTS
    stems = list(weights.values())
    S_LIGHT, S_MED, S_BOLD = stems[0], weights[default], stems[-1]
    WEIGHTS = list(weights.items())


def width_factor(stem):
    if stem <= S_MED:
        return 1.0 + 0.03 * (stem - S_MED) / max(1.0, S_MED - S_LIGHT)
    return 1.0 + 0.03 * (stem - S_MED) / max(1.0, S_BOLD - S_MED)


# ---------------------------------------------------------------- geometry helpers
def P(a, rx, ry, cx, cy):
    """Point on ellipse at angle a (degrees, 0 = right, 90 = up)."""
    r = math.radians(a)
    return (cx + rx * math.cos(r), cy + ry * math.sin(r))


def arc_cmds(cx, cy, rx, ry, a0, a1, move=True):
    """Arc commands from angle a0 to a1 (degrees). Positive direction = counter-clockwise
    in y-up space. Spans >180 are split so flags stay unambiguous."""
    cmds = []
    if move:
        cmds.append(("M",) + P(a0, rx, ry, cx, cy))
    n = max(1, int(math.ceil(abs(a1 - a0) / 179.0)))
    step = (a1 - a0) / n
    sweep = 1 if a1 > a0 else 0
    for i in range(1, n + 1):
        cmds.append(("A", rx, ry, 0, sweep) + P(a0 + step * i, rx, ry, cx, cy))
    return cmds


def ellipse_cmds(cx, cy, rx, ry):
    return arc_cmds(cx, cy, rx, ry, 0, 360) + [("Z",)]


def line_pt(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def at_y(p, q, y):
    """x where the infinite line p-q crosses height y."""
    return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])


def offset_line(p, q, dist):
    """Shift segment p-q perpendicular by dist (positive = to the left of travel)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * dist, dx / L * dist
    return (p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny)


def skeleton_from_outer(p, q, h, inward_sign):
    """Given the OUTER edge line through p,q and half stroke h, return the skeleton line."""
    return offset_line(p, q, h * inward_sign)


def solve_vee(xl, xr, y_lo, y_hi, s, apex_down=True, W=None):
    """Two diagonals whose outer edges pass through (xl, y_open) and (xr, y_open), meeting
    in a mitred apex trimmed flat to width W at y_cut. Returns (x_skel_at_open, y_apex, alpha).
    y_open is y_hi for an apex pointing down (v), y_lo for an apex pointing up (A)."""
    h = s / 2.0
    W = W if W is not None else 1.1 * s
    cx = (xl + xr) / 2.0
    H = y_hi - y_lo
    alpha = math.atan((cx - xl) / H)
    for _ in range(40):
        ta, sa, ca = math.tan(alpha), math.sin(alpha), math.cos(alpha)
        # distance from cut line to skeleton apex so that the trimmed flat is W wide
        d_apex = -W / (2 * ta) + h / sa
        if apex_down:
            y_a = y_lo + d_apex
            alpha = math.atan((cx - xl - h / ca) / (y_hi - y_a))
        else:
            y_a = y_hi - d_apex
            alpha = math.atan((cx - xl - h / ca) / (y_a - y_lo))
    x_open = xl + h / math.cos(alpha)
    return x_open, y_a, alpha


def solve_zigzag(xl, xr, y_lo, y_hi, s, n, W=None):
    """n equal diagonals alternating between y_hi and y_lo with mitred apexes trimmed to W.
    Returns list of skeleton vertices, left to right, starting at the top (y_hi side)."""
    h = s / 2.0
    W = W if W is not None else 1.1 * s

    def build(alpha):
        ta, sa, ca = math.tan(alpha), math.sin(alpha), math.cos(alpha)
        d = -W / (2 * ta) + h / sa          # apex overshoot beyond cut line
        y_bot, y_top = y_lo + d, y_hi - d   # skeleton apex heights (bottom / top)
        x = xl + h / ca                      # skeleton x at the y_hi opening edge
        # first stroke starts at the top-left; its top is the open (clipped) end
        pts = [(x - (y_hi - y_top) * ta, y_top) if False else None]
        pts = []
        # vertex 0: top-left open end (skeleton point at y_hi), extended above later
        x0 = x
        pts.append((x0, y_hi))
        run = (y_hi - y_bot) * ta
        xa = x0 + run
        pts.append((xa, y_bot))
        for i in range(1, n):
            if i % 2 == 1:   # going up to a top vertex
                xa = xa + (y_top - y_bot) * ta
                pts.append((xa, y_top))
            else:            # going down to a bottom vertex
                xa = xa + (y_top - y_bot) * ta
                pts.append((xa, y_bot))
        # last vertex: if n is even we end at the top (open end at y_hi), if odd at bottom
        last = pts[-1]
        if n % 2 == 0:
            # replace last top vertex by the open end at y_hi (same line)
            xe = pts[-2][0] + (y_hi - y_bot) * ta
            pts[-1] = (xe, y_hi)
            right_outer = xe + h / ca
        else:
            xe = pts[-2][0] + (y_top - y_lo) * ta
            pts[-1] = (xe, y_lo)
            right_outer = xe + h / ca
        return pts, right_outer

    lo, hi = math.radians(5), math.radians(80)
    for _ in range(60):
        mid = (lo + hi) / 2
        _, ro = build(mid)
        if ro < xr:
            lo = mid
        else:
            hi = mid
    pts, _ = build((lo + hi) / 2)
    return pts


def extend_open_ends(pts, y_lo, y_hi, margin=60):
    """Extend first and last segments of a polyline beyond the clip band."""
    pts = list(pts)
    a, b = pts[0], pts[1]
    ty = y_hi + margin if a[1] >= b[1] else y_lo - margin
    pts[0] = (at_y(a, b, ty), ty)
    a, b = pts[-1], pts[-2]
    ty = y_hi + margin if a[1] >= b[1] else y_lo - margin
    pts[-1] = (at_y(a, b, ty), ty)
    return pts


def poly_cmds(pts):
    cmds = [("M",) + tuple(pts[0])]
    for p in pts[1:]:
        cmds.append(("L",) + tuple(p))
    return cmds


BIG = 5000


def band(y_lo, y_hi):
    """Cut rectangles that keep only y_lo..y_hi (flat horizontal cuts)."""
    return [[-BIG, y_hi, BIG, BIG], [-BIG, -BIG, BIG, y_lo]]


def ellipse_cut_right(cx, cy, rx, ry, s, inner_angle, lo=None, hi=None):
    """Vertical flat terminal cut on the right side of an ellipse stroke. The inner corner of
    the cut sits at inner_angle (degrees) on the inner contour. Returns (cutX, rect)."""
    h = s / 2.0
    rxi, rxo, ryo = rx - h, rx + h, ry + h
    cut_x = cx + rxi * math.cos(math.radians(inner_angle))
    yo = ryo * math.sqrt(max(0.0, 1 - ((cut_x - cx) / rxo) ** 2))
    y_top = cy + yo if hi is None else hi
    y_bot = cy - yo if lo is None else lo
    return cut_x, [cut_x, y_bot, BIG, y_top]


def ellipse_cut_left(cx, cy, rx, ry, s, inner_angle, lo=None, hi=None):
    h = s / 2.0
    rxi, rxo, ryo = rx - h, rx + h, ry + h
    cut_x = cx + rxi * math.cos(math.radians(inner_angle))
    yo = ryo * math.sqrt(max(0.0, 1 - ((cut_x - cx) / rxo) ** 2))
    y_top = cy + yo if hi is None else hi
    y_bot = cy - yo if lo is None else lo
    return cut_x, [-BIG, y_bot, cut_x, y_top]


# ---------------------------------------------------------------- element builders
def stroke(cmds, w, cut=None):
    e = {"cmds": cmds, "w": w}
    if cut:
        e["cut"] = cut
    return e


def dot(cx, cy, r):
    return {"c": [cx, cy, r]}


def fill_poly(c, pts):
    """Filled polygon whose points are given in FINAL (width-scaled) x-space. Stored divided
    by the width factor so serialisation lands every corner exactly where it was computed."""
    cmds = [("M", pts[0][0] / c.wf, pts[0][1])] + [("L", x / c.wf, y) for x, y in pts[1:]] + [("Z",)]
    return {"cmds": cmds, "f": True}


def inner_corner(c, cx, cy, rx, ry, ang):
    """Point on the INNER contour of a stroked ellipse at skeleton angle ang (degrees), i.e.
    the skeleton point moved half a stroke along the inward normal. Computed in final x-space
    (stroke width is not scaled, the ellipse is) and returned in design space."""
    wf, h = c.wf, c.h
    t = math.radians(ang)
    rxf = rx * wf
    nx, ny = ry * math.cos(t), rxf * math.sin(t)
    n = math.hypot(nx, ny)
    px, py = cx * wf + rxf * math.cos(t), cy + ry * math.sin(t)
    return (px - h * nx / n) / wf, py - h * ny / n


def face_cut(c, cx, cy, rx, ry, ang, side):
    """Anchored vertical terminal face (the s_like technique): the stroked ellipse skeleton ENDS
    at angle ang; the face is the vertical line through that end's inner-contour corner, and the
    returned cut rectangle removes the quadrant beyond the corner that holds the butt cap.
    side: 'ur' upper-right, 'lr' lower-right, 'ul' upper-left, 'll' lower-left terminal.
    Returns (rect, ix, iy) with the corner in design space."""
    ix, iy = inner_corner(c, cx, cy, rx, ry, ang)
    rect = {"ur": [ix, iy - 0.5, BIG, BIG], "lr": [ix, -BIG, BIG, iy + 0.5],
            "ul": [-BIG, iy - 0.5, ix, BIG], "ll": [-BIG, -BIG, ix, iy + 0.5]}[side]
    return rect, ix, iy


def lerp_w(c, light, medium, bold):
    """Piecewise-linear per-weight value keyed on the stem (lightest / default / boldest)."""
    s = c.s
    if s <= S_MED:
        return light + (medium - light) * (s - S_LIGHT) / max(1.0, S_MED - S_LIGHT)
    return medium + (bold - medium) * (s - S_MED) / max(1.0, S_BOLD - S_MED)


def c_angle(c):
    """Inner-contour angle of the c / C terminal faces: 30 deg up to Medium, 45 deg at Bold, so
    the face's acute corner never gets spiky as the inner radius shrinks."""
    return max(30.0, 30.0 + 0.3 * (c.s - S_MED))


def diag_angle(x_hi, y_hi, x_lo, y_lo, s):
    """Angle from vertical of a band of width s whose right edge passes through (x_hi, y_hi) and
    whose left edge passes through (x_lo, y_lo), the band running between those two points."""
    D = math.hypot(x_hi - x_lo, y_hi - y_lo)
    return math.atan2(x_hi - x_lo, y_hi - y_lo) - math.asin(s / D)


def vline(x, y0, y1, w):
    return stroke([("M", x, y0), ("L", x, y1)], w)


def hline(x0, x1, y, w):
    return stroke([("M", x0, y), ("L", x1, y)], w)


class Ctx:
    """Per-weight derived values."""

    def __init__(self, stem):
        self.s = stem
        self.h = stem / 2.0
        self.wf = width_factor(stem)
        self.b = round(0.94 * stem, 1)       # horizontal stroke
        self.hb = self.b / 2.0
        self.d = round(1.09 * stem, 1)       # dot diameter
        self.rd = self.d / 2.0
        # lowercase bowl skeleton radii
        self.rx = (LC_W - stem) / 2.0
        self.ry = (LC_H - stem) / 2.0
        # capital ellipse skeleton radii
        self.RX = (UC_W - stem) / 2.0
        self.RY = (UC_H - stem) / 2.0
        # lowercase arch (n): outer width 420
        self.rxn = (420 - stem) / 2.0
        self.ryn = self.rxn * RATIO
        self.cyn = XH + OVER - self.h - self.ryn


# ---------------------------------------------------------------- glyphs
GLYPHS = {}


def glyph(name, adv):
    def deco(fn):
        GLYPHS[name] = (adv, fn)
        return fn
    return deco


# ---------- lowercase ----------
@glyph("o", 560)
def g_o(c):
    return [stroke(ellipse_cmds(280, LC_CY, c.rx, c.ry), c.s)]


def bowl_with_stem(c, stem_left, y0, y1, adv):
    """b/d/p/q family: bowl outer 480 tangent to a stem."""
    if stem_left:
        sx = SB_S + c.h
        cx = sx + c.rx
    else:
        cx = SB_R + LC_W / 2.0
        sx = cx + c.rx
    return [vline(sx, y0, y1, c.s), stroke(ellipse_cmds(cx, LC_CY, c.rx, c.ry), c.s)]


@glyph("b", 590)
def g_b(c): return bowl_with_stem(c, True, 0, ASC, 590)


@glyph("d", 590)
def g_d(c): return bowl_with_stem(c, False, 0, ASC, 590)


@glyph("p", 590)
def g_p(c): return bowl_with_stem(c, True, DESC, XH, 590)


@glyph("q", 590)
def g_q(c): return bowl_with_stem(c, False, DESC, XH, 590)


@glyph("a.ss01", 560)
def g_a_ss01(c):
    cx = SB_R + LC_W / 2.0
    sx = cx + c.rx
    return [vline(sx, 0, XH, c.s), stroke(ellipse_cmds(cx, LC_CY, c.rx, c.ry), c.s)]


@glyph("a", 540)
def g_a(c):
    # Double-storey. Right stem from the baseline to the hood's springing height hy. Hood: exact
    # half-ellipse from the stem (0 deg, tangent vertical, flush with the stem's right edge) over
    # the top to 9 o'clock, where the tangent is vertical again so the butt cap is a horizontal
    # full-width flat cut. Bowl: ellipse on the baseline whose skeleton is tangent to the stem
    # centre line, so its outer right edge merges into the stem with no step.
    # Vertical budget (x-height 510 + overshoots = 534) per weight: bowl outer height, clearance
    # between bowl top and hood terminal, hood band. At Bold the stem alone (158) leaves no room
    # for an open hood counter, so the hood there is the solid half-ellipse (inner radius 0) and
    # the clearance drops to 30; see the report. The a is allowed to grow to 555 (x1.03 = 572,
    # 6 percent over Medium) at Bold.
    s, h = c.s, c.h
    adv = lerp_w(c, 540, 540, 555)
    right_outer = adv - SB_S
    sx = right_outer - h
    bowl_w = right_outer - 50                     # bowl outer left edge at x = 50
    bowl_h = lerp_w(c, 330, 330, 346)             # outer height incl. overshoot (counter >= 30)
    gap = lerp_w(c, 40, 40, 30)                   # hood terminal to bowl outer top
    rxb, ryb = (bowl_w - s) / 2.0, (bowl_h - s) / 2.0
    bx, by = sx - rxb, -OVER + h + ryb
    hy = (-OVER + bowl_h) + gap                   # hood springs here; terminal cap at this y
    ryh = XH + OVER - h - hy
    x_t = SB_R + 20 + h                           # hood terminal centre x
    rxh = (sx - x_t) / 2.0
    hcx = sx - rxh
    if ryh - h >= 1:
        hood = stroke(arc_cmds(hcx, hy, rxh, ryh, 0, 180), s)
    else:
        # degenerate counter: fill the outer half-ellipse down to the flat underside at hy
        # (h / wf: the outer offset must stay h after width scaling, flush with the stem edge)
        ho = h / c.wf
        hood = {"cmds": arc_cmds(hcx, hy, rxh + ho, ryh + h, 0, 180) + [("L", sx + ho, hy), ("Z",)], "f": True}
    # the stem runs 3 units up into the hood band (hidden inside it) so there is no seam at hy
    return (adv, [vline(sx, 0, hy + 3, s), hood, stroke(ellipse_cmds(bx, by, rxb, ryb), s)])


@glyph("c", 520)
def g_c(c):
    cx = SB_R + LC_W / 2.0
    _, cut = ellipse_cut_right(cx, LC_CY, c.rx, c.ry, c.s, c_angle(c))
    return [stroke(ellipse_cmds(cx, LC_CY, c.rx, c.ry), c.s, [cut])]


@glyph("e", 540)
def g_e(c):
    # Lower terminal: anchored vertical face through the inner-contour corner at skeleton angle
    # -theta (steeper at Bold so the aperture stays open). Everything right of the face from the
    # baseline up to the bar's centre line is removed, so the face runs cleanly from the corner
    # down to the outer contour and the bar hides the ring's cut edge. The bar runs to the
    # bowl's rightmost outer edge (h / wf keeps the end flush after width scaling).
    cx = 270
    bar_y = 265
    theta = lerp_w(c, 40, 48, 68)
    _, ix, _ = face_cut(c, cx, LC_CY, c.rx, c.ry, -theta, "lr")
    cut = [ix, -BIG, BIG, bar_y]
    return [stroke(ellipse_cmds(cx, LC_CY, c.rx, c.ry), c.s, [cut]),
            hline(cx - c.rx, cx + c.rx + c.h / c.wf, bar_y, c.b)]


@glyph("f", 380)
def g_f(c):
    sx = 16 + 120 + c.h           # same left clearance as the t crossbar
    rxf, ryf = 130, 130 * RATIO
    top = ASC - c.h
    path = [("M", sx, 0), ("L", sx, top - ryf)] + arc_cmds(sx + rxf, top - ryf, rxf, ryf, 180, 90, move=False)
    return [stroke(path, c.s), hline(sx - c.h - 120, sx + c.h + 120, XH - c.hb, c.b)]


@glyph("g", 560)
def g_g(c):
    cx = SB_R + LC_W / 2.0
    sx = SB_R + LC_W - c.h                 # stem centre, outer edge tangent to bowl right edge
    rxt = 200
    ryt = 60 + c.h                         # inner radius stays 60 at every weight
    ty = DESC + c.h                        # tail skeleton so the BOTTOM edge sits at -230
    yc = ty + ryt                          # curve centre height = end of the straight stem
    path = [("M", sx, XH), ("L", sx, yc)] + arc_cmds(sx - rxt, yc, rxt, ryt, 0, -90, move=False) + [("L", 60, ty)]
    return [stroke(ellipse_cmds(cx, LC_CY, c.rx, c.ry), c.s), stroke(path, c.s)]


def arch(c, x_from, x_to, up=True):
    """Half-ellipse arch between two stem centre lines. up=True: n/m/h arch at the top."""
    rx = (x_to - x_from) / 2.0
    ry = rx * RATIO
    if up:
        cy = XH + OVER - c.h - ry
        return arc_cmds(x_from + rx, cy, rx, ry, 180, 0), cy
    cy = -OVER + c.h + ry
    return arc_cmds(x_from + rx, cy, rx, ry, 180, 360), cy


@glyph("n", 560)
def g_n(c):
    lx, rx_ = SB_S + c.h, 560 - SB_S - c.h
    a, cy = arch(c, lx, rx_)
    return [vline(lx, 0, XH, c.s), stroke(a + [("L", rx_, 0)], c.s)]


@glyph("h", 560)
def g_h(c):
    lx, rx_ = SB_S + c.h, 560 - SB_S - c.h
    a, cy = arch(c, lx, rx_)
    return [vline(lx, 0, ASC, c.s), stroke(a + [("L", rx_, 0)], c.s)]


@glyph("m", 860)
def g_m(c):
    lx, rx_ = SB_S + c.h, 860 - SB_S - c.h
    mx = (lx + rx_) / 2.0
    a1, _ = arch(c, lx, mx)
    a2, _ = arch(c, mx, rx_)
    return [vline(lx, 0, XH, c.s), stroke(a1 + [("L", mx, 0)], c.s), stroke(a2 + [("L", rx_, 0)], c.s)]


@glyph("u", 560)
def g_u(c):
    lx, rx_ = SB_S + c.h, 560 - SB_S - c.h
    a, cy = arch(c, lx, rx_, up=False)
    return [stroke([("M", lx, XH), ("L", lx, cy)] + a[1:], c.s), vline(rx_, 0, XH, c.s)]


@glyph("i", 248)
def g_i(c):
    return [vline(124, 0, XH, c.s), dot(124, 580 + c.rd, c.rd)]


@glyph("j", 248)
def g_j(c):
    return [vline(124, DESC, XH, c.s), dot(124, 580 + c.rd, c.rd)]


@glyph("l", 248)
def g_l(c):
    return [vline(124, 0, ASC, c.s)]


@glyph("k", 520)
def g_k(c):
    sx = SB_S + c.h
    return [vline(sx, 0, ASC, c.s)] + k_arms(c, sx, 500, XH, 255)


@glyph("r", 330)
def g_r(c):
    sx = SB_S + c.h
    rxr = 130
    ryr = rxr * RATIO
    cy = XH + OVER - c.h - ryr
    return [vline(sx, 0, XH, c.s), stroke(arc_cmds(sx + rxr, cy, rxr, ryr, 180, 90), c.s)]


def s_like(c, adv, y_top_outer, y_bot_outer, sb, beta_deg=38.0):
    """Three-piece s: upper arc, straight spine tangent to both arcs, lower arc.
    Bowl proportions (r = ry/rx) are solved so the outer width equals adv - 2*sb.
    Terminals are vertical flat faces: each arc ends exactly at skeleton angle theta_t and the
    face is the vertical line through that end's INNER-contour corner, so the butt cap lies
    entirely inside the removed region and the face runs cleanly from the inner corner up (or
    down) to the outer contour. Nothing of the stroke continues past the face."""
    s, h = c.s, c.h
    T, B = y_top_outer - h, y_bot_outer + h
    Hsk = T - B
    ryu, ryl = 0.47 * Hsk / 2.0, 0.53 * Hsk / 2.0
    beta = math.radians(beta_deg)
    theta_t = math.radians(30 + (s - S_MED) * 0.18)
    target = adv - 2 * sb

    def face_dx(rx, ry):
        # horizontal distance from the skeleton end to its inner-contour corner at theta_t
        nx, ny = ry * math.cos(theta_t), rx * math.sin(theta_t)
        return h * nx / math.hypot(nx, ny)

    def solve(r):
        rxu, rxl = ryu / r, ryl / r
        thl = math.atan(r / math.tan(beta))
        L = (Hsk - (ryu + ryl) * (1 + math.sin(thl))) / math.sin(beta)
        width = ((rxu + rxl) * (math.cos(thl) + math.cos(theta_t)) - L * math.cos(beta)
                 - face_dx(rxu, ryu) - face_dx(rxl, ryl))
        return rxu, rxl, thl, L, width

    lo, hi = 0.3, 4.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if solve(mid)[4] > target:
            lo = mid
        else:
            hi = mid
    r = (lo + hi) / 2
    rxu, rxl, thl, L, width = solve(r)
    thu = thl + math.pi
    cy_s = T - (L / 2) * math.sin(beta) - ryu * (1 + math.sin(thl))
    Tu = (-(L / 2) * math.cos(beta), cy_s + (L / 2) * math.sin(beta))
    Tl = ((L / 2) * math.cos(beta), cy_s - (L / 2) * math.sin(beta))
    Cu = (Tu[0] - rxu * math.cos(thu), Tu[1] - ryu * math.sin(thu))
    Cl = (Tl[0] - rxl * math.cos(thl), Tl[1] - ryl * math.sin(thl))
    tt = math.degrees(theta_t)
    iu = inner_corner(c, Cu[0], Cu[1], rxu, ryu, tt)          # upper terminal inner corner
    il = inner_corner(c, Cl[0], Cl[1], rxl, ryl, tt - 180)    # lower terminal inner corner
    dx = sb - il[0]                                    # shift so the lower face sits at sb
    Cu, Cl = (Cu[0] + dx, Cu[1]), (Cl[0] + dx, Cl[1])
    Tl = (Tl[0] + dx, Tl[1])
    iu, il = (iu[0] + dx, iu[1]), (il[0] + dx, il[1])
    upper = arc_cmds(Cu[0], Cu[1], rxu, ryu, tt, math.degrees(thu))
    lower = arc_cmds(Cl[0], Cl[1], rxl, ryl, math.degrees(thl), tt - 180, move=False)
    cmds = upper + [("L",) + Tl] + lower
    # the butt caps point outward from the inner corners, so clipping right-of/above the upper
    # corner and left-of/below the lower corner removes exactly the flare beyond each face
    cuts = [[iu[0], iu[1] - 0.5, BIG, BIG], [-BIG, -BIG, il[0], il[1] + 0.5]]
    return [stroke(cmds, s, cuts)]


@glyph("s", 480)
def g_s(c):
    return s_like(c, 480, XH + OVER, -OVER, 40)


@glyph("t", 380)
def g_t(c):
    sx = 190
    return [vline(sx, 0, TH, c.s), hline(sx - c.h - 120, sx + c.h + 120, XH - c.hb, c.b)]


@glyph("v", 500)
def g_v(c):
    pts = solve_zigzag(20, 480, 0, XH, c.s, 2)
    return [stroke(poly_cmds(extend_open_ends(pts, 0, XH)), c.s, band(0, XH))]


@glyph("w", 760)
def g_w(c):
    pts = solve_zigzag(20, 740, 0, XH, c.s, 4)
    return [stroke(poly_cmds(extend_open_ends(pts, 0, XH)), c.s, band(0, XH))]


def cross_diag(c, xl, xr, y_lo, y_hi):
    """Skeleton of a diagonal whose outer edges pass (xl, y_hi) and (xr, y_lo)."""
    h = c.h
    alpha = math.atan((xr - xl) / (y_hi - y_lo))
    for _ in range(30):
        alpha = math.atan((xr - xl - 2 * h / math.cos(alpha)) / (y_hi - y_lo))
    o = h / math.cos(alpha)
    return (xl + o, y_hi), (xr - o, y_lo)


@glyph("x", 500)
def g_x(c):
    p, q = cross_diag(c, 20, 480, 0, XH)
    ext = extend_open_ends([p, q], 0, XH)
    m = extend_open_ends([(500 - p[0], p[1]), (500 - q[0], q[1])], 0, XH)
    return [stroke(poly_cmds(ext), c.s, band(0, XH)), stroke(poly_cmds(m), c.s, band(0, XH))]


@glyph("y", 500)
def g_y(c):
    # right diagonal: outer right edge through (480, 510), outer left edge through (110, -230)
    p, q = cross_diag(c, 110, 480, DESC, XH)       # p at top-right? no: cross_diag gives (xl,y_hi)->(xr,y_lo)
    # mirror so it runs from top-right down to bottom-left
    p, q = (500 - p[0] + 0, p[1]), (500 - q[0], q[1])
    # recompute: we want outer edges through (480, XH) and (110, DESC): mirror of (20, XH)-(390, DESC)
    p, q = cross_diag(c, 500 - 480, 500 - 110, DESC, XH)
    p, q = (500 - p[0], p[1]), (500 - q[0], q[1])
    right = extend_open_ends([p, q], DESC, XH)
    # left diagonal: outer edge through (20, XH), meets right skeleton at y = 40
    yj = 40
    xj = at_y(p, q, yj)
    alpha = math.atan((xj - 20) / (XH - yj))
    for _ in range(30):
        alpha = math.atan((xj - 20 - c.h / math.cos(alpha)) / (XH - yj))
    a0 = (20 + c.h / math.cos(alpha), XH)
    a1 = (xj, yj)
    left = [(at_y(a0, a1, XH + 60), XH + 60), line_pt(a0, a1, 1 + 0.3 * c.h / math.hypot(a1[0] - a0[0], a1[1] - a0[1]))]
    return [stroke(poly_cmds(right), c.s, band(DESC, XH)), stroke(poly_cmds(left), c.s, band(DESC, XH))]


def z_poly(c, xl, xr, y_hi):
    """z/Z as one filled polygon: top and bottom bars of thickness c.b spanning xl..xr and a
    diagonal of full stem width whose outer edges pass exactly through the top-right corner of
    the top bar and the bottom-left corner of the bottom bar (mitred, no overhang)."""
    s, b = c.s, c.b
    xl, xr = xl * c.wf, xr * c.wf
    t = math.tan(diag_angle(xr, y_hi, xl, 0, s))
    pts = [(xl, y_hi), (xr, y_hi), (xr - (y_hi - b) * t, b), (xr, b), (xr, 0),
           (xl, 0), (xl + (y_hi - b) * t, y_hi - b), (xl, y_hi - b)]
    return [fill_poly(c, pts)]


@glyph("z", 480)
def g_z(c):
    return z_poly(c, 20, 460, XH)


# ---------- uppercase ----------
@glyph("A", 660)
def g_A(c):
    pts = solve_zigzag(20, 640, 0, CAP, c.s, 2)
    # zigzag starts at the top; for A we flip vertically within the band
    pts = [(x, CAP - y) for x, y in pts]
    pts = extend_open_ends(pts, 0, CAP)
    y_bar = 220
    xl, xr = at_y(pts[0], pts[1], y_bar), at_y(pts[2], pts[1], y_bar)
    return [stroke(poly_cmds(pts), c.s, band(0, CAP)), hline(xl, xr, y_bar, c.b)]


def bowl_half(c, x_from, y_top, y_bot, right_outer):
    """B/D/P/R bowl: horizontal from x_from to the arc, half-ellipse down, horizontal back."""
    ry = (y_top - y_bot) / 2.0
    rx = min(ry * (UC_W / UC_H), right_outer - c.h - x_from - 10)
    xa = right_outer - c.h - rx
    cy = (y_top + y_bot) / 2.0
    return [("M", x_from, y_top), ("L", xa, y_top)] + arc_cmds(xa, cy, rx, ry, 90, -90, move=False) + [("L", x_from, y_bot)]


@glyph("B", 620)
def g_B(c):
    sx = SB_S + c.h
    mid = 360
    return [vline(sx, 0, CAP, c.s),
            stroke(bowl_half(c, SB_S, CAP - c.h, mid, 550), c.s),
            stroke(bowl_half(c, SB_S, mid, c.h, 570), c.s)]


@glyph("C", 700)
def g_C(c):
    cx = SB_R + UC_W / 2.0
    _, cut = ellipse_cut_right(cx, UC_CY, c.RX, c.RY, c.s, c_angle(c))
    return [stroke(ellipse_cmds(cx, UC_CY, c.RX, c.RY), c.s, [cut])]


@glyph("D", 660)
def g_D(c):
    sx = SB_S + c.h
    return [vline(sx, 0, CAP, c.s), stroke(bowl_half(c, SB_S, CAP - c.h, c.h, 610), c.s)]


@glyph("E", 560)
def g_E(c):
    sx = SB_S + c.h
    return [vline(sx, 0, CAP, c.s), hline(SB_S, 510, CAP - c.hb, c.b), hline(SB_S, 510, c.hb, c.b),
            hline(SB_S, 490, 360, c.b)]


@glyph("F", 540)
def g_F(c):
    sx = SB_S + c.h
    return [vline(sx, 0, CAP, c.s), hline(SB_S, 500, CAP - c.hb, c.b), hline(SB_S, 470, 360, c.b)]


@glyph("G", 740)
def g_G(c):
    # Same ring and upper terminal as C. The ring is removed right of the terminal face from the
    # ellipse centre line (y = 350) up, so the lower-right quadrant ends exactly at 3 o'clock,
    # buried under the bar. Bar centred on y = 350, thickness 0.94 stem, right end flush with the
    # ellipse's rightmost outer edge (the bar's end is the short vertical between 350 and the bar
    # top; the outer contour below is tangent-vertical there, so there is no step). Left end: a
    # full-width vertical cut 0.3 stem left of centre, well clear of the inner left of the bowl.
    # Below y = 350 the bar stops at the skeleton x (inside the ring band), because the outer
    # contour recedes from its rightmost point there; a rectangle would leave a lip.
    cx = SB_R + UC_W / 2.0
    cut_x, cutC = ellipse_cut_right(cx, UC_CY, c.RX, c.RY, c.s, c_angle(c))
    cut = [cut_x, UC_CY, BIG, cutC[3]]
    xL, xS = (cx - 0.3 * c.s) * c.wf, (cx + c.RX) * c.wf
    xR, hb = xS + c.h, c.hb
    bar = fill_poly(c, [(xL, UC_CY - hb), (xS, UC_CY - hb), (xS, UC_CY), (xR, UC_CY),
                        (xR, UC_CY + hb), (xL, UC_CY + hb)])
    return [stroke(ellipse_cmds(cx, UC_CY, c.RX, c.RY), c.s, [cut]), bar]


@glyph("H", 700)
def g_H(c):
    lx, rx_ = SB_S + c.h, 700 - SB_S - c.h
    return [vline(lx, 0, CAP, c.s), vline(rx_, 0, CAP, c.s), hline(SB_S, 700 - SB_S, 360, c.b)]


@glyph("I", 248)
def g_I(c):
    return [vline(124, 0, CAP, c.s)]


@glyph("J", 500)
def g_J(c):
    # Stem plus a quarter-ellipse hook that ends exactly at the ellipse's 6 o'clock point, where
    # the tangent is horizontal, so the butt cap is a full-width vertical face. The skeleton end
    # x is the left sidebearing, so that face IS the hook's left edge at x = 70. The curve
    # springs from the stem at y = 230 and overshoots the baseline by 12 like the other rounds.
    sx = 500 - SB_S - c.h
    cy = 230
    rxj, ryj = sx - SB_S, cy + OVER - c.h
    path = [("M", sx, CAP), ("L", sx, cy)] + arc_cmds(sx - rxj, cy, rxj, ryj, 0, -90, move=False)
    return [stroke(path, c.s)]


def k_arms(c, sx, right_outer, y_top, y_meet, y_bot=0):
    """Straight arm and leg leaving the stem at y_meet, outer edges reaching right_outer at y_top / y_bot."""
    h = c.h
    out = []
    for y_end in (y_top, y_bot):
        alpha = math.atan((right_outer - sx) / abs(y_end - y_meet))
        for _ in range(30):
            alpha = math.atan((right_outer - h / math.cos(alpha) - sx) / abs(y_end - y_meet))
        x_sk = right_outer - h / math.cos(alpha)
        p0, p1 = (sx, y_meet), (x_sk, y_end)
        out.append(stroke([("M",) + p0, ("L",) + line_pt(p0, p1, 1.12)], c.s, band(y_bot, y_top)))
    return out


@glyph("K", 620)
def g_K(c):
    sx = SB_S + c.h
    return [vline(sx, 0, CAP, c.s)] + k_arms(c, sx, 600, CAP, 360)


@glyph("L", 500)
def g_L(c):
    sx = SB_S + c.h
    return [vline(sx, 0, CAP, c.s), hline(SB_S, 460, c.hb, c.b)]


@glyph("M", 860)
def g_M(c):
    lx, rx_ = SB_S + c.h, 860 - SB_S - c.h
    cx = 430
    h = c.h
    W = 1.1 * c.s
    alpha = math.atan((cx - lx) / CAP)
    for _ in range(40):
        y_a = -W / (2 * math.tan(alpha)) + h / math.sin(alpha)
        alpha = math.atan((cx - lx) / (CAP - y_a))
    pts = [(lx, 0), (lx, CAP), (cx, y_a), (rx_, CAP), (rx_, 0)]
    return [stroke(poly_cmds(pts), c.s, band(0, CAP))]


@glyph("N", 700)
def g_N(c):
    lx, rx_ = SB_S + c.h, 700 - SB_S - c.h
    pts = [(lx, 0), (lx, CAP), (rx_, 0), (rx_, CAP)]
    return [stroke(poly_cmds(pts), c.s, band(0, CAP))]


@glyph("O", 740)
def g_O(c):
    return [stroke(ellipse_cmds(370, UC_CY, c.RX, c.RY), c.s)]


@glyph("P", 600)
def g_P(c):
    sx = SB_S + c.h
    return [vline(sx, 0, CAP, c.s), stroke(bowl_half(c, SB_S, CAP - c.h, 320, 560), c.s)]


@glyph("Q", 740)
def g_Q(c):
    cx = 370
    p = P(-58, c.RX, c.RY, cx, UC_CY)
    d = (math.cos(math.radians(-45)), math.sin(math.radians(-45)))
    p0 = (p[0] - 150 * d[0], p[1] - 150 * d[1])
    p1 = (p[0] + 200 * d[0], p[1] + 200 * d[1])
    return [stroke(ellipse_cmds(cx, UC_CY, c.RX, c.RY), c.s),
            stroke([("M",) + p0, ("L",) + p1], c.s, [[-BIG, -BIG, BIG, -60]])]


@glyph("R", 620)
def g_R(c):
    sx = SB_S + c.h
    y_bot = 330
    bowl = bowl_half(c, SB_S, CAP - c.h, y_bot, 560)
    xa = bowl[1][1]
    h = c.h
    right_outer = 600
    alpha = math.atan((right_outer - xa) / y_bot)
    for _ in range(30):
        alpha = math.atan((right_outer - h / math.cos(alpha) - xa) / y_bot)
    x_sk = right_outer - h / math.cos(alpha)
    leg = [(xa - 10, y_bot), (x_sk, 0)]
    leg = [leg[0], line_pt(leg[0], leg[1], 1.15)]
    return [vline(sx, 0, CAP, c.s), stroke(bowl, c.s), stroke(poly_cmds(leg), c.s, band(0, CAP))]


@glyph("S", 580)
def g_S(c):
    return s_like(c, 580, CAP + OVER, -OVER, 40)


@glyph("T", 580)
def g_T(c):
    return [vline(290, 0, CAP, c.s), hline(20, 560, CAP - c.hb, c.b)]


@glyph("U", 680)
def g_U(c):
    lx, rx_ = SB_S + c.h, 680 - SB_S - c.h
    rx = (rx_ - lx) / 2.0
    ry = rx * (UC_H / UC_W)
    cy = -OVER + c.h + ry
    path = [("M", lx, CAP), ("L", lx, cy)] + arc_cmds(lx + rx, cy, rx, ry, 180, 360, move=False) + [("L", rx_, CAP)]
    return [stroke(path, c.s)]


@glyph("V", 660)
def g_V(c):
    pts = solve_zigzag(20, 640, 0, CAP, c.s, 2)
    return [stroke(poly_cmds(extend_open_ends(pts, 0, CAP)), c.s, band(0, CAP))]


@glyph("W", 920)
def g_W(c):
    pts = solve_zigzag(20, 900, 0, CAP, c.s, 4)
    return [stroke(poly_cmds(extend_open_ends(pts, 0, CAP)), c.s, band(0, CAP))]


@glyph("X", 620)
def g_X(c):
    p, q = cross_diag(c, 20, 600, 0, CAP)
    a = extend_open_ends([p, q], 0, CAP)
    b = extend_open_ends([(620 - p[0], p[1]), (620 - q[0], q[1])], 0, CAP)
    return [stroke(poly_cmds(a), c.s, band(0, CAP)), stroke(poly_cmds(b), c.s, band(0, CAP))]


@glyph("Y", 620)
def g_Y(c):
    cx = 310
    y_m = 330
    h = c.h
    alpha = math.atan((cx - 20) / (CAP - y_m))
    for _ in range(30):
        alpha = math.atan((cx - 20 - h / math.cos(alpha)) / (CAP - y_m))
    x0 = 20 + h / math.cos(alpha)
    pts = extend_open_ends([(x0, CAP), (cx, y_m), (620 - x0, CAP)], 0, CAP)
    return [stroke(poly_cmds(pts), c.s, band(0, CAP)), vline(cx, 0, y_m + 0.3 * h, c.s)]


@glyph("Z", 600)
def g_Z(c):
    return z_poly(c, 20, 580, CAP)


# ---------- figures ----------
FIG_W = 560


@glyph("zero", FIG_W)
def g_zero(c):
    rx, ry = (480 - c.s) / 2.0, (CAP + 2 * OVER - c.s) / 2.0
    return [stroke(ellipse_cmds(280, UC_CY, rx, ry), c.s)]


@glyph("one", 340)
def g_one(c):
    # Plain stem plus a 45-degree flag of full stem width, as one filled polygon. The flag's
    # upper edge leaves the stem's top-left corner (so it is flush with the top at y = 700);
    # its skeleton starts on the stem centre line and runs 1.7 stems to a butt (perpendicular)
    # cut. The flag grows with the stem, so the advance is set from the drawn width: left
    # sidebearing 48 (Medium 340 unchanged), right sidebearing 70.
    s, h, wf = c.s, c.h, c.wf
    k = 1 / math.sqrt(2)
    L = s * lerp_w(c, 1.7, 1.7, 1.25)      # flag capped at Bold so the advance stays <= 400
    sx = (340 - SB_S - h) * wf
    xL, xR = sx - h, sx + h
    y0 = CAP - h * (math.sqrt(2) - 1)      # skeleton height where it crosses the stem centre
    ex, ey = sx - L * k, y0 - L * k        # skeleton end
    tip = ex - h * k                       # leftmost point (upper corner of the butt cut)
    dx = 48 * wf - tip
    pts = [(xR, 0), (xR, CAP), (xL, CAP), (ex - h * k, ey + h * k), (ex + h * k, ey - h * k),
           (xL, CAP - s * math.sqrt(2)), (xL, 0)]
    pts = [(x + dx, y) for x, y in pts]
    adv = (xR + dx + SB_S * wf) / wf
    return (adv, [fill_poly(c, pts)])


@glyph("two", FIG_W)
def g_two(c):
    # Stroked arc from the upper-left terminal (anchored vertical face at 140 deg) clockwise to
    # the exit angle, then diagonal + base as ONE filled polygon in final x-space (like 7): the
    # diagonal leaves the arc exactly where the arc's tangent equals its direction, its
    # upper-left edge passes through the base's top-left corner (SB_R, b) and its lower-right
    # edge meets the base's top edge; the base is b thick with a full-width vertical right end.
    s, h, b, wf = c.s, c.h, c.b, c.wf
    rx = (480 - s) / 2.0
    ry = rx * RATIO * 0.98
    cx = 280
    cy = CAP - h - ry
    rxf, cxf = rx * wf, cx * wf
    xl, xr = SB_R * wf, 520 * wf

    def geom(a):
        t = math.radians(a)
        S = (cxf + rxf * math.cos(t), cy + ry * math.sin(t))
        nx, ny = ry * math.cos(t), rxf * math.sin(t)
        n = math.hypot(nx, ny)
        nx, ny = nx / n, ny / n                                  # outward normal
        tx, ty = rxf * math.sin(t), -ry * math.cos(t)
        m = math.hypot(tx, ty)
        tx, ty = tx / m, ty / m                                  # clockwise (down-left) tangent
        return (S[0] - h * nx, S[1] - h * ny), (S[0] + h * nx, S[1] + h * ny), (tx, ty)

    def err(a):
        I, _, (tx, ty) = geom(a)
        return tx * (b - I[1]) - ty * (xl - I[0])                # 0 when (xl, b) is on the inner edge line

    lo, hi = -85.0, -15.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if err(lo) * err(mid) <= 0:
            hi = mid
        else:
            lo = mid
    a_e = (lo + hi) / 2
    I, O, (tx, ty) = geom(a_e)
    xm = O[0] + (b - O[1]) * tx / ty                             # lower-right edge meets the base top
    I0, O0 = (I[0] - tx, I[1] - ty), (O[0] - tx, O[1] - ty)      # 1 unit back into the arc: no seam
    body = [I0, (xl, b), (xl, 0), (xr, 0), (xr, b), (xm, b), O0]
    th = 140.0
    cut, _, _ = face_cut(c, cx, cy, rx, ry, th, "ul")
    return [stroke(arc_cmds(cx, cy, rx, ry, th, a_e), s, [cut]), fill_poly(c, body)]


@glyph("three", FIG_W)
def g_three(c):
    # two stacked bowls meeting at the waist with horizontal tangents; vertical terminal cuts.
    # The advance follows the drawn width so the figure sits centred between 50-unit sidebearings.
    s, h = c.s, c.h
    waist = 362
    ryl = (waist - h) / 2.0
    ryu = (CAP - h - waist) / 2.0
    rxl = ryl * 1.3
    rxu = ryu * 1.3
    xw = 520 - h - rxl
    cu = (xw, waist + ryu)
    cl = (xw, waist - ryl)
    # Both arcs end exactly at their terminal angles (40 deg below / above the horizontal, where
    # the stroke runs about 47 deg from vertical) and get anchored vertical faces; the bowls meet
    # at the waist with a common horizontal tangent.
    th = 40.0
    path = (arc_cmds(cu[0], cu[1], rxu, ryu, 180 - th, -90)
            + arc_cmds(cl[0], cl[1], rxl, ryl, 90, -(180 - th), move=False))
    cut_u, ixu, _ = face_cut(c, cu[0], cu[1], rxu, ryu, 180 - th, "ul")
    cut_l, ixl, _ = face_cut(c, cl[0], cl[1], rxl, ryl, 180 + th, "ll")
    left_face = min(ixu, ixl)
    dx = 50 - left_face
    els = translate([stroke(path, s, [cut_u, cut_l])], dx)
    return (round(520 + dx + 50), els)


@glyph("four", FIG_W)
def g_four(c):
    s, h, b, hb = c.s, c.h, c.b, c.hb
    sx = 390
    bar_y = 190
    # diagonal + bar as one path (width b) with a mitred corner trimmed by the left cut
    top_x = sx - h - 60 - hb          # diagonal's right edge sits 60 left of the stem at the top
    p_top = (top_x, CAP + 40)
    p_corner = (SB_R + 40, bar_y)
    # choose the corner so the diagonal's outer edge hits (30, bar_y - hb)
    path = [("M",) + p_top, ("L",) + p_corner, ("L", 530, bar_y)]
    return [vline(sx, 0, CAP, s), stroke(path, b, [[-BIG, CAP, BIG, BIG], [-BIG, -BIG, 30, BIG]])]


@glyph("five", FIG_W)
def g_five(c):
    # Top bar (b thick, top edge at cap height, right end a vertical cut) + left vertical (s wide,
    # left edge flush with the bar's left end) + horizontal neck (s thick, centre y = neck) as ONE
    # filled polygon in final x-space, so every corner is an exact mitre. The bowl arc springs
    # from the neck's end at its 12 o'clock point (tangent horizontal, co-linear with the neck's
    # centre line) and ends at 220 deg with an anchored vertical face.
    s, h, b, wf = c.s, c.h, c.b, c.wf
    neck = 430
    ry = (neck - h) / 2.0
    rx = (480 - s) / 2.0 - 10
    cx = 520 - h - rx
    cy = (neck + h) / 2.0
    xl = (SB_R + 10) * wf
    xr = 500 * wf
    xk = cx * wf + 3                              # neck runs 3 units into the arc band: no seam
    top = [(xl, CAP), (xr, CAP), (xr, CAP - b), (xl + s, CAP - b), (xl + s, neck + h),
           (xk, neck + h), (xk, neck - h), (xl, neck - h)]
    cut, _, _ = face_cut(c, cx, cy, rx, ry, 220, "ll")
    return [fill_poly(c, top), stroke(arc_cmds(cx, cy, rx, ry, 90, -140), s, [cut])]


@glyph("six", FIG_W)
def g_six(c):
    s, h = c.s, c.h
    rx = (480 - s) / 2.0
    ry = (462 - s) / 2.0
    cx, cy = 280, -OVER + h + ry
    # top arc: quarter of a large ellipse tangent to the bowl's left side. It ends exactly at
    # its 12 o'clock point, where the tangent is horizontal, so the butt cap is a vertical flat
    # cut of full stroke width and nothing continues past it. No clipping.
    ryT = CAP - h - cy
    rxT = 320
    cT = (cx - rx + rxT, cy)
    top = arc_cmds(cT[0], cT[1], rxT, ryT, 180, 90)
    return [stroke(ellipse_cmds(cx, cy, rx, ry), s), stroke(top, s)]


@glyph("seven", 520)
def g_seven(c):
    # Top bar (thickness c.b) and full-stem diagonal as one filled polygon: the diagonal's
    # upper-right edge passes exactly through the bar's top-right corner, its lower-left edge
    # through (150, 0), and it is cut flat on the baseline. Crossbar (PRD 9.4): thickness c.b
    # centred on y = 350, reaching one stem beyond each edge of the diagonal at that height.
    s, b, wf = c.s, c.b, c.wf
    xl, xr, xb = 20 * wf, 500 * wf, 150 * wf
    t = math.tan(diag_angle(xr, CAP, xb, 0, s))
    body = [(xl, CAP), (xr, CAP), (xr - CAP * t, 0), (xb, 0), (xb + (CAP - b) * t, CAP - b), (xl, CAP - b)]
    yc = 350
    x_left, x_right = xb + yc * t, xr - (CAP - yc) * t
    bar = [(x_left - s, yc - b / 2.0), (x_right + s, yc - b / 2.0),
           (x_right + s, yc + b / 2.0), (x_left - s, yc + b / 2.0)]
    return [fill_poly(c, body), fill_poly(c, bar)]


@glyph("eight", FIG_W)
def g_eight(c):
    s, h = c.s, c.h
    Hsk = CAP + 2 * OVER - s
    ryu, ryl = Hsk * 0.235, Hsk * 0.265
    rxl = (480 - s) / 2.0
    rxu = rxl - 18
    cu = (280, CAP + OVER - h - ryu)
    cl = (280, -OVER + h + ryl)
    return [stroke(ellipse_cmds(cu[0], cu[1], rxu, ryu), s), stroke(ellipse_cmds(cl[0], cl[1], rxl, ryl), s)]


def translate(els, dx):
    out = []
    for e in els:
        if "c" in e:
            out.append(dot(e["c"][0] + dx, e["c"][1], e["c"][2]))
            continue
        cmds = []
        for cmd in e["cmds"]:
            if cmd[0] in ("M", "L"):
                cmds.append((cmd[0], cmd[1] + dx, cmd[2]))
            elif cmd[0] == "A":
                cmds.append(("A", cmd[1], cmd[2], cmd[3], cmd[4], cmd[5] + dx, cmd[6]))
            else:
                cmds.append(cmd)
        ne = {"cmds": cmds, "w": e["w"]} if "w" in e else {"cmds": cmds, "f": True}
        if "cut" in e:
            ne["cut"] = [[max(-BIG, r[0] + dx), r[1], min(BIG, r[2] + dx), r[3]] for r in e["cut"]]
        out.append(ne)
    return out


def rotate180(els, cx, cy):
    out = []
    for e in els:
        if "c" in e:
            x, y, r = e["c"]
            out.append(dot(2 * cx - x, 2 * cy - y, r))
            continue
        cmds = []
        for cmd in e["cmds"]:
            if cmd[0] in ("M", "L"):
                cmds.append((cmd[0], 2 * cx - cmd[1], 2 * cy - cmd[2]))
            elif cmd[0] == "A":
                cmds.append(("A", cmd[1], cmd[2], cmd[3], cmd[4], 2 * cx - cmd[5], 2 * cy - cmd[6]))
            else:
                cmds.append(cmd)
        ne = {"cmds": cmds, "w": e["w"]} if "w" in e else {"cmds": cmds, "f": True}
        if "cut" in e:
            ne["cut"] = [[2 * cx - r[2], 2 * cy - r[3], 2 * cx - r[0], 2 * cy - r[1]] for r in e["cut"]]
        out.append(ne)
    return out


@glyph("nine", FIG_W)
def g_nine(c):
    return rotate180(g_six(c), 280, CAP / 2.0)


# ---------- punctuation ----------
@glyph("period", 260)
def g_period(c):
    return [dot(130, c.rd, c.rd)]


@glyph("comma", 260)
def g_comma(c):
    # Head: the period's circle (diameter 1.09 stem, sitting on the baseline). Tail: filled
    # quadrilateral whose right edge is tangent to the circle at its lower right and runs
    # down-left at 20 deg from vertical; the top edge is the circle's diameter perpendicular to
    # that direction (so the left edge springs from the circle's lower left); the end is a flat
    # cut perpendicular to the tail, 55 percent of the diameter wide, with its lowest corner at
    # y = -1.2 diameter. Circle and polygon are both filled (union), no clipping.
    r, d, wf = c.rd, c.d, c.wf
    ang = math.radians(20)
    u = (-math.sin(ang), -math.cos(ang))                       # tail direction (down-left)
    n = (math.cos(ang), -math.sin(ang))                        # unit normal, pointing right
    C = (130 * wf, r)
    Tr = (C[0] + r * n[0], C[1] + r * n[1])                    # tangent point, lower right
    Tl = (C[0] - r * n[0], C[1] - r * n[1])                    # opposite point, lower left
    L = (Tr[1] + 1.2 * d) / -u[1]                              # length so the bottom corner is at -1.2 d
    Er = (Tr[0] + L * u[0], Tr[1] + L * u[1])
    we = 0.55 * d
    El = (Er[0] - we * n[0], Er[1] - we * n[1])
    return [dot(130, r, r), fill_poly(c, [Tr, Er, El, Tl])]


@glyph("colon", 260)
def g_colon(c):
    return [dot(130, c.rd, c.rd), dot(130, XH - c.rd, c.rd)]


@glyph("hyphen", 320)
def g_hyphen(c):
    return [hline(40, 280, 265, c.b)]


@glyph("exclam", 260)
def g_exclam(c):
    return [dot(130, c.rd, c.rd), vline(130, c.d + 120, CAP, c.s)]


@glyph("question", 460)
def g_question(c):
    # Head arc from the upper-left terminal (anchored vertical face at 140 deg) clockwise to
    # a_e, then a reverse arc of the same aspect ratio (radii lam * rx, lam * ry, tangent at the
    # join) that turns the stroke back to vertical exactly on the stem line x = sx, then the
    # straight vertical down to a flat cut above the dot. Every junction is tangent-continuous.
    s, h = c.s, c.h
    rx = (380 - s) / 2.0
    ry = rx * RATIO * 0.85
    cx = 250
    cy = CAP - h - ry
    sx = cx - 0.45 * rx
    a_e = -72.0
    t = math.radians(a_e)
    lam = (sx - cx - rx * math.cos(t)) / (rx * (math.cos(t) - 1))
    c2 = (cx + (1 + lam) * rx * math.cos(t), cy + (1 + lam) * ry * math.sin(t))
    y_end = c.d + 110
    th = 140.0
    path = (arc_cmds(cx, cy, rx, ry, th, a_e)
            + arc_cmds(c2[0], c2[1], lam * rx, lam * ry, a_e + 180, 180, move=False)
            + [("L", sx, y_end)])
    cut, _, _ = face_cut(c, cx, cy, rx, ry, th, "ul")
    return [stroke(path, s, [cut]), dot(sx, c.rd, c.rd)]


# ---------------------------------------------------------------- serialisation
def fmt(v):
    r = round(v, 1)
    return str(int(r)) if r == int(r) else str(r)


def cmds_to_d(cmds, wf):
    parts = []
    for cmd in cmds:
        if cmd[0] in ("M", "L"):
            parts.append("%s%s %s" % (cmd[0], fmt(cmd[1] * wf), fmt(cmd[2])))
        elif cmd[0] == "A":
            parts.append("A%s %s 0 %d %d %s %s" % (fmt(cmd[1] * wf), fmt(cmd[2]), cmd[3], cmd[4], fmt(cmd[5] * wf), fmt(cmd[6])))
        else:
            parts.append("Z")
    return " ".join(parts)


def build(stem):
    c = Ctx(stem)
    wf = width_factor(stem)
    out = {"space": {"adv": round(SPACE * wf), "el": []}}
    for name, (adv, fn) in GLYPHS.items():
        els = []
        res = fn(c)
        if isinstance(res, tuple):
            adv, res = res
        for e in res:
            if "c" in e:
                x, y, r = e["c"]
                els.append({"c": [round(x * wf, 1), round(y, 1), round(r, 1)]})
            elif e.get("f"):
                els.append({"d": cmds_to_d(e["cmds"], wf), "f": 1})
            else:
                o = {"d": cmds_to_d(e["cmds"], wf), "w": e["w"]}
                if "cut" in e:
                    o["cut"] = [[round(max(-BIG, min(BIG, r[0] * wf)), 1), round(r[1], 1),
                                 round(max(-BIG, min(BIG, r[2] * wf)), 1), round(r[3], 1)] for r in e["cut"]]
                els.append(o)
        out[name] = {"adv": round(adv * wf), "el": els}
    return out


ORDER = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
         "u", "v", "w", "x", "y", "z", "a.ss01",
         "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
         "U", "V", "W", "X", "Y", "Z",
         "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "period", "comma", "colon", "hyphen", "exclam", "question"]

CHAR_MAP = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
            "7": "seven", "8": "eight", "9": "nine", ".": "period", ",": "comma", ":": "colon",
            "-": "hyphen", "!": "exclam", "?": "question", " ": "space"}


def main():
    ap = argparse.ArgumentParser(description="write specimen/glyphs.json for the project")
    ap.add_argument("--root", default=os.getcwd(), help="project root (default: cwd)")
    root = ap.parse_args().root
    proj = load_project(root)
    configure(proj["weights"], proj["default"])
    out_path = os.path.join(proj["root"], "specimen", "glyphs.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    data = {"family": proj["family"], "default": proj["default"],
            "metrics": {"upm": UPM, "cap": CAP, "xh": XH, "asc": ASC, "desc": DESC, "th": TH, "over": OVER,
                        "space": SPACE},
            "order": ORDER, "charmap": CHAR_MAP, "weights": {}}
    for wname, stem in WEIGHTS:
        data["weights"][wname] = {"stem": stem, "css": CSS_WEIGHTS[wname], "bar": round(0.94 * stem, 1),
                                  "dot": round(1.09 * stem, 1), "glyphs": build(stem)}
    missing = [n for n in ORDER if n not in GLYPHS]
    if missing:
        sys.exit("missing glyphs: %s" % missing)
    with open(out_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("wrote %s (%d glyphs x %d weights, %d bytes)" % (out_path, len(GLYPHS), len(WEIGHTS), os.path.getsize(out_path)))


if __name__ == "__main__":
    main()
