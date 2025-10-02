#!/usr/bin/env python3
"""
Script d'export KML composé pour Google Earth
Permet l'export flexible d'espaces aériens selon différents critères
"""

import argparse
import sys
import os
import subprocess
from typing import List, Optional

# Import des services
sys.path.insert(0, os.path.dirname(__file__))
from extractor import KMLExtractor

def launch_google_earth_pro(kml_file_path: str) -> bool:
    """
    Lance Google Earth Pro avec le fichier KML spécifié
    
    Args:
        kml_file_path: Chemin vers le fichier KML à ouvrir
        
    Returns:
        True si le lancement a réussi, False sinon
    """
    # Emplacements possibles de Google Earth Pro
    possible_paths = [
        r"C:\Program Files\Google\Google Earth Pro\client\googleearth.exe",
        r"C:\Program Files (x86)\Google\Google Earth Pro\client\googleearth.exe",
        r"C:\Program Files\Google\Google Earth Pro\googleearth.exe",
        r"C:\Program Files (x86)\Google\Google Earth Pro\googleearth.exe"
    ]
    
    # Trouver Google Earth Pro
    google_earth_path = None
    for path in possible_paths:
        if os.path.exists(path):
            google_earth_path = path
            break
    
    if not google_earth_path:
        print("❌ Google Earth Pro non trouvé dans les emplacements habituels:")
        for path in possible_paths:
            print(f"   - {path}")
        print("   Veuillez vérifier l'installation de Google Earth Pro")
        return False
    
    # Vérifier que le fichier KML existe
    if not os.path.exists(kml_file_path):
        print(f"❌ Fichier KML non trouvé: {kml_file_path}")
        return False
    
    try:
        # Lancer Google Earth Pro avec le fichier KML
        print(f"🚀 Lancement de Google Earth Pro avec: {kml_file_path}")
        print(f"   Utilisation de: {google_earth_path}")
        subprocess.Popen([google_earth_path, kml_file_path], shell=False)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du lancement de Google Earth Pro: {e}")
        return False


class GoogleEarthExporter:
    """
    Exporteur KML spécialisé pour Google Earth
    Propose différents modes d'export selon les besoins
    NOUVEAU: Utilise les extracteurs améliorés avec parties visibles
    """
    
    def __init__(self, database_path: str = 'sia_database.db'):
        self.database_path = database_path
        self.extractor = None
    
    def connect(self) -> bool:
        """Initialise la connexion à la base et au cache"""
        print("✨ Utilisation de l'extracteur KML (parties visibles)")
        self.extractor = KMLExtractor(self.database_path)
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
        
        # Utiliser l'extracteur amélioré
        return self.extractor.extract_airspace_to_kml(lk=espace_lk, output_file=output_path)
    
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
        
        # Utiliser l'extracteur amélioré avec KML combiné
        return self._create_combined_kml(espace_lks, output_path, output_name)
    
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
    
    def _export_all_spaces_standard(self, output_path: str) -> bool:
        """
        Export automatique de tous les espaces avec l'extracteur amélioré
        """
        try:
            cursor = self.extractor.db_connection.cursor()
            cursor.execute("SELECT lk FROM espaces ORDER BY lk")  # Export de tous les espaces
            espace_lks = [row[0] for row in cursor.fetchall()]
            
            if not espace_lks:
                print("❌ Aucun espace trouvé dans la base")
                return False
            
            print(f"📤 Export automatique de {len(espace_lks)} espaces")
            return self.export_multiple_airspaces(espace_lks, output_path, "Export automatique d'espaces aériens", False)
            
        except Exception as e:
            print(f"❌ Erreur export automatique standard: {e}")
            return False
    

    
    def _create_combined_kml(self, espace_lks: List[str], output_path: str, output_name: str) -> bool:
        """
        Crée un KML combiné avec l'extracteur amélioré
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        try:
            print(f"🔄 Création du KML combiné avec {len(espace_lks)} espace(s)")
            
            # Créer la structure KML de base
            kml = ET.Element('kml')
            kml.set('xmlns', 'http://www.opengis.net/kml/2.2')
            
            document = ET.SubElement(kml, 'Document')
            
            # Nom et description du document
            name = ET.SubElement(document, 'name')
            name.text = output_name
            
            description = ET.SubElement(document, 'description')
            desc_text = f"""
            Export combiné de {len(espace_lks)} espace(s) aérien(s)
            Généré avec l'extracteur amélioré (parties visibles)
            Espaces inclus:
            """
            for i, lk in enumerate(espace_lks, 1):
                desc_text += f"\n  {i}. {lk}"
            
            description.text = desc_text.strip()
            
            # Traiter chaque espace directement dans le document (sans dossier intermédiaire)
            for espace_lk in espace_lks:
                print(f"   📋 Traitement de {espace_lk}...")
                
                try:
                    # Récupérer l'espace
                    airspace = self.extractor.get_airspace_by_lk(espace_lk)
                    if not airspace:
                        print(f"      ⚠️ Espace non trouvé: {espace_lk}")
                        continue
                    
                    # Récupérer les parties
                    parts = self.extractor.get_parts_for_airspace(airspace['pk'])
                    if not parts:
                        print(f"      ⚠️ Aucune partie trouvée pour: {espace_lk}")
                        continue
                    
                    # Ajouter les styles spécifiques à cet espace
                    self._add_space_specific_styles(document, airspace, parts)
                    
                    # Créer un dossier pour cet espace directement dans le document
                    space_folder = ET.SubElement(document, 'Folder')
                    space_folder_name = ET.SubElement(space_folder, 'name')
                    space_folder_name.text = airspace['lk']  # Utiliser directement le lk
                    
                    # Ajouter chaque partie avec le bon style
                    for part in parts:
                        self._add_part_to_folder_with_colors(space_folder, part, airspace)
                    
                    print(f"      ✅ {len(parts)} partie(s) ajoutée(s)")
                    
                except Exception as e:
                    print(f"      ❌ Erreur traitement {espace_lk}: {str(e)[:50]}...")
                    continue
            
            # Convertir en chaîne XML formatée
            rough_string = ET.tostring(kml, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            kml_content = reparsed.toprettyxml(indent='  ')
            
            # Sauvegarder
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            file_size = len(kml_content.encode('utf-8'))
            print(f"✅ KML combiné sauvegardé: {output_path} ({file_size:,} octets)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création KML combiné: {e}")
            return False
    
    def _add_space_specific_styles(self, document, airspace, parts):
        """Ajoute les styles spécifiques à un espace avec les bonnes couleurs"""
        import xml.etree.ElementTree as ET
        from color_service import get_space_color
        
        # Déterminer la couleur pour ce type d'espace
        type_espace = airspace['type_espace']
        
        # Trouver une classe représentative - privilégier la classe A
        classe = None
        classes_found = set()
        for part in parts:
            for volume in part['volumes']:
                if volume['classe']:
                    classes_found.add(volume['classe'])
        
        # Ordre de priorité : A > B > C > D > E > autres
        priority_order = ['A', 'B', 'C', 'D', 'E']
        for priority_class in priority_order:
            if priority_class in classes_found:
                classe = priority_class
                break
        
        # Si aucune classe prioritaire, prendre la première trouvée
        if not classe and classes_found:
            classe = list(classes_found)[0]
        
        # Obtenir la couleur spécifique
        base_color = get_space_color(type_espace, classe, 'kml')
        
        # Style unique pour cet espace
        style_id = f'volumeStyle_{airspace["pk"]}'
        
        # Vérifier si le style existe déjà
        existing_style = document.find(f'.//Style[@id="{style_id}"]')
        if existing_style is not None:
            return  # Style déjà ajouté
        
        # Style principal pour les volumes extrudés
        main_style = ET.SubElement(document, 'Style')
        main_style.set('id', style_id)
        
        line_style = ET.SubElement(main_style, 'LineStyle')
        line_color = ET.SubElement(line_style, 'color')
        line_color.text = f'ff{base_color[2:]}'  # Couleur opaque pour les contours
        line_width = ET.SubElement(line_style, 'width')
        line_width.text = '2'
        
        poly_style = ET.SubElement(main_style, 'PolyStyle')
        poly_color = ET.SubElement(poly_style, 'color')
        poly_color.text = f'80{base_color[2:]}'  # 50% d'opacité
        poly_fill = ET.SubElement(poly_style, 'fill')
        poly_fill.text = '1'
        poly_outline = ET.SubElement(poly_style, 'outline')
        poly_outline.text = '1'
    
    def _add_part_to_folder_with_colors(self, parent_folder, part, airspace):
        """Ajoute une partie d'espace au dossier parent avec les bonnes couleurs"""
        import xml.etree.ElementTree as ET
        import re
        
        coordinates = self._parse_contour_coordinates(part['contour'])
        
        if not coordinates:
            return
        
        # S'assurer que le polygone est fermé
        if coordinates and coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        # Calculer les altitudes
        min_floor, max_ceiling = self._get_part_altitude_range(part)
        
        # Créer directement un placemark avec le lk de la partie (structure simplifiée)
        volume_placemark = ET.SubElement(parent_folder, 'Placemark')
        volume_name = ET.SubElement(volume_placemark, 'name')
        volume_name.text = part['lk']  # Utiliser directement le lk de la partie
        
        # Ajouter une description enrichie pour le mouse over
        volume_description = ET.SubElement(volume_placemark, 'description')
        part_name = part['nom_partie'] if part['nom_partie'] and part['nom_partie'] != '.' else f"Partie {part['numero_partie'] or 'principale'}"
        
        # Convertir les altitudes en pieds pour l'affichage (standard aéronautique)
        min_floor_ft = int(min_floor * 3.28084)  # mètres vers pieds
        max_ceiling_ft = int(max_ceiling * 3.28084)
        
        # Récupérer les classes des volumes de cette partie
        volume_classes = set()
        for volume in part['volumes']:
            if volume['classe']:
                volume_classes.add(volume['classe'])
        
        classes_text = ', '.join(sorted(volume_classes)) if volume_classes else 'Non spécifiée'
        type_espace = airspace['type_espace']
        
        # Déterminer la classe dominante de l'espace entier (pour cohérence)
        espace_classes = set()
        for p in [part]:  # On pourrait passer toutes les parties, mais on a seulement celle-ci ici
            for vol in p['volumes']:
                if vol['classe']:
                    espace_classes.add(vol['classe'])
        
        # Classe dominante (privilégier A)
        classe_dominante = None
        priority_order = ['A', 'B', 'C', 'D', 'E']
        for priority_class in priority_order:
            if priority_class in espace_classes:
                classe_dominante = priority_class
                break
        if not classe_dominante and espace_classes:
            classe_dominante = list(espace_classes)[0]
        
        desc_lines = [
            f"Espace: {type_espace} (classe dominante: {classe_dominante or 'N/A'})",
            f"Partie: {part_name}",
            f"Classes de cette partie: {classes_text}",
            f"Plancher: {min_floor_ft} ft ({min_floor:.0f} m)",
            f"Plafond: {max_ceiling_ft} ft ({max_ceiling:.0f} m)"
        ]
        volume_description.text = '\n'.join(desc_lines)
        
        # Référencer le style spécifique à cet espace
        volume_style_url = ET.SubElement(volume_placemark, 'styleUrl')
        volume_style_url.text = f'#volumeStyle_{airspace["pk"]}'
        
        volume_polygon = ET.SubElement(volume_placemark, 'Polygon')
        volume_extrude = ET.SubElement(volume_polygon, 'extrude')
        volume_extrude.text = '1'
        
        volume_altitude_mode = ET.SubElement(volume_polygon, 'altitudeMode')
        volume_altitude_mode.text = 'absolute'
        
        volume_outer = ET.SubElement(volume_polygon, 'outerBoundaryIs')
        volume_ring = ET.SubElement(volume_outer, 'LinearRing')
        volume_coords = ET.SubElement(volume_ring, 'coordinates')
        
        volume_coord_strings = []
        for lat, lon in coordinates:
            volume_coord_strings.append(f"{lon},{lat},{max_ceiling}")
        volume_coords.text = ' '.join(volume_coord_strings)
    
    def _add_part_to_folder(self, parent_folder, part, airspace):
        """Méthode legacy - utilise la nouvelle méthode avec couleurs"""
        return self._add_part_to_folder_with_colors(parent_folder, part, airspace)
    
    def _parse_contour_coordinates(self, contour: str):
        """Parse les coordonnées depuis le champ 'contour'"""
        import re
        
        coordinates = []
        
        if not contour:
            return coordinates
        
        lines = contour.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            coord_pattern = r'(\d+\.?\d*)\s+(\d+\.?\d*)'
            matches = re.findall(coord_pattern, line)
            
            for match in matches:
                try:
                    lat = float(match[0])
                    lon = float(match[1])
                    if 40 <= lat <= 55 and -10 <= lon <= 10:
                        coordinates.append((lat, lon))
                        break
                except ValueError:
                    continue
        
        return coordinates
    
    def _get_part_altitude_range(self, part):
        """Calcule la plage d'altitude pour une partie"""
        if not part['volumes']:
            return 0.0, 1000.0
        
        surface_elevation = 0.0
        min_floor = float('inf')
        max_ceiling = float('-inf')
        
        for volume in part['volumes']:
            floor_alt = self._parse_altitude_to_meters(
                volume['plancher'], 
                volume['plancher_ref_unite'], 
                is_ceiling=False, 
                surface_elevation=surface_elevation
            )
            ceiling_alt = self._parse_altitude_to_meters(
                volume['plafond'], 
                volume['plafond_ref_unite'], 
                is_ceiling=True, 
                surface_elevation=surface_elevation
            )
            
            min_floor = min(min_floor, floor_alt)
            max_ceiling = max(max_ceiling, ceiling_alt)
        
        return min_floor if min_floor != float('inf') else 0.0, max_ceiling if max_ceiling != float('-inf') else 1000.0
    
    def _parse_altitude_to_meters(self, altitude: str, ref_unite: str, is_ceiling: bool = True, surface_elevation: float = 0.0) -> float:
        """Convertit une altitude en mètres"""
        import re
        
        if not ref_unite:
            return 0.0
        
        try:
            if ref_unite == "SFC":
                return surface_elevation
            elif ref_unite == "UNL":
                if is_ceiling:
                    return 19500 * 0.3048
                else:
                    return 18000 * 0.3048
            
            if isinstance(altitude, str):
                altitude_clean = re.sub(r'[^\d.]', '', altitude)
                if not altitude_clean:
                    return 0.0
                altitude_val = float(altitude_clean)
            else:
                altitude_val = float(altitude)
            
            if ref_unite.startswith("FL"):
                return altitude_val * 100 * 0.3048
            elif "ft" in ref_unite.lower():
                if "ASFC" in ref_unite:
                    return surface_elevation + (altitude_val * 0.3048)
                else:
                    return altitude_val * 0.3048
            elif "m" in ref_unite.lower():
                if "ASFC" in ref_unite:
                    return surface_elevation + altitude_val
                else:
                    return altitude_val
            else:
                return altitude_val * 0.3048
                
        except (ValueError, TypeError):
            return 0.0

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

# Lancement automatique de Google Earth Pro
python google_earth_export.py --single "[LF][TMA LE BOURGET]" --output bourget.kml --launch

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
    
    # Option pour lancer Google Earth Pro
    parser.add_argument('--launch', action='store_true',
                       help='Lancer automatiquement Google Earth Pro avec le fichier KML généré')
    
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
    
    # Initialisation de l'exporteur (toujours avec l'extracteur amélioré)
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
        
        else:
            # Mode automatique - export de tous les espaces disponibles
            print("🔄 Aucun critère spécifique - export automatique des espaces disponibles")
            success = exporter._export_all_spaces_standard(args.output)
        
        # Les statistiques ne sont plus nécessaires avec l'extracteur amélioré
        
        # Lancer Google Earth Pro si demandé et export réussi
        if success and args.launch and args.output and not args.stats:
            # Convertir en chemin absolu si nécessaire
            output_path = os.path.abspath(args.output)
            launch_google_earth_pro(output_path)
        
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