# Mining ELABE

Extraction automatique des données de sondage ELABE depuis les PDFs sources.

## 🎯 Fonctionnalités

- ✅ **Détection automatique des pages** : Identifie automatiquement les pages contenant les données
- ✅ **Extraction robuste** : Extrait 30 candidats par page avec leurs 5 scores d'opinion
- ✅ **Support multi-format** : Gère les PDFs avec pages 13-17 ou 17-21
- ✅ **Détection d'anomalies** : Identifie les scores manquants ou incorrects
- ✅ **Export des anomalies** : Génère des rapports détaillés pour correction manuelle
- ✅ **Validation automatique** : Utilise `candidates.csv` pour identifier les candidats

## 📁 Structure

```
mining_ELABE/
├── __init__.py              # Point d'entrée du module
├── elabe_build.py          # 🎯 CLI principal (utiliser celui-ci !)
├── elabe_miner.py          # Classe principale d'extraction
├── elabe_builder.py        # Construction des CSV
├── page_detector.py        # Détection automatique des pages
├── elabe_poll.py           # Structure de données ElabeLine
├── anomaly_detector.py     # Détection et export des anomalies
├── tests/                  # Tests unitaires
├── dev/                    # Scripts de développement/debug
└── old_fashion_way/        # Ancien workflow manuel (déprécié)
```

## 🚀 Usage rapide

### CLI (recommandé)

```bash
# Extraire toutes les populations d'un PDF
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511

# Extraire une seule population
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511 --population all

# Écraser les fichiers existants
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511 --overwrite
```

### API Python (usage avancé)

```python
from mining_ELABE import ElabeMiner, PageDetector, ElabeBuilder

# 1. Détecter les pages de données
detector = PageDetector(pdf_path)
data_pages = detector.detect_data_pages(start_page=1, end_page=25)

print(detector.get_summary(data_pages))
# 📊 5 page(s) de données détectée(s) :
#   • Page 13: Ensemble des Français
#   • Page 14: Électeurs de gauche
#   • Page 15: Électeurs de Macron
#   • Page 16: Électeurs d'extrême droite
#   • Page 17: Abstentionnistes

# 2. Extraire chaque page
miner = ElabeMiner(pdf_path)

for page_num, population in data_pages:
    lines = miner.extract_page(page_num)
    print(f"✓ {len(lines)} candidats extraits")
    
    # Vérifier les anomalies
    if miner.has_anomalies():
        miner.export_anomalies(output_dir, population)
    
    # Réinitialiser pour la page suivante
    miner.anomaly_detector.anomalies.clear()
```

### Script complet

```bash
# Éditer le fichier pour changer le PDF
cd mining_ELABE

# Extraire toutes les populations
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511

# Résultat : 5 CSV générés automatiquement
ls -1 ../../polls/elabe_202511/elabe_202511_*.csv
```

## 📊 Format des données

### Structure ElabeLine

Chaque ligne représente un candidat avec ses 5 scores d'opinion :
- **Très positive** : % d'image très positive
- **Plutôt positive** : % d'image plutôt positive  
- **Plutôt négative** : % d'image plutôt négative
- **Très négative** : % d'image très négative
- **Sans opinion** : % sans opinion

**Validation** : La somme des 5 scores doit toujours égaler 100%

### Populations détectées

- `all` : Ensemble des Français
- `left` : Électeurs de gauche et des écologistes
- `macron` : Électeurs d'Emmanuel Macron
- `farright` : Électeurs de Marine Le Pen et d'Éric Zemmour
- `absentionists` : Abstentionnistes, votes blancs et nuls

## ⚠️ Gestion des anomalies

Le système détecte automatiquement 3 types d'anomalies :

### 1. Scores manquants (total < 100%)

Exemple : Laurent Nunez - Page 18
- **Scores extraits** : [8, 13, 29, 48] = 98%
- **Manque** : 2%
- **Position suggérée** : début (avant le premier score)

Le système génère un fichier `mining_anomalie_absentionists.txt` :

```
ANOMALIE #1
Page:           18
Ligne:          18
Candidat:       Laurent Nunez

Scores extraits: [8, 13, 29, 48]
Total:           98% (attendu 100%)
Différence:      +2%

Position suggérée du score manquant:
  → début (avant le premier score)

ACTION REQUISE:
  1. Ouvrir le PDF source
  2. Aller à la page 18
  3. Trouver la ligne 'Laurent Nunez'
  4. Vérifier si une barre de 2% est présente mais illisible
  5. Si oui, ajouter manuellement le score manquant
  6. Scores attendus: ajouter 2% au début
```

### 2. Scores en excès (total > 100%)

Généralement causé par la capture du total (6ème colonne).
Le système filtre automatiquement en ne gardant que les 5 premiers scores.

### 3. Lignes avec 4 scores au lieu de 5

Certains candidats n'ont que 4 colonnes dans le PDF.
Le système accepte les lignes avec 4 ou 5 scores.

## 🔧 Outils inclus

### elabe_build.py (CLI principal)

Script principal pour l'extraction automatisée :

```bash
# Aide complète
python elabe_build.py --help

# Extraire tout
python elabe_build.py <pdf_path> <date>

# Options
--population {all,left,macron,farright,absentionists}
--overwrite              # Écraser les CSV existants
--candidates <path>      # Chemin vers candidates.csv
```

### dev/elabe_analyzer.py (debug)

Outil d'exploration pour comprendre la structure d'un PDF :

```bash
# Analyser tout le PDF
python dev/elabe_analyzer.py polls/elabe_202511/source.pdf

# Analyser une page spécifique
python dev/elabe_analyzer.py polls/elabe_202511/source.pdf --page 17

# Sauvegarder le rapport
python dev/elabe_analyzer.py polls/elabe_202511/source.pdf --save analysis.txt
```

## 📝 Résultats

### elabe_202510 (pages 13-17)
- ✅ 150 candidats extraits (30 par page)
- ⚠️ 2 anomalies détectées :
  - Jordan Bardella (page 14) : manque 4%
  - Marion Maréchal (page 14) : manque 2%

### elabe_202511 (pages 17-21)
- ✅ 150 candidats extraits (30 par page)
- ⚠️ 1 anomalie détectée :
  - Laurent Nunez (page 18) : manque 2%

## 🛠️ Développement

### Dépendances

```python
pdfminer.six  # Extraction PDF
```

### Tests

```bash
# Test du détecteur de pages
python test_page_detector.py

# Test du miner
python test_miner.py

# Test de détection d'anomalies
python test_anomalies.py
```

## 📚 Architecture

Le module suit le pattern établi par `mining_IFOP` :

1. **ElabeLine** : Implémente `CandidatePollInterface`
2. **ElabeMiner** : Extrait les données du PDF
3. **PageDetector** : Détecte automatiquement les pages de données
4. **AnomalyDetector** : Valide et exporte les anomalies

### Gestion des apostrophes typographiques

Les PDFs ELABE utilisent l'apostrophe typographique (U+2019) au lieu de l'apostrophe standard (U+0027).
Le système normalise automatiquement les apostrophes pour la détection des populations.
