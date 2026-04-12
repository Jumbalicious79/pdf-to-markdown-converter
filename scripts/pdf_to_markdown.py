#!/usr/bin/env python3
"""
PDF to Markdown Converter
Converts PDF files to Markdown format while preserving structure and formatting.
"""

import os
import sys
import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
import logging

# Try to import required libraries
try:
    import pymupdf  # PyMuPDF (import as pymupdf, not fitz)
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFToMarkdownConverter:
    """Converts PDF files to Markdown format."""

    def __init__(self,
                 extract_images: bool = False,
                 image_dir: str = "images",
                 preserve_formatting: bool = True,
                 page_breaks: bool = True,
                 backend: str = "auto",
                 use_ocr: bool = False,
                 ocr_language: str = "eng",
                 strip_headers_footers: bool = False,
                 embed_images: bool = False,
                 image_dpi: int = 150,
                 page_separators: bool = False,
                 cleanup: bool = False):
        """
        Initialize the converter.

        Args:
            extract_images: Whether to extract images from PDF
            image_dir: Directory to save extracted images
            preserve_formatting: Try to preserve text formatting
            page_breaks: Add page break markers in markdown
            backend: Which library to use ('pymupdf4llm', 'pymupdf', 'pdfplumber', 'auto')
            use_ocr: Enable OCR for scanned PDFs (pymupdf4llm only)
            ocr_language: OCR language code (default: eng)
            strip_headers_footers: Remove repeated page headers/footers (pymupdf4llm only)
            embed_images: Embed images as base64 instead of separate files (pymupdf4llm only)
            image_dpi: Resolution for extracted images (default: 150)
            page_separators: Add page separator lines in output (pymupdf4llm only)
            cleanup: Send output through LLM for structural cleanup
        """
        self.extract_images = extract_images
        self.image_dir = image_dir
        self.preserve_formatting = preserve_formatting
        self.page_breaks = page_breaks
        self.use_ocr = use_ocr
        self.ocr_language = ocr_language
        self.strip_headers_footers = strip_headers_footers
        self.embed_images = embed_images
        self.image_dpi = image_dpi
        self.page_separators = page_separators
        self.cleanup = cleanup
        self.backend = self._select_backend(backend)

    def _select_backend(self, backend: str) -> str:
        """Select the PDF processing backend."""
        if backend == "auto":
            if PYMUPDF4LLM_AVAILABLE:
                return "pymupdf4llm"
            elif PYMUPDF_AVAILABLE:
                return "pymupdf"
            elif PDFPLUMBER_AVAILABLE:
                return "pdfplumber"
            else:
                raise ImportError(
                    "No PDF library available. Install with:\n"
                    "  pip install pymupdf4llm\n"
                    "  or\n"
                    "  pip install pymupdf\n"
                    "  or\n"
                    "  pip install pdfplumber"
                )
        elif backend == "pymupdf4llm" and not PYMUPDF4LLM_AVAILABLE:
            raise ImportError("pymupdf4llm not installed. Install with: pip install pymupdf4llm")
        elif backend == "pymupdf" and not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed. Install with: pip install pymupdf")
        elif backend == "pdfplumber" and not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")

        return backend

    def convert_file(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert a PDF file to Markdown.

        Args:
            pdf_path: Path to the PDF file
            output_path: Optional output path (defaults to same name with .md)

        Returns:
            Path to the output markdown file
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")

        # Determine output path
        if output_path is None:
            output_path = pdf_path.with_suffix('.md')
        else:
            output_path = Path(output_path)

        logger.info(f"Converting {pdf_path} to {output_path}")
        logger.info(f"Using backend: {self.backend}")

        # Extract content based on backend
        if self.backend == "pymupdf4llm":
            markdown_content = self._convert_with_pymupdf4llm(pdf_path, output_path)
        elif self.backend == "pymupdf":
            markdown_content = self._convert_with_pymupdf(pdf_path, output_path)
        else:
            markdown_content = self._convert_with_pdfplumber(pdf_path, output_path)

        # Post-process cleanup (all backends)
        markdown_content = self._cleanup_markdown(markdown_content)

        # Optional LLM cleanup
        if self.cleanup:
            markdown_content = self._llm_cleanup(markdown_content, pdf_path.name)

        # Write markdown file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding='utf-8')
        logger.info(f"Successfully converted to {output_path}")

        return str(output_path)

    def _convert_with_pymupdf4llm(self, pdf_path: Path, output_path: Path) -> str:
        """Convert using pymupdf4llm for high-quality markdown output."""
        import pymupdf4llm

        kwargs = {
            "show_progress": False,
            "force_text": True,
            "header": not self.strip_headers_footers,
            "footer": not self.strip_headers_footers,
            "page_separators": self.page_separators,
            "dpi": self.image_dpi,
        }

        # OCR settings
        if self.use_ocr:
            kwargs["use_ocr"] = True
            kwargs["force_ocr"] = False
            kwargs["ocr_language"] = self.ocr_language
            kwargs["ocr_dpi"] = 300
        else:
            kwargs["use_ocr"] = False

        # Image handling (embed_images and write_images are mutually exclusive)
        if self.extract_images:
            if self.embed_images:
                kwargs["embed_images"] = True
            else:
                image_dir = output_path.parent / self.image_dir / output_path.stem
                image_dir.mkdir(parents=True, exist_ok=True)
                kwargs["write_images"] = True
                kwargs["image_path"] = str(image_dir)

        logger.info(f"Processing {pdf_path.name} with pymupdf4llm")

        try:
            md_text = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)
        except Exception as e:
            if self.use_ocr and "ocr" in str(e).lower():
                logger.warning(f"OCR failed: {e}")
                logger.warning("Install Tesseract for scanned PDF support: brew install tesseract")
                # Retry without OCR
                kwargs["use_ocr"] = False
                md_text = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)
            else:
                raise

        # Add source header
        header = f"# {pdf_path.stem}\n\n*Converted from: {pdf_path.name}*\n\n---\n\n"

        # Fix image paths to be relative to the output file
        if self.extract_images and not self.embed_images:
            image_dir = output_path.parent / self.image_dir / output_path.stem
            rel_image_dir = os.path.relpath(image_dir, output_path.parent)
            md_text = md_text.replace(str(image_dir), rel_image_dir)

        return header + md_text

    def _convert_with_pymupdf(self, pdf_path: Path, output_path: Path) -> str:
        """Convert using PyMuPDF."""
        import pymupdf

        markdown_lines = []
        markdown_lines.append(f"# {pdf_path.stem}\n")
        markdown_lines.append(f"*Converted from: {pdf_path.name}*\n")
        markdown_lines.append("---\n")

        # Create image directory if needed
        if self.extract_images and PIL_AVAILABLE:
            image_dir = output_path.parent / self.image_dir / output_path.stem
            image_dir.mkdir(parents=True, exist_ok=True)

        doc = pymupdf.open(str(pdf_path))

        for page_num, page in enumerate(doc, 1):
            logger.info(f"Processing page {page_num}/{len(doc)}")

            # Add page marker
            if self.page_breaks and page_num > 1:
                markdown_lines.append("\n---\n")
                markdown_lines.append(f"*Page {page_num}*\n\n")

            # Extract text
            text = page.get_text()

            if self.preserve_formatting:
                # Process text to preserve structure
                text = self._process_text_formatting(text)

            markdown_lines.append(text)

            # Extract images if requested
            if self.extract_images and PIL_AVAILABLE:
                images = self._extract_page_images_pymupdf(page, page_num, image_dir)
                for img_path, img_name in images:
                    rel_path = os.path.relpath(img_path, output_path.parent)
                    markdown_lines.append(f"\n![{img_name}]({rel_path})\n")

        doc.close()

        return '\n'.join(markdown_lines)

    def _convert_with_pdfplumber(self, pdf_path: Path, output_path: Path) -> str:
        """Convert using pdfplumber."""
        import pdfplumber

        markdown_lines = []
        markdown_lines.append(f"# {pdf_path.stem}\n")
        markdown_lines.append(f"*Converted from: {pdf_path.name}*\n")
        markdown_lines.append("---\n")

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Processing page {page_num}/{len(pdf.pages)}")

                # Add page marker
                if self.page_breaks and page_num > 1:
                    markdown_lines.append("\n---\n")
                    markdown_lines.append(f"*Page {page_num}*\n\n")

                # Extract text
                text = page.extract_text() or ""

                if self.preserve_formatting:
                    text = self._process_text_formatting(text)

                markdown_lines.append(text)

                # Extract tables if present
                tables = page.extract_tables()
                for table in tables:
                    markdown_lines.append("\n" + self._table_to_markdown(table) + "\n")

        return '\n'.join(markdown_lines)

    def _process_text_formatting(self, text: str) -> str:
        """
        Process text to preserve formatting and convert to markdown.
        Used only by pymupdf and pdfplumber backends.
        """
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append("")
                continue

            # Detect headers (all caps, short lines)
            if line.isupper() and len(line) < 60:
                processed_lines.append(f"## {line.title()}")
            # Detect bullet points
            elif line.startswith(('•', '·', '-', '*', '◦')):
                processed_lines.append(f"- {line[1:].strip()}")
            # Detect numbered lists
            elif re.match(r'^\d+[\.\)]\s', line):
                processed_lines.append(line)
            # Regular paragraph
            else:
                processed_lines.append(line)

        # Join and clean up multiple blank lines
        text = '\n'.join(processed_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _table_to_markdown(self, table: List[List]) -> str:
        """Convert a table to markdown format."""
        if not table or not table[0]:
            return ""

        markdown = []

        # Header row
        header = table[0]
        markdown.append("| " + " | ".join(str(cell or "") for cell in header) + " |")
        markdown.append("|" + "|".join("---" for _ in header) + "|")

        # Data rows
        for row in table[1:]:
            markdown.append("| " + " | ".join(str(cell or "") for cell in row) + " |")

        return '\n'.join(markdown)

    def _extract_page_images_pymupdf(self, page, page_num: int, image_dir: Path) -> List[Tuple[str, str]]:
        """Extract images from a page using PyMuPDF."""
        images = []
        image_list = page.get_images()

        for img_index, img in enumerate(image_list, 1):
            try:
                # Get image data
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]

                # Save image
                image_name = f"page_{page_num}_img_{img_index}.png"
                image_path = image_dir / image_name

                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                images.append((str(image_path), image_name))
                logger.info(f"Extracted image: {image_name}")

            except Exception as e:
                logger.warning(f"Failed to extract image {img_index} on page {page_num}: {e}")

        return images

    # ── Post-processing ─────────────────────────────────────────────

    def _cleanup_markdown(self, text: str) -> str:
        """Post-process markdown to fix common conversion artifacts."""
        # Remove unicode replacement characters (common in TOC/dotted leaders)
        text = text.replace('\ufffd', '')

        # Remove image placeholder lines
        text = re.sub(r'\*\*==> picture \[\d+ x \d+\] intentionally omitted <==\*\*\n?', '', text)

        # Convert "picture text" blocks into proper markdown tables where possible
        text = self._convert_picture_text_tables(text)

        # Remove duplicate/near-duplicate headers (e.g., "# **I NTRODUCTION**" followed by "## INTRODUCTION")
        text = self._deduplicate_headers(text)

        # Strip trailing whitespace from each line
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)

        # Collapse 3+ consecutive blank lines to 2
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Normalize header levels (compress gaps)
        text = self._normalize_header_levels(text)

        # Fix broken table formatting
        text = self._fix_table_formatting(text)

        # Ensure file ends with single newline
        text = text.rstrip('\n') + '\n'

        return text

    def _convert_picture_text_tables(self, text: str) -> str:
        """Convert picture text blocks with tabular data into markdown tables."""
        # Match picture text blocks
        pattern = re.compile(
            r'\*\*----- Start of picture text -----\*\*<br>\n'
            r'(.*?)'
            r'\*\*----- End of picture text -----\*\*<br>',
            re.DOTALL
        )

        def convert_block(match):
            block = match.group(1)
            # Split on <br> tags to get rows
            raw_lines = re.split(r'<br>\s*\n?', block)
            lines = [line.strip() for line in raw_lines if line.strip()]

            if not lines:
                return ''

            # Try to detect if this is tabular data by checking for consistent
            # column-like spacing (2+ spaces between items) in multiple lines
            tabular_lines = []
            for line in lines:
                # Split on 2+ spaces (column separator heuristic)
                cols = re.split(r'\s{2,}', line)
                tabular_lines.append(cols)

            # Check if most lines have a similar column count (table-like)
            col_counts = [len(cols) for cols in tabular_lines]
            if not col_counts:
                return '\n'.join(lines) + '\n'

            most_common_count = max(set(col_counts), key=col_counts.count)

            # If at least half the lines have similar column counts and >1 column, render as table
            matching = sum(1 for c in col_counts if c == most_common_count)
            if most_common_count > 1 and matching >= len(col_counts) * 0.4:
                # Normalize all rows to the same column count
                table_rows = []
                for cols in tabular_lines:
                    if len(cols) < most_common_count:
                        cols.extend([''] * (most_common_count - len(cols)))
                    elif len(cols) > most_common_count:
                        # Merge extra columns into the last one
                        cols = cols[:most_common_count - 1] + ['  '.join(cols[most_common_count - 1:])]
                    table_rows.append(cols)

                # Build markdown table
                md_lines = []
                md_lines.append('| ' + ' | '.join(table_rows[0]) + ' |')
                md_lines.append('|' + '|'.join('---' for _ in table_rows[0]) + '|')
                for row in table_rows[1:]:
                    md_lines.append('| ' + ' | '.join(row) + ' |')
                return '\n'.join(md_lines) + '\n'
            else:
                # Not tabular, just return as plain text
                return '\n'.join(lines) + '\n'

        return pattern.sub(convert_block, text)

    def _deduplicate_headers(self, text: str) -> str:
        """Remove duplicate or near-duplicate headers, including running page headers."""
        lines = text.split('\n')
        result = []
        prev_header_text = None

        # First pass: detect running headers (repeated headers that appear 3+ times)
        header_counts = {}
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                normalized = self._normalize_header_text(header_match.group(2))
                header_counts[normalized] = header_counts.get(normalized, 0) + 1

        # Headers appearing 3+ times are likely running page headers
        running_headers = {h for h, count in header_counts.items() if count >= 3}

        # Track which running headers we've already kept
        seen_running = set()

        # Second pass: remove duplicates and running headers
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                normalized = self._normalize_header_text(header_match.group(2))

                # Skip running page headers (keep the first occurrence)
                if normalized in running_headers:
                    if normalized not in seen_running:
                        seen_running.add(normalized)
                        result.append(line)
                    else:
                        continue
                elif prev_header_text and prev_header_text == normalized:
                    # Skip consecutive duplicate
                    continue
                else:
                    result.append(line)

                prev_header_text = normalized
            else:
                if line.strip():
                    prev_header_text = None
                result.append(line)

        return '\n'.join(result)

    @staticmethod
    def _normalize_header_text(text: str) -> str:
        """Normalize header text for comparison (strip formatting, spaces, case)."""
        text = re.sub(r'[*_`]', '', text)       # Remove markdown formatting
        text = re.sub(r'\s+', '', text).upper()  # Remove ALL spaces and uppercase
        return text

    def _normalize_header_levels(self, text: str) -> str:
        """Compress header level gaps (e.g., #, ### -> #, ##)."""
        header_pattern = re.compile(r'^(#{1,6})\s', re.MULTILINE)

        # Find all header levels used
        levels_used = sorted(set(
            len(m.group(1)) for m in header_pattern.finditer(text)
        ))

        if len(levels_used) <= 1:
            return text

        # Build mapping: only compress if there are gaps
        has_gaps = False
        for i in range(1, len(levels_used)):
            if levels_used[i] - levels_used[i - 1] > 1:
                has_gaps = True
                break

        if not has_gaps:
            return text

        # Map each used level to consecutive levels starting from the minimum
        min_level = levels_used[0]
        level_map = {}
        for i, level in enumerate(levels_used):
            level_map[level] = min_level + i

        def replace_header(match):
            old_level = len(match.group(1))
            new_level = level_map.get(old_level, old_level)
            return '#' * new_level + ' '

        return header_pattern.sub(replace_header, text)

    def _fix_table_formatting(self, text: str) -> str:
        """Fix common table formatting issues."""
        lines = text.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Detect a table row (has pipes and content)
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                # Collect the full table block
                table_lines = []
                while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_lines.append(lines[i])
                    i += 1

                # Check if separator row exists (row 2 should be |---|---|)
                has_separator = (
                    len(table_lines) >= 2
                    and re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|$', table_lines[1].strip())
                )

                if not has_separator and len(table_lines) >= 2:
                    # Insert a separator after the first row
                    col_count = table_lines[0].count('|') - 1
                    separator = '|' + '|'.join('---' for _ in range(col_count)) + '|'
                    table_lines.insert(1, separator)

                result.extend(table_lines)
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)

    # ── LLM cleanup ─────────────────────────────────────────────────

    def _llm_cleanup(self, text: str, source_name: str = "") -> str:
        """
        Use an LLM to clean up markdown structure.

        Tries two modes in order:
        1. Anthropic API (if ANTHROPIC_API_KEY is set and anthropic package installed)
        2. Claude Code CLI subprocess (if 'claude' command is available)

        Silently returns original text if neither is available.
        """
        system_prompt = (
            "You are a markdown document cleanup assistant. "
            "Fix structural issues in this converted-from-PDF markdown: "
            "fix header hierarchy, clean up broken tables, remove conversion artifacts "
            "(page numbers in wrong places, repeated headers/footers, broken sentences "
            "split across lines that should be joined), "
            "fix list formatting, and improve readability. "
            "Preserve ALL actual content — do not summarize or remove information. "
            "Return ONLY the cleaned markdown with no commentary or explanation."
        )

        # Mode 1: Anthropic API
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                logger.info("Using Anthropic API for LLM cleanup")
                return self._llm_cleanup_via_api(text, system_prompt)
            except ImportError:
                logger.info("anthropic package not installed, trying Claude CLI...")
            except Exception as e:
                logger.warning(f"Anthropic API cleanup failed: {e}")
                logger.info("Falling back to Claude CLI...")

        # Mode 2: Claude Code CLI
        if shutil.which("claude"):
            logger.info("Using Claude Code CLI for LLM cleanup")
            return self._llm_cleanup_via_cli(text, system_prompt)

        # Neither available
        logger.warning(
            "LLM cleanup requested but unavailable. Options:\n"
            "  1. Set ANTHROPIC_API_KEY and install anthropic: pip install anthropic\n"
            "  2. Install Claude Code CLI: npm install -g @anthropic-ai/claude-code\n"
            "Returning unmodified markdown."
        )
        return text

    def _llm_cleanup_via_api(self, text: str, system_prompt: str) -> str:
        """Clean up markdown using the Anthropic API directly."""
        import anthropic

        client = anthropic.Anthropic()
        max_chunk_size = 80000

        if len(text) <= max_chunk_size:
            chunks = [text]
        else:
            chunks = self._split_into_chunks(text, max_chunk_size)

        cleaned_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"LLM cleanup: processing chunk {i + 1}/{len(chunks)}")
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16384,
                system=system_prompt,
                messages=[{"role": "user", "content": chunk}],
            )
            cleaned_chunks.append(message.content[0].text)

        return "\n\n".join(cleaned_chunks)

    def _llm_cleanup_via_cli(self, text: str, system_prompt: str) -> str:
        """Clean up markdown using the Claude Code CLI as a subprocess."""
        prompt = f"{system_prompt}\n\nHere is the markdown to clean up:\n\n{text}"

        try:
            result = subprocess.run(
                ["claude", "--print", "--prompt", prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                logger.warning(f"Claude CLI returned non-zero or empty output: {result.stderr}")
                return text
        except subprocess.TimeoutExpired:
            logger.warning("Claude CLI timed out after 120 seconds")
            return text
        except Exception as e:
            logger.warning(f"Claude CLI cleanup failed: {e}")
            return text

    def _split_into_chunks(self, text: str, max_size: int) -> List[str]:
        """Split text into chunks at paragraph boundaries."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para) + 2  # +2 for the \n\n separator
            if current_size + para_size > max_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    # ── Directory conversion ─────────────────────────────────────────

    def convert_directory(self, input_dir: str, output_dir: Optional[str] = None) -> List[str]:
        """
        Convert all PDF files in a directory.

        Args:
            input_dir: Directory containing PDF files
            output_dir: Optional output directory (defaults to same as input)

        Returns:
            List of output file paths
        """
        input_path = Path(input_dir)

        if not input_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {input_dir}")

        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path

        pdf_files = list(input_path.glob("*.pdf")) + list(input_path.glob("*.PDF"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return []

        output_files = []

        for pdf_file in pdf_files:
            try:
                output_file = output_path / pdf_file.with_suffix('.md').name
                result = self.convert_file(str(pdf_file), str(output_file))
                output_files.append(result)
            except Exception as e:
                logger.error(f"Failed to convert {pdf_file}: {e}")

        return output_files


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single PDF
  %(prog)s document.pdf

  # Convert with custom output
  %(prog)s document.pdf -o notes.md

  # Convert all PDFs in a directory
  %(prog)s --dir ./pdfs --output-dir ./markdown

  # Extract images
  %(prog)s document.pdf --extract-images

  # Enable OCR for scanned PDFs
  %(prog)s document.pdf --ocr

  # Strip headers/footers and use LLM cleanup
  %(prog)s document.pdf --strip-headers-footers --cleanup

  # Use specific backend
  %(prog)s document.pdf --backend pdfplumber
        """
    )

    parser.add_argument('pdf_file', nargs='?', help='Path to PDF file')
    parser.add_argument('-o', '--output', help='Output markdown file path')
    parser.add_argument('--dir', dest='directory', help='Convert all PDFs in directory')
    parser.add_argument('--output-dir', help='Output directory for batch conversion')
    parser.add_argument('--extract-images', action='store_true',
                       help='Extract images from PDF')
    parser.add_argument('--image-dir', default='images',
                       help='Directory for extracted images (default: images)')
    parser.add_argument('--no-formatting', action='store_true',
                       help='Disable formatting preservation')
    parser.add_argument('--no-page-breaks', action='store_true',
                       help='Disable page break markers')
    parser.add_argument('--backend', choices=['auto', 'pymupdf4llm', 'pymupdf', 'pdfplumber'],
                       default='auto', help='PDF processing backend (default: pymupdf4llm if available)')
    parser.add_argument('--ocr', action='store_true',
                       help='Enable OCR for scanned PDFs (pymupdf4llm backend only)')
    parser.add_argument('--ocr-language', default='eng',
                       help='OCR language code (default: eng)')
    parser.add_argument('--strip-headers-footers', action='store_true',
                       help='Remove repeated page headers and footers (pymupdf4llm backend only)')
    parser.add_argument('--page-separators', action='store_true',
                       help='Add page separator lines in output (pymupdf4llm backend only)')
    parser.add_argument('--embed-images', action='store_true',
                       help='Embed images as base64 instead of separate files (pymupdf4llm backend only)')
    parser.add_argument('--image-dpi', type=int, default=150,
                       help='Image resolution in DPI (default: 150)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Send output through LLM for structural cleanup (uses Anthropic API or Claude CLI)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if neither file nor directory specified
    if not args.pdf_file and not args.directory:
        parser.error("Either provide a PDF file or use --dir for batch conversion")

    # Create converter
    converter = PDFToMarkdownConverter(
        extract_images=args.extract_images,
        image_dir=args.image_dir,
        preserve_formatting=not args.no_formatting,
        page_breaks=not args.no_page_breaks,
        backend=args.backend,
        use_ocr=args.ocr,
        ocr_language=args.ocr_language,
        strip_headers_footers=args.strip_headers_footers,
        embed_images=args.embed_images,
        image_dpi=args.image_dpi,
        page_separators=args.page_separators,
        cleanup=args.cleanup,
    )

    try:
        if args.directory:
            # Batch conversion
            output_files = converter.convert_directory(args.directory, args.output_dir)
            print(f"\n✅ Converted {len(output_files)} files")
            for file in output_files:
                print(f"  • {file}")
        else:
            # Single file conversion
            output = converter.convert_file(args.pdf_file, args.output)
            print(f"✅ Successfully converted to: {output}")

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall required packages:")
        print("  pip install pymupdf4llm pillow")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
