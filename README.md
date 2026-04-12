# PDF to Markdown Converter

A Python tool that converts PDF files to Markdown format while preserving structure, formatting, and optionally extracting images.

## Quick Start (3 Steps)

### Option 1: Auto-Convert Everything (Easiest!)

1. **Place your PDFs** in the `input/` directory (including subdirectories!)
2. **Run**: `./convert_all.sh`  
3. **Get your Markdown files** from the `output/` directory with matching structure

### Option 2: Convert Specific File

```bash
# macOS / Linux
./convert.sh document.pdf

# Windows
convert.bat document.pdf
```

**That's it!** Dependencies install automatically on first run.

## Features

- **Convert single PDFs or entire directories**
- **High-quality layout detection** via pymupdf4llm (headers, lists, tables, code blocks)
- **OCR support** for scanned PDFs (`--ocr`)
- **Header/footer removal** to strip repeated page headers/footers (`--strip-headers-footers`)
- **Extract and embed images** as separate files or inline base64
- **Table detection and conversion** to Markdown tables
- **Post-processing cleanup** (normalizes headers, fixes tables, removes artifacts)
- **LLM-powered cleanup** via Claude API or Claude Code CLI (`--cleanup`)
- **Batch processing** for multiple files
- **Directory structure preservation** - subdirectories maintained in output
- **Auto-setup** - no manual dependency installation

## Usage Examples

### Simple Commands

```bash
# Auto-convert all PDFs in input/ directory (including subdirectories)
./convert_all.sh

# Convert specific PDF
./convert.sh document.pdf

# Convert with images extracted
./convert.sh document.pdf --extract-images

# Convert a scanned PDF with OCR
./convert.sh scanned-document.pdf --ocr

# Strip repeated page headers/footers
./convert.sh report.pdf --strip-headers-footers
```

### LLM Cleanup

```bash
# Clean up with Claude API (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=your-key ./convert.sh messy.pdf --cleanup

# Clean up with Claude Code CLI (if installed, no API key needed)
./convert.sh messy.pdf --cleanup

# Combine options for best results
./convert.sh report.pdf --strip-headers-footers --ocr --cleanup
```

### Advanced Usage

```bash
# Full control with all options
python3 scripts/pdf_to_markdown.py document.pdf \
  --extract-images \
  --image-dir custom-images \
  --strip-headers-footers \
  --ocr \
  --image-dpi 300 \
  --output custom-name.md \
  --verbose

# Embed images inline (base64, no separate files)
python3 scripts/pdf_to_markdown.py document.pdf --extract-images --embed-images

# Batch convert directory with pdfplumber backend
python3 scripts/pdf_to_markdown.py --dir ./pdfs --output-dir ./converted --backend pdfplumber
```

### Python API

```python
from scripts.pdf_to_markdown import PDFToMarkdownConverter

# Create converter with options
converter = PDFToMarkdownConverter(
    extract_images=True,
    strip_headers_footers=True,
    use_ocr=True,
    cleanup=False,
)

# Convert files
output = converter.convert_file("document.pdf")
files = converter.convert_directory("./pdfs", "./markdown")
```

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output, -o` | Output file path | Same name with .md extension |
| `--dir` | Convert all PDFs in directory | - |
| `--output-dir` | Output directory for batch conversion | Same as input |
| `--extract-images` | Extract and embed images | False |
| `--embed-images` | Embed images as base64 (no separate files) | False |
| `--image-dir` | Directory for extracted images | `images` |
| `--image-dpi` | Image resolution in DPI | 150 |
| `--ocr` | Enable OCR for scanned PDFs | False |
| `--ocr-language` | OCR language code | `eng` |
| `--strip-headers-footers` | Remove repeated page headers/footers | False |
| `--page-separators` | Add page separator lines in output | False |
| `--cleanup` | Send output through LLM for structural cleanup | False |
| `--no-formatting` | Disable formatting preservation | False |
| `--no-page-breaks` | Disable page break markers | False |
| `--backend` | PDF library (auto/pymupdf4llm/pymupdf/pdfplumber) | `auto` |
| `--verbose, -v` | Enable verbose output | False |

## Output Format

The converter produces clean Markdown with:

- **Headers** detected from document layout and formatting
- **Lists** (bullet points and numbered lists)
- **Tables** converted to Markdown format
- **Images** embedded with proper paths (if extracted)
- **Page breaks** marked with horizontal rules
- **Metadata** (source file information)
- **Post-processed** to normalize header levels and fix table formatting

## PDF Processing Backends

The converter supports three backends (auto-selected by priority, or specify with `--backend`):

### pymupdf4llm (Default, Recommended)
- **Pros**: Best quality output, layout-aware extraction, OCR support, handles headers/footers/code blocks
- **Cons**: Larger installation size
- **Best for**: Most documents - this should be your default

### PyMuPDF
- **Pros**: Fast, handles complex PDFs, image extraction
- **Cons**: Basic text-only extraction with heuristic formatting
- **Best for**: Fallback when pymupdf4llm is unavailable

### pdfplumber
- **Pros**: Superior table detection, lighter weight
- **Cons**: Slower, limited image support
- **Best for**: Documents with lots of tables

## LLM Cleanup

The `--cleanup` flag sends the converted markdown through an LLM for structural cleanup. This fixes issues that automated post-processing can't handle, like broken sentences split across lines, misidentified headers, and conversion artifacts.

### Two Modes (tried in order)

1. **Anthropic API**: If `ANTHROPIC_API_KEY` is set and the `anthropic` package is installed, it calls the API directly. Install with: `pip install anthropic`

2. **Claude Code CLI**: If no API key is available but the `claude` command is on your PATH, it pipes the markdown through Claude Code as a subprocess.

If neither is available, the flag is silently skipped with a warning -- the converter still produces output, just without the LLM cleanup pass.

Large documents are automatically chunked at paragraph boundaries to stay within token limits.

## Project Structure

```
pdf-to-markdown-converter/
├── convert.sh              # Wrapper script (macOS/Linux)
├── convert_all.sh          # Batch convert (macOS/Linux)
├── convert.bat             # Launcher (Windows) → calls convert.ps1
├── convert_all.bat         # Batch launcher (Windows) → calls convert_all.ps1
├── convert.ps1             # Wrapper script (Windows PowerShell)
├── convert_all.ps1         # Batch convert (Windows PowerShell)
├── scripts/
│   └── pdf_to_markdown.py  # Main converter
├── input/                  # Place PDF files here
│   ├── reports/           # Example: organize by type
│   ├── manuals/           # Subdirectories are preserved
│   └── presentations/     # in output structure
├── output/                 # Converted markdown files
│   └── images/            # Extracted images (if enabled)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation & Setup

### Automatic (Recommended)
```bash
# Just run the converter - it handles setup automatically
./convert.sh your-file.pdf
```

### Manual
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install LLM cleanup support
pip install anthropic
```

## Requirements

- **Python 3.7+**
- **pymupdf4llm** (auto-installed, includes PyMuPDF)
- **Pillow** for image extraction (auto-installed)
- **anthropic** for LLM cleanup (optional, install manually)
- **Tesseract** for OCR (optional, install with `brew install tesseract`)

## Troubleshooting

### Common Issues

**ImportError: No PDF library available**
```bash
pip install pymupdf4llm
```

**Images not extracting**
```bash
pip install pillow
# Use --extract-images flag
```

**Poor text extraction from scanned PDFs**
```bash
# Install Tesseract OCR
brew install tesseract  # macOS
sudo apt install tesseract-ocr  # Linux

# Then use --ocr flag
./convert.sh scanned-doc.pdf --ocr
```

**Tables not formatting correctly**
- Use pdfplumber backend: `--backend pdfplumber`

**LLM cleanup not working**
```bash
# Option 1: Set API key
export ANTHROPIC_API_KEY=your-key-here
pip install anthropic

# Option 2: Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
```

**Repeated headers/footers in output**
```bash
# Use the strip flag
./convert.sh report.pdf --strip-headers-footers
```

## Limitations

- OCR requires Tesseract to be installed separately
- Complex layouts may not convert perfectly
- Password-protected PDFs not supported
- Some PDF forms/annotations not supported
- LLM cleanup requires either an Anthropic API key or Claude Code CLI

---

**PDF to Markdown Converter** - Convert your PDFs to clean, structured Markdown!

*Created: 2025-08-08 | Updated: 2026-04-12*
