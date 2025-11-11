# coding: utf-8
"""
Analyse détaillée: où est le 2% manquant pour Laurent Nunez ?
"""

import pathlib
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

PDF_PATH = pathlib.Path(__file__).parent.parent.parent / "polls" / "elabe_202511" / "source.pdf"

def analyze_laurent_nunez_detailed():
    """Analyse ultra-détaillée de la ligne Laurent Nunez."""
    print("\n🔍 ANALYSE DÉTAILLÉE: Laurent Nunez (Page 18)")
    print("="*80)
    
    for page_number, page_layout in enumerate(extract_pages(str(PDF_PATH)), start=1):
        if page_number != 18:
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
        
        # 1. Trouver le Y de Laurent Nunez
        laurent_y = None
        for elem in elements:
            text = elem['text']
            if 'Laurent Nunez' in text:
                laurent_y = elem['y']
                break
        
        print(f"\n✅ Laurent Nunez à Y = {laurent_y:.2f}")
        
        # 2. Trouver TOUS les nombres (0-100) dans une large bande autour
        all_numbers = []
        for elem in elements:
            text = elem['text'].replace('%', '').strip()
            try:
                value = int(text)
                if 0 <= value <= 100:
                    y_diff = abs(elem['y'] - laurent_y)
                    if y_diff <= 10.0:  # Large bande
                        all_numbers.append({
                            'value': value,
                            'x': elem['x'],
                            'y': elem['y'],
                            'y_diff': y_diff
                        })
            except ValueError:
                pass
        
        # Trier par Y puis X
        all_numbers.sort(key=lambda n: (-n['y'], n['x']))
        
        print(f"\n📊 Tous les nombres à ±10px de Y = {laurent_y:.2f} :")
        print(f"{'':4s} {'X':>8s}  {'Y':>8s}  {'ΔY':>6s}  {'Val':>5s}")
        print("-" * 35)
        
        for n in all_numbers:
            marker = "🎯" if n['y_diff'] < 0.5 else "  "
            print(f"{marker} {n['x']:8.2f}  {n['y']:8.2f}  {n['y_diff']:6.2f}  {n['value']:5d}")
        
        # 3. Grouper par Y avec différentes tolérances
        print(f"\n🔍 Groupement avec différentes tolérances :\n")
        
        for tolerance in [0.5, 1.0, 2.0, 3.0, 5.0]:
            # Filtrer ceux très proches de laurent_y
            close_numbers = [n for n in all_numbers if n['y_diff'] < tolerance]
            close_numbers.sort(key=lambda n: n['x'])
            
            if close_numbers:
                values = [n['value'] for n in close_numbers]
                total = sum(values)
                status = "✓" if total == 100 else f"⚠️  {total}%"
                
                print(f"  Tolérance ±{tolerance}px: {len(close_numbers)} scores → {values} | {status}")
        
        # 4. Analyse des X positions (colonnes attendues)
        print(f"\n📏 Analyse des colonnes (X positions) :\n")
        
        # Trouver toutes les colonnes de la page
        all_score_numbers = []
        for elem in elements:
            text = elem['text'].replace('%', '').strip()
            try:
                value = int(text)
                if 0 <= value <= 100:
                    all_score_numbers.append({
                        'value': value,
                        'x': elem['x'],
                        'y': elem['y']
                    })
            except ValueError:
                pass
        
        # Regrouper par X (colonnes)
        x_positions = {}
        for n in all_score_numbers:
            x_rounded = round(n['x'] / 10) * 10  # Arrondir à 10px
            if x_rounded not in x_positions:
                x_positions[x_rounded] = []
            x_positions[x_rounded].append(n)
        
        # Garder les colonnes avec au moins 10 valeurs
        main_columns = {x: nums for x, nums in x_positions.items() if len(nums) >= 10}
        sorted_columns = sorted(main_columns.keys())
        
        print(f"  Colonnes principales détectées ({len(sorted_columns)}) :")
        for x in sorted_columns:
            count = len(main_columns[x])
            print(f"    X ≈ {x:5.0f}px : {count:2d} valeurs")
        
        # 5. Pour Laurent Nunez, vérifier chaque colonne
        print(f"\n🎯 Scores de Laurent Nunez par colonne :\n")
        
        laurent_scores = []
        for x in sorted_columns:
            # Chercher un score proche de laurent_y et de cette colonne X
            candidates = [n for n in all_numbers 
                         if abs(n['x'] - x) < 15 and n['y_diff'] < 3.0]
            if candidates:
                best = min(candidates, key=lambda n: n['y_diff'])
                laurent_scores.append(best)
                print(f"  Colonne X≈{x:5.0f} : {best['value']:3d}%  (Y={best['y']:.2f}, ΔY={best['y_diff']:.2f})")
        
        if laurent_scores:
            total = sum(s['value'] for s in laurent_scores)
            print(f"\n  Total: {total}% {'✓' if total == 100 else '⚠️'}")
            
            if total != 100:
                diff = 100 - total
                print(f"\n  💡 Différence: {diff:+d}%")
                print(f"     → Vérifier le PDF pour un score manquant de {abs(diff)}%")
        
        break

if __name__ == "__main__":
    analyze_laurent_nunez_detailed()
