import re
from pathlib import Path
from pdfminer.high_level import extract_text
import json
import argparse
import sys
import csv


def extract_metadata(pdf_path):
    try:
        text = extract_text(str(pdf_path), page_numbers=[0, 1, 2])
    except Exception as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        return None

    text = re.sub(r"\s+", " ", text)
    metadata = {}

    # Sample Size
    sample_match = re.search(r"Echantillon de\s*([\d\s]+)\s*personnes", text, re.IGNORECASE)
    if sample_match:
        metadata["sample_size"] = int(sample_match.group(1).replace(" ", ""))
    else:
        match = re.search(r"(\d[\d\s]*)\s*personnes.*?représentatif", text, re.IGNORECASE)
        if match:
            metadata["sample_size"] = int(match.group(1).replace(" ", ""))

    # Dates
    # Pattern: "Interrogation par internet du 6 au 7 janvier 2026"
    date_match = re.search(r"Interrogation par internet du\s*(.*?20\d{2})", text, re.IGNORECASE)
    if date_match:
        date_str = date_match.group(1)  # "6 au 7 janvier 2026"
        metadata["raw_date"] = date_str

        months = {
            "janvier": "01",
            "février": "02",
            "mars": "03",
            "avril": "04",
            "mai": "05",
            "juin": "06",
            "juillet": "07",
            "août": "08",
            "aout": "08",
            "septembre": "09",
            "octobre": "10",
            "novembre": "11",
            "décembre": "12",
        }

        # Regex for "d1 au d2 month year"
        m1 = re.search(r"(\d+)\s*au\s*(\d+)\s*([a-zA-Zéû]+)\s*(\d{4})", date_str, re.IGNORECASE)
        if m1:
            day_start, day_end, month_name, year = m1.groups()
            month_key = month_name.lower()
            if month_key in months:
                metadata["start_date"] = f"{year}-{months[month_key]}-{int(day_start):02d}"
                metadata["end_date"] = f"{year}-{months[month_key]}-{int(day_end):02d}"

        # Regex for "d1 et d2 month year"
        if "start_date" not in metadata:
            m2 = re.search(r"(\d+)\s*et\s*(\d+)\s*([a-zA-Zéû]+)\s*(\d{4})", date_str, re.IGNORECASE)
            if m2:
                day_start, day_end, month_name, year = m2.groups()
                month_key = month_name.lower()
                if month_key in months:
                    metadata["start_date"] = f"{year}-{months[month_key]}-{int(day_start):02d}"
                    metadata["end_date"] = f"{year}-{months[month_key]}-{int(day_end):02d}"

    return metadata


def update_polls_csv(polls_csv_path, poll_id, metadata):
    if not metadata or "sample_size" not in metadata or "start_date" not in metadata:
        print("Missing metadata, cannot update polls.csv")
        return False

    rows_to_add = []
    populations = ["all", "left", "macron", "absentionists", "farright"]

    # Check if poll_id exists
    existing_poll_ids = set()
    if polls_csv_path.exists():
        with open(polls_csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_poll_ids.add(row["poll_id"])

    if poll_id in existing_poll_ids:
        print(f"Poll {poll_id} already in polls.csv")
        return False

    # Prepare rows
    # Columns: poll_id,poll_type,nb_people,start_date,end_date,folder,population,pdf_url
    for pop in populations:
        row = [
            poll_id,
            "pt2",
            str(metadata["sample_size"]),
            metadata["start_date"],
            metadata["end_date"],
            f"polls/{poll_id}",
            pop,
            "",  # pdf_url empty based on user example
        ]
        rows_to_add.append(row)

    # Append to file
    with open(polls_csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_add)

    print(f"Added {len(rows_to_add)} rows to polls.csv")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--update-csv", type=Path, help="Path to polls.csv to update")
    parser.add_argument("--poll-id", type=str, help="Poll ID (required if updating CSV)")

    args = parser.parse_args()

    data = extract_metadata(args.pdf_path)
    print(json.dumps(data, indent=2))

    if args.update_csv and args.poll_id:
        if data:
            update_polls_csv(args.update_csv, args.poll_id, data)
        else:
            print("Failed to extract metadata")
            sys.exit(1)
