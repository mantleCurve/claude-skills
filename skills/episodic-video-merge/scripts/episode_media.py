#!/usr/bin/env python3
"""Audit CFR episode tails and build verified chaptered MP4 compilations."""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args, log=None):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if log:
        Path(log).write_text(result.stderr)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed; {log or result.stderr[-2000:]}")
    return result


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams',
                           '-show_format', '-show_chapters', '-of', 'json', path]).stdout)


def stream(data, kind):
    return next(s for s in data['streams'] if s['codec_type'] == kind)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def decode(path, log):
    result = run(['ffmpeg', '-nostdin', '-hide_banner', '-v', 'error', '-threads', '2',
                  '-i', path, '-map', '0:v:0', '-map', '0:a:0', '-fps_mode:v',
                  'passthrough', '-enc_time_base:v', 'demux', '-f', 'null', '-'], log)
    require(not result.stderr.strip(), f'Decode diagnostics: {log}')


def select_episodes(directory, selection=None, expected=None):
    files = {}
    for p in Path(directory).glob('Episode_*.mp4'):
        m = re.fullmatch(r'Episode_(\d+)\.mp4', p.name)
        if m:
            n = int(m[1])
            require(n > 0 and n not in files, f'Duplicate/invalid episode: {n}')
            files[n] = p.resolve()
    require(files, 'No Episode_NN.mp4 source files found')
    if selection:
        first, last = map(int, selection.split(':'))
        require(0 < first <= last, 'Range must be FIRST:LAST, inclusive')
        wanted = list(range(first, last + 1))
    else:
        wanted = list(range(1, (expected or max(files)) + 1))
        if expected:
            require(set(files) == set(wanted), 'Source count differs from expected series')
    require(set(wanted).issubset(files), f'Missing episodes: {sorted(set(wanted)-set(files))}')
    return [(n, files[n]) for n in wanted]


def packets(path):
    raw = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_packets',
               '-show_entries', 'packet=pts,duration', '-of', 'json', path]).stdout
    return json.loads(raw)['packets']


def clock_info(path, data, normalize_timing=False):
    v = stream(data, 'video')
    rate = Fraction(v['r_frame_rate'])
    require(rate > 0 and rate == Fraction(v['avg_frame_rate']), f'Non-CFR rate: {path.name}')
    time_base = Fraction(v['time_base'])
    rows = packets(path)
    require(rows and all('pts' in p and 'duration' in p for p in rows), 'Missing packet timing')
    pts = sorted(int(p['pts']) for p in rows)
    step = 1 / rate
    # Permit one source time-base tick of rounding (e.g. fractional-rate input).
    drift = max(abs((p - pts[0]) * time_base - i * step) for i, p in enumerate(pts))
    tolerance = max(time_base, step / 2) if normalize_timing else time_base
    require(drift <= tolerance, f'Variable rate or timestamp gap: {path.name}; '
            f'maximum deviation {float(drift):.6f}s. --normalize-timing permits at most half a frame.')
    require(all(abs(int(p['duration']) * time_base - step) <= time_base for p in rows),
            f'Irregular frame durations: {path.name}')
    return rate, len(pts), pts[0] * time_base, drift


def audit(args):
    output = Path(args.output).resolve()
    require(not output.exists(), f'Output exists: {output}')
    report = []
    for n, path in select_episodes(args.episodes, args.range, args.expected_count):
        data = probe(path)
        v, a = stream(data, 'video'), stream(data, 'audio')
        result = run(['ffmpeg', '-nostdin', '-hide_banner', '-v', 'info', '-sseof',
                      str(-args.window), '-threads', '2', '-i', path, '-an', '-vf',
                      'freezedetect=n=0.001:d=0.12', '-fps_mode:v', 'passthrough',
                      '-enc_time_base:v', 'demux', '-f', 'framemd5', '-'])
        hashes = [line.split(',')[-1].strip() for line in result.stdout.splitlines()
                  if line and not line.startswith('#')]
        require(hashes, f'No decoded tail frames: {path}')
        count = 1
        for value in reversed(hashes[:-1]):
            if value != hashes[-1]:
                break
            count += 1
        rate = Fraction(v['avg_frame_rate'])
        item = {'episode': n, 'path': str(path), 'video_start': v.get('start_time'),
                'audio_start': a.get('start_time'), 'video_duration': v.get('duration'),
                'container_duration': data['format'].get('duration'),
                'frame_rate': str(rate), 'tail_window_seconds': args.window,
                'exact_tail_frames': count, 'exact_tail_seconds_at_average_rate': float(count / rate),
                'freeze_may_extend_before_window': count == len(hashes),
                'near_static_events': re.findall(
                    r'lavfi.freezedetect.(freeze_start|freeze_duration|freeze_end): ([\d.-]+)',
                    result.stderr)}
        report.append(item)
        print(f'Episode {n:02d}: {count} identical final frames', flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)


def build(args):
    final = Path(args.output).resolve()
    require(final.suffix.lower() == '.mp4', 'Output must be MP4')
    require(not final.exists(), f'Refusing to overwrite {final}')
    final.parent.mkdir(parents=True, exist_ok=True)
    work = final.with_suffix('.work')
    owner = work / '.episode-media-work'
    require(not work.exists() or owner.exists(), f'Unowned work directory exists: {work}')
    work.mkdir(exist_ok=True)
    owner.write_text('Disposable intermediates owned by episode_media.py\n')
    overrides = json.loads(Path(args.trim_overrides).read_text()) if args.trim_overrides else {}
    inputs = select_episodes(args.episodes, args.range, args.expected_count)
    records, common, offset = [], None, 0
    for n, path in inputs:
        data = probe(path)
        v, a = stream(data, 'video'), stream(data, 'audio')
        rate, source_frames, video_start, timing_drift = clock_info(path, data, args.normalize_timing)
        geometry = (v['width'], v['height'], str(rate), v.get('sample_aspect_ratio', '1:1'))
        require(not any(float(s.get('rotation', 0)) != 0 for s in v.get('side_data_list', [])),
                f'Normalize rotation first: {path.name}')
        common = common or geometry
        require(geometry == common, 'Normalize mismatched dimensions, aspect ratios, or rates first')
        total_trim = Fraction(str(overrides.get(str(n), args.trim_end)))
        require(total_trim >= 0, 'Trim cannot be negative')
        trim_frames = math.ceil(total_trim * rate)
        frames = source_frames - trim_frames
        require(frames > 0, f'Trim removes all of episode {n}')
        duration = frames / rate
        audio_offset = video_start - Fraction(a.get('start_time', '0'))
        audio_cut = round(audio_offset * args.audio_rate)
        audio_samples = round(duration * args.audio_rate)
        config = {'episode': n, 'source_sha256': digest(path), 'source_frames': source_frames,
                  'frames': frames, 'trim_frames': trim_frames, 'trim_seconds': float(trim_frames / rate),
                  'rate': str(rate), 'encoder': args.encoder, 'bitrate': args.bitrate,
                  'audio_rate': args.audio_rate, 'audio_offset_seconds': float(audio_offset),
                  'normalize_timing': args.normalize_timing,
                  'source_max_timing_deviation_seconds': float(timing_drift),
                  'schema': 1}
        target = work / f'Episode_{n:04d}.mov'
        stamp = target.with_suffix('.json')
        reuse = False
        if stamp.exists() and target.exists():
            prior = json.loads(stamp.read_text())
            reuse = prior.get('config') == config and prior.get('sha256') == digest(target)
        if not reuse:
            require(shutil.disk_usage(work).free > 1_000_000_000, 'Less than 1 GB free; free disk space')
            audio_filter = [f'aresample={args.audio_rate}', 'asetpts=PTS-STARTPTS']
            if audio_cut >= 0:
                audio_filter += [f'atrim=start_sample={audio_cut}', 'asetpts=PTS-STARTPTS']
            else:
                audio_filter += [f'adelay={-audio_cut}S:all=1']
            audio_filter += ['apad', f'atrim=end_sample={audio_samples}', 'asetpts=N/SR/TB']
            encoder = (['-c:v', 'libx264', '-preset', 'fast', '-crf', '18']
                       if args.encoder == 'libx264' else
                       ['-c:v', 'h264_videotoolbox', '-b:v', args.bitrate])
            log = work / f'trim_{n:04d}.log'
            result = run(['ffmpeg', '-nostdin', '-hide_banner', '-v', 'warning', '-y', '-threads', '2',
                          '-i', path, '-map', '0:v:0', '-map', '0:a:0', '-map_metadata', '-1',
                          '-map_chapters', '-1', '-vf',
                          f'trim=end_frame={frames},setpts=N*{rate.denominator}/({rate.numerator}*TB)',
                          '-af', ','.join(audio_filter), *encoder, '-profile:v', 'high', '-bf', '0',
                          '-g', str(math.ceil(float(rate) * 2)), '-pix_fmt', 'yuv420p', '-r', str(rate),
                          '-fps_mode:v', 'cfr', '-video_track_timescale', str(rate.numerator),
                          '-c:a', 'pcm_s16le', '-ar', str(args.audio_rate), '-ac', '2', target], log)
            require(not result.stderr.strip(), f'Review encoder warnings: {log}')
            check = probe(target)
            cv, ca = stream(check, 'video'), stream(check, 'audio')
            require(int(cv['nb_frames']) == frames, 'Intermediate frame count mismatch')
            require(abs(float(cv['start_time'])) < 0.00001, 'Video start is not zero')
            require(abs(float(ca['start_time'])) < 0.00001, 'Audio start is not zero')
            require(abs(float(cv['duration']) - float(duration)) < 0.00001, 'Video duration mismatch')
            require(abs(float(ca['duration']) - float(duration)) <= 1 / args.audio_rate + 0.000002,
                    'Audio duration mismatch')
            write_json(stamp, {'config': config, 'sha256': digest(target)})
        records.append({**config, 'duration_seconds': float(duration), 'start_frame': offset,
                        'end_frame': offset + frames, 'intermediate': target.name})
        offset += frames
        print(f'Episode {n:02d}: {trim_frames} frames trimmed ({float(trim_frames / rate):.3f}s)', flush=True)
    rate = Fraction(common[2])
    duration = offset / rate
    write_json(work / 'manifest.json', records)
    (work / 'concat.txt').write_text(''.join(
        f"file '{r['intermediate']}'\nduration {r['duration_seconds']:.12f}\n" for r in records))
    metadata = [';FFMETADATA1', 'title=' + escape_metadata(args.title)]
    chapter_text = []
    for r in records:
        title = f"Episode {r['episode']:02d}"
        metadata += ['[CHAPTER]', f'TIMEBASE={rate.denominator}/{rate.numerator}',
                     f"START={r['start_frame']}", f"END={r['end_frame']}", f'title={title}']
        ms = round(Fraction(r['start_frame'], 1) / rate * 1000)
        chapter_text.append(f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d} {title}')
    (work / 'chapters.ffmetadata').write_text('\n'.join(metadata) + '\n')
    partial = work / 'result.partial.mp4'
    print(f'Merging {len(records)} episodes with chapters; then verifying full decode.', flush=True)
    result = run(['ffmpeg', '-nostdin', '-hide_banner', '-v', 'warning', '-y', '-f', 'concat',
                  '-safe', '0', '-i', work / 'concat.txt', '-f', 'ffmetadata', '-i', work / 'chapters.ffmetadata',
                  '-map', '0:v:0', '-map', '0:a:0', '-map_metadata', '1', '-map_chapters', '1',
                  '-c:v', 'copy', '-video_track_timescale', str(rate.numerator), '-c:a', 'aac',
                  '-b:a', '128k', '-af', 'aresample=async=1:first_pts=0', '-movflags', '+faststart',
                  partial], work / 'merge.log')
    require(not result.stderr.strip(), f"Review merge warnings: {work / 'merge.log'}")
    data = probe(partial)
    v, a = stream(data, 'video'), stream(data, 'audio')
    require(int(v['nb_frames']) == offset, 'Final frame count mismatch')
    require(abs(float(v['start_time'])) < 0.00001, 'Final picture starts after zero')
    require(abs(float(data['format']['duration']) - float(duration)) < 0.05, 'Final duration mismatch')
    require(abs(float(a['duration']) - float(duration)) < 0.05, 'Final audio duration mismatch')
    require(len(data['chapters']) == len(records), 'Incorrect chapter count')
    for chapter, record in zip(data['chapters'], records):
        require(chapter['tags']['title'] == f"Episode {record['episode']:02d}", 'Chapter title mismatch')
        # FFmpeg stores MP4 chapter times in milliseconds.
        for field, frame_key in [('start_time', 'start_frame'), ('end_time', 'end_frame')]:
            require(abs(float(chapter[field]) - float(record[frame_key] / rate)) <= 0.0011,
                    f'Incorrect chapter {field}')
    rows = packets(partial)
    time_base = Fraction(v['time_base'])
    require(len(rows) == offset, 'Packet/frame count mismatch')
    require(all(int(p['pts']) * time_base == i / rate and
                int(p['duration']) * time_base == 1 / rate for i, p in enumerate(rows)),
            'Gap or irregular duration in final video timeline')
    decode(partial, work / 'decode.log')
    require(not final.exists(), f'Final file appeared during processing: {final}')
    partial.rename(final)
    report = {'file': str(final), 'episodes': [r['episode'] for r in records], 'chapters': len(records),
              'duration_seconds': float(duration), 'size_bytes': final.stat().st_size,
              'sha256': digest(final), 'frame_rate': str(rate), 'video_frames': offset,
              'continuous_video_timestamps': True, 'chapter_boundaries_verified': True,
              'full_audio_video_decode_passed': True, 'trims': records}
    write_json(final.with_suffix('.verification.json'), report)
    final.with_suffix('.chapters.txt').write_text('\n'.join(chapter_text) + '\n')
    if not args.keep_work:
        shutil.rmtree(work)
    print(json.dumps({k: v for k, v in report.items() if k != 'trims'}, indent=2), flush=True)


def escape_metadata(value):
    require('\n' not in value and '\r' not in value, 'Title must be a single line')
    return re.sub(r'([\\=;#])', r'\\\1', value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['audit', 'build']:
        p = sub.add_parser(command)
        p.add_argument('--episodes', required=True)
        p.add_argument('--output', required=True)
        p.add_argument('--range', help='Inclusive FIRST:LAST; retains episode numbering')
        p.add_argument('--expected-count', type=int)
        if command == 'audit':
            p.add_argument('--window', type=float, default=4)
        else:
            p.add_argument('--trim-end', required=True, help='Total seconds to cut from each original ending')
            p.add_argument('--trim-overrides', help='JSON object: episode number -> total trim seconds')
            p.add_argument('--title', default='Episode compilation')
            p.add_argument('--encoder', choices=['libx264', 'h264_videotoolbox'], default='libx264')
            p.add_argument('--bitrate', default='4000k', help='Hardware encoder bitrate')
            p.add_argument('--audio-rate', type=int, default=48000)
            p.add_argument('--keep-work', action='store_true')
            p.add_argument('--normalize-timing', action='store_true',
                           help='Repair source timestamp jitter of at most half a frame')
    args = parser.parse_args()
    for tool in ['ffmpeg', 'ffprobe']:
        require(shutil.which(tool), f'Missing executable: {tool}')
    (audit if args.command == 'audit' else build)(args)


if __name__ == '__main__':
    main()
