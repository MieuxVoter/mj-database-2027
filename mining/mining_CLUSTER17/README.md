# Mining CLUSTER 17 (############# À FAIRE #############)

Extraction automatique des données de sondage CLUSTER !/ depuis les PDFs sources.

## 🎯 Fonctionnalités

- ✅ **Détection automatique des pages** : Identifie automatiquement les pages contenant les données
- ✅ **Extraction robuste** : Extrait 30 candidats par page avec leurs 5 scores d'opinion
- ✅ **Support multi-format** : Gère les PDFs avec pages 13-17 ou 17-21
- ✅ **Détection d'anomalies** : Identifie les scores manquants ou incorrects
- ✅ **Export des anomalies** : Génère des rapports détaillés pour correction manuelle
- ✅ **Validation automatique** : Utilise `candidates.csv` pour identifier les candidats

## 📁 Structure

```
mining_ELABE/
├── __init__.py              # Point d'entrée du module
├── elabe_build.py          # 🎯 CLI principal (utiliser celui-ci !)
├── elabe_miner.py          # Classe principale d'extraction
├── elabe_builder.py        # Construction des CSV
├── page_detector.py        # Détection automatique des pages
├── elabe_poll.py           # Structure de données ElabeLine
├── anomaly_detector.py     # Détection et export des anomalies
├── tests/                  # Tests unitaires
├── dev/                    # Scripts de développement/debug
└── old_fashion_way/        # Ancien workflow manuel (déprécié)
```

## 🚀 Usage rapide

### CLI (recommandé)

```bash
# Extraire toutes les populations d'un PDF
python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 

# Extraire une seule population
python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 --population left

python -m mining.mining_CLUSTER17.cluster17_build  polls/cluster17_202510/source.pdf 202511 ---overwrite
```