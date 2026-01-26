#!/bin/bash
# Script to update modules lock file
# Usage: ./scripts/update_modules_lock.sh

set -e

echo "🔄 Updating modules lock file..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if rapidkit is installed
if ! command -v rapidkit &> /dev/null; then
    echo "📦 Installing RapidKit..."
    pip install -e .[dev]
fi

# Generate the lock file
echo "🔒 Generating modules lock file..."
rapidkit modules lock --overwrite

echo "✅ Modules lock file updated successfully!"
echo "📄 File: .rapidkit/modules.lock.yaml"
