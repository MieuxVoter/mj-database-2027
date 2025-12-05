import argparse
import unicodedata
import re


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
