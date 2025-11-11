"""
Main ELABE Scraper Module

Orchestrates the scraping of ELABE barometer PDFs.
"""

import requests
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from .config import BASE_URL, BAROMETER_URL_TEMPLATE_WITH_DASH, BAROMETER_URL_TEMPLATE_NO_DASH, MONTH_URL_MAP, HEADERS
from .url_extractor import extract_pdf_url
from .date_extractor import extract_publication_date_from_url, generate_poll_id
from .pdf_downloader import download_pdf
from .metadata_writer import write_metadata


def scrape_elabe_barometer(
    output_dir: str = "../../polls",
    dry_run: bool = False,
    force: bool = False,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Scrape ELABE barometer PDF for a given month/year.

    Args:
        output_dir: Directory to save polls (default: "../../polls")
        dry_run: If True, only show what would be done
        force: If True, overwrite existing polls
        year: Year to scrape (default: current year)
        month: Month to scrape (default: current month)

    Returns:
        Dictionary with scraping results:
        {
            "success": bool,
            "poll_id": str,
            "output_path": Path or None,
            "skipped": bool,
            "message": str
        }
    """
    # Default to current month/year
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # Construct page URL
    month_slug = MONTH_URL_MAP.get(month)
    if not month_slug:
        return {
            "success": False,
            "poll_id": None,
            "output_path": None,
            "skipped": False,
            "message": f"Month {month} not in MONTH_URL_MAP",
        }

    # Try both URL formats (with and without dash)
    page_urls = [
        BAROMETER_URL_TEMPLATE_WITH_DASH.format(month_name=month_slug, year=year),
        BAROMETER_URL_TEMPLATE_NO_DASH.format(month_name=month_slug, year=year),
    ]

    try:
        # Create session
        session = requests.Session()

        # Try each URL format
        html_content = None
        page_url = None

        for url in page_urls:
            print(f"Trying URL: {url}")
            try:
                response = session.get(url, headers=HEADERS)
                response.raise_for_status()
                html_content = response.text
                page_url = url
                print(f"✓ Found page at: {page_url}")
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"  404 - Trying next format...")
                    continue
                raise

        if not html_content or not page_url:
            return {
                "success": False,
                "poll_id": None,
                "output_path": None,
                "skipped": False,
                "message": f"Could not find page for {month_slug} {year} (tried both URL formats)",
            }

        # Extract PDF URL
        pdf_url = extract_pdf_url(html_content)

        if not pdf_url:
            return {
                "success": False,
                "poll_id": None,
                "output_path": None,
                "skipped": False,
                "message": f"Could not find PDF URL on page: {page_url}",
            }

        print(f"Found PDF URL: {pdf_url}")

        # Extract publication date
        publication_date = extract_publication_date_from_url(pdf_url)
        if not publication_date:
            # Fallback to month/year
            publication_date = f"{year}-{month:02d}-01"

        print(f"Publication date: {publication_date}")

        # Generate poll ID
        poll_id = generate_poll_id(publication_date)

        # Check if already exists
        output_path = Path(output_dir) / poll_id
        pdf_path = output_path / "source.pdf"
        metadata_path = output_path / "metadata.txt"

        if pdf_path.exists() and metadata_path.exists() and not force:
            return {
                "success": True,
                "poll_id": poll_id,
                "output_path": output_path,
                "skipped": True,
                "message": f"Poll {poll_id} already exists (use --force to overwrite)",
            }

        if dry_run:
            return {
                "success": True,
                "poll_id": poll_id,
                "output_path": output_path,
                "skipped": False,
                "message": f"[DRY RUN] Would download PDF to {pdf_path}",
            }

        # Download PDF
        print(f"Downloading PDF...")
        pdf_content = download_pdf(pdf_url, session, HEADERS)

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Save PDF
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)

        print(f"Saved PDF to: {pdf_path}")

        # Write metadata
        write_metadata(
            output_dir=Path(output_dir),
            poll_id=poll_id,
            publication_date=publication_date,
            page_url=page_url,
            pdf_url=pdf_url,
        )

        print(f"Wrote metadata to: {metadata_path}")

        return {
            "success": True,
            "poll_id": poll_id,
            "output_path": output_path,
            "skipped": False,
            "message": f"Successfully scraped {poll_id}",
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "poll_id": None,
            "output_path": None,
            "skipped": False,
            "message": f"Error fetching page or PDF: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "poll_id": None,
            "output_path": None,
            "skipped": False,
            "message": f"Unexpected error: {str(e)}",
        }
