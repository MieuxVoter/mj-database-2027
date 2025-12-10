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
                # Normaliser les colonnes avant de filtrer et de renommer
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

        logger.info("📦  Extraction et construction des CSV...")
        logger.info("")
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

