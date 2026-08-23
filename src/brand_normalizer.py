"""
Brand Normalizer - 3-Layer Dynamic Resolution with Distributor Detection
========================================================================
Layer 1: E1_Brand / DIB_Brand (if real)
Layer 2: Part_Manuf parse + distributor detection + brand-in-desc scan
Layer 3: Clean company name -> brand candidate
"""
import re
from typing import Dict, List, Tuple

_MANUF_PATTERN = re.compile(r'^(.*?)\s*\(([^)]+)\)\s*$')

_PLACEHOLDERS = {
    '-- unbranded --', '-- no unilog brand --', '-- no dib brand --',
    '-- no e1 brand --', '--', '-', 'nan', 'none', '',
}

_COMPANY_SUFFIXES = re.compile(
    r'\b(?:Inc\.?|LLC\.?|LTD\.?|Co\.?|Corp\.?|Mfg\.?|Manufacturing|'
    r'Industries|International|Supply|Supplies|Distributors?|Distribution|'
    r'Solutions|Systems|Technologies|Products?|Services|Group|Company|'
    r'Enterprises|Associates|Partners|USA|Intl)\b',
    re.IGNORECASE,
)

_DESCRIPTIVE_WORDS = re.compile(
    r'\b(?:Lighting|Electric|Wiring|Devices|Gypsum|Innovations|Machinery|'
    r'Accessory|Accessories|Prod|Building\s*Materials|Lumber|Parksite|'
    r'Cascade|Hardware|Fastener|Safety|Industrial|Wholesale)\b',
    re.IGNORECASE,
)

DISTRIBUTOR_SIGNALS = [
    'dealers', 'cooperative', 'supply', 'industrial', 'wholesale',
    'distributor', 'cascade', 'lumber', 'parksite', 'building materials',
    'hardware', 'home center', 'wholesale', 'outlet', 'warehouse',
]

MPN_BRAND_PREFIXES = {
    # === POWER TOOL BRANDS ===
    # Milwaukee
    r'^48-': 'Milwaukee',
    r'^49-': 'Milwaukee',
    r'^40-': 'Milwaukee',
    r'^41-': 'Milwaukee',
    r'^42-': 'Milwaukee',
    r'^43-': 'Milwaukee',
    r'^44-': 'Milwaukee',
    r'^45-': 'Milwaukee',
    r'^46-': 'Milwaukee',
    r'^47-': 'Milwaukee',
    r'^50-': 'Milwaukee',
    r'^23-': 'Milwaukee',
    r'^24-': 'Milwaukee',
    r'^25-': 'Milwaukee',
    r'^26-': 'Milwaukee',
    r'^27-': 'Milwaukee',
    r'^28-': 'Milwaukee',
    r'^29-': 'Milwaukee',
    r'^20-': 'Milwaukee',
    r'^21-': 'Milwaukee',
    r'^22-': 'Milwaukee',
    r'^30-': 'Milwaukee',
    r'^31-': 'Milwaukee',
    r'^M12': 'Milwaukee',
    r'^M18': 'Milwaukee',
    r'^M18F': 'Milwaukee',
    r'^MXF': 'Milwaukee',
    r'^MFL': 'Milwaukee',
    r'^BTP': 'Milwaukee',
    r'^BTC': 'Milwaukee',
    r'^BTB': 'Milwaukee',
    # Makita
    r'^XT': 'Makita',
    r'^XDT': 'Makita',
    r'^XRJ': 'Makita',
    r'^XPH': 'Makita',
    r'^XRW': 'Makita',
    r'^XBP': 'Makita',
    r'^XCS': 'Makita',
    r'^XFD': 'Makita',
    r'^XSH': 'Makita',
    r'^XZT': 'Makita',
    r'^XOC': 'Makita',
    r'^XAG': 'Makita',
    r'^XAD': 'Makita',
    r'^XAU': 'Makita',
    r'^XSV': 'Makita',
    r'^XGT': 'Makita',
    r'^XR0': 'Makita',
    r'^XBU': 'Makita',
    r'^XCG': 'Makita',
    r'^XCL': 'Makita',
    r'^XDS': 'Makita',
    r'^XHF': 'Makita',
    r'^XJW': 'Makita',
    r'^XPK': 'Makita',
    # DeWalt
    r'^DCD': 'DeWalt',
    r'^DCF': 'DeWalt',
    r'^DCS': 'DeWalt',
    r'^DWE': 'DeWalt',
    r'^DW': 'DeWalt',
    r'^DCB': 'DeWalt',
    r'^DCG': 'DeWalt',
    r'^DCH': 'DeWalt',
    r'^DCN': 'DeWalt',
    r'^DCR': 'DeWalt',
    r'^DCK': 'DeWalt',
    r'^DWS': 'DeWalt',
    r'^DWV': 'DeWalt',
    r'^DWH': 'DeWalt',
    r'^DWP': 'DeWalt',
    r'^DWD': 'DeWalt',
    r'^DWF': 'DeWalt',
    r'^DWST': 'DeWalt',
    # Ryobi
    r'^P1': 'Ryobi',
    r'^P2': 'Ryobi',
    r'^P3': 'Ryobi',
    r'^P4': 'Ryobi',
    r'^P5': 'Ryobi',
    r'^P6': 'Ryobi',
    r'^P7': 'Ryobi',
    r'^P8': 'Ryobi',
    r'^P9': 'Ryobi',
    r'^RY18': 'Ryobi',
    r'^RYOBI': 'Ryobi',
    # Ridgid
    r'^R86': 'Ridgid',
    r'^R87': 'Ridgid',
    r'^R88': 'Ridgid',
    r'^R89': 'Ridgid',
    r'^R90': 'Ridgid',
    r'^R91': 'Ridgid',
    r'^R92': 'Ridgid',
    r'^R93': 'Ridgid',
    r'^R94': 'Ridgid',
    r'^R95': 'Ridgid',
    r'^RID': 'Ridgid',
    r'^R18': 'Ridgid',
    r'^RG': 'Ridgid',
    r'^R28': 'Ridgid',
    r'^R44': 'Ridgid',
    r'^R45': 'Ridgid',
    # Bosch
    r'^BSH': 'Bosch',
    r'^SHX': 'Bosch',
    r'^SHV': 'Bosch',
    r'^SHE': 'Bosch',
    r'^SHP': 'Bosch',
    r'^SHS': 'Bosch',
    r'^SHM': 'Bosch',
    r'^GSG': 'Bosch',
    r'^GUE': 'Bosch',
    r'^SMT': 'Bosch',
    r'^B1': 'Bosch',
    r'^GBS': 'Bosch',
    r'^GWS': 'Bosch',
    r'^GKH': 'Bosch',
    r'^GST': 'Bosch',
    r'^GSS': 'Bosch',
    r'^GSR': 'Bosch',
    r'^GBH': 'Bosch',
    r'^GDE': 'Bosch',
    r'^GCM': 'Bosch',
    r'^GTS': 'Bosch',
    r'^GOF': 'Bosch',
    r'^GMF': 'Bosch',
    r'^PR111': 'Bosch',
    # Hilti
    r'^TE': 'Hilti',
    r'^TEC': 'Hilti',
    r'^SIW': 'Hilti',
    r'^DD': 'Hilti',
    r'^DX': 'Hilti',
    r'^SI': 'Hilti',
    r'^AG': 'Hilti',
    r'^CMW': 'Hilti',
    r'^SPX': 'Hilti',
    r'^SP': 'Hilti',
    r'^HK': 'Hilti',
    # Festool
    r'^FES': 'Festool',
    r'^FEST': 'Festool',
    r'^EK': 'Festool',
    r'^DT': 'Festool',
    r'^MFT': 'Festool',
    r'^CXL': 'Festool',
    r'^CXS': 'Festool',
    r'^TSC': 'Festool',
    r'^HKC': 'Festool',
    r'^HL': 'Festool',
    # Metabo
    r'^MET': 'Metabo',
    r'^WPB': 'Metabo',
    r'^KGS': 'Metabo',
    r'^KGT': 'Metabo',
    r'^BS': 'Metabo',
    r'^GA': 'Metabo',
    r'^WEV': 'Metabo',
    # Metabo HPT
    r'^C10': 'Metabo HPT',
    r'^C12': 'Metabo HPT',
    r'^C7': 'Metabo HPT',
    r'^C8': 'Metabo HPT',
    r'^NR': 'Metabo HPT',
    r'^KC': 'Metabo HPT',
    r'^DH': 'Metabo HPT',
    # Craftsman
    r'^CM': 'Craftsman',
    r'^CME': 'Craftsman',
    r'^CMW': 'Craftsman',
    r'^CMT': 'Craftsman',
    r'^CMX': 'Craftsman',
    r'^CMV': 'Craftsman',
    r'^CRAFT': 'Craftsman',
    # Kobalt
    r'^KB': 'Kobalt',
    r'^KBO': 'Kobalt',
    r'^KOBA': 'Kobalt',
    # Husky
    r'^H2': 'Husky',
    r'^HUSK': 'Husky',
    # === APPLIANCE BRANDS ===
    # NOTE: Specific patterns MUST come before broad patterns (e.g., PDSH before PD)
    # KitchenAid (specific first)
    r'^KDT': 'KitchenAid',
    r'^KDF': 'KitchenAid',
    r'^KDR': 'KitchenAid',
    r'^KUB': 'KitchenAid',
    r'^KSM': 'KitchenAid',
    r'^KHM': 'KitchenAid',
    r'^KFE': 'KitchenAid',
    r'^KPA': 'KitchenAid',
    r'^KD': 'KitchenAid',
    # Whirlpool (specific first)
    r'^WFW': 'Whirlpool',
    r'^WDT': 'Whirlpool',
    r'^WDTS': 'Whirlpool',
    r'^WTW': 'Whirlpool',
    r'^WHR': 'Whirlpool',
    r'^WML': 'Whirlpool',
    r'^WDF': 'Whirlpool',
    r'^WRS': 'Whirlpool',
    r'^WRT': 'Whirlpool',
    r'^WD': 'Whirlpool',
    # Frigidaire (specific first - MUST come before GE PD pattern)
    r'^PDSH': 'Frigidaire',
    r'^PDD': 'Frigidaire',
    r'^PDW': 'Frigidaire',
    r'^FFTR': 'Frigidaire',
    r'^FFIF': 'Frigidaire',
    r'^FFGF': 'Frigidaire',
    r'^FFSS': 'Frigidaire',
    r'^FGHD': 'Frigidaire',
    r'^FTFG': 'Frigidaire',
    r'^FPEW': 'Frigidaire',
    r'^FPCD': 'Frigidaire',
    r'^FF': 'Frigidaire',
    r'^FG': 'Frigidaire',
    # GE (specific first - AFTER Frigidaire PD patterns)
    r'^GEA': 'GE',
    r'^GEB': 'GE',
    r'^PTD': 'GE',
    r'^PTW': 'GE',
    r'^JB': 'GE',
    r'^JBP': 'GE',
    r'^JT': 'GE',
    r'^GFE': 'GE',
    r'^GNE': 'GE',
    r'^PSE': 'GE',
    r'^GSE': 'GE',
    r'^GTE': 'GE',
    r'^GDE': 'GE',
    r'^PF': 'GE',
    r'^PGS': 'GE',
    r'^PFS': 'GE',
    r'^CWE': 'GE',
    r'^CSE': 'GE',
    r'^PT': 'GE',
    r'^PD': 'GE',
    # LG (specific first)
    r'^LGF': 'LG',
    r'^LDF': 'LG',
    r'^LDP': 'LG',
    r'^LDC': 'LG',
    r'^LDS': 'LG',
    r'^LMX': 'LG',
    r'^LFX': 'LG',
    r'^LSC': 'LG',
    r'^LDT': 'LG',
    r'^LGC': 'LG',
    r'^LRE': 'LG',
    r'^LD': 'LG',
    r'^LW': 'LG',
    r'^LR': 'LG',
    r'^LS': 'LG',
    r'^LT': 'LG',
    r'^WF': 'LG',
    # Samsung (specific first)
    r'^RF2': 'Samsung',
    r'^RS2': 'Samsung',
    r'^NX': 'Samsung',
    r'^RF': 'Samsung',
    r'^RS': 'Samsung',
    r'^WA': 'Samsung',
    r'^WW': 'Samsung',
    r'^DW': 'Samsung',
    r'^RB': 'Samsung',
    r'^DA': 'Samsung',
    r'^SS': 'Samsung',
    r'^DC': 'Samsung',
    r'^RT': 'Samsung',
    # Maytag (specific first)
    r'^MDB8': 'Maytag',
    r'^MDB6': 'Maytag',
    r'^MEDB': 'Maytag',
    r'^MH': 'Maytag',
    r'^MDB': 'Maytag',
    r'^MED': 'Maytag',
    r'^MV': 'Maytag',
    r'^MFI': 'Maytag',
    r'^MFW': 'Maytag',
    r'^MEW': 'Maytag',
    r'^MTW': 'Maytag',
    r'^MHW': 'Maytag',
    r'^MVW': 'Maytag',
    r'^MGT': 'Maytag',
    r'^MBL': 'Maytag',
    # Speed Queen
    r'^DF': 'Speed Queen',
    r'^AE': 'Speed Queen',
    r'^ATT': 'Speed Queen',
    r'^SF': 'Speed Queen',
    r'^SET': 'Speed Queen',
    r'^AGN': 'Speed Queen',
    # Electrolux
    r'^EWFC': 'Electrolux',
    r'^EIFW': 'Electrolux',
    r'^EIF': 'Electrolux',
    r'^EWI': 'Electrolux',
    r'^EI': 'Electrolux',
    r'^EW': 'Electrolux',
    r'^EF': 'Electrolux',
    r'^WC': 'Electrolux',
    # Miele
    r'^WCI': 'Miele',
    r'^WXE': 'Miele',
    r'^G7': 'Miele',
    r'^W1': 'Miele',
    r'^T1': 'Miele',
    r'^G': 'Miele',
    # Amana
    r'^ABT': 'Amana',
    r'^ABB': 'Amana',
    r'^ADE': 'Amana',
    r'^NTW': 'Amana',
    # === ELECTRICAL BRANDS ===
    # Leviton
    r'^60-': 'Leviton',
    r'^140': 'Leviton',
    r'^26': 'Leviton',
    r'^17': 'Leviton',
    r'^060': 'Leviton',
    r'^014': 'Leviton',
    r'^80': 'Leviton',
    r'^88': 'Leviton',
    r'^36': 'Leviton',
    r'^66': 'Leviton',
    r'^47': 'Leviton',
    r'^52': 'Leviton',
    r'^56': 'Leviton',
    r'^31': 'Leviton',
    r'^75': 'Leviton',
    r'^19': 'Leviton',
    r'^16': 'Leviton',
    r'^33': 'Leviton',
    r'^14': 'Leviton',
    # Lutron
    r'^LQ': 'Lutron',
    r'^LUT': 'Lutron',
    r'^PD-': 'Lutron',
    r'^CA-': 'Lutron',
    r'^DV-': 'Lutron',
    r'^GRX-': 'Lutron',
    r'^SU-': 'Lutron',
    r'^PJ2-': 'Lutron',
    r'^NWK-': 'Lutron',
    r'^RRK-': 'Lutron',
    # Siemens
    r'^RF-': 'Siemens',
    r'^QF': 'Siemens',
    r'^QP': 'Siemens',
    r'^QT': 'Siemens',
    r'^QB': 'Siemens',
    r'^TLM': 'Siemens',
    r'^TY': 'Siemens',
    r'^SN': 'Siemens',
    r'^H1': 'Siemens',
    # Square D
    r'^SWD': 'Square D',
    r'^QO': 'Square D',
    r'^QOB': 'Square D',
    r'^HOM': 'Square D',
    r'^HOM1': 'Square D',
    r'^HOM2': 'Square D',
    r'^HOMC': 'Square D',
    r'^NQOD': 'Square D',
    r'^NRXT': 'Square D',
    # Eaton
    r'^BR': 'Eaton',
    r'^BRN': 'Eaton',
    r'^CH': 'Eaton',
    r'^CHN': 'Eaton',
    r'^BRD': 'Eaton',
    r'^CL': 'Eaton',
    r'^CLN': 'Eaton',
    r'^BAB': 'Eaton',
    r'^TLC': 'Eaton',
    # Hubbell
    r'^HBL': 'Hubbell',
    r'^HUB': 'Hubbell',
    r'^WR': 'Hubbell',
    r'^SS': 'Hubbell',
    r'^SB': 'Hubbell',
    r'^CW': 'Hubbell',
    r'^SBX': 'Hubbell',
    r'^WP': 'Hubbell',
    # === PLUMBING BRANDS ===
    # Moen
    r'^CA': 'Moen',
    r'^DL': 'Moen',
    r'^T6': 'Moen',
    r'^T2': 'Moen',
    r'^S': 'Moen',
    r'^67': 'Moen',
    r'^MT': 'Moen',
    # Kohler
    r'^K-': 'Kohler',
    r'^KO': 'Kohler',
    # Delta
    r'^13': 'Delta',
    r'^15': 'Delta',
    r'^16': 'Delta',
    r'^17': 'Delta',
    r'^18': 'Delta',
    r'^19': 'Delta',
    r'^20': 'Delta',
    r'^21': 'Delta',
    r'^22': 'Delta',
    r'^24': 'Delta',
    r'^25': 'Delta',
    r'^32': 'Delta',
    r'^33': 'Delta',
    r'^34': 'Delta',
    r'^42': 'Delta',
    r'^43': 'Delta',
    r'^44': 'Delta',
    r'^53': 'Delta',
    r'^54': 'Delta',
    r'^55': 'Delta',
    r'^56': 'Delta',
    r'^57': 'Delta',
    r'^58': 'Delta',
    r'^59': 'Delta',
    r'^62': 'Delta',
    r'^64': 'Delta',
    r'^72': 'Delta',
    r'^75': 'Delta',
    r'^76': 'Delta',
    r'^77': 'Delta',
    r'^78': 'Delta',
    r'^80': 'Delta',
    r'^82': 'Delta',
    r'^83': 'Delta',
    r'^84': 'Delta',
    r'^85': 'Delta',
    r'^86': 'Delta',
    r'^92': 'Delta',
    # Pfister
    r'^97': 'Pfister',
    r'^98': 'Pfister',
    r'^96': 'Pfister',
    r'^F5': 'Pfister',
    r'^LG': 'Pfister',
    # Rheem
    r'^RGR': 'Rheem',
    r'^RHM': 'Rheem',
    r'^SP2': 'Rheem',
    r'^AP1': 'Rheem',
    r'^PP': 'Rheem',
    # A.O. Smith
    r'^42': 'A.O. Smith',
    r'^52': 'A.O. Smith',
    r'^62': 'A.O. Smith',
    r'^72': 'A.O. Smith',
    r'^82': 'A.O. Smith',
    r'^92': 'A.O. Smith',
    # Bradford White
    r'^MI': 'Bradford White',
    r'^M-I': 'Bradford White',
    # === BUILDING MATERIALS ===
    # Trex
    r'^TREX': 'Trex',
    r'^TX': 'Trex',
    # AZEK
    r'^AZK': 'AZEK',
    r'^AZ': 'AZEK',
    # TimberTech
    r'^TT': 'TimberTech',
    r'^TMBR': 'TimberTech',
    # Fiberon
    r'^FIB': 'Fiberon',
    r'^FB': 'Fiberon',
    # James Hardie
    r'^JH': 'James Hardie',
    r'^HARDI': 'James Hardie',
    # LP SmartSide
    r'^LP': 'LP SmartSide',
    r'^LPS': 'LP SmartSide',
    # === SAFETY BRANDS ===
    # 3M
    r'^3M': '3M',
    r'^3MB': '3M',
    r'^3MC': '3M',
    r'^3MH': '3M',
    r'^3MS': '3M',
    r'^3MT': '3M',
    r'^3MV': '3M',
    r'^SJ': '3M',
    r'^600': '3M',
    r'^850': '3M',
    r'^900': '3M',
    # Honeywell
    r'^HON': 'Honeywell',
    r'^HO': 'Honeywell',
    r'^L4': 'Honeywell',
    r'^CT': 'Honeywell',
    # MCR Safety
    r'^MCR': 'MCR Safety',
    r'^GCR': 'MCR Safety',
    # === LIGHTING BRANDS ===
    # Philips
    r'^PHI': 'Philips',
    r'^92': 'Philips',
    r'^75': 'Philips',
    r'^25': 'Philips',
    r'^42': 'Philips',
    r'^43': 'Philips',
    r'^44': 'Philips',
    r'^45': 'Philips',
    r'^53': 'Philips',
    r'^54': 'Philips',
    r'^55': 'Philips',
    r'^61': 'Philips',
    r'^62': 'Philips',
    # Cree
    r'^CP': 'Cree',
    r'^CRM': 'Cree',
    r'^CB': 'Cree',
    # Feit
    r'^FEIT': 'Feit',
    r'^FT': 'Feit',
    r'^BCP': 'Feit',
    r'^BP': 'Feit',
    r'^OM': 'Feit',
    # Sylvania
    r'^SYLV': 'Sylvania',
    r'^SY': 'Sylvania',
    # Satco
    r'^BF': 'Satco',
    r'^S11': 'Satco',
    r'^S30': 'Satco',
    # Kichler
    r'^KICL': 'Kichler',
    r'^KIC': 'Kichler',
    # Lithonia
    r'^LIT': 'Lithonia',
    # Sea Gull
    r'^SG': 'Sea Gull',
    r'^SEA': 'Sea Gull',
    # === HAND TOOLS ===
    # Klein
    r'^KL': 'Klein',
    # Stanley
    r'^STMT': 'Stanley',
    # Irwin
    r'^IRW': 'Irwin',
    r'^136': 'Irwin',
    # Lenox
    r'^LX': 'Lenox',
    # Channellock
    r'^CH': 'Channellock',
    r'^3': 'Channellock',
    r'^4': 'Channellock',
    # Knipex
    r'^KN': 'Knipex',
    r'^87': 'Knipex',
    r'^86': 'Knipex',
    r'^85': 'Knipex',
    r'^84': 'Knipex',
    r'^72': 'Knipex',
    r'^73': 'Knipex',
    r'^74': 'Knipex',
    r'^75': 'Knipex',
    r'^76': 'Knipex',
    r'^77': 'Knipex',
    r'^78': 'Knipex',
    # Wiha
    r'^WI': 'Wiha',
    # Wera
    r'^WR': 'Wera',
    r'^05': 'Wera',
    # === OTHER BRANDS ===
    # Diablo
    r'^DCB': 'Diablo',
    r'^DBD': 'Diablo',
    r'^DBS': 'Diablo',
    r'^SCM': 'Diablo',
    r'^SF': 'Diablo',
    r'^DIO': 'Diablo',
    r'^DIB': 'Diablo',
    r'^D10': 'Diablo',
    r'^D12': 'Diablo',
    r'^D7': 'Diablo',
    r'^D8': 'Diablo',
    r'^D9': 'Diablo',
    # Mirka
    r'^5B-': 'Mirka',
    r'^9A-': 'Mirka',
    r'^31-': 'Mirka',
    r'^MIR': 'Mirka',
    r'^MIRK': 'Mirka',
    r'^DERO': 'Mirka',
    # Southwire
    r'^SW': 'Southwire',
    r'^S': 'Southwire',
    r'^12': 'Southwire',
    r'^10': 'Southwire',
    r'^8': 'Southwire',
    # Black & Decker
    r'^B': 'Black & Decker',
    # Freud
    r'^FT': 'Freud',
    r'^165': 'Freud',
    r'^125': 'Freud',
    r'^96': 'Freud',
    # Kreg
    r'^KRT': 'Kreg',
    r'^KREG': 'Kreg',
    r'^KJP': 'Kreg',
    # Hunter Fan
    r'^HF': 'Hunter Fan',
    # Vessel Tools
    r'^VST': 'Vessel Tools',
    # Whiteside
    r'^W': 'Whiteside',
    r'^WHITESIDE': 'Whiteside',
    # VELUX
    r'^VEL': 'VELUX',
    # Simpson Strong-Tie
    r'^ST': 'Simpson Strong-Tie',
    r'^SMS': 'Simpson Strong-Tie',
    r'^SD': 'Simpson Strong-Tie',
    r'^FP': 'Simpson Strong-Tie',
    # GRK
    r'^GRK': 'GRK',
    # FastenMaster
    r'^FM': 'FastenMaster',
    r'^TR': 'FastenMaster',
    # Senco
    r'^SEN': 'Senco',
    r'^SC': 'Senco',
    r'^SN': 'Senco',
    r'^SL': 'Senco',
    # Streamlight
    r'^STR': 'Streamlight',
    r'^ST': 'Streamlight',
    # Snap-on
    r'^SA': 'Snap-on',
    r'^SG': 'Snap-on',
    r'^TA': 'Snap-on',
    r'^TR': 'Snap-on',
    r'^EPLR': 'Snap-on',
    # GearWrench
    r'^GW': 'GearWrench',
    r'^81': 'GearWrench',
    r'^82': 'GearWrench',
    r'^83': 'GearWrench',
    r'^84': 'GearWrench',
    r'^85': 'GearWrench',
    r'^86': 'GearWrench',
    # Gerber
    r'^GBO': 'Gerber',
    r'^GBF': 'Gerber',
    # Leatherman
    r'^LM': 'Leatherman',
    r'^LEA': 'Leatherman',
    # Panasonic
    r'^NL': 'Panasonic',
    r'^KX': 'Panasonic',
    r'^EASA': 'Panasonic',
    r'^PT': 'Panasonic',
    r'^SC': 'Panasonic',
    # Broan
    r'^BN': 'Broan',
    # NuTone
    r'^NU': 'NuTone',
    # Watts
    r'^WAT': 'Watts',
    r'^LF': 'Watts',
    r'^FV': 'Watts',
    r'^PLT': 'Watts',
    # SharkBite
    r'^SBC': 'SharkBite',
    r'^SBV': 'SharkBite',
    r'^SBX': 'SharkBite',
    r'^U': 'SharkBite',
    # Deckorators
    r'^DK': 'Deckorators',
    r'^DECK': 'Deckorators',
    # Andersen
    r'^AND': 'Andersen',
    # ProVia
    r'^PV': 'ProVia',
    r'^PRO': 'ProVia',
    # CMT
    r'^CMT': 'CMT',
    # Regex patterns
    r'^P[A-Z]{2}\d': 'GE',
    r'^F[A-Z]{2}\d': 'Frigidaire',
}

APPLIANCE_BRANDS = [
    'FRIGIDAIRE', 'Whirlpool', 'KitchenAid', 'Maytag', 'GE', 'LG',
    'Samsung', 'Bosch', 'Electrolux', 'Amana', 'Speed Queen', 'Miele',
    'Fisher & Paykel', 'Frigidaire', 'Fisher', 'Paykel',
]

# Direct MPN-to-brand lookup for known products where MPN prefix alone isn't enough
MPN_BRAND_LOOKUP = {
    # Frigidaire dishwashers (PD prefix, but these are Frigidaire not GE)
    'PDSH4816AF': 'Frigidaire',
    'PDSH': 'Frigidaire',
    'PDD': 'Frigidaire',
    'PDW': 'Frigidaire',
    'KDFM404KPS': 'KitchenAid',
    'KDTS424SBE': 'KitchenAid',
    'KDTS324SPS': 'KitchenAid',
    'KDPS624SJP': 'KitchenAid',
    'KDTS624SBE': 'KitchenAid',
    'KDT': 'KitchenAid',
    # Whirlpool
    'WDTS7024RZ': 'Whirlpool',
    'WKE100HWA': 'Whirlpool',
    'WDTS': 'Whirlpool',
    # GE
    'PDT715SYVFS': 'GE',
    'PDD415PYYFS': 'GE',
    'PTD70GBPTDG': 'GE',
    'PTD70GBSTWS': 'GE',
    'PTW705BSTWS': 'GE',
    'PTD': 'GE',
    'PTW': 'GE',
    # LG
    'LDPH5554D': 'LG',
    # Speed Queen
    'FF7011WN': 'Speed Queen',
    'DF7004WE': 'Speed Queen',
    'DR7004BE': 'Speed Queen',
    'DV2000WE': 'Speed Queen',
    'DC5004WE': 'Speed Queen',
    'DC5004BE': 'Speed Queen',
    'DR5004WG': 'Speed Queen',
    'DR7004BG': 'Speed Queen',
    'DR7004WG': 'Speed Queen',
    'DV2000WG': 'Speed Queen',
    'DC5004WG': 'Speed Queen',
    'DC5004BG': 'Speed Queen',
    'TV2000WN': 'Speed Queen',
    'TC5003BN': 'Speed Queen',
    'TR7006WN': 'Speed Queen',
    'TR7006BN': 'Speed Queen',
    'TR5006WN': 'Speed Queen',
    'DF': 'Speed Queen',
    # Maytag
    'MVWP586GW': 'Maytag',
    # Bosch
    'SHX': 'Bosch',
    'SHV': 'Bosch',
    'SHE': 'Bosch',
    'SHP': 'Bosch',
    # Trex (from E1_Brand)
    'TREX': 'Trex',
    # TimberTech (from E1_Brand)
    'TIMBERTECH': 'TimberTech',
}

# Manufacturer name mapping (brand -> correct manufacturer name)
BRAND_TO_MANUFACTURER = {
    'Frigidaire': 'Rheem Manufacturing',
    'Whirlpool': 'Whirlpool Corporation',
    'KitchenAid': 'Whirlpool Corporation',
    'Maytag': 'Whirlpool Corporation',
    'GE': 'GE Appliances',
    'LG': 'LG Electronics',
    'Samsung': 'Samsung Electronics',
    'Bosch': 'Bosch Home Appliances',
    'Electrolux': 'Electrolux',
    'Speed Queen': 'Alliance Laundry Systems',
    'Miele': 'Miele',
    'Amana': 'Whirlpool Corporation',
    'Diablo': 'Freud Inc',
    'Milwaukee': 'Milwaukee Tool',
    'Makita': 'Makita USA',
    'DeWalt': 'DeWalt Industrial Tool',
    '3M': '3M Company',
    'Mirka': 'Mirka Ltd',
    'Trex': 'Trex Company',
    'TimberTech': 'AZEK Building Products',
    'AZEK': 'AZEK Building Products',
    'Kichler': 'Kichler Lighting',
    'Satco': 'Satco Products',
    'Leviton': 'Leviton Manufacturing',
    'Lutron': 'Lutron Electronics',
    'Southwire': 'Southwire Company',
    'Klein': 'Klein Tools',
    'Stanley': 'Stanley Black & Decker',
    'Irwin': 'Irwin Industrial Tools',
    'Lenox': 'Lenox International',
    'Ryobi': 'TTI Consumer Products',
    'Ridgid': 'Emerson Electric',
    'Craftsman': 'Stanley Black & Decker',
    'Bosch': 'Robert Bosch GmbH',
    'Festool': 'Festool GmbH',
    'Hilti': 'Hilti Corporation',
    'Metabo': 'Metabo Power Tools',
    'Moen': 'Fortune Brands Innovations',
    'Kohler': 'Kohler Company',
    'Delta': 'Masco Corporation',
    'Pfister': 'Spectrum Brands',
    'Rheem': 'Rheem Manufacturing',
    'Honeywell': 'Honeywell International',
    'Panasonic': 'Panasonic Corporation',
    'Philips': 'Signify North America',
    'Cree': 'Cree Lighting',
    'Feit': 'Feit Electric',
    'Sylvania': 'Osram Sylvania',
    'ProVia': 'ProVia by MWE',
    'VELUX': 'VELUX Group',
    'James Hardie': 'James Hardie Industries',
    'LP SmartSide': 'Louisiana-Pacific Corporation',
    'Simpson Strong-Tie': 'Simpson Strong-Tie',
    'GRK': 'ITW Construction Products',
    'FastenMaster': 'ITW Construction Products',
    'SharkBite': 'Reliance Worldwide Corp',
    'Watts': 'Watts Water Technologies',
    'Broan': 'Broan-NuTone',
    'NuTone': 'Broan-NuTone',
    'Hunter Fan': 'Hunter Fan Company',
    'Streamlight': 'Streamlight Inc',
    'Snap-on': 'Snap-on Incorporated',
    'GearWrench': 'Apex Tool Group',
    'Knipex': 'Knipex Tools',
    'Wiha': 'Wiha Tools',
    'Wera': 'Wera Tool Holding',
    'Leatherman': 'Leatherman Tool Group',
    'Gerber': 'Fiskars Brands',
    'Channellock': 'Channellock Inc',
    'Vise-Grip': 'Snap-on Incorporated',
    'Senco': 'Senco Brands',
    'Kreg': 'Kreg Tool Company',
    'Deckorators': 'UFP Industries',
    'Fiberon': 'CPG International',
    'Andersen': 'Andersen Corporation',
    'Premier Metals': 'Premier Building Products',
    'Rees Cast Stone': 'Rees Cast Stone Company',
    'Palmer Donavin': 'Palmer Donavin Mfg Company',
    'U S Lumber': 'U S Lumber Group',
    'Boise Cascade': 'Boise Cascade Company',
    'Parksite': 'Parksite Inc',
    'Westwood Lumber': 'Westwood Lumber Sales',
    'Huber': 'Huber Engineered Woods',
    'Certainteed': 'CertainTeed Corporation',
    'Hager': 'Hager Companies',
    'Emseal': 'Emseal Joint Systems',
    'Velux': 'VELUX America',
    'United Window': 'United Window & Door',
    'Schumacher': 'Schumacher Electric',
    'Metalmark': 'Metalmark Industrial',
    'Carlon': 'Thomas & Betts',
    'Cooper': 'Eaton Corporation',
    'Prime': 'Prime Wire & Cable',
    'Satco': 'Satco Products',
    'Kichler': 'Kichler Lighting',
}

KNOWN_BRANDS = APPLIANCE_BRANDS + [
    '3M', 'Norton', 'Diablo', 'Mirka', 'Milwaukee', 'Makita', 'DeWalt',
    'Ryobi', 'Ridgid', 'Craftsman', 'Klein', 'Klein Tools',
    'Stanley', 'Irwin', 'Lenox', 'Hilti', 'Festool', 'Metabo',
    'Freud', 'CMT', 'Senco', 'Streamlight', 'Leviton', 'Lutron',
    'Siemens', 'Philips', 'Cree', 'Feit', 'Sylvania',
    'Moen', 'Kohler', 'Pfister', 'SharkBite', 'Rheem', 'A.O. Smith',
    'Honeywell', 'Panasonic', 'Hunter', 'Broan', 'NuTone',
    'Trex', 'AZEK', 'TimberTech', 'Fiberon', 'Deckorators',
    'Andersen', 'James Hardie', 'LP SmartSide', 'ProVia',
    'Grainger', 'Ply Gem', 'Eaton', 'Hubbell', 'Watts',
    'Southwire', 'Satco', 'Kichler', 'Sea Gull', 'Lithonia',
    'Snap-on', 'GearWrench', 'Knipex', 'Wiha', 'Wera',
    'Leatherman', 'Gerber', 'Channellock', 'Vise-Grip',
    'Simpson Strong-Tie', 'GRK', 'FastenMaster',
    'Finyline', 'Kreg', 'Mirka', 'Hunter Fan', 'U S Tape',
    'Vessel Tools', 'Premier Metals', 'Palmer Donavin',
    'Whiteside', 'VELUX', 'Rees Cast Stone', 'Edge Eyewear',
    'Tech Gear', 'Oliver', 'Prime',
]


class BrandNormalizer:

    def __init__(self, data_loader=None):
        self.data_loader = data_loader
        self._manufacturer_vocab = {}
        self._all_manuf_names = []

    def build_vocab(self, input_data):
        name_to_clean = {}
        for row in input_data:
            raw = row.get('Part_Manuf', '') or ''
            name, code = self._parse_manuf_string(raw)
            if name:
                clean = self._clean_to_brand(name)
                if clean:
                    name_to_clean[name] = clean
                    name_to_clean[code.upper()] = clean if clean else name
                    name_to_clean[clean.lower()] = clean
        self._manufacturer_vocab = name_to_clean
        self._all_manuf_names = list({
            v for v in name_to_clean.values()
            if isinstance(v, str) and len(v) > 2
        })

    def _parse_manuf_string(self, raw):
        if not raw:
            return '', ''
        m = _MANUF_PATTERN.match(raw.strip())
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return raw.strip(), ''

    def _clean_to_brand(self, company_name):
        if not company_name:
            return ''
        clean = _COMPANY_SUFFIXES.sub('', company_name).strip(' ,.')
        clean = _DESCRIPTIVE_WORDS.sub('', clean).strip(' ,.')
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean if clean else company_name

    def _is_distributor(self, manuf_name):
        if not manuf_name:
            return False
        lower = manuf_name.lower()
        return any(sig in lower for sig in DISTRIBUTOR_SIGNALS)

    def _scan_desc_for_brand(self, part_desc, mpn=''):
        if not part_desc:
            return ''
        
        # 1. Check direct MPN-to-brand lookup first (most specific)
        if mpn:
            mpn_upper = mpn.upper().strip()
            if mpn_upper in MPN_BRAND_LOOKUP:
                return MPN_BRAND_LOOKUP[mpn_upper]
            # Check prefix matches in lookup (sorted by length, longest first)
            for lookup_mpn in sorted(MPN_BRAND_LOOKUP.keys(), key=len, reverse=True):
                if mpn_upper.startswith(lookup_mpn) and len(lookup_mpn) >= 3:
                    return MPN_BRAND_LOOKUP[lookup_mpn]
        
        # 2. Check description for known brand names
        desc_upper = part_desc.upper()
        for brand in KNOWN_BRANDS:
            if brand.upper() in desc_upper:
                return brand
        
        # 3. Check MPN prefix patterns (sorted by length, longest first for specificity)
        if mpn:
            combined = (mpn + ' ' + part_desc).strip()
            sorted_patterns = sorted(MPN_BRAND_PREFIXES.items(), key=lambda x: len(x[0]), reverse=True)
            for pattern, brand in sorted_patterns:
                if re.match(pattern, combined.strip(), re.IGNORECASE):
                    return brand
        
        return ''

    def _find_brand_in_desc(self, part_desc):
        if not part_desc or not self._all_manuf_names:
            return ''
        desc_lower = part_desc.lower()
        best = ''
        best_len = 0
        for name in self._all_manuf_names:
            if len(name) < 3:
                continue
            if name.lower() in desc_lower and len(name) > best_len:
                best = name
                best_len = len(name)
        return best

    def _extract_brand_from_desc(self, part_desc):
        if not part_desc:
            return ''
        words = part_desc.strip().split()
        for n in [3, 2, 1]:
            if len(words) >= n:
                candidate = ' '.join(words[:n])
                for brand in KNOWN_BRANDS:
                    if candidate.lower() == brand.lower():
                        return candidate
        return ''

    def normalize(self, part_manuf, e1_brand='', unilog_brand='',
                  dib_brand='', part_desc='', mpn=''):
        result = {
            'manufacturer_name': '',
            'brand_name': '',
            'manufacturer_code': '',
            'confidence': 0.0,
            'method': 'none',
        }

        name, code = self._parse_manuf_string(part_manuf)
        if not name or name.lower().strip() in _PLACEHOLDERS:
            return result

        result['manufacturer_name'] = name
        result['manufacturer_code'] = code

        # 1. Check E1_Brand, Unilog_Brand, DIB_Brand first
        for brand_val in [e1_brand, unilog_brand, dib_brand]:
            if brand_val and brand_val.lower().strip() not in _PLACEHOLDERS:
                result['brand_name'] = brand_val.strip()
                result['confidence'] = 0.95
                result['method'] = 'brand_column'
                # Use correct manufacturer name if known
                known_manuf = BRAND_TO_MANUFACTURER.get(brand_val.strip(), '')
                if known_manuf:
                    result['manufacturer_name'] = known_manuf
                return result

        # 2. If manufacturer is a distributor, scan description for brand
        if self._is_distributor(name):
            brand_in_desc = self._scan_desc_for_brand(part_desc, mpn)
            if brand_in_desc:
                result['brand_name'] = brand_in_desc
                result['confidence'] = 0.90
                result['method'] = 'distributor_desc_scan'
                # Use correct manufacturer name if known
                known_manuf = BRAND_TO_MANUFACTURER.get(brand_in_desc, '')
                if known_manuf:
                    result['manufacturer_name'] = known_manuf
                return result

        # 3. Scan description for brand
        brand_from_desc = self._scan_desc_for_brand(part_desc, mpn)
        if brand_from_desc:
            result['brand_name'] = brand_from_desc
            result['confidence'] = 0.85
            result['method'] = 'desc_brand_scan'
            # Use correct manufacturer name if known
            known_manuf = BRAND_TO_MANUFACTURER.get(brand_from_desc, '')
            if known_manuf:
                result['manufacturer_name'] = known_manuf
            return result

        # 4. Check code lookup
        if code:
            code_upper = code.upper()
            if code_upper in self._manufacturer_vocab:
                mapped = self._manufacturer_vocab[code_upper]
                if mapped:
                    result['brand_name'] = mapped
                    result['confidence'] = 0.80
                    result['method'] = 'code_lookup'
                    return result

        # 5. Clean company name
        clean = self._clean_to_brand(name)
        if clean and len(clean) >= 2:
            result['brand_name'] = clean
            result['confidence'] = 0.70
            result['method'] = 'manuf_clean'
            return result

        # 6. Find brand in description
        brand_in_desc = self._find_brand_in_desc(part_desc)
        if brand_in_desc:
            result['brand_name'] = brand_in_desc
            result['confidence'] = 0.60
            result['method'] = 'desc_scan'
            return result

        # 7. Extract first words from description
        brand_from_first_words = self._extract_brand_from_desc(part_desc)
        if brand_from_first_words:
            result['brand_name'] = brand_from_first_words
            result['confidence'] = 0.80
            result['method'] = 'first_word_desc'
            return result

        # 8. Fallback to manufacturer name
        result['brand_name'] = name
        result['confidence'] = 0.30
        result['method'] = 'fallback'
        return result

    def get_brand_from_desc(self, part_desc):
        return self._scan_desc_for_brand(part_desc) or self._find_brand_in_desc(part_desc)

    def extract_brand_from_manufacturer(self, part_manuf):
        name, _ = self._parse_manuf_string(part_manuf)
        return self._clean_to_brand(name)
