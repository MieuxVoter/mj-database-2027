import pandas as pd
import pytest

required_files = ['candidates.csv', 
                      'polls.csv', 
                      'poll_types.csv'
                      ]

def test_csv_files_exist():
    
    for file in required_files:
        assert pd.read_csv(file) is not None, f"Fichier {file} manquant ou invalide"

def test_csv_encoding():
    
    for file in required_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                f.read() 
        except UnicodeDecodeError:
            raise AssertionError(f"Le fichier {file} n'est pas encodé en UTF-8")

