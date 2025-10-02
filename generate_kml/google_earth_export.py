#!/usr/bin/env python3
"""
Script d'export KML composé pour Google Earth
Permet l'export flexible d'espaces aériens selon différents critères
"""

import argparse
import sys
import os
from typing import List, Optional

# Import des services
sys.path.insert(0, os.path.dirname(__file__))
from enhanced_extractor import EnhancedKMLExtractor

class GoogleEarthExporter:
    """
    Exporteur KML spécialisé pour Google Earth
    Propose différents modes d'export selon les besoins
    """
    
    def __init__(self, database_path: str = 'sia_database.db'):
        self.database_path = database_path
        self.extractor = None
    
    def connect(self) -> bool:
        """Initialise la connexion à la base et au cache"""
        self.extractor = EnhancedKMLExtractor(self.database_path)
        return self.extractor.connect_database()
    
    def close(self):
        """Ferme les connexions"""
        if self.extractor:
            self.extractor.close_connection()
    
    def export_single_airspace(self, espace_lk: str, output_path: str, 
                              force_regenerate: bool = False) -> bool:
        """
        Exporte un espace aérien individuel
        
        Args:
            espace_lk: Identifiant de l'espace
            output_path: Chemin de sortie du fichier KML
            force_regenerate: Force la régénération du cache
        
        Returns:
            True si succès, False sinon
        """
        print(f"📤 Export espace individuel: {espace_lk}")
        
        kml_content = self.extractor.extract_airspace_kml_cached(espace_lk, force_regenerate)
        if not kml_content:
            print(f"❌ Impossible de générer le KML pour {espace_lk}")
            return False
        
        return self._save_kml(kml_content, output_path)
    
    def export_multiple_airspaces(self, espace_lks: List[str], output_path: str,
                                 output_name: str = "Espaces combinés",
                                 force_regenerate: bool = False) -> bool:
        """
        Exporte plusieurs espaces dans un KML combiné
        
        Args:
            espace_lks: Liste des identifiants d'espaces
            output_path: Chemin de sortie du fichier KML
            output_name: Nom du document KML
            force_regenerate: Force la régénération du cache
        
        Returns:
            True si succès, False sinon
        """
        print(f"📤 Export multi-espaces: {len(espace_lks)} espace(s)")
        
        kml_content = self.extractor.export_multiple_airspaces(
            espace_lks, output_name, force_regenerate
        )
        
        if not kml_content:
            print("❌ Impossible de générer le KML combiné")
            return False
        
        return self._save_kml(kml_content, output_path)
    
    def export_by_region(self, region_keywords: List[str], output_path: str,
                        classe: str = None, force_regenerate: bool = False) -> bool:
        """
        Exporte tous les espaces d'une région (par mots-clés)
        
        Args:
            region_keywords: Mots-clés pour identifier la région (ex: ["PARIS", "BOURGET"])
            output_path: Chemin de sortie du fichier KML
            classe: Filtrer par classe d'espace (optionnel)
            force_regenerate: Force la régénération du cache
        
        Returns:
            True si succès, False sinon
        """
        print(f"🗺️ Export par région: {', '.join(region_keywords)}")
        
        # Rechercher tous les espaces contenant les mots-clés
        espace_lks = self._find_airspaces_by_keywords(region_keywords, classe)
        
        if not espace_lks:
            print(f"❌ Aucun espace trouvé pour la région: {', '.join(region_keywords)}")
            return False
        
        region_name = f"Région {' + '.join(region_keywords)}"
        if classe:
            region_name += f" (Classe {classe})"
        
        return self.export_multiple_airspaces(espace_lks, output_path, region_name, force_regenerate)
    
    def export_by_class(self, classe: str, output_path: str,
                       altitude_min: int = None, altitude_max: int = None) -> bool:
        """
        Exporte tous les volumes d'une classe donnée
        
        Args:
            classe: Classe d'espace (A, B, C, D, E)
            output_path: Chemin de sortie du fichier KML
            altitude_min: Altitude minimum (optionnel)
            altitude_max: Altitude maximum (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        print(f"🏷️ Export par classe: {classe}")
        
        output_name = f"Espaces classe {classe}"
        if altitude_min or altitude_max:
            alt_range = f"{altitude_min or 0}-{altitude_max or '∞'}ft"
            output_name += f" ({alt_range})"
        
        kml_content = self.extractor.export_by_criteria(
            classe=classe,
            altitude_min=altitude_min,
            altitude_max=altitude_max,
            output_name=output_name
        )
        
        if not kml_content:
            print(f"❌ Aucun volume trouvé pour la classe {classe}")
            return False
        
        return self._save_kml(kml_content, output_path)
    
    def export_by_type(self, espace_type: str, output_path: str,
                      classe: str = None) -> bool:
        """
        Exporte tous les espaces d'un type donné
        
        Args:
            espace_type: Type d'espace (TMA, CTR, SIV, etc.)
            output_path: Chemin de sortie du fichier KML
            classe: Filtrer par classe (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        print(f"🔖 Export par type: {espace_type}")
        
        output_name = f"Espaces {espace_type}"
        if classe:
            output_name += f" classe {classe}"
        
        kml_content = self.extractor.export_by_criteria(
            espace_type=espace_type,
            classe=classe,
            output_name=output_name
        )
        
        if not kml_content:
            print(f"❌ Aucun espace trouvé pour le type {espace_type}")
            return False
        
        return self._save_kml(kml_content, output_path)
    
    def export_flight_level_range(self, fl_min: int, fl_max: int, output_path: str,
                                 classe: str = None) -> bool:
        """
        Exporte tous les volumes dans une plage de niveaux de vol
        
        Args:
            fl_min: Niveau de vol minimum (ex: 100 pour FL100)
            fl_max: Niveau de vol maximum (ex: 200 pour FL200)
            output_path: Chemin de sortie du fichier KML
            classe: Filtrer par classe (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        # Conversion FL vers pieds (1 FL = 100 ft)
        altitude_min = fl_min * 100
        altitude_max = fl_max * 100
        
        print(f"✈️ Export FL{fl_min:03d}-FL{fl_max:03d} ({altitude_min}-{altitude_max}ft)")
        
        output_name = f"Espaces FL{fl_min:03d}-FL{fl_max:03d}"
        if classe:
            output_name += f" classe {classe}"
        
        kml_content = self.extractor.export_by_criteria(
            altitude_min=altitude_min,
            altitude_max=altitude_max,
            classe=classe,
            output_name=output_name
        )
        
        if not kml_content:
            print(f"❌ Aucun volume trouvé pour FL{fl_min:03d}-FL{fl_max:03d}")
            return False
        
        return self._save_kml(kml_content, output_path)
    
    def _find_airspaces_by_keywords(self, keywords: List[str], classe: str = None) -> List[str]:
        """Trouve les espaces par mots-clés dans leur identifiant lk"""
        try:
            cursor = self.extractor.db_connection.cursor()
            
            # Construire la requête avec filtres
            where_conditions = []
            params = []
            
            # Filtrage par mots-clés (OR entre les mots-clés)
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("e.lk LIKE ?")
                params.append(f"%{keyword}%")
            
            if keyword_conditions:
                where_conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # Filtrage par classe si spécifié
            if classe:
                where_conditions.append('''
                    EXISTS (
                        SELECT 1 FROM volumes v
                        JOIN parties p ON v.partie_ref = p.pk
                        WHERE p.espace_ref = e.pk AND v.classe = ?
                    )
                ''')
                params.append(classe)
            
            query = "SELECT DISTINCT e.lk FROM espaces e"
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            query += " ORDER BY e.lk"
            
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Erreur recherche espaces: {e}")
            return []
    
    def _save_kml(self, kml_content: str, output_path: str) -> bool:
        """
        Sauvegarde le contenu KML dans un fichier
        
        Args:
            kml_content: Contenu KML à sauvegarder
            output_path: Chemin de sortie
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Créer le dossier parent si nécessaire
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Seulement si le chemin contient un dossier
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            file_size = len(kml_content.encode('utf-8'))
            print(f"✅ KML sauvegardé: {output_path} ({file_size:,} octets)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde KML: {e}")
            return False
    
    def show_statistics(self):
        """Affiche les statistiques de cache et de performance"""
        if not self.extractor:
            print("❌ Extracteur non initialisé")
            return
        
        stats = self.extractor.get_cache_statistics()
        
        print("\\n📊 Statistiques de performance:")
        print("=" * 50)
        
        # Statistiques de session
        session = stats.get('session_stats', {})
        print(f"Session actuelle:")
        print(f"  Volumes traités: {session.get('volumes_processed', 0)}")
        print(f"  Cache hits: {session.get('cache_hits', 0)}")
        print(f"  Cache misses: {session.get('cache_misses', 0)}")
        print(f"  KML générés: {session.get('kml_generated', 0)}")
        
        # Statistiques globales du cache
        print(f"\\nCache global:")
        print(f"  Entrées totales: {stats.get('total_entries', 0)}")
        print(f"  Taille totale: {stats.get('total_size_bytes', 0):,} octets")
        print(f"  Taille moyenne: {stats.get('average_size_bytes', 0):.0f} octets")
        
        # Distribution par classe
        class_dist = stats.get('class_distribution', [])
        if class_dist:
            print(f"\\nDistribution par classe:")
            for item in class_dist[:5]:  # Top 5
                print(f"  Classe {item['classe']}: {item['count']} volumes ({item['size']:,} octets)")

    def export_with_filters(self, keyword: str = None, space_type: str = None, 
                           space_class: str = None, max_results: int = None,
                           case_sensitive: bool = False, output_path: str = None,
                           force_regenerate: bool = False) -> bool:
        """
        Export avec filtrage avancé (similaire à list_entities.py)
        
        Args:
            keyword: Mot-clé à rechercher dans lk
            space_type: Type d'espace (TMA, CTR, etc.)
            space_class: Classe d'espace (A, B, C, D, E, F, G)
            max_results: Nombre maximum d'espaces
            case_sensitive: Recherche sensible à la casse
            output_path: Fichier de sortie
            force_regenerate: Force la régénération du cache
            
        Returns:
            True si succès, False sinon
        """
        print("🔍 Recherche avec filtres avancés...")
        
        # Construire la requête de recherche
        try:
            cursor = self.extractor.db_connection.cursor()
            
            # Base de la requête
            query = """
            SELECT DISTINCT e.lk, e.nom, e.pk
            FROM espaces e
            WHERE 1=1
            """
            params = []
            
            # Filtre par mot-clé
            if keyword:
                if case_sensitive:
                    query += " AND e.lk LIKE ?"
                    params.append(f"%{keyword}%")
                else:
                    query += " AND LOWER(e.lk) LIKE LOWER(?)"
                    params.append(f"%{keyword}%")
            
            # Filtre par type d'espace
            if space_type:
                query += f" AND UPPER(e.lk) LIKE '%{space_type.upper()}%'"
            
            # Filtre par classe d'espace
            if space_class:
                query += """
                AND EXISTS (
                    SELECT 1 FROM volumes v
                    JOIN parties p ON v.partie_ref = p.pk
                    WHERE p.espace_ref = e.pk AND v.classe = ?
                )
                """
                params.append(space_class.upper())
            
            # Tri et limite
            query += " ORDER BY e.lk"
            if max_results:
                query += f" LIMIT {max_results}"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                print("❌ Aucun espace trouvé avec les critères spécifiés")
                return False
            
            print(f"✅ {len(results)} espace(s) trouvé(s)")
            
            # Afficher les espaces trouvés
            print("\n📋 Espaces à exporter:")
            espace_lks = []
            for i, (lk, nom, pk) in enumerate(results, 1):
                print(f"  {i:3}. {lk} (PK: {pk})")
                espace_lks.append(lk)
            
            # Générer le titre automatiquement
            title_parts = []
            if keyword:
                title_parts.append(f"mot-clé '{keyword}'")
            if space_type:
                title_parts.append(f"type {space_type}")
            if space_class:
                title_parts.append(f"classe {space_class}")
            
            title = f"Espaces aériens - {', '.join(title_parts)}" if title_parts else "Export d'espaces aériens"
            
            # Export KML combiné
            return self.export_multiple_airspaces(espace_lks, output_path, title, force_regenerate)
            
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Export KML composé pour Google Earth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'usage:

# Export d'un espace individuel
python google_earth_export.py --single "[LF][TMA LE BOURGET]" --output bourget.kml

# Export de plusieurs espaces
python google_earth_export.py --multiple "[LF][TMA LE BOURGET]" "[LF][SIV LE BOURGET]" --output region_bourget.kml

# Export par région (tous les espaces contenant "PARIS")
python google_earth_export.py --region "PARIS" --output region_paris.kml --class D

# Export par classe
python google_earth_export.py --class D --output classe_d.kml --alt-min 1000 --alt-max 5000

# Export par type d'espace
python google_earth_export.py --type TMA --output tma_all.kml --class D

# Export par niveaux de vol
python google_earth_export.py --flight-levels 100 200 --output fl100_200.kml

# NOUVEAU: Export avec filtrage avancé (similaire à list_entities.py)
python google_earth_export.py --keyword "BOURGET" --output bourget_spaces.kml
python google_earth_export.py --space-type TMA --output all_tma.kml
python google_earth_export.py --space-class D --output class_d_spaces.kml
python google_earth_export.py --keyword "PARIS" --space-type TMA --max-results 10 --output paris_tma.kml

# Affichage des statistiques
python google_earth_export.py --stats
        """
    )
    
    parser.add_argument('--database', type=str, default='sia_database.db',
                       help='Chemin vers la base SQLite')
    
    # Modes d'export mutuellement exclusifs
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument('--single', type=str,
                            help='Export d\'un espace individuel (identifiant lk)')
    export_group.add_argument('--multiple', nargs='+',
                            help='Export de plusieurs espaces (identifiants lk)')
    export_group.add_argument('--region', type=str,
                            help='Export par région (mot-clé dans les identifiants)')
    export_group.add_argument('--class', type=str, dest='space_class_old',
                            help='Export par classe d\'espace (A, B, C, D, E)')
    export_group.add_argument('--type', type=str, dest='space_type_old',
                            help='Export par type d\'espace (TMA, CTR, SIV, etc.)')
    export_group.add_argument('--flight-levels', nargs=2, type=int, metavar=('FL_MIN', 'FL_MAX'),
                            help='Export par plage de niveaux de vol (ex: 100 200)')
    export_group.add_argument('--stats', action='store_true',
                            help='Afficher les statistiques de cache')
    
    # NOUVEAU: Filtrage avancé (similaire à list_entities.py) - peut être combiné
    parser.add_argument('-k', '--keyword', type=str,
                       help='Mot-clé à rechercher dans les identifiants lk')
    parser.add_argument('--space-type', type=str,
                       help='Filtrer par type d\'espace (TMA, CTR, CTA, SIV, P, D, R, etc.)')
    parser.add_argument('--space-class', type=str, choices=['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                       help='Filtrer par classe d\'espace aérien')
    parser.add_argument('--max-results', '-m', type=int,
                       help='Nombre maximum d\'espaces à exporter')
    parser.add_argument('--case-sensitive', '-c', action='store_true',
                       help='Recherche sensible à la casse')
    
    # Options communes
    parser.add_argument('--output', type=str,
                       help='Fichier KML de sortie (requis sauf pour --stats)')
    parser.add_argument('--name', type=str,
                       help='Nom du document KML (optionnel)')
    parser.add_argument('--force', action='store_true',
                       help='Force la régénération du cache')
    
    # Filtres additionnels
    parser.add_argument('--alt-min', type=int,
                       help='Altitude minimum en pieds')
    parser.add_argument('--alt-max', type=int,
                       help='Altitude maximum en pieds')
    
    args = parser.parse_args()
    
    # Validation des arguments
    if not args.stats and not args.output:
        print("❌ --output est requis (sauf pour --stats)")
        return 1
    
    # Vérifier si on utilise le mode filtrage avancé
    using_advanced_filters = any([args.keyword, args.space_type, args.space_class])
    using_classic_modes = any([args.single, args.multiple, args.region, 
                              args.space_class_old, args.space_type_old, args.flight_levels])
    
    if not args.stats and not using_advanced_filters and not using_classic_modes:
        # Mode "tous les espaces" - demander confirmation
        response = input("⚠️  Aucun filtre spécifié. Exporter TOUS les espaces en base ? (y/N): ").strip().lower()
        if response != 'y':
            print("Export annulé")
            return 0
        # Si l'utilisateur confirme, activer le mode filtrage avancé sans filtres
        using_advanced_filters = True
    
    # Initialisation
    exporter = GoogleEarthExporter(args.database)
    
    if not exporter.connect():
        print("❌ Impossible de se connecter à la base de données")
        return 1
    
    try:
        success = False
        
        # Traitement selon le mode choisi
        if args.stats:
            exporter.show_statistics()
            success = True
            
        elif using_advanced_filters:
            # NOUVEAU: Mode filtrage avancé (priorité sur les modes classiques)
            success = exporter.export_with_filters(
                keyword=args.keyword,
                space_type=args.space_type,
                space_class=args.space_class,
                max_results=args.max_results,
                case_sensitive=args.case_sensitive,
                output_path=args.output,
                force_regenerate=args.force
            )
            
        elif args.single:
            success = exporter.export_single_airspace(args.single, args.output, args.force)
            
        elif args.multiple:
            name = args.name or f"Export de {len(args.multiple)} espace(s)"
            success = exporter.export_multiple_airspaces(args.multiple, args.output, name, args.force)
            
        elif args.region:
            success = exporter.export_by_region([args.region], args.output, args.space_class_old, args.force)
            
        elif args.space_class_old:
            success = exporter.export_by_class(args.space_class_old, args.output, args.alt_min, args.alt_max)
            
        elif args.space_type_old:
            success = exporter.export_by_type(args.space_type_old, args.output, args.space_class_old)
            
        elif args.flight_levels:
            fl_min, fl_max = args.flight_levels
            success = exporter.export_flight_level_range(fl_min, fl_max, args.output, args.space_class_old)
        
        # Afficher les statistiques finales
        if success and not args.stats:
            exporter.show_statistics()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\n❌ Opération interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return 1
    finally:
        exporter.close()

if __name__ == "__main__":
    sys.exit(main())