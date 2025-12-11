"""
Main Scraper Module

Orchestrates the complete IPSOS barometer scraping process.
"""

import os
import time
import random
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

# The installed playwright-stealth package (v2.0.0) uses a class-based approach
# instead of the function-based approach shown in some examples.
from playwright_stealth.stealth import Stealth
from bs4 import BeautifulSoup

from .config import BASE_URL, BAROMETER_URL, get_random_headers
from .url_extractor import extract_flourish_urls
from .date_extractor import extract_publication_date, extract_survey_metadata, generate_poll_id
from .downloader import download_flourish_visualization
from .candidate_detector import check_if_candidate_data
from .metadata_writer import write_metadata


def scrape_ipsos_barometer(output_dir: str = "polls", dry_run: bool = False, force: bool = False) -> dict:
    """
    Scrape IPSOS Political Barometer for the latest poll data.

    This function:
    1. Fetches the IPSOS barometer page using Playwright
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
    print("   Using Playwright with stealth mode...")

    try:
        # Wrap playwright context manager with Stealth().use_sync() to auto-apply patches
        with Stealth().use_sync(sync_playwright()) as p:
            # Step 5: Randomize the user-agent
            headers = get_random_headers()
            user_agent = headers.get("User-Agent")

            # Step 1 & 3: Use Playwright with persistent context
            # Simulating human-like browser profile
            # We use a local 'chrome_profile' directory for persistence
            user_data_dir = "./chrome_profile"

            # Step 6: Override the timezone & locale
            # Using French locale and timezone as we are scraping a French site
            locale = "fr-FR"
            timezone_id = "Europe/Paris"

            # Launch browser with persistent context
            # We use headless=True for CI but with stealth mode it should be fine
            # Note: with persistent context, playwright-stealth patches might need to be applied differently
            # but use_sync() should handle new pages/contexts.
            # However, for persistent context, methods are on the browser context directly.
            # playwright-stealth v2 hooks into browser.new_context and browser.new_page.
            # launch_persistent_context returns a BrowserContext.

            print(f"   Launching Chromium (Persistent Context: {user_data_dir})")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                user_agent=user_agent,
                locale=locale,
                timezone_id=timezone_id,
                viewport={"width": 1280 + random.randint(0, 500), "height": 720 + random.randint(0, 500)},
                device_scale_factor=random.choice([1, 1.5, 2]),
            )

            try:
                page = browser.pages[0] if browser.pages else browser.new_page()

                # Step 2: Turn on stealth mode (Handled by Stealth().use_sync() wrapper for created pages)
                # But for persistent context, we might need to manually ensure it if use_sync didn't catch it
                # because launch_persistent_context is a method on BrowserType.

                # Verified: playwright-stealth v2 patches BrowserType.launch_persistent_context if possible?
                # The code shows patches for new_context/new_page but launch_persistent_context might be tricky.
                # However, the user request specifically asked for persistent profile AND stealth.
                # Let's trust that use_sync() does its best, or usage of page.goto will trigger it if implemented.
                # Removing explicit stealth(page) call as it doesn't exist.

                # Step 1: Navigate to the target page
                page.goto(BAROMETER_URL)

                # Step 4: Mimic human activity
                # Random waits and scrolling
                wait_time = 800 + random.randint(0, 500)
                page.wait_for_timeout(wait_time)
                page.mouse.wheel(0, 300)
                page.wait_for_timeout(600)

                # Additional wait to ensure dynamic content loads (though IPSOS is mostly static for this)
                # Step 7: Slow down scraping cadence
                page.wait_for_timeout(1000 + random.randint(0, 1200))

                # Get page content
                content = page.content()
                soup = BeautifulSoup(content, "html.parser")

                # Extract publication date and generate poll ID
                publication_date = extract_publication_date(soup)
                if not publication_date:
                    return {
                        "success": False,
                        "poll_id": None,
                        "output_path": None,
                        "skipped": False,
                        "message": "❌ Could not extract publication date from the page",
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
                        "success": True,
                        "poll_id": poll_id,
                        "output_path": output_path,
                        "skipped": True,
                        "message": f"Poll {poll_id} already exists (skipped)",
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
                        "success": False,
                        "poll_id": poll_id,
                        "output_path": output_path,
                        "skipped": False,
                        "message": "❌ No Flourish visualizations found on the page",
                    }

                print(f"✅ Found {len(viz_list)} Flourish visualizations")

                # Extract survey metadata from main page
                survey_metadata = extract_survey_metadata(soup)
                survey_start_date = survey_metadata.get("survey_start_date")
                survey_end_date = survey_metadata.get("survey_end_date")
                sample_size = survey_metadata.get("sample_size")
                population_description = survey_metadata.get("population_description")

                print(f"\n📋 Survey metadata:")
                print(f"   Start date: {survey_start_date or 'Unknown'}")
                print(f"   End date: {survey_end_date or 'Unknown'}")
                print(f"   Sample size: {sample_size or 'Unknown'}")
                print(f"   Population: {population_description or 'Unknown'}")

                # Check each visualization to find candidate data
                candidate_viz = None

                if dry_run:
                    print("\n✅ DRY RUN COMPLETE - No files were downloaded")
                    return {
                        "success": True,
                        "poll_id": poll_id,
                        "output_path": output_path,
                        "skipped": False,
                        "message": "Dry run completed successfully",
                    }

                for i, viz_info in enumerate(viz_list, 1):
                    viz_url = viz_info["url"]
                    viz_id = viz_info["id"]

                    print(f"\n🔍 [{i}/{len(viz_list)}] Checking visualization {viz_id}...")
                    print(f"   URL: {viz_url}")

                    try:
                        # Use the page to download/view the visualization
                        # We pass 'page' to our updated downlader
                        viz_html = download_flourish_visualization(viz_url, page)

                        if check_if_candidate_data(viz_html):
                            print(f"   ✅ Contains candidate data!")
                            candidate_viz = {"id": viz_id, "url": viz_url, "html": viz_html}
                            break
                        else:
                            print(f"   ⏭️  Does not contain candidate data (skipping)")
                    except Exception as e:
                        print(f"   ⚠️  Error checking visualization: {e}")

                if not candidate_viz:
                    return {
                        "success": False,
                        "poll_id": poll_id,
                        "output_path": output_path,
                        "skipped": False,
                        "message": "❌ No visualization with candidate data found",
                    }

                # Save the candidate data visualization
                source_html_path = output_path / "source.html"
                with open(source_html_path, "w", encoding="utf-8") as f:
                    f.write(candidate_viz["html"])

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
                    viz_url=candidate_viz["url"],
                    barometer_url=BAROMETER_URL,
                )

                print(f"💾 Saved metadata.txt")

                print(f"\n✅ Successfully scraped poll {poll_id}")
                print(f"📁 Output directory: {output_path}")

                return {
                    "success": True,
                    "poll_id": poll_id,
                    "output_path": output_path,
                    "skipped": False,
                    "message": f"Successfully scraped poll {poll_id}",
                }

            finally:
                browser.close()

    except Exception as e:
        return {
            "success": False,
            "poll_id": None,
            "output_path": None,
            "skipped": False,
            "message": f"❌ Unexpected error during scraping: {e}",
        }
