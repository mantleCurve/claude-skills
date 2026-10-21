#!/usr/bin/env python3
"""Local integration checks. Generate tiny fixtures; never contact a real media site."""
import functools
import http.server
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from episode_media import digest, probe, stream

SCRIPTS = Path(__file__).resolve().parent


def command(*args, success=True):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if success and result.returncode:
        raise AssertionError(result.stderr + result.stdout)
    if not success and result.returncode == 0:
        raise AssertionError('Expected a failure')
    return result


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='episode-pipeline-test-')
        cls.root = Path(cls.temp.name)
        cls.sources = cls.root / 'sources'
        cls.sources.mkdir()
        for n in range(4, 9):
            command('ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=25:duration=2.4',
                    '-f', 'lavfi', '-i', f'sine=frequency={300+n*100}:sample_rate=44100:duration=3.48',
                    '-vf', 'tpad=stop_mode=clone:stop_duration=1,setpts=PTS+0.08/TB',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '0', '-bf', '0', '-g', '25',
                    '-fps_mode:v', 'passthrough', '-c:a', 'aac', cls.sources / f'Episode_{n:02d}.mp4')
        cls.hashes = {p.name: digest(p) for p in cls.sources.glob('*.mp4')}
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0),
                        functools.partial(QuietHandler, directory=str(cls.root)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def test_audit_and_five_episode_cut(self):
        audit = self.root / 'audit.json'
        command(sys.executable, SCRIPTS / 'episode_media.py', 'audit', '--episodes', self.sources,
                '--range', '4:8', '--output', audit)
        records = json.loads(audit.read_text())
        self.assertEqual([r['episode'] for r in records], [4, 5, 6, 7, 8])
        self.assertTrue(all(r['exact_tail_frames'] >= 25 for r in records))
        output = self.root / 'test-cut.mp4'
        command(sys.executable, SCRIPTS / 'episode_media.py', 'build', '--episodes', self.sources,
                '--range', '4:8', '--trim-end', '2.04', '--output', output)
        report = json.loads(output.with_suffix('.verification.json').read_text())
        self.assertEqual(report['episodes'], [4, 5, 6, 7, 8])
        self.assertEqual(report['chapters'], 5)
        self.assertEqual(report['video_frames'], 170)
        self.assertAlmostEqual(report['duration_seconds'], 6.8)
        self.assertTrue(all(r['trim_frames'] == 51 for r in report['trims']))
        self.assertTrue(all(abs(r['audio_offset_seconds'] - 0.08) < 0.001 for r in report['trims']))
        self.assertEqual({p.name: digest(p) for p in self.sources.glob('*.mp4')}, self.hashes)
        self.assertFalse(output.with_suffix('.work').exists())
        before = digest(output)
        command(sys.executable, SCRIPTS / 'episode_media.py', 'build', '--episodes', self.sources,
                '--range', '4:8', '--trim-end', '2.04', '--output', output, success=False)
        self.assertEqual(digest(output), before)

    def test_fractional_rate_and_override(self):
        folder = self.root / 'fractional'
        folder.mkdir()
        command('ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=30000/1001:duration=2.002',
                '-f', 'lavfi', '-i', 'sine=sample_rate=48000:duration=2.002',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-bf', '0', '-c:a', 'aac',
                folder / 'Episode_01.mp4')
        overrides = self.root / 'overrides.json'
        overrides.write_text('{"1": 0.5}')
        output = self.root / 'fractional.mp4'
        command(sys.executable, SCRIPTS / 'episode_media.py', 'build', '--episodes', folder,
                '--expected-count', '1', '--trim-end', '0', '--trim-overrides', overrides,
                '--output', output)
        report = json.loads(output.with_suffix('.verification.json').read_text())
        self.assertEqual(report['frame_rate'], '30000/1001')
        self.assertEqual(report['trims'][0]['trim_frames'], 15)
        self.assertEqual(report['video_frames'], 45)

    def test_download_hls_direct_and_resume(self):
        hls = self.root / 'hls'
        hls.mkdir()
        command('ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-i', self.sources / 'Episode_04.mp4', '-c', 'copy', '-f', 'hls', '-hls_time', '1',
                '-hls_list_size', '0', '-hls_segment_filename', hls / 'seg%03d.ts', hls / 'high.m3u8')
        (hls / 'master.m3u8').write_text('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=320x180\nhigh.m3u8\n')
        manifest = self.root / 'download-sources.json'
        manifest.write_text(json.dumps([
            {'episode': 1, 'url': self.url + '/hls/master.m3u8'},
            {'episode': 2, 'url': self.url + '/sources/Episode_05.mp4'}]))
        output = self.root / 'downloaded'
        argv = [sys.executable, SCRIPTS / 'download_episodes.py', '--manifest', manifest,
                '--expected-count', '2', '--output', output]
        command(*argv)
        report = json.loads((output / 'download-manifest.json').read_text())
        self.assertEqual(len(report), 2)
        self.assertTrue(all(r['full_audio_video_decode_passed'] for r in report))
        self.assertEqual(stream(probe(output / 'Episode_01.mp4'), 'video')['width'], 320)
        second = command(*argv)
        self.assertEqual(second.stdout.count('reused verified source'), 2)
        with (output / 'Episode_01.mp4').open('ab') as f:
            f.write(b'changed')
        command(*argv, success=False)

    def test_reject_missing_episode_and_unowned_work(self):
        command(sys.executable, SCRIPTS / 'episode_media.py', 'build', '--episodes', self.sources,
                '--range', '3:8', '--trim-end', '0', '--output', self.root / 'missing.mp4', success=False)
        output = self.root / 'unowned.mp4'
        folder = output.with_suffix('.work')
        folder.mkdir()
        sentinel = folder / 'keep.txt'
        sentinel.write_text('unrelated')
        command(sys.executable, SCRIPTS / 'episode_media.py', 'build', '--episodes', self.sources,
                '--range', '4:8', '--trim-end', '0', '--output', output, success=False)
        self.assertEqual(sentinel.read_text(), 'unrelated')

    def test_late_audio_stays_late(self):
        folder = self.root / 'late-audio'
        folder.mkdir()
        command('ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=25:duration=3',
                '-itsoffset', '0.5', '-f', 'lavfi', '-i', 'sine=sample_rate=48000:duration=2.5',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-bf', '0', '-c:a', 'aac',
                folder / 'Episode_01.mp4')
        output = self.root / 'late-audio.mp4'
        command(sys.executable, SCRIPTS / 'episode_media.py', 'build', '--episodes', folder,
                '--expected-count', '1', '--trim-end', '0', '--output', output)
        report = json.loads(output.with_suffix('.verification.json').read_text())
        self.assertLess(report['trims'][0]['audio_offset_seconds'], -0.4)
        samples = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-t', '0.25',
                                  '-vn', '-f', 's16le', '-'], capture_output=True, check=True).stdout
        import array
        values = array.array('h', samples)
        self.assertTrue(values)
        self.assertLess(max(abs(v) for v in values), 10, 'Leading silence was lost')

    def test_reject_unsupported_hls(self):
        bad = self.root / 'encrypted.m3u8'
        bad.write_text('#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="key"\n#EXTINF:1,\nseg.ts\n#EXT-X-ENDLIST\n')
        manifest = self.root / 'unsupported.json'
        manifest.write_text(json.dumps([{'episode': 1, 'url': self.url + '/encrypted.m3u8'}]))
        output = self.root / 'unsupported'
        result = command(sys.executable, SCRIPTS / 'download_episodes.py', '--manifest', manifest,
                         '--expected-count', '1', '--output', output, success=False)
        self.assertIn('Unsupported HLS feature', result.stderr)
        self.assertFalse((output / 'Episode_01.mp4').exists())


if __name__ == '__main__':
    for executable in ['ffmpeg', 'ffprobe', 'curl']:
        if not shutil.which(executable):
            raise SystemExit(f'Required for integration tests: {executable}')
    unittest.main(verbosity=2)
