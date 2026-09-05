#!/usr/bin/env bash
# Stage the publish tree for Cloudflare Pages into .cf-dist/
#
# This is the Pages "build command". It exists because website/ is both the
# static site and its source tree: src/, vite.config.js and package.json live
# inside the folder Netlify published wholesale, which put them on the public
# site. Publishing a staged copy keeps build sources off Cloudflare.
#
# Pages build settings that match this script:
#   Build command:           bash scripts/build-cf.sh
#   Build output directory:  .cf-dist
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/website"
STAGE="$ROOT/.cf-dist"

rm -rf "$STAGE"
cp -r "$SRC" "$STAGE"

# Build sources, tooling and local config must not be published.
rm -rf "$STAGE/src" "$STAGE/scripts" "$STAGE/node_modules" \
       "$STAGE/.claude" "$STAGE/.wrangler" "$STAGE/dist"
rm -f  "$STAGE/package.json" "$STAGE/package-lock.json" \
       "$STAGE/vite.config.js" "$STAGE/tailwind.config.js" \
       "$STAGE/postcss.config.js" "$STAGE/DEPLOYMENT.md" \
       "$STAGE/.env" "$STAGE/.env.example"

# 404.html at the top level is load-bearing: without it Pages treats the site
# as a single-page app and answers every unmatched path with / at status 200.
if [[ ! -f "$STAGE/404.html" ]]; then
  echo "ERROR: $STAGE/404.html missing -- Pages would soft-404 the whole site." >&2
  exit 1
fi

# Pages rejects any single asset over 25 MiB; fail loudly rather than mid-upload.
if find "$STAGE" -type f -size +25M | grep -q .; then
  echo "ERROR: asset(s) over the 25 MiB Cloudflare Pages limit:" >&2
  find "$STAGE" -type f -size +25M -printf '  %s %p\n' >&2
  exit 1
fi

echo "Staged $(find "$STAGE" -type f | wc -l) files into .cf-dist"
