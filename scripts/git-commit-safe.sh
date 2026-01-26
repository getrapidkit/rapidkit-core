#!/usr/bin/env bash
# Advanced Git commit helper with pre-commit checks
# Save as git-commit-safe.sh and chmod +x

COMMIT_MSG="$1"
FULL_CHECK=false
EMERGENCY=false

# Parse optional flags
shift
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --full) FULL_CHECK=true ;;
        --emergency) EMERGENCY=true ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$COMMIT_MSG" ]; then
    echo "❌ Commit message required. Usage: ./git-commit-safe.sh 'Your commit message'"
    exit 1
fi

echo "📝 Staging all changes..."
git add .

# Run quick check
echo "🚀 Running quick pre-commit checks..."
if ! python scripts/pre_commit_manager.py quick; then
    echo "❌ Quick checks failed."
    if [ "$EMERGENCY" = true ]; then
        echo "⚠️ Emergency commit enabled. Bypassing hooks..."
        python scripts/pre_commit_manager.py emergency --reason "$COMMIT_MSG"
        exit 0
    else
        exit 1
    fi
fi

# Optional full check
if [ "$FULL_CHECK" = true ]; then
    echo "🔍 Running full pre-commit audit..."
    if ! python scripts/pre_commit_manager.py full; then
        echo "❌ Full audit failed."
        if [ "$EMERGENCY" = true ]; then
            echo "⚠️ Emergency commit enabled. Bypassing hooks..."
            python scripts/pre_commit_manager.py emergency --reason "$COMMIT_MSG"
            exit 0
        else
            exit 1
        fi
    fi
fi

# If all checks passed
echo "✅ All pre-commit checks passed. Creating commit..."
git commit -m "$COMMIT_MSG"
