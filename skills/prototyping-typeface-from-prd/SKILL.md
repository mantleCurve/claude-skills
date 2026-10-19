---
name: prototyping-typeface-from-prd
description: Use when someone wants a new typeface or font designed from a brief, a font PRD written, sample glyphs drawn, a type specimen page, a WOFF/OTF prototype or an editable type tester, especially a geometric sans with letterform rules such as a straight t, a straight j, a single-storey g, and named weights (Light, Medium, Bold). Also use to review or extend an existing skeleton-based glyph generator.
---

# Prototyping a typeface from a PRD

## Overview

Write the PRD first, with numeric metrics, then draw. Glyphs are stroke skeletons on a 1000 UPM
grid, stroked per weight into `specimen/glyphs.json`; specimen, proof sheets and fonts all
render that file. Review every terminal and junction at every weight on proof sheets first.
Scripts read family and weights from `font.json` or the PRD.

## When to use

A brief for a new font family or UI face; a font PRD; sample glyphs; a specimen or type tester;
an OTF/WOFF prototype. Not for editing existing fonts, hinting, kerning or full character sets.

## Workflow

Project: `docs/PRD.md`, `font.json`, `tools/glyphs.py`, `specimen/`, `fonts/`, `proofs/`.
`SKILL=~/.claude/skills/prototyping-typeface-from-prd`.

1. **PRD.** Write `docs/PRD.md` from [references/prd-template.md](references/prd-template.md):
   22 sections, numeric metrics (8), each mandated glyph as `**glyph (subtitle)**` plus bullets
   with coordinates (9.1), weights table (12), Appendix A strings. Resolve conflicting metrics
   there. Copy `font.example.json` to `font.json`.
2. **Metrics.** Copy `glyphs.py` to `tools/glyphs.py`; set its metrics block to PRD section 8.
   Read [references/glyph-construction.md](references/glyph-construction.md) first.
3. **Glyphs.** Rewrite the `@glyph` recipes to the PRD, mandated glyphs first; run `glyphs.py`.
4. **Review loop.** Render the eight proof sheets in
   [references/review-checklist.md](references/review-checklist.md), Read every PNG, fix,
   regenerate, re-render; Bold fails first.
5. **Specimen.** `build_specimen.py` creates `specimen/index.html` from the template once,
   then refreshes only its marked regions.
6. **Fonts and tester.** `python3 -m venv .venv && .venv/bin/pip install fonttools skia-pathops brotli`,
   then `build_font.py --screenshot`.
7. **Publish.** Screenshot specimen and tester at 1280 and 400 px, Read them, publish both as
   artifacts (checklist section 5).

## Quick reference

All commands take `--root <project>` (default: cwd); all but `build_font.py` are stdlib-only.

| Script | Output | Command |
|---|---|---|
| `glyphs.py` | `specimen/glyphs.json` | `python3 tools/glyphs.py` |
| `proof.py` | proof sheet per weight; `--zoom`, `--png` | `python3 $SKILL/scripts/proof.py proofs/lc1.html a b c --png proofs/lc1.png` |
| `build_specimen.py` | `specimen/index.html` | `python3 $SKILL/scripts/build_specimen.py` |
| `build_font.py` | OTF/WOFF/WOFF2 per weight, `specimen/tester.html` | `.venv/bin/python $SKILL/scripts/build_font.py --screenshot` |
| `screenshot.py` | headless Chrome PNG; `--wrap` for doctype-less pages | `python3 $SKILL/scripts/screenshot.py specimen/index.html out.png --wrap --width 400` |

## Common mistakes

| Mistake | Fix |
|---|---|
| Clip-rectangle terminal trim leaves a sliver or wedge | End the skeleton where the tangent gives the cut (12/6 o'clock for a vertical face, 3/9 horizontal) or use `face_cut` |
| Diagonal meeting a bar as two strokes: stepped corner (z Z 7 1 2 5 E) | One filled polygon, mitres from `diag_angle` |
| Monoline double-storey a and s congest at Bold | Counters ≥ 30, clearance ≥ 40, steeper terminals, ≤ 6 % width growth, documented |
| g tail counter fills at Bold | Tail inner radius ≥ 60 at the boldest master |
| Arch overshoots or seams at its stem | Skeleton tangent to the stem centre; stem overlaps 1 to 3 units into the arch |
| "g as in the reference image" | PRD gives bowl box, stem x, tail radius, terminal x/y, clearances |
| Judging a fix from path data | Re-render proof sheets after every fix; Read the PNGs |
| Conflicting PRD metrics (fixed descender vs minimum clearance) | Reconcile in the PRD, never silently |
