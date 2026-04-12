@echo off
REM Launcher for batch PDF to Markdown conversion (Windows)
REM Usage: convert_all.bat [options]
powershell -ExecutionPolicy Bypass -File "%~dp0convert_all.ps1" %*
