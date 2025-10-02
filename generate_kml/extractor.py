#!/usr/bin/env python3
"""
Service d'extraction KML pour espaces aériens XML-SIA
Extrait un espace aérien et génère un fichier KML avec tous ses volumes combinés.

Usage:
    python kml_extractor.py --espace-lk "[LF][TMA LE BOURGET]" --output airspace.kml
    python kml_extractor.py --espace-pk 304333 --output airspace.kml
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
    Extracteur KML pour espaces aériens XML-SIA
    Génère des fichiers KML à partir des données de la base SQLite
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
    
    def get_volumes_for_airspace(self, espace_pk: int) -> List[Dict]:
        """Récupère tous les volumes d'un espace aérien avec leurs données géographiques"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT 
                v.pk, v.lk, v.sequence, 
                v.plafond_ref_unite, v.plafond, 
                v.plancher_ref_unite, v.plancher,
                v.classe, v.hor_code, v.hor_txt,
                p.contour, p.geometrie, p.nom_partie
            FROM volumes v
            JOIN parties p ON v.partie_ref = p.pk
            WHERE p.espace_ref = ?
            ORDER BY v.sequence
        """, (espace_pk,))
        
        volumes = []
        for row in cursor.fetchall():
            volumes.append({
                'pk': row[0],
                'lk': row[1],
                'sequence': row[2],
                'plafond_ref_unite': row[3],
                'plafond': row[4],
                'plancher_ref_unite': row[5],
                'plancher': row[6],
                'classe': row[7],
                'hor_code': row[8],
                'hor_txt': row[9],
                'contour': row[10],
                'geometrie': row[11],
                'nom_partie': row[12]
            })
        
        return volumes
    
    def parse_contour_coordinates(self, contour: str) -> List[Tuple[float, float]]:
        """
        Parse les coordonnées depuis le champ 'contour'
        Format attendu: "1000010,Cloture=309741,49.389444 1.899167,grc(49.389444 1.899167:0m:=)"
        """
        coordinates = []
        
        if not contour:
            return coordinates
        
        # Diviser par les sauts de ligne pour traiter chaque point
        lines = contour.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Rechercher les coordonnées dans le format "lat lon"
            # Utiliser une regex pour trouver les coordonnées décimales
            coord_pattern = r'(\d+\.?\d*)\s+(\d+\.?\d*)'
            matches = re.findall(coord_pattern, line)
            
            for match in matches:
                try:
                    lat = float(match[0])
                    lon = float(match[1])
                    # Vérifier que les coordonnées sont dans des plages raisonnables
                    if 40 <= lat <= 55 and -10 <= lon <= 10:  # Zone France approximative
                        coordinates.append((lat, lon))
                        break  # Prendre seulement la première coordonnée valide par ligne
                except ValueError:
                    continue
        
        return coordinates
    
    def parse_altitude_to_meters(self, altitude: str, ref_unite: str, is_ceiling: bool = True, surface_elevation: float = 0.0) -> float:
        """
        Convertit une altitude en mètres selon l'unité de référence définie dans le XSD
        
        Args:
            altitude: Valeur d'altitude (str ou numérique)
            ref_unite: Unité de référence selon AltiCode XSD (FL, ft AMSL, ft ASFC, SFC, UNL)
            is_ceiling: True pour plafond, False pour plancher (affecte le traitement de UNL)
            surface_elevation: Élévation du sol en mètres (pour ft ASFC)
        
        Returns:
            Altitude en mètres absolus (MSL)
        """
        if not ref_unite:
            return 0.0
        
        try:
            # Cas spéciaux selon le XSD
            if ref_unite == "SFC":
                # SFC = Surface, altitude = 0 (niveau du sol)
                return surface_elevation
            
            elif ref_unite == "UNL":
                # UNL = Unlimited (sans limite)
                if is_ceiling:
                    # Pour un plafond UNL, utiliser le niveau de vol max VFR (FL195 = 19500 ft)
                    return 19500 * 0.3048  # ~5944m
                else:
                    # Pour un plancher UNL (cas rare), utiliser une valeur très haute
                    return 18000 * 0.3048  # ~5486m
            
            # Extraire la valeur numérique
            if isinstance(altitude, str):
                # Gérer les cas comme "2500" ou "FL195"
                alt_str = altitude.strip()
                if alt_str.startswith('FL'):
                    # Niveau de vol : FL195 = 19500 ft
                    fl_value = float(alt_str[2:])
                    alt_value = fl_value * 100  # FL195 -> 19500 ft
                    ref_unite = "ft AMSL"  # Les FL sont toujours en ft AMSL
                else:
                    alt_value = float(alt_str.split()[0]) if ' ' in alt_str else float(alt_str)
            else:
                alt_value = float(altitude)
            
            # Conversion selon l'unité de référence
            if ref_unite == "FL":
                # Niveau de vol : directement en centaines de pieds AMSL
                return alt_value * 100 * 0.3048  # FL -> ft -> mètres
            
            elif ref_unite == "ft AMSL":
                # Pieds Above Mean Sea Level (altitude absolue)
                return alt_value * 0.3048  # ft -> mètres
            
            elif ref_unite == "ft ASFC":
                # Pieds Above Surface (altitude relative au sol)
                altitude_msl = (alt_value * 0.3048) + surface_elevation
                return altitude_msl
            
            else:
                # Cas par défaut : supposer que c'est déjà en mètres
                print(f"⚠ Unité d'altitude inconnue: {ref_unite}, traitement par défaut")
                return alt_value
                
        except (ValueError, TypeError) as e:
            print(f"⚠ Erreur conversion altitude '{altitude}' {ref_unite}: {e}")
            return 0.0

    def create_kml_document(self, airspace: Dict, volumes: List[Dict]) -> str:
        """Crée un document KML pour l'espace aérien et ses volumes"""
        
        # Créer l'élément racine KML
        kml = ET.Element('kml')
        kml.set('xmlns', 'http://www.opengis.net/kml/2.2')
        
        document = ET.SubElement(kml, 'Document')
        
        # Informations générales sur l'espace
        name = ET.SubElement(document, 'name')
        name.text = f"{airspace['nom']} ({airspace['lk']})"
        
        description = ET.SubElement(document, 'description')
        desc_text = f"""
        Espace aérien: {airspace['nom']}
        Identifiant: {airspace['lk']}
        Type: {airspace['type_espace']}
        """
        if airspace['altr_ft']:
            desc_text += f"        Altitude de référence: {airspace['altr_ft']} ft"
        description.text = desc_text.strip()
        
        # Déterminer la couleur basée sur le type d'espace et la classe du premier volume
        type_espace = airspace['type_espace']
        classe = volumes[0]['classe'] if volumes and volumes[0]['classe'] else None
        
        # Obtenir la couleur depuis le service
        base_color = get_space_color(type_espace, classe, 'kml')
        
        # Styles pour les différentes parties du volume avec la couleur appropriée
        # Style pour les murs (surfaces verticales)
        wall_style = ET.SubElement(document, 'Style')
        wall_style.set('id', 'wallStyle')
        
        wall_line_style = ET.SubElement(wall_style, 'LineStyle')
        wall_line_color = ET.SubElement(wall_line_style, 'color')
        wall_line_color.text = f'ff{base_color[2:]}'  # Couleur opaque pour les lignes
        wall_line_width = ET.SubElement(wall_line_style, 'width')  
        wall_line_width.text = '2'
        
        wall_poly_style = ET.SubElement(wall_style, 'PolyStyle')
        wall_poly_color = ET.SubElement(wall_poly_style, 'color')
        wall_poly_color.text = f'40{base_color[2:]}'  # Couleur avec 25% d'opacité (0x40 = 64 = 25% de 255)
        
        # Style pour le plancher et le plafond
        floor_ceiling_style = ET.SubElement(document, 'Style')
        floor_ceiling_style.set('id', 'floorCeilingStyle')
        
        fc_line_style = ET.SubElement(floor_ceiling_style, 'LineStyle')
        fc_line_color = ET.SubElement(fc_line_style, 'color')
        fc_line_color.text = f'ff{base_color[2:]}'  # Couleur opaque pour les lignes
        fc_line_width = ET.SubElement(fc_line_style, 'width')
        fc_line_width.text = '1'
        
        fc_poly_style = ET.SubElement(floor_ceiling_style, 'PolyStyle')
        fc_poly_color = ET.SubElement(fc_poly_style, 'color')
        fc_poly_color.text = f'60{base_color[2:]}'  # Couleur avec opacité légèrement plus forte pour plancher/plafond
        
        # Créer un dossier pour tous les volumes
        folder = ET.SubElement(document, 'Folder')
        folder_name = ET.SubElement(folder, 'name')
        folder_name.text = 'Volumes'
        
        # Traiter chaque volume
        for volume in volumes:
            coordinates = self.parse_contour_coordinates(volume['contour'])
            
            if not coordinates:
                print(f"⚠ Aucune coordonnée trouvée pour le volume {volume['lk']}")
                continue
            
            # Calculer les altitudes en mètres
            # TODO: Récupérer l'élévation du sol depuis les données géographiques si disponible
            surface_elevation = 0.0  # Pour l'instant, utiliser 0m comme référence
            
            floor_altitude = self.parse_altitude_to_meters(
                volume['plancher'], 
                volume['plancher_ref_unite'], 
                is_ceiling=False, 
                surface_elevation=surface_elevation
            )
            ceiling_altitude = self.parse_altitude_to_meters(
                volume['plafond'], 
                volume['plafond_ref_unite'], 
                is_ceiling=True, 
                surface_elevation=surface_elevation
            )
            

            
            # Créer un dossier pour ce volume
            volume_folder = ET.SubElement(folder, 'Folder')
            vol_folder_name = ET.SubElement(volume_folder, 'name')
            vol_name = f"Volume {volume['sequence']}"
            if volume['nom_partie']:
                vol_name += f" - {volume['nom_partie']}"
            vol_folder_name.text = vol_name
            
            vol_description = ET.SubElement(volume_folder, 'description')
            # Formatage amélioré des descriptions d'altitude
            def format_altitude_desc(alt_val, alt_unit, alt_meters):
                if alt_unit == "SFC":
                    return f"SFC (surface, {alt_meters:.0f}m)"
                elif alt_unit == "UNL":
                    return f"UNL (sans limite, ~{alt_meters:.0f}m)"
                elif alt_unit and alt_unit.startswith("FL"):
                    return f"FL{alt_val} ({alt_meters:.0f}m)"
                else:
                    return f"{alt_val} {alt_unit or ''} ({alt_meters:.0f}m)"
            
            vol_desc = f"""
            Volume: {volume['lk']}
            Séquence: {volume['sequence']}
            Plafond: {format_altitude_desc(volume['plafond'], volume['plafond_ref_unite'], ceiling_altitude)}
            Plancher: {format_altitude_desc(volume['plancher'], volume['plancher_ref_unite'], floor_altitude)}
            """
            if volume['classe']:
                vol_desc += f"            Classe: {volume['classe']}"
            vol_description.text = vol_desc.strip()
            
            # S'assurer que le polygone est fermé
            if coordinates and coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            
            # 1. Créer le plancher (floor)
            floor_placemark = ET.SubElement(volume_folder, 'Placemark')
            floor_name = ET.SubElement(floor_placemark, 'name')
            floor_name.text = f"Plancher ({volume['plancher']} {volume['plancher_ref_unite'] or ''})"
            
            floor_style_url = ET.SubElement(floor_placemark, 'styleUrl')
            floor_style_url.text = '#floorCeilingStyle'
            
            floor_polygon = ET.SubElement(floor_placemark, 'Polygon')
            floor_altitude_mode = ET.SubElement(floor_polygon, 'altitudeMode')
            floor_altitude_mode.text = 'absolute'
            
            floor_outer = ET.SubElement(floor_polygon, 'outerBoundaryIs')
            floor_ring = ET.SubElement(floor_outer, 'LinearRing')
            floor_coords = ET.SubElement(floor_ring, 'coordinates')
            
            floor_coord_strings = []
            for lat, lon in coordinates:
                floor_coord_strings.append(f"{lon},{lat},{floor_altitude}")
            floor_coords.text = ' '.join(floor_coord_strings)
            
            # 2. Créer le plafond (ceiling)
            ceiling_placemark = ET.SubElement(volume_folder, 'Placemark')
            ceiling_name = ET.SubElement(ceiling_placemark, 'name')
            ceiling_name.text = f"Plafond ({volume['plafond']} {volume['plafond_ref_unite'] or ''})"
            
            ceiling_style_url = ET.SubElement(ceiling_placemark, 'styleUrl')
            ceiling_style_url.text = '#floorCeilingStyle'
            
            ceiling_polygon = ET.SubElement(ceiling_placemark, 'Polygon')
            ceiling_altitude_mode = ET.SubElement(ceiling_polygon, 'altitudeMode')
            ceiling_altitude_mode.text = 'absolute'
            
            ceiling_outer = ET.SubElement(ceiling_polygon, 'outerBoundaryIs')
            ceiling_ring = ET.SubElement(ceiling_outer, 'LinearRing')
            ceiling_coords = ET.SubElement(ceiling_ring, 'coordinates')
            
            ceiling_coord_strings = []
            # Inverser l'ordre des points pour le plafond (normale vers le bas)
            for lat, lon in reversed(coordinates):
                ceiling_coord_strings.append(f"{lon},{lat},{ceiling_altitude}")
            ceiling_coords.text = ' '.join(ceiling_coord_strings)
            
            # 3. Créer les murs (walls) entre chaque paire de points
            for i in range(len(coordinates) - 1):
                lat1, lon1 = coordinates[i]
                lat2, lon2 = coordinates[i + 1]
                
                wall_placemark = ET.SubElement(volume_folder, 'Placemark')
                wall_name = ET.SubElement(wall_placemark, 'name')
                wall_name.text = f"Mur {i+1}"
                
                wall_style_url = ET.SubElement(wall_placemark, 'styleUrl')
                wall_style_url.text = '#wallStyle'
                
                wall_polygon = ET.SubElement(wall_placemark, 'Polygon')
                wall_altitude_mode = ET.SubElement(wall_polygon, 'altitudeMode')
                wall_altitude_mode.text = 'absolute'
                
                wall_outer = ET.SubElement(wall_polygon, 'outerBoundaryIs')
                wall_ring = ET.SubElement(wall_outer, 'LinearRing')
                wall_coords = ET.SubElement(wall_ring, 'coordinates')
                
                # Créer un rectangle vertical pour le mur
                # Points dans l'ordre : bas1, bas2, haut2, haut1, bas1 (pour fermer)
                wall_coord_strings = [
                    f"{lon1},{lat1},{floor_altitude}",    # Point 1 au plancher
                    f"{lon2},{lat2},{floor_altitude}",    # Point 2 au plancher
                    f"{lon2},{lat2},{ceiling_altitude}",  # Point 2 au plafond
                    f"{lon1},{lat1},{ceiling_altitude}",  # Point 1 au plafond
                    f"{lon1},{lat1},{floor_altitude}"     # Retour au point 1 au plancher
                ]
                wall_coords.text = ' '.join(wall_coord_strings)
        
        # Convertir en chaîne XML formatée
        rough_string = ET.tostring(kml, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent='  ')
    
    def extract_airspace_to_kml(self, lk: str = None, pk: int = None, output_file: str = None) -> bool:
        """
        Extrait un espace aérien et génère un fichier KML
        
        Args:
            lk: Identifiant lk de l'espace (ex: "[LF][TMA LE BOURGET]")
            pk: Identifiant pk de l'espace (ex: 304333)
            output_file: Chemin du fichier KML de sortie
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
            
            # Récupérer les volumes
            volumes = self.get_volumes_for_airspace(airspace['pk'])
            if not volumes:
                print(f"✗ Aucun volume trouvé pour l'espace {airspace['lk']}")
                return False
            
            print(f"✓ {len(volumes)} volume(s) trouvé(s)")
            
            # Générer le KML
            kml_content = self.create_kml_document(airspace, volumes)
            
            # Déterminer le fichier de sortie
            if not output_file:
                # Utiliser la clé lk pour normaliser le nom de fichier
                source_lk = lk if lk else airspace['lk']
                
                # Normaliser la clé lk en nom de fichier valide
                safe_name = re.sub(r'[^\w\-_.]', '_', source_lk)  # Remplacer chars spéciaux par _
                safe_name = re.sub(r'_+', '_', safe_name)         # Fusionner multiples _ en un seul
                safe_name = safe_name.strip('_')                  # Supprimer _ en début/fin
                
                output_file = f"{safe_name}.kml"
            
            # Écrire le fichier
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            print(f"✓ Fichier KML généré: {output_file}")
            return True
            
        except Exception as e:
            print(f"✗ Erreur lors de l'extraction: {e}")
            return False
        
        finally:
            self.close_connection()

def main():
    """Point d'entrée principal du script"""
    parser = argparse.ArgumentParser(
        description="Extrait un espace aérien XML-SIA et génère un fichier KML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
    python kml_extractor.py --espace-lk "[LF][TMA LE BOURGET]"
    python kml_extractor.py --espace-pk 304333 --output bourget.kml
    python kml_extractor.py --espace-lk "[LF][TMA LE BOURGET]" --output airspace.kml
        """
    )
    
    parser.add_argument('--espace-lk', 
                        help='Identifiant lk de l\'espace aérien (ex: "[LF][TMA LE BOURGET]")')
    parser.add_argument('--espace-pk', type=int,
                        help='Identifiant pk de l\'espace aérien (ex: 304333)')
    parser.add_argument('--output', '-o',
                        help='Fichier KML de sortie (par défaut: clé_lk_normalisée.kml)')
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