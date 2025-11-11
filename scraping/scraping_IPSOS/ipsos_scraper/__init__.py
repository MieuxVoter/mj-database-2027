"""
IPSOS Scraper Package

A modular package for scraping IPSOS Political Barometer data.

Modules:
    config: Configuration constants (URLs, patterns, headers)
    url_extractor: Extract Flourish visualization URLs
    date_extractor: Extract dates and survey metadata
    downloader: Download visualization HTML
    candidate_detector: Identify candidate voting data
    metadata_writer: Write metadata.txt files
    scraper: Main orchestration module
"""

from .scraper import scrape_ipsos_barometer

__version__ = "1.0.0"
__all__ = ["scrape_ipsos_barometer"]
