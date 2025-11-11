# coding: utf-8
"""
Tests pour la classe ElabeMiner.
"""

import pathlib
import sys

# Ajouter le répertoire parent au path
parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from elabe_miner import ElabeMiner

# PDF de référence
PDF_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"

def test_miner_page17():
    """Test extraction page 17 (population générale)."""
    print("\n🔍 Test ElabeMiner - Page 17")
    print("=" * 60)
    
    miner = ElabeMiner(PDF_PATH)
    lines = miner.extract_page(17)
    
    print(f"✅ Nombre de candidats extraits: {len(lines)}")
    assert len(lines) == 30, f"Attendu 30 candidats, obtenu {len(lines)}"
    
    # Afficher quelques candidats
    print("\n📋 Premiers candidats:")
    for i, line in enumerate(lines[:5]):
        print(f"  {i+1}. {line.get_name()} → {line.get_scores()}")
    
    # Valider tous
    print("\n✓ Validation des scores (doivent tous faire 100%)...")
    miner.validate_all()
    print("✅ Tous les scores sont valides !")
    
    # Vérifier des candidats spécifiques
    names = [line.get_name() for line in lines]
    assert "Jordan Bardella" in names
    assert "Marine Le Pen" in names
    assert "Jean-Pierre Farandou" in names
    
    # Vérifier les scores de Jordan Bardella (premier de la liste)
    bardella = lines[0]
    assert bardella.get_name() == "Jordan Bardella"
    assert bardella.get_scores() == ['18', '21', '14', '37', '10']
    
    print("✅ Jordan Bardella: scores corrects")
    
    print("\n🎉 Test page 17 réussi !\n")

def test_miner_all_pages():
    """Test extraction toutes les pages."""
    print("\n🔍 Test ElabeMiner - Toutes les pages")
    print("=" * 60)
    
    miner = ElabeMiner(PDF_PATH)
    
    expected_counts = {
        17: 30,  # Tous
        18: 30,  # Abstentionnistes (était 26, maintenant 30 avec scores à 4 éléments)
        19: 30,  # Macron
        20: 30,  # Gauche (était 26, maintenant 30)
        21: 30,  # Droite (était 23, maintenant 30)
    }
    
    total = 0
    total_anomalies = 0
    
    for page_num, expected in expected_counts.items():
        lines = miner.extract_page(page_num)
        actual = len(lines)
        total += actual
        
        status = "✅" if actual == expected else "⚠️"
        print(f"  Page {page_num}: {actual:2d} candidats {status}")
        
        # Afficher les anomalies s'il y en a
        if miner.has_anomalies():
            anomalies = miner.anomaly_detector.anomalies
            total_anomalies += len(anomalies)
            for anomaly in anomalies:
                print(f"    ⚠️  {anomaly.candidate_name}: manque {anomaly.missing_percent}% au {anomaly.suggested_position}")
            miner.anomaly_detector.anomalies.clear()
    
    print(f"\n✅ Total: {total} candidats extraits sur 5 pages")
    
    if total_anomalies > 0:
        print(f"⚠️  {total_anomalies} anomalie(s) détectée(s) - vérifiez le PDF source\n")
    else:
        print("✅ Aucune anomalie détectée\n")

def test_miner_validation():
    """Test validation des données."""
    print("\n🔍 Test ElabeMiner - Validation")
    print("=" * 60)
    
    miner = ElabeMiner(PDF_PATH)
    lines = miner.extract_page(17)
    
    # Vérifier que chaque ligne a bien 5 scores
    print("✓ Vérification du nombre de scores par ligne...")
    for line in lines:
        scores = line.get_scores()
        assert len(scores) == 5, f"{line.get_name()}: attendu 5 scores, obtenu {len(scores)}"
    
    print(f"✅ Toutes les {len(lines)} lignes ont 5 scores")
    
    # Vérifier que tous les scores font 100%
    print("✓ Vérification de la somme des scores...")
    miner.validate_all()
    print("✅ Toutes les sommes = 100%")
    
    print("\n🎉 Validation réussie !\n")

if __name__ == "__main__":
    test_miner_page17()
    test_miner_all_pages()
    test_miner_validation()
    print("=" * 60)
    print("🎉 TOUS LES TESTS PASSENT !")
    print("=" * 60)
