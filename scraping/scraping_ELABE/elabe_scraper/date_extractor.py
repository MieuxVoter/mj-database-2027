"""
Date Extraction Module

Functions for extracting dates and generating poll IDs.
"""

import re
from datetime import datetime
from typing import Optional

from .config import MONTH_NAME_MAP, PDF_FILENAME_PATTERN


def extract_publication_date_from_url(pdf_url: str) -> Optional[str]:
    """
    Extract publication date from PDF URL filename.
    
    The PDF filename contains the date in format YYYYMMDD.
    Example: 20251106_les_echos_observatoire-politique.pdf
    
    Args:
        pdf_url: The PDF URL containing the date
        
    Returns:
        Date in YYYY-MM-DD format, or None if not found
    """
    match = re.search(PDF_FILENAME_PATTERN, pdf_url)
    
    if match:
        date_str = match.group(1)  # YYYYMMDD
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return None


def generate_poll_id(publication_date: Optional[str] = None) -> str:
    """
    Generate poll ID in format elabe_YYYYMM.
    
    Args:
        publication_date: Publication date in YYYY-MM-DD format.
                         If None, uses current date.
    
    Returns:
        Poll ID string (e.g., "elabe_202511")
    """
    if publication_date:
        try:
            date_obj = datetime.strptime(publication_date, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.now()
    else:
        date_obj = datetime.now()
    
    return f"elabe_{date_obj.strftime('%Y%m')}"
