#!/bin/bash
# Developer Environment Setup Script
# This script ensures all required development tools are installed:
# - hadolint: Dockerfile linter
# - shellcheck: Shell script linter
# - pre-commit: Git hooks framework
# - black: Python code formatter
# - ruff: Python linter & fixer
# - mypy: Type checker
# - bandit: Security scanner

set -e

echo "🚀 Setting up RapidKit development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Prefer tooling provided by the project's Poetry environment when available.
poetry_tool_available() {
    local tool="$1"
    command_exists poetry && poetry run "$tool" --version >/dev/null 2>&1
}

# Install a Python CLI tool into the user environment and verify it is runnable.
# This avoids relying on whatever `pip` happens to point at.
install_python_cli_tool() {
    local tool="$1"
    local module_name="${2:-$1}"

    # If the tool is available via Poetry, treat it as installed.
    if poetry_tool_available "$tool"; then
        print_success "$tool is available via poetry"
        return 0
    fi

    if command_exists "$tool"; then
        print_success "$tool is already installed"
        return 0
    fi

    print_status "Installing $tool..."
    python3 -m pip install --user --upgrade "$tool"

    if command_exists "$tool"; then
        print_success "$tool installed successfully"
        return 0
    fi

    # As a fallback, accept module availability (and create a small shim).
    if python3 -c "import ${module_name}" >/dev/null 2>&1; then
        mkdir -p ~/.local/bin
        cat >"$HOME/.local/bin/$tool" <<EOF
#!/usr/bin/env bash
exec python3 -m ${module_name} "$@"
EOF
        chmod +x "$HOME/.local/bin/$tool"
        if command_exists "$tool"; then
            print_success "$tool installed (shim created)"
            return 0
        fi
    fi

    print_error "Failed to install $tool"
    return 1
}

# Install hadolint
install_hadolint() {
    if command_exists hadolint; then
        print_success "hadolint is already installed"
        return 0
    fi

    print_status "Installing hadolint..."
    curl -sSL https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -o ~/.local/bin/hadolint
    chmod +x ~/.local/bin/hadolint

    if command_exists hadolint; then
        print_success "hadolint installed successfully"
    else
        print_error "Failed to install hadolint"
        return 1
    fi
}

# Install shellcheck
install_shellcheck() {
    if command_exists shellcheck; then
        print_success "shellcheck is already installed"
        return 0
    fi

    print_status "Installing shellcheck..."
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y shellcheck
    elif command_exists yum; then
        sudo yum install -y ShellCheck
    elif command_exists dnf; then
        sudo dnf install -y ShellCheck
    elif command_exists brew; then
        brew install shellcheck
    else
        print_error "Package manager not found. Please install shellcheck manually."
        return 1
    fi

    if command_exists shellcheck; then
        print_success "shellcheck installed successfully"
    else
        print_error "Failed to install shellcheck"
        return 1
    fi
}

# Install pre-commit
install_pre_commit() {
    install_python_cli_tool "pre-commit" "pre_commit"
}

# Install black
install_black() {
    install_python_cli_tool "black" "black"
}

# Install ruff
install_ruff() {
    install_python_cli_tool "ruff" "ruff"
}

# Install mypy
install_mypy() {
    install_python_cli_tool "mypy" "mypy"
}

# Install bandit
install_bandit() {
    install_python_cli_tool "bandit" "bandit"
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    if poetry_tool_available pre-commit; then
        poetry run pre-commit install
        poetry run pre-commit install --hook-type commit-msg
    else
        pre-commit install
        pre-commit install --hook-type commit-msg
    fi

    print_success "Pre-commit hooks installed"
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."

    local failed=0

    if ! command_exists hadolint; then
        print_error "hadolint not found"
        failed=1
    else
        print_success "hadolint: $(hadolint --version)"
    fi

    if ! command_exists shellcheck; then
        print_error "shellcheck not found"
        failed=1
    else
        print_success "shellcheck: $(shellcheck --version)"
    fi

    if command_exists pre-commit; then
        print_success "pre-commit: $(pre-commit --version)"
    elif poetry_tool_available pre-commit; then
        print_success "pre-commit (poetry): $(poetry run pre-commit --version)"
    else
        print_error "pre-commit not found"
        failed=1
    fi

    if command_exists black; then
        print_success "black: $(black --version)"
    elif poetry_tool_available black; then
        print_success "black (poetry): $(poetry run black --version)"
    else
        print_error "black not found"
        failed=1
    fi

    if command_exists ruff; then
        print_success "ruff: $(ruff --version)"
    elif poetry_tool_available ruff; then
        print_success "ruff (poetry): $(poetry run ruff --version)"
    else
        print_error "ruff not found"
        failed=1
    fi

    if command_exists mypy; then
        print_success "mypy: $(mypy --version)"
    elif poetry_tool_available mypy; then
        print_success "mypy (poetry): $(poetry run mypy --version)"
    else
        print_error "mypy not found"
        failed=1
    fi

    if command_exists bandit; then
        print_success "bandit: $(bandit --version)"
    elif poetry_tool_available bandit; then
        print_success "bandit (poetry): $(poetry run bandit --version)"
    else
        print_error "bandit not found"
        failed=1
    fi

    return $failed
}

# Main function
main() {
    print_status "Starting RapidKit development environment setup..."

    # Create local bin directory if it doesn't exist
    mkdir -p ~/.local/bin

    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_warning "Please add ~/.local/bin to your PATH"
        echo "Add this to your ~/.bashrc or ~/.zshrc:"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi

    # Install development tools
    print_status "Installing development tools..."
    install_hadolint
    install_shellcheck
    install_pre_commit
    install_black
    install_ruff
    install_mypy
    install_bandit

    # Setup pre-commit
    setup_pre_commit

    # Verify
    if verify_installation; then
        print_success "🎉 All tools installed successfully!"
        print_status "Run 'pre-commit run --all-files' to test all hooks"
        print_status "Happy coding! 🚀"
    else
        print_error "❌ Some tools failed to install. Please check the errors above."
        exit 1
    fi
}

# Run main function
main "$@"
