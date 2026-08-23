"""
Category-Specific Attribute Extraction Grammars
Expanded with generic fallback and more patterns per category.
"""
import re
from typing import Dict, List

ABRASIVE_ATTRS = [
    ("Grit", r"(?:^|\s|-)P?(\d{2,3})(?:\s|$|-|/)", ""),
    ("Grit", r"GRIT\s*(\d{1,4})\b", ""),
    ("Diameter", r'(\d+(?:[./]\d+)?)["\u201d]', "in"),
    ("Width x Length", r'(\d+[./\d]*)["\u201d]?\s*[xX]\s*(\d+[./\d]*)', "in"),
    ("Quantity", r"(\d+)\s*(?:Disc|Pack|Pc|Pcs|Ct|per\s+Box|Roll|Sheet)\b", "EA"),
    ("Abrasive Type", r"(Aluminum\s+Oxide|Zirconia|Ceramic|Silicon\s+Carbide|Cubitron|Diamond|Abranet|HIOLIT|Stikit|Hookit)", ""),
    ("Backing", r"\b(Film|Paper|Cloth|Foam|Fiber)\b", ""),
    ("Series", r"([A-Z][a-z]+(?:\s+[IVX]+)?)\s+Series\b", ""),
    ("Material", r"(Aluminum\s+Oxide|Zirconia|Ceramic|Silicon\s+Carbide|Film|Paper|Cloth)", ""),
    ("Diameter", r"(\d+(?:\.\d+)?)\s*(?:in|inch)\b", "in"),
]

APPLIANCE_ATTRS = [
    ("Series", r"([\w\s]+?)\s+Series\b", ""),
    ("Voltage Rating", r"(\d+)\s*V\b", "V"),
    ("Amperage Rating", r"(\d+)\s*A\b", "A"),
    ("Mounting Type", r"(Built[-\s]?in|Leg|Freestanding|Under\s+Counter|Wall\s+Mount|Drop[-\s]?in|Top\s*mount|Slide[-\s]*In|Front\s*Control|Over[-\s]*The[-\s]*Range)", ""),
    ("Number of Wash Cycles", r"(\d+)[-\s]*(?:Wash\s+)?[Cc]ycles?", ""),
    ("Sound Level", r"(\d+)\s*dBA\b", "dBA"),
    ("Color", r"(BSS|Black\s+Stainless|SS|Stainless\s+Steel|Bk|Black|Wh|White|DG|Dark\s+Gray|BO|Bisque|Slate|Panel\s+Ready|Gray|Graphite|Platinum)", ""),
    ("Material", r"(?:Material|Finish)[:\s]+(Stainless\s+Steel|Black|White)", ""),
    ("Size", r"(\d+[-\d/\s]*in\s+[HWD](?:\s*[xX\u00d7]\s*[\d/\-]+\s*in)+)", ""),
    ("Additional Information", r"((?:Clean\s*Boost|Steam\s*Clean|Sanitize|Heated\s*Dry|Energy\s*Star)[\w\s]*)", ""),
    ("Capacity", r"(\d+(?:\.\d+)?)\s*(?:cu\.?\s*ft|cu\s*ft|CF)\b", "cu ft"),
    ("Weight", r"(\d+(?:\.\d+)?)\s*(?:lb|lbs)\b", "lb"),
    ("Width", r"(\d+(?:\.\d+)?)\s*in\b", "in"),
    ("Type", r"(Dishwasher|Washer|Dryer|Range|Oven|Microwave|Refrigerator|Freezer|Disposal)", ""),
    ("Energy Star", r"(Energy\s*Star)\b", ""),
    ("Display Only", r"(Display\s*Only)\b", ""),
]

LIGHTING_ATTRS = [
    ("Wattage", r"(\d+(?:\.\d+)?)\s*W\b", "W"),
    ("Color Temperature", r"(\d{4})\s*K\b", "K"),
    ("Color Temperature", r"(\d{3,4})\s*[Kk](?:elvin)?\b", "K"),
    ("Lumens", r"(\d+)\s*(?:LM|Lm|lm|Lumens?)\b", "lm"),
    ("Voltage", r"(\d+(?:[-\/]\d+)?)\s*V\b", "V"),
    ("Finish", r"\b(Black|Bronze|Chrome|Nickel|Gold|White|Silver|Oil[-\s]Rubbed|Brushed|Polished|Satin|Matte|Antique|Pewter|Frosted|Clear)\b", ""),
    ("Base Type", r"\b(E26|E27|GU10|GU24|Medium\s+Base|Candelabra|Bi[-\s]Pin|Edison)\b", ""),
    ("CCT", r"(Multi\s+CCT|Tunable|Warm|Cool|Daylight)\b", ""),
    ("CRI", r"CRI\s*(\d{2,3})\b", ""),
    ("IP Rating", r"IP(\d{2})\b", ""),
    ("Wattage Equivalent", r"(\d+)\s*W(?:att)?\s*(?:equiv|eq)", "W"),
    ("Dimmable", r"(Dimmable|Non[-\s]Dimmable)\b", ""),
    ("Size", r"(\d+)\s*(?:in|inch)\b", "in"),
    ("Color", r"\b(White|Black|Bronze|Nickel|Chrome|Brushed|Oil\s*Rubbed|Satin|Matte|Frosted)\b", ""),
    ("Lumens", r"(\d+)\s*(?:lm|LM|Lumens?)\b", "lm"),
]

BUILDING_ATTRS = [
    ("Length", r"(\d+(?:\.\d+)?)\s*(?:'|ft|feet)\b", "ft"),
    ("Width", r"(\d+(?:\.\d+)?)\s*(?:in|inch)\b", "in"),
    ("Color", r"\b(White|Black|Brown|Tan|Gray|Grey|Cedar|Teak|Natural|Classic|Coastal|IPE|Walnut|Mahogany|Driftwood|Tidal|Fog|Silver|Bronze|Chocolate|Copper|Sand|Khaki|Umber)\b", ""),
    ("Material", r"\b(Composite|Aluminum|Alm|PVC|Steel|Vinyl|Wood|Fiber\s+Cement|Cedar|WPC|Iron|Brass|Copper|Galvanized|Zinc|Stainless|Cast)\b", ""),
    ("Style", r"\b(Select|Classic|Premium|Horizontal|Vertical|Square|Round|Curved|Flat|Radius|Dogear|Beveled|Bullnose|Half\s*Round)\b", ""),
    ("Series", r"([\w]+)\s+(?:Select|Classic|Series)\b", ""),
    ("Profile", r"(T1-11|Ship\s*Lap|Channel\s*Lap|Dutch\s*Lap|Smooth|Wood\s*Grain|Tongue\s+and\s+Groove|T&G)", ""),
    ("Coverage", r"(\d+(?:\.\d+)?)\s*(?:sq\s*ft|sqft|sq\.?\s*ft)", "sq ft"),
    ("Thickness", r"(\d+(?:\.\d+)?)\s*(?:in|inch|mm)\b", "in"),
    ("Nominal Size", r"(\d+)\s*x\s*(\d+)\b", ""),
    ("R-Value", r"R[-\s]?(\d+(?:\.\d+)?)\b", ""),
    ("Weight", r"(\d+(?:\.\d+)?)\s*(?:lb|lbs)\b", "lb"),
    ("Insulation R-Value", r"R[-\s]?(\d+(?:\.\d+)?)\b", ""),
]

ELECTRICAL_ATTRS = [
    ("Box Size", r"(\d+[-\dx]+)\s*(?:Box|Oct)\b", ""),
    ("Gang", r"(\d+)\s*G(?:ang)?\b", ""),
    ("Material", r"\b(PVC|Metal|Steel|Plastic|Galvanized|Copper|Aluminum)\b", ""),
    ("Voltage", r"(\d+)\s*V\b", "V"),
    ("Amperage", r"(\d+)\s*A\b", "A"),
    ("Circuit Type", r"\b(GFCI|AFCI|Standard|Duplex|Tamper[-\s]Resistant|Quad|Combo|Split)\b", ""),
    ("Color", r"\b(White|Ivory|Almond|Black|Gray|Light\s*Almond|Brown)\b", ""),
    ("Wire Gauge", r"(\d+)\s*AWG\b", "AWG"),
    ("Load Center", r"(\d+)\s*A\s*(?:Load|Main|Panel)\b", "A"),
    ("Circuit Count", r"(\d+)\s*(?:Circuit|Space|Position)\b", ""),
    ("NEMA Rating", r"NEMA\s*(\d+[A-Z]*)\b", ""),
    ("Connector Type", r"\b(RJ45|RJ11|Cat5|Cat5e|Cat6|Cat6a|USB[-\s]A|USB[-\s]B|USB[-\s]C|HDMI|FType)\b", ""),
    ("Wattage", r"(\d+(?:\.\d+)?)\s*W\b", "W"),
    ("Gauge", r"(\d+)\s*(?:GA|ga|gauge)\b", ""),
]

POWER_TOOL_ATTRS = [
    ("Voltage", r"(\d+)\s*(?:V|Volt)", "V"),
    ("Amperage", r"(\d+(?:\.\d+)?)\s*(?:A|Amp)", "A"),
    ("Chuck Size", r"(\d+(?:\.\d+)?)\s*in(?:ch)?\s*(?:chuck)?", "in"),
    ("Blade Size", r"(\d+)\s*in(?:ch)?\s*(?:blade|saw)", "in"),
    ("Weight", r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\b", "lb"),
    ("RPM", r"(\d+)\s*(?:RPM|rpm)", "RPM"),
    ("Cordless", r"(Cordless|20V\s*MAX|18V|FLEXVOLT|M12|M18|20V|12V|60V|40V|80V)", ""),
    ("Battery", r"((?:\d+\.?\d*)\s*(?:Ah|ah|AMP-HR))", ""),
    ("Color", r"(Yellow|Black|Red|Orange|Green|Blue|Teal|Gray)", ""),
    ("Motor Type", r"(Brushless|Brushed)\s*(?:Motor)?", ""),
    ("SPM", r"(\d+)\s*(?:SPM|spm)", ""),
    ("Capacity", r"(\d+(?:\.\d+)?)\s*(?:in|mm)\s*(?:capacity|opening|cut)", ""),
    ("Depth of Cut", r"(\d+(?:\.\d+)?)\s*in(?:ch)?\s*(?:depth|cut)", "in"),
    ("Gauge", r"(\d+)\s*(?:ga|gauge)\b", ""),
]

SAFETY_ATTRS = [
    ("Type", r"(Cut[-\s]*Resistant|Impact|Chemical|Latex|Nitrile|Leather|Hi[-\s]Vis|HiVis)", ""),
    ("Level", r"(Level\s*\d|ANSI\s*\d+|CE\s*\d+|Class\s*\d+)", ""),
    ("Size", r"(XS|S|M|L|XL|XXL|Small|Medium|Large)", ""),
    ("Color", r"(Black|Blue|Green|Orange|Red|Hi[-\s]*Vis|Yellow|HiVis|Pink)", ""),
    ("Material", r"(Nitrile|Latex|Leather|Nylon|Polyester|ABS|Polycarbonate|Polypropylene|Neoprene|Spandex)", ""),
    ("Cut Level", r"Cut\s*Level\s*(\d)", ""),
    ("Coating", r"(Poly\s*urethane|PU|PVC|Latex|Nitrile|Foam\s*Lined|Thinsulate|Waterproof)", ""),
]

FASTENER_ATTRS = [
    ("Size", r"(\d+(?:\.\d+)?)\s*(?:x|X|\u00d7)\s*(\d+(?:\.\d+)?)", ""),
    ("Length", r"(\d+(?:\.\d+)?)\s*(?:in|inch|mm)\b", ""),
    ("Thread", r"#(\d+(?:-\d+)?)", ""),
    ("Head Type", r"(Phillips|Flat|Hex|Torx|Robertson|Round|Oval|Trim|Bugle|Pan|Button|Flat\s*Head|Round\s*Head)", ""),
    ("Material", r"(Steel|Stainless|Zinc|Brass|Plastic|Drywall|Concrete|Hardened|Grade\s*\d)", ""),
    ("Quantity", r"(\d+)\s*(?:Pack|Box|Pc|Pcs|Ct|per\s+Box|Case)\b", "EA"),
    ("Thread Type", r"(Self[-\s]Tapping|Self[-\s]Drilling|Coarse|Fine|Machine|Wood|Sheet\s*Metal)\b", ""),
    ("Drive Type", r"(Phillips|Slotted|Hex|Torx|Robertson|Square)\b", ""),
    ("Gauge", r"(\d+)\s*(?:ga|gauge|GA)\b", ""),
]

DECKING_ATTRS = [
    ("Length", r"(\d+(?:\.\d+)?)\s*(?:'|ft|feet)\b", "ft"),
    ("Width", r"(\d+(?:\.\d+)?)\s*(?:in|inch)\b", "in"),
    ("Color", r"\b(Walnut|Teak|Driftwood|Tidal|Fog|Silver|Bronze|Chocolate|Copper|Sand|Coastal|Classic|IPE|Gray|Brown|White|Black|Cedar|Mahogany|Rustic|Cypress|Spiced\s*Rum|Tiger\s*Wood|Lava|Vintage|Timber|Arctic|Island)\b", ""),
    ("Material", r"\b(Composite|Aluminum|PVC|Steel|Wood|WPC|Capstock)\b", ""),
    ("Style", r"\b(Select|Classic|Premium|Pro|Edge|Square|Round)\b", ""),
    ("Profile", r"\b(Grooved|Square\s*Edge|Radius\s*Edge|Flat|Reversible)\b", ""),
    ("Coverage", r"(\d+(?:\.\d+)?)\s*(?:sq\s*ft|sqft|sq\.?\s*ft)", "sq ft"),
    ("Board Length", r"(\d+)\s*(?:'|ft)\b", "ft"),
    ("Fastener Type", r"\b(Clip|Screw|Nail|Hidden|Surface)\b", ""),
    ("Weight", r"(\d+(?:\.\d+)?)\s*(?:lb|lbs)\b", "lb"),
]

GRAMMAR_MAP = {
    "Abrasives": ABRASIVE_ATTRS,
    "Appliances": APPLIANCE_ATTRS,
    "Lighting": LIGHTING_ATTRS,
    "Building Materials": BUILDING_ATTRS,
    "Power Tools": POWER_TOOL_ATTRS,
    "Hand Tools": POWER_TOOL_ATTRS,
    "Electrical": ELECTRICAL_ATTRS,
    "Safety Products": SAFETY_ATTRS,
    "Safety": SAFETY_ATTRS,
    "Fasteners": FASTENER_ATTRS,
    "Decking": DECKING_ATTRS,
    "Fans": LIGHTING_ATTRS,
    "Windows & Doors": BUILDING_ATTRS,
    "Plumbing": BUILDING_ATTRS,
    "Automotive": POWER_TOOL_ATTRS,
}

GENERIC_ATTRS = [
    ("Voltage", r"(\d+)\s*V\b", "V"),
    ("Amperage", r"(\d+(?:\.\d+)?)\s*A\b", "A"),
    ("Wattage", r"(\d+(?:\.\d+)?)\s*W\b", "W"),
    ("Weight", r"(\d+(?:\.\d+)?)\s*(?:lb|lbs)\b", "lb"),
    ("Color", r"\b(White|Black|Gray|Grey|Silver|Bronze|Red|Blue|Green|Brown|Natural|Clear|Chrome|Nickel|Brushed|Matte|Satin)\b", ""),
    ("Material", r"\b(Steel|Stainless|Aluminum|Plastic|PVC|Copper|Brass|Nylon|Rubber|Ceramic|Glass|Wood|Composite|Vinyl|Iron|Zinc|Galvanized|Nitrile|Leather)\b", ""),
    ("Size", r"(\d+(?:\.\d+)?)\s*(?:in|inch|mm|cm)\b", ""),
    ("Quantity", r"(\d+)\s*(?:Pack|Box|Pc|Pcs|Ct|Case|Roll|Sheet|Disc|Set|Pair|Kit)\b", "EA"),
    ("Gauge", r"(\d+)\s*(?:ga|gauge|AWG)\b", ""),
    ("NEMA Rating", r"NEMA\s*(\d+[A-Z]*)\b", ""),
    ("IP Rating", r"IP(\d{2,3})\b", ""),
    ("Diameter", r"(\d+(?:\.\d+)?)\s*(?:in|inch|mm|cm)\s*(?:dia|diameter)\b", ""),
    ("Length", r"(\d+(?:\.\d+)?)\s*(?:ft|feet|foot)\b", "ft"),
    ("Thread Size", r"#(\d+(?:-\d+)?)\b", ""),
    ("Head Type", r"\b(Hex|Phillips|Slotted|Torx|Star|Flat|Round|Pan|Binding|Carriage)\b", ""),
    ("Application", r"\b(Indoor|Outdoor|Commercial|Industrial|Residential|Heavy[- ]Duty)\b", ""),
    ("Pack Type", r"\b(Bulk|Pack|Box|Case|Kit|Set|Bundle)\b", ""),
]


def _get_attrs_for_classpath(classpath):
    if not classpath:
        return GENERIC_ATTRS
    for category, attrs in GRAMMAR_MAP.items():
        if classpath.startswith(category):
            return attrs
    return GENERIC_ATTRS


def _extract_attrs(text, grammar):
    attributes = []
    if not text or not grammar:
        return attributes
    for label, pattern, uom in grammar:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            value = m.group(1).strip() if m.lastindex else m.group(0).strip()
            if value and len(value) > 0:
                already = any(a["label"].lower() == label.lower() for a in attributes)
                if not already:
                    attributes.append({"label": label, "value": value, "uom": uom})
    return attributes


def extract_grammar_attributes(desc, classpath, dimensions):
    grammar = _get_attrs_for_classpath(classpath)
    attrs = _extract_attrs(desc, grammar)
    # Also try generic attrs for fields not covered by category grammar
    generic = _extract_attrs(desc, GENERIC_ATTRS)
    existing_labels = {a["label"].lower() for a in attrs}
    for g in generic:
        if g["label"].lower() not in existing_labels:
            attrs.append(g)
    return attrs


def _generic_grammar(dimensions):
    return GENERIC_ATTRS


def extract_attributes_from_text(text, classpath=''):
    grammar = _get_attrs_for_classpath(classpath)
    return _extract_attrs(text, grammar)
