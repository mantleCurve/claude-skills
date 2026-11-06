#!/usr/bin/env bash
# render.sh <project-dir> <name> [name...]
#
# Renders <project-dir>/<name>.html (a 1080x1350 CSS px poster) with headless Chrome at device scale 2:
#   out/<name>.png          2160x2700 master (Instagram 4:5 at 2x)
#   out/<name>.jpg          high-quality JPEG of the master (ffmpeg -q:v 2)
#   out/preview-<name>.jpg  540px-wide preview, for looking at the result quickly
#
# Headless Chrome sometimes exits without writing anything when several renders run at once, so each
# render is tried up to 4 times and only counts when the PNG exists and is not empty.
# Chrome path: set $CHROME to override the default macOS location.
# Exit status is non-zero if any poster failed; the others still render.
set -uo pipefail

CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
TRIES=4

die() { echo "render.sh: error: $*" >&2; exit 1; }
[ $# -ge 2 ] || { echo "usage: render.sh <project-dir> <name> [name...]" >&2; exit 2; }
[ -d "$1" ] || die "project folder not found: $1"
proj=$(cd "$1" && pwd)
shift
[ -x "$CHROME" ] || die "Chrome not found at: $CHROME (set CHROME=/path/to/chrome)"
command -v ffmpeg >/dev/null 2>&1 || die "ffmpeg not found. Install it, e.g.: brew install ffmpeg"
mkdir -p "$proj/out"

failed=()
for name in "$@"; do
  name=${name%.html}
  html="$proj/$name.html"
  png="$proj/out/$name.png"
  if [ ! -f "$html" ]; then
    echo "render: $name: no such file $html" >&2
    failed+=("$name"); continue
  fi
  url="file://$(printf '%s' "$html" | sed -e 's/%/%25/g' -e 's/ /%20/g' -e 's/#/%23/g' -e 's/?/%3F/g')"

  ok=0
  for try in $(seq 1 $TRIES); do
    rm -f "$png"
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
      --force-device-scale-factor=2 --window-size=1080,1350 --virtual-time-budget=10000 \
      --screenshot="$png" "$url" >/dev/null 2>&1
    if [ -s "$png" ]; then ok=1; break; fi
    echo "render: $name: Chrome wrote no image (try $try of $TRIES)" >&2
    sleep $((try * 2))
  done
  if [ $ok -ne 1 ]; then
    echo "render: $name: FAILED after $TRIES tries" >&2
    failed+=("$name"); continue
  fi

  if ! ffmpeg -v error -y -i "$png" -frames:v 1 -q:v 2 "$proj/out/$name.jpg" ||
     ! ffmpeg -v error -y -i "$png" -frames:v 1 -vf scale=540:-1 "$proj/out/preview-$name.jpg"; then
    echo "render: $name: JPEG export failed" >&2
    failed+=("$name"); continue
  fi
  echo "render: $name -> $png"
done

if [ ${#failed[@]} -gt 0 ]; then
  echo "render.sh: failed: ${failed[*]}" >&2
  exit 1
fi
