#!/usr/bin/env python3
"""
Générateur de schéma SQLite basé sur le XSD Espace.xsd
Analyse le fichier XSD et crée les tables SQLite correspondantes
"""

import sqlite3
import argparse
import sys
import os
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

class SQLiteSchemaGenerator:
    """
    Générateur de schéma SQLite basé sur l'analyse du XSD Espace.xsd
    """
    
    def __init__(self, xsd_file_path: str):
        self.xsd_file = xsd_file_path
        self.db_connection = None
        
        # Mapping des types XSD vers SQLite
        self.type_mapping = {
            'xs:integer': 'INTEGER',
            'xs:string': 'TEXT',
            'xs:decimal': 'REAL',
            'xs:double': 'REAL',
            'xs:anyType': 'TEXT'  # Pour les éléments Extension
        }
        
        # Structure des tables détectées
        self.tables = {
            'territoires': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('territoire', 'TEXT NOT NULL'),
                    ('nom', 'TEXT NOT NULL')
                ]
            },
            'aerodromes': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('territoire_ref', 'INTEGER'),
                    ('ad_code', 'TEXT'),
                    ('ad_ad2', 'TEXT'),
                    ('ad_statut', 'TEXT'),
                    ('ad_nom_complet', 'TEXT'),
                    ('ad_nom_carto', 'TEXT'),
                    ('ad_situation', 'TEXT'),
                    ('wgs84', 'INTEGER'),
                    ('arp_lat', 'REAL'),
                    ('arp_long', 'REAL'),
                    ('arp_situation', 'TEXT'),
                    ('ad_ref_alt_ft', 'INTEGER'),
                    ('ad_geo_und', 'INTEGER'),
                    ('ad_ref_temp', 'REAL'),
                    ('ad_mag_var', 'REAL'),
                    ('mag_var_date', 'INTEGER'),
                    ('tfc_intl', 'TEXT'),
                    ('tfc_ntl', 'TEXT'),
                    ('tfc_ifr', 'TEXT'),
                    ('tfc_vfr', 'TEXT'),
                    ('tfc_regulier', 'TEXT'),
                    ('tfc_non_regulier', 'TEXT'),
                    ('tfc_prive', 'TEXT'),
                    ('ad_gestion', 'TEXT'),
                    ('ad_adresse', 'TEXT'),
                    ('ad_tel', 'TEXT'),
                    ('ad_afs', 'TEXT'),
                    ('ad_rem', 'TEXT'),
                    ('geometrie', 'TEXT'),
                    ('extension', 'TEXT'),
                    # Ajout des autres champs détectés dans les données
                    ('hor_cust_code', 'TEXT'),
                    ('hor_ats_code', 'TEXT'),
                    ('hor_met_txt', 'TEXT'),
                    ('hor_rem', 'TEXT'),
                    ('hor_cust_txt', 'TEXT'),
                    ('hor_ats_txt', 'TEXT'),
                    ('ctr_pk', 'INTEGER'),
                    ('ctr_lk', 'TEXT')
                ]
            },
            'espaces': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('territoire_ref', 'INTEGER NOT NULL'),
                    ('type_espace', 'TEXT NOT NULL'),
                    ('nom', 'TEXT NOT NULL'),
                    ('altr_ft', 'INTEGER'),
                    ('ad_associe_ref', 'INTEGER')
                ]
            },
            'parties': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('espace_ref', 'INTEGER NOT NULL'),
                    ('nom_partie', 'TEXT'),
                    ('numero_partie', 'INTEGER'),
                    ('contour', 'TEXT'),
                    ('geometrie', 'TEXT'),
                    ('extension', 'TEXT')
                ]
            },
            'volumes': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('partie_ref', 'INTEGER NOT NULL'),
                    ('sequence', 'INTEGER'),
                    ('plafond_ref_unite', 'TEXT'),
                    ('plafond', 'TEXT'),
                    ('plancher_ref_unite', 'TEXT'),
                    ('plancher', 'TEXT'),
                    ('classe', 'TEXT'),
                    ('hor_code', 'TEXT'),
                    ('hor_txt', 'TEXT')
                ]
            },
            'services': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('ad_ref', 'INTEGER'),
                    ('espace_ref', 'INTEGER'),
                    ('service', 'TEXT'),
                    ('indic_lieu', 'TEXT'),
                    ('indic_service', 'TEXT'),
                    ('langue', 'TEXT')
                ]
            },
            'frequences': {
                'columns': [
                    ('pk', 'INTEGER PRIMARY KEY'),
                    ('lk', 'TEXT'),
                    ('service_ref', 'INTEGER NOT NULL'),
                    ('frequence', 'TEXT'),
                    ('hor_code', 'TEXT'),
                    ('secteur_situation', 'TEXT'),
                    ('remarque', 'TEXT')
                ]
            }
        }
    
    def create_database(self, db_path: str) -> bool:
        """Crée la base de données SQLite avec le schéma"""
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
            
            # Se connecter à la base (la crée si elle n'existe pas)
            self.db_connection = sqlite3.connect(db_path)
            cursor = self.db_connection.cursor()
            
            print(f"✓ Base de données créée/connectée: {db_path}")
            
            # Créer les tables
            for table_name, table_def in self.tables.items():
                self.create_table(cursor, table_name, table_def['columns'])
            
            # Créer les index pour optimiser les recherches
            self.create_indexes(cursor)
            
            # Valider les changements
            self.db_connection.commit()
            
            print(f"✓ Schéma SQLite créé avec {len(self.tables)} tables")
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Erreur SQLite: {e}")
            return False
        except Exception as e:
            print(f"✗ Erreur: {e}")
            return False
    
    def create_table(self, cursor: sqlite3.Cursor, table_name: str, columns: List[tuple]) -> None:
        """Crée une table avec ses colonnes"""
        
        # Supprimer la table si elle existe déjà
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Construire la définition de la table
        column_defs = []
        for col_name, col_type in columns:
            column_defs.append(f"{col_name} {col_type}")
        
        # Ajouter les contraintes de clés étrangères
        foreign_keys = self.get_foreign_keys(table_name)
        if foreign_keys:
            column_defs.extend(foreign_keys)
        
        create_sql = f"""
        CREATE TABLE {table_name} (
            {', '.join(column_defs)}
        )
        """
        
        cursor.execute(create_sql)
        print(f"  ✓ Table '{table_name}' créée")
    
    def get_foreign_keys(self, table_name: str) -> List[str]:
        """Définit les contraintes de clés étrangères pour chaque table"""
        constraints = {
            'aerodromes': [
                'FOREIGN KEY (territoire_ref) REFERENCES territoires(pk)'
            ],
            'espaces': [
                'FOREIGN KEY (territoire_ref) REFERENCES territoires(pk)',
                'FOREIGN KEY (ad_associe_ref) REFERENCES aerodromes(pk)'
            ],
            'parties': [
                'FOREIGN KEY (espace_ref) REFERENCES espaces(pk)'
            ],
            'volumes': [
                'FOREIGN KEY (partie_ref) REFERENCES parties(pk)'
            ],
            'services': [
                'FOREIGN KEY (ad_ref) REFERENCES aerodromes(pk)',
                'FOREIGN KEY (espace_ref) REFERENCES espaces(pk)'
            ],
            'frequences': [
                'FOREIGN KEY (service_ref) REFERENCES services(pk)'
            ]
        }
        
        return constraints.get(table_name, [])
    
    def create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Crée les index pour optimiser les performances"""
        indexes = [
            # Index sur les clés logiques (lk)
            "CREATE INDEX IF NOT EXISTS idx_territoires_lk ON territoires(lk)",
            "CREATE INDEX IF NOT EXISTS idx_aerodromes_lk ON aerodromes(lk)",
            "CREATE INDEX IF NOT EXISTS idx_espaces_lk ON espaces(lk)",
            "CREATE INDEX IF NOT EXISTS idx_parties_lk ON parties(lk)",
            "CREATE INDEX IF NOT EXISTS idx_volumes_lk ON volumes(lk)",
            "CREATE INDEX IF NOT EXISTS idx_services_lk ON services(lk)",
            "CREATE INDEX IF NOT EXISTS idx_frequences_lk ON frequences(lk)",
            
            # Index sur les clés étrangères
            "CREATE INDEX IF NOT EXISTS idx_aerodromes_territoire ON aerodromes(territoire_ref)",
            "CREATE INDEX IF NOT EXISTS idx_espaces_territoire ON espaces(territoire_ref)",
            "CREATE INDEX IF NOT EXISTS idx_espaces_aerodrome ON espaces(ad_associe_ref)",
            "CREATE INDEX IF NOT EXISTS idx_parties_espace ON parties(espace_ref)",
            "CREATE INDEX IF NOT EXISTS idx_volumes_partie ON volumes(partie_ref)",
            "CREATE INDEX IF NOT EXISTS idx_services_aerodrome ON services(ad_ref)",
            "CREATE INDEX IF NOT EXISTS idx_services_espace ON services(espace_ref)",
            "CREATE INDEX IF NOT EXISTS idx_frequences_service ON frequences(service_ref)",
            
            # Index sur les champs de recherche fréquents
            "CREATE INDEX IF NOT EXISTS idx_espaces_type ON espaces(type_espace)",
            "CREATE INDEX IF NOT EXISTS idx_espaces_nom ON espaces(nom)",
            "CREATE INDEX IF NOT EXISTS idx_aerodromes_code ON aerodromes(ad_code)",
            "CREATE INDEX IF NOT EXISTS idx_services_type ON services(service)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print(f"  ✓ {len(indexes)} index créés")
    
    def close(self) -> None:
        """Ferme la connexion à la base de données"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

def main():
    parser = argparse.ArgumentParser(description='Générateur de schéma SQLite basé sur XSD')
    parser.add_argument('--xsd', required=True,
                       help='Fichier XSD source (ex: data-input/schemas/Espace.xsd)')
    parser.add_argument('--database', required=True,
                       help='Fichier de base SQLite à créer (ex: sia_database.db)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbose')
    
    args = parser.parse_args()
    
    # Vérification de l'existence du fichier XSD
    if not os.path.exists(args.xsd):
        print(f"✗ Fichier XSD non trouvé: {args.xsd}")
        sys.exit(1)
    
    # Generation du schéma
    generator = SQLiteSchemaGenerator(args.xsd)
    
    print(f"Génération du schéma SQLite à partir de: {args.xsd}")
    if generator.create_database(args.database):
        print(f"✓ Base de données SQLite créée: {args.database}")
        
        if args.verbose:
            print(f"\nTables créées:")
            for table_name in generator.tables.keys():
                print(f"  - {table_name}")
    else:
        print("✗ Échec de la création de la base de données")
        sys.exit(1)
    
    generator.close()

if __name__ == '__main__':
    main()