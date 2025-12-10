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

    def __init__(self, file: pathlib.Path, population: Population | None = None) -> None:

        self.file = file
        self.population = population

    def extract_data(self, start_page: int = 1) -> None:

        logger.info("")
        logger.info("🔍 Détection et extraction des pages de données... ")

        pages = list(extract_pages(str(self.file)))
        total_pages = len(pages)

        process_extractor = Cluster17PDFExtractor(self.file, self.population)

        # Détection des pages pertinentes contenant des sondages
        data_pages = []
        for page_num in range(start_page, total_pages + 1):
            page_layout = pages[page_num - 1]

            if process_extractor._is_page_relevant(page_layout):
                data_pages.append(page_num)

        logger.info(f"📊 {len(data_pages)} page(s) de données détectée(s) :")
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
            logger.debug("="*50)
            logger.debug("Résumé des tableaux et des populations obtenus")
            logger.debug("="*50)
            logger.debug("")
            for survey in surveys:
                logger.debug(f"📄 Page: {survey['Page']}")
                logger.debug(f"🧠 Population: {survey['Étiquette de population']}")
                logger.debug(f"🧾 Table id: {survey['Table id']}")
                logger.debug(f"📏 Dimensions de la table: {survey['df'].shape}")
                logger.debug("")

        # Commencer la création des CSV
        process_builder = Cluster17CSVBuilder(self.file.parent)

        # for survey in surveys:
        #     process_builder.create_csv(survey)

        process_builder.create_csv(surveys[1])





        



        return None