# coding: utf-8

import pathlib
from typing import Dict
from candidate import Candidate


class Manager:
    def __init__(self):
        # Prénom d'abord
        self.candidates_first: Dict[str, Candidate] = {}
        # Nom d'abord
        self.candidates_last: Dict[str, Candidate] = {}

    def load_csv(self, filepath: pathlib.Path):
        with filepath.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines[1:]:  # Skip header
            parts = line.strip().split(",")
            if len(parts) >= 3:
                candidate = Candidate(id=parts[0], first_name=parts[1].strip(), last_name=parts[2].strip())
                first_name = candidate.first_name.lower()
                last_name = candidate.last_name.lower()
                self.candidates_first[first_name + " " + last_name] = candidate
                self.candidates_last[last_name + " " + first_name] = candidate

    def find_candidate(self, full_name: str) -> Candidate:
        result = None

        full_name = full_name.strip().lower()
        if full_name in self.candidates_first:
            result = self.candidates_first[full_name]
        elif full_name in self.candidates_last:
            result = self.candidates_last[full_name]

        return result
