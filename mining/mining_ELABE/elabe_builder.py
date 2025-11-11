# coding: utf-8
"""
Builder pour générer les CSV ELABE depuis les données extraites.

Ce builder adapte l'architecture IFOP pour ELABE:
- Format ELABE : 5 colonnes (très positive, plutôt positive, plutôt négative, très négative, sans opinion)
- Poll type : pt2
- 5 populations : all, left, macron, farright, absentionists
"""

import pathlib
import sys
from typing import List

# Importer depuis mining_IFOP
ifop_path = pathlib.Path(__file__).parent.parent / "mining_IFOP"
sys.path.insert(0, str(ifop_path))
from poll import CandidatePollInterface
from manager import Manager


class ElabeBuilder:
    """
    Construit les CSV ELABE à partir des données extraites.
    
    Format de sortie:
    candidate_id,intention_mention_1-5,intention_mention_6,intention_mention_7,poll_type_id,population
    
    Pour ELABE:
    - intention_mention_1 : Image très positive (%)
    - intention_mention_2 : Image plutôt positive (%)
    - intention_mention_3 : Image plutôt négative (%)
    - intention_mention_4 : Image très négative (%)
    - intention_mention_5 : Sans opinion (%)
    - intention_mention_6 : vide (non utilisé par ELABE)
    - intention_mention_7 : vide (non utilisé par ELABE)
    - poll_type_id : pt2 (baromètre politique)
    - population : all, left, macron, farright, absentionists
    """
    
    def __init__(self, path_to_candidates: pathlib.Path, results: List[CandidatePollInterface]):
        """
        Initialise le builder.
        
        Args:
            path_to_candidates: Chemin vers candidates.csv
            results: Liste des ElabeLine extraites
        
        Raises:
            ValueError: Si des candidats sont inconnus
        """
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
            print(f"❌ Candidats inconnus : {unknown_candidates}")
            raise ValueError(
                f"Candidats inconnus : {', '.join(unknown_candidates)}. "
                f"Veuillez compléter le fichier {self.path_to_candidates}"
            )
    
    def write(self, output_path: pathlib.Path, poll_type: str, population: str):
        """
        Écrit le CSV de sortie.
        
        Args:
            output_path: Chemin du fichier CSV à créer
            poll_type: Type de sondage (pt2 pour ELABE)
            population: Population cible (all, left, macron, farright, absentionists)
        """
        with output_path.open("w", encoding="utf-8") as f:
            # En-tête
            header = [
                "candidate_id",
                "intention_mention_1",  # Image très positive
                "intention_mention_2",  # Image plutôt positive
                "intention_mention_3",  # Image plutôt négative
                "intention_mention_4",  # Image très négative
                "intention_mention_5",  # Sans opinion
                "intention_mention_6",  # vide
                "intention_mention_7",  # vide
                "poll_type_id",
                "population",
            ]
            f.write(",".join(header) + "\n")
            
            # Données
            for result in self.results:
                candidate = self.manager.find_candidate(result.get_name())
                scores = result.get_scores()
                
                # ELABE a 5 scores, on complète avec 2 vides pour atteindre 7
                if len(scores) < 7:
                    scores = list(scores)  # Copie pour ne pas modifier l'original
                    scores.extend([""] * (7 - len(scores)))
                
                line = [candidate.id, *scores, poll_type, population]
                f.write(",".join(line) + "\n")
        
        print(f"✅ CSV généré : {output_path}")
        print(f"   📊 {len(self.results)} candidats")
        print(f"   🏷️  Population : {population}")
        print(f"   📋 Type : {poll_type}")
