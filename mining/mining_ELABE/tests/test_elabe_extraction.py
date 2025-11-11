#!/usr/bin/env python3
# coding: utf-8
"""
Test de l'extraction des données ELABE - Page 17
"""

import pathlib
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer


def extract_candidates_and_scores(pdf_path: pathlib.Path, page_num: int = 17, debug: bool = False):
    """
    Extrait les noms de candidats et leurs scores depuis une page PDF ELABE.
    
    Args:
        pdf_path: Chemin vers le PDF
        page_num: Numéro de page (17-21)
        debug: Afficher les messages de debug
    
    Returns:
        dict: {nom_candidat: [score1, score2, score3, score4, score5]}
    """
    for page_number, page_layout in enumerate(extract_pages(str(pdf_path)), start=1):
        if page_number != page_num:
            continue
        
        elements = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:
                    elements.append({
                        'text': text,
                        'x': element.x0,
                        'y': element.y0
                    })
        
        # 1. Trouver le bloc des noms
        names_block = None
        for elem in elements:
            if 'Jordan Bardella' in elem['text'] and 'Marine Le Pen' in elem['text']:
                names_block = elem
                break
        
        if not names_block:
            return {}
        
        candidate_names = [n.strip() for n in names_block['text'].split('\n') if n.strip()]
        
        # 2. Extraire les scores (nombres uniquement)
        scores = []
        for elem in elements:
            text = elem['text'].replace('%', '').strip()
            try:
                value = int(text)
                if 0 <= value <= 100:
                    scores.append({
                        'value': value,
                        'x': elem['x'],
                        'y': elem['y']
                    })
            except ValueError:
                pass
        
        # Trier les scores par Y (haut en bas) puis regrouper
        scores.sort(key=lambda s: -s['y'])
        
        # Regrouper par ligne (même Y ± 2)
        lines = []
        current_line = []
        current_y = None
        
        for score in scores:
            if current_y is None:
                current_y = score['y']
                current_line = [score]
            elif abs(score['y'] - current_y) < 2.0:
                current_line.append(score)
            else:
                if current_line:
                    # Trier la ligne par X (gauche à droite)
                    current_line.sort(key=lambda s: s['x'])
                    lines.append(current_line)
                current_line = [score]
                current_y = score['y']
        
        if current_line:
            current_line.sort(key=lambda s: s['x'])
            lines.append(current_line)
        
        # Filtrer les lignes qui ont 5 ou 6 éléments (6 = 5 scores + total)
        # Ne garder que les 5 premiers éléments de chaque ligne
        score_lines = []
        for line in lines:
            if len(line) >= 5:
                # Ne prendre que les 5 premiers éléments (ignorer le total si présent)
                score_lines.append(line[:5])
        
        # Debug optionnel
        if debug:
            print(f"\nDEBUG: {len(lines)} lignes totales, {len(score_lines)} avec 5+ éléments")
            if len(lines) > 0:
                print(f"Ligne 1 (Y≈{lines[0][0]['y']:.2f}): {[s['value'] for s in lines[0][:5]]}")
            if len(lines) > 1:
                print(f"Ligne 2 (Y≈{lines[1][0]['y']:.2f}): {[s['value'] for s in lines[1][:5]]}")
            if len(lines) >= 2:
                line_values = [s['value'] for s in lines[-2][:5]]
                print(f"Ligne -2 (Y≈{lines[-2][0]['y']:.2f}): {line_values}")
                if len(lines[-1]) >= 5:
                    line_values = [s['value'] for s in lines[-1][:5]]
                    print(f"Ligne -1 (Y≈{lines[-1][0]['y']:.2f}): {line_values}")
        
        # 3. Associer candidats et scores
        results = {}
        for i in range(min(len(candidate_names), len(score_lines))):
            name = candidate_names[i]
            scores_values = [s['value'] for s in score_lines[i]]
            results[name] = scores_values
        
        return results
    
    return {}


def test_elabe_page17_extraction():
    """Test l'extraction des données de la page 17 du PDF ELABE novembre 2025"""
    pdf_path = pathlib.Path("../../polls/elabe_202511/source.pdf")
    
    assert pdf_path.exists(), f"PDF non trouvé : {pdf_path}"
    
    # Extraire les données
    results = extract_candidates_and_scores(pdf_path, page_num=17, debug=True)
    
    # Vérifications
    assert len(results) > 0, "Aucune donnée extraite"
    
    # Tests spécifiques demandés
    expected = {
        "Jordan Bardella": [18, 21, 14, 37, 10],
        "Marine Le Pen": [15, 22, 15, 38, 10],
        "Edouard Philippe": [4, 29, 25, 27, 15],
        "Nicolas Sarkozy": [5, 20, 21, 40, 14],
        "Jean-Noël Barrot": [1, 8, 14, 22, 55],
        "Jean-Pierre Farandou": [1, 7, 12, 17, 63],
        "Eric Zemmour": [5, 14, 14, 57, 10],
        "Olivier Faure": [1, 14, 24, 29, 32],
    }
    
    for name, expected_scores in expected.items():
        assert name in results, f"Candidat '{name}' non trouvé dans les résultats"
        actual_scores = results[name]
        assert actual_scores == expected_scores, \
            f"{name}: attendu {expected_scores}, obtenu {actual_scores}"
        
        # Vérifier que la somme = 100
        total = sum(actual_scores)
        assert total == 100, f"{name}: total = {total}% (attendu 100%)"
    
    print(f"\n✅ Test réussi ! {len(expected)} candidats vérifiés :")
    for name, scores in expected.items():
        print(f"  • {name:25s} : {scores} (total: {sum(scores)}%)")


if __name__ == "__main__":
    test_elabe_page17_extraction()
