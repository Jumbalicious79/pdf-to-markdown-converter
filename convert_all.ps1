# Auto-convert all PDFs in input/ directory (including subdirectories) - Windows PowerShell
# Usage: .\convert_all.ps1 [options]
# Extra flags (--ocr, --cleanup, etc.) are passed through to the Python script

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check Python installation
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: Python 3 is not installed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install Python 3 on Windows:" -ForegroundColor Yellow
        Write-Host "  1. Download from https://www.python.org/downloads/"
        Write-Host "  2. Run the installer"
        Write-Host "  3. IMPORTANT: Check 'Add Python to PATH' during installation"
        Write-Host ""
        Write-Host "Or install via winget:" -ForegroundColor Yellow
        Write-Host "  winget install Python.Python.3.13"
        exit 1
    }
    $python = "python3"
} else {
    $python = "python"
}

# Check and activate virtual environment
$venvPath = Join-Path $ScriptDir "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found. Run .\convert.ps1 first to set up." -ForegroundColor Yellow
    exit 1
}
& $venvActivate

Write-Host "Auto-converting all PDFs in input/ directory (including subdirectories)" -ForegroundColor Cyan
Write-Host "=================================================="

# Check if input directory exists
$inputDir = Join-Path $ScriptDir "input"
if (-not (Test-Path $inputDir)) {
    Write-Host "ERROR: input/ directory not found" -ForegroundColor Red
    exit 1
}

# Find all PDFs in input directory (including subdirectories)
$pdfFiles = Get-ChildItem -Path $inputDir -Include "*.pdf", "*.PDF" -Recurse -File

if ($pdfFiles.Count -eq 0) {
    Write-Host "No PDF files found in input/ directory or subdirectories" -ForegroundColor Yellow
    Write-Host "Place your PDF files in the input/ directory (or subdirectories) first"
    exit 0
}

Write-Host "Found $($pdfFiles.Count) PDF file(s) to convert" -ForegroundColor Green

# Show files found
Write-Host ""
Write-Host "PDF files found:" -ForegroundColor Cyan
foreach ($pdf in $pdfFiles) {
    $relPath = $pdf.FullName.Substring($ScriptDir.Length + 1)
    Write-Host "  $relPath"
}

Write-Host ""
Write-Host "Starting conversions..." -ForegroundColor Cyan
Write-Host ""

# Process each PDF individually to preserve directory structure
foreach ($pdf in $pdfFiles) {
    # Get relative path from input/ directory
    $relPath = $pdf.FullName.Substring($inputDir.Length + 1)
    $relDir = Split-Path -Parent $relPath

    # Create output directory structure
    $outputDir = Join-Path $ScriptDir "output"
    if ($relDir) {
        $outputDir = Join-Path $outputDir $relDir
    }
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    # Get filename without extension
    $filename = [System.IO.Path]::GetFileNameWithoutExtension($pdf.Name)

    # Full output path
    $outputFile = Join-Path $outputDir "$filename.md"

    $inputRelPath = $pdf.FullName.Substring($ScriptDir.Length + 1)
    $outputRelPath = $outputFile.Substring($ScriptDir.Length + 1)
    Write-Host "Converting: $inputRelPath -> $outputRelPath" -ForegroundColor Cyan

    # Convert the PDF (pass through any extra flags)
    & $python scripts\pdf_to_markdown.py $pdf.FullName -o $outputFile @args
}

Write-Host ""
Write-Host "All conversions complete!" -ForegroundColor Green
Write-Host "Check the output/ directory for your markdown files" -ForegroundColor Cyan

# List converted files
$outputDir = Join-Path $ScriptDir "output"
if (Test-Path $outputDir) {
    Write-Host ""
    Write-Host "Converted files:"
    Get-ChildItem -Path $outputDir -Include "*.md" -Recurse -File | Sort-Object FullName | ForEach-Object {
        $relPath = $_.FullName.Substring($ScriptDir.Length + 1)
        Write-Host "  OK $relPath" -ForegroundColor Green
    }
}

# Deactivate virtual environment
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
}
