#!/usr/bin/env python3
"""
Service de listing et recherche d'entités XML-SIA avec filtrage avancé
Liste et filtre les entités depuis le fichier XML ou la base SQLite

Usage:
    # Lister tous les espaces TMA
    python list_entities.py --type espace --space-type TMA
    
    # Rechercher par mot-clé dans les identifiants lk
    python list_entities.py --keyword "BOURGET" --source database
    
    # Lister les espaces de classe D
    python list_entities.py --type espace --space-class D
    
    # Combiner les filtres
    python list_entities.py --type espace --space-type TMA --keyword "PARIS" --max-results 10
"""

import sqlite3
import argparse
import sys
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import re

@dataclass
class SearchResult:
    """Résultat de recherche structuré"""
    entity_type: str    # Type d'entité (territoire, aerodrome, espace, etc.)
    pk: int            # Clé primaire
    lk: str            # Clé logique (attribut lk)
    source: str        # Source: 'database' ou 'xml'
    
    def __str__(self):
        return f"{self.entity_type:<12} | PK:{self.pk:<8} | {self.lk}"
    
    def format_with_source(self, show_source: bool = False):
        """Format avec ou sans indication de source"""
        if show_source:
            source_indicator = "DB" if self.source == "database" else "XML"
            return f"{self.entity_type:<12} | PK:{self.pk:<8} | [{source_indicator:>3}] | {self.lk}"
        else:
            return str(self)

class EntitySearchService:
    """
    Service de recherche d'entités XML-SIA par mot-clé
    Supporte la recherche dans la base SQLite et/ou le fichier XML
    """
    
    def __init__(self, database_path: str = 'sia_database.db', xml_file_path: str = None):
        self.database_path = database_path
        self.xml_file_path = xml_file_path
        self.db_connection = None
        
        # Mapping des entités et leurs tables/sections
        self.entity_mapping = {
            'database': {
                'territoire': 'territoires',
                'aerodrome': 'aerodromes', 
                'espace': 'espaces',
                'partie': 'parties',
                'volume': 'volumes',
                'service': 'services',
                'frequence': 'frequences'
            },
            'xml': {
                'territoire': './/TerritoireS/Territoire',
                'aerodrome': './/AdS/Ad',
                'espace': './/EspaceS/Espace', 
                'partie': './/PartieS/Partie',
                'volume': './/VolumeS/Volume',
                'service': './/ServiceS/Service',
                'frequence': './/FrequenceS/Frequence'
            }
        }
    
    def connect_database(self) -> bool:
        """Se connecte à la base de données SQLite"""
        try:
            if not os.path.exists(self.database_path):
                print(f"✗ Base de données non trouvée: {self.database_path}")
                return False
            
            self.db_connection = sqlite3.connect(self.database_path)
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Erreur de connexion SQLite: {e}")
            return False
    
    def close_connection(self):
        """Ferme la connexion à la base de données"""
        if self.db_connection:
            self.db_connection.close()
    
    def search_in_database(self, keyword: str, case_sensitive: bool = False) -> List[SearchResult]:
        """
        Recherche par mot-clé dans la base de données SQLite
        
        Args:
            keyword: Mot-clé à rechercher dans les attributs lk
            case_sensitive: Recherche sensible à la casse
        
        Returns:
            Liste des résultats de recherche
        """
        if not self.connect_database():
            return []
        
        results = []
        cursor = self.db_connection.cursor()
        
        try:
            # Rechercher dans chaque table
            for entity_type, table_name in self.entity_mapping['database'].items():
                if case_sensitive:
                    query = f"SELECT pk, lk FROM {table_name} WHERE lk LIKE ? AND lk IS NOT NULL"
                    search_pattern = f"%{keyword}%"
                else:
                    query = f"SELECT pk, lk FROM {table_name} WHERE LOWER(lk) LIKE LOWER(?) AND lk IS NOT NULL"
                    search_pattern = f"%{keyword}%"
                
                cursor.execute(query, (search_pattern,))
                
                for row in cursor.fetchall():
                    pk, lk = row
                    results.append(SearchResult(
                        entity_type=entity_type,
                        pk=pk,
                        lk=lk,
                        source='database'
                    ))
        
        except sqlite3.Error as e:
            print(f"✗ Erreur de recherche dans la base: {e}")
        
        finally:
            self.close_connection()
        
        return results
    
    def search_in_xml(self, keyword: str, case_sensitive: bool = False) -> List[SearchResult]:
        """
        Recherche par mot-clé dans le fichier XML
        
        Args:
            keyword: Mot-clé à rechercher dans les attributs lk
            case_sensitive: Recherche sensible à la casse
        
        Returns:
            Liste des résultats de recherche
        """
        if not self.xml_file_path or not os.path.exists(self.xml_file_path):
            print(f"✗ Fichier XML non trouvé: {self.xml_file_path}")
            return []
        
        results = []
        
        try:
            # Parser le fichier XML
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            # Rechercher dans chaque type d'entité
            for entity_type, xpath in self.entity_mapping['xml'].items():
                elements = root.findall(xpath)
                
                for element in elements:
                    pk = element.get('pk')
                    lk = element.get('lk')
                    
                    if pk and lk:
                        # Vérifier si le mot-clé correspond
                        if case_sensitive:
                            match = keyword in lk
                        else:
                            match = keyword.lower() in lk.lower()
                        
                        if match:
                            results.append(SearchResult(
                                entity_type=entity_type,
                                pk=int(pk),
                                lk=lk,
                                source='xml'
                            ))
        
        except ET.ParseError as e:
            print(f"✗ Erreur de parsing XML: {e}")
        except Exception as e:
            print(f"✗ Erreur lors de la recherche XML: {e}")
        
        return results
    
    def search(self, keyword: str, source: str = 'database', case_sensitive: bool = False) -> List[SearchResult]:
        """
        Recherche par mot-clé dans la source spécifiée
        
        Args:
            keyword: Mot-clé à rechercher
            source: Source de recherche ('database', 'xml', ou 'both')
            case_sensitive: Recherche sensible à la casse
        
        Returns:
            Liste des résultats de recherche triés
        """
        results = []
        
        if source in ['database', 'both']:
            db_results = self.search_in_database(keyword, case_sensitive)
            results.extend(db_results)
        
        if source in ['xml', 'both']:
            xml_results = self.search_in_xml(keyword, case_sensitive)
            results.extend(xml_results)
        
        # Trier les résultats par type d'entité puis par lk
        results.sort(key=lambda r: (r.entity_type, r.lk))
        
        return results
    
    def search_and_display(self, keyword: str, source: str = 'database', 
                          case_sensitive: bool = False, max_results: int = None) -> bool:
        """
        Recherche et affiche les résultats formatés
        
        Args:
            keyword: Mot-clé à rechercher
            source: Source de recherche 
            case_sensitive: Recherche sensible à la casse
            max_results: Nombre maximum de résultats à afficher
        
        Returns:
            True si des résultats ont été trouvés
        """
        print(f"🔍 Recherche de '{keyword}' dans {source}")
        print(f"   Sensible à la casse: {'Oui' if case_sensitive else 'Non'}")
        print("=" * 80)
        
        results = self.search(keyword, source, case_sensitive)
        
        if not results:
            print("❌ Aucun résultat trouvé")
            return False
        
        # Limiter les résultats si demandé
        display_results = results[:max_results] if max_results else results
        
        # Afficher les résultats par type
        show_source = (source == 'both')
        current_type = None
        for result in display_results:
            if result.entity_type != current_type:
                current_type = result.entity_type
                print(f"\n📁 {current_type.upper()}S:")
            
            print(f"   {result.format_with_source(show_source)}")
        
        # Résumé
        print(f"\n📊 Résumé:")
        total_shown = len(display_results)
        total_found = len(results)
        
        if max_results and total_found > max_results:
            print(f"   Affichés: {total_shown}/{total_found} résultats")
        else:
            print(f"   Total: {total_found} résultat(s) trouvé(s)")
        
        # Comptage par type d'entité
        by_type = {}
        for result in results:
            by_type[result.entity_type] = by_type.get(result.entity_type, 0) + 1
        
        print("   Répartition par type:")
        for entity_type, count in sorted(by_type.items()):
            print(f"     {entity_type}: {count}")
        
        return True
    
    def search_and_display_filtered(self, keyword: str, entity_type_filter: str = None,
                                   space_type_filter: str = None, space_class_filter: str = None,
                                   source: str = 'database', case_sensitive: bool = False, 
                                   max_results: int = None) -> bool:
        """
        Recherche par mot-clé avec filtrage par type d'entité et autres filtres
        
        Args:
            keyword: Mot-clé à rechercher
            entity_type_filter: Type d'entité à filtrer (ex: 'espace')
            space_type_filter: Filtre sur le type d'espace (ex: TMA, CTR)
            space_class_filter: Filtre sur la classe d'espace (A, B, C, D, E)
            source: Source de recherche 
            case_sensitive: Recherche sensible à la casse
            max_results: Nombre maximum de résultats à afficher
        
        Returns:
            True si des résultats ont été trouvés
        """
        print(f"🔍 Recherche de '{keyword}' dans {source}")
        if entity_type_filter:
            print(f"   Filtré par type: {entity_type_filter}")
        if space_type_filter:
            print(f"   Filtre type d'espace: {space_type_filter}")
        if space_class_filter:
            print(f"   Filtre classe: {space_class_filter}")
        print(f"   Sensible à la casse: {'Oui' if case_sensitive else 'Non'}")
        print("=" * 80)
        
        # Recherche de base par mot-clé
        results = self.search(keyword, source, case_sensitive)
        
        if not results:
            print("❌ Aucun résultat trouvé")
            return False
        
        # Filtrage par type d'entité
        if entity_type_filter:
            results = [r for r in results if r.entity_type == entity_type_filter]
        
        # Filtrage spécifique aux espaces
        if entity_type_filter == 'espace' and (space_type_filter or space_class_filter):
            filtered_results = []
            for result in results:
                details = self._get_space_details(result.pk, result.source)
                if details:
                    # Filtre par type d'espace
                    if space_type_filter and details.get('type_espace') != space_type_filter:
                        continue
                    # Filtre par classe d'espace
                    if space_class_filter and details.get('classe') != space_class_filter:
                        continue
                    filtered_results.append(result)
            results = filtered_results
        
        if not results:
            print("❌ Aucun résultat après filtrage")
            return False
        
        # Limiter les résultats si demandé
        display_results = results[:max_results] if max_results else results
        
        # Afficher les résultats par type
        show_source = (source == 'both')
        current_type = None
        for result in display_results:
            if result.entity_type != current_type:
                current_type = result.entity_type
                print(f"\n📁 {current_type.upper()}S:")
            
            print(f"   {result.format_with_source(show_source)}")
        
        # Résumé
        print(f"\n📊 Résumé:")
        total_shown = len(display_results)
        total_found = len(results)
        
        if max_results and total_found > max_results:
            print(f"   Affichés: {total_shown}/{total_found} résultats")
        else:
            print(f"   Total: {total_found} résultat(s) trouvé(s)")
        
        # Comptage par type d'entité
        by_type = {}
        for result in results:
            by_type[result.entity_type] = by_type.get(result.entity_type, 0) + 1
        
        print("   Répartition par type:")
        for entity_type, count in sorted(by_type.items()):
            print(f"     {entity_type}: {count}")
        
        return True
    
    def list_by_type_and_display(self, entity_type: str, space_type_filter: str = None, 
                                space_class_filter: str = None, source: str = 'database',
                                max_results: int = None, verbose: bool = False) -> bool:
        """
        Liste les entités par type avec filtres avancés et affichage formaté
        
        Args:
            entity_type: Type d'entité à lister
            space_type_filter: Filtre sur le type d'espace (ex: TMA, CTR)
            space_class_filter: Filtre sur la classe d'espace (A, B, C, D, E)
            source: Source de données ('database', 'xml', 'both')
            max_results: Limite du nombre de résultats
            verbose: Affichage détaillé
        """
        print(f"🔍 Listing des entités de type '{entity_type}'")
        
        if space_type_filter:
            print(f"   Filtre type d'espace: {space_type_filter}")
        if space_class_filter:
            print(f"   Filtre classe: {space_class_filter}")
        
        results = []
        
        try:
            if source in ['database', 'both']:
                results.extend(self._list_from_database(entity_type, space_type_filter, 
                                                      space_class_filter, max_results))
                
            if source in ['xml', 'both']:
                results.extend(self._list_from_xml(entity_type, space_type_filter, 
                                                 space_class_filter, max_results))
        except Exception as e:
            print(f"✗ Erreur lors du listing: {e}")
            return False
        
        if not results:
            print("   Aucun résultat trouvé.")
            return False
        
        # Supprimer les doublons si source='both'
        if source == 'both':
            seen = set()
            unique_results = []
            for result in results:
                key = (result.entity_type, result.pk, result.lk)
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            results = unique_results
        
        # Limiter les résultats
        if max_results and len(results) > max_results:
            results = results[:max_results]
            print(f"   (Affichage limité aux {max_results} premiers résultats)")
        
        # Affichage des résultats
        print(f"\n📋 Résultats ({len(results)}):")
        print("-" * 80)
        
        show_source = (source == 'both')
        for i, result in enumerate(results, 1):
            if verbose:
                source_info = f" [{'DB' if result.source == 'database' else 'XML'}]" if show_source else ""
                print(f"{i:3d}. {result.entity_type:<10} | PK:{result.pk:<8}{source_info} | {result.lk}")
                if entity_type == 'espace':
                    # Affichage détaillé pour les espaces
                    details = self._get_space_details(result.pk, result.source)
                    if details:
                        print(f"      Type: {details.get('type_espace', 'N/A'):<6} | "
                              f"Nom: {details.get('nom', 'N/A')}")
            else:
                # Affichage compact
                if entity_type == 'espace':
                    details = self._get_space_details(result.pk, result.source)
                    type_espace = details.get('type_espace', 'N/A') if details else 'N/A'
                    nom = details.get('nom', 'N/A') if details else 'N/A'
                    source_info = f" [{'DB' if result.source == 'database' else 'XML'}]" if show_source else ""
                    print(f"{type_espace:<6} | {nom:<25}{source_info} | {result.lk}")
                else:
                    print(f"{i:3d}. {result.format_with_source(show_source)}")
        
        print(f"\n✓ Total: {len(results)} {entity_type}(s) trouvé(s)")
        return True
    
    def _list_from_database(self, entity_type: str, space_type_filter: str = None,
                          space_class_filter: str = None, max_results: int = None) -> List[SearchResult]:
        """Liste les entités depuis la base de données avec filtres"""
        if not self.connect_database():
            return []
        
        table = self.entity_mapping['database'].get(entity_type)
        if not table:
            print(f"✗ Type d'entité non supporté: {entity_type}")
            return []
        
        # Construction de la requête avec filtres
        conditions = []
        params = []
        
        if entity_type == 'espace':
            # Si on a un filtre de classe, on doit joindre avec les volumes
            if space_class_filter:
                base_query = """
                    SELECT DISTINCT e.pk, e.lk 
                    FROM espaces e
                    JOIN parties p ON e.pk = p.espace_ref
                    JOIN volumes v ON p.pk = v.partie_ref
                """
                conditions.append("v.classe = ?")
                params.append(space_class_filter)
                
                # Ajouter le filtre de type si présent
                if space_type_filter:
                    conditions.append("e.type_espace = ?")
                    params.append(space_type_filter)
            else:
                # Pas de filtre de classe, requête simple
                base_query = f"SELECT pk, lk FROM {table}"
                if space_type_filter:
                    conditions.append("type_espace = ?")
                    params.append(space_type_filter)
        else:
            # Autres types d'entités
            base_query = f"SELECT pk, lk FROM {table}"
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Déterminer la colonne pour ORDER BY selon le type de requête
        if space_class_filter and entity_type == 'espace':
            base_query += " ORDER BY e.lk"
        else:
            base_query += " ORDER BY lk"
        
        if max_results:
            base_query += f" LIMIT {max_results}"
        
        cursor = self.db_connection.cursor()
        cursor.execute(base_query, params)
        
        results = []
        for pk, lk in cursor.fetchall():
            results.append(SearchResult(entity_type, pk, lk, 'database'))
        
        return results
    
    def _list_from_xml(self, entity_type: str, space_type_filter: str = None,
                      space_class_filter: str = None, max_results: int = None) -> List[SearchResult]:
        """Liste les entités depuis le fichier XML avec filtres"""
        if not self.xml_file_path or not os.path.exists(self.xml_file_path):
            print(f"✗ Fichier XML non trouvé: {self.xml_file_path}")
            return []
        
        xpath = self.entity_mapping['xml'].get(entity_type)
        if not xpath:
            print(f"✗ Type d'entité non supporté: {entity_type}")
            return []
        
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            # Pas de namespace - chercher directement les éléments
            if entity_type == 'espace':
                # Structure spécifique: EspaceS/Espace
                espaces_section = root.find('.//EspaceS')
                if espaces_section is None:
                    return []
                elements = espaces_section.findall('Espace')
            else:
                # Pour d'autres types, utiliser le mapping existant (à corriger si nécessaire)
                elements = root.findall(xpath)
            
            results = []
            count = 0
            
            for element in elements:
                # Vérification des filtres
                if entity_type == 'espace':
                    if space_type_filter:
                        # TypeEspace est un élément enfant, pas un attribut
                        type_espace_elem = element.find('TypeEspace')
                        type_espace = type_espace_elem.text if type_espace_elem is not None else ''
                        if type_espace != space_type_filter:
                            continue
                    
                    # Pour les classes, chercher dans les volumes (structure à adapter)
                    if space_class_filter:
                        # Chercher la classe dans les volumes de cet espace
                        pk = element.get('pk', '')
                        volumes_section = root.find('.//VolumeS')
                        if volumes_section is not None:
                            volumes = [v for v in volumes_section.findall('Volume') 
                                     if v.find('Partie') is not None and 
                                     v.find('Partie').get('espace_pk') == pk]
                            has_class = any(vol.find('.//Classe') is not None and 
                                          vol.find('.//Classe').text == space_class_filter 
                                          for vol in volumes)
                            if not has_class:
                                continue
                
                pk = int(element.get('pk', 0))
                lk = element.get('lk', '')
                
                results.append(SearchResult(entity_type, pk, lk, 'xml'))
                count += 1
                
                if max_results and count >= max_results:
                    break
            
            return results
            
        except ET.ParseError as e:
            print(f"✗ Erreur parsing XML: {e}")
            return []
    
    def _get_space_details(self, pk: int, source: str) -> Dict:
        """Récupère les détails d'un espace aérien (nom, type)"""
        if source == 'database' and self.connect_database():
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT nom, type_espace FROM espaces WHERE pk = ?", (pk,))
            row = cursor.fetchone()
            if row:
                return {'nom': row[0], 'type_espace': row[1]}
        
        elif source == 'xml':
            # Chercher dans le XML
            if not self.xml_file_path or not os.path.exists(self.xml_file_path):
                return {}
            
            try:
                tree = ET.parse(self.xml_file_path)
                root = tree.getroot()
                
                # Chercher l'espace avec le bon pk
                espaces_section = root.find('.//EspaceS')
                if espaces_section is not None:
                    for espace in espaces_section.findall('Espace'):
                        if espace.get('pk') == str(pk):
                            # Extraire nom et type d'espace
                            nom_elem = espace.find('Nom')
                            type_elem = espace.find('TypeEspace')
                            
                            return {
                                'nom': nom_elem.text if nom_elem is not None else 'N/A',
                                'type_espace': type_elem.text if type_elem is not None else 'N/A'
                            }
            except ET.ParseError:
                pass
        
        return {}

def main():
    """Point d'entrée principal du script"""
    parser = argparse.ArgumentParser(
        description='Service de listing et recherche d\'entités XML-SIA avec filtrage avancé',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
    # Lister tous les espaces TMA (recommandé pour voir les espaces disponibles)
    python list_entities.py --type espace --space-type TMA
    
    # Rechercher par mot-clé dans les identifiants lk
    python list_entities.py --keyword "BOURGET"
    
    # Lister les espaces de classe D avec limite de résultats
    python list_entities.py --type espace --space-class D --max-results 20
    
    # Combiner type d'espace et mot-clé
    python list_entities.py --type espace --space-type TMA --keyword "PARIS"
        """
    )
    
    # Options de recherche et filtrage (maintenant combinables)
    parser.add_argument('-k', '--keyword',
                        help='Mot-clé à rechercher dans les attributs lk')
    parser.add_argument('--type', 
                        choices=['territoire', 'aerodrome', 'espace', 'partie', 'volume', 'service', 'frequence'],
                        help='Type d\'entité à lister ou filtrer')
    
    # Options de filtrage pour les espaces aériens
    parser.add_argument('--space-type',
                        help='Filtrer par type d\'espace (TMA, CTR, CTA, P, D, R, etc.)')
    parser.add_argument('--space-class',
                        choices=['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                        help='Filtrer par classe d\'espace aérien')
    
    # Options générales
    parser.add_argument('-s', '--source', 
                        choices=['database', 'xml', 'both'], 
                        default='database',
                        help='Source de recherche (défaut: database)')
    parser.add_argument('--xml-file',
                        help='Chemin vers le fichier XML (requis pour source=xml ou both)')
    parser.add_argument('--database', '-d',
                        default='sia_database.db',
                        help='Chemin vers la base SQLite (défaut: sia_database.db)')
    parser.add_argument('--case-sensitive', '-c', action='store_true',
                        help='Recherche sensible à la casse')
    parser.add_argument('--max-results', '-m', type=int,
                        help='Nombre maximum de résultats à afficher')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Affichage détaillé avec informations supplémentaires')
    
    args = parser.parse_args()
    
    # Validation des arguments
    if not args.keyword and not args.type:
        print("✗ Vous devez spécifier au moins --keyword ou --type")
        parser.print_help()
        sys.exit(1)
        
    if args.source in ['xml', 'both'] and not args.xml_file:
        print("✗ --xml-file est requis quand source=xml ou both")
        sys.exit(1)
    
    # Validation des filtres d'espaces pour les non-espaces
    if (args.space_type or args.space_class) and args.type and args.type != 'espace':
        print("✗ --space-type et --space-class ne peuvent être utilisés qu'avec --type espace")
        sys.exit(1)
    
    # Créer le service de recherche
    searcher = EntitySearchService(args.database, args.xml_file)
    
    try:
        if args.keyword and args.type:
            # Mode combiné : recherche par mot-clé filtrée par type
            found = searcher.search_and_display_filtered(
                keyword=args.keyword,
                entity_type_filter=args.type,
                space_type_filter=args.space_type,
                space_class_filter=args.space_class,
                source=args.source,
                case_sensitive=args.case_sensitive,
                max_results=args.max_results
            )
        elif args.keyword:
            # Mode recherche par mot-clé dans tous les types
            found = searcher.search_and_display(
                keyword=args.keyword,
                source=args.source,
                case_sensitive=args.case_sensitive,
                max_results=args.max_results
            )
        else:
            # Mode listing par type avec filtres
            found = searcher.list_by_type_and_display(
                entity_type=args.type,
                space_type_filter=args.space_type,
                space_class_filter=args.space_class,
                source=args.source,
                max_results=args.max_results,
                verbose=args.verbose
            )
        
        sys.exit(0 if found else 1)
        
    except Exception as e:
        print(f"✗ Erreur lors de l'exécution: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()