# claude-skills

Reusable skills for [Claude Code](https://claude.com/claude-code). Each skill lives in
`skills/<name>/` with a `SKILL.md` that Claude reads, plus any scripts and templates it needs.

| Skill | What it does |
|---|---|
| [`episodic-video-merge`](skills/episodic-video-merge) | Downloads and verifies numbered episodes, audits frozen tails, makes adjustable trim tests, and merges MP4s with one chapter per episode. |
| [`jev-posthog`](skills/jev-posthog) | Combines PostHog visitor behavior with Jev intent classification, CRM deduplication, and tailored follow-up drafts. |
| [`vistprint_india_photo_album_landscape`](skills/vistprint_india_photo_album_landscape) | Builds print-safe landscape photo albums with complete photo coverage, consistent ivory backgrounds, separate covers, and verified 300 DPI JPG exports for the Vistaprint India editor. |
| [`seo-skill`](skills/seo-skill) | Implement SEO/AEO-ready sites and CMS editors: nested services and locations, metadata, OG/X cards, schema, AI draft editing, mobile performance, and a tested audit-evidence gate. |
| [`travel-journey-site`](skills/travel-journey-site) | Turns a trip (a few places, or a poster) into a deployed, data-driven itinerary site: map, trains, flights, fares, hour-aware ride estimates, traffic, weather, air quality, budget, bookings. Reference build: https://mantlecurve.github.io/agra-delhi-varanasi-journey/ |
| [`prototyping-typeface-from-prd`](skills/prototyping-typeface-from-prd) | Designs a typeface from a brief: a 22-section font PRD with numeric metrics, sample glyphs as stroke skeletons on a 1000 UPM grid, proof sheets reviewed at every weight, a specimen page, and OTF/WOFF prototypes with an editable type tester. |
| [`cutout-type-posters`](skills/cutout-type-posters) | Turns one photo of a person into premium 4:5 Instagram posts: on-device subject cutout (Apple Vision), clean grade, bold uppercase type fitted to exact widths, four proven templates (stepped strips, colour block, Swiss grid, number balloon), a 100-style catalogue, batch workflow for many variations, and headless-Chrome 2160×2700 renders with contact sheets. macOS. |
| [`unexpected-accent-palette`](skills/unexpected-accent-palette) | Turns a two-colour base pair into a memorable palette with one hue-distant, high-chroma accent: OKLCH hue/chroma checks, ranked accent suggestions, light/dark tokens with computed WCAG contrast, a side-by-side HTML preview, and accent-area measurement on screenshots. |

## Install

Skills are just folders. Claude Code loads them from `~/.claude/skills/` (available in every
project) or from `.claude/skills/` inside a project (available there only).

**For all your projects**

```bash
git clone https://github.com/mantleCurve/claude-skills.git
mkdir -p ~/.claude/skills
cp -r claude-skills/skills/travel-journey-site ~/.claude/skills/
```

**For one project**

```bash
mkdir -p .claude/skills
cp -r /path/to/claude-skills/skills/travel-journey-site .claude/skills/
```

**Keep it updated with a symlink instead of a copy**

```bash
ln -s "$(pwd)/claude-skills/skills/travel-journey-site" ~/.claude/skills/travel-journey-site
git -C claude-skills pull   # later, to update
```

Start a new Claude Code session afterwards. The skill appears in the skills list and can be
invoked as `/travel-journey-site` or by describing the task ("plan a trip site for …").

### Requirements for `travel-journey-site`

The skill drives a few tools from inside Claude Code:

- `gh` (GitHub CLI), logged in, for creating the repo and enabling GitHub Pages
- Python 3 with Pillow (`pip install pillow`) for the climate and image-layer scripts
- Node 18+ with Playwright (`npm i playwright`) and a Chromium under `~/.cache/ms-playwright`
  (`npx playwright install chromium`) for the headless checks
- Network access: Open-Meteo (weather, air quality), OpenStreetMap tiles, Google Fonts

### Requirements for `cutout-type-posters`

- macOS 14+ with Swift (Xcode Command Line Tools) for the on-device Apple Vision subject cutout
- `ffmpeg` for grading, masks and JPEG export (no `drawtext` needed)
- Google Chrome (headless) for rendering; override the path with `$CHROME`
- Network access: Google Fonts

## Use

For photo posters:

```
/cutout-type-posters make this photo a premium 4:5 birthday post, uppercase only — then give me 20 different styles
```

Claude cuts the subject out on your Mac, grades the photo, builds the layouts from the templates,
renders 2160×2700 PNG/JPG files and checks every one before showing a contact sheet.

For episode downloads, trim tests, and chaptered compilations:

```bash
./install.sh episodic-video-merge
```

Then ask, for example:

```text
/episodic-video-merge Download the complete series from this URL, inspect the
endings, and make an episodes 4–8 trim test with one chapter per episode.
Keep videos paused and preserve the original downloads.
```

Requires Python 3.10+, FFmpeg, ffprobe, and curl. The skill includes portable local
scripts and a documented 2.04-second preset from an accepted 25 fps test; trims
remain configurable for other footage. Run its generated-fixture integration
checks with `python3 skills/episodic-video-merge/scripts/test_pipeline.py`.

For visitor intent and follow-up workflows:

```bash
./install.sh jev-posthog
```

Then start a new Claude Code session and ask:

```text
/jev-posthog Add visitor intent classification and draft follow-ups to this website.
```

The skill adapts to the existing website, CRM, and email provider. Live classification
requires a TypeSafe API key and a configured PostHog project. It includes integration
references and a sample request, with draft-first delivery and explicit unknown outcomes
when evidence is weak. Visitor identity must come from known first-party data or a
separately configured enrichment provider.

For SEO implementation and audits:

```bash
./install.sh seo-skill
```

Then start a new Claude Code session and ask:

```text
/seo-skill Add complete SEO controls to this CMS, verify their rendered HTML,
and audit the service hierarchy and mobile performance. Keep staging private.
```

The skill adapts to your stack. Its optional local report gate requires Node 18+
and no npm dependencies. Browser/crawl tools are needed only for the checks you
request; unavailable measurements are reported explicitly. It does not promise
rankings or include paid integrations, client data, or third-party installers.

For colour palettes and CTA accents:

```bash
./install.sh unexpected-accent-palette
```

Then ask, for example:

```text
/unexpected-accent-palette Our site is charcoal #21232E and royal blue #105BFF and
it feels forgettable. Keep the brand colours, add one accent for the CTA, and give
me light and dark CSS tokens with contrast results.
```

Requires Python 3.9+ (standard library only). FFmpeg is needed only for `coverage`,
which measures how much of a screenshot the accent covers. The skill keeps your base
pair, proposes exactly one accent hue, and reports contrast computed by its script,
never estimated. Run its tests with
`python3 skills/unexpected-accent-palette/scripts/test_accent.py`.

For the travel skill:

```
/travel-journey-site Bangalore home. Jaipur 3 days, Jodhpur 2, Udaipur 3. Mid February, two of us.
```

or attach a travel poster and say "build the journey site from this".

Claude will transcribe the itinerary, research fares, timetables, tickets, coordinates and
climate with sources, write `data.js` against the documented schema, copy the engine, run the
checks, ask for a repo name, deploy to GitHub Pages and hand back the live URL. Expect a long
session: the research alone is a few dozen web searches.

## Layout of a skill

```
skills/travel-journey-site/
  SKILL.md                 what Claude reads: inputs, steps, rules, report format
  template/index.html      the page engine (generic; reads data.js)
  template/data.example.js the reference trip data, the schema by example
  template/img/            fallback textures (backdrop, stone, skyline)
  scripts/climate.py       monthly normals from three years of daily station data
  scripts/layers.py        cut illustration layers out of a poster as alpha WebP
  scripts/check.js         headless render check: errors, counts, clashes, screenshots
  scripts/scroll-check.js  scrolls like a person, reports anything left invisible
  scripts/deploy.sh        new public repo + GitHub Pages + live verification
```

## License

MIT for the code in this repository. Trip data in the example is from public sources cited in
its `sources` list; verify fares and timetables before booking.
