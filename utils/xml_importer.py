#!/usr/bin/env python3
"""
Importeur XML vers SQLite pour les données XML-SIA
Charge les données XML dans les tables SQLite créées par schema_generator.py
"""

import sqlite3
import argparse
import sys
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any

class XMLImporter:
    """
    Importeur de données XML-SIA vers SQLite
    """
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.db_connection = None
        self.stats = {
            'territoires': 0,
            'aerodromes': 0,
            'espaces': 0,
            'parties': 0,
            'volumes': 0,
            'services': 0,
            'frequences': 0
        }
    
    def connect_database(self) -> bool:
        """Se connecte à la base de données SQLite"""
        try:
            if not os.path.exists(self.database_path):
                print(f"✗ Base de données non trouvée: {self.database_path}")
                print("  Utilisez d'abord schema_generator.py pour créer la base")
                return False
            
            self.db_connection = sqlite3.connect(self.database_path)
            print(f"✓ Connecté à la base: {self.database_path}")
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Erreur de connexion SQLite: {e}")
            return False
    
    def import_xml_file(self, xml_path: str) -> bool:
        """Importe les données d'un fichier XML dans la base SQLite"""
        try:
            # Charger le XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            print(f"✓ Fichier XML chargé: {xml_path}")
            
            cursor = self.db_connection.cursor()
            
            # Commencer une transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Importer chaque type d'entité dans l'ordre des dépendances
            self.import_territoires(cursor, root)
            self.import_aerodromes(cursor, root)
            self.import_espaces(cursor, root)
            self.import_parties(cursor, root)
            self.import_volumes(cursor, root)
            self.import_services(cursor, root)
            self.import_frequences(cursor, root)
            
            # Valider la transaction
            cursor.execute("COMMIT")
            
            print(f"✓ Import terminé avec succès")
            self.print_import_stats()
            return True
            
        except ET.ParseError as e:
            print(f"✗ Erreur de parsing XML: {e}")
            return False
        except sqlite3.Error as e:
            print(f"✗ Erreur SQLite: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            return False
        except Exception as e:
            print(f"✗ Erreur: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    def import_territoires(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les territoires"""
        territoires_section = root.find('TerritoireS')
        if territoires_section is None:
            return
            
        for territoire in territoires_section.findall('Territoire'):
            pk = int(territoire.get('pk'))
            lk = territoire.get('lk')
            territoire_code = territoire.find('Territoire').text if territoire.find('Territoire') is not None else None
            nom = territoire.find('Nom').text if territoire.find('Nom') is not None else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO territoires 
                (pk, lk, territoire, nom) 
                VALUES (?, ?, ?, ?)
            """, (pk, lk, territoire_code, nom))
            
            self.stats['territoires'] += 1
    
    def import_aerodromes(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les aérodromes"""
        ads_section = root.find('AdS')
        if ads_section is None:
            return
            
        for ad in ads_section.findall('Ad'):
            # Récupérer les attributs de base
            pk = int(ad.get('pk'))
            lk = ad.get('lk')
            
            # Récupérer les références
            territoire_elem = ad.find('Territoire')
            territoire_ref = int(territoire_elem.get('pk')) if territoire_elem is not None else None
            
            ctr_elem = ad.find('Ctr')
            ctr_pk = int(ctr_elem.get('pk')) if ctr_elem is not None else None
            ctr_lk = ctr_elem.get('lk') if ctr_elem is not None else None
            
            # Récupérer tous les champs texte
            def get_text(elem_name: str) -> Optional[str]:
                elem = ad.find(elem_name)
                return elem.text if elem is not None else None
            
            def get_real(elem_name: str) -> Optional[float]:
                elem = ad.find(elem_name)
                try:
                    return float(elem.text) if elem is not None and elem.text else None
                except (ValueError, TypeError):
                    return None
            
            def get_int(elem_name: str) -> Optional[int]:
                elem = ad.find(elem_name)
                try:
                    return int(elem.text) if elem is not None and elem.text else None
                except (ValueError, TypeError):
                    return None
            
            # Insérer l'aérodrome
            cursor.execute("""
                INSERT OR REPLACE INTO aerodromes 
                (pk, lk, territoire_ref, ad_code, ad_ad2, ad_statut, ad_nom_complet, 
                 ad_nom_carto, ad_situation, wgs84, arp_lat, arp_long, arp_situation,
                 ad_ref_alt_ft, ad_geo_und, ad_ref_temp, ad_mag_var, mag_var_date,
                 tfc_intl, tfc_ntl, tfc_ifr, tfc_vfr, tfc_regulier, tfc_non_regulier, 
                 tfc_prive, ad_gestion, ad_adresse, ad_tel, ad_afs, ad_rem,
                 hor_cust_code, hor_ats_code, hor_met_txt, hor_rem, hor_cust_txt, hor_ats_txt,
                 ctr_pk, ctr_lk, geometrie, extension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pk, lk, territoire_ref,
                get_text('AdCode'), get_text('AdAd2'), get_text('AdStatut'),
                get_text('AdNomComplet'), get_text('AdNomCarto'), get_text('AdSituation'),
                get_int('Wgs84'), get_real('ArpLat'), get_real('ArpLong'), get_text('ArpSituation'),
                get_int('AdRefAltFt'), get_int('AdGeoUnd'), get_real('AdRefTemp'),
                get_real('AdMagVar'), get_int('MagVarDate'),
                get_text('TfcIntl'), get_text('TfcNtl'), get_text('TfcIfr'), get_text('TfcVfr'),
                get_text('TfcRegulier'), get_text('TfcNonRegulier'), get_text('TfcPrive'),
                get_text('AdGestion'), get_text('AdAdresse'), get_text('AdTel'),
                get_text('AdAfs'), get_text('AdRem'),
                get_text('HorCustCode'), get_text('HorAtsCode'), get_text('HorMetTxt'),
                get_text('HorRem'), get_text('HorCustTxt'), get_text('HorAtsTxt'),
                ctr_pk, ctr_lk,
                get_text('Geometrie'), get_text('Extension')
            ))
            
            self.stats['aerodromes'] += 1
    
    def import_espaces(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les espaces aériens"""
        espaces_section = root.find('EspaceS')
        if espaces_section is None:
            return
            
        for espace in espaces_section.findall('Espace'):
            pk = int(espace.get('pk'))
            lk = espace.get('lk')
            
            # Récupérer les références
            territoire_elem = espace.find('Territoire')
            territoire_ref = int(territoire_elem.get('pk')) if territoire_elem is not None else None
            
            ad_associe_elem = espace.find('AdAssocie')
            ad_associe_ref = int(ad_associe_elem.get('pk')) if ad_associe_elem is not None else None
            
            # Récupérer les champs
            type_espace = espace.find('TypeEspace').text if espace.find('TypeEspace') is not None else None
            nom = espace.find('Nom').text if espace.find('Nom') is not None else None
            
            altr_ft_elem = espace.find('AltrFt')
            altr_ft = int(altr_ft_elem.text) if altr_ft_elem is not None and altr_ft_elem.text else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO espaces 
                (pk, lk, territoire_ref, type_espace, nom, altr_ft, ad_associe_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pk, lk, territoire_ref, type_espace, nom, altr_ft, ad_associe_ref))
            
            self.stats['espaces'] += 1
    
    def import_parties(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les parties d'espaces"""
        parties_section = root.find('PartieS')
        if parties_section is None:
            return
            
        for partie in parties_section.findall('Partie'):
            pk = int(partie.get('pk'))
            lk = partie.get('lk')
            
            # Référence à l'espace
            espace_elem = partie.find('Espace')
            espace_ref = int(espace_elem.get('pk')) if espace_elem is not None else None
            
            # Champs
            nom_partie = partie.find('NomPartie').text if partie.find('NomPartie') is not None else None
            
            numero_partie_elem = partie.find('NumeroPartie')
            numero_partie = int(numero_partie_elem.text) if numero_partie_elem is not None and numero_partie_elem.text else None
            
            contour = partie.find('Contour').text if partie.find('Contour') is not None else None
            geometrie = partie.find('Geometrie').text if partie.find('Geometrie') is not None else None
            extension = partie.find('Extension').text if partie.find('Extension') is not None else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO parties 
                (pk, lk, espace_ref, nom_partie, numero_partie, contour, geometrie, extension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pk, lk, espace_ref, nom_partie, numero_partie, contour, geometrie, extension))
            
            self.stats['parties'] += 1
    
    def import_volumes(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les volumes"""
        volumes_section = root.find('VolumeS')
        if volumes_section is None:
            return
            
        for volume in volumes_section.findall('Volume'):
            pk = int(volume.get('pk'))
            lk = volume.get('lk')
            
            # Référence à la partie
            partie_elem = volume.find('Partie')
            partie_ref = int(partie_elem.get('pk')) if partie_elem is not None else None
            
            # Champs
            def get_text(elem_name: str) -> Optional[str]:
                elem = volume.find(elem_name)
                return elem.text if elem is not None else None
            
            def get_int(elem_name: str) -> Optional[int]:
                elem = volume.find(elem_name)
                try:
                    return int(elem.text) if elem is not None and elem.text else None
                except (ValueError, TypeError):
                    return None
            
            cursor.execute("""
                INSERT OR REPLACE INTO volumes 
                (pk, lk, partie_ref, sequence, plafond_ref_unite, plafond, 
                 plancher_ref_unite, plancher, classe, hor_code, hor_txt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pk, lk, partie_ref,
                get_int('Sequence'),
                get_text('PlafondRefUnite'), get_text('Plafond'),
                get_text('PlancherRefUnite'), get_text('Plancher'),
                get_text('Classe'), get_text('HorCode'), get_text('HorTxt')
            ))
            
            self.stats['volumes'] += 1
    
    def import_services(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les services"""
        services_section = root.find('ServiceS')
        if services_section is None:
            return
            
        for service in services_section.findall('Service'):
            pk = int(service.get('pk'))
            lk = service.get('lk')
            
            # Références optionnelles
            ad_elem = service.find('Ad')
            ad_ref = int(ad_elem.get('pk')) if ad_elem is not None else None
            
            espace_elem = service.find('Espace')
            espace_ref = int(espace_elem.get('pk')) if espace_elem is not None else None
            
            # Champs
            def get_text(elem_name: str) -> Optional[str]:
                elem = service.find(elem_name)
                return elem.text if elem is not None else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO services 
                (pk, lk, ad_ref, espace_ref, service, indic_lieu, indic_service, langue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pk, lk, ad_ref, espace_ref,
                get_text('Service'), get_text('IndicLieu'), 
                get_text('IndicService'), get_text('Langue')
            ))
            
            self.stats['services'] += 1
    
    def import_frequences(self, cursor: sqlite3.Cursor, root: ET.Element) -> None:
        """Importe les fréquences"""
        frequences_section = root.find('FrequenceS')
        if frequences_section is None:
            return
            
        for frequence in frequences_section.findall('Frequence'):
            pk = int(frequence.get('pk'))
            lk = frequence.get('lk')
            
            # Référence au service
            service_elem = frequence.find('Service')
            service_ref = int(service_elem.get('pk')) if service_elem is not None else None
            
            # Champs
            def get_text(elem_name: str) -> Optional[str]:
                elem = frequence.find(elem_name)
                return elem.text if elem is not None else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO frequences 
                (pk, lk, service_ref, frequence, hor_code, secteur_situation, remarque)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pk, lk, service_ref,
                get_text('Frequence'), get_text('HorCode'),
                get_text('SecteurSituation'), get_text('Remarque')
            ))
            
            self.stats['frequences'] += 1
    
    def print_import_stats(self) -> None:
        """Affiche les statistiques d'import"""
        print(f"\n=== Statistiques d'import ===")
        total = 0
        for entity_type, count in self.stats.items():
            if count > 0:
                print(f"  {entity_type}: {count} enregistrements")
                total += count
        print(f"  Total: {total} enregistrements importés")
    
    def close(self) -> None:
        """Ferme la connexion à la base de données"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

def main():
    parser = argparse.ArgumentParser(description='Importeur XML vers SQLite pour XML-SIA')
    parser.add_argument('--xml', required=True,
                       help='Fichier XML à importer (ex: data-output/TMA_LE_BOURGET.xml)')
    parser.add_argument('--database', required=True,
                       help='Base de données SQLite (ex: sia_database.db)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbose')
    
    args = parser.parse_args()
    
    # Vérification de l'existence du fichier XML
    if not os.path.exists(args.xml):
        print(f"✗ Fichier XML non trouvé: {args.xml}")
        sys.exit(1)
    
    # Import des données
    importer = XMLImporter(args.database)
    
    if not importer.connect_database():
        sys.exit(1)
    
    print(f"Import des données XML: {args.xml}")
    if importer.import_xml_file(args.xml):
        print(f"✓ Import terminé avec succès")
    else:
        print("✗ Échec de l'import")
        sys.exit(1)
    
    importer.close()

if __name__ == '__main__':
    main()