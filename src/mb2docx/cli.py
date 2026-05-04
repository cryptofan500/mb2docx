"""Command-line interface for mb2docx."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import __version__
from .config import CL_STYLE, CV_STYLE, OutputConfig, default_output_dir, load_saved_author
from .logging_utils import configure_logging
from .pipeline import generate_documents


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mb2docx",
        description="Convert AI markdown-box CV/CL paste into ATS-friendly DOCX.",
    )

    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    cv_group = p.add_mutually_exclusive_group(required=True)
    cv_group.add_argument("--cv-file", type=Path, help="Path to CV text/markdown file.")
    cv_group.add_argument("--cv-text", type=str, help="CV text provided inline.")

    cl_group = p.add_mutually_exclusive_group(required=False)
    cl_group.add_argument("--cl-file", type=Path, help="Path to cover letter text/markdown file.")
    cl_group.add_argument("--cl-text", type=str, help="Cover letter text provided inline.")

    p.add_argument("--out-dir", type=Path, default=default_output_dir(), help="Output directory.")
    p.add_argument("--author", type=str, default=None, help="DOCX author metadata (persists between sessions).")

    p.add_argument("--combine", action="store_true", help="Also generate a combined DOCX if CL is provided.")
    p.add_argument("--only-combined", action="store_true", help="If --combine, skip separate files.")

    p.add_argument("--verbose", action="store_true", help="Verbose logging.")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.out_dir / "logs", verbose=args.verbose)
    log = logging.getLogger(__name__)

    cv_text = _read_text_file(args.cv_file) if args.cv_file else args.cv_text
    cl_text = None
    if getattr(args, "cl_file", None):
        cl_text = _read_text_file(args.cl_file)
    elif getattr(args, "cl_text", None):
        cl_text = args.cl_text

    # Get author - use provided, or load saved, or default
    author = args.author
    if not author:
        author = load_saved_author() or "Author"

    # Build output config with author-based filenames
    author_filename = author.replace(" ", "_")
    output = OutputConfig(
        out_dir=args.out_dir,
        author_name=author,
        cv_filename=f"CV_{author_filename}.docx",
        cl_filename=f"CoverLetter_{author_filename}.docx",
        combined_filename=f"CV_and_CoverLetter_{author_filename}.docx",
    )

    paths = generate_documents(
        cv_text=cv_text,
        cl_text=cl_text,
        output=output,
        cv_style=CV_STYLE,
        cl_style=CL_STYLE,
        also_generate_combined=args.combine,
        only_combined=args.only_combined,
    )

    for pth in paths:
        log.info("OUTPUT: %s", pth)
        print(f"Generated: {pth}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
