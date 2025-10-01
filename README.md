# XML SIA Analyzer

Analyseur XML SIA (Service d'Information Aéronautique) - Outil d'inventaire et d'analyse des données aéronautiques françaises.

## Description

Ce projet fournit des services Python pour analyser les fichiers XML SIA export, inventorier les entités présentes et générer des rapports détaillés sur la structure des données aéronautiques.

## Fonctionnalités

### Service d'Inventaire (`inventory/sia_entity_inventory.py`)
- **Inventaire complet** des types d'entités XML SIA
- **Classification intelligente** des attributs d'entités 
- **Analyse de couverture** par rapport à la documentation SIA v6.0
- **Formats de sortie multiples** :
  - Texte : Rapport condensé pour consultation rapide
  - JSON : Données structurées pour réutilisation programmatique  
  - HTML : Interface interactive avec navigation

### Capacités d'Analyse
- Traitement progressif de gros fichiers XML (630K+ lignes)
- Détection hiérarchique des relations entité-attribut
- Mapping avec la documentation officielle SIA v6.0
- Statistiques de couverture et conformité

## Installation

```bash
# Cloner le repository
git clone <repository-url>
cd xml-sia

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Installer les dépendances (aucune dépendance externe requise)
# Le projet utilise uniquement des modules Python standard
```

## Utilisation

### Service d'Inventaire

```bash
# Rapport texte standard (par défaut)
python inventory/sia_entity_inventory.py

# Rapport JSON détaillé pour réutilisation
python inventory/sia_entity_inventory.py --json

# Rapport HTML interactif
python inventory/sia_entity_inventory.py --html

# Les deux formats détaillés
python inventory/sia_entity_inventory.py --json --html
```

### Structure des Données

Les rapports analysent :
- **23 types d'entités** documentées SIA v6.0 (95.8% de couverture)
- **299 attributs** classifiés automatiquement
- **25 conteneurs** d'entités structurant les données
- Statistiques de conformité et classification

## Structure du Projet

```
xml-sia/
├── inventory/              # Services d'analyse
│   └── sia_entity_inventory.py
├── input/                  # Données d'entrée
│   ├── *.xml              # Fichiers XML SIA (ignorés par Git)
│   ├── *.md               # Documentation SIA
│   └── *.pdf              # Documentation SIA
├── output/                 # Rapports générés
│   └── inventory/         # Rapports d'inventaire
└── README.md              # Cette documentation
```

## Documentation Technique

### Entités SIA Supportées

Le service reconnaît et analyse toutes les entités de la spécification SIA v6.0 :
- Aérodromes (Ad), Pistes (Rwy), Hélistations
- Espaces aériens (Espace), Volumes, Parties
- Routes aériennes, Segments, Points d'appui (NavFix)
- Obstacles, Phares, Aides radio (RadioNav)
- Services de communication, Fréquences
- Et bien d'autres...

### Formats de Sortie

- **Texte** : Synthèse condensée avec statistiques principales
- **JSON** : Structure complète avec métadonnées, entités détaillées, attributs exhaustifs
- **HTML** : Interface web avec navigation, sections collapsibles, design responsive

## Contribution

Ce projet analyse les données aéronautiques officielles françaises selon la spécification SIA v6.0.

## Licence

Projet d'analyse de données publiques aéronautiques françaises.