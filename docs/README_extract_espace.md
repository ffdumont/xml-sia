# Extracteur d'Espaces Aériens XML-SIA

## Description

Script Python pour extraire un espace aérien du fichier XML-SIA avec toutes ses dépendances, basé sur le schéma XSD `Espace.xsd` pour assurer la conformité XML-SIA v6.0.

## Fonctionnalités

- **Extraction complète** : Extrait un espace aérien et toutes ses dépendances selon le modèle XML-SIA
- **Basé sur XSD** : Utilise le schéma `Espace.xsd` pour garantir la structure correcte
- **Recherche flexible** : Recherche par `pk` (clé primaire) ou `lk` (clé logique)
- **Validation des relations** : Suit toutes les références XSD (TerritoireRef, AdAssocieRef, etc.)
- **XML conforme** : Génère un XML de sortie respectant le schéma XSD

## Dépendances extraites

Selon la structure XSD, le script extrait automatiquement :

```
Espace (entité principale)
├── Territoire (via TerritoireRef) - obligatoire
├── Aérodrome associé (via AdAssocieRef) - optionnel  
├── Parties de l'espace (Partie[])
│   ├── Contours et géométries
│   └── Volumes de chaque partie (Volume[])
├── Services ATS (Service[])
│   └── Fréquences des services (Frequence[])
└── Bordures (via références géométriques)
```

## Installation

Aucune dépendance externe requise, utilise uniquement les modules Python standard :
- `xml.etree.ElementTree`
- `argparse`
- `xml.dom.minidom`

## Usage

### Syntaxe de base

```bash
python extract_espace.py --input <fichier_xml_sia> --identifier <pk_ou_lk>
```

### Exemples

1. **Extraction par pk (clé primaire)** :
```bash
python extract_espace.py --input input/XML_SIA_2025-10-02.xml --identifier "304333"
```

2. **Extraction par lk (clé logique)** :
```bash
python extract_espace.py --input input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]"
```

3. **Sauvegarde dans un fichier** :
```bash
python extract_espace.py --input input/XML_SIA_2025-10-02.xml --identifier "304333" --output output/tma_bourget.xml
```

4. **Mode verbose** :
```bash
python extract_espace.py --input input/XML_SIA_2025-10-02.xml --identifier "304333" --verbose
```

### Options complètes

- `--input`, `-i` : Fichier XML SIA d'entrée (obligatoire)
- `--identifier`, `-id` : Identifiant pk ou lk de l'espace à extraire (obligatoire)
- `--output`, `-o` : Fichier XML de sortie (optionnel, affichage stdout par défaut)
- `--xsd` : Fichier XSD de validation (par défaut : `output/Espace.xsd`)
- `--verbose`, `-v` : Mode verbose avec résumé détaillé

## Exemple de résultat

Le script extrait la TMA Le Bourget avec toutes ses dépendances :

```xml
<?xml version="1.0" encoding="ISO-8859-1"?>
<SiaExport xmlns:sia="http://www.sia.aviation-civile.gouv.fr/siaexport" 
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
           xsi:schemaLocation="http://www.sia.aviation-civile.gouv.fr/siaexport Espace.xsd">
  <TerritoireS>
    <Territoire pk="100" lk="[LF]">
      <Territoire>LF</Territoire>
      <Nom>FRANCE</Nom>
    </Territoire>
  </TerritoireS>
  <AdS>
    <Ad pk="83" lk="[LF][PT]">
      <!-- Données complètes de l'aérodrome PONTOISE -->
    </Ad>
  </AdS>
  <EspaceS>
    <Espace pk="304333" lk="[LF][TMA LE BOURGET]">
      <Territoire pk="100" lk="[LF]"/>
      <TypeEspace>TMA</TypeEspace>
      <Nom>LE BOURGET</Nom>
      <AltrFt>5000</AltrFt>
      <AdAssocie pk="83" lk="[LF][PT]"/>
    </Espace>
  </EspaceS>
  <PartieS>
    <!-- Parties de la TMA avec géométries -->
  </PartieS>
  <VolumeS>
    <!-- Volumes avec plafonds, planchers, classes d'espace -->
  </VolumeS>
  <ServiceS>
    <!-- Services ATS associés -->
  </ServiceS>
  <FrequenceS>
    <!-- Fréquences des services -->
  </FrequenceS>
</SiaExport>
```

## Messages d'information

Le script affiche des informations détaillées sur l'extraction :

- ✓ Espace trouvé par pk/lk
- → Références découvertes
- ✓ Entités résolues
- Résumé final avec compteurs

## Exemple complet - TMA Le Bourget

```bash
# Extraction complète de la TMA Le Bourget
python extract_espace.py \
    --input input/XML_SIA_2025-10-02.xml \
    --identifier "[LF][TMA LE BOURGET]" \
    --output output/tma_bourget_complete.xml \
    --verbose

# Résultat : 11 entités extraites
# - 1 Territoire (FRANCE)
# - 1 Aérodrome (PONTOISE) 
# - 1 Espace (TMA LE BOURGET)
# - 1 Partie (géométrie)
# - 1 Volume (plafond/plancher)
# - 3 Services ATS
# - 3 Fréquences
```

## Structure des fichiers

```
xml-sia/
├── extract_espace.py          # Script principal
├── input/
│   └── XML_SIA_2025-10-02.xml # Fichier SIA source
├── output/
│   ├── Espace.xsd             # Schéma XSD complet avec élément racine SiaExport
│   └── tma_bourget_clean.xml  # Résultat d'extraction optimisé
└── README_extract_espace.md   # Cette documentation
```

## Validation XSD

Le schéma XSD `Espace.xsd` a été complété pour inclure :

1. **Élément racine `SiaExport`** : Permet la validation complète du XML généré
2. **Définitions complètes** : Tous les types `Territoire`, `Ad`, `Service`, `Frequence` avec leur structure réelle
3. **Sections contenantes** : `TerritoireS`, `AdS`, `EspaceS`, `PartieS`, `VolumeS`, `ServiceS`, `FrequenceS`
4. **Validation VS Code** : Le XML généré ne produit plus d'erreurs de validation dans l'éditeur

### Cohérence avec la Spécification SIA v6.0 ✅

Le schéma XSD a été **validé pour cohérence** avec la documentation officielle `2022-12-28 - siaexport6a.md` :

- ✅ **7 entités principales** conformes (Espace, Partie, Volume, Service, Frequence, Ad, Territoire)
- ✅ **Toutes les relations** entre entités respectées selon la spécification SIA
- ✅ **Structure XML** identique aux données réelles du fichier XML-SIA source
- ✅ **Types de données** conformes (énumérations, entiers, textes, géométries)
- ✅ **Cardinalités** respectées (obligatoire/optionnel, unique/multiple)

**Approche validée** : Utilisation d'éléments XML plutôt que d'attributs XML pour les données métier, conforme aux données réelles et aux bonnes pratiques XML.

Voir `COHERENCE_REPORT.md` pour l'analyse détaillée de cohérence.

## Avantages de l'approche basée sur XSD

1. **Conformité garantie** : Le XML généré respecte le schéma officiel XML-SIA v6.0
2. **Relations complètes** : Suit toutes les références définies dans le XSD
3. **Validation structurelle** : Assure la cohérence des données extraites
4. **Évolutivité** : S'adapte automatiquement aux évolutions du schéma XSD
5. **Formatage optimisé** : XML propre sans lignes vides excessives (réduction de 57% du nombre de lignes)

## Notes importantes

- Le script recherche d'abord l'espace par `pk`, puis par `lk` si non trouvé
- L'aérodrome associé affiché peut être différent de l'aérodrome éponyme (ici PONTOISE au lieu du BOURGET)
- Toutes les géométries et contours sont préservés dans l'extraction
- Les horaires d'activité et classes d'espace sont inclus dans les volumes

## Dépannage

- **"Espace non trouvé"** : Vérifiez l'identifiant `pk` ou `lk` dans le fichier source
- **"Section EspaceS non trouvée"** : Le fichier XML n'est pas au format SIA attendu
- **Erreur de parsing** : Le fichier XML est malformé ou corrompu