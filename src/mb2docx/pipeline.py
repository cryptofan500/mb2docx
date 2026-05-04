"""Document generation pipeline - V6."""
from __future__ import annotations

import logging
from pathlib import Path

from .clean import clean_ai_paste
from .config import CL_STYLE, CV_STYLE, DocxStyleConfig, OutputConfig
from .docx_writer import add_page_break, build_docx, new_document, render_blocks, safe_save_docx
from .parser import parse_markdown_like

log = logging.getLogger(__name__)


def generate_documents(
    *,
    cv_text: str,
    cl_text: str | None,
    output: OutputConfig,
    cv_style: DocxStyleConfig | None = None,
    cl_style: DocxStyleConfig | None = None,
    style: DocxStyleConfig | None = None,  # Legacy support
    also_generate_combined: bool = False,
    only_combined: bool = False,
) -> list[Path]:
    """Generate DOCX files from CV and optional CL text.

    Args:
        cv_text: Raw CV text (markdown or plain)
        cl_text: Optional raw cover letter text
        output: Output configuration
        cv_style: Style for CV (default: CV_STYLE)
        cl_style: Style for CL (default: CL_STYLE)
        style: Legacy single style (overrides both if provided)
        also_generate_combined: Generate combined CV+CL file
        only_combined: Skip separate files, only generate combined

    Returns:
        List of generated file paths
    """
    outputs: list[Path] = []

    # Resolve styles
    if style:
        cv_style = style
        cl_style = style
    else:
        cv_style = cv_style or CV_STYLE
        cl_style = cl_style or CL_STYLE

    # Clean and parse CV
    cv_clean = clean_ai_paste(cv_text)
    if not cv_clean:
        raise ValueError("CV text is empty after cleaning.")

    cv_blocks = parse_markdown_like(cv_clean, is_cover_letter=False)
    log.info(f"Parsed CV: {len(cv_blocks)} blocks")

    # Debug: Log block types
    for i, blk in enumerate(cv_blocks[:10]):
        log.debug(f"CV Block {i}: {type(blk).__name__} - {str(blk)[:50]}")

    # Clean and parse CL if provided
    cl_blocks = None
    if cl_text and cl_text.strip():
        cl_clean = clean_ai_paste(cl_text)
        if cl_clean:
            cl_blocks = parse_markdown_like(cl_clean, is_cover_letter=True)
            log.info(f"Parsed CL: {len(cl_blocks)} blocks")

    # Determine what to generate
    has_cl = cl_blocks is not None
    generate_combined = also_generate_combined and has_cl
    generate_separate = not (only_combined and generate_combined)

    # Generate separate files
    if generate_separate:
        # CV
        cv_doc = build_docx(
            cv_blocks,
            cfg=cv_style,
            title="Curriculum Vitae",
            author=output.author_name,
        )
        cv_out = output.out_dir / output.cv_filename
        outputs.append(safe_save_docx(cv_doc, cv_out).path)
        log.info(f"Generated CV: {cv_out}")

        # CL
        if cl_blocks:
            cl_doc = build_docx(
                cl_blocks,
                cfg=cl_style,
                title="Cover Letter",
                author=output.author_name,
            )
            cl_out = output.out_dir / output.cl_filename
            outputs.append(safe_save_docx(cl_doc, cl_out).path)
            log.info(f"Generated CL: {cl_out}")

    # Generate combined file
    if generate_combined and cl_blocks:
        combined = new_document(
            cfg=cl_style,
            title="CV and Cover Letter",
            author=output.author_name,
        )

        # Cover letter first
        render_blocks(combined, cl_blocks, cl_style)
        add_page_break(combined)

        # Then CV (need to adjust margins mid-document is not possible,
        # so we use CL style throughout combined doc)
        render_blocks(combined, cv_blocks, cl_style)

        combined_out = output.out_dir / output.combined_filename
        outputs.append(safe_save_docx(combined, combined_out).path)
        log.info(f"Generated combined: {combined_out}")

    return outputs
