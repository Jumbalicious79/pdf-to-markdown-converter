# PDF to Markdown Converter - Windows PowerShell script
# Usage: .\convert.ps1 [pdf_file or directory] [options]
# Extra flags (--ocr, --cleanup, etc.) are passed through to the Python script

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check Python installation
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: Python is not installed" -ForegroundColor Red
        Write-Host "Please install Python 3 first: https://www.python.org/downloads/"
        exit 1
    }
    $python = "python3"
} else {
    $python = "python"
}

# Check if virtual environment exists
$venvPath = Join-Path $ScriptDir "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    & $python -m venv venv

    # Activate virtual environment
    & $venvActivate

    # Install requirements
    Write-Host "Installing requirements..." -ForegroundColor Cyan
    pip install --upgrade pip 2>&1 | Out-Null
    pip install pymupdf4llm pillow 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to install dependencies" -ForegroundColor Red
        Write-Host "Try manually: pip install pymupdf4llm pillow"
        exit 1
    }
} else {
    # Activate existing virtual environment
    & $venvActivate
}

# Parse arguments: first positional arg is the file/dir, rest are extra flags
if ($args.Count -eq 0) {
    # No arguments - show help
    & $python scripts\pdf_to_markdown.py --help
} elseif (Test-Path $args[0] -PathType Container) {
    # Directory provided
    $dirArg = $args[0]
    $extraArgs = $args[1..($args.Count - 1)]
    Write-Host "Converting all PDFs in directory: $dirArg" -ForegroundColor Cyan
    & $python scripts\pdf_to_markdown.py --dir $dirArg --output-dir output\ @extraArgs
} else {
    # File provided
    $pdfFile = $args[0]
    Write-Host "Converting PDF: $pdfFile" -ForegroundColor Cyan

    if ($args.Count -ge 2 -and -not $args[1].StartsWith("--")) {
        # Second arg is output path
        $outputArg = $args[1]
        $extraArgs = if ($args.Count -gt 2) { $args[2..($args.Count - 1)] } else { @() }
        & $python scripts\pdf_to_markdown.py $pdfFile -o $outputArg @extraArgs
    } else {
        # Default output to output/ directory
        $filename = [System.IO.Path]::GetFileNameWithoutExtension($pdfFile)
        $extraArgs = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }
        & $python scripts\pdf_to_markdown.py $pdfFile -o "output\$filename.md" @extraArgs
    }
}

# Deactivate virtual environment
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
}
