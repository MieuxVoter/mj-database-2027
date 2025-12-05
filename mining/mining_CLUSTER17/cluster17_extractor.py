import pathlib
import logging
import re
from typing import List
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
    




    def extract_data(self, start_page: int = 1) -> List:

        logger.info("")
        logger.info("🔍 Détection des pages de données... ")

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

        val = 38
        self._get_tables_and_captions(val)
        self.buscar_captions_refinado(val)
        self.buscar_captions_inteligente(val)



        return []
    

    def _get_tables_and_captions(self, page_number: int):

        with pdfplumber.open(self.file) as pdf:
            total_pages = len(pdf.pages)
            if page_number < 1 or page_number > len(pdf.pages):
                logging.error(f"Numéro de page invalide: {page_number}. "
                                f"Le PDF ne comporte que {total_pages} pages.")
                raise ValueError(f"Le PDF ne comporte que {total_pages} pages.")
            
            page = pdf.pages[page_number - 1]
           
            # Détecter les tables (objets Table)
            table_objects = page.find_tables()

            logger.debug(f"Page : {page_number} — {len(table_objects)} table(s) détectée(s)")
            for i, t in enumerate(table_objects, start=1):
                x0, y0, x1, y1 = t.bbox
                logger.debug(f"Table {i}: bbox = ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
            
            # Extraire les tables
            logger.debug(f"")
            for i, t in enumerate(table_objects, start=1):
                table_data = t.extract()  

                # création pandas dataframe
                df = pd.DataFrame(table_data)
                # Nettoyage du DataFrame
                df = df.dropna(how="all").reset_index(drop=True)
                df.columns = df.iloc[0] if not df.empty else None
                df = df[1:] if len(df) > 1 else df    

                logger.debug(f"Table {i}")
                logger.debug("Imprimer uniquement le .head() du dataframe\n" + tabulate(df.head(), headers='keys', tablefmt='psql'))



    def buscar_captions_refinado(self, page_number, margen=100):
        """
        Busca captions justo encima de cada tabla, evitando incluir títulos de página.
        """
        resultados = []
        margen_superior=120

        with pdfplumber.open(self.file) as pdf:
            page = pdf.pages[page_number - 1]

            tables = sorted(page.find_tables(), key=lambda t: t.bbox[1])  # de arriba a abajo
            words = page.extract_words(use_text_flow=True)

            for i, t in enumerate(tables, start=1):
                x0, y_top, x1, y_bottom = t.bbox

                # límite superior: borde inferior de la tabla anterior
                y_limite_inferior = tables[i-2].bbox[3] if i > 1 else 0

                # 1️buscar solo entre el borde superior y la tabla anterior
                encima = [
                    w for w in words
                    if y_limite_inferior < w["bottom"] < y_top
                    and y_top - w["bottom"] < margen_superior
                    and x0 - 20 < w["x0"] < x1 + 20
                ]

                #  agrupar por línea y ordenar
                lineas = {}
                for w in encima:
                    y_line = round(w["top"], -1)
                    lineas.setdefault(y_line, []).append(w["text"])

                sorted_lines = sorted(lineas.items(), key=lambda kv: kv[0])
                ultimas_lineas = [" ".join(v) for _, v in sorted_lines[-2:]]
                caption = " ".join(ultimas_lineas).strip()

                #  limpiar título global y restos
                caption = re.sub(r"BAROMÈTRE DES PERSONNALITÉS.*", "", caption, flags=re.I)
                caption = re.sub(r"^\d+\s+\S+", "", caption).strip()  # elimina si empieza con número
                caption = re.sub(r"\s{2,}", " ", caption)

                resultados.append({
                    "tabla_id": i,
                    "bbox": t.bbox,
                    "caption": caption
                })

                print(f"Tabla {i}: '{caption}'")

        return resultados
                


    def buscar_captions_inteligente(self, page_number, margen_vertical=200, margen_horizontal=150):
        """
        Busca captions justo encima de cada tabla, con heurísticas robustas.
        - Amplía márgenes verticales y horizontales.
        - Usa patrones de texto típicos ("Électeurs", "Concernant").
        """
        resultados = []

        with pdfplumber.open(self.file) as pdf:
            page = pdf.pages[page_number - 1]
            tables = sorted(page.find_tables(), key=lambda t: t.bbox[1])  # de arriba a abajo
            words = page.extract_words(use_text_flow=True)
            full_text = page.extract_text() or ""

            for i, t in enumerate(tables, start=1):
                x0, y_top, x1, y_bottom = t.bbox
                y_limite_inferior = tables[i-2].bbox[3] if i > 1 else 0

                # 1️⃣ Buscar texto en el margen ampliado
                encima = [
                    w for w in words
                    if y_limite_inferior < w["bottom"] < y_top
                    and y_top - w["bottom"] < margen_vertical
                    and (x0 - margen_horizontal) < w["x0"] < (x1 + margen_horizontal)
                ]

                # 2️ Agrupar líneas
                lineas = {}
                for w in encima:
                    y_line = round(w["top"], -1)
                    lineas.setdefault(y_line, []).append(w["text"])

                sorted_lines = sorted(lineas.items(), key=lambda kv: kv[0])
                ultimas_lineas = [" ".join(v) for _, v in sorted_lines[-3:]]
                caption = " ".join(ultimas_lineas).strip()

                # 3️ Limpieza de ruido
                caption = re.sub(r"BAROMÈTRE DES PERSONNALITÉS.*", "", caption, flags=re.I)
                caption = re.sub(r"^\d+\s+\S+", "", caption).strip()
                caption = re.sub(r"\s{2,}", " ", caption)

                # 4️ Heurística de rescate (buscar directamente texto tipo 'Électeurs …')
                if not caption or not re.search(r"Électeurs|Concernant", caption, flags=re.I):
                    regex_caption = re.search(r"(Électeurs[^\\n]+|Concernant[^\\n]+)", full_text, re.I)
                    caption = regex_caption.group(1).strip() if regex_caption else caption

                resultados.append({
                    "tabla_id": i,
                    "bbox": t.bbox,
                    "caption": caption
                })

                print(f" Tabla {i}: '{caption}'")

        return resultados