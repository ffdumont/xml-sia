#!/usr/bin/env python3
"""
Extracteur KML pour espaces aériens XML-SIA
Extracteur optimisé qui met l'accent sur les parties d'espaces et simplifie la géométrie
"""

import sqlite3
import argparse
import sys
import os
import re
from typing import List, Dict, Optional, Tuple
from xml.dom import minidom
import xml.etree.ElementTree as ET

# Import du service de couleurs
from color_service import get_space_color

class KMLExtractor:
    """
    Extracteur KML amélioré qui:
    - Met en évidence les noms des parties d'espaces
    - Simplifie la géométrie en utilisant des extrusions
    - Réduit le nombre d'éléments KML générés
    """
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.db_connection = None
    
    def connect_database(self) -> bool:
        """Se connecte à la base de données SQLite"""
        try:
            if not os.path.exists(self.database_path):
                print(f"✗ Base de données non trouvée: {self.database_path}")
                return False
            
            self.db_connection = sqlite3.connect(self.database_path)
            print(f"✓ Connecté à la base: {self.database_path}")
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Erreur de connexion SQLite: {e}")
            return False
    
    def close_connection(self):
        """Ferme la connexion à la base de données"""
        if self.db_connection:
            self.db_connection.close()
    
    def get_airspace_by_lk(self, lk: str) -> Optional[Dict]:
        """Récupère un espace aérien par son identifiant lk"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT pk, lk, nom, type_espace, altr_ft
            FROM espaces 
            WHERE lk = ?
        """, (lk,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            'pk': row[0],
            'lk': row[1],
            'nom': row[2],
            'type_espace': row[3],
            'altr_ft': row[4]
        }
    
    def get_airspace_by_pk(self, pk: int) -> Optional[Dict]:
        """Récupère un espace aérien par son identifiant pk"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT pk, lk, nom, type_espace, altr_ft
            FROM espaces 
            WHERE pk = ?
        """, (pk,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            'pk': row[0],
            'lk': row[1],
            'nom': row[2],
            'type_espace': row[3],
            'altr_ft': row[4]
        }
    
    def get_parts_for_airspace(self, espace_pk: int) -> List[Dict]:
        """
        Récupère toutes les parties d'un espace aérien avec leurs volumes
        Regroupe par partie pour une meilleure organisation
        """
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT 
                p.pk as partie_pk,
                p.lk as partie_lk,
                p.nom_partie,
                p.numero_partie,
                p.contour,
                p.geometrie,
                GROUP_CONCAT(v.pk) as volume_pks,
                GROUP_CONCAT(v.lk, '|') as volume_lks,
                GROUP_CONCAT(v.sequence, '|') as sequences,
                GROUP_CONCAT(v.plafond_ref_unite, '|') as plafond_unites,
                GROUP_CONCAT(v.plafond, '|') as plafonds,
                GROUP_CONCAT(v.plancher_ref_unite, '|') as plancher_unites,
                GROUP_CONCAT(v.plancher, '|') as planchers,
                GROUP_CONCAT(v.classe, '|') as classes,
                GROUP_CONCAT(v.hor_code, '|') as hor_codes,
                GROUP_CONCAT(v.hor_txt, '|') as hor_txts
            FROM parties p
            LEFT JOIN volumes v ON p.pk = v.partie_ref
            WHERE p.espace_ref = ?
            GROUP BY p.pk, p.lk, p.nom_partie, p.numero_partie, p.contour, p.geometrie
            ORDER BY p.numero_partie, p.nom_partie
        """, (espace_pk,))
        
        parts = []
        for row in cursor.fetchall():
            # Parser les volumes concaténés
            volumes = []
            if row[6]:  # volume_pks existe
                volume_pks = row[6].split(',')
                volume_lks = row[7].split('|') if row[7] else []
                sequences = row[8].split('|') if row[8] else []
                plafond_unites = row[9].split('|') if row[9] else []
                plafonds = row[10].split('|') if row[10] else []
                plancher_unites = row[11].split('|') if row[11] else []
                planchers = row[12].split('|') if row[12] else []
                classes = row[13].split('|') if row[13] else []
                hor_codes = row[14].split('|') if row[14] else []
                hor_txts = row[15].split('|') if row[15] else []
                
                for i, pk in enumerate(volume_pks):
                    volumes.append({
                        'pk': int(pk),
                        'lk': volume_lks[i] if i < len(volume_lks) else '',
                        'sequence': int(sequences[i]) if i < len(sequences) and sequences[i] else 0,
                        'plafond_ref_unite': plafond_unites[i] if i < len(plafond_unites) else None,
                        'plafond': plafonds[i] if i < len(plafonds) else None,
                        'plancher_ref_unite': plancher_unites[i] if i < len(plancher_unites) else None,
                        'plancher': planchers[i] if i < len(planchers) else None,
                        'classe': classes[i] if i < len(classes) and classes[i] != 'None' else None,
                        'hor_code': hor_codes[i] if i < len(hor_codes) and hor_codes[i] != 'None' else None,
                        'hor_txt': hor_txts[i] if i < len(hor_txts) and hor_txts[i] != 'None' else None,
                    })
            
            parts.append({
                'pk': row[0],
                'lk': row[1],
                'nom_partie': row[2],
                'numero_partie': row[3],
                'contour': row[4],
                'geometrie': row[5],
                'volumes': volumes
            })
        
        return parts
    
    def parse_contour_coordinates(self, contour: str) -> List[Tuple[float, float]]:
        """
        Parse les coordonnées depuis le champ 'contour'
        Gère les coordonnées classiques ET les définitions géométriques (cercles)
        """
        import math
        coordinates = []
        
        if not contour:
            return coordinates
        
        lines = contour.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Vérifier s'il y a une définition de cercle
            circle_pattern = r'cir\(([-+]?\d+\.?\d*)\s+([-+]?\d+\.?\d*):(\d+\.?\d*):([A-Z]+)'
            circle_match = re.search(circle_pattern, line)
            
            if circle_match:
                # C'est un cercle - générer des points sur le périmètre
                center_lat = float(circle_match.group(1))
                center_lon = float(circle_match.group(2))
                radius = float(circle_match.group(3))
                unit = circle_match.group(4)
                
                # Convertir le rayon en degrés (approximation)
                if unit == 'NM':  # Nautical Miles
                    radius_deg = radius / 60.0  # 1 degré ≈ 60 NM
                elif unit == 'KM':
                    radius_deg = radius / 111.0  # 1 degré ≈ 111 km
                elif unit == 'M':
                    radius_deg = radius / 111000.0  # 1 degré ≈ 111000 m
                else:
                    radius_deg = radius / 60.0  # Par défaut, supposer NM
                
                # Générer 36 points sur le cercle (tous les 10 degrés)
                num_points = 36
                for i in range(num_points + 1):  # +1 pour fermer le cercle
                    angle = (i * 2 * math.pi) / num_points
                    
                    # Approximation simple (valable pour les petites distances)
                    lat = center_lat + radius_deg * math.cos(angle)
                    lon = center_lon + radius_deg * math.sin(angle) / math.cos(math.radians(center_lat))
                    
                    coordinates.append((lat, lon))
                
                print(f"   🔵 Cercle détecté: centre({center_lat:.3f}, {center_lon:.3f}), rayon {radius} {unit} → {len(coordinates)} points")
                return coordinates
            
            # Sinon, parser les coordonnées classiques
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
    
    def parse_altitude_to_meters(self, altitude: str, ref_unite: str, is_ceiling: bool = True, surface_elevation: float = 0.0) -> float:
        """
        Convertit une altitude en mètres selon l'unité de référence
        Version simplifiée de l'original
        """
        if not ref_unite:
            return 0.0
        
        try:
            if ref_unite == "SFC":
                return surface_elevation
            
            elif ref_unite == "UNL":
                if is_ceiling:
                    return 19500 * 0.3048  # FL195
                else:
                    return 18000 * 0.3048
            
            # Extraire la valeur numérique
            if isinstance(altitude, str):
                altitude_clean = re.sub(r'[^\d.]', '', altitude)
                if not altitude_clean:
                    return 0.0
                altitude_val = float(altitude_clean)
            else:
                altitude_val = float(altitude)
            
            # Conversion selon l'unité
            if ref_unite.startswith("FL"):
                return altitude_val * 100 * 0.3048  # FL en mètres
            elif "ft" in ref_unite.lower():
                if "ASFC" in ref_unite:
                    return surface_elevation + (altitude_val * 0.3048)
                else:  # AMSL
                    return altitude_val * 0.3048
            elif "m" in ref_unite.lower():
                if "ASFC" in ref_unite:
                    return surface_elevation + altitude_val
                else:  # AMSL
                    return altitude_val
            else:
                return altitude_val * 0.3048  # Défaut en pieds
                
        except (ValueError, TypeError):
            return 0.0
    
    def create_multigeometry_3d(self, parent_element, coordinates, min_floor, max_ceiling):
        """
        Crée une géométrie 3D complète (plancher + plafond + murs) sous un élément parent
        
        Args:
            parent_element: Element XML parent où ajouter la MultiGeometry
            coordinates: Liste de tuples (lat, lon) définissant le contour
            min_floor: Altitude du plancher en mètres
            max_ceiling: Altitude du plafond en mètres
        """
        import xml.etree.ElementTree as ET
        
        # Géométrie 3D complète (plancher + plafond + murs)
        multi_geometry = ET.SubElement(parent_element, 'MultiGeometry')
        
        # 1. Polygone plancher
        floor_polygon = ET.SubElement(multi_geometry, 'Polygon')
        floor_altitude_mode = ET.SubElement(floor_polygon, 'altitudeMode')
        floor_altitude_mode.text = 'absolute'
        floor_outer = ET.SubElement(floor_polygon, 'outerBoundaryIs')
        floor_ring = ET.SubElement(floor_outer, 'LinearRing')
        floor_coords = ET.SubElement(floor_ring, 'coordinates')
        
        # Coordonnées plancher (sens horaire pour face vers le bas)
        floor_coord_strings = []
        for lat, lon in reversed(coordinates):  # Inverser pour orientation correcte
            floor_coord_strings.append(f"{lon},{lat},{min_floor}")
        floor_coords.text = ' '.join(floor_coord_strings)
        
        # 2. Polygone plafond  
        ceiling_polygon = ET.SubElement(multi_geometry, 'Polygon')
        ceiling_altitude_mode = ET.SubElement(ceiling_polygon, 'altitudeMode')
        ceiling_altitude_mode.text = 'absolute'
        ceiling_outer = ET.SubElement(ceiling_polygon, 'outerBoundaryIs')
        ceiling_ring = ET.SubElement(ceiling_outer, 'LinearRing')
        ceiling_coords = ET.SubElement(ceiling_ring, 'coordinates')
        
        # Coordonnées plafond (sens antihoraire pour face vers le haut)
        ceiling_coord_strings = []
        for lat, lon in coordinates:
            ceiling_coord_strings.append(f"{lon},{lat},{max_ceiling}")
        ceiling_coords.text = ' '.join(ceiling_coord_strings)
        
        # 3. Murs (un polygone vertical par segment)
        for i in range(len(coordinates) - 1):  # -1 car dernier point = premier
            lat1, lon1 = coordinates[i]
            lat2, lon2 = coordinates[i + 1]
            
            # Créer un polygone vertical pour ce segment
            wall_polygon = ET.SubElement(multi_geometry, 'Polygon')
            wall_altitude_mode = ET.SubElement(wall_polygon, 'altitudeMode')
            wall_altitude_mode.text = 'absolute'
            wall_outer = ET.SubElement(wall_polygon, 'outerBoundaryIs')
            wall_ring = ET.SubElement(wall_outer, 'LinearRing')
            wall_coords = ET.SubElement(wall_ring, 'coordinates')
            
            # Rectangle vertical : bas1 -> haut1 -> haut2 -> bas2 -> bas1
            wall_coord_strings = [
                f"{lon1},{lat1},{min_floor}",      # Point 1 plancher
                f"{lon1},{lat1},{max_ceiling}",    # Point 1 plafond
                f"{lon2},{lat2},{max_ceiling}",    # Point 2 plafond
                f"{lon2},{lat2},{min_floor}",      # Point 2 plancher
                f"{lon1},{lat1},{min_floor}"       # Fermeture
            ]
            wall_coords.text = ' '.join(wall_coord_strings)
        
        return multi_geometry

    def estimate_surface_elevation(self, contour: str) -> float:
        """
        Estime l'élévation de surface basée sur la géométrie de l'espace
        Approximation basée sur des données connues pour les régions françaises
        """
        if not contour:
            return 0.0
        
        # Extraire les coordonnées pour estimer la région
        coordinates = self.parse_contour_coordinates(contour)
        if not coordinates:
            return 0.0
        
        # Calculer le centre approximatif
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Approximations basées sur les régions françaises
        # Limoges area (45.8°N, 1.2°E) : ~350m
        if 45.5 <= center_lat <= 46.2 and 0.8 <= center_lon <= 1.8:
            return 350.0
        
        # Paris area (48.8°N, 2.3°E) : ~100m
        elif 48.3 <= center_lat <= 49.3 and 1.8 <= center_lon <= 2.8:
            return 100.0
        
        # Bourget area (proche Paris) : ~60m
        elif 48.8 <= center_lat <= 49.0 and 2.3 <= center_lon <= 2.6:
            return 60.0
        
        # France métropolitaine générale : ~200m (moyenne)
        elif 42.0 <= center_lat <= 52.0 and -5.0 <= center_lon <= 10.0:
            return 200.0
        
        # Défaut
        return 0.0

    def get_part_altitude_range(self, part: Dict) -> Tuple[float, float]:
        """
        Calcule la plage d'altitude pour une partie (min plancher, max plafond)
        """
        if not part['volumes']:
            return 0.0, 1000.0  # Valeurs par défaut
        
        # Estimer l'élévation de surface basée sur la géométrie
        surface_elevation = self.estimate_surface_elevation(part.get('contour', ''))
        min_floor = float('inf')
        max_ceiling = float('-inf')
        
        for volume in part['volumes']:
            floor_alt = self.parse_altitude_to_meters(
                volume['plancher'], 
                volume['plancher_ref_unite'], 
                is_ceiling=False, 
                surface_elevation=surface_elevation
            )
            ceiling_alt = self.parse_altitude_to_meters(
                volume['plafond'], 
                volume['plafond_ref_unite'], 
                is_ceiling=True, 
                surface_elevation=surface_elevation
            )
            
            min_floor = min(min_floor, floor_alt)
            max_ceiling = max(max_ceiling, ceiling_alt)
        
        return min_floor if min_floor != float('inf') else 0.0, max_ceiling if max_ceiling != float('-inf') else 1000.0
    
    def create_simplified_kml_document(self, airspace: Dict, parts: List[Dict]) -> str:
        """
        Crée un document KML optimisé qui met l'accent sur les parties
        Utilise l'extrusion KML au lieu de créer plancher/plafond/murs séparément
        """
        # Créer la structure KML de base
        kml = ET.Element('kml')
        kml.set('xmlns', 'http://www.opengis.net/kml/2.2')
        
        document = ET.SubElement(kml, 'Document')
        
        # Nom du document avec le lk de l'espace
        name = ET.SubElement(document, 'name')
        name.text = airspace['lk']
        
        # Déterminer la couleur de base
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
        
        base_color = get_space_color(type_espace, classe, 'kml')
        
        # Style principal pour les volumes extrudés
        main_style = ET.SubElement(document, 'Style')
        main_style.set('id', 'volumeStyle')
        
        line_style = ET.SubElement(main_style, 'LineStyle')
        line_color = ET.SubElement(line_style, 'color')
        line_color.text = f'ff{base_color[2:]}'  # Couleur opaque pour les contours
        line_width = ET.SubElement(line_style, 'width')
        line_width.text = '2'
        
        poly_style = ET.SubElement(main_style, 'PolyStyle')
        poly_color = ET.SubElement(poly_style, 'color')
        poly_color.text = f'80{base_color[2:]}'  # Couleur avec 50% d'opacité
        poly_fill = ET.SubElement(poly_style, 'fill')
        poly_fill.text = '1'
        poly_outline = ET.SubElement(poly_style, 'outline')
        poly_outline.text = '1'
        
        # Style pour les contours au sol (référence)
        ground_style = ET.SubElement(document, 'Style')
        ground_style.set('id', 'groundStyle')
        
        ground_line_style = ET.SubElement(ground_style, 'LineStyle')
        ground_line_color = ET.SubElement(ground_line_style, 'color')
        ground_line_color.text = f'ff{base_color[2:]}'
        ground_line_width = ET.SubElement(ground_line_style, 'width')
        ground_line_width.text = '1'
        
        ground_poly_style = ET.SubElement(ground_style, 'PolyStyle')
        ground_poly_color = ET.SubElement(ground_poly_style, 'color')
        ground_poly_color.text = f'20{base_color[2:]}'  # Très transparent
        ground_poly_fill = ET.SubElement(ground_poly_style, 'fill')
        ground_poly_fill.text = '1'
        
        # Traiter chaque partie directement dans le document (sans dossier intermédiaire)
        for part in parts:
            coordinates = self.parse_contour_coordinates(part['contour'])
            
            if not coordinates:
                print(f"⚠ Aucune coordonnée trouvée pour la partie {part['nom_partie']}")
                continue
            
            # S'assurer que le polygone est fermé
            if coordinates and coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            
            # Calculer la plage d'altitude pour cette partie
            min_floor, max_ceiling = self.get_part_altitude_range(part)
            
            # Créer directement un placemark dans le document (structure plate)
            volume_placemark = ET.SubElement(document, 'Placemark')
            volume_name = ET.SubElement(volume_placemark, 'name')
            volume_name.text = part['lk']  # Utiliser directement le lk de la partie
            
            # Ajouter une description concise pour le mouse over
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
            
            desc_lines = [
                f"Espace: {type_espace} (classe dominante: {classe or 'N/A'})",
                f"Partie: {part_name}",
                f"Classes de cette partie: {classes_text}",
                f"Plancher: {min_floor_ft} ft ({min_floor:.0f} m)",
                f"Plafond: {max_ceiling_ft} ft ({max_ceiling:.0f} m)"
            ]
            volume_description.text = '\n'.join(desc_lines)
            
            # Style du volume
            volume_style_url = ET.SubElement(volume_placemark, 'styleUrl')
            volume_style_url.text = '#volumeStyle'
            
            # Utiliser la méthode utilitaire pour créer la géométrie 3D
            self.create_multigeometry_3d(volume_placemark, coordinates, min_floor, max_ceiling)
        
        # Convertir en chaîne XML formatée
        rough_string = ET.tostring(kml, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent='  ')
    
    def get_airspace_kml_content(self, lk: str = None, pk: int = None) -> Optional[str]:
        """
        Génère le contenu KML pour un espace aérien sans l'écrire dans un fichier
        """
        if not self.connect_database():
            return None
        
        try:
            # Récupérer l'espace aérien
            if lk:
                airspace = self.get_airspace_by_lk(lk)
            elif pk:
                airspace = self.get_airspace_by_pk(pk)
            else:
                return None
            
            if not airspace:
                return None
            
            # Récupérer les parties avec leurs volumes
            parts = self.get_parts_for_airspace(airspace['pk'])
            if not parts:
                return None
            
            # Générer et retourner le contenu KML
            return self.create_simplified_kml_document(airspace, parts)
            
        except Exception as e:
            print(f"✗ Erreur lors de la génération du contenu KML: {e}")
            return None
        finally:
            self.close_connection()

    def extract_airspace_to_kml(self, lk: str = None, pk: int = None, output_file: str = None) -> bool:
        """
        Extrait un espace aérien et génère un fichier KML amélioré
        """
        if not self.connect_database():
            return False
        
        try:
            # Récupérer l'espace aérien
            if lk:
                airspace = self.get_airspace_by_lk(lk)
            elif pk:
                airspace = self.get_airspace_by_pk(pk)
            else:
                print("✗ Vous devez spécifier soit --espace-lk soit --espace-pk")
                return False
            
            if not airspace:
                print(f"✗ Espace aérien non trouvé: {lk or pk}")
                return False
            
            print(f"✓ Espace trouvé: {airspace['nom']} ({airspace['lk']})")
            
            # Récupérer les parties
            parts = self.get_parts_for_airspace(airspace['pk'])
            if not parts:
                print(f"✗ Aucune partie trouvée pour l'espace {airspace['lk']}")
                return False
            
            # Compter le total de volumes
            total_volumes = sum(len(part['volumes']) for part in parts)
            print(f"✓ {len(parts)} partie(s) trouvée(s) avec {total_volumes} volume(s)")
            
            # Afficher les détails des parties
            for part in parts:
                part_name = part['nom_partie'] if part['nom_partie'] and part['nom_partie'] != '.' else f"#{part['numero_partie']}"
                print(f"  - Partie {part_name}: {len(part['volumes'])} volume(s)")
            
            # Générer le KML simplifié
            kml_content = self.create_simplified_kml_document(airspace, parts)
            
            # Déterminer le fichier de sortie
            if not output_file:
                source_lk = lk if lk else airspace['lk']
                safe_name = re.sub(r'[^\w\-_.]', '_', source_lk)
                safe_name = re.sub(r'_+', '_', safe_name)
                safe_name = safe_name.strip('_')
                output_file = f"{safe_name}.kml"
            
            # Écrire le fichier
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            print(f"✓ Fichier KML amélioré généré: {output_file}")
            return True
            
        except Exception as e:
            print(f"✗ Erreur lors de l'extraction: {e}")
            return False
        
        finally:
            self.close_connection()

def main():
    """Point d'entrée principal du script"""
    parser = argparse.ArgumentParser(
        description="Extrait un espace aérien XML-SIA et génère un fichier KML amélioré",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Améliorations par rapport à l'extracteur standard:
- Met en évidence les noms des parties d'espaces
- Utilise l'extrusion KML pour simplifier la géométrie
- Réduit le nombre d'éléments KML générés
- Organisation plus claire par parties

Exemples d'utilisation:
    python extractor.py --espace-lk "[LF][TMA LE BOURGET]"
    python extractor.py --espace-lk "[LF][TMA SEINE]" --output seine.kml
        """
    )
    
    parser.add_argument('--espace-lk', 
                        help='Identifiant lk de l\'espace aérien (ex: "[LF][TMA SEINE]")')
    parser.add_argument('--espace-pk', type=int,
                        help='Identifiant pk de l\'espace aérien')
    parser.add_argument('--output', '-o',
                        help='Fichier KML de sortie (par défaut: clé_lk.kml)')
    parser.add_argument('--database', '-d', 
                        default='sia_database.db',
                        help='Chemin vers la base de données SQLite (défaut: sia_database.db)')
    
    args = parser.parse_args()
    
    # Vérifier les arguments
    if not args.espace_lk and not args.espace_pk:
        print("✗ Vous devez spécifier soit --espace-lk soit --espace-pk")
        parser.print_help()
        sys.exit(1)
    
    # Créer l'extracteur et lancer l'extraction
    extractor = KMLExtractor(args.database)
    success = extractor.extract_airspace_to_kml(
        lk=args.espace_lk,
        pk=args.espace_pk,
        output_file=args.output
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()