# Compatibilité des formats PDF ELABE

## 🎯 Version actuelle supportée

Le système `mining_ELABE` est **optimisé pour le format récent** (octobre-novembre 2025) :
- ✅ **elabe_202510** (octobre 2025) : 30 candidats × 5 populations = 150 lignes
- ✅ **elabe_202511** (novembre 2025) : 30 candidats × 5 populations = 150 lignes

### Caractéristiques du format récent
- Pages de données : **13-17** ou **17-21**
- Nombre de scores par candidat : **5** (très positive, plutôt positive, plutôt négative, très négative, sans opinion)
- Nombre de candidats par page : **30**
- Total : **150 candidats** extraits

## ⚠️ Formats plus anciens (partiellement supportés)

### elabe_202509 (septembre 2025)
**Statut** : ⚠️ **Extraction partielle** - Format différent

- Pages de données : 16-20
- Candidats extraits : **49 au lieu de ~150**
- Anomalies : **25 détectées**
- Problème : Seulement **4 scores** extraits au lieu de 5

#### Résultats d'extraction

| Population      | Candidats | Anomalies | Attendu |
|-----------------|-----------|-----------|---------|
| all             | 7         | 6         | ~30     |
| left            | 14        | 8         | ~30     |
| macron          | 12        | 4         | ~30     |
| farright        | 11        | 5         | ~30     |
| absentionists   | 5         | 2         | ~30     |
| **TOTAL**       | **49**    | **25**    | **~150**|

#### Diagnostic
```bash
$ python elabe_build.py ../../polls/elabe_202509/source.pdf 202509
✅ 5 fichiers CSV générés
⚠️  Mais seulement 49 candidats extraits (au lieu de ~150)
⚠️  25 anomalies de scores manquants
```

**Cause** : Structure de tableau PDF différente
- Le système ne détecte que **7 candidats** sur la page "all" au lieu de 30
- Seulement **4 scores** extraits au lieu de 5

### Autres PDFs plus anciens

Non testés pour le moment :
- elabe_202408 (août 2025)
- elabe_202410 (avril 2025)
- elabe_202411 (avril 2025)
- elabe_202506 (juin 2025)
- elabe_202507 (juillet 2025)

## 📋 Recommandations

### Pour les PDFs récents (oct-nov 2025 et futurs)
✅ **Utiliser directement** :
```bash
python elabe_build.py <pdf_path> <date>
```

### Pour les PDFs plus anciens (avant octobre 2025)
⚠️ **Deux options** :

#### Option 1 : Utiliser quand même (avec corrections manuelles)
```bash
# Extraire ce qui est possible
python elabe_build.py ../../polls/elabe_202509/source.pdf 202509

# Examiner les anomalies
cat ../../polls/elabe_202509/mining_anomalie_*.txt

# Compléter manuellement les candidats manquants
```

**Avantages** :
- Rapide pour les candidats détectés
- Export automatique des anomalies

**Inconvénients** :
- Extraction incomplète (49/150 candidats)
- Nécessite beaucoup de corrections manuelles

#### Option 2 : Adapter le code (développement nécessaire)
Créer un adaptateur spécifique pour les anciens formats :
```python
# mining_ELABE/adapters/elabe_202509_adapter.py
class Elabe202509Adapter(ElabeMiner):
    """Adaptateur pour le format septembre 2025."""
    # Logique spécifique pour extraire 30 candidats
    # avec la structure de tableau différente
```

**Avantages** :
- Extraction complète automatique
- Pas de corrections manuelles

**Inconvénients** :
- Développement nécessaire (~4-8h)
- Maintenance d'adaptateurs multiples

## 🔄 Stratégie recommandée

### Approche pragmatique

1. **Focus sur le présent et le futur**
   - Le système actuel fonctionne parfaitement pour les PDFs récents
   - Optimiser pour octobre 2025+ (format stable)

2. **PDFs anciens : Au cas par cas**
   - Si besoin ponctuel → Extraction partielle + corrections manuelles
   - Si besoin récurrent → Développer adaptateur spécifique

3. **Versioning**
   ```
   mining_ELABE/
   ├── Core (format actuel, oct-nov 2025+)
   └── adapters/ (formats anciens, si besoin)
       ├── elabe_202509_adapter.py
       └── elabe_202408_adapter.py
   ```

## 💡 Pour toi (développeur futur)

> **Principe** : "Don't fix what ain't broken"

- ✅ **Le système actuel fonctionne bien** pour les PDFs récents
- ✅ **Garde cette version** comme référence principale
- ✅ **Upgrade pour les futurs formats** (2026+)
- ⚠️ **Adaptateurs pour anciens** seulement si vraiment nécessaire

### Si tu dois traiter elabe_202509
1. Utilise l'extraction actuelle pour avoir une base (49 candidats)
2. Examine les anomalies exportées
3. Complète manuellement les 101 candidats manquants
4. Ou investis 4-8h pour créer un adaptateur spécifique

### Si ELABE change le format en 2026
1. Teste avec `python elabe_build.py <nouveau_pdf> <date>`
2. Si anomalies massives → Format a changé
3. Utilise `dev/elabe_analyzer.py` pour comprendre le nouveau format
4. Adapte `elabe_miner.py` pour le nouveau format
5. **Conserve cette version** dans une branche git pour référence

## 🔍 Debug d'un nouveau PDF

```bash
# 1. Tester l'extraction
python elabe_build.py <pdf_path> <date>

# 2. Si problème, analyser le PDF
python dev/elabe_analyzer.py <pdf_path> --page <page_num>

# 3. Comparer avec un PDF qui fonctionne
python dev/elabe_analyzer.py ../../polls/elabe_202510/source.pdf --page 13

# 4. Identifier les différences de structure
# 5. Adapter elabe_miner.py si nécessaire
```

---

**Dernière mise à jour** : 11 novembre 2025  
**Versions testées** :
- ✅ elabe_202510 (octobre 2025) - Parfait
- ✅ elabe_202511 (novembre 2025) - Parfait
- ⚠️ elabe_202509 (septembre 2025) - Partiel (49/150 candidats)
