# Download and recovery

## Discover once; keep a local mapping

Start with the series' actual episode list and stated count. Inspect the page or permitted network observations without starting playback where possible. Record the selected language/version and each episode's observed media URL. A page URL is not necessarily a media URL. Resolve relative playlist paths against the playlist URL, not against the webpage URL. Reuse available originals and manifests.

Example local manifest (substitute actual observed URLs):

```json
[
  {"episode": 1, "url": "https://media.example.com/observed-asset-1/master.m3u8"},
  {"episode": 2, "url": "https://media.example.com/observed-asset-2/master.m3u8"}
]
```

Run with `--expected-count 2` for this example. The helper rejects gaps, duplicate numbers, and duplicate URLs. Identical files under different episode numbers are also rejected. Retain a local mapping if a legitimate source needs investigation; do not claim completeness solely from filenames.

Headers can be supplied as a private JSON string-to-string object via `--headers-file`. They are never included in verification reports. Avoid putting credentials on a command line or publishing signed URLs. The helper's curl configuration files have owner-only permissions and are removed after requests.

## HLS handling

Inspect master variants and audio groups. For the helper's supported case, choose the highest pixel count, breaking ties by bandwidth. Do not infer quality from a URL suffix such as `sd`; probe actual dimensions and codec. Download every segment of an ended VOD playlist, including relative URLs, then construct a local playlist for FFmpeg. Segment names preserve order. Downloads use partial files, finite retry/time limits, and modest concurrency.

Some CDNs accept curl but reject another client's TLS/session behavior or stall FFmpeg's network reader. The helper uses curl to localize supported MPEG-TS HLS, then runs FFmpeg against local files. That is a transport fallback, not a reason to defeat an access-control block. Refresh an expired URL through normal authorized access; stop after bounded retries if access remains denied.

The helper deliberately rejects live playlists, encryption keys, fMP4 `EXT-X-MAP`, byte ranges, alternate audio groups, discontinuities, and recursive masters. For those, use an installed maintained downloader or FFmpeg only when it supports the actual accessible format, with headers/session access the user already authorized. Consult the installed tool's help for its exact options. Preserve all necessary init segments and selected audio tracks. Do not turn unsupported DRM into a decryption project. Fully probe and decode any externally downloaded result before treating it as an original.

## The HEVC failure that must not recur

One episodic source contained changing HEVC parameter sets between segments. An earlier MP4 remux tagged `hvc1` removed in-band configuration needed later in the stream. The resulting video opened and had plausible metadata but froze or failed when decoded beyond segment boundaries.

For HEVC sources of this kind, preserve in-band parameter sets with `-tag:v hev1` during acquisition. Verify the entire acquired file. If a damaged `hvc1` remux has already discarded configuration, changing its tag afterward cannot recover the missing data: reacquire from intact source segments, then decode to H.264 if broad player compatibility is wanted. A successful probe or first-frame preview is insufficient.

## Resume and completeness

Every source gets a SHA-256 and a successful full-decode record. The helper checks that the source URL/header configuration and file hash still match before reusing it. Segment caches are isolated by source and request-header fingerprints; failed downloads remain partial. Preserve good sources, but refresh or quarantine a suspect cached segment when a reproducible decode failure points to it.

Compare the final manifest to the expected number set. Confirm actual episode identities when the source can return a preview, recap, or repeated default episode. Do not publish a “complete” merge from 47 accessible episodes when the series advertises 60. If unavailable episodes require user action, finish the accessible work and clearly report the missing range.
