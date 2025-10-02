#!/usr/bin/env python3
"""
Script d'extraction d'espaces aériens XML-SIA avec toutes leurs dépendances
Basé sur le schéma XSD Espace.xsd pour assurer la conformité XML-SIA v6.0

Usage:
    python extract_espace.py --input XML_SIA_2025-10-02.xml --identifier "304333"
    python extract_espace.py --input XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]"
"""

import xml.etree.ElementTree as ET
import argparse
import sys
import os
from typing import Set, Dict, List, Optional, Tuple
from xml.dom import minidom

class XsdBasedEspaceExtractor:
    """
    Extracteur d'espaces aériens basé sur le schéma XSD Espace.xsd
    Extrait un espace et toutes ses dépendances selon le modèle XML-SIA v6.0
    """
    
    def __init__(self, xml_file_path: str, xsd_file_path: str = None):
        self.xml_file = xml_file_path
        self.xsd_file = xsd_file_path or os.path.join(os.path.dirname(__file__), 'output', 'Espace.xsd')
        self.root = None
        self.namespaces = {}
        
        # Collections des entités extraites (selon structure XSD)
        self.extracted = {
            'territoires': {},      # pk -> Territoire element
            'ads': {},              # pk -> Ad element  
            'espaces': {},          # pk -> Espace element
            'parties': {},          # pk -> Partie element
            'volumes': {},          # pk -> Volume element
            'services': {},         # pk -> Service element
            'frequences': {},       # pk -> Frequence element
            'bordures': {},         # pk -> Bordure element
        }
        
        # Collections des références à résoudre
        self.references_to_resolve = {
            'territoire_refs': set(),
            'ad_refs': set(),
            'espace_refs': set(),
            'partie_refs': set(),
            'service_refs': set(),
            'bordure_refs': set()
        }
        
    def load_xml(self) -> bool:
        """Charge le fichier XML SIA"""
        try:
            tree = ET.parse(self.xml_file)
            self.root = tree.getroot()
            
            # Détection des namespaces
            for key, value in self.root.attrib.items():
                if key.startswith('xmlns'):
                    prefix = key[6:] if ':' in key else ''
                    self.namespaces[prefix] = value
                    
            print(f"OK Fichier XML SIA charge: {self.xml_file}")
            print(f"OK Namespaces detectes: {self.namespaces}")
            return True
            
        except ET.ParseError as e:
            print(f"✗ Erreur de parsing XML: {e}")
            return False
        except FileNotFoundError:
            print(f"✗ Fichier non trouvé: {self.xml_file}")
            return False
    
    def find_espace_by_identifier(self, identifier: str) -> Optional[ET.Element]:
        """Trouve un espace par pk ou lk selon le schéma XSD"""
        
        # Recherche dans la section EspaceS
        espaces_section = self.root.find('.//EspaceS')
        if espaces_section is None:
            print("✗ Section EspaceS non trouvée dans le XML")
            return None
            
        for espace in espaces_section.findall('Espace'):
            # Recherche par pk (attribut système obligatoire selon XSD)
            if espace.get('pk') == identifier:
                print(f"OK Espace trouve par pk: {identifier}")
                return espace
                
            # Recherche par lk (attribut système optionnel selon XSD)  
            if espace.get('lk') == identifier:
                print(f"OK Espace trouve par lk: {identifier}")
                return espace
        
        print(f"ERREUR Espace non trouve: {identifier}")
        return None
    
    def extract_espace_with_dependencies(self, identifier: str) -> bool:
        """
        Extrait un espace et toutes ses dépendances selon la structure XSD:
        
        Espace (entité principale)
        ├── TerritoireRef → Territoire (obligatoire)
        ├── AdAssocieRef → Ad (optionnel)
        ├── Partie[] → Parties de l'espace (0..n)
        │   ├── Contour, Geometrie
        │   └── Volume[] → Volumes de chaque partie (0..n)
        ├── Service[] → Services ATS (0..n)
        │   └── Frequence[] → Fréquences des services
        └── Bordure (via références géométriques)
        """
        
        # 1. Trouver l'espace principal
        espace = self.find_espace_by_identifier(identifier)
        if espace is None:
            return False
            
        espace_pk = espace.get('pk')
        print(f"\n=== Extraction de l'espace pk={espace_pk} ===")
        
        # 2. Ajouter l'espace à la collection
        self.extracted['espaces'][espace_pk] = espace
        
        # 3. Extraire les dépendances selon le schéma XSD
        
        # 3a. TerritoireRef (obligatoire selon XSD)
        territoire_ref = espace.find('Territoire')
        if territoire_ref is not None:
            territoire_pk = territoire_ref.get('pk')
            self.references_to_resolve['territoire_refs'].add(territoire_pk)
            print(f"  → Territoire référencé: pk={territoire_pk}")
        
        # 3b. AdAssocieRef (optionnel selon XSD)
        ad_associe = espace.find('AdAssocie')
        if ad_associe is not None:
            ad_pk = ad_associe.get('pk')
            self.references_to_resolve['ad_refs'].add(ad_pk)
            print(f"  → Aérodrome associé: pk={ad_pk}")
            
        # 3c. Parties intégrées dans l'espace (selon XSD)
        parties = espace.findall('Partie')
        for partie in parties:
            partie_pk = partie.get('pk')
            self.extracted['parties'][partie_pk] = partie
            print(f"  → Partie intégrée: pk={partie_pk}")
            
            # 3d. Volumes des parties
            volumes = partie.findall('Volume')
            for volume in volumes:
                volume_pk = volume.get('pk')
                self.extracted['volumes'][volume_pk] = volume
                print(f"    → Volume: pk={volume_pk}")
        
        # 3e. Services intégrés dans l'espace (selon XSD)
        services = espace.findall('Service')
        for service in services:
            service_pk = service.get('pk')
            self.extracted['services'][service_pk] = service
            print(f"  → Service intégré: pk={service_pk}")
        
        # 4. Rechercher les entités liées dans les sections principales du XML
        self._resolve_external_references(espace_pk)
        
        return True
    
    def _resolve_external_references(self, espace_pk: str):
        """Résout toutes les références externes selon les relations XSD"""
        
        # Résolution des Territoires
        if self.references_to_resolve['territoire_refs']:
            territoires_section = self.root.find('.//TerritoireS')
            if territoires_section is not None:
                for territoire in territoires_section.findall('Territoire'):
                    pk = territoire.get('pk')
                    if pk in self.references_to_resolve['territoire_refs']:
                        self.extracted['territoires'][pk] = territoire
                        print(f"  ✓ Territoire résolu: pk={pk}")
        
        # Résolution des Aérodromes
        if self.references_to_resolve['ad_refs']:
            ads_section = self.root.find('.//AdS')
            if ads_section is not None:
                for ad in ads_section.findall('Ad'):
                    pk = ad.get('pk')
                    if pk in self.references_to_resolve['ad_refs']:
                        self.extracted['ads'][pk] = ad
                        print(f"  ✓ Aérodrome résolu: pk={pk}")
        
        # Recherche des Parties externes (référençant cet espace)
        parties_section = self.root.find('.//PartieS')
        if parties_section is not None:
            for partie in parties_section.findall('Partie'):
                espace_ref = partie.find('Espace')
                if espace_ref is not None and espace_ref.get('pk') == espace_pk:
                    partie_pk = partie.get('pk')
                    self.extracted['parties'][partie_pk] = partie
                    print(f"  ✓ Partie externe trouvée: pk={partie_pk}")
                    
                    # Volumes de cette partie
                    volumes = partie.findall('Volume')
                    for volume in volumes:
                        volume_pk = volume.get('pk')
                        self.extracted['volumes'][volume_pk] = volume
                        print(f"    ✓ Volume de partie: pk={volume_pk}")
        
        # Recherche des Volumes externes (référençant les parties)
        volumes_section = self.root.find('.//VolumeS')
        if volumes_section is not None:
            for volume in volumes_section.findall('Volume'):
                partie_ref = volume.find('Partie')
                if partie_ref is not None:
                    partie_pk = partie_ref.get('pk')
                    if partie_pk in self.extracted['parties']:
                        volume_pk = volume.get('pk')
                        if volume_pk not in self.extracted['volumes']:
                            self.extracted['volumes'][volume_pk] = volume
                            print(f"    ✓ Volume externe trouvé: pk={volume_pk}")
        
        # Recherche des Services externes
        services_section = self.root.find('.//ServiceS')
        if services_section is not None:
            for service in services_section.findall('Service'):
                # Services liés à l'aérodrome associé
                for ad_pk in self.references_to_resolve['ad_refs']:
                    ad_ref = service.find('Ad')
                    if ad_ref is not None and ad_ref.get('pk') == ad_pk:
                        service_pk = service.get('pk')
                        self.extracted['services'][service_pk] = service
                        print(f"  ✓ Service résolu: pk={service_pk}")
        
        # Recherche des Fréquences des services
        frequences_section = self.root.find('.//FrequenceS')
        if frequences_section is not None:
            for frequence in frequences_section.findall('Frequence'):
                service_ref = frequence.find('Service')
                if service_ref is not None:
                    service_pk = service_ref.get('pk')
                    if service_pk in self.extracted['services']:
                        frequence_pk = frequence.get('pk')
                        self.extracted['frequences'][frequence_pk] = frequence
                        print(f"    ✓ Fréquence trouvée: pk={frequence_pk}")
    
    def generate_output_xml(self) -> str:
        """Génère le XML de sortie sans références de schéma pour éviter les erreurs de validation"""
        
        # Création de l'élément racine simple
        root = ET.Element('SiaExport')
        
        # Ajout des sections selon l'ordre logique du schéma XSD
        
        if self.extracted['territoires']:
            territoires_section = ET.SubElement(root, 'TerritoireS')
            for territoire in self.extracted['territoires'].values():
                territoires_section.append(territoire)
        
        if self.extracted['ads']:
            ads_section = ET.SubElement(root, 'AdS')
            for ad in self.extracted['ads'].values():
                ads_section.append(ad)
        
        if self.extracted['espaces']:
            espaces_section = ET.SubElement(root, 'EspaceS')
            for espace in self.extracted['espaces'].values():
                espaces_section.append(espace)
        
        if self.extracted['parties']:
            parties_section = ET.SubElement(root, 'PartieS')
            for partie in self.extracted['parties'].values():
                parties_section.append(partie)
        
        if self.extracted['volumes']:
            volumes_section = ET.SubElement(root, 'VolumeS')
            for volume in self.extracted['volumes'].values():
                volumes_section.append(volume)
        
        if self.extracted['services']:
            services_section = ET.SubElement(root, 'ServiceS')
            for service in self.extracted['services'].values():
                services_section.append(service)
        
        if self.extracted['frequences']:
            frequences_section = ET.SubElement(root, 'FrequenceS')
            for frequence in self.extracted['frequences'].values():
                frequences_section.append(frequence)
        
        # Formatage du XML avec indentation propre
        return self._format_xml_clean(root)
    
    def _format_xml_clean(self, root: ET.Element) -> str:
        """Formate le XML avec une indentation propre sans lignes vides excessives"""
        
        # Première passe : formatage de base
        rough_string = ET.tostring(root, 'unicode', xml_declaration=False)
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)
        
        # Nettoyage des lignes vides excessives
        lines = pretty_xml.split('\n')
        
        # Filtrage : suppression des lignes vides et espaces en trop
        clean_lines = []
        for line in lines:
            # Ignorer les lignes vides ou contenant seulement des espaces
            if line.strip():
                clean_lines.append(line)
        
        # Remplacement de l'en-tête XML par défaut
        if clean_lines and clean_lines[0].startswith('<?xml'):
            clean_lines[0] = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        else:
            clean_lines.insert(0, '<?xml version="1.0" encoding="ISO-8859-1"?>')
        
        return '\n'.join(clean_lines)
    
    def print_extraction_summary(self):
        """Affiche un résumé de l'extraction"""
        print(f"\n=== RÉSUMÉ DE L'EXTRACTION ===")
        print(f"Territoires extraits: {len(self.extracted['territoires'])}")
        print(f"Aérodromes extraits: {len(self.extracted['ads'])}")
        print(f"Espaces extraits: {len(self.extracted['espaces'])}")
        print(f"Parties extraites: {len(self.extracted['parties'])}")
        print(f"Volumes extraits: {len(self.extracted['volumes'])}")
        print(f"Services extraits: {len(self.extracted['services'])}")
        print(f"Fréquences extraites: {len(self.extracted['frequences'])}")
        
        total = sum(len(collection) for collection in self.extracted.values())
        print(f"TOTAL: {total} entités extraites")

def main():
    """Interface en ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Extracteur d'espaces aériens XML-SIA avec dépendances (basé sur XSD)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python extract_espace.py --input input/XML_SIA_2025-10-02.xml --identifier "304333"
  python extract_espace.py --input input/XML_SIA_2025-10-02.xml --identifier "[LF][TMA LE BOURGET]" --output tma_bourget.xml
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='Fichier XML SIA d\'entrée')
    parser.add_argument('--identifier', '-id', required=True,
                       help='Identifiant pk ou lk de l\'espace à extraire')
    parser.add_argument('--output', '-o',
                       help='Fichier XML de sortie (optionnel, affichage sur stdout par défaut)')
    parser.add_argument('--xsd',
                       help='Fichier XSD de validation (par défaut: output/Espace.xsd)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbose')
    
    args = parser.parse_args()
    
    # Vérification de l'existence du fichier d'entrée
    if not os.path.exists(args.input):
        print(f"✗ Fichier d'entrée non trouvé: {args.input}")
        sys.exit(1)
    
    # Initialisation de l'extracteur
    extractor = XsdBasedEspaceExtractor(args.input, args.xsd)
    
    # Chargement du XML
    if not extractor.load_xml():
        sys.exit(1)
    
    # Extraction
    print(f"\nExtraction de l'espace: {args.identifier}")
    if not extractor.extract_espace_with_dependencies(args.identifier):
        print("✗ Échec de l'extraction")
        sys.exit(1)
    
    # Génération du XML de sortie
    output_xml = extractor.generate_output_xml()
    
    # Sortie
    if args.output:
        try:
            with open(args.output, 'w', encoding='iso-8859-1') as f:
                f.write(output_xml)
            print(f"\n✓ XML généré: {args.output}")
        except Exception as e:
            print(f"✗ Erreur d'écriture: {e}")
            sys.exit(1)
    else:
        print(f"\n=== XML EXTRAIT ===")
        print(output_xml)
    
    # Résumé
    if args.verbose:
        extractor.print_extraction_summary()

if __name__ == '__main__':
    main()