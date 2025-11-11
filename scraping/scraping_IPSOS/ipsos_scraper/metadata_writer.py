"""
Metadata Writer Module

Functions for writing metadata.txt files with survey information.
"""

from pathlib import Path
from typing import Optional


def write_metadata(
    output_path: Path,
    publication_date: Optional[str],
    survey_start_date: Optional[str],
    survey_end_date: Optional[str],
    sample_size: Optional[str],
    population_description: Optional[str],
    viz_url: str,
    barometer_url: str
) -> None:
    """
    Write metadata.txt file with survey information.
    
    Args:
        output_path: Directory where metadata.txt will be written
        publication_date: Publication date (YYYY-MM-DD format)
        survey_start_date: Survey start date (YYYY-MM-DD format)
        survey_end_date: Survey end date (YYYY-MM-DD format)
        sample_size: Sample size (e.g., "1000 personnes")
        population_description: Description of surveyed population
        viz_url: URL of the Flourish visualization
        barometer_url: URL of the barometer page
    """
    metadata_path = output_path / "metadata.txt"
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        f.write(f"publication_date: {publication_date or 'Unknown'}\n")
        f.write(f"survey_start_date: {survey_start_date or 'Unknown'}\n")
        f.write(f"survey_end_date: {survey_end_date or 'Unknown'}\n")
        f.write(f"sample_size: {sample_size or 'Unknown'}\n")
        f.write(f"population_description: {population_description or 'Unknown'}\n")
        f.write(f"visualization_url: {viz_url}\n")
        f.write(f"source_url: {barometer_url}\n")
