# Coverage and content

## Discover before generating

Read robots.txt and sitemap declarations, then recurse through sitemap indexes and compressed sitemaps with bounded URL counts, response sizes, timeouts and visited-set loop protection. Parse XML with external entity resolution disabled. Preserve raw inventories and record inaccessible sources instead of claiming complete coverage.

Keep fetching within the requested sites. If building a server-side crawler, allowlist targets and defend against private-network URLs, redirect escapes and DNS rebinding. Never forward authorization headers across origins. If HTTP access is blocked, use an available browser; let the user handle interactive challenges. Inspect the actual menus too: sitemap URLs often omit the grouping expressed in navigation.

Normalize scheme/host/trailing-slash conventions for comparison without changing existing live URLs blindly. Separate services, subservices, categories, locations, neighborhood pages, posts and utility pages. Retain provenance: source URL, source site, retrieved date, inferred audience/category and review status. Report discovered versus classified versus drafted versus ready counts separately.

## Content model

Use stable IDs and explicit slugs. Suggested fields: `id`, `parentId`, `kind`, `audience`, `title`, `slug`, `sortOrder`, `status`, `verified`, `sourceUrls`, content blocks and SEO settings. Support arbitrary valid nesting with cycle checks and a bounded UI depth. Residential and commercial can share category labels while retaining distinct page IDs and content.

Changing parent must not automatically change an established URL. Validate missing parents, cycles, sibling ordering, duplicate routes and published children beneath draft parents. Let owners review inherited category choices. Migrations should update untouched seeds only, never overwrite editor revisions.

Generate directory links and breadcrumbs from the same persisted tree. A service catalog should expose individual child pages, not just category cards. On a private preview, drafts can use protected review routes; public navigation, sitemaps and exports must exclude them. Do not confuse a review route with publication.

## Local relevance

Use owner-confirmed name, phone, address, license and service area consistently. Keep business location distinct from places served: a nearby town is not a second office. Confirm service availability and operational claims before publication. Use actual business expertise, photos and approved reviews where available.

A useful service page explains the problem, signs it needs attention, what the service involves, practical limitations, next steps and relevant questions. Link to related services and its parent. A location page needs real local usefulness; if only the place name changes, consolidate or keep it a draft. Never manufacture neighborhood knowledge or testimonials to fill a template.

Use original descriptions and natural topic language. Focus keyword and related terms help plan intent and detect competing pages; exact-match density and presence in every heading are not requirements. Title/description length ranges can be editorial hints, not hard search-engine limits. Avoid using word count, an arbitrary answer-block length, or llms.txt as a ranking prerequisite.

## Unicode hygiene

Inspect field, offset (state UTF-16 versus code-point offsets), code point and context before cleaning. Offer a preview/diff and revision-backed save. Flag zero-width spaces, BOMs, soft hyphens and unusual controls; remove only accidental characters for the current language/workflow. NFC normalization and replacing nonbreaking spaces may be appropriate for English prose but are not universally lossless.

Preserve ZWJ/ZWNJ, directional controls, combining marks and emoji sequences unless their removal is specifically reviewed. Test both an accidental hidden character and legitimate multilingual/emoji input. Never advertise cleanup as defeating AI detectors or removing statistical model watermarks.
