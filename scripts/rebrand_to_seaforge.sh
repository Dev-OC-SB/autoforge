#!/bin/bash
# Rebrand AutoForge to SeaForge
# This script updates all references in the codebase

set -e

echo "🌊 Rebranding AutoForge to SeaForge..."

# Function to replace in files
replace_in_files() {
    local search="$1"
    local replace="$2"
    local pattern="$3"
    
    echo "  Replacing '$search' with '$replace' in $pattern files..."
    find . -type f -name "$pattern" \
        ! -path "./node_modules/*" \
        ! -path "./venv/*" \
        ! -path "./.git/*" \
        ! -path "./ui/node_modules/*" \
        ! -path "./__pycache__/*" \
        ! -path "./ui/dist/*" \
        ! -path "./scripts/rebrand_to_seaforge.sh" \
        -exec sed -i "s/$search/$replace/g" {} +
}

# Update README and documentation
echo "📝 Updating documentation..."
replace_in_files "AutoForge" "SeaForge" "*.md"
replace_in_files "autoforge" "seaforge" "*.md"

# Update Python files
echo "🐍 Updating Python files..."
replace_in_files "AutoForge" "SeaForge" "*.py"
replace_in_files "autoforge" "seaforge" "*.py"
replace_in_files "AUTOFORGE" "SEAFORGE" "*.py"

# Update JavaScript/TypeScript files
echo "⚛️  Updating JS/TS files..."
replace_in_files "AutoForge" "SeaForge" "*.ts"
replace_in_files "AutoForge" "SeaForge" "*.tsx"
replace_in_files "AutoForge" "SeaForge" "*.js"
replace_in_files "AutoForge" "SeaForge" "*.jsx"

# Update configuration files
echo "⚙️  Updating configuration files..."
replace_in_files "autoforge" "seaforge" "*.json"
replace_in_files "autoforge" "seaforge" "*.yml"
replace_in_files "autoforge" "seaforge" "*.yaml"
replace_in_files "AutoForge" "SeaForge" "*.json"

# Update Docker files
echo "🐳 Updating Docker files..."
replace_in_files "AutoForge" "SeaForge" "Dockerfile*"
replace_in_files "autoforge" "seaforge" "Dockerfile*"
replace_in_files "autoforge" "seaforge" "docker-compose*.yml"

# Update environment files
echo "🔐 Updating environment files..."
if [ -f ".env.example" ]; then
    sed -i 's/AUTOFORGE/SEAFORGE/g' .env.example
    sed -i 's/autoforge/seaforge/g' .env.example
fi

# Update HTML files
echo "🌐 Updating HTML files..."
replace_in_files "AutoForge" "SeaForge" "*.html"

echo ""
echo "✅ Rebranding complete!"
echo ""
echo "📋 Summary of changes:"
echo "  - All 'AutoForge' → 'SeaForge'"
echo "  - All 'autoforge' → 'seaforge'"
echo "  - All 'AUTOFORGE' → 'SEAFORGE'"
echo ""
echo "🔍 Files updated:"
echo "  - Documentation (*.md)"
echo "  - Python files (*.py)"
echo "  - JavaScript/TypeScript (*.ts, *.tsx, *.js, *.jsx)"
echo "  - Configuration (*.json, *.yml, *.yaml)"
echo "  - Docker files"
echo "  - HTML files"
echo ""
echo "⚠️  Manual review recommended for:"
echo "  - Git repository URLs"
echo "  - External links"
echo "  - API endpoints"
echo "  - Database names"
echo ""
