#!/usr/bin/env python3
"""
ELABE Barometer Scraper

CLI wrapper for scraping ELABE political barometer PDFs.
Downloads PDF reports from https://elabe.fr/barometre-politique-{month}-{year}/

Usage:
    python scrape_elabe_barometer.py                    # Scrape current month
    python scrape_elabe_barometer.py --dry-run          # Show what would be done
    python scrape_elabe_barometer.py --force            # Overwrite existing polls
    python scrape_elabe_barometer.py --month 10 --year 2025  # Specific month
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import elabe_scraper
sys.path.insert(0, str(Path(__file__).parent))

from elabe_scraper import scrape_elabe_barometer


def main():
    parser = argparse.ArgumentParser(
        description="Scrape ELABE political barometer PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Scrape current month
  %(prog)s --dry-run               # Show what would be done
  %(prog)s --force                 # Overwrite existing polls
  %(prog)s --month 11 --year 2025  # Scrape November 2025
        """,
    )

    parser.add_argument(
        "--output-dir", type=str, default="../../polls", help="Output directory for polls (default: ../../polls)"
    )

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without downloading")

    parser.add_argument("--force", action="store_true", help="Overwrite existing polls")

    parser.add_argument("--month", type=int, help="Month to scrape (1-12, default: current month)")

    parser.add_argument("--year", type=int, help="Year to scrape (default: current year)")

    args = parser.parse_args()

    # Run scraper
    result = scrape_elabe_barometer(
        output_dir=args.output_dir, dry_run=args.dry_run, force=args.force, year=args.year, month=args.month
    )

    # Print result
    if result["skipped"]:
        print(f"\n✓ {result['message']}")
    elif result["success"]:
        print(f"\n✓ {result['message']}")
        if result["output_path"]:
            print(f"  Output: {result['output_path']}")
    else:
        print(f"\n✗ {result['message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
