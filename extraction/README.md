# Module Extraction - Traitement des données XML-SIA

Ce module contient les outils pour extraire et traiter les données depuis les fichiers XML-SIA.

## Fichiers

- `extract_espace.py` : Extraction d'espaces aériens spécifiques depuis les fichiers XML
- `search_entities.py` : Recherche et filtrage d'entités dans les données XML

## Usage

```python
from extraction.extract_espace import extract_airspace
from extraction.search_entities import search_spaces

# Extraction d'un espace spécifique
extract_airspace("XML_SIA_2025-10-02.xml", "[LF][TMA LE BOURGET]")

# Recherche d'entités
results = search_spaces("TMA", class_filter="D")
```

## Fonctionnalités

- Extraction d'espaces aériens individuels
- Préservation de la structure XML complète
- Recherche avancée avec filtres
- Support des géométries complexes