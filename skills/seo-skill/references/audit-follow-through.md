# Turn audit findings into verified fixes

Treat a supplied SEO audit as a set of testable claims. Inspect the referenced source, build output, live release and export separately. Record confirmed defects, claims already addressed, unsupported conclusions and owner-dependent work. Preserve the user's active implementation work when a new audit arrives.

## Template and location similarity

Exact-string uniqueness checks miss city-name substitutions. Compare substantive page text separately from shared navigation/footer boilerplate. Include introductions, body, sections and FAQs; checking only an often-empty body field can give a false pass.

Use token shingles or another documented similarity measure. The bundled `scripts/content-quality.mjs` exports `shingles()` and `similarity()` for three-word Jaccard comparisons. For location-template detection, normalize only the known location name from each record to a common placeholder before comparing; retain the original text and explain normalization in the evidence. Compare like page types and report the matching URLs and score, not just a red badge. Cache token sets within an audit instead of retokenizing each pair.

A threshold such as 75% is a review heuristic, not a Google policy or ranking boundary. Test both a city-swapped pair that should be flagged and unrelated service pages that should not. Don't optimize prose merely to evade a similarity detector. Ask whether the page serves a distinct useful intent.

Local substance must be true: owner-supplied work examples, expertise, service limits and confirmed location details. Never invent housing stock, pipe ages, travel times, municipal issues or customer jobs. No fixed word count makes a doorway page useful. If evidence is unavailable, consolidate with appropriate redirects or keep incomplete pages excluded from indexing pending review. Do not delete established URLs without checking their history. Report noindex containment as containment, not as a completed content rewrite.

## Descriptions and timestamps

Do not hard-cut a summary at character 160. Prefer a hand-written description; fallback to complete sentences that fit, otherwise a whole-word cut with an ellipsis. Inspect endings for dangling phrases. The bundled `descriptionFrom()` helper preserves complete sentences where possible; its length cap is an application convention, not a search-engine requirement. Keep explicit editor overrides.

Apply changes to existing stored content as well as seeds/build templates. Migrate untouched seed records only, or use a reviewed draft patch. Record before/after, actor, timestamp and fields changed. Preserve edited pages and handle version conflicts.

Sitemap lastmod should come from meaningful persisted content changes. A renderer may already support it while seed data lacks timestamps. Use a real fixed source-maintenance date for seeds when known, not the current build time on every deploy. Omit unknown dates instead of fabricating freshness.

## Distinguish artifacts and facts

- A backend deployment's `dist/` can legitimately include protected CMS assets. Inspect the actual public export allowlist and the marketing page network requests before claiming those assets ship to visitors. Keep admin HTML noindex and authenticated, and test the export archive itself.
- LocalBusiness properties should use known image/logo URLs and verified entity details. Optional sameAs, map, geo, hours and pricing controls should leave unknown values unset. Show relevant hours/maps/prices visibly when emitted. A GBP URL or priceRange is not a guarantee of local-pack eligibility or rankings.
- Privacy/terms drafts are not published policies. Surface their review status as a launch dependency; do not assert legal completeness or fill unknown practices from generic boilerplate. Short contact pages aren't defective merely for being short.
- Review placeholders should stay unindexed until useful verified review information is available. Do not fabricate a review feed or imply that publishing a self-serving rating produces Google review stars.
- Inspect an SVG before suggesting SVGO. An embedded raster payload may dominate its size, and a smaller PNG may be a different white/reversed wordmark. Check visual equivalence and brand authorization before replacing it.
- A static-output audit cannot measure field CWV, Google indexing, backlinks, local-pack rankings or AI citations. Do not turn inferred performance into observed lab results.

Recheck current primary guidance on [spam policies](https://developers.google.com/search/docs/essentials/spam-policies), [LocalBusiness](https://developers.google.com/search/docs/appearance/structured-data/local-business) and [sitemap lastmod](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
