# coding: utf-8
"""
Extraction complète avec export des anomalies.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from elabe_miner import ElabeMiner
from page_detector import PageDetector

# Chemins
POLLS_DIR = pathlib.Path(__file__).parent.parent.parent / "polls"
PDF_NAME = "elabe_202510"  # Changeable
PDF_PATH = POLLS_DIR / PDF_NAME / "source.pdf"
OUTPUT_DIR = POLLS_DIR / PDF_NAME


def extract_with_anomaly_export():
    """Extrait toutes les pages et exporte les anomalies."""
    print("\n🔍 EXTRACTION ELABE avec export des anomalies")
    print("=" * 80)
    print(f"PDF: {PDF_NAME}")
    print(f"Sortie: {OUTPUT_DIR}")
    print("=" * 80)

    # 1. Détecter automatiquement les pages de données
    print("\n📊 Détection des pages de données...")
    detector = PageDetector(PDF_PATH)
    data_pages = detector.detect_data_pages(start_page=1, end_page=25)

    if not data_pages:
        print("❌ Aucune page de données détectée")
        return

    print(detector.get_summary(data_pages))

    # 2. Extraire chaque page
    miner = ElabeMiner(PDF_PATH)
    total_candidates = 0
    total_anomalies = 0

    for page_num, population in data_pages:
        print(f"\n📄 Page {page_num}: {population}")
        print("-" * 80)

        # Extraire la page
        lines = miner.extract_page(page_num)
        total_candidates += len(lines)
        print(f"✓ {len(lines)} candidats extraits")

        # Exporter les anomalies si détectées
        if miner.has_anomalies():
            anomaly_count = len(miner.anomaly_detector.anomalies)
            total_anomalies += anomaly_count

            print(f"⚠️  {anomaly_count} anomalie(s) détectée(s)")

            # Afficher un résumé
            for anomaly in miner.anomaly_detector.anomalies:
                print(
                    f"   - {anomaly.candidate_name}: manque {anomaly.missing_percent}% au {anomaly.suggested_position}"
                )

            # Exporter dans un fichier
            output_file = miner.export_anomalies(OUTPUT_DIR, population)

            # Réinitialiser pour la page suivante
            miner.anomaly_detector.anomalies.clear()
        else:
            print("✅ Aucune anomalie")

    print("\n" + "=" * 80)
    print(f"✅ EXTRACTION TERMINÉE")
    print(f"   Pages détectées: {len(data_pages)}")
    print(f"   Total: {total_candidates} candidats extraits")

    if total_anomalies > 0:
        print(f"   ⚠️  {total_anomalies} anomalie(s) détectée(s)")
        print(f"   📝 Rapports exportés dans: {OUTPUT_DIR}")
        print(f"   → Vérifiez les fichiers mining_anomalie_*.txt")
    else:
        print(f"   ✅ Aucune anomalie détectée")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    extract_with_anomaly_export()
