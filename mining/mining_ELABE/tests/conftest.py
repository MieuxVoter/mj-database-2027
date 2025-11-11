# coding: utf-8
"""
Configuration pytest pour les tests mining_ELABE.
"""

import sys
import pathlib

# Ajouter le répertoire parent (mining_ELABE) au path
parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Définir le chemin vers les PDFs
POLLS_DIR = parent_dir.parent.parent / "polls"


def get_pdf_path(poll_name: str) -> pathlib.Path:
    """Retourne le chemin vers un PDF de sondage."""
    return POLLS_DIR / poll_name / "source.pdf"
