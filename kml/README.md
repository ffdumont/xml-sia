# Module KML - Génération d'exports KML

Ce module contient les outils pour générer des fichiers KML à partir des espaces aériens XML-SIA.

## Fichiers

- `extractor.py` : Extracteur KML principal avec support 3D
- `color_service.py` : Service d'attribution des couleurs selon les standards OACI

## Usage

```python
from kml.extractor import KMLExtractor
from kml.color_service import get_space_color

# Extraction KML
extractor = KMLExtractor("database/sia_database.db")
extractor.extract_airspace_kml("[LF][TMA LE BOURGET]", "output.kml")

# Service de couleurs
color = get_space_color("TMA", "D")  # Retourne la couleur bleu foncé
```

## Standards OACI respectés

- Classe A : Rouge
- Classes B, C, D : Bleu foncé  
- Classe E : Bleu clair
- Zones spéciales (P, D, R) : Rouge
- Espaces d'information : Bleu clair