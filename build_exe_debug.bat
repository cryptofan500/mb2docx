@echo off
cd /d "%~dp0"
echo Building debug standalone EXE (with console window)...
uv run pyinstaller --noconfirm --clean mb2docx-gui-debug.spec
echo.
echo Build complete! Check dist/mb2docx-gui-debug.exe
pause
