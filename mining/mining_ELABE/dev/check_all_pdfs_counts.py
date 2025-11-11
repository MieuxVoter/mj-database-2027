# coding: utf-8
"""
Vérifier le nombre de candidats dans tous les PDFs ELABE récents.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from elabe_miner import ElabeMiner

# Dossier des polls
POLLS_DIR = pathlib.Path(__file__).parent.parent.parent / "polls"

# PDFs récents (format oct-nov 2025)
RECENT_PDFS = [
    "elabe_202510",
    "elabe_202511",
]

def check_pdf(pdf_name: str):
    """Vérifie un PDF."""
    print(f"\n{'='*70}")
    print(f"📄 {pdf_name}")
    print('='*70)
    
    pdf_path = POLLS_DIR / pdf_name / "source.pdf"
    if not pdf_path.exists():
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    miner = ElabeMiner(pdf_path)
    
    pages = {
        17: "Tous",
        18: "Abstentionnistes",
        19: "Macron",
        20: "Gauche",
        21: "Droite",
    }
    
    for page_num, population in pages.items():
        lines = miner.extract_page(page_num)
        count = len(lines)
        print(f"  Page {page_num} ({population:18s}): {count:2d} candidats")

if __name__ == "__main__":
    print("\n🔍 VÉRIFICATION DU NOMBRE DE CANDIDATS PAR PDF")
    
    for pdf_name in RECENT_PDFS:
        check_pdf(pdf_name)
    
    print("\n" + "="*70)
