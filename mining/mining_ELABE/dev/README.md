# dev/ - Scripts de développement et exploration

Ce dossier contient les scripts utilisés pendant le développement du système d'extraction ELABE.
Ces scripts ne sont **pas nécessaires** pour utiliser le mining ELABE en production.

## 📁 Contenu

### 🔍 Scripts d'exploration

- **`elabe_analyzer.py`** : Outil d'analyse de structure PDF
  - Explore les pages d'un PDF ELABE
  - Affiche les éléments textuels et leur position
  - Usage : `python elabe_analyzer.py <pdf_path> [--page N]`

- **`ANALYSIS.md`** : Documentation des observations sur la structure des PDFs
  - Résultats de l'exploration initiale
  - Patterns identifiés
  - Stratégies d'extraction

### 🧪 Scripts de test/validation

- **`check_all_pdfs_counts.py`** : Vérifie le nombre de candidats par page sur tous les PDFs

- **`detect_anomalies.py`** : Prototype de détection d'anomalies
  - Remplacé par `anomaly_detector.py` (dans le core)

- **`analyze_missing_score.py`** : Analyse des scores manquants
  - Aide à comprendre les anomalies de somme ≠ 100%

- **`show_apostrophe_codes.py`** : Debug des caractères d'apostrophe
  - Utilisé pour résoudre le problème d'apostrophe typographique (U+2019)

### 🔧 Prototypes

- **`extract_and_export.py`** : Premier prototype d'extraction complète
  - **Remplacé par** : `elabe_build.py` (CLI principal dans le core)
  - Conservé pour référence historique

### 📄 Fichiers d'analyse

- **`analysis_page17.txt`** : Analyse détaillée de la page 17
- **`analysis_page7.txt`** : Analyse de la page 7
- **`analysis_page9.txt`** : Analyse de la page 9

Ces fichiers ont été générés par `elabe_analyzer.py` lors de l'exploration initiale.

## ⚠️ Important

Ces scripts sont conservés pour :
- **Documentation historique** du processus de développement
- **Outils de debug** en cas de problème sur un nouveau PDF
- **Références** pour de futures améliorations

Pour utiliser le mining ELABE en production, utilisez uniquement :
```bash
cd /path/to/mining_ELABE
python elabe_build.py <pdf_path> <date> [--population <pop>]
```

Voir `../README.md` pour la documentation complète.
