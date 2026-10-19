# Review loop and publishing checklist

Every change to `tools/glyphs.py` is followed by: regenerate, render the proof sheets, look at
them with the Read tool, fix, repeat. Never judge a glyph from its path data or from a single
weight; the faults that matter (slivers at a terminal, stepped corners, a closing counter) only
show in the rendered Bold or Light.

## 1. Regenerate

```bash
SKILL=~/.claude/skills/prototyping-typeface-from-prd
python3 tools/glyphs.py --root .            # the project's copy of the generator
```

## 2. The eight proof sheets

One row per weight, lightest first; red lines at baseline, x-height and cap height. The PNG is
sized to its content, so nothing is clipped. Render all eight after any change that touches a
shared helper (arch, s_like, face_cut, solve_zigzag, Ctx); render just the affected sheet for a
single-glyph fix.

```bash
mkdir -p proofs
proof() { python3 "$SKILL/scripts/proof.py" --root . "$@"; }     # a function: zsh does not split "$P"
proof proofs/lc1.html a a.ss01 b c d e f g h            --png proofs/lc1.png
proof proofs/lc2.html i j k l m n o p q                 --png proofs/lc2.png
proof proofs/lc3.html r s t u v w x y z                 --png proofs/lc3.png
proof proofs/uc1.html A B C D E F G H I                 --png proofs/uc1.png
proof proofs/uc2.html J K L M N O P Q R                 --png proofs/uc2.png
proof proofs/uc3.html S T U V W X Y Z                   --png proofs/uc3.png
proof proofs/fig.html zero one two three four five six seven eight nine --png proofs/fig.png
proof proofs/pun.html period comma colon hyphen exclam question         --png proofs/pun.png
```

Then `Read` each PNG. For a suspect junction, zoom: `--zoom x0,y0,x1,y1` (font units, y up) crops
every cell to that box, e.g. the g tail `--zoom 0,-260,560,120 --px 420`, the e terminal
`--zoom 250,-20,560,300`, an s terminal `--zoom 280,300,500,540`.

The equivalent manual command, if a sheet is needed without `--png`:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --hide-scrollbars --window-size=2000,1300 --screenshot=proofs/lc1.png "file://$PWD/proofs/lc1.html"
```

## 3. What to inspect, per glyph class

Check every item at every weight. Bold first: it fails first.

**All glyphs**
- Outer edges land on the metric lines (baseline 0, x-height, cap height, ascender, descender);
  round forms overshoot by exactly the PRD overshoot, top and bottom.
- No sliver, wedge or hairline left where a clip rectangle met a stroke; no stroke continuing
  past a terminal face.
- Every junction of two elements overlaps (a stem runs a few units into the arch or hood it meets);
  no seam, no step on the shared outer edge.
- Advance width matches the PRD width table (shown under each cell); sidebearings symmetric where
  the PRD says so.

**Rounds (o c e b d p q O C G Q, figures 0 6 8 9)**
- Same ellipse family per case; the bowl is tangent to its stem on the outer edge with no bump.
- Terminal faces on c, e, C, G are true verticals of full stroke width, with the inner corner
  where the recipe anchors it; the e bar hides the ring's cut and ends flush with the bowl.
- Counters stay open at Bold: lowercase bowl counter at least 30 units tall where a hood or bar
  crosses it, apertures (c, e, s) at least 40 units.

**s and S**
- Both terminals are vertical faces of full width; the spine is tangent to both arcs; the two
  bowls' outer edges reach the sidebearings. At Bold the lower terminal must not touch the spine.

**Arched (n m h u r f)**
- Arch springs from the stem with the join overlapped, not butted; r and f terminals are
  horizontal full-width flat cuts (the skeleton ends where the tangent is vertical).

**Diagonals (v w x y z k A V W X Y Z K M N R, figures 1 2 4 7)**
- Mitred apexes trimmed flat to 1.1 stems, both sides symmetric; open ends cut flat on the metric
  band, no overshoot beyond it.
- Where a diagonal meets a bar (z Z 7 1 2 5 E), the corner is one filled polygon: no step, no
  notch, no overhang past the bar's end.

**Mandated glyphs (whatever the PRD fixes; in the reference family t j g)**
- Re-read the PRD's bullets for each and tick them literally: stem x and width, crossbar y range
  and extent, dot diameter and clearance, tail terminal position, tail inner radius at the
  boldest master, clearance between tail and bowl.

**Dots and punctuation**
- Dot diameter 1.09 stem at every weight; comma tail flat-cut; exclam gap above the dot scales
  with the stem.

**Width growth**
- Compare the advance under each cell across the rows: Light to Bold growth at most 6 percent
  (PRD 12); a glyph that needs more (the double-storey a at Bold) gets a documented exception in
  the recipe comment and in the PRD.

## 4. Specimen and tester shots

```bash
python3 $SKILL/scripts/build_specimen.py --root .
python3 $SKILL/scripts/screenshot.py specimen/index.html proofs/specimen-1280.png --wrap --width 1280 --height 2600
python3 $SKILL/scripts/screenshot.py specimen/index.html proofs/specimen-400.png  --wrap --width 400  --height 2400
.venv/bin/python $SKILL/scripts/build_font.py --root . --screenshot      # fonts/screenshots/tester-{1280,400}.png
```

Read all four. Check: the hero word is the family name set in its own glyphs; one card per
mandated glyph with the PRD bullets; the weight toggle lists every weight; the sample settings
wrap at 400 px with no horizontal scroll; the tester status reads "<Family> 300 · 500 · 700
loaded" (not the serif fallback) and the ss01 toggle changes the a. In the tester, compare the
Bold row against the Bold proof sheet: the font is stroked by Skia from the same skeletons, so any
difference is a `cut` rectangle the stroker handled differently from the browser's clip-path.

## 5. Artifact page contract (publishing the specimen or tester)

Both templates already follow it; keep it when editing them:

- The file starts at `<title>` with no `<!doctype>`, `<html>`, `<head>` or `<body>`: the host
  wraps the page. That is why `screenshot.py --wrap` exists for local shots.
- `<title>` is a two-to-four-word name ("Testa Specimen"), first line of the file; then
  `<meta name="claude:viewport-fit-sides" content="cover">`.
- Colours are tokens on `:root`, redefined for dark mode twice: under
  `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {...} }` and under
  `:root[data-theme="dark"] {...}`; `body` has an explicit background.
- 16 px side gutters using `max(16px, env(safe-area-inset-left))` / right; sticky bars offset by
  `env(safe-area-inset-top)`; no horizontal page scroll at 400 px (tables wrap in
  `.table-wrap { overflow-x: auto }`).
- No external scripts. The only external resource is the Google Fonts stylesheet for the UI face
  (allowed CDN); the glyph data and the WOFFs are inlined, so the page works offline.
- Keep the rendered file under 16 MB; three sample-set WOFFs plus glyph JSON are well under 1 MB.
- Publish `specimen/index.html` and `specimen/tester.html` as two artifacts (icon: "font"), with
  one-sentence descriptions naming the family and the milestone.
