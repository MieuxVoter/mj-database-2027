# coding: utf-8
"""
Extraction des données depuis les PDFs ELABE.
"""

import pathlib
import csv
from typing import List, Dict, Set, Optional
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

try:
    from .elabe_poll import ElabeLine
    from .anomaly_detector import AnomalyDetector
except ImportError:
    from elabe_poll import ElabeLine
    from anomaly_detector import AnomalyDetector

class ElabeMiner:
    """
    Extracteur de données pour les PDFs ELABE.
    
    Gère l'extraction des noms de candidats et de leurs scores d'opinion
    depuis les pages de données des baromètres politiques ELABE.
    """
    
    def __init__(self, pdf_path: pathlib.Path, candidates_csv: Optional[pathlib.Path] = None):
        """
        Initialise le mineur ELABE.
        
        Args:
            pdf_path: Chemin vers le PDF à analyser
            candidates_csv: Chemin vers le fichier CSV des candidats (optionnel)
        """
        self.pdf_path = pdf_path
        self.lines: List[ElabeLine] = []
        self.anomaly_detector = AnomalyDetector()
        
        # Charger la liste des candidats
        if candidates_csv is None:
            # Chemin par défaut: ../../candidates.csv depuis le répertoire du script
            candidates_csv = pathlib.Path(__file__).parent.parent.parent / "candidates.csv"
        
        self.known_candidates = self._load_candidates(candidates_csv)
    
    def _load_candidates(self, csv_path: pathlib.Path) -> Set[str]:
        """
        Charge la liste des candidats depuis le CSV.
        
        Args:
            csv_path: Chemin vers candidates.csv
        
        Returns:
            Ensemble des noms complets des candidats
        """
        candidates = set()
        
        if not csv_path.exists():
            # Fallback: quelques noms connus
            return {
                'Jordan Bardella', 'Marine Le Pen', 'Edouard Philippe',
                'François Ruffin', 'Fabien Roussel', 'Gabriel Attal'
            }
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Format: "Prénom Nom"
                name = row['name'].strip()
                surname = row['surname'].strip()
                if name and surname:
                    full_name = f"{name} {surname}"
                    candidates.add(full_name)
        
        return candidates
    
    def extract_page(self, page_num: int = 17) -> List[ElabeLine]:
        """
        Extrait les données d'une page spécifique.
        
        Args:
            page_num: Numéro de page à extraire (17-21 pour ELABE)
        
        Returns:
            Liste des lignes extraites
        """
        self.lines = []
        
        # Extraire les éléments de la page
        for page_number, page_layout in enumerate(extract_pages(str(self.pdf_path)), start=1):
            if page_number != page_num:
                continue
            
            elements = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        elements.append({
                            'text': text,
                            'x': element.x0,
                            'y': element.y0
                        })
            
            # 1. Extraire les noms de candidats
            candidate_names = self._extract_candidate_names(elements)
            
            if not candidate_names:
                return []
            
            # 2. Extraire les scores
            score_lines = self._extract_scores(elements)
            
            # 3. Associer noms ↔ scores et détecter les anomalies
            for i in range(min(len(candidate_names), len(score_lines))):
                name = candidate_names[i]
                scores = [str(s['value']) for s in score_lines[i]]
                
                # Vérifier les anomalies
                anomaly = self.anomaly_detector.check_line(
                    page_num=page_num,
                    line_num=i + 1,
                    candidate_name=name,
                    scores=scores
                )
                
                line = ElabeLine(name, y_position=score_lines[i][0]['y'])
                for score in scores:
                    line.add_score(score)
                
                self.lines.append(line)
            
            break
        
        return self.lines
    
    def _extract_candidate_names(self, elements: List[Dict]) -> List[str]:
        """
        Extrait les noms des candidats depuis les éléments du PDF.
        
        Pour le format récent ELABE (oct-nov 2025), les noms sont dans un seul
        bloc texte séparés par des retours à la ligne.
        
        Stratégie robuste: chercher le bloc qui contient le plus de noms
        de candidats connus (depuis candidates.csv).
        
        Args:
            elements: Liste des éléments textuels du PDF
        
        Returns:
            Liste des noms de candidats
        """
        candidate_blocks = []
        
        for elem in elements:
            text = elem['text']
            lines = [n.strip() for n in text.split('\n') if n.strip()]
            
            # Compter combien de noms connus sont dans ce bloc
            known_count = sum(1 for line in lines if line in self.known_candidates)
            
            # Si au moins 5 candidats connus ET entre 20-35 lignes
            if known_count >= 5 and 20 <= len(lines) <= 35:
                candidate_blocks.append({
                    'lines': lines,
                    'count': len(lines),
                    'known_count': known_count,
                    'y': elem['y']
                })
        
        # Prendre le bloc avec le plus de candidats connus
        # (en cas d'égalité, prendre celui avec le plus de lignes)
        if candidate_blocks:
            best_block = max(candidate_blocks, key=lambda b: (b['known_count'], b['count']))
            return best_block['lines']
        
        return []
    
    def _extract_scores(self, elements: List[Dict]) -> List[List[Dict]]:
        """
        Extrait et organise les scores depuis les éléments du PDF.
        
        Les scores sont des valeurs numériques organisées en lignes (même Y)
        et colonnes (X croissants).
        
        Args:
            elements: Liste des éléments textuels du PDF
        
        Returns:
            Liste de lignes, chaque ligne contenant 5 scores
        """
        # Filtrer les éléments numériques (scores)
        scores = []
        for elem in elements:
            text = elem['text'].replace('%', '').strip()
            try:
                value = int(text)
                if 0 <= value <= 100:
                    scores.append({
                        'value': value,
                        'x': elem['x'],
                        'y': elem['y']
                    })
            except ValueError:
                pass
        
        # Trier par Y (haut en bas)
        scores.sort(key=lambda s: -s['y'])
        
        # Regrouper par ligne (même Y ± 3 pour capturer tous les petits scores)
        lines = []
        current_line = []
        current_y = None
        tolerance = 3.0  # Augmenté de 2.0 à 3.0
        
        for score in scores:
            if current_y is None:
                current_y = score['y']
                current_line = [score]
            elif abs(score['y'] - current_y) < tolerance:
                current_line.append(score)
            else:
                if current_line:
                    # Trier la ligne par X (gauche à droite)
                    current_line.sort(key=lambda s: s['x'])
                    lines.append(current_line)
                current_line = [score]
                current_y = score['y']
        
        if current_line:
            current_line.sort(key=lambda s: s['x'])
            lines.append(current_line)
        
        # Filtrer les lignes avec 4+ éléments (certains candidats ont 4 ou 5 scores)
        # Garder tous les scores de chaque ligne (4 ou 5)
        score_lines = []
        for line in lines:
            if len(line) >= 4:
                # Si 6+ éléments, ne garder que les 5 premiers (cas du total en 6e colonne)
                if len(line) >= 6:
                    score_lines.append(line[:5])
                else:
                    score_lines.append(line)
        
        return score_lines
    
    def get_lines(self) -> List[ElabeLine]:
        """Retourne les lignes extraites."""
        return self.lines
    
    def validate_all(self) -> bool:
        """
        Valide toutes les lignes extraites.
        
        Returns:
            True si toutes les lignes sont valides
        
        Raises:
            ValueError: Si une ligne est invalide
        """
        for line in self.lines:
            line.check()
        return True
    
    def get_anomalies_summary(self) -> str:
        """Retourne un résumé des anomalies détectées."""
        return self.anomaly_detector.get_summary()
    
    def has_anomalies(self) -> bool:
        """Retourne True si des anomalies ont été détectées."""
        return self.anomaly_detector.has_anomalies()
    
    def export_anomalies(self, output_dir: pathlib.Path, population_name: str):
        """
        Exporte les anomalies détectées dans un fichier texte.
        
        Args:
            output_dir: Répertoire de sortie
            population_name: Nom de la population (ex: "all", "absentionists")
        """
        if self.has_anomalies():
            return self.anomaly_detector.export_to_file(output_dir, population_name)
