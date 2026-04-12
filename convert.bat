@echo off
REM Launcher for PDF to Markdown conversion (Windows)
REM Usage: convert.bat [pdf_file or directory] [options]
powershell -ExecutionPolicy Bypass -File "%~dp0convert.ps1" %*
