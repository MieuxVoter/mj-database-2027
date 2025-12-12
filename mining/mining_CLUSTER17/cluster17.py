import pathlib
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any
from pdfminer.high_level import extract_pages
from core.settings.logger import setup_logging
from core.population import Population
from mining.mining_CLUSTER17.cluster17_extractor import Cluster17PDFExtractor
from mining.mining_CLUSTER17.cluster17_builder import Cluster17CSVBuilder

setup_logging()
logger = logging.getLogger("app")


class Cluster17:
    """
    Classe orchestratrice pour l'extraction et la construction des données
    du baromètre Cluster17 à partir d'un fichier PDF.
    """

    def __init__(self, file: pathlib.Path, poll_id: str, population: Optional[Population] = None) -> None:
        """
        Initialise le processus Cluster17.

        Args:
            file : Path
                Chemin complet vers le fichier PDF à analyser.
            poll_id : str
                Identifiant du sondage (ex. "cluster17_202511").
            population : Population, optionnel
                Population ou sous-échantillon concerné (ex. Population.LFI)
        """

        if not isinstance(file, Path):
            logger.error("Le paramètre 'file' doit être une instance de pathlib.Path.")
            raise TypeError("Le paramètre 'file' doit être une instance de pathlib.Path.")
        if not isinstance(poll_id, str):
            logger.error("Le paramètre 'poll_id' doit être une chaîne de caractères.")
            raise TypeError("Le paramètre 'poll_id' doit être une chaîne de caractères.")
        if population is not None and not isinstance(population, Population):
            logger.error("Le paramètre 'population' doit être une instance de Population ou None.")
            raise TypeError("Le paramètre 'population' doit être une instance de Population ou None.")

        if not file.exists():
            logger.error(f"Le fichier spécifié est introuvable : {file}")
            raise FileNotFoundError(f"Le fichier spécifié est introuvable : {file}")

        self.file: Path = file
        self.poll_id: str = poll_id
        self.population: Optional[Population] = population

    def process_data(self, start_page: int = 1) -> None:
        """
        Exécute le pipeline complet d'extraction et de transformation des données
        du baromètre Cluster17 à partir d’un fichier PDF.

        Étapes principales :
            1. Nettoyage des anciens fichiers CSV/TXT si le niveau de log est DEBUG.
            2. Lecture du fichier PDF et détection des pages pertinentes.
            3. Extraction des tableaux et populations pour chaque page détectée.
            4. Construction et export des fichiers CSV correspondants.
            5. Journalisation des erreurs et résumé des fichiers générés.

        Args
            start_page : int, optionnel
                Numéro de page à partir duquel commencer l’analyse.
                Par défaut : 1.

        Returns
            Cette méthode ne renvoie pas de valeur.
            Les résultats sont enregistrés sur disque (fichiers CSV)
            et les événements sont consignés dans les logs.
        """
        try:
            # Si le niveau de log est DEBUG, tous les fichiers `.csv` et `.txt` existants
            # dans le dossier du PDF sont supprimés avant le traitement.
            if logger.isEnabledFor(logging.DEBUG):
                try:
                    for ext in ("csv", "txt"):
                        [f.unlink() for f in Path(self.file.parent).rglob(f"*.{ext}")]
                    logger.debug("Ancien(s) fichier(s) CSV/TXT supprimé(s) (mode DEBUG).")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer certains fichiers avant traitement : {e}")

            logger.info("🔍  Détection et extraction des pages de données... ")
            logger.info("=" * 70)

            try:
                pages = list(extract_pages(str(self.file)))
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la lecture du fichier PDF : {e}")
                return

            total_pages = len(pages)

            # Commencer l'extraction de tables et populations
            process_extractor = Cluster17PDFExtractor(self.file, self.population)

            # Détection des pages pertinentes contenant des sondages
            data_pages: List[int] = []
            for page_num in range(start_page, total_pages + 1):
                try:
                    page_layout = pages[page_num - 1]
                    if process_extractor.is_page_relevant(page_layout):
                        data_pages.append(page_num)
                except Exception as e:
                    logger.error(f"Erreur inattendue lors de l’analyse de la page {page_num} : {e}")

            if not data_pages:
                logger.warning("Aucune page pertinente détectée dans ce PDF")
                return

            logger.info(f"📊  {len(data_pages)} page(s) de données détectée(s) :")
            if self.population:
                logger.info("\tSeules les sondages correspondant à la population spécifiée seront prises en compte.")
            logger.info("")

            # Obtenir les tableaux et les populations
            surveys: List[Dict[str, Any]] = []
            for page in data_pages:
                try:
                    survey_data = process_extractor.get_tables_population(page)
                    for table in survey_data:

                        if self.population:
                            if self.population == table["Population"]:
                                logger.info(f"• Page {page} : {table['Étiquette de population']}")
                                surveys.append(table)
                        else:
                            logger.info(f"• Page {page} : {table['Étiquette de population']}")
                            surveys.append(table)

                except Exception as e:
                    logger.error(f"Erreur inattendue lors de l’extraction des données de la page {page} : {e}")

            if not surveys:
                logger.warning("Aucune table extraite du PDF")
                return

            logger.info("")
            logger.info("📦  Extraction et construction des CSV...")
            logger.info("=" * 70)

            # Commencer la création des CSV
            process_builder = Cluster17CSVBuilder(self.file.parent, self.poll_id)

            nb_csv_created = 0
            for survey in surveys:
                try:
                    if process_builder.create_csv(survey):
                        nb_csv_created += 1
                except Exception as e:
                    logger.error(
                        f"Erreur inattendue lors de la création du CSV pour "
                        f"{survey.get('Étiquette de population', 'Inconnue')} : {e}"
                    )

            logger.info("")
            logger.info("=" * 70)
            logger.info(f"✅  {nb_csv_created} fichier(s) CSV généré(s)")
            logger.info("")

        except FileNotFoundError as e:
            logger.error(f"Fichier PDF introuvable : {e}")
            raise

        except Exception as e:
            logger.exception(f"Erreur inattendue lors du traitement du fichier {self.file} : {e}")
            raise
