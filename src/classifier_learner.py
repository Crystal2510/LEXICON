"""
Classifier Learner - Keyword + TF-IDF + Manufacturer Context
"""
import re
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

HAS_SKLEARN = None

def _ensure_sklearn():
    global HAS_SKLEARN
    if HAS_SKLEARN is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.calibration import CalibratedClassifierCV
            HAS_SKLEARN = True
        except ImportError:
            HAS_SKLEARN = False
    return HAS_SKLEARN

MANUF_CATEGORY_HINTS = {
    'lighting': 'Lighting', 'electric': 'Electrical', 'wiring': 'Electrical',
    'appliance': 'Appliances & Consumer Electronics', 'lumber': 'Building Materials & Hardscape',
    'cascade': 'Building Materials & Hardscape', 'nail': 'Fasteners',
    'abrasive': 'Abrasives', 'tool': 'Power Tools', 'machinery': 'Power Tools',
    'safety': 'Safety Products', 'hardware': 'Building Materials & Hardscape',
    'plumb': 'Building Materials & Hardscape', 'roof': 'Building Materials & Hardscape',
    'siding': 'Building Materials & Hardscape', 'deck': 'Building Materials & Hardscape',
    'window': 'Building Materials & Hardscape', 'door': 'Building Materials & Hardscape',
    'fastener': 'Fasteners', 'screw': 'Fasteners', 'bolt': 'Fasteners',
    'wire': 'Electrical', 'cable': 'Electrical', 'conduit': 'Electrical',
    'switch': 'Electrical', 'outlet': 'Electrical', 'breaker': 'Electrical',
    'fixture': 'Lighting', 'bulb': 'Lighting', 'lamp': 'Lighting',
    'fan': 'Lighting', 'recess': 'Lighting', 'led': 'Lighting',
    'pipe': 'Building Materials & Hardscape', 'valve': 'Building Materials & Hardscape',
    'faucet': 'Building Materials & Hardscape', 'fitting': 'Building Materials & Hardscape',
    'drywall': 'Building Materials & Hardscape', 'insulation': 'Building Materials & Hardscape',
    'shingle': 'Building Materials & Hardscape', 'decking': 'Building Materials & Hardscape',
    'railing': 'Building Materials & Hardscape', 'fence': 'Building Materials & Hardscape',
    'satco': 'Lighting', 'nuvo': 'Lighting', 'kichler': 'Lighting', 'sylvania': 'Lighting',
    'cree': 'Lighting', 'feit': 'Lighting', 'hubble': 'Electrical',
    'leviton': 'Electrical', 'lutron': 'Electrical', 'square d': 'Electrical',
    'siemens': 'Electrical', 'square': 'Electrical',
    'first alert': 'Safety Products', 'kidde': 'Safety Products',
    'streamlight': 'Lighting', 'police security': 'Lighting',
    'milwaukee': 'Power Tools', 'makita': 'Power Tools', 'dewalt': 'Power Tools',
    'freud': 'Power Tools', 'cmt': 'Power Tools', 'senco': 'Power Tools',
    'woodpeckers': 'Hand Tools', 'sabre': 'Electrical',
    'prebena': 'Fasteners', 'miller': 'Electrical',
    'saw stop': 'Power Tools', 'mafell': 'Power Tools',
}

SUBCATEGORY_HINTS = {
    'wall': 'Wall Lights', 'ceiling': 'Ceiling Lights', 'recessed': 'Recessed Lighting',
    'track': 'Track Lighting', 'flood': 'Flood Lights', 'path': 'Path Lights',
    'spot': 'Spot Lights', 'area': 'Area Lights', 'step': 'Step Lights',
    'under cabinet': 'Under Cabinet Lights', 'night': 'Night Lights',
    'wall pack': 'Wall Packs', 'outdoor': 'Outdoor Lights',
    'switch': 'Switches', 'outlet': 'Outlets', 'breaker': 'Breakers',
    'conduit': 'Conduit', 'wire': 'Wire', 'cable': 'Cable',
    'cover': 'Cover Plates', 'box': 'Boxes', 'plate': 'Cover Plates',
    'screw': 'Screws', 'nail': 'Nails', 'bolt': 'Bolts',
    'anchor': 'Anchors', 'hinge': 'Hinges', 'clip': 'Clips',
    'glove': 'Gloves', 'glass': 'Eyewear', 'goggles': 'Eyewear',
    'helmet': 'Head Protection', 'mask': 'Respiratory Protection',
    'disc': 'Discs', 'belt': 'Belts', 'wheel': 'Wheels',
    'pad': 'Pads', 'brush': 'Brushes', 'sandpaper': 'Paper',
    'drill': 'Drills', 'saw': 'Saws', 'grinder': 'Grinders',
    'sander': 'Sanders', 'router': 'Routers', 'nailer': 'Nailers',
    'impact': 'Impact Drivers', 'jigsaw': 'Jigsaws', 'trimmer': 'Trimmers',
    'blower': 'Blowers', 'vacuum': 'Vacuums',
    'wrench': 'Wrenches', 'socket': 'Sockets', 'plier': 'Pliers',
    'screwdriver': 'Screwdrivers', 'hammer': 'Hammers', 'level': 'Levels',
    'clamp': 'Clamps', 'chisel': 'Chisels', 'snip': 'Snips',
    'dishwasher': 'Built-In Dishwashers', 'refrigerator': 'Refrigerators',
    'freezer': 'Freezers', 'microwave': 'Microwaves', 'oven': 'Wall Ovens',
    'range': 'Range Hoods', 'washer': 'Washers', 'dryer': 'Dryers',
    'disposer': 'Garbage Disposals',
    'deck board': 'Deck Boards', 'post': 'Posts', 'railing': 'Railings',
    'siding': 'Siding', 'shingle': 'Shingles', 'window': 'Windows',
    'door': 'Doors', 'glass': 'Glass', 'lumber': 'Lumber',
    'plywood': 'Plywood', 'subfloor': 'Subfloor',
    'pipe': 'Pipes', 'fitting': 'Fittings', 'valve': 'Valves', 'faucet': 'Faucets',
}

BASE_CATEGORIES = {
    'drill': 'Power Tools>Drills', 'driver': 'Power Tools>Drivers',
    'saw': 'Power Tools>Saws', 'grinder': 'Power Tools>Grinders',
    'sander': 'Power Tools>Sanders', 'router': 'Power Tools>Routers',
    'jigsaw': 'Power Tools>Jigsaws', 'impact': 'Power Tools>Impact Drivers',
    'hammer drill': 'Power Tools>Hammer Drills', 'trimmer': 'Power Tools>Trimmers',
    'blower': 'Power Tools>Blowers', 'nailer': 'Power Tools>Nailers',
    'stapler': 'Power Tools>Staplers', 'circular': 'Power Tools>Circular Saws',
    'miter': 'Power Tools>Miter Saws',
    'wrench': 'Hand Tools>Wrenches', 'socket': 'Hand Tools>Sockets',
    'plier': 'Hand Tools>Pliers', 'screwdriver': 'Hand Tools>Screwdrivers',
    'hammer': 'Hand Tools>Hammers', 'level': 'Hand Tools>Levels',
    'clamp': 'Hand Tools>Clamps', 'chisel': 'Hand Tools>Chisels',
    'snip': 'Hand Tools>Snips',
    'disc': 'Abrasives>Discs', 'film disc': 'Abrasives>Discs',
    'sanding belt': 'Abrasives>Belts', 'belt': 'Abrasives>Belts',
    'grinding': 'Abrasives>Wheels', 'wheel': 'Abrasives>Wheels',
    'sandpaper': 'Abrasives>Paper',
    'outlet': 'Electrical>Outlets', 'switch': 'Electrical>Switches',
    'wire': 'Electrical>Wire', 'cable': 'Electrical>Cable',
    'breaker': 'Electrical>Breakers', 'conduit': 'Electrical>Conduit',
    'box': 'Electrical>Boxes', 'cover': 'Electrical>Cover Plates',
    'bulb': 'Lighting>Bulbs', 'fixture': 'Lighting>Fixtures',
    'lamp': 'Lighting>Lamps', 'led': 'Lighting>LED',
    'recessed': 'Lighting>Recessed Lighting', 'ceiling fan': 'Lighting>Ceiling Fans',
    'under cabinet': 'Lighting>Under Cabinet Lights',
    'path light': 'Lighting>Path Lights', 'spot light': 'Lighting>Spot Lights',
    'flood light': 'Lighting>Flood Lights', 'wall pack': 'Lighting>Wall Packs',
    'area light': 'Lighting>Area Lights', 'step light': 'Lighting>Step Lights',
    'wall': 'Lighting>Wall Lights', 'ceiling': 'Lighting>Ceiling Lights',
    'dishwasher': 'Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers',
    'refrigerator': 'Appliances & Consumer Electronics>Kitchen Appliances>Refrigerators',
    'freezer': 'Appliances & Consumer Electronics>Kitchen Appliances>Freezers',
    'microwave': 'Appliances & Consumer Electronics>Kitchen Appliances>Microwaves',
    'oven': 'Appliances & Consumer Electronics>Kitchen Appliances>Wall Ovens',
    'range hood': 'Appliances & Consumer Electronics>Kitchen Appliances>Range Hoods',
    'washer': 'Appliances & Consumer Electronics>Laundry>Washers',
    'dryer': 'Appliances & Consumer Electronics>Laundry>Dryers',
    'disposer': 'Appliances & Consumer Electronics>Kitchen Appliances>Garbage Disposals',
    'window': 'Building Materials & Hardscape>Windows & Doors>Windows',
    'door': 'Building Materials & Hardscape>Windows & Doors>Doors',
    'patio door': 'Building Materials & Hardscape>Windows & Doors>Doors',
    'skylight': 'Building Materials & Hardscape>Windows & Doors>Skylights',
    'glass': 'Building Materials & Hardscape>Windows & Doors>Glass',
    'lumber': 'Building Materials & Hardscape>Lumber & Sheathing>Lumber',
    'subfloor': 'Building Materials & Hardscape>Lumber & Sheathing>Subfloor',
    'plywood': 'Building Materials & Hardscape>Lumber & Sheathing>Plywood',
    'drywall': 'Building Materials & Hardscape>Drywall & Insulation>Drywall',
    'insulation': 'Building Materials & Hardscape>Drywall & Insulation>Insulation',
    'shingle': 'Building Materials & Hardscape>Roofing>Shingles',
    'metal roofing': 'Building Materials & Hardscape>Roofing>Metal Roofing',
    'siding': 'Building Materials & Hardscape>Siding>Siding',
    'deck': 'Building Materials & Hardscape>Decking>Deck Boards',
    'deck board': 'Building Materials & Hardscape>Decking>Deck Boards',
    'post': 'Building Materials & Hardscape>Decking>Posts',
    'railing': 'Building Materials & Hardscape>Decking>Railings',
    'fence': 'Building Materials & Hardscape>Fencing>Fencing',
    'pipe': 'Building Materials & Hardscape>Plumbing>Pipes',
    'fitting': 'Building Materials & Hardscape>Plumbing>Fittings',
    'valve': 'Building Materials & Hardscape>Plumbing>Valves',
    'faucet': 'Building Materials & Hardscape>Plumbing>Faucets',
    'glove': 'Safety Products>Gloves', 'glasses': 'Safety Products>Eyewear',
    'helmet': 'Safety Products>Head Protection',
    'mask': 'Safety Products>Respiratory Protection',
    'screw': 'Fasteners>Screws', 'nail': 'Fasteners>Nails',
    'bolt': 'Fasteners>Bolts', 'anchor': 'Fasteners>Anchors',
    'hinge': 'Fasteners>Hinges', 'rivet': 'Fasteners>Rivets',
    'rainscreen': 'Building Materials & Hardscape>Siding>Rainscreen',
    'composite': 'Building Materials & Hardscape>Decking>Deck Boards',
    'hanger': 'Electrical>Hangers',
    'downlight': 'Lighting>Recessed Lighting', 'down light': 'Lighting>Recessed Lighting',
    'highbay': 'Lighting>Fixtures', 'high bay': 'Lighting>Fixtures',
    'halogen': 'Lighting>Bulbs', 'pin': 'Lighting>Bulbs',
    't4': 'Lighting>Bulbs',
    'load center': 'Electrical>Load Centers', 'load cntr': 'Electrical>Load Centers',
    'cover plate': 'Electrical>Cover Plates', 'cover sw': 'Electrical>Cover Plates',
    'decor plate': 'Electrical>Cover Plates', 'decora': 'Electrical>Switches',
    'dimmer': 'Electrical>Switches>Dimmers', 'lutron': 'Electrical>Switches>Dimmers',
    'flashlight': 'Lighting>Flashlights', 'flash lt': 'Lighting>Flashlights',
    'flash light': 'Lighting>Flashlights', 'headlight': 'Lighting>Headlamps',
    'hearing protector': 'Safety Products>Hearing Protection',
    'fire extinguisher': 'Safety Products>Fire Extinguishers',
    'smoke': 'Safety Products>Smoke Detectors', 'co alarm': 'Safety Products>Smoke Detectors',
    'alarm': 'Safety Products>Smoke Detectors',
    'heated hoodie': 'Safety Products>Heated Apparel', 'heated gear': 'Safety Products>Heated Apparel',
    'mason line': 'Hand Tools>Measuring>Line', 'rafter square': 'Hand Tools>Measuring>Squares',
    'plug cutter': 'Power Tools>Drill Bits', 'drive bit': 'Power Tools>Drill Bits',
    'driver bit': 'Power Tools>Drill Bits', 'phillips': 'Power Tools>Drill Bits',
    'torx': 'Power Tools>Drill Bits', 'hole saw': 'Power Tools>Drill Bits>Hole Saws',
    'hole dozer': 'Power Tools>Drill Bits>Hole Saws',
    'tile blade': 'Power Tools>Saws>Blades', 'framing blade': 'Power Tools>Saws>Blades',
    'diamond': 'Power Tools>Saws>Blades',
    'battery': 'Power Tools>Batteries & Chargers', 'charger': 'Power Tools>Batteries & Chargers',
    'starter kit': 'Power Tools>Batteries & Chargers', 'rapid charger': 'Power Tools>Batteries & Chargers',
    'ratchet': 'Hand Tools>Wrenches>Ratchets', 'wrench': 'Hand Tools>Wrenches',
    'universal joint': 'Hand Tools>Wrenches', 'drive': 'Hand Tools>Screwdrivers',
    'mechanical pencil': 'Hand Tools>Measuring>Pencils', 'pencil': 'Hand Tools>Measuring>Pencils',
    'voltage detector': 'Hand Tools>Test Equipment', 'insulated': 'Hand Tools>Wrenches',
    'shears': 'Power Tools>Shears', 'pruning': 'Power Tools>Shears',
    'blower': 'Power Tools>Blowers', 'vacuum': 'Power Tools>Vacuums',
    'table assembly': 'Power Tools>Table Saws', 'table saw': 'Power Tools>Table Saws',
    'speaker': 'Appliances & Consumer Electronics>Electronics>Speakers',
    'bluetooth': 'Appliances & Consumer Electronics>Electronics>Speakers',
    'organizer': 'Hand Tools>Storage', 'deep compact': 'Hand Tools>Storage',
    'insulated r-sheathing': 'Building Materials & Hardscape>Lumber & Sheathing>Sheathing',
    'r-sheathing': 'Building Materials & Hardscape>Lumber & Sheathing>Sheathing',
    'zip system': 'Building Materials & Hardscape>Lumber & Sheathing>Sheathing',
    'heater kit': 'Appliances & Consumer Electronics>Heating & Cooling>Heaters',
    'motor oil': 'Automotive>Fluids & Chemicals',
    'vinyl wrap': 'Building Materials & Hardscape>General',
    'fine fissured': 'Building Materials & Hardscape>General',
    'planing machine': 'Power Tools>Planers',
    'planer': 'Power Tools>Planers',
    'drywall compound': 'Building Materials & Hardscape>Drywall & Insulation>Drywall',
    'joint compound': 'Building Materials & Hardscape>Drywall & Insulation>Drywall',
    'vinyl wrapped': 'Electrical>Wire',
    'inside cas': 'Electrical>Wire',
    'duration': 'Building Materials & Hardscape>Drywall & Insulation>Drywall',
    'truedef': 'Building Materials & Hardscape>Drywall & Insulation>Drywall',
    'wburg': 'Building Materials & Hardscape>Drywall & Insulation>Drywall',
    'carpentry': 'Power Tools>Planers',
}


class ClassifierLearner:

    def __init__(self):
        self.base_categories = BASE_CATEGORIES
        self._vectorizer = None
        self._ml_model = None
        self._trained = False
        self._label_map = {}
        self._reverse_label_map = {}

    def _keyword_classify(self, desc):
        desc_lower = desc.lower()
        best_cat = None
        best_score = 0
        for keyword, category in self.base_categories.items():
            if keyword in desc_lower:
                score = len(keyword) / max(len(desc_lower), 1) + 0.3
                if score > best_score:
                    best_score = score
                    best_cat = category
        return best_cat, min(best_score, 0.95)

    def _get_manufacturer_category_hint(self, part_manuf):
        if not part_manuf:
            return ''
        manuf_lower = part_manuf.lower()
        for keyword, category in MANUF_CATEGORY_HINTS.items():
            if keyword in manuf_lower:
                return category
        return ''

    def _get_subcategory_hint(self, part_desc, broad_category):
        if not part_desc:
            return broad_category
        desc_lower = part_desc.lower()
        for keyword, subcat in SUBCATEGORY_HINTS.items():
            if keyword in desc_lower:
                full = f"{broad_category}>{subcat}" if ">" not in subcat else subcat
                return full
        return broad_category

    def learn_from_data(self, input_data):
        logger.info("Learning classification patterns...")
        descriptions = []
        labels = []

        for row in input_data:
            desc = str(row.get('Part_Desc', ''))
            cat, conf = self._keyword_classify(desc)
            descriptions.append(desc)
            if cat and conf >= 0.4:
                labels.append(cat)
            else:
                labels.append(None)

        labeled_descs = [d for d, l in zip(descriptions, labels) if l]
        labeled_labels = [l for l in labels if l]

        logger.info(f"Auto-labeled {len(labeled_labels)}/{len(input_data)} rows")

        if not _ensure_sklearn() or len(set(labeled_labels)) < 3:
            logger.info("Using keyword-only classification")
            return

        unique_labels = sorted(set(labeled_labels))
        label_counts = Counter(labeled_labels)
        min_count = min(label_counts.values())
        if min_count < 2:
            filtered = [(d, l) for d, l in zip(labeled_descs, labeled_labels) if label_counts[l] >= 2]
            if len(set(l for _, l in filtered)) < 2:
                logger.info("Too few samples per class for ML")
                return
            labeled_descs = [d for d, _ in filtered]
            labeled_labels = [l for _, l in filtered]
            unique_labels = sorted(set(labeled_labels))

        self._label_map = {i: l for i, l in enumerate(unique_labels)}
        self._reverse_label_map = {l: i for i, l in self._label_map.items()}

        y = [self._reverse_label_map[l] for l in labeled_labels]

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.calibration import CalibratedClassifierCV

        self._vectorizer = TfidfVectorizer(
            analyzer='char_wb', ngram_range=(2, 4),
            max_features=5000, sublinear_tf=True,
        )
        X = self._vectorizer.fit_transform(labeled_descs)

        min_class_count = min(Counter(y).values())
        n_folds = min(3, min_class_count)

        base_clf = MultinomialNB(alpha=0.1)
        self._ml_model = CalibratedClassifierCV(base_clf, cv=n_folds, method='sigmoid')
        self._ml_model.fit(X, y)
        self._trained = True

        logger.info(f"Trained TF-IDF on {len(y)} samples, {len(unique_labels)} classes, {n_folds}-fold CV")

    def classify_product(self, part_desc, part_manuf=''):
        keyword_cat, keyword_conf = self._keyword_classify(part_desc)

        if self._trained and self._ml_model and self._vectorizer:
            try:
                X = self._vectorizer.transform([part_desc])
                proba = self._ml_model.predict_proba(X)[0]
                max_idx = proba.argmax()
                ml_conf = proba[max_idx]
                ml_cat = self._label_map.get(max_idx, None)

                if ml_conf > 0.65:
                    if keyword_cat and keyword_cat == ml_cat:
                        return ml_cat, min(ml_conf + 0.1, 0.99)
                    elif keyword_conf > 0.7:
                        return keyword_cat, keyword_conf
                    else:
                        return ml_cat, ml_conf
            except Exception:
                pass

        if keyword_cat:
            return keyword_cat, keyword_conf

        if part_manuf:
            hint = self._get_manufacturer_category_hint(part_manuf)
            if hint:
                subcat = self._get_subcategory_hint(part_desc, hint)
                return subcat, 0.40

        return 'General', 0.0

    def classify_with_ml(self, part_desc):
        if not self._trained:
            return None, 0.0
        try:
            X = self._vectorizer.transform([part_desc])
            proba = self._ml_model.predict_proba(X)[0]
            max_idx = proba.argmax()
            return self._label_map.get(max_idx), proba[max_idx]
        except Exception:
            return None, 0.0

    def get_stats(self):
        return {'trained': self._trained, 'classes': len(self._label_map)}
