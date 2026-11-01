# Placement and accessibility

The accent works by being rare (isolation effect, pre-attentive pop-out). Every rule here protects that rarity, or makes sure the accent never becomes the only way information gets across.

## Placement map

| Element | Accent? | How |
|---|---|---|
| Primary CTA (one per view) | **Yes** | `accent` fill, `on-accent` label, `accent-hover` / `accent-active` states |
| Secondary / tertiary buttons | No | Outline in `border-strong`, `text` label, or a Support fill |
| One headline word or phrase | **Yes, one** | `accent` as text only where `analyze` says it passes (3:1 is enough at ≥ 24px or ≥ 18.66px bold) |
| Badge / "New" pill / tag | **Yes, one** | `accent-soft` background + `accent-soft-text` |
| Focal glow, rim light, illustration highlight | **Yes, small** | Blur or gradient of the accent, kept behind the focal object |
| Chart: one series or the key data point | **Yes, one** | See Data visualisation |
| Active nav item / current selection / selected row | **Yes** | Indicator bar or `accent-soft` row, plus a non-colour cue (weight, icon, `aria-current`) |
| Focus ring | Yes | `focus-ring`: 2px outline, 2px offset, ≥ 3:1 on the surface |
| Links in body copy | No | `brand-text` with an underline |
| Headings, icons, dividers, borders | No | Neutrals or Support |
| Body text, paragraphs | **Never** | `text`, `text-muted` |
| Section / page / card backgrounds | **Never** | Mood, Support, `surface-raised` |
| Several CTAs side by side | **Never** | One accent CTA; demote the others |
| Error, warning, success messages | **Never** | `danger` / `warning` / `success` with an icon and text |

Area budget: about 3–10% of a viewport is typical. A single CTA on a long page can be under 1%, and that's fine. Over 15% is sprawl; over 30% means the accent has become a base colour. Measure on a screenshot with `python3 scripts/accent.py coverage shot.png ACCENT`. Check the hover-state hex too if the screenshot shows hover.

## States (derived, same hue)

`tokens` derives every state from the accent's OKLCH hue, so states never introduce a new hue:

- **hover / active**: lightness moves ±0.05 / ±0.10. The script first moves away from the page (stronger fill), but only if the label keeps 4.5:1; otherwise it moves the way that raises label contrast. If a state drops under 3:1 against the page, a note says so. That's acceptable for a transient state of a labelled button, not for a button whose fill is its only boundary.
- **soft**: a 16% OKLab mix of the accent into the surface, used for badge and selection backgrounds. `accent-soft-text` is the accent hue, darkened or lightened until it reaches 4.5:1 on that soft tint.
- **disabled**: a 35% mix with chroma cut to 40%, plus a muted label. WCAG exempts disabled controls from contrast, but signal the state with `disabled` / `aria-disabled` and the cursor, not with colour alone.
- **on-accent**: the script picks the label colour (a tinted near-black or near-white, falling back to pure black or white) with the best contrast that passes 4.5:1, and checks it against hover and active too.

## Light and dark mode

- **Same hue, adjusted lightness.** `tokens --mode light|dark` keeps the hue and moves only lightness, as far as needed for 3:1 against that mode's surface. It keeps as much chroma as the sRGB gamut allows, and notes the change, e.g. `accent lightness -0.070 (#FE8500 -> #DF7400)`.
- **Surface choice:** `auto` uses BASE1 as the page. `light` uses the lighter base if L ≥ 0.9, otherwise a derived near-white tinted with the base hue. `dark` uses the darker base if L ≤ 0.40, otherwise a derived near-black.
- Generate both modes and scope them: `--selector ':root'` for one and `--selector '[data-theme=dark]'` for the other, or wrap one in `@media (prefers-color-scheme: dark)`.
- On dark surfaces a fully saturated accent can glow and vibrate. If it looks harsh, cut chroma by 10–20% and run `analyze` again.

## Data visualisation

- **One highlighted series or data point in the accent; everything else in base tints.** Use tints of Support blended toward the surface, or neutral tints when Support and the surface clash in hue (blending complementary hues makes mud).
- Label the highlighted bar or series directly (value plus name). Don't rely on a legend swatch.
- The highlight mark needs ≥ 3:1 against the chart background (WCAG 1.4.11). Neighbouring marks should differ by lightness, not only hue.
- If the chart needs several categorical colours, it's a categorical palette problem, not an accent problem. Keep the accent out of it, or use it only for the single series under discussion.

## Semantic colour collisions

The accent must not be mistaken for a status. `analyze` WARNs when the accent hue is within 30° of error red (27°), warning amber (70°) or success green (150°). `tokens` then:

1. moves the status hue to the far edge of its allowed band (danger 15–40°, warning 58–90°, success 138–168°);
2. sets status chroma ≤ 0.14 and below the accent's, so status colours stay quieter;
3. makes each status colour pass 4.5:1 as text on the surface;
4. notes when the gap is still under 30°. Then the status must be carried by its icon and its words ("Error: card declined"), never by hue alone.

For example, a pink or crimson accent next to error red: move the error hue toward orange-red, darken it, always show an icon, and never use the accent for destructive buttons.

## Colour-vision deficiency

About 1 in 12 men and 1 in 200 women have a red-green deficiency. `analyze` simulates deuteranopia and protanopia (Machado et al. 2009, severity 1.0) and WARNs when the accent lands within OKLab ΔE 0.10 of a base. In the reel set, hot pink on sky blue does this (ΔE 0.090 under deuteranopia).

Mitigations, in order:

1. Keep a lightness difference between the accent and the colour around it. Lightness survives every type of colour-vision deficiency.
2. Add a non-colour cue: a label, icon, weight, underline, shape or position.
3. Pick an accent with more lightness contrast against the base.

Blue-yellow (tritan) deficiency is rare and not simulated. Blue + yellow accents still differ strongly in lightness.

## WCAG 2.2 thresholds (as used by the script)

| Content | Minimum | Criterion |
|---|---|---|
| Body text, labels, placeholder text | 4.5:1 | 1.4.3 Contrast (Minimum) |
| Large text: ≥ 24px regular or ≥ 18.66px bold | 3:1 | 1.4.3 |
| UI component boundaries, focus indicators, icons that convey meaning, chart marks | 3:1 against adjacent colours | 1.4.11 Non-text Contrast |
| Disabled controls, pure decoration, logos | no requirement | exemptions in 1.4.3 / 1.4.11 |
| Information shown by colour | must also exist in a non-colour form | 1.4.1 Use of Color |
| Focus indicator | visible; ≥ 3:1 is the practical bar (2.2 AAA 2.4.13 asks for a 2px outline at 3:1) | 2.4.7 / 2.4.13 |

Contrast is the WCAG 2.x ratio `(L1 + 0.05) / (L2 + 0.05)` on relative luminance (sRGB linearised with the 0.04045 threshold). It's compared unrounded. The script truncates when printing, so "4.50:1" is never a rounded-up 4.499. A filled button whose label passes 4.5:1 on the fill doesn't also need its fill to reach 3:1 against the page, because the label identifies the control. Icon-only buttons and outline-free toggles do need it.

## Colour space notes

Hue, chroma and lightness are measured in **OKLCH** (Björn Ottosson's OKLab), which is perceptually even enough that "90° apart" means roughly the same visual jump anywhere on the wheel. HSL hue angles don't: blue→pink looks big but measures only 63–84° in OKLCH. Out-of-gamut colours are brought into sRGB by reducing chroma at fixed lightness and hue, so a clipped colour keeps its identity. Near-neutral colours (C < 0.03, or C < 0.06 when L < 0.15 or L > 0.97) have no meaningful hue and are ignored in hue checks.
