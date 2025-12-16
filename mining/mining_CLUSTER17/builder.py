import pathlib
import logging
from pathlib import Path
import pandas as pd
from typing import Dict, Any
from core.helpers import normalize, ensure_newline, survey_exists
from mining.mining_CLUSTER17.anomaly_detector import AnomalyDetector


class CSVBuilder:
    """
    Classe responsable de la génération et du nettoyage des fichiers CSV
    pour le baromètre Cluster17.
    """

    # Chemin du fichier de référence des candidats et polls
    CANDIDATES_CSV: Path = Path(__file__).resolve().parent.parent.parent / "candidates.csv"
    POLLS_CSV: Path = Path(__file__).resolve().parent.parent.parent / "polls.csv"

    # Colonnes à conserver
    COLUMNS_KEEP = [
        "personnalite",
        "vous la soutenez",
        "vous l'appreciez",
        "vous ne l'appreciez pas",
        "vous n'avez pas d'avis sur elle/ vous ne la connaissez pas",
    ]

    # Mappage des nouveaux noms de colonnes
    RENAME_COLUMNS = {
        "vous la soutenez": "intention_mention_1",
        "vous l'appreciez": "intention_mention_2",
        "vous ne l'appreciez pas": "intention_mention_3",
        "vous n'avez pas d'avis sur elle/ vous ne la connaissez pas": "intention_mention_4",
    }

    EXPECTED_COLS = {
        "personnalite",
        "intention_mention_1",
        "intention_mention_2",
        "intention_mention_3",
        "intention_mention_4",
    }

    def __init__(self, path: pathlib.Path, poll_type: str) -> None:
        """
        Initialise le constructeur du générateur CSV.

        Args:
            path : Path
                Répertoire où seront enregistrés les fichiers CSV.
            poll_type : str
                Identifiant du sondage (ex. "cluster17_202511").
        """

        self.path: Path = path
        self.poll_type: str = poll_type
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """
        Valide les paramètres d'entrée.
        """
        if not isinstance(self.path, Path):
            self.logger.error("Le paramètre 'path' doit être une instance de pathlib.Path.")
            raise TypeError("Le paramètre 'path' doit être une instance de pathlib.Path.")
        if not self.path.exists():
            self.logger.error(f"Le répertoire est introuvable : {self.path}")
            raise FileNotFoundError(f"Le répertoire spécifié est introuvable : {self.path}")

        if not isinstance(self.poll_type, str):
            self.logger.error("Le paramètre 'poll_type' doit être une chaîne de caractères.")
            raise TypeError("Le paramètre 'poll_type' doit être une chaîne de caractères.")

    def _clean_survey_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie et normalise les données d'une enquête Cluster17.

        Étapes principales :
        1. Normalise les noms de colonnes.
        2. Filtre uniquement les colonnes d'intérêt (COLUMNS_KEEP).
        3. Renomme les colonnes selon le mapping défini (RENAME_COLUMNS).
        4. Supprime le symbole '%' et convertit les valeurs en entiers.
            (Toutes les colonnes sauf 'personnalite' sont traitées.)

        Args:
            df: pd.DataFrame
                Données brutes extraites d'une table du baromètre.

        Returns:
            pd.DataFrame
                Données nettoyées, prêtes pour export CSV ou fusion avec candidats.
        """

        df.columns = [normalize(col) for col in df.columns]
        df = df.filter(items=self.COLUMNS_KEEP)
        df = df.rename(columns=self.RENAME_COLUMNS)

        for col in df.columns:
            if col != "personnalite":
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace("%", "", regex=False)
                    .str.strip()
                    .replace("", pd.NA)
                    .astype(float)
                    .astype("Int64")
                )

        return df

    def _merge_candidates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Fusionne les données d'enquête avec le fichier de référence des candidats.

        Cette méthode associe à chaque personnalité son identifiant unique (`candidate_id`)
        en se basant sur une comparaison de noms normalisés (sans accents, minuscules, etc.).
        Elle renvoie à la fois le DataFrame enrichi et le nombre d'identifiants non trouvés.

        Étapes principales :
        1. Vérifier l'existence du fichier de référence `candidates.csv`.
        2. Lire et normaliser les noms et prénoms du fichier des candidats.
        3. Normaliser la colonne `personnalite` du DataFrame d'enquête.
        4. Fusionner les deux DataFrames sur le nom complet normalisé.
        5. Réordonner les colonnes et signaler les identifiants manquants.

        Args:
            df : pd.DataFrame
                Données nettoyées provenant d'une table du baromètre.

        Returns:
            Dict[str, Any]
                - Si succès : {"df": DataFrame fusionné, "missing": nombre d'identifiants manquants}.
        """

        if not self.CANDIDATES_CSV.exists():
            raise FileNotFoundError(
                f"Le fichier << candidates.csv >> est requis mais introuvable : {self.CANDIDATES_CSV}"
            )
            return None

        ORDERED_COLUMNS = [
            "personnalite",
            "candidate_id",
            "intention_mention_1",
            "intention_mention_2",
            "intention_mention_3",
            "intention_mention_4",
        ]

        df_candidates = pd.read_csv(self.CANDIDATES_CSV)
        df_candidates["name_norm"] = df_candidates["name"].apply(normalize)
        df_candidates["surname_norm"] = df_candidates["surname"].apply(normalize)
        df_candidates["personnalite_norm"] = (
            df_candidates["name_norm"].str.cat(df_candidates["surname_norm"], sep=" ").str.strip()
        )

        df["personnalite_norm"] = df["personnalite"].apply(normalize)

        df_merged = df.merge(df_candidates[["personnalite_norm", "candidate_id"]], on=["personnalite_norm"], how="left")

        df_merged.drop(columns=["personnalite_norm"], inplace=True)
        df_merged = df_merged[ORDERED_COLUMNS]
        nb_missing = df_merged["candidate_id"].isnull().sum()

        return {"df": df_merged, "missing": nb_missing}

    def build_all(self, survey_metadata, surveys) -> int:
        """
        Crée le fichier CSV nettoyé et fusionné pour une population donnée du baromètre Cluster17.

        Cette méthode exécute l’ensemble du pipeline pour un tableau extrait :
        1. Nettoyage et normalisation des données brutes issues du PDF.
        2. Fusion avec le fichier de référence des candidats (`candidates.csv`).
        3. Génération du fichier CSV final dans le répertoire de sortie.
        4. Détection automatique et export des anomalies éventuelles (Cluster17AnomalyDetector).

        Args:
            List[Dict[str, Any]]:
                Une liste combinée de tous les tableaux extraits.

        Returns:
            int
                Nombre des fichiers .csv générés.
        """

        nb_csv_created = 0

        for survey in surveys:

            # Construire le chemin de sortie
            filename = f"{self.path.name}_{survey['Population']}.csv"
            output_path = Path(self.path) / filename

            # -----------------------------------------------------------------
            # Nettoyage et normalisation des données brutes
            # -----------------------------------------------------------------
            df = self._clean_survey_data(survey["df"].copy())

            if df.empty:
                raise ValueError(
                    "Le tableau est invalide: DataFrame vide | "
                    f"population={survey.get('Étiquette de population', 'Inconnue')} | "
                    f"page={survey.get('Page', 'N/A')}"
                )

            missing_cols = self.EXPECTED_COLS - set(df.columns)
            if missing_cols:
                raise ValueError(
                    "Le tableau est invalide: colonnes obligatoires manquantes | "
                    f"colonnes={sorted(missing_cols)} | "
                    f"population={survey.get('Étiquette de population', 'Inconnue')} | "
                    f"page={survey.get('Page', 'N/A')}"
                )

            # -----------------------------------------------------------------
            # Fusion avec le fichier de référence des candidats
            # -----------------------------------------------------------------
            result = self._merge_candidates(df)
            df = result["df"]

            # -----------------------------------------------------------------
            # Écriture et détails du fichier CSV
            # -----------------------------------------------------------------
            try:
                df.to_csv(output_path, index=False, encoding="utf-8")
                self.logger.info(f"✅ CSV généré : {output_path}")
                self.logger.info(f"\t📄 Page: {survey.get('Page', 'N/A')}")
                self.logger.info(f"\t📊 {df['candidate_id'].notnull().sum()} candidats trouvés")
                self.logger.info(f"\t🧠 Population : {survey.get('Étiquette de population', 'Inconnue')}")
                self.logger.info(f"\t📋 Type : {self.poll_type}")
            except PermissionError as e:
                self.logger.error(f"Permission refusée pour écrire {output_path} : {e}")
                continue

            # -----------------------------------------------------------------
            # Génération du rapport d’anomalies
            # -----------------------------------------------------------------
            anomalies = AnomalyDetector(df, self.path)
            df = anomalies.analyze(survey)

            # -----------------------------------------------------------------
            # Ajouter sondage dedans polls.csv
            # -----------------------------------------------------------------
            ensure_newline(self.POLLS_CSV)

            poll_id = self.path.name

            if survey_exists(self.POLLS_CSV, poll_id, survey["Population"].value):
                self.logger.info(
                    f"\t♻️  Sondage existe déjà dans << polls.csv >> (poll_id={poll_id}, population={survey['Population'].value}) — passer"
                )
            else:
                new_survey = {
                    "poll_id": poll_id,
                    "poll_type": self.poll_type,
                    "nb_people": survey_metadata["sample_size"],
                    "start_date": survey_metadata["start_date"],
                    "end_date": survey_metadata["end_date"],
                    "folder": str(self.path),
                    "population": survey["Population"].value,
                    "pdf_url": survey_metadata["pdf_url"],
                }

                df_new_survey = pd.DataFrame([new_survey])
                df_new_survey.to_csv(self.POLLS_CSV, mode="a", header=False, index=False, encoding="utf-8")
                self.logger.info(
                    f"\t➕  Sondage ajoutée dans << polls.csv >> (poll_id={poll_id}, population={survey['Population'].value})"
                )

            nb_csv_created += 1

        return nb_csv_created
