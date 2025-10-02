# Utils - Utilitaires de base de données et validation

Ce répertoire contient les utilitaires pour la gestion de la base de données SQLite et la validation des données XML-SIA.

## 📋 Utilitaires disponibles

### `xml_importer.py` - Import XML vers SQLite
Importe les données XML-SIA vers une base de données SQLite pour accès rapide.

**Usage :**
```bash
python utils/xml_importer.py --input data-input/XML_SIA_2025-10-02.xml --output sia_database.db
```

### `check_db.py` - Vérification de la base de données
Vérifie la cohérence et l'intégrité de la base de données SQLite.

**Usage :**
```bash
python utils/check_db.py --database sia_database.db
```

### `verify_data.py` - Validation des données
Valide la cohérence des données entre XML source et base SQLite.

**Usage :**
```bash
python utils/verify_data.py --xml data-input/XML_SIA_2025-10-02.xml --db sia_database.db
```

### `schema_generator.py` - Génération de schémas
Génère automatiquement les schémas de base de données à partir du XML-SIA.

**Usage :**
```bash
python utils/schema_generator.py --input data-input/XML_SIA_2025-10-02.xml
```

### `sia_entity_inventory.py` - Inventaire des entités SIA
Génère un inventaire complet des entités présentes dans le fichier XML-SIA.

**Usage :**
```bash
python utils/sia_entity_inventory.py --input data-input/XML_SIA_2025-10-02.xml --output data-output/inventory/
```

## 🎯 Workflow recommandé

1. **Import** : `xml_importer.py` pour créer la base SQLite
2. **Validation** : `verify_data.py` pour vérifier la cohérence
3. **Inventaire** : `sia_entity_inventory.py` pour analyser le contenu
4. **Maintenance** : `check_db.py` pour vérifications périodiques

## 📊 Base de données SQLite

La base `sia_database.db` contient 7 tables principales :
- `territoires` (2 entités)
- `aerodromes` (688 entités)  
- `espaces` (943 entités)
- `parties` (4,854 entités)
- `volumes` (5,117 entités)
- `services` (2,027 entités)
- `frequences` (2,179 entités)

## 🔧 Performance

- **SQLite** : Recherches <1ms par requête
- **XML direct** : ~583ms pour recherche complète
- **Import initial** : ~30s pour XML-SIA complet