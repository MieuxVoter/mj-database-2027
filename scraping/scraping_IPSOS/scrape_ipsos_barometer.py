#!/usr/bin/env python3
"""
IPSOS Barometer Scraper

This script scrapes the IPSOS political barometer page to find Flourish visualizations,
downloads their HTML source, and organizes them by date.

Usage:
    python scrape_ipsos_barometer.py [--output-dir OUTPUT_DIR] [--dry-run]
"""

import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# Configuration
BASE_URL = "https://www.ipsos.com"
BAROMETER_URL = "https://www.ipsos.com/fr-fr/barometre-politique-ipsos-bva-la-tribune-dimanche"

# Patterns for finding Flourish visualizations
# The page uses public.flourish.studio for thumbnails, we need to extract the visualization IDs
FLOURISH_VIZ_PATTERN = r'visualisation/(\d+)'
FLOURISH_EMBED_TEMPLATE = "https://flo.uri.sh/visualisation/{}/embed?auto=1"

# HTTP Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def extract_flourish_urls(html_content: str) -> List[Dict[str, str]]:
    """
    Extract all Flourish visualization IDs from HTML content and construct embed URLs.
    
    The IPSOS page uses public.flourish.studio thumbnails, we extract the IDs
    and construct the flo.uri.sh embed URLs.
    
    Args:
        html_content: The HTML content to search
        
    Returns:
        List of dicts containing visualization ID and full URL
    """
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
        flourish_urls.append({
            "id": viz_id,
            "url": embed_url,
            "embed_url": embed_url
        })
    
    return flourish_urls


def extract_publication_date(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to extract the publication date from the IPSOS page.
    
    Args:
        soup: BeautifulSoup object of the page
        
    Returns:
        Date string in YYYY-MM-DD format, or None if not found
    """
    # Try to find date in meta tags
    date_meta = soup.find("meta", {"property": "article:published_time"})
    if date_meta and date_meta.get("content"):
        try:
            date_str = str(date_meta["content"])
            parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return parsed_date.strftime("%Y-%m-%d")
        except:
            pass
    
    # Try to find date in the page content
    # Look for common French date patterns
    date_patterns = [
        r"(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})",
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
    ]
    
    month_map = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }
    
    text = soup.get_text()
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 3 and match.group(2) in month_map:
                day, month_name, year = match.groups()
                month = month_map[month_name.lower()]
                try:
                    date_obj = datetime(int(year), month, int(day))
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    pass
            elif len(match.groups()) == 3:
                day, month, year = match.groups()
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime("%Y-%m-%d")
                except:
                    pass
    
    return None


def extract_survey_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract survey metadata from the 'A propos de ce sondage' section.
    
    Example text:
    "Enquête Ipsos bva-CESI École d'ingénieurs pour La Tribune Dimanche menée du 
    6 au 7 novembre 2025 auprès de 1000 personnes, constituant un échantillon 
    national représentatif de la population française âgée de 18 ans et plus."
    
    Args:
        soup: BeautifulSoup object of the page
        
    Returns:
        Dict with survey_start_date, survey_end_date, sample_size, population_description
    """
    metadata: Dict[str, str] = {}
    
    month_map = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }
    
    # Look for the survey information in the page text
    text = soup.get_text()
    
    # Pattern: "menée du X au Y MONTH YEAR"
    date_range_pattern = r"menée du (\d{1,2}) au (\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})"
    match = re.search(date_range_pattern, text, re.IGNORECASE)
    
    if match:
        start_day, end_day, month_name, year = match.groups()
        month = month_map[month_name.lower()]
        
        try:
            start_date = datetime(int(year), month, int(start_day))
            end_date = datetime(int(year), month, int(end_day))
            metadata["survey_start_date"] = start_date.strftime("%Y-%m-%d")
            metadata["survey_end_date"] = end_date.strftime("%Y-%m-%d")
        except:
            pass
    
    # Pattern: "auprès de XXXX personnes"
    sample_pattern = r"auprès de (\d+)\s+personnes"
    match = re.search(sample_pattern, text, re.IGNORECASE)
    
    if match:
        metadata["sample_size"] = match.group(1)
    
    # Pattern: extract population description after "représentatif"
    pop_pattern = r"représentatif de ([^.]+)"
    match = re.search(pop_pattern, text, re.IGNORECASE)
    
    if match:
        metadata["population_description"] = match.group(1).strip()
    
    return metadata


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
    flourish_data_pattern = r'_Flourish_data\s*=\s*(\{[^;]+\})'
    match = re.search(flourish_data_pattern, html_content, re.DOTALL)
    
    if not match:
        # Fallback to full HTML check if no Flourish data found
        search_content = html_content
    else:
        # Only search within the Flourish data JSON
        search_content = match.group(1)
    
    # Common politician last names that indicate this is a candidate poll
    politician_indicators = [
        "Bardella", "Le Pen", "Mélenchon", "Macron", 
        "Philippe", "Darmanin", "Attal", "Hollande",
        "Glucksmann", "Zemmour", "Roussel", "Bertrand",
        "Retailleau", "Ruffin", "Ciotti", "Tondelier"
    ]
    
    # Count how many politician names appear
    matches = sum(1 for name in politician_indicators if name in search_content)
    
    # If we find multiple politician names in the data section, it's likely candidate data
    return matches >= 3


def generate_poll_id(date: Optional[str] = None) -> str:
    """
    Generate a poll ID in the format ipsos_YYYYMM.
    
    Args:
        date: Optional date string in YYYY-MM-DD format
        
    Returns:
        Poll ID string
    """
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            return f"ipsos_{dt.strftime('%Y%m')}"
        except:
            pass
    
    # Fallback to current date
    return f"ipsos_{datetime.now().strftime('%Y%m')}"


def scrape_ipsos_barometer(output_dir: str = "../../polls", dry_run: bool = False, force: bool = False) -> List[Dict]:
    """
    Main scraping function: downloads IPSOS barometer page and extracts Flourish visualizations.
    
    Args:
        output_dir: Directory to save downloaded files
        dry_run: If True, don't actually download files
        force: If True, re-download even if folder exists (default: skip existing)
        
    Returns:
        List of dicts with information about downloaded visualizations
    """
    print(f"🔍 Scraping IPSOS Barometer: {BAROMETER_URL}")
    print()
    
    # Create session for connection pooling
    session = requests.Session()
    
    # Download the main barometer page
    print("📥 Downloading main page...")
    response = session.get(BAROMETER_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract publication date
    pub_date = extract_publication_date(soup)
    if pub_date:
        print(f"📅 Publication date: {pub_date}")
    else:
        print("⚠️  Could not extract publication date, using current date")
        pub_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extract survey metadata from "A propos de ce sondage" section
    print("📊 Extracting survey metadata...")
    survey_metadata = extract_survey_metadata(soup)
    
    if survey_metadata.get("survey_start_date"):
        print(f"   📅 Survey dates: {survey_metadata['survey_start_date']} to {survey_metadata['survey_end_date']}")
    if survey_metadata.get("sample_size"):
        print(f"   👥 Sample size: {survey_metadata['sample_size']} people")
    if survey_metadata.get("population_description"):
        print(f"   🎯 Population: {survey_metadata['population_description']}")
    print()
    
    # Generate poll ID
    poll_id = generate_poll_id(pub_date)
    print(f"🆔 Poll ID: {poll_id}")
    print()
    
    # Check if output directory already exists
    output_path = Path(output_dir) / poll_id
    if not force and output_path.exists() and not dry_run:
        source_html = output_path / "source.html"
        if source_html.exists():
            print(f"⏭️  Skipping {poll_id}: folder already exists")
            print(f"   Use --force to re-download")
            print(f"   Existing file: {source_html}")
            return []
    
    # Extract Flourish visualization URLs
    print("🔎 Searching for Flourish visualizations...")
    flourish_vizs = extract_flourish_urls(response.text)
    
    if not flourish_vizs:
        print("❌ No Flourish visualizations found!")
        return []
    
    print(f"✅ Found {len(flourish_vizs)} Flourish visualization(s)")
    for viz in flourish_vizs:
        print(f"   - ID: {viz['id']}, URL: {viz['url']}")
    print()
    
    # Create output directory
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {output_path}")
    else:
        print(f"📁 Would create directory: {output_path} (dry-run mode)")
    print()
    
    # First pass: identify which visualization contains candidate data
    print("🔍 Identifying which visualization contains candidate voting data...")
    candidate_viz_id = None
    
    for viz in flourish_vizs:
        try:
            html_content = download_flourish_visualization(viz["embed_url"], session)
            if check_if_candidate_data(html_content):
                candidate_viz_id = viz["id"]
                print(f"   ✓ Found candidate data in visualization {viz['id']}")
                # Cache the content to avoid re-downloading
                viz["_cached_html"] = html_content
                break
        except Exception as e:
            print(f"   ⚠️  Error checking visualization {viz['id']}: {e}")
    
    if not candidate_viz_id:
        print("   ⚠️  Could not identify candidate data visualization, will download the first one")
        candidate_viz_id = flourish_vizs[0]["id"]
    
    print()
    
    # Download only the candidate data visualization
    print(f"📥 Downloading candidate data visualization (ID: {candidate_viz_id})...")
    
    results = []
    for viz in flourish_vizs:
        if viz["id"] != candidate_viz_id:
            continue
            
        filename = "source.html"
        filepath = output_path / filename
        
        if dry_run:
            print(f"   [DRY-RUN] Would download: {viz['embed_url']}")
            print(f"   [DRY-RUN] Would save to: {filepath}")
            results.append({
                "poll_id": poll_id,
                "viz_id": viz["id"],
                "url": viz["embed_url"],
                "saved_path": str(filepath),
                "dry_run": True
            })
        else:
            try:
                # Use cached content if available
                if "_cached_html" in viz:
                    html_content = viz["_cached_html"]
                else:
                    html_content = download_flourish_visualization(viz["embed_url"], session)
                
                # Save to file
                filepath.write_text(html_content, encoding="utf-8")
                
                print(f"   ✅ Saved to: {filepath}")
                results.append({
                    "poll_id": poll_id,
                    "viz_id": viz["id"],
                    "url": viz["embed_url"],
                    "saved_path": str(filepath),
                    "size_bytes": len(html_content)
                })
            except Exception as e:
                print(f"   ❌ Error downloading visualization {viz['id']}: {e}")
                results.append({
                    "poll_id": poll_id,
                    "viz_id": viz["id"],
                    "url": viz["embed_url"],
                    "error": str(e)
                })
        print()
    
    # Save metadata to file
    if not dry_run and results:
        metadata_file = output_path / "metadata.txt"
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(f"# IPSOS Barometer Poll Metadata\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"poll_id: {poll_id}\n")
            f.write(f"publication_date: {pub_date}\n")
            f.write(f"source_url: {BAROMETER_URL}\n")
            f.write(f"visualization_id: {candidate_viz_id}\n")
            f.write(f"visualization_url: https://flo.uri.sh/visualisation/{candidate_viz_id}/embed?auto=1\n")
            f.write(f"\n# Survey metadata (extracted from 'A propos de ce sondage' section)\n")
            
            # Use extracted survey dates if available, otherwise fall back to publication date
            survey_start = survey_metadata.get("survey_start_date", pub_date)
            survey_end = survey_metadata.get("survey_end_date", pub_date)
            sample_size = survey_metadata.get("sample_size", "1000")
            pop_desc = survey_metadata.get("population_description", "représentatif de la population française âgée de 18 ans et plus")
            
            f.write(f"survey_start_date: {survey_start}\n")
            f.write(f"survey_end_date: {survey_end}\n")
            f.write(f"sample_size: {sample_size}\n")
            f.write(f"population_description: {pop_desc}\n")
            f.write(f"\n# Additional metadata\n")
            f.write(f"poll_type: pt1\n")
            f.write(f"population: all\n")
        
        print(f"📝 Saved metadata to: {metadata_file}")
        print()
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape IPSOS political barometer for Flourish visualizations"
    )
    parser.add_argument(
        "--output-dir",
        default="../../polls",
        help="Output directory for downloaded files (default: ../../polls)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without downloading files"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if poll folder already exists"
    )
    
    args = parser.parse_args()
    
    try:
        results = scrape_ipsos_barometer(
            output_dir=args.output_dir,
            dry_run=args.dry_run,
            force=args.force
        )
        
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        
        print(f"✅ Successfully downloaded: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if successful:
            print()
            print("Downloaded files:")
            for r in successful:
                if not r.get("dry_run"):
                    size_kb = r.get("size_bytes", 0) / 1024
                    print(f"   - {r['saved_path']} ({size_kb:.1f} KB)")
                else:
                    print(f"   - {r['saved_path']} (dry-run)")
        
        if failed:
            print()
            print("Failed downloads:")
            for r in failed:
                print(f"   - Viz ID {r['viz_id']}: {r['error']}")
        
        print()
        if args.dry_run:
            print("🔍 This was a dry run. Run without --dry-run to actually download files.")
        else:
            print("✅ Done! Files are ready for extraction with extract_ipsos_from_html.py")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
