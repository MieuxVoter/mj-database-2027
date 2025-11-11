# coding: utf-8
"""
Test du système de détection d'anomalies.
"""

import pathlib
import sys

parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from elabe_miner import ElabeMiner

PDF_PATH = pathlib.Path(__file__).parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"

def test_anomaly_detection():
    """Test la détection d'anomalies sur toutes les pages."""
    print("\n🔍 TEST: Détection d'anomalies")
    print("="*80)
    
    miner = ElabeMiner(PDF_PATH)
    
    pages = {
        17: "Ensemble des Français",
        18: "Abstentionnistes",
        19: "Électeurs de Macron",
        20: "Électeurs de gauche",
        21: "Électeurs d'extrême droite",
    }
    
    total_anomalies = 0
    
    for page_num, population in pages.items():
        print(f"\n📄 Page {page_num}: {population}")
        print("-" * 80)
        
        lines = miner.extract_page(page_num)
        print(f"✓ {len(lines)} candidats extraits")
        
        # Afficher les anomalies
        if miner.has_anomalies():
            print(f"\n{miner.get_anomalies_summary()}")
            total_anomalies += len(miner.anomaly_detector.anomalies)
        else:
            print("✅ Aucune anomalie détectée")
        
        # Réinitialiser le détecteur pour la page suivante
        miner.anomaly_detector.anomalies.clear()
    
    print("\n" + "="*80)
    if total_anomalies > 0:
        print(f"⚠️  TOTAL: {total_anomalies} anomalie(s) détectée(s) dans le PDF")
        print("   → Veuillez vérifier le PDF source et corriger manuellement si nécessaire")
    else:
        print("✅ Aucune anomalie détectée dans tout le PDF")
    print("="*80)

if __name__ == "__main__":
    test_anomaly_detection()
