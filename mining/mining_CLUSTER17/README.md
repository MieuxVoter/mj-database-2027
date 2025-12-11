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
mining_CLUSTER17/
├── cluster17_build.py              # 🎯 CLI principal (utiliser celui-ci !)
├── cluster17.py                    # Exécute le pipeline complet d'extraction et de transformation des données 
├── cluster17_extractor.py          # Responsable de l'extraction des tableaux et des légendes (captions) à partir d'un page PDF
├── cluster17_builder.py            # Responsable de la génération et du nettoyage des fichiers CSV 
├── cluster17_anomaly_detector.py   # Vérifie les identifiants manquants et les incohérences dans les totaux d’intention
├── tests/                          # Tests unitaires (MISSING)
```

## 🚀 Usage rapide

### CLI (recommandé)

```bash
# Extraire toutes les populations d'un PDF
python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 

# Extraire une seule population (MISSING)
python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 --population left

python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 ---overwrite
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





## ⚠️ Gestion des anomalies

Le système détecte automatiquement 3 types d'anomalies :

### 1. Candidats introuvables dans `candidates.csv`


Exemple : Lucie Castets - Page 19
- **Page** :            19
- **Candidat** :        Lucie Castets
- **Population** :      lepen

Le système génère un fichier `mining_anomalie_absentionists.txt` :
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
	3. Si le candidat est absent, ajoutez-le manuellement dans « candidates.csv ».
	4. Si le nom existe déjà mais avec une orthographe différente (accents, espaces, etc.),
	   ne modifiez PAS le fichier « candidates.csv ».
	   Dans ce cas, vous pouvez :
	     Renseigner manuellement la colonne « candidate_id » directement
	     dans le fichier CSV de l’enquête concernée.
```

### 2. Scores manquants (total < 100%)

Exemple : Lucie Castets - Page 19
- **Scores extraits** : [8, 13, 29, 48] = 98%
- **Total** :           110% (attendu 100%)
- **Différence** :      +10%

Le système génère un fichier `mining_anomalie_absentionists.txt` :

```
ANOMALIE #1
Page:			19
Candidat:		Lucie Castets
Population:		lepen

Scores extraits:	[2, 18, 62, 28]
Total:				110% (attendu 100%)
Différence:			+10%

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
	4. Enregistrez le fichier corrigé avant de relancer le traitement.
```
