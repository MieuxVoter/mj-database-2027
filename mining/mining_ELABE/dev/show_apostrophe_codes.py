# coding: utf-8
"""
Afficher les codes des caractères dans le texte du PDF.
"""

import pathlib
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

PDF_PATH = pathlib.Path(__file__).parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"

for page_number, page_layout in enumerate(extract_pages(str(PDF_PATH)), start=1):
    if page_number != 19:
        continue

    for element in page_layout:
        if isinstance(element, LTTextContainer):
            text = element.get_text().strip()
            if "Emmanuel Macron" in text:
                print(f"Texte trouvé: {text}")
                print(f"\nCodes hex des caractères:")
                for i, char in enumerate(text):
                    if char in "''" or (i > 0 and text[i - 1] == "d"):
                        print(f"  Position {i}: '{char}' → U+{ord(char):04X} ({ord(char)})")
                break
    break
