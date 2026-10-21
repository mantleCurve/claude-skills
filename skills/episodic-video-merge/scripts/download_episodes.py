#!/usr/bin/env python3
"""Download observed episode media URLs; verify before recording completion."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from episode_media import decode, digest, probe, require, run, stream, write_json


def http_url(url):
    parts = urlsplit(url)
    require(parts.scheme in {'http', 'https'} and parts.hostname and not parts.username,
            'Media URLs must be HTTP(S), without embedded credentials')
    return url


def quote_config(value):
    require('\n' not in value and '\r' not in value and '\x00' not in value,
            'Newline/NUL in URL or request header')
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def fetch(url, target, headers):
    http_url(url)
    target = Path(target)
    partial = target.with_name(target.name + '.partial')
    lines = ['url = ' + quote_config(url)]
    for k, v in headers.items():
        require(isinstance(k, str) and isinstance(v, str) and ':' not in k,
                'Headers must be a string-to-string object')
        lines.append('header = ' + quote_config(f'{k}: {v}'))
    # Do not expose signed URLs or authentication headers through process arguments.
    fd, config = tempfile.mkstemp(prefix='episode-curl-', suffix='.conf')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        result = subprocess.run(['curl', '--config', config, '--fail', '--location', '--silent',
                                 '--show-error', '--proto', '=http,https', '--proto-redir', '=http,https',
                                 '--retry', '2', '--retry-delay', '1', '--connect-timeout', '10',
                                 '--max-time', '180', '--output', str(partial)], capture_output=True)
        require(result.returncode == 0, f'curl failed (code {result.returncode}); check access/expiry')
        require(partial.exists() and partial.stat().st_size > 0, 'Downloaded an empty response')
        partial.replace(target)
    finally:
        Path(config).unlink(missing_ok=True)


def attributes(line):
    return {m[1]: (m[2][1:-1] if m[2].startswith('"') else m[2]) for m in
            re.finditer(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)', line)}


def localize_hls(url, first, cache, headers, workers):
    playlist = first.read_text(encoding='utf-8-sig')
    require(playlist.lstrip().startswith('#EXTM3U'), 'Response is not an HLS playlist')
    if '#EXT-X-STREAM-INF:' in playlist:
        require('#EXT-X-MEDIA:' not in playlist, 'Alternate media groups need a full HLS downloader')
        lines = [s.strip() for s in playlist.splitlines() if s.strip()]
        variants = []
        for i, line in enumerate(lines):
            if line.startswith('#EXT-X-STREAM-INF:'):
                require(i + 1 < len(lines) and not lines[i + 1].startswith('#'), 'Malformed HLS variant')
                attr = attributes(line.split(':', 1)[1])
                require('AUDIO' not in attr, 'External audio group requires a full HLS downloader')
                w, h = map(int, attr.get('RESOLUTION', '0x0').split('x'))
                variants.append((w * h, int(attr.get('BANDWIDTH', '0')), urljoin(url, lines[i + 1])))
        require(variants, 'No HLS video variants')
        url = max(variants)[2]
        media = cache / 'media.m3u8'
        fetch(url, media, headers)
        playlist = media.read_text(encoding='utf-8-sig')
    require('#EXT-X-ENDLIST' in playlist, 'Live/incomplete playlist is not supported')
    forbidden = ['#EXT-X-KEY', '#EXT-X-MAP', '#EXT-X-BYTERANGE', '#EXT-X-DISCONTINUITY',
                 '#EXT-X-STREAM-INF', '#EXT-X-MEDIA:', '#EXT-X-I-FRAMES-ONLY', '#EXT-X-GAP']
    require(not any(tag in playlist for tag in forbidden),
            'Unsupported HLS feature; use the documented alternate downloader path')
    entries = [s.strip() for s in playlist.splitlines() if s.strip() and not s.startswith('#')]
    durations = re.findall(r'^#EXTINF:([0-9.]+)', playlist, re.M)
    require(entries and len(entries) == len(durations), 'Malformed/empty media playlist')
    expected = sum(map(float, durations))
    # Expired URLs may yield a different playlist: never reuse mismatched segments.
    identity = hashlib.sha256((url + '\n' + playlist).encode()).hexdigest()
    segments = cache / ('segments-' + identity[:16])
    segments.mkdir(exist_ok=True)

    def segment(pair):
        index, relative = pair
        path = segments / f'{index:06d}.ts'
        if not path.exists():
            fetch(urljoin(url, relative), path, headers)
        with path.open('rb') as f:
            prefix = f.read(564)
        require(len(prefix) >= 188 and prefix[0] == 0x47 and
                (len(prefix) < 377 or prefix[188] == prefix[376] == 0x47),
                'Expected MPEG-TS segments; use an appropriate downloader for other HLS formats')
        return path.name

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        names = list(pool.map(segment, enumerate(entries)))
    # Only local references and required timing tags enter the playback playlist.
    localized = ['#EXTM3U', '#EXT-X-VERSION:3', '#EXT-X-TARGETDURATION:' + str(math_ceil_max(durations))]
    for seconds, name in zip(durations, names):
        localized += [f'#EXTINF:{seconds},', name]
    localized.append('#EXT-X-ENDLIST')
    path = segments / 'local.m3u8'
    path.write_text('\n'.join(localized) + '\n')
    return path, expected


def math_ceil_max(durations):
    import math
    return math.ceil(max(map(float, durations)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--expected-count', required=True, type=int)
    parser.add_argument('--output', required=True)
    parser.add_argument('--headers-file', help='Private JSON header object; never committed')
    parser.add_argument('--workers', type=int, default=3, choices=range(1, 9))
    args = parser.parse_args()
    for tool in ['curl', 'ffmpeg', 'ffprobe']:
        require(shutil.which(tool), f'Missing executable: {tool}')
    manifest = json.loads(Path(args.manifest).read_text())
    require(isinstance(manifest, list) and args.expected_count > 0, 'Invalid manifest/count')
    require(all(isinstance(e, dict) and type(e.get('episode')) is int and
                isinstance(e.get('url'), str) for e in manifest), 'Invalid manifest entries')
    manifest.sort(key=lambda e: e['episode'])
    require([e['episode'] for e in manifest] == list(range(1, args.expected_count + 1)),
            'Manifest has missing, extra, or duplicate episode numbers')
    require(len({e['url'] for e in manifest}) == len(manifest), 'Duplicate episode media URL')
    for entry in manifest:
        http_url(entry['url'])
    headers = json.loads(Path(args.headers_file).read_text()) if args.headers_file else {}
    require(isinstance(headers, dict), 'Headers file must contain an object')
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    cache_root = root / '.download-work'
    cache_root.mkdir(exist_ok=True)
    records, hashes = [], set()
    for entry in manifest:
        n = entry['episode']
        target = root / f'Episode_{n:02d}.mp4'
        stamp = root / f'Episode_{n:02d}.verified.json'
        identity = hashlib.sha256(json.dumps([entry['url'], headers], sort_keys=True).encode()).hexdigest()
        if target.exists():
            require(stamp.exists(), f'Existing unverified file; inspect before replacing: {target}')
            prior = json.loads(stamp.read_text())
            require(prior.get('request_fingerprint') == identity and prior.get('sha256') == digest(target),
                    f'Existing source/configuration changed: {target}; inspect before replacing')
            require(prior['sha256'] not in hashes, 'Identical content for different episodes')
            hashes.add(prior['sha256'])
            records.append(prior)
            print(f'Episode {n:02d}: reused verified source', flush=True)
            continue
        require(shutil.disk_usage(root).free > 1_000_000_000, 'Less than 1 GB free; free disk space')
        cache = cache_root / f'{n:04d}-{identity[:16]}'
        cache.mkdir(exist_ok=True)
        response = cache / 'source.response'
        fetch(entry['url'], response, headers)
        with response.open('rb') as f:
            prefix = f.read(32).lstrip(b'\xef\xbb\xbf\r\n ')
        if prefix.startswith(b'#EXTM3U'):
            source, expected = localize_hls(entry['url'], response, cache, headers, args.workers)
        else:
            source, expected = response, None
        data = probe(source)
        v, a = stream(data, 'video'), stream(data, 'audio')
        require(v['codec_name'] in {'h264', 'hevc'}, 'Transcode unsupported video codec deliberately')
        partial = cache / 'episode.partial.mp4'
        codec_tag = ['-tag:v', 'hev1'] if v['codec_name'] == 'hevc' else []
        result = run(['ffmpeg', '-nostdin', '-hide_banner', '-v', 'warning', '-y', '-i', source,
                      '-map', '0:v:0', '-map', '0:a:0', '-map_metadata', '-1', '-map_chapters', '-1',
                      '-c', 'copy', *codec_tag, '-movflags', '+faststart', partial], cache / 'remux.log')
        require(not result.stderr.strip(), f'Review remux warnings: {cache / "remux.log"}')
        completed = probe(partial)
        cv, ca = stream(completed, 'video'), stream(completed, 'audio')
        duration = float(completed['format']['duration'])
        if expected is not None:
            require(abs(duration - expected) < 0.5, 'Downloaded duration differs from HLS segment sum')
        decode(partial, cache / 'decode.log')
        checksum = digest(partial)
        require(checksum not in hashes, 'Identical content for different episodes')
        hashes.add(checksum)
        record = {'episode': n, 'request_fingerprint': identity, 'sha256': checksum,
                  'duration_seconds': duration, 'playlist_duration_seconds': expected,
                  'width': cv['width'], 'height': cv['height'], 'video_codec': cv['codec_name'],
                  'audio_codec': ca['codec_name'], 'frame_rate': cv['r_frame_rate'],
                  'size_bytes': partial.stat().st_size, 'full_audio_video_decode_passed': True}
        require(not target.exists(), 'Destination appeared during download')
        partial.rename(target)
        write_json(stamp, record)
        records.append(record)
        shutil.rmtree(cache)
        print(f'Episode {n:02d}: downloaded and fully decoded ({duration:.2f}s)', flush=True)
    write_json(root / 'download-manifest.json', records)
    print(f'All {len(records)} expected episodes downloaded and verified.', flush=True)


if __name__ == '__main__':
    main()
