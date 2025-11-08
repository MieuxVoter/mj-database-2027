# Comment ajouter un sondage au dépôt mj-database-2027

Ce guide explique comment ajouter un nouveau sondage à la base de données des sondages pour l'élection présidentielle de 2027.

## Structure générale

Le dépôt est organisé comme suit :
- `candidates.csv` : Liste des candidats avec leurs identifiants
- `poll_types.csv` : Types de sondages avec leurs échelles de notation
- `polls.csv` : Métadonnées des sondages
- `polls/` : Dossier contenant les données détaillées de chaque sondage

## Étapes pour ajouter un nouveau sondage

### 1. Préparer les données du sondage

Avant d'ajouter un sondage, assurez-vous d'avoir :
- Les résultats du sondage pour chaque candidat
- Les informations sur l'institut de sondage
- Les dates de réalisation du sondage
- Le nombre de personnes interrogées
- L'échelle utilisée (mentions de satisfaction)

### 2. Vérifier ou ajouter le type de sondage

Consultez le fichier `poll_types.csv` pour voir si le type de sondage existe déjà.

**Structure de poll_types.csv :**
```csv
id,institut,commanditaire,mention1,mention2,mention3,mention4,mention5,mention6,mention7,nombre_mentions,question
```

**Exemple :**
```csv
pt1,IPSOS,La Tribune Dimanche,très satisfait,plutôt satisfait,ni satisfait ni insatisfait,plutôt insatisfait,très insatisfait,NSP,,6,"Pour chacune des personnalités politiques suivantes..."
```

Si votre sondage utilise une nouvelle échelle ou un nouvel institut, ajoutez une nouvelle ligne avec un identifiant unique (pt3, pt4, etc.). (pt = poll type)

### 3. Vérifier les candidats

Consultez `candidates.csv` pour vous assurer que tous les candidats de votre sondage sont référencés.

**Structure de candidates.csv :**
```csv
candidate_id,name,surname,parti,annonce_candidature,retrait_candidature,second_round
```

Si un candidat manque, ajoutez-le avec un identifiant/acronyme unique.

### 4. Créer le dossier du sondage

Créez un nouveau dossier dans `polls/` avec le format : `institut_AAAAMM/`

**Exemple :** `elabe_202501/` pour un sondage Elabe de janvier 2025

### 5. Créer les fichiers de données

Dans le dossier du sondage, créez les fichiers CSV nécessaires :

#### Fichier principal (obligatoire)
- `[institut]_[AAAAMM]_all.csv` : Résultats pour toute la population

#### Fichiers par segment (optionnels, selon les données disponibles)
- `[institut]_[AAAAMM]_left.csv` : Résultats pour l'électorat de gauche
- `[institut]_[AAAAMM]_macron.csv` : Résultats pour l'électorat macroniste
- `[institut]_[AAAAMM]_farright.csv` : Résultats pour l'électorat d'extrême droite
- `[institut]_[AAAAMM]_absentionists.csv` : Résultats pour les abstentionnistes

#### Structure des fichiers CSV de données
```csv
candidate_id,intention_mention_1,intention_mention_2,intention_mention_3,intention_mention_4,intention_mention_5,intention_mention_6,intention_mention_7,poll_type_id,population
```

**Exemple pour un sondage IPSOS (6 mentions) :**
```csv
candidate_id,intention_mention_1,intention_mention_2,intention_mention_3,intention_mention_4,intention_mention_5,intention_mention_6,intention_mention_7,poll_type_id,population
EP,9,22,28,19,17,5,,pt1,all
JB,15,17,16,10,37,5,,pt1,all
MLP,15,17,18,10,35,5,,pt1,all
```

**Exemple pour un sondage ELABE (5 mentions) :**
```csv
candidate_id,intention_mention_1,intention_mention_2,intention_mention_3,intention_mention_4,intention_mention_5,intention_mention_6,intention_mention_7,poll_type_id,population
EP,10,34,21,20,15,,,pt2,all
JB,17,21,12,39,11,,,pt2,all
```

**Important :**
- Les valeurs sont des pourcentages/ou des votes (int)
- Laissez vides les colonnes mention non utilisées
- Utilisez l'ID du type de sondage correct (pt1, pt2, etc.)
- Indiquez la population concernée (all, left, macron, si inconnue mettre all)

### 6. Mettre à jour polls.csv

Ajoutez les métadonnées de votre sondage dans `polls.csv` :

```csv
poll_id,poll_type,nb_people,start_date,end_date,folder,population
```

**Exemple :**
```csv
elabe_202501,pt2,1001,2025-01-07,2025-01-08,polls/elabe_202501,all
elabe_202501,pt2,1001,2025-01-07,2025-01-08,polls/elabe_202501,left
elabe_202501,pt2,1001,2025-01-07,2025-01-08,polls/elabe_202501,macron
```

**Important :**
- Ajoutez une ligne par fichier de données créé
- Utilisez le format AAAA-MM-JJ pour les dates
- Le poll_id doit correspondre au nom du dossier
- Le poll_type doit correspondre à l'ID dans poll_types.csv

### 7. Exemple complet

Supposons que vous voulez ajouter un sondage Harris Interactive de février 2025 :

1. **Créer le dossier :** `polls/harris_202502/`

2. **Ajouter le type de sondage dans poll_types.csv :**
```csv
pt3,Harris Interactive,LCI,excellent,très bon,bon,moyen,mauvais,très mauvais,,6,"Comment jugez-vous chaque personnalité ?"
```

3. **Créer le fichier de données :** `polls/harris_202502/harris_202502_all.csv`
```csv
candidate_id,intention_mention_1,intention_mention_2,intention_mention_3,intention_mention_4,intention_mention_5,intention_mention_6,intention_mention_7,poll_type_id,population
EP,8,15,25,30,18,4,,pt3,all
JB,12,18,20,25,20,5,,pt3,all
```

4. **Ajouter dans polls.csv :**
```csv
harris_202502,pt3,1200,2025-02-15,2025-02-17,polls/harris_202502,all
```

### 8. Validation (Facultatif)

Après avoir ajouté votre sondage :

1. Vérifiez que tous les fichiers sont bien créés
2. Vérifiez la cohérence des identifiants entre les fichiers
3. Assurez-vous que les pourcentages sont cohérents
4. Testez le script `merge.py` pour vous assurer qu'il fonctionne correctement

### 9. Vous pouvez ouvrir une Pull Request (PR)
Votre travail est prêt à être ajouté au dépôt principal et autres sondages.
On travaillera avec un fork (copie personnelle en ligne du repository)
La CI (Github Action) se chargera d'executer 8 quand vous ajouterez un sondage.

### 10. Bonnes pratiques

- **Nommage cohérent :** Respectez le format `institut_AAAAMM`
- **Données complètes :** N'ajoutez que des candidats avec des données réelles
- **Vérification :** Double-vérifiez les pourcentages et les totaux
- **Documentation :** Ajoutez des commentaires si nécessaire sur les spécificités du sondage

### 11. Ressources

- `candidates.csv` : Liste des candidats référencés
- `poll_types.csv` : Types de sondages supportés
- `polls.csv` : Index de tous les sondages
- `merge.py` : Script pour fusionner les données

## Questions fréquentes

**Q : Que faire si un candidat n'est pas dans la liste ?**
R : Ajoutez-le dans `candidates.csv` avec un identifiant unique.

**Q : Comment gérer les sondages avec des échelles différentes ?**
R : Créez un nouveau type de sondage dans `poll_types.csv`.

**Q : Puis-je ajouter des segments de population personnalisés ?**
R : Oui, mais assurez-vous de les documenter et de mettre à jour `polls.csv` en conséquence.

**Q : Comment gérer les candidats absents d'un sondage ?**
R : Ne les incluez tout simplement pas dans le fichier CSV du sondage.
