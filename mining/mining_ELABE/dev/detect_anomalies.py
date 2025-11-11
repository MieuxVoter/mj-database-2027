# coding: utf-8
"""
Détection des anomalies: lignes avec somme != 100%
"""

import pathlib
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

PDF_PATH = pathlib.Path(__file__).parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"


def find_anomalies_in_page(page_num: int):
    """Détecte les lignes avec somme != 100%."""
    print(f"\n{'='*80}")
    print(f"📄 PAGE {page_num}")
    print("=" * 80)

    for page_number, page_layout in enumerate(extract_pages(str(PDF_PATH)), start=1):
        if page_number != page_num:
            continue

        elements = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:
                    elements.append({"text": text, "x": element.x0, "y": element.y0})

        # Extraire les noms
        candidate_names = []
        for elem in elements:
            text = elem["text"]
            lines = [n.strip() for n in text.split("\n") if n.strip()]

            # Compter combien de lignes semblent être des noms (> 5 caractères, pas que des chiffres)
            name_like = sum(
                1 for line in lines if len(line) > 5 and not line.replace("%", "").replace(" ", "").isdigit()
            )

            if name_like >= 20 and 20 <= len(lines) <= 35:
                candidate_names = lines
                break

        # Extraire les scores
        scores = []
        for elem in elements:
            text = elem["text"].replace("%", "").strip()
            try:
                value = int(text)
                if 0 <= value <= 100:
                    scores.append({"value": value, "x": elem["x"], "y": elem["y"]})
            except ValueError:
                pass

        # Trier par Y
        scores.sort(key=lambda s: -s["y"])

        # Regrouper par ligne
        lines = []
        current_line = []
        current_y = None

        for score in scores:
            if current_y is None:
                current_y = score["y"]
                current_line = [score]
            elif abs(score["y"] - current_y) < 2.0:
                current_line.append(score)
            else:
                if current_line:
                    current_line.sort(key=lambda s: s["x"])
                    lines.append({"scores": current_line, "y": current_y})
                current_line = [score]
                current_y = score["y"]

        if current_line:
            current_line.sort(key=lambda s: s["x"])
            lines.append({"scores": current_line, "y": current_y})

        # Filtrer les lignes avec 4+ scores
        data_lines = [line for line in lines if len(line["scores"]) >= 4]

        print(f"\n📊 Analyse de {len(data_lines)} lignes de données :\n")

        anomalies = []
        for i, line in enumerate(data_lines):
            values = [s["value"] for s in line["scores"]]
            total = sum(values)

            if total != 100:
                # Trouver le candidat correspondant
                candidate = candidate_names[i] if i < len(candidate_names) else f"Ligne {i+1}"

                diff = 100 - total
                anomalies.append(
                    {
                        "line_num": i + 1,
                        "candidate": candidate,
                        "scores": values,
                        "total": total,
                        "missing": diff,
                        "y": line["y"],
                    }
                )

        if not anomalies:
            print("✅ Toutes les lignes ont un total de 100%")
        else:
            print(f"⚠️  {len(anomalies)} anomalie(s) détectée(s) :\n")
            for anomaly in anomalies:
                print(f"  Ligne {anomaly['line_num']:2d}: {anomaly['candidate']}")
                print(f"    Scores: {anomaly['scores']}")
                print(f"    Total:  {anomaly['total']}% (manque {anomaly['missing']:+d}%)")

                # Analyser où pourrait être le score manquant
                if anomaly["missing"] > 0:
                    print(f"    ⚠️  Il MANQUE {anomaly['missing']}%")

                    # Vérifier s'il y a des petits scores (< 5) qui pourraient être confondus
                    small_scores = [s for s in anomaly["scores"] if s < 5]
                    if small_scores:
                        print(f"    💡 Petits scores présents: {small_scores}")
                        print(f"       → Le {anomaly['missing']}% pourrait être confondu avec un autre score")

                    # Vérifier la position (début ou fin)
                    first_score = anomaly["scores"][0]
                    last_score = anomaly["scores"][-1]

                    if first_score < 5:
                        print(f"    💡 Premier score très petit ({first_score}%)")
                        print(f"       → Le {anomaly['missing']}% pourrait être AVANT")
                    elif last_score < 5:
                        print(f"    💡 Dernier score très petit ({last_score}%)")
                        print(f"       → Le {anomaly['missing']}% pourrait être APRÈS")
                    else:
                        print(f"    💡 Pas de très petit score aux extrémités")
                        print(f"       → Le {anomaly['missing']}% pourrait être AU MILIEU")
                else:
                    print(f"    ⚠️  Total EXCÈDE de {-anomaly['missing']}%")

                print()

        break


if __name__ == "__main__":
    print("\n🔍 DÉTECTION DES ANOMALIES (total != 100%)")

    for page_num in [17, 18, 19, 20, 21]:
        find_anomalies_in_page(page_num)

    print("=" * 80)
