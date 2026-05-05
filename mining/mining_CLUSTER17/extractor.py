import pathlib
from pathlib import Path
import logging
import re
from typing import List, Dict, Any
import pdfplumber
import pandas as pd
from datetime import date
from tabulate import tabulate
from pdfminer.layout import LTTextContainer
from pdfminer.high_level import extract_pages
from core.utils.helpers import normalize
from core.models.population import Population


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

    MONTHS_FR = {
        "janvier": "01",
        "février": "02",
        "fevrier": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "août": "08",
        "aout": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "décembre": "12",
        "decembre": "12",
    }

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
        self.logger = logging.getLogger(__name__)
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
        has_title = bool(re.search(r"\bbarometre\b.*\bpersonnalites\b", normalized_text))
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
            List[Dict[str, Any]]
                    Une liste de dictionnaires, où chaque élément représente un tableau et son contexte textuel associé.
        """

        self.logger.debug("")
        self.logger.debug("=" * 50)
        self.logger.debug(f"Obtenir des tables et ses populations — Page: {page_number}")
        self.logger.debug("=" * 50)
        self.logger.debug("")

        with pdfplumber.open(self.pdf_path) as pdf:

            total_pages = len(pdf.pages)

            if page_number < 1 or page_number > len(pdf.pages):
                raise ValueError(f"Numéro de page invalide: {page_number} / {total_pages}. ")

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
                except (KeyError, IndexError, ValueError) as e:
                    self.logger.warning(f"Table ignorée | page={page_number} | table={idx} | reason={e}")

        return survey_data

    def _read_metadata_txt(self) -> Dict[str, str]:
        """
        Lire un fichier metadata.txt formaté sous forme de paires « clé : valeur ».

        Args:
            path : Path
                Chemin d'accès au fichier metadata.txt.

        Returns:
            Dict[str, str]
                Dictionnaire contenant des clés et des valeurs de métadonnées.

        """
        metadata_path = self.pdf_path.parent / "metadata.txt"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        metadata: Dict[str, str] = {}

        with metadata_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if ":" not in line:
                    raise ValueError(f"Malformed metadata line: {line}")

                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

        return metadata

    def _extract_methodology_metadata(self, end_page: int = 5) -> Dict[str, Any]:
        """
        Extrait les métadonnées méthodologiques clés à partir de la section
        « MÉTHODOLOGIE » d’un PDF Cluster17.

        Cette méthode parcourt les premières pages du document afin de localiser
        la page contenant le titre « MÉTHODOLOGIE », puis en extrait les informations
        suivantes :
        - la taille de l’échantillon (nombre de personnes interrogées),
        - les dates de réalisation des interviews (format ISO YYYY-MM-DD).

        Args:
            end_page (int, optional):
                Nombre maximum de pages à analyser depuis le début du PDF.
                Par défaut à 5, ce qui couvre généralement la section méthodologique.

        Returns:
            Dict[str, Any]:
                Dictionnaire contenant les métadonnées extraites :
                {
                    "sample_size": int,        # Taille de l’échantillon
                    "start_date": str,         # Date de début des interviews (YYYY-MM-DD)
                    "end_date": str,           # Date de fin des interviews (YYYY-MM-DD)
                }
        """

        methodology_text = ""

        # Trouver la page "MÉTHODOLOGIE"
        with pdfplumber.open(self.pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages[:end_page], start=1):
                page_text = page.extract_text()
                if not page_text:
                    continue

                if re.search(r"\bm[ée]thodologie\b", page_text, flags=re.IGNORECASE):
                    methodology_text = page_text
                    self.logger.info(f"📐  Page MÉTHODOLOGIE détectée (page {idx})")
                    break

        if not methodology_text:
            raise ValueError("Page MÉTHODOLOGIE introuvable dans le PDF")

        # -------------------------
        # Taille de l’échantillon
        # -------------------------
        sample_match = re.search(
            r"[ée]chantillon\s+(?:de|:)\s*([\d\s]+)\s+personnes", methodology_text, flags=re.IGNORECASE
        )
        if not sample_match:
            raise ValueError("Impossible d’extraire la taille de l’échantillon")

        sample_size = int(sample_match.group(1).replace(" ", ""))
        self.logger.debug(f"sample_size: {sample_size}")

        # -------------------------
        # Dates d’interviews
        # -------------------------
        RE_ONE_MONTH = re.compile(
            r"Interviews réalisées du\s+(\d{1,2})\s+au\s+(\d{1,2})\s+" r"([a-zàâäéèêëîïôöùûüç]+)\s+(\d{4})",
            flags=re.IGNORECASE,
        )

        RE_TWO_MONTHS = re.compile(
            r"Interviews réalisées du\s+(\d{1,2})\s+"
            r"([a-zàâäéèêëîïôöùûüç]+)\s+au\s+"
            r"(\d{1,2})(?:er)?\s+"
            r"([a-zàâäéèêëîïôöùûüç]+)\s+(\d{2,4})",
            flags=re.IGNORECASE,
        )

        # Cas A : un seul mois (ex: octobre 2025)
        m = RE_ONE_MONTH.search(methodology_text)
        if m:
            d1, d2, month, year = m.groups()

            month_norm = month.lower()
            if month_norm not in self.MONTHS_FR:
                raise ValueError(f"Mois non reconnu : {month}")

            y = int(year)
            m_num = int(self.MONTHS_FR[month_norm])

            start_date = date(y, m_num, int(d1)).isoformat()
            end_date = date(y, m_num, int(d2)).isoformat()

        # Cas B : deux mois (ex: août → septembre 25)
        else:
            m = RE_TWO_MONTHS.search(methodology_text)
            if not m:
                raise ValueError("Impossible d’extraire les dates d’interviews")

            d1, m1, d2, m2, year = m.groups()

            m1 = m1.lower()
            m2 = m2.lower()

            if m1 not in self.MONTHS_FR or m2 not in self.MONTHS_FR:
                raise ValueError(f"Mois non reconnu : {m1}, {m2}")

            y = int(year) if len(year) == 4 else int(f"20{year}")

            start_date = date(y, int(self.MONTHS_FR[m1]), int(d1)).isoformat()
            end_date = date(y, int(self.MONTHS_FR[m2]), int(d2)).isoformat()

        self.logger.debug(f"start_date: {start_date} | end_date: {end_date}")
        self.logger.debug("")

        # -------------------------
        # Lecture de l'URL du pdf à partir de metadata.txt
        # -------------------------
        metadata_txt = self._read_metadata_txt()
        pdf_url = metadata_txt.get("pdf_url")
        if not pdf_url:
            raise ValueError("pdf_url introuvable dans metadata.txt")

        self.logger.debug(f"pdf_url: {pdf_url}")

        return {"sample_size": sample_size, "start_date": start_date, "end_date": end_date, "pdf_url": pdf_url}

    def extract_all(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Exécute l'extraction complète du fichier PDF :
        - Détection des pages pertinentes
        - Extraction des tableaux et populations associées

        Returns:
            Dict[str, Any]:
                Dictionnaire contenant les métadonnées :
                {
                    "sample_size": int,        # Taille de l’échantillon
                    "start_date": str,         # Date de début des interviews (YYYY-MM-DD)
                    "end_date": str,           # Date de fin des interviews (YYYY-MM-DD)
                }

            List[Dict[str, Any]]
                    Une liste de dictionnaires, où chaque élément représente un tableau et son contexte textuel associé.
        """
        # -----------------------------------------------------------------
        # Extraction des métadonnées de l'enquête
        # -----------------------------------------------------------------
        survey_metadata = self._extract_methodology_metadata()

        # -----------------------------------------------------------------
        # Détection des pages pertinentes contenant des sondages
        # -----------------------------------------------------------------
        pages = list(extract_pages(str(self.pdf_path)))
        total_pages = len(pages)
        data_pages: List[int] = []

        for page_num in range(1, total_pages + 1):
            page_layout = pages[page_num - 1]
            if self._is_page_relevant(page_layout):
                data_pages.append(page_num)

        if not data_pages:
            self.logger.warning("Aucune page pertinente détectée dans ce PDF")
            return []

        self.logger.info(f"📊  {len(data_pages)} page(s) de données détectée(s) :")

        # -----------------------------------------------------------------
        # Obtenir les tableaux et les populations
        # -----------------------------------------------------------------
        surveys: List[Dict[str, Any]] = []
        for page_number in data_pages:
            survey_data = self._get_tables_population(page_number)
            for table in survey_data:
                self.logger.info(f"  • Page {page_number} : {table['Étiquette de population']}")
            surveys.extend(survey_data)

        if not surveys:
            self.logger.warning("Aucune table extraite du PDF")
            return []

        return survey_metadata, surveys
