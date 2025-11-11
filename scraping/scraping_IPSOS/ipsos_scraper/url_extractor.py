"""
URL Extraction Module

Functions for extracting and processing Flourish visualization URLs.
"""

import re
from typing import List, Dict, Union

from bs4 import BeautifulSoup

from .config import FLOURISH_VIZ_PATTERN, FLOURISH_EMBED_TEMPLATE


def extract_flourish_urls(html_content: Union[str, BeautifulSoup]) -> List[Dict[str, str]]:
    """
    Extract all Flourish visualization IDs from HTML content and construct embed URLs.

    The IPSOS page uses public.flourish.studio thumbnails, we extract the IDs
    and construct the flo.uri.sh embed URLs.

    Args:
        html_content: The HTML content to search (string or BeautifulSoup object)

    Returns:
        List of dicts containing visualization ID and full URL
    """
    # Convert BeautifulSoup to string if needed
    if isinstance(html_content, BeautifulSoup):
        html_content = str(html_content)

    flourish_urls = []

    # Find all visualization IDs
    matches = re.finditer(FLOURISH_VIZ_PATTERN, html_content)
    viz_ids = set()  # Use set to avoid duplicates

    for match in matches:
        viz_id = match.group(1)
        viz_ids.add(viz_id)

    # Construct embed URLs for each unique visualization ID
    for viz_id in sorted(viz_ids):  # Sort for consistent ordering
        embed_url = FLOURISH_EMBED_TEMPLATE.format(viz_id)
        flourish_urls.append({"id": viz_id, "url": embed_url, "embed_url": embed_url})

    return flourish_urls
