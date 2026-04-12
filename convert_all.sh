#!/bin/bash

# Auto-convert all PDFs in input/ directory (including subdirectories) to markdown in output/ directory
# Usage: ./convert_all.sh [options]
# Extra flags (--ocr, --cleanup, etc.) are passed through to the Python script

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check and activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Run ./convert.sh first to set up.${NC}"
    exit 1
fi
source venv/bin/activate

echo -e "${BLUE}🔄 Auto-converting all PDFs in input/ directory (including subdirectories)${NC}"
echo "=================================================="

# Check if input directory exists and has PDFs
if [ ! -d "input" ]; then
    echo -e "${RED}❌ input/ directory not found${NC}"
    exit 1
fi

# Count PDFs in input directory (including subdirectories)
pdf_count=$(find input/ -type f \( -name "*.pdf" -o -name "*.PDF" \) | wc -l)

if [ $pdf_count -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No PDF files found in input/ directory or subdirectories${NC}"
    echo "Place your PDF files in the input/ directory (or subdirectories) first"
    exit 0
fi

echo -e "${GREEN}📄 Found $pdf_count PDF file(s) to convert${NC}"

# Show directory structure with PDFs
echo ""
echo -e "${BLUE}PDF files found:${NC}"
find input/ -type f \( -name "*.pdf" -o -name "*.PDF" \) | while read -r pdf_file; do
    echo "  📄 $pdf_file"
done

echo ""
echo -e "${BLUE}Starting conversions...${NC}"
echo ""

# Process each PDF individually to preserve directory structure
find input/ -type f \( -name "*.pdf" -o -name "*.PDF" \) | while read -r pdf_file; do
    # Get relative path from input/ directory
    rel_path="${pdf_file#input/}"

    # Create output directory structure
    output_dir="output/$(dirname "$rel_path")"
    mkdir -p "$output_dir"

    # Get filename without extension
    filename=$(basename "$rel_path" .pdf)
    filename=$(basename "$filename" .PDF)

    # Full output path
    output_file="$output_dir/${filename}.md"

    echo -e "${BLUE}Converting:${NC} $pdf_file → $output_file"

    # Convert the PDF (pass through any extra flags)
    python3 scripts/pdf_to_markdown.py "$pdf_file" -o "$output_file" "$@"
done

echo ""
echo -e "${GREEN}✅ All conversions complete!${NC}"
echo -e "${BLUE}📂 Check the output/ directory for your markdown files${NC}"

# List the converted files with directory structure
if [ -d "output" ]; then
    echo ""
    echo "Converted files:"
    find output/ -type f -name "*.md" | sort | while read -r md_file; do
        echo "  ✓ $md_file"
    done

    # Show directory structure
    echo ""
    echo -e "${BLUE}Output directory structure:${NC}"
    tree output/ 2>/dev/null || find output/ -type d | sort | while read -r dir; do
        level=$(echo "$dir" | sed 's/[^/]//g' | wc -c)
        indent=$(printf "%*s" $((level * 2)) "")
        echo "${indent}$(basename "$dir")/"
    done
fi

# Deactivate virtual environment
deactivate 2>/dev/null
