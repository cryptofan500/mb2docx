"""Smart CV/CL Parser - V7 Grok Compatible.

Major upgrades:
1. Detects Title Case section headings (e.g., "Professional Experience" without #)
2. Detects split Job Entries (Title on Line 1, Date on Line 2)
3. Detects comma-separated Title/Institution (Manager, Company, Location)
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .model import (
    AddressBlock, Block, ClosingBlock, ContactBlock, DateLineBlock,
    HeadingBlock, InstitutionBlock, JobEntryBlock, ListBlock,
    ParagraphBlock, SalutationBlock, SectionHeadingBlock
)

# ============================================================================
# REGEX PATTERNS
# ============================================================================

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UL_ITEM_RE = re.compile(r"^\s*[-*•]\s+(.+?)\s*$")
_OL_ITEM_RE = re.compile(r"^\s*(\d+)[\.)]\s+(.+?)\s*$")
_PHONE_RE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

_MONTH_NAMES = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

# Matches "June 2018 - Present" or "Jan 2020 - Feb 2021"
_DATE_RANGE_RE = re.compile(
    rf"({_MONTH_NAMES}\s+\d{{4}})\s*[-–—]\s*({_MONTH_NAMES}\s+\d{{4}}|Present|Current)",
    re.IGNORECASE
)

# Matches just "Graduated 2004" or "May 2020" at end of string
_SINGLE_DATE_RE = re.compile(
    rf"({_MONTH_NAMES}\s+\d{{4}}|Graduated\s+\d{{4}})$",
    re.IGNORECASE
)

_DATE_ONLY_RE = re.compile(
    rf"^{_MONTH_NAMES}\s+\d{{1,2}},?\s+\d{{4}}$",
    re.IGNORECASE
)

_SALUTATION_RE = re.compile(r"^Dear\s+.+[,:]?\s*$", re.IGNORECASE)
_CLOSING_RE = re.compile(
    r"^(Sincerely|Best\s+regards?|Kind\s+regards?|Regards|Respectfully|"
    r"Thank\s+you|Yours\s+truly|Warm\s+regards?)[,]?\s*$",
    re.IGNORECASE
)

_ALL_CAPS_RE = re.compile(r"^[A-Z][A-Z\s&]+$")

# Keywords that suggest a line is a section heading if Title Cased
SECTION_KEYWORDS = {
    'summary', 'experience', 'work', 'employment', 'history',
    'education', 'skills', 'certifications', 'credentials',
    'projects', 'languages', 'interests', 'volunteer',
    'profile', 'qualifications', 'expertise', 'technical',
    'additional', 'information', 'affiliations'
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _looks_like_name(line: str) -> bool:
    words = line.split()
    if len(words) < 1 or len(words) > 5:
        return False
    # ALL CAPS name
    if line.isupper() and len(line) < 50:
        return True
    # Title Case name
    if all(w[0].isupper() for w in words if w):
        return True
    return False

def _looks_like_contact(line: str) -> bool:
    if "@" in line or "|" in line:
        return True
    if _PHONE_RE.search(line) and len(line) < 100:
        return True
    # LinkedIn URL
    if "linkedin.com" in line.lower():
        return True
    return False


def _looks_like_address_or_contact(line: str) -> bool:
    """Check if line is address or contact info (for header block)."""
    # Standard contact checks
    if _looks_like_contact(line):
        return True
    # Short lines that could be address/city/state
    if len(line) < 60:
        # Contains common address patterns
        if re.search(r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Blvd|Lane|Ln)', line, re.IGNORECASE):
            return True
        # City, State ZIP pattern
        if re.search(r'[A-Z][a-z]+,?\s+[A-Z]{2}\s+\d{5}', line):
            return True
        # Just city, state
        if re.search(r'^[A-Z][a-z]+,\s+[A-Z]{2}', line):
            return True
    return False

def _looks_like_section_heading(line: str) -> bool:
    """Detect section headings (ALL CAPS or known Title Case keywords)."""
    stripped = line.strip()
    words = stripped.split()

    if len(words) < 1 or len(words) > 6:
        return False
    if len(stripped) < 4:
        return False

    # Case 1: ALL CAPS (e.g. PROFESSIONAL SUMMARY)
    if _ALL_CAPS_RE.match(stripped):
        return True

    # Case 2: Title Case with Keyword (e.g. Professional Experience)
    lower_words = set(w.lower() for w in words)
    # Check if any word is a keyword
    if not lower_words.intersection(SECTION_KEYWORDS):
        return False
    # Check if it looks like a header (Title Case)
    if all(w[0].isupper() for w in words if w[0].isalpha()):
        return True

    return False

def _extract_date_range(line: str) -> Optional[str]:
    """Return just the date range string if found, else None."""
    match = _DATE_RANGE_RE.search(line)
    if match:
        return match.group(0).strip()
    match_single = _SINGLE_DATE_RE.search(line)
    if match_single:
        return match_single.group(0).strip()
    return None

def _split_line_title_date(line: str) -> Tuple[str, Optional[str]]:
    """Split 'Title Date' into parts."""
    # Check if date is at the end
    match = _DATE_RANGE_RE.search(line) or _SINGLE_DATE_RE.search(line)
    if match:
        date_str = match.group(0)
        title_part = line[:match.start()].strip()
        # Clean trailing separators
        title_part = re.sub(r'[\t\s,–—-]+$', '', title_part)
        return (title_part, date_str)
    return (line, None)

def _parse_job_title_line(line: str) -> Tuple[str, Optional[str]]:
    """Handle 'Title, Company, Location' format.

    Returns (Job Title, Institution string).
    Pattern: "Title, Company, City, State" -> Title + "Company | City, State"
    """
    if "," not in line:
        return (line, None)

    parts = line.split(",")
    if len(parts) < 2:
        return (line, None)

    title = parts[0].strip()

    if len(parts) == 2:
        # "Title, Company" -> just company
        institution = parts[1].strip()
    elif len(parts) == 3:
        # "Title, Company, Location" -> "Company | Location"
        institution = f"{parts[1].strip()} | {parts[2].strip()}"
    else:
        # "Title, Company, City, State" -> "Company | City, State"
        company = parts[1].strip()
        location = ", ".join(p.strip() for p in parts[2:])
        institution = f"{company} | {location}"

    return (title, institution)

# ============================================================================
# MAIN PARSER
# ============================================================================

def parse_markdown_like(text: str, is_cover_letter: bool = False) -> List[Block]:
    if is_cover_letter:
        return _parse_cover_letter(text)
    return _parse_cv(text)

def _parse_cv(text: str) -> List[Block]:
    blocks: List[Block] = []
    lines = text.split("\n")
    para_buf: List[str] = []

    seen_name = False
    seen_contact = False
    prev_was_job_entry = False  # Track if we just added a job entry

    def flush_para():
        nonlocal para_buf
        if para_buf:
            txt = " ".join(s.strip() for s in para_buf if s.strip())
            if txt:
                blocks.append(ParagraphBlock(type="paragraph", text=txt))
            para_buf = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            flush_para()
            prev_was_job_entry = False
            i += 1
            continue

        # ---------------------------------------------------------
        # 1. MARKDOWN HEADERS (#)
        # ---------------------------------------------------------
        m = _HEADING_RE.match(line)
        if m:
            flush_para()
            level = len(m.group(1))
            txt = m.group(2).strip()
            if level == 1 and not seen_name:
                blocks.append(HeadingBlock(type="heading", level=1, text=txt))
                seen_name = True
            else:
                # Check if this header contains a date range (job entry vs section heading)
                date_in_header = _extract_date_range(txt)
                if date_in_header:
                    # This is a job entry in markdown format: ### Title	Date
                    title_part, date_part = _split_line_title_date(txt)
                    job_title, inst = _parse_job_title_line(title_part)
                    blocks.append(JobEntryBlock(type="job_entry", title=job_title, date_range=date_part))
                    if inst:
                        blocks.append(InstitutionBlock(type="institution", text=inst))
                        prev_was_job_entry = False
                    else:
                        prev_was_job_entry = True
                else:
                    # No date = section heading, uppercase it
                    blocks.append(SectionHeadingBlock(type="section_heading", text=txt.upper()))
            i += 1
            continue

        # ---------------------------------------------------------
        # 1b. INSTITUTION after job entry (no date, not a bullet, not a heading)
        # ---------------------------------------------------------
        if prev_was_job_entry:
            # Check if this line is an institution (after job entry)
            if not _looks_like_section_heading(line) and not line.startswith(('-', '*', '•')) and not _extract_date_range(line):
                flush_para()
                blocks.append(InstitutionBlock(type="institution", text=line))
                prev_was_job_entry = False
                i += 1
                continue
            prev_was_job_entry = False

        # ---------------------------------------------------------
        # 2. NAME (First non-empty line)
        # ---------------------------------------------------------
        if not seen_name and _looks_like_name(line):
            flush_para()
            blocks.append(HeadingBlock(type="heading", level=1, text=line))
            seen_name = True
            i += 1
            continue

        # ---------------------------------------------------------
        # 3. CONTACT INFO (Multi-line address + contact merged into one)
        # ---------------------------------------------------------
        if seen_name and not seen_contact:
            # If current line is address or contact-like, gather all header lines
            if _looks_like_address_or_contact(line):
                flush_para()

                # V9.2 FIX: If line already has pipe separators, preserve exactly as-is
                if '|' in line:
                    blocks.append(ContactBlock(type="contact_header", text=line))
                    seen_contact = True
                    i += 1
                    continue

                # Otherwise gather multi-line header info until section heading
                contact_lines = [line]
                i += 1
                while i < len(lines):
                    next_ln = lines[i].strip()
                    if not next_ln:
                        i += 1
                        continue
                    if _looks_like_section_heading(next_ln):
                        break
                    if _HEADING_RE.match(next_ln):
                        break
                    # Gather address/contact lines (short lines, or contact-like)
                    if _looks_like_address_or_contact(next_ln) or (len(next_ln) < 50 and not next_ln.startswith(('-', '*', '•'))):
                        contact_lines.append(next_ln)
                        i += 1
                    else:
                        break

                # Merge multi-line contacts with smart separators
                # Address parts use ", " while contact items use " | "
                address_parts = []
                contact_parts = []

                for cl in contact_lines:
                    # Determine if this is address or contact info
                    is_contact = (
                        '@' in cl or
                        _PHONE_RE.search(cl) or
                        'linkedin' in cl.lower() or
                        '|' in cl  # Already pipe-separated
                    )
                    if is_contact:
                        contact_parts.append(cl)
                    else:
                        address_parts.append(cl)

                # Build final contact line
                parts_to_join = []
                if address_parts:
                    # Join address parts with comma
                    parts_to_join.append(", ".join(address_parts))
                # Add contact parts with pipes
                parts_to_join.extend(contact_parts)

                full_contact = " | ".join(parts_to_join)
                blocks.append(ContactBlock(type="contact_header", text=full_contact))
                seen_contact = True
                continue

        # ---------------------------------------------------------
        # 4. SECTION HEADING (Title Case or ALL CAPS)
        # ---------------------------------------------------------
        if _looks_like_section_heading(line):
            flush_para()
            blocks.append(SectionHeadingBlock(type="section_heading", text=line.upper()))
            i += 1
            continue

        # ---------------------------------------------------------
        # 5. JOB ENTRY DETECTION (Complex)
        # ---------------------------------------------------------
        # Case A: Title and Date on SAME line
        # "Manager 2020-2021"
        date_in_line = _extract_date_range(line)

        if date_in_line:
            flush_para()
            title_part, date_part = _split_line_title_date(line)
            job_title, inst = _parse_job_title_line(title_part)

            blocks.append(JobEntryBlock(type="job_entry", title=job_title, date_range=date_part))
            if inst:
                blocks.append(InstitutionBlock(type="institution", text=inst))
                prev_was_job_entry = False
            else:
                prev_was_job_entry = True  # Look for institution on next line
            i += 1
            continue

        # Case B: Title on Line 1, Date on Line 2 (Grok Style)
        # "Senior Manager"
        # "June 2018 - Present"
        if i + 1 < len(lines):
            next_line = lines[i+1].strip()
            date_in_next = _extract_date_range(next_line)

            # If next line is ONLY a date (or close to it)
            if date_in_next and len(next_line) < 50:
                flush_para()
                # Current line is title (+ optionally institution)
                job_title, inst = _parse_job_title_line(line)

                blocks.append(JobEntryBlock(type="job_entry", title=job_title, date_range=date_in_next))
                if inst:
                    blocks.append(InstitutionBlock(type="institution", text=inst))
                    prev_was_job_entry = False
                else:
                    prev_was_job_entry = True  # Look for institution on next line

                i += 2  # Skip both lines
                continue

        # ---------------------------------------------------------
        # 6. LISTS
        # ---------------------------------------------------------
        if _UL_ITEM_RE.match(line) or _OL_ITEM_RE.match(line):
            flush_para()
            items = []
            is_ordered = bool(_OL_ITEM_RE.match(line))

            # Consume list
            while i < len(lines):
                curr = lines[i].strip()
                if not curr:
                    break

                m_ul = _UL_ITEM_RE.match(curr)
                m_ol = _OL_ITEM_RE.match(curr)

                if m_ul:
                    items.append(m_ul.group(1))
                elif m_ol:
                    items.append(m_ol.group(2))
                else:
                    break
                i += 1

            blocks.append(ListBlock(type="list", ordered=is_ordered, items=items))
            continue

        # ---------------------------------------------------------
        # 7. PARAGRAPH
        # ---------------------------------------------------------
        para_buf.append(line)
        i += 1

    flush_para()
    return blocks

def _parse_cover_letter(text: str) -> List[Block]:
    """Parser for Cover Letter with proper header handling.

    V9.1 Fix: Now correctly detects name and contact at the top
    of cover letters, matching the CV parser behavior.

    V9.1.1 Fix: Pre-scans for phone/email at bottom to include in header.
    """
    blocks = []
    lines = text.split("\n")

    # === PRE-SCAN: Find phone/email at the bottom (after closing) ===
    # These will be added to the header contact line
    footer_phone = ""
    footer_email = ""
    for j in range(len(lines) - 1, -1, -1):
        ln = lines[j].strip()
        if not ln:
            continue
        if '@' in ln and not footer_email:
            footer_email = ln
        elif _PHONE_RE.search(ln) and not footer_phone:
            footer_phone = ln
        elif _CLOSING_RE.match(ln):
            break  # Stop when we hit the closing
        elif _looks_like_name(ln):
            continue  # Skip signature name
        elif len(ln) > 50:
            break  # Hit body text, stop

    i = 0
    para_buf = []

    seen_name = False
    seen_contact = False
    seen_date = False
    in_address = False
    address_buf = []
    # V9.3.0: track whether footer phone/email were promoted into the header
    # so we can blank them on the eventual ClosingBlock and avoid duplication.
    promoted_phone = False
    promoted_email = False

    def flush():
        nonlocal para_buf
        if para_buf:
            t = " ".join(para_buf)
            blocks.append(ParagraphBlock(type="paragraph", text=t))
            para_buf = []

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            flush()
            if address_buf:
                blocks.append(AddressBlock(type="address_block", lines=tuple(address_buf)))
                address_buf = []
                in_address = False
            i += 1
            continue

        # ===== V9.1 FIX: NAME DETECTION =====
        # First non-empty line before date should be the name
        if not seen_name and not seen_date:
            # V9.3.0 FIX: Strip leading markdown heading marker (e.g., "# Jane Doe")
            # so both "# JANE DOE" and "# Jane Doe" are recognised as the name.
            heading_match = _HEADING_RE.match(line)
            if heading_match and len(heading_match.group(1)) == 1:
                candidate = heading_match.group(2).strip()
            else:
                candidate = line
            if _looks_like_name(candidate):
                flush()
                blocks.append(HeadingBlock(type="heading", level=1, text=candidate))
                seen_name = True
                i += 1
                continue

        # ===== V9.1 FIX: CONTACT DETECTION =====
        # After name, before date, gather contact/address lines
        if seen_name and not seen_contact and not seen_date:
            if _looks_like_contact(line) or _looks_like_address_or_contact(line):
                flush()
                # Gather all contact/address lines until date or salutation
                contact_lines = [line]
                i += 1
                while i < len(lines):
                    next_ln = lines[i].strip()
                    if not next_ln:
                        i += 1
                        continue
                    # Stop if we hit the date
                    if _DATE_ONLY_RE.match(next_ln):
                        break
                    # Stop if we hit salutation
                    if _SALUTATION_RE.match(next_ln):
                        break
                    # Gather contact-like or short address-like lines
                    if _looks_like_contact(next_ln) or _looks_like_address_or_contact(next_ln):
                        contact_lines.append(next_ln)
                        i += 1
                    elif len(next_ln) < 50 and not next_ln.startswith(('-', '*', '•')):
                        # Short lines might be part of address
                        contact_lines.append(next_ln)
                        i += 1
                    else:
                        break

                # Merge with smart separators (like CV parser does)
                address_parts = []
                contact_parts = []

                for cl in contact_lines:
                    is_contact = (
                        '@' in cl or
                        _PHONE_RE.search(cl) or
                        'linkedin' in cl.lower() or
                        '|' in cl
                    )
                    if is_contact:
                        contact_parts.append(cl)
                    else:
                        address_parts.append(cl)

                parts_to_join = []
                if address_parts:
                    parts_to_join.append(", ".join(address_parts))
                parts_to_join.extend(contact_parts)

                # Add footer phone/email to header (found during pre-scan)
                if footer_phone and footer_phone not in " ".join(parts_to_join):
                    parts_to_join.append(footer_phone)
                    promoted_phone = True
                if footer_email and footer_email not in " ".join(parts_to_join):
                    parts_to_join.append(footer_email)
                    promoted_email = True

                full_contact = " | ".join(parts_to_join)
                blocks.append(ContactBlock(type="contact_header", text=full_contact))
                seen_contact = True
                continue
        # ===== END V9.1 FIX =====

        # Date
        if not seen_date and _DATE_ONLY_RE.match(line):
            flush()
            blocks.append(DateLineBlock(type="date_line", text=line))
            seen_date = True
            in_address = True
            i += 1
            continue

        # Salutation
        if _SALUTATION_RE.match(line):
            flush()
            if address_buf:
                blocks.append(AddressBlock(type="address_block", lines=tuple(address_buf)))
                address_buf = []
            blocks.append(SalutationBlock(type="salutation", text=line))
            in_address = False
            i += 1
            continue

        # Address block collection (recipient address after date)
        if in_address:
            address_buf.append(line)
            i += 1
            continue

        # Closing
        if _CLOSING_RE.match(line):
            flush()
            # Look for signature, phone, email (skip empty lines between each)
            sig = ""
            phone = ""
            email = ""
            j = i + 1

            # Skip empty lines and get signature (name)
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                potential_sig = lines[j].strip()
                if potential_sig and len(potential_sig.split()) <= 5 and '@' not in potential_sig:
                    sig = potential_sig
                    j += 1

            # Look for phone and email on subsequent lines
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                # Check for phone number
                if _PHONE_RE.search(next_line) and not phone:
                    phone = next_line
                    j += 1
                    continue
                # Check for email
                if '@' in next_line and not email:
                    email = next_line
                    j += 1
                    continue
                # If neither phone nor email, stop
                break

            i = j - 1  # Position before the increment
            # V9.3.0: if these values were already promoted to the header
            # contact line, blank them here so they aren't rendered twice.
            if promoted_phone:
                phone = ""
            if promoted_email:
                email = ""
            blocks.append(ClosingBlock(type="closing", closing=line, signature=sig, phone=phone, email=email))
            i += 1
            continue

        # Body paragraphs
        para_buf.append(line)
        i += 1

    flush()
    return blocks
