# Outils XML-SIA

Ce dossier contient les outils d'extraction et de validation pour les données XML-SIA v6.0.

## Scripts disponibles

### `extract_espace.py`
**Outil d'extraction d'espaces aériens avec résolution de dépendances**

```bash
python extract_espace.py --input ../data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]" --verbose
```

**Fonctionnalités** :
- Extraction par identifiant `lk` ou `pk`
- Résolution automatique des dépendances (Territoire, Ad, Partie, Volume, Service, Frequence)
- Validation XSD automatique
- Formatage XML optimisé
- Mode verbose pour diagnostic

### `check_coherence.py`
**Outil de validation de cohérence XSD vs Spécification SIA**

```bash
python check_coherence.py
```

**Fonctionnalités** :
- Comparaison automatique XSD vs documentation SIA officielle
- Analyse des relations `relation(EntityName)`
- Validation des types et cardinalités
- Rapport détaillé de conformité
- Détection des incohérences

## Dépendances

- Python 3.7+
- Modules standard : `xml.etree.ElementTree`, `xml.dom.minidom`, `argparse`, `re`

## Utilisation

Les scripts sont conçus pour être exécutés depuis la racine du projet :

```bash
# Extraction
python tools/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]"

# Validation
python tools/check_coherence.py
```

## Sortie

- **Extraction** : Fichiers XML dans `data-output/`
- **Validation** : Rapports dans `docs/`