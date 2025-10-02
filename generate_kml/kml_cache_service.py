#!/usr/bin/env python3
"""
Service de gestion du cache KML par volume pour XML-SIA
Optimise les performances en cachant les KML générés par volume
"""

import sqlite3
import hashlib
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class KMLCacheService:
    """
    Service de gestion du cache KML en base de données (par volume)
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db_connection = db_connection
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_stores': 0,
            'cache_invalidations': 0
        }
    
    def get_volume_kml(self, volume_pk: int) -> Optional[str]:
        """
        Récupère le contenu KML d'un volume depuis le cache
        
        Args:
            volume_pk: Clé primaire du volume
        
        Returns:
            Contenu KML ou None si non trouvé
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT kml_content FROM kml_cache 
                WHERE volume_ref = ?
            ''', (volume_pk,))
            
            result = cursor.fetchone()
            if result:
                self.stats['cache_hits'] += 1
                return result[0]
            else:
                self.stats['cache_misses'] += 1
                return None
                
        except sqlite3.Error as e:
            print(f"❌ Erreur lecture cache volume {volume_pk}: {e}")
            return None
    
    def store_volume_kml(self, volume_pk: int, kml_content: str) -> bool:
        """
        Stocke le contenu KML d'un volume en cache
        
        Args:
            volume_pk: Clé primaire du volume
            kml_content: Contenu KML à stocker
        
        Returns:
            True si succès, False sinon
        """
        try:
            content_hash = hashlib.sha256(kml_content.encode('utf-8')).hexdigest()
            file_size = len(kml_content.encode('utf-8'))
            
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO kml_cache 
                (volume_ref, kml_content, content_hash, file_size)
                VALUES (?, ?, ?, ?)
            ''', (volume_pk, kml_content, content_hash, file_size))
            
            self.db_connection.commit()
            self.stats['cache_stores'] += 1
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Erreur stockage KML volume {volume_pk}: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue stockage volume {volume_pk}: {e}")
            return False
    
    def is_volume_cached(self, volume_pk: int) -> bool:
        """
        Vérifie si le KML du volume est en cache
        
        Args:
            volume_pk: Clé primaire du volume
        
        Returns:
            True si en cache, False sinon
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT 1 FROM kml_cache WHERE volume_ref = ?
            ''', (volume_pk,))
            
            return cursor.fetchone() is not None
            
        except sqlite3.Error:
            return False
    
    def get_espace_volumes_kml(self, espace_pk: int) -> List[Tuple[int, str]]:
        """
        Récupère tous les KML des volumes d'un espace avec leurs IDs
        
        Args:
            espace_pk: Clé primaire de l'espace
        
        Returns:
            Liste de tuples (volume_pk, kml_content) ordonnés par séquence
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT v.pk, kc.kml_content 
                FROM kml_cache kc
                JOIN volumes v ON kc.volume_ref = v.pk
                JOIN parties p ON v.partie_ref = p.pk
                WHERE p.espace_ref = ?
                ORDER BY v.sequence
            ''', (espace_pk,))
            
            results = cursor.fetchall()
            self.stats['cache_hits'] += len(results)
            return results
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lecture cache espace {espace_pk}: {e}")
            return []
    
    def get_espace_cache_status(self, espace_pk: int) -> Dict[str, int]:
        """
        Retourne le statut de cache pour un espace
        
        Args:
            espace_pk: Clé primaire de l'espace
        
        Returns:
            Dictionnaire avec statistiques de cache
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Total des volumes de l'espace
            cursor.execute('''
                SELECT COUNT(*) FROM volumes v
                JOIN parties p ON v.partie_ref = p.pk
                WHERE p.espace_ref = ?
            ''', (espace_pk,))
            total_volumes = cursor.fetchone()[0]
            
            # Volumes en cache
            cursor.execute('''
                SELECT COUNT(*) FROM kml_cache kc
                JOIN volumes v ON kc.volume_ref = v.pk
                JOIN parties p ON v.partie_ref = p.pk
                WHERE p.espace_ref = ?
            ''', (espace_pk,))
            cached_volumes = cursor.fetchone()[0]
            
            return {
                'total_volumes': total_volumes,
                'cached_volumes': cached_volumes,
                'cache_ratio': cached_volumes / total_volumes if total_volumes > 0 else 0
            }
            
        except sqlite3.Error as e:
            print(f"❌ Erreur statut cache espace {espace_pk}: {e}")
            return {'total_volumes': 0, 'cached_volumes': 0, 'cache_ratio': 0}
    
    def invalidate_volume_cache(self, volume_pk: int) -> bool:
        """
        Invalide le cache KML pour un volume
        
        Args:
            volume_pk: Clé primaire du volume
        
        Returns:
            True si succès, False sinon
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('DELETE FROM kml_cache WHERE volume_ref = ?', (volume_pk,))
            deleted_count = cursor.rowcount
            self.db_connection.commit()
            
            if deleted_count > 0:
                self.stats['cache_invalidations'] += 1
            
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Erreur invalidation cache volume {volume_pk}: {e}")
            return False
    
    def invalidate_espace_cache(self, espace_pk: int) -> int:
        """
        Invalide le cache KML pour tous les volumes d'un espace
        
        Args:
            espace_pk: Clé primaire de l'espace
        
        Returns:
            Nombre de volumes invalidés
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                DELETE FROM kml_cache 
                WHERE volume_ref IN (
                    SELECT v.pk FROM volumes v
                    JOIN parties p ON v.partie_ref = p.pk
                    WHERE p.espace_ref = ?
                )
            ''', (espace_pk,))
            
            deleted_count = cursor.rowcount
            self.db_connection.commit()
            
            if deleted_count > 0:
                self.stats['cache_invalidations'] += deleted_count
            
            return deleted_count
            
        except sqlite3.Error as e:
            print(f"❌ Erreur invalidation cache espace {espace_pk}: {e}")
            return 0
    
    def get_cached_volumes_by_criteria(self, classe: str = None, 
                                     espace_type: str = None,
                                     altitude_min: int = None,
                                     altitude_max: int = None) -> List[Tuple[int, str, Dict]]:
        """
        Récupère les volumes en cache selon des critères
        
        Args:
            classe: Classe d'espace (A, B, C, D, E)
            espace_type: Type d'espace (TMA, CTR, etc.)
            altitude_min: Altitude minimum en pieds
            altitude_max: Altitude maximum en pieds
        
        Returns:
            Liste de tuples (volume_pk, kml_content, volume_info)
        """
        try:
            # Construction de la requête avec filtres
            where_conditions = []
            params = []
            
            base_query = '''
                SELECT v.pk, kc.kml_content, v.lk, v.classe, v.plafond, v.plancher,
                       e.nom as espace_nom, e.type_espace
                FROM kml_cache kc
                JOIN volumes v ON kc.volume_ref = v.pk
                JOIN parties p ON v.partie_ref = p.pk
                JOIN espaces e ON p.espace_ref = e.pk
            '''
            
            if classe:
                where_conditions.append('v.classe = ?')
                params.append(classe)
            
            if espace_type:
                where_conditions.append('e.type_espace LIKE ?')
                params.append(f'%{espace_type}%')
            
            if altitude_min is not None:
                where_conditions.append('CAST(v.plancher AS INTEGER) >= ?')
                params.append(altitude_min)
            
            if altitude_max is not None:
                where_conditions.append('CAST(v.plafond AS INTEGER) <= ?')
                params.append(altitude_max)
            
            if where_conditions:
                query = base_query + ' WHERE ' + ' AND '.join(where_conditions)
            else:
                query = base_query
            
            query += ' ORDER BY e.nom, v.sequence'
            
            cursor = self.db_connection.cursor()
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                volume_pk, kml_content = row[0], row[1]
                volume_info = {
                    'lk': row[2],
                    'classe': row[3],
                    'plafond': row[4],
                    'plancher': row[5],
                    'espace_nom': row[6],
                    'espace_type': row[7]
                }
                results.append((volume_pk, kml_content, volume_info))
            
            return results
            
        except sqlite3.Error as e:
            print(f"❌ Erreur recherche cache par critères: {e}")
            return []
    
    def cleanup_orphaned_cache(self) -> int:
        """
        Nettoie les entrées de cache orphelines (volumes supprimés)
        
        Returns:
            Nombre d'entrées supprimées
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                DELETE FROM kml_cache 
                WHERE volume_ref NOT IN (SELECT pk FROM volumes)
            ''')
            
            deleted_count = cursor.rowcount
            self.db_connection.commit()
            
            return deleted_count
            
        except sqlite3.Error as e:
            print(f"❌ Erreur nettoyage cache orphelin: {e}")
            return 0
    
    def get_cache_statistics(self) -> Dict:
        """
        Retourne les statistiques complètes du cache
        
        Returns:
            Dictionnaire avec toutes les statistiques
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*), SUM(file_size), AVG(file_size) FROM kml_cache")
            general_stats = cursor.fetchone()
            
            # Statistiques par classe
            cursor.execute('''
                SELECT v.classe, COUNT(*), SUM(kc.file_size)
                FROM kml_cache kc
                JOIN volumes v ON kc.volume_ref = v.pk
                GROUP BY v.classe
                ORDER BY COUNT(*) DESC
            ''')
            class_stats = cursor.fetchall()
            
            # Statistiques temporelles
            cursor.execute('''
                SELECT 
                    MIN(generated_at) as oldest,
                    MAX(generated_at) as newest,
                    COUNT(CASE WHEN generated_at > datetime('now', '-1 day') THEN 1 END) as last_24h
                FROM kml_cache
            ''')
            time_stats = cursor.fetchone()
            
            return {
                'session_stats': self.stats.copy(),
                'total_entries': general_stats[0] or 0,
                'total_size_bytes': general_stats[1] or 0,
                'average_size_bytes': general_stats[2] or 0,
                'class_distribution': [{'classe': row[0], 'count': row[1], 'size': row[2]} 
                                     for row in class_stats],
                'oldest_entry': time_stats[0],
                'newest_entry': time_stats[1],
                'entries_last_24h': time_stats[2] or 0
            }
            
        except sqlite3.Error as e:
            print(f"❌ Erreur statistiques cache: {e}")
            return {'error': str(e)}
    
    def reset_session_stats(self):
        """Remet à zéro les statistiques de session"""
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_stores': 0,
            'cache_invalidations': 0
        }