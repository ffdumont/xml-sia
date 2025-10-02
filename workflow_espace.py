#!/usr/bin/env python3
"""
Workflow interactif pour traiter les espaces aériens XML-SIA
- Recherche par mot-clé avec list_entities.py
- Sélection interactive des espaces
- Vérification de présence en base
- Extraction XML et import en base
- Génération KML

Usage:
    python workflow_espace.py --keyword "BOURGET"
    python workflow_espace.py --keyword "TMA" --source database
"""

import argparse
import sys
import os
import subprocess
from typing import List, Dict, Optional
import sqlite3

# Import des modules existants
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'extraction'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generate_kml'))

from list_entities import EntitySearchService, SearchResult
from extract_espace import XsdBasedEspaceExtractor
from xml_importer import XMLImporter
from extractor import KMLExtractor
from google_earth_export import GoogleEarthExporter, launch_google_earth_pro

class WorkflowEspace:
    """
    Workflow interactif pour traiter les espaces aériens XML-SIA
    """
    
    def __init__(self, database_path: str = 'sia_database.db', 
                 xml_source: str = 'data-input/XML_SIA_2025-10-02.xml'):
        self.database_path = database_path
        self.xml_source = xml_source
        self.search_service = EntitySearchService(database_path, xml_source)
        self.processed_spaces = []
        self.selected_spaces = []
        self.launch_google_earth = False
        
    def search_spaces(self, keyword: str) -> List[SearchResult]:
        """
        Recherche les espaces par mot-clé dans les deux sources :
        1. Cherche dans la base de données
        2. Cherche dans le XML source
        3. Combine les résultats en évitant les doublons
        
        Args:
            keyword: Mot-clé de recherche
        
        Returns:
            Liste des espaces trouvés avec indication de la source
        """
        print(f"🔍 Recherche des espaces avec le mot-clé '{keyword}'...")
        
        all_spaces = []
        
        # 1. Recherche dans la base de données
        print("  📊 Recherche dans la base de données...")
        db_results = self.search_service.search_in_database(keyword)
        db_spaces = [r for r in db_results if r.entity_type == 'espace']
        
        if db_spaces:
            print(f"  ✅ {len(db_spaces)} espace(s) trouvé(s) dans la base")
            all_spaces.extend(db_spaces)
        
        # 2. Recherche dans le XML source (toujours, même si on a trouvé en base)
        print("  📄 Recherche dans le XML source...")
        xml_results = self.search_service.search_in_xml(keyword)
        xml_spaces = [r for r in xml_results if r.entity_type == 'espace']
        
        if xml_spaces:
            print(f"  ✅ {len(xml_spaces)} espace(s) trouvé(s) dans le XML")
            
            # Éviter les doublons en comparant les clés lk
            existing_lks = {space.lk for space in all_spaces}
            for xml_space in xml_spaces:
                if xml_space.lk not in existing_lks:
                    all_spaces.append(xml_space)
                    
        if all_spaces:
            total_count = len(all_spaces)
            db_count = len(db_spaces) if db_spaces else 0
            xml_count = len(xml_spaces) if xml_spaces else 0
            unique_count = total_count
            print(f"  📊 Total: {unique_count} espace(s) unique(s) (base: {db_count}, XML: {xml_count})")
            return all_spaces
        
        print(f"  ❌ Aucun espace trouvé avec le mot-clé '{keyword}' (ni en base ni dans le XML)")
        return []
    
    def display_spaces(self, spaces: List[SearchResult]):
        """Affiche la liste des espaces trouvés"""
        print("\n📋 Espaces trouvés:")
        print("=" * 80)
        for i, space in enumerate(spaces, 1):
            print(f"  {i:2d}. {space.lk} (PK: {space.pk})")
        print("=" * 80)
    
    def select_spaces(self, spaces: List[SearchResult]) -> List[SearchResult]:
        """
        Sélection interactive des espaces à traiter
        
        Args:
            spaces: Liste des espaces disponibles
        
        Returns:
            Liste des espaces sélectionnés
        """
        if not spaces:
            return []
        
        self.display_spaces(spaces)
        
        print("\n🎯 Sélection des espaces à traiter:")
        print("  - Entrez les numéros séparés par des virgules (ex: 1,3,5)")
        print("  - Tapez 'all' pour sélectionner tous les espaces")
        print("  - Tapez 'quit' pour annuler")
        
        while True:
            choice = input("\n➤ Votre choix: ").strip().lower()
            
            if choice == 'quit':
                print("❌ Opération annulée")
                return []
            
            if choice == 'all':
                print(f"✅ Tous les espaces sélectionnés ({len(spaces)})")
                return spaces
            
            try:
                # Parse des numéros sélectionnés
                indices = [int(x.strip()) for x in choice.split(',')]
                selected_spaces = []
                
                for idx in indices:
                    if 1 <= idx <= len(spaces):
                        selected_spaces.append(spaces[idx - 1])
                    else:
                        print(f"⚠️ Numéro invalide: {idx}")
                        continue
                
                if selected_spaces:
                    print(f"✅ {len(selected_spaces)} espace(s) sélectionné(s)")
                    for space in selected_spaces:
                        print(f"  - {space.lk}")
                    return selected_spaces
                else:
                    print("❌ Aucun espace valide sélectionné")
                    
            except ValueError:
                print("❌ Format invalide. Utilisez des numéros séparés par des virgules")
    
    def check_space_in_database(self, space_lk: str) -> bool:
        """
        Vérifie si un espace est déjà présent dans la base de données
        
        Args:
            space_lk: Identifiant lk de l'espace
        
        Returns:
            True si l'espace est présent, False sinon
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM espaces WHERE lk = ?", (space_lk,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la vérification en base: {e}")
            return False
    
    def extract_and_import_space(self, space: SearchResult) -> bool:
        """
        Extrait un espace du XML source et l'importe en base
        
        Args:
            space: Espace à traiter
        
        Returns:
            True si succès, False sinon
        """
        print(f"\n🔄 Traitement de l'espace: {space.lk}")
        
        # Vérifier si déjà en base
        if self.check_space_in_database(space.lk):
            print(f"  ℹ️  Espace déjà présent en base")
            response = input("  ➤ Forcer la ré-extraction ? (y/N): ").strip().lower()
            if response != 'y':
                print("  ⏭️  Passage au suivant")
                return True
        
        try:
            # 1. Extraction XML
            print(f"  📤 Extraction depuis {self.xml_source}...")
            
            try:
                extractor = XsdBasedEspaceExtractor(self.xml_source)
                
                # Charger le fichier XML
                if not extractor.load_xml():
                    print(f"    ✗ Erreur lors du chargement du fichier XML: {self.xml_source}")
                    return False
                
                # Générer nom de fichier de sortie
                output_filename = space.lk.replace('[', '').replace(']', '').replace(' ', '_')
                if not output_filename.endswith('.xml'):
                    output_filename += '.xml'
                output_path = os.path.join('data-output', output_filename)
                
                # Extraction
                print(f"    🔍 Recherche de l'espace: {space.lk}")
                if not extractor.extract_espace_with_dependencies(space.lk):
                    print(f"  ❌ Échec de l'extraction XML")
                    return False
                
                # Générer et sauvegarder le XML extrait
                print(f"    📝 Génération du XML...")
                xml_content = extractor.generate_output_xml()
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                print(f"  ✅ XML extrait vers: {output_path}")
                
            except Exception as extract_error:
                print(f"  ❌ Erreur d'extraction: {extract_error}")
                import traceback
                traceback.print_exc()
                return False
            
            # 2. Import en base SQLite
            print(f"  📥 Import dans la base SQLite...")
            try:
                importer = XMLImporter(self.database_path)
                
                if not importer.connect_database():
                    print(f"  ❌ Échec de connexion à la base")
                    return False
                
                if not importer.import_xml_file(output_path):
                    print(f"  ❌ Échec de l'import en base")
                    return False
                
                print(f"  ✅ Import terminé")
                return True
                
            except Exception as import_error:
                print(f"  ❌ Erreur d'import: {import_error}")
                return False
            
        except Exception as e:
            print(f"  ❌ Erreur générale lors du traitement: {e}")
            return False
    
    def generate_kml_for_space(self, space_lk: str, use_cache: bool = True) -> bool:
        """
        Génère le fichier KML pour un espace avec cache optimisé
        
        Args:
            space_lk: Identifiant lk de l'espace
            use_cache: Utiliser le cache par volume (défaut: True)
        
        Returns:
            True si succès, False sinon
        """
        try:
            print(f"  🗺️  Génération KML pour {space_lk}...")
            
            # Créer l'extracteur KML avec cache
            kml_extractor = KMLExtractor(self.database_path)
            
            if not kml_extractor.connect_database():
                print(f"  ❌ Impossible de se connecter à la base")
                return False
            
            # Générer le contenu KML
            kml_content = kml_extractor.get_airspace_kml_content(lk=space_lk)
            
            if not kml_content:
                print(f"  ❌ Impossible de générer le KML")
                return False
            
            # Nom de fichier KML
            kml_filename = space_lk.replace('[', '').replace(']', '').replace(' ', '_')
            if not kml_filename.endswith('.kml'):
                kml_filename += '.kml'
            kml_path = os.path.join('data-output', 'kml', kml_filename)
            
            # S'assurer que le dossier existe
            os.makedirs(os.path.dirname(kml_path), exist_ok=True)
            
            # Sauvegarder
            with open(kml_path, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            file_size = len(kml_content.encode('utf-8'))
            print(f"  ✅ KML généré: {kml_path} ({file_size:,} octets)")
            
            # Statistiques de génération (système de cache non applicable avec le nouvel extracteur)
            
            kml_extractor.close_connection()
            return True
            
        except Exception as e:
            print(f"  ❌ Erreur génération KML: {e}")
            return False
    
    def generate_consolidated_export(self) -> bool:
        """
        Génère un fichier d'export consolidé avec tous les espaces de la base
        
        Returns:
            True si succès, False sinon
        """
        print(f"\n📦 Génération de l'export consolidé SIA...")
        print("================================================================================")
        
        try:
            # Créer l'exporteur Google Earth
            exporter = GoogleEarthExporter(self.database_path)
            if not exporter.connect():
                print("❌ Impossible de se connecter à la base pour l'export consolidé")
                return False
            
            # Chemin de sortie
            output_path = "data-output/sia_export.kml"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Export automatique de tous les espaces disponibles
            print("🔄 Export automatique de tous les espaces disponibles en base...")
            success = exporter._export_all_spaces_standard(output_path)
            
            if success:
                # Vérifier la taille du fichier
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✅ Export consolidé généré: {output_path} ({file_size:,} octets)")
                    print(f"📊 Tous les espaces de la base inclus dans l'export")
                    
                    # Lancer Google Earth Pro si demandé
                    if self.launch_google_earth:
                        print(f"\n🚀 Lancement de Google Earth Pro...")
                        full_path = os.path.abspath(output_path)
                        if launch_google_earth_pro(full_path):
                            print(f"✅ Google Earth Pro lancé avec {output_path}")
                        else:
                            print("⚠️ Impossible de lancer Google Earth Pro")
                            
                else:
                    print("❌ Fichier d'export non créé")
                    success = False
            else:
                print("❌ Échec de la génération de l'export consolidé")
            
            exporter.close()
            return success
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export consolidé: {e}")
            return False
    
    def process_selected_spaces(self, selected_spaces: List[SearchResult]) -> bool:
        """
        Traite tous les espaces sélectionnés
        
        Args:
            selected_spaces: Liste des espaces à traiter
        
        Returns:
            True si au moins un espace traité avec succès
        """
        if not selected_spaces:
            return False
        
        print(f"\n🚀 Début du traitement de {len(selected_spaces)} espace(s)")
        print("=" * 80)
        
        success_count = 0
        
        for i, space in enumerate(selected_spaces, 1):
            print(f"\n[{i}/{len(selected_spaces)}] 🎯 Traitement: {space.lk}")
            
            # Extraction et import
            if self.extract_and_import_space(space):
                self.processed_spaces.append(space)
                success_count += 1
            else:
                print(f"  ❌ Échec du traitement de {space.lk}")
        
        print(f"\n📊 Résumé du traitement:")
        print(f"  ✅ Succès: {success_count}/{len(selected_spaces)}")
        print(f"  ❌ Échecs: {len(selected_spaces) - success_count}/{len(selected_spaces)}")
        
        return success_count > 0
    
    def generate_all_kml(self) -> bool:
        """
        Génère les KML pour tous les espaces traités
        
        Returns:
            True si au moins un KML généré
        """
        if not self.processed_spaces:
            print("⚠️  Aucun espace traité, pas de KML à générer")
            return False
        
        print(f"\n🗺️  Génération des fichiers KML pour {len(self.processed_spaces)} espace(s)")
        print("=" * 80)
        
        success_count = 0
        
        # Déterminer si on utilise le cache (argument passé depuis main)
        use_cache = getattr(self, 'use_cache', True)
        
        for i, space in enumerate(self.processed_spaces, 1):
            print(f"\n[{i}/{len(self.processed_spaces)}]", end=" ")
            if self.generate_kml_for_space(space.lk, use_cache):
                success_count += 1
        
        print(f"\n📊 Résumé génération KML:")
        print(f"  ✅ Succès: {success_count}/{len(self.processed_spaces)}")
        print(f"  ❌ Échecs: {len(self.processed_spaces) - success_count}/{len(self.processed_spaces)}")
        
        return success_count > 0
    
    def run_workflow(self, keyword: str) -> bool:
        """
        Exécute le workflow complet avec logique en cascade
        
        Args:
            keyword: Mot-clé de recherche
        
        Returns:
            True si workflow réussi
        """
        print("🎯 Workflow de traitement des espaces XML-SIA")
        print("=" * 80)
        
        # 1. Recherche des espaces (base puis XML si nécessaire)
        spaces = self.search_spaces(keyword)
        if not spaces:
            return False
        
        # 2. Sélection interactive
        selected_spaces = self.select_spaces(spaces)
        if not selected_spaces:
            return False
        
        # Stocker les espaces sélectionnés pour l'export consolidé
        self.selected_spaces = selected_spaces
        
        # 3. Traitement (extraction + import)
        if not self.process_selected_spaces(selected_spaces):
            print("❌ Aucun espace traité avec succès")
            return False
        
        # 4. Génération KML
        if not self.generate_all_kml():
            print("❌ Aucun KML généré")
            return False
        
        # 5. Génération du fichier d'export consolidé
        if not self.generate_consolidated_export():
            print("⚠️ Échec de la génération du fichier d'export consolidé")
        
        print("\n🎉 Workflow terminé avec succès!")
        return True

def main():
    parser = argparse.ArgumentParser(
        description="Workflow interactif pour traiter les espaces aériens XML-SIA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python workflow_espace.py --keyword "CHEVREUSE"
  python workflow_espace.py --keyword "BOURGET" --no-cache
  python workflow_espace.py --keyword "PARIS" --xml-source "data-input/XML_SIA_2025-10-02.xml"
  python workflow_espace.py --keyword "AVORD" --launch

Le workflow recherche automatiquement :
  1. D'abord dans la base de données
  2. Si pas trouvé, dans le fichier XML source
  3. Extrait et importe les espaces trouvés dans le XML
  4. Génère les KML avec cache par volume
        """
    )
    
    parser.add_argument('--keyword', type=str, required=True,
                       help='Mot-clé pour rechercher les espaces aériens')
    parser.add_argument('--database', type=str, default='sia_database.db',
                       help='Chemin vers la base SQLite (défaut: sia_database.db)')
    parser.add_argument('--xml-source', type=str, default='data-input/XML_SIA_2025-10-02.xml',
                       help='Fichier XML source (défaut: data-input/XML_SIA_2025-10-02.xml)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Désactiver le cache KML par volume (mode legacy)')
    parser.add_argument('--launch', action='store_true',
                       help='Lancer Google Earth Pro avec le fichier d\'export consolidé')
    
    args = parser.parse_args()
    
    # Vérifier les fichiers requis
    if not os.path.exists(args.xml_source):
        print(f"❌ Fichier XML source non trouvé: {args.xml_source}")
        return 1
    
    if not os.path.exists(args.database):
        print(f"⚠️ Base de données non trouvée: {args.database}")
        print("   Le workflow pourra quand même fonctionner avec le XML source")
    
    # Créer et exécuter le workflow
    workflow = WorkflowEspace(args.database, args.xml_source)
    workflow.use_cache = not args.no_cache  # Configurer l'usage du cache
    workflow.launch_google_earth = args.launch  # Configurer le lancement de Google Earth
    
    try:
        success = workflow.run_workflow(args.keyword)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Opération interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())