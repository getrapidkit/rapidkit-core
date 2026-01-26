#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from the core project root so Poetry reliably finds pyproject.toml,
# regardless of the caller's current working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <command> [args...]" >&2
  exit 1
fi

POETRY_BIN=${POETRY_BIN:-poetry}
TEST_PYTHON=${TEST_PYTHON:-}
INSTALL_ARGS=${POETRY_INSTALL_ARGS:-"--with dev"}

resolve_test_python() {
  if [ -n "${TEST_PYTHON:-}" ]; then
    echo "$TEST_PYTHON"
    return 0
  fi

  # Prefer pinned interpreter when available, but gracefully fall back on
  # platforms where python3.10 isn't packaged (e.g., Debian 13).
  for candidate in python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done

  return 1
}

if ! command -v "$POETRY_BIN" >/dev/null 2>&1; then
  echo "Poetry executable '$POETRY_BIN' not found in PATH." >&2
  exit 127
fi

TEST_PYTHON="$(resolve_test_python || true)"
if [ -z "$TEST_PYTHON" ]; then
  echo "No suitable Python interpreter found in PATH (tried: python3.10, python3, python)." >&2
  exit 127
fi

if ! command -v "$TEST_PYTHON" >/dev/null 2>&1; then
  echo "Selected interpreter '$TEST_PYTHON' not found in PATH." >&2
  exit 127
fi

if ! "$TEST_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  echo "Interpreter '$TEST_PYTHON' is too old. Need Python >= 3.10." >&2
  "$TEST_PYTHON" -V >&2 || true
  exit 127
fi

DEFAULT_EXEC="$($POETRY_BIN env info --executable 2>/dev/null || true)"

$POETRY_BIN env use "$TEST_PYTHON" >/dev/null
trap 'if [ -n "$DEFAULT_EXEC" ]; then $POETRY_BIN env use "$DEFAULT_EXEC" >/dev/null; fi' EXIT

if [ -n "$INSTALL_ARGS" ]; then
  # shellcheck disable=SC2086
  $POETRY_BIN install $INSTALL_ARGS >/dev/null
else
  $POETRY_BIN install >/dev/null
fi

$POETRY_BIN run "$@"
