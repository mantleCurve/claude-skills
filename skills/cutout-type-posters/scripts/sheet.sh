#!/usr/bin/env bash
# sheet.sh <project-dir>
#
# Builds a labelled contact sheet of every out/preview-*.jpg (made by render.sh) as out/sheet.jpg,
# by writing out/sheet.html (a grid, each tile captioned with its file name) and screenshotting it
# with headless Chrome. Chrome path: set $CHROME to override the default macOS location.
set -euo pipefail

CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
TRIES=4

die() { echo "sheet.sh: error: $*" >&2; exit 1; }
[ $# -eq 1 ] || { echo "usage: sheet.sh <project-dir>" >&2; exit 2; }
[ -d "$1/out" ] || die "no out/ folder in $1. Render some posters first with render.sh."
out=$(cd "$1/out" && pwd)
[ -x "$CHROME" ] || die "Chrome not found at: $CHROME (set CHROME=/path/to/chrome)"
command -v ffmpeg >/dev/null 2>&1 || die "ffmpeg not found. Install it, e.g.: brew install ffmpeg"

previews=()
while IFS= read -r f; do previews+=("$f"); done < <(cd "$out" && ls -1 preview-*.jpg 2>/dev/null | sort)
n=${#previews[@]}
[ "$n" -gt 0 ] || die "no out/preview-*.jpg in $1. Render some posters first with render.sh."

# Layout: an 88px title band, up to 4 columns of 400x500 tiles with a 44px caption under each, 24px gaps, 40px margins.
cols=$(( n < 4 ? n : 4 )); rows=$(( (n + cols - 1) / cols ))
W=$(( 80 + cols * 400 + (cols - 1) * 24 ))
H=$(( 88 + rows * 544 + (rows - 1) * 24 + 40 ))

esc() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/"/\&quot;/g'; }
{
  cat <<EOF
<!doctype html><html><head><meta charset="utf-8"><style>
body { margin: 0; background: #1a1a1a; color: #eee; font: 600 15px/1.2 -apple-system, "Helvetica Neue", Arial, sans-serif; }
h1 { margin: 0; padding: 40px 40px 0; height: 88px; box-sizing: border-box; font-size: 22px; letter-spacing: .08em; text-transform: uppercase; color: #fff; }
.g { display: grid; grid-template-columns: repeat($cols, 400px); gap: 24px; padding: 0 40px 40px; }
figure { margin: 0; } img { display: block; width: 400px; height: 500px; object-fit: cover; background: #333; }
figcaption { height: 44px; padding-top: 12px; box-sizing: border-box; letter-spacing: .06em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style></head><body><h1>Contact sheet &mdash; $n poster$( [ "$n" -eq 1 ] || echo s )</h1><div class="g">
EOF
  for f in "${previews[@]}"; do
    label=${f#preview-}; label=${label%.jpg}
    printf '<figure><img src="%s"><figcaption>%s</figcaption></figure>\n' "$(esc "$f")" "$(esc "$label")"
  done
  echo '</div></body></html>'
} > "$out/sheet.html"

url="file://$(printf '%s' "$out/sheet.html" | sed -e 's/%/%25/g' -e 's/ /%20/g' -e 's/#/%23/g' -e 's/?/%3F/g')"
png="$out/.sheet.png"
ok=0
for try in $(seq 1 $TRIES); do
  rm -f "$png"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --force-device-scale-factor=1 --window-size=$W,$H --virtual-time-budget=5000 \
    --screenshot="$png" "$url" >/dev/null 2>&1 || true
  if [ -s "$png" ]; then ok=1; break; fi
  echo "sheet: Chrome wrote no image (try $try of $TRIES)" >&2
  sleep $((try * 2))
done
[ $ok -eq 1 ] || die "Chrome failed to screenshot the sheet after $TRIES tries"
ffmpeg -v error -y -i "$png" -frames:v 1 -q:v 2 "$out/sheet.jpg"
rm -f "$png"
echo "sheet: $n posters -> $out/sheet.jpg"
