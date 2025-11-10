#!/usr/bin/env python3
"""
Example script showing how to add a complete new poll to the database.
This script automates the full workflow.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def add_poll_to_csv(
    poll_id: str, poll_type: str, nb_people: int, start_date: str, end_date: str, folder: str, population: str = "all"
):
    """
    Add a poll entry to polls.csv

    Args:
        poll_id: e.g., "ipsos_202511"
        poll_type: e.g., "pt1"
        nb_people: e.g., 1000
        start_date: e.g., "2025-11-06"
        end_date: e.g., "2025-11-07"
        folder: e.g., "polls/ipsos_202511"
        population: e.g., "all"
    """
    polls_csv = Path("polls.csv")

    # Check if entry already exists
    with open(polls_csv, "r", encoding="utf-8") as f:
        content = f.read()
        if poll_id in content and population in content:
            print(f"⚠ Entry for {poll_id} ({population}) already exists in polls.csv")
            return False

    # Append new entry
    new_line = f"{poll_id},{poll_type},{nb_people},{start_date},{end_date},{folder},{population}\n"

    with open(polls_csv, "a", encoding="utf-8") as f:
        f.write(new_line)

    print(f"✓ Added {poll_id} ({population}) to polls.csv")
    return True


def main():
    """
    Example workflow for adding IPSOS November 2025 poll
    """
    print("=" * 60)
    print("Adding IPSOS November 2025 Poll")
    print("=" * 60)

    # Configuration
    poll_id = "ipsos_202511"
    poll_type = "pt1"  # IPSOS type
    nb_people = 1000
    start_date = "2025-11-06"
    end_date = "2025-11-07"
    folder = "polls/ipsos_202511"
    source_html = Path(f"{folder}/source.html")

    # Step 1: Check if source file exists
    print(f"\n1. Checking source file...")
    if not source_html.exists():
        print(f"✗ Error: {source_html} not found")
        print(f"   Please download the HTML source and save it to {source_html}")
        sys.exit(1)
    print(f"✓ Found {source_html}")

    # Step 2: Extract data
    print(f"\n2. Extracting data from HTML...")
    result = subprocess.run(
        ["python", "mining/mining_IPSOS/extract_ipsos_from_html.py", str(source_html)], capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"✗ Error extracting data:")
        print(result.stderr)
        sys.exit(1)

    print(result.stdout)

    # Step 3: Add to polls.csv
    print(f"\n3. Adding metadata to polls.csv...")
    add_poll_to_csv(poll_id, poll_type, nb_people, start_date, end_date, folder, "all")

    # Step 4: Run merge
    print(f"\n4. Running merge.py...")
    result = subprocess.run(["python", "merge.py"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ Error running merge:")
        print(result.stderr)
        sys.exit(1)

    print(result.stdout)

    # Done
    print("\n" + "=" * 60)
    print("✓ Successfully added poll to database!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  - {folder}/{poll_id}_all.csv")
    print(f"  - mj2027.csv (updated)")
    print(f"\nNext steps:")
    print(f"  - Review the changes")
    print(f"  - Commit to git")
    print(f"  - Create a pull request")


if __name__ == "__main__":
    main()
