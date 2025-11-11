# coding: utf-8
"""
Test du détecteur de pages.
"""

import pathlib
import sys

parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from page_detector import PageDetector

POLLS_DIR = pathlib.Path(__file__).parent.parent.parent / "polls"

def test_detector(pdf_name: str):
    """Test le détecteur sur un PDF."""
    pdf_path = POLLS_DIR / pdf_name / "source.pdf"
    
    if not pdf_path.exists():
        print(f"❌ PDF non trouvé: {pdf_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"📄 {pdf_name}")
    print('='*80)
    
    detector = PageDetector(pdf_path)
    
    # Détecter les pages (chercher entre pages 1 et 25)
    data_pages = detector.detect_data_pages(start_page=1, end_page=25)
    
    print(f"\n{detector.get_summary(data_pages)}")

if __name__ == "__main__":
    print("\n🔍 TEST: Détection des pages de données")
    
    # Tester les deux PDFs
    test_detector("elabe_202510")
    test_detector("elabe_202511")
    
    print("\n" + "="*80)
