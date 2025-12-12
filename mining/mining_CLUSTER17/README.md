# Mining CLUSTER 17

Extraction automatique des données de sondage CLUSTER 17/ depuis les PDFs sources.

## 🎯 Fonctionnalités

- ✅ **Détection automatique des pages** : Identifie automatiquement les pages contenant les données
- ✅ **Extraction robuste** : Extrait candidats et légendes (captions) par page avec leurs 4 scores d'opinion
- ✅ **Détection d'anomalies** : Identifie les scores manquants ou incorrects
- ✅ **Export des anomalies** : Génère des rapports détaillés pour correction manuelle
- ✅ **Validation automatique** : Utilise `candidates.csv` pour identifier les candidats

## 📁 Structure

```
mining/
│
├── base_pipeline.py                 	# Classe abstraite commune à tous les pipelines
│
└── mining_CLUSTER17/
	├── orchestrator.py                 # Orchestrateur principal du pipeline Cluster17
	├── extractor.py         			# Extraction des tableaux et légendes depuis le PDF
	├── builder.py            			# Nettoyage, fusion et export CSV
	├── anomaly_detector.py   			# Détection et rapport des anomalies
	├── cli.py              			# Interface en ligne de commande (exécution utilisateur)
	└── tests/                          # Tests unitaires (MISSING)
```

## Flux de traitement global
```bash
PDF Source → Extraction → Nettoyage / Normalisation → Fusion candidats.csv
          → Détection anomalies → CSV final + Rapport TXT
```
1. Extraction (extractor.py)
	- Analyse les pages PDF.
	- Identifie automatiquement les tableaux de sondage.
	- Détecte la population correspondante (étiquette, page, etc.).
2. Construction (builder.py)
	- Nettoie les colonnes et les valeurs (normalisation, suppression du symbole %).
	- Fusionne les données avec candidates.csv.
	- Génère le fichier CSV final.
	- Déclenche l’analyse des anomalies.
3. Détection d’anomalies (anomaly_detector.py)
	- Vérifie les incohérences entre les colonnes d’intention (total ≠ 100 %).
	- Supprime automatiquement les candidats dont l’écart dépasse ±4 %.
	- Exporte un rapport détaillé dans mining_anomalie_<population>.txt.
4. Orchestration (orchestrator.py)
	- Coordonne toutes les étapes via Cluster17Pipeline, héritant de BasePipeline.
5. Exécution CLI (cli.py)
	- Permet de lancer l’ensemble du pipeline depuis le terminal.

## 🚀 Usage rapide

### CLI (recommandé)

**Commande de base**
```bash
python -m mining_CLUSTER17.cli <chemin_du_pdf> <date_du_sondage>
```

**Exemple concret**
```bash
python -m mining.mining_CLUSTER17.cli  polls/cluster17_202510/source.pdf 202510
```

## 📊 Format des données

### Structure ElabeLine

Chaque ligne représente un candidat avec ses 4 scores d'opinion :
- **Vous la soutenez** : % de personnes déclarant soutenir la personnalité.
- **Vous l’appréciez** : % de personnes exprimant une opinion favorable envers la personnalité.
- **Vous ne l’appréciez pas** : % de personnes exprimant une opinion défavorable envers la personnalité.
- **Vous n’avez pas d’avis sur elle/Vous ne la connaissez pas** : % de personnes n’ayant pas d’opinion ou déclarant ne pas connaître la personnalité.

**Validation** : La somme des 4 scores doit toujours égaler 100%

### Populations détectées

- `all` : Ensemble des Français  
- `macron` : Électeurs d’Emmanuel Macron  
- `lepen` : Électeurs de Marine Le Pen 2022  
- `melenchon` : Électeurs de Jean-Luc Mélenchon 2022  
- `lfi` : Électeurs de LFI aux Européennes 2024  
- `ecologistes` : Électeurs Les Écologistes aux Européennes 2024  
- `pspp` : Électeurs PS/PP aux Européennes 2024  
- `renaissance` : Électeurs Renaissance aux Européennes 2024  
- `lr` : Électeurs LR aux Européennes 2024  
- `rn` : Électeurs RN aux Européennes 2024  
- `reconquete` : Électeurs Reconquête aux Européennes 2024  





## ⚠️ Gestion des anomalies (Le système génère un fichier `mining_anomalie_POPULATION.txt` :)

Le système détecte automatiquement 2 types d'anomalies :

### 1. Candidats introuvables dans `candidates.csv`

Exemple : Lucie Castets - Page 19
- **Page** :            19
- **Candidat** :        Lucie Castets
- **Population** :      lepen

```
ANOMALIE #1
Page:			19
Candidat:		Lucie Castets
Population:		lepen

Description:
	Le candidat n’a pas été trouvé dans le fichier « candidates.csv ».
	Il est possible que ce candidat n’existe pas dans la base de référence ou qu’une erreur orthographique soit présente dans le nom.

ACTION REQUISE :
	1. Ouvrez le fichier « candidates.csv »
	2. Vérifiez si le candidat « Lucie Castets » est présent dans la base de référence.
	3. Si le nom existe déjà mais avec une orthographe différente (accents, espaces, etc.),
	   ne modifiez PAS le fichier « candidates.csv ».
	   Dans ce cas, vous pouvez :
	     Renseigner manuellement la colonne « candidate_id » directement
	     dans le fichier CSV de l’enquête concernée.	
	4. Si le candidat est absent, ajoutez-le manuellement dans « candidates.csv ».
		Dans ce cas, vous pouvez :
		 Relancer le processus d'extraction des données.
```

### 2. Scores manquants (total ± 100%)

Exemple : Lucie Castets - Page 19
- **Scores extraits** : [8, 13, 29, 48] = 98%
- **Total** :           110% (attendu 100%)
- **Différence** :      +1%



```
ANOMALIE #1
Page:			19
Candidat:		Lucie Castets
Population:		lepen

Scores extraits:	[2, 18, 62, 28]
Total:				110% (attendu 100%)
Différence:			+1%

Description:
	Le total des intentions de vote pour ce candidat ne correspond pas à 100 %.
	Cela indique une incohérence dans les pourcentages extraits depuis le PDF, qui peut être due à une erreur de reconnaissance, à une valeur manquante ou à un doublon.

ACTION REQUISE :
	1. Ouvrez le fichier PDF de l’enquête correspondante.
	2. Recherchez la ligne du candidat « Rachida Dati » et vérifiez les pourcentages affichés.
	3. Si une erreur est détectée, corrigez manuellement les valeurs
	   dans le fichier CSV de la population correspondante :
	     • Pour un total supérieur à 100 %, vérifiez s’il existe un doublon ou une valeur mal lue.
	     • Pour un total inférieur à 100 %, vérifiez s’il manque une colonne ou une donnée tronquée.
	4. Enregistrez le fichier corrigé et NE RELANCEZ PAS le processus d'extraction des données.
```

Si l'écart d'intention dépasse ±4%, le candidat sera supprimé automatiquement du fichier CSV

```
Page:				19
Candidat:			Rachida Dati
Population:			lepen

Scores extraits:	[2, 18, 62, 28]
Total:				110% (attendu 100%)
Différence:			+10%

Description:
	Le total des intentions de vote pour ce candidat ne correspond pas à 100 %.
	Cela indique une incohérence dans les pourcentages extraits depuis le PDF, qui peut être due à une erreur de reconnaissance, à une valeur manquante ou à un doublon.

ACTION AUTOMATIQUE :
	Ce candidat a été supprimé automatiquement du fichier CSV car son écart d’intention dépasse ±4%.
```