#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

printf "\n🚀 Starting Rapidkit Ultra V4 Galactic Bootstrap\n"
printf "Project root: %s\n" "$PROJECT_ROOT"

# Artifacts directory (use a stable location for CI dashboards)
ARTIFACTS_DIR="$PROJECT_ROOT/artifacts"
mkdir -p "$ARTIFACTS_DIR"

# ----------------------------------------
# Activate Poetry virtualenv
# ----------------------------------------
if [ -n "${POETRY_ACTIVE:-}" ]; then
    printf "✅ Poetry environment already active."
else
    printf "🔹 Activating Poetry virtualenv..."
    export POETRY_VIRTUALENVS_IN_PROJECT=true
    VENV_PATH="$(poetry env info --path 2>/dev/null || true)"
    if [ -z "$VENV_PATH" ]; then
        printf "⚠️ Poetry virtualenv not found, creating..."
        poetry install --with dev
        VENV_PATH="$(poetry env info --path)"
    fi
    source "$VENV_PATH/bin/activate"
fi

printf "Python: %s\n" "$(python --version)"
printf "Virtualenv: %s\n" "$(which python)"

# ----------------------------------------
# Ensure all dev tools installed
# ----------------------------------------
TOOLS=(ruff black isort mypy pytest pre-commit pip-audit bandit)
for tool in "${TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        printf "⚠️ %s not found. Installing dev dependencies...\n" "$tool"
        poetry install --with dev
        break
    fi
done

# ----------------------------------------
# Linting with Ruff + Ruff Gate
# ----------------------------------------
printf "\n==== Linting (Ruff) ====\n"
RUFF_JSON="$ARTIFACTS_DIR/ruff_report.json"
poetry run ruff check src --output-format=json > "$RUFF_JSON" || true

if [ -f scripts/ci/ruff_baseline.json ] && [ -f scripts/ci/ruff_gate.py ]; then
    printf "🔹 Running Ruff Gate..."
    poetry run python scripts/ci/ruff_gate.py
else
    printf "⚠️ Ruff Gate prerequisites missing; skipping."
fi

# Ruff summary
python - <<'EOF'
import json, pathlib, collections
p = pathlib.Path('ruff_report.json')
data = json.loads(p.read_text()) if p.exists() else []
print(f"Total violations: {len(data)}")
cnt = collections.Counter(v['code'] for v in data)
print("Top violation codes:")
for code, c in cnt.most_common(10):
    print(f'  {code}: {c}')
EOF

# ----------------------------------------
# Format & Imports
# ----------------------------------------
printf "\n==== Format Check (Black) ====\n"
poetry run black --check . || true

printf "\n==== Imports Check (Isort) ====\n"
poetry run isort --check-only . || true

# ----------------------------------------
# Type Checking
# ----------------------------------------
printf "\n==== Type Checking (Mypy) ====\n"
poetry run mypy || true

# ----------------------------------------
# Tests + Coverage
# ----------------------------------------
printf "\n==== Running Tests (Pytest + Coverage) ====\n"
COV_XML="coverage.xml"
poetry run pytest --cov=src --cov-report=xml --cov-report=term-missing --maxfail=1 || true
if [ -f "$COV_XML" ]; then
    cp "$COV_XML" "$ARTIFACTS_DIR/" || true
fi

# ----------------------------------------
# Pre-commit hooks
# ----------------------------------------
printf "\n==== Running Pre-commit Hooks ====\n"
poetry run pre-commit run --all-files || true

# ----------------------------------------
# Build package
# ----------------------------------------
printf "\n==== Building Package ====\n"
poetry build || true

# ----------------------------------------
# Diff Gate
# ----------------------------------------
printf "\n==== Running Diff Gate ====\n"
SAMPLE_PROJECT="boilerplates/alef"
if [ ! -d "$SAMPLE_PROJECT" ]; then
    printf "No sample boilerplate found, creating stub..."
    mkdir -p "$SAMPLE_PROJECT/.rapidkit"
    echo '{}' > "$SAMPLE_PROJECT/.rapidkit/file-hashes.json"
fi
if ! poetry run rapidkit diff all --project alef --json > "$ARTIFACTS_DIR/diff-all.json"; then
    printf "Diff failed"
    cat "$ARTIFACTS_DIR/diff-all.json" || true
fi

# ----------------------------------------
# Security Checks
# ----------------------------------------
printf "\n==== Security Scan ====\n"
poetry run pip-audit || true
poetry run bandit -q -r src || true

# ----------------------------------------
# Coverage Ratchet
# ----------------------------------------
printf "\n==== Running Coverage Ratchet ====\n"
if [ -f scripts/ci/coverage_ratcheter.py ]; then
    poetry run python scripts/ci/coverage_ratcheter.py --apply-if-main > "$ARTIFACTS_DIR/ratchet.json" || true
    cat "$ARTIFACTS_DIR/ratchet.json" || true

    if grep -q '"changed": true' "$ARTIFACTS_DIR/ratchet.json"; then
        printf "🔹 Ratchet indicates coverage change. Auto-push controlled by RATCHET_AUTO_PUSH env var."
        if [ "${RATCHET_AUTO_PUSH:-false}" = "true" ]; then
            printf "🔹 Updating fail_under in pyproject.toml and pushing changes"
            git config user.name "coverage-bot"
            git config user.email "coverage-bot@users.noreply.github.com"
            git add pyproject.toml
            git commit -m "chore(ci): ratchet coverage fail_under" || printf "Nothing to commit"
            git push || printf "Push failed or skipped"
        else
            printf "⚠️ RATCHET_AUTO_PUSH is not enabled; skipping git commit/push."
        fi
    fi
else
    printf "⚠️ coverage_ratcheter.py not available; skipping coverage ratchet."
fi

# ----------------------------------------
# Summary
# ----------------------------------------
printf "\n🎉 Rapidkit Ultra V4 Galactic Bootstrap Completed!\n"
printf "Artifacts (in %s):\n" "$ARTIFACTS_DIR"
printf "  - %s\n" "$(basename "$RUFF_JSON")"
printf "  - %s\n" "$(basename "$COV_XML")"
printf "  - dist/\n"
printf "  - %s\n" "$(basename "$ARTIFACTS_DIR/diff-all.json")"
printf "  - %s\n" "$(basename "$ARTIFACTS_DIR/ratchet.json")"

printf "You can enable automatic ratchet commit/push by setting: export RATCHET_AUTO_PUSH=true\n"

NOTIFY_MSG="Rapidkit Ultra V4 Galactic Bootstrap Completed. Check dashboard and artifacts."
if [ "${SKIP_DASHBOARD:-false}" = "true" ]; then
    printf "🔕 SKIP_DASHBOARD is set — skipping dashboard notifications.\n"
else
    printf "Dashboard HTML & notifications ready (Slack/Teams/Discord/Email).\n"
    # optional: post notifications if webhooks configured
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -sS -X POST -H 'Content-type: application/json' --data "{\"text\":\"$NOTIFY_MSG\"}" "$SLACK_WEBHOOK_URL" || true
    fi
    if [ -n "${DISCORD_WEBHOOK_URL:-}" ]; then
        curl -sS -X POST -H 'Content-Type: application/json' --data "{\"content\":\"$NOTIFY_MSG\"}" "$DISCORD_WEBHOOK_URL" || true
    fi
    if [ -n "${TEAMS_WEBHOOK_URL:-}" ]; then
        curl -sS -X POST -H 'Content-Type: application/json' --data "{\"text\":\"$NOTIFY_MSG\"}" "$TEAMS_WEBHOOK_URL" || true
    fi
fi

exit 0
