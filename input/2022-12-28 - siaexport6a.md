# Modèle de données XML-SIA v6.0
**Service de l'Information Aéronautique (SIA)**  
**Date**: 28 décembre 2022  
**Version**: SiaExport V6.0

---

## 1. Objet du document

Ce document décrit le modèle de données servant de support au fichier d'export XML-SIA.

### Précisions importantes

- **Type de données**: Image complète de la base à une date donnée (élément "situation" avec attributs XML indiquant les dates de publication et d'entrée en vigueur)

- **Attribut "pk"**: Chaque entité possède un attribut XML "pk" (entier) servant de clé d'identification unique persistante dans le temps

- **Attribut "lk"**: Reconstitue la clé primaire pour faciliter l'interprétation humaine (ne doit pas être utilisé pour des traitements)

- **Élément "Extension"**: Type xs:any optionnel destiné à stocker des informations annexes non documentées ou tester de futures extensions sans invalider le fichier XML

---

## 2. Généralités

Le modèle est décrit sous forme entités/associations :
- **Entité**: Collection d'éléments dotés de caractéristiques communes (attributs)
- **Association**: Liens ou relations entre entités

### Symboles utilisés dans les diagrammes

```
Objet1 ·-◄ Objet2
```
Un Objet1 est associé à un nombre quelconque d'Objet2, un Objet2 est associé à un Objet1 et un seul.

```
Objet2 ·-□ Objet3
```
Un Objet2 est associé à un Objet3 au maximum, un Objet3 est associé à un Objet2 et un seul.

```
Objet3 ·-◄ Objet4 ·-┤
```
Un Objet3 est associé à un nombre quelconque d'Objet4, un Objet4 est associé à un Objet3 au maximum.

**Symbole en gras**: La relation est identifiante pour l'objet situé à sa droite.

**Cas particulier**: Association multiple (Objet4 ⟷ Objet5) - l'un des objets contient un attribut complexe (ex: attribut Contour dans Partie)

---

## 3. Diagramme Entités-Associations

```
Territoire
    │
    ├──◄ Helistation
    ├──◄ Obstacle
    ├──◄ Phare
    ├──◄ Bordure ──○ Partie ──◄ Volume
    ├──◄ Espace ···◄ Partie       └──◄ Frequence
    │        └─··◄ Service
    │
    ├──◄ Ad ──◄ VorInsChk
    │      │
    │      ├──◄ Rwy ──◄ Ils ──┬── DmeIls
    │      │      │            ├── Gp
    │      │      ├──◄ RwyLgt  └── Mkr
    │      │      └──◄ TwyDecDist
    │
    ├──◄ NavFix ──┬── RadioNav ┐··Ad
    │             │             │
    └──◄ Route ──◄ Segment ──┤··Cdr
                       │
                       └── (relations NavFix)
```

---

## 4. Présentation des entités

| Objet | Définition |
|-------|------------|
| **Ad** | Aérodromes |
| **Bordure** | Lignes d'appui pour description de contours d'espaces (frontières, fleuves...) |
| **Cdr** | Restrictions d'utilisation des segments de route |
| **DmeIls** | DME d'atterrissage associés aux ILS |
| **Espace** | Espaces aériens de toutes natures |
| **Frequence** | Fréquences disponibles pour les services |
| **Gp** | Radiophares d'alignement de descente (glide-path) des ILS |
| **Helistation** | Hélistations |
| **Ils** | Radiophares d'alignement de piste (localizer, LLZ) des ILS |
| **Mkr** | Radiobornes (OM, MM, IM) des ILS |
| **NavFix** | Points d'appui du réseau de routes (aides radio comprises) |
| **Obstacle** | Obstacles |
| **Partie** | Parties d'espaces aériens |
| **Phare** | Phares marins et feux aéronautiques |
| **RadioNav** | Aides radio |
| **Route** | Routes aériennes |
| **Rwy** | Pistes de décollage/atterrissage des aérodromes |
| **RwyLgt** | Balisage lumineux des pistes |
| **Segment** | Caractéristiques d'une route entre deux points consécutifs |
| **Service** | Services aux vols supportés par communications sol/air |
| **Territoire** | Territoires où se situent les autres entités |
| **TwyDecDist** | Réductions de distance décollage |
| **Volume** | Caractéristiques du découpage vertical des espaces aériens |
| **VorInsChk** | Points de vérification VOR-INS sur les aérodromes |

---

## 5. Domaines simples

| Domaine | Définition |
|---------|------------|
| `entier(min,max)` | Nombre entier dans l'intervalle [min,max] |
| `decimal(min,max,p)` | Nombre décimal dans [min,max] avec p chiffres décimaux max |
| `Latitude` | Latitude en degrés décimaux: decimal(-90,+90,6) |
| `Longitude` | Longitude en degrés décimaux: decimal(-180,+180,6) |
| `texte(max)` | Chaîne de caractères de longueur max (encodage ISO-8859-1) |
| `Alpha3` | Chaîne de 1 à 3 lettres: [A-Z]{1,3} |
| `AlphaNum4` | Chaîne de 1 à 4 caractères alphanumériques: [A-Z0-9]{1,4} |
| `enum(liste)` | Toute valeur présente dans "liste" |
| `relation(entite)` | Toute occurrence de "entite" |

### Domaines géométriques particuliers

#### `contour`
Décrit l'emprise horizontale des espaces. Consiste en :
- **Cercle**: centre et rayon donnés
- **Énumération de points** connectés par :
  - `ortho`: arc d'orthodromie
  - `parallele`: arc de parallèle
  - `arc`: arc de cercle orienté (centre et rayon donnés)
  - `bordure`: via une bordure (polyline décrivant frontière, côte...) de clé donnée

**Syntaxe générale**: `[latitude,longitude,méthode(arg1,arg2,..)]*`

**Note**: Calcul nécessaire pour assurer cohérence et conformité aux exigences EAD lors de l'utilisation des méthodes arc ou bordure.

#### `geometrie`
Résolution de la spécification sous forme de polyligne pour faciliter l'utilisation par des SIG.

---

## 6. Contenu des entités

**Légende**:
- `cle`: Attribut membre de la clé primaire
- `!`: Attribut obligatoire
- `?`: Attribut optionnel

### Entité: **Ad** (Aérodromes)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire où se situe l'aérodrome |
| `cle` AdCode | AlphaNum4 | Code de l'aérodrome |
| `!` AdAd2 | enum(OuiNon) | AD décrit en AD2 |
| `!` AdStatut | enum(AdStatut) | Statut de l'aérodrome |
| `!` AdNomComplet | texte(60) | Nom complet de l'AD |
| `?` AdNomCarto | texte(30) | Nom utilisé sur les cartes |
| `?` Ctr | relation(Espace) | CTR associée à l'AD |
| `?` AdSituation | texte(60) | Direction et distance de la ville |
| `!` Wgs84 | enum(Wgs84) | Précision coordonnées WGS84 (hérité par objets descendants) |
| `!` ArpLat | Latitude | Latitude de l'ARP |
| `!` ArpLong | Longitude | Longitude de l'ARP |
| `?` ArpSituation | texte(240) | Situation de l'ARP |
| `?` AdRefAltFt | entier(-1000,30000) | Altitude de référence (pieds) |
| `?` AdGeoUnd | entier(-1000,1000) | Ondulation du géoïde |
| `?` AdRefTemp | decimal(-10,40,2) | Température de référence (°C) |
| `?` AdMagVar | decimal(-180,180,2) | Déclinaison magnétique |
| `!` TfcIntl | enum(OuiNon) | Ouvert au trafic international commercial |
| `!` TfcNtl | enum(OuiNon) | Ouvert au trafic national commercial |
| `!` TfcIfr | enum(OuiNon) | Ouvert au trafic IFR |
| `!` TfcVfr | enum(OuiNon) | Ouvert au trafic VFR |
| `!` TfcRegulier | enum(OuiNon) | Ouvert au trafic commercial régulier |
| `!` TfcNonRegulier | enum(OuiNon) | Ouvert au trafic commercial non régulier |
| `!` TfcPrive | enum(OuiNon) | Ouvert au trafic privé |
| `?` AdGestion | texte(60) | Gestionnaire de l'AD |
| `?` AdAdresse | texte(100) | Adresse postale |
| `?` AdTel | texte(100) | Téléphone |
| `?` AdFax | texte(100) | Fax |
| `?` AdTelex | texte(100) | Télex |
| `?` AdAfs | texte(100) | Adresse RSFTA |
| `?` AdRem | texte(240) | Remarques données administratives |
| `?` HorAdminCode | enum(Hor) | Horaire administratif codé |
| `?` HorCustCode | enum(Hor) | Horaire douane codé |
| `?` HorAtsCode | enum(Hor) | Horaire services ATS codé |
| `?` HorSanTxt | texte(240) | Horaire service sanitaire |
| `?` HorBiaTxt | texte(240) | Horaire BIA/BRIA |
| `?` HorBdpTxt | texte(240) | Horaire BDP |
| `?` HorMetTxt | texte(240) | Horaire météo |
| `?` HorAvtTxt | texte(240) | Horaire avitaillement |
| `?` HorManutentionTxt | texte(240) | Horaire manutention |
| `?` HorSureteTxt | texte(240) | Horaire sûreté |
| `?` HorDegivrageTxt | texte(240) | Horaire dégivrage |
| `?` HorRem | texte(240) | Remarques sur horaires |
| `?` HorAdminTxt | texte(240) | Horaire administratif (si non codable) |
| `?` HorCustTxt | texte(240) | Horaire douane (si non codable) |
| `?` HorAtsTxt | texte(240) | Horaire ATS (si non codable) |
| ... | ... | *(suite: services escale, SSLIA, déneigement, etc.)* |
| `!` Geometrie | geometrie | Position ARP: latArp,longArp |

### Entité: **Bordure** (Lignes d'appui d'espaces)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire de la bordure |
| `cle` Code | texte(60) | Code d'identification |
| `!` Nom | texte(60) | Nom en clair |
| `!` Wgs84 | enum(Wgs84) | Précision coordonnées WGS84 |
| `!` Geometrie | geometrie | Géométrie sous forme de polyline |

### Entité: **Cdr** (Restrictions segments de route)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` CdrCat | enum(Cdr) | Type de restriction |
| `cle` Segment | relation(Segment) | Segment où débute la restriction |
| `cle` PlafondFl | entier(30,460) | FL plafond |
| `?` FinCdr | relation(Segment) | Segment où se termine la restriction |
| `!` PlancherFl | entier(30,460) | FL plancher |
| `!` HorCdrCode | enum(Hor) | Horaire d'application |
| `?` HorCdrTxt | texte(240) | Horaire (si non codable) |
| `?` Remarque | texte(240) | Remarque |

### Entité: **DmeIls** (DME d'atterrissage)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Ils | relation(Ils) | Identification par l'ILS |
| `!` Latitude | Latitude | Latitude du DME |
| `!` Longitude | Longitude | Longitude du DME |
| `?` AltitudeFt | entier(-1000,30000) | Altitude (ft) |
| `?` Situation | texte(30) | Situation |
| `?` Portee | decimal(0,1000,2) | Portée (NM) |
| `?` FlPorteeVert | entier(0,1000) | Portée verticale (FL) |
| `?` ZeroTdz | enum(OuiNon) | Distance 0 au TDZ ou au DME |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **Espace** (Espaces aériens)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire de l'espace |
| `cle` TypeEspace | enum(TypeEspace) | Type d'espace |
| `cle` Nom | texte(40) | Nom de l'espace |
| `?` AltrFt | entier(-1000,30000) | Altitude de transition (ft AMSL) |
| `?` AdAssocie | relation(Ad) | Aérodrome principal associé |

### Entité: **Frequence** (Fréquences des services)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Service | relation(Service) | Service désigné |
| `cle` Frequence | decimal(0,1000,3) | Fréquence (MHz) |
| `?` Espacement | enum(EspFreq) | Espacement de fréquence |
| `!` HorCode | enum(Hor) | Horaire de fonctionnement |
| `?` HorTxt | texte(240) | Horaire (si non codable) |
| `?` Suppletive | enum(OuiNon) | Fréquence supplétive |
| `?` SecteurSituation | texte(100) | Secteurs desservis/situation |
| `?` Remarque | texte(240) | Remarque |

### Entité: **Gp** (Glide-path des ILS)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Ils | relation(Ils) | Identification par l'ILS |
| `!` Latitude | Latitude | Latitude du GP |
| `!` Longitude | Longitude | Longitude du GP |
| `?` AltitudeFt | entier(-1000,30000) | Altitude (ft) |
| `?` Situation | texte(30) | Situation |
| `!` Pente | decimal(0,10,2) | Pente du GP |
| `!` RdhFt | decimal(0,100,2) | RDH (ft) |
| `?` Couverture | texte(100) | Couverture |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **Helistation** (Hélistations)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire de l'hélistation |
| `cle` Nom | texte(60) | Nom |
| `!` Atlas | enum(OuiNon) | Figure dans l'atlas |
| `!` Statut | enum(AdStatut) | Statut |
| `!` Ifr | enum(OuiNon) | Ouverte au trafic IFR |
| `!` Nuit | enum(OuiNon) | Accessible la nuit |
| `!` Latitude | Latitude | Latitude |
| `!` Longitude | Longitude | Longitude |
| `!` Wgs84 | enum(Wgs84) | Précision WGS84 |
| `?` AltitudeFt | entier(-1000,30000) | Altitude |
| `?` HauteurFt | entier(0,1000) | Hauteur hors sol TLOF |
| `?` DimFato | texte(40) | Dimensions FATO |
| `?` DimTlof | texte(40) | Dimensions TLOF |
| `?` SousCat | enum(HelCat) | Catégorie |
| `?` ClassePerf | texte(30) | Classe de performances |
| `?` HelRef | texte(50) | Hélicoptère de référence |
| `?` EnTerrasse | enum(OuiNon) | TLOF surélevée |
| `?` ZoneHabitee | enum(ZoneHabitee) | En zone habitée |
| `?` Revetement | texte(40) | Revêtement TLOF |
| `?` Resistance | texte(40) | Résistance TLOF |
| `?` HorTxt | texte(70) | Horaire |
| `?` Sslia | texte(70) | SSLIA |
| `?` Balisage | texte(70) | Balisage |
| `?` Exploitant | texte(140) | Exploitant |
| `?` Remarque | texte(1000) | Remarque |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **Ils** (Localizer des ILS)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Rwy | relation(Rwy) | Piste desservie |
| `cle` Qfu | enum(Qfu) | Sens de piste |
| `!` Ident | Alpha3 | Indicatif ILS |
| `!` Frequence | decimal(108,112,2) | Fréquence LLZ |
| `!` IlsCat | enum(IlsCat) | Catégorie ILS |
| `?` IlsGuidage | enum(IlsGuidage) | Niveau de guidage |
| `?` IlsSecurite | enum(IlsSecurite) | Niveau de sécurité |
| `!` Latitude | Latitude | Latitude LLZ |
| `!` Longitude | Longitude | Longitude LLZ |
| `?` AltitudeFt | entier(-1000,30000) | Altitude (ft) |
| `?` Couverture | texte(100) | Couverture |
| `?` Situation | texte(30) | Situation |
| `!` HorCode | enum(Hor) | Horaire de fonctionnement |
| `?` Remarque | texte(240) | Remarques |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **Mkr** (Radiobornes des ILS)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Ils | relation(Ils) | ILS associé |
| `cle` Mkr | enum(Mkr) | Type de marker (OM/MM/IM) |
| `!` Latitude | Latitude | Latitude |
| `!` Longitude | Longitude | Longitude |
| `?` AltitudeFt | entier(-1000,30000) | Altitude (ft) |
| `?` Situation | texte(30) | Situation |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **NavFix** (Points d'appui réseau de routes)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire du NavFix |
| `cle` NavType | enum(NavType) | Type de NavFix |
| `cle` Ident | texte(10) | Indicatif |
| `!` Wgs84 | enum(Wgs84) | Précision WGS84 |
| `!` Latitude | Latitude | Latitude |
| `!` Longitude | Longitude | Longitude |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **Obstacle** (Obstacles)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire de l'obstacle |
| `cle` NumeroNom | texte(10) | Nom ou numéro |
| `!` Latitude | Latitude | Latitude |
| `!` Longitude | Longitude | Longitude |
| `!` Wgs84 | enum(Wgs84) | Précision WGS84 |
| `!` TypeObst | enum(TypeObst) | Type d'obstacle |
| `!` Combien | entier(0,99) | Nombre d'obstacles (0=inconnu) |
| `!` AmslFt | entier(-1000,30000) | Altitude AMSL sommet (ft) |
| `!` AglFt | entier(0,10000) | Hauteur hors sol (ft) |
| `!` Balisage | enum(BalObst) | Balisage |
| `?` Remarque | texte(240) | Remarque |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **Partie** (Parties d'espaces aériens)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Espace | relation(Espace) | Espace auquel appartient la partie |
| `cle` NomPartie | texte(20) | Nom de la partie |
| `!` NumeroPartie | entier(0,32767) | Ordre de tri par défaut |
| `?` NomUsuel | texte(50) | Nom usuel |
| `!` Contour | contour | Limites latérales (spécification) |
| `?` Geometrie | geometrie | Limites sous forme de polyline (pour SIG) |

### Entité: **Phare** (Phares marins et feux aéronautiques)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire du phare |
| `cle` NumeroNom | texte(10) | Nom ou numéro |
| `!` Type | enum(Phare) | Type de phare |
| `!` Latitude | Latitude | Latitude |
| `!` Longitude | Longitude | Longitude |
| `!` Wgs84 | enum(Wgs84) | Précision WGS84 |
| `!` Situation | texte(40) | Situation |
| `?` Signal | texte(20) | Signal d'identification |
| `?` Intensite | entier(0,10000) | Intensité |
| `?` Remarque | texte(100) | Remarque |
| `!` HorCode | enum(Hor) | Horaire d'activité codé |
| `?` HorTxt | texte(100) | Horaire (si non codable) |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

### Entité: **RadioNav** (Aides radio)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` NavFix | relation(NavFix) | NavFix associé |
| `!` Frequence | decimal(0,1000,3) | Fréquence (ou VOR appariée pour TACAN) |
| `?` Situation | texte(30) | Situation |
| `?` Ad | relation(Ad) | AD où se situe l'aide radio |
| `?` Station | texte(60) | Station (si pas un AD) |
| `?` LatDme | Latitude | Latitude DME/TACAN |
| `?` LongDme | Longitude | Longitude DME/TACAN |
| `?` AltitudeFt | entier(-1000,30000) | Altitude (ft) |
| `!` HorCode | enum(Hor) | Horaire de fonctionnement |
| `?` Usage | enum(Usage) | Usage préférentiel |
| `?` Portee | decimal(0,1000,2) | Portée (NM) |
| `?` FlPorteeVert | entier(0,1000) | Portée verticale (FL) |
| `?` Couverture | texte(40) | Couverture |
| `?` Remarque | texte(240) | Remarque |
| `?` Geometrie | geometrie | Position: LatDme,LongDme |

### Entité: **Route** (Routes aériennes)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | relation(Territoire) | Territoire de la route |
| `cle` Prefixe | Alpha3 | Préfixe du nom |
| `cle` Numero | entier(1,999) | Numéro de la route |
| `!` Origine | relation(NavFix) | NavFix d'origine |
| `!` RouteType | enum(RouteType) | Type de route |
| `?` TypeCompteRendu | enum(CompteRendu) | Compte-rendu obligatoire/facultatif |
| `?` OrigineTxt | texte(40) | Commentaire sur l'origine |
| `?` Remarque | texte(1000) | Remarque |

### Entité: **Rwy** (Pistes)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Ad | relation(Ad) | Aérodrome |
| `cle` Rwy | texte(7) | Identification piste (ex: 09L/27R) |
| `?` Longueur | decimal(0,5000,1) | Longueur (m) |
| `?` Principale | enum(OuiNon) | Piste principale |
| `?` Revetement | enum(Revetement) | Revêtement |
| `?` BandeDim | texte(40) | Dimensions de la bande |
| `?` LatThr1 | Latitude | Latitude extrémité 1 |
| `?` LongThr1 | Longitude | Longitude extrémité 1 |
| `?` AltFtThr1 | entier(-1000,30000) | Altitude extrémité 1 (ft) |
| `?` LatDThr1 | Latitude | Latitude seuil décalé 1 |
| `?` LongDThr1 | Longitude | Longitude seuil décalé 1 |
| `?` AltFtDThr1 | entier(-1000,30000) | Altitude seuil décalé 1 (ft) |
| `?` RwyRem1 | texte(240) | Remarques (sens 1) |
| `?` Largeur | decimal(0,500,1) | Largeur (m) |
| `?` OrientationGeo | decimal(0,180,2) | Orientation géographique |
| `?` Resistance | texte(40) | Résistance |
| ... | ... | *(données sens 2, distances déclarées, etc.)* |
| `?` Geometrie | geometrie | Axe de piste: Thr1,DThr1,DThr2,Thr2 |

### Entité: **RwyLgt** (Balisage lumineux pistes)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Rwy | relation(Rwy) | Piste balisée |
| `cle` Qfu | enum(Qfu) | Direction balisée |
| `?` LgtApchCat | enum(LgtApchCat) | Catégorie OACI balisage d'approche |
| `?` LgtApchLongueur | entier(0,5000) | Longueur balisage d'approche (m) |
| `?` LgtApchIntensite | texte(80) | Intensité balisage d'approche |
| `?` LgtThrCouleur | texte(20) | Couleur balisage de seuil |
| `?` PapiVasis | enum(PapiVasis) | Type aide visuelle d'alignement |
| `?` PapiVasisPente | decimal(0,100,2) | Pente de descente (%) |
| `?` MehtFt | entier(0,100) | MEHT (pieds) |
| `?` LgtTdzLongueur | texte(20) | Longueur balisage TDZ |
| `?` LgtAxeLongueur | texte(80) | Longueur balisage axial |
| `?` LgtAxeEspace | texte(20) | Espacement balisage axial |
| `?` LgtAxeCouleur | texte(20) | Couleur balisage axial |
| `?` LgtAxeIntensite | texte(20) | Intensité balisage axial |
| `?` LgtBordLongueur | texte(80) | Longueur balisage latéral |
| `?` LgtBordEspace | texte(20) | Espacement balisage latéral |
| `?` LgtBordCouleur | texte(20) | Couleur balisage latéral |
| `?` LgtBordIntensite | texte(20) | Intensité balisage latéral |
| `?` LgtFinCouleur | texte(20) | Couleur balisage d'extrémité |
| `?` LgtSwyLongueur | texte(20) | Longueur balisage SWY |
| `?` LgtSwyCouleur | texte(20) | Couleur balisage SWY |
| `?` LgtRem | texte(240) | Remarque sur le balisage |

### Entité: **Segment** (Segments de route)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Route | relation(Route) | Route à laquelle appartient le segment |
| `cle` Sequence | entier(0,32767) | Numéro d'ordre dans la route |
| `!` NavFixOrigine | relation(NavFix) | NavFix où débute le segment |
| `!` NavFixExtremite | relation(NavFix) | NavFix où se termine le segment |
| `?` CompteRendu | enum(CompteRendu) | Compte-rendu obligatoire/facultatif à l'extrémité |
| `?` ExtremiteTxt | texte(40) | Commentaire sur l'extrémité |
| `!` Circulation | enum(Circulation) | Sens de circulation et séries de niveaux |
| `?` CodeRnp | enum(Rnp) | Précision de navigation requise |
| `!` PlafondRefUnite | enum(AltiCode) | Référence et unité du plafond |
| `!` Plafond | entier(-1000,100000) | Valeur du plafond |
| `!` PlancherRefUnite | enum(AltiCode) | Référence et unité du plancher |
| `!` Plancher | entier(-1000,100000) | Valeur du plancher |
| `?` Distance | entier(1000) | Longueur du segment (NM) |
| `?` RouteMag | entier(0,360) | Orientation magnétique |
| `?` Acc | texte(30) | ACC gestionnaire |
| `?` Remarque | texte(1000) | Remarque |
| `!` Geometrie | geometrie | Géométrie du segment (polyline) |

### Entité: **Service** (Services ATS)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Ad ou Espace | relation(Ad ou Espace) | AD ou centre fournissant le service |
| `cle` Service | enum(SvcAts) | Type du service |
| `cle` IndicLieu | texte(20) | Partie "lieu" de l'indicatif d'appel |
| `cle` IndicService | enum(IndicService) | Partie "service" de l'indicatif d'appel |
| `?` Langue | enum(Langue) | Langue(s) utilisée(s) |

### Entité: **Territoire** (Territoires)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Territoire | texte(5) | Code identifiant le territoire |
| `!` Nom | texte(60) | Nom du territoire |

### Entité: **TwyDecDist** (Réductions distances décollage)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Rwy | relation(Rwy) | Piste concernée |
| `cle` Twy | texte(20) | Identification voie d'accès |
| `cle` Qfu | enum(Qfu) | Direction concernée |
| `!` ReducTkofDist | entier(0,5000) | Réduction distances décollage (m) |

### Entité: **Volume** (Volumes d'espaces aériens)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Partie | relation(Partie) | Partie à laquelle appartient le volume |
| `cle` Sequence | entier(0,32767) | Numéro d'identification |
| `!` PlafondRefUnite | enum(AltiCode) | Référence et unité du plafond |
| `!` Plafond | entier(-1000,100000) | Valeur du plafond |
| `?` Plafond2 | entier(0,100000) | Plafond alternatif en ft ASFC (valeur max effective) |
| `!` PlancherRefUnite | enum(AltiCode) | Référence et unité du plancher |
| `!` Plancher | entier(-1000,100000) | Valeur du plancher |
| `?` Plancher2 | entier(0,100000) | Plancher alternatif en ft ASFC (valeur min effective) |
| `?` Classe | enum(Classe) | Classe du volume |
| `!` HorCode | enum(Hor) | Horaire d'activité codé |
| `?` HorTxt | texte(240) | Horaire (si non codable) |
| `?` Rtba | enum(Rtba) | Appartenance réseau basse altitude (zones R) |
| `?` Activite | texte(240) | Activité |
| `?` Remarque | texte(1000) | Remarque |

### Entité: **VorInsChk** (Points de vérification VOR-INS)

| Attribut | Domaine | Définition |
|----------|---------|------------|
| `cle` Ad | relation(Ad) | Aérodrome où se situe le point |
| `cle` VorIns | enum(VorIns) | Point de calage VOR ou INS |
| `cle` Ident | texte(20) | Identification du point |
| `?` Wgs84 | enum(OuiNon) | Coordonnées WGS84 |
| `!` Latitude | Latitude | Latitude |
| `!` Longitude | Longitude | Longitude |
| `!` Geometrie | geometrie | Position: Latitude,Longitude |

---

## 7. Domaines énumérés

### AdStatut - Statut des aérodromes

| Code | Signification |
|------|---------------|
| ADM | Réservé aux ACFT de l'État |
| CAP | Ouvert à la circulation aérienne publique |
| MIL | À usage militaire |
| OFF | Désaffecté |
| PRV | À usage privé |
| RST | Agréé à usage restreint |
| TPD | Transport public à la demande |

### AltiCode - Codage des limites verticales

| Code | Signification |
|------|---------------|
| FL | Niveau de vol |
| ft AMSL | Pieds au-dessus du niveau moyen des mers |
| ft ASFC | Pieds au-dessus de la surface |
| SFC | La surface (valeur sans signification) |
| UNL | Illimité (valeur sans signification) |

### BalObst - Balisage des obstacles

| Code | Signification |
|------|---------------|
| jour | Balisage de jour |
| jour et nuit | Balisage de jour et de nuit |
| non balisé | Non balisé |
| nuit | Balisage de nuit |

### Cdr - Restrictions segments de route

| Code | Signification |
|------|---------------|
| 1 | Planifiable |
| 2 | Planifiable sur la base du msg xxxx |
| 3 | Non planifiable |

### Circulation - Sens circulation et séries de FL

| Code | Signification |
|------|---------------|
| (0-X) | Aucune série FL pré-allouée (sens unique vers origine) |
| (0=0) | Aucune série FL pré-allouée (double sens) |
| (1-X) | Série impaire vers l'origine (sens unique) |
| (1=2) | Série paire vers l'extrémité, impaire en sens opposé |
| (2-X) | Série paire vers l'origine (sens unique) |
| (2=1) | Série impaire vers l'extrémité, paire en sens opposé |
| (X-0) | Aucune série FL pré-allouée (sens unique vers extrémité) |
| (X-1) | Série impaire vers l'extrémité (sens unique) |
| (X-2) | Série paire vers l'extrémité (sens unique) |
| (XxX) | Inutilisable |

### Classe - Classes d'espace

| Code | Signification |
|------|---------------|
| A | Classe A |
| B | Classe B |
| C | Classe C |
| D | Classe D |
| E | Classe E |
| F | Classe F |
| G | Classe G |

### CompteRendu - Types de points de compte-rendu

| Code | Signification |
|------|---------------|
| facultatif | Facultatif |
| obligatoire | Obligatoire |
| fac ATS met | Facultatif ATS MET |
| obl ATS met | Obligatoire ATS MET |

### EspFreq - Espacements de fréquences COM

| Code | Signification |
|------|---------------|
| 25 kHz | Espacement 25 kHz |
| 8.33 kHz | Espacement 8.33 kHz |

### HelCat - Catégories d'hélistations

| Code | Signification |
|------|---------------|
| HA | Hélistation HA |
| HB | Hélistation HB |

### Hor - Horaires de fonctionnement

| Code | Signification |
|------|---------------|
| H24 | 24 heures |
| HJ | De jour |
| HJ+ | SR-30 SS+30 |
| HN | De nuit |
| HO | Suivant les besoins |
| HX | Pas d'horaire défini |
| WE | Le week-end |
| WE+ | Le week-end et la nuit |

### IlsCat - Catégories ILS

| Code | Signification |
|------|---------------|
| ? | Non définie |
| I | Catégorie 1 |
| II | Catégorie 2 |
| III | Catégorie 3 |

### IlsGuidage - Niveaux de guidage ILS

| Code | Signification |
|------|---------------|
| A | Niveau A |
| B | Niveau B |
| E | Niveau E |
| T | Niveau T |

### IlsSecurite - Niveaux de sécurité ILS

| Code | Signification |
|------|---------------|
| 1 | Niveau 1 |
| 2 | Niveau 2 |
| 3 | Niveau 3 |
| 4 | Niveau 4 |

### IndicService - Indicatifs d'appel radio

| Code | Signification |
|------|---------------|
| . | Auto-information |
| Approche | Service de contrôle d'approche |
| CCM | Service de contrôle militaire |
| Contrôle | Service de contrôle en route |
| Essais | Centre d'essais en vol |
| GCA | Approche contrôlée du sol |
| Gonio | Service de guidage gonio |
| Information | Service d'information de vol |
| Prévol | Contrôle prévol |
| Radar | Contrôle radar |
| Sol | Contrôle sol |
| Tour | Contrôle d'aérodrome |
| Trafic | Service d'information de trafic |

### Langue - Langues utilisées

| Code | Signification |
|------|---------------|
| en | Anglais |
| fr | Français |
| fr-en | Français et anglais |
| fr--en--de | Français, anglais, allemand |
| fr--en--it | Français, anglais, italien |
| fr--en--sp | Français, anglais, espagnol |

### LgtApchCat - Catégories balisage d'approche

| Code | Signification |
|------|---------------|
| 2 feux à éclats | 2 feux à éclats |
| CAT I | Catégorie I |
| CAT I-II | Catégorie I-II |
| CAT I-II-III | Catégorie I-II-III |
| CAT II | Catégorie II |
| CAT II-III | Catégorie II-III |
| CAT III | Catégorie III |
| Fé séquentiel | Feux séquentiels |

### Mkr - Types de marker ILS

| Code | Signification |
|------|---------------|
| IM | Radioborne intérieure |
| MM | Radioborne intermédiaire |
| OM | Radioborne extérieure |

### NavType - Types de NavFix

| Code | Signification |
|------|---------------|
| DME-ATT | DME d'atterrissage non associé à ILS |
| L | Radiophare MF non directionnel faible puissance |
| NDB | Radiophare MF non directionnel |
| PNP | Point non publié |
| TACAN | Système de navigation aérienne tactique |
| VOR | Radiophare omnidirectionnel VHF |
| VOR-DME | VOR + dispositif mesure de distance |
| VORTAC | VOR + TACAN |
| WPT | Point codé en 5 lettres |

### OuiNon - Valeur logique

| Code | Signification |
|------|---------------|
| non | Non |
| oui | Oui |

### PapiVasis - Aides visuelles à l'atterrissage

| Code | Signification |
|------|---------------|
| PAPI | PAPI |
| VASIS | VASIS |

### Phare - Types de phares

| Code | Signification |
|------|---------------|
| HBN | Phare de danger |
| IBN | Phare d'identification |
| PH | Phare marin |

### Qfu - Sens d'atterrissage

| Code | Signification |
|------|---------------|
| 1 | QFU de plus bas numéro |
| 2 | QFU de plus haut numéro |

### Revetement - Revêtements pistes et aires

| Code | Signification |
|------|---------------|
| asphalte | Asphalte |
| béton | Béton |
| béton bitumineux | Béton bitumineux |
| enrobé bitumineux | Enrobé bitumineux |
| gazon | Gazon |
| hydrocarboné | Hydrocarboné |
| macadam | Macadam |
| non revêtue | Non revêtue |
| revêtue | Revêtue |
| tarmac | Tarmac |

### Rnp - Précision de navigation requise

| Code | Signification |
|------|---------------|
| 1 | RNP 1 |
| 10 | RNP 10 |
| 5 | RNP 5 |

### RouteType - Types de routes

| Code | Signification |
|------|---------------|
| AWY | Voie aérienne (espace inférieur) |
| DOM | Route domestique |
| PDR | Itinéraire prédéterminé |
| RNAV | Route RNAV |
| WE | Itinéraire prédéterminé de week-end |

### Rtba - Appartenance réseau basse altitude

| Code | Signification |
|------|---------------|
| BA | Basse altitude |
| TBA | Très basse altitude |

### SsliaCat - Catégories SSLIA

| Code | Signification |
|------|---------------|
| 1 | Catégorie 1 |
| 2 | Catégorie 2 |
| 3 | Catégorie 3 |
| 4 | Catégorie 4 |
| 5 | Catégorie 5 |
| 6 | Catégorie 6 |
| 7 | Catégorie 7 |
| 8 | Catégorie 8 |
| 9 | Catégorie 9 |

### SvcAts - Services ATS

| Code | Signification |
|------|---------------|
| A/A | Auto Information |
| ACC | Contrôle en route (espace inférieur) |
| AFIS | Service d'information de vol |
| APP | Contrôle d'approche |
| ATIS | Service automatique d'information de vol (région terminale) |
| ATIS/S | ATIS surface |
| ATIS/V | ATIS VFR (portée réduite) |
| CCM | Centre de contrôle militaire |
| CEV | Essais en vol |
| D-ATIS | Service automatique d'information via data-link |
| FIS | Service d'information de vol |
| PAR | Radar d'approche de précision |
| SPAR | Radar léger d'approche de précision |
| SRE | Radar de surveillance d'approche de précision |
| TWR | Contrôle d'aérodrome |
| UAC | Contrôle en route (espace supérieur) |
| VDF | Service gonio |

### TypeEspace - Types d'espace

| Code | Signification |
|------|---------------|
| ACC | Centre de contrôle régional |
| CTA | Région de contrôle |
| CTL | Secteur de contrôle |
| CTR | Zone de contrôle |
| LTA | Région inférieure de contrôle |
| OCA | Région océanique de contrôle |
| S/CTA | CTA (militaire) |
| S/CTR | CTR (militaire) |
| TMA | Région terminale de contrôle |
| UAC | Centre de contrôle d'espace supérieur |
| UTA | Région supérieure de contrôle |
| FIR | Région d'information de vol |
| SIV | Secteur d'information de vol |
| UIR | Région supérieure d'information de vol |
| Aer | Activité de loisirs - aéromodélisme |
| Bal | Activité de loisirs - ballon captif |
| Pje | Activité de loisirs - parachutage |
| Tr Pla | Activité de loisirs - treuillage planeurs |
| Tr VL | Activité de loisirs - treuillage vol libre |
| Tr PVL | Activité de loisirs - treuillage planeurs + vol libre |
| Vol | Activité de loisirs - voltige |
| CBA | Cross-border Area |
| D | Zone dangereuse |
| P | Zone interdite |
| ZIT | Zone Interdite Temporaire permanente |
| R | Zone réglementée |
| ZRT | Zone Réglementée Temporaire permanente |
| PRN | Parcs et réserves naturels |
| SUR | Établissement portant marques d'interdiction de survol |
| NAV | Station d'aides radio hors aérodrome |

### TypeObstacle - Types d'obstacles

| Code | Signification |
|------|---------------|
| Antenne | Antenne |
| Bâtiment | Bâtiment |
| Câble | Câble |
| Centrale thermique | Centrale thermique |
| Château d'eau | Château d'eau |
| Cheminée | Cheminée |
| Derrick | Derrick |
| Église | Église |
| Éolienne(s) | Éolienne(s) |
| Grue | Grue |
| Mât | Mât |
| Phare marin | Phare marin |
| Pile de pont | Pile de pont |
| Portique | Portique |
| Pylône | Pylône |
| Silo | Silo |
| Terril | Terril |
| Torchère | Torchère |
| Tour | Tour |
| Treillis métallique | Treillis métallique |
| Autre | Autre (type précisé en observation) |

### UniteDistance - Unités de distance

| Code | Signification |
|------|---------------|
| km | Kilomètre |
| m | Mètre |
| NM | Mille marin |

### Usage - Utilisation des aides radio

| Code | Signification |
|------|---------------|
| A | Aérodrome |
| AE | Aérodrome + en route |
| E | En route |

### VorIns - Types de points de calage

| Code | Signification |
|------|---------------|
| INS | Calage inertie |
| VOR | Calage VOR |

### Wgs84 - Précision des coordonnées WGS84

| Code | Signification |
|------|---------------|
| 0 | Précision 1 seconde |
| 1 | Précision 0.1 seconde |
| 2 | Précision 0.01 seconde |
| x | Non WGS84 |

### ZoneHabitee - Environnement

| Code | Signification |
|------|---------------|
| hostile habité | Hostile habité |
| hostile inhabité | Hostile inhabité |
| non hostile | Non hostile |

---

## Notes d'utilisation pour GitHub Copilot / Claude Sonnet

Cette documentation décrit un modèle de données XML pour l'information aéronautique (SIA - Service de l'Information Aéronautique). Elle peut être utilisée pour :

1. **Générer des parsers XML** basés sur ce schéma
2. **Valider des données** conformes au modèle SiaExport v6.0
3. **Créer des requêtes** sur les entités et leurs relations
4. **Implémenter des conversions** entre formats de données aéronautiques
5. **Générer de la documentation** sur les données aéronautiques françaises

### Points clés à retenir

- Toutes les coordonnées géographiques sont en degrés décimaux
- Les altitudes peuvent être exprimées en FL, ft AMSL, ou ft ASFC
- Les relations entre entités suivent un modèle strict entité-association
- Les attributs "pk" et "lk" permettent l'identification et le traçage des éléments
- Les domaines énumérés sont exhaustifs et doivent être respectés
- Le type "contour" nécessite une résolution en géométrie pour exploitation SIG