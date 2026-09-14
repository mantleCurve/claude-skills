#!/usr/bin/env bash
# Deploy a static site directory to a new GitHub Pages repo.
# Usage: deploy.sh <site-dir> <owner/repo> "<description>"
set -euo pipefail
DIR="$1"; REPO="$2"; DESC="${3:-Travel journey site}"
cd "$DIR"
if [ ! -d .git ]; then git init -q -b main; fi
git add -A
git -c user.name="$(gh api user --jq .login)" -c user.email="$(git config user.email || echo noreply@users.noreply.github.com)" \
  commit -q -m "Living itinerary site" || true
if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "Repo $REPO already exists; refusing to push into it. Pick a new name." >&2; exit 1
fi
gh repo create "$REPO" --public --source=. --remote=origin --push --description "$DESC" >/dev/null
gh api -X POST "repos/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/' --jq '.html_url'
OWNER="${REPO%%/*}"; NAME="${REPO##*/}"
URL="https://$(echo "$OWNER" | tr '[:upper:]' '[:lower:]').github.io/$NAME/"
for i in $(seq 1 24); do
  s=$(gh api "repos/$REPO/pages/builds/latest" --jq .status 2>/dev/null || true)
  if [ "$s" = "built" ] && [ "$(curl -s -o /dev/null -w '%{http_code}' "$URL")" = "200" ]; then break; fi
  sleep 10
done
echo "live: $URL ($(curl -s -o /dev/null -w '%{http_code}' "$URL"))"
echo "data.js: $(curl -s -o /dev/null -w '%{http_code}' "${URL}data.js")"
