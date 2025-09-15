# PDF to Markdown Converter

A Python tool that converts PDF files to Markdown format while preserving structure, formatting, and optionally extracting images.

## 🚀 Quick Start (3 Steps)

### Option 1: Auto-Convert Everything (Easiest!)

1. **Place your PDFs** in the `input/` directory (including subdirectories!)
2. **Run**: `./convert_all.sh`  
3. **Get your Markdown files** from the `output/` directory with matching structure

### Option 2: Convert Specific File

```bash
./convert.sh document.pdf
# Output appears in output/document.md
```

**That's it!** Dependencies install automatically on first run. 🎉

## Features

- 📄 **Convert single PDFs or entire directories**
- 🎨 **Preserve text formatting and structure** (headers, lists, tables)
- 🖼️ **Extract and embed images** (optional)
- 📊 **Table detection and conversion** to Markdown tables
- 📑 **Page break markers** for multi-page documents
- 🔄 **Multiple PDF backends** (PyMuPDF or pdfplumber)
- 🚀 **Batch processing** for multiple files
- 📁 **Directory structure preservation** - subdirectories maintained in output
- ⚡ **Auto-setup** - no manual dependency installation

## Usage Examples

### Simple Commands

```bash
# Auto-convert all PDFs in input/ directory (including subdirectories)
./convert_all.sh

# Convert specific PDF
./convert.sh document.pdf

# Convert with images extracted
python3 scripts/pdf_to_markdown.py document.pdf --extract-images

# Convert directory with better table detection
python3 scripts/pdf_to_markdown.py --dir ./pdfs --backend pdfplumber
```

### Advanced Usage

```bash
# Full control with all options
python3 scripts/pdf_to_markdown.py document.pdf \
  --extract-images \
  --image-dir custom-images \
  --backend pdfplumber \
  --output custom-name.md \
  --verbose

# Batch convert directory
python3 scripts/pdf_to_markdown.py --dir ./documents --output-dir ./converted
```

### Python API

```python
from scripts.pdf_to_markdown import PDFToMarkdownConverter

# Create converter with options
converter = PDFToMarkdownConverter(
    extract_images=True,
    preserve_formatting=True,
    page_breaks=True
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
| `--image-dir` | Directory for extracted images | `images` |
| `--no-formatting` | Disable formatting preservation | False |
| `--no-page-breaks` | Disable page break markers | False |
| `--backend` | PDF library (auto/pymupdf/pdfplumber) | `auto` |
| `--verbose, -v` | Enable verbose output | False |

## Output Format

The converter produces clean Markdown with:

- **Headers** detected from formatting (ALL CAPS → `## Headers`)
- **Lists** (bullet points and numbered lists)
- **Tables** converted to Markdown format
- **Images** embedded with proper paths (if extracted)
- **Page breaks** marked with horizontal rules
- **Metadata** (source file information)

### Example Output

```markdown
# Document Title

*Converted from: document.pdf*

---

## Chapter 1

This is the content from the PDF with preserved formatting.

- Bullet point 1
- Bullet point 2

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

![Page 1 Image](images/document/page_1_img_1.png)

---
*Page 2*

Content continues...
```

## PDF Processing Backends

The converter supports two backends (auto-selected or specify with `--backend`):

### PyMuPDF (Default)
- **Pros**: Fast, handles complex PDFs well, excellent image extraction
- **Cons**: Larger installation size
- **Best for**: Documents with images, complex layouts

### pdfplumber  
- **Pros**: Superior table detection, lighter weight
- **Cons**: Slower, limited image support
- **Best for**: Documents with lots of tables

## Project Structure

```
pdf-to-markdown-converter/
├── convert.sh              # Easy wrapper script
├── convert_all.sh          # Auto-convert all PDFs in input/ (including subdirs)
├── scripts/
│   └── pdf_to_markdown.py  # Main converter (500+ lines)
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
# or
pip install pymupdf pillow
```

## Requirements

- **Python 3.7+**
- **PyMuPDF** or **pdfplumber** (auto-installed)
- **Pillow** for image extraction (auto-installed)

## Troubleshooting

### Common Issues

**❌ ImportError: No PDF library available**
```bash
pip install pymupdf
# or
pip install pdfplumber
```

**❌ Images not extracting**
```bash
pip install pillow
# Use --extract-images flag
```

**❌ Poor text extraction**
- Try different backend: `--backend pdfplumber`
- Some scanned PDFs need OCR (not currently supported)

**❌ Tables not formatting correctly**
- Use pdfplumber backend: `--backend pdfplumber`

## Limitations

- Does not perform OCR on scanned PDFs
- Complex layouts may not convert perfectly  
- Password-protected PDFs not supported
- Some PDF forms/annotations not supported

## Advanced Features

- **Smart header detection**: ALL CAPS text becomes headers
- **List recognition**: Bullet points and numbers
- **Table extraction**: PDF tables → Markdown tables  
- **Image embedding**: Automatic image extraction and linking
- **Batch processing**: Handle entire directories
- **Error handling**: Graceful failure with helpful messages
- **Cross-platform**: Works on macOS, Linux, Windows

## Workflow Examples

### Daily Document Processing
```bash
# Organize PDFs in subdirectories, then convert all
cp ~/Downloads/reports/*.pdf input/reports/
cp ~/Downloads/manuals/*.pdf input/manuals/
./convert_all.sh
open output/
```

### Organized File Processing
```bash
# Directory structure is preserved in output
input/
├── reports/
│   ├── 2024/
│   │   └── quarterly-report.pdf
│   └── monthly-summary.pdf
└── manuals/
    └── user-guide.pdf

# After ./convert_all.sh:
output/
├── reports/
│   ├── 2024/
│   │   └── quarterly-report.md
│   └── monthly-summary.md
└── manuals/
    └── user-guide.md
```

### Academic Papers  
```bash
# Convert with images for papers with figures
python3 scripts/pdf_to_markdown.py research-paper.pdf --extract-images
```

### Business Reports
```bash  
# Use pdfplumber for better table handling
python3 scripts/pdf_to_markdown.py quarterly-report.pdf --backend pdfplumber
```

---

**🎉 PDF to Markdown Converter** - Convert your PDFs to clean, structured Markdown in seconds!

*Created: 2025-08-08*