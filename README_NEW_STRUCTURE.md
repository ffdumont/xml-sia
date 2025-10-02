# XML-SIA - Nouvelle Structure Organisée

Projet de traitement et visualisation des espaces aériens XML-SIA avec structure modulaire optimisée.

## 📁 Structure du Projet

```
xml-sia/
├── config/                    # Configuration (couleurs OACI, paramètres)
│   └── color_rules.csv       # Règles de couleurs selon standards OACI
├── data-input/               # Données d'entrée
│   ├── XML_SIA_2025-10-02.xml
│   └── schemas/              # Schémas XSD
├── data-output/              # Données de sortie
│   ├── kml/                  # Fichiers KML générés
│   └── inventory/            # Rapports d'inventaire
├── database/                 # Base de données SQLite
│   └── sia_database.db
├── kml/                      # 🆕 Module de génération KML
│   ├── __init__.py
│   ├── extractor.py          # Extracteur KML principal (ex: kml_extractor.py)
│   ├── color_service.py      # Service de sélection des couleurs OACI
│   └── README.md
├── extraction/               # 🆕 Module d'extraction XML
│   ├── __init__.py
│   ├── extract_espace.py     # Extraction d'espaces aériens
│   ├── search_entities.py    # Recherche d'entités
│   └── README.md
├── validation/               # 🆕 Module de validation
│   ├── __init__.py
│   ├── check_coherence.py    # Contrôle de cohérence
│   └── README.md
├── tests/                    # 🆕 Tests (réservé pour futurs tests)
│   └── __init__.py
├── utils/                    # Utilitaires généraux
├── tools/                    # Scripts utilitaires (allégé)
├── schemas/                  # Scripts de schémas (allégé)
└── generate_kml.py           # 🆕 Script principal de génération KML
```

## 🚀 Usage Principal

### Génération KML avec service de couleurs OACI

```bash
# Génération d'un espace spécifique
python generate_kml.py --espace-lk "[LF][TMA LE BOURGET]" --output bourget.kml

# Liste des espaces disponibles
python generate_kml.py --list-spaces

# Génération par identifiant numérique
python generate_kml.py --espace-pk 304333 --output espace.kml
```

### Utilisation des modules

```python
# Module KML - Génération avec couleurs OACI
from kml.extractor import KMLExtractor
from kml.color_service import get_space_color

extractor = KMLExtractor("database/sia_database.db")
color = get_space_color("TMA", "D")  # Retourne bleu foncé selon OACI

# Module extraction
from extraction.extract_espace import extract_airspace
from extraction.search_entities import search_spaces

# Module validation  
from validation.check_coherence import validate_xml_data
```

## 🎨 Service de Couleurs OACI

Le service de couleurs applique automatiquement les standards OACI :

- **Classe A** : Rouge (`#FF0000`)
- **Classes B, C, D** : Bleu foncé (`#0066CC`) 
- **Classe E** : Bleu clair (`#6699FF`)
- **Zones spéciales** (P, D, R, ZIT, ZRT) : Rouge
- **Espaces d'information** (FIR, UIR) : Bleu clair
- **Activités de loisirs** : Orange (`#FF9900`)

Configuration dans `config/color_rules.csv` avec encodage Latin-1.

## 🔧 Améliorations Apportées

✅ **Structure modulaire claire** : Séparation fonctionnelle en modules  
✅ **Élimination des doublons** : Fini les fichiers dupliqués  
✅ **Service de couleurs OACI** : Couleurs automatiques selon les standards  
✅ **Imports simplifiés** : Structure de modules Python propre  
✅ **Documentation intégrée** : README dans chaque module  
✅ **Script principal unifié** : `generate_kml.py` pour l'usage courant  

## 📋 Migration depuis l'ancienne structure

- `core/kml_extractor.py` → `kml/extractor.py`
- `core/color_service.py` → `kml/color_service.py`  
- `core/search_entities.py` → `extraction/search_entities.py`
- `tools/extract_espace.py` → `extraction/extract_espace.py` (version consolidée)
- `tools/check_coherence.py` → `validation/check_coherence.py` (version consolidée)

Les anciens scripts fonctionnent avec les nouveaux imports :
```python
# Ancien : from core.kml_extractor import KMLExtractor
# Nouveau : from kml.extractor import KMLExtractor
```