#!/usr/bin/env python3
"""
Validation script for poll data files.
Checks CSV files for common errors before merging into the main database.
"""

import csv
import sys
from pathlib import Path
from typing import List, Tuple


def validate_csv_structure(csv_file: Path) -> List[str]:
    """Check if CSV has the correct structure."""
    errors = []

    expected_headers = [
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

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if headers != expected_headers:
                errors.append(f"Invalid headers. Expected: {expected_headers}, Got: {headers}")

            # Check each row
            for i, row in enumerate(reader, start=2):  # Start at 2 (after header)
                # Check candidate_id is not empty
                if not row.get("candidate_id", "").strip():
                    errors.append(f"Line {i}: Empty candidate_id")

                # Check poll_type_id
                poll_type = row.get("poll_type_id", "").strip()
                if not poll_type:
                    errors.append(f"Line {i}: Empty poll_type_id")
                elif not poll_type.startswith("pt"):
                    errors.append(f"Line {i}: Invalid poll_type_id '{poll_type}' (should start with 'pt')")

                # Check population
                population = row.get("population", "").strip()
                valid_populations = ["all", "left", "macron", "farright", "absentionists"]
                if population not in valid_populations:
                    errors.append(f"Line {i}: Invalid population '{population}' (should be one of {valid_populations})")

                # Check at least one mention has a value
                mentions = [row.get(f"intention_mention_{j}", "").strip() for j in range(1, 8)]
                if all(not m for m in mentions):
                    errors.append(f"Line {i}: No mention values for candidate {row.get('candidate_id')}")

                # Check mention values are numeric where present
                for j, mention in enumerate(mentions, start=1):
                    if mention:
                        try:
                            value = float(mention)
                            if value < 0 or value > 100:
                                errors.append(f"Line {i}: Mention {j} value {value} is out of range [0, 100]")
                        except ValueError:
                            errors.append(f"Line {i}: Mention {j} value '{mention}' is not numeric")

    except FileNotFoundError:
        errors.append(f"File not found: {csv_file}")
    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return errors


def validate_candidate_ids(csv_file: Path, candidates_csv: Path = Path("candidates.csv")) -> List[str]:
    """Check if all candidate IDs exist in candidates.csv."""
    errors = []

    # Load valid candidate IDs
    valid_ids = set()
    try:
        with open(candidates_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                valid_ids.add(row["candidate_id"])
    except Exception as e:
        return [f"Error reading candidates.csv: {e}"]

    # Check CSV candidate IDs
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):
                candidate_id = row.get("candidate_id", "").strip()
                if candidate_id and candidate_id not in valid_ids:
                    errors.append(f"Line {i}: Unknown candidate_id '{candidate_id}' (not in candidates.csv)")
    except Exception as e:
        errors.append(f"Error validating candidate IDs: {e}")

    return errors


def validate_percentages(csv_file: Path, tolerance: float = 5.0) -> List[str]:
    """Check if mention percentages roughly sum to 100% (with tolerance)."""
    warnings = []

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):
                mentions = []
                for j in range(1, 8):
                    value = row.get(f"intention_mention_{j}", "").strip()
                    if value:
                        try:
                            mentions.append(float(value))
                        except ValueError:
                            pass  # Already caught by structure validation

                if mentions:
                    total = sum(mentions)
                    if abs(total - 100) > tolerance:
                        warnings.append(
                            f"Line {i}: Mention sum is {total:.1f}% "
                            f"(expected ~100% ±{tolerance}%) for {row.get('candidate_id')}"
                        )
    except Exception as e:
        warnings.append(f"Error validating percentages: {e}")

    return warnings


def validate_poll_metadata(poll_folder: Path) -> List[str]:
    """Check if poll folder structure is correct."""
    errors = []

    if not poll_folder.exists():
        return [f"Poll folder does not exist: {poll_folder}"]

    if not poll_folder.is_dir():
        return [f"Poll path is not a directory: {poll_folder}"]

    # Check for at least one CSV file
    csv_files = list(poll_folder.glob("*.csv"))
    if not csv_files:
        errors.append(f"No CSV files found in {poll_folder}")

    return errors


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python mining/mining_IPSOS/validate_poll.py <poll_csv_file> [--strict]")
        print("\nExample:")
        print("  python mining/mining_IPSOS/validate_poll.py polls/ipsos_202511/ipsos_202511_all.csv")
        print("\nOptions:")
        print("  --strict    Treat warnings as errors")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    strict = "--strict" in sys.argv

    print(f"Validating: {csv_file}")
    print("=" * 60)

    # Run all validations
    all_errors = []
    all_warnings = []

    # 1. Structure validation
    print("\n1. Checking CSV structure...")
    errors = validate_csv_structure(csv_file)
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ CSV structure is valid")

    # 2. Candidate ID validation
    print("\n2. Checking candidate IDs...")
    errors = validate_candidate_ids(csv_file)
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ All candidate IDs are valid")

    # 3. Percentage validation (warnings only)
    print("\n3. Checking percentage sums...")
    warnings = validate_percentages(csv_file)
    if warnings:
        all_warnings.extend(warnings)
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        print("  ✓ All percentages sum correctly")

    # 4. Folder validation
    print("\n4. Checking poll folder...")
    poll_folder = csv_file.parent
    errors = validate_poll_metadata(poll_folder)
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ Poll folder structure is valid")

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if all_errors:
        print(f"\n✗ Found {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)

    if all_warnings:
        print(f"\n⚠ Found {len(all_warnings)} warning(s):")
        for warning in all_warnings:
            print(f"  - {warning}")

        if strict:
            print("\n✗ Validation failed (strict mode)")
            sys.exit(1)
        else:
            print("\n✓ Validation passed with warnings")
            sys.exit(0)

    print("\n✓ All validations passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
