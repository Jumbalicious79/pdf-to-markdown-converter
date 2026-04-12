#!/bin/bash

# Simple wrapper script for PDF to Markdown conversion
# Usage: ./convert.sh [pdf_file or directory] [options]
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

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3 first"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv

    # Activate virtual environment
    source venv/bin/activate

    # Install requirements
    echo -e "${BLUE}📦 Installing requirements...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    pip install pymupdf4llm pillow > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        echo "Try manually: pip install pymupdf4llm pillow"
        exit 1
    fi
else
    # Activate existing virtual environment
    source venv/bin/activate
fi

# Run the converter
if [ $# -eq 0 ]; then
    # No arguments - show help
    python3 scripts/pdf_to_markdown.py --help
elif [ -d "$1" ]; then
    # Directory provided
    echo -e "${BLUE}📁 Converting all PDFs in directory: $1${NC}"
    dir_arg="$1"
    shift
    python3 scripts/pdf_to_markdown.py --dir "$dir_arg" --output-dir output/ "$@"
else
    # File provided
    echo -e "${BLUE}📄 Converting PDF: $1${NC}"
    pdf_file="$1"
    shift

    # Check if next arg looks like an output path (no leading --)
    if [ $# -ge 1 ] && [[ ! "$1" == --* ]]; then
        output_arg="$1"
        shift
        python3 scripts/pdf_to_markdown.py "$pdf_file" -o "$output_arg" "$@"
    else
        filename=$(basename "$pdf_file" .pdf)
        python3 scripts/pdf_to_markdown.py "$pdf_file" -o "output/${filename}.md" "$@"
    fi
fi

# Deactivate virtual environment
deactivate 2>/dev/null
