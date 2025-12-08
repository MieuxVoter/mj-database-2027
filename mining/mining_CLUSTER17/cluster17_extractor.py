import pathlib
import logging
import re
from typing import List, Dict, Any
import pdfplumber
import pandas as pd
from tabulate import tabulate
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from core.settings.logger import setup_logging
from core.helpers import normalize
from core.population import Population

setup_logging()
logger = logging.getLogger("app")


class Cluster17PDFExtractor:

    COLUMN_HEADER_PATTERNS = [
        r"vous\s+la\s+soutenez",
        r"vous\s+l['’]appreciez",
        r"vous\s+ne\s+l['’]appreciez\s*pas",
        r"vous\s+n['’]avez\s+pas\s+d['’]avis\s+sur\s+elle",
        r"vous\s+ne\s+la\s+connaissez\s+pas",
    ]

    min_table_rows: int = 3
    gap_multiplier: float = 1.8
    min_gap: float = 4.0

    def __init__(self, file: pathlib.Path, population: Population | None = None) -> None:

        self.file = file
        self.population = population

    def _is_page_relevant(self, page_layout) -> bool:
        """
        Analysez une page PDF pour déterminer si elle contient un tableau correspondant
        à une sondage du Cluster 17.

        Il repose sur la détection combinée de plusieurs critères :
        - Présence du titre attendu dans le texte normalisé.
        - Densité totale de lignes suffisante (indicative de tableaux).
        - Abondance de petits blocs de texte (cellules ou lignes courtes).
        - Densité numérique élevée (valeurs en pourcentage ou numériques).
        - Existence d'en-têtes attendus dans des colonnes connues.

        Args:
            page_layout: Objet itérable provenant de `pdfminer`
                qui contient les éléments de texte (`LTTextContainer`)
                et leur disposition sur la page.

        Returns:
            bool: `True` si la page présente les caractéristiques typiques
                d'un tableau de sondage Cluster 17, `False` dans le cas contraire.
        """

        page_text = ""
        text_blocks = []

        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()

                if text:
                    page_text += text + "\n"
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    text_blocks.append({"text": text, "line_count": len(lines)})

        normalized_text = normalize(page_text)

        #  Détectant le titre
        has_title = "barometre des personnalites" in normalized_text

        # Densité totale des lignes
        total_lines = sum(b["line_count"] for b in text_blocks)

        # Blocs (petites tables)
        small_blocks = [b for b in text_blocks if 1 <= b["line_count"] <= 4]

        # Densité numérique (% ou nombre)
        num_blocks = sum(1 for b in text_blocks if "%" in b["text"] or any(ch.isdigit() for ch in b["text"]))

        has_numeric_density = num_blocks >= 5

        # Règles combinées pour tables
        has_table_structure = (
            total_lines >= 20 or len(small_blocks) >= 25  # il y a beaucoup de lignes  # beaucoup de petits blocs
        )

        has_expected_columns = sum(bool(re.search(p, normalized_text)) for p in self.COLUMN_HEADER_PATTERNS) >= 2

        return has_title and has_table_structure and has_numeric_density and has_expected_columns
    

    def _get_tables_population(self, page_number: int) -> List[Dict[str, Any]] | None:
        """
        Extrait d'une page PDF les **tableaux** et les **blocs de texte (légendes ou populations)**
        qui se trouvent immédiatement au-dessus d'eux, en renvoyant les deux éléments dans une structure combinée.
        
        Args:
            page_number: Numéro de la page à analyser (indexée 1). 
                Il doit être compris entre 1 et le nombre total de pages du PDF.

        Returns:
            List[Dict[str, Any]] | None
                    Une liste de dictionnaires, où chaque élément représente un tableau et son contexte textuel associé.

            Si aucun tableau n'est détecté sur la page, renvoie `None`.        
        """

        logger.debug("")
        logger.debug("="*50)
        logger.debug(f"Obtenir des tables et ses populations — Page: {page_number}")
        logger.debug("="*50)
        logger.debug("")

        with pdfplumber.open(self.file) as pdf:

            total_pages = len(pdf.pages)
            
            if page_number < 1 or page_number > len(pdf.pages):
                logging.error(f"Numéro de page invalide: {page_number}. "
                                f"Le PDF ne comporte que {total_pages} pages.")
                raise ValueError(f"Le PDF ne comporte que {total_pages} pages.")
            
            page = pdf.pages[page_number - 1]    

            # Détecter les tables 
            table_objects = sorted(page.find_tables(), key=lambda t: t.bbox[1])
            bboxes = [t.bbox for t in table_objects]

            logger.debug(f"Table(s) détectée(s) :\t{len(table_objects)} ")
            logger.debug("")

            # Extraire tous les mots avec coordonnées
            words = page.extract_words(use_text_flow=True)

            y_prev_bottom = 0
            survey_data = []
            for idx, (x0, y_top, x1, y_bottom) in enumerate(bboxes, start=1):
                logger.debug(f"Obtenir les information du table {idx}")  
                logger.debug(f"bbox table :\t({x0:.1f}, {y_top:.1f}, {x1:.1f}, {y_bottom:.1f})") 

                # Extraire texte avant la table (caption / population)
                segment_words = [w for w in words if y_prev_bottom <= w["bottom"] <= y_top]  
                sorted_words = sorted(segment_words, key=lambda w: (w["top"], w["x0"]))
                segment_texte = " ".join(w["text"] for w in sorted_words)  

                # supprimer le titre principal
                clean_text = re.sub(
                    r"BAROMÈTRE DES PERSONNALITÉS\s+[A-ZÉÈÊÎÔÛÂÀÙÇ\-]+",
                    "",
                    segment_texte,
                    flags=re.IGNORECASE
                ).strip()  

                population = None
                population_label = None
                if clean_text:
                    logger.debug(f"Légende:\t{clean_text}")
                    population_detected = Population.detect_from_text(clean_text)
                    if population_detected:
                        population, population_label = population_detected
                        logger.debug(f"population:\t{population}")     
                    
                # Extraire la table
                df = pd.DataFrame(table_objects[idx - 1].extract())

                # Nettoyage du DataFrame
                df = df.dropna(how="all").reset_index(drop=True)
                if not df.empty:
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)

                logger.debug(f"columns: {df.columns.tolist()}")
                logger.debug("Aperçu du DataFrame :\n" + tabulate(df.head(), headers="keys", tablefmt="psql"))

                survey_data.append({
                    "Table id": idx,
                    "Légende de tableau": clean_text,
                    "Population": population,
                    "Étiquette de population": population_label,
                    "df": df
                })
                                    
                y_prev_bottom = y_bottom 
                logger.debug("")   

        return survey_data


    def extract_data(self, start_page: int = 1) -> List:

        logger.info("")
        logger.info("🔍 Détection et extraction des pages de données... ")

        pages = list(extract_pages(str(self.file)))
        total_pages = len(pages)

        # Détection des pages pertinentes contenant des sondages
        data_pages = []
        for page_num in range(start_page, total_pages + 1):
            page_layout = pages[page_num - 1]

            if self._is_page_relevant(page_layout):
                data_pages.append(page_num)

        logger.info(f"📊 {len(data_pages)} page(s) de données détectée(s) :")
        logger.info("")

        for page in data_pages:
            survey_data = self._get_tables_population(page)
            for table in survey_data:
                logger.info(f"• Page {page} : {table['Étiquette de population']}")

        return []