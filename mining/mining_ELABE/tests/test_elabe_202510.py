# coding: utf-8
"""
Test sur elabe_202510 pour vérifier les anomalies.
"""

import pathlib
import sys

parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from elabe_miner import ElabeMiner

# Chemins
POLLS_DIR = pathlib.Path(__file__).parent.parent.parent / "polls"
PDF_NAME = "elabe_202510"
PDF_PATH = POLLS_DIR / PDF_NAME / "source.pdf"
OUTPUT_DIR = POLLS_DIR / PDF_NAME

# Mapping pages → populations
POPULATIONS = {
    17: "all",
    18: "absentionists",
    19: "macron",
    20: "left",
    21: "farright",
}

def test_elabe_202510():
    """Test sur elabe_202510."""
    print(f"\n🔍 Test: {PDF_NAME}")
    print("="*80)
    
    if not PDF_PATH.exists():
        print(f"❌ PDF non trouvé: {PDF_PATH}")
        return
    
    miner = ElabeMiner(PDF_PATH)
    total_candidates = 0
    total_anomalies = 0
    
    for page_num, population in POPULATIONS.items():
        print(f"\n📄 Page {page_num}: {population}")
        
        lines = miner.extract_page(page_num)
        total_candidates += len(lines)
        print(f"   {len(lines)} candidats extraits")
        
        if miner.has_anomalies():
            anomaly_count = len(miner.anomaly_detector.anomalies)
            total_anomalies += anomaly_count
            
            for anomaly in miner.anomaly_detector.anomalies:
                print(f"   ⚠️  {anomaly.candidate_name}: {anomaly.missing_percent:+d}% au {anomaly.suggested_position}")
            
            miner.export_anomalies(OUTPUT_DIR, population)
            miner.anomaly_detector.anomalies.clear()
        else:
            print(f"   ✅ OK")
    
    print(f"\n{'='*80}")
    print(f"Total: {total_candidates} candidats | {total_anomalies} anomalie(s)")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    test_elabe_202510()
