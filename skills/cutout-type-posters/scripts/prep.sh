#!/usr/bin/env bash
# prep.sh <photo> <outdir>
#
# Turns one photo into every asset the poster templates use, all the same pixel size as the photo:
#   clean.png          the photo with a soft, slightly desaturated "clean" grade (all colour work starts here)
#   bw.png             black-and-white version of clean.png
#   mask.png           Apple Vision subject mask (white = subject)
#   cutout.png         clean.png with the background transparent (for light backgrounds)
#   cutout-dark.png    tighter cutout, mask eroded + softened, so no light halo shows on dark backgrounds
#   comp-bw-color.png  colour subject over the black-and-white room
#   subject.json       {"width","height","x1","y1","x2","y2"}: photo size and the subject's bounding box
#
# Needs macOS 14+ (Vision foreground masks), the Swift toolchain (xcode-select --install) and ffmpeg.
set -euo pipefail

die() { echo "prep.sh: error: $*" >&2; exit 1; }

[ $# -eq 2 ] || { echo "usage: prep.sh <photo> <outdir>" >&2; exit 2; }
photo=$1
out=$2
here=$(cd "$(dirname "$0")" && pwd)

command -v swift   >/dev/null 2>&1 || die "swift not found. Install the command line tools: xcode-select --install"
command -v ffmpeg  >/dev/null 2>&1 || die "ffmpeg not found. Install it, e.g.: brew install ffmpeg"
command -v ffprobe >/dev/null 2>&1 || die "ffprobe not found (it ships with ffmpeg). Install it, e.g.: brew install ffmpeg"
[ -f "$here/cutout.swift" ] || die "cutout.swift is missing next to prep.sh ($here)"
[ -f "$photo" ] || die "photo not found: $photo"
mkdir -p "$out"

# 0. Normalise the input to an 8-bit RGBA PNG so Vision and ffmpeg see exactly the same pixels.
src="$out/.prep-source.png"
raw="$out/.prep-vision-cutout.png"
trap 'rm -f "$src" "$raw"' EXIT
ffmpeg -v error -y -i "$photo" -frames:v 1 -vf format=rgba "$src" \
  || die "ffmpeg could not read $photo (for HEIC, convert first: sips -s format png in.heic --out in.png)"

# 1. Subject mask with Apple Vision.
echo "prep: finding the subject with Apple Vision..."
if ! vision_log=$(swift "$here/cutout.swift" "$src" "$raw" "$out/mask.png" 2>&1); then
  echo "$vision_log" >&2
  case "$vision_log" in
    *"no subject found"*) die "Vision found no foreground subject in $photo. Use a photo with one clear person, pet or object." ;;
    *) die "the Vision cutout failed (needs macOS 14 or later)." ;;
  esac
fi

# 2. Clean grade: gentle S-curve, cool shadows, a little less saturation, light sharpening.
GRADE="curves=r='0/0.0 0.25/0.24 0.5/0.55 0.8/0.86 1/1':g='0/0.0 0.25/0.245 0.5/0.555 0.8/0.865 1/1':b='0/0.01 0.25/0.26 0.5/0.57 0.8/0.88 1/1',eq=saturation=0.88:contrast=1.04,colorbalance=rh=-0.03:bh=0.03:rm=-0.01,unsharp=5:5:0.6"
echo "prep: grading..."
ffmpeg -v error -y -i "$src" -vf "$GRADE,format=rgb24" "$out/clean.png"
ffmpeg -v error -y -i "$out/clean.png" -vf "hue=s=0,curves=all='0/0.08 0.5/0.6 1/1',format=rgb24" "$out/bw.png"

# 3. Cutouts: the graded photo with the Vision mask as alpha.
echo "prep: building cutouts..."
ffmpeg -v error -y -i "$out/clean.png" -i "$out/mask.png" \
  -filter_complex "[1:v]format=gray[m];[0:v][m]alphamerge,format=rgba" "$out/cutout.png"
ffmpeg -v error -y -i "$out/clean.png" -i "$out/mask.png" \
  -filter_complex "[1:v]format=gray,erosion,erosion,erosion,erosion,gblur=sigma=1.1[m];[0:v][m]alphamerge,format=rgba" "$out/cutout-dark.png"
ffmpeg -v error -y -i "$out/bw.png" -i "$out/cutout.png" \
  -filter_complex "[0:v][1:v]overlay=format=auto,format=rgb24" "$out/comp-bw-color.png"

# 4. Subject bounding box from the mask (pixels brighter than 60/255 count as subject).
IFS=x read -r W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$out/mask.png")
bbox=$(ffmpeg -hide_banner -i "$out/mask.png" -vf "format=gray,bbox=min_val=60" -f null - 2>&1 | grep -o 'x1:[0-9-]* x2:[0-9-]* y1:[0-9-]* y2:[0-9-]*' | tail -1 || true)
[ -n "$bbox" ] || die "the subject mask is empty, so there is no subject to place. Try a photo with a clearer subject."
x1=$(echo "$bbox" | sed 's/.*x1:\([0-9-]*\).*/\1/'); x2=$(echo "$bbox" | sed 's/.*x2:\([0-9-]*\).*/\1/')
y1=$(echo "$bbox" | sed 's/.*y1:\([0-9-]*\).*/\1/'); y2=$(echo "$bbox" | sed 's/.*y2:\([0-9-]*\).*/\1/')
[ "$x2" -gt "$x1" ] && [ "$y2" -gt "$y1" ] || die "the subject mask is empty, so there is no subject to place."
printf '{"width": %d, "height": %d, "x1": %d, "y1": %d, "x2": %d, "y2": %d}\n' "$W" "$H" "$x1" "$y1" "$x2" "$y2" > "$out/subject.json"

echo "prep: done -> $(cd "$out" && pwd)"
echo "  photo ${W}x${H}; subject box x ${x1}..${x2}, y ${y1}..${y2} (centre x $(( (x1 + x2) / 2 )), feet y ${y2})"
cat "$out/subject.json"
