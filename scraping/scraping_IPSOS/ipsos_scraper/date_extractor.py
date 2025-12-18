"""
Date Extraction Module

Functions for extracting publication and survey dates from IPSOS pages.
"""

import re
from datetime import datetime
from typing import Optional, Dict
from bs4 import BeautifulSoup

from .config import MONTH_MAP


def extract_publication_date(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to extract the publication date from the IPSOS page.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    # Try to find date in <time datetime="..."> element first (most reliable for IPSOS)
    # The IPSOS page uses <time datetime="2025-12-13">13.12.25</time>
    # But some elements may have malformed datetime like "13.12.25", so we look for ISO format
    time_elements = soup.find_all("time", attrs={"datetime": True})
    for time_element in time_elements:
        datetime_attr = str(time_element.get("datetime", ""))
        # Check if it looks like an ISO date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...)
        if re.match(r"^\d{4}-\d{2}-\d{2}", datetime_attr):
            try:
                # Handle both "2025-12-13" and "2025-12-13T16:00:00+01:00" formats
                if "T" in datetime_attr:
                    datetime_attr = datetime_attr.split("T")[0]
                parsed_date = datetime.strptime(datetime_attr, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            except:
                continue

    # Try to find date in meta tags
    date_meta = soup.find("meta", {"property": "article:published_time"})
    if date_meta and date_meta.get("content"):
        try:
            date_str = str(date_meta["content"])
            parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return parsed_date.strftime("%Y-%m-%d")
        except:
            pass

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

    text = soup.get_text()
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

    # Look for the survey information in the page text
    text = soup.get_text()

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
