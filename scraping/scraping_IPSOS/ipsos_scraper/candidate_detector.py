"""
Candidate Detection Module

Functions for identifying which visualizations contain candidate voting data.
"""

import re

from .config import POLITICIAN_INDICATORS


def check_if_candidate_data(html_content: str) -> bool:
    """
    Check if HTML contains candidate voting data (vs policy issues or other data).

    Looks for politician names specifically in the Flourish data section
    to distinguish candidate polls from policy priority polls.

    Args:
        html_content: The HTML content to check

    Returns:
        True if likely contains candidate data, False otherwise
    """
    # Extract the _Flourish_data section which contains the actual visualization data
    flourish_data_pattern = r"_Flourish_data\s*=\s*(\{[^;]+\})"
    match = re.search(flourish_data_pattern, html_content, re.DOTALL)

    if not match:
        # Fallback to full HTML check if no Flourish data found
        search_content = html_content
    else:
        # Only search within the Flourish data JSON
        search_content = match.group(1)

    # Count how many politician names appear
    matches = sum(1 for name in POLITICIAN_INDICATORS if name in search_content)

    # If we find multiple politician names in the data section, it's likely candidate data
    return matches >= 3
