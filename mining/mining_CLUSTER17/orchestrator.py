import pathlib
import logging
from typing import List, Dict, Any
from mining.base_pipeline import BasePipeline
from mining.mining_CLUSTER17.extractor import PDFExtractor
from mining.mining_CLUSTER17.builder import CSVBuilder


class Cluster17Pipeline(BasePipeline):
    """
    Classe orchestratrice pour l'extraction et la construction des données
    du baromètre Cluster17 à partir d'un fichier PDF.
    """

    def __init__(self, pdf_path: pathlib.Path, poll_id: str) -> None:
        """
        Initialise le pipeline Cluster17.

        Args:
            file : Path
                Chemin complet vers le fichier PDF à analyser.
            poll_id : str
                Identifiant du sondage (ex. "cluster17_202511").
        """

        super().__init__(pdf_path, poll_id)
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract(self) -> List[Dict[str, Any]]:
        """
        Extrait les données brutes depuis le fichier PDF (tables + métadonnées).
        """
        extractor = PDFExtractor(self.pdf_path)
        data = extractor.extract_all()
        return data

    def build(self, extracted_data) -> int:
        """
        Générer les fichiers CSV et détecter les anomalies
        """
        builder = CSVBuilder(self.pdf_path.parent, self.poll_id)
        nb_csv_created = builder.build_all(extracted_data)
        return nb_csv_created
