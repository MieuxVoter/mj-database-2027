import pathlib
import logging
from pathlib import Path
import pandas as pd
from typing import Dict, Any 
from core.settings.logger import setup_logging
from core.helpers import normalize
from core.population import Population

setup_logging()
logger = logging.getLogger("app")


class Cluster17CSVBuilder:

    def __init__(self, path: pathlib.Path):
        
        self.path = path

    COLUMNS_KEEP = [
        "personnalite",
        "vous la soutenez",
        "vous l'appreciez",
        "vous ne l'appreciez pas",
        "vous n'avez pas d'avis sur elle/ vous ne la connaissez pas"
    ]

    RENAME_COLUMNS = {
        "vous la soutenez": "intention_mention_1",
        "vous l'appreciez": "intention_mention_2",
        "vous ne l'appreciez pas": "intention_mention_3",
        "vous n'avez pas d'avis sur elle/ vous ne la connaissez pas": "intention_mention_4"
    }

    CANDIDATES_CSV = pathlib.Path(__file__).parent.parent.parent / "candidates.csv"

    def clean_survey_data(self, df: pd.DataFrame) -> pd.DataFrame:
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
    
    def merge_candidates(self, df: pd.DataFrame, population: Population) -> Dict[str, Any] | None:
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
        --------
            Dict[str, Any] | None
                - Si succès : {"df": DataFrame fusionné, "missing": nombre d'identifiants manquants}.
                 Si erreur ou fichier manquant : None.
        """

        if not self.CANDIDATES_CSV.exists():
            logger.error(f"Le fichier << candidates.csv >> est introuvable : {self.CANDIDATES_CSV}")
            return None

        try:

            ORDERED_COLUMNS = [
                "personnalite", "candidate_id", "intention_mention_1",
                 "intention_mention_2", "intention_mention_3", "intention_mention_4"
            ]

            df_candidates = pd.read_csv(self.CANDIDATES_CSV)
            df_candidates["name_norm"] = df_candidates["name"].apply(normalize)
            df_candidates["surname_norm"] = df_candidates["surname"].apply(normalize)
            df_candidates["personnalite_norm"] = (
                df_candidates["name_norm"].str.cat(df_candidates["surname_norm"], sep=" ").str.strip()
            )

            df["personnalite_norm"] = df["personnalite"].apply(normalize)

            df_merged = df.merge(
                df_candidates[["personnalite_norm", "candidate_id"]],
                on=["personnalite_norm"],
                how="left"
            )

            df_merged.drop(columns=["personnalite_norm"], inplace=True)
            df_merged = df_merged[ORDERED_COLUMNS]
            nb_missing = df_merged["candidate_id"].isnull().sum()

            return {"df": df_merged, "missing": nb_missing}
        
        except Exception as e:
            logger.error(f"Erreur lors de la fusion des candidats : {e}")
            return None






    def create_csv(self, survey: Dict[str, Any], overwrite: bool = False) -> bool:

        logger.info("")

        # Construire le chemin de sortie
        filename = f"{self.path.name}_{survey['Population']}.csv"
        output_path = Path(self.path) / filename

        # Vérifier l'existence du fichier
        if output_path.exists() and not overwrite:
            logger.warning(f"⏭️  {filename} existe déjà (utilizez --overwrite pour écraser)")
            return False
        
        df = self.clean_survey_data(survey['df'].copy())
        result = self.merge_candidates(df, survey['Population'])

        if result:
            df = result["df"]
            nb_missing = result["missing"]
            df.to_csv(output_path, index=False, encoding="utf-8")
            logger.info(f"✅ CSV généré : {output_path}")
            logger.info(f"\t📊 {df["candidate_id"].notnull().sum()} candidats trouvés")
            if nb_missing > 0:
                logger.warning(
                    f"\t{nb_missing} identifiant(s) de candidat introuvable(s). "
                    f"Vérifiez le fichier d’anomalies associé à la population « {survey['Population']} »."
                )
            logger.info(f"\t🧠 Population : {survey['Étiquette de population']}")
            logger.info(f"\t📋 Type : pt2") ####--> a CAMBIAR











        return True

