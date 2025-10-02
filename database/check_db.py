#!/usr/bin/env python3
"""
Script pour vérifier la structure de la base de données SQLite
"""

import sqlite3
import sys

def check_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables créées: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        # Vérifier la structure de la table espaces
        print(f"\nStructure de la table 'espaces':")
        cursor.execute("PRAGMA table_info(espaces)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
        
        # Vérifier les index
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"\nIndex créés: {len(indexes)}")
        for idx in indexes[:5]:  # Afficher les 5 premiers
            print(f"  - {idx}")
        if len(indexes) > 5:
            print(f"  ... et {len(indexes) - 5} autres")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == '__main__':
    db_path = 'sia_database.db'
    check_database(db_path)