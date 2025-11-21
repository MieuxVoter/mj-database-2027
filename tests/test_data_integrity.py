import os
import pandas as pd


def test_candidates_no_duplicate_acronyms():
    df = pd.read_csv("candidates.csv")
    duplicates = df[df.duplicated("candidate_id", keep=False)]

    assert duplicates.empty, f"Doublons d'acronymes détectés : {duplicates['candidate_id'].tolist()}"


def test_poll_types_unique_ids():
    df = pd.read_csv("poll_types.csv")
    duplicates = df[df.duplicated("id", keep=False)]

    assert duplicates.empty, f"Doublons d'IDs détectés : {duplicates['id'].tolist()}"


def test_poll_folders_declared_in_polls_csv():
    """Vérifie que tous les dossiers dans polls/ sont déclarés dans polls.csv"""
    # Get all folders in polls/ directory
    polls_dir = "polls"
    actual_folders = set()
    for item in os.listdir(polls_dir):
        item_path = os.path.join(polls_dir, item)
        # print(f"item_path: {item_path}")

        if os.path.isdir(item_path):
            # Use forward slash to match the format in polls.csv
            csv_files = [
                f for f in os.listdir(item_path)
                if f.lower().endswith(".csv")
            ]

            if csv_files:
                actual_folders.add(f"{polls_dir}/{item}")

    # Get all folders declared in polls.csv
    df = pd.read_csv("polls.csv")
    declared_folders = set(df["folder"].unique())

    # Find folders that exist but are not declared
    missing_in_csv = actual_folders - declared_folders

    assert not missing_in_csv, f"Dossiers non déclarés dans polls.csv : {sorted(missing_in_csv)}"


def test_poll_csv_filenames_match_poll_ids():
    """Vérifie que les noms des fichiers CSV dans les dossiers correspondent aux poll_ids déclarés dans polls.csv"""
    df = pd.read_csv("polls.csv")
    polls_dir = "polls"

    # Group poll_ids by folder
    folder_to_poll_ids = {}
    for _, row in df.iterrows():
        folder = row["folder"]
        poll_id = row["poll_id"]
        if folder not in folder_to_poll_ids:
            folder_to_poll_ids[folder] = set()
        folder_to_poll_ids[folder].add(poll_id)

    errors = []

    # Check each folder
    for folder_path, expected_poll_ids in folder_to_poll_ids.items():
        if not os.path.isdir(folder_path):
            continue

        # Get all CSV files in the folder
        csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

        # Extract poll_id prefixes from CSV filenames
        # Expected format: {poll_id}_{suffix}.csv
        for csv_file in csv_files:
            # Get the prefix before the first underscore after poll_id
            # e.g., "elabe_202407_all.csv" -> check if it starts with "elabe_202407"
            found_match = False
            for expected_poll_id in expected_poll_ids:
                if csv_file.startswith(f"{expected_poll_id}_"):
                    found_match = True
                    break

            if not found_match:
                errors.append(
                    f"Fichier '{csv_file}' dans {folder_path} ne correspond à aucun poll_id déclaré: {sorted(expected_poll_ids)}"
                )

    assert not errors, f"Erreurs de correspondance des fichiers CSV:\n" + "\n".join(errors)
