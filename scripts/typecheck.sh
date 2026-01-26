#!/usr/bin/env bash
set -euo pipefail
# Enterprise typecheck wrapper ensuring consistent module discovery.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src"

echo "[typecheck] Running mypy with strict enterprise config"
poetry run mypy -p core -p cli -p modules -p kits "$@"
