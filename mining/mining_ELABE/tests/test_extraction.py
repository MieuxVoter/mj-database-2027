#!/usr/bin/env python3
# coding: utf-8
"""
Test d'extraction des données ELABE - Page 17

Objectif : Valider qu'on peut extraire correctement les noms et scores
"""

import pathlib
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer


def extract_page_17(pdf_path: pathlib.Path):
    """Extrait les données de la page 17"""
    
    print(f"📄 Extraction de : {pdf_path}")
    print("=" * 80)
    
    # Extraire la page 17
    for page_num, page_layout in enumerate(extract_pages(str(pdf_path)), start=1):
        if page_num != 17:
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
        
        print(f"✓ {len(elements)} éléments extraits\n")
        
        # 1. Trouver le bloc des noms
        names_block = None
        for elem in elements:
            if 'Jordan Bardella' in elem['text'] and 'Marine Le Pen' in elem['text']:
                names_block = elem
                break
        
        if not names_block:
            print("❌ Bloc des noms non trouvé")
            return
        
        print("📝 NOMS DES CANDIDATS")
        print("-" * 80)
        candidate_names = [n.strip() for n in names_block['text'].split('\n') if n.strip()]
        for i, name in enumerate(candidate_names, start=1):
            print(f"{i:2d}. {name}")
        
        print(f"\n✓ {len(candidate_names)} candidats trouvés")
        
        # 2. Extraire les scores (nombres uniquement)
        scores = []
        for elem in elements:
            text = elem['text'].replace('%', '').strip()
            try:
                value = int(text)
                if 0 <= value <= 100:  # Filtrer les valeurs raisonnables
                    scores.append({
                        'value': value,
                        'x': elem['x'],
                        'y': elem['y']
                    })
            except ValueError:
                pass
        
        print(f"\n🔢 SCORES")
        print("-" * 80)
        print(f"✓ {len(scores)} valeurs numériques extraites")
        
        # Trier les scores par Y (haut en bas)
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
        
        print(f"✓ {len(lines)} lignes de scores détectées")
        
        # Debug : afficher toutes les lignes détectées avec leur taille
        print(f"\n🔍 DEBUG : Détail des lignes")
        print("-" * 80)
        for i, line in enumerate(lines, start=1):
            values = [s['value'] for s in line]
            y_values = [s['y'] for s in line]
            y_avg = sum(y_values) / len(y_values) if y_values else 0
            print(f"Ligne {i:2d} (Y≈{y_avg:6.2f}, {len(line)} éléments) : {values}")
        
        # 3. Associer candidats et scores
        print(f"\n📊 ASSOCIATION CANDIDATS ↔ SCORES")
        print("=" * 80)
        
        # Filtrer les lignes qui ont 5 éléments (les colonnes de scores)
        score_lines = [line for line in lines if len(line) == 5]
        
        print(f"✓ {len(score_lines)} lignes avec exactement 5 scores")
        print(f"  (Total lignes détectées : {len(lines)})")
        print(f"  (Lignes avec 5 éléments : indices {[i for i, line in enumerate(lines, start=1) if len(line) == 5]})")
        print()
        
        if len(score_lines) != len(candidate_names):
            print(f"ℹ️  Note : {len(candidate_names)} candidats mais {len(score_lines)} lignes de scores")
            print(f"   → {len(candidate_names) - len(score_lines)} candidat(s) sans données (marqués 'NP*' = Non Posé)")
            print()
        
        # Afficher TOUTES les associations pour trouver le problème
        print("TOUTES les associations :")
        print("-" * 80)
        
        for i in range(len(candidate_names)):
            name = candidate_names[i]
            if i < len(score_lines):
                scores_values = [s['value'] for s in score_lines[i]]
                total = sum(scores_values)
                status = "✓" if total == 100 else f"⚠️  {total}%"
                print(f"{i+1:2d}. {name:25s} | {scores_values[0]:2d} {scores_values[1]:2d} {scores_values[2]:2d} {scores_values[3]:2d} {scores_values[4]:2d} | Total: {total:3d}% {status}")
            else:
                print(f"{i+1:2d}. {name:25s} | ❌ PAS DE SCORES")
        
        # 4. Statistiques de validation
        print(f"\n📈 VALIDATION")
        print("=" * 80)
        
        valid_count = 0
        invalid_count = 0
        
        for i in range(len(score_lines)):
            scores_values = [s['value'] for s in score_lines[i]]
            total = sum(scores_values)
            if total == 100:
                valid_count += 1
            else:
                invalid_count += 1
                if i < len(candidate_names):
                    print(f"⚠️  {candidate_names[i]}: Total = {total}%")
        
        print(f"\n✓ Lignes valides (total = 100%) : {valid_count}")
        if invalid_count > 0:
            print(f"⚠️  Lignes invalides : {invalid_count}")
        
        return


if __name__ == "__main__":
    pdf_path = pathlib.Path("../../polls/elabe_202511/source.pdf")
    
    if not pdf_path.exists():
        print(f"❌ Fichier non trouvé : {pdf_path}")
        exit(1)
    
    extract_page_17(pdf_path)
