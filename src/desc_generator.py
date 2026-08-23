"""
Description Generator Module for Unilog Product Intelligence Pipeline.

Generates multiple formatted descriptions from parsed product data
following Unilog content guidelines.
"""

from typing import Dict, List, Optional
import re


class DescriptionGenerator:
    """Generates formatted product descriptions from parsed attributes."""

    BRAND_TRADEMARKS = {
        "FRIGIDAIRE": "FRIGIDAIRE®",
        "Whirlpool": "Whirlpool®",
        "Whirlpool Corporation": "Whirlpool Corporation®",
        "KitchenAid": "KitchenAid®",
        "Maytag": "Maytag®",
        "Amana": "Amana®",
        "GE": "GE®",
        "General Electric": "General Electric®",
        "Samsung": "Samsung®",
        "LG": "LG®",
        "Bosch": "Bosch®",
        "Electrolux": "Electrolux®",
        "Milwaukee": "Milwaukee®",
        "Makita": "Makita®",
        "DeWalt": "DeWalt®",
        "DeWALT": "DeWALT®",
        "Dewalt": "Dewalt®",
        "Ryobi": "Ryobi®",
        "Ridgid": "Ridgid®",
        "Craftsman": "Craftsman®",
        "Kobalt": "Kobalt®",
        "Husky": "Husky®",
        "Stanley": "Stanley®",
        "Irwin": "Irwin®",
        "Lenox": "Lenox®",
        "Klein": "Klein®",
        "Southwire": "Southwire®",
        "Leviton": "Leviton®",
        "Lutron": "Lutron®",
        "Siemens": "Siemens®",
        "Square D": "Square D®",
        "Philips": "Philips®",
        "Cree": "Cree®",
        "Feit": "Feit®",
        "Sylvania": "Sylvania®",
        "Trex": "Trex®",
        "AZEK": "AZEK®",
        "TimberTech": "TimberTech®",
        "Fiberon": "Fiberon®",
        "Deckorators": "Deckorators®",
        "Satco": "Satco®",
        "Kichler": "Kichler®",
        "Streamlight": "Streamlight®",
        "Senco": "Senco®",
        "Freud": "Freud®",
        "CMT": "CMT®",
        "Festool": "Festool®",
        "Metabo": "Metabo®",
        "Hitachi": "Hitachi®",
        "Moen": "Moen®",
        "Kohler": "Kohler®",
        "American Standard": "American Standard®",
        "Pfister": "Pfister®",
        "SharkBite": "SharkBite®",
        "Oatey": "Oatey®",
        "Watts": "Watts®",
        "First Alert": "First Alert®",
        "Police Security": "Police Security®",
        "ACG Brands": "ACG Brands®",
        "MillerTech": "MillerTech®",
        "Woodpeckers": "Woodpeckers®",
        "Sabre": "Sabre®",
        "Prebena": "Prebena®",
        "Mafell": "Mafell®",
        "Saw Stop": "Saw Stop®",
        "Speed Queen": "Speed Queen®",
        "Miele": "Miele®",
        "Diablo": "Diablo®",
        "3M": "3M®",
        "Norton": "Norton®",
        "Grainger": "Grainger®",
        "Hilti": "Hilti®",
        "Bosch": "Bosch®",
        "Fischer": "Fischer®",
        "Hillman": "Hillman®",
        "Leatherman": "Leatherman®",
        "Gerber": "Gerber®",
        "OX Tools": "OX Tools®",
        "Channellock": "Channellock®",
        "Vise-Grip": "Vise-Grip®",
        "Knipex": "Knipex®",
        "Wiha": "Wiha®",
        "Wera": "Wera®",
        "Snap-on": "Snap-on®",
        "GearWrench": "GearWrench®",
        "Simpson Strong-Tie": "Simpson Strong-Tie®",
        "GRK": "GRK®",
        "FastenMaster": "FastenMaster®",
        "DeckMate": "DeckMate®",
        "Starborn": "Starborn®",
        " TOGGLER": "TOGGLER®",
        "Eaton": "Eaton®",
        "Leviton": "Leviton®",
        "Cooper": "Cooper®",
        "Pass & Seymour": "Pass & Seymour®",
        "Hubbell": "Hubbell®",
        "Wiremold": "Wiremold®",
        "Arlington": "Arlington®",
        "Raco": "Raco®",
        "Mars": "Mars®",
        "Intermatic": "Intermatic®",
        "Everbilt": "Everbilt®",
        "Keeney": "Keeney®",
        "PlumbWorks": "PlumbWorks®",
        "Fluidmaster": "Fluidmaster®",
        "BrassCraft": "BrassCraft®",
        "Wolverine Brass": "Wolverine Brass®",
        "Delta": "Delta®",
        "Peerless": "Peerless®",
        "Symmons": "Symmons®",
        "Rheem": "Rheem®",
        "A.O. Smith": "A.O. Smith®",
        "Bradford White": "Bradford White®",
        "Navien": "Navien®",
        "Noritz": "Noritz®",
        "Rinnai": "Rinnai®",
        "Lennox": "Lennox®",
        "Trane": "Trane®",
        "Carrier": "Carrier®",
        "Goodman": "Goodman®",
        "Daikin": "Daikin®",
        "Honeywell": "Honeywell®",
        "Emerson": "Emerson®",
        "Contactor": "Contactor®",
        "White-Rodgers": "White-Rodgers®",
        "Aspen": "Aspen®",
        "Aspenaire": "Aspenaire®",
        "Field Controls": "Field Controls®",
        "Tjernlund": "Tjernlund®",
        "Master Flow": "Master Flow®",
        "Ventamatic": "Ventamatic®",
        "Coolerado": "Coolerado®",
        "Broan": "Broan®",
        "NuTone": "NuTone®",
        "Panasonic": "Panasonic®",
        "Hunter": "Hunter®",
        "Fanimation": "Fanimation®",
        "Minka": "Minka®",
        "WAC Lighting": "WAC Lighting®",
        "ET2": "ET2®",
        "Sea Gull": "Sea Gull®",
        "Progress": "Progress®",
        "Generation Lighting": "Generation Lighting®",
        "Hampton Bay": "Hampton Bay®",
        "Globe": "Globe®",
        "Lithonia": "Lithonia®",
        "Commercial Electric": "Commercial Electric®",
        "Enbrighten": "Enbrighten®",
        "Ushio": "Ushio®",
        "Bulbrite": "Bulbrite®",
        "Sunbeam": "Sunbeam®",
        "Leviton": "Leviton®",
        "Jasco": "Jasco®",
        "Legrand": "Legrand®",
        "Wiremold": "Wiremold®",
        "Arlington": "Arlington®",
        "Raco": "Raco®",
        "Westbury": "Westbury®",
        "Andersen": "Andersen®",
        "Jamsill": "Jamsill®",
        "James Hardie": "James Hardie®",
        "LP SmartSide": "LP SmartSide®",
        "ProVia": "ProVia®",
        "Gentek": "Gentek®",
        "Ply Gem": "Ply Gem®",
        "MI Windows": "MI Windows®",
        "Sunlite": "Sunlite®",
        "CEinfinity": "CEinfinity®",
        "PLT": "PLT®",
        "Maxxima": "Maxxima®",
        "Hudson": "Hudson®",
        "Sea Gull Lighting": "Sea Gull Lighting®",
        "Paradigm": "Paradigm®",
        "Globe Electric": "Globe Electric®",
        "Finyline": "Finyline®",
        "Kreg": "Kreg®",
        "Mirka": "Mirka®",
        "Hunter Fan": "Hunter Fan®",
        "U S Tape": "U S Tape®",
        "Vessel Tools": "Vessel Tools®",
        "Premier Metals": "Premier Metals®",
        "Palmer Donavin": "Palmer Donavin®",
        "Whiteside": "Whiteside®",
        "VELUX": "VELUX®",
        "Appliance Dealers Cooperative": "Appliance Dealers Cooperative®",
        "Rees Cast Stone": "Rees Cast Stone®",
        "Edge Eyewear": "Edge Eyewear®",
        "Tech Gear": "Tech Gear®",
        "Jasco": "Jasco®",
        "Oliver": "Oliver®",
        "Prime": "Prime®",
        "AJM": "AJM®",
        "BRK": "BRK®",
        "Black & Decker": "Black & Decker®",
        "Bow": "Bow®",
        "Century Components": "Century Components®",
        "Carlon": "Carlon®",
        "Certainteed": "Certainteed®",
        "DSI Westbury": "DSI Westbury®",
        "Dremel": "Dremel®",
        "Emseal Joint": "Emseal Joint®",
        "Fenton Bros": "Fenton Bros®",
        "GT-Lite": "GT-Lite®",
        "Grizzly": "Grizzly®",
        "J&G": "J&G®",
        "James Hardie": "James Hardie®",
        "JAMESHARDIE": "James Hardie®",
        "JPW": "JPW®",
        "Jet": "Jet®",
        "Malco": "Malco®",
        "Marshalltown Trowel": "Marshalltown Trowel®",
        "Maxsa": "Maxsa®",
        "MillerTech Energy": "MillerTech Energy®",
        "Mirka Abrasives": "Mirka Abrasives®",
        "National Hardware": "National Hardware®",
        "Ohio Firewatch Protection": "Ohio Firewatch Protection®",
        "United Window & Door": "United Window & Door®",
        "V & V Appliance Parts": "V & V Appliance Parts®",
        "Wera Tools NA": "Wera Tools NA®",
        "Wiz": "Wiz®",
    }

    MAX_MOBILE_DESC_LEN = 80
    MIN_MOBILE_DESC_LEN = 60
    MAX_INVOICE_DESC_LEN = 40

    def _title_case(self, text: str) -> str:
        """Capitalize words but keep brand symbols and special formatting."""
        if not text:
            return ""
        words = text.split()
        result = []
        for word in words:
            if word in ("®", "™", "©"):
                result.append(word)
            elif word.startswith("®") or word.startswith("™"):
                prefix = word[0]
                rest = word[1:]
                result.append(prefix + rest.capitalize())
            elif word.isupper() and len(word) <= 4:
                result.append(word)
            else:
                result.append(word.capitalize())
        return " ".join(result)

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text at proper word boundary without breaking words."""
        if not text or len(text) <= max_len:
            return text
        truncated = text[:max_len].rsplit(" ", 1)[0]
        if truncated.endswith((",", ".", ";", ":", " ")):
            truncated = truncated[:-1].rstrip()
        return truncated

    def _format_dimension(self, value: str, uom: str) -> str:
        """Format dimension as 'value uom' with proper spacing."""
        if not value:
            return ""
        value = value.strip()
        uom = uom.strip() if uom else ""
        return f"{value} {uom}".strip() if uom else value

    def _join_features(self, features: List[str], separator: str = ", ") -> str:
        """Join feature list with given separator, filtering empty strings."""
        cleaned = [f.strip() for f in features if f and f.strip()]
        return separator.join(cleaned)

    def _apply_trademark(self, brand: str) -> str:
        """Apply trademark symbol to brand if recognized."""
        if not brand:
            return ""
        for key, trademarked in self.BRAND_TRADEMARKS.items():
            if key.lower() == brand.strip().lower():
                return trademarked
        return brand

    def _clean_brand(self, brand: str) -> str:
        """Remove existing trademark symbols before processing."""
        if not brand:
            return ""
        return brand.replace("®", "").replace("™", "").replace("©", "").strip()

    def generate_mobile_desc(
        self,
        brand: str,
        product_type: str,
        series: str,
        mpn: str,
        features_list: List[str],
        mounting: Optional[str] = None,
        material: Optional[str] = None,
        color: Optional[str] = None,
        part_desc: Optional[str] = None,
        grit: Optional[str] = None,
        quantity: Optional[str] = None,
        raw_dimensions: Optional[str] = None,
    ) -> str:
        """Generate mobile description, 60-80 characters.

        Format: Brand, ProductType, Series, Dimensions, Material, Color, Grit, MPN
        Example: "Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF"
        """
        clean_brand = self._clean_brand(brand)
        brand_display = self._apply_trademark(clean_brand)
        if not brand_display and brand:
            brand_display = brand

        parts = []
        if brand_display:
            parts.append(brand_display)
        if product_type:
            parts.append(product_type.strip())
        if series:
            parts.append(series.strip())
        if raw_dimensions:
            parts.append(raw_dimensions.strip())
        if material:
            parts.append(material.strip())
        if color:
            parts.append(color.strip())
        if grit:
            grit_str = grit if grit.startswith("P") else f"P{grit}"
            parts.append(grit_str)
        if quantity:
            parts.append(f"{quantity} pack")
        if mounting:
            parts.append(mounting.strip())

        desc = ", ".join(parts)

        if len(desc) > self.MAX_MOBILE_DESC_LEN:
            desc = self._truncate(desc, self.MAX_MOBILE_DESC_LEN)

        if len(desc) < self.MIN_MOBILE_DESC_LEN and features_list:
            remaining_budget = self.MAX_MOBILE_DESC_LEN - len(desc) - 2
            added_features = []
            for feat in features_list:
                if feat and len(feat) + 2 <= remaining_budget:
                    added_features.append(feat)
                    remaining_budget -= len(feat) + 2
            if added_features:
                desc = desc + ", " + ", ".join(added_features)

        if len(desc) < self.MIN_MOBILE_DESC_LEN and part_desc:
            clean_part = part_desc.strip()
            if mpn and clean_part.startswith(mpn.strip()):
                clean_part = clean_part[len(mpn.strip()):].strip().lstrip("-").strip()
            if clean_part:
                words_to_add = []
                for word in clean_part.split():
                    if word not in desc and not any(word.lower() in desc.lower() for _ in [1]):
                        words_to_add.append(word)
                filler = " ".join(words_to_add)
                if filler:
                    remaining_budget = self.MAX_MOBILE_DESC_LEN - len(desc) - 2
                    if len(filler) <= remaining_budget:
                        desc = desc + ", " + filler
                    else:
                        truncated = filler[:remaining_budget]
                        last_space = truncated.rfind(" ")
                        if last_space > 20:
                            truncated = truncated[:last_space]
                        if truncated:
                            desc = desc + ", " + truncated

        if len(desc) < self.MIN_MOBILE_DESC_LEN and mpn:
            mpn_str = mpn.strip()
            if mpn_str not in desc:
                remaining_budget = self.MAX_MOBILE_DESC_LEN - len(desc) - 2
                if len(mpn_str) <= remaining_budget:
                    if desc:
                        desc = desc + ", " + mpn_str
                    else:
                        desc = mpn_str

        if len(desc) > self.MAX_MOBILE_DESC_LEN:
            desc = self._truncate(desc, self.MAX_MOBILE_DESC_LEN)

        if not desc and mpn:
            desc = mpn.strip()

        return desc

    def generate_invoice_desc(
        self,
        product_type: str,
        attributes_dict: Optional[Dict[str, str]] = None,
        part_desc: Optional[str] = None,
        grit: Optional[str] = None,
        material: Optional[str] = None,
        color: Optional[str] = None,
        raw_dimensions: Optional[str] = None,
    ) -> str:
        """Generate invoice description, max 40 chars, ALL CAPS.

        Format: Product type + key specs compressed.
        Example: "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN"
        """
        parts = []
        if product_type:
            parts.append(product_type.strip().upper())

        if attributes_dict:
            key_specs = [
                "mounting",
                "wash_cycles",
                "material",
                "voltage",
                "amperage",
                "width",
                "height",
                "depth",
                "capacity",
                "color",
                "finish",
                "installation",
            ]
            for key in key_specs:
                if key in attributes_dict and attributes_dict[key]:
                    val = attributes_dict[key].strip()
                    if key == "width":
                        val = val.replace(" ", "")
                        if "in" not in val.lower():
                            val += "IN"
                        parts.append(val.upper())
                    elif key == "height":
                        val = val.replace(" ", "")
                        if "in" not in val.lower():
                            val += "IN"
                        parts.append(val.upper())
                    elif key == "depth":
                        val = val.replace(" ", "")
                        if "in" not in val.lower():
                            val += "IN"
                        parts.append(val.upper())
                    elif key == "voltage":
                        val = val.replace(" ", "")
                        if "v" not in val.lower():
                            val += "V"
                        parts.append(val.upper())
                    elif key == "amperage":
                        val = val.replace(" ", "")
                        if "a" not in val.lower():
                            val += "A"
                        parts.append(val.upper())
                    else:
                        parts.append(val.upper())

            remaining_keys = [
                k for k in attributes_dict
                if k not in key_specs and attributes_dict[k]
            ]
            for key in remaining_keys:
                val = attributes_dict[key].strip().upper()
                if val:
                    parts.append(val)

        desc = " ".join(parts)

        if not desc and part_desc:
            clean = re.sub(r'[^A-Za-z0-9/\s\-\.]', ' ', part_desc).strip()
            desc = clean.upper()[:self.MAX_INVOICE_DESC_LEN]

        if grit:
            grit_str = f"P{grit}" if not grit.startswith("P") else grit.upper()
            if grit_str not in desc:
                test = (desc + " " + grit_str).strip()
                if len(test) <= self.MAX_INVOICE_DESC_LEN:
                    desc = test
                elif not desc:
                    desc = grit_str[:self.MAX_INVOICE_DESC_LEN]

        if material and material.upper() not in desc:
            test = (desc + " " + material.upper()).strip()
            if len(test) <= self.MAX_INVOICE_DESC_LEN:
                desc = test

        if color and color.upper() not in desc:
            test = (desc + " " + color.upper()).strip()
            if len(test) <= self.MAX_INVOICE_DESC_LEN:
                desc = test

        if raw_dimensions and raw_dimensions.upper() not in desc:
            has_dim = any(x in desc for x in ['IN', 'FT', '"', 'MM', 'CM', 'X'])
            if not has_dim:
                dim_clean = raw_dimensions.replace('"', 'IN').replace("'", 'FT').replace(' ', '').upper()
                test = (desc + " " + dim_clean).strip()
                if len(test) <= self.MAX_INVOICE_DESC_LEN:
                    desc = test

        desc = self._truncate(desc, self.MAX_INVOICE_DESC_LEN)
        desc = desc.upper()

        return desc

    def generate_short_desc(
        self,
        brand: str,
        series: str,
        mpn: str,
        product_type: str,
        features_list: List[str],
    ) -> str:
        """Generate product title / short description.

        Format: "BRAND Series MPN ProductType With Features"
        Example: "FRIGIDAIRE Professional Series PDSH4816AF Dishwasher
                  With CleanBoost, Leg Mounting, 5-Wash Cycle, Stainless Steel"
        """
        clean_brand = self._clean_brand(brand)
        brand_upper = clean_brand.upper() if clean_brand else ""

        parts = []
        if brand_upper:
            parts.append(brand_upper)
        if series:
            parts.append(series.strip())
        if mpn:
            parts.append(mpn.strip())
        if product_type:
            parts.append(product_type.strip())

        if features_list and any(f.strip() for f in features_list):
            joined = self._join_features(features_list, ", ")
            parts.append("With " + joined)

        return " ".join(parts)

    def generate_long_desc(
        self,
        brand: str,
        product_type: str,
        series: str,
        attributes_dict: Optional[Dict[str, str]] = None,
        features_list: Optional[List[str]] = None,
        additional_info: Optional[str] = None,
    ) -> str:
        """Generate full product description.

        Format: "BRAND ProductType With Features, Series, Specs..., Material, Additional Info: ..."
        Example: "FRIGIDAIRE Dishwasher With CleanBoost, Professional Series,
                  5 Wash Cycles, 120 V, 15 A, Leg Mounting, 24 in W x 24-1/4 in D..."
        """
        clean_brand = self._clean_brand(brand)
        brand_upper = clean_brand.upper() if clean_brand else ""

        parts = []
        if brand_upper:
            parts.append(brand_upper)
        if product_type:
            parts.append(product_type.strip())

        if features_list and any(f.strip() for f in features_list):
            joined = self._join_features(features_list, ", ")
            parts.append("With " + joined)

        if series:
            parts.append(series.strip())

        if attributes_dict:
            spec_order = [
                "wash_cycles",
                "voltage",
                "amperage",
                "mounting",
                "width",
                "height",
                "depth",
                "material",
                "color",
                "finish",
                "capacity",
                "installation",
                "energy_rating",
                "water_usage",
                "noise_level",
            ]

            for key in spec_order:
                if key in attributes_dict and attributes_dict[key]:
                    val = attributes_dict[key].strip()
                    label = key.replace("_", " ").title()
                    parts.append(f"{val} {label}" if not val.endswith(label) else val)

            for key, val in attributes_dict.items():
                if key not in spec_order and val and val.strip():
                    parts.append(val.strip())

        if additional_info and additional_info.strip():
            parts.append(f"Additional Info: {additional_info.strip()}")

        desc = ", ".join(parts)
        desc = self._truncate(desc, 500)

        return desc

    def generate_retail_desc(
        self,
        series: str,
        product_type: str,
        features_list: List[str],
    ) -> str:
        """Generate marketing / retail description.

        Format: "Series ProductType, Features..."
        Example: "Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel"
        """
        parts = []
        if series:
            parts.append(series.strip())
        if product_type:
            parts.append(product_type.strip())

        base = " ".join(parts) if parts else ""

        feature_str = ""
        if features_list and any(f.strip() for f in features_list):
            feature_str = self._join_features(features_list, ", ")

        if base and feature_str:
            return f"{base}, {feature_str}"
        elif base:
            return base
        else:
            return feature_str

    def generate_marketing_desc(
        self,
        brand: str,
        product_type: str,
        features_list: Optional[List[str]] = None,
    ) -> str:
        """Generate 1-2 sentence marketing copy.

        Generic but appealing description based on product type and features.
        """
        clean_brand = self._clean_brand(brand)
        brand_name = self._apply_trademark(clean_brand) if clean_brand else ""
        if not brand_name and brand:
            brand_name = brand

        ptype = product_type.strip() if product_type else "product"

        if features_list and len(features_list) > 0:
            top_features = [f.strip() for f in features_list[:3] if f.strip()]
            features_text = self._join_features(top_features, ", ")
            sentence1 = (
                f"Upgrade your home with the {brand_name} {ptype}, "
                f"designed to deliver exceptional performance and reliability."
            )
            sentence2 = (
                f"Featuring {features_text}, this {ptype} combines "
                f"innovative technology with sleek design to meet your everyday needs."
            )
        else:
            sentence1 = (
                f"Discover the {brand_name} {ptype}, engineered for "
                f"outstanding performance and lasting durability."
            )
            sentence2 = (
                f"With a focus on quality and efficiency, this {ptype} is "
                f"the perfect addition to any modern home."
            )

        return f"{sentence1} {sentence2}"

    def generate_item_features(self, features_list: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate dict with ITEM_FEATURES_1 through ITEM_FEATURES_20.

        Each item from features_list is assigned to a numbered key.
        Unused keys are set to empty string.
        """
        result = {}
        for i in range(1, 21):
            key = f"ITEM_FEATURES_{i}"
            if features_list and i <= len(features_list):
                val = features_list[i - 1]
                result[key] = val.strip() if val else ""
            else:
                result[key] = ""
        return result
