#!/bin/bash
# Git Commit Wrapper: Always enforce commit message validation
# This ensures validation runs even with --no-verify

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if this is a commit command
if [[ "$1" == "commit" ]]; then
    # Check if --no-verify is used
    if [[ "$*" == *"--no-verify"* ]]; then
        echo "⚠️  Warning: --no-verify detected, but commit message validation will still run"
    fi

    # Run the original git commit command
    if git "$@"; then
        # Get the latest commit message
        COMMIT_MSG=$(git log -1 --pretty=%B)

        # Create a temporary file for the commit message
        TEMP_FILE=$(mktemp)
        echo "$COMMIT_MSG" > "$TEMP_FILE"

        # Run validation
        if ! "$SCRIPT_DIR/enforce-commit-message.sh" "$TEMP_FILE"; then
            # Clean up temp file
            rm -f "$TEMP_FILE"
            echo ""
            echo "❌ Commit message validation failed!"
            echo "🔄 The commit was made but doesn't follow standards."
            echo "💡 Please amend the commit message:"
            echo "   git commit --amend"
            exit 1
        fi

        # Clean up temp file
        rm -f "$TEMP_FILE"
    fi
else
    # For other git commands, run normally
    git "$@"
fi
