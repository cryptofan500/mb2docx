@echo off
cd /d "%~dp0"
echo Building standalone EXE (release, no console)...
uv run pyinstaller --noconfirm --clean mb2docx-gui.spec
echo.
echo Build complete! Check dist/mb2docx-gui.exe
pause
