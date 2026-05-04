"""Configuration and defaults for mb2docx V9 - Forensic Verbatim.

This configuration matches the exact formatting extracted from the
Bob_Frok_CV.docx and Bob_Frok_CL.docx exemplars using analyze_exemplar.py.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class DocxStyleConfig:
    """Document styling configuration for exact exemplar match.

    All values extracted from gold-standard DOCX files using analyze_exemplar.py.
    """
    # Font
    font_name: str = "Calibri"

    # Font sizes (points)
    name_size_pt: int = 18
    contact_size_pt: int = 10
    section_heading_size_pt: int = 12  # FORENSIC: Exemplar uses 12pt, not 11pt
    body_size_pt: int = 11

    # Margins (inches)
    margin_inches: float = 1.0  # FORENSIC: Exemplar uses 1.0", not 0.75"

    # Tab stop position for right-aligned dates (inches)
    # For 1.0" margins: 8.5" - 1.0" - 1.0" = 6.5"
    tab_stop_inches: float = 6.5  # FORENSIC: Was 7.0, now 6.5

    # Job entry separator pattern - THE KEY FIX
    # "PIPE" = render as "Title | Date" inline text (Bob Frok exemplar style)
    # "TAB" = render as "Title\tDate" with right-aligned tab stop
    # "NONE" = no date on same line
    job_entry_separator: Literal["PIPE", "TAB", "NONE"] = "PIPE"

    # Spacing (points) - all extracted from exemplar XML
    space_after_name_pt: int = 0      # FORENSIC: 0pt (tight)
    space_after_contact_pt: int = 10  # FORENSIC: 200 twips = 10pt
    space_before_section_pt: int = 12 # FORENSIC: 240 twips = 12pt
    space_after_section_pt: int = 6   # FORENSIC: 120 twips = 6pt
    space_after_job_entry_pt: int = 0 # FORENSIC: 0pt (tight to institution)
    space_after_institution_pt: int = 5  # FORENSIC: 100 twips = 5pt
    space_after_paragraph_pt: int = 10   # FORENSIC: 200 twips = 10pt
    space_after_bullet_pt: int = 0       # FORENSIC: 0pt (tight bullets)
    space_after_last_bullet_pt: int = 10 # FORENSIC: 10pt before next section


# ============================================================================
# PRE-CONFIGURED STYLES - Extracted from Bob Frok exemplars
# ============================================================================

CV_STYLE = DocxStyleConfig(
    font_name="Calibri",
    name_size_pt=18,
    contact_size_pt=10,
    section_heading_size_pt=12,  # FORENSIC: 12pt, NOT 11pt
    body_size_pt=11,
    margin_inches=1.0,           # FORENSIC: 1.0", NOT 0.75"
    tab_stop_inches=6.5,         # FORENSIC: 6.5", NOT 7.0"
    job_entry_separator="PIPE",  # CRITICAL: PIPE, NOT TAB
    space_after_name_pt=0,
    space_after_contact_pt=10,
    space_before_section_pt=12,
    space_after_section_pt=6,
    space_after_job_entry_pt=0,
    space_after_institution_pt=5,
    space_after_paragraph_pt=10,
    space_after_bullet_pt=0,
    space_after_last_bullet_pt=10,
)

CL_STYLE = DocxStyleConfig(
    font_name="Calibri",
    name_size_pt=18,
    contact_size_pt=10,
    section_heading_size_pt=11,
    body_size_pt=11,
    margin_inches=1.0,
    tab_stop_inches=6.5,
    job_entry_separator="NONE",
    space_after_name_pt=0,
    space_after_contact_pt=20,
    space_before_section_pt=12,
    space_after_section_pt=6,
    space_after_job_entry_pt=0,
    space_after_institution_pt=5,
    space_after_paragraph_pt=10,
    space_after_bullet_pt=0,
    space_after_last_bullet_pt=10,
)


# ============================================================================
# SETTINGS PERSISTENCE (unchanged from V7)
# ============================================================================

def _get_config_dir() -> Path:
    """Get cross-platform config directory."""
    if os.name == 'nt':
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            return Path(appdata) / 'mb2docx'
    else:
        return Path.home() / '.config' / 'mb2docx'
    return Path.home() / '.mb2docx'


def _get_config_path() -> Path:
    """Get path to settings file."""
    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'settings.json'


def load_saved_author() -> str | None:
    """Load saved author name from config."""
    try:
        config_path = _get_config_path()
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding='utf-8'))
            return data.get('author_name')
    except Exception:
        pass
    return None


def save_author(name: str) -> None:
    """Save author name to config."""
    try:
        config_path = _get_config_path()
        data = {}
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding='utf-8'))
        data['author_name'] = name
        config_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    except Exception:
        pass


def load_saved_output_dir() -> str | None:
    """Load saved output directory from config."""
    try:
        config_path = _get_config_path()
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding='utf-8'))
            return data.get('output_dir')
    except Exception:
        pass
    return None


def save_output_dir(path: str) -> None:
    """Save output directory to config."""
    try:
        config_path = _get_config_path()
        data = {}
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding='utf-8'))
        data['output_dir'] = path
        config_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    except Exception:
        pass


def default_output_dir() -> Path:
    """Get default output directory (Documents folder)."""
    saved = load_saved_output_dir()
    if saved and Path(saved).exists():
        return Path(saved)

    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes
            CSIDL_PERSONAL = 5
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
            docs = Path(buf.value)
            if docs.exists():
                return docs / "MB2DOCX_Output"
        except Exception:
            pass

    home = Path.home()
    candidates = [home / "Documents", home]
    for c in candidates:
        if c.exists():
            return c / "MB2DOCX_Output"
    return home / "MB2DOCX_Output"


@dataclass
class OutputConfig:
    """Output configuration."""
    out_dir: Path
    author_name: str = ""  # Set on first run via GUI
    cv_filename: str = "CV.docx"
    cl_filename: str = "CoverLetter.docx"
    combined_filename: str = "CV_and_CoverLetter.docx"
