#!/usr/bin/env python3
"""
KMLExtractor avancé avec cache par volume pour XML-SIA
Extension du KMLExtractor existant avec système de cache intelligent
"""

import sqlite3
import os
import sys
from typing import List, Dict, Optional, Tuple
from xml.dom import minidom
import xml.etree.ElementTree as ET

# Import des services existants
sys.path.insert(0, os.path.dirname(__file__))
from extractor import KMLExtractor
from color_service import get_space_color
from kml_cache_service import KMLCacheService

class EnhancedKMLExtractor(KMLExtractor):
    """
    KMLExtractor avec cache en base de données par volume
    Optimise les performances et permet la composition flexible de KML
    """
    
    def __init__(self, database_path: str):
        super().__init__(database_path)
        self.cache_service = None
        self.stats = {
            'volumes_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'kml_generated': 0
        }
    
    def connect_database(self) -> bool:
        """Se connecte à la base et initialise le service de cache"""
        if super().connect_database():
            self.cache_service = KMLCacheService(self.db_connection)
            return True
        return False
    
    def create_volume_kml_placemark(self, volume: Dict) -> str:
        """
        Crée un placemark KML pour un volume individuel
        Utilise le KMLExtractor de base pour générer la géométrie
        
        Args:
            volume: Dictionnaire avec les données du volume
        
        Returns:
            Fragment KML <Placemark> pour ce volume
        """
        try:
            # Créer un KML temporaire avec juste ce volume pour extraire son contenu
            espace_info = self.get_espace_by_volume(volume['pk'])
            if not espace_info:
                print(f"❌ Impossible de trouver l'espace pour le volume {volume['pk']}")
                return ""
            
            # Utiliser la méthode de base pour créer le KML du volume
            # En créant un mini-document avec juste ce volume
            temp_airspace = {
                'pk': espace_info['pk'],
                'lk': espace_info['lk'],
                'nom': espace_info['nom'],
                'type_espace': espace_info['type_espace'],
                'altr_ft': None
            }
            
            # Créer le KML avec juste ce volume
            temp_kml = self.create_kml_document(temp_airspace, [volume])
            
            # Extraire TOUS les Placemarks du volume (plancher + plafond)
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(temp_kml)
                placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
                if placemarks:
                    # Déterminer le type d'espace pour les styles appropriés
                    type_espace = espace_info.get('type_espace', 'OTHER').lower()
                    
                    # Concaténer tous les placemarks du volume avec styles corrigés
                    placemark_content = ""
                    for placemark in placemarks:
                        placemark_xml = ET.tostring(placemark, encoding='unicode')
                        
                        # Remplacer les références de style par les styles spécifiques au type
                        placemark_xml = placemark_xml.replace('#wallStyle', f'#{type_espace}WallStyle')
                        placemark_xml = placemark_xml.replace('#floorCeilingStyle', f'#{type_espace}FloorCeilingStyle')
                        placemark_xml = placemark_xml.replace('#defaultStyle', f'#{type_espace}DefaultStyle')
                        
                        placemark_content += placemark_xml + "\n"
                    return placemark_content.strip()
                else:
                    print(f"❌ Aucun Placemark trouvé dans le KML généré pour le volume {volume['pk']}")
                    return ""
            except ET.ParseError as e:
                print(f"❌ Erreur parsing KML pour volume {volume['pk']}: {e}")
                return ""
            
        except Exception as e:
            print(f"❌ Erreur création placemark volume {volume.get('pk')}: {e}")
            return ""
    
    def get_volume_kml_cached(self, volume: Dict, force_regenerate: bool = False) -> Optional[str]:
        """
        Récupère le KML d'un volume avec cache intelligent
        
        Args:
            volume: Dictionnaire avec les données du volume
            force_regenerate: Force la régénération même si en cache
        
        Returns:
            Fragment KML pour ce volume ou None
        """
        volume_pk = volume['pk']
        self.stats['volumes_processed'] += 1
        
        # Vérifier le cache si pas de régénération forcée
        if not force_regenerate and self.cache_service.is_volume_cached(volume_pk):
            cached_kml = self.cache_service.get_volume_kml(volume_pk)
            if cached_kml:
                self.stats['cache_hits'] += 1
                return cached_kml
        
        # Générer le KML du volume
        self.stats['cache_misses'] += 1
        volume_kml = self.create_volume_kml_placemark(volume)
        
        if not volume_kml:
            return None
        
        # Stocker en cache
        if self.cache_service.store_volume_kml(volume_pk, volume_kml):
            self.stats['kml_generated'] += 1
        
        return volume_kml
    
    def extract_airspace_kml_cached(self, espace_lk: str, force_regenerate: bool = False) -> Optional[str]:
        """
        Extrait le KML complet d'un espace avec cache par volume
        
        Args:
            espace_lk: Identifiant lk de l'espace
            force_regenerate: Force la régénération de tous les volumes
        
        Returns:
            KML complet de l'espace ou None
        """
        # Récupérer l'espace
        airspace = self.get_airspace_by_lk(espace_lk)
        if not airspace:
            print(f"❌ Espace non trouvé: {espace_lk}")
            return None
        
        espace_pk = airspace['pk']
        volumes = self.get_volumes_for_airspace(espace_pk)
        if not volumes:
            print(f"❌ Aucun volume trouvé pour l'espace: {espace_lk}")
            return None
        
        print(f"🔄 Traitement de {len(volumes)} volume(s) pour {espace_lk}")
        
        # Récupérer les KML de chaque volume (avec cache)
        volume_kmls = []
        
        for volume in volumes:
            volume_kml = self.get_volume_kml_cached(volume, force_regenerate)
            if volume_kml:
                volume_kmls.append(volume_kml)
        
        if not volume_kmls:
            print(f"❌ Aucun KML généré pour les volumes de {espace_lk}")
            return None
        
        # Statistiques de cache
        cache_ratio = (self.stats['cache_hits'] / self.stats['volumes_processed']) * 100
        print(f"✅ Cache hit: {self.stats['cache_hits']}/{self.stats['volumes_processed']} volumes ({cache_ratio:.1f}%)")
        
        # Combiner les KML des volumes en un KML d'espace complet
        return self.combine_volume_kmls(airspace, volume_kmls)
    
    def combine_volume_kmls(self, airspace: Dict, volume_kmls: List[str]) -> str:
        """
        Combine les KML de volumes individuels en KML d'espace complet
        
        Args:
            airspace: Informations de l'espace aérien
            volume_kmls: Liste des fragments KML des volumes
        
        Returns:
            KML complet combiné
        """
        # Déterminer la couleur appropriée pour cet espace
        from color_service import get_space_color
        type_espace = airspace.get('type_espace', 'OTHER')
        
        # Récupérer la classe du premier volume si disponible
        espace_pk = airspace['pk']
        volumes = self.get_volumes_for_airspace(espace_pk)
        classe = volumes[0].get('classe') if volumes else None
        
        base_color = get_space_color(type_espace, classe, 'kml')
        print(f"  🎨 {type_espace} classe {classe or 'N/A'} → {base_color}")
        
        # En-tête KML avec métadonnées
        kml_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name><![CDATA[{airspace.get('nom', 'Espace aérien')}]]></name>
    <description><![CDATA[
        Identifiant: {airspace.get('lk', 'N/A')}
        Type: {airspace.get('type_espace', 'N/A')}
        Nombre de volumes: {len(volume_kmls)}
        Généré le: {self.get_current_timestamp()}
        Source: XML-SIA / Base SQLite avec cache
    ]]></description>
    
    <!-- Styles avec couleurs appropriées -->
    <Style id="wallStyle">
        <LineStyle>
            <color>ff{base_color[2:]}</color>
            <width>2</width>
        </LineStyle>
        <PolyStyle>
            <color>40{base_color[2:]}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
    </Style>
    
    <Style id="floorCeilingStyle">
        <LineStyle>
            <color>ff{base_color[2:]}</color>
            <width>2</width>
        </LineStyle>
        <PolyStyle>
            <color>60{base_color[2:]}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
    </Style>
    
    <Style id="defaultStyle">
        <PolyStyle>
            <color>{base_color}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
        <LineStyle>
            <color>ff{base_color[2:]}</color>
            <width>2</width>
        </LineStyle>
    </Style>'''
        
        # Corps : tous les volumes
        kml_body = '\\n'.join(volume_kmls)
        
        # Pied avec métadonnées
        kml_footer = f'''
    
    <!-- Statistiques de génération -->
    <!--
        Volumes traités: {self.stats['volumes_processed']}
        Cache hits: {self.stats['cache_hits']}
        Cache misses: {self.stats['cache_misses']}
        KML générés: {self.stats['kml_generated']}
    -->
</Document>
</kml>'''
        
        return kml_header + kml_body + kml_footer
    
    def export_multiple_airspaces(self, espace_lks: List[str], 
                                 output_name: str = "Espaces combinés",
                                 force_regenerate: bool = False) -> Optional[str]:
        """
        Combine plusieurs espaces dans un seul KML
        
        Args:
            espace_lks: Liste des identifiants lk des espaces
            output_name: Nom du document KML final
            force_regenerate: Force la régénération des caches
        
        Returns:
            KML combiné ou None
        """
        print(f"🔄 Export combiné de {len(espace_lks)} espace(s)")
        
        # Définir les styles dynamiques basés sur les types d'espaces réels
        from color_service import get_space_color
        
        # Analyser les types d'espaces pour créer des styles appropriés
        space_types = set()
        space_colors = {}
        
        for espace_lk in espace_lks:
            airspace = self.get_airspace_by_lk(espace_lk)
            if airspace:
                type_espace = airspace.get('type_espace', 'OTHER')
                # Récupérer la classe du premier volume si disponible
                volumes = self.get_volumes_for_airspace(airspace['pk'])
                classe = volumes[0].get('classe') if volumes else None
                
                space_types.add(type_espace)
                color = get_space_color(type_espace, classe, 'kml')
                space_colors[type_espace] = color
                print(f"  🎨 {type_espace} classe {classe or 'N/A'} → {color}")
        
        # Générer les styles pour chaque type d'espace
        styles_html = '\n    <!-- Styles pour espaces aériens -->'
        
        for space_type in space_types:
            color = space_colors[space_type]
            styles_html += f'''
    
    <Style id="{space_type.lower()}WallStyle">
        <LineStyle>
            <color>ff{color[2:]}</color>
            <width>2</width>
        </LineStyle>
        <PolyStyle>
            <color>40{color[2:]}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
    </Style>
    
    <Style id="{space_type.lower()}FloorCeilingStyle">
        <LineStyle>
            <color>ff{color[2:]}</color>
            <width>2</width>
        </LineStyle>
        <PolyStyle>
            <color>60{color[2:]}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
    </Style>
    
    <Style id="{space_type.lower()}DefaultStyle">
        <PolyStyle>
            <color>{color}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
        <LineStyle>
            <color>ff{color[2:]}</color>
            <width>2</width>
        </LineStyle>
    </Style>'''
        
        # En-tête du document combiné
        kml_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name><![CDATA[{output_name}]]></name>
    <description><![CDATA[
        Export combiné de {len(espace_lks)} espace(s) aérien(s)
        Généré le: {self.get_current_timestamp()}
        Source: XML-SIA / Base SQLite avec cache
    ]]></description>{styles_html}'''
        
        all_volume_kmls = []
        processed_spaces = 0
        
        for espace_lk in espace_lks:
            print(f"  📍 Traitement: {espace_lk}")
            
            # Récupérer l'espace et ses volumes
            airspace = self.get_airspace_by_lk(espace_lk)
            if not airspace:
                print(f"    ⚠️ Espace non trouvé: {espace_lk}")
                continue
            
            volumes = self.get_volumes_for_airspace(airspace['pk'])
            if not volumes:
                print(f"    ⚠️ Aucun volume pour: {espace_lk}")
                continue
            
            # Ajouter un dossier pour cet espace
            folder_header = f'''
    <Folder>
        <name><![CDATA[{airspace.get('nom', espace_lk)}]]></name>
        <description><![CDATA[{airspace.get('lk', 'N/A')} - {len(volumes)} volume(s)]]></description>'''
            
            volume_kmls_for_space = []
            for volume in volumes:
                volume_kml = self.get_volume_kml_cached(volume, force_regenerate)
                if volume_kml:
                    # Indenter le contenu du volume pour le dossier
                    indented_kml = '\\n'.join(['    ' + line for line in volume_kml.split('\\n')])
                    volume_kmls_for_space.append(indented_kml)
            
            if volume_kmls_for_space:
                folder_content = folder_header + '\\n'.join(volume_kmls_for_space) + '\\n    </Folder>'
                all_volume_kmls.append(folder_content)
                processed_spaces += 1
                print(f"    ✅ {len(volume_kmls_for_space)} volume(s) traité(s)")
        
        if not all_volume_kmls:
            print("❌ Aucun volume traité pour l'export combiné")
            return None
        
        # Finaliser le document
        kml_body = '\\n'.join(all_volume_kmls)
        kml_footer = '''
</Document>
</kml>'''
        
        # Statistiques finales
        total_cache_ratio = (self.stats['cache_hits'] / max(self.stats['volumes_processed'], 1)) * 100
        print(f"✅ Export terminé: {processed_spaces} espace(s), {self.stats['volumes_processed']} volume(s)")
        print(f"📊 Performance cache: {self.stats['cache_hits']}/{self.stats['volumes_processed']} hits ({total_cache_ratio:.1f}%)")
        
        return kml_header + kml_body + kml_footer
    
    def export_by_criteria(self, classe: str = None, espace_type: str = None,
                          altitude_min: int = None, altitude_max: int = None,
                          output_name: str = "Export par critères") -> Optional[str]:
        """
        Exporte tous les volumes correspondant aux critères spécifiés
        
        Args:
            classe: Classe d'espace (A, B, C, D, E)
            espace_type: Type d'espace (TMA, CTR, etc.)
            altitude_min: Altitude minimum en pieds
            altitude_max: Altitude maximum en pieds
            output_name: Nom du document de sortie
        
        Returns:
            KML filtré ou None
        """
        print(f"🔍 Export par critères: classe={classe}, type={espace_type}, alt={altitude_min}-{altitude_max}")
        
        # Récupérer les volumes en cache correspondant aux critères
        cached_volumes = self.cache_service.get_cached_volumes_by_criteria(
            classe=classe,
            espace_type=espace_type,
            altitude_min=altitude_min,
            altitude_max=altitude_max
        )
        
        if not cached_volumes:
            print("❌ Aucun volume en cache ne correspond aux critères")
            return None
        
        print(f"✅ {len(cached_volumes)} volume(s) trouvé(s) en cache")
        
        # Construire la description des critères
        criteria_desc = []
        if classe:
            criteria_desc.append(f"Classe: {classe}")
        if espace_type:
            criteria_desc.append(f"Type: {espace_type}")
        if altitude_min:
            criteria_desc.append(f"Alt min: {altitude_min}ft")
        if altitude_max:
            criteria_desc.append(f"Alt max: {altitude_max}ft")
        
        criteria_text = ", ".join(criteria_desc) if criteria_desc else "Tous"
        
        # En-tête KML
        kml_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name><![CDATA[{output_name}]]></name>
    <description><![CDATA[
        Export filtré par critères: {criteria_text}
        Nombre de volumes: {len(cached_volumes)}
        Généré le: {self.get_current_timestamp()}
        Source: Cache KML
    ]]></description>'''
        
        # Corps avec tous les volumes filtrés
        volume_kmls = [kml_content for _, kml_content, _ in cached_volumes]
        kml_body = '\\n'.join(volume_kmls)
        
        # Pied
        kml_footer = '''
</Document>
</kml>'''
        
        return kml_header + kml_body + kml_footer
    
    def get_current_timestamp(self) -> str:
        """Retourne un timestamp formaté pour les métadonnées"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_espace_by_volume(self, volume_pk: int) -> Dict:
        """
        Récupère les informations de l'espace pour un volume donné
        
        Args:
            volume_pk: Clé primaire du volume
        
        Returns:
            Dictionnaire avec les informations de l'espace
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT e.pk, e.lk, e.nom, e.type_espace
                FROM espaces e
                JOIN parties p ON e.pk = p.espace_ref
                JOIN volumes v ON p.pk = v.partie_ref
                WHERE v.pk = ?
            ''', (volume_pk,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'pk': result[0],
                    'lk': result[1],
                    'nom': result[2],
                    'type_espace': result[3]
                }
            return {}
            
        except sqlite3.Error as e:
            print(f"❌ Erreur récupération espace pour volume {volume_pk}: {e}")
            return {}
    
    def get_cache_statistics(self) -> Dict:
        """Retourne les statistiques de cache et de session"""
        cache_stats = self.cache_service.get_cache_statistics() if self.cache_service else {}
        cache_stats['session_stats'] = self.stats.copy()
        return cache_stats
    
    def reset_session_stats(self):
        """Remet à zéro les statistiques de session"""
        self.stats = {
            'volumes_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'kml_generated': 0
        }
        if self.cache_service:
            self.cache_service.reset_session_stats()