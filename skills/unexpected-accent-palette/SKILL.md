---
name: unexpected-accent-palette
description: Use when choosing or fixing a colour palette for a website, app, brand, slide deck or poster; when a two-colour brand or design feels flat, generic, forgettable, basic or "fine but boring"; when picking a CTA, highlight or accent colour; or when writing colour tokens, a theme, or light/dark colour variables.
---

# Unexpected accent palette

**Two base colours set the mood. One unexpected, high-chroma accent, used sparingly on the thing to click or the focal point, makes the design memorable.** You don't need more colours, you need one that surprises.

Why: the **isolation (von Restorff) effect** makes the one item that differs get noticed and remembered, and **pre-attentive pop-out** lets a lone distant hue be found at a glance. Both need the accent to stay rare. Every extra use or extra hue weakens it.

## Roles: 2 + 1

| Role | What it is | Typical area |
|---|---|---|
| **Mood** (BASE1) | dominant base, usually the page background | most of the view |
| **Support** (BASE2) | second base: brand surfaces, secondary buttons, links, chart series | some |
| **Accent** | one hue far from both bases (its tints and shades are allowed) | ~3–10% of a viewport |

Neutrals derived from the bases and status colours (error, warning, success) aren't extra hues. Keep them quieter than the accent.

## Workflow

Run scripts from this skill's folder: `python3 scripts/accent.py <command> ...` (Python 3.9+, stdlib only).

1. **Identify the base pair** from the brief, brand, CSS or screenshot. BASE1 (first argument) is the Mood/page background. **Keep the user's colours.** Change a base only where a needed use fails WCAG, and then only its lightness, minimally, saying so. `tokens` does this and records it.
2. **Analyze:** `analyze BASE1 BASE2 [ACCENT] [--extra HEX ...]`. It prints OKLCH, hue distances, a contrast matrix and PASS/NOTE/WARN/FAIL checks. Pass the design's other colours to `--extra` to catch a second accent hue. Exit 1 means a FAIL.
3. **No accent yet, or it FAILs:** `suggest BASE1 BASE2 [--mode light|dark] [--count 6]` gives deterministic, ranked candidates.
4. **Pick one with reasons:** hue distance, temperature flip, chroma, contrast, status-colour clearance, brand fit. Candidates sit at the gamut edge. Softening chroma 10–20% is fine; run `analyze` again after.
5. **Tokens:** `tokens BASE1 BASE2 ACCENT --mode light` and `--mode dark` (`--format css|tailwind|json`, `--selector '[data-theme=dark]'`). Use its hexes as they are. They cover hover, pressed, soft, disabled, on-accent, focus and status colours, with every text pair verified.
6. **Place** the accent using the rules below.
7. **Verify by looking.** `preview BASE1 BASE2 ACCENT -o <project>/palette-preview.html` renders the base pair alone vs. with the accent. On a screenshot of the real page, `coverage shot.png ACCENT` (needs ffmpeg) warns at 0% or over 15% and fails over 30%.
8. **Report** in the format below.

**Never compute contrast by hand** or write "≈4.6:1, please confirm in a checker". Paste the script's output.

## Quick reference

| Check | Target | Where |
|---|---|---|
| Hue distance (OKLCH) | ≥ 90° from each chromatic base. 45–90° passes only with a warm/cool flip. Under 45° FAILs. Near-neutral bases are ignored | `analyze` hue-distance |
| Temperature | Cool pair → warm accent, or the reverse | temperature |
| Chroma | ≥ 0.12, ideally above the bases. Under 0.07 isn't an accent | chroma |
| Accent fill vs page | ≥ 3:1 for icon-only controls, focus rings and chart marks. A labelled button only needs its label to pass | accent-fill |
| Label on accent | ≥ 4.5:1, colour chosen by the script | `on-accent` token |
| Accent as text | Only where it passes: 4.5:1 for body text, 3:1 for ≥ 24px (or ≥ 18.66px bold) | accent-as-text |
| Status colours | ≥ 30° from the accent hue, quieter, always with icon + text | semantic, `tokens` |
| Area | ~3–10% of the view. Over 15% is sprawl | `coverage` |

## Placement

**Accent goes on:** the primary CTA (one per view), one highlighted word or badge, a focal glow, one chart series or key data point, the active state or current selection, and the focus ring.

**Never on:** body text, large backgrounds or sections, several competing CTAs, decoration everywhere (every icon, border or heading), status messages, or anything that signals by colour alone.

States, dark mode, data viz, colour vision and WCAG: [placement-and-accessibility.md](references/placement-and-accessibility.md). The nine reel palettes, measured: [examples.md](references/examples.md).

## Red flags: stop and fix

- **The "accent" is the base hue again**, e.g. #2F6BFF beside #09318D (1° apart). `analyze` FAILs it.
- **The CTA is in a base colour** while the accent decorates something else.
- **You replaced the user's base pair.** The pair sets the mood; the fix is the accent.
- **There's a fourth hue** (a violet glow, teal icons) beside the accent. `--extra` FAILs it.
- **Contrast is estimated** or "to be verified".
- **The accent is on two competing buttons**, on paragraphs, or used as a section background.
- **The error red can't be told apart** from a red or pink accent.

## Report format

1. **Palette table:** `| Role | Hex | OKLCH | Area | Use |` for Mood, Support, Accent, the tokens you used and the status colours.
2. **Why this accent:** hue distance, temperature and chroma, with numbers from `analyze`.
3. **Where the accent goes:** list every element, plus the `coverage` result if measured.
4. **Contrast:** paste the script's lines verbatim (analyze checks and the tokens contrast block, for each mode made).
5. **Deliberately not accent:** e.g. secondary buttons, links, headings, icons, errors.
6. **Changes to the user's colours:** "none", or the token note (e.g. "accent lightness −0.070 → #DF7400 for 3:1 on #F8FAFF in light mode").
