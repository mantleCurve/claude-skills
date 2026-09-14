---
name: travel-journey-site
description: Turn a trip itinerary (from a poster image, a text plan, or a conversation) into a deployed, data-driven "living itinerary" website with a real map, distances from coordinates, train and flight timetables and fares, hour-aware Uber/cab estimates, traffic profiles, closed-day detection, climate normals, live weather and AQI, budget calculator and bookings checklist. Use when someone asks for an interactive travel plan, itinerary site, trip planner page, or to "replicate" the Agra–Delhi–Varanasi journey site for another trip.
---

# Travel journey site

Minimum input: a home city, two or more destinations, roughly how many days in each, and a
rough month. Everything else (sights, fares, timetables, coordinates, climate, air) you research
and fill in. With no poster there is no diorama art: the hero stage and chapter art collapse
cleanly, and the page still carries the poster look through type, backdrop, embers and stamps.
If the user can supply any illustration per city (their own photos work), cut them with
`layers.py` or just save them as `img/<cityKey>.webp` with transparent surroundings.

You produce two files, `index.html` (a generic engine, copied from this skill unchanged) and
`data.js` (everything trip-specific), test them headless, and deploy to GitHub Pages.
The reference build is https://mantlecurve.github.io/agra-delhi-varanasi-journey/ ; its data
file is `template/data.example.js` in this skill. Read that example before writing a new one.

## 1. Collect the itinerary

From the user's poster, text, or answers, establish:
- home city and airport; each destination city with the days spent there
- the sights per city (the poster's lists are the source of truth; do not invent extra stops)
- the order of legs between cities and the intended mode (train, flight, cab)
- departure date if known (otherwise pick a sensible default in the best season), travellers, ticket type (domestic vs foreign)

If the input is an image, read it and transcribe every list before doing anything else.

## 2. Research real facts (WebSearch / WebFetch), and record sources

For every inter-city leg: train number, departure and arrival times, running days, fare per class;
flight duration and the current published fare range; cab fare and road distance.
For every sight: entry fee for both ticket types, opening hours, closed day, typical visit length.
For every city: airport and main station names, a typical hourly traffic profile (TomTom index,
local reporting), UberGo-class rate card, notable airport-to-centre fare.
Search per item; a handful of queries per leg is normal. Put each URL used into `sources` so the
page's footer cites it. Fares change, so date the sources in the footer text.

## 3. Coordinates and climate

- Look up lat/lng for the home city, its airport, every city centre, airport, station,
  the place you'll sleep, and every sight. The engine computes all distances from these
  (haversine × 1.3 inside cities, × 1.25 for rail, × 1 for flights). Get them right.
- Run `scripts/climate.py` with each city's coordinates. It pulls three years of daily
  history from Open-Meteo's archive and prints the `hi`, `lo` and `rain` arrays you paste
  into `climate`. Set `aqi` (1 good … 5 very poor per month) from local reporting.

```
python3 ~/.claude/skills/travel-journey-site/scripts/climate.py "delhi 28.61 77.21" "agra 27.18 78.02"
```

## 3b. Visual layers (this is what keeps it from looking generic)

The engine expects `img/backdrop.jpg`, `img/stone.jpg`, `img/skyline.jpg` and one alpha WebP per
city named `img/<cityKey>.webp` (the hero and each city chapter float these as parallax layers).
If the user gave a poster, lift the artwork out of it with `scripts/layers.py`:

```
LO=50 HI=96 python3 ~/.claude/skills/travel-journey-site/scripts/layers.py poster.png site/img \
  "agra:35,275,435,730:45,288,170,405;45,545,205,712:42,292,431,650"
```
Each argument is `name:cropbox:cut;cut...:keepbox` in poster pixel coordinates. Cuts erase printed
text so live HTML replaces it; the keep box drops everything outside the illustration (this is what
removes the poster's card borders). Dark pixels become transparent, so the layer floats on any dark
background. Always composite the results on a flat dark sheet and LOOK at them before using them.
Make `backdrop.jpg` by blurring the whole poster heavily at low resolution, `stone.jpg` from a
texture strip of its margins, `skyline.jpg` from its footer band (erase printed text by pasting
plain patches). The template's `img/` holds the reference set as a fallback when there is no poster.

Design rules that the template already follows, keep them: warm near-black ground, cream DM Serif
Display titles, Bitter slab body at 18px+ and weight 500–800 (figures in Bitter 800), Kalam 700 script
for stamps and taglines in saffron, hairlines not boxes, dioramas unboxed with drop shadows, embers,
grain. Every metric gets an icon chip (`chip('thermo', …)` etc. in the engine). Text must read from
across a room: nothing under 14px, body copy 18px, weights bold. Never use Inter, Roboto, Helvetica
or other sterile sans faces, never glass cards or gradient blobs.

## 4. Write `data.js`

Copy `template/data.example.js`, keep the shape, replace the content. City keys must match the
WebP file names. The chapter taglines live in the engine's `CITYTAG` map near `renderDays`; set
one per city key. Key rules:
- `legs[].options[0]` is the default; give trains a `classes` array with matching `fare` pairs.
- `days[].items` use `kind` ∈ sight | ride | walk | train | flight | meal | free.
  Rides name `from`/`to` as a sight id or one of `home`, `homeAirport`, `stay`, `hub`, `rail`,
  `rail2`. A ride that happens in a city other than the day's `city` MUST set `cityRef`.
  `fixed: [lo, hi]` overrides the estimate for prebooked cabs. `metro: true` uses flat metro fares.
- `closed` strings are matched against weekday names, so write "Friday", "Monday", "Never".
- `festivals[].m` is 1-based month. `packing` lists are chosen by the month's heat, cold, rain, smog.
- `defaultStart` is an ISO date. Pick one whose weekdays clear every `closed` rule and train running day.
- Air: each city needs `air.monthly` (12 CPCB AQI averages, from CPCB bulletins or press coverage of
  monthly averages), `air.fog` (0–3 per month) and `air.note`. Top-level `airHourly` is the 24-hour
  multiplier (overnight inversion high, early afternoon low). The engine rates every outdoor hour,
  flags fog on early-morning sights, builds the Air section and pulls a live five-day forecast.
  For a smog-season trip, research the latest monthly averages; they move year to year.
- Keep blurbs original, short, and useful. No filler.

Then copy `template/index.html` next to it. The hero title, the three `<img src="img/…webp">`
lines in the hero stage, the three `.tag` taglines, the `CITYTAG` map, the nav, the section
copy and the `<title>` are the trip-specific text in the engine: replace them for the new cities
(add or remove `.dio` blocks to match the city count). Leave the script logic alone.

## 5. Test headless before deploying

```
cd <site dir> && python3 -m http.server 8790 &
node ~/.claude/skills/travel-journey-site/scripts/check.js http://127.0.0.1:8790/
```
`check.js` needs `playwright` installed somewhere on NODE_PATH (the scratchpad from earlier
sessions has it; `npm i playwright` otherwise) and a Chromium under `~/.cache/ms-playwright`.
It fails loudly on page errors and prints how many days and legs rendered, the map stats,
closed-day clashes, and the budget total. Zero page errors and the right day count are
required. Then take a couple of screenshots and look at them: hero, map, one day, weather.

Then run `scripts/scroll-check.js <url>`: it scrolls the page like a person WITHOUT overriding
the reveal styles and reports anything still at opacity 0, the chapter order, and per-day opacity.
The first check overrides reveal CSS to screenshot, so it cannot catch a block that never reveals.

Common failures: a ride whose `from`/`to` doesn't resolve (missing `cityRef`), a sight id
typo, a leg `fromPt`/`toPt` key the city doesn't have, duplicate element ids, a scroll-reveal
applied to a container taller than the viewport (it never reaches the threshold).

## 6. Deploy

```
bash ~/.claude/skills/travel-journey-site/scripts/deploy.sh <site dir> <github-owner>/<repo-name> "one-line description"
```
Creates the public repo, pushes `main`, enables Pages from the root, waits for the build,
and curls the live URL plus `data.js`. Never push into an existing repo the user didn't name.

## 7. Report

Give the live URL first. Then, in plain prose, what the page does (map, legs, day-by-day,
weather, traffic, budget, bookings) and which numbers were verified against which sources.
Say clearly that ride fares are estimates from rate cards and traffic profiles, not live quotes.
