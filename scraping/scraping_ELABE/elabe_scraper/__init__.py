"""
ELABE Barometer Scraper Package

A modular package for scraping ELABE political barometer PDFs.
"""

__version__ = "1.0.0"

from .scraper import scrape_elabe_barometer

__all__ = ["scrape_elabe_barometer"]
