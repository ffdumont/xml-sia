# Core - Programmes principaux de production

Ce répertoire contient les programmes principaux de production pour le traitement des données XML-SIA.

## 📋 Programmes disponibles

### `extract_espace.py` - Extraction XSD d'espaces aériens
Extrait un espace aérien spécifique du fichier XML-SIA avec toutes ses dépendances.

**Usage :**
```bash
python core/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]" --verbose
```

**Fonctionnalités :**
- Extraction ciblée par identifiant `lk` ou `pk`
- Résolution automatique de toutes les dépendances
- Validation XSD intégrée
- Support TMA, CTR, espaces complexes

### `kml_extractor.py` - Génération KML 3D des volumes aériens  
Génère des fichiers KML 3D représentant les volumes d'espaces aériens avec plancher, plafond et parois verticales.

**Usage :**
```bash
python core/kml_extractor.py --lk "[LF][TMA LE BOURGET]"
```

**Fonctionnalités :**
- Volumes 3D complets (plancher + plafond + parois)
- Conversion d'altitudes : FL, ft AMSL, ft ASFC, SFC, UNL
- Normalisation des noms de fichiers selon clé `lk`
- Couleur uniforme : bleu avec 25% d'opacité

### `search_entities.py` - Service de recherche d'entités
Recherche d'entités par mots-clés dans les attributs `lk` sur XML-SIA ou base SQLite.

**Usage :**
```bash
python core/search_entities.py --type espace --keyword "TMA"
python core/search_entities.py --source xml --keyword "BOURGET"
```

**Fonctionnalités :**
- Recherche par mots-clés dans les attributs `lk`
- Support multi-sources : XML-SIA et base SQLite
- 7 types d'entités supportés
- Performance optimisée

## 🎯 Utilisation recommandée

1. **Recherche** : Utiliser `search_entities.py` pour trouver les clés `lk` des espaces
2. **Extraction** : Utiliser `extract_espace.py` pour extraire les données XML
3. **Visualisation** : Utiliser `kml_extractor.py` pour générer les volumes 3D

## 📁 Sorties

- **Extractions XML** : `data-output/`
- **Volumes KML** : `data-output/kml/`
- **Rapports** : stdout avec niveau de verbosité configurable