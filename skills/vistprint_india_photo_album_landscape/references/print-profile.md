# Tested landscape profile and revision lessons

These values came from an iterative user-reviewed album, not a Vistaprint specification. Verify the current selected product's template if exact physical dimensions are needed. Do not browse or change the user's product just to enforce this example.

## Accepted interior settings

| Setting | Tested value |
|---|---|
| Interior pages | 24; previous 15/20-page versions were superseded |
| Photo coverage | 135 source files, all used once as foreground |
| Standard final canvas | 3732 × 2900 pixels, ratio 1.28689655:1 |
| Density | 300 DPI in both axes |
| Inferred physical extent | 12.44 × 9.6667 inches at that DPI; not a claimed trim size |
| Colour intent | Solid RGB ivory `#F5ECD9` |
| Final sampled JPG colour in this renderer | RGB (244, 236, 217); expected to be uniform across pages |
| Safety inset | 3.5% of width/height on every edge, followed by 93% uniform content scaling |
| Internal spacing | About 12 scaled points margin and 7 scaled points gap on a canvas whose short side is normalized to 595.2756 points |
| Photo mats | Thin warm white; about 2 scaled points |
| Footer | Small album name at left, page number at right, both inside safe region |
| Output | JPEG quality 98, no chroma subsampling, RGB, 300 DPI |
| Filenames | `photo_new_ivory_1.jpg` … `photo_new_ivory_24.jpg` |

The approved first-page proof was 3634 × 2752 pixels, with a 6% inset, while subsequent pages used the newer dimensions above. That first proof was intentionally preserved in the historical export; **do not reproduce this inconsistency in a new album by default**. For an existing album, do not silently replace an approved first-page composition to standardize dimensions. Explain the difference and adapt it only when requested.

The 3.5% inset is a tested starting point, not a guarantee for arbitrary editor zoom/crop settings. A screenshot's visible crop may depend on how the user placed the image. Moving text inward fixes safe-area problems; DPI does not.

## Layout algorithm

After a three-photo opener, distribute remaining photos evenly over the remaining interior pages, retaining chronological or user-specified groups. Balance integer counts using a ceiling division of remaining photos by remaining pages. Do not hardcode the example filenames, photo count, or opener.

For each group, compare justified rows and transposed columns:

1. Enumerate partitions into a manageable number of rows/columns (1–4 was enough for 5–6-photo pages).
2. Compute row height as available width minus gaps, divided by the sum of source aspect ratios.
3. If the rows exceed available height, shrink them together; center remaining space consistently.
4. Score candidates by usable photo area and size balance. A weighted arithmetic/geometric area score can prevent one photo becoming unusably small.
5. Inspect real content, not only rectangle geometry. Feature family portraits appropriately, preserve heads and feet, and try alternate row/column patterns if the chosen solution leaves excessive whitespace.

For the opening title, first compute the actual top edge of the photo block. In the tested design, title and script subtitle baselines sat approximately 40 and 18 scaled points above that edge. This corrected a large empty gap left by independently top-anchored text.

Render original, EXIF-corrected photos at the required effective resolution. In the original build, an image cache near 320 DPI at placement size reduced memory use. Invalidate resized caches when a source file's checksum changes. Never upscale low-resolution source photos silently.

## What the iterations established

- A4/A5 portrait/landscape PDFs were early deliverables. The printer upload ultimately needed individual landscape JPGs at a custom ratio, not renamed A4 pages.
- Matching a whole screenshot initially included UI/gutter geometry. A later explicit rectangle gave the narrower 3732:2900 ratio. Prefer a selected page rectangle or printer template over screenshot bounds.
- Content outside the editor's inner dashed boundary was lost, including the right photo edge and the bottom album name. Safety space must cover the footer and decorations too.
- Shrinking everything by 12% added too much dead space. A 7% total reduction, tighter internal spacing, and repacked photo layouts improved usable area after proofing.
- Heavy vertical heritage borders became conspicuous after insetting. They were removed, not merely pushed farther inward.
- Faded background photos on every fourth page caused apparent and actual colour differences. They were removed on every page; the final background is solid ivory. Do not re-enable them because an earlier style reference included them.
- Covers were separate, intentionally reused photos, and used AI artwork. Their interpolation and possible photographic changes were disclosed. A later interior-background revision did not automatically prove those textured covers had an identical solid background.

For changes limited to colour or borders, compare page assignments and image rectangles before/after. Rebuilding with a different packing configuration can unexpectedly move photos even when the requested change sounds cosmetic.
