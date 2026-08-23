"""
Description Formula Engine - Ground-Truth Aligned
"""
import re
from typing import Dict, List, Optional

MAX_INVOICE = 40
MAX_MOBILE = 80
MIN_MOBILE = 60

INVOICE_ABBREVS = {
    'Leg': 'LEG', 'Built-in': 'BLTN', 'Freestanding': 'FRST',
    'Wall Mount': 'WLMT', 'Under Counter': 'UNDCT',
    'Stainless Steel': 'SST', 'Black Stainless': 'BKST',
    'White': 'WHT', 'Aluminum': 'ALM', 'PVC': 'PVC',
    'Black': 'BLK', 'Gray': 'GRY', 'Bisque': 'BISQ',
    'Panel Ready': 'PAN',
    'SS': 'SST',
}


def _smart_truncate(text, max_len):
    if not text or len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    if truncated and truncated[-1] in ",.;: ":
        truncated = truncated[:-1].rstrip()
    return truncated


def _get_category(classpath):
    if not classpath:
        return "generic"
    cl = classpath.lower()
    if "abrasive" in cl:
        return "abrasives"
    if "lighting" in cl:
        return "lighting"
    if any(k in cl for k in ["building", "lumber", "siding", "decking", "roofing", "drywall"]):
        return "building"
    if any(k in cl for k in ["power tool", "hand tool"]):
        return "power_tools"
    if any(k in cl for k in ["appliance", "kitchen", "laundry"]):
        return "appliance"
    if "electrical" in cl:
        return "electrical"
    if "fastener" in cl:
        return "fastener"
    if "safety" in cl:
        return "safety"
    return "generic"


def generate_invoice_desc(product_type, attributes, dimensions,
                          classpath="", grit="", quantity="", raw_dimensions=""):
    cat = _get_category(classpath)
    attr_dict = {}
    if attributes:
        attr_dict = {a["label"].lower(): a["value"] for a in attributes}

    parts = []

    if cat == "abrasives":
        ptype = product_type.upper() if product_type else "ABRASIVE"
        parts.append(ptype[:12])
        if raw_dimensions:
            d = raw_dimensions.replace('"', 'IN').replace("'", 'FT').replace(' ', '')
            parts.append(d.upper()[:10])
        if grit:
            g = grit if grit.startswith('P') else f"P{grit}"
            parts.append(g.upper())
        mat = dimensions.get("material", "") or attr_dict.get("abrasive type", "")
        if mat:
            parts.append(mat.upper()[:6])
        if quantity:
            parts.append(f"{quantity}PK")

    elif cat == "appliance":
        ptype = product_type.upper() if product_type else ""
        if ptype:
            parts.append(ptype)
        mounting = attr_dict.get("mounting type", "") or dimensions.get("mounting", "")
        if mounting:
            abbr = INVOICE_ABBREVS.get(mounting, mounting.upper()[:4])
            parts.append(abbr)
        cycles = attr_dict.get("number of wash cycles", "") or dimensions.get("wash_cycles", "")
        if cycles:
            parts.append(cycles)
        color = attr_dict.get("color", "") or dimensions.get("color", "")
        if color:
            abbr = INVOICE_ABBREVS.get(color, color.upper()[:3])
            parts.append(abbr)
        voltage = dimensions.get("voltage", "")
        if voltage:
            v = re.sub(r'\s+', '', str(voltage))
            if 'v' not in v.lower():
                v += 'V'
            parts.append(v.upper())
        amperage = dimensions.get("amperage", "")
        if amperage:
            a = re.sub(r'\s+', '', str(amperage))
            if 'a' not in a.lower():
                a += 'A'
            parts.append(a.upper())
        sound = attr_dict.get("sound level", "") or dimensions.get("sound_level", "")
        if sound:
            s = re.sub(r'\s+', '', str(sound))
            if 'dba' not in s.lower():
                s += 'DBA'
            parts.append(s.upper())
        else:
            depth = dimensions.get("depth_open", "") or dimensions.get("depth", "")
            if depth:
                d = re.sub(r'\s+', '', str(depth))
                if 'in' not in d.lower():
                    d += 'IN'
                parts.append(d.upper())

    elif cat == "lighting":
        ptype = product_type.upper() if product_type else ""
        if ptype:
            parts.append(ptype[:12])
        finish = dimensions.get("finish", "") or attr_dict.get("finish", "")
        if finish:
            parts.append(finish.upper()[:5])
        wattage = dimensions.get("wattage", "")
        if wattage:
            parts.append(f"{wattage}W")
        cct = dimensions.get("color_temp", "") or attr_dict.get("color temperature", "")
        if cct:
            parts.append(f"{cct}K")
        base = dimensions.get("lamp_base", "") or attr_dict.get("base type", "")
        if base:
            parts.append(base.upper()[:6])

    elif cat == "building":
        ptype = product_type.upper() if product_type else ""
        if ptype:
            parts.append(ptype[:12])
        if raw_dimensions:
            d = raw_dimensions.replace('"', 'IN').replace("'", 'FT').replace(' ', '')
            parts.append(d.upper()[:12])
        color = dimensions.get("color", "") or attr_dict.get("color", "")
        if color:
            parts.append(color.upper()[:6])
        material = dimensions.get("material", "") or attr_dict.get("material", "")
        if material:
            parts.append(material.upper()[:6])

    elif cat == "power_tools":
        ptype = product_type.upper() if product_type else ""
        if ptype:
            parts.append(ptype[:12])
        voltage = dimensions.get("voltage", "")
        if voltage:
            v = re.sub(r'\s+', '', str(voltage))
            if 'v' not in v.lower():
                v += 'V'
            parts.append(v.upper())

    else:
        ptype = product_type.upper() if product_type else ""
        if ptype:
            parts.append(ptype[:16])
        for key in ["voltage", "amperage", "wattage", "color", "material"]:
            val = dimensions.get(key, "") or attr_dict.get(key, "")
            if val:
                parts.append(str(val).upper()[:8])

    if not parts:
        parts.append("PRODUCT")

    desc = " ".join(parts)

    if raw_dimensions and not any(d in desc for d in ['IN', 'FT', '"', 'X', 'MM']):
        d_clean = raw_dimensions.replace('"', 'IN').replace("'", 'FT').replace(' ', '').upper()
        test = f"{desc} {d_clean}"
        if len(test) <= MAX_INVOICE:
            desc = test

    return _smart_truncate(desc, MAX_INVOICE).upper()


def generate_mobile_desc(manufacturer, brand, product_type, series, mpn,
                         mounting="", attributes=None, raw_dimensions="",
                         classpath="", part_desc="", grit="", quantity="",
                         color="", material=""):
    parts = []
    if manufacturer:
        parts.append(manufacturer.strip())
    if brand and brand != manufacturer:
        parts.append(brand.strip())
    if product_type:
        parts.append(product_type.strip())
    if series:
        s = series.strip()
        if "series" not in s.lower():
            parts.append(f"{s} Series")
        else:
            parts.append(s)
    if mpn:
        parts.append(mpn.strip())

    seen = set()
    unique_parts = []
    for p in parts:
        key = p.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique_parts.append(p)
    parts = unique_parts

    if mounting:
        test = f"{', '.join(parts)}, {mounting.strip()}"
        if len(test) <= MAX_MOBILE:
            parts.append(mounting.strip())

    if raw_dimensions:
        test = f"{', '.join(parts)}, {raw_dimensions.strip()}"
        if len(test) <= MAX_MOBILE:
            parts.append(raw_dimensions.strip())

    desc = ", ".join(parts)

    if len(desc) > MAX_MOBILE:
        while len(desc) > MAX_MOBILE and len(parts) > 3:
            parts.pop()
            desc = ", ".join(parts)
        if len(desc) > MAX_MOBILE:
            desc = _smart_truncate(desc, MAX_MOBILE)

    if len(desc) < MIN_MOBILE and attributes:
        for a in attributes[:10]:
            tag = f"{a['label']}={a['value']}"
            if tag.lower() not in desc.lower():
                test = f"{desc}, {tag}"
                if len(test) <= MAX_MOBILE:
                    desc = test
                else:
                    break

    if len(desc) < MIN_MOBILE:
        extras = []
        if part_desc:
            clean_part = part_desc.strip()
            if mpn and clean_part.startswith(mpn.strip()):
                clean_part = clean_part[len(mpn.strip()):].strip().lstrip("-").strip()
            if clean_part:
                extras.append(clean_part[:40])
        if color:
            extras.append(color)
        if material:
            extras.append(material)
        if grit:
            extras.append(f"P{grit}" if not grit.startswith("P") else grit)
        if quantity:
            extras.append(f"{quantity} pack")
        for extra in extras:
            if extra and extra.lower() not in desc.lower():
                test = f"{desc}, {extra}"
                if len(test) <= MAX_MOBILE:
                    desc = test
                else:
                    break

    if len(desc) < MIN_MOBILE and mpn and mpn not in desc:
        test = f"{desc}, {mpn}" if desc else mpn
        if len(test) <= MAX_MOBILE:
            desc = test

    if len(desc) > MAX_MOBILE:
        desc = _smart_truncate(desc, MAX_MOBILE)

    return desc
