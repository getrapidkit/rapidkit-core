#!/bin/bash
# Setup script to enforce commit message validation even with --no-verify

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔧 Setting up enforced commit message validation..."
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f ".pre-commit-config.yaml" ]; then
    echo "❌ Error: Please run this script from the RapidKit repository root"
    echo "   Current directory: $(pwd)"
    echo "   Looking for: pyproject.toml, .pre-commit-config.yaml"
    exit 1
fi

# Create a backup of the original git binary path
ORIGINAL_GIT=$(which git)

# Create a wrapper function for git
cat > "$REPO_ROOT/.git-commit-wrapper" << EOF
#!/bin/bash
# Git wrapper that enforces commit message validation

SCRIPT_DIR="$SCRIPT_DIR"

# Check if this is a commit command in this repository
if [[ "\$PWD" == "$REPO_ROOT"* ]] && [[ "\$1" == "commit" ]]; then
    # Check if --no-verify is used
    if [[ "\$*" == *"--no-verify"* ]]; then
        echo "⚠️  Warning: --no-verify detected, but commit message validation will still run"
    fi

    # Run the original git commit command
    "$ORIGINAL_GIT" "\$@"

    # If commit was successful, validate the message
    if [ \$? -eq 0 ]; then
        # Get the latest commit message
        COMMIT_MSG=\$("$ORIGINAL_GIT" log -1 --pretty=%B 2>/dev/null)

        if [ -n "\$COMMIT_MSG" ]; then
            # Run validation
            if ! "\$SCRIPT_DIR/enforce-commit-message.sh" <(echo "\$COMMIT_MSG") 2>/dev/null; then
                echo ""
                echo "❌ Commit message validation failed!"
                echo "🔄 The commit was made but doesn't follow standards."
                echo "💡 Please amend the commit message:"
                echo "   $ORIGINAL_GIT commit --amend"
                exit 1
            fi
        fi
    fi
else
    # For other commands or outside this repo, run normally
    "$ORIGINAL_GIT" "\$@"
fi
EOF

chmod +x "$REPO_ROOT/.git-commit-wrapper"

# Add to .bashrc or create alias
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Check if alias already exists
if ! grep -q "alias git=" "$SHELL_RC" 2>/dev/null; then
    {
        echo ""
        echo "# RapidKit: Enforce commit message validation"
        echo "alias git='$REPO_ROOT/.git-commit-wrapper'"
    } >> "$SHELL_RC"
    echo "✅ Added git alias to $SHELL_RC"
    echo "🔄 Please run: source $SHELL_RC"
else
    echo "⚠️  Git alias already exists in $SHELL_RC"
    echo "💡 Please check and update it manually if needed"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 What was configured:"
echo "  • Git wrapper script created at: $REPO_ROOT/.git-commit-wrapper"
echo "  • Shell alias added to: $SHELL_RC"
echo ""
echo "🔍 Testing setup..."
echo "  Run: source $SHELL_RC"
echo "  Then try: git commit --no-verify -m 'test: this should fail'"
echo ""
echo "⚠️  Note: This only affects git commands run from this repository"
