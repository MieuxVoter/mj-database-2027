import pandas as pd

def test_candidates_no_duplicate_acronyms():
    df = pd.read_csv('candidates.csv')
    duplicates = df[df.duplicated('candidate_id', 
                                  keep=False
                                  )]
    
    assert duplicates.empty, f"Doublons d'acronymes détectés : {duplicates['acronyme'].tolist()}"

def test_poll_types_unique_ids():
    df = pd.read_csv('poll_types.csv')
    duplicates = df[df.duplicated('id', 
                                  keep=False
                                  )]
    
    assert duplicates.empty, f"Doublons d'IDs détectés : {duplicates['id'].tolist()}"
