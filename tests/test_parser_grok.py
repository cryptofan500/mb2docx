"""Tests specifically for Grok/Plain text formats."""
from mb2docx.model import ContactBlock, InstitutionBlock, JobEntryBlock, SectionHeadingBlock
from mb2docx.parser import parse_markdown_like


def test_grok_split_lines_job():
    """Test Title on line 1, Date on line 2."""
    text = """
Senior Delivery Manager, Amazon Web Services (AWS), Toronto, ON
June 2018 – Present
"""
    blocks = parse_markdown_like(text)
    jobs = [b for b in blocks if isinstance(b, JobEntryBlock)]
    insts = [b for b in blocks if isinstance(b, InstitutionBlock)]

    assert len(jobs) == 1
    assert jobs[0].title == "Senior Delivery Manager"
    assert "June 2018" in jobs[0].date_range

    assert len(insts) == 1
    assert "Amazon Web Services" in insts[0].text
    assert "Toronto" in insts[0].text

def test_grok_title_case_heading():
    """Test 'Professional Experience' without markdown hash."""
    text = """
Bob Frok
email@test.com

Professional Experience

Senior Manager
2020 - 2021
"""
    blocks = parse_markdown_like(text)
    sections = [b for b in blocks if isinstance(b, SectionHeadingBlock)]

    assert len(sections) == 1
    assert sections[0].text == "PROFESSIONAL EXPERIENCE"

def test_grok_contact_multiline():
    """Test contact info spread across lines (realistic Grok format)."""
    text = """
Bob Frok
email@test.com
(555) 123-4567
123 Main St, City, State
"""
    blocks = parse_markdown_like(text)
    contact_blocks = [b for b in blocks if isinstance(b, ContactBlock)]
    assert len(contact_blocks) == 1
    assert "|" in contact_blocks[0].text
    assert "email@test.com" in contact_blocks[0].text
    assert "123 Main St" in contact_blocks[0].text
