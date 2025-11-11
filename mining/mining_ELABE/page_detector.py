# coding: utf-8
"""
Détecteur de pages de données dans les PDFs ELABE.
"""

import pathlib
from typing import List, Tuple, Optional
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer


class PageDetector:
    """Détecte les pages contenant des données de sondage."""
    
    def __init__(self, pdf_path: pathlib.Path):
        """
        Initialise le détecteur.
        
        Args:
            pdf_path: Chemin vers le PDF à analyser
        """
        self.pdf_path = pdf_path
    
    def detect_data_pages(self, start_page: int = 1, end_page: int = 30) -> List[Tuple[int, str]]:
        """
        Détecte les pages contenant des tableaux de données.
        
        Stratégie : Une page de données ELABE contient :
        - Un titre comme "Le classement des personnalités"
        - Une mention de population (Ensemble, abstentionnistes, etc.)
        - Un bloc avec 20-35 noms de candidats
        - Des colonnes de scores numériques
        
        Args:
            start_page: Page de début (incluse)
            end_page: Page de fin (incluse)
        
        Returns:
            Liste de tuples (numéro_page, type_population)
        """
        data_pages = []
        
        for page_num in range(start_page, end_page + 1):
            result = self._check_page(page_num)
            if result:
                data_pages.append(result)
        
        return data_pages
    
    def _check_page(self, page_num: int) -> Optional[Tuple[int, str]]:
        """
        Vérifie si une page contient des données.
        
        Args:
            page_num: Numéro de page à vérifier
        
        Returns:
            Tuple (page_num, population) si c'est une page de données, None sinon
        """
        for page_number, page_layout in enumerate(extract_pages(str(self.pdf_path)), start=1):
            if page_number != page_num:
                continue
            
            # Extraire tout le texte de la page
            page_text = ""
            text_blocks = []
            
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        page_text += text + "\n"
                        
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        if len(lines) >= 20:
                            text_blocks.append({
                                'text': text,
                                'lines': lines,
                                'line_count': len(lines)
                            })
            
            # Vérifier les marqueurs d'une page de données
            has_title = "Le classement des personnalités" in page_text
            has_candidates = any(block['line_count'] >= 20 for block in text_blocks)
            
            if not (has_title and has_candidates):
                break
            
            # Déterminer le type de population
            population = self._identify_population(page_text)
            
            return (page_num, population)
        
        return None
    
    def _identify_population(self, page_text: str) -> str:
        """
        Identifie le type de population depuis le texte de la page.
        
        Args:
            page_text: Texte complet de la page
        
        Returns:
            Identifiant de population ("all", "absentionists", etc.)
        """
        # Normaliser les apostrophes typographiques (U+2019) en apostrophes standard (U+0027)
        text_lower = page_text.lower().replace('\u2019', "'")
        
        # Patterns de détection (avec apostrophes standard)
        patterns = {
            "all": [
                "ensemble des français",
                "tous les français",
                "l'ensemble des français"
            ],
            "absentionists": [
                "abstentionnistes",
                "votes blancs et nuls",
                "non-inscrits"
            ],
            "macron": [
                "électeurs d'emmanuel macron",
                "électeurs de macron"
            ],
            "left": [
                "électeurs de gauche et des écologistes",
                "électeurs de gauche",
                "sympathisants de gauche"
            ],
            "farright": [
                "électeurs de marine le pen et d'éric zemmour",
                "électeurs de marine le pen",
                "électeurs d'extrême droite",
                "électeurs du rassemblement national"
            ]
        }
        
        # Chercher le premier pattern qui matche
        for pop_id, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return pop_id
        
        # Si rien ne matche, retourner "unknown"
        return "unknown"
    
    def get_summary(self, data_pages: List[Tuple[int, str]]) -> str:
        """
        Génère un résumé des pages détectées.
        
        Args:
            data_pages: Liste des pages détectées
        
        Returns:
            Résumé formaté
        """
        if not data_pages:
            return "Aucune page de données détectée"
        
        summary = f"📊 {len(data_pages)} page(s) de données détectée(s) :\n\n"
        
        for page_num, population in data_pages:
            pop_name = {
                "all": "Ensemble des Français",
                "absentionists": "Abstentionnistes",
                "macron": "Électeurs de Macron",
                "left": "Électeurs de gauche",
                "farright": "Électeurs d'extrême droite",
                "unknown": "Population inconnue"
            }.get(population, population)
            
            summary += f"  • Page {page_num:2d}: {pop_name}\n"
        
        return summary
