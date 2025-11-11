#!/usr/bin/env python3
"""
IPSOS Barometer Scraper

This script scrapes the IPSOS political barometer page to find Flourish visualizations,
downloads their HTML source, and organizes them by date.

This is now a lightweight CLI wrapper around the ipsos_scraper package.

Usage:
    python scrape_ipsos_barometer.py [--output-dir OUTPUT_DIR] [--dry-run] [--force]

Options:
    --output-dir: Directory where polls will be saved (default: polls)
    --dry-run: Show what would be done without actually downloading
    --force: Download even if poll already exists (overrides --skip-existing)
"""

import argparse
import sys

from ipsos_scraper import scrape_ipsos_barometer


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scrape IPSOS political barometer for Flourish visualizations")
    parser.add_argument(
        "--output-dir", default="../../polls", help="Output directory for downloaded files (default: ../../polls)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without downloading files")
    parser.add_argument("--force", action="store_true", help="Force re-download even if poll folder already exists")

    args = parser.parse_args()

    try:
        result = scrape_ipsos_barometer(output_dir=args.output_dir, dry_run=args.dry_run, force=args.force)

        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)

        if result["success"]:
            if result["skipped"]:
                print(f"⏭️  {result['message']}")
                print(f"   Use --force to re-download")
            else:
                print(f"✅ {result['message']}")
                if not args.dry_run:
                    print(f"   Poll ID: {result['poll_id']}")
                    print(f"   Output: {result['output_path']}")
        else:
            print(f"❌ {result['message']}")
            sys.exit(1)

        print()
        if args.dry_run:
            print("🔍 This was a dry run. Run without --dry-run to actually download files.")
        else:
            if not result["skipped"]:
                print("✅ Done! Files are ready for extraction with extract_ipsos_from_html.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
