# tests/conftest.py
import pytest
import os
import tempfile
import shutil
import subprocess
import pandas as pd

# Constantes globales
EXPECTED_FILES = [
    'mj2027.csv',
    'mj2027_left.csv',
    'mj2027_farright.csv',
    'mj2027_macron.csv',
    'mj2027_absentionists.csv'
]

EXPECTED_COLUMNS_DIC = {
    "full": [
        'candidate_id', 'intention_mention_1', 'intention_mention_2', 'intention_mention_3',
        'intention_mention_4', 'intention_mention_5', 'intention_mention_6', 'intention_mention_7',
        'poll_type_id', 'population', 'poll_id', 'poll_type', 'nb_people', 'start_date',
        'end_date', 'folder', 'population', 'id', 'institut', 'commanditaire', 'mention1', 'mention2',
        'mention3', 'mention4', 'mention5', 'mention6', 'mention7', 'nombre_mentions',
        'question', 'name', 'surname', 'parti', 'annonce_candidature', 'retrait_candidature',
        'second_round', 'candidate'
    ],
    "restricted": [
        'candidate_id', 'intention_mention_1', 'intention_mention_2', 'intention_mention_3',
        'poll_type_id', 'population', 'poll_id', 'poll_type', 'nb_people', 'start_date',
        'end_date', 'folder', 'id', 'institut', 'commanditaire', 'mention1', 'mention2',
        'mention3', 'nombre_mentions', 'question', 'name', 'surname', 'parti',
        'annonce_candidature', 'retrait_candidature', 'second_round'
    ]
}

# Fixtures
@pytest.fixture
def temp_env():
    """Fixture pour créer un environnement temporaire"""
    temp_dir = tempfile.TemporaryDirectory()
    shutil.copytree('.', temp_dir.name, dirs_exist_ok=True)
    yield temp_dir
    temp_dir.cleanup()  

@pytest.fixture
def merged_env(temp_env):
    """Fixture pour un environnement où merge.py a été exécuté"""
    result = subprocess.run(
        ['python', 'merge.py'],
        cwd=temp_env.name,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"merge.py a échoué: {result.stderr}"
    return temp_env

# Fonctions utilitaires
def verify_files_exist(temp_dir, 
                       expected_files=EXPECTED_FILES
                       ):
    """Vérifie que les fichiers attendus existent dans le dossier temporaire"""
    for file in expected_files:
        assert os.path.exists(os.path.join(temp_dir.name, file)), f"Fichier manquant: {file}"

def load_valid_candidates(temp_dir):
    """Charge la liste des candidats valides depuis candidates.csv"""
    return pd.read_csv(os.path.join(temp_dir.name, 'candidates.csv'))['candidate_id'].tolist()

def verify_file_not_empty(file_path, 
                          file_name
                          ):
    """Vérifie qu'un fichier n'est pas vide"""
    df = pd.read_csv(file_path)
    assert not df.empty, f"Fichier vide: {file_name}"
    return df

def verify_no_duplicates(df, 
                         file_name
                         ):
    """Vérifie qu'il n'y a pas de doublons dans un DataFrame"""
    assert not df.duplicated().any(), f"Des doublons ont été détectés dans {file_name}"

def verify_candidate_references(df, 
                                candidates, 
                                file_name
                                ):
    """Vérifie que toutes les références aux candidats sont valides"""
    for candidate_id in df['candidate_id']:
        assert candidate_id in candidates, f"Candidat invalide '{candidate_id}' détecté dans {file_name}"

def verify_columns(df, 
                   expected_columns, 
                   file_path
                   ):
    """Vérifie que toutes les colonnes attendues existent et qu'il n'y a pas de colonnes supplémentaires"""
    missing_columns = set(expected_columns) - set(df.columns)
    extra_columns = set(df.columns) - set(expected_columns)
    assert not missing_columns, f"Colonnes manquantes dans {file_path}: {sorted(missing_columns)}"
    assert not extra_columns, f"Colonnes supplémentaires dans {file_path}: {sorted(extra_columns)}"

def get_expected_columns(file_name):
    """Retourne la liste des colonnes attendues pour un fichier donné"""
    if file_name == 'mj2027.csv':
        return EXPECTED_COLUMNS_DIC['full']
    else:
        return EXPECTED_COLUMNS_DIC['restricted']
