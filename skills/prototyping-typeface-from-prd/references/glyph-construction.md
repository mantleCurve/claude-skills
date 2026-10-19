# Glyph construction system

How `scripts/glyphs.py` turns PRD numbers into glyphs. The recipes below are the ones that shipped
in the reference family (a geometric sans: straight t and j, single-storey open-tail g); a new
face keeps the system and rewrites the recipes against its own PRD section 8 and 9.

## 1. Coordinate system

- 1000 units per em, y up, baseline at y = 0, glyph origin at x = 0; the advance width is the
  right edge of the glyph box.
- SVG is y down, so every renderer draws the glyph inside `<g transform="scale(1 -1)">` and uses a
  viewBox whose y is the negated top (`viewBox="x0 -top w h"`). Guides are drawn at `-y`.
- Fonts (build_font.py) take the same y-up data unchanged.

## 2. Metric lines and overshoot (module constants, mirror PRD section 8)

| Constant | Reference value | Meaning |
|---|---|---|
| `CAP` | 700 | cap height |
| `XH` | 510 | x-height |
| `ASC` | 750 | ascender of b d f h k l |
| `DESC` | -230 | descender of g j p q y |
| `TH` | 650 | t height |
| `OVER` | 12 | round overshoot above and below the lines |
| `LC_W, LC_H, LC_CY` | 480, 534, 255 | lowercase bowl outer box and its centre height |
| `UC_W, UC_H, UC_CY` | 660, 724, 350 | capital ellipse outer box and centre |
| `SB_S, SB_R` | 70, 40 | default sidebearing of a straight stem / a round |
| `SPACE` | 240 | word space advance |
| `RATIO` | LC_H / LC_W = 1.1125 | the ellipse family's height-to-width ratio |

Flat-topped and flat-bottomed strokes end exactly on the metric line; every round form's outer
contour overshoots it by `OVER` (bowl outer height 534 = 510 + 2 × 12).

## 3. Skeleton-centred strokes and the half-stem rule

A glyph is a list of elements:

- **stroke**: an open or closed skeleton path (M, L, A, Z), stroked with width `w`, butt caps,
  mitre joins, mitre limit 10; optional `cut` rectangles removed afterwards.
- **dot**: a filled circle `[cx, cy, r]`.
- **filled polygon**: a closed path filled directly (used where two straight strokes must meet in
  an exact mitre).

Because strokes are centred on the skeleton, every design coordinate is an **outer edge** moved
in by half a stem `h = s / 2`:

- stem centre x = sidebearing + h (left stem) or advance − sidebearing − h (right stem);
- a bowl with outer box W × H has skeleton radii `rx = (W − s) / 2`, `ry = (H − s) / 2`;
- an arch whose outer top must sit at XH + OVER has its skeleton centre at `XH + OVER − h − ry`;
- a horizontal bar whose top edge is on the x-height has skeleton y = `XH − hb` (`hb = b / 2`).

Per-weight derived values live in `Ctx(stem)`: `s`, `h`, `wf` (width factor), `b = 0.94 s`
(horizontal stroke), `hb`, `d = 1.09 s` (dot diameter), `rd`, `rx ry` (lowercase bowl skeleton
radii), `RX RY` (capital), `rxn ryn cyn` (the n arch, outer width 420).

**Width factor.** Every x coordinate is designed in default-weight width space and multiplied by
`wf` at serialisation (0.97 at the lightest stem, 1.00 at the default, 1.03 at the boldest,
piecewise linear on the stem). Stroke widths are not scaled. Filled polygons are computed in
final space and stored divided by `wf` (`fill_poly`) so their mitres land exactly. `lerp_w(c,
light, medium, bold)` gives any per-weight value keyed on the same three stems.

## 4. Ellipse families

- **Lowercase rounds** (o c e b d p q, the g bowl, the ss01 a): one ellipse, outer 480 × 534,
  centre y 255. Ratio 0.90 width-to-height ("slightly condensed").
- **Capital rounds** (O C G Q, the B D P R bowls by scaling): outer 660 × 724, centre y 350.
- **Arches** (n m h u, r, f): half-ellipses between two stem centre lines with
  `ry = rx × RATIO`, so every arch belongs to the same family whatever its span.
- **Figures**: 0 on a 480 × 724 ellipse (cap height plus overshoots); 6 9 bowls 480 × 462; 8 as
  two stacked ellipses (upper 18 narrower); 3 as two bowls with rx = 1.3 ry.

Angles are degrees counter-clockwise from 3 o'clock (0 = right, 90 = top, 180 = left, −90 =
bottom). `arc_cmds(cx, cy, rx, ry, a0, a1)` emits SVG arcs from a0 to a1, splitting spans over
179° so sweep flags stay unambiguous.

## 5. Terminal rules

All terminals are **flat cuts, horizontal or vertical, at full stroke width**. Three ways to get
one; pick the first that applies.

1. **End the skeleton where the tangent gives the cut.** A butt cap is perpendicular to the
   skeleton. End an arc at 12 or 6 o'clock (tangent horizontal) for a vertical face: J's hook
   (ends at −90°), the top arc of 6 (ends at 90°), r and f (end at 90°). End it at 3 or 9 o'clock
   (tangent vertical) for a horizontal face: the a hood (0° → 180°), the u arch. Nothing to clip.
2. **Anchored face** (`face_cut`, the s_like technique) when the arc must stop at an oblique
   angle θ: end the skeleton exactly at θ, find the end's **inner-contour corner**
   (`inner_corner`: the skeleton point moved h along the inward normal, computed in final x
   space), and remove the quadrant beyond that corner (`ur`, `lr`, `ul`, `ll`). The face is the
   vertical through the corner; the butt cap lies entirely inside the removed region, so the
   face runs cleanly from the inner corner to the outer contour. Used by s S e 2 3 5 ?.
3. **Band or full cut** (`band`, `ellipse_cut_right/left`) when a stroke should simply stop at a
   metric line: extend the skeleton 60 units past the line (`extend_open_ends`) and keep only
   the band between the lines (v w x y A V W X Y M N K legs, R leg, k arms). c and C use one
   vertical cut through the whole ring at the inner-contour x of `c_angle` (30°, rising to 45°
   at the boldest stem so the acute corner never spikes).

What goes wrong: a clip rectangle laid across a stroke that continues past it leaves a sliver or a
wedge of the butt cap on the far side (the Bold c and s did this). Rule 1 or 2 removes the cause;
never paper over it with a second rectangle.

## 6. Diagonal + bar glyphs are one filled polygon

Where a diagonal of full stem width meets a horizontal bar of width `b`, two overlapping strokes
leave a stepped or notched corner at every weight except the one it was tuned at. Compute the
corners instead: `diag_angle(x_hi, y_hi, x_lo, y_lo, s)` gives the angle of a band of width `s`
whose right edge passes through one point and left edge through the other; from it the polygon
vertices follow and the mitre is exact. Glyphs built this way: **z Z** (`z_poly`), **7**, **1**
(stem plus flag), **2** (arc stroke plus a diagonal-and-base polygon tangent to the arc), **5**
(top bar, left vertical and neck as one polygon), **E**-style bars where they meet a stem (G's bar
with its stepped end under the ring), the comma tail.

## 7. Per-glyph recipes (reference family)

Advance widths in default-weight space; `s` stem, `h = s/2`, `b` bar, `rx ry` lowercase radii.

**Lowercase**

| Glyph | Adv | Construction |
|---|---|---|
| o | 560 | ellipse centre (280, 255), radii rx ry |
| b d p q | 590 | `bowl_with_stem`: bowl outer 480 tangent to a stem at x = SB_S + h (b p, stem left) or at the bowl's right skeleton edge (d q); stems 0→750 (b d) or −230→510 (p q) |
| a.ss01 | 560 | bowl as o, right stem 0→510 at cx + rx |
| a | 540 (555 at Bold) | double-storey: right stem from 0 up 3 units into the hood band; hood = half-ellipse 0°→180° springing at `hy`, flush with the stem's right edge, ending at 9 o'clock (horizontal flat cut) with terminal centre x = SB_R + 20 + h; bowl ellipse on the baseline, outer left edge x = 50, outer height 330 (346 Bold), skeleton tangent to the stem centre line. Vertical budget per weight: bowl height + gap (40, 30 at Bold) + hood band; when the hood's inner radius would drop below 1 the hood becomes a filled solid half-ellipse |
| c | 520 | o ellipse at cx = SB_R + 240 with one vertical cut right of the inner-contour x at `c_angle` |
| e | 540 | ellipse at cx = 270; lower terminal: anchored face `lr` at skeleton angle −θ (θ = 40 / 48 / 68 by weight), cut everything right of the face from the baseline up to the bar centre y = 265; bar from cx − rx to cx + rx + h/wf, thickness b |
| f | 380 | stem at x = 16 + 120 + h from 0 to 750 − h then arc (rx 130, ry 130·RATIO) 180°→90° (vertical cut at the top); crossbar as t |
| g | 560 | o bowl at cx = SB_R + 240; stem centre x = SB_R + 480 − h (outer edge tangent to the bowl), from 510 down to `yc`; quarter-ellipse (rx 200, ry 60 + h, so the inner radius stays 60 at every weight) 0°→−90°, then a straight tail to x = 60 at y = DESC + h (bottom edge on −230); the tail ends at 9 o'clock so the butt cap is a vertical flat cut |
| h n m | 560 / 560 / 860 | stems at SB_S + h and adv − SB_S − h; `arch(c, x_from, x_to)` half-ellipse between them with ry = rx·RATIO, centre at XH + OVER − h − ry, followed by the right leg to 0; m splits at the midpoint with equal counters; h stem to 750 |
| u | 560 | n rotated: left stem 510 → arch centre, arch 180°→360° at −OVER + h + ry, right stem 0→510 |
| i j l | 248 | stem at x = 124: 0→510 (i), −230→510 (j), 0→750 (l); dot radius rd centred at y = 580 + rd (bottom edge 580, 70 clear of the x-height) |
| k | 520 | stem 0→750; `k_arms`: arm and leg leave the stem centre at y = 255, outer edges reaching x = 500 at 510 and 0, skeletons extended 12 percent past and clipped to the band 0..510 |
| r | 330 | stem 0→510, arc rx 130 from 180° to 90° (vertical cut at the top) |
| s | 480 | `s_like(adv 480, top XH + OVER, bottom −OVER, sb 40)`: upper arc (47 percent of the skeleton height) and lower arc (53 percent) joined by a straight spine at β = 38° tangent to both; the bowls' ratio is solved so the outer width equals adv − 2 sb; both arcs end at θ_t = 30° + 0.18·(s − default) and get anchored faces (`ur` upper, `ll` lower); then shifted so the lower face sits at x = sb |
| t | 380 | stem at x = 190 from 0 to 650; crossbar from stem edge − 120 to stem edge + 120, top on the x-height, thickness b |
| v w | 500 / 760 | `solve_zigzag(20, adv − 20, 0, 510, s, n)`: n equal diagonals (2 / 4) whose outer edges pass the corners, mitred apexes trimmed flat to 1.1 s; open ends extended 60 and clipped to the band |
| x | 500 | `cross_diag`: one diagonal whose outer edges pass (20, 510) and (480, 0), mirrored; both clipped to the band |
| y | 500 | right diagonal with outer edges through (480, 510) and (110, −230), clipped −230..510; left diagonal from (20, 510) meeting the right skeleton at y = 40, extended 0.3 h past the meeting |
| z | 480 | `z_poly(20, 460, 510)` one filled polygon, bars thickness b, diagonal of full stem width through the top-right and bottom-left bar corners |

**Uppercase**

| Glyph | Adv | Construction |
|---|---|---|
| A | 660 | zigzag of 2 flipped (apex up), band 0..700; bar at y = 220 between the skeletons, thickness b |
| B | 620 | stem; two `bowl_half` strokes (horizontal from x = 70, half-ellipse down, horizontal back): upper 700 − h → 360 reaching outer x 550, lower 360 → h reaching 570 |
| C | 700 | capital ellipse at cx = SB_R + 330 with the `c_angle` vertical cut |
| D | 660 | stem; one bowl_half 700 − h → h reaching 610 |
| E F | 560 / 540 | stem; bars of thickness b: top (top edge 700), bottom (E), middle centred at y = 360 (geometric 350 corrected up 10), middle shorter (E 490, F 470), top E 510 / F 500 |
| G | 740 | the C ring cut right of the terminal face only from y = 350 up; bar as a filled polygon centred at y = 350, left end at cx − 0.3 s, right end flush with the ring's outer edge above 350 and stopping at the skeleton x below it |
| H | 700 | two stems, bar centred at 360 |
| I | 248 | stem at 124, 0→700 |
| J | 500 | stem at adv − SB_S − h from 700 down to 230, quarter-ellipse 0°→−90° with rx = stem x − 70, ry = 230 + 12 − h, ending at 6 o'clock so the vertical face is the hook's left edge at x = 70 |
| K | 620 | stem; k_arms meeting at y = 360, reaching 600 |
| L | 500 | stem; bottom bar to 460 |
| M | 860 | polyline (lx,0) (lx,700) (430, y_a) (rx,700) (rx,0) with the apex depth solved so the trimmed flat is 1.1 s; band 0..700 |
| N | 700 | polyline (lx,0) (lx,700) (rx,0) (rx,700); band |
| O | 740 | capital ellipse centre (370, 350) |
| P R | 600 / 620 | stem; bowl_half 700 − h → 320 (P, reaching 560) or → 330 (R); R leg from (bowl arc x − 10, 330) to outer x 600 at the baseline, extended 15 percent, band 0..700 |
| Q | 740 | O plus a 45° tail stroke through the ellipse point at −58°, 150 inside and 200 outside, cut below y = −60 |
| S | 580 | `s_like(580, 712, −12, 40)` |
| T | 580 | stem at 290; top bar 20..560 |
| U | 680 | stems from 700 down, half-ellipse (ry = rx × 724/660) bottoming at −12 |
| V W | 660 / 920 | zigzag 2 / 4 on 0..700 |
| X | 620 | cross_diag mirrored on 0..700 |
| Y | 620 | arms from (20, 700) and (600, 700) to (310, 330), stem from 0 to 330 + 0.3 h |
| Z | 600 | z_poly(20, 580, 700) |

**Figures** (advance 560 unless noted)

| Glyph | Construction |
|---|---|
| 0 | ellipse 480 wide, 724 tall (overshoots), centre (280, 350) |
| 1 (adv from drawing, ≈340) | one polygon: stem plus a 45° flag of full stem width leaving the stem's top-left corner, length 1.7 s (1.25 s at Bold), butt cut; left sidebearing 48 |
| 2 | arc (rx = (480 − s)/2, ry = rx·RATIO·0.98, centre y 700 − h − ry) from an anchored `ul` face at 140° clockwise to the exit angle where its tangent equals the diagonal; diagonal + base (b thick, full-width vertical right end at 520) as one polygon whose inner edge passes the base's top-left corner (40, b) |
| 3 | two bowls (rx = 1.3 ry) meeting at the waist y = 362 with a shared horizontal tangent; both ends at 40° from the horizontal with anchored faces (`ul`, `ll`); shifted so the left face sits at x = 50; advance = drawn width + 50 |
| 4 | stem at 390; diagonal + bar (width b) as one path from (top_x, 740) to (80, 190) to (530, 190), clipped above 700 and left of 30 |
| 5 | top bar + left vertical + neck (centre y 430) as one polygon in final space; bowl arc springing from the neck's end at 12 o'clock, ending at 220° with an anchored `ll` face |
| 6 | bowl 480 × 462 on the baseline; top arc = quarter of a larger ellipse (rx 320, ry up to 700 − h) tangent to the bowl's left side, ending at 12 o'clock (vertical cut, no clip) |
| 7 (adv 520) | top bar (b) + diagonal (full s) polygon: right edge through the bar's top-right corner, left edge through (150, 0); crossbar b thick centred at y = 350, one stem beyond each diagonal edge |
| 8 | two ellipses: upper ry = 0.235 H, lower 0.265 H, lower rx = (480 − s)/2, upper 18 narrower |
| 9 | 6 rotated 180° about (280, 350) |

**Punctuation**

| Glyph | Adv | Construction |
|---|---|---|
| period | 260 | dot radius rd on the baseline at x = 130 |
| comma | 260 | the period dot plus a filled quadrilateral tail: right edge tangent at the dot's lower right running down-left at 20° from vertical, flat end 0.55 d wide, lowest corner at −1.2 d |
| colon | 260 | dots at y = rd and XH − rd |
| hyphen | 320 | bar 40..280 centred at y = 265, thickness b |
| exclam | 260 | dot plus stem from d + 120 to 700 |
| question | 460 | head arc (rx = (380 − s)/2, ry = rx·RATIO·0.85) from an anchored `ul` face at 140° clockwise to −72°, a tangent reverse arc back to vertical on the stem line x = cx − 0.45 rx, straight down to y = d + 110; dot on the baseline |

## 8. Bold checks (apply at the boldest master before anything is called done)

- Lowercase bowl counters at least 30 units where a hood or bar crosses (a, e); apertures (c e s)
  at least 40 units of clearance.
- Width growth lightest → boldest at most 6 percent per glyph; a documented exception may go to
  555 → 572 (the double-storey a).
- The g tail's inner radius stays at least 60 (`ryt = 60 + h`); the tail terminal must not touch
  the bowl.
- Terminal-face angles steepen with weight (`c_angle` 30° → 45°, e θ 40° → 68°, s θ_t + 0.18° per
  unit of stem) so the acute corner of a face never spikes and the aperture stays open.
- The a hood degenerates gracefully: when the hood's inner radius would be under 1 unit, draw it
  as a solid half-ellipse and reduce the gap to 30, and say so in the PRD.
- A fixed descender (−230) and a minimum tail clearance can conflict at Bold: reconcile them in
  the PRD (which one gives), never silently in the recipe.
- Every element pair that meets must overlap into the other by 1 to 3 units (stem into hood, neck
  into arc, diagonal one unit back into the ring) so no seam opens when the font is built by
  boolean union.

## 9. glyphs.json format

```
{
  "family": "Testa", "default": "Medium",
  "metrics": {"upm": 1000, "cap": 700, "xh": 510, "asc": 750, "desc": -230, "th": 650, "over": 12, "space": 240},
  "order": ["a", "b", ..., "question"],              // display and font glyph order
  "charmap": {"0": "zero", ".": "period", " ": "space", ...},   // characters whose glyph name differs
  "weights": {
    "<Weight>": {
      "stem": 108, "css": 500, "bar": 101.5, "dot": 117.7,
      "glyphs": {
        "<name>": { "adv": 560, "el": [
          {"d": "M ... A ... Z", "w": 108, "cut": [[x0, y0, x1, y1], ...]},   // stroked skeleton; cut optional
          {"c": [cx, cy, r]},                                                  // filled dot
          {"d": "M ... L ... Z", "f": 1}                                       // filled polygon
        ]}
      }
    }
  }
}
```

Coordinates are font units, y up, already width-scaled per weight; `cut` rectangles are in the
same space and are applied as an even-odd clip (specimen, proof sheets) or a boolean difference
(build_font.py). Letters are keyed by the character itself, alternates as `<base>.ss01`; anything
else uses the names in `charmap`.
