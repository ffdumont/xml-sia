# XML-SIA : Extraction et validation d'espaces aériens

Outils d'extraction et de validation pour les données XML-SIA (Système d'Information Aéronautique) version 6.0.

## 🎯 Objectif

Extraire des espaces aériens spécifiques du fichier XML-SIA officiel avec toutes leurs dépendances (territoires, aérodromes, parties, volumes, services, fréquences) et valider la cohérence avec les spécifications officielles.

## 📁 Structure

```
xml-sia/
├── tools/                         # Outils d'extraction et validation
│   ├── extract_espace.py         # Outil d'extraction principal
│   ├── check_coherence.py        # Validation XSD vs spécification
│   └── README.md                  # Documentation des outils
├── schemas/                       # Schémas XSD et validation
│   ├── Espace.xsd                # Schéma XSD des espaces
│   └── test_validation_xsd.xml   # Tests de validation
├── data-input/                    # Données sources SIA
│   ├── schemas/                  # Schémas XSD (incluant Espace.xsd)
│   └── XML_SIA_2025-10-02.xml   # Fichier XML SIA principal
├── data-output/                   # Extractions générées
│   ├── schemas/                  # Rapports de validation  
│   └── inventory/                # Rapports d'inventaire
├── docs/                          # Documentation et rapports
│   ├── README_extract_espace.md  # Guide d'utilisation
│   ├── COHERENCE_REPORT.md       # Rapport de validation
│   └── RELATIONS_ANALYSIS_REPORT.md # Analyse des relations
├── inventory/                     # Analyses d'inventaire
└── README.md                      # Ce fichier
```

## 🚀 Utilisation rapide

### Extraction d'un espace aérien
```bash
# Extraire la TMA Le Bourget avec toutes ses dépendances
python tools/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]" --verbose

# Extraire une CTR par pk
python tools/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "1204" --verbose
```

### Validation de cohérence
```bash
# Vérifier la cohérence XSD vs spécification SIA
python tools/check_coherence.py
```

## 📊 Fonctionnalités principales

### 🎯 Extraction d'espaces aériens (`tools/extract_espace.py`)
- **Extraction ciblée** par identifiant `lk` ou `pk`
- **Résolution automatique** de toutes les dépendances
- **Validation XSD** intégrée
- **Formatage XML** optimisé (réduction 57% des lignes vides)
- **Support complet** : TMA, CTR, espaces complexes

### ✅ Validation de cohérence (`tools/check_coherence.py`)
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

### TMA Le Bourget (Espace complexe)
```bash
python tools/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]"
```
**Résultat** : 11 entités extraites (Territoire, Ad, Espace, 2 Parties, 2 Volumes, 3 Services, 2 Fréquences)

### CTR Pontoise (Espace simple)
```bash
python tools/extract_espace.py --input data-input/XML_SIA_2025-10-02.xml --identifier "[LF][CTR PONTOISE]"
```
**Résultat** : 11 entités extraites avec relations CTR ↔ Aérodrome

## ✨ Points forts

- **🎯 Extraction ciblée** : Extrait uniquement ce qui est nécessaire
- **🔗 Dépendances complètes** : Résolution automatique de toutes les relations
- **✅ Validation intégrée** : Conformité XSD automatique
- **📊 Analyse de qualité** : Validation contre spécification officielle
- **🚀 Performance** : Traitement rapide même sur gros fichiers XML-SIA
- **📝 Documentation** : Couverture complète avec exemples

---

*Développé pour l'extraction et la validation des données XML-SIA v6.0 - Format officiel français d'échange d'informations aéronautiques*