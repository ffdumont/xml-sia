# Module Validation - Contrôle de cohérence des données XML-SIA

Ce module contient les outils pour valider et contrôler la cohérence des données XML-SIA.

## Fichiers

- `check_coherence.py` : Contrôle de cohérence des espaces aériens et validation des données

## Usage

```python
from validation.check_coherence import validate_xml_data

# Validation des données
results = validate_xml_data("XML_SIA_2025-10-02.xml")
```

## Contrôles effectués

- Validation des schémas XSD
- Cohérence des géométries
- Intégrité des références
- Conformité aux standards OACI