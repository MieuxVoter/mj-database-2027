import os
import pandas as pd
import pytest


def get_poll_files():
    """Récupère tous les fichiers CSV de sondages dans polls/"""
    polls_dir = "polls"
    csv_files_list = []

    for folder_name in sorted(os.listdir(polls_dir)):
        folder_path = os.path.join(polls_dir, folder_name)
        if os.path.isdir(folder_path):
            # Get all CSV files in this folder
            csv_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(".csv")])
            for csv_file in csv_files:
                csv_path = os.path.join(folder_path, csv_file)
                csv_files_list.append(csv_path)

    return csv_files_list


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
            csv_files = [f for f in os.listdir(item_path) if f.lower().endswith(".csv")]

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


@pytest.mark.parametrize("csv_path", get_poll_files())
def test_poll_percentages_sum_to_100(csv_path):
    """Vérifie que la somme des pourcentages vaut 100 pour chaque ligne d'un fichier CSV de sondage"""
    errors = []

    try:
        df = pd.read_csv(csv_path)

        # Find all columns that start with "intention_mention_"
        intention_cols = [col for col in df.columns if col.startswith("intention_mention_")]

        if not intention_cols:
            # Skip files without intention_mention columns
            return

        # Check each row
        for idx, row in df.iterrows():
            # Calculate the sum of percentage values
            percentage_sum = row[intention_cols].sum()

            # Check if sum equals 100
            if percentage_sum != 100:
                candidate_id = row.get(
                    "candidate_id", f"row {idx + 2}"
                )  # +2 because idx is 0-based and there's a header
                errors.append(
                    f"  Ligne {idx + 2} (candidate: {candidate_id}): " f"somme = {percentage_sum}% (attendu: 100%)"
                )

    except Exception as e:
        errors.append(f"  Erreur lors de la lecture: {str(e)}")

    assert not errors, f"Lignes avec des sommes incorrectes dans {csv_path}:\n" + "\n".join(errors)


@pytest.mark.parametrize("csv_path", get_poll_files())
def test_poll_mentions_alignment(csv_path):
    """Vérifie que le nombre de colonnes 'intention_mention' remplies correspond au type de sondage"""

    # Load poll types
    try:
        poll_types = pd.read_csv("poll_types.csv").set_index("id")
    except FileNotFoundError:
        pytest.fail("Fichier poll_types.csv introuvable")

    try:
        df = pd.read_csv(csv_path)

        if df.empty:
            return

        # Check if poll_type_id exists
        if "poll_type_id" not in df.columns:
            pytest.fail(f"Colonne 'poll_type_id' manquante dans {csv_path}")

        # Get poll type for this file (assuming all rows have same type, check first one)
        poll_type_id = df["poll_type_id"].iloc[0]

        if poll_type_id not in poll_types.index:
            pytest.fail(f"Type de sondage inconnu: {poll_type_id} dans {csv_path}")

        # Check that all 7 mention columns exist
        for i in range(1, 8):
            col_name = f"intention_mention_{i}"
            if col_name not in df.columns:
                pytest.fail(
                    f"Colonne manquante dans {csv_path}: {col_name} (tous les fichiers doivent avoir 7 colonnes mentions)"
                )

        expected_mentions = poll_types.loc[poll_type_id, "nombre_mentions"]

        # Count filled intention_mention columns
        intention_cols = [f"intention_mention_{i}" for i in range(1, 8)]

        filled_cols_count = 0
        for col in intention_cols:
            # Check if column has any non-null value
            # We consider a column filled if it has at least one non-NaN value
            if df[col].notna().any():
                filled_cols_count += 1

        assert (
            filled_cols_count == expected_mentions
        ), f"Fichier {csv_path} (type {poll_type_id}): {filled_cols_count} colonnes remplies, attendu {expected_mentions}"

    except Exception as e:
        pytest.fail(f"Erreur lors de l'analyse de {csv_path}: {str(e)}")
