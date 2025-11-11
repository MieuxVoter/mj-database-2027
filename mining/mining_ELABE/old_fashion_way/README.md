# old_fashion_way/ - Ancien workflow manuel

Ce dossier contient l'ancien workflow manuel utilisé avant l'automatisation.

## 📁 Contenu

- **`manual_mining_elabe_pdf.py`** : Script original de mining manuel
  - Nécessitait une intervention humaine pour chaque page
  - **Déprécié** : remplacé par le système automatisé

- **`zeros.csv`** : Fichier de mapping des zéros
  - Utilisé dans l'ancien workflow manuel

- **`names.txt`** : Liste de noms de candidats
  - Fichier temporaire de l'ancien workflow

- **`table.txt`** : Export de table temporaire

## ⚠️ Statut

**DÉPRÉCIÉ** - Ne pas utiliser

Ce workflow a été remplacé par le système automatisé :
```bash
python elabe_build.py <pdf_path> <date>
```

Conservé uniquement pour référence historique.
