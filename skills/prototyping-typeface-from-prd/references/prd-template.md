# PRD template for a typeface

Write `docs/PRD.md` from this skeleton before drawing anything. Replace every `{{...}}`; delete
the `> note` blocks. Keep the 22 section headings and their numbering: `build_specimen.py` and
`project.py` read the H1, the header table, the "Mandated glyphs" blocks, the "Weights and axes"
table and "Appendix A" from this structure (see the notes at the end).

The defaults given are for a geometric sans on a 1000 UPM grid, the family this skill was built
on. A humanist or grotesque brief changes the numbers, not the sections.

---

```markdown
# {{FAMILY}} — Product Requirements Document

| Field | Value |
|---|---|
| Product | {{FAMILY}} typeface family |
| Owner | {{OWNER}} |
| Version | PRD v1.0, {{DATE}} |
| Status | Draft for review |
| Classification | {{e.g. Geometric sans-serif, slightly condensed, medium-weight default}} |

---

## 1. Summary

{{One paragraph: lineage (the faces it descends from), construction (circles and straights,
monoline or modulated), proportion (narrow / normal / wide), default-weight feel. This paragraph
becomes the specimen's lede.}}

{{N}} letterforms are fixed by brief and are non-negotiable identity markers:

1. **{{glyph}}** {{one sentence of geometry, e.g. "is fully straight: a vertical stem with a horizontal crossbar, flat-cut at the baseline, no tail or hook".}}
2. **{{glyph}}** {{...}}
3. **{{glyph}}** {{...}}

## 2. Problem and opportunity

{{Why an existing face does not do: one bullet per reference face and its failing.}}

- {{Reference A}} is {{wide / light at Regular / proprietary / humanist ...}}.
- {{Reference B}} ...

{{One sentence: what this face changes.}}

## 3. Goals

| # | Goal | Measure |
|---|---|---|
| G1 | Recognisably {{geometric}}: round glyphs built on the same ellipse | Visual audit against construction grid |
| G2 | {{Proportion}}: average lowercase advance {{4 to 8}} percent {{less}} than {{reference}} at equal x-height | Width comparison over the pangram set |
| G3 | Default instance is {{Medium (wght 500)}}, stem about {{108}} units per 1000 | Measured stem at the default master |
| G4 | Mandated glyphs ({{t j g}}) hold at every weight | Glyph review checklist signed off per master |
| G5 | Usable from {{11}} px UI text to {{200}} pt display | Rendering review at 11, 13, 16 px |
| G6 | {{Character coverage target}} | {{percent of a named glyph set}} |
| G7 | Variable font plus static instances | Single wght axis {{300 to 700}}, {{5}} static instances |

## 4. Non-goals

- No italic in v1 ({{v2 follow-up}}); brand usage must not rely on faux italics.
- No optical size axis in v1.
- No width axis; the proportion is fixed.
- No {{Cyrillic, Greek, ...}} in v1; metrics and spacing conventions must not prevent them later.
- No icons, emoji or dingbats.

## 5. Anti-goals

These would make the face a failure even if every goal is technically met:

- {{The opposite of each mandated glyph, e.g. "Any curvature on the t stem".}}
- Drifting into {{humanist}} territory to fix spacing problems; spacing problems are solved with spacing and kerning.
- {{Over-wide / over-tight}} setting that reads like {{reference}}.
- A default weight that reads {{light}} on a white UI at 14 px.

## 6. Target users and use cases

| User | Use case | What they need |
|---|---|---|
| Brand and marketing | Wordmarks, headlines, decks | Distinctive {{identity glyphs}}; tight display spacing; strong Bold |
| Product designers | Web and mobile UI, 12 to 24 px | Even texture, clear i l 1 I distinction, tabular figures |
| Developers | Design tokens, web font loading | WOFF2 variable, small file size, stable feature names |
| Content writers | Long-form reading | Comfortable x-height, open apertures |

## 7. Design principles

1. **{{Compass and ruler.}}** Every curve derives from a circle or an ellipse with a fixed ratio; every straight is a true vertical or horizontal unless legibility demands otherwise.
2. **{{Near-monoline.}}** Horizontal strokes are {{4 to 6}} percent thinner than verticals to appear optically equal.
3. **{{Flat cuts.}}** Terminals are cut flat, horizontally or vertically, never at an angle.
4. **{{Economy of width.}}** Round forms are ellipses at roughly {{0.90}} width-to-height.
5. **{{Presence by default.}}** The recommended default is {{Medium 500}}.
6. **Legibility over purity.** Where pure geometry hurts reading (I vs l, rn vs m, a at small sizes) legibility wins and the deviation is documented.

## 8. Metrics and proportions

All values are font units on a 1000 units-per-em grid, measured at the default {{Medium}} master. Overshoot applies to round forms.

| Metric | Value | Notes |
|---|---|---|
| Units per em | 1000 | |
| Cap height | {{700}} | |
| x-height | {{510}} | {{73}} percent of cap height |
| Ascender (b d f h k l) | {{750}} | {{50}} above cap height |
| Descender (g j p q y) | {{-230}} | |
| t height | {{650}} | Shorter than ascender, taller than x-height |
| Round overshoot | {{12}} | Top and bottom of o, c, e, s, and caps O, C, G, Q, S |
| Vertical stem, {{Medium}} | {{108}} | |
| Horizontal stroke, {{Medium}} | {{102}} | {{94}} percent of vertical |
| Vertical stem, {{Light 300}} | {{62}} | |
| Vertical stem, {{Bold 700}} | {{158}} | |
| Lowercase o outer width | {{480}} | Height {{534}} including overshoot; ratio {{0.90}} |
| Capital O outer width | {{660}} | Height {{724}} including overshoot; ratio {{0.91}} |
| Dot diameter (i, j, punctuation) | {{118}} | Round; {{109}} percent of stem |
| Dot clearance above x-height | {{70}} | |
| Default sidebearing, straight stem | {{70}} | |
| Default sidebearing, round | {{40}} | |
| Typo line gap | 0 | hhea and OS/2 metrics set equal, USE_TYPO_METRICS on |
| Ascender / descender (metrics) | {{950 / -250}} | Leaves room for diacritics and the descender |

Width targets for key glyphs (advance width including sidebearings, {{Medium}}):

| Glyph | Advance | Glyph | Advance |
|---|---|---|---|
| n | {{560}} | H | {{700}} |
| o | {{560}} | O | {{740}} |
| i | {{248}} | I | {{248}} |
| t | {{380}} | T | {{580}} |
| j | {{248}} | J | {{500}} |
| g | {{560}} | G | {{740}} |
| a | {{540}} | A | {{660}} |
| s | {{480}} | S | {{580}} |
| e | {{540}} | E | {{560}} |
| m | {{860}} | M | {{860}} |

## 9. Glyph specifications

### 9.1 Mandated glyphs

**{{t}} ({{straight}})**
- {{Stem: width, from y = ... to y = ..., cut flat at both ends.}}
- {{Crossbar: y range, extent beyond each stem edge, total width.}}
- {{What must never appear: tail, hook, spur, curve.}}
- {{Sidebearings.}}

**{{j}} ({{straight}})**
- {{...}}

**{{g}} ({{single-storey, open tail}})**
- {{Bowl: ellipse size, alignment, how it closes on the stem.}}
- {{Stem: width, x, y range.}}
- {{Tail: where it springs, radius, where it flattens, terminal y and x.}}
- {{Clearances that keep it open, e.g. "at least 160 units between the tail terminal and the bowl".}}
- {{Boldest-master constraint, e.g. "tail inner radius stays at least 60 units".}}

### 9.2 Lowercase

| Glyph | Construction |
|---|---|
| a | {{Double-storey by default ...; single-storey as `ss01`.}} |
| b d p q | {{Shared ellipse bowl with a straight stem; extents.}} |
| c e | {{Same ellipse as o; terminal cuts; e bar height.}} |
| f | {{Stem height, arc radius, crossbar geometry shared with t.}} |
| h m n u | {{Arched forms from half-ellipses on straight stems.}} |
| i l | {{...}} |
| k | {{Stem; arm and leg meeting height.}} |
| r | {{Stem with a short arc branch; terminal.}} |
| s | {{Two stacked arcs, flat vertical cuts, spine angle.}} |
| v w x y z | {{Straight diagonals, flat cuts; y descender.}} |

### 9.3 Uppercase

- O C G Q built on the {{660 x 724}} ellipse. {{G bar, no spur.}}
- A V W X Y Z M N K are straight-sided with mitred apexes trimmed flat to a width of {{1.1}} stems.
- B D P R have bowls derived from the capital ellipse, sliced by a straight stem.
- E F L T H have strokes placed at geometric mid-heights, then optically corrected upward by {{10}} units.
- I is a plain stem. {{Serifed alternate `ss02`?}}
- J {{descends / sits on the baseline}} with {{...}}.
- S is a wider version of lowercase s on the capital ellipse.

### 9.4 Figures

- Default: proportional lining figures, height {{700}}.
- `tnum`: tabular lining figures on a {{560}} advance.
- `onum`: oldstyle figures.
- 1 {{flag and base rules; `ss03` alternate}}.
- 0 is an ellipse; `zero` provides a slashed zero.
- {{4 open or closed; 7 crossbar; 6 and 9 forms and terminal cuts.}}

### 9.5 Punctuation and symbols

- Period, comma, colon, semicolon, dots on i and j, and quotation marks share the round dot family ({{118}} diameter at {{Medium}}).
- Comma and quotation tails are {{short straight diagonals, flat cut}}.
- Hyphen, en dash, em dash sit at y = {{265}} (centre of x-height), thickness {{102}}.
- Parentheses and brackets use the capital ellipse radius; brackets are square.
- Currency: {{$ € £ ¥ ₹ ¢}}.
- Arrows: {{left, right, up, down}}, built from the diagonal of v.
- @ uses the {{single-storey}} a inside the ellipse.

## 10. Character set

| Set | Coverage | Count (approx) |
|---|---|---|
| Basic Latin | U+0020 to U+007E | 95 |
| Latin-1 Supplement | U+00A0 to U+00FF | 96 |
| Latin Extended-A | U+0100 to U+017F | 128 |
| {{Further blocks or "deferred to v1.1"}} | | |
| General punctuation | Dashes, quotes, bullet, ellipsis, dagger, per mille | 24 |
| Currency | {{...}} | {{9}} |
| Letterlike and math | © ® ™ ° ± × ÷ − ≈ ≠ ≤ ≥ µ ¶ § | 18 |
| Arrows | ← → ↑ ↓ | 4 |
| Figures | lining, tabular, oldstyle, superior, inferior, fractions | 70 |
| Diacritics | {{list}} | {{24 spacing + 12 combining}} |

Target total: approximately {{520}} glyphs per master in v1.0.

## 11. OpenType features

| Tag | Behaviour |
|---|---|
| kern | Class-based kerning, target under {{1,200}} pairs after class reduction |
| liga | {{fi, fl, ffi, ffl}}; ligatures must not break a mandated glyph's rule |
| calt | {{Contextual spacing for repeated straight stems}} |
| tnum / pnum | Tabular and proportional figures |
| onum / lnum | Oldstyle and lining figures |
| zero | Slashed zero |
| frac | Pre-built ½ ¼ ¾ plus arbitrary fractions |
| sups / subs / numr / dnom | Superior and inferior figures |
| case | Case-sensitive punctuation for all-caps settings |
| ss01 | {{Single-storey a}} |
| ss02 | {{Serifed I}} |
| ss03 | {{1 with base}} |
| salt | {{The ss01 + ss02 set}} |
| locl | {{Romanian comma-below, Dutch ij, Catalan punt volat, Turkish dotless i}} |
| mark / mkmk | Anchor-based diacritic placement |

## 12. Weights and axes

| Instance | wght | Vertical stem | Intended use |
|---|---|---|---|
| Light | 300 | {{62}} | Large display, captions on dark |
| Regular | 400 | {{86}} | Long-form body text at 16 px and above |
| Medium (default) | 500 | {{108}} | UI body, buttons, navigation, default brand text |
| SemiBold | 600 | {{132}} | Subheads, emphasis |
| Bold | 700 | {{158}} | Headlines, wordmarks |

- Drawn masters: {{Light 300 and Bold 700; Medium is the design origin and is checked as an instance}}.
- Widths grow with weight by no more than {{6}} percent from the lightest to the boldest master.
- The variable font's default instance is {{Medium 500}}.

## 13. Spacing and kerning

- Spacing is set on straight stems first (n, H), then rounds (o, O), then everything derived.
- Default letter-spacing: n-to-n gap approximately {{1.6}} stems at {{Medium}}.
- Display tracking guidance: {{-1 percent at 48 pt and above, 0 at text sizes, +2 percent at 11 to 12 px}}.
- Kerning classes for round left, round right, straight left, straight right, diagonal, and {{any mandated glyph that needs its own class, e.g. the tail-less t against rounds}}.

## 14. Rendering, hinting and technical requirements

| Requirement | Specification |
|---|---|
| Source format | UFO3 per master plus a designspace file |
| Build | fontmake, reproducible via one `make build` command |
| Variable output | TTF with gvar, HVAR, STAT, fvar; WOFF2 of the same |
| Static output | OTF (CFF) and TTF for each instance; WOFF2 for each |
| Hinting | ttfautohint for TTF statics and variable, control file for {{i, j, t stems}}; CFF unhinted |
| Vertical metrics | hhea, typo and win metrics aligned; line height 1.2 em renders identically on macOS, Windows, Android, iOS |
| Family naming | Family "{{FAMILY}}"; RIBBI static names plus typographic names; variable named "{{FAMILY}} Variable" |
| File size | Variable WOFF2 under {{60}} KB for the Latin set |
| Validation | fontbakery universal and googlefonts profiles pass with zero FAILs |
| Licence | {{SIL Open Font License 1.1 (placeholder; see Open Questions)}} |
| Vendor ID | {{four characters, to be registered}} |

## 15. Deliverables

1. Source repository: `sources/`, `fonts/`, `docs/`, `specimen/`, `tools/`.
2. Variable font: `{{FAMILY}}[wght].ttf` and `.woff2`.
3. Static fonts: {{5}} OTF, {{5}} TTF, {{5}} WOFF2.
4. Specimen website showing construction grid, mandated glyphs, full character set, weight toggle and sample settings.
5. Usage guidelines: recommended sizes, tracking, weight pairing, CSS snippet with `font-feature-settings` examples.
6. Glyph review checklist signed per master.

## 16. Milestones

| Phase | Scope | Exit criteria |
|---|---|---|
| M0 Spec and samples | This PRD; sample glyphs rendered as SVG on the construction grid | Stakeholder approval of {{mandated glyphs}} and overall proportion |
| M1 Core lowercase | a to z, default master, spaced | Pangram sets read evenly at 14 px and 72 pt |
| M2 Core uppercase and figures | A to Z, 0 to 9, basic punctuation | Mixed-case paragraphs and tables pass review |
| M3 Weight masters | Light and Bold masters, interpolation check | Default instance matches M1 drawings within 4 units |
| M4 Extended set | Latin-1, Extended-A, diacritics, currency, features | Fontbakery passes; locl and mark features tested |
| M5 Hinting and engineering | ttfautohint, metrics, naming, STAT | Renders cleanly at 11 to 16 px on Windows and macOS |
| M6 Specimen and release | Website, docs, licence, v1.0 tag | Public release candidate; sign-off |

## 17. Quality assurance

- **Construction audit:** every round glyph overlaid on the master ellipse; deviation beyond {{6}} units requires a documented reason.
- **Mandated glyph check:** {{automated assertion per mandated glyph, e.g. "t and j contours contain no off-curve points in the stem region".}}
- **Text tests:** pangrams, UI strings (Save, Cancel, Settings, 12:45, $1,234.56), accented strings, all-caps settings.
- **Size tests:** 11, 12, 13, 14, 16, 20, 24, 32, 48, 96 px screenshots across platforms.
- **Confusables:** I l 1 | ; O 0 ; rn m ; cl d ; tested at 12 px.
- **Diff review:** every change to sources includes a before-and-after proof.

## 18. Success metrics after release

| Metric | Target |
|---|---|
| Adoption | {{...}} |
| Fontbakery | Zero FAILs on the googlefonts profile |
| Web performance | Variable WOFF2 under {{60}} KB, no layout shift when swapped from the fallback stack |
| Legibility | No confusable-pair complaints in the first 90 days |
| Recognition | Blind test: users identify {{FAMILY}} from the word "{{justify}}" at {{80}} percent against {{references}} |

## 19. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| {{Mandated glyph}} spaces poorly next to rounds | Uneven texture | Dedicated kerning class; test "{{to ta te}}" early |
| {{Mandated glyph}} is mistaken for {{...}} in small UI | Legibility | {{...}} |
| {{Open-tail g collapses at Bold}} | Dark spot in text | {{Enforce minimum tail inner radius 60; widen tail terminal at Bold}} |
| Narrow proportions make Light look stringy | Weak display Light | {{Allow Light to be 2 percent wider}} |
| Interpolated default drifts | Default weight off-brief | Add a master if any stem is off by more than 4 units |
| Resemblance to {{reference}} | Originality concern | Document differences; legal review before release |

## 20. Open questions

| # | Question | Default if unanswered |
|---|---|---|
| Q1 | Licence: open or proprietary? | {{OFL 1.1}} |
| Q2 | {{Default a: double-storey or single-storey?}} | {{Double-storey, single-storey in ss01}} |
| Q3 | {{...}} | {{...}} |

## 21. Appendix A — Sample strings for review

- `Hamburgefonstiv` and `HAMBURGEFONSTIV`
- `The quick brown fox jumps over the lazy dog`
- `{{a string that exercises every mandated glyph, e.g. justify tight jet gentle gadget jogging}}`
- `Sphinx of black quartz, judge my vow`
- `{{FAMILY}} 0123456789 $1,234.56 12:45`
- `Save Cancel Settings Done 12:45`
- `Il1 O0 rn m cl d ij lj to ta te`
- `Zażółć gęślą jaźń · Příliš žluťoučký kůň · Ærøskøbing`

## 22. Appendix B — Reference comparison

| Face | Width | Default weight feel | {{t}} | {{j}} | {{g}} | {{FAMILY}} difference |
|---|---|---|---|---|---|---|
| {{Futura}} | Wide | Light | Straight stem, curved base | Hooked | Single-storey, hooked | {{...}} |
| {{Gill Sans}} | Normal | Regular | Curved tail | Hooked | Double-storey | {{...}} |
| {{Product Sans}} | Normal | Regular | Curved tail | Hooked | Single-storey open tail | {{...}} |
| {{Jost}} | Wide | Light-Regular | Straight stem, curved base | Hooked | Single-storey | {{...}} |
```

---

## Choosing the numbers

**x-height.** 65 percent of cap height is the classic geometric proportion (Futura); 70 to 75
percent reads better in UI at 12 to 16 px and is the right default for a product face (the
reference family uses 510 / 700 = 73 percent). Above 76 percent ascenders get short and b d h k l
lose distinction from the x-height band.

**Ascender and descender.** Ascender 40 to 60 above cap height so that l and I differ; descender
deep enough that g p q y keep an open counter at the boldest weight. A fixed descender (-230) and
a minimum tail clearance can conflict at Bold: decide in the PRD which one bends (the reference
lets the tail terminal thicken but never moves the descender) and write the rule down here, not in
the generator.

**Stem per weight.** Set the default stem as a fraction of the em: 0.10 to 0.11 for a confident
UI default, 0.085 for a classic Regular. Lightest master roughly 0.55 to 0.6 of the default, boldest
roughly 1.45 to 1.5 of it; beyond 0.16 em the lowercase counters of a e s close at a 480-wide
bowl. Horizontal strokes 0.94 of the stem; dots 1.09 of the stem.

**Widths.** Pick the lowercase bowl outer width (480 for "slightly condensed", 500 to 520 for
normal) and derive: o advance = bowl + 2 × round sidebearing; n advance = o advance; i advance =
stem + 2 × straight sidebearing. Capital O about 1.35 × the lowercase bowl. Let widths grow at
most 6 percent from lightest to boldest so weight changes in UI do not reflow violently.

**Mandated glyphs.** Describe them with coordinates (stem x, y ranges, radii, terminal positions)
and with the clearances that must survive at the boldest weight. "As in the reference image" is
not a specification; the generator needs numbers.

## What the scripts read from this file

- `project.py`: the H1 (`<Family> — ...`), the header table rows Owner / Version / Classification,
  and the "Weights and axes" table (style name in the first column, "Vertical stem" column).
  `font.json` overrides any of these.
- `build_specimen.py`: the first paragraph under "Summary" (hero lede), each `**glyph (subtitle)**`
  block with its bullets under "Mandated glyphs" (one card each; the glyph token must be a glyph
  name or a character in the generator's charmap), and the backticked bullets under "Sample
  strings" (sample settings; strings mostly outside the drawn set become notes).
