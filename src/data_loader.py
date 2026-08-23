"""
Data Loader Module
==================
Loads all lookup tables from CSV/Excel files into memory.

What is a lookup table?
- A dictionary where you give a key (like a manufacturer name)
  and it returns the correct value (like the official brand name)
- This is faster than searching through thousands of rows every time

Think of it like a phone book:
- Key = Person's name (what you search for)
- Value = Phone number (what you get back)
"""
import pandas as pd
import os
from pathlib import Path


class DataLoader:
    """
    Loads and caches all reference data files.
    
    Attributes:
        data_dir: Path to the data folder containing reference files
        manufacturer_list: Dict mapping manufacturer names to brand info
        lov_data: Dict mapping classpaths to valid attributes
        uom_table: Dict mapping UOM abbreviations to full forms
        fraction_table: Dict mapping decimals to fractions
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Path to folder with reference files.
                     If None, uses the 'data' folder in project root
        """
        if data_dir is None:
            # Go up one level from src/ to project root, then into data/
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        # These will be populated when load_all() is called
        self.manufacturer_list = {}
        self.lov_data = {}
        self.uom_table = {}
        self.fraction_table = {}
        self.content_rules = {}
        
        # Track what's been loaded
        self._loaded = False
    
    def load_all(self):
        """
        Load all reference files. Call this once at startup.
        
        This method tries to load each file. If a file doesn't exist,
        it prints a warning but continues (so the system still works
        with whatever files are available).
        """
        print("=" * 60)
        print("LOADING REFERENCE DATA")
        print("=" * 60)
        
        # Load each file, handle missing files gracefully
        self._load_manufacturer_list()
        self._load_lov_data()
        self._load_uom_table()
        self._load_fraction_table()
        self._load_content_rules()
        
        self._loaded = True
        print("=" * 60)
        print("ALL REFERENCE DATA LOADED SUCCESSFULLY")
        print("=" * 60)
    
    def _load_manufacturer_list(self):
        """
        Load the manufacturer and brand list.
        
        This file has 27,000+ rows mapping:
        - MANUFACTURER_NAME -> The official company name
        - MANUFACTURER_CODE -> Short code (like "KICLI" for Kichler)
        - BRAND_NAME -> The brand they sell under
        - BRAND_CODE -> Short code for the brand
        
        Example:
        - "Kichler Lighting (KICLI)" -> Brand: "Kichler"
        - "Freud Inc (2435)" -> Brand: "Diablo"
        """
        file_path = self.data_dir / "UniCat_Manufacturer_and_Brand_List.xlsx"
        
        if not file_path.exists():
            print(f"  [WARNING] Manufacturer list not found: {file_path}")
            print(f"  -> Brand normalization will use basic matching")
            # Create empty structure
            self.manufacturer_list = {
                'by_name': {},
                'by_code': {},
                'by_brand': {}
            }
            return
        
        try:
            df = pd.read_excel(file_path)
            print(f"  Loading manufacturer list: {len(df)} rows")
            
            # Build lookup dictionaries for fast access
            self.manufacturer_list = {
                'by_name': {},    # Map: manufacturer_name -> row data
                'by_code': {},    # Map: manufacturer_code -> row data
                'by_brand': {},   # Map: brand_name -> row data
                'dataframe': df   # Keep the full dataframe for fuzzy matching
            }
            
            for _, row in df.iterrows():
                name = str(row.get('MANUFACTURER_NAME', '')).strip()
                code = str(row.get('MANUFACTURER_CODE', '')).strip()
                brand = str(row.get('BRAND_NAME', '')).strip()
                brand_code = str(row.get('BRAND_CODE', '')).strip()
                
                entry = {
                    'manufacturer_name': name,
                    'manufacturer_code': code,
                    'brand_name': brand,
                    'brand_code': brand_code
                }
                
                if name:
                    self.manufacturer_list['by_name'][name.lower()] = entry
                if code:
                    self.manufacturer_list['by_code'][code.upper()] = entry
                if brand:
                    self.manufacturer_list['by_brand'][brand.lower()] = entry
            
            print(f"  [OK] Loaded {len(self.manufacturer_list['by_name'])} manufacturers")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load manufacturer list: {e}")
            self.manufacturer_list = {
                'by_name': {},
                'by_code': {},
                'by_brand': {}
            }
    
    def _load_lov_data(self):
        """
        Load the List of Values (LOV) data.
        
        LOV = List of Values
        This tells us what attributes are valid for each product category.
        
        Example:
        - Classpath: "Abrasives > Abrasive Belts > Sanding Belts"
        - Valid attributes: Width, Length, Grit, Material
        - Valid values for Width: "1/2 in", "3/4 in", "1 in", etc.
        """
        file_path = self.data_dir / "Unicat_Lov_v1_0_Updated_With_Remarks.xlsx"
        
        if not file_path.exists():
            print(f"  [WARNING] LOV data not found: {file_path}")
            print(f"  -> Product classification will use basic matching")
            self.lov_data = {
                'by_classpath': {},
                'all_classpaths': [],
                'dataframe': None
            }
            return
        
        try:
            df = pd.read_excel(file_path)
            print(f"  Loading LOV data: {len(df)} rows")
            
            self.lov_data = {
                'by_classpath': {},  # Map: classpath -> list of valid attributes
                'all_classpaths': [],  # List of all unique classpaths
                'dataframe': df  # Keep for fuzzy matching
            }
            
            # Group by classpath
            for classpath, group in df.groupby('Classpath'):
                if pd.notna(classpath):
                    attributes = []
                    for _, row in group.iterrows():
                        attr_label = str(row.get('Attribute Label', '')).strip()
                        attr_values = str(row.get('Attribute Values', '')).strip()
                        if attr_label:
                            attributes.append({
                                'label': attr_label,
                                'values': attr_values.split('|') if attr_values else [],
                                'filterable': str(row.get('Filtering Y/N', '')).upper() == 'Y'
                            })
                    self.lov_data['by_classpath'][str(classpath).strip()] = attributes
                    self.lov_data['all_classpaths'].append(str(classpath).strip())
            
            print(f"  [OK] Loaded {len(self.lov_data['by_classpath'])} classpaths")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load LOV data: {e}")
            self.lov_data = {
                'by_classpath': {},
                'all_classpaths': [],
                'dataframe': None
            }
    
    def _load_uom_table(self):
        """
        Load the Unit of Measure (UOM) standards.
        
        UOM = Unit of Measure
        This standardizes how we write units.
        
        Example:
        - "inches" -> "in"
        - "IN." -> "in"
        - "inch" -> "in"
        - Always: "24 in" (number + space + unit)
        """
        file_path = self.data_dir / "Unilog_Master_UOM_Standards_Abbreviations_and_Terms.xlsx"
        
        if not file_path.exists():
            print(f"  [WARNING] UOM table not found: {file_path}")
            print(f"  -> Unit normalization will use basic rules")
            self.uom_table = {
                'standard': {},     # Map: variation -> standard form
                'categories': {},   # Map: category -> list of valid UOMs
                'dataframe': None
            }
            return
        
        try:
            df = pd.read_excel(file_path)
            print(f"  Loading UOM table: {len(df)} rows")
            
            self.uom_table = {
                'standard': {},
                'categories': {},
                'dataframe': df
            }
            
            for _, row in df.iterrows():
                standard = str(row.get('Abbreviation', '')).strip()
                category = str(row.get('Measurement Type', '')).strip()
                
                # Map all variations to the standard form
                for col in df.columns:
                    if col not in ['Abbreviation', 'Measurement Type']:
                        variation = str(row.get(col, '')).strip()
                        if variation and variation != 'nan':
                            self.uom_table['standard'][variation.lower()] = standard
                
                if category and category != 'nan':
                    if category not in self.uom_table['categories']:
                        self.uom_table['categories'][category] = []
                    if standard and standard not in self.uom_table['categories'][category]:
                        self.uom_table['categories'][category].append(standard)
            
            print(f"  [OK] Loaded {len(self.uom_table['standard'])} UOM variations")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load UOM table: {e}")
            self.uom_table = {
                'standard': {},
                'categories': {},
                'dataframe': None
            }
    
    def _load_fraction_table(self):
        """
        Load the decimal-to-fraction conversion table.
        
        This converts decimal inches to fractions (which buyers search for).
        
        Example:
        - 0.5 -> "1/2"
        - 0.25 -> "1/4"
        - 0.125 -> "1/8"
        - 50.25 -> "50-1/4"
        """
        file_path = self.data_dir / "Decimal_Fraction.xlsx"
        
        if not file_path.exists():
            print(f"  [WARNING] Fraction table not found: {file_path}")
            print(f"  -> Fraction conversion will use built-in table")
            # Built-in common fractions
            self.fraction_table = {
                'decimal_to_fraction': {
                    0.015625: '1/64', 0.03125: '1/32', 0.046875: '3/64',
                    0.0625: '1/16', 0.078125: '5/64', 0.09375: '3/32',
                    0.109375: '7/64', 0.125: '1/8', 0.140625: '9/64',
                    0.15625: '5/32', 0.171875: '11/64', 0.1875: '3/16',
                    0.203125: '13/64', 0.21875: '7/32', 0.234375: '15/64',
                    0.25: '1/4', 0.265625: '17/64', 0.28125: '9/32',
                    0.296875: '19/64', 0.3125: '5/16', 0.328125: '21/64',
                    0.34375: '11/32', 0.359375: '23/64', 0.375: '3/8',
                    0.390625: '25/64', 0.40625: '13/32', 0.421875: '27/64',
                    0.4375: '7/16', 0.453125: '29/64', 0.46875: '15/32',
                    0.484375: '31/64', 0.5: '1/2', 0.515625: '33/64',
                    0.53125: '17/32', 0.546875: '35/64', 0.5625: '9/16',
                    0.578125: '37/64', 0.59375: '19/32', 0.609375: '39/64',
                    0.625: '5/8', 0.640625: '41/64', 0.65625: '21/32',
                    0.671875: '43/64', 0.6875: '11/16', 0.703125: '45/64',
                    0.71875: '23/32', 0.734375: '47/64', 0.75: '3/4',
                    0.765625: '49/64', 0.78125: '25/32', 0.796875: '51/64',
                    0.8125: '13/16', 0.828125: '53/64', 0.84375: '27/32',
                    0.859375: '55/64', 0.875: '7/8', 0.890625: '57/64',
                    0.90625: '29/32', 0.921875: '59/64', 0.9375: '15/16',
                    0.953125: '61/64', 0.96875: '31/32', 0.984375: '63/64'
                },
                'fraction_to_decimal': {}  # Will be built from above
            }
            # Build reverse mapping
            for dec, frac in self.fraction_table['decimal_to_fraction'].items():
                self.fraction_table['fraction_to_decimal'][frac] = dec
            return
        
        try:
            df = pd.read_excel(file_path)
            print(f"  Loading fraction table: {len(df)} rows")
            
            self.fraction_table = {
                'decimal_to_fraction': {},
                'fraction_to_decimal': {}
            }
            
            # Parse the side-by-side column blocks
            # The file has 4 pairs of Fraction | Decimal columns
            fraction_cols = [col for col in df.columns if 'Fraction' in str(col)]
            decimal_cols = [col for col in df.columns if 'Decimal' in str(col)]
            
            for _, row in df.iterrows():
                for frac_col, dec_col in zip(fraction_cols, decimal_cols):
                    frac = str(row.get(frac_col, '')).strip()
                    dec = row.get(dec_col)
                    if frac and pd.notna(dec):
                        try:
                            dec_val = float(dec)
                            self.fraction_table['decimal_to_fraction'][dec_val] = frac
                            self.fraction_table['fraction_to_decimal'][frac] = dec_val
                        except (ValueError, TypeError):
                            pass
            
            print(f"  [OK] Loaded {len(self.fraction_table['decimal_to_fraction'])} conversions")
            
        except Exception as e:
            print(f"  [ERROR] Failed to load fraction table: {e}")
            self.fraction_table = {
                'decimal_to_fraction': {},
                'fraction_to_decimal': {}
            }
    
    def _load_content_rules(self):
        """
        Load content generation rules from the guidelines document.
        
        These rules define:
        - Character limits for each description type
        - Casing rules (UPPER, Title Case, etc.)
        - Field ordering in descriptions
        """
        # Since we can't easily parse .docx, we'll use hard-coded rules
        # based on the guidelines. These can be updated when the docx is available.
        
        self.content_rules = {
            'INVOICE_DESC': {
                'max_length': 40,
                'casing': 'UPPER',
                'description': 'Short invoice line item, max 40 chars, ALL CAPS'
            },
            'MOBILE_DESC': {
                'min_length': 60,
                'max_length': 80,
                'casing': 'Title Case',
                'description': 'Mobile app description, 60-80 chars, Title Case'
            },
            'SHORT_DESC': {
                'max_length': 150,
                'casing': 'Title Case',
                'description': 'Search results, product page title'
            },
            'LONG_DESC1': {
                'max_length': 2000,
                'casing': 'Title Case',
                'description': 'Full product page description'
            },
            'RETAIL_DESC': {
                'max_length': 200,
                'casing': 'Title Case',
                'description': 'Marketing/retail description'
            },
            'MARKETING_DESCRIPTION': {
                'max_length': 500,
                'casing': 'Sentence case',
                'description': 'Marketing copy, 1-2 sentences'
            }
        }
        
        print(f"  [OK] Content rules loaded")
    
    def get_manufacturer_info(self, part_manuf: str) -> dict:
        """
        Look up manufacturer information.
        
        Args:
            part_manuf: The Part_Manuf value from input CSV
                       Example: "Freud Inc (2435)"
        
        Returns:
            Dict with manufacturer_name, brand_name, etc.
            Or empty dict if not found
        """
        if not self.manufacturer_list:
            return {}
        
        # Try exact match first
        manuf_lower = part_manuf.lower().strip()
        if manuf_lower in self.manufacturer_list['by_name']:
            return self.manufacturer_list['by_name'][manuf_lower]
        
        # Try extracting code from parentheses
        # "Freud Inc (2435)" -> code = "2435"
        code = ''
        if '(' in part_manuf and ')' in part_manuf:
            code = part_manuf.split('(')[-1].replace(')', '').strip()
            if code.upper() in self.manufacturer_list['by_code']:
                return self.manufacturer_list['by_code'][code.upper()]
        
        # Try fuzzy matching (find closest match)
        best_match = None
        best_score = 0
        
        for name, info in self.manufacturer_list['by_name'].items():
            # Simple similarity: count common words
            words1 = set(manuf_lower.split())
            words2 = set(name.split())
            common = len(words1 & words2)
            total = max(len(words1), len(words2))
            score = common / total if total > 0 else 0
            
            if score > best_score and score > 0.5:
                best_score = score
                best_match = info
        
        return best_match if best_match else {}
    
    def get_classpath_attributes(self, classpath: str) -> list:
        """
        Get valid attributes for a classpath.
        
        Args:
            classpath: Example: "Abrasives > Abrasive Belts > Sanding Belts"
        
        Returns:
            List of dicts with attribute labels and valid values
        """
        if not self.lov_data or not self.lov_data['by_classpath']:
            return []
        
        # Try exact match
        if classpath in self.lov_data['by_classpath']:
            return self.lov_data['by_classpath'][classpath]
        
        # Try partial match (find classpath that contains our value)
        for known_path, attrs in self.lov_data['by_classpath'].items():
            if classpath.lower() in known_path.lower():
                return attrs
        
        return []
    
    def decimal_to_fraction(self, value: float) -> str:
        """
        Convert a decimal value to a fraction string.
        
        Args:
            value: Decimal number (e.g., 0.5)
        
        Returns:
            Fraction string (e.g., "1/2")
        """
        if not self.fraction_table or not self.fraction_table['decimal_to_fraction']:
            # Use built-in conversion
            return str(value)
        
        # Find the closest fraction
        closest = min(
            self.fraction_table['decimal_to_fraction'].keys(),
            key=lambda x: abs(x - value),
            default=None
        )
        
        if closest and abs(closest - value) < 0.01:
            return self.fraction_table['decimal_to_fraction'][closest]
        
        return str(value)
    
    def normalize_uom(self, unit: str) -> str:
        """
        Normalize a unit of measure to the standard form.
        
        Args:
            unit: Any variation (e.g., "inches", "IN.", "inch")
        
        Returns:
            Standard form (e.g., "in")
        """
        if not self.uom_table or not self.uom_table['standard']:
            return unit
        
        # Try exact match
        unit_lower = unit.lower().strip()
        if unit_lower in self.uom_table['standard']:
            return self.uom_table['standard'][unit_lower]
        
        # Return as-is if no match found
        return unit
