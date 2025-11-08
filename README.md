# Base de données des sondages - Élection présidentielle 2027 

## À propos

Ce dépôt contient une base de données structurée des sondages d'opinion pour l'élection présidentielle française de 2027. Les données sont organisées pour appliquer le **Jugement Majoritaire**, permettant une analyse approfondie de l'opinion publique sur les différents candidats et de prédire qui sortirait gagnant avec ce mode de départage.

## Objectifs

- 📊 **Centraliser les données** : Rassembler les sondages de différents instituts dans un format standardisé
- 🔍 **Faciliter l'analyse** : Permettre des comparaisons entre instituts, périodes et segments de population
- 📈 **Suivre l'évolution** : Tracker l'évolution de l'opinion publique au fil du temps
- 🎯 **Appliquer le Jugement Majoritaire** : Utiliser une méthodologie d'analyse plus riche que les intentions de vote classiques

## 📋 Ajouter un sondage

Ce guide [📋 Comment ajouter un sondage](./COMMENT_AJOUTER_UN_SONDAGE.md) vous explique étape par étape comment : Structurer vos données, Ajouter de nouveaux candidats ou instituts Respecter les conventions de nommage, Valider vos données.

## Structure des données

Le dépôt est organisé autour de quatre composants principaux :

- **`candidates.csv`** : Liste des candidats potentiels avec leurs informations
- **`poll_types.csv`** : Définition des différents types de sondages et leurs échelles
- **`polls.csv`** : Métadonnées de tous les sondages (dates, instituts, populations)
- **`polls/`** : Données détaillées de chaque sondage, organisées par institut et date

## Types de sondages supportés

- **IPSOS** : Échelle de satisfaction à 6 niveaux (très satisfait → très insatisfait)
- **ELABE** : Échelle d'image à 5 niveaux (très positive → très négative)
- **Autres instituts** : Extensible selon les besoins

## Segments de population

Les données sont disponibles pour différents segments :
- **Ensemble de la population** (`all`)
- **Électorat de gauche** (`left`)
- **Électorat macroniste** (`macron`)
- **Électorat d'extrême droite** (`farright`)
- **Abstentionnistes** (`absentionists`)

## Utilisation

```python
import pandas as pd

# Charger les métadonnées des sondages
polls = pd.read_csv('mj2027.csv')
```

## Note importante

Ce dépôt n'applique pas la règle du jugement majoritaire, mais répertorie les sondages compatibles, il peut servir à appliquer d'autres régles de départage comme le vote par approbation.

## Licence

Ce projet est sous licence [MIT](LICENSE.md).

## Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur ce dépôt.
