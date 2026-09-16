# Audit evidence and release verification

Use observations appropriate to the task: CMS record checks, generated HTML checks, a live crawl, browser measurements and authenticated account data are different scopes. Report them separately. A saved CMS field does not prove its tag is in the active release; a successful HTTP response does not prove the form reached storage or email.

## Report contract

The bundled `scripts/gate.mjs` validates this small, versioned contract using Node 18+ and no dependencies. It reads a local file only; it does not crawl, assess semantic truth, run an LLM, or contact a third party.

Required root fields:

- `schemaVersion`: integer `1`.
- `rulesVersion`: nonempty implementation/rules identifier.
- `generatedAt`: ISO timestamp with timezone.
- `scope`: nonempty description of what was actually checked.
- `pageCount`: nonnegative integer for the inspected scope.
- `issues`: array of records, each with nonempty `name` and `url`, `status` (`pass`, `warning`, `error`), `evidence` (nonempty string/object/array), and string `recommendation` (nonempty for warning/error).
- `unmeasured`: array of nonempty strings naming relevant checks that were not performed; use an empty array only if justified by the stated scope.

Optional fields can include source URLs, tool versions, private-preview status, summary counts, page IDs, artifact paths, dependencies, failure checks and leading indicators. The gate derives counts from issues; it does not trust a summary or model-authored overall verdict. Keep credentials and lead data out of reports.

Each finding should say what was observed, why it matters, what to change and how to verify it. For example: record the two routes sharing a canonical, rather than only “canonical problem.” Treat editorial ranges as warnings. The project decides which concrete failures block its build.

Run from the skill folder:

```sh
node scripts/gate.mjs /absolute/path/to/seo-report.json
node --test scripts/gate.test.mjs
```

Exit contract: `0` valid evidence with no error findings (warnings are printed); `1` valid report with error findings; `2` missing, unreadable, malformed or incomplete contract. Empty page/issue sets fail as incomplete evidence. This is a structural gate, not proof the submitted observations are true or exhaustive. Integrate it after the actual check producer and retain both report and stderr in CI. Never invent passing rows to satisfy it. Do not mark a hosted CI check as executed based on local tests.

## Verification matrix

| Change | Required observable evidence |
|---|---|
| SEO editor | Save all fields, reload from persistence, build, inspect escaped emitted tags; reject malformed schema/extra metadata |
| Schema | Parse JSON-LD, test script-boundary injection, inspect visible factual correspondence, use relevant validators |
| Hierarchy | Test missing/cyclic parents, category order, audience switching and child routes; ensure drafts absent from public exports |
| Redirects | Actual 301/308 and destination, collision/loop rejection, query behavior and static-host configuration |
| AI edits | Allowlisted draft patch, revision/diff, malformed/provider-error handling, no unauthorized publication |
| Permissions | Editor cannot invoke admin-only mutations even by calling the API directly |
| Leads | Valid submission persists once; invalid/spam input rejected; notification failures retry without losing the lead |
| Performance | Mobile screenshot plus trace/network evidence with conditions, selected image variant, overflow and interaction checks |
| Publishing | Build artifact ID matches promoted release; rollback and asset coherence; anonymous protected-route denial when private |

## Deployment invariants

Verify provider identity/workspace/project/service/environment using the credential intended for that target before changing resources. A workspace-scoped token can fail an account-wide CLI identity call while still working through scoped APIs; do not silently fall back to a logged-in account. Record nonsecret target identifiers locally, keep secrets out of Git/logs, and verify resulting service URLs.

Password protection must cover HTML, previews, assets, media and APIs as intended. Separate site-preview access from CMS role authorization. Keep private cache behavior and noindex headers consistent. Publishing a content release does not grant permission to make a private site public or delete an older project.

After deployment, inspect the live HTML and form path, authenticate to the CMS as permitted, verify the active build, and test anonymous denial. Report missing email/AI credentials or unfinished content honestly. Public launch/indexing is a distinct transition when staging was requested.
