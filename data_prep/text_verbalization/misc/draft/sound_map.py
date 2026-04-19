from typing import Dict, List, Optional

# Define unit categories
class UnitCategories:
    CURRENCY = 'currency'
    LENGTH = 'length'
    WEIGHT = 'weight'
    VOLUME = 'volume'
    AREA = 'area'
    SPEED = 'speed'
    TEMPERATURE = 'temperature'

# Define unit mappings with categories
UNIT_MAP = {
    # Currency
    'currency': {
        'đ': 'đồng',
        'vnđ': 'Việt Nam đồng',
        'k': 'ca',
        'm': 'mờ',
        'usd': 'đô la',
        'eur': 'euro',
        'gbp': 'bảng Anh',
    },
    
    # Length
    'length': {
        'mm': 'mi li mét',
        'cm': 'xen ti mét',
        'dm': 'đề xi mét',
        'm': 'mét',
        'km': 'ki lô mét',
    },
    
    # Weight
    'weight': {
        'mg': 'mi li gam',
        'g': 'gam',
        'kg': 'ki lô gam',
        't': 'tấn',
    },
    
    # Volume
    'volume': {
        'ml': 'mi li lít',
        'l': 'lít',
    },
    
    # Area
    'area': {
        'm2': 'mét vuông',
        'km2': 'ki lô mét vuông',
    },
    
    # Speed
    'speed': {
        'km/h': 'ki lô mét trên giờ',
        'm/s': 'mét trên giây',
    },
    
    # Temperature
    'temperature': {
        '°c': 'độ xê',
        'c': 'độ xê',
    }
}

def get_units(category: Optional[str] = None) -> Dict[str, str]:
    """Get units by category or all units if no category specified.
    
    Args:
        category: One of the UnitCategories values or None for all units.
        
    Returns:
        Dictionary of unit symbols to their spoken forms.
    """
    if category:
        return UNIT_MAP.get(category, {})
    
    # Return all units combined if no category specified
    all_units = {}
    for units in UNIT_MAP.values():
        all_units.update(units)
    return all_units

def get_unit_categories() -> List[str]:
    """Get list of available unit categories."""
    return list(UNIT_MAP.keys())

# For backward compatibility
UNIT_SOUND_MAP = get_units()
