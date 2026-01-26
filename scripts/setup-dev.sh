#!/bin/bash
# RapidKit Development Environment Setup Script
# Ensures all development tools are properly installed and configured

set -e

echo "🚀 Setting up RapidKit development environment..."
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f ".pre-commit-config.yaml" ]; then
    echo "❌ Error: Please run this script from the root of the RapidKit repository"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "📦 Installing dependencies..."
make install-all

echo ""
echo "🔧 Installing and verifying pre-commit hooks..."
make check-hooks

echo ""
echo "🧹 Formatting code..."
make format

echo ""
echo "🔍 Running initial checks..."
make lint

echo ""
echo "🧪 Running tests..."
make test

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 You're all set! Here are some useful commands:"
echo "  make test          - Run tests"
echo "  make lint          - Check code quality"
echo "  make format        - Format code"
echo "  make pre-commit-all - Run all pre-commit checks"
echo "  make help          - Show all available commands"
echo ""
echo "💡 Pro tip: Always run 'make check-hooks' before starting development"
