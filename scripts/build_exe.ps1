# Build a Windows GUI executable (no console window) using PyInstaller.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot\..

Write-Host "==> Syncing dependencies (includes dev group by default)"
uv sync

Write-Host "==> Building EXE via PyInstaller (using mb2docx-gui.spec)"
uv run pyinstaller --noconfirm --clean mb2docx-gui.spec

Write-Host "==> Done. Output in .\dist\mb2docx-gui.exe"

Pop-Location
