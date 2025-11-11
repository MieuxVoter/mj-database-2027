"""
Main Scraper Module

Orchestrates the complete IPSOS barometer scraping process.
"""

import os
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, BAROMETER_URL, HEADERS
from .url_extractor import extract_flourish_urls
from .date_extractor import (
    extract_publication_date,
    extract_survey_metadata,
    generate_poll_id
)
from .downloader import download_flourish_visualization
from .candidate_detector import check_if_candidate_data
from .metadata_writer import write_metadata


def scrape_ipsos_barometer(
    output_dir: str = "polls",
    dry_run: bool = False,
    force: bool = False
) -> dict:
    """
    Scrape IPSOS Political Barometer for the latest poll data.
    
    This function:
    1. Fetches the IPSOS barometer page
    2. Extracts the publication date and generates poll ID (ipsos_YYYYMM)
    3. Checks if poll already exists (skip if --force not set)
    4. Identifies Flourish visualizations on the page
    5. Downloads only the visualization containing candidate voting data
    6. Extracts survey metadata (dates, sample size, population)
    7. Saves source.html and metadata.txt
    
    Args:
        output_dir: Directory where polls will be saved (default: "polls")
        dry_run: If True, only print what would be done without downloading
        force: If True, download even if poll already exists (default: False)
        
    Returns:
        Dictionary with scraping results:
        {
            'success': bool,
            'poll_id': str,
            'output_path': Path,
            'skipped': bool,
            'message': str
        }
    """
    print(f"\n🔍 Fetching IPSOS barometer page: {BAROMETER_URL}")
    
    session = requests.Session()
    
    try:
        # Fetch the main barometer page
        response = session.get(BAROMETER_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract publication date and generate poll ID
        publication_date = extract_publication_date(soup)
        if not publication_date:
            return {
                'success': False,
                'poll_id': None,
                'output_path': None,
                'skipped': False,
                'message': "❌ Could not extract publication date from the page"
            }
        
        poll_id = generate_poll_id(publication_date)
        print(f"📅 Publication date: {publication_date}")
        print(f"📊 Poll ID: {poll_id}")
        
        # Prepare output directory
        output_path = Path(output_dir) / poll_id
        
        # Check if poll already exists (unless --force is set)
        source_html_path = output_path / "source.html"
        if source_html_path.exists() and not force:
            print(f"⏭️  Poll {poll_id} already exists. Skipping download.")
            print(f"   (Use --force to override and re-download)")
            return {
                'success': True,
                'poll_id': poll_id,
                'output_path': output_path,
                'skipped': True,
                'message': f"Poll {poll_id} already exists (skipped)"
            }
        
        if dry_run:
            print("\n🔍 DRY RUN - Would create directory:")
            print(f"   {output_path}")
            print("\n🔍 Extracting Flourish visualizations...")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            print(f"\n📁 Created output directory: {output_path}")
            print("\n🔍 Extracting Flourish visualizations...")
        
        # Extract all Flourish visualization URLs
        viz_list = extract_flourish_urls(soup)
        
        if not viz_list:
            return {
                'success': False,
                'poll_id': poll_id,
                'output_path': output_path,
                'skipped': False,
                'message': "❌ No Flourish visualizations found on the page"
            }
        
        print(f"✅ Found {len(viz_list)} Flourish visualizations")
        
        # Extract survey metadata from main page
        survey_metadata = extract_survey_metadata(soup)
        survey_start_date = survey_metadata.get('survey_start_date')
        survey_end_date = survey_metadata.get('survey_end_date')
        sample_size = survey_metadata.get('sample_size')
        population_description = survey_metadata.get('population_description')
        
        print(f"\n📋 Survey metadata:")
        print(f"   Start date: {survey_start_date or 'Unknown'}")
        print(f"   End date: {survey_end_date or 'Unknown'}")
        print(f"   Sample size: {sample_size or 'Unknown'}")
        print(f"   Population: {population_description or 'Unknown'}")
        
        # Check each visualization to find candidate data
        candidate_viz = None
        for i, viz_info in enumerate(viz_list, 1):
            viz_url = viz_info['url']
            viz_id = viz_info['id']
            
            if dry_run:
                print(f"\n🔍 [{i}/{len(viz_list)}] Would check visualization {viz_id}")
                print(f"   URL: {viz_url}")
            else:
                print(f"\n🔍 [{i}/{len(viz_list)}] Checking visualization {viz_id}...")
                print(f"   URL: {viz_url}")
                
                try:
                    viz_html = download_flourish_visualization(viz_url, session)
                    
                    if check_if_candidate_data(viz_html):
                        print(f"   ✅ Contains candidate data!")
                        candidate_viz = {
                            'id': viz_id,
                            'url': viz_url,
                            'html': viz_html
                        }
                        break
                    else:
                        print(f"   ⏭️  Does not contain candidate data (skipping)")
                except Exception as e:
                    print(f"   ⚠️  Error checking visualization: {e}")
        
        if dry_run:
            print("\n✅ DRY RUN COMPLETE - No files were downloaded")
            return {
                'success': True,
                'poll_id': poll_id,
                'output_path': output_path,
                'skipped': False,
                'message': "Dry run completed successfully"
            }
        
        if not candidate_viz:
            return {
                'success': False,
                'poll_id': poll_id,
                'output_path': output_path,
                'skipped': False,
                'message': "❌ No visualization with candidate data found"
            }
        
        # Save the candidate data visualization
        source_html_path = output_path / "source.html"
        with open(source_html_path, 'w', encoding='utf-8') as f:
            f.write(candidate_viz['html'])
        
        file_size = os.path.getsize(source_html_path)
        print(f"\n💾 Saved source.html ({file_size:,} bytes)")
        
        # Write metadata.txt
        write_metadata(
            output_path=output_path,
            publication_date=publication_date,
            survey_start_date=survey_start_date,
            survey_end_date=survey_end_date,
            sample_size=sample_size,
            population_description=population_description,
            viz_url=candidate_viz['url'],
            barometer_url=BAROMETER_URL
        )
        
        print(f"💾 Saved metadata.txt")
        
        print(f"\n✅ Successfully scraped poll {poll_id}")
        print(f"📁 Output directory: {output_path}")
        
        return {
            'success': True,
            'poll_id': poll_id,
            'output_path': output_path,
            'skipped': False,
            'message': f"Successfully scraped poll {poll_id}"
        }
        
    except requests.RequestException as e:
        return {
            'success': False,
            'poll_id': None,
            'output_path': None,
            'skipped': False,
            'message': f"❌ Error fetching barometer page: {e}"
        }
    except Exception as e:
        return {
            'success': False,
            'poll_id': None,
            'output_path': None,
            'skipped': False,
            'message': f"❌ Unexpected error: {e}"
        }
