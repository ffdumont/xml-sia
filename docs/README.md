# Documentation XML-SIA

Ce dossier centralise toute la documentation du projet d'extraction et validation XML-SIA v6.0.

## Guides d'utilisation

### `README_extract_espace.md`
Documentation complète de l'outil d'extraction d'espaces aériens
- Guide d'installation et utilisation
- Exemples d'extraction
- Résolution de problèmes

## Rapports d'analyse

### `COHERENCE_REPORT.md`
Rapport de validation du schéma XSD contre la spécification SIA officielle
- Analyse de conformité
- Entités validées
- Statistiques de couverture

### `RELATIONS_ANALYSIS_REPORT.md`
Analyse détaillée des relations dans la spécification SIA v6.0
- Inventaire des relations `relation(EntityName)`
- Validation de l'implémentation XSD
- Recommandations d'amélioration

## Spécifications officielles

### `specifications/`
Dossier pour les documents de référence SIA (à ajouter) :
- `2022-12-28 - siaexport6a.md` - Spécification officielle SIA v6.0
- Autres documents de référence

## Organisation

```
docs/
├── README.md                      # Ce fichier
├── README_extract_espace.md       # Guide d'utilisation extraction
├── COHERENCE_REPORT.md           # Rapport validation XSD
├── RELATIONS_ANALYSIS_REPORT.md  # Analyse des relations
└── specifications/               # Documents officiels SIA
    └── (documents de référence)
```

## Mise à jour

La documentation est maintenue automatiquement par les outils d'analyse :
- `tools/check_coherence.py` génère/met à jour les rapports de validation
- Les guides d'utilisation sont mis à jour manuellement selon les évolutions