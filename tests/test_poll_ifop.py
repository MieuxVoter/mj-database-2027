import pathlib

import pandas as pd

_PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent


def test_pt3_all_sums():
    """Vérification des sommes pour les sondages pt3 - all"""

    # Chargement du fichier polls.csv
    polls_df = pd.read_csv("polls.csv")

    polls = []
    for _, row in polls_df.iterrows():
        if row.loc["poll_type"] != "pt3" or row.loc["population"] != "all":
            continue

        poll_path = _PROJECT_DIR / row.loc["folder"] / (row.loc["poll_id"] + "_all.csv")
        assert poll_path.exists(), f"Le sondage {poll_path} n'existe pas"
        polls.append(poll_path)

    for poll in polls:
        poll_df = pd.read_csv(poll)

        for _, row in poll_df.iterrows():
            poll_error_message = f"Dans sondage {poll.name} : pour {row.loc['candidate_id']},"

            sum = 0

            for i in range(1, 7):
                col = f"intention_mention_{i}"
                sum += row.loc[col]

            assert sum == 100, f"{poll_error_message} somme incohérente = {sum}"
