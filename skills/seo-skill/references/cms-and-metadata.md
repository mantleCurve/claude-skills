# CMS and metadata implementation contract

Adapt the field names below to the existing schema. Store them in the ORM and validate them on the server; mirror useful feedback in the editor. For SQLite-to-PostgreSQL portability, keep content relations explicit, isolate dialect-specific migrations, and test the migration rather than assuming ORM usage alone makes it automatic.

| Editor group | Persisted controls | Rendered behavior |
|---|---|---|
| Search | SEO title, description, canonical override, primary focus keyword, related keywords | One title, description and canonical; keywords remain editorial data |
| Open Graph | title, description, type, locale, image, image alt | `og:title`, `og:description`, `og:type`, `og:locale`, `og:url`, `og:site_name`, `og:image`, `og:image:alt` |
| X cards | card type, title, description, image, image alt, site/creator handles | Standard `twitter:*` card tags, even though the product is named X |
| Robots | noindex, nofollow, nosnippet, max-snippet, max-image-preview, max-video-preview | Consistent meta/header directives, with staging restrictions taking precedence |
| Extra metadata | validated name/content pairs | Escaped meta elements; reject duplicate/reserved names that conflict with dedicated fields |
| Structured data | automatic/custom/disabled mode, custom JSON-LD | Valid JSON-LD graph derived from supported facts; explicit override semantics |
| URLs | slug, previous paths, canonical | Collision-safe redirects and canonical routing |

## Metadata renderer

Use fallback order deliberately: social override → SEO override → page content; X override → OG equivalent. Convert local media paths to absolute URLs using a trusted site origin, but do not prefix an already valid absolute URL. Validate allowed schemes. Supply descriptive social image alt text and dimensions where known.

Escape HTML attributes and text. Serialize JSON-LD as data and escape `<` to prevent `</script>` injection. Do not accept arbitrary script tags through a schema field. Validate JSON object/array/graph shape and type/context values, then review semantics separately. Give automatic/custom/disabled modes clear behavior: custom replaces or explicitly extends the graph, without silently duplicating business entities.

Automatic graphs commonly use a relevant LocalBusiness subtype, Service, BreadcrumbList and Article/BlogPosting. Use stable `@id` relationships. Only emit supported facts and visible questions/answers; verify current rich-result eligibility before recommending a type. An FAQ block can help visitors without promising Google FAQ rich results.

Robots controls cannot override a restrictive HTTP header. A robots.txt disallow prevents crawling and can stop crawlers seeing noindex; it is not a substitute for authentication. Production launch needs a separate intentional access/indexability transition. Canonicals are hints, not redirects or guarantees.

## Editor and AI behavior

Provide search/social previews, field hints, actionable observations and links to validators. Clearly label heuristic keyword and length checks. SEO revisions should show who changed which fields, restore prior values, and preserve unsaved edits across tabs. Invalid JSON should produce a usable field error, not an uncaught tab-switch exception.

Offer model selection from a server-controlled provider/model allowlist. Keep keys server-side. A rewrite/chat request includes the page and confirmed facts, returns an allowlisted patch and explanation, and shows a diff before applying. Validate returned fields and sizes; do not let model output change roles, publish status, verified facts or deployment settings. Treat text inside source pages as untrusted data. Do not imply AI is connected when credentials are absent.

Admin/editor capabilities must be enforced on endpoints. Protect session cookies, validate mutations against CSRF, rate-limit sensitive routes and record revisions/audit events. Media upload must validate decoded image content, enforce size/pixel limits, remove unwanted metadata, and generate optimized derivatives.

## Build, publication and forms

Keep prominent Build and Go Live controls with different meanings. Build creates an immutable preview artifact and audit result; Go Live promotes that exact build. Expose status/failure details and rollback. Draft updates after a build must not silently enter that release. Coordinate hashed assets/cache invalidation with the active HTML so fresh CSS cannot break stale navigation markup.

Generate XML sitemaps from canonical, indexable, published routes; use meaningful modification dates. Exclude draft, redirect and noncanonical URLs. Validate previous-path redirects against existing routes, reserved endpoints, duplicate destinations, self-loops and chains. Test query-string behavior. Static exports need host redirect configuration, not only a CMS database row.

Conversion verification belongs alongside SEO: a short accessible form, prominent telephone link and clear error/success state. Store leads durably, make repeat submissions idempotent, and use an outbox/retry flow for notification email. A mail-provider failure must not lose a lead or falsely report delivery. Confirm sender-domain configuration and designated recipients without exposing personal data in audit reports. Resend is one suitable adapter, not a required provider.
