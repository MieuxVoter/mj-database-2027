"""
Date Extraction Module

Functions for extracting publication and survey dates from IPSOS pages.
"""

import re
from datetime import datetime
from typing import Optional, Dict
from bs4 import BeautifulSoup

from .config import MONTH_MAP


def _get_filtered_soup_for_main_article(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Create a filtered BeautifulSoup object with related articles sections removed.

    The IPSOS page contains "Sur le même sujet" and "Articles liés" sections that
    link to other polls with their own dates. We need to exclude these to avoid
    extracting dates from the wrong poll.
    """
    soup_copy = BeautifulSoup(str(soup), "html.parser")

    # Remove common related articles sections by their headings
    related_headings = ["Sur le même sujet", "Articles liés", "Articles similaires", "Voir aussi", "Lire aussi"]

    for heading_text in related_headings:
        for element in soup_copy.find_all(string=re.compile(heading_text, re.IGNORECASE)):
            # Navigate up to find the containing section
            parent = element.find_parent()
            while parent:
                if parent.name in ["section", "aside", "div"]:
                    parent_text_preview = parent.get_text()[:300].lower()
                    if any(h.lower() in parent_text_preview for h in related_headings):
                        parent.decompose()
                        break
                parent = parent.find_parent()
                if parent and parent.name in ["body", "html", "main"]:
                    break

    return soup_copy


def extract_publication_date(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to extract the publication date from the IPSOS page.

    This function first filters out related articles sections to avoid
    picking up dates from linked articles.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    # CRITICAL: Filter out related articles sections first
    # The IPSOS page has "Sur le même sujet" and "Articles liés" sections
    # that contain links to other polls with their own <time> elements
    filtered_soup = _get_filtered_soup_for_main_article(soup)

    # Strategy 1: Extract from page title (most reliable for poll month)
    # IPSOS page titles are like: "Baromètre politique... - Décembre 2025 | Ipsos"
    title_element = soup.find("title")
    if title_element:
        title_text = title_element.get_text()
        # Look for "Month YYYY" pattern in title
        title_month_pattern = (
            r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})"
        )
        match = re.search(title_month_pattern, title_text, re.IGNORECASE)
        if match:
            month_name, year = match.groups()
            from .config import MONTH_MAP

            month = MONTH_MAP[month_name.lower()]
            # For poll ID purposes, we use the 1st of the month as the date
            # The actual publication date will be found below
            title_date = datetime(int(year), month, 1)
            # Don't return yet - try to find exact date, but remember this as fallback
            title_based_date = title_date.strftime("%Y-%m-%d")
    else:
        title_based_date = None

    # Strategy 2: Try to find date in meta tags (most reliable if present)
    date_meta = filtered_soup.find("meta", {"property": "article:published_time"})
    if date_meta and date_meta.get("content"):
        try:
            date_str = str(date_meta["content"])
            parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return parsed_date.strftime("%Y-%m-%d")
        except:
            pass

    # Strategy 3: Find date in <time datetime="..."> elements
    # IPSOS uses multiple formats:
    #   - ISO format: datetime="2025-12-13" (correct)
    #   - Malformed: datetime="13.12.25" (DD.MM.YY format)
    time_elements = filtered_soup.find_all("time", attrs={"datetime": True})
    for time_element in time_elements:
        datetime_attr = str(time_element.get("datetime", ""))

        # Check for ISO date format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...)
        if re.match(r"^\d{4}-\d{2}-\d{2}", datetime_attr):
            try:
                if "T" in datetime_attr:
                    datetime_attr = datetime_attr.split("T")[0]
                parsed_date = datetime.strptime(datetime_attr, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            except:
                continue

        # Check for malformed DD.MM.YY format (common on IPSOS)
        if re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}$", datetime_attr):
            try:
                parts = datetime_attr.split(".")
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if year < 100:  # 2-digit year
                    year += 2000
                parsed_date = datetime(year, month, day)
                return parsed_date.strftime("%Y-%m-%d")
            except:
                continue

    # Strategy 4: If we found a title-based date, use it as fallback
    if title_based_date:
        return title_based_date

    # Try to find date in the page content
    # Look for common French date patterns
    date_patterns = [
        # 13 janvier 2025
        r"(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})",
        # 13/12/2025
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
        # 13.12.25 or 13.12.2025
        r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})",
        # Décembre 2025 (month + year only)
        r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})",
    ]

    text = filtered_soup.get_text()
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        groups = match.groups()

        try:
            # Case 1: "13 janvier 2025"
            if len(groups) == 3 and groups[1].lower() in MONTH_MAP:
                day, month_name, year = groups
                month = MONTH_MAP[month_name.lower()]
                date_obj = datetime(int(year), month, int(day))
                return date_obj.strftime("%Y-%m-%d")

            # Case 2: "13/12/2025"
            if len(groups) == 3 and "/" in pattern:
                day, month, year = groups
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime("%Y-%m-%d")

            # Case 3: "13.12.25" or "13.12.2025"
            if len(groups) == 3 and "." in pattern:
                day, month, year = groups
                year = int(year)
                if year < 100:  # 2-digit year → assume 2000+
                    year += 2000
                date_obj = datetime(year, int(month), int(day))
                return date_obj.strftime("%Y-%m-%d")

            # Case 4: "Décembre 2025" (no day → assume 1st of month)
            if len(groups) == 2:
                month_name, year = groups
                month = MONTH_MAP[month_name.lower()]
                date_obj = datetime(int(year), month, 1)
                return date_obj.strftime("%Y-%m-%d")

        except Exception:
            continue

    return None


def _get_main_article_text(soup: BeautifulSoup) -> str:
    """
    Extract text from the main article content, excluding related articles sections.

    Uses _get_filtered_soup_for_main_article to remove "Sur le même sujet" and
    "Articles liés" sections, then extracts text.
    """
    # Strategy 1: Find "A propos de ce sondage" section specifically
    # This section contains the survey methodology info we need
    about_heading = soup.find(string=re.compile(r"A propos de ce sondage", re.IGNORECASE))
    if about_heading:
        parent = about_heading.find_parent()
        if parent:
            container = parent.find_parent()
            if container:
                section_text = container.get_text(separator=" ", strip=True)
                if "menée du" in section_text.lower():
                    return section_text

    # Strategy 2: Use filtered soup (shared filtering logic)
    filtered_soup = _get_filtered_soup_for_main_article(soup)

    # Try to find main article element
    main_article = filtered_soup.find("article") or filtered_soup.find("main")
    if main_article:
        return main_article.get_text(separator=" ", strip=True)

    # Fallback: return full filtered text
    return filtered_soup.get_text(separator=" ", strip=True)


def extract_survey_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract survey metadata from the 'A propos de ce sondage' section.

    Example text:
    "Enquête Ipsos bva-CESI École d'ingénieurs pour La Tribune Dimanche menée du
    6 au 7 novembre 2025 auprès de 1000 personnes, constituant un échantillon
    national représentatif de la population française âgée de 18 ans et plus."

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        Dict with survey_start_date, survey_end_date, sample_size, population_description
    """
    metadata: Dict[str, str] = {}

    # Get text from main article, excluding related articles sections
    text = _get_main_article_text(soup)

    # Pattern: "menée du X au Y MONTH YEAR"
    date_range_pattern = r"menée du (\d{1,2}) au (\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})"
    match = re.search(date_range_pattern, text, re.IGNORECASE)

    if match:
        start_day, end_day, month_name, year = match.groups()
        month = MONTH_MAP[month_name.lower()]

        try:
            start_date = datetime(int(year), month, int(start_day))
            end_date = datetime(int(year), month, int(end_day))
            metadata["survey_start_date"] = start_date.strftime("%Y-%m-%d")
            metadata["survey_end_date"] = end_date.strftime("%Y-%m-%d")
        except:
            pass

    # Pattern: "auprès de XXXX personnes"
    sample_pattern = r"auprès de (\d+)\s+personnes"
    match = re.search(sample_pattern, text, re.IGNORECASE)

    if match:
        metadata["sample_size"] = match.group(1)

    # Pattern: extract population description after "représentatif"
    pop_pattern = r"représentatif de ([^.]+)"
    match = re.search(pop_pattern, text, re.IGNORECASE)

    if match:
        metadata["population_description"] = match.group(1).strip()

    return metadata


def generate_poll_id(date: Optional[str] = None) -> str:
    """
    Generate a poll ID in the format ipsos_YYYYMM.

    Args:
        date: Optional date string in YYYY-MM-DD format

    Returns:
        Poll ID string
    """
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            return f"ipsos_{dt.strftime('%Y%m')}"
        except:
            pass

    # Fallback to current date
    return f"ipsos_{datetime.now().strftime('%Y%m')}"
