"""
Brand Learner Module
====================
Learns brand-to-manufacturer mappings from input data patterns.

Instead of using a pre-built lookup table, this module analyzes
the input CSV to discover:
1. Which brands appear in descriptions
2. Which manufacturers make which brands
3. Common abbreviations and their full forms

This makes the system SELF-LEARNING - it gets smarter as it processes more data.
"""
import re
from collections import defaultdict


class BrandLearner:
    """
    Learns brand mappings from input data patterns.
    
    How it works:
    1. Scan all Part_Desc values to find brand names
    2. Map each brand to its manufacturer (from Part_Manuf)
    3. Build a lookup table for future use
    """
    
    def __init__(self):
        # Learned mappings
        self.brand_to_manufacturer = {}  # brand -> manufacturer_name
        self.manufacturer_to_brand = {}  # manufacturer -> brand
        self.brand_patterns = {}  # brand -> regex pattern
        self.abbreviation_map = {}  # short form -> full brand name
        
        # Statistics
        self.brand_counts = defaultdict(int)
        self.manufacturer_counts = defaultdict(int)
        
        # Common brand patterns to look for
        self.known_brands = {
            # Power Tools
            'milw': 'Milwaukee',
            'milwaukee': 'Milwaukee',
            'dewalt': 'DEWALT',
            'de walt': 'DEWALT',
            'makita': 'Makita',
            'bosch': 'Bosch',
            'festool': 'Festool',
            'kreg': 'Kreg',
            'irwin': 'Irwin',
            
            # Abrasives
            'diablo': 'Diablo',
            '3m': '3M',
            'mirka': 'Mirka',
            'norton': 'Norton',
            
            # Lighting
            'kichler': 'Kichler',
            'satco': 'Satco',
            'lithonia': 'Lithonia',
            'feit': 'Feit Electric',
            'philips': 'Philips',
            
            # Appliances
            'ge': 'GE',
            'lg': 'LG',
            'whirlpool': 'Whirlpool',
            'frigidaire': 'FRIGIDAIRE',
            'kitchenaid': 'KitchenAid',
            'speed queen': 'Speed Queen',
            'sq': 'Speed Queen',
            
            # Electrical
            'leviton': 'Leviton',
            'southwire': 'Southwire',
            'square d': 'Square D',
            
            # Building Materials
            'trex': 'TREX',
            'timbertech': 'TIMBERTECH',
            'lp': 'LP',
            'james hardie': 'JAMESHARDIE',
            'azek': 'AZEK',
            
            # Windows/Doors
            'velux': 'VELUX',
            'provia': 'PROVIA',
            'andersen': 'ANDERSEN',
        }
    
    def learn_from_data(self, input_data):
        """
        Learn brand mappings from input data.
        
        Args:
            input_data: List of dicts with Mfg_Part_Num, Part_Desc, Part_Manuf, etc.
        """
        print("Learning brand mappings from input data...")
        
        for row in input_data:
            part_desc = str(row.get('Part_Desc', '')).lower()
            part_manuf = str(row.get('Part_Manuf', '')).strip()
            dib_brand = str(row.get('DIB_Brand', '')).strip()
            e1_brand = str(row.get('E1_Brand', '')).strip()
            
            # Skip placeholder values
            if part_manuf in ['-', '--', '', 'nan', '-- No DIB Brand --']:
                continue
            
            # Extract manufacturer name (remove code in parentheses)
            manuf_name = re.sub(r'\s*\([^)]*\)', '', part_manuf).strip()
            
            # Try to find brand in description
            brand = self._extract_brand(part_desc)
            
            if brand and manuf_name:
                # Learn the mapping
                self.brand_to_manufacturer[brand.lower()] = manuf_name
                self.manufacturer_to_brand[manuf_name.lower()] = brand
                self.brand_counts[brand] += 1
                self.manufacturer_counts[manuf_name] += 1
            
            # Use DIB_Brand if available
            if dib_brand and dib_brand not in ['-- No DIB Brand --', '--', '']:
                self.brand_to_manufacturer[dib_brand.lower()] = manuf_name
                self.manufacturer_to_brand[manuf_name.lower()] = dib_brand
        
        print(f"Learned {len(self.brand_to_manufacturer)} brand-to-manufacturer mappings")
        print(f"Learned {len(self.manufacturer_to_brand)} manufacturer-to-brand mappings")
    
    def _extract_brand(self, desc):
        """Extract brand name from description."""
        desc_lower = desc.lower()
        
        # Check known brands
        for abbrev, full_name in self.known_brands.items():
            # Use word boundaries
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, desc_lower):
                return full_name
        
        return None
    
    def get_manufacturer(self, brand):
        """Get manufacturer name from brand."""
        if brand.lower() in self.brand_to_manufacturer:
            return self.brand_to_manufacturer[brand.lower()]
        return None
    
    def get_brand(self, manufacturer):
        """Get brand name from manufacturer."""
        if manufacturer.lower() in self.manufacturer_to_brand:
            return self.manufacturer_to_brand[manufacturer.lower()]
        return None
    
    def get_brand_for_product(self, part_desc, part_manuf):
        """
        Get the best brand name for a product.
        
        Args:
            part_desc: Product description
            part_manuf: Manufacturer string
        
        Returns:
            Tuple of (brand_name, manufacturer_name, confidence)
        """
        # Extract manufacturer name
        manuf_name = re.sub(r'\s*\([^)]*\)', '', part_manuf).strip()
        
        # Try to find brand in description
        brand = self._extract_brand(part_desc)
        
        if brand:
            # Check if we've seen this brand-manufacturer pair
            known_manuf = self.get_manufacturer(brand)
            if known_manuf:
                return brand, known_manuf, 0.95
            else:
                return brand, manuf_name, 0.85
        
        # Check if we know this manufacturer's brand
        known_brand = self.get_brand(manuf_name)
        if known_brand:
            return known_brand, manuf_name, 0.80
        
        # No confident match - return empty instead of wrong brand
        return "", "", 0.0
    
    def get_stats(self):
        """Get learning statistics."""
        return {
            'total_brands': len(self.brand_to_manufacturer),
            'total_manufacturers': len(self.manufacturer_to_brand),
            'top_brands': sorted(self.brand_counts.items(), key=lambda x: -x[1])[:10],
            'top_manufacturers': sorted(self.manufacturer_counts.items(), key=lambda x: -x[1])[:10]
        }
