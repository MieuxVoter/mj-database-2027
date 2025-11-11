# Structure du module mining_ELABE

Cette documentation décrit l'organisation du module après le nettoyage du 11 novembre 2025.

## 📂 Organisation

```
mining_ELABE/
├── Core (7 fichiers Python)
│   ├── elabe_build.py         ⭐ CLI principal
│   ├── elabe_miner.py         Extraction depuis PDF
│   ├── elabe_builder.py       Construction CSV
│   ├── elabe_poll.py          Structure ElabeLine
│   ├── page_detector.py       Détection automatique pages
│   ├── anomaly_detector.py    Gestion anomalies
│   └── __init__.py            Module init
│
├── Documentation
│   ├── README.md              Documentation principale
│   ├── TODO.md                Suivi des phases
│   └── STRUCTURE.md           Ce fichier
│
├── tests/                     Tests unitaires (pytest)
├── dev/                       Scripts de développement
└── old_fashion_way/           Ancien workflow (déprécié)
```

## 🎯 Fichiers principaux

### elabe_build.py (CLI)
**Usage** : Script principal pour extraire automatiquement les données ELABE
```bash
python elabe_build.py <pdf_path> <date> [options]
```

### elabe_miner.py
**Classe** : `ElabeMiner`
- Extrait les candidats et scores depuis un PDF
- Utilise `PageDetector` pour trouver les pages de données
- Détecte les anomalies avec `AnomalyDetector`

### elabe_builder.py
**Classe** : `ElabeBuilder`
- Construit les CSV au format requis (10 colonnes)
- Vérifie les candidats contre `candidates.csv`
- Compatible avec le workflow IFOP

### page_detector.py
**Classe** : `PageDetector`
- Détecte automatiquement les pages contenant les données
- Identifie les 5 populations (all, left, macron, farright, absentionists)
- Gère les variations de pages (13-17 ou 17-21)

### anomaly_detector.py
**Classe** : `AnomalyDetector`
- Détecte les scores manquants (total ≠ 100%)
- Suggère la position du score manquant
- Exporte les rapports d'anomalies

### elabe_poll.py
**Classe** : `ElabeLine`
- Implémente `CandidatePollInterface` (compatibilité IFOP)
- Stocke : nom du candidat + 5 scores
- Valide que la somme = 100%

## 📁 Dossiers

### tests/
Tests unitaires avec pytest
- `conftest.py` : Configuration pytest
- `test_miner.py` : Tests du miner
- `test_page_detector.py` : Tests du détecteur
- etc.

### dev/
Scripts de développement et debug
- **Ne pas utiliser en production**
- Voir `dev/README.md` pour détails

### old_fashion_way/
Ancien workflow manuel (avant automatisation)
- **Déprécié**
- Conservé pour historique

## 🚀 Utilisation rapide

### En ligne de commande
```bash
# Extraire toutes les populations
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511

# Une seule population
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511 --population all

# Avec écrasement
python elabe_build.py ../../polls/elabe_202511/source.pdf 202511 --overwrite
```

### En Python
```python
from elabe_miner import ElabeMiner
from elabe_builder import ElabeBuilder
from page_detector import PageDetector

# Détecter les pages
detector = PageDetector(pdf_path)
pages = detector.detect_data_pages()

# Extraire
miner = ElabeMiner(pdf_path)
lines = miner.extract_page(page_num)

# Construire CSV
builder = ElabeBuilder(candidates_csv, lines)
builder.write(output_path, 'pt2', 'all')
```

## 📝 Historique

- **Phase 1** : Exploration et analyse (oct-nov 2025)
- **Phase 2** : Extraction de base (nov 2025)
- **Phase 3** : Organisation et validation (nov 2025)
- **Phase 4** : Construction CSV (nov 2025)
- **Nettoyage** : 11 novembre 2025 (ce document)

---

**Dernière mise à jour** : 11 novembre 2025
