import pathlib
import logging
from typing import List, Dict, Any
from pdfminer.high_level import extract_pages
from core.settings.logger import setup_logging
from core.population import Population
from mining.mining_CLUSTER17.cluster17_extractor import Cluster17PDFExtractor
from mining.mining_CLUSTER17.cluster17_builder import Cluster17CSVBuilder

setup_logging()
logger = logging.getLogger("app")


class Cluster17:

    def __init__(self, file: pathlib.Path, poll_id: str, population: Population | None = None) -> None:

        self.file = file
        self.poll_id = poll_id
        self.population = population

    def process_data(self, start_page: int = 1) -> None:

        # logger.info("")
        logger.info("🔍  Détection et extraction des pages de données... ")
        logger.info("="*60)

        pages = list(extract_pages(str(self.file)))
        total_pages = len(pages)

        # Commencer l'extraction de tables et populations
        process_extractor = Cluster17PDFExtractor(self.file, self.population)

        # Détection des pages pertinentes contenant des sondages
        data_pages = []
        for page_num in range(start_page, total_pages + 1):
            page_layout = pages[page_num - 1]

            if process_extractor._is_page_relevant(page_layout):
                data_pages.append(page_num)

        logger.info(f"📊  {len(data_pages)} page(s) de données détectée(s) :")
        logger.info("")
        
        # Obtenir les tableaux et les populations 
        surveys : List[Dict[str, Any]] = []
        for page in data_pages:
            survey_data = process_extractor._get_tables_population(page)
            for table in survey_data:
                logger.info(f"• Page {page} : {table['Étiquette de population']}")

            surveys.extend(survey_data)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("")
            logger.debug("="*60)
            logger.debug("Résumé des tableaux et des populations obtenus")
            logger.debug("="*60)
            logger.debug("")
            for survey in surveys:
                logger.debug(f"📄 Page: {survey['Page']}")
                logger.debug(f"🧠 Population: {survey['Étiquette de population']}")
                logger.debug(f"🧾 Table id: {survey['Table id']}")
                logger.debug(f"📏 Dimensions de la table: {survey['df'].shape}")
                logger.debug("")

        # Commencer la création des CSV
        process_builder = Cluster17CSVBuilder(self.file.parent, self.poll_id)

        logger.info("")
        logger.info("📦  Extraction et construction des CSV...")
        logger.info("="*60)
        nb_csv_created = 0
        for survey in surveys:
            csv_created = process_builder.create_csv(survey)
            if csv_created:
                nb_csv_created += 1

        logger.info("")
        logger.info("="*60)
        logger.info(f"✅  {nb_csv_created} fichier(s) CSV généré(s)")
        logger.info("")




        



        return None