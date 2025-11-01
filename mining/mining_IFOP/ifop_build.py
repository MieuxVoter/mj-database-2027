# coding: utf-8

import pathlib

from miner import Miner
from builder import Builder

_SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
_POLL_DIR = _SCRIPT_DIR.parent.parent / "polls"
_DEFAULT_CANDIDATE_PATH = _SCRIPT_DIR.parent.parent / "candidates.csv"

if __name__ == "__main__":
    import argparse
    import pathlib

    argparser = argparse.ArgumentParser(description="Traitement des fichiers PDF IFOP")
    argparser.add_argument("pdf_path", type=pathlib.Path, help="Chemin vers le fichier PDF à traiter")
    argparser.add_argument("poll_date", type=str, help="Date du sondage (format AAAAMM)")

    argparser.add_argument(
        "--candidates-path",
        type=pathlib.Path,
        default=_DEFAULT_CANDIDATE_PATH,
        help="Chemin vers le fichier des candidats",
    )

    argparser.add_argument(
        "--poll-type",
        "-t",
        type=str,
        default="pt3",
        help="ID du type de sondage (par défaut : pt3)",
    )

    argparser.add_argument(
        "--prefix",
        "-x",
        type=str,
        default="ifop",
        help="Préfixe pour le fichier de sortie (par défaut : ifop)",
    )
    argparser.add_argument(
        "--population",
        "-P",
        type=str,
        default="all",
        help="Population cible (par défaut : all)",
    )

    argparser.add_argument("--pages", "-p", type=int, nargs="+", default=None, help="Pages à analyser")
    argparser.add_argument("--score-number", type=int, default=7, help="Nombre de mentions (par défaut: 7)")

    argparser.add_argument(
        "--overwrite",
        "-o",
        action="store_true",
        help="Écraser le fichier de sortie s'il existe",
    )

    args = argparser.parse_args()

    pdf_path = args.pdf_path.resolve(strict=True)
    candidates_path = args.candidates_path.resolve(strict=True)

    poll_id = f"{args.prefix}_{args.poll_date}"
    output_dir = _POLL_DIR / poll_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{poll_id}_{args.population}.csv"

    if not args.overwrite and output_path.exists():
        print(
            f"Le fichier de sortie {output_path} existe déjà. Veuillez le supprimer, choisir un autre suffixe ou utiliser l'option --overwrite."
        )
        exit(1)

    # Traitement du PDF
    miner = Miner()
    miner.load_pdf(pdf_path, args.score_number, pages=args.pages)

    results = miner.get_results()

    builder = Builder(candidates_path, results)
    builder.write(output_path, args.poll_type, args.population)
    print(f"Résultats écrits dans {output_path}")
