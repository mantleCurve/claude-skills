---
name: episodic-video-merge
description: Download an accessible episodic video series, inspect and trim frozen endings, test selected episodes, and merge a complete MP4 with one chapter per episode. Use for numbered episode downloads, smooth episode joins, or chaptered compilations from existing local videos.
---

# Episodic video download, trim, and merge

Produce a numbered, verified source collection and a new MP4 with accurate episode chapters. Use Python 3.10+, FFmpeg, ffprobe, and curl locally. The scripts need no Python packages. They do not require a video-authoring framework or a hosted service.

## Establish the series and scope

Use the current conversation and existing project files to determine the series, episode count, output folder, language/audio choice, and requested range. Preserve original episodes and earlier deliverables. A request for “just episodes 4–8 to test” produces only that test; an acknowledgment of the test records the accepted setting without silently launching a full rebuild.

Inspect existing manifests, downloads, and scripts before revisiting a site. Do not infer episode URLs by incrementing an opaque asset ID. Record the actual page/stream mapping and verify that every expected number occurs once. An accessible subset is not a complete series.

Keep videos paused and autoplay disabled unless the user asks for playback. Prefer direct reads and local tools. When browser interaction is needed, use the environment's permitted browser tool and its documented APIs. Do not repeatedly click play or follow advertising redirects. Existing approval for a particular site's required interaction applies only within that task. Do not bypass login, payment, DRM, or browser security blocks.

Read [download-and-recovery.md](references/download-and-recovery.md) for stream discovery, HLS variants, resumable downloads, and the HEVC parameter-set failure encountered in this workflow.

## Download and verify the sources

Create a local `sources.json` with observed HTTP(S) media URLs and sequential episode numbers. Keep signed URLs, cookies, headers, and media out of the skill repository. The helper supports direct files and simple, unencrypted, muxed MPEG-TS VOD HLS; use the reference's alternate path for other formats.

```bash
python3 /path/to/episodic-video-merge/scripts/download_episodes.py \
  --manifest sources.json --expected-count 60 --output episodes
```

The downloader selects the largest HLS variant, fetches segments with bounded retries, retains in-band HEVC configuration using `hev1` when appropriate, and fully decodes every completed episode. It records hashes and only reuses a verified file whose hash still matches. Do not re-download good originals merely to change a trim.

## Inspect endings and choose the cut

```bash
python3 /path/to/episodic-video-merge/scripts/episode_media.py audit \
  --episodes episodes --output ending-audit.json --range 4:8
```

The audit reports stream start times, frame rates, exact repeated decoded tail frames, and near-static detection events over the last four seconds. These are evidence, not an automatic verdict: subtle motion, compressed stills, or deliberate dramatic pauses can fool a threshold. A clean decode and continuous timestamps do not establish that an ending looks smooth.

Read [timing-and-validation.md](references/timing-and-validation.md) before changing trim or merge logic. Keep trim choices in **frames**, with their corresponding seconds. Round an additional requested cut up to a whole frame and add it to the previous cut; do not repeatedly round a nominal total and lose an increment.

The originating 25 fps series used 25 frames (1.00 s), then 38 (1.52 s), then **51 frames (2.04 s)** from every ending. The user accepted the 51-frame episodes 4–8 test. This is a known preset for that series, **not the default for unrelated footage**. A separate episode had a 42-frame exact freeze; inspect outliers rather than assuming all tails match.

## Make the requested test or complete merge

Build directly from original episodes to avoid repeatedly encoding an already lossy test. Choose a new filename for each revision. `--trim-end` means the **total** cut from each original ending, not an incremental cut. `--trim-overrides` accepts a JSON object mapping episode numbers to total trim seconds for outliers.

```bash
python3 /path/to/episodic-video-merge/scripts/episode_media.py build \
  --episodes episodes --range 4:8 --trim-end 2.04 --normalize-timing \
  --output Series_Episodes_04-08_Test_Trim_2p04s.mp4 --title "Series — trim test"
```

After the user requests applying an accepted setting to the complete series:

```bash
python3 /path/to/episodic-video-merge/scripts/episode_media.py build \
  --episodes episodes --expected-count 60 --trim-end 2.04 --normalize-timing \
  --output Series_All_60_Trim_2p04s.mp4 --title "Series — complete"
```

The default encoder is portable `libx264` at CRF 18. On a supported Mac, `--encoder h264_videotoolbox` uses a configurable hardware bitrate (default 4 Mbps). This is a re-encode; do not call it lossless. The helper requires matching dimensions and constant frame rates, strips inherited container metadata/chapters, normalizes video starts, preserves audio's offset relative to picture, and uses PCM audio intermediates so individual AAC priming delays do not accumulate. It encodes the final AAC track once and embeds one chapter per included episode, retaining the original episode numbers.

`--normalize-timing` repairs small source timestamp jitter, capped at half a frame of cumulative deviation from the native frame grid. This was needed for the originating series. Omit it for strict timing checks; larger gaps or variable frame rates still stop the build. The report records the measured deviation.

“Stripping” here means the requested tail cuts and replacement of inherited container metadata. Do not silently remove subtitles burned into the picture, watermarks, opening scenes, credits, or speech. Separate audio/subtitle tracks require explicit selection before using the helper, which selects the first video and audio stream.

## Validate and hand back

The build checks all output video timestamps, frame count, duration, chapter titles/starts/ends, and full audio/video decoding before renaming its `.partial.mp4`. It writes a verification report and chapter text beside the result. If validation fails, retain logs and intermediates; do not label the output complete. Fix the specific cause rather than suppressing warnings globally.

For a trim test, deliver the file, actual extra and total cut, included episodes, and chapter count. Let the user judge the remaining pause in their player. For a full merge, also state duration, size, and any missing episodes or unverified conditions. Do not autoplay the deliverable.

The helper removes only its own intermediates after success unless `--keep-work` is set. Originals, earlier cuts, manifests, and final reports remain. Never commit downloaded videos, local source manifests, or authentication material when sharing this skill.
