#!/usr/bin/env python3
# coding: utf-8
"""
Script CLI pour extraire et construire les CSV ELABE.

Usage:
    python elabe_build.py <pdf_path> <date> [--population <pop>] [--overwrite]

Exemples:
    # Extraire toutes les populations
    python elabe_build.py ../../polls/elabe_202511/source.pdf 202511
    
    # Extraire une seule population
    python elabe_build.py ../../polls/elabe_202511/source.pdf 202511 --population all
    
    # Écraser les fichiers existants
    python elabe_build.py ../../polls/elabe_202511/source.pdf 202511 --overwrite
"""

import argparse
import pathlib
import sys

try:
    from elabe_miner import ElabeMiner
    from elabe_builder import ElabeBuilder
    from page_detector import PageDetector
except ImportError:
    # Si on exécute depuis mining/mining_ELABE
    parent_dir = pathlib.Path(__file__).parent
    sys.path.insert(0, str(parent_dir))
    from elabe_miner import ElabeMiner
    from elabe_builder import ElabeBuilder
    from page_detector import PageDetector


# Mapping des populations
POPULATION_MAP = {
    "all": "Ensemble des Français",
    "left": "Électeurs de gauche",
    "macron": "Électeurs d'Emmanuel Macron",
    "farright": "Électeurs d'extrême droite",
    "absentionists": "Abstentionnistes",
}

POLL_TYPE = "pt2"  # Type de sondage ELABE


def main():
    parser = argparse.ArgumentParser(
        description="Extraction automatique des données ELABE depuis PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "pdf_path",
        type=pathlib.Path,
        help="Chemin vers le PDF source"
    )
    
    parser.add_argument(
        "date",
        help="Date du sondage au format AAAAMM (ex: 202511)"
    )
    
    parser.add_argument(
        "--population",
        choices=list(POPULATION_MAP.keys()),
        help="Population à extraire (si omis, extrait toutes les populations)"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écraser les fichiers CSV existants"
    )
    
    parser.add_argument(
        "--candidates",
        type=pathlib.Path,
        default=None,
        help="Chemin vers candidates.csv (par défaut: ../../candidates.csv)"
    )
    
    args = parser.parse_args()
    
    # Vérifications
    if not args.pdf_path.exists():
        print(f"❌ Erreur : PDF non trouvé : {args.pdf_path}")
        sys.exit(1)
    
    # Déterminer le chemin des candidats
    if args.candidates is None:
        # Chercher candidates.csv à la racine du projet
        candidates_csv = pathlib.Path(__file__).parent.parent.parent / "candidates.csv"
    else:
        candidates_csv = args.candidates
    
    if not candidates_csv.exists():
        print(f"❌ Erreur : candidates.csv non trouvé : {candidates_csv}")
        sys.exit(1)
    
    # Déterminer le répertoire de sortie
    output_dir = args.pdf_path.parent
    
    print("🚀 Extraction ELABE")
    print("=" * 70)
    print(f"📄 PDF       : {args.pdf_path}")
    print(f"📅 Date      : {args.date}")
    print(f"📂 Sortie    : {output_dir}")
    print(f"👥 Candidats : {candidates_csv}")
    print()
    
    # Étape 1 : Détecter les pages de données
    print("🔍 Détection des pages de données...")
    detector = PageDetector(args.pdf_path)
    data_pages = detector.detect_data_pages(start_page=1, end_page=25)
    
    if not data_pages:
        print("❌ Erreur : Aucune page de données détectée")
        sys.exit(1)
    
    print(detector.get_summary(data_pages))
    print()
    
    # Filtrer les populations si nécessaire
    if args.population:
        data_pages = [(p, pop) for p, pop in data_pages if pop == args.population]
        if not data_pages:
            print(f"❌ Erreur : Population '{args.population}' non trouvée dans le PDF")
            sys.exit(1)
    
    # Étape 2 : Extraire et construire les CSV
    print(f"📦 Extraction et construction des CSV...")
    print()
    
    miner = ElabeMiner(args.pdf_path)
    success_count = 0
    error_count = 0
    
    for page_num, population in data_pages:
        try:
            # Nom du fichier
            output_filename = f"elabe_{args.date}_{population}.csv"
            output_path = output_dir / output_filename
            
            # Vérifier si le fichier existe
            if output_path.exists() and not args.overwrite:
                print(f"⏭️  {output_filename} existe déjà (utilisez --overwrite pour écraser)")
                continue
            
            # Extraire la page
            lines = miner.extract_page(page_num)
            
            if not lines:
                print(f"❌ {output_filename} : Aucun candidat extrait")
                error_count += 1
                continue
            
            # Vérifier les anomalies
            if miner.has_anomalies():
                print(f"⚠️  {output_filename} : {len(miner.anomaly_detector.anomalies)} anomalie(s) détectée(s)")
                miner.export_anomalies(output_dir, population)
                # Nettoyer pour la page suivante
                miner.anomaly_detector.anomalies.clear()
            
            # Construire le CSV
            builder = ElabeBuilder(candidates_csv, lines)
            builder.write(output_path, POLL_TYPE, population)
            
            success_count += 1
            print()
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {population} (page {page_num}) : {e}")
            error_count += 1
            import traceback
            traceback.print_exc()
            print()
    
    # Résumé
    print("=" * 70)
    print(f"✅ {success_count} fichier(s) CSV généré(s)")
    if error_count > 0:
        print(f"❌ {error_count} erreur(s)")
    print()
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
