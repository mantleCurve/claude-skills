# Originating clip

Source: user-provided igexport-Dd_7b41RsOx.mp4, about 73 seconds. Summary based on visible captions and demonstrated screens; not a verbatim audio transcript.

The speaker proposes building a visitor-intent and follow-up system using an existing landing page, PostHog, and TypeSafe AI's Jev. Approximate sequence:

- 0–16s: pitches a self-built alternative to expensive visitor-identification/outreach tooling.
- 16–30s: install PostHog, gather behavior, and analyze visitors into archetypes.
- 30–40s: prepare a different follow-up email for each archetype.
- 40–54s: after a visit, check the CRM for previous outreach; send activity/context to Jev, select a persona, and route to an email.
- 54–62s: use submitted emails when available; otherwise mentions third-party identity tools and claims they find emails around 20% of the time.
- 62–73s: closes by promoting more Jev + PostHog use cases.

Screens show named intent events, a TypeSafe Choice response, HubSpot, and a cold-outreach branch mentioning Instantly. They suggest a confidence cutoff of 0.6. That cutoff is an example from the clip, not an evaluated production standard. The cost and email-match-rate claims are the speaker's claims and have not been independently established here.

The useful reusable pattern is behavioral analytics → intent classification → CRM checks → tailored follow-up. Identity enrichment is a separate integration, and neither a confident Jev category nor PostHog telemetry supplies a verified email address for every anonymous visitor. The skill adds unknown outcomes, robust job handling, and draft-first delivery to make the pattern usable without treating the promotional claims as guarantees.
