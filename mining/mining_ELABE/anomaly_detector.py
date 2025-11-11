# coding: utf-8
"""
Classe pour gérer les anomalies détectées lors de l'extraction.
"""

import pathlib
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ExtractionAnomaly:
    """Représente une anomalie détectée lors de l'extraction."""
    
    page_num: int
    line_num: int
    candidate_name: str
    extracted_scores: List[int]
    total: int
    missing_percent: int
    suggested_position: str  # "début", "milieu", "fin"
    message: str
    
    def __str__(self) -> str:
        """Représentation textuelle de l'anomalie."""
        return (
            f"⚠️  ANOMALIE - Page {self.page_num}, Ligne {self.line_num}\n"
            f"   Candidat: {self.candidate_name}\n"
            f"   Scores extraits: {self.extracted_scores}\n"
            f"   Total: {self.total}% (attendu 100%)\n"
            f"   Différence: {self.missing_percent:+d}%\n"
            f"   Position suggérée: {self.suggested_position}\n"
            f"   💡 {self.message}"
        )


class AnomalyDetector:
    """Détecte et analyse les anomalies dans les données extraites."""
    
    def __init__(self):
        self.anomalies: List[ExtractionAnomaly] = []
    
    def check_line(self, page_num: int, line_num: int, candidate_name: str, 
                   scores: List[str]) -> Optional[ExtractionAnomaly]:
        """
        Vérifie une ligne et retourne une anomalie si détectée.
        
        Args:
            page_num: Numéro de page
            line_num: Numéro de ligne
            candidate_name: Nom du candidat
            scores: Liste des scores (strings)
        
        Returns:
            ExtractionAnomaly si anomalie détectée, None sinon
        """
        try:
            numeric_scores = [int(s) for s in scores]
        except ValueError:
            return ExtractionAnomaly(
                page_num=page_num,
                line_num=line_num,
                candidate_name=candidate_name,
                extracted_scores=[],
                total=0,
                missing_percent=0,
                suggested_position="inconnu",
                message="Scores non numériques détectés"
            )
        
        total = sum(numeric_scores)
        
        if total == 100:
            return None  # Pas d'anomalie
        
        missing = 100 - total
        
        # Déterminer la position probable du score manquant
        suggested_position = self._suggest_position(numeric_scores, missing)
        
        # Générer le message
        message = self._generate_message(numeric_scores, missing, suggested_position)
        
        anomaly = ExtractionAnomaly(
            page_num=page_num,
            line_num=line_num,
            candidate_name=candidate_name,
            extracted_scores=numeric_scores,
            total=total,
            missing_percent=missing,
            suggested_position=suggested_position,
            message=message
        )
        
        self.anomalies.append(anomaly)
        return anomaly
    
    def _suggest_position(self, scores: List[int], missing: int) -> str:
        """
        Suggère où se trouve probablement le score manquant.
        
        Args:
            scores: Liste des scores extraits
            missing: Pourcentage manquant (positif si manque, négatif si trop)
        
        Returns:
            "début", "milieu", "fin", ou description
        """
        if missing < 0:
            return "trop de scores (probablement le total en 6ème colonne)"
        
        if missing == 0:
            return "OK"
        
        if len(scores) == 0:
            return "aucun score extrait"
        
        # Si le score manquant est très petit (≤ 5%)
        if abs(missing) <= 5:
            # Analyser les extrémités
            first = scores[0] if scores else 0
            last = scores[-1] if scores else 0
            
            # Si le premier score est petit, le manquant est probablement avant
            if first <= 10:
                return "début (avant le premier score)"
            # Si le dernier score est petit, le manquant est probablement après
            elif last <= 10:
                return "fin (après le dernier score)"
            # Sinon, probablement au milieu
            else:
                return "milieu (entre deux scores)"
        else:
            # Score manquant important
            return "position indéterminée"
    
    def _generate_message(self, scores: List[int], missing: int, position: str) -> str:
        """Génère un message d'aide pour l'utilisateur."""
        if missing > 0:
            return (
                f"Il MANQUE {missing}% dans le PDF (barre illisible ou absente). "
                f"Le score manquant se trouve probablement au {position}. "
                f"Veuillez vérifier le PDF et corriger manuellement si nécessaire."
            )
        elif missing < 0:
            return (
                f"Le total EXCÈDE de {-missing}%. "
                f"Cela indique probablement que le total (6ème colonne) a été capturé par erreur."
            )
        else:
            return "OK"
    
    def get_summary(self) -> str:
        """Retourne un résumé des anomalies détectées."""
        if not self.anomalies:
            return "✅ Aucune anomalie détectée"
        
        summary = f"⚠️  {len(self.anomalies)} anomalie(s) détectée(s) :\n\n"
        for i, anomaly in enumerate(self.anomalies, 1):
            summary += f"{i}. {anomaly}\n\n"
        
        return summary
    
    def has_anomalies(self) -> bool:
        """Retourne True si des anomalies ont été détectées."""
        return len(self.anomalies) > 0
    
    def export_to_file(self, output_path: pathlib.Path, population_name: str):
        """
        Exporte les anomalies dans un fichier texte.
        
        Args:
            output_path: Chemin du répertoire de sortie
            population_name: Nom de la population (ex: "all", "absentionists", etc.)
        """
        if not self.anomalies:
            return  # Pas d'export si pas d'anomalies
        
        filename = f"mining_anomalie_{population_name}.txt"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT D'ANOMALIES - EXTRACTION ELABE\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Population: {population_name}\n")
            f.write(f"Nombre d'anomalies: {len(self.anomalies)}\n\n")
            f.write("=" * 80 + "\n\n")
            
            for i, anomaly in enumerate(self.anomalies, 1):
                f.write(f"ANOMALIE #{i}\n")
                f.write("-" * 80 + "\n\n")
                f.write(f"Page:           {anomaly.page_num}\n")
                f.write(f"Ligne:          {anomaly.line_num}\n")
                f.write(f"Candidat:       {anomaly.candidate_name}\n\n")
                f.write(f"Scores extraits: {anomaly.extracted_scores}\n")
                f.write(f"Total:           {anomaly.total}% (attendu 100%)\n")
                f.write(f"Différence:      {anomaly.missing_percent:+d}%\n\n")
                f.write(f"Position suggérée du score manquant:\n")
                f.write(f"  → {anomaly.suggested_position}\n\n")
                f.write(f"Recommandation:\n")
                f.write(f"  {anomaly.message}\n\n")
                
                # Actions à effectuer
                if anomaly.missing_percent > 0:
                    f.write(f"ACTION REQUISE:\n")
                    f.write(f"  1. Ouvrir le PDF source\n")
                    f.write(f"  2. Aller à la page {anomaly.page_num}\n")
                    f.write(f"  3. Trouver la ligne '{anomaly.candidate_name}'\n")
                    f.write(f"  4. Vérifier si une barre de {anomaly.missing_percent}% est présente mais illisible\n")
                    f.write(f"  5. Si oui, ajouter manuellement le score manquant\n")
                    f.write(f"  6. Scores attendus: ajouter {anomaly.missing_percent}% au {anomaly.suggested_position}\n\n")
                
                f.write("=" * 80 + "\n\n")
            
            f.write("\nFIN DU RAPPORT\n")
        
        print(f"📝 Anomalies exportées: {filepath}")
        return filepath
