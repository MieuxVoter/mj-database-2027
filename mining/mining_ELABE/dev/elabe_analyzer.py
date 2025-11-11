#!/usr/bin/env python3
# coding: utf-8
"""
ELABE PDF Analyzer

Outil d'exploration pour comprendre la structure des PDFs ELABE.
Extrait et affiche les éléments textuels avec leurs positions pour identifier les patterns.

Usage:
    python elabe_analyzer.py path/to/elabe_202511/source.pdf
    python elabe_analyzer.py path/to/elabe_202511/source.pdf --page 5
    python elabe_analyzer.py path/to/elabe_202511/source.pdf --save analysis.txt
"""

import argparse
import pathlib
from typing import List, Optional

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno


class TextElement:
    """Représente un élément de texte avec sa position"""

    def __init__(self, text: str, x: float, y: float, page: int):
        self.text = text.strip()
        self.x = x
        self.y = y
        self.page = page

    def __repr__(self):
        return f"Page {self.page} | Y:{self.y:6.2f} X:{self.x:6.2f} | {repr(self.text)}"


class ElabeAnalyzer:
    """Analyse la structure d'un PDF ELABE"""

    def __init__(self):
        self.elements: List[TextElement] = []

    def load_pdf(self, pdf_path: pathlib.Path, pages: Optional[List[int]] = None):
        """
        Charge et analyse un PDF ELABE

        Args:
            pdf_path: Chemin vers le PDF
            pages: Liste des numéros de pages à analyser (None = toutes)
        """
        print(f"📄 Analyse du PDF : {pdf_path}")
        print(f"📑 Pages à analyser : {pages if pages else 'Toutes'}")
        print("-" * 80)

        page_count = 0
        for page_num, page_layout in enumerate(extract_pages(str(pdf_path)), start=1):
            # Filtrer les pages si spécifié
            if pages and page_num not in pages:
                continue

            page_count += 1
            self._analyze_page(page_layout, page_num)

        print(f"\n✓ {page_count} page(s) analysée(s)")
        print(f"✓ {len(self.elements)} éléments textuels extraits")

    def _analyze_page(self, page_layout, page_num: int):
        """Analyse une page et extrait les éléments textuels"""

        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()

                if not text:
                    continue

                # Position du coin inférieur gauche
                x = element.x0
                y = element.y0

                text_element = TextElement(text, x, y, page_num)
                self.elements.append(text_element)

    def display_elements(self, sort_by: str = "y"):
        """
        Affiche les éléments extraits

        Args:
            sort_by: Critère de tri ('y' pour vertical, 'x' pour horizontal)
        """
        if not self.elements:
            print("⚠️  Aucun élément trouvé")
            return

        # Trier les éléments
        if sort_by == "y":
            # Trier par page, puis Y décroissant (haut en bas)
            self.elements.sort(key=lambda e: (e.page, -e.y))
        elif sort_by == "x":
            # Trier par page, puis X croissant (gauche à droite)
            self.elements.sort(key=lambda e: (e.page, e.x))
        else:
            # Trier par page uniquement
            self.elements.sort(key=lambda e: e.page)

        print("\n" + "=" * 80)
        print("ÉLÉMENTS TEXTUELS EXTRAITS")
        print("=" * 80)

        current_page = None
        for elem in self.elements:
            if elem.page != current_page:
                current_page = elem.page
                print(f"\n{'─' * 80}")
                print(f"PAGE {current_page}")
                print(f"{'─' * 80}")

            print(elem)

    def analyze_structure(self):
        """Analyse et affiche les patterns identifiés"""
        if not self.elements:
            print("⚠️  Aucun élément à analyser")
            return

        print("\n" + "=" * 80)
        print("ANALYSE DE STRUCTURE")
        print("=" * 80)

        # Grouper par page
        pages = {}
        for elem in self.elements:
            if elem.page not in pages:
                pages[elem.page] = []
            pages[elem.page].append(elem)

        for page_num in sorted(pages.keys()):
            elements = pages[page_num]

            print(f"\n📄 Page {page_num} : {len(elements)} éléments")

            # Identifier les lignes (même Y)
            y_positions = {}
            for elem in elements:
                y_key = round(elem.y, 1)  # Regrouper par Y arrondi
                if y_key not in y_positions:
                    y_positions[y_key] = []
                y_positions[y_key].append(elem)

            print(f"   └─ {len(y_positions)} lignes horizontales détectées")

            # Identifier les colonnes (même X)
            x_positions = {}
            for elem in elements:
                x_key = round(elem.x, 1)  # Regrouper par X arrondi
                if x_key not in x_positions:
                    x_positions[x_key] = []
                x_positions[x_key].append(elem)

            print(f"   └─ {len(x_positions)} colonnes verticales détectées")

            # Identifier les nombres (scores potentiels)
            numbers = [e for e in elements if self._is_number(e.text)]
            print(f"   └─ {len(numbers)} nombres détectés (scores potentiels)")

            # Identifier les noms (texte long)
            names = [e for e in elements if len(e.text) > 5 and not self._is_number(e.text)]
            print(f"   └─ {len(names)} noms potentiels détectés")

    def _is_number(self, text: str) -> bool:
        """Vérifie si le texte est un nombre"""
        text = text.replace("%", "").strip()
        try:
            float(text)
            return True
        except ValueError:
            return False

    def save_report(self, output_path: pathlib.Path):
        """Sauvegarde le rapport d'analyse dans un fichier"""
        with output_path.open("w", encoding="utf-8") as f:
            f.write("RAPPORT D'ANALYSE PDF ELABE\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Nombre total d'éléments : {len(self.elements)}\n\n")

            # Éléments triés par position
            self.elements.sort(key=lambda e: (e.page, -e.y))

            current_page = None
            for elem in self.elements:
                if elem.page != current_page:
                    current_page = elem.page
                    f.write(f"\n{'─' * 80}\n")
                    f.write(f"PAGE {current_page}\n")
                    f.write(f"{'─' * 80}\n\n")

                f.write(f"{elem}\n")

        print(f"\n✓ Rapport sauvegardé dans : {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyseur de structure pour PDFs ELABE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  %(prog)s polls/elabe_202511/source.pdf
  %(prog)s polls/elabe_202511/source.pdf --page 17
  %(prog)s polls/elabe_202511/source.pdf --save analysis.txt
        """,
    )

    parser.add_argument("pdf_path", type=pathlib.Path, help="Chemin vers le PDF ELABE à analyser")

    parser.add_argument("--page", "-p", type=int, action="append", help="Numéro de page à analyser (répétable)")

    parser.add_argument("--sort", "-s", choices=["y", "x", "page"], default="y", help="Critère de tri (défaut: y)")

    parser.add_argument("--save", type=pathlib.Path, help="Sauvegarder le rapport dans un fichier")

    parser.add_argument("--no-structure", action="store_true", help="Ne pas afficher l'analyse de structure")

    args = parser.parse_args()

    # Vérifier que le fichier existe
    if not args.pdf_path.exists():
        print(f"❌ Erreur : Le fichier {args.pdf_path} n'existe pas")
        return 1

    # Analyser le PDF
    analyzer = ElabeAnalyzer()
    analyzer.load_pdf(args.pdf_path, pages=args.page)

    # Afficher les éléments
    analyzer.display_elements(sort_by=args.sort)

    # Analyser la structure
    if not args.no_structure:
        analyzer.analyze_structure()

    # Sauvegarder si demandé
    if args.save:
        analyzer.save_report(args.save)

    return 0


if __name__ == "__main__":
    exit(main())
