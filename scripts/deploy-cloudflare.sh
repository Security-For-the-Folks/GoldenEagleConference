#!/usr/bin/env bash
# Deploy the static site in website/ to Cloudflare Pages (direct upload).
#
# Stages a clean copy first: website/ contains build sources (src/, vite config,
# package.json) and tooling that must not be published. Netlify published them
# by mistake; this staging step is what keeps them off Cloudflare.
#
# Usage: scripts/deploy-cloudflare.sh [--production]
set -euo pipefail

PROJECT="themocs"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/website"
STAGE="$ROOT/.cf-dist"

rm -rf "$STAGE"
cp -r "$SRC" "$STAGE"

# Drop build sources, tooling and local config from the publish tree.
rm -rf "$STAGE/src" "$STAGE/scripts" "$STAGE/node_modules" \
       "$STAGE/.claude" "$STAGE/.wrangler" "$STAGE/dist"
rm -f  "$STAGE/package.json" "$STAGE/package-lock.json" \
       "$STAGE/vite.config.js" "$STAGE/tailwind.config.js" \
       "$STAGE/postcss.config.js" "$STAGE/DEPLOYMENT.md" \
       "$STAGE/.env" "$STAGE/.env.example"

# Pages rejects any single asset over 25 MiB; fail loudly rather than mid-upload.
if find "$STAGE" -type f -size +25M | grep -q .; then
  echo "ERROR: asset(s) over the 25 MiB Cloudflare Pages limit:" >&2
  find "$STAGE" -type f -size +25M -printf '  %s %p\n' >&2
  exit 1
fi

BRANCH_ARG=()
if [[ "${1:-}" == "--production" ]]; then
  BRANCH_ARG=(--branch main)
fi

npx wrangler pages deploy "$STAGE" --project-name "$PROJECT" "${BRANCH_ARG[@]}"
