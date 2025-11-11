# coding: utf-8
"""
Classes pour représenter les données d'un sondage ELABE.
"""

from typing import List, Optional
import sys
import pathlib

# Ajouter le chemin vers mining_IFOP pour importer l'interface
ifop_path = pathlib.Path(__file__).parent.parent / "mining_IFOP"
sys.path.insert(0, str(ifop_path))
import poll as ifop_poll
from poll import CandidatePollInterface


class ElabeLine(CandidatePollInterface):
    """
    Représente une ligne de données ELABE pour un candidat.
    
    Format ELABE : 5 colonnes d'opinion
    - Une image très positive
    - Une image plutôt positive
    - Une image plutôt négative
    - Une image très négative
    - Sans opinion
    """
    
    def __init__(self, name: str, y_position: float = 0.0):
        """
        Initialise une ligne ELABE.
        
        Args:
            name: Nom du candidat
            y_position: Position Y dans le PDF (pour debug/tri)
        """
        self.name = name
        self.y_position = y_position
        self.scores: List[str] = []
    
    def add_score(self, score: str):
        """Ajoute un score à la ligne."""
        self.scores.append(score)
    
    def get_name(self) -> str:
        """Retourne le nom du candidat."""
        return self.name
    
    def get_scores(self) -> List[str]:
        """Retourne la liste des 5 scores."""
        return self.scores
    
    def check(self, expected_score_count: Optional[int] = None) -> bool:
        """
        Valide la ligne de données.
        
        Args:
            expected_score_count: Nombre de scores attendus (None = auto-détection 4 ou 5)
        
        Returns:
            True si la ligne est valide
        
        Raises:
            ValueError: Si la validation échoue
        """
        # Si pas de nombre attendu, vérifier que c'est 4 ou 5
        if expected_score_count is None:
            if len(self.scores) not in [4, 5]:
                raise ValueError(
                    f"{self.name}: attendu 4 ou 5 scores, obtenu {len(self.scores)}"
                )
        else:
            # Vérifier le nombre de scores
            if len(self.scores) != expected_score_count:
                raise ValueError(
                    f"{self.name}: attendu {expected_score_count} scores, "
                    f"obtenu {len(self.scores)}"
                )
        
        # Vérifier que tous les scores sont des nombres
        try:
            numeric_scores = [int(s) for s in self.scores]
        except ValueError as e:
            raise ValueError(f"{self.name}: score non numérique - {e}")
        
        # Vérifier que la somme = 100%
        total = sum(numeric_scores)
        if total != 100:
            raise ValueError(
                f"{self.name}: somme = {total}% (attendu 100%). "
                f"Scores: {self.scores}"
            )
        
        return True
    
    def __repr__(self) -> str:
        """Représentation textuelle de la ligne."""
        return f"ElabeLine({self.name}, scores={self.scores}, total={sum(int(s) for s in self.scores)}%)"
