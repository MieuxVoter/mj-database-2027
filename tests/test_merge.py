# tests/test_merge.py
import os
from conftest import verify_files_exist, load_valid_candidates, verify_file_not_empty, verify_no_duplicates, verify_candidate_references, verify_columns, get_expected_columns, EXPECTED_FILES

def test_poll_mergeable_with_main(merged_env):
    """Vérifie que merge.py s'exécute et génère les fichiers attendus."""
    verify_files_exist(merged_env)

def test_poll_data_consistency(merged_env):
    """Vérifie la cohérence des données après merging."""
    candidates = load_valid_candidates(merged_env)

    for file in EXPECTED_FILES:
        file_path = os.path.join(merged_env.name, file)
        if not os.path.exists(file_path):
            print(f"⚠️ {file} n'existe pas.")
            continue

        df = verify_file_not_empty(file_path, file)
        verify_no_duplicates(df, file)
        verify_candidate_references(df, candidates, file)

        expected_columns = get_expected_columns(file)
        verify_columns(df, expected_columns, file_path)

        print(f"✅ {file} est valide.")
