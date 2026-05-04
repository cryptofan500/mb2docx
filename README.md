# mb2docx

Local Windows 10+ tool (GUI + CLI) to convert AI **markdown-box** CV / cover letter text into **ATS-friendly** `.docx` files.

**Version 9.3.0** - Audit fixes: cover-letter heading, footer dedup, structural tests, tracked PyInstaller specs, CI lint

## Changelog

### V9.3.0 (May 2026)
- **Fix:** Cover letter `# Name` markdown headings now render correctly (previously the `#` prefix prevented name detection, so `# Pawel Zawadzki` was treated as a section heading).
- **Fix:** Phone/email no longer duplicated between cover-letter header and signature when supplied only at the bottom of the input — promoted contact lines are tracked and stripped from the closing block.
- **Test:** New `tests/test_docx_writer.py` adds structural assertions (font size, bold, alignment, hanging indent, PIPE separator) for the rendered DOCX.
- **Build:** PyInstaller spec files (`mb2docx-gui.spec`, `mb2docx-gui-debug.spec`) are now tracked. `build_exe.bat` and `build_exe_debug.bat` invoke them directly so release/debug builds are reproducible.
- **CI:** Re-enabled `ruff check src/ tests/` between dependency install and pytest. Cleared accumulated lint debt across `src/` and `tests/` (PEP 585 type hints, import sorting, `contextlib.suppress`). `gui.py` is intentionally out of scope for this pass.

### V9.2.0 (January 2026)
- **Fix:** CV bullet indentation now matches Gold Standard (0.5" left indent, was 0.25")
- **Fix:** Job entry dates no longer bold (only title is bold, matching Gold Standard)
- **Fix:** `**` markdown markers stripped from job titles (was showing literally)
- **Fix:** Contact line preserved exactly as input (no reordering when pipe-separated)
- Cover Letter formatting verified perfect
- Program is faithful to input: spelling, capitalization, omissions preserved as-is

### V9.1.0 (January 2026)
- **Fix:** Cover Letter name now renders as 18pt, BOLD, CENTERED (was incorrectly left-aligned body text)
- **Fix:** Cover Letter contact info now renders as 10pt, CENTERED, pipe-separated (was merged into first paragraph)
- **Fix:** Bullet text now wraps under text with hanging indent (was wrapping under bullet character)
- All launcher files now portable (no hardcoded paths)

### V9.0.0
- Forensic format matching to Bob Frok exemplars
- PIPE separator for job entries (not TAB)
- Comprehensive test suite (27+ tests)

## Requirements

- Windows 10+
- Python 3.10+
- `uv` package manager

## Installation

```powershell
uv sync
```

## Running the Application

### Method 1: Double-click `run.bat`
The simplest way - just double-click `run.bat` in the project folder.

### Method 2: Double-click `run.vbs`
Silent launcher - no console window.

### Method 3: Command line with uv
```powershell
uv run mb2docx-gui
```

### Method 4: Python module
```powershell
uv run python -m mb2docx.gui
```

### Method 5: Standalone EXE
```powershell
dist\mb2docx-gui.exe
```
Build with `build_exe.bat` (release, no console window) or `build_exe_debug.bat`
(includes a console for troubleshooting). Both scripts call PyInstaller against
the tracked spec files `mb2docx-gui.spec` and `mb2docx-gui-debug.spec`.

### CLI Usage
```powershell
uv run mb2docx --help
```

## Features

- Paste CV + optional cover letter directly into the GUI
- Generates:
  - `CV_[YourName].docx`
  - `CoverLetter_[YourName].docx` (if provided)
  - Optional: `CV_and_CoverLetter_[YourName].docx` (combined; default OFF)
- **Professional formatting**: Matches healthcare industry standards
- Strict subset Markdown support:
  - Headings (`#`, `##`, ...)
  - Bullets (`-`, `*`, `•`) with hanging indent
  - Numbered lists (`1.`, `1)`)
  - Bold (`**text**`)
  - Paragraphs separated by blank lines
- Cleans typical copy/paste artifacts:
  - Removes ``` fences
  - Removes leading `>` quote markers
  - Removes zero-width formatting chars

## Output Format

Documents follow professional standards:
- **Calibri font** (most ATS-compatible)
- **Name**: 18pt bold, centered, ALL CAPS
- **Contact**: 10pt, centered, pipe-separated
- **Section headings**: 12pt bold, ALL CAPS
- **Job entries**: Bold title, non-bold date with pipe separator
- **Institutions**: 11pt italic
- **Body text**: 11pt
- **Bullets**: Hanging indent (text wraps under text, not under bullet)
- No tables, columns, or graphics (ATS-hostile)

## Development

```powershell
# Run tests
uv run pytest tests/ -v

# Type checking
uv run mypy src/

# Linting (run on the same paths as CI)
uv run ruff check src/ tests/
```

## Author

Pawel Zawadzki
