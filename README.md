# XML-SIA : Extraction et validation d'espaces aériens

Outils d'extracti# 4. Générer KML 3D avec couleurs OACI
python generate_kml.py --espace-lk "[LF][TMA AVORD]" --database sia_database_avord.db --output data-output/kml/TMA_AVORD.kml et de validation pour les données XML-SIA (Système d'Information Aéronautique) version 6.0.

## 🎯 Objectif

Extraire des espaces aériens spécifiques du fichier XML-SIA officiel avec toutes leurs dépendances (territoires, aérodromes, parties, volumes, services, fréquences) et valider la cohérence avec les spécifications officielles.

## 📁 Structure

```
xml-sia/
├── generate_kml/                  # Module de génération KML avec couleurs OACI
│   ├── extractor.py              # Extraction KML 3D des volumes aériens
│   └── color_service.py          # Service de couleurs selon standards OACI
├── extraction/                    # Module d'extraction et recherche
│   ├── extract_espace.py         # Extraction XSD d'espaces avec dépendances
│   └── list_entities.py          # Service de listing et recherche d'entités
├── utils/                         # Utilitaires de base de données et validation
│   ├── check_db.py               # Vérification de la base de données
│   ├── schema_generator.py       # Génération de schémas
│   ├── verify_data.py            # Validation des données
│   ├── xml_importer.py           # Import XML vers SQLite
│   └── sia_entity_inventory.py   # Inventaire des entités SIA
├── schemas/                       # Schémas XSD et validation
│   ├── check_coherence.py        # Validation XSD vs spécification
│   └── extract_espace.py         # Legacy - utiliser extraction/extract_espace.py
├── tools/                         # Outils legacy
│   ├── check_coherence.py        # Legacy - utiliser validation/check_coherence.py
│   └── extract_espace.py         # Legacy - utiliser extraction/extract_espace.py
├── data-input/                    # Données sources SIA  
│   ├── schemas/                  # Schémas XSD (incluant Espace.xsd)
│   └── XML_SIA_2025-10-02.xml   # Fichier XML SIA principal
├── data-output/                   # Extractions générées
│   ├── kml/                      # Volumes KML 3D générés
│   ├── schemas/                  # Rapports de validation
│   └── inventory/                # Rapports d'inventaire
├── docs/                          # Documentation et spécifications
│   └── specifications/           # Spécifications SIA officielles
├── sia_database.db               # Base de données SQLite des entités SIA
└── README.md                      # Ce fichier
```

## 🚀 Utilisation rapide

### Extraction d'un espace aérien
```bash
# Extraire la TMA Le Bourget avec toutes ses dépendances
python extraction/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]" --verbose

# Extraire une CTR par pk
python extraction/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "1204" --verbose
```

### Génération KML 3D
```bash
# Générer un volume KML 3D pour un espace aérien
python generate_kml.py --espace-lk "[LF][TMA LE BOURGET]"

# Lister les espaces TMA disponibles
python extraction/list_entities.py --type espace --space-type TMA
```

### Workflow complet (recherche → extraction → base → KML)
```bash
# 1. Rechercher l'espace
python extraction/list_entities.py -k "AVORD" --source xml --xml-file data-input/XML_SIA_2025-10-02.xml

# 2. Extraire avec dépendances  
python extraction/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA AVORD]" --output data-output/TMA_AVORD.xml

# 3. Créer base dédiée
python utils/schema_generator.py --xsd data-input/schemas/Espace.xsd --database tma_avord.db
python utils/xml_importer.py --xml data-output/TMA_AVORD.xml --database tma_avord.db

# 4. Générer KML 3D avec couleurs OACI
python generate_kml/generate_kml.py --espace-lk "[LF][TMA AVORD]" --database tma_avord.db --output data-output/kml/TMA_AVORD.kml
```

### Validation de cohérence
```bash
# Vérifier la cohérence XSD vs spécification SIA
python validation/check_coherence.py
```

## 📊 Fonctionnalités principales

### 🎯 Extraction d'espaces aériens (`extraction/extract_espace.py`)
- **Extraction ciblée** par identifiant `lk` ou `pk`
- **Résolution automatique** de toutes les dépendances
- **Validation XSD** intégrée
- **Formatage XML** optimisé (réduction 57% des lignes vides)
- **Support complet** : TMA, CTR, espaces complexes

### 🗺️ Génération KML 3D (`generate_kml/generate_kml.py`)
- **Volumes 3D** avec plancher, plafond et parois verticales
- **Conversion d'altitudes** : FL, ft AMSL, ft ASFC, SFC, UNL
- **Normalisation des noms** de fichiers selon clé `lk`
- **Couleur uniforme** : bleu avec 25% d'opacité (KML: 40ff0000)

### 🔍 Recherche d'entités (`extraction/list_entities.py`)
- **Recherche par mots-clés** dans les attributs `lk`
- **Support multi-sources** : XML-SIA et base SQLite
- **7 types d'entités** : territoire, aerodrome, espace, partie, volume, service, frequence
- **Performance optimisée** : <1ms sur SQLite, ~583ms sur XML

### ✅ Validation de cohérence (`validation/check_coherence.py`)
- **Analyse des relations** `relation(EntityName)` selon spécification SIA
- **Validation XSD** contre documentation officielle
- **Détection automatique** des incohérences
- **Rapport détaillé** de conformité (21 entités analysées)

### 📋 Schéma XSD (`schemas/Espace.xsd`)
- **Conformité 100%** avec spécification SIA v6.0
- **Relations complètes** entre entités aéronautiques
- **Validation automatique** des extractions
- **Documentation intégrée** des relations CTR ↔ Aérodrome

## 🛠️ Installation

```bash
# Prérequis : Python 3.7+
git clone <repository-url>
cd xml-sia

# Aucune dépendance externe requise
# Modules standard : xml.etree.ElementTree, xml.dom.minidom, argparse
```

## 📖 Documentation détaillée

- **[Guide d'utilisation](docs/README_extract_espace.md)** : Instructions complètes d'extraction
- **[Rapport de cohérence](docs/COHERENCE_REPORT.md)** : Validation XSD vs spécification
- **[Analyse des relations](docs/RELATIONS_ANALYSIS_REPORT.md)** : Relations SIA détectées et validées

## 🎯 Exemples d'extraction

### Extraction XML : TMA Le Bourget (Espace complexe)
```bash
python extraction/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]"
```
**Résultat** : 11 entités extraites (Territoire, Ad, Espace, 2 Parties, 2 Volumes, 3 Services, 2 Fréquences)

### Génération KML : Volume 3D TMA Le Bourget
```bash
python generate_kml/generate_kml.py --espace-lk "[LF][TMA LE BOURGET]"
```
**Résultat** : Fichier `TMA_LE_BOURGET.kml` avec volume 3D complet

### Recherche : Espaces TMA disponibles
```bash
python extraction/list_entities.py --type espace --keyword "TMA"
```
**Résultat** : Liste des 943 espaces TMA avec leurs clés `lk`

## 🔄 Workflow complet end-to-end

### Exemple : Traitement complet de la TMA AVORD

Ce workflow montre comment traiter un espace aérien de A à Z, depuis la recherche jusqu'à la visualisation KML 3D.

#### Étape 1 : 🔍 Recherche de l'espace
```bash
# Rechercher "AVORD" dans le XML-SIA pour trouver la clé lk
python extraction/list_entities.py -k "AVORD" --source xml --xml-file data-input/XML_SIA_2025-10-02.xml
```
**Résultat** : `[LF][TMA AVORD]` (PK: 301113) + `[LF][CTR AVORD]` (PK: 4393)

#### Étape 2 : 📁 Extraction XML avec dépendances
```bash
# Extraire la TMA AVORD avec toutes ses dépendances
python extraction/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA AVORD]" --output data-output/TMA_AVORD_extracted.xml --verbose
```
**Résultat** : 51 entités extraites (1 territoire, 1 aérodrome, 1 espace, 3 parties, 3 volumes, 6 services, 36 fréquences)

#### Étape 3 : 💾 Création de base de données dédiée
```bash
# Créer le schéma SQLite
python utils/schema_generator.py --xsd data-input/schemas/Espace.xsd --database sia_database_avord.db --verbose

# Importer les données extraites
python utils/xml_importer.py --xml data-output/TMA_AVORD_extracted.xml --database sia_database_avord.db --verbose
```
**Résultat** : Base SQLite `sia_database_avord.db` avec 51 enregistrements

#### Étape 4 : 🗺️ Génération du volume KML 3D
```bash
# Générer le KML 3D de la TMA AVORD
python generate_kml/extractor.py --espace-lk "[LF][TMA AVORD]" --database sia_database_avord.db --output data-output/kml/TMA_AVORD.kml
```
**Résultat** : Fichier `TMA_AVORD.kml` avec volume 3D (plancher + plafond + parois verticales)

#### 📊 Composition finale de la TMA AVORD :
- **Structure** : 3 parties (1.1, 1.2, 2) avec 3 volumes associés
- **Services** : 6 services (TWR, APP, SRE, PAR, UDF, VDF)  
- **Fréquences** : 36 fréquences radio assignées
- **Visualisation** : Volume 3D bleu (25% opacité) dans Google Earth

Ce workflow peut être reproduit pour n'importe quel espace aérien du XML-SIA en remplaçant "AVORD" par le mot-clé souhaité.

## ✨ Points forts

- **🎯 Extraction ciblée** : Extrait uniquement ce qui est nécessaire
- **🔗 Dépendances complètes** : Résolution automatique de toutes les relations
- **✅ Validation intégrée** : Conformité XSD automatique
- **📊 Analyse de qualité** : Validation contre spécification officielle
- **🚀 Performance** : Traitement rapide même sur gros fichiers XML-SIA
- **📝 Documentation** : Couverture complète avec exemples

---

*Développé pour l'extraction et la validation des données XML-SIA v6.0 - Format officiel français d'échange d'informations aéronautiques*