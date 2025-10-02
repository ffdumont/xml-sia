#!/usr/bin/env python3
"""
Script pour vérifier les données importées dans la base SQLite
"""

import sqlite3
import sys

def check_imported_data(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== Vérification des données importées ===\n")
        
        # Vérifier chaque table
        tables = ['territoires', 'aerodromes', 'espaces', 'parties', 'volumes', 'services', 'frequences']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize()}: {count} enregistrements")
            
            # Afficher un exemple pour les tables avec des données
            if count > 0:
                if table == 'espaces':
                    cursor.execute("SELECT pk, lk, nom, type_espace FROM espaces LIMIT 1")
                    row = cursor.fetchone()
                    if row:
                        print(f"  → Exemple: pk={row[0]}, lk='{row[1]}', nom='{row[2]}', type='{row[3]}'")
                elif table == 'aerodromes':
                    cursor.execute("SELECT pk, lk, ad_nom_complet FROM aerodromes LIMIT 1")
                    row = cursor.fetchone()
                    if row:
                        print(f"  → Exemple: pk={row[0]}, lk='{row[1]}', nom='{row[2]}'")
                elif table == 'services':
                    cursor.execute("SELECT pk, lk, service, indic_lieu FROM services LIMIT 3")
                    rows = cursor.fetchall()
                    for row in rows:
                        print(f"  → Service: pk={row[0]}, type='{row[2]}', lieu='{row[3]}'")
        
        # Vérification des relations
        print(f"\n=== Vérification des relations ===")
        
        # Espace -> Territoire
        cursor.execute("""
            SELECT e.nom, t.nom 
            FROM espaces e 
            JOIN territoires t ON e.territoire_ref = t.pk
        """)
        relations = cursor.fetchall()
        for rel in relations:
            print(f"Espace '{rel[0]}' → Territoire '{rel[1]}'")
        
        # Espace -> Aérodrome
        cursor.execute("""
            SELECT e.nom, a.ad_nom_complet 
            FROM espaces e 
            JOIN aerodromes a ON e.ad_associe_ref = a.pk
        """)
        relations = cursor.fetchall()
        for rel in relations:
            print(f"Espace '{rel[0]}' → Aérodrome '{rel[1]}'")
        
        # Parties -> Espace
        cursor.execute("""
            SELECT p.nom_partie, e.nom 
            FROM parties p 
            JOIN espaces e ON p.espace_ref = e.pk
        """)
        relations = cursor.fetchall()
        for rel in relations:
            print(f"Partie '{rel[0]}' → Espace '{rel[1]}'")
        
        # Services -> Aérodrome
        cursor.execute("""
            SELECT s.service, s.indic_lieu, a.ad_nom_complet 
            FROM services s 
            JOIN aerodromes a ON s.ad_ref = a.pk
        """)
        relations = cursor.fetchall()
        for rel in relations:
            print(f"Service '{rel[0]} {rel[1]}' → Aérodrome '{rel[2]}'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == '__main__':
    db_path = 'sia_database.db'
    check_imported_data(db_path)