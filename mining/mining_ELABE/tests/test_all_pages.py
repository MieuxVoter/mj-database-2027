#!/usr/bin/env python3
# coding: utf-8
"""
Test de l'extraction des 5 pages de données ELABE (pages 17-21)
"""

import pathlib
import sys

parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from test_elabe_extraction import extract_candidates_and_scores


def test_all_populations():
    """Test l'extraction des 5 populations (pages 17-21)"""
    pdf_path = pathlib.Path(__file__).parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"
    
    if not pdf_path.exists():
        print(f"❌ PDF non trouvé : {pdf_path}")
        sys.exit(1)
    
    populations = {
        17: "Ensemble des Français (all)",
        18: "Population 2",
        19: "Population 3",
        20: "Population 4",
        21: "Population 5"
    }
    
    print("=" * 80)
    print("TEST DES 5 PAGES DE DONNÉES ELABE (pages 17-21)")
    print("=" * 80)
    
    all_ok = True
    
    for page_num, pop_name in populations.items():
        print(f"\n📄 PAGE {page_num} - {pop_name}")
        print("-" * 80)
        
        # Extraire les données
        results = extract_candidates_and_scores(pdf_path, page_num=page_num)
        
        if len(results) == 0:
            print(f"  ❌ Aucune donnée extraite")
            all_ok = False
            continue
        
        print(f"  ✓ {len(results)} candidats extraits")
        
        # Vérifier que tous les totaux = 100%
        invalid_totals = []
        for name, scores in results.items():
            total = sum(scores)
            if total != 100:
                invalid_totals.append((name, total))
        
        if invalid_totals:
            print(f"  ⚠️  {len(invalid_totals)} candidat(s) avec total ≠ 100% :")
            for name, total in invalid_totals[:3]:  # Afficher max 3
                print(f"     - {name}: {total}%")
            all_ok = False
        else:
            print(f"  ✓ Tous les totaux = 100%")
        
        # Afficher quelques exemples
        print(f"\n  Exemples (3 premiers candidats) :")
        for i, (name, scores) in enumerate(list(results.items())[:3]):
            total = sum(scores)
            status = "✓" if total == 100 else f"⚠️ {total}%"
            print(f"    {name:30s} : {scores} | Total: {total}% {status}")
        
        # Afficher les 2 derniers
        print(f"\n  Exemples (2 derniers candidats) :")
        for name, scores in list(results.items())[-2:]:
            total = sum(scores)
            status = "✓" if total == 100 else f"⚠️ {total}%"
            print(f"    {name:30s} : {scores} | Total: {total}% {status}")
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ SUCCÈS : Toutes les pages extraites correctement !")
    else:
        print("⚠️  ATTENTION : Certaines pages ont des problèmes")
        sys.exit(1)
    print("=" * 80)


if __name__ == "__main__":
    test_all_populations()
