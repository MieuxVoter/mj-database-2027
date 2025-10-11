import os
import pandas as pd

def test_poll_filename_format():

    for item in os.listdir('polls/'):
        item_path = os.path.join('polls/', item)

        if os.path.isdir(item_path):

            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)

                if os.path.isfile(file_path):

                    assert '_' in file, f"Nom de fichier invalide dans {item}/ : {file}"

                    assert file.endswith('.csv'), f"Extension invalide dans {item}/ : {file}"


def test_poll_references_valid_candidates():

    candidates = pd.read_csv('candidates.csv')['candidate_id'].tolist()

    for item in os.listdir('polls/'):
        item_path = os.path.join('polls/', item)

        if os.path.isdir(item_path):
            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)

                if os.path.isfile(file_path) and file.endswith('.csv'):
                    df = pd.read_csv(file_path)

                    for candidate_ref in df['candidate_id']:  
                        assert candidate_ref in candidates, \
                            f"Candidat invalide '{candidate_ref}' dans {file_path}"