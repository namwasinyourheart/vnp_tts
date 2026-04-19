from typing import Dict, Optional, List, Union
import os
import sys
from pathlib import Path

# Add project root to path to allow importing sound_map
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def load_sound_map(unit_type: Optional[str] = None, 
                  file_path: Optional[str] = None, 
                  default_map: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Load a sound map with support for categorized units.
    
    This function can load units in several ways:
    1. From the central sound_map.UNIT_MAP by category
    2. From a custom text file
    3. From a provided default map
    
    Args:
        unit_type: Type of units to load (e.g., 'currency', 'length'). 
                   Uses sound_map.UnitCategories for valid values.
        file_path: Path to a text file with custom units (format: key#value).
        default_map: Default map to return if no matching units are found.
        
    Returns:
        Dictionary mapping unit symbols to their spoken forms.
    """
    # First try to load from sound_map.py
    try:
        from sound_map import get_units, UnitCategories
        
        # If no specific type requested, get all units
        if unit_type is None:
            return get_units()
            
        # Try to get units by category name
        units = get_units(unit_type.lower())
        if units:
            return units
            
    except (ImportError, AttributeError):
        pass  # Fall through to file loading
    
    # Try to load from file if specified
    if file_path and os.path.exists(file_path):
        try:
            sound_map = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('#')
                        if len(parts) == 2:
                            key, value = parts
                            sound_map[key] = value
            return sound_map
        except (IOError, UnicodeDecodeError):
            pass
    
    # Return default map if provided and no other sources available
    return default_map.copy() if default_map is not None else {}