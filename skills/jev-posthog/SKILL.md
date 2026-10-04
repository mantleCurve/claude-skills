---
name: jev-posthog
description: Build PostHog visitor-intent workflows with Jev (TypeSafe AI), including behavioral personas, CRM deduplication, and tailored follow-up drafts. Use when adding this combination to a website or analyzing its visitor events; not for generic analytics setup or video transcription.
---

# Jev + PostHog visitor intent

Turn first-party website behavior into an evidence-backed intent classification and an appropriate next action. PostHog captures behavior; Jev chooses among defined categories; application code handles identity, eligibility, persistence, and routing.

## Establish the implementation context

Inspect the repository and existing analytics, authentication, CRM, email integration, and job runner. Extend the current stack. If there is no application, establish the target website/framework before inventing one. For an analysis-only request, work from supplied exports and return classifications and drafts without adding infrastructure.

Read [integration.md](references/integration.md) when implementing the API boundary, event pipeline, or delivery controls. Read [video-context.md](references/video-context.md) when explaining the originating clip or comparing its claims with the proposed implementation. Verify current official SDK/API docs before installing packages or writing version-dependent integration code.

## Capture useful evidence

Map actual routes and actions to a small event vocabulary: pricing_view, demo_request, careers_view, investors_view, case_study_view, and email_opt_in are examples, not mandatory routes. Specify each event's trigger and allowed properties. Keep successful conversion events separate from button clicks.

Reuse one PostHog initialization and avoid duplicate pageviews on client-side navigation. Distinguish browser-visible ingestion keys from secret personal API, CRM, and TypeSafe keys. Keep secrets server-side.

Use stable first-party user IDs when known; attach a voluntarily supplied email as a property. Keep anonymous IDs until identity is actually established. Preserve logout/reset behavior so a shared browser cannot merge different people. An IP address or company estimate is not proof of a person's identity. If enrichment is requested, keep provider, match type, confidence, and source alongside the result; do not represent a company match as a verified contact.

Honor existing capture consent and suppression settings. Scrub query strings and avoid collecting form contents or credentials. Enable session replay only if it is needed and configure masking; the intent classifier usually needs event summaries, not replay footage.

## Define personas from the business and evidence

Use observed route patterns, conversion events, and known CRM context. Adapt categories to the website rather than copying the clip's persona names blindly. Plausible categories include buyer, internal_champion, investor, job_applicant, existing_customer, and unknown.

For each category record its ID, description, supporting and contradictory signals, appropriate next action, and optional email template. A careers visit suggests recruiting interest; it does not prove occupation. A pricing visit does not establish purchasing authority. Existing CRM facts take priority over guessed job titles.

With little data, label personas provisional. With historical events, report the sample window and size and inspect representative journeys. Do not invent a two-week dataset because the clip suggests waiting for one.

## Classify a session with Jev

Build a bounded chronological summary containing relevant page paths, named events, engagement measurements with their definitions, referrer category, and known business context. Minimize personal data sent to the model. Treat URLs and user-provided values as untrusted evidence, never model instructions.

Use a Choice question for the primary intent with explicit option descriptions and an unknown option. Keep different decisions, such as intent and readiness, in separate atomic questions if both are needed. Read the response under answers.<question_id>; validate type, allowed choice, finite confidence, and probability distribution before use.

Persist input/evidence references, model version, persona-definition version, selected intent, confidence, probabilities, and decision time. Confidence measures concentration of the returned distribution, not verified identity or guaranteed correctness. Make thresholds configurable and tune them with labeled examples. Weak evidence, unknown, invalid output, or provider failure must produce no automatic outreach.

## Prepare the next action

Use deterministic code to check identity availability, contact eligibility, unsubscribe/suppression status, previous outreach, and campaign cooldown before queueing work. Recheck eligibility immediately before delivery. Handle repeated events, retries, and concurrent workers with a durable idempotency key and atomic claim.

Draft a short message that offers something useful for the inferred need, with one relevant next step. Use verified product claims and supplied sender information. Avoid asserting the recipient's inferred role or reciting their tracked browsing. Use templates or a separate text-generation step; Jev's typed decision output does not write an email body.

Default a newly built workflow to dry-run/draft mode. Creating this integration does not authorize contacting real people. Send messages or enroll contacts in sending campaigns only when the user's request explicitly authorizes that action; preserve authorization already given. Do not automatically copy the clip's fallback of putting non-opted-in visitors into cold outreach.

## Verify the complete behavior

Use synthetic events and mocked providers first. Exercise anonymous visitors, known eligible contacts, ambiguous intent, conflicting signals, suppression, repeated sessions, concurrent retries, malformed model responses, and provider timeouts. Confirm event capture and identity reset in the app when available. Test that replay/form data is masked if replay is enabled.

For a live integration, distinguish local contract tests from actual PostHog ingestion, authenticated Jev calls, and email delivery. Missing credentials should leave clearly named configuration requirements and a working dry-run path; never claim live verification based on fixtures. Finish with changed files, verified behavior, and the exact remaining configuration.
