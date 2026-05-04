"""Data structures for parsed document blocks - V6."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HeadingBlock:
    """Document name/title (level 1) - rendered as bold centered."""
    type: Literal["heading"]
    level: int
    text: str


@dataclass(frozen=True)
class ContactBlock:
    """Contact information line - rendered centered, smaller font."""
    type: Literal["contact_header"]
    text: str


@dataclass(frozen=True)
class SectionHeadingBlock:
    """Section heading like EDUCATION, EXPERIENCE - rendered bold ALL CAPS."""
    type: Literal["section_heading"]
    text: str


@dataclass(frozen=True)
class JobEntryBlock:
    """Job title with date - rendered as: BOLD title + TAB + BOLD date."""
    type: Literal["job_entry"]
    title: str
    date_range: str


@dataclass(frozen=True)
class InstitutionBlock:
    """Institution/company name - rendered ITALIC."""
    type: Literal["institution"]
    text: str


@dataclass(frozen=True)
class ParagraphBlock:
    """Regular paragraph text."""
    type: Literal["paragraph"]
    text: str


@dataclass(frozen=True)
class ListBlock:
    """List of items (bullets)."""
    type: Literal["list"]
    ordered: bool
    items: Sequence[str]


# Cover Letter specific blocks
@dataclass(frozen=True)
class DateLineBlock:
    """Standalone date line for cover letter."""
    type: Literal["date_line"]
    text: str


@dataclass(frozen=True)
class AddressBlock:
    """Multi-line address block for cover letter."""
    type: Literal["address_block"]
    lines: Sequence[str]


@dataclass(frozen=True)
class SalutationBlock:
    """Salutation like 'Dear Hiring Manager,'."""
    type: Literal["salutation"]
    text: str


@dataclass(frozen=True)
class ClosingBlock:
    """Closing with signature name, phone, and email."""
    type: Literal["closing"]
    closing: str  # e.g., "Sincerely,"
    signature: str  # e.g., "John Doe"
    phone: str = ""  # e.g., "(647) 123 1234"
    email: str = ""  # e.g., "bob@email.com"


Block = (
    HeadingBlock | ContactBlock | SectionHeadingBlock | JobEntryBlock |
    InstitutionBlock | ParagraphBlock | ListBlock |
    DateLineBlock | AddressBlock | SalutationBlock | ClosingBlock
)
