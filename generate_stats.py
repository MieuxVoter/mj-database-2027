#!/usr/bin/env python3
"""
Generate statistics JSON file for README badges.

This script counts the number of polls by institute and generates a stats.json
file that can be consumed by dynamic shields.io badges.
"""

import json
import os
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
    
    # Count polls by checking folder names
    for folder in polls_dir.iterdir():
        if not folder.is_dir():
            continue
        
        folder_name = folder.name.lower()
        
        # Check if folder contains poll data (has .csv or .html files)
        has_data = any(
            f.suffix in ['.csv', '.html'] 
            for f in folder.iterdir() 
            if f.is_file()
        )
        
        if not has_data:
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


if __name__ == "__main__":
    main()
