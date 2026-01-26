#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_REMOTE="${UPSTREAM_REMOTE:-upstream}"
BRANCH="${BRANCH:-main}"

echo "== Fetch upstream =="
git fetch "$UPSTREAM_REMOTE" --tags

echo "== Merge fast-forward =="
git merge --ff-only "$UPSTREAM_REMOTE/$BRANCH" || {
  echo "Cannot fast-forward. Resolve manually." >&2; exit 1; }

echo "== Diff all =="
rapidkit diff all --json > .rapidkit/last-diff.json || true

echo "== Auto merge template_updated files =="
rapidkit merge module --auto-apply-template-updated --strategy prefer-template || true

echo "Done. Review .rapidkit/last-diff.json"
