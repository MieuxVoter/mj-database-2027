#!/usr/bin/env python3
# coding: utf-8
"""
Test de l'extraction sur tous les PDFs ELABE disponibles
"""

import pathlib
import sys

parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from test_elabe_extraction import extract_candidates_and_scores


def test_all_pdfs():
    """Test l'extraction sur tous les PDFs ELABE"""
    
    base_dir = pathlib.Path(__file__).parent.parent.parent / "polls"
    
    pdfs = [
        base_dir / "elabe_202408" / "source.pdf",
        base_dir / "elabe_202410" / "source.pdf",
        base_dir / "elabe_202411" / "source.pdf",
        base_dir / "elabe_202506" / "source.pdf",
        base_dir / "elabe_202507" / "source.pdf",
        base_dir / "elabe_202509" / "source.pdf",
        base_dir / "elabe_202510" / "source.pdf",
        base_dir / "elabe_202511" / "source.pdf",
    ]
    
    print("=" * 80)
    print("TEST DE L'EXTRACTION SUR TOUS LES PDFs ELABE")
    print("=" * 80)
    
    all_ok = True
    summary = []
    
    for pdf_path_str in pdfs:
        pdf_path = pathlib.Path(pdf_path_str)
        poll_id = pdf_path.parent.name
        
        print(f"\n📁 {poll_id}")
        print("-" * 80)
        
        if not pdf_path.exists():
            print(f"  ⚠️  PDF non trouvé : {pdf_path}")
            summary.append((poll_id, "ABSENT", 0, 0))
            continue
        
        # Tester la page 17 (Ensemble des Français)
        try:
            results = extract_candidates_and_scores(pdf_path, page_num=17, debug=False)
            
            if len(results) == 0:
                print(f"  ❌ Aucune donnée extraite")
                summary.append((poll_id, "ÉCHEC", 0, 0))
                all_ok = False
                continue
            
            # Vérifier les totaux
            invalid_count = 0
            for name, scores in results.items():
                total = sum(scores)
                if total != 100:
                    invalid_count += 1
            
            status = "✅ OK" if invalid_count == 0 else f"⚠️  {invalid_count} erreurs"
            print(f"  {status} - {len(results)} candidats extraits")
            
            # Afficher 2 exemples
            first_two = list(results.items())[:2]
            for name, scores in first_two:
                total = sum(scores)
                print(f"    • {name:25s} : {scores} (total: {total}%)")
            
            summary.append((poll_id, "OK" if invalid_count == 0 else "ERREURS", len(results), invalid_count))
            
            if invalid_count > 0:
                all_ok = False
                
        except Exception as e:
            print(f"  ❌ Erreur : {e}")
            summary.append((poll_id, "EXCEPTION", 0, 0))
            all_ok = False
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"{'PDF':<20} {'Statut':<15} {'Candidats':<12} {'Erreurs'}")
    print("-" * 80)
    for poll_id, status, candidates, errors in summary:
        print(f"{poll_id:<20} {status:<15} {candidates:<12} {errors}")
    
    print("\n" + "=" * 80)
    if all_ok:
        valid_pdfs = [s for s in summary if s[1] == "OK"]
        print(f"✅ SUCCÈS : {len(valid_pdfs)}/{len(pdfs)} PDFs extraits correctement !")
    else:
        print("⚠️  ATTENTION : Certains PDFs ont des problèmes")
        sys.exit(1)
    print("=" * 80)


if __name__ == "__main__":
    test_all_pdfs()
