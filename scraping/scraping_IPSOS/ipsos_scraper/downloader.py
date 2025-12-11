"""
Downloader Module

Functions for downloading Flourish visualizations.
"""

from playwright.sync_api import Page
import time
import random

def download_flourish_visualization(viz_url: str, page: Page) -> str:
    """
    Download the HTML source of a Flourish visualization using Playwright.

    Args:
        viz_url: The URL of the Flourish visualization
        page: Playwright Page object

    Returns:
        The HTML content of the visualization
    """
    page.goto(viz_url)
    # Add some human-like delay
    time.sleep(1 + random.uniform(0, 2))
    return page.content()
