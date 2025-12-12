# ⚙️ Module de configuration du logging

Ce module fournit une configuration centralisée et personnalisable du système de **logging** Python, incluant une gestion des **niveaux de log via une énumération (`Enum`)**, des **couleurs en console**, et des formateurs cohérents pour tout type d’application (scripts, API, pipelines de données, etc.).

## 📁 Structure recommandée

```
MJ_DATABASE-2027/
│
├── utils/
│   ├── logger.py     
│   └── __init__.py
│
├── main.py
└── requirements.txt
```

## 🧩 Contenu du module

1. LogLevel (Enum)

Définit les niveaux standards de log comme une énumération typée :

```Python
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
```

Ce qui permet de référencer les niveaux de manière sûre et cohérente dans ton code :

```Python
LOG_LEVEL = LogLevel.INFO
```

Pour afficher plus de détails dans la console (voir logs debug), il est nécessaire de définir le niveau de journalisation sur DEBUG en `logger.py`

```Python
LOG_LEVEL = LogLevel.DEBUG
```






2. Configurer le journal 

Initialise le système de logging à l’aide de `setup_logging()` et  `dictConfig`.

Inclut :
- Un formateur standard (standard)
- Un formateur coloré (colorlog.ColoredFormatter)
- Un handler de console
- Un logger principal (app)

Exemple d’utilisation

```Python
import logging
from utils.logger import setup_logging

setup_logging()
logger = logging.getLogger("app")

logger.info("Application démarrée 🚀")
logger.warning("Attention : ceci est un avertissement")
logger.error("Une erreur est survenue")
```
Sortie attendue - mode `LOG_LEVEL = LogLevel.INFO` (avec couleurs en console) :

```Bash
[INFO]: Application démarrée 🚀
[WARNING]: Attention : ceci est un avertissement
[ERROR]: Une erreur est survenue
```

Sortie attendue - mode `LOG_LEVEL = LogLevel.DEBUG` (avec couleurs en console) :

```Bash
[INFO] (main): Application démarrée 🚀
[WARNING] (main): Attention : ceci est un avertissement
[ERROR] (main): Une erreur est survenue
```

🚀 Exemple d’intégration dans `main.py`

```Python
import logging
from utils.logger import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger("app")
    logger.info("Démarrage de l’application principale...")

if __name__ == "__main__":
    main()
```

## 🧰 Dépendances

Ce module utilise la bibliothèque `logging` et `colorlog` pour colorer les messages dans la console.

```Bash
logging==0.4.9.6
colorlog==6.10.1
```

## 🔧 exemples de logging

```Python
logger.info("╔═══════════════════════════════════════════════════════════════════════════╗")
logger.info("║ 🚀  Début du processus d’extraction du sondage Cluster 17                 ║")
logger.info("╚═══════════════════════════════════════════════════════════════════════════╝")
logger.info(f"📄 PDF         : {args.file}")
logger.info(f"📅 Date        : {args.date[:4]}-{args.date[4:]}")
if args.population:
    logger.info(f"🧠 Population  : Une seule population à extraire << {args.population.label} >>")
else:
    logger.info("🧠 Population  : Toutes les population à extraire")
logger.info(f"📂 Sortie      : {OUTPUT_DIR}")
logger.info(f"👥 Candidats   : {CANDIDATES_CSV}")
logger.info("")
```
Sortie attendue - mode `LOG_LEVEL = LogLevel.INFO` (avec couleurs en console) :

```Bash
[INFO]: ╔═══════════════════════════════════════════════════════════════════════════╗
[INFO]: ║ 🚀  Début du processus d’extraction du sondage Cluster 17                 ║
[INFO]: ╚═══════════════════════════════════════════════════════════════════════════╝
[INFO]: 📄 PDF         : polls/cluster17_202510/source.pdf
[INFO]: 📅 Date        : 2025-11
[INFO]: 🧠 Population  : Toutes les population à extraire
[INFO]: 📂 Sortie      : polls/cluster17_202510
[INFO]: 👥 Candidats   : /home/samir/workspace/miexuvoter/mj-database-2027/candidates.csv
```

Sortie attendue - mode `LOG_LEVEL = LogLevel.DEBUG` (avec couleurs en console) :

```Bash
[INFO] (cluster17_build): ╔═══════════════════════════════════════════════════════════════════════════╗
[INFO] (cluster17_build): ║ 🚀  Début du processus d’extraction du sondage Cluster 17                 ║
[INFO] (cluster17_build): ╚═══════════════════════════════════════════════════════════════════════════╝
[INFO] (cluster17_build): 📄 PDF         : polls/cluster17_202510/source.pdf
[INFO] (cluster17_build): 📅 Date        : 2025-11
[INFO] (cluster17_build): 🧠 Population  : Toutes les population à extraire
[INFO] (cluster17_build): 📂 Sortie      : polls/cluster17_202510
[INFO] (cluster17_build): 👥 Candidats   : /home/samir/workspace/miexuvoter/mj-database-2027/candidates.csv
```