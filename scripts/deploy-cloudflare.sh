#!/usr/bin/env bash
# Deploy website/ to Cloudflare Pages by direct upload from a workstation.
#
# Only needed for out-of-band deploys. The Pages project is git-connected and
# builds on push; see website/DEPLOYMENT.md for the build settings.
#
# Usage: scripts/deploy-cloudflare.sh [--production]
set -euo pipefail

PROJECT="themocs"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$ROOT/scripts/build-cf.sh"

BRANCH_ARG=()
if [[ "${1:-}" == "--production" ]]; then
  BRANCH_ARG=(--branch main)
fi

npx wrangler pages deploy "$ROOT/.cf-dist" --project-name "$PROJECT" "${BRANCH_ARG[@]}"
