#!/usr/bin/env python3
"""
Générateur KML pour espaces aériens XML-SIA - Nouvelle structure

Usage:
    python generate_kml.py --espace-lk "[LF][TMA LE BOURGET]" --output airspace.kml
    python generate_kml.py --espace-pk 304333 --output airspace.kml
"""

import argparse
import sys
from extractor import KMLExtractor

def main():
    parser = argparse.ArgumentParser(
        description="Générateur KML pour espaces aériens XML-SIA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python generate_kml.py --espace-lk "[LF][TMA LE BOURGET]" --output bourget.kml
  python generate_kml.py --espace-pk 304333 --output espace.kml
  
Pour lister les espaces disponibles, utilisez :
  python extraction/list_entities.py --type espace --keyword TMA
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--espace-lk', type=str, 
                      help='Identifiant lk de l\'espace aérien (ex: "[LF][TMA LE BOURGET]")')
    group.add_argument('--espace-pk', type=int,
                      help='Identifiant pk de l\'espace aérien')
    
    parser.add_argument('--output', type=str, default='airspace.kml',
                       help='Fichier KML de sortie (défaut: airspace.kml)')
    parser.add_argument('--database', type=str, default='sia_database.db',
                       help='Chemin vers la base de données SQLite (défaut: sia_database.db)')
    
    args = parser.parse_args()
    
    # Créer l'extracteur
    extractor = KMLExtractor(args.database)
    
    if not extractor.connect_database():
        print("✗ Impossible de se connecter à la base de données")
        return 1
    
    try:
        # Extraction par lk ou pk
        if args.espace_lk:
            airspace = extractor.get_airspace_by_lk(args.espace_lk)
            if not airspace:
                print(f"✗ Espace aérien non trouvé: {args.espace_lk}")
                return 1
        else:
            airspace = extractor.get_airspace_by_pk(args.espace_pk)
            if not airspace:
                print(f"✗ Espace aérien non trouvé avec pk: {args.espace_pk}")
                return 1
        
        print(f"✓ Espace trouvé: {airspace['nom']} ({airspace['lk']})")
        
        # Récupérer les volumes
        volumes = extractor.get_volumes_for_airspace(airspace['pk'])
        if not volumes:
            print("✗ Aucun volume trouvé pour cet espace")
            return 1
        
        print(f"✓ {len(volumes)} volume(s) trouvé(s)")
        
        # Générer le KML
        kml_content = extractor.create_kml_document(airspace, volumes)
        
        # Sauvegarder
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(kml_content)
        
        print(f"✓ Fichier KML généré: {args.output}")
        return 0
        
    except Exception as e:
        print(f"✗ Erreur lors de la génération: {e}")
        return 1
    finally:
        extractor.close_connection()

if __name__ == "__main__":
    sys.exit(main())