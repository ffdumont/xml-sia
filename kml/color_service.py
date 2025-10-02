"""
Service de sélection de couleurs pour les espaces aériens
Basé sur les règles OACI et le fichier de configuration color_rules.csv
"""

import csv
import os
from typing import Dict, Tuple, Optional
from pathlib import Path


class ColorService:
    """Service pour attribuer des couleurs aux espaces aériens selon leur type et classe."""
    
    def __init__(self, config_file: str = None):
        """
        Initialise le service de couleurs.
        
        Args:
            config_file: Chemin vers le fichier de configuration des couleurs.
                        Si None, utilise le fichier par défaut dans config/color_rules.csv
        """
        if config_file is None:
            # Utilise le chemin relatif depuis le répertoire du script ou du projet
            current_dir = Path(__file__).parent
            config_file = current_dir.parent / "config" / "color_rules.csv"
        
        self.config_file = config_file
        self.color_rules: Dict[Tuple[str, str], Dict[str, str]] = {}
        self.default_colors = {
            'kml': 'ff888888',  # Gris par défaut
            'hex': '#888888',
            'description': 'Couleur par défaut'
        }
        
        self._load_color_rules()
    
    def _load_color_rules(self):
        """Charge les règles de couleurs depuis le fichier CSV."""
        try:
            with open(self.config_file, 'r', encoding='latin-1') as file:
                reader = csv.reader(file, delimiter=';')
                for line_num, row in enumerate(reader, 1):
                    # Ignore les lignes de commentaire et les lignes vides
                    if not row or row[0].startswith('#') or len(row) < 4:
                        continue
                    
                    try:
                        type_espace = row[0].strip()
                        classe = row[1].strip() if row[1].strip() else None
                        couleur_kml = row[2].strip()
                        couleur_hex = row[3].strip()
                        description = row[4].strip() if len(row) > 4 else ""
                        
                        # Utilise un tuple (type, classe) comme clé
                        # classe peut être None pour les zones sans classe
                        key = (type_espace, classe)
                        self.color_rules[key] = {
                            'kml': couleur_kml,
                            'hex': couleur_hex,
                            'description': description
                        }
                        
                    except (IndexError, ValueError) as e:
                        print(f"Erreur ligne {line_num} dans {self.config_file}: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"Fichier de configuration non trouvé: {self.config_file}")
            print("Utilisation des couleurs par défaut.")
        except Exception as e:
            print(f"Erreur lors du chargement de {self.config_file}: {e}")
    
    def get_color(self, type_espace: str, classe: Optional[str] = None, 
                  format_type: str = 'kml') -> str:
        """
        Retourne la couleur appropriée pour un espace aérien.
        
        Args:
            type_espace: Type d'espace (TMA, CTR, P, D, etc.)
            classe: Classe d'espace (A, B, C, D, E, etc.) - optionnel
            format_type: Format de couleur souhaité ('kml' ou 'hex')
            
        Returns:
            Code couleur dans le format demandé
        """
        # Cherche d'abord avec type et classe
        key = (type_espace, classe)
        if key in self.color_rules:
            return self.color_rules[key].get(format_type, self.default_colors[format_type])
        
        # Si pas trouvé, cherche avec type seulement (classe = None)
        key_no_class = (type_espace, None)
        if key_no_class in self.color_rules:
            return self.color_rules[key_no_class].get(format_type, self.default_colors[format_type])
        
        # Couleur par défaut si aucune règle trouvée
        return self.default_colors[format_type]
    
    def get_color_info(self, type_espace: str, classe: Optional[str] = None) -> Dict[str, str]:
        """
        Retourne toutes les informations de couleur pour un espace aérien.
        
        Args:
            type_espace: Type d'espace (TMA, CTR, P, D, etc.)
            classe: Classe d'espace (A, B, C, D, E, etc.) - optionnel
            
        Returns:
            Dictionnaire avec les clés 'kml', 'hex', 'description'
        """
        # Cherche d'abord avec type et classe
        key = (type_espace, classe)
        if key in self.color_rules:
            return self.color_rules[key].copy()
        
        # Si pas trouvé, cherche avec type seulement (classe = None)
        key_no_class = (type_espace, None)
        if key_no_class in self.color_rules:
            return self.color_rules[key_no_class].copy()
        
        # Informations par défaut si aucune règle trouvée
        return self.default_colors.copy()
    
    def list_rules(self) -> Dict[Tuple[str, Optional[str]], Dict[str, str]]:
        """
        Retourne toutes les règles de couleurs chargées.
        
        Returns:
            Dictionnaire des règles avec (type, classe) comme clés
        """
        return self.color_rules.copy()
    
    def reload_config(self):
        """Recharge le fichier de configuration."""
        self.color_rules.clear()
        self._load_color_rules()


# Instance globale du service (singleton pattern)
_color_service_instance = None


def get_color_service(config_file: str = None) -> ColorService:
    """
    Retourne l'instance du service de couleurs (pattern singleton).
    
    Args:
        config_file: Chemin vers le fichier de configuration (utilisé seulement à la première création)
        
    Returns:
        Instance du ColorService
    """
    global _color_service_instance
    if _color_service_instance is None:
        _color_service_instance = ColorService(config_file)
    return _color_service_instance


# Fonctions utilitaires pour un usage simple
def get_space_color(type_espace: str, classe: Optional[str] = None, 
                   format_type: str = 'kml') -> str:
    """
    Fonction utilitaire pour obtenir rapidement une couleur d'espace.
    
    Args:
        type_espace: Type d'espace (TMA, CTR, P, D, etc.)
        classe: Classe d'espace (A, B, C, D, E, etc.) - optionnel
        format_type: Format de couleur ('kml' ou 'hex')
        
    Returns:
        Code couleur dans le format demandé
    """
    service = get_color_service()
    return service.get_color(type_espace, classe, format_type)


def get_space_color_info(type_espace: str, classe: Optional[str] = None) -> Dict[str, str]:
    """
    Fonction utilitaire pour obtenir toutes les infos de couleur d'un espace.
    
    Args:
        type_espace: Type d'espace (TMA, CTR, P, D, etc.)
        classe: Classe d'espace (A, B, C, D, E, etc.) - optionnel
        
    Returns:
        Dictionnaire avec 'kml', 'hex', 'description'
    """
    service = get_color_service()
    return service.get_color_info(type_espace, classe)


if __name__ == "__main__":
    # Tests du service
    service = ColorService()
    
    print("=== Test du service de couleurs ===")
    print()
    
    # Tests avec différents types d'espaces
    test_cases = [
        ("TMA", "D"),
        ("TMA", "E"),
        ("TMA", "A"),
        ("CTR", "D"),
        ("P", None),
        ("D", None),
        ("R", None),
        ("FIR", None),
        ("Inconnu", "X")  # Test avec type/classe non définis
    ]
    
    for type_espace, classe in test_cases:
        color_info = service.get_color_info(type_espace, classe)
        classe_str = classe if classe else "sans classe"
        print(f"{type_espace} {classe_str}:")
        print(f"  KML: {color_info['kml']}")
        print(f"  Hex: {color_info['hex']}")
        print(f"  Description: {color_info['description']}")
        print()
    
    print(f"Nombre de règles chargées: {len(service.color_rules)}")