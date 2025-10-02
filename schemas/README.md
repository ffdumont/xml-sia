# Schémas XSD XML-SIA

Ce dossier contient les schémas XSD pour la validation des données XML-SIA v6.0.

## Fichiers

### `Espace.xsd`
**Schéma XSD principal pour l'extraction d'espaces aériens**

- **Entité racine** : `SiaExport` 
- **Entités définies** : Territoire, Ad, Espace, Partie, Volume, Service, Frequence
- **Validation** : Structure et relations des espaces aériens
- **Conformité** : 100% compatible avec spécification SIA v6.0

### `test_validation_xsd.xml`
**Fichier de test pour validation XSD**

Exemple minimal validant la structure du schéma.

## Utilisation

### Validation manuelle
```bash
# Validation avec xmllint (si disponible)
xmllint --schema schemas/Espace.xsd data/output/mon_fichier.xml --noout
```

### Validation automatique
La validation est intégrée dans `tools/extract_espace.py` :
- Validation automatique après extraction
- Rapport d'erreurs si structure incorrecte
- Génération de XML conforme au schéma

## Structure du schéma

```xml
<SiaExport>
  <TerritoireS>...</TerritoireS>
  <AdS>...</AdS>
  <EspaceS>...</EspaceS>
  <PartieS>...</PartieS>
  <VolumeS>...</VolumeS>
  <ServiceS>...</ServiceS>
  <FrequenceS>...</FrequenceS>
</SiaExport>
```

## Relations supportées

- **Espace** → Territoire (obligatoire)
- **Espace** → Ad (optionnel, via AdAssocie)
- **Partie** → Espace (obligatoire)
- **Volume** → Partie (obligatoire)
- **Service** → Ad ou Espace (obligatoire)
- **Frequence** → Service (obligatoire)

Toutes les relations utilisent des références `pk`/`lk` conformes à la spécification SIA.