#!/usr/bin/env python3
"""Tests for accent.py. Run: python3 scripts/test_accent.py

Fixtures (PPM/PNG images, preview HTML) are written to $ACCENT_TEST_FIXTURES, else to
<skill>/.test-fixtures/ (git-ignored). Never to a system temp folder.
"""
import html.parser
import json
import math
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import accent as A  # noqa: E402

ACCENT_PY = str(SCRIPTS / "accent.py")
FIXTURES = Path(os.environ.get("ACCENT_TEST_FIXTURES") or SCRIPTS.parent / ".test-fixtures")

# The nine palettes from the three reels (BASE1 Mood, BASE2 Support, ACCENT).
REEL = [
    ("#0593C6", "#FCFFFF", "#D83995"),
    ("#02070A", "#0297DE", "#FC734D"),
    ("#09318D", "#FFFFFF", "#FD91CC"),
    ("#21232E", "#105BFF", "#FE8500"),
    ("#F0F0F0", "#533DFB", "#FA67D0"),
    ("#74FFED", "#171F44", "#FE81D1"),
    ("#FD550A", "#015D47", "#E0F354"),
    ("#01010D", "#6331FB", "#88F9C0"),
    ("#DBF2FC", "#072D59", "#FD6E88"),
]
HAS_FFMPEG = shutil.which("ffmpeg") is not None


def run(*args, env=None):
    return subprocess.run([sys.executable, ACCENT_PY, *args], capture_output=True, text=True, env=env)


def status_of(res, cid):
    return [c["status"] for c in res["checks"] if c["id"] == cid]


def write_ppm(path, w, h, bg, fg=None, fg_pixels=0):
    """Pure-Python P6 image: background with the first fg_pixels pixels in fg colour."""
    data = bytearray()
    for i in range(w * h):
        data += bytes(fg if fg and i < fg_pixels else bg)
    path.write_bytes(b"P6\n%d %d\n255\n" % (w, h) + bytes(data))
    return path


class ColourMaths(unittest.TestCase):
    def test_contrast_extremes(self):
        self.assertAlmostEqual(A.contrast((255, 255, 255), (0, 0, 0)), 21.0, places=6)
        self.assertAlmostEqual(A.contrast((0, 0, 0), (255, 255, 255)), 21.0, places=6)
        self.assertEqual(A.contrast((10, 20, 30), (10, 20, 30)), 1.0)

    def test_grey_767676_on_white(self):
        r = A.contrast(A.parse_hex("#767676"), (255, 255, 255))
        self.assertAlmostEqual(r, 4.54, places=2)
        self.assertGreaterEqual(r, 4.5)
        self.assertEqual(A.fmt_ratio(r), "4.54:1")

    def test_ratio_never_rounds_up(self):
        self.assertEqual(A.fmt_ratio(4.4999), "4.49:1")

    def test_hex_parsing(self):
        for text in ("#abc", "abc", "#aabbcc", "aabbcc", "  #AABBCC "):
            self.assertEqual(A.to_hex(A.parse_hex(text)), "#AABBCC")
        for bad in ("", "#ab", "abcd", "zzzzzz", "#12345g", "#1234567", "red"):
            with self.assertRaises(A.ColourError, msg=bad):
                A.parse_hex(bad)

    def test_reference_oklch(self):
        L, C, h = A.rgb_to_oklch((255, 0, 0))  # published: oklch(62.80% 0.2577 29.23)
        self.assertAlmostEqual(L, 0.6280, places=3)
        self.assertAlmostEqual(C, 0.2577, places=3)
        self.assertAlmostEqual(h, 29.23, places=1)
        L, C, _ = A.rgb_to_oklch((255, 255, 255))
        self.assertAlmostEqual(L, 1.0, places=4)
        self.assertLess(C, 1e-4)

    def test_oklch_round_trip(self):
        vals = list(range(0, 256, 15)) + [255]
        for r in vals:
            for g in vals:
                for b in vals:
                    rgb, clipped = A.oklch_to_rgb(*A.rgb_to_oklch((r, g, b)))
                    self.assertEqual(rgb, (r, g, b))
                    self.assertFalse(clipped)

    def test_gamut_clip_reduces_chroma_only(self):
        rgb, clipped = A.oklch_to_rgb(0.7, 0.4, 150.0)
        self.assertTrue(clipped)
        L, C, h = A.rgb_to_oklch(rgb)
        self.assertAlmostEqual(L, 0.7, delta=0.01)
        self.assertAlmostEqual(h, 150.0, delta=2.0)
        self.assertLess(C, 0.4)

    def test_hue_distance_wraps(self):
        self.assertEqual(A.hue_dist(350, 10), 20)
        self.assertEqual(A.hue_dist(0, 180), 180)


class Analyze(unittest.TestCase):
    def test_reel_palettes_have_no_fail(self):
        for b1, b2, acc in REEL:
            res = A.analyze(b1, b2, acc)
            fails = [c for c in res["checks"] if c["status"] == "FAIL"]
            self.assertEqual(fails, [], "%s %s %s" % (b1, b2, acc))
            self.assertEqual(status_of(res, "text-on-accent"), ["PASS"])

    def test_reel_palette_cli_exit_zero(self):
        p = run("analyze", "21232E", "105BFF", "FE8500")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Verdict", p.stdout)

    def test_monochrome_baseline_fails_hue_distance(self):
        res = A.analyze("#09318D", "#FFFFFF", "#2F6BFF")
        self.assertEqual(status_of(res, "hue-distance"), ["FAIL"])
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(run("analyze", "#09318D", "#FFFFFF", "#2F6BFF").returncode, 1)

    def test_second_accent_hue_fails(self):
        res = A.analyze("#21232E", "#105BFF", "#FE8500", extras=["#8B5CF6", "#1A1C25", "#3D7BFF"])
        st = [c["status"] for c in res["checks"] if c["id"] == "extra"]
        self.assertEqual(st, ["FAIL", "PASS", "PASS"])  # violet competes; neutral and blue tint are fine

    def test_near_neutral_bases_ignore_hue(self):
        res = A.analyze("#FFFFFF", "#141414", "#FE8500")
        self.assertEqual(status_of(res, "hue-distance"), ["PASS"])
        self.assertEqual(res["hue_distances"], {"BASE1": None, "BASE2": None})

    def test_muted_accent_fails_chroma(self):
        res = A.analyze("#09318D", "#FFFFFF", "#9A8F85")
        self.assertEqual(status_of(res, "chroma"), ["FAIL"])

    def test_semantic_collision_warns(self):
        self.assertEqual(status_of(A.analyze("#DBF2FC", "#072D59", "#FD6E88"), "semantic"), ["WARN"])

    def test_json_and_bad_hex(self):
        p = run("analyze", "abc", "#fff", "#FE8500", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("contrast", json.loads(p.stdout))
        p = run("analyze", "#12345", "#FFFFFF")
        self.assertEqual(p.returncode, 2)
        self.assertIn("not a hex colour", p.stderr)


class Suggest(unittest.TestCase):
    def test_deep_blue_white(self):
        res = A.suggest("#09318D", "#FFFFFF", count=6)
        self.assertEqual(len(res["candidates"]), 6)
        bg = A.parse_hex(res["background"])
        for c in res["candidates"]:
            rgb = A.parse_hex(c["hex"])
            self.assertTrue(A.in_gamut(*A.rgb_to_oklch(rgb), eps=1e-4), c["hex"])
            self.assertGreaterEqual(A.contrast(rgb, bg), 3.0, c["hex"])
            self.assertGreaterEqual(A.contrast(A.parse_hex(c["text"]), rgb), 4.5, c["hex"])
        top = A.parse_hex(res["candidates"][0]["hex"])
        d = A.hue_dist(A.rgb_to_oklch(top)[2], A.rgb_to_oklch(A.parse_hex("#09318D"))[2])
        self.assertGreaterEqual(d, 90.0)
        self.assertGreaterEqual(A.contrast(top, bg), 3.0)
        self.assertEqual(A.analyze("#09318D", "#FFFFFF", res["candidates"][0]["hex"])["verdict"] != "FAIL", True)

    def test_deterministic_and_modes(self):
        self.assertEqual(A.suggest("#21232E", "#105BFF"), A.suggest("#21232E", "#105BFF"))
        for mode in ("light", "dark"):
            res = A.suggest("#21232E", "#105BFF", count=4, mode=mode)
            bg = A.parse_hex(res["background"])
            self.assertEqual(res["mode"], mode)
            for c in res["candidates"]:
                self.assertGreaterEqual(A.contrast(A.parse_hex(c["hex"]), bg), 3.0)

    def test_cli(self):
        p = run("suggest", "#21232E", "#105BFF", "--count", "3", "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(json.loads(p.stdout)["candidates"]), 3)


class Tokens(unittest.TestCase):
    TEXT_PAIRS = [("text", "surface"), ("text", "surface-raised"), ("text-muted", "surface"),
                  ("text-muted", "surface-raised"), ("brand-text", "surface"), ("on-accent", "accent"),
                  ("on-accent", "accent-hover"), ("on-accent", "accent-active"),
                  ("accent-soft-text", "accent-soft"), ("danger", "surface"), ("warning", "surface"),
                  ("success", "surface")]

    def test_text_pairs_pass_everywhere(self):
        for b1, b2, acc in REEL + [("#09318D", "#FFFFFF", "#2F6BFF")]:
            for mode in ("auto", "light", "dark"):
                res = A.build_tokens(b1, b2, acc, mode)
                T = {k: A.parse_hex(v["hex"]) for k, v in res["tokens"].items()}
                for fg, bg in self.TEXT_PAIRS:
                    self.assertGreaterEqual(A.contrast(T[fg], T[bg]), 4.5, "%s/%s %s %s %s" % (fg, bg, b1, b2, mode))
                for fg in ("accent", "focus-ring", "border-strong"):
                    self.assertGreaterEqual(A.contrast(T[fg], T["surface"]), 3.0, "%s %s %s" % (fg, b1, mode))
                self.assertTrue(all(p["ok"] for p in res["contrast"]))

    def test_bases_kept_and_accent_hue_kept(self):
        res = A.build_tokens("#21232E", "#105BFF", "#FE8500", "light")
        T = res["tokens"]
        self.assertEqual((T["mood"]["hex"], T["support"]["hex"]), ("#21232E", "#105BFF"))
        h0 = A.rgb_to_oklch(A.parse_hex("#FE8500"))[2]
        h1 = A.rgb_to_oklch(A.parse_hex(T["accent"]["hex"]))[2]
        self.assertLess(A.hue_dist(h0, h1), 3.0)
        self.assertTrue(any("accent lightness" in n for n in res["notes"]))

    def test_semantic_hue_moves_away_from_accent(self):
        res = A.build_tokens("#DBF2FC", "#072D59", "#FD6E88")
        ha = A.rgb_to_oklch(A.parse_hex(res["tokens"]["accent"]["hex"]))[2]
        hd = A.rgb_to_oklch(A.parse_hex(res["tokens"]["danger"]["hex"]))[2]
        self.assertGreater(A.hue_dist(ha, hd), A.hue_dist(ha, A.SEMANTIC["danger"][0]))

    def test_formats(self):
        css = run("tokens", "#09318D", "#FFFFFF", "#FD91CC", "--selector", "[data-theme=dark]")
        self.assertEqual(css.returncode, 0, css.stderr)
        self.assertIn("[data-theme=dark] {", css.stdout)
        self.assertIn("--color-on-accent:", css.stdout)
        tw = run("tokens", "#09318D", "#FFFFFF", "#FD91CC", "--format", "tailwind", "--mode", "light")
        self.assertIn("@theme {", tw.stdout)
        js = json.loads(run("tokens", "#09318D", "#FFFFFF", "#FD91CC", "--format", "json").stdout)
        self.assertIn("accent-hover", js["tokens"])


class TagBalance(html.parser.HTMLParser):
    VOID = {"meta", "br", "img", "input", "link", "hr"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(tag)
        else:
            self.stack.pop()


class PreviewAndCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FIXTURES.mkdir(parents=True, exist_ok=True)

    def test_preview_html(self):
        out = FIXTURES / "preview-test.html"
        p = run("preview", "#21232E", "#105BFF", "#FE8500", "-o", str(out))
        self.assertEqual(p.returncode, 0, p.stderr)
        text = out.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("<!doctype html>"))
        for needle in ("Base pair only", "With accent", "#FE8500", "Contrast (WCAG"):
            self.assertIn(needle, text)
        self.assertNotIn("http://", text.replace("http://www.w3.org", ""))  # self-contained
        tb = TagBalance()
        tb.feed(text)
        self.assertEqual((tb.errors, tb.stack), ([], []))

    @unittest.skipUnless(HAS_FFMPEG, "ffmpeg not installed")
    def test_coverage_levels(self):
        bg, acc = (0x21, 0x23, 0x2E), (0xFE, 0x85, 0x00)
        cases = [(0.06, "PASS", 0), (0.0, "WARN", 0), (0.20, "WARN", 0), (0.40, "FAIL", 1)]
        for share, status, code in cases:
            path = write_ppm(FIXTURES / ("coverage-%02d.ppm" % int(share * 100)), 100, 100, bg, acc, int(share * 10000))
            res = A.coverage(str(path), "#FE8500", size=100)
            self.assertEqual(res["status"], status, share)
            self.assertAlmostEqual(res["percent"], share * 100, delta=0.01)
            self.assertEqual(run("coverage", str(path), "#FE8500", "--size", "100").returncode, code)

    @unittest.skipUnless(HAS_FFMPEG, "ffmpeg not installed")
    def test_coverage_png_from_lavfi(self):
        png = FIXTURES / "coverage-lavfi.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x21232E:s=200x200",
                        "-f", "lavfi", "-i", "color=c=0xFE8500:s=40x50", "-filter_complex", "overlay=20:20",
                        "-frames:v", "1", str(png)], check=True)
        res = A.coverage(str(png), "#FE8500", size=200)
        self.assertAlmostEqual(res["percent"], 5.0, delta=0.6)
        self.assertEqual(res["status"], "PASS")

    def test_coverage_without_ffmpeg(self):
        env = dict(os.environ, PATH=str(FIXTURES / "no-such-bin"))
        path = write_ppm(FIXTURES / "coverage-noffmpeg.ppm", 10, 10, (0, 0, 0))
        p = run("coverage", str(path), "#FE8500", env=env)
        self.assertEqual(p.returncode, 2)
        self.assertIn("ffmpeg not found", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
