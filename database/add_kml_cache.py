#!/usr/bin/env python3
"""
Migration pour ajouter la table kml_cache à la base de données XML-SIA
Permet le stockage du cache KML par volume pour optimiser les performances
"""

import sqlite3
import argparse
import sys
import os

def add_kml_cache_table(database_path: str, verbose: bool = False) -> bool:
    """
    Ajoute la table kml_cache à la base de données existante
    
    Args:
        database_path: Chemin vers la base SQLite
        verbose: Mode verbeux
    
    Returns:
        True si succès, False sinon
    """
    try:
        if not os.path.exists(database_path):
            print(f"❌ Base de données non trouvée: {database_path}")
            return False
        
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        if verbose:
            print(f"🔗 Connexion à la base: {database_path}")
        
        # Vérifier si la table existe déjà
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='kml_cache'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table kml_cache existe déjà")
            conn.close()
            return True
        
        # Créer la table kml_cache
        if verbose:
            print("📋 Création de la table kml_cache...")
        
        cursor.execute('''
            CREATE TABLE kml_cache (
                pk INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_ref INTEGER NOT NULL,
                kml_content TEXT NOT NULL,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                content_hash TEXT NOT NULL,
                file_size INTEGER,
                FOREIGN KEY (volume_ref) REFERENCES volumes(pk),
                UNIQUE(volume_ref)
            )
        ''')
        
        # Créer les index
        if verbose:
            print("🔍 Création des index...")
        
        cursor.execute('CREATE INDEX idx_kml_cache_volume_ref ON kml_cache(volume_ref)')
        cursor.execute('CREATE INDEX idx_kml_cache_hash ON kml_cache(content_hash)')
        cursor.execute('CREATE INDEX idx_kml_cache_generated_at ON kml_cache(generated_at)')
        
        # Valider les changements
        conn.commit()
        
        # Vérification finale
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'kml_cache%'")
        objects_created = cursor.fetchone()[0]
        
        conn.close()
        
        if verbose:
            print(f"✅ Migration terminée: {objects_created} objets créés (table + index)")
        else:
            print("✅ Table kml_cache créée avec succès")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def show_cache_stats(database_path: str) -> bool:
    """
    Affiche les statistiques de la table kml_cache
    
    Args:
        database_path: Chemin vers la base SQLite
    
    Returns:
        True si succès, False sinon
    """
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='kml_cache'
        """)
        
        if not cursor.fetchone():
            print("❌ Table kml_cache n'existe pas")
            return False
        
        # Statistiques générales
        cursor.execute("SELECT COUNT(*) FROM kml_cache")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(file_size) FROM kml_cache")
        total_size = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(file_size) FROM kml_cache")
        avg_size = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT MIN(generated_at), MAX(generated_at) 
            FROM kml_cache
        """)
        date_range = cursor.fetchone()
        
        print("\n📊 Statistiques de cache KML:")
        print("=" * 50)
        print(f"  Entrées en cache: {total_entries}")
        print(f"  Taille totale: {total_size:,} octets ({total_size/1024:.1f} KB)")
        print(f"  Taille moyenne: {avg_size:.0f} octets")
        
        if date_range[0]:
            print(f"  Période: {date_range[0]} → {date_range[1]}")
        
        # Top 5 des plus gros KML
        cursor.execute("""
            SELECT kc.volume_ref, kc.file_size, v.lk, kc.generated_at
            FROM kml_cache kc
            JOIN volumes v ON kc.volume_ref = v.pk
            ORDER BY kc.file_size DESC
            LIMIT 5
        """)
        
        top_volumes = cursor.fetchall()
        if top_volumes:
            print("\n🔝 Top 5 volumes par taille KML:")
            for vol_ref, size, lk, gen_at in top_volumes:
                print(f"  Volume {vol_ref}: {size:,} octets - {lk or 'N/A'}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Migration pour ajouter le cache KML par volume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python add_kml_cache.py --database sia_database.db
  python add_kml_cache.py --database sia_database.db --stats
  python add_kml_cache.py --database sia_database.db --verbose
        """
    )
    
    parser.add_argument('--database', type=str, default='sia_database.db',
                       help='Chemin vers la base SQLite (défaut: sia_database.db)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbeux')
    parser.add_argument('--stats', action='store_true',
                       help='Afficher les statistiques de cache existant')
    
    args = parser.parse_args()
    
    if args.stats:
        success = show_cache_stats(args.database)
    else:
        success = add_kml_cache_table(args.database, args.verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())