"""V6 Parser Tests - Verify smart detection works."""
from mb2docx.model import (
    ContactBlock,
    HeadingBlock,
    InstitutionBlock,
    JobEntryBlock,
    SectionHeadingBlock,
)
from mb2docx.parser import parse_markdown_like


def test_name_detection_all_caps():
    """ALL CAPS name should be detected."""
    text = "JANE DOE"
    blocks = parse_markdown_like(text, is_cover_letter=False)
    assert len(blocks) >= 1
    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[0].level == 1
    assert blocks[0].text == "JANE DOE"


def test_contact_detection():
    """Contact line with email and pipes should be detected."""
    text = """JANE DOE
janedoe@example.com | (555) 123-4567 | Toronto, ON"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    assert len(blocks) >= 2
    assert isinstance(blocks[0], HeadingBlock)
    assert isinstance(blocks[1], ContactBlock)
    assert "|" in blocks[1].text


def test_section_heading_detection():
    """ALL CAPS section heading should be detected."""
    text = """JANE DOE
email@test.com | phone

PROFESSIONAL SUMMARY

Some text here."""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    section_headings = [b for b in blocks if isinstance(b, SectionHeadingBlock)]
    assert len(section_headings) >= 1
    assert "PROFESSIONAL SUMMARY" in section_headings[0].text


def test_job_entry_with_date():
    """Job entry with date range should split title and date."""
    text = """WORK EXPERIENCE

Telemedicine Physician February 2024 - January 2025
CanadianInsulin.com, Remote"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    job_entries = [b for b in blocks if isinstance(b, JobEntryBlock)]
    assert len(job_entries) >= 1
    assert job_entries[0].title == "Telemedicine Physician"
    assert "2024" in job_entries[0].date_range
    assert "2025" in job_entries[0].date_range


def test_institution_after_job():
    """Institution should be detected after job entry."""
    text = """Telemedicine Physician February 2024 - January 2025
CanadianInsulin.com, Remote
- Did some work"""
    blocks = parse_markdown_like(text, is_cover_letter=False)
    institutions = [b for b in blocks if isinstance(b, InstitutionBlock)]
    assert len(institutions) >= 1
    assert "CanadianInsulin" in institutions[0].text


def test_full_cv_structure():
    """Test full CV structure detection."""
    text = """JANE DOE
janedoe@example.com | (555) 123-4567 | Toronto, ON M5V 1A1

PROFESSIONAL SUMMARY

Healthcare professional with clinical training.

EDUCATION

Doctor of Medicine (MD) August 2017 - May 2021
Example University Medical School, City, Country
- Graduated with honors

WORK EXPERIENCE

Telemedicine Physician February 2024 - January 2025
Example Healthcare Company, Remote
- Conducted 50+ patient consultations weekly"""

    blocks = parse_markdown_like(text, is_cover_letter=False)

    # Should have: Name, Contact, Section (PROFESSIONAL), Paragraph,
    # Section (EDUCATION), Job, Institution, List,
    # Section (WORK), Job, Institution, List

    names = [b for b in blocks if isinstance(b, HeadingBlock) and b.level == 1]
    contacts = [b for b in blocks if isinstance(b, ContactBlock)]
    sections = [b for b in blocks if isinstance(b, SectionHeadingBlock)]
    jobs = [b for b in blocks if isinstance(b, JobEntryBlock)]
    institutions = [b for b in blocks if isinstance(b, InstitutionBlock)]

    assert len(names) == 1, f"Expected 1 name, got {len(names)}"
    assert len(contacts) == 1, f"Expected 1 contact, got {len(contacts)}"
    assert len(sections) >= 3, f"Expected 3+ sections, got {len(sections)}"
    assert len(jobs) >= 2, f"Expected 2+ jobs, got {len(jobs)}"
    assert len(institutions) >= 2, f"Expected 2+ institutions, got {len(institutions)}"
