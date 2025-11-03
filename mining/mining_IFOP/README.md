# Scraper de Sondages IFOP

Ce scraper permet d'extraire les résultats de sondages IFOP depuis les PDF "tableau de bord des personnalités" publiés chaque mois, et de les enregistrer dans des fichiers CSV structurés.

## Dépendances

- pandas
- pdfminer.six

Installez-les avec :
```bash
pip install pandas pdfminer.six
```
## Arborescence fichiers
 ```
MJ-DATABASE-2027/
│
├── mining/
│   └── mining_IFOP/
│       ├── candidate.py
│       ├── manager.py
│       ├── miner.py
│       ├── builder.py
│       ├── poll.py
│       ├── ifop_build.py
│       └── pdfs/
│
├── tests/
│   └── test_poll_ifop.py
│
├── polls/
│
└── pyproject.toml
```

## Exécution

1. Déposez votre fichier PDF dans le dossier `mining_IFOP/pdfs/`.

2. Ouvrez un terminal et placez-vous dans le dossier `mining_IFOP`

3. utilisez la commande : 

```
python ifop_build.py "mining_IFOP/pdfs/[Nom du PDF].pdf" AAAAMM [options]
```

## Options disponibles

| Option                  | Description                                         |
|-------------------------|--------------------------------------------------   |
| `--pages` ou `-p`       | Pages à analyser (ex: `--pages 7 8`)                |
| `--overwrite` ou `-o`   | Écraser le fichier de sortie s'il existe            |
| `--candidates-path`     | Chemin vers le fichier des candidats                |
| `--poll-type` ou `-t`   | Type de sondage (défaut : `pt3`)                    |
| `--prefix` ou `-x`      | Préfixe pour le fichier de sortie (défaut : `ifop`) |
| `--population` ou `-P`  | Population cible (défaut : `all`)                   |

## Sortie
Les fichiers CSV seront générés dans :

```
polls/{préfixe}_{date_du_sondage}/{préfixe}_{date_du_sondage}_{population}.csv
```
