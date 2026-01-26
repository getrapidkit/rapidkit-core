#!/bin/bash
# Git Hook: Enforce commit message format
# This hook runs even when --no-verify is used

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the commit message file
COMMIT_MSG_FILE=$1

# Check if the script exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_SCRIPT="$SCRIPT_DIR/check_commit_message.py"

if [ ! -f "$CHECK_SCRIPT" ]; then
    echo -e "${RED}❌ Error: Commit message validation script not found at $CHECK_SCRIPT${NC}"
    echo -e "${YELLOW}💡 Make sure you're in the correct repository directory${NC}"
    exit 1
fi

# Read the commit message
if [ -f "$COMMIT_MSG_FILE" ]; then
    COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")
elif [ -p "$COMMIT_MSG_FILE" ]; then
    # Handle process substitution (e.g., <(echo "message"))
    COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")
else
    echo -e "${RED}❌ Error: Commit message file not found${NC}"
    exit 1
fi

# Run the validation script
echo -e "${YELLOW}🔍 Validating commit message...${NC}"
if python "$CHECK_SCRIPT" "$COMMIT_MSG" 2>/dev/null; then
    echo -e "${GREEN}✅ Commit message is valid!${NC}"
    exit 0
else
    echo -e "${RED}❌ Invalid commit message format!${NC}"
    echo ""
    echo -e "${YELLOW}💡 Commit message must follow conventional format:${NC}"
    echo "   type(scope): description"
    echo ""
    echo -e "${YELLOW}📝 Examples:${NC}"
    echo "   • feat: add user authentication"
    echo "   • fix: resolve login bug"
    echo "   • docs: update README"
    echo "   • debug: add debugging steps"
    echo "   • refactor: improve code structure"
    echo ""
    echo -e "${YELLOW}🔧 Allowed types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert, debug${NC}"
    echo ""
    echo -e "${RED}🚫 Commit rejected. Please fix the commit message and try again.${NC}"
    echo -e "${YELLOW}💡 Tip: Use 'git commit --amend' to edit the message${NC}"
    exit 1
fi
