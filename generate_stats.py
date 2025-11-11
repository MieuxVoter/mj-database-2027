#!/usr/bin/env python3
"""
Generate statistics JSON file for README badges.

This script counts the number of polls by institute and generates a stats.json
file that can be consumed by dynamic shields.io badges.
It also updates static badges in README.md directly.
"""

import json
import re
from pathlib import Path


def count_polls_by_institute():
    """Count polls by institute from the polls/ directory."""
    polls_dir = Path("polls")
    
    stats = {
        "ipsos": 0,
        "elabe": 0,
        "ifop": 0,
        "odoxa": 0,
        "cluster17": 0,
        "total": 0
    }
    
    if not polls_dir.exists():
        print(f"⚠️  Warning: {polls_dir} directory not found")
        return stats
    
    # Count polls by checking folder names with CSV files
    for folder in polls_dir.iterdir():
        if not folder.is_dir():
            continue
        
        folder_name = folder.name.lower()
        
        # Check if folder contains CSV files (actual poll data)
        csv_files = list(folder.glob("*.csv"))
        if not csv_files:
            continue
        
        # Count by institute based on folder name prefix
        if folder_name.startswith("ipsos_"):
            stats["ipsos"] += 1
            stats["total"] += 1
        elif folder_name.startswith("elabe_"):
            stats["elabe"] += 1
            stats["total"] += 1
        elif folder_name.startswith("ifop_"):
            stats["ifop"] += 1
            stats["total"] += 1
        elif folder_name.startswith("odoxa_"):
            stats["odoxa"] += 1
            stats["total"] += 1
        elif folder_name.startswith("cluster17_"):
            stats["cluster17"] += 1
            stats["total"] += 1
    
    return stats


def update_readme_badges(readme_path: Path, stats: dict) -> bool:
    """Update the poll count badges in the README.

    Returns True if the file was modified, False otherwise.
    """
    if not readme_path.exists():
        print(f"⚠️  Warning: {readme_path} not found")
        return False
    
    content = readme_path.read_text(encoding="utf-8")
    original_content = content
    
    # Patterns to match each institute badge (static badges)
    patterns = {
        "ipsos": (
            r"!\[IPSOS Polls\]\(https://img\.shields\.io/badge/IPSOS-\d+_sondages-blue\)",
            lambda c: f"![IPSOS Polls](https://img.shields.io/badge/IPSOS-{c}_sondages-blue)"
        ),
        "elabe": (
            r"!\[ELABE Polls\]\(https://img\.shields\.io/badge/ELABE-\d+_sondages-green\)",
            lambda c: f"![ELABE Polls](https://img.shields.io/badge/ELABE-{c}_sondages-green)"
        ),
        "ifop": (
            r"!\[IFOP Polls\]\(https://img\.shields\.io/badge/IFOP-\d+_sondages-orange\)",
            lambda c: f"![IFOP Polls](https://img.shields.io/badge/IFOP-{c}_sondages-orange)"
        ),
        "odoxa": (
            r"!\[ODOXA Polls\]\(https://img\.shields\.io/badge/ODOXA-\d+_sondages-red\)",
            lambda c: f"![ODOXA Polls](https://img.shields.io/badge/ODOXA-{c}_sondages-red)"
        ),
        "cluster17": (
            r"!\[Cluster17 Polls\]\(https://img\.shields\.io/badge/Cluster17-\d+_sondages-purple\)",
            lambda c: f"![Cluster17 Polls](https://img.shields.io/badge/Cluster17-{c}_sondages-purple)"
        ),
        "total": (
            r"!\[Total Polls\]\(https://img\.shields\.io/badge/Total-\d+_sondages-brightgreen\)",
            lambda c: f"![Total Polls](https://img.shields.io/badge/Total-{c}_sondages-brightgreen)"
        ),
    }
    
    # Update each badge
    for key, (pattern, replacement_fn) in patterns.items():
        count = stats.get(key, 0)
        replacement = replacement_fn(count)
        content = re.sub(pattern, replacement, content)
    
    # Write back if modified
    if content != original_content:
        readme_path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    """Generate stats.json file."""
    print("📊 Counting polls by institute...")
    
    stats = count_polls_by_institute()
    
    # Print summary
    print("\n📈 Poll Statistics:")
    print(f"   IPSOS:     {stats['ipsos']:2d} polls")
    print(f"   ELABE:     {stats['elabe']:2d} polls")
    print(f"   IFOP:      {stats['ifop']:2d} polls")
    print(f"   ODOXA:     {stats['odoxa']:2d} polls")
    print(f"   Cluster17: {stats['cluster17']:2d} polls")
    print(f"   ─────────────────")
    print(f"   TOTAL:     {stats['total']:2d} polls")
    
    # Write to stats.json
    stats_file = Path("stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Stats written to {stats_file}")
    
    # Update README badges
    readme_path = Path("README.md")
    modified = update_readme_badges(readme_path, stats)
    
    if modified:
        print(f"✅ Updated badges in {readme_path}")
    else:
        print(f"ℹ️  Badges already up to date in {readme_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
