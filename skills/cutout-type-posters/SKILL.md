---
name: cutout-type-posters
description: Use when turning one photo of a person into premium Instagram posts — birthday, milestone, announcement or "make this photo look premium" — with bold uppercase typography, subject cutouts, clean whites or flat colour, deliberate crops. Also when asked for many style variations of one photo (10, 50, 100 designs), a 4:5 feed post, or to make an edit look like a top design account instead of a filter.
---

# Cutout type posters

**One real photo + a clean subject cutout + bold UPPERCASE type + a deliberate layout = a post that looks designed, not filtered.** Everything is HTML/CSS rendered by headless Chrome at 2160×2700 (Instagram 4:5 at 2×), so every design is exact, editable and re-renderable.

## What "premium" means here (learned the hard way)

Rejected as cheap: warm hazy "luxury" grades, gold foil, script fonts, thin high-contrast serifs (Bodoni-style), italic serif headlines, wedding-invitation layouts, font specimen pickers.
Approved: ALL-CAPS heavy grotesks (condensed, normal or extended widths), clean neutral whites or one flat bold colour, the subject cut out and interacting with the type, cuts/strips/grids, tiny tracked labels as a second voice. See `references/craft.md`.

When the person shares an example they made, treat it as the **quality bar, never the template**: match its confidence, not its layout.

## Workflow

1. **Prep the photo** (macOS, on-device, nothing uploaded):
   `scripts/prep.sh <photo> <project>/assets` → `clean.png` (bright neutral grade), `bw.png`, `cutout.png` (RGBA), `cutout-dark.png` (eroded edge for dark backgrounds), `comp-bw-color.png` (B&W room, subject in colour), `mask.png`, `subject.json` (subject bounding box). Note the face box by eye from a preview; layouts must never cut through it.
2. **Start from a template** in `templates/` (copy it and `base.css` + `fit.js` into the project):
   - `strips.html` — photo cut into stepped vertical strips (wide centre strip holds the face), B&W room / colour subject, rotated type column.
   - `block.html` — flat colour poster, giant condensed words behind the cutout, name in extended white caps in front of the legs.
   - `swiss.html` — waist-up crop over extra-wide stacked caps, one red accent word, rule + 4-field info row.
   - `balloon.html` — the subject holding a giant number on a string; big two-line headline in the empty corner.
   Fill the `{{PLACEHOLDERS}}` and the config block at the top of the script (crop origin/scale, face-safe widths, anchor and hand points from `subject.json`).
3. **Render and look**: `scripts/render.sh <project> <name> [...]` → `out/<name>.png`, `.jpg`, `preview-<name>.jpg`. Read every preview. Then zoom (ffmpeg `crop=`) on the face, cutout edges, joins (string ↔ hand, knot ↔ number) and the smallest text before calling it done.
4. **Many variations**: pick distinct concepts from `references/styles.md` (100 styles in 5 families). For 20+ designs, split into batches of ~20 per subagent, each with its own folder, numbered files, the shared brief (rules below + craft.md) and its own concept list, so no two batches overlap. Give each batch a different headline font per design. Watch for stalls (no new render for 20 min). Finish with `scripts/sheet.sh` contact sheets and your own review pass.

## Hard rules

- 4:5, 1080×1350 CSS px, device scale 2. ALL TEXT UPPERCASE (`text-transform: uppercase` on the canvas).
- Only the real photo. Never warp, stretch or AI-regenerate the face. Colour treatments (duotone, halftone, posterize, riso grain, B&W) are fine.
- Cuts, strips, shards and panels never slice the face.
- Don't enlarge a crop past ~1.6× CSS px of source pixels — faces go soft. Ask for the original camera file if the shared image is small.
- Key text inside 48 px margins, never over the face, never clipped by accident. Words hidden behind the subject must stay readable.
- No real brand names, logos or imitations of a real product UI.
- Outputs go in a real project folder the person owns — never `/tmp` or a session scratchpad.
- Fonts from Google Fonts via `<link>`; list every face in `window.FACES` so `fit.js` waits for it before measuring.

## Pitfalls that cost real iterations

| Symptom | Cause | Fix |
|---|---|---|
| Fitted headline far too small | measured the element box (`scrollWidth` of a block = container width) | measure the text with a `Range` (`fit.js` does) |
| Fitted size random between renders | measured before the web font loaded | `document.fonts.load()` every face first (`window.FACES`) |
| Rotated type huge | measured after `rotate(-90deg)` (bbox width = line height) | measure first, rotate in `afterFit` |
| One short word becomes enormous | each line fitted to full width | fit the longest line, give the others the same size |
| Light halo round the subject on dark grounds | mask edge contains wall pixels | use `cutout-dark.png` (eroded mask); a faint rim that is real backlight in the photo stays |
| String "stabbed" into a balloon number | line started inside the glyph | measure ink bottom with canvas `actualBoundingBoxDescent`, add a knot, draw the string behind the subject so the hand covers its end |
| Headless Chrome exits with no PNG | several renders at once | `render.sh` retries and checks the file |
| Accented capitals (Ê, Å) hit the row above | tight stacked line-height (.74 in `block.html`) | loosen to ~.84 for that row or avoid accents in stacked words |
| A red banner covers the render | `fit.js` caught an error: unfilled `{{PLACEHOLDER}}`, font not loaded, missing image, crop gap, bad config | read the banner text and fix that, never ship a bannered render |
