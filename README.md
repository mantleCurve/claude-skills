# claude-skills

Reusable skills for [Claude Code](https://claude.com/claude-code). Each skill lives in
`skills/<name>/` with a `SKILL.md` that Claude reads, plus any scripts and templates it needs.

| Skill | What it does |
|---|---|
| [`vistprint_india_photo_album_landscape`](skills/vistprint_india_photo_album_landscape) | Builds print-safe landscape photo albums with complete photo coverage, consistent ivory backgrounds, separate covers, and verified 300 DPI JPG exports for the Vistaprint India editor. |
| [`seo-skill`](skills/seo-skill) | Implement SEO/AEO-ready sites and CMS editors: nested services and locations, metadata, OG/X cards, schema, AI draft editing, mobile performance, and a tested audit-evidence gate. |
| [`travel-journey-site`](skills/travel-journey-site) | Turns a trip (a few places, or a poster) into a deployed, data-driven itinerary site: map, trains, flights, fares, hour-aware ride estimates, traffic, weather, air quality, budget, bookings. Reference build: https://mantlecurve.github.io/agra-delhi-varanasi-journey/ |

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

## Use

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
