import pathlib
import logging
from pathlib import Path
import pandas as pd
from typing import Dict, Any
from core.settings.logger import setup_logging
from core.helpers import normalize
from core.population import Population
from mining.mining_CLUSTER17.cluster17_anomaly_detector import Cluster17AnomalyDetector

setup_logging()
logger = logging.getLogger("app")


class Cluster17CSVBuilder:
    """
    Classe responsable de la génération et du nettoyage des fichiers CSV
    pour le baromètre Cluster17.
    """

    def __init__(self, path: pathlib.Path, poll_id: str) -> None:
        """
        Initialise le constructeur du générateur CSV.

        Args:
            path : Path
                Répertoire où seront enregistrés les fichiers CSV.
            poll_id : str
                Identifiant du sondage (ex. "cluster17_202511").
        """

        if not isinstance(path, Path):
            logger.error("Le paramètre 'path' doit être une instance de pathlib.Path.")
            raise TypeError("Le paramètre 'path' doit être une instance de pathlib.Path.")
        if not isinstance(poll_id, str):
            logger.error("Le paramètre 'poll_id' doit être une chaîne de caractères.")
            raise TypeError("Le paramètre 'poll_id' doit être une chaîne de caractères.")

        if not path.exists():
            logger.error(f"Le répertoire est introuvable : {path}")
            raise FileNotFoundError(f"Le répertoire spécifié est introuvable : {path}")

        self.path: Path = path
        self.poll_id: str = poll_id

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

    # Chemin du fichier de référence des candidats
    CANDIDATES_CSV: Path = Path(__file__).resolve().parent.parent.parent / "candidates.csv"

    EXPECTED_COLS = {
        "personnalite",
        "intention_mention_1",
        "intention_mention_2",
        "intention_mention_3",
        "intention_mention_4",
    }

    def __clean_survey_data(self, df: pd.DataFrame) -> pd.DataFrame:
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

    def __merge_candidates(self, df: pd.DataFrame, population: Population) -> Dict[str, Any] | None:
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
            population : Population
                opulation ou sous-échantillon concerné (ex : "Électeurs LFI aux Européennes 2024").

        Returns:
            Dict[str, Any] | None
                - Si succès : {"df": DataFrame fusionné, "missing": nombre d'identifiants manquants}.
                 Si erreur ou fichier manquant : None.
        """

        if not self.CANDIDATES_CSV.exists():
            logger.error(f"Le fichier << candidates.csv >> est introuvable : {self.CANDIDATES_CSV}")
            return None

        try:

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

            df_merged = df.merge(
                df_candidates[["personnalite_norm", "candidate_id"]], on=["personnalite_norm"], how="left"
            )

            df_merged.drop(columns=["personnalite_norm"], inplace=True)
            df_merged = df_merged[ORDERED_COLUMNS]
            nb_missing = df_merged["candidate_id"].isnull().sum()

            return {"df": df_merged, "missing": nb_missing}

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la fusion des candidats : {e}")
            return None

    def create_csv(self, survey: Dict[str, Any], overwrite: bool = False) -> bool:
        """
        Crée le fichier CSV nettoyé et fusionné pour une population donnée du baromètre Cluster17.

        Cette méthode exécute l’ensemble du pipeline pour un tableau extrait :
        1. Nettoyage et normalisation des données brutes issues du PDF.
        2. Fusion avec le fichier de référence des candidats (`candidates.csv`).
        3. Génération du fichier CSV final dans le répertoire de sortie.
        4. Détection automatique et export des anomalies éventuelles (Cluster17AnomalyDetector).

        Args
            survey : Dict[str, Any]
                Dictionnaire décrivant la population et le contexte d’extraction du sondage.
                Chaque élément représente un tableau et son contexte textuel associé.
                    - "Population" : instance de Population ou chaîne identifiant la population.
                    - "Page" : numéro de page du PDF (int, optionnel).
                    - "Étiquette de population" : description textuelle du sous-échantillon.
                    - "df" : DataFrame brut de la table extraite.
            overwrite : bool, optionnel
                Si True, écrase le fichier existant.
                Si False (par défaut), saute la création si le fichier existe déjà.

        Returns
            bool
                True  → si le fichier CSV a été généré avec succès.
                False → si une erreur est survenue à une quelconque étape du processus.
        """

        # Construire le chemin de sortie
        filename = f"{self.path.name}_{survey['Population']}.csv"
        output_path = Path(self.path) / filename

        # Vérifier l'existence du fichier
        if output_path.exists() and not overwrite:
            logger.warning(f"⏭️  {filename} existe déjà (utilizez --overwrite pour écraser)")
            return False

        try:

            try:
                df = self.__clean_survey_data(survey["df"].copy())

                if df.empty:
                    logger.warning(f"Le tableau pour {survey.get('population', 'Inconnue')} est vide. CSV non créé.")
                    return False
            except Exception as e:
                logger.error(
                    f"Erreur inattendue lors du nettoyage des données pour {survey.get('Population', 'Inconnue')} : {e}"
                )

            missing_cols = self.EXPECTED_COLS - set(df.columns)
            if missing_cols:
                logger.error(f"Colonnes manquantes dans {filename} : {missing_cols}")
                return False

            result = self.__merge_candidates(df, survey["Population"])
            if not result:
                logger.error(f"Échec de la fusion des candidats pour {survey.get('population', 'Inconnue')}")
                return False

            df = result["df"]

            try:
                df.to_csv(output_path, index=False, encoding="utf-8")

                logger.info(f"✅ CSV généré : {output_path}")
                logger.info(f"\t📄 Page: {survey.get('Page', 'N/A')}")
                logger.info(f"\t📊 {df["candidate_id"].notnull().sum()} candidats trouvés")
                logger.info(f"\t🧠 Population : {survey.get('Étiquette de population', 'Inconnue')}")
                logger.info(f"\t📋 Type : {self.poll_id}")
            except Exception as e:
                logger.error(f"Erreur inattendue lors de l’écriture du fichier CSV {filename} : {e}")
                return False

            # Génération du rapport d’anomalies
            anomalies = Cluster17AnomalyDetector(df, self.path)
            anomalies.generate_anomaly_report(survey)

            return True

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création du CSV {filename} : {e}")
            return False
