# Sources and provenance

This is an original, reusable synthesis of a custom local-service website/CMS implementation. It includes no client credentials, customer records, proprietary brand guide, business-specific seed content, or third-party runtime. It is guidance plus a structural audit gate, not a bundled CMS, crawler or SEO data subscription.

## Primary references to recheck when applying

- Google Search Essentials: https://developers.google.com/search/docs/essentials
- Helpful content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- AI features: https://developers.google.com/search/docs/appearance/ai-features
- Supported meta tags: https://developers.google.com/search/docs/crawling-indexing/special-tags
- Robots directives: https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag
- Structured-data policies: https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- LocalBusiness: https://developers.google.com/search/docs/appearance/structured-data/local-business
- Sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
- Open Graph: https://ogp.me/
- Core Web Vitals: https://web.dev/articles/vitals
- Responsive images: https://web.dev/learn/images/responsive-images

For X cards, verify current official X developer documentation; the implementation convention uses `twitter:*` names. Product rebranding is not grounds to invent `x:*` tags.

## WordPress plugin patterns considered

- Yoast analysis: https://developer.yoast.com/features/analysis/overview/
- Yoast focus keyword: https://yoast.com/focus-keyword/
- Yoast sitemap specification: https://developer.yoast.com/features/xml-sitemaps/functional-specification/
- Yoast breadcrumbs: https://yoast.com/features/breadcrumbs/
- Rank Math advanced settings: https://rankmath.com/kb/advanced-tab/
- AIOSEO revisions: https://aioseo.com/docs/tracking-changes-to-your-seo-using-seo-revisions/

Adapted patterns: editor-level metadata, focus-topic guidance, robots controls, social overrides, structured data, canonical/sitemap consistency, redirects and revisions. These references do not imply complete plugin parity, integration with those products, or their endorsement.

## Community workflows reviewed

- AgriciDaniel/codex-seo at `9a644f68d39d242a7a41a0017f7286dd0512fc3b`: https://github.com/AgriciDaniel/codex-seo/tree/9a644f68d39d242a7a41a0017f7286dd0512fc3b
- SNLabat/SEO-GEO-AEO-Skill at `a2c8769b85813912b2b01cd12c3484f061b439fc`: https://github.com/SNLabat/SEO-GEO-AEO-Skill/tree/a2c8769b85813912b2b01cd12c3484f061b439fc
- AgriciDaniel/claude-seo: https://github.com/AgriciDaniel/claude-seo (user-supplied workflow overview considered; no pinned executable adopted).
- A user-supplied InfiniSynapse article informed the distinction between model review and deterministic report parsing. Its unrelated project's schema and CLI were not adopted.

Review context: 2026-09-16. No third-party installer or paid extension is required or executed by this skill. Community claims are not primary evidence for search-engine behavior. Recheck changing guidance rather than carrying forward a source's release date, star count, scoring claims or promises of ranking/citation benefits.
