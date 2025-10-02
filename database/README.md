# Database package pour XML-SIA

Ce dossier contient les services pour gérer les données XML-SIA dans une base SQLite :

## Services

- **schema_generator.py** : Génère le schéma SQLite basé sur le XSD Espace.xsd
- **xml_importer.py** : Import les données XML dans la base SQLite
- **verify_data.py** : Vérifie les données importées et les relations
- **check_db.py** : Vérifie la structure de la base de données

## Workflow complet

### 1. Extraire un espace aérien depuis le XML source
```bash
python tools/extract_espace.py --input "data-input/XML_SIA_2025-10-02.xml" --identifier "[LF][TMA LE BOURGET]" --output "data-output/TMA_LE_BOURGET.xml"
```

### 2. Générer le schéma SQLite
```bash
python database/schema_generator.py --xsd "data-input/schemas/Espace.xsd" --database "sia_database.db" --verbose
```

### 3. Importer les données XML
```bash
python database/xml_importer.py --xml "data-output/TMA_LE_BOURGET.xml" --database "sia_database.db" --verbose
```

### 4. Vérifier les données importées
```bash
python database/verify_data.py
```

## Structure de la base de données

### Tables créées

- **territoires** : Données des territoires (France, etc.)
- **aerodromes** : Informations des aérodromes 
- **espaces** : Espaces aériens (TMA, CTR, etc.)
- **parties** : Parties géométriques des espaces
- **volumes** : Volumes 3D avec altitudes et classes
- **services** : Services ATS (TWR, ATIS, VDF, etc.)
- **frequences** : Fréquences radio des services

### Relations

- espaces → territoires (territoire_ref)
- espaces → aerodromes (ad_associe_ref)
- parties → espaces (espace_ref)
- volumes → parties (partie_ref)
- services → aerodromes (ad_ref)
- services → espaces (espace_ref)
- frequences → services (service_ref)

## Exemple avec TMA LE BOURGET

Le test avec TMA LE BOURGET importe :
- 1 territoire (FRANCE)
- 1 aérodrome (PONTOISE CORMEILLES EN VEXIN)
- 1 espace aérien (TMA LE BOURGET)
- 1 partie géométrique
- 1 volume (1500-2500 ft AMSL, Classe D)
- 3 services (ATIS, TWR, VDF PONTOISE)
- 3 fréquences radio

## Index et performances

Le schéma inclut 19 index optimisés pour :
- Recherches par clés logiques (lk)
- Jointures sur clés étrangères
- Recherches par type d'espace, nom, code aérodrome
- Requêtes sur les services ATS