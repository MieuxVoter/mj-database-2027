# 🧩 BasePipeline — Module de base pour pipelines d’extraction depuis PDF

## 📘 Présentation

`base_pipeline.py` définit la classe abstraite **`BasePipeline`**, qui constitue le **socle commun** de tous les pipelines d’extraction et de construction de données du projet **Cluster17 Mining**.  

Cette classe établit un **modèle d’orchestration générique**, garantissant :
- la validation des paramètres d’entrée,  
- le nettoyage automatique des anciens fichiers,  
- la gestion uniforme du cycle d’extraction et de construction,  
- la journalisation détaillée des opérations.

Elle implémente le **pattern “Template Method”**, où la structure du flux est fixée mais les étapes concrètes (`extract`, `build`) sont définies par les sous-classes.

---

## ⚙️ Objectif

`BasePipeline` fournit un cadre robuste et extensible permettant :

- d’exécuter un pipeline complet sans répéter la logique d’orchestration ;
- de garantir la cohérence des logs et la gestion des erreurs ;
- de simplifier la création de pipelines spécifiques (ex. `Cluster17Pipeline`).

---

## 🧠 Structure de la classe

```python
class BasePipeline(ABC):
    def __init__(self, pdf_path: Path, poll_id: str):
        ...
    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        ...
    @abstractmethod
    def build(self, extracted_data) -> int:
        ...
    def run(self):
        ...
````

---

## 🔁 Cycle d’exécution

| Étape | Description                                   | Méthode correspondante      |
| ----- | --------------------------------------------- | --------------------------- |
| 1     | Validation du fichier PDF et de l’identifiant | `_validate_inputs()`        |
| 2     | Suppression des anciens fichiers CSV/TXT      | `_cleanup_existing_files()` |
| 3     | Extraction des données brutes                 | `extract()` *(abstraite)*   |
| 4     | Construction des artefacts finaux             | `build()` *(abstraite)*     |
| 5     | Journalisation du résultat global             | `run()`                     |

---

## 🧩 Utilisation

### 1. Créer une sous-classe

```python
from pathlib import Path
from mining.base_pipeline import BasePipeline

class MyPipeline(BasePipeline):
    def extract(self):
        print("Extraction en cours...")
        return [{"df": "mock_dataframe"}]

    def build(self, extracted_data):
        print(f"Construction terminée ({len(extracted_data)} tables traitées)")
        return len(extracted_data)
```

---

### 2. Exécuter le pipeline

```python
if __name__ == "__main__":
    pdf_file = Path("data/cluster17_202511.pdf")
    pipeline = MyPipeline(pdf_file, poll_id="cluster17_202511")
    pipeline.run()
```

**Sortie attendue :**

```
🧹 Nettoyage des anciens fichiers avant traitement...
🔍  Détection et extraction des pages de données...
📦  Extraction et construction des CSV...
✅  1 fichier(s) CSV généré(s)
```

---

## 🧾 Détails des méthodes

### `__init__(self, pdf_path, poll_id)`

Initialise le pipeline et valide les entrées :

* `pdf_path` : chemin vers le fichier source (PDF, API, etc.)
* `poll_id` : identifiant du sondage (ex. `"cluster17_202511"`)

---

### `_validate_inputs()`

Vérifie :

* que `pdf_path` est un `Path` existant,
* que `poll_id` est une chaîne valide.
  Lève `TypeError` ou `FileNotFoundError` en cas d’erreur.

---

### `_cleanup_existing_files(extensions=("csv", "txt"))`

Supprime les anciens fichiers `.csv` et `.txt` dans le répertoire du PDF avant un nouveau traitement.
Les fichiers inaccessibles sont ignorés mais journalisés.

---

### `extract()`

Méthode **abstraite** à implémenter dans les sous-classes.
Doit renvoyer une **liste de dictionnaires** décrivant les tableaux extraits, par exemple :

```python
[
  {"Page": 1, "Population": "Générale", "df": <DataFrame>},
  {"Page": 2, "Population": "Jeunes", "df": <DataFrame>}
]
```

---

### `build(extracted_data)`

Méthode **abstraite** chargée de construire les fichiers finaux (CSV, TXT, etc.).
Retourne le **nombre de fichiers créés**.

---

### `run()`

Méthode principale orchestrant le processus complet :

1. Nettoyage des anciens fichiers
2. Extraction des données
3. Construction des artefacts
4. Journalisation du résultat

---

## 🧩 Exemple concret — `Cluster17Pipeline`

Implémentation pratique dans `mining_CLUSTER17/orchestrator.py` :

```python
class Cluster17Pipeline(BasePipeline):
    def extract(self):
        extractor = PDFExtractor(self.pdf_path)
        return extractor.extract_all()

    def build(self, extracted_data):
        builder = CSVBuilder(self.pdf_path.parent, self.poll_id)
        return builder.build_all(extracted_data)
```

---

## 🪵 Journalisation

Le module utilise `logging` pour tracer chaque étape :

```
INFO  [BasePipeline] 🧹 Nettoyage des anciens fichiers avant traitement...
INFO  [BasePipeline] 📦  Extraction et construction des CSV...
ERROR [BasePipeline] Erreur inattendue dans le pipeline : <message>
```

---

## 🧱 Points techniques clés

| Élément           | Description                                    |
| ----------------- | ---------------------------------------------- |
| **Pattern**       | Template Method Pattern                        |
| **Type**          | Classe abstraite (`ABC`)                       |
| **Objectif**      | Standardiser l’exécution des pipelines         |
| **Validation**    | Vérification stricte des entrées               |
| **Extensibilité** | Compatible avec tout pipeline (PDF, API, etc.) |
| **Logs**          | Gestion complète via le module `logging`       |

---
