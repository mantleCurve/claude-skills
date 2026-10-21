# Timing, trimming, and validation

## Separate a still image from a timing gap

Probe video/audio `start_time`, durations, time bases, frame rate, frame count, sample rate, and dimensions. Inspect decoded final frames with `framemd5` and near-static events with `freezedetect`. The audit hashes full-resolution decoded frames; near-static detection runs on the same picture. A run reaching the end of the audit window is a lower bound if the freeze began before that window.

Exact duplicate frames find literal holds; low-level noise can make a visibly static image produce different hashes. Near-static thresholds can mistake intentional low motion for a defect. Treat both as candidates for a small test. Do not remove all apparently still shots automatically.

The originating sources placed video at +0.08 s while audio began at zero. Using each full container duration during concatenation added avoidable holds. Reset video timestamps and adjust the audio by the **difference** between its start and the video's start. If audio starts earlier, cut that leading interval; if it starts later, prepend the corresponding silence. Never reset both timestamps independently without accounting for their relative offset.

## Cut in frames

At 25 fps, a frame lasts 0.04 s. A requested additional 0.5 s becomes 13 frames, or 0.52 s, when rounded upward. The accepted sequence was 25 → 38 → 51 removed frames, corresponding to 1.00 → 1.52 → 2.04 seconds. Recompute every chapter after every trim. Count kept decoded frames rather than relying on a container's rounded duration.

The helper inspects source packet presentation times (sorted to account for B-frame decode order). By default it allows only one time-base tick of rounding. The originating episodes had a native 25 fps grid with shifts of 6.68–20 ms; `--normalize-timing` permits at most half a frame of cumulative deviation and writes each decoded frame back to the exact native grid. It records the deviation and still rejects larger gaps and variable-rate metadata. Matching dimensions/rates are required across the selection. For mismatched or variable-rate sources, deliberately normalize to an agreed geometry and frame rate first and document that conversion; do not hide a conversion inside a claimed lossless merge. Rotated source metadata also requires deliberate normalization.

For rate N/D, use video track time scale N, so each output frame is exactly D ticks. Chapter time base is D/N and chapter starts/ends are cumulative **kept frame indices**. This avoids accumulated decimal rounding, including fractional rates such as 30000/1001.

## Encode and concatenate without adding pauses

Re-encode precise cuts; stream-copy cuts near inter-frame boundaries can retain unwanted frames or depend on discarded references. Use identical encoder settings for all intermediate episodes. Store intermediate audio as PCM, then encode one continuous final AAC track to avoid one priming delay per episode. Match audio duration to the kept picture; fractional sample boundaries can be rounded by at most one sample, with final resampling repairing tiny discontinuities.

The helper uses explicit mapping to one video/audio track and `-map_metadata -1 -map_chapters -1` for intermediates. The final file receives fresh title metadata and episode chapters. Embedded subtitles or extra language tracks are outside this helper's default mapping and need an intentional extension if requested.

## Evidence before completion

Require all of these:

- Expected episode numbers, frame count, dimensions, and output rate.
- Exactly one chapter per included episode; correct title, first-frame start, and next-episode end.
- Video packet timestamps starting at zero with exactly one frame interval between successive frames, including every join.
- Audio/video end durations within the declared encoding tolerance.
- Full decoding of the final video **and audio**, not just a successful FFmpeg exit from the merge.

For a null-output full decode, preserve source timing:

```bash
ffmpeg -nostdin -hide_banner -v error -i result.mp4 \
  -map 0:v:0 -map 0:a:0 \
  -fps_mode:v passthrough -enc_time_base:v demux -f null -
```

Without these timing flags, the null muxer's chosen time base can introduce misleading timestamp-rounding diagnostics. Still investigate actual warnings; never hide them wholesale. A clean decode proves decodability, and contiguous PTS proves no timestamp gaps. Neither proves that intentional or compressed still footage has disappeared. State that distinction and use the user's selected test range for visual acceptance.

Keep partial output and logs if a check fails. Rename to the final filename only after validation. Remove only disposable files created by this run, never originals or previous deliverables.
