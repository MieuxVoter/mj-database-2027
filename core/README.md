# Documentation CORE
1. [Population](#population)
2. [Logging](#logging)

## Population

Ce module définit la classe `Population`, une énumération (`Enum`) représentant les **catégories de population ou électorats**
utilisées dans différentes **sondages (par exemple : *Cluster17*, *Elabe*).

Chaque population (candidat, groupe d’électeurs, etc.) peut appartenir à une ou plusieurs sondages.<br/>
La classe fournit des méthodes utilitaires pour récupérer les populations par enquête et inversement, pour savoir dans quelles enquêtes une population apparaît.

```Python

class Population(str, Enum):
    ALL = "all"
    LEFT = "left"
    MACRON = "macron"
    FARRIGHT = "farright"
    ABSTENTIONISTS = "absentionists"
    JLMELENCHON = "melenchon"
    MLPEN = "lepen"
    LFI = "lfi"
    ECOLOGISTES = "ecologistes"
    PSPP = "pspp"
    RENAISSANCE = "renaissance"
    LR = "lr"
    RN = "rn"
    RECONQUETE = "reconquete"

    # Définition des enquêtes par population/candidats
    __SURVEY_MAP__ = {
        "CLUSTER17": [
            "all", "macron", "lepen", "melenchon",
            "lfi", "ecologistes", "pspp", "renaissance",
            "lr", "rn", "reconquete"
        ],
        "ELABE": [
            "all", "macron", "left", "farright", "absentionists"
        ],
    }
```

### 🔧 Exemple d’utilisation

1️⃣ Lister les populations d’une sondage

```Python
from core.population import Population

POPULATION = Population.by_survey("CLUSTER17")
print([p.value for p in POPULATION])
```

Résultat :

```
['all', 'macron', 'lepen', 'melenchon', 'lfi', 'ecologistes',
 'pspp', 'renaissance', 'lr', 'rn', 'reconquete']
```

2️⃣ Savoir dans quelles enquêtes une population apparaît

```Python
Population.surveys_for(Population.MACRON)
```

Résultat :

```
['CLUSTER17', 'ELABE']
```

3️⃣ Afficher une étiquette lisible
Chaque membre possède une propriété label qui retourne une étiquette explicite :

```
print(Population.MACRON.label)
# → "Électeurs d'Emmanuel Macron"
```

4️⃣ Utilisation avec `argparse`

L’énumération est compatible avec argparse pour être utilisée comme choix de paramètre CLI :

```Python
import argparse
from core.population import Population

# Population de Cluster 17
POPULATION = Population.by_survey("CLUSTER17")

parser = argparse.ArgumentParser(description="Extraction des populations d’un sondage.")
parser.add_argument(
    "--population",
    type=Population,
    choices=list(Population),
    help="Population à extraire (si omise, extrait toutes les populations de l’enquête)"
)

args = parser.parse_args()

if args.population:
    print(f"Population sélectionnée : {args.population.label}")
else: 
    print(f"Population  :" {[p.value for p in POPULATION]})
```

Avec une population définie

```Bash
python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 --population lepen

# Résultat : 
Population sélectionnée : Électeurs de Marine Le Pen 2022
```

Sans population définie

```Bash
python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511

# Résultat : 
Population sélectionnée :  ['all', 'macron', 'melenchon', 'lepen', 'lfi', 'ecologistes', 'pspp', 'renaissance', 'lr', 'rn', 'reconquete']
```

### ➕ Ajouter une nouvelle population

1️⃣ Déclarer un nouveau membre dans l’énumération
(par exemple, un nouveau groupe d’électeurs) :

```Python
class Population(str, Enum):
    ...
    NOUVEAUXVERTS = "nouveauxverts"
```
2️⃣ L’ajouter aux enquêtes correspondantes dans `__SURVEY_MAP__` :

```Python
__SURVEY_MAP__ = {
    "CLUSTER17": [
        "all", "macron", "lepen", "melenchon",
        "lfi", "ecologistes", "pspp", "renaissance",
        "lr", "rn", "reconquete", "nouveauxverts"  # 👈 ajouté ici
    ],
    "ELABE": [
        "all", "macron", "left", "farright", "absentionists"
    ],
}
```
3️⃣ Ajouter son étiquette dans `label`

```Python
labels = {
    ...
    "nouveauxverts": "Électeurs des Nouveaux Verts",
}
```

### ➕ Ajouter une nouvelle sondage

1️⃣ Créer une nouvelle clé dans `__SURVEY_MAP__` :

```Python
__SURVEY_MAP__ = {
    "CLUSTER17": [...],
    "ELABE": [...],
    "IFOP": [  # 👈 Nouvelle enquête
        "all", "macron", "lepen", "melenchon"
    ]
}
```
La nouvelle enquête devient immédiatement fonctionnelle sans modifier la logique du reste du programme.

### Méthodes principales
| Méthode                       | Description                                                                        | Exemple                                     |
| ----------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------- |
| `Population.by_survey(name)`  | Retourne toutes les populations d’une enquête donnée (`"CLUSTER17"` ou `"ELABE"`). | `Population.by_survey("ELABE")`             |
| `Population.surveys_for(pop)` | Retourne la liste des enquêtes où la population donnée apparaît.                   | `Population.surveys_for(Population.MACRON)` |
| `Population.label`            | Retourne une étiquette lisible (ex. “Électeurs de LFI aux Européennes 2024”).      | `Population.LFI.label`                      |



### 🧾 Détail des sondages
| Enquête       | Populations                                                                            |
| ------------- | -------------------------------------------------------------------------------------- |
| **CLUSTER17** | all, macron, lepen, melenchon, lfi, ecologistes, pspp, renaissance, lr, rn, reconquete |
| **ELABE**     | all, macron, left, farright, absentionists                                             |

## Logging
[Voir la documentation](./settings/README.md)