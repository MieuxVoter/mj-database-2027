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

    REQUIRED_METADATA_FIELDS = {"poll_id", "pdf_url"}

    def __init__(self, pdf_path: Path, poll_type: str):
        """
        Initialise le processus du pipeline.

        Args:
            file : Path
                Chemin complet vers le fichier PDF à analyser.
            poll_type : str
                Identifiant du sondage (ex. "pt4").
        """

        self.pdf_path: Path = pdf_path
        self.poll_type: str = poll_type
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
        if not isinstance(self.poll_type, str):
            self.logger.error("Le paramètre 'poll_type' doit être une chaîne de caractères.")
            raise TypeError("Le paramètre 'pollpoll_type_id' doit être une chaîne de caractères.")

    @abstractmethod
    def extract(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Extraire les données de la source (PDF)"""
        pass

    @abstractmethod
    def build(self, survey_metadata, surveys) -> int:
        """Construisez les artefacts (CSV, TXT, etc.)"""
        pass

    def _validate_metadata(self) -> None:
        """
        Valide l'existence et la structure minimale du fichier metadata.txt.
        """
        metadata_file = Path(self.pdf_path.parent) / "metadata.txt"
        if not metadata_file.is_file():
            raise FileNotFoundError(f"<< metadata.txt >> requis mais absent : {metadata_file}")
        self.logger.info("✅  << metadata.txt >> détecté")

        metadata: dict[str, str] = {}
        for line_number, raw_line in enumerate(metadata_file.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()

            # ignorer lignes vides et commentaires
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                raise ValueError(f"Structure invalide dans metadata.txt " f"(ligne {line_number}) : '{raw_line}'")

            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

        missing_fields = self.REQUIRED_METADATA_FIELDS - metadata.keys()
        if missing_fields:
            raise ValueError(f"Champs obligatoires manquants dans metadata.txt : {sorted(missing_fields)}")

        self.logger.info("📄  Structure de << metadata.txt >> validée")

    def _cleanup_existing_files(self, extensions=("csv", "txt")) -> None:
        """
        Supprime les anciens fichiers avant le traitement si nécessaire.
        """
        try:
            base_path = self.pdf_path.parent
            files_to_delete = []

            # Rechercher tous les fichiers correspondants
            for ext in extensions:
                for f in base_path.rglob(f"*.{ext}"):
                    if f.name == "metadata.txt":
                        continue
                    files_to_delete.append(f)

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
            self.logger.info("📄  Validation du fichier << metadata.txt >>...")
            self.logger.info("=" * 70)
            self._validate_metadata()
            self.logger.info("")

            self.logger.info("🧹 Nettoyage des anciens fichiers avant traitement...")
            self.logger.info("=" * 70)
            self._cleanup_existing_files()
            self.logger.info("")

            self.logger.info("🔍  Détection et extraction des pages de données... ")
            self.logger.info("=" * 70)
            survey_metadata, surveys = self.extract()
            self.logger.info("")

            self.logger.info("📦  Extraction et construction des CSV...")
            self.logger.info("=" * 70)
            nb_csv_created = self.build(survey_metadata, surveys)
            self.logger.info("")

            self.logger.info("=" * 70)
            self.logger.info(f"✅  {nb_csv_created} fichier(s) CSV généré(s)")
            self.logger.info("")

        except FileNotFoundError as e:
            self.logger.error(f"Erreur de configuration : {e}")
            raise

        except Exception as e:
            self.logger.error(f"Erreur inattendue dans le pipeline : {e}")
            raise
