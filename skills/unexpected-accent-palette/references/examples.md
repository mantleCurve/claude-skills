# The nine reel palettes, measured

Source: three short design reels. Each one shows a website hero in a two-colour base pair ("looks good / clean / solid / basic / forgettable"), then adds a third swatch, and the hero gains the accent. Hexes are as printed on the swatch cards. #5 and its accent had typos on the cards and were corrected from the pixels.

## Palettes

| # | Base 1 (Mood) | Base 2 (Support) | Accent | Accent used on | Claimed effect |
|---|---|---|---|---|---|
| 1 | Sky Blue #0593C6 | White #FCFFFF | Hot Pink #D83995 | motion-blur figure in hero | stops the scroll |
| 2 | Midnight Black #02070A | Electric Blue #0297DE | Cantaloupe #FC734D | light-burst glow, UI cards | looks expensive |
| 3 | Deep Blue #09318D | Pure White #FFFFFF | Bubblegum Pink #FD91CC | CTA, badge, donut chart | ready to deploy |
| 4 | Charcoal #21232E | Royal Blue #105BFF | Tangerine #FE8500 | nav CTA, product shots | different vibe |
| 5 | Marshmallow #F0F0F0 | Galactic Violet #533DFB | Bubblegum Pink #FA67D0 | visor tint, CTA | looks premium |
| 6 | Aqua Jade #74FFED | Midnight Abyss #171F44 | Baby Pink #FE81D1 | CTA, network nodes | impossible to ignore |
| 7 | Mandarin #FD550A | Forest Green #015D47 | Crest Yellow #E0F354 | display type, SHOP NOW | you know where to click |
| 8 | Onyx #01010D | Electric Indigo #6331FB | Tropical Mint #88F9C0 | CTA, rim light | recognisable anywhere |
| 9 | Seal Blue #DBF2FC | Navy #072D59 | Crimson Pink #FD6E88 | CTA, gradient core | page comes together |

## Numbers from `python3 scripts/accent.py analyze BASE1 BASE2 ACCENT`

OKLCH is given as L / C / h. Δh is the accent's hue distance from each chromatic base ("–" means the base is near-neutral and its hue is ignored). "Fill" is the contrast of the accent against BASE1 / BASE2.

| # | Accent OKLCH | Δh vs B1 / B2 | Temp (pair → accent) | Accent C vs max base C | Fill vs B1 / B2 | Label on accent | Non-PASS checks |
|---|---|---|---|---|---|---|---|
| 1 | 0.61 / 0.212 / 350 | 118° / – | cool → warm | 0.212 > 0.127 | 1.21 / 4.22 | #000 4.93 | base-text, accent-fill, colour-vision (deutan ΔE 0.090) |
| 2 | 0.71 / 0.176 / 36 | – / 156° | cool → warm | 0.176 > 0.148 | 7.42 / 1.18 | #000 7.69 | semantic (9° from error red) |
| 3 | 0.79 / 0.147 / 347 | 84° / – | cool → warm | 0.147 ≈ 0.158 | 5.50 / 2.07 | #000 10.09 | none above NOTE |
| 4 | 0.74 / 0.182 / 55 | – / 153° | cool → warm | 0.182 < 0.252 | 6.37 / 2.16 | #000 8.56 | base-text 2.94, semantic (15° from warning) |
| 5 | 0.73 / 0.212 / 340 | – / 63° | cool → warm | 0.212 < 0.263 | 2.32 / 2.30 | #000 7.91 | accent-fill |
| 6 | 0.77 / 0.177 / 343 | 159° / 72° | cool → warm | 0.177 > 0.124 | 1.86 / 7.04 | #000 9.27 | accent-fill |
| 7 | 0.92 / 0.179 / 116 | 77° / 54° | mixed → transitional | 0.179 < 0.215 | 2.64 / 6.44 | #000 17.11 | hue-distance WARN, base-text 2.43, accent-fill |
| 8 | 0.90 / 0.132 / 160 | – / 123° | cool → cool | 0.132 < 0.270 | 16.17 / 4.86 | #000 16.35 | base-text 3.32, semantic (10° from success) |
| 9 | 0.72 / 0.175 / 11 | – / 116° | cool → warm | 0.175 > 0.089 | 2.33 / 5.07 | #000 7.76 | accent-fill, semantic (16° from error red) |

None of the nine FAILs (this is a test case in `scripts/test_accent.py`).

## Why each one works

1. **Sky blue + white → hot pink.** It's 118° from the only chromatic base and flips temperature. Pink on sky blue is just 1.21:1, so the reel uses it on a figure (a focal point), not as a control on blue. Under deuteranopia, pink and sky blue nearly merge (ΔE 0.090). Never use colour alone for meaning here.
2. **Black + electric blue → cantaloupe.** The near-black Mood leaves blue as the only hue, and the accent sits 156° away. It's the brightest thing on a 7.42:1 dark field. Because it's close to error red, `tokens` moves danger to 15°. That's still only 21° apart, so icons and text are mandatory on errors.
3. **Deep blue + white → bubblegum pink.** Only 84° in OKLCH (blue→pink looks farther than it measures), but the warm/cool flip carries it. 5.50:1 on deep blue means it's a strong CTA fill with a black label (10.09:1).
4. **Charcoal + royal blue → tangerine.** Royal blue (C 0.252) is *more* saturated than the accent, so the pop comes from the 153° hue jump and the lightness (L 0.74 vs 0.55). Keep royal blue off the CTA. Blue text on charcoal is 2.94:1, so it's a fill, not a text colour; `tokens` derives `brand-text` #5F94FF for links.
5. **Off-white + violet → bubblegum pink.** 63° plus a flip. Pink on #F0F0F0 is 2.32:1, fine for a labelled button (black label 7.91:1) but not for an icon-only control. `tokens --mode light` darkens it to #E14FB9 (−0.070 L, same hue) for those uses.
6. **Aqua jade + midnight → baby pink.** It's 159° from jade and 72° from the midnight blue, with a flip. On the midnight surface it reaches 7.04:1. This is a palette where Support is the real page colour, so put `#171F44` first when generating tokens.
7. **Mandarin + forest → crest yellow.** The odd one out. The base pair spans warm and cool, and the acid yellow is only 54–77° from the bases. It works through lightness (L 0.92 against 0.67 and 0.43), which is why `analyze` WARNs rather than FAILs. Don't copy this pattern as the default.
8. **Onyx + electric indigo → tropical mint.** 123° from indigo but no temperature flip (all cool). The distance and very high lightness carry it (16.17:1 on onyx). Mint sits on top of success green, so give status colours icons and text, and shift the success hue.
9. **Seal blue + navy → crimson pink.** It's 116° from navy and flips temperature. On the pale seal blue it's 2.33:1, so the CTA label carries contrast. It's close to error red, which `tokens` moves to 40° and flags as needing icon + text.

## What the measurements changed in the method

- **Blue → pink is only 63–84° in OKLCH** (palettes 3, 5, 6), even though it reads as a big jump. So 45–90° passes when the temperature flips, and only under 45° FAILs.
- **5 of 9 accents are less chromatic than a base.** "Chroma clearly above the bases" is a preference, not a gate. Absolute chroma ≥ 0.12 is what all nine share (min 0.132).
- **Accent-on-Mood fill is under 3:1 in 5 of 9.** The reels lean on labelled buttons and focal imagery. For icon-only controls, focus rings and chart marks, use the lightness-adjusted `accent` from `tokens`.
- **4 of 9 collide with a status hue.** That's why `tokens` always emits shifted, quieter status colours.

## The two baseline failures this skill exists to prevent

| Case | What the agent did | What `analyze` says |
|---|---|---|
| #09318D + #FFFFFF, "make it memorable" | "Accent" #2F6BFF, CTA in base blue | hue-distance **FAIL**: 1° from BASE1. `suggest` tops out with yellow #FEEF00 (158°), amber #FFA400, red-orange #FF7800, then lime, pink #FD0097, red. |
| #21232E + #105BFF, "feels forgettable" | Replaced both bases, added a violet glow next to the accent, hand-computed contrast | `--extra #8B5CF6` **FAIL**: a new hue competing with the accent. The bases stay as they are; the accent is tangerine-like (`suggest`: #FEEF00, #FFA400, #FF7800, #FD0097 ...). |
