#!/usr/bin/env python3
"""Screenshot an HTML file with headless Chrome. Stdlib only.

    python3 screenshot.py <page.html> <out.png> [--width 1280] [--height 1400] [--wrap]

--wrap prefixes the page with the document skeleton (<!doctype html><html><head><meta charset>
<meta viewport>) that the artifact host adds: use it for specimen/index.html and tester.html,
which start at <title> and have no doctype of their own. Proof sheets from proof.py are complete
documents and need no wrapping. Chrome refuses windows narrower than about 500 px, so a phone-width
shot is taken inside an iframe of the requested width.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SKELETON = ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">')


def find_chrome():
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(p):
            return p
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def shoot(src, out, width=1280, height=1400, wrap=False):
    chrome = find_chrome()
    if not chrome:
        sys.exit("headless Chrome not found; install Google Chrome or Chromium")
    src = os.path.abspath(src)
    out = os.path.abspath(out)
    tmpdir = tempfile.mkdtemp(prefix="shot-", dir=os.path.dirname(src))
    try:
        page = src
        if wrap:
            page = os.path.join(tmpdir, "wrapped.html")
            with open(page, "w", encoding="utf-8") as f:
                f.write(SKELETON + open(src, encoding="utf-8").read())
        win_w = width
        if width < 500:
            frame = os.path.join(tmpdir, "frame.html")
            with open(frame, "w", encoding="utf-8") as f:
                f.write(SKELETON + '<style>body{margin:0}iframe{display:block;width:%dpx;height:%dpx;border:0}</style>'
                        '</head><body><iframe src="file://%s"></iframe>' % (width, height, page))
            page, win_w = frame, 500
        subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=%d,%d" % (win_w, height), "--screenshot=%s" % out,
                        "file://" + page], check=True, capture_output=True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("page")
    ap.add_argument("png")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=1400)
    ap.add_argument("--wrap", action="store_true", help="prefix the artifact document skeleton")
    a = ap.parse_args()
    print("wrote", shoot(a.page, a.png, a.width, a.height, a.wrap))


if __name__ == "__main__":
    main()
