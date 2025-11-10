# Mining IPSOS - Extraction de sondages IPSOS

Ce dossier contient les outils pour extraire automatiquement les données de sondages IPSOS depuis des fichiers HTML sources.

## Scripts disponibles

### `extract_ipsos_from_html.py`

Extrait les données de sondages IPSOS depuis des fichiers HTML sources (visualisations Flourish).

**Usage depuis la racine du projet :**
```bash
python mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_AAAAMM/source.html [output.csv]
```

**Exemple :**
```bash
# Extraction automatique (génère ipsos_202511_all.csv dans le même dossier)
python mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_202511/source.html

# Avec nom de fichier de sortie personnalisé
python mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_202511/source.html polls/ipsos_202511/custom.csv
```

### `validate_poll.py`

Valide la structure et le contenu d'un fichier CSV de sondage.

**Usage depuis la racine du projet :**
```bash
python mining_IPSOS/validate_poll.py polls/ipsos_AAAAMM/ipsos_AAAAMM_all.csv [--strict]
```

**Exemple :**
```bash
python mining_IPSOS/validate_poll.py polls/ipsos_202511/ipsos_202511_all.csv
```

### `example_add_poll.py`

Script d'exemple montrant le workflow complet automatisé.

**Usage depuis la racine du projet :**
```bash
python mining_IPSOS/example_add_poll.py
```

⚠️ **Note :** Éditez d'abord le script pour configurer les dates et détails du sondage.

## Format IPSOS

- **6 mentions de satisfaction** :
  1. Très satisfait
  2. Plutôt satisfait
  3. Ni satisfait ni insatisfait
  4. Plutôt insatisfait
  5. Très insatisfait
  6. NSP (Ne se prononce pas)

- **Type de sondage** : `pt1`
- **Population** : Généralement uniquement `all`
- **Question** : "Pour chacune des personnalités politiques suivantes, diriez-vous que si elle devenait président(e) de la République en 2027, vous seriez satisfait(e) ou mécontent(e) ?"

## Workflow complet

### 1. Télécharger le HTML source
```bash
# Sauvegarder la page complète dans polls/ipsos_AAAAMM/source.html
mkdir -p polls/ipsos_202512
# Télécharger depuis le site IPSOS/La Tribune Dimanche
```

### 2. Extraire les données
```bash
python mining_IPSOS/extract_ipsos_from_html.py polls/ipsos_202512/source.html
```

### 3. Valider les données
```bash
python mining_IPSOS/validate_poll.py polls/ipsos_202512/ipsos_202512_all.csv
```

### 4. Ajouter les métadonnées dans polls.csv
```bash
echo "ipsos_202512,pt1,1000,2025-12-04,2025-12-05,polls/ipsos_202512,all" >> polls.csv
```

### 5. Fusionner avec la base de données
```bash
python merge.py
```

### 6. Vérifier et commiter
```bash
git add polls/ipsos_202512/ polls.csv mj2027.csv
git commit -m "Add IPSOS December 2025 poll"
git push
```

## Ajouter un nouveau candidat

Si un candidat n'est pas reconnu par le script :

### Ajouter dans `candidates.csv` (racine du projet)
```csv
NC,Nouveau,Candidat,Parti,,,
```

Le script charge automatiquement tous les candidats depuis ce fichier, **aucune modification du code n'est nécessaire** !

## Dépendances

Aucune dépendance externe ! Utilise uniquement la bibliothèque standard Python :
- `json` : Parsing des données JSON
- `re` : Expressions régulières
- `csv` : Manipulation CSV
- `pathlib` : Gestion des chemins
- `subprocess` : Exécution de commandes (pour example_add_poll.py)

## Exemples de données

### Entrée (HTML source)
Le fichier HTML contient du JavaScript avec les données au format JSON :
```json
{"label":"Jordan Bardella","metadata":[],"value":[21,16,15,8,38,2]}
```

### Sortie (CSV)
```csv
candidate_id,intention_mention_1,intention_mention_2,intention_mention_3,intention_mention_4,intention_mention_5,intention_mention_6,intention_mention_7,poll_type_id,population
JB,21,16,15,8,38,2,,pt1,all
```

## Dépannage

### "Candidate not found in mapping"
→ Ajouter le candidat dans `candidates.csv` à la racine du projet  
→ Format: `ID,Prénom,Nom,Parti,,,`  
→ Le script le chargera automatiquement au prochain lancement

### "Could not find data array in HTML file"
→ Vérifier que le fichier source.html contient bien les données JSON (rechercher `"data":[`)

### "Validation failed"
→ Utiliser `--strict` pour voir tous les problèmes
→ Vérifier le format CSV et les valeurs de pourcentages

## Tests réussis

✅ **IPSOS Novembre 2025** (`ipsos_202511`)
- 28 candidats extraits
- 0 erreur de mapping
- Validation 100% réussie
- Fusionné avec succès dans `mj2027.csv`

## Voir aussi

- Documentation générale : `../README.md`
- Mining ELABE : `../mining_ELABE/`
- Mining IFOP : `../mining_IFOP/`
