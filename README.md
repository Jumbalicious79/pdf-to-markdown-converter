# PDF to Markdown Converter

A Python tool that converts PDF files to Markdown format while preserving structure, formatting, and optionally extracting images. Works on **macOS**, **Linux**, and **Windows**.

## Prerequisites

### Python 3.7+

The converter requires Python 3.7 or later. The scripts will detect if Python is missing and tell you where to get it.

**macOS:**
```bash
# Check if Python is installed
python3 --version

# If not installed, install via Homebrew
brew install python3

# Or download from https://www.python.org/downloads/
```

**Windows:**
```powershell
# Check if Python is installed
python --version

# If not installed, download from https://www.python.org/downloads/
# IMPORTANT: Check "Add Python to PATH" during installation
```

### Optional: Tesseract (for OCR)

Only needed if you want to convert scanned PDFs using the `--ocr` flag.

**macOS:**
```bash
brew install tesseract
```

**Windows:**
```powershell
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
# Add Tesseract to your PATH after installation
```

### Optional: Anthropic API or Claude Code CLI (for LLM cleanup)

Only needed if you want to use the `--cleanup` flag for AI-powered cleanup.

```bash
# Option 1: Anthropic API
pip install anthropic
export ANTHROPIC_API_KEY=your-key-here  # macOS/Linux
set ANTHROPIC_API_KEY=your-key-here     # Windows CMD
$env:ANTHROPIC_API_KEY="your-key-here"  # Windows PowerShell

# Option 2: Claude Code CLI (no API key needed)
npm install -g @anthropic-ai/claude-code
```

---

## Quick Start

### macOS / Linux

```bash
# 1. Clone or download the project
git clone https://github.com/Jumbalicious79/pdf-to-markdown-converter.git
cd pdf-to-markdown-converter

# 2. Make scripts executable (first time only)
chmod +x convert.sh convert_all.sh

# 3. Convert a PDF (auto-installs dependencies on first run)
./convert.sh document.pdf

# 4. Output appears in output/document.md
```

**Batch convert** -- place PDFs in `input/` then:
```bash
./convert_all.sh
```

### Windows

```powershell
# 1. Clone or download the project
git clone https://github.com/Jumbalicious79/pdf-to-markdown-converter.git
cd pdf-to-markdown-converter

# 2. Convert a PDF (auto-installs dependencies on first run)
convert.bat document.pdf

# 3. Output appears in output\document.md
```

**Batch convert** -- place PDFs in `input\` then:
```powershell
convert_all.bat
```

### What Happens on First Run

On **both** platforms, the first time you run the converter it will:

1. Check that Python 3 is installed (tells you where to get it if not)
2. Create a virtual environment (`venv/`)
3. Install `pymupdf4llm` and `Pillow` automatically
4. Run the conversion

Subsequent runs skip setup and go straight to conversion.

---

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
- **Directory structure preservation** -- subdirectories maintained in output
- **Cross-platform** -- macOS, Linux, and Windows

---

## Usage

### Basic Commands

**macOS / Linux:**
```bash
# Convert a single PDF
./convert.sh document.pdf

# Convert all PDFs in input/ directory
./convert_all.sh

# Convert with options
./convert.sh document.pdf --ocr --strip-headers-footers
```

**Windows:**
```powershell
# Convert a single PDF
convert.bat document.pdf

# Convert all PDFs in input\ directory
convert_all.bat

# Convert with options
convert.bat document.pdf --ocr --strip-headers-footers
```

### Common Options

```bash
# Enable OCR for scanned PDFs
./convert.sh scanned-doc.pdf --ocr                    # macOS/Linux
convert.bat scanned-doc.pdf --ocr                     # Windows

# Strip repeated page headers/footers
./convert.sh report.pdf --strip-headers-footers       # macOS/Linux
convert.bat report.pdf --strip-headers-footers        # Windows

# Extract images
./convert.sh document.pdf --extract-images            # macOS/Linux
convert.bat document.pdf --extract-images             # Windows

# LLM cleanup (requires Anthropic API key or Claude CLI)
./convert.sh messy.pdf --cleanup                      # macOS/Linux
convert.bat messy.pdf --cleanup                       # Windows

# Combine options for best results
./convert.sh report.pdf --strip-headers-footers --ocr --cleanup
convert.bat report.pdf --strip-headers-footers --ocr --cleanup
```

### Advanced Usage (Direct Python)

For full control, run the Python script directly. This works the same on all platforms once the venv is activated.

**macOS / Linux:**
```bash
source venv/bin/activate
python3 scripts/pdf_to_markdown.py document.pdf \
  --extract-images \
  --strip-headers-footers \
  --ocr \
  --image-dpi 300 \
  --output custom-name.md \
  --verbose
deactivate
```

**Windows:**
```powershell
.\venv\Scripts\Activate.ps1
python scripts\pdf_to_markdown.py document.pdf `
  --extract-images `
  --strip-headers-footers `
  --ocr `
  --image-dpi 300 `
  --output custom-name.md `
  --verbose
deactivate
```

### Python API

```python
from scripts.pdf_to_markdown import PDFToMarkdownConverter

converter = PDFToMarkdownConverter(
    extract_images=True,
    strip_headers_footers=True,
    use_ocr=True,
    cleanup=False,
)

output = converter.convert_file("document.pdf")
files = converter.convert_directory("./pdfs", "./markdown")
```

---

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

---

## PDF Processing Backends

The converter supports three backends (auto-selected by priority, or specify with `--backend`):

### pymupdf4llm (Default, Recommended)
- Best quality output, layout-aware extraction, OCR support, handles headers/footers/code blocks
- Best for: most documents

### PyMuPDF
- Fast, handles complex PDFs, image extraction
- Basic text-only extraction with heuristic formatting
- Best for: fallback when pymupdf4llm is unavailable

### pdfplumber
- Superior table detection, lighter weight
- Slower, limited image support
- Best for: documents with lots of tables

---

## LLM Cleanup

The `--cleanup` flag sends the converted markdown through an LLM for structural cleanup. This fixes issues that automated post-processing can't handle, like broken sentences split across lines, misidentified headers, and conversion artifacts.

**Two modes (tried in order):**

1. **Anthropic API** -- if `ANTHROPIC_API_KEY` is set and the `anthropic` package is installed
2. **Claude Code CLI** -- if no API key is available but the `claude` command is on your PATH

If neither is available, the flag is silently skipped with a warning -- the converter still produces output, just without the LLM cleanup pass. Large documents are automatically chunked at paragraph boundaries.

---

## Project Structure

```
pdf-to-markdown-converter/
├── convert.sh              # Wrapper script (macOS/Linux)
├── convert_all.sh          # Batch convert (macOS/Linux)
├── convert.bat             # Launcher (Windows) -> calls convert.ps1
├── convert_all.bat         # Batch launcher (Windows) -> calls convert_all.ps1
├── convert.ps1             # Wrapper script (Windows PowerShell)
├── convert_all.ps1         # Batch convert (Windows PowerShell)
├── scripts/
│   └── pdf_to_markdown.py  # Main converter
├── input/                  # Place PDF files here (subdirectories preserved)
├── output/                 # Converted markdown files appear here
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Manual Installation

If you prefer to set up manually instead of using the auto-setup scripts:

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Optional: LLM cleanup support
pip install anthropic
```

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Optional: LLM cleanup support
pip install anthropic
```

---

## Requirements

| Requirement | Required? | Install |
|-------------|-----------|---------|
| Python 3.7+ | Yes | [python.org](https://www.python.org/downloads/) or `brew install python3` |
| pymupdf4llm | Yes (auto-installed) | `pip install pymupdf4llm` |
| Pillow | Yes (auto-installed) | `pip install Pillow` |
| Tesseract | Only for `--ocr` | `brew install tesseract` (macOS) or [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki) |
| anthropic | Only for `--cleanup` | `pip install anthropic` |
| Claude Code CLI | Only for `--cleanup` | `npm install -g @anthropic-ai/claude-code` |

---

## Troubleshooting

### Python not found

**macOS:**
```bash
# Install via Homebrew
brew install python3

# Or download from python.org
open https://www.python.org/downloads/
```

**Windows:**
```powershell
# Download from python.org -- check "Add Python to PATH" during install
start https://www.python.org/downloads/
```

### No PDF library available
```bash
pip install pymupdf4llm
```

### Images not extracting
```bash
pip install Pillow
# Use the --extract-images flag
```

### Poor text extraction from scanned PDFs

Install Tesseract OCR, then use the `--ocr` flag:

**macOS:**
```bash
brew install tesseract
./convert.sh scanned-doc.pdf --ocr
```

**Windows:**
```powershell
# Download and install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH, then:
convert.bat scanned-doc.pdf --ocr
```

### Tables not formatting correctly

Use the pdfplumber backend:
```bash
./convert.sh report.pdf --backend pdfplumber       # macOS/Linux
convert.bat report.pdf --backend pdfplumber         # Windows
```

### Repeated headers/footers in output
```bash
./convert.sh report.pdf --strip-headers-footers    # macOS/Linux
convert.bat report.pdf --strip-headers-footers      # Windows
```

### LLM cleanup not working

```bash
# Option 1: Set Anthropic API key
export ANTHROPIC_API_KEY=your-key-here              # macOS/Linux
$env:ANTHROPIC_API_KEY="your-key-here"              # Windows PowerShell
pip install anthropic

# Option 2: Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
```

### Windows: "execution of scripts is disabled"

If PowerShell blocks the script, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Or use the `.bat` launcher which handles this automatically.

---

## Limitations

- OCR requires Tesseract to be installed separately
- Complex layouts may not convert perfectly
- Password-protected PDFs not supported
- Some PDF forms/annotations not supported
- LLM cleanup requires either an Anthropic API key or Claude Code CLI

---

**PDF to Markdown Converter** -- Convert your PDFs to clean, structured Markdown!

*Created: 2025-08-08 | Updated: 2026-04-12*
