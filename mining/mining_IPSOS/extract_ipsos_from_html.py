#!/usr/bin/env python3
"""
Script to extract IPSOS poll data from HTML source files and convert to CSV format.
Usage: python extract_ipsos_from_html.py <source_html_file> <output_csv_file>
"""

import json
import re
import sys
import csv
import codecs
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


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
        with open(candidates_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create full name from name and surname
                name = row.get("name", "").strip()
                surname = row.get("surname", "").strip()
                candidate_id = row.get("candidate_id", "").strip()

                if name and surname and candidate_id:
                    # Remove comma from name if present (e.g., "François, Rebsamen")
                    name = name.replace(",", "")
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


def extract_metadata_from_html(html_file: Path) -> Dict[str, Optional[str]]:
    """
    Extract poll metadata from HTML file (sample size, source, etc.).

    Note: Survey dates are typically NOT included in Flourish HTML exports
    and must be added manually to polls.csv.

    Returns:
        Dictionary with metadata keys: 'sample_size', 'source', 'footer_note'
    """
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    metadata: Dict[str, Optional[str]] = {
        "sample_size": None,
        "source": None,
        "footer_note": None,
        "start_date": None,
        "end_date": None,
    }

    # Extract footer note (contains sample size info)
    footer_pattern = r'"layout\.footer_note":\s*"([^"]+)"'
    footer_match = re.search(footer_pattern, content)

    if footer_match:
        try:
            footer = footer_match.group(1)
            # Decode unicode escapes like \u003c
            footer_decoded = codecs.decode(footer, "unicode_escape")
            # Remove HTML tags
            footer_clean = re.sub(r"<[^>]+>", "", footer_decoded)
            metadata["footer_note"] = footer_clean.strip()

            # Extract sample size (N=1000, n=1000, échantillon de 1000, 1000 personnes)
            sample_match = re.search(
                r"(?:[Nn]|n)\s*=\s*(\d+)|(?:échantillon(?:\s+de)?|sample(?:\s+size)?(?:\s+de)?)\s*(?:de\s*)?(\d+)|(?:(\d+)\s*personnes)",
                footer_clean,
                re.IGNORECASE,
            )
            if sample_match:
                # sample_match may have multiple groups - pick the first non-empty
                sample = next((g for g in sample_match.groups() if g), None)
                if sample:
                    metadata["sample_size"] = sample
        except:
            pass

    # Extract source/title info
    source_patterns = [
        r'"layout\.header_title":\s*"([^"]+)"',
        r'"layout\.footer_note_secondary":\s*"([^"]+)"',
    ]

    for pattern in source_patterns:
        source_match = re.search(pattern, content)
        if source_match and source_match.group(1):
            try:
                source = source_match.group(1)
                source_decoded = codecs.decode(source, "unicode_escape")
                source_clean = re.sub(r"<[^>]+>", "", source_decoded).strip()
                if source_clean and not metadata["source"]:
                    metadata["source"] = source_clean
            except:
                pass

    # Try to extract survey dates from footer or content
    # 1) ISO dates: 2025-11-06 or 2025/11/06
    iso_range = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})(?:\s*(?:to|\-|–|au|à|and)\s*(\d{4}[-/]\d{2}[-/]\d{2}))?", content)
    if iso_range:
        try:
            start = iso_range.group(1).replace("/", "-")
            metadata["start_date"] = datetime.fromisoformat(start).date().isoformat()
            if iso_range.group(2):
                end = iso_range.group(2).replace("/", "-")
                metadata["end_date"] = datetime.fromisoformat(end).date().isoformat()
            else:
                metadata["end_date"] = metadata["start_date"]
            return metadata
        except Exception:
            pass

    # 2) dd/mm/YYYY or d/m/YYYY patterns
    dm_range = re.search(
        r"(\d{1,2}[\/\\]\d{1,2}[\/\\]\d{4})(?:\s*(?:to|\-|–|au|à|and)\s*(\d{1,2}[\/\\]\d{1,2}[\/\\]\d{4}))?", content
    )
    if dm_range:
        try:
            s = dm_range.group(1).replace("\\", "/")
            metadata["start_date"] = datetime.strptime(s, "%d/%m/%Y").date().isoformat()
            if dm_range.group(2):
                e = dm_range.group(2).replace("\\", "/")
                metadata["end_date"] = datetime.strptime(e, "%d/%m/%Y").date().isoformat()
            else:
                metadata["end_date"] = metadata["start_date"]
            return metadata
        except Exception:
            pass

    # 3) French textual dates like 'du 6 au 7 novembre 2025' or '6-7 novembre 2025' or '6 et 7 novembre 2025'
    # month mapping
    months = {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12,
    }
    fr_range = re.search(
        r"du\s*(\d{1,2})\s*(?:au|à|a|et|-)\s*(\d{1,2})\s+([A-Za-zéûàôç]+)\s*(\d{4})",
        footer_clean or content,
        re.IGNORECASE,
    )
    if fr_range:
        try:
            d1 = int(fr_range.group(1))
            d2 = int(fr_range.group(2))
            month_name = fr_range.group(3).lower()
            year = int(fr_range.group(4))
            m = months.get(month_name)
            if m:
                metadata["start_date"] = datetime(year, m, d1).date().isoformat()
                metadata["end_date"] = datetime(year, m, d2).date().isoformat()
                return metadata
        except Exception:
            pass

    # 4) single day like '6 novembre 2025'
    single_fr = re.search(r"(\d{1,2})\s+([A-Za-zéûàôç]+)\s*(\d{4})", footer_clean or content, re.IGNORECASE)
    if single_fr:
        try:
            d = int(single_fr.group(1))
            month_name = single_fr.group(2).lower()
            year = int(single_fr.group(3))
            m = months.get(month_name)
            if m:
                metadata["start_date"] = datetime(year, m, d).date().isoformat()
                metadata["end_date"] = metadata["start_date"]
        except Exception:
            pass

    return metadata


def extract_data_from_html(html_file: Path) -> List[Dict]:
    """
    Extract the data array from HTML file.

    Returns:
        List of dictionaries with 'label' and 'value' keys
    """
    print(f"Reading HTML file: {html_file}")

    with open(html_file, "r", encoding="utf-8") as f:
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
            if content[end_idx] == "[":
                bracket_count += 1
            elif content[end_idx] == "]":
                bracket_count -= 1
            end_idx += 1

        data_str = "[" + content[start_idx : end_idx - 1] + "]"
    else:
        data_str = "[" + matches.group(1) + "]"

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


def convert_to_csv(
    data: List[Dict],
    output_file: Path,
    candidates_mapping: Dict[str, str],
    poll_type: str = "pt1",
    population: str = "all",
):
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
        "population",
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
    with open(output_file, "w", newline="", encoding="utf-8") as f:
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


def infer_dates_from_folder(folder_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Infer survey dates from folder name like 'ipsos_202511' or 'elabe_202412'.
    Assumes format: <institute>_YYYYMM

    Returns start_date and end_date in ISO format, or (None, None) if cannot parse.
    Uses mid-month (15th) as a reasonable default.
    """
    match = re.search(r"(\d{4})(\d{2})", folder_name)
    if match:
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            # Use middle of the month as default survey date
            day = 15
            # Check if valid date
            date_obj = datetime(year, month, day)
            start_date = date_obj.date().isoformat()
            # Assume 1-day survey by default
            end_date = start_date
            return start_date, end_date
        except (ValueError, OverflowError):
            pass
    return None, None


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python mining/mining_IPSOS/extract_ipsos_from_html.py <source_html_file> [output_csv_file]")
        print("\nExample:")
        print(
            "  python mining/mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_202511/source.html polls/ipsos_202511/ipsos_202511_all.csv"
        )
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

        # Extract metadata from HTML
        print("\n" + "=" * 80)
        print("EXTRACTING METADATA")
        print("=" * 80)
        metadata = extract_metadata_from_html(html_file)

        # If dates not found in HTML, infer from folder name
        if not metadata["start_date"] or not metadata["end_date"]:
            inferred_start, inferred_end = infer_dates_from_folder(html_file.parent.name)
            if inferred_start:
                metadata["start_date"] = inferred_start
                metadata["end_date"] = inferred_end
                print(f"⚠ Survey dates inferred from folder name: {inferred_start} to {inferred_end}")
                print(f"  (Using mid-month default. Verify with original source if needed.)")

        if metadata["sample_size"]:
            print(f"✓ Sample size: {metadata['sample_size']} personnes")
        else:
            print("⚠ Sample size: Not found in HTML")

        if metadata["source"]:
            print(f"✓ Source: {metadata['source']}")
        else:
            print("⚠ Source: Not found in HTML")

        if metadata["start_date"] and metadata["end_date"]:
            print(f"✓ Survey dates: {metadata['start_date']} to {metadata['end_date']}")
        else:
            print("⚠ Survey dates: Could not determine from HTML or folder name")

        # Generate polls.csv entry suggestion
        poll_id = html_file.parent.name
        poll_type = "pt1"  # IPSOS uses pt1 (6 mentions)
        nb_people = metadata["sample_size"] or "1000"
        start_date = metadata["start_date"] or "YYYY-MM-DD"
        end_date = metadata["end_date"] or "YYYY-MM-DD"
        folder = html_file.parent
        population = "all"

        polls_csv_entry = f"{poll_id},{poll_type},{nb_people},{start_date},{end_date},{folder},{population}"

        print("\n" + "=" * 80)
        print("UPDATING POLLS.CSV")
        print("=" * 80)

        # Check if entry already exists in polls.csv
        polls_csv_path = Path("polls.csv")
        entry_exists = False

        if polls_csv_path.exists():
            with open(polls_csv_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
                if poll_id in existing_content:
                    entry_exists = True

        if entry_exists:
            print(f"⚠ Entry for {poll_id} already exists in polls.csv")
            print(f"  Suggested entry: {polls_csv_entry}")
            print(f"  Skipping to avoid duplicates.")
        else:
            # Append to polls.csv
            with open(polls_csv_path, "a", encoding="utf-8") as f:
                f.write(f"{polls_csv_entry}\n")
            print(f"✓ Added entry to polls.csv:")
            print(f"  {polls_csv_entry}")
            if metadata["start_date"]:
                print(
                    "\n⚠ Note: Survey dates were inferred from folder name. Please verify with the original IPSOS report."
                )
            else:
                print("\n⚠ IMPORTANT: Update polls.csv with actual survey dates from the IPSOS report.")

        # Extract data from HTML
        print("\n" + "=" * 80)
        print("EXTRACTING CANDIDATE DATA")
        print("=" * 80)
        data = extract_data_from_html(html_file)

        # Convert to CSV
        convert_to_csv(data, output_file, candidates_mapping)

        print(f"\n✓ All done! CSV file created at: {output_file}")
        print(f"\nNext steps:")
        print(f"  1. Review the CSV file: {output_file}")
        print(f"  2. Verify survey dates in polls.csv if needed")
        print(f"  3. Run merge.py to update the database")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
