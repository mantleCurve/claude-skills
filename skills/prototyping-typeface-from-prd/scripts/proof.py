#!/usr/bin/env python3
"""Proof sheet: selected glyphs at every weight, drawn with the same SVG logic as the specimen. Stdlib only.

    python3 proof.py --root <project> <out.html> name1 name2 ... [--px 360] [--zoom x0,y0,x1,y1 ...] [--png out.png]

One row per weight (lightest first), one cell per glyph name (glyph names as in glyphs.json:
letters as themselves, figures as zero..nine, punctuation as period/comma/colon/hyphen/exclam/question,
alternates as a.ss01). Red lines mark baseline, x-height and cap height.
--zoom crops every glyph to the box (font units, y up) at high magnification; repeat for several boxes.
--png also renders the sheet with headless Chrome (via screenshot.py) so it can be inspected with
the Read tool; the sheet is 2000 px wide, the height follows the number of rows.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_project, add_root_arg  # noqa: E402

clip_id = [0]


def body(g):
    out = ""
    for e in g["el"]:
        if "c" in e:
            out += '<circle cx="%s" cy="%s" r="%s" fill="currentColor"/>' % tuple(e["c"])
            continue
        if e.get("f"):
            out += '<path d="%s" fill="currentColor"/>' % e["d"]
            continue
        clip = ""
        if e.get("cut"):
            clip_id[0] += 1
            cid = "cp%d" % clip_id[0]
            d = "M-5000 -5000H5000V5000H-5000Z"
            for r in e["cut"]:
                d += "M%s %sH%sV%sH%sZ" % (r[0], r[1], r[2], r[3], r[0])
            out += '<clipPath id="%s"><path clip-rule="evenodd" d="%s"/></clipPath>' % (cid, d)
            clip = ' clip-path="url(#%s)"' % cid
        out += ('<path d="%s" fill="none" stroke="currentColor" stroke-width="%s" stroke-linecap="butt" '
                'stroke-linejoin="miter" stroke-miterlimit="10"%s/>' % (e["d"], e["w"], clip))
    return out


def svg(g, px, metrics, box=None, guides=True):
    if box:
        x0, y0, x1, y1 = box
    else:
        x0, y0, x1, y1 = -40, metrics.get("desc", -230) - 30, g["adv"] + 40, metrics.get("asc", 750) + 30
    w, h = x1 - x0, y1 - y0
    scale = px / h
    lines = ""
    if guides:
        for y in (0, metrics.get("xh", 510), metrics.get("cap", 700)):
            lines += '<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="#e33" stroke-width="%s"/>' % (x0, x1, -y, -y, 1 / scale)
    return ('<svg width="%d" height="%d" viewBox="%s %s %s %s" xmlns="http://www.w3.org/2000/svg">%s'
            '<g transform="scale(1 -1)">%s</g></svg>' % (round(w * scale), round(px), x0, -y1, w, h, lines, body(g)))


def main():
    ap = add_root_arg(argparse.ArgumentParser(description=__doc__.strip().splitlines()[0]))
    ap.add_argument("out", help="output .html")
    ap.add_argument("names", nargs="+", help="glyph names")
    ap.add_argument("--px", type=int, default=360, help="cell height in px (default 360)")
    ap.add_argument("--zoom", action="append", default=[], help="x0,y0,x1,y1 crop box in font units")
    ap.add_argument("--png", help="also screenshot the sheet to this PNG with headless Chrome")
    a = ap.parse_args()
    proj = load_project(a.root)
    if not os.path.exists(proj["glyphs_json"]):
        sys.exit("no %s: run glyphs.py first" % proj["glyphs_json"])
    data = json.load(open(proj["glyphs_json"], encoding="utf-8"))
    metrics = data.get("metrics", {})
    zooms = [[float(v) for v in z.split(",")] for z in a.zoom]
    weights = sorted(data["weights"], key=lambda w: data["weights"][w]["stem"])
    html = ['<!doctype html><meta charset="utf-8"><title>proof</title><style>body{margin:0;background:#fff;color:#111;font:14px system-ui}'
            '.row{display:flex;gap:24px;padding:12px;border-bottom:1px solid #ccc;align-items:flex-start}'
            '.cell{text-align:center}.cell svg{display:block;background:#fafafa}</style>']
    missing = []
    row_w = 0
    for wname in weights:
        gl = data["weights"][wname]["glyphs"]
        html.append('<div class="row"><div style="width:70px;padding-top:8px"><b>%s</b></div>' % wname)
        w = 70 + 24
        for n in a.names:
            g = gl.get(n)
            if not g:
                missing.append(n)
                html.append('<div class="cell"><div style="padding:8px;color:#b33">no glyph %s</div></div>' % n)
                w += 140
                continue
            if zooms:
                for z in zooms:
                    cell = svg(g, a.px, metrics, z)
                    html.append('<div class="cell">%s<div>%s %s</div></div>' % (cell, n, z))
                    w += int(cell.split('width="')[1].split('"')[0]) + 24
            else:
                cell = svg(g, a.px, metrics)
                html.append('<div class="cell">%s<div>%s adv %s</div></div>' % (cell, n, g["adv"]))
                w += int(cell.split('width="')[1].split('"')[0]) + 24
        row_w = max(row_w, w)
        html.append("</div>")
    open(a.out, "w", encoding="utf-8").write("".join(html))
    print("wrote", a.out)
    if missing:
        print("missing glyphs:", " ".join(sorted(set(missing))), file=sys.stderr)
    if a.png:
        from screenshot import shoot
        # the window follows the content: nothing is clipped, however many names are given
        height = len(weights) * (a.px + 60) + 20
        print("wrote", shoot(a.out, a.png, width=min(6000, max(600, row_w + 40)), height=height))


if __name__ == "__main__":
    main()
