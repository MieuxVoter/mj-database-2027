import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class BasePipeline(ABC):
    """
    Classe de base abstraite pour les pipelines d'extraction et de construction
    de données (Cluster17, etc.).

    Elle fournit une structure commune et des validations initiales.
    """

    def __init__(self, pdf_path: Path, poll_id: str):
        """
        Initialise le processus du pipeline.

        Args:
            file : Path
                Chemin complet vers le fichier PDF à analyser.
            poll_id : str
                Identifiant du sondage (ex. "pt4").
        """

        self.pdf_path: Path = pdf_path
        self.poll_id: str = poll_id
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
        if not isinstance(self.poll_id, str):
            self.logger.error("Le paramètre 'poll_id' doit être une chaîne de caractères.")
            raise TypeError("Le paramètre 'poll_id' doit être une chaîne de caractères.")

    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        """Extraire les données de la source (PDF)"""
        pass

    @abstractmethod
    def build(self, extracted_data) -> int:
        """Construisez les artefacts (CSV, TXT, etc.)"""
        pass

    def _cleanup_existing_files(self, extensions=("csv", "txt")) -> None:
        """
        Supprime les anciens fichiers avant le traitement si nécessaire.
        """
        try:
            base_path = self.pdf_path.parent
            files_to_delete = []

            # Rechercher tous les fichiers correspondants
            for ext in extensions:
                files_to_delete.extend(list(Path(base_path).rglob(f"*.{ext}")))

            if not files_to_delete:
                self.logger.info(f"Aucun fichier .csv/.txt trouvé à supprimer dans : {base_path}")
                return

            for f in files_to_delete:
                try:
                    f.unlink()
                except Exception as e:
                    self.logger.error(f"Impossible de supprimer le fichier : {f} ({e})")

            self.logger.info(f"{len(files_to_delete)} ancien(s) fichier(s) supprimé(s) dans : {base_path}")

        except Exception as e:
            self.logger.error(f"Erreur inattendue lors du nettoyage des fichiers : {e}")

    def run(self):
        """
        Exécute le pipeline complet.
        """
        try:
            self.logger.info("🧹 Nettoyage des anciens fichiers avant traitement...")
            self.logger.info("=" * 70)
            self._cleanup_existing_files()
            self.logger.info("")

            self.logger.info("🔍  Détection et extraction des pages de données... ")
            self.logger.info("=" * 70)
            data = self.extract()
            self.logger.info("")

            self.logger.info("📦  Extraction et construction des CSV...")
            self.logger.info("=" * 70)
            nb_csv_created = self.build(data)
            self.logger.info("")

            self.logger.info("=" * 70)
            self.logger.info(f"✅  {nb_csv_created} fichier(s) CSV généré(s)")
            self.logger.info("")

        except Exception as e:
            self.logger.error(f"Erreur inattendue dans le pipeline : {e}")
            raise
