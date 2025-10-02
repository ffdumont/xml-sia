#!/usr/bin/env python3
"""
Script de vérification de cohérence entre le schéma XSD et la documentation officielle XML-SIA v6.0
Croise le fichier Espace.xsd avec input/2022-12-28 - siaexport6a.md
"""

import re
import os
from typing import Dict, List, Set, Tuple

class SiaSpecificationParser:
    """Parse la spécification SIA pour extraire les définitions d'entités"""
    
    def __init__(self, spec_file: str):
        with open(spec_file, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.entities = {}
        
    def parse_entities(self) -> Dict[str, Dict]:
        """Extrait toutes les définitions d'entités de la spécification"""
        
        # Pattern pour trouver les entités
        entity_pattern = r'### Entité: \*\*(\w+)\*\* \(([^)]+)\)'
        
        # Pattern pour les attributs
        attr_pattern = r'\| `([^`]*)`\s+([^|]+)\s+\|\s+([^|]+)\s+\|\s+([^|]+)\s+\|'
        
        entities = {}
        
        # Trouver toutes les entités
        for match in re.finditer(entity_pattern, self.content):
            entity_name = match.group(1)
            entity_desc = match.group(2)
            entity_start = match.end()
            
            # Trouver la prochaine entité ou la fin du fichier
            next_entity = re.search(r'### Entité:', self.content[entity_start:])
            if next_entity:
                entity_end = entity_start + next_entity.start()
            else:
                entity_end = len(self.content)
            
            entity_section = self.content[entity_start:entity_end]
            
            # Extraire les attributs
            attributes = {}
            for attr_match in re.finditer(attr_pattern, entity_section):
                attr_flags = attr_match.group(1).strip()
                attr_name = attr_match.group(2).strip()
                attr_domain = attr_match.group(3).strip()
                attr_desc = attr_match.group(4).strip()
                
                # Déterminer si l'attribut est obligatoire
                is_key = 'cle' in attr_flags
                is_required = '!' in attr_flags
                is_optional = '?' in attr_flags
                
                attributes[attr_name] = {
                    'domain': attr_domain,
                    'description': attr_desc,
                    'is_key': is_key,
                    'is_required': is_required,
                    'is_optional': is_optional,
                    'flags': attr_flags
                }
            
            entities[entity_name] = {
                'description': entity_desc,
                'attributes': attributes
            }
        
        return entities

class XsdParser:
    """Parse le fichier XSD pour extraire les définitions"""
    
    def __init__(self, xsd_file: str):
        with open(xsd_file, 'r', encoding='utf-8') as f:
            self.content = f.read()
    
    def extract_complex_types(self) -> Dict[str, Dict]:
        """Extrait les définitions de complexTypes du XSD"""
        
        complex_types = {}
        
        # Pattern pour les complexTypes
        type_pattern = r'<xs:complexType name="(\w+)">'
        
        for match in re.finditer(type_pattern, self.content):
            type_name = match.group(1)
            type_start = match.start()
            
            # Trouver la fin du complexType
            type_end = self.content.find('</xs:complexType>', type_start)
            if type_end == -1:
                continue
                
            type_section = self.content[type_start:type_end + len('</xs:complexType>')]
            
            # Extraire les éléments
            elements = []
            element_pattern = r'<xs:element name="(\w+)"[^>]*(?:type="([^"]*)")?[^>]*(?:minOccurs="([^"]*)")?[^>]*(?:maxOccurs="([^"]*)")?[^>]*/?>'
            
            for elem_match in re.finditer(element_pattern, type_section):
                elem_name = elem_match.group(1)
                elem_type = elem_match.group(2) or "complex"
                min_occurs = elem_match.group(3) or "1"
                max_occurs = elem_match.group(4) or "1"
                
                elements.append({
                    'name': elem_name,
                    'type': elem_type,
                    'minOccurs': min_occurs,
                    'maxOccurs': max_occurs
                })
            
            # Extraire les attributs
            attributes = []
            attr_pattern = r'<xs:attribute name="(\w+)"[^>]*(?:type="([^"]*)")?[^>]*(?:use="([^"]*)")?[^>]*/?>'
            
            for attr_match in re.finditer(attr_pattern, type_section):
                attr_name = attr_match.group(1)
                attr_type = attr_match.group(2) or "xs:string"
                attr_use = attr_match.group(3) or "optional"
                
                attributes.append({
                    'name': attr_name,
                    'type': attr_type,
                    'use': attr_use
                })
            
            complex_types[type_name] = {
                'elements': elements,
                'attributes': attributes,
                'definition': type_section
            }
        
        return complex_types

class SiaCoherenceChecker:
    """Vérificateur de cohérence entre XSD et spécification SIA"""
    
    def __init__(self, spec_file: str, xsd_file: str):
        self.spec_parser = SiaSpecificationParser(spec_file)
        self.xsd_parser = XsdParser(xsd_file)
        
        self.sia_entities = self.spec_parser.parse_entities()
        self.xsd_types = self.xsd_parser.extract_complex_types()
        
    def check_coherence(self) -> Dict[str, List[str]]:
        """Vérifie la cohérence entre XSD et spécification"""
        
        results = {
            'conformity': [],
            'missing_entities': [],
            'extra_entities': [],
            'attribute_mismatches': [],
            'structure_issues': []
        }
        
        # Entités principales à vérifier
        core_entities = ['Espace', 'Partie', 'Volume', 'Service', 'Frequence', 'Ad', 'Territoire']
        
        for entity in core_entities:
            if entity in self.sia_entities and entity in self.xsd_types:
                results['conformity'].append(f"✓ Entité {entity} présente dans XSD et spécification")
                
                # Vérifier les attributs/éléments
                sia_attrs = self.sia_entities[entity]['attributes']
                xsd_elements = {elem['name']: elem for elem in self.xsd_types[entity]['elements']}
                xsd_attributes = {attr['name']: attr for attr in self.xsd_types[entity]['attributes']}
                
                # Vérifier les correspondances
                for attr_name, attr_info in sia_attrs.items():
                    if attr_name in xsd_elements:
                        xsd_elem = xsd_elements[attr_name]
                        
                        # Vérifier si l'élément obligatoire dans SIA est bien required dans XSD
                        if attr_info['is_required'] and xsd_elem['minOccurs'] == '0':
                            results['attribute_mismatches'].append(
                                f"⚠ {entity}.{attr_name}: Obligatoire dans SIA mais optionnel dans XSD"
                            )
                        
                        # Vérifier les relations
                        self._check_relation_consistency(entity, attr_name, attr_info, xsd_elem, results)
                        
                        results['conformity'].append(f"✓ {entity}.{attr_name} correspond")
                    elif attr_name in xsd_attributes:
                        xsd_attr = xsd_attributes[attr_name]
                        
                        # Vérifier les relations pour les attributs aussi
                        self._check_relation_consistency(entity, attr_name, attr_info, xsd_attr, results)
                        
                        results['conformity'].append(f"✓ {entity}.{attr_name} défini comme attribut XSD")
                    else:
                        if not attr_info['is_optional']:
                            results['attribute_mismatches'].append(
                                f"✗ {entity}.{attr_name}: Manquant dans XSD (requis dans SIA)"
                            )
                
            elif entity in self.sia_entities:
                results['missing_entities'].append(f"✗ Entité {entity} manquante dans XSD")
            elif entity in self.xsd_types:
                results['extra_entities'].append(f"? Entité {entity} dans XSD mais pas dans spéc de base")
        
        return results
    
    def _check_relation_consistency(self, entity_name: str, attr_name: str, attr_info: Dict, 
                                  xsd_item: Dict, results: Dict[str, List[str]]):
        """Vérifie la cohérence des relations SIA vs XSD"""
        
        domain = attr_info['domain'].strip()
        
        # Détecter si c'est une relation
        relation_match = re.match(r'relation\((\w+)\)', domain)
        if relation_match:
            target_entity = relation_match.group(1)
            
            # Pour un élément XSD
            if 'type' in xsd_item:
                xsd_type = xsd_item['type']
                
                # Vérifier que le type XSD correspond à l'entité cible
                if xsd_type == f"{target_entity}RefType":
                    results['conformity'].append(
                        f"✓ {entity_name}.{attr_name}: Relation vers {target_entity} correctement typée"
                    )
                elif xsd_type == "xs:string" and xsd_item.get('name') in ['pk', 'lk']:
                    # Référence par clé primaire ou logique - acceptable
                    results['conformity'].append(
                        f"✓ {entity_name}.{attr_name}: Référence {target_entity} par clé"
                    )
                else:
                    # Vérifier si c'est un attribut pk/lk qui référence
                    if any(attr.get('name') == 'pk' for attr in self.xsd_types.get(entity_name, {}).get('attributes', [])):
                        results['conformity'].append(
                            f"✓ {entity_name}.{attr_name}: Relation {target_entity} avec attributs pk/lk"
                        )
                    else:
                        results['attribute_mismatches'].append(
                            f"⚠ {entity_name}.{attr_name}: Relation vers {target_entity} mal typée "
                            f"(XSD: {xsd_type}, attendu: {target_entity}RefType ou pk/lk)"
                        )
            
            # Vérifier que l'entité cible existe
            if target_entity not in self.xsd_types:
                results['structure_issues'].append(
                    f"❌ {entity_name}.{attr_name}: Relation vers {target_entity} mais entité inexistante dans XSD"
                )
        
        # Détecter les relations multiples (ex: "relation(Service)*")
        multi_relation_match = re.match(r'relation\((\w+)\)\*', domain)
        if multi_relation_match:
            target_entity = multi_relation_match.group(1)
            
            if 'maxOccurs' in xsd_item and xsd_item['maxOccurs'] == 'unbounded':
                results['conformity'].append(
                    f"✓ {entity_name}.{attr_name}: Relation multiple vers {target_entity} correctement définie"
                )
            else:
                results['attribute_mismatches'].append(
                    f"⚠ {entity_name}.{attr_name}: Relation multiple vers {target_entity} "
                    f"mais maxOccurs≠unbounded dans XSD"
                )
    
    def print_report(self):
        """Affiche le rapport de cohérence"""
        
        results = self.check_coherence()
        
        print("="*80)
        print("RAPPORT DE COHÉRENCE XSD vs SPÉCIFICATION SIA v6.0")
        print("="*80)
        
        print(f"\n📋 ENTITÉS SIA ANALYSÉES: {len(self.sia_entities)}")
        for name, info in self.sia_entities.items():
            print(f"  - {name}: {info['description']} ({len(info['attributes'])} attributs)")
        
        print(f"\n🔧 TYPES XSD DÉFINIS: {len(self.xsd_types)}")
        for name, info in self.xsd_types.items():
            elem_count = len(info['elements'])
            attr_count = len(info['attributes'])
            print(f"  - {name}: {elem_count} éléments, {attr_count} attributs")
        
        print(f"\n✅ CONFORMITÉS ({len(results['conformity'])})")
        for item in results['conformity']:
            print(f"  {item}")
        
        if results['missing_entities']:
            print(f"\n❌ ENTITÉS MANQUANTES ({len(results['missing_entities'])}):")
            for item in results['missing_entities']:
                print(f"  {item}")
        
        if results['extra_entities']:
            print(f"\n➕ ENTITÉS SUPPLÉMENTAIRES ({len(results['extra_entities'])}):")
            for item in results['extra_entities']:
                print(f"  {item}")
        
        if results['attribute_mismatches']:
            print(f"\n⚠️  DIVERGENCES ATTRIBUTS ({len(results['attribute_mismatches'])}):")
            for item in results['attribute_mismatches']:
                print(f"  {item}")
        
        if results['structure_issues']:
            print(f"\n🔗 PROBLÈMES STRUCTURELS ({len(results['structure_issues'])}):")
            for item in results['structure_issues']:
                print(f"  {item}")
        
        # Analyse spécifique des relations
        self._print_relations_analysis()
        
        # Analyse détaillée des entités principales
        print(f"\n📊 ANALYSE DÉTAILLÉE DES ENTITÉS PRINCIPALES")
        print("-" * 60)
        
        core_entities = ['Espace', 'Partie', 'Volume', 'Service', 'Frequence']
        
        for entity in core_entities:
            if entity in self.sia_entities:
                print(f"\n🔍 {entity.upper()}")
                sia_entity = self.sia_entities[entity]
                print(f"   Description SIA: {sia_entity['description']}")
                
                if entity in self.xsd_types:
                    xsd_type = self.xsd_types[entity]
                    print(f"   XSD: {len(xsd_type['elements'])} éléments, {len(xsd_type['attributes'])} attributs")
                    
                    # Détail des attributs obligatoires
                    required_attrs = [name for name, info in sia_entity['attributes'].items() 
                                    if info['is_required'] or info['is_key']]
                    if required_attrs:
                        print(f"   Attributs SIA obligatoires: {', '.join(required_attrs)}")
                else:
                    print(f"   ❌ Pas de définition XSD correspondante")
        
        print(f"\n" + "="*80)
    
    def _print_relations_analysis(self):
        """Analyse détaillée des relations dans la spécification SIA"""
        
        print(f"\n🔗 ANALYSE DES RELATIONS SIA")
        print("-" * 60)
        
        relations_found = {}
        
        # Parcourir toutes les entités pour trouver les relations
        for entity_name, entity_info in self.sia_entities.items():
            for attr_name, attr_info in entity_info['attributes'].items():
                domain = attr_info['domain'].strip()
                
                # Relations simples
                relation_match = re.match(r'relation\((\w+)\)', domain)
                if relation_match:
                    target_entity = relation_match.group(1)
                    if entity_name not in relations_found:
                        relations_found[entity_name] = []
                    relations_found[entity_name].append({
                        'attribute': attr_name,
                        'target': target_entity,
                        'type': 'simple',
                        'required': attr_info['is_required'] or attr_info['is_key']
                    })
                
                # Relations multiples
                multi_relation_match = re.match(r'relation\((\w+)\)\*', domain)
                if multi_relation_match:
                    target_entity = multi_relation_match.group(1)
                    if entity_name not in relations_found:
                        relations_found[entity_name] = []
                    relations_found[entity_name].append({
                        'attribute': attr_name,
                        'target': target_entity,
                        'type': 'multiple',
                        'required': attr_info['is_required'] or attr_info['is_key']
                    })
        
        if relations_found:
            print(f"\n📊 Relations détectées dans la spécification SIA :")
            for entity, relations in relations_found.items():
                print(f"\n   {entity.upper()} :")
                for rel in relations:
                    req_marker = " (obligatoire)" if rel['required'] else " (optionnel)"
                    type_marker = "→*" if rel['type'] == 'multiple' else "→"
                    print(f"     {rel['attribute']} {type_marker} {rel['target']}{req_marker}")
                    
                    # Vérifier la cohérence XSD
                    if entity in self.xsd_types:
                        xsd_elements = {elem['name']: elem for elem in self.xsd_types[entity]['elements']}
                        xsd_attributes = {attr['name']: attr for attr in self.xsd_types[entity]['attributes']}
                        
                        if rel['attribute'] in xsd_elements:
                            xsd_elem = xsd_elements[rel['attribute']]
                            if rel['type'] == 'multiple' and xsd_elem.get('maxOccurs') != 'unbounded':
                                print(f"       ⚠ XSD: maxOccurs devrait être 'unbounded'")
                            elif xsd_elem.get('type') == f"{rel['target']}RefType":
                                print(f"       ✓ XSD: Correctement typé comme {rel['target']}RefType")
                            elif 'pk' in [a['name'] for a in self.xsd_types[entity]['attributes']]:
                                print(f"       ✓ XSD: Référence par pk/lk")
                            else:
                                print(f"       ? XSD: Type {xsd_elem.get('type', 'inconnu')}")
        else:
            print("   Aucune relation détectée dans la spécification")

def main():
    """Point d'entrée principal"""
    
    spec_file = "input/2022-12-28 - siaexport6a.md"
    xsd_file = "output/Espace.xsd"
    
    if not os.path.exists(spec_file):
        print(f"❌ Fichier de spécification non trouvé: {spec_file}")
        return
    
    if not os.path.exists(xsd_file):
        print(f"❌ Fichier XSD non trouvé: {xsd_file}")
        return
    
    checker = SiaCoherenceChecker(spec_file, xsd_file)
    checker.print_report()

if __name__ == '__main__':
    main()