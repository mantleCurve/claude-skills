#!/usr/bin/env bash
# Install one or all skills from this repo into ~/.claude/skills (or .claude/skills with --project).
# Usage: ./install.sh [--project] [skill-name ...]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude/skills"
if [ "${1:-}" = "--project" ]; then DEST=".claude/skills"; shift; fi
mkdir -p "$DEST"
if [ $# -eq 0 ]; then set -- $(ls "$HERE/skills"); fi
for s in "$@"; do
  [ -d "$HERE/skills/$s" ] || { echo "no such skill: $s" >&2; exit 1; }
  rm -rf "$DEST/$s"; cp -r "$HERE/skills/$s" "$DEST/$s"
  echo "installed $s -> $DEST/$s"
done
echo "Start a new Claude Code session to pick them up."
