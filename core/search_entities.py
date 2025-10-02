#!/usr/bin/env python3
"""
Service de recherche par mot-clé pour entités XML-SIA
Recherche dans les attributs lk des entités depuis le fichier XML ou la base SQLite

Usage:
    python search_entities.py --keyword "BOURGET" --source database
    python search_entities.py --keyword "TMA" --source xml --xml-file data-input/XML_SIA_2025-10-02.xml
    python search_entities.py --keyword "PT" --source both
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
        current_type = None
        for result in display_results:
            if result.entity_type != current_type:
                current_type = result.entity_type
                print(f"\n📁 {current_type.upper()}S:")
            
            print(f"   {result}")
        
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

def main():
    """Point d'entrée principal du script"""
    parser = argparse.ArgumentParser(
        description="Recherche d'entités XML-SIA par mot-clé dans les attributs lk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
    python search_entities.py -k "BOURGET"
    python search_entities.py -k "TMA" --source database
    python search_entities.py -k "PT" --source xml --xml-file data-input/XML_SIA_2025-10-02.xml
    python search_entities.py -k "PARIS" --source both --case-sensitive
    python search_entities.py -k "LF" --max-results 10
        """
    )
    
    parser.add_argument('-k', '--keyword', required=True,
                        help='Mot-clé à rechercher dans les attributs lk')
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
    
    args = parser.parse_args()
    
    # Validation des arguments
    if args.source in ['xml', 'both'] and not args.xml_file:
        print("✗ --xml-file est requis quand source=xml ou both")
        sys.exit(1)
    
    # Créer le service de recherche
    searcher = EntitySearchService(args.database, args.xml_file)
    
    # Effectuer la recherche
    found = searcher.search_and_display(
        keyword=args.keyword,
        source=args.source,
        case_sensitive=args.case_sensitive,
        max_results=args.max_results
    )
    
    sys.exit(0 if found else 1)

if __name__ == '__main__':
    main()