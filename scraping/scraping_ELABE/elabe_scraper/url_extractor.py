"""
URL Extraction Module

Functions for extracting PDF URL from ELABE barometer pages.
"""

import re
from typing import Optional

from .config import PDF_LINK_PATTERN


def extract_pdf_url(html_content: str) -> Optional[str]:
    """
    Extract PDF download URL from ELABE barometer page.
    
    Looks for the "Télécharger le rapport" link in the HTML.
    
    Args:
        html_content: The HTML content of the barometer page
        
    Returns:
        PDF URL if found, None otherwise
    """
    # Search for the download link pattern
    match = re.search(PDF_LINK_PATTERN, html_content, re.DOTALL | re.IGNORECASE)
    
    if match:
        pdf_url = match.group(1)
        return pdf_url
    
    return None
