# Mobile-first delivery and measurement

Inspect requested reference sites at a phone viewport, not only desktop screenshots. Record actual behavior: booking/call/menu placement, menu expansion, category-to-subcategory navigation, sticky actions, forms and content priority. Borrow useful interaction patterns without copying unsupported business claims or unlicensed assets. Apply the supplied brand guide; do not extract or distribute licensed fonts without authorization.

## Navigation and conversions

Start at 360–390 px and verify 320 px plus tablet/desktop. Use accessible toggle buttons with expanded state and controls relationships; avoid hover-only menus. Large service trees often work as audience tabs and category/child columns on desktop, single-open accordions on phones. Derive both from the same content tree and preserve a usable no-JS fallback.

Verify open/close, repeat-click collapse, audience switching, viewport changes, keyboard focus, Escape, and every visible child link. Check labels and ordering against the source inventory. Keep call/request actions reachable without covering form submit buttons or final content; account for safe-area insets. Use adequate touch targets, readable type, explicit form labels and visible focus. Check horizontal overflow and keyboard-open layouts.

Audit typography across all generated routes when practical: computed font-family, intended weight/size/line-height, fallback fonts and visible overflow. Form controls can inherit bold label weights through `font: inherit`; set their intended normal weight explicitly. Browser-native select popups may use OS-controlled styling. Don't promise a licensed brand font is loaded when only its fallback is available. Maintain semantic type hierarchy rather than forcing every text element to one size.

For large service forms, use a searchable picker with audience/category filters and nested service choices. Include a “Something else” path with an explicit custom-description field, server validation, persistence, notification email and admin display/export. Keep local availability claims qualified. Stack narrow filters to avoid clipped labels. Preserve native/no-JS selection where feasible; don't hide a required control without supplying accessible validation. Test keyboard selection, Escape, zero results, category reset and custom input. Initialization must not steal focus or scroll the visitor down to the form on page load.

## Image and asset pipeline

- Decode and validate uploads before processing. Apply EXIF rotation; strip unneeded metadata while respecting required attribution/provenance. Bound file size, dimensions and decoded pixel count.
- Generate widths matching real display sizes; do not upscale. AVIF with WebP/JPEG fallback can reduce bytes. Tune quality against visual inspection, not just minimum byte size. Logos/text/line art may need SVG or lossless formats; sanitize untrusted SVG or disallow it.
- Emit `picture`/`srcset`/accurate `sizes` with explicit width/height or aspect ratio. Check the browser's `currentSrc` and transferred bytes at mobile DPR, since a small viewport can still request a large image.
- Do not lazy-load the LCP image. Prioritize only the actual above-fold hero; lazy-load below-fold media. Avoid preloading unused variants.
- Serve crawlable HTML with minimal client JavaScript, deferred enhancements, compressed text, correctly typed images and versioned static assets. Keep CMS bundles out of the public page. Subset licensed self-hosted fonts or use a sensible fallback; do not block rendering on unnecessary font downloads.
- Cache public static files at an appropriate CDN when supported, keeping private previews and authenticated data out of shared public caches. A static frontend can be independent of a slower CMS backend, but forms and previews still need correct origin/auth behavior.

## Evidence

For each performance run, record timestamp, URL/release, viewport/DPR, network and CPU throttling, cold/warm cache, authentication, browser/tool version and whether data is lab or field. Run at least a realistic mobile scenario; use unthrottled results only with that qualification. Inspect network requests and layout, not just a Lighthouse score.

Measure LCP, CLS and available interaction evidence; TTFB/FCP and transfer sizes help diagnose causes. INP requires interactions/field data and must not be fabricated from TBT. Recheck current web.dev thresholds when reporting. A user target such as “under one second” needs a named metric and conditions; a local cached result does not prove every visitor loads in a second.

Retain screenshots/traces or report paths. Fix demonstrated bottlenecks (oversized hero, blocking assets, fonts, main-thread work, slow HTML delivery), rerun the affected measurement, and report remaining limitations. Do not publish invented benchmark results.
