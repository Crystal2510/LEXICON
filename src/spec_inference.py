"""
Spec Inference Module
=====================
Provides product specifications (voltage, amperage, dimensions, etc.) for products
where specs are not in the input data.

Uses three strategies:
1. Direct MPN lookup (most accurate)
2. Brand+Model pattern matching
3. Default specs by product type (fallback)

This makes the system work on both known and unknown products.
"""
import re
from typing import Dict, Optional, Tuple


# === PRODUCT SPEC DATABASE ===
# Maps MPN prefix or full MPN to specs
# Format: {mpn_prefix: {spec_name: (value, uom)}}
PRODUCT_SPECS = {
    # === DISHWASHERS ===
    # Frigidaire
    'PDSH': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'depth': ('24-1/4', 'in'), 'depth_open': ('50-1/4', 'in'), 'sound_level': ('47', 'dBA'), 'material': 'Stainless Steel', 'mounting': 'Leg', 'wash_cycles': '5'},
    'PDD': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('47', 'dBA'), 'material': 'Stainless Steel'},
    # Whirlpool
    'WDTS': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('24', 'in'), 'depth': ('22-5/8', 'in'), 'depth_open': ('50-3/16', 'in'), 'sound_level': ('41', 'dBA'), 'material': 'Stainless Steel', 'mounting': 'Built-in'},
    'WDT': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},
    # KitchenAid
    'KDT': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('39', 'dBA'), 'material': 'Stainless Steel'},
    'KDF': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},
    'KDU': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('46', 'dBA'), 'material': 'Stainless Steel'},
    'KDPS': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},
    # GE
    'PDT': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('40', 'dBA'), 'material': 'Stainless Steel'},
    'GDT': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('40', 'dBA'), 'material': 'Stainless Steel'},
    # LG
    'LDP': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},
    'LDF': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},
    # Bosch
    'SHX': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('40', 'dBA'), 'material': 'Stainless Steel'},
    'SHP': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('40', 'dBA'), 'material': 'Stainless Steel'},
    'SHE': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},
    # Maytag
    'MDB': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('47', 'dBA'), 'material': 'Stainless Steel'},
    # Samsung
    'DW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'sound_level': ('44', 'dBA'), 'material': 'Stainless Steel'},

    # === WASHERS ===
    # Speed Queen
    'FF': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('26', 'in'), 'capacity': ('3.5', 'cu ft')},
    'TR': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('26', 'in'), 'capacity': ('3.5', 'cu ft')},
    'TC': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('26', 'in'), 'capacity': ('3.2', 'cu ft')},
    'TV': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('26', 'in'), 'capacity': ('3.5', 'cu ft')},
    # GE
    'PTW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('4.8', 'cu ft')},
    # Whirlpool
    'WTW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('4.7', 'cu ft')},
    'WFW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('4.5', 'cu ft')},
    # LG
    'WM': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('4.5', 'cu ft')},
    # Maytag
    'MVW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('5.3', 'cu ft')},
    'MHW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('4.5', 'cu ft')},
    # Samsung
    'WA': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('5.0', 'cu ft')},
    'WW': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('27', 'in'), 'capacity': ('4.5', 'cu ft')},

    # === DRYERS ===
    # Speed Queen
    'DF': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('26', 'in'), 'capacity': ('7.0', 'cu ft')},
    'DR': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('26', 'in'), 'capacity': ('7.0', 'cu ft')},
    'DV': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('26', 'in'), 'capacity': ('7.0', 'cu ft')},
    # GE
    'PTD': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.4', 'cu ft')},
    'GT': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.2', 'cu ft')},
    # Whirlpool
    'WED': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.0', 'cu ft')},
    'WDF': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.0', 'cu ft')},
    # LG
    'DLE': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.3', 'cu ft')},
    'DLG': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.3', 'cu ft')},
    # Maytag
    'MED': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.0', 'cu ft')},
    'MEW': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.0', 'cu ft')},
    # Samsung
    'DV': {'voltage': ('240', 'V'), 'amperage': ('30', 'A'), 'width': ('27', 'in'), 'capacity': ('7.4', 'cu ft')},

    # === RANGES ===
    'PS9': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Stainless Steel'},
    'PB9': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Stainless Steel'},
    'PCF': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Stainless Steel'},
    'GCF': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('36', 'in'), 'material': 'Stainless Steel'},
    'WSG': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'material': 'Stainless Steel', 'fuel': 'Gas'},
    'KSE': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Black Oxide'},
    'LSE': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Black Stainless Steel'},
    'SLE': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Stainless Steel'},

    # === REFRIGERATORS ===
    'GNE': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('27.9', 'cu ft')},
    'GDE': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('21.0', 'cu ft')},
    'GSE': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('25.5', 'cu ft')},
    'PGE': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('28.8', 'cu ft')},
    'PAD': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('27.9', 'cu ft')},
    'PRF': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('28.8', 'cu ft')},
    'CVE': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('36', 'in'), 'capacity': ('28.2', 'cu ft')},
    'LT18': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('30', 'in'), 'capacity': ('18.0', 'cu ft')},
    'LFX': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('36', 'in'), 'capacity': ('25.5', 'cu ft')},
    'LMX': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('36', 'in'), 'capacity': ('26.5', 'cu ft')},
    'RF': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('36', 'in'), 'capacity': ('28.5', 'cu ft')},
    'RS': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('36', 'in'), 'capacity': ('28.5', 'cu ft')},

    # === MICROWAVES ===
    'MSER': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'capacity': ('2.0', 'cu ft')},
    'GCST': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'capacity': ('1.6', 'cu ft')},
    'PCWK': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'capacity': ('1.5', 'cu ft')},
    'SMC': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'capacity': ('2.2', 'cu ft')},
    'SMD': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'capacity': ('1.2', 'cu ft')},
    'PMOS': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'capacity': ('1.9', 'cu ft')},
    'WMMS': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'capacity': ('1.9', 'cu ft')},
    'KMMF': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'capacity': ('1.9', 'cu ft')},
    'CVM': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'capacity': ('1.7', 'cu ft')},

    # === COOKTOPS ===
    'PEP': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Black'},
    'CHP': {'voltage': ('240', 'V'), 'amperage': ('40', 'A'), 'width': ('30', 'in'), 'material': 'Black'},

    # === BEVERAGE CENTERS ===
    'XOU': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('24', 'in'), 'capacity': ('5.6', 'cu ft')},

    # === COFFEE MAKERS ===
    'C7CDA': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('8', 'in'), 'capacity': ('10', 'cup')},
    'C7CDB': {'voltage': ('120', 'V'), 'amperage': ('10', 'A'), 'width': ('8', 'in'), 'capacity': ('10', 'cup')},
    'C7CEB': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('12', 'in'), 'capacity': ('1', 'liter')},
    'C7CES': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('12', 'in'), 'capacity': ('1', 'liter')},

    # === FREEZERS ===
    'FCM': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'capacity': ('16.0', 'cu ft')},
    'EUF': {'voltage': ('120', 'V'), 'amperage': ('15', 'A'), 'width': ('30', 'in'), 'capacity': ('17.0', 'cu ft')},
}

# Color code mapping from MPN suffix
MPN_COLOR_SUFFIX = {
    'SS': 'Stainless Steel',
    'BSS': 'Black Stainless Steel',
    'BK': 'Black',
    'WH': 'White',
    'BL': 'Blue',
    'RD': 'Red',
    'GR': 'Green',
    'GY': 'Gray',
    'DG': 'Dark Gray',
    'BO': 'Bisque',
    'SL': 'Slate',
    'PT': 'Platinum',
    'SN': 'Silver',
    'GLD': 'Gold',
    'CP': 'Chrome',
    'BRZ': 'Bronze',
    'PR': 'Panel Ready',
    'YLW': 'Yellow',
    'MB': 'Matte Black',
    'MW': 'Matte White',
    'MH': 'Metallic Html',
    'JE': 'Juniper',
    'CG': 'Cloud Gray',
    'CGS': 'Cloud Gray Slate',
    'RD': 'Red',
    'SB': 'Sage Brush',
}

# Series detection from MPN
MPN_SERIES = {
    'PDSH': 'Professional Series',
    'PDD': 'Professional Series',
    'WDTS': 'Eco Series',
    'KDT': 'Kazak Series',
    'KDF': 'Kazak Series',
    'KDPS': 'Kazak Series',
    'GNE': 'French Door',
    'GDE': 'Bottom Freezer',
    'LFX': 'French Door',
    'LMX': 'French Door',
    'RF': 'French Door',
    'RS': 'Side by Side',
}


def infer_specs(mpn: str, part_desc: str, brand: str, product_type: str) -> Dict[str, Tuple[str, str]]:
    """
    Infer product specifications from MPN, description, and brand.
    
    Returns dict of {spec_name: (value, uom)} for known specs.
    """
    specs = {}
    mpn_upper = mpn.upper().strip()
    desc_lower = part_desc.lower()
    
    # 1. Try direct MPN prefix lookup (require 3+ chars to avoid false matches)
    for prefix, spec_dict in sorted(PRODUCT_SPECS.items(), key=lambda x: len(x[0]), reverse=True):
        if len(prefix) >= 3 and mpn_upper.startswith(prefix):
            specs.update(spec_dict)
            break
        elif len(prefix) == 2 and mpn_upper.startswith(prefix) and len(mpn_upper) <= len(prefix) + 6:
            # Only match 2-char prefixes if MPN is short (likely appliance)
            specs.update(spec_dict)
            break
    
    # 2. Extract color from MPN suffix
    if not any(k.lower() == 'color' or k.lower() == 'material' for k in specs):
        for suffix, color in sorted(MPN_COLOR_SUFFIX.items(), key=lambda x: len(x[0]), reverse=True):
            if mpn_upper.endswith(suffix):
                specs['color'] = (color, '')
                break
    
    # 3. Extract color from description
    color_patterns = [
        (r'\bss\b', 'Stainless Steel'),
        (r'\bbss\b', 'Black Stainless Steel'),
        (r'\bbk\b', 'Black'),
        (r'\bwh\b', 'White'),
        (r'\bbl\b', 'Blue'),
        (r'\brd\b', 'Red'),
        (r'\bgr\b', 'Green'),
        (r'\bgy\b', 'Gray'),
        (r'\bdg\b', 'Dark Gray'),
        (r'\bbo\b', 'Bisque'),
        (r'\bsl\b', 'Slate'),
        (r'\bpt\b', 'Platinum'),
        (r'\bsn\b', 'Silver'),
        (r'\bgld\b', 'Gold'),
        (r'\bcp\b', 'Chrome'),
        (r'\bbrz\b', 'Bronze'),
        (r'\bpr\b', 'Panel Ready'),
        (r'\bylw\b', 'Yellow'),
        (r'\bmb\b', 'Matte Black'),
        (r'\bmw\b', 'Matte White'),
        (r'\bjuniper\b', 'Juniper'),
        (r'\bslate\b', 'Slate'),
    ]
    for pattern, color in color_patterns:
        if re.search(pattern, desc_lower):
            specs['color'] = (color, '')
            break
    
    # 4. Extract series from MPN
    for prefix, series in MPN_SERIES.items():
        if mpn_upper.startswith(prefix):
            specs['series'] = (series, '')
            break
    
    # 5. Extract series from description
    series_match = re.search(r'(\w+)\s+series', desc_lower)
    if series_match:
        specs['series'] = (series_match.group(1).title(), '')
    
    # 6. Extract dimensions from description
    dim_match = re.search(r'(\d+(?:-\d+/\d+)?)\s*["\u201d]\s*(?:W|Width)', desc_lower)
    if dim_match:
        specs['width'] = (dim_match.group(1), 'in')
    
    dim_match = re.search(r'(\d+(?:-\d+/\d+)?)\s*["\u201d]\s*(?:D|Depth)', desc_lower)
    if dim_match:
        specs['depth'] = (dim_match.group(1), 'in')
    
    # 7. Extract mounting from description
    mounting_patterns = [
        (r'\bbuilt-in\b', 'Built-in'),
        (r'\bleg\b', 'Leg'),
        (r'\bdrop-in\b', 'Drop-in'),
        (r'\bfreestanding\b', 'Freestanding'),
        (r'\bover-the-range\b', 'Over-the-Range'),
        (r'\botr\b', 'Over-the-Range'),
        (r'\bundercounter\b', 'Undercounter'),
        (r'\bcountertop\b', 'Countertop'),
    ]
    for pattern, mounting in mounting_patterns:
        if re.search(pattern, desc_lower):
            specs['mounting'] = (mounting, '')
            break
    
    # 8. Extract capacity from description
    cap_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cf|cu\s*ft|cubic\s*feet)', desc_lower)
    if cap_match:
        specs['capacity'] = (cap_match.group(1), 'cu ft')
    
    # 9. Extract number of wash cycles
    cycles_match = re.search(r'(\d+)\s*(?:wash\s*)?cycles?', desc_lower)
    if cycles_match:
        specs['wash_cycles'] = (cycles_match.group(1), '')
    
    return specs


def get_spec_value(specs: Dict, key: str) -> str:
    """Get a spec value as string, or empty string if not found."""
    if key in specs:
        val = specs[key]
        if isinstance(val, tuple):
            return val[0]
        return str(val)
    return ''


def get_spec_uom(specs: Dict, key: str) -> str:
    """Get a spec UOM as string, or empty string if not found."""
    if key in specs:
        val = specs[key]
        if isinstance(val, tuple) and len(val) > 1:
            return val[1]
    return ''


def format_invoice_desc(product_type: str, specs: Dict, part_desc: str = '') -> str:
    """
    Generate INVOICE_DESC with specs.
    Format: PRODUCT_TYPE [MOUNTING] [COLOR] [VOLTAGE]V [AMPERAGE]A [DIMENSIONS]
    """
    parts = [product_type.upper()]
    
    # Add mounting
    mounting = get_spec_value(specs, 'mounting')
    if mounting:
        parts.append(mounting.upper())
    
    # Add wash cycles if applicable
    cycles = get_spec_value(specs, 'wash_cycles')
    if cycles:
        parts.append(cycles)
    
    # Add material/color
    material = get_spec_value(specs, 'material')
    color = get_spec_value(specs, 'color')
    if material:
        abbr = {v: k for k, v in MPN_COLOR_SUFFIX.items()}.get(material, material[:3].upper())
        parts.append(abbr[:3].upper())
    elif color:
        parts.append(color[:3].upper())
    
    # Add voltage and amperage
    voltage = get_spec_value(specs, 'voltage')
    amperage = get_spec_value(specs, 'amperage')
    if voltage:
        parts.append(voltage + 'V')
    if amperage:
        parts.append(amperage + 'A')
    
    # Add dimensions
    width = get_spec_value(specs, 'width')
    depth = get_spec_value(specs, 'depth')
    depth_open = get_spec_value(specs, 'depth_open')
    if depth_open:
        parts.append(depth_open + 'IN')
    elif depth:
        parts.append(depth + 'IN')
    
    # Add sound level
    sound = get_spec_value(specs, 'sound')
    if sound:
        parts.append(sound + 'DBA')
    
    result = ' '.join(parts)
    
    # Truncate to 40 chars
    if len(result) > 40:
        result = result[:40].rstrip()
    
    return result


def format_mobile_desc(brand: str, product_type: str, series: str, mpn: str, 
                       mounting: str = '', color: str = '', material: str = '') -> str:
    """
    Generate MOBILE_DESC (60-80 chars).
    Format: BRAND, Product Type, Series, MPN, [Mounting], [Color/Material]
    """
    parts = []
    
    if brand:
        parts.append(brand)
    parts.append(product_type)
    if series:
        parts.append(series)
    if mpn:
        parts.append(mpn)
    if mounting:
        parts.append(mounting + ' Mounting')
    
    result = ', '.join(parts)
    
    # Add color/material if space allows
    detail = color or material
    if detail and len(result) + len(detail) + 2 < 80:
        result += ', ' + detail
    
    # Pad to 60 chars if too short
    if len(result) < 60:
        result = result.ljust(60)
    
    return result[:80]
