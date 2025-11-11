"""
Metadata Writer Module

Functions for writing metadata files for ELABE polls.
"""

from pathlib import Path
from typing import Optional


def write_metadata(output_dir: Path, poll_id: str, publication_date: str, page_url: str, pdf_url: str) -> None:
    """
    Write metadata.txt file for the poll.

    Args:
        output_dir: Base output directory
        poll_id: Poll identifier (e.g., "elabe_202511")
        publication_date: Publication date in YYYY-MM-DD format
        page_url: URL of the barometer page
        pdf_url: URL of the downloaded PDF
    """
    poll_dir = output_dir / poll_id
    poll_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = poll_dir / "metadata.txt"

    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(f"poll_id: {poll_id}\n")
        f.write(f"publication_date: {publication_date}\n")
        f.write(f"page_url: {page_url}\n")
        f.write(f"pdf_url: {pdf_url}\n")
        f.write(f"source_file: source.pdf\n")
