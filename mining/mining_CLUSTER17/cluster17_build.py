import sys
import pathlib
import argparse
import logging
from core.settings.logger import setup_logging
from core.helpers import valid_date
from core.population import Population
from mining.mining_CLUSTER17.cluster17 import Cluster17

# Type de sondage CLUSTER17
POLL_ID = "pt4"

# Population de Cluster 17
POPULATION = Population.by_survey("CLUSTER17")


def main():

    setup_logging()
    logger = logging.getLogger("app")

    parser = argparse.ArgumentParser(
        prog="Cluser17 mining",
        description="Extraction automatique des données CLUSTER 17 depuis PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("file", type=pathlib.Path, help="Chemin vers le PDF source")
    parser.add_argument("date", type=valid_date, help="Date du sondage au format AAAAMM (ex: 202511)")
    parser.add_argument(
        "--population",
        type=Population,
        choices=list(Population),
        help="Population à extraire (si omis, extrait toutes les populations)",
    )
    parser.add_argument("--overwrite", action="store_true", help="Écraser les fichiers CSV existants")

    args = parser.parse_args()

    if not args.file.exists():
        logger.error(f"Le fichier << {args.file} >> n'existe pas.")
        sys.exit(1)
    else:
        OUTPUT_DIR = args.file.parent
        CANDIDATES_CSV = pathlib.Path(__file__).parent.parent.parent / "candidates.csv"
        if not CANDIDATES_CSV.exists():
            logger.error(f"Le fichier << candidates.csv >> est introuvable : {CANDIDATES_CSV}")
            sys.exit(1)

    logger.info("╔═══════════════════════════════════════════════════════════════════════════╗")
    logger.info("║ 🚀  Début d’extraction du Cluster 17                                      ║")
    logger.info("╚═══════════════════════════════════════════════════════════════════════════╝")
    logger.info(f"📄 PDF         : {args.file}")
    logger.info(f"📅 Date        : {args.date[:4]}-{args.date[4:]}")
    if args.population:
        logger.info(f"🧠 Population  : Une seule population à extraire << {args.population.label} >>")
    else:
        logger.info(f"🧠 Population  : {', '.join(p.value for p in POPULATION)}")
    logger.info(f"📂 Sortie      : {OUTPUT_DIR}")
    logger.info(f"👥 Candidats   : {CANDIDATES_CSV}")
    logger.info("")

    process = Cluster17(args.file, POLL_ID, args.population)
    process.process_data()

if __name__ == "__main__":
    sys.exit(main())
