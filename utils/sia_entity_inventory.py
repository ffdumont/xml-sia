#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service d'inventaire XML SIA - Analyse et comptage des types d'entités
Basé sur la documentation SiaExport V6.0

Ce service fait l'inventaire complet des entités présentes dans le fichier XML SIA,
les compte et les mappe avec la documentation officielle.
"""

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
import logging
from typing import Dict, List, Optional
import sys
import re
import argparse
import json
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XMLSIAInventory:
    """
    Service d'inventaire des entités XML SIA
    """
    
    def __init__(self, xml_file_path: str):
        """
        Initialise le service d'inventaire
        
        Args:
            xml_file_path: Chemin vers le fichier XML SIA à analyser
        """
        self.xml_file_path = Path(xml_file_path)
        if not self.xml_file_path.exists():
            raise FileNotFoundError(f"Le fichier {xml_file_path} n'existe pas")
        
        # Mapping des entités documentées selon SIA v6.0
        self.documented_entities = {
            'Ad': {
                'name': 'Aérodromes',
                'description': 'Aérodromes civils et militaires',
                'documented': True
            },
            'Bordure': {
                'name': 'Lignes d\'appui d\'espaces',
                'description': 'Lignes d\'appui pour description de contours d\'espaces (frontières, fleuves...)',
                'documented': True
            },
            'Cdr': {
                'name': 'Restrictions segments de route',
                'description': 'Restrictions d\'utilisation des segments de route',
                'documented': True
            },
            'DmeIls': {
                'name': 'DME d\'atterrissage',
                'description': 'DME d\'atterrissage associés aux ILS',
                'documented': True
            },
            'Espace': {
                'name': 'Espaces aériens',
                'description': 'Espaces aériens de toutes natures',
                'documented': True
            },
            'Frequence': {
                'name': 'Fréquences des services',
                'description': 'Fréquences disponibles pour les services',
                'documented': True
            },
            'Gp': {
                'name': 'Glide-path des ILS',
                'description': 'Radiophares d\'alignement de descente (glide-path) des ILS',
                'documented': True
            },
            'Helistation': {
                'name': 'Hélistations',
                'description': 'Hélistations civiles et militaires',
                'documented': True
            },
            'Ils': {
                'name': 'Localizer des ILS',
                'description': 'Radiophares d\'alignement de piste (localizer, LLZ) des ILS',
                'documented': True
            },
            'Mkr': {
                'name': 'Radiobornes des ILS',
                'description': 'Radiobornes (OM, MM, IM) des ILS',
                'documented': True
            },
            'NavFix': {
                'name': 'Points d\'appui réseau de routes',
                'description': 'Points d\'appui du réseau de routes (aides radio comprises)',
                'documented': True
            },
            'Obstacle': {
                'name': 'Obstacles',
                'description': 'Obstacles à la navigation aérienne',
                'documented': True
            },
            'Partie': {
                'name': 'Parties d\'espaces aériens',
                'description': 'Parties d\'espaces aériens',
                'documented': True
            },
            'Phare': {
                'name': 'Phares marins et feux aéronautiques',
                'description': 'Phares marins et feux aéronautiques',
                'documented': True
            },
            'RadioNav': {
                'name': 'Aides radio',
                'description': 'Aides radio (VOR, NDB, TACAN...)',
                'documented': True
            },
            'Route': {
                'name': 'Routes aériennes',
                'description': 'Routes aériennes (airways)',
                'documented': True
            },
            'Rwy': {
                'name': 'Pistes',
                'description': 'Pistes de décollage/atterrissage des aérodromes',
                'documented': True
            },
            'RwyLgt': {
                'name': 'Balisage lumineux pistes',
                'description': 'Balisage lumineux des pistes',
                'documented': True
            },
            'Segment': {
                'name': 'Segments de routes',
                'description': 'Caractéristiques d\'une route entre deux points consécutifs',
                'documented': True
            },
            'Service': {
                'name': 'Services de communications',
                'description': 'Services aux vols supportés par communications sol/air',
                'documented': True
            },
            'Territoire': {
                'name': 'Territoires',
                'description': 'Territoires où se situent les autres entités',
                'documented': True
            },
            'TwyDecDist': {
                'name': 'Réductions distance décollage',
                'description': 'Réductions de distance décollage',
                'documented': True
            },
            'Volume': {
                'name': 'Volumes d\'espaces aériens',
                'description': 'Caractéristiques du découpage vertical des espaces aériens',
                'documented': True
            },
            'VorInsChk': {
                'name': 'Points vérification VOR-INS',
                'description': 'Points de vérification VOR-INS sur les aérodromes',
                'documented': True
            }
        }
        
        self.file_info = self._get_file_info()
        logger.info(f"Fichier XML SIA chargé: {self.xml_file_path.name}")
        logger.info(f"Taille: {self.file_info['size_mb']:.2f} MB, {self.file_info['lines']} lignes")
    
    def _get_file_info(self) -> Dict:
        """Récupère les informations de base du fichier"""
        stat = self.xml_file_path.stat()
        with open(self.xml_file_path, 'r', encoding='iso-8859-1') as f:
            lines = sum(1 for _ in f)
        
        return {
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'lines': lines
        }
    
    def get_xml_header_info(self) -> Dict:
        """Récupère les informations d'en-tête du fichier XML"""
        try:
            with open(self.xml_file_path, 'r', encoding='iso-8859-1') as f:
                header_content = []
                for i, line in enumerate(f):
                    header_content.append(line)
                    if '</Situation>' in line or i > 10:
                        break
                header_xml = ''.join(header_content)
            
            # Extraction par regex pour plus de robustesse
            sia_match = re.search(r'<SiaExport[^>]*Date="([^"]*)"[^>]*Origine="([^"]*)"[^>]*Version="([^"]*)"', header_xml)
            situation_match = re.search(r'<Situation[^>]*pubDate="([^"]*)"[^>]*effDate="([^"]*)"', header_xml)
            
            return {
                'export_date': sia_match.group(1) if sia_match else 'N/A',
                'origine': sia_match.group(2) if sia_match else 'N/A',
                'version': sia_match.group(3) if sia_match else 'N/A',
                'publication_date': situation_match.group(1) if situation_match else 'N/A',
                'effective_date': situation_match.group(2) if situation_match else 'N/A'
            }
        except Exception as e:
            logger.warning(f"Impossible de parser l'en-tête XML: {e}")
            return {'error': str(e)}
    
    def scan_entities(self, max_lines: Optional[int] = None) -> Dict:
        """
        Scanne le fichier XML pour inventorier tous les types d'entités
        
        Args:
            max_lines: Limite optionnelle du nombre de lignes à scanner
            
        Returns:
            Dictionnaire avec l'inventaire complet des entités
        """
        logger.info("Début de l'inventaire des entités XML SIA...")
        
        # Compteurs
        entity_containers = Counter()  # Conteneurs (AdS, EspaceS, etc.)
        individual_entities = Counter()  # Entités individuelles
        unknown_elements = set()  # Éléments non documentés
        entity_attributes = defaultdict(set)  # entité -> {attributs}
        
        # Stack pour suivre la hiérarchie et détecter les attributs
        element_stack = []
        line_count = 0
        
        try:
            with open(self.xml_file_path, 'r', encoding='iso-8859-1') as f:
                for line_num, line in enumerate(f, 1):
                    line_count += 1
                    
                    if max_lines and line_count > max_lines:
                        logger.info(f"Arrêt de l'inventaire à la ligne {max_lines}")
                        break
                    
                    stripped_line = line.strip()
                    
                    # Traitement des balises ouvrantes
                    if stripped_line.startswith('<') and not stripped_line.startswith('</') and not stripped_line.startswith('<?'):
                        # Extraction du nom de l'élément
                        element_match = re.match(r'<(\w+)', stripped_line)
                        if element_match:
                            element_name = element_match.group(1)
                            
                            # Classification des éléments
                            if element_name.endswith('S') and len(element_name) > 1:
                                # Conteneurs d'entités
                                entity_containers[element_name] += 1
                                if not stripped_line.endswith('/>'):
                                    element_stack.append(element_name)
                            elif element_name in self.documented_entities:
                                # Entités documentées
                                individual_entities[element_name] += 1
                                if not stripped_line.endswith('/>'):
                                    element_stack.append(element_name)
                            elif element_name not in ['SiaExport', 'Situation', 'Extension', 'Geometrie'] and len(element_name) > 1:
                                # Détection des attributs d'entités
                                parent_entity = self._find_parent_entity(element_stack)
                                if parent_entity:
                                    entity_attributes[parent_entity].add(element_name)
                                else:
                                    # Éléments vraiment non classifiés
                                    unknown_elements.add(element_name)
                                
                                if not stripped_line.endswith('/>'):
                                    element_stack.append(element_name)
                    
                    # Traitement des balises fermantes
                    elif stripped_line.startswith('</'):
                        closing_element = stripped_line[2:-1].split()[0]
                        if element_stack and element_stack[-1] == closing_element:
                            element_stack.pop()
                    
                    # Affichage du progrès
                    if line_count % 50000 == 0:
                        logger.info(f"Inventaire en cours... {line_count:,} lignes traitées")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'inventaire: {e}")
            return {'error': str(e)}
        
        logger.info(f"Inventaire terminé. {line_count:,} lignes analysées")
        
        return {
            'lines_scanned': line_count,
            'entity_containers': dict(entity_containers),
            'individual_entities': dict(individual_entities),
            'unknown_elements': sorted(list(unknown_elements)),
            'entity_attributes': {k: sorted(list(v)) for k, v in entity_attributes.items()},
            'total_container_types': len(entity_containers),
            'total_individual_entity_types': len(individual_entities),
            'total_unknown_elements': len(unknown_elements),
            'total_classified_attributes': sum(len(attrs) for attrs in entity_attributes.values())
        }
    
    def _find_parent_entity(self, element_stack: List[str]) -> Optional[str]:
        """
        Trouve l'entité parente dans la pile des éléments
        """
        # Parcourir la pile de bas en haut pour trouver une entité documentée
        for element in reversed(element_stack):
            if element in self.documented_entities:
                return element
        return None
    
    def analyze_coverage(self, scan_results: Dict) -> Dict:
        """
        Analyse la couverture des entités documentées vs trouvées
        
        Args:
            scan_results: Résultats du scan des entités
            
        Returns:
            Analyse de couverture
        """
        individual_entities = scan_results.get('individual_entities', {})
        
        # Entités trouvées et documentées
        found_documented = {}
        for entity_name, count in individual_entities.items():
            if entity_name in self.documented_entities:
                found_documented[entity_name] = {
                    'count': count,
                    'info': self.documented_entities[entity_name]
                }
        
        # Entités documentées mais absentes
        missing_documented = {}
        for entity_name, info in self.documented_entities.items():
            if entity_name not in individual_entities:
                missing_documented[entity_name] = info
        
        # Entités trouvées mais non documentées  
        found_undocumented = {}
        for entity_name, count in individual_entities.items():
            if entity_name not in self.documented_entities:
                found_undocumented[entity_name] = {
                    'count': count,
                    'info': {
                        'name': 'Non documenté',
                        'description': 'Entité trouvée mais non présente dans la documentation SIA v6.0',
                        'documented': False
                    }
                }
        
        # Calculs de couverture
        total_documented = len(self.documented_entities)
        found_documented_count = len(found_documented)
        coverage_ratio = found_documented_count / total_documented if total_documented > 0 else 0
        
        return {
            'found_documented': found_documented,
            'missing_documented': missing_documented,
            'found_undocumented': found_undocumented,
            'total_documented_entities': total_documented,
            'found_documented_count': found_documented_count,
            'missing_documented_count': len(missing_documented),
            'found_undocumented_count': len(found_undocumented),
            'coverage_ratio': coverage_ratio
        }
    
    def generate_inventory_report(self, scan_results: Dict) -> str:
        """
        Génère un rapport d'inventaire détaillé
        """
        report = []
        report.append("=" * 100)
        report.append("INVENTAIRE XML SIA - TYPES D'ENTITÉS ET COUVERTURE DOCUMENTAIRE")
        report.append("=" * 100)
        report.append(f"Fichier analysé: {self.xml_file_path.name}")
        report.append(f"Lignes analysées: {scan_results.get('lines_scanned', 0):,}")
        report.append("")
        
        # Informations générales
        header_info = self.get_xml_header_info()
        report.append("INFORMATIONS GÉNÉRALES:")
        report.append("-" * 50)
        report.append(f"Version SIA: {header_info.get('version', 'N/A')}")
        report.append(f"Origine: {header_info.get('origine', 'N/A')}")
        report.append(f"Date d'export: {header_info.get('export_date', 'N/A')}")
        report.append(f"Date de publication: {header_info.get('publication_date', 'N/A')}")
        report.append(f"Date d'entrée en vigueur: {header_info.get('effective_date', 'N/A')}")
        report.append("")
        
        # Analyse de couverture
        coverage = self.analyze_coverage(scan_results)
        
        report.append("📊 SYNTHÈSE DE COUVERTURE:")
        report.append("-" * 50)
        report.append(f"Entités documentées SIA v6.0: {coverage['total_documented_entities']}")
        report.append(f"Entités documentées trouvées: {coverage['found_documented_count']}")
        report.append(f"Entités documentées manquantes: {coverage['missing_documented_count']}")
        report.append(f"Entités non documentées trouvées: {coverage['found_undocumented_count']}")
        report.append(f"Taux de couverture: {coverage['coverage_ratio']:.1%}")
        report.append("")
        
        # Entités documentées trouvées
        found_doc = coverage['found_documented']
        if found_doc:
            report.append("✅ ENTITÉS DOCUMENTÉES TROUVÉES:")
            report.append("-" * 70)
            # Tri par nombre d'occurrences décroissant
            sorted_found = sorted(found_doc.items(), key=lambda x: x[1]['count'], reverse=True)
            for entity_name, data in sorted_found:
                count = data['count']
                info = data['info']
                report.append(f"  {entity_name:15} ({count:>7,} occ.) - {info['name']}")
                report.append(f"                    └─ {info['description']}")
            report.append("")
        
        # Entités documentées manquantes
        missing_doc = coverage['missing_documented']
        if missing_doc:
            report.append("❌ ENTITÉS DOCUMENTÉES MANQUANTES:")
            report.append("-" * 70)
            for entity_name, info in sorted(missing_doc.items()):
                report.append(f"  {entity_name:15} (      0 occ.) - {info['name']}")
                report.append(f"                    └─ {info['description']}")
            report.append("")
        
        # Entités non documentées trouvées
        found_undoc = coverage['found_undocumented']
        if found_undoc:
            report.append("❓ ENTITÉS NON DOCUMENTÉES TROUVÉES:")
            report.append("-" * 70)
            # Tri par nombre d'occurrences décroissant
            sorted_undoc = sorted(found_undoc.items(), key=lambda x: x[1]['count'], reverse=True)
            for entity_name, data in sorted_undoc[:20]:  # Limiter à 20 pour la lisibilité
                count = data['count']
                report.append(f"  {entity_name:15} ({count:>7,} occ.) - Non documenté dans SIA v6.0")
            
            if len(found_undoc) > 20:
                report.append(f"  ... et {len(found_undoc) - 20} autres entités non documentées")
            report.append("")
        
        # Attributs d'entités identifiés
        entity_attributes = scan_results.get('entity_attributes', {})
        if entity_attributes:
            report.append("🔗 ATTRIBUTS D'ENTITÉS IDENTIFIÉS:")
            report.append("-" * 70)
            total_classified_attrs = 0
            for entity_name, attributes in sorted(entity_attributes.items()):
                if attributes:
                    total_classified_attrs += len(attributes)
                    # Afficher quelques attributs principaux pour chaque entité
                    attrs_sample = attributes[:8]  # Limiter à 8 attributs par entité
                    attrs_str = ', '.join(attrs_sample)
                    if len(attributes) > 8:
                        attrs_str += f" ... (+{len(attributes) - 8} autres)"
                    report.append(f"  {entity_name:15} ({len(attributes):>3} attr.) : {attrs_str}")
            
            report.append(f"\n  Total attributs classifiés: {total_classified_attrs}")
            report.append("")
        
        # Conteneurs d'entités
        containers = scan_results.get('entity_containers', {})
        if containers:
            report.append("📦 CONTENEURS D'ENTITÉS:")
            report.append("-" * 50)
            for container_name, count in sorted(containers.items()):
                entity_type = container_name[:-1] if container_name.endswith('S') else container_name
                if entity_type in self.documented_entities:
                    description = f"Conteneur de {self.documented_entities[entity_type]['name']}"
                else:
                    description = "Conteneur d'entités non documentées"
                report.append(f"  {container_name:15} ({count:>7,} occ.) - {description}")
            report.append("")
        
        # Éléments techniques non classifiés
        unknown = scan_results.get('unknown_elements', [])
        if unknown:
            report.append("🔧 ÉLÉMENTS TECHNIQUES NON CLASSIFIÉS (échantillon):")
            report.append("-" * 70)
            # Afficher seulement les 20 premiers éléments non classifiés
            for element in sorted(unknown)[:20]:
                report.append(f"  - {element}")
            if len(unknown) > 20:
                report.append(f"  ... et {len(unknown) - 20} autres éléments non classifiés")
            report.append("")
        
        # Résumé final
        report.append("📈 RÉSUMÉ FINAL:")
        report.append("-" * 50)
        total_entities = coverage['found_documented_count'] + coverage['found_undocumented_count']
        classified_attrs = scan_results.get('total_classified_attributes', 0)
        unclassified_elements = scan_results.get('total_unknown_elements', 0)
        
        report.append(f"Total types d'entités trouvées: {total_entities}")
        report.append(f"Types de conteneurs: {scan_results.get('total_container_types', 0)}")
        report.append(f"Attributs d'entités classifiés: {classified_attrs}")
        report.append(f"Éléments techniques non classifiés: {unclassified_elements}")
        report.append(f"Conformité à SIA v6.0: {coverage['coverage_ratio']:.1%}")
        
        # Calcul du pourcentage de classification
        total_technical_elements = classified_attrs + unclassified_elements
        if total_technical_elements > 0:
            classification_ratio = classified_attrs / total_technical_elements
            report.append(f"Taux de classification des éléments: {classification_ratio:.1%}")
        
        return "\n".join(report)
    
    def generate_json_report(self, scan_results: Dict) -> str:
        """
        Génère un rapport d'inventaire complet au format JSON
        
        Args:
            scan_results: Résultats du scan des entités
            
        Returns:
            Rapport JSON structuré avec tous les détails
        """
        coverage_analysis = self.analyze_coverage(scan_results)
        metadata = self.get_xml_header_info()
        
        # Construction de la structure JSON complète
        json_report = {
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "xml_file": str(self.xml_file_path),
                "file_size_mb": self.file_info['size_mb'],
                "lines_analyzed": scan_results['lines_scanned'],
                "xml_metadata": metadata
            },
            "summary": {
                "entities_documented_sia_v6": len(self.documented_entities),
                "entities_documented_found": len(coverage_analysis['found_documented']),
                "entities_documented_missing": len(coverage_analysis['missing_documented']),
                "entities_undocumented_found": len(coverage_analysis['found_undocumented']),
                "coverage_percentage": round(coverage_analysis['coverage_ratio'] * 100, 1),
                "container_types": scan_results['total_container_types'],
                "classified_attributes": scan_results['total_classified_attributes'],
                "unclassified_elements": scan_results['total_unknown_elements'],
                "classification_rate": round((scan_results['total_classified_attributes'] / 
                                           (scan_results['total_classified_attributes'] + scan_results['total_unknown_elements'])) * 100, 1) if (scan_results['total_classified_attributes'] + scan_results['total_unknown_elements']) > 0 else 100
            },
            "entities": {
                "documented_found": {},
                "documented_missing": {},
                "undocumented_found": {}
            },
            "attributes": {
                "by_entity": scan_results['entity_attributes'],
                "total_count": scan_results['total_classified_attributes'],
                "detailed_list": {}
            },
            "containers": scan_results['entity_containers'],
            "unclassified_elements": scan_results['unknown_elements']
        }
        
        # Remplissage des entités documentées trouvées
        for entity_name, data in coverage_analysis['found_documented'].items():
            json_report["entities"]["documented_found"][entity_name] = {
                "count": data['count'],
                "name": data['info']['name'],
                "description": data['info']['description'],
                "attributes": scan_results['entity_attributes'].get(entity_name, []),
                "attribute_count": len(scan_results['entity_attributes'].get(entity_name, []))
            }
        
        # Remplissage des entités documentées manquantes
        for entity_name, info in coverage_analysis['missing_documented'].items():
            json_report["entities"]["documented_missing"][entity_name] = {
                "name": info['name'],
                "description": info['description']
            }
        
        # Remplissage des entités non documentées trouvées
        for entity_name, data in coverage_analysis['found_undocumented'].items():
            json_report["entities"]["undocumented_found"][entity_name] = {
                "count": data['count'],
                "name": data['info']['name'],
                "description": data['info']['description']
            }
        
        # Index détaillé des attributs
        for entity_name, attributes in scan_results['entity_attributes'].items():
            for attr in attributes:
                if attr not in json_report["attributes"]["detailed_list"]:
                    json_report["attributes"]["detailed_list"][attr] = []
                json_report["attributes"]["detailed_list"][attr].append(entity_name)
        
        return json.dumps(json_report, indent=2, ensure_ascii=False)
    
    def generate_html_report(self, scan_results: Dict) -> str:
        """
        Génère un rapport d'inventaire complet au format HTML
        
        Args:
            scan_results: Résultats du scan des entités
            
        Returns:
            Rapport HTML avec navigation et sections collapsibles
        """
        coverage_analysis = self.analyze_coverage(scan_results)
        metadata = self.get_xml_header_info()
        
        html_parts = []
        
        # En-tête HTML avec CSS
        html_parts.append("""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventaire XML SIA - Rapport Détaillé</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #7f8c8d; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .summary-card { background: #ecf0f1; padding: 20px; border-radius: 5px; text-align: center; }
        .summary-card h3 { margin: 0 0 10px 0; color: #2c3e50; }
        .summary-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .entity-list { margin: 15px 0; }
        .entity-item { background: #f8f9fa; margin: 5px 0; padding: 15px; border-left: 4px solid #3498db; }
        .entity-name { font-weight: bold; color: #2c3e50; }
        .entity-count { color: #e74c3c; font-weight: bold; }
        .entity-description { color: #7f8c8d; font-style: italic; margin-top: 5px; }
        .attributes { margin-top: 10px; }
        .attribute-tag { display: inline-block; background: #3498db; color: white; padding: 2px 8px; margin: 2px; border-radius: 3px; font-size: 0.85em; }
        .collapsible { background-color: #3498db; color: white; cursor: pointer; padding: 15px; border: none; text-align: left; outline: none; font-size: 16px; width: 100%; margin-top: 10px; }
        .collapsible:hover { background-color: #2980b9; }
        .collapsible.active { background-color: #2980b9; }
        .content { padding: 0; max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; background-color: #f1f1f1; }
        .content.show { max-height: 1000px; padding: 15px; }
        .navigation { position: fixed; top: 20px; right: 20px; background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .navigation ul { list-style: none; padding: 0; margin: 0; }
        .navigation li { margin: 5px 0; }
        .navigation a { text-decoration: none; color: #3498db; }
        .navigation a:hover { text-decoration: underline; }
        .missing { color: #e74c3c; }
        .found { color: #27ae60; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>""")
        
        # Navigation
        html_parts.append("""
    <div class="navigation">
        <h4>Navigation</h4>
        <ul>
            <li><a href="#summary">Synthèse</a></li>
            <li><a href="#entities-found">Entités trouvées</a></li>
            <li><a href="#entities-missing">Entités manquantes</a></li>
            <li><a href="#attributes">Attributs détaillés</a></li>
            <li><a href="#containers">Conteneurs</a></li>
            <li><a href="#metadata">Métadonnées</a></li>
        </ul>
    </div>""")
        
        html_parts.append('<div class="container">')
        
        # Titre principal
        html_parts.append(f"""
    <h1>📊 Inventaire XML SIA - Rapport Détaillé</h1>
    <p><strong>Fichier analysé:</strong> {self.xml_file_path.name}</p>
    <p><strong>Lignes analysées:</strong> {scan_results['lines_scanned']:,}</p>
    <p><strong>Généré le:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>""")
        
        # Synthèse avec cartes
        html_parts.append(f"""
    <h2 id="summary">📈 Synthèse de Couverture</h2>
    <div class="summary-grid">
        <div class="summary-card">
            <h3>Taux de Couverture</h3>
            <div class="summary-value">{coverage_analysis['coverage_ratio']*100:.1f}%</div>
            <p>{len(coverage_analysis['found_documented'])}/{len(self.documented_entities)} entités documentées trouvées</p>
        </div>
        <div class="summary-card">
            <h3>Types d'Entités</h3>
            <div class="summary-value">{scan_results['total_individual_entity_types']}</div>
            <p>types d'entités identifiées</p>
        </div>
        <div class="summary-card">
            <h3>Attributs Classifiés</h3>
            <div class="summary-value">{scan_results['total_classified_attributes']}</div>
            <p>attributs d'entités identifiés</p>
        </div>
        <div class="summary-card">
            <h3>Conteneurs</h3>
            <div class="summary-value">{scan_results['total_container_types']}</div>
            <p>types de conteneurs</p>
        </div>
    </div>""")
        
        # Entités documentées trouvées
        html_parts.append(f'<h2 id="entities-found">✅ Entités Documentées Trouvées ({len(coverage_analysis["found_documented"])})</h2>')
        html_parts.append('<div class="entity-list">')
        
        for entity_name, data in sorted(coverage_analysis['found_documented'].items(), key=lambda x: x[1]['count'], reverse=True):
            attributes = scan_results['entity_attributes'].get(entity_name, [])
            attr_display = ' '.join([f'<span class="attribute-tag">{attr}</span>' for attr in attributes[:10]])
            if len(attributes) > 10:
                attr_display += f' <span class="attribute-tag">+{len(attributes)-10} autres</span>'
            
            html_parts.append(f"""
        <div class="entity-item">
            <div class="entity-name">{entity_name} <span class="entity-count">({data['count']:,} occ.)</span> - {data['info']['name']}</div>
            <div class="entity-description">{data['info']['description']}</div>
            <div class="attributes"><strong>{len(attributes)} attributs:</strong> {attr_display}</div>
        </div>""")
        
        html_parts.append('</div>')
        
        # Entités documentées manquantes
        if coverage_analysis['missing_documented']:
            html_parts.append(f'<h2 id="entities-missing">❌ Entités Documentées Manquantes ({len(coverage_analysis["missing_documented"])})</h2>')
            html_parts.append('<div class="entity-list">')
            
            for entity_name, info in coverage_analysis['missing_documented'].items():
                html_parts.append(f"""
            <div class="entity-item">
                <div class="entity-name missing">{entity_name} - {info['name']}</div>
                <div class="entity-description">{info['description']}</div>
            </div>""")
            
            html_parts.append('</div>')
        
        # Section des attributs détaillés avec sections collapsibles
        html_parts.append('<h2 id="attributes">🔗 Attributs Détaillés par Entité</h2>')
        
        for entity_name in sorted(scan_results['entity_attributes'].keys()):
            attributes = scan_results['entity_attributes'][entity_name]
            entity_info = self.documented_entities.get(entity_name, {'name': 'Non documenté', 'description': ''})
            
            html_parts.append(f"""
        <button class="collapsible">{entity_name} ({len(attributes)} attributs) - {entity_info['name']}</button>
        <div class="content">
            <p><em>{entity_info['description']}</em></p>
            <div class="attributes">""")
            
            for attr in sorted(attributes):
                html_parts.append(f'<span class="attribute-tag">{attr}</span>')
            
            html_parts.append('</div></div>')
        
        # Conteneurs
        html_parts.append(f'<h2 id="containers">📦 Conteneurs d\'Entités ({len(scan_results["entity_containers"])})</h2>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Conteneur</th><th>Occurrences</th><th>Description</th></tr>')
        
        for container_name, count in sorted(scan_results['entity_containers'].items()):
            base_entity = container_name[:-1] if container_name.endswith('S') else container_name
            entity_info = self.documented_entities.get(base_entity, {'name': 'Non documenté', 'description': ''})
            description = f"Conteneur de {entity_info['name']}"
            
            html_parts.append(f'<tr><td>{container_name}</td><td style="text-align: center;">{count}</td><td>{description}</td></tr>')
        
        html_parts.append('</table>')
        
        # Métadonnées XML
        html_parts.append('<h2 id="metadata">📋 Métadonnées du Fichier XML</h2>')
        html_parts.append('<table>')
        if metadata and 'error' not in metadata:
            for key, value in metadata.items():
                html_parts.append(f'<tr><td><strong>{key.replace("_", " ").title()}</strong></td><td>{value}</td></tr>')
        else:
            html_parts.append('<tr><td colspan="2">Métadonnées non disponibles</td></tr>')
        html_parts.append('</table>')
        
        # Script JavaScript pour les sections collapsibles
        html_parts.append("""
    <script>
        document.querySelectorAll('.collapsible').forEach(function(collapsible) {
            collapsible.addEventListener('click', function() {
                this.classList.toggle('active');
                var content = this.nextElementSibling;
                content.classList.toggle('show');
            });
        });
    </script>
</div>
</body>
</html>""")
        
        return '\n'.join(html_parts)


def main():
    """Fonction principale"""
    # Configuration des arguments en ligne de commande
    parser = argparse.ArgumentParser(
        description="Service d'inventaire XML SIA - Analyse et comptage des types d'entités",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formats de sortie:
  Par défaut (texte) : Rapport condensé lisible pour consultation rapide
  --json            : Rapport JSON structuré complet pour réutilisation programmatique
  --html            : Rapport HTML interactif avec navigation et sections collapsibles

Exemples:
  python sia_entity_inventory.py                    # Rapport texte standard
  python sia_entity_inventory.py --json             # Rapport JSON détaillé
  python sia_entity_inventory.py --html             # Rapport HTML interactif
  python sia_entity_inventory.py --json --html      # Les deux formats détaillés
        """
    )
    
    parser.add_argument('--json', action='store_true', 
                       help='Génère un rapport JSON détaillé (sia_inventory_report.json)')
    parser.add_argument('--html', action='store_true',
                       help='Génère un rapport HTML interactif (sia_inventory_report.html)')
    
    args = parser.parse_args()
    
    xml_file = Path(__file__).parent / "input" / "XML_SIA_2025-10-02.xml"
    
    if not xml_file.exists():
        print(f"ERREUR: Le fichier {xml_file} n'existe pas")
        sys.exit(1)
    
    try:
        # Initialisation du service d'inventaire
        inventory = XMLSIAInventory(str(xml_file))
        
        # Inventaire des entités
        print("Inventaire en cours du fichier XML SIA...")
        print(f"Taille du fichier: {inventory.file_info['size_mb']:.2f} MB")
        
        # Scan complet
        scan_results = inventory.scan_entities()
        
        # Génération des rapports selon les options
        reports_generated = []
        
        # Rapport texte (toujours généré, affiché seulement si pas d'autres formats)
        if not args.json and not args.html:
            report = inventory.generate_inventory_report(scan_results)
            print("\n")
            print(report)
            
            # Sauvegarde du rapport texte
            report_file = Path(__file__).parent / "sia_inventory_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            reports_generated.append(str(report_file))
        
        # Rapport JSON
        if args.json:
            json_report = inventory.generate_json_report(scan_results)
            json_file = Path(__file__).parent / "sia_inventory_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_report)
            reports_generated.append(str(json_file))
            print(f"✅ Rapport JSON détaillé généré: {json_file}")
        
        # Rapport HTML
        if args.html:
            html_report = inventory.generate_html_report(scan_results)
            html_file = Path(__file__).parent / "sia_inventory_report.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            reports_generated.append(str(html_file))
            print(f"✅ Rapport HTML interactif généré: {html_file}")
        
        # Résumé des rapports générés
        if reports_generated:
            print(f"\n📊 Résumé de l'inventaire:")
            print(f"   • {scan_results['lines_scanned']:,} lignes analysées")
            print(f"   • {scan_results['total_individual_entity_types']} types d'entités trouvées")
            print(f"   • {scan_results['total_classified_attributes']} attributs classifiés")
            print(f"   • {len(reports_generated)} rapport(s) généré(s)")
            
            for report_path in reports_generated:
                print(f"     └─ {Path(report_path).name}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'inventaire: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()