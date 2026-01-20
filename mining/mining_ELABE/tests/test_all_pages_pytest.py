#!/usr/bin/env python3
# coding: utf-8
"""
Tests pytest pour l'extraction ELABE - Toutes les pages
"""

import pytest
import pathlib
import sys

parent_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from test_elabe_extraction import extract_candidates_and_scores

PDF_PATH = pathlib.Path(__file__).parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"


@pytest.mark.parametrize(
    "page_num,expected_candidates",
    [
        (17, 30),  # Ensemble des Français
        (18, 26),  # Population 2
        (19, 30),  # Population 3
        (20, 26),  # Population 4
        (21, 23),  # Population 5
    ],
)
def test_page_extraction(page_num, expected_candidates):
    """Test l'extraction d'une page spécifique"""
    if not PDF_PATH.exists():
        pytest.skip(f"PDF non trouvé : {PDF_PATH}")

    results = extract_candidates_and_scores(PDF_PATH, page_num=page_num)

    # Vérifier le nombre de candidats
    assert (
        len(results) == expected_candidates
    ), f"Page {page_num}: attendu {expected_candidates} candidats, obtenu {len(results)}"

    # Vérifier que tous les totaux = 100%
    for name, scores in results.items():
        total = sum(scores)
        assert total == 100, f"Page {page_num}, {name}: total = {total}% (attendu 100%)"

    # Vérifier que chaque candidat a 5 scores
    for name, scores in results.items():
        assert len(scores) == 5, f"Page {page_num}, {name}: {len(scores)} scores (attendu 5)"


def test_page17_specific_candidates():
    """Test des candidats spécifiques de la page 17"""
    if not PDF_PATH.exists():
        pytest.skip(f"PDF non trouvé : {PDF_PATH}")

    results = extract_candidates_and_scores(PDF_PATH, page_num=17)

    expected = {
        "Jordan Bardella": [18, 21, 14, 37, 10],
        "Marine Le Pen": [15, 22, 15, 38, 10],
        "Jean-Noël Barrot": [1, 8, 14, 22, 55],
        "Jean-Pierre Farandou": [1, 7, 12, 17, 63],
        "Eric Zemmour": [5, 14, 14, 57, 10],
    }

    for name, expected_scores in expected.items():
        assert name in results, f"Candidat '{name}' non trouvé"
        assert results[name] == expected_scores, f"{name}: attendu {expected_scores}, obtenu {results[name]}"


def test_page18_has_different_candidates():
    """Vérifier que la page 18 a des candidats différents"""
    if not PDF_PATH.exists():
        pytest.skip(f"PDF non trouvé : {PDF_PATH}")

    results = extract_candidates_and_scores(PDF_PATH, page_num=18)

    # Vérifier quelques candidats attendus
    assert "Fabien Roussel" in results
    assert "François Ruffin" in results
    assert "Raphaël Glucksmann" in results


def test_all_pages_have_data():
    """Vérifier que toutes les pages ont des données"""
    if not PDF_PATH.exists():
        pytest.skip(f"PDF non trouvé : {PDF_PATH}")

    for page_num in [17, 18, 19, 20, 21]:
        results = extract_candidates_and_scores(PDF_PATH, page_num=page_num)
        assert len(results) > 0, f"Page {page_num}: aucune donnée extraite"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
