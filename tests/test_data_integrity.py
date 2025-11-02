import os
import pandas as pd


def test_candidates_no_duplicate_acronyms():
    df = pd.read_csv("candidates.csv")
    duplicates = df[df.duplicated("candidate_id", keep=False)]

    assert duplicates.empty, f"Doublons d'acronymes détectés : {duplicates['acronyme'].tolist()}"


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
        if os.path.isdir(item_path):
            # Use forward slash to match the format in polls.csv
            actual_folders.add(f"{polls_dir}/{item}")
    
    # Get all folders declared in polls.csv
    df = pd.read_csv("polls.csv")
    declared_folders = set(df["folder"].unique())
    
    # Find folders that exist but are not declared
    missing_in_csv = actual_folders - declared_folders
    
    assert not missing_in_csv, f"Dossiers non déclarés dans polls.csv : {sorted(missing_in_csv)}"
