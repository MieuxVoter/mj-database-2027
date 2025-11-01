# coding: utf-8

import pathlib
from typing import List
from poll import CandidatePollInterface

from manager import Manager


class Builder:
    def __init__(self, path_to_candidates: pathlib.Path, results: List[CandidatePollInterface]):
        self.path_to_candidates = path_to_candidates
        self.manager = Manager()
        self.manager.load_csv(self.path_to_candidates)

        self.results = results

        unknown_candidates = []

        # Vérification des candidats
        for result in self.results:
            candidate = self.manager.find_candidate(result.get_name())
            if candidate is None:
                unknown_candidates.append(result.get_name())

        if unknown_candidates:
            print(unknown_candidates)
            raise ValueError(
                f"Candidats inconnus : {', '.join(unknown_candidates)}. Veuillez compléter le fichier des candidats."
            )

    def write(self, output_path: pathlib.Path, poll_type: str, population: str):
        with output_path.open("w", encoding="utf-8") as f:
            # En-tête
            header = [
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
            f.write(",".join(header) + "\n")

            for result in self.results:
                candidate = self.manager.find_candidate(result.get_name())
                scores = result.get_scores()

                if len(scores) < 7:
                    scores.extend([""] * (7 - len(scores)))

                line = [candidate.id, *scores, poll_type, population]
                f.write(",".join(line) + "\n")
