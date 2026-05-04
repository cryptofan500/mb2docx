"""Tests for parser.py."""
from mb2docx.model import (
    AddressBlock,
    ClosingBlock,
    ContactBlock,
    DateLineBlock,
    HeadingBlock,
    InstitutionBlock,
    JobEntryBlock,
    ListBlock,
    SalutationBlock,
    SectionHeadingBlock,
)
from mb2docx.parser import parse_markdown_like


def test_parser_name_heading():
    """Test name heading parsing."""
    text = "# JANE DOE"
    blocks = parse_markdown_like(text)
    assert len(blocks) == 1
    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[0].level == 1
    assert blocks[0].text == "JANE DOE"


def test_parser_contact_line():
    """Test contact line detection."""
    text = """# JANE DOE

email@example.com | (555) 123-4567 | City, State"""
    blocks = parse_markdown_like(text)
    assert len(blocks) == 2
    assert isinstance(blocks[0], HeadingBlock)
    assert isinstance(blocks[1], ContactBlock)
    assert "@" in blocks[1].text


def test_parser_section_heading():
    """Test ALL CAPS section heading."""
    text = """# Name

contact@email.com | phone

## PROFESSIONAL SUMMARY

Some text here."""
    blocks = parse_markdown_like(text)
    # Find section heading
    section_headings = [b for b in blocks if isinstance(b, SectionHeadingBlock)]
    assert len(section_headings) == 1
    assert section_headings[0].text == "PROFESSIONAL SUMMARY"


def test_parser_unordered_list():
    """Test unordered list parsing."""
    text = """- Item 1
- Item 2
- Item 3"""
    blocks = parse_markdown_like(text)
    assert len(blocks) == 1
    assert isinstance(blocks[0], ListBlock)
    assert blocks[0].ordered is False
    assert blocks[0].items == ["Item 1", "Item 2", "Item 3"]


def test_parser_mixed_content():
    """Test mixed content parsing."""
    text = """# Name

email@test.com | phone

## EDUCATION

Some paragraph text here.

- Bullet 1
- Bullet 2"""
    blocks = parse_markdown_like(text)
    assert len(blocks) >= 4
    # Check we have various block types
    types = [type(b).__name__ for b in blocks]
    assert "HeadingBlock" in types
    assert "ContactBlock" in types
    assert "SectionHeadingBlock" in types
    assert "ListBlock" in types


# V5: New tests for smart date/job entry detection

def test_parser_job_entry_with_date_range():
    """Test job entry detection with date range (no markdown markers)."""
    text = """JANE DOE
email@test.com | phone

WORK EXPERIENCE

Senior Developer                                    June 2020 - Present
Tech Company
"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    job_entries = [b for b in blocks if isinstance(b, JobEntryBlock)]
    assert len(job_entries) == 1
    assert job_entries[0].title == "Senior Developer"
    assert "June 2020" in job_entries[0].date_range
    assert "Present" in job_entries[0].date_range


def test_parser_institution_after_job():
    """Test institution detection after job entry."""
    text = """Name
email@test.com

WORK EXPERIENCE

Manager June 2018 - December 2020
Big Company, Location
- Did stuff
"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    institutions = [b for b in blocks if isinstance(b, InstitutionBlock)]
    assert len(institutions) == 1
    assert "Big Company" in institutions[0].text


def test_parser_cover_letter_date_line():
    """Test cover letter date line detection."""
    text = """JANE DOE
email@test.com | phone

January 22, 2026

Dear Hiring Manager,

Body text.
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    date_lines = [b for b in blocks if isinstance(b, DateLineBlock)]
    assert len(date_lines) == 1
    assert "January 22, 2026" in date_lines[0].text


def test_parser_cover_letter_address_block():
    """Test cover letter address block detection."""
    text = """Name
email@test.com

January 1, 2026

Hiring Manager
Company Name
123 Main Street
City, State 12345

Dear Hiring Manager,

Body.
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    addresses = [b for b in blocks if isinstance(b, AddressBlock)]
    assert len(addresses) == 1
    assert len(addresses[0].lines) == 4
    assert "Hiring Manager" in addresses[0].lines[0]


def test_parser_cover_letter_salutation():
    """Test salutation detection."""
    text = """Name
email@test.com

Dear Dr. Smith,

Body text.
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    salutations = [b for b in blocks if isinstance(b, SalutationBlock)]
    assert len(salutations) == 1
    assert "Dear" in salutations[0].text


def test_parser_cover_letter_closing():
    """Test closing and signature detection."""
    text = """Name
email@test.com

Dear Hiring Manager,

Body text here.

Sincerely,

John Doe
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    closings = [b for b in blocks if isinstance(b, ClosingBlock)]
    assert len(closings) == 1
    assert "Sincerely" in closings[0].closing
    assert "John Doe" in closings[0].signature


def test_parser_name_without_markdown():
    """Test name detection without # marker."""
    text = """JOHN DOE
email@test.com"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    assert len(blocks) == 2
    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[0].text == "JOHN DOE"


def test_parser_all_caps_section_without_markdown():
    """Test section heading detection without ## marker."""
    text = """John Doe
email@test.com

PROFESSIONAL EXPERIENCE

Some text.
"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    sections = [b for b in blocks if isinstance(b, SectionHeadingBlock)]
    assert len(sections) == 1
    assert "PROFESSIONAL EXPERIENCE" in sections[0].text


# V9.3.0 audit fixes — cover-letter heading bugs (C1 + C2)

def test_cover_letter_markdown_heading_all_caps():
    """`# JANE DOE` at top of cover letter must produce HeadingBlock with no leading '#'."""
    text = """# JANE DOE
email@test.com | (555) 123-4567

January 1, 2026

Dear Hiring Manager,

Body.
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    headings = [b for b in blocks if isinstance(b, HeadingBlock)]
    assert len(headings) == 1
    assert headings[0].level == 1
    assert headings[0].text == "JANE DOE"


def test_cover_letter_markdown_heading_title_case():
    """`# Jane Doe` (Title Case) must also be detected as the name."""
    text = """# Jane Doe
email@test.com | (555) 123-4567

January 1, 2026

Dear Hiring Manager,

Body.
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    headings = [b for b in blocks if isinstance(b, HeadingBlock)]
    assert len(headings) == 1
    assert headings[0].level == 1
    assert headings[0].text == "Jane Doe"


def test_cover_letter_plain_name_still_works():
    """Plain `JANE DOE` (no '#') must continue to work as before."""
    text = """JANE DOE
email@test.com | (555) 123-4567

January 1, 2026

Dear Hiring Manager,

Body.
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    headings = [b for b in blocks if isinstance(b, HeadingBlock)]
    assert len(headings) == 1
    assert headings[0].level == 1
    assert headings[0].text == "JANE DOE"


# V9.3.0 audit fixes — phone/email duplication (H1)

def _collect_strings(blocks):
    """Flatten every string field across a Block list."""
    out = []
    for b in blocks:
        for v in b.__dict__.values():
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, (tuple, list)):
                out.extend(item for item in v if isinstance(item, str))
    return "\n".join(out)


def test_cover_letter_phone_email_only_at_bottom_no_duplication():
    """Phone/email after signature must not appear in BOTH header and ClosingBlock."""
    text = """JANE DOE
Toronto, ON M5V 1A1

January 22, 2026

Dear Hiring Manager,

Body text for the cover letter goes here in this paragraph form.

Sincerely,

Jane Doe
(555) 123-4567
jane@example.com
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    combined = _collect_strings(blocks)
    assert combined.count("(555) 123-4567") == 1
    assert combined.count("jane@example.com") == 1

    # Closing block fields must be blank (the values live in the contact header).
    closings = [b for b in blocks if isinstance(b, ClosingBlock)]
    assert len(closings) == 1
    assert closings[0].phone == ""
    assert closings[0].email == ""


def test_cover_letter_phone_email_at_top_unchanged():
    """Phone/email under the name must not produce spurious ClosingBlock fields."""
    text = """JANE DOE
jane@example.com | (555) 123-4567

January 22, 2026

Dear Hiring Manager,

Body text.

Sincerely,

Jane Doe
"""
    blocks = parse_markdown_like(text, is_cover_letter=True)
    closings = [b for b in blocks if isinstance(b, ClosingBlock)]
    assert len(closings) == 1
    assert closings[0].phone == ""
    assert closings[0].email == ""
