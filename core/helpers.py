import argparse
import unicodedata
import re
from pathlib import Path
import pandas as pd


def valid_date(value: str) -> str:
    """
    Valide que la date soit au format AAAAMM (ex: 202511)

    Args:
        value (str): La chaîne représentant la date à valider.

    Returns:
        str: La valeur initiale si la date est valide.

    Raises:
        argparse.ArgumentTypeError: Si la chaîne ne correspond pas au format attendu.
    """

    if len(value) != 6 or not value.isdigit():
        raise argparse.ArgumentTypeError("La date doit être au format AAAAMM, ex: 202511")

    year = int(value[:4])
    month = int(value[4:6])

    if not (1 <= month <= 12):
        raise argparse.ArgumentTypeError(f"Mois invalide ({month}) dans la date '{value}'")

    if year < 2000 or year > 2100:
        raise argparse.ArgumentTypeError(f"Année invalide ({year}) dans la date '{value}'")

    return value


def normalize(text: str) -> str:
    """
    Convertit le texte en minuscules, sans accents ni sauts étranges.

    Args:
        text (str): Le texte á normaliser.

    Returns:
        str: Texte normalisé.
    """
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("’", "'")
    text = text.replace("‐", "-")  # guion Unicode raro → ASCII
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)  # fusionne mots coupés
    text = text.replace("-", " ")  # ← unifica guiones a espacio
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ensure_newline(path: Path) -> None:
    """
    Assurez que le fichier fourni se termine par un caractère de nouvelle ligne.

    Cette fonction est destinée à être utilisée avant d'ajouter des données à un fichier CSV.
    Si le fichier ne se termine pas par un saut de ligne (``\\n``), celui-ci est ajouté afin d'éviter

    Args:
        path : Path
            Chemin d'accès au fichier qui doit se terminer par un caractère de nouvelle ligne.
    """
    if not path.exists():
        raise FileNotFoundError(f"Le fichier est requis mais introuvable : {path}")

    with path.open("rb+") as f:
        f.seek(-1, 2)
        last_char = f.read(1)
        if last_char != b"\n":
            f.write(b"\n")


def survey_exists(
    csv_path: Path,
    poll_id: str,
    population: str,
) -> bool:
    """
    Vérifiez si un sondage existe déjà dans le fichier CSV des sondages.

    Un sondage est considéré comme unique par la paire (poll_id, population).
    """
    df = pd.read_csv(
        csv_path,
        usecols=["poll_id", "population"],
        dtype=str,
    )

    return ((df["poll_id"] == poll_id) & (df["population"] == population)).any()
