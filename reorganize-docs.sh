#!/bin/bash
# Documentation Reorganization Script
# This script moves detailed documentation files into a docs/ subdirectory

set -e

echo "📚 HondaLink Controller - Documentation Reorganization"
echo "=================================================="
echo ""

# Create docs directory if it doesn't exist
echo "Creating docs/ directory..."
mkdir -p docs

# Move documentation files to docs/
echo "Moving documentation files to docs/..."

# Files to move to docs/
FILES_TO_MOVE=(
    "DOCKER.md"
    "SECURITY.md"
    "TESTING_GUIDE.md"
    "REMOTE_START_MONITORING.md"
    "IMPLEMENTATION.md"
    "IMPLEMENTATION_SUMMARY.md"
)

for file in "${FILES_TO_MOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ Moving $file to docs/"
        git mv "$file" "docs/$file"
    else
        echo "  ⚠ $file not found, skipping"
    fi
done

# Move the docs README
if [ -f "docs-README.md" ]; then
    echo "  ✓ Setting up docs/README.md"
    git mv "docs-README.md" "docs/README.md"
fi

echo ""
echo "✅ Documentation reorganization complete!"
echo ""
echo "Files moved to docs/:"
for file in "${FILES_TO_MOVE[@]}"; do
    if [ -f "docs/$file" ]; then
        echo "  - docs/$file"
    fi
done

echo ""
echo "📝 Next steps:"
echo "  1. Review the changes with: git status"
echo "  2. Commit the changes with: git commit -m 'Reorganize documentation into docs/ folder'"
echo "  3. All existing links in documentation have been updated to reference docs/ subdirectory"
echo ""
