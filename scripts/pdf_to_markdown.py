#!/usr/bin/env python3
"""
PDF to Markdown Converter
Converts PDF files to Markdown format while preserving structure and formatting.
"""

import os
import sys
import argparse
import re
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
                 backend: str = "auto"):
        """
        Initialize the converter.
        
        Args:
            extract_images: Whether to extract images from PDF
            image_dir: Directory to save extracted images
            preserve_formatting: Try to preserve text formatting
            page_breaks: Add page break markers in markdown
            backend: Which library to use ('pymupdf', 'pdfplumber', 'auto')
        """
        self.extract_images = extract_images
        self.image_dir = image_dir
        self.preserve_formatting = preserve_formatting
        self.page_breaks = page_breaks
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
        
        # Write markdown file
        output_path.write_text(markdown_content, encoding='utf-8')
        logger.info(f"Successfully converted to {output_path}")
        
        return str(output_path)
    
    def _convert_with_pymupdf4llm(self, pdf_path: Path, output_path: Path) -> str:
        """Convert using pymupdf4llm for high-quality markdown output."""
        import pymupdf4llm

        # Build options
        kwargs = {
            "show_progress": False,
        }

        # Handle image extraction
        if self.extract_images:
            image_dir = output_path.parent / self.image_dir / output_path.stem
            image_dir.mkdir(parents=True, exist_ok=True)
            kwargs["write_images"] = True
            kwargs["image_path"] = str(image_dir)

        logger.info(f"Processing {pdf_path.name} with pymupdf4llm")
        md_text = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)

        # Add source header
        header = f"# {pdf_path.stem}\n\n*Converted from: {pdf_path.name}*\n\n---\n\n"

        # Fix image paths to be relative to the output file
        if self.extract_images:
            rel_image_dir = os.path.relpath(
                output_path.parent / self.image_dir / output_path.stem,
                output_path.parent
            )
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
        backend=args.backend
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
        print("  pip install pymupdf pillow")
        print("  or")
        print("  pip install pdfplumber pillow")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()