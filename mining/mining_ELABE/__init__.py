# coding: utf-8
"""
Mining ELABE - Extraction automatique des données de sondage ELABE.

Ce module permet d'extraire automatiquement les données des baromètres
politiques ELABE depuis les PDFs sources.

Fonctionnalités :
- Détection automatique des pages de données
- Extraction des candidats et scores
- Détection et export des anomalies
- Support des PDFs avec structures variables (pages 13-17 ou 17-21)

Usage:
    from mining_ELABE import ElabeMiner, PageDetector

    # Détecter les pages
    detector = PageDetector(pdf_path)
    pages = detector.detect_data_pages()

    # Extraire les données
    miner = ElabeMiner(pdf_path)
    for page_num, population in pages:
        lines = miner.extract_page(page_num)
        if miner.has_anomalies():
            miner.export_anomalies(output_dir, population)
"""

__version__ = "0.1.0"
__author__ = "Pierre Puchaud"

from .elabe_miner import ElabeMiner
from .page_detector import PageDetector
from .elabe_poll import ElabeLine
from .anomaly_detector import AnomalyDetector, ExtractionAnomaly
from .elabe_builder import ElabeBuilder

__all__ = [
    "ElabeMiner",
    "PageDetector",
    "ElabeLine",
    "AnomalyDetector",
    "ExtractionAnomaly",
    "ElabeBuilder",
]
