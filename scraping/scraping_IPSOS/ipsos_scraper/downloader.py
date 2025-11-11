"""
Downloader Module

Functions for downloading Flourish visualizations.
"""

import requests

from .config import HEADERS


def download_flourish_visualization(viz_url: str, session: requests.Session) -> str:
    """
    Download the HTML source of a Flourish visualization.
    
    Args:
        viz_url: The URL of the Flourish visualization
        session: requests Session object
        
    Returns:
        The HTML content of the visualization
    """
    response = session.get(viz_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text
