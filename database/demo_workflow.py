#!/usr/bin/env python3
"""
Script de démonstration complète du workflow XML-SIA vers SQLite
Utilise TMA_LE_BOURGET comme exemple
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    print("-" * 60)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        print(f"✅ {description} - Succès")
    else:
        print(f"❌ {description} - Échec")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    
    return True

def main():
    """Workflow de démonstration complet"""
    print("=" * 70)
    print("🚀 DÉMONSTRATION WORKFLOW XML-SIA vers SQLite")
    print("=" * 70)
    
    # Configuration
    python_exe = "C:/Users/franc/dev/xml-sia/.venv/Scripts/python.exe"
    xml_source = "data-input/XML_SIA_2025-10-02.xml"
    identifier = "[LF][TMA LE BOURGET]"
    extracted_xml = "data-output/TMA_LE_BOURGET.xml"
    xsd_file = "data-input/schemas/Espace.xsd"
    database_file = "sia_demo.db"
    
    # Supprimer l'ancienne base pour une démo propre
    if os.path.exists(database_file):
        os.remove(database_file)
        print(f"🗑️  Ancienne base supprimée: {database_file}")
    
    # Étape 1: Extraction de l'espace aérien
    if not run_command(
        f'{python_exe} tools/extract_espace.py --input "{xml_source}" --identifier "{identifier}" --output "{extracted_xml}"',
        "Extraction de la TMA LE BOURGET"
    ):
        return False
    
    # Étape 2: Génération du schéma SQLite
    if not run_command(
        f'{python_exe} database/schema_generator.py --xsd "{xsd_file}" --database "{database_file}" --verbose',
        "Génération du schéma SQLite"
    ):
        return False
    
    # Étape 3: Import des données XML
    if not run_command(
        f'{python_exe} database/xml_importer.py --xml "{extracted_xml}" --database "{database_file}" --verbose',
        "Import des données XML"
    ):
        return False
    
    # Étape 4: Vérification des données
    if not run_command(
        f'{python_exe} database/verify_data.py',
        "Vérification des données importées"
    ):
        return False
    
    print("\n" + "=" * 70)
    print("🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 70)
    print(f"📁 Base de données créée: {database_file}")
    print(f"📄 XML extrait: {extracted_xml}")
    print(f"📊 Schéma basé sur: {xsd_file}")
    print("\n💡 Vous pouvez maintenant:")
    print(f"   - Interroger la base avec sqlite3 {database_file}")
    print(f"   - Examiner les données avec database/verify_data.py")
    print(f"   - Utiliser les services pour d'autres extractions")
    
    return True

if __name__ == '__main__':
    if not main():
        sys.exit(1)