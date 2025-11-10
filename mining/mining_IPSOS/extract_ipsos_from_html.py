#!/usr/bin/env python3
"""
Script to extract IPSOS poll data from HTML source files and convert to CSV format.
Usage: python extract_ipsos_from_html.py <source_html_file> <output_csv_file>
"""

import json
import re
import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple


def load_candidates_mapping(candidates_csv: Path = Path("candidates.csv")) -> Dict[str, str]:
    """
    Load candidate name to ID mapping from candidates.csv
    
    Args:
        candidates_csv: Path to candidates.csv file
    
    Returns:
        Dictionary mapping "Firstname Lastname" to candidate_id
    """
    mapping = {}
    
    try:
        with open(candidates_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create full name from name and surname
                name = row.get('name', '').strip()
                surname = row.get('surname', '').strip()
                candidate_id = row.get('candidate_id', '').strip()
                
                if name and surname and candidate_id:
                    # Remove comma from name if present (e.g., "François, Rebsamen")
                    name = name.replace(',', '')
                    full_name = f"{name} {surname}"
                    mapping[full_name] = candidate_id
        
        print(f"Loaded {len(mapping)} candidates from {candidates_csv}")
        return mapping
        
    except FileNotFoundError:
        print(f"Error: {candidates_csv} not found")
        print("Make sure you're running the script from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {candidates_csv}: {e}")
        sys.exit(1)


def normalize_name(name: str) -> str:
    """Normalize candidate name for matching."""
    # Remove extra spaces and standardize
    name = " ".join(name.split())
    return name


def extract_data_from_html(html_file: Path) -> List[Dict]:
    """
    Extract the data array from HTML file.
    
    Returns:
        List of dictionaries with 'label' and 'value' keys
    """
    print(f"Reading HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Search for the data pattern in the HTML
    # Pattern: "data":[{"label":"Name","metadata":[],"value":[numbers]},...]
    # We need to find the complete data array
    pattern = r'"data":\[(\{[^\]]*\}(?:,\{[^\]]*\})*)\]'
    
    matches = re.search(pattern, content)
    
    if not matches:
        # Try a simpler approach - find between "data":[ and the closing ]
        start_marker = '"data":['
        start_idx = content.find(start_marker)
        if start_idx == -1:
            raise ValueError("Could not find 'data':[ in HTML file")
        
        # Find the matching closing bracket
        start_idx += len(start_marker)
        bracket_count = 1
        end_idx = start_idx
        
        while bracket_count > 0 and end_idx < len(content):
            if content[end_idx] == '[':
                bracket_count += 1
            elif content[end_idx] == ']':
                bracket_count -= 1
            end_idx += 1
        
        data_str = '[' + content[start_idx:end_idx-1] + ']'
    else:
        data_str = '[' + matches.group(1) + ']'
    
    # Parse the JSON data
    try:
        data = json.loads(data_str)
        print(f"Found {len(data)} candidates in the data")
        return data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Problematic string (first 500 chars): {data_str[:500]}")
        print(f"Problematic string (last 500 chars): {data_str[-500:]}")
        raise


def map_candidate_to_id(label: str, candidates_mapping: Dict[str, str]) -> str:
    """
    Map a candidate label to their ID.
    
    Args:
        label: Candidate name from HTML (e.g., "Jordan Bardella")
        candidates_mapping: Dictionary mapping names to IDs
    
    Returns:
        Candidate ID (e.g., "JB") or raises error if not found
    """
    normalized = normalize_name(label)
    
    # Try direct match
    if normalized in candidates_mapping:
        return candidates_mapping[normalized]
    
    # Try case-insensitive match
    for name, cid in candidates_mapping.items():
        if name.lower() == normalized.lower():
            return cid
    
    # Not found
    raise ValueError(
        f"Candidate '{label}' not found in candidates.csv. "
        f"Please add them to candidates.csv with format: ID,FirstName,LastName,Party,,,"
    )


def convert_to_csv(data: List[Dict], output_file: Path, candidates_mapping: Dict[str, str], 
                   poll_type: str = "pt1", population: str = "all"):
    """
    Convert extracted data to CSV format.
    
    Args:
        data: List of candidate data dictionaries
        output_file: Path to output CSV file
        candidates_mapping: Dictionary mapping candidate names to IDs
        poll_type: Poll type ID (default: pt1 for IPSOS)
        population: Population segment (default: all)
    """
    print(f"Converting to CSV: {output_file}")
    
    # CSV header
    header = [
        "candidate_id",
        "intention_mention_1",
        "intention_mention_2", 
        "intention_mention_3",
        "intention_mention_4",
        "intention_mention_5",
        "intention_mention_6",
        "intention_mention_7",
        "poll_type_id",
        "population"
    ]
    
    rows = []
    unmapped_candidates = []
    
    for item in data:
        label = item.get("label", "")
        values = item.get("value", [])
        
        try:
            candidate_id = map_candidate_to_id(label, candidates_mapping)
            
            # Create row with values
            row = [candidate_id]
            
            # Add the 6 mention values (IPSOS has 6 mentions)
            for i in range(6):
                if i < len(values):
                    row.append(values[i])
                else:
                    row.append("")
            
            # Add empty 7th mention (IPSOS only has 6)
            row.append("")
            
            # Add poll type and population
            row.append(poll_type)
            row.append(population)
            
            rows.append(row)
            
        except ValueError as e:
            unmapped_candidates.append(label)
            print(f"Warning: {e}")
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    
    print(f"✓ Successfully wrote {len(rows)} candidates to {output_file}")
    
    if unmapped_candidates:
        print(f"\n⚠ Warning: {len(unmapped_candidates)} candidates were not mapped:")
        for candidate in unmapped_candidates:
            print(f"  - {candidate}")
        print("\nPlease add these candidates to candidates.csv with format:")
        print("  candidate_id,name,surname,parti,annonce_candidature,retrait_candidature,second_round")
        print("  NC,Nouveau,Candidat,Parti,,,")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python mining/mining_IPSOS/extract_ipsos_from_html.py <source_html_file> [output_csv_file]")
        print("\nExample:")
        print("  python mining/mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_202511/source.html polls/ipsos_202511/ipsos_202511_all.csv")
        sys.exit(1)
    
    html_file = Path(sys.argv[1])
    
    if not html_file.exists():
        print(f"Error: File '{html_file}' not found")
        sys.exit(1)
    
    # Determine output file
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        # Auto-generate output filename based on input
        output_file = html_file.parent / f"{html_file.parent.name}_all.csv"
    
    try:
        # Load candidates mapping from CSV
        candidates_mapping = load_candidates_mapping()
        
        # Extract data from HTML
        data = extract_data_from_html(html_file)
        
        # Convert to CSV
        convert_to_csv(data, output_file, candidates_mapping)
        
        print(f"\n✓ All done! CSV file created at: {output_file}")
        print(f"\nNext steps:")
        print(f"  1. Review the CSV file: {output_file}")
        print(f"  2. Add metadata to polls.csv")
        print(f"  3. Run merge.py to update the database")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
