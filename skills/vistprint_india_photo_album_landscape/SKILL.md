---
name: vistprint_india_photo_album_landscape
description: Prepare landscape photo albums for the Vistaprint India editor, including source-photo coverage, print-safe layouts, consistent ivory backgrounds, front/back covers, and numbered 300 DPI JPG exports. Use for album creation or revisions from local photo folders and printer screenshots.
---

# Vistaprint India landscape photo albums

The identifier intentionally preserves the user's spelling `vistprint_india_photo_album_landscape`.

Create reviewable local album images for upload to the printer's editor. This skill does not place orders or upload personal photos automatically. Keep personal photos, albums, previews, and source inventories outside this skill repository.

## Start from the latest accepted proof

Recover the source folder, page count, approved layout, printer canvas ratio, output naming, and background choice from the conversation or project notes. Ask only for missing decisions that block a useful proof. If starting fresh, establish total interior pages, maximum photos per page, photos that must stay together, covers, and desired style. Check that page capacity can accommodate all photos before laying out the album.

Use the latest curated folder. Do not silently remove visually similar photographs: separate files may be intentional alternate shots. Create a per-file inventory with dimensions, EXIF orientation, and a checksum, and assign each foreground photo exactly once. Keep a page manifest so revisions never shuffle or omit photos accidentally. If a cover reuses an interior photo, record that as a deliberate cover reuse; do not claim zero repetitions across covers and interiors.

Read [references/print-profile.md](references/print-profile.md) for the tested profile, layout mechanics, and the lessons from the actual printer previews. Its dimensions are empirical settings from one album, not official specifications for every Vistaprint product.

## Proof before batch

1. Make page 1 as a single high-quality JPG. Keep its title near the photo block, rather than anchoring the title to the top edge while centering the photos separately.
2. Inspect the uploaded printer proof when the user supplies it. Distinguish the image selection box, visible page, inner dashed print boundary, gutter shadow, and surrounding editor UI. Match the requested image rectangle, not automatically the whole screenshot.
3. Test an interior page on the opposite side of the spread. A proof that fits a right-hand page may expose gutter or crop problems on a left-hand page.
4. Once approved, batch the remaining pages with the accepted settings. Preserve independently approved pages exactly unless asked to revise them. Describe any remaining dimension differences.

Do not guess physical trim, bleed, or spine widths from screenshot pixels. Prefer printer dimensions or templates when available; otherwise label the ratio as screenshot-derived. A 300 DPI tag alone cannot establish printer compatibility.

## Design and production

- Use one solid ivory base, `#F5ECD9`, throughout unless the user chooses otherwise. The final accepted workflow has **no transparent/faded background photos, gradients, paper textures, or side-border lines**. Earlier experiments with those were superseded.
- Use the same RGB rendering/export pipeline for every page. The rendered JPG RGB can differ slightly from the design hex; check actual pixels across exported files before saying their backgrounds match.
- Use restrained serif titles, an optional script subtitle on the opening page, thin white photo mats, small ornaments only if desired, and a discreet footer/page number. Fonts must be available and licensed; avoid platform-specific font paths in reusable code.
- Prefer full-photo aspect ratios and upright EXIF orientation. Try justified rows and columns, varied hero sizes, and a balanced distribution of photos. Do not stretch faces or silently crop heads/feet to fill space. If excess whitespace remains, compare alternate layouts before enlarging everything beyond the safe area.
- Keep all photos, ornaments, text, and footers within the safe rectangle. Fill the entire outer canvas with the base colour so trimming reveals the same colour. Apply layout scaling separately to each page with save/restore; a PDF page break resets transforms.
- For requested groups, lock the group to one page and repack other pages without exceeding capacity. Track unplaced photos explicitly; never hide overflow.
- Revisions should operate on the original photo files and layout data, not on a low-resolution editor screenshot. Preserve the accepted photo grouping and placement whenever changing only a background or border.

PDF is an optional intermediate. A useful implementation is ReportLab for layout plus PyMuPDF for rendering. Deliver JPG only when requested; keep temporary PDFs and contact sheets in a scratch directory.

## Front and back covers

Create separate files outside the interior page count unless the user requests otherwise. Use the accepted aspect ratio and background. Keep titles and faces well inside the print boundary. Do not invent a barcode or spine; a wraparound cover needs the printer's actual template.

Prefer original-photo compositing for identity fidelity and native image detail. If image generation is available and appropriate, use it for requested cover artwork, explicitly preserve identities, inspect the result, and save prompts and generation notes alongside the private output. If unavailable, compose from originals; do not require a specific provider. Disclose AI-generated details and upscaling. Never call interpolated artwork native 300 DPI detail merely because it has 300 DPI metadata.

## Export and verification

The optional [scripts/export_jpgs.py](scripts/export_jpgs.py) exports a correctly sized PDF to a fresh numbered JPG directory and verifies dimensions, DPI, page count, and optional background sampling. It does not fix layout or resize a mismatched PDF. Requires Python 3, PyMuPDF, and Pillow.

```bash
python scripts/export_jpgs.py album.pdf output/jpg/album-final \
  --width 3732 --height 2900 --dpi 300 --pages 24 \
  --prefix photo_new_ivory --uniform-background
```

Before delivery:

- Verify every source photo is assigned exactly once in the interior manifest, with no omissions, and the source inventory has not changed during the build.
- Inspect contact sheets for **every page**, plus full-size views of revised pages, tight footers, and dense layouts. Check text clipping, overlap, distortion, and image sharpness.
- Verify actual file encoding is JPEG, not PNG with a `.jpg` suffix; verify pixel dimensions and embedded DPI after the final conversion. Some image tools reset DPI during padding/conversion.
- Sample multiple empty background points across every JPG and inspect the render manifest to confirm background-photo layers are absent. Matching only the outer corners is insufficient if a tinted panel remains inside.
- Use `photo_new_ivory_1.jpg` through `photo_new_ivory_24.jpg` when following this workflow's final naming choice; adapt the range to the requested count. Verify filenames numerically, since lexical sorting puts 10 before 2.
- Deliver the final folder and useful individual proof links. State what changed, dimensions, DPI, page count, and any material limitation. Do not claim the printer proof is verified unless it has actually been inspected.

Store a short private handoff next to the album with source location, settings, latest approved proofs, manifest, filenames, and superseded variants. Never publish that personal handoff or photographs with this reusable skill.
