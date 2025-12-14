import logging
import pandas as pd
import pathlib
from pathlib import Path
from typing import Dict, Any


class AnomalyDetector:
    """
    Classe de détection et de rapport d’anomalies pour les fichiers CSV du baromètre Cluster17.
    Vérifie les identifiants manquants et les incohérences dans les totaux d’intention
    """

    REQUIRED_COLUMNS_CANDIDATE = {"candidate_id", "personnalite"}

    REQUIRED_COLUMNS_INTENTION = {
        "intention_mention_1",
        "intention_mention_2",
        "intention_mention_3",
        "intention_mention_4",
    }

    def __init__(self, df: pd.DataFrame, path: pathlib.Path) -> None:
        """
        Initialise le constructeur du du générateur d'anomalies TXT.

        Args:
            df (pd.DataFrame): DataFrame du sondage avec les colonnes intention_mention_1..4

            path (Path): Répertoire où seront enregistrés les anomalies en fichier TXT.
        """
        self.df: pd.DataFrame = df.copy()
        self.path: Path = path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """
        Valide les paramètres d'entrée.
        """
        if not isinstance(self.df, pd.DataFrame):
            self.logger.error("Le paramètre 'df' doit être un objet pandas.DataFrame")
            raise TypeError("Le paramètre 'df' doit être un objet pandas.DataFrame")
        if self.df.empty:
            self.logger.error("Le paramètre 'df' doit être un objet pandas.DataFrame")
            raise TypeError("Le paramètre 'df' doit être un objet pandas.DataFrame")

        if not isinstance(self.path, Path):
            self.logger.error("Le paramètre 'path' doit être une instance de pathlib.Path.")
            raise TypeError("Le paramètre 'path' doit être une instance de pathlib.Path.")
        if not self.path.exists():
            self.logger.error(f"Le répertoire est introuvable : {self.path}")
            raise FileNotFoundError(f"Le répertoire spécifié est introuvable : {self.path}")

    def __get_missing_candidates_id(self) -> Dict[str, Any]:
        """
        Détecte les lignes du DataFrame qui ne possèdent pas de valeur valide dans la colonne `candidate_id`.

        Args:
            df (pd.DataFrame): DataFrame du sondage avec les colonnes intention_mention_1..4

        Returns:
            Dict[str, Any]: Un dictionnaire avec les clés suivantes
                {
                    "count": int,  # Nombre total de lignes sans `candidate_id`.
                    "rows": (`List[str]`): Liste contenant les noms des personnalités concernées.
                }
        """

        try:

            missing_cols = self.REQUIRED_COLUMNS_CANDIDATE - set(self.df.columns)
            if missing_cols:
                raise KeyError(f"Colonnes manquantes dans le DataFrame : {missing_cols}")

            # Détecter les valeurs nulles ou vides dans candidate_id
            mask_missing = self.df["candidate_id"].isna() | (self.df["candidate_id"].astype(str).str.strip() == "")

            # Extraire les noms des personnalités dont l'identifiant de candidat est manquant
            missing_rows = self.df.loc[mask_missing, "personnalite"].dropna().tolist()

            return {"count": len(missing_rows), "names": missing_rows}

        except KeyError as e:
            self.logger.error(f"Erreur : {e}")
            raise

        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la détection des candidats manquants: {e}")
            return {"count": 0, "names": []}

    def __get_inconsistent_intentions(self) -> Dict[str, Any]:
        """
        Renvoie les personnalités dont la somme des intentions est différente de 100.

        Args:
            df (pd.DataFrame): DataFrame avec les colonnes intention_mention_1..4

        Returns:
            Dict[str, Any]: Un dictionnaire avec les clés suivantes
                {
                    "count": int,  # nombre d'incohérences
                    "rows": List[Dict[str, Any]]  # Liste des dicts avec détails par candidat
                }
        """
        try:

            required_columns = self.REQUIRED_COLUMNS_CANDIDATE | self.REQUIRED_COLUMNS_INTENTION

            missing_cols = required_columns - set(self.df.columns)
            if missing_cols:
                raise KeyError(f"Colonnes manquantes dans le DataFrame : {missing_cols}")

            # Convertir en numérique pour des raisons de sécurité
            self.df[list(self.REQUIRED_COLUMNS_INTENTION)] = self.df[list(self.REQUIRED_COLUMNS_INTENTION)].apply(
                pd.to_numeric, errors="coerce"
            )

            # Calculer la somme des intentions
            self.df["total_intention"] = self.df[list(self.REQUIRED_COLUMNS_INTENTION)].sum(axis=1, skipna=True)

            # Filtrer les valeurs où le total est différent de 100
            mask = self.df["total_intention"] != 100
            inconsistent = self.df.loc[mask].copy()

            # Calculer la différence (positive ou négative)
            inconsistent["difference"] = inconsistent["total_intention"] - 100

            # -----------------------------------------------------------------
            # Supprimer du DataFrame principal les candidats dont la différence > ±4 %
            # -----------------------------------------------------------------
            to_remove = inconsistent.loc[inconsistent["difference"].abs() > 4, "candidate_id"].tolist()

            if to_remove:
                before_count = len(self.df)
                self.df = self.df[~self.df["candidate_id"].isin(to_remove)].reset_index(drop=True)
                removed_count = before_count - len(self.df)
            else:
                removed_count = 0

            # Colonnes à retourner (données de base + intentions)
            result_columns = list(required_columns) + ["total_intention", "difference"]

            # Préparez une sortie structurée
            rows = inconsistent[result_columns].to_dict(orient="records")

            return {"count": len(rows), "rows": rows, "removed_count": removed_count}

        except KeyError as e:
            self.logger.error(f"Erreur : {e}")
            raise

        except Exception as e:
            self.logger.exception(f"Erreur inattendue lors de la vérification des intentions : {e}")
            return {"count": 0, "rows": []}

    def _generate_anomaly_report(self, survey: Dict[str, Any]) -> bool:
        """
        Génère un rapport détaillé des anomalies détectées lors de l'extraction des données
        du baromètre Cluster 17 à partir d’un fichier PDF.

        Ce rapport regroupe deux types d'anomalies :
        1. Les candidats introuvables dans le fichier de référence « candidates.csv ».
        2. Les incohérences dans les totaux d’intentions de vote (somme ≠ 100 %).

        Le rapport est exporté sous forme de fichier texte (`mining_anomalie_<population>.txt`)
        dans le répertoire d’analyse correspondant.

        Chaque anomalie inclut :
        - La page et la population concernées.
        - Le nom du candidat.
        - Si l'erreur concerne l'intention de vote totale
            - Les scores d’intentions extraits.
            - Le total calculé et la différence par rapport à 100 %.
        - Une description du problème.
        - Les actions requises pour la correction manuelle.

        Args:
            survey : Dict[str, Any]
                Dictionnaire décrivant la population et le contexte d’extraction du sondage.
                Chaque élément représente un tableau et son contexte textuel associé.
                    - "Population" : instance de Population ou chaîne identifiant la population.
                    - "Page" : numéro de page du PDF (int, optionnel).
                    - "Étiquette de population" : description textuelle du sous-échantillon.
                    - "df" : DataFrame brut de la table extraite.

            df (pd.DataFrame): DataFrame du sondage avec les colonnes intention_mention_1..4

        Returns:
            bool :
                True  → si le rapport d’anomalies a été généré avec succès.
                False → en cas d’erreur lors de la création ou de l’écriture du fichier.
        """

        # Construire le chemin de sortie
        filename = f"mining_anomalie_{survey.get("Population")}.txt"
        output_path = Path(self.path) / filename

        try:

            candidates_id = self.__get_missing_candidates_id()

            intentions = self.__get_inconsistent_intentions()
            removed_count = intentions.get("removed_count", 0)

            if candidates_id["count"] == 0 and intentions["count"] == 0:
                self.logger.info(
                    f"\t📝 Aucune anomalie détectée pour la population « {survey.get('Population')} » — aucun fichier généré."
                )
                return False

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("RAPPORT D'ANOMALIES - EXTRACTION CLUSTER 17\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Population: {survey.get("Population")}\n")
                f.write(f"Nombre d'anomalies: {candidates_id['count'] + intentions['count']}\n\n")
                f.write("=" * 80 + "\n\n")

                count_total = 1

                # -----------------------------------------------------------------
                # Le candidat n’a pas été trouvé
                # -----------------------------------------------------------------
                if candidates_id["names"]:
                    for name in candidates_id["names"]:
                        f.write(f"ANOMALIE #{count_total}\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(f"Page:\t\t\t{survey.get("Page")}\n")
                        f.write(f"Candidat:\t\t{name}\n")
                        f.write(f"Population:\t\t{survey.get("Population")}\n\n")
                        f.write("Description:\n")
                        f.write(
                            "\tLe candidat n’a pas été trouvé dans le fichier « candidates.csv ».\n"
                            "\tIl est possible que ce candidat n’existe pas dans la base de référence "
                            "ou qu’une erreur orthographique soit présente dans le nom.\n\n"
                        )

                        f.write("ACTION REQUISE :\n")
                        f.write("\t1. Ouvrez le fichier « candidates.csv »\n")
                        f.write(f"\t2. Vérifiez si le candidat « {name} » est présent dans la base de référence.\n")
                        f.write(
                            "\t3. Si le nom existe déjà mais avec une orthographe différente (accents, espaces, etc.),\n"
                            "\t   ne modifiez PAS le fichier « candidates.csv ».\n"
                            "\t   Dans ce cas, vous pouvez :\n"
                            "\t     Renseigner manuellement la colonne « candidate_id » directement\n"
                            "\t     dans le fichier CSV de l’enquête concernée.\n"
                        )
                        f.write(
                            "\t4. Si le candidat est absent, ajoutez-le manuellement dans « candidates.csv ».\n"
                            "\t   Dans ce cas, vous pouvez :\n"
                            "\t     Relancer le processus d'extraction des données.\n\n"
                        )

                        count_total += 1
                        f.write("=" * 80 + "\n\n")

                # -----------------------------------------------------------------
                # Le total des intentions ne correspond pas à 100 %
                # -----------------------------------------------------------------
                if intentions["count"] > 0:
                    for row in intentions["rows"]:
                        f.write(f"ANOMALIE #{count_total}\n")
                        f.write("-" * 80 + "\n\n")
                        f.write(f"Page:\t\t\t\t{survey.get("Page")}\n")
                        f.write(f"Candidat:\t\t\t{row['personnalite']}\n")
                        f.write(f"Population:\t\t\t{survey.get("Population")}\n\n")

                        # --- Scores / Détails ---
                        scores = [
                            row.get("intention_mention_1", None),
                            row.get("intention_mention_2", None),
                            row.get("intention_mention_3", None),
                            row.get("intention_mention_4", None),
                        ]
                        scores_clean = [s for s in scores if s is not None]
                        f.write(f"Scores extraits:\t{scores_clean}\n")

                        f.write(f"Total:\t\t\t\t{row['total_intention']}% (attendu 100%)\n")

                        diff = row["difference"]
                        sign = "+" if diff > 0 else ""
                        f.write(f"Différence:\t\t\t{sign}{diff}%\n\n")

                        f.write("Description:\n")
                        f.write(
                            "\tLe total des intentions de vote pour ce candidat ne correspond pas à 100 %.\n"
                            "\tCela indique une incohérence dans les pourcentages extraits depuis le PDF, "
                            "qui peut être due à une erreur de reconnaissance, à une valeur manquante ou à un doublon.\n\n"
                        )

                        if abs(row["difference"]) > 4:
                            f.write("ACTION AUTOMATIQUE :\n")
                            f.write(
                                "\tCe candidat a été supprimé automatiquement du fichier CSV "
                                "car son écart d’intention dépasse ±4%.\n\n"
                            )
                        else:
                            f.write("ACTION REQUISE :\n")
                            f.write("\t1. Ouvrez le fichier PDF de l’enquête correspondante.\n")
                            f.write(
                                f"\t2. Recherchez la ligne du candidat « {row['personnalite']} » et vérifiez les pourcentages affichés.\n"
                            )
                            f.write(
                                "\t3. Si une erreur est détectée, corrigez manuellement les valeurs\n"
                                "\t   dans le fichier CSV de la population correspondante :\n"
                                "\t     • Pour un total supérieur à 100 %, vérifiez s’il existe un doublon ou une valeur mal lue.\n"
                                "\t     • Pour un total inférieur à 100 %, vérifiez s’il manque une colonne ou une donnée tronquée.\n"
                            )
                            f.write(
                                "\t4. Enregistrez le fichier corrigé et NE RELANCEZ PAS le processus d'extraction des données.\n\n"
                            )

                        count_total += 1
                        f.write("=" * 80 + "\n\n")

                f.write("\nFIN DU RAPPORT\n")

                if count_total > 1:
                    self.logger.info(f"\t📝 Anomalies exportées : {output_path}")

                if candidates_id["count"] > 0:
                    self.logger.warning(
                        f"\t   ⚠️  {candidates_id["count"]} identifiant(s) de candidat introuvable(s). "
                        f"Vérifiez le fichier d’anomalies associé à la population « {survey.get("Population")} »."
                    )

                if intentions["count"] > 0:
                    self.logger.warning(
                        f"\t   ⚠️  {intentions["count"]} incohérence(s) détectée(s) dans les totaux d’intentions de vote. "
                        f"Vérifiez le fichier d’anomalies associé à la population « {survey.get("Population")} »."
                    )

                if removed_count > 0:
                    self.logger.warning(
                        f"\t       ❌  {removed_count} candidat(s) supprimé(s) du CSV pour écart > ±4% dans les intentions."
                    )

            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport d'anomalies : {e}")
            return False

    def analyze(self, survey: Dict[str, Any]) -> pd.DataFrame:
        """
        Lance la détection des anomalies, génère le rapport TXT,
        et retourne un DataFrame nettoyé (avec les lignes supprimées si nécessaire).
        """
        try:
            self._generate_anomaly_report(survey)
            return self.df
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des anomalies : {e}")
            return self.df
