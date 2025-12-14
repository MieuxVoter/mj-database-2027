import pathlib
from pathlib import Path
import logging
import re
from typing import List, Dict, Any
import pdfplumber
import pandas as pd
from tabulate import tabulate
from pdfminer.layout import LTTextContainer
from pdfminer.high_level import extract_pages
from core.helpers import normalize
from core.population import Population


class PDFExtractor:
    """
    Classe responsable de l'extraction des tableaux et des légendes (captions)
    à partir d'un PDF du baromètre Cluster17.
    """

    # Colonnes à trouver dans les tableaux
    COLUMN_HEADER_PATTERNS = [
        r"vous\s+la\s+soutenez",
        r"vous\s+l['’]appreciez",
        r"vous\s+ne\s+l['’]appreciez\s*pas",
        r"vous\s+n['’]avez\s+pas\s+d['’]avis\s+sur\s+elle",
        r"vous\s+ne\s+la\s+connaissez\s+pas",
    ]

    def __init__(self, pdf_path: pathlib.Path) -> None:
        """
        Initialise l'extracteur PDF pour le baromètre Cluster17.

        Args:
            file : Path
                Chemin complet vers le fichier PDF à analyser.
            population : Population, optionnel
                Population ou sous-échantillon concerné (ex. Population.LFI)
        """
        self.pdf_path: Path = pdf_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """
        Valide les paramètres d'entrée.
        """
        if not isinstance(self.pdf_path, Path):
            self.logger.error("Le paramètre 'pdf_path' doit être une instance de pathlib.Path.")
            raise TypeError("Le paramètre 'pdf_path' doit être une instance de pathlib.Path.")
        if not self.pdf_path.exists():
            self.logger.error(f"Le fichier spécifié est introuvable : {self.pdf_path}")
            raise FileNotFoundError(f"Le fichier spécifié est introuvable : {self.pdf_path}")

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

        # -----------------------------------------------------------------
        # Règles d’identification
        # -----------------------------------------------------------------
        # Détectant le titre
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

    def _get_tables_population(self, page_number: int) -> List[Dict[str, Any]]:
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

        self.logger.debug("")
        self.logger.debug("=" * 50)
        self.logger.debug(f"Obtenir des tables et ses populations — Page: {page_number}")
        self.logger.debug("=" * 50)
        self.logger.debug("")

        with pdfplumber.open(self.pdf_path) as pdf:

            total_pages = len(pdf.pages)

            if page_number < 1 or page_number > len(pdf.pages):
                logging.error(
                    f"Numéro de page invalide: {page_number}. " f"Le PDF ne comporte que {total_pages} pages."
                )
                raise ValueError(f"Le PDF ne comporte que {total_pages} pages.")

            page = pdf.pages[page_number - 1]

            # Détecter les tables
            table_objects = sorted(page.find_tables(), key=lambda t: t.bbox[1])

            if not table_objects:
                self.logger.debug(f"Aucune table détectée à la page {page_number}.")
                return []

            bboxes = [t.bbox for t in table_objects]

            self.logger.debug(f"Table(s) détectée(s) :\t{len(table_objects)} ")
            self.logger.debug("")

            # Extraire tous les mots avec coordonnées
            words = page.extract_words(use_text_flow=True)

            y_prev_bottom = 0
            survey_data = []
            for idx, (x0, y_top, x1, y_bottom) in enumerate(bboxes, start=1):
                try:
                    self.logger.debug(f"Obtenir les information du table {idx}")
                    self.logger.debug(f"bbox table :\t({x0:.1f}, {y_top:.1f}, {x1:.1f}, {y_bottom:.1f})")

                    # Extraire texte avant la table (caption / population)
                    segment_words = [w for w in words if y_prev_bottom <= w["bottom"] <= y_top]
                    sorted_words = sorted(segment_words, key=lambda w: (w["top"], w["x0"]))
                    segment_texte = " ".join(w["text"] for w in sorted_words)

                    # supprimer le titre principal
                    clean_text = re.sub(
                        r"BAROMÈTRE DES PERSONNALITÉS\s+[A-ZÉÈÊÎÔÛÂÀÙÇ\-]+", "", segment_texte, flags=re.IGNORECASE
                    ).strip()

                    population = None
                    population_label = None
                    if clean_text:
                        self.logger.debug(f"Légende:\t{clean_text}")
                        population_detected = Population.detect_from_text(clean_text)
                        if population_detected:
                            population, population_label = population_detected
                            self.logger.debug(f"population:\t{population}")

                    # Extraire la table
                    df = pd.DataFrame(table_objects[idx - 1].extract())

                    # Nettoyage du DataFrame
                    df = df.dropna(how="all").reset_index(drop=True)
                    if not df.empty:
                        df.columns = df.iloc[0]
                        df = df[1:].reset_index(drop=True)

                    self.logger.debug(f"columns: {df.columns.tolist()}")
                    self.logger.debug("Aperçu du DataFrame :\n" + tabulate(df.head(), headers="keys", tablefmt="psql"))

                    survey_data.append(
                        {
                            "Page": page_number,
                            "Table id": idx,
                            "Légende de tableau": clean_text,
                            "Population": population,
                            "Étiquette de population": population_label,
                            "df": df,
                        }
                    )

                    y_prev_bottom = y_bottom
                    self.logger.debug("")
                except Exception as e:
                    self.logger.warning(
                        f"Erreur inattendue lors du traitement de la table {idx} page {page_number} : {e}"
                    )
                    continue

        return survey_data

    def extract_all(self) -> List[Dict[str, Any]]:
        """
        Exécute l'extraction complète du fichier PDF :
        - Détection des pages pertinentes
        - Extraction des tableaux et populations associées

        Returns:
            Une liste combinée de tous les tableaux extraits.
        """

        try:
            pages = list(extract_pages(str(self.pdf_path)))
            total_pages = len(pages)
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la lecture du fichier PDF : {e}")
            return []

        # -----------------------------------------------------------------
        # Détection des pages pertinentes contenant des sondages
        # -----------------------------------------------------------------
        data_pages: List[int] = []
        for page_num in range(1, total_pages + 1):
            try:
                page_layout = pages[page_num - 1]
                if self._is_page_relevant(page_layout):
                    data_pages.append(page_num)
            except Exception as e:
                self.logger.error(f"Erreur inattendue lors de l’analyse de la page {page_num} : {e}")

        if not data_pages:
            self.logger.warning("Aucune page pertinente détectée dans ce PDF")
            return []

        self.logger.info(f"📊  {len(data_pages)} page(s) de données détectée(s) :")
        self.logger.info("")

        # -----------------------------------------------------------------
        # Obtenir les tableaux et les populations
        # -----------------------------------------------------------------
        surveys: List[Dict[str, Any]] = []
        for page_number in data_pages:
            try:
                survey_data = self._get_tables_population(page_number)
                for table in survey_data:
                    self.logger.info(f" • Page {page_number} : {table['Étiquette de population']}")
                surveys.extend(survey_data)
            except Exception as e:
                self.logger.error(f"Erreur inattendue lors de l’extraction des données de la page {page} : {e}")

        if not surveys:
            self.logger.warning("Aucune table extraite du PDF")
            return []

        return surveys
