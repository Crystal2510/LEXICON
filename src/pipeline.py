from __future__ import annotations
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

pd = None
ThreadPoolExecutor = None
as_completed = None

def _ensure_deps():
    global pd, ThreadPoolExecutor, as_completed
    if pd is None:
        import pandas as _pd
        pd = _pd
    if ThreadPoolExecutor is None:
        from concurrent.futures import ThreadPoolExecutor as _TE, as_completed as _ac
        ThreadPoolExecutor = _TE
        as_completed = _ac

# Lazy module-level imports
_DataLoader = None
_BrandNormalizer = None
_BrandLearner = None
_ClassifierLearner = None
_DescriptionParser = None
_DescriptionGenerator = None
_WebEnricher = None
_extract_grammar = None
_engine_mobile = None
_engine_invoice = None
_smart_truncate = None

def _ensure_modules():
    global _DataLoader, _BrandNormalizer, _BrandLearner, _ClassifierLearner
    global _DescriptionParser, _DescriptionGenerator, _WebEnricher
    global _extract_grammar, _engine_mobile, _engine_invoice, _smart_truncate
    if _DataLoader is None:
        from src.data_loader import DataLoader as _DL
        from src.brand_normalizer import BrandNormalizer as _BN
        from src.brand_learner import BrandLearner as _BL
        from src.classifier_learner import ClassifierLearner as _CL
        from src.description_parser import DescriptionParser as _DP
        from src.desc_generator import DescriptionGenerator as _DG
        from src.web_sourcing import WebEnricher as _WE
        from src.attribute_grammars import extract_grammar_attributes as _eg
        from src.desc_engine import generate_mobile_desc as _em, generate_invoice_desc as _ei, _smart_truncate as _st
        _DataLoader = _DL
        _BrandNormalizer = _BN
        _BrandLearner = _BL
        _ClassifierLearner = _CL
        _DescriptionParser = _DP
        _DescriptionGenerator = _DG
        _WebEnricher = _WE
        _extract_grammar = _eg
        _engine_mobile = _em
        _engine_invoice = _ei
        _smart_truncate = _st


CLASSPATH_TO_UNSPSC = {
    "Abrasives>Belts>Sanding Belts": "31191501",
    "Abrasives>Belts": "31191501",
    "Abrasives>Discs>Film Discs": "31191502",
    "Abrasives>Discs>Sanding Discs": "31191502",
    "Abrasives>Discs>Cut Off Discs": "31191503",
    "Abrasives>Discs>Cutting Discs": "31191503",
    "Abrasives>Discs>Grinding Discs": "31191504",
    "Abrasives>Discs>Flap Discs": "31191505",
    "Abrasives>Discs>Hook and Loop Discs": "31191506",
    "Abrasives>Wheels>Grinding Wheels": "31191601",
    "Abrasives>Wheels>Cut Off Wheels": "31191602",
    "Abrasives>Wheels>Flap Wheels": "31191603",
    "Abrasives>Wheels>Wire Wheels": "31191604",
    "Abrasives>Pads>Sanding Pads": "31191701",
    "Abrasives>Pads>Polishing Pads": "31191702",
    "Abrasives>Pads>Buffing Pads": "31191703",
    "Abrasives>Sponges>Sanding Sponges": "31191801",
    "Abrasives>Brushes>Wire Brushes": "31191901",
    "Abrasives>General": "31190000",
    "Power Tools>Drills": "27111901",
    "Power Tools>Drivers>Impact Drivers": "27111902",
    "Power Tools>Saws>Circular Saws": "27111501",
    "Power Tools>Saws>Miter Saws": "27111502",
    "Power Tools>Saws>Table Saws": "27111503",
    "Power Tools>Saws>Band Saws": "27111504",
    "Power Tools>Saws>Reciprocating Saws": "27111505",
    "Power Tools>Saws>Jigsaws": "27111506",
    "Power Tools>Sanders": "27111700",
    "Power Tools>Grinders": "27111800",
    "Power Tools>Routers": "27112000",
    "Power Tools>Nailers": "27112100",
    "Power Tools>Chainsaws": "27112200",
    "Power Tools>Blowers": "27112300",
    "Hand Tools>Wrenches": "27111500",
    "Hand Tools>Sockets": "27111600",
    "Hand Tools>Pliers": "27111300",
    "Hand Tools>Screwdrivers": "27111400",
    "Hand Tools>Hammers": "27111200",
    "Hand Tools>Measuring>Tape Measures": "27112501",
    "Hand Tools>Measuring>Levels": "27112502",
    "Hand Tools>Clamps": "27112600",
    "Hand Tools>Files": "27112700",
    "Safety>Eye Protection>Glasses": "46181501",
    "Safety>Eye Protection>Goggles": "46181502",
    "Safety>Hand Protection>Gloves": "46181600",
    "Safety>Head Protection>Hard Hats": "46181700",
    "Safety>Hearing Protection>Ear Plugs": "46181801",
    "Safety>Hearing Protection>Ear Muffs": "46181802",
    "Safety>Respiratory>Respirators": "46181901",
    "Safety>Respiratory>Dust Masks": "46181902",
    "Electrical>Wire": "26121600",
    "Electrical>Wire>Cable": "26121601",
    "Electrical>Wire>Tape": "26121602",
    "Electrical>Outlets": "39121401",
    "Electrical>Outlets>GFCI": "39121400",
    "Electrical>Switches": "39121500",
    "Electrical>Switches>Dimmers": "39121501",
    "Electrical>Breakers": "39121600",
    "Electrical>Conduit": "26121700",
    "Electrical>Cover Plates": "39121800",
    "Lighting>LED": "39112100",
    "Lighting>Bulbs": "39112101",
    "Lighting>Fixtures": "39111600",
    "Lighting>Ceiling Fans": "39111700",
    "Building Materials & Hardscape>Decking>Deck Boards": "30161700",
    "Building Materials & Hardscape>Decking>Railing": "30161800",
    "Building Materials & Hardscape>Lumber & Sheathing>Lumber": "30111500",
    "Building Materials & Hardscape>Lumber & Sheathing>Plywood": "30111600",
    "Building Materials & Hardscape>Lumber & Sheathing>OSB": "30111700",
    "Building Materials & Hardscape>Lumber & Sheathing>Sheathing": "30111800",
    "Building Materials & Hardscape>Lumber & Sheathing>Subfloor": "30111900",
    "Building Materials & Hardscape>Windows & Doors>Windows": "30151500",
    "Building Materials & Hardscape>Windows & Doors>Doors": "30151600",
    "Building Materials & Hardscape>Windows & Doors>Skylights": "30151700",
    "Building Materials & Hardscape>Plumbing>Faucets": "40141604",
    "Building Materials & Hardscape>Plumbing>Toilets": "40141601",
    "Building Materials & Hardscape>Plumbing>Sinks": "40141602",
    "Building Materials & Hardscape>Plumbing>Valves": "40141701",
    "Building Materials & Hardscape>Plumbing>Pipes": "40141702",
    "Building Materials & Hardscape>Plumbing>Fittings": "40141700",
    "Building Materials & Hardscape>Roofing>Metal Panels": "30151800",
    "Building Materials & Hardscape>Roofing>Shingles": "30151900",
    "Building Materials & Hardscape>Building Envelope>Rainscreen": "30152000",
    "Building Materials & Hardscape>Caulks & Sealants>Caulks": "30131500",
    "Building Materials & Hardscape>Caulks & Sealants>Sealants": "30131600",
    "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers": "52141501",
    "Appliances & Consumer Electronics>Kitchen Appliances>Refrigerators": "52141502",
    "Appliances & Consumer Electronics>Kitchen Appliances>Microwaves": "52141503",
    "Appliances & Consumer Electronics>Kitchen Appliances>Ranges": "52141504",
    "Appliances & Consumer Electronics>Laundry>Washers": "52141601",
    "Appliances & Consumer Electronics>Laundry>Dryers": "52141602",
    "Fasteners>Screws": "31161700",
    "Fasteners>Nails": "31161600",
    "Fasteners>Bolts": "31161500",
    "Fasteners>Nuts": "31161400",
    "Fasteners>Washers": "31161300",
    "Fasteners>Anchors": "31161200",
    "Power Tools>Drill Bits": "27111903",
    "Power Tools>Drill Bits>Hole Saws": "27111904",
    "Power Tools>Saws>Blades": "27111507",
    "Power Tools>Batteries & Chargers": "27111905",
    "Power Tools>Shears": "27112500",
    "Power Tools>Vacuums": "27112600",
    "Power Tools>Planers": "27112400",
    "Power Tools>Trimmers": "27112700",
    "Power Tools>Outdoor>String Trimmers": "27112701",
    "Power Tools>Outdoor>Lawn Mowers": "27112702",
    "Power Tools>Outdoor>Leaf Blowers": "27112703",
    "Power Tools>Outdoor>Hedge Trimmers": "27112704",
    "Power Tools>Table Saws": "27111503",
    "Lighting>Flashlights": "39112102",
    "Lighting>Headlamps": "39112103",
    "Lighting>Fixtures>Pendant Lights": "39111601",
    "Lighting>Fixtures>Chandeliers": "39111602",
    "Lighting>Fixtures>Wall Sconces": "39111603",
    "Lighting>Fixtures>Recessed Lights": "39111604",
    "Lighting>Fixtures>Track Lights": "39111605",
    "Lighting>Fixtures>Flood Lights": "39111606",
    "Lighting>Fixtures>Spot Lights": "39111607",
    "Lighting>Fixtures>Area Lights": "39111608",
    "Lighting>Fixtures>Wall Packs": "39111609",
    "Lighting>Fixtures>Under Cabinet Lights": "39111610",
    "Lighting>Fixtures>Night Lights": "39111611",
    "Lighting>Fixtures>Emergency Lights": "39111612",
    "Lighting>Fixtures>Exit Signs": "39111613",
    "Lighting>Fixtures>Step Lights": "39111614",
    "Lighting>Fixtures>Landscape Lights": "39111615",
    "Lighting>Fixtures>Puck Lights": "39111616",
    "Lighting>Wall Lights": "39111600",
    "Lighting>Ceiling Lights": "39111600",
    "Lighting>Lamps": "39111600",
    "Lighting>Bulbs>BR40": "39112101",
    "Lighting>Bulbs>BR30": "39112101",
    "Lighting>Bulbs>PAR38": "39112101",
    "Lighting>Bulbs>PAR30": "39112101",
    "Lighting>Bulbs>PAR20": "39112101",
    "Lighting>Bulbs>MR16": "39112101",
    "Lighting>Bulbs>GU10": "39112101",
    "Lighting>LED>Strips": "39112104",
    "Building Materials & Hardscape>Decking>Fascia": "30161700",
    "Building Materials & Hardscape>Decking>Railing>Railing Kits": "30161801",
    "Building Materials & Hardscape>Decking>Railing>Post Sleeves": "30161802",
    "Building Materials & Hardscape>Decking>Railing>Post Caps": "30161803",
    "Building Materials & Hardscape>Decking>Railing>Balusters": "30161804",
    "Building Materials & Hardscape>Decking>Railing>Gates": "30161805",
    "Building Materials & Hardscape>Decking>Fasteners": "30161900",
    "Building Materials & Hardscape>Decking>Fasteners>Deck Screws": "30161901",
    "Building Materials & Hardscape>Decking>Structural>Joists": "30162000",
    "Building Materials & Hardscape>Decking>Structural>Joist Tape": "30162001",
    "Building Materials & Hardscape>Decking>Structural>Ledger Boards": "30162002",
    "Building Materials & Hardscape>Decking>Deck Boards>Composite": "30161701",
    "Building Materials & Hardscape>Fencing>Fencing": "30162100",
    "Building Materials & Hardscape>Windows & Doors>Hardware>Hinges": "30151601",
    "Building Materials & Hardscape>Windows & Doors>Hardware>Knobs": "30151602",
    "Building Materials & Hardscape>Windows & Doors>Hardware>Deadbolts": "30151603",
    "Building Materials & Hardscape>Windows & Doors>Hardware>Locksets": "30151604",
    "Building Materials & Hardscape>Windows & Doors>Hardware>Handles": "30151605",
    "Building Materials & Hardscape>Windows & Doors>Accessories>Weatherstripping": "30151606",
    "Building Materials & Hardscape>Windows & Doors>Accessories>Thresholds": "30151607",
    "Building Materials & Hardscape>Windows & Doors>Doors>Sliding": "30151608",
    "Building Materials & Hardscape>Windows & Doors>Doors>French": "30151609",
    "Building Materials & Hardscape>Windows & Doors>Doors>Entry": "30151610",
    "Building Materials & Hardscape>Windows & Doors>Doors>Garage": "30151611",
    "Building Materials & Hardscape>Windows & Doors>Doors>Patio": "30151612",
    "Building Materials & Hardscape>Windows & Doors>Windows>Basement": "30151501",
    "Building Materials & Hardscape>Windows & Doors>Windows>Hopper": "30151502",
    "Building Materials & Hardscape>Windows & Doors>Windows>Sliding": "30151503",
    "Building Materials & Hardscape>Plumbing>Toilet Parts>Flush Handles": "40141605",
    "Building Materials & Hardscape>Plumbing>Toilet Parts>Wax Rings": "40141606",
    "Building Materials & Hardscape>Plumbing>Toilet Parts>Seats": "40141607",
    "Building Materials & Hardscape>Plumbing>Drains": "40141800",
    "Building Materials & Hardscape>Plumbing>Drains>Pop-Up": "40141801",
    "Building Materials & Hardscape>Plumbing>Drains>Overflow": "40141802",
    "Building Materials & Hardscape>Plumbing>Supply Lines": "40141900",
    "Building Materials & Hardscape>Plumbing>Traps": "40142000",
    "Building Materials & Hardscape>Plumbing>Valves>Ball": "40141703",
    "Building Materials & Hardscape>Plumbing>Valves>Check": "40141704",
    "Building Materials & Hardscape>Plumbing>Valves>Stop": "40141705",
    "Building Materials & Hardscape>Plumbing>Valves>Angle Stops": "40141706",
    "Building Materials & Hardscape>Plumbing>Valves>Flush": "40141707",
    "Building Materials & Hardscape>Plumbing>Valves>Fill": "40141708",
    "Building Materials & Hardscape>Plumbing>Fittings>Elbows": "40141709",
    "Building Materials & Hardscape>Plumbing>Fittings>Tees": "40141710",
    "Building Materials & Hardscape>Plumbing>Fittings>Couplings": "40141711",
    "Building Materials & Hardscape>Plumbing>Fittings>Connectors": "40141712",
    "Building Materials & Hardscape>Plumbing>Fittings>Adapters": "40141713",
    "Building Materials & Hardscape>Plumbing>Fittings>Flexible Connectors": "40141714",
    "Building Materials & Hardscape>Lumber & Sheathing>Furring Strips": "30112000",
    "Building Materials & Hardscape>Lumber & Sheathing>Studs": "30112100",
    "Building Materials & Hardscape>Lumber & Sheathing>Beams": "30112200",
    "Building Materials & Hardscape>Lumber & Sheathing>Posts": "30112300",
    "Building Materials & Hardscape>Trim & Moulding>Moulding": "30121500",
    "Building Materials & Hardscape>Trim & Moulding>Trim": "30121501",
    "Building Materials & Hardscape>Trim & Moulding>Baseboards": "30121502",
    "Building Materials & Hardscape>Trim & Moulding>Crown Moulding": "30121503",
    "Building Materials & Hardscape>Trim & Moulding>Casing": "30121504",
    "Building Materials & Hardscape>Adhesives": "30131700",
    "Building Materials & Hardscape>Foam": "30131800",
    "Building Materials & Hardscape>Roofing>Shingles": "30151900",
    "Building Materials & Hardscape>Roofing>Metal Panels": "30151800",
    "Building Materials & Hardscape>Roofing>Ice & Water": "30152100",
    "Building Materials & Hardscape>Concrete & Masonry>Concrete": "30140000",
    "Building Materials & Hardscape>Concrete & Masonry>Mortar": "30140100",
    "Building Materials & Hardscape>Concrete & Masonry>Grout": "30140200",
    "Building Materials & Hardscape>Concrete & Masonry>Cement": "30140300",
    "Building Materials & Hardscape>General": "30000000",
    "Appliances & Consumer Electronics>Heating & Cooling>Water Heaters": "52141700",
    "Appliances & Consumer Electronics>Heating & Cooling>Heaters": "52141701",
    "Appliances & Consumer Electronics>Kitchen Appliances>Garbage Disposals": "52141505",
    "Appliances & Consumer Electronics>Kitchen Appliances>Range Hoods": "52141506",
    "Appliances & Consumer Electronics>Kitchen Appliances>Cooktops": "52141507",
    "Appliances & Consumer Electronics>Kitchen Appliances>Wall Ovens": "52141508",
    "Appliances & Consumer Electronics>Kitchen Appliances>Compact Refrigerators": "52141509",
    "Appliances & Consumer Electronics>Kitchen Appliances>Ice Makers": "52141510",
    "Appliances & Consumer Electronics>Kitchen Appliances>Wine Coolers": "52141511",
    "Appliances & Consumer Electronics>Kitchen Appliances>Freezers": "52141512",
    "Appliances & Consumer Electronics>Laundry>Laundry Centers": "52141603",
    "Appliances & Consumer Electronics>Electronics>Speakers": "52142000",
    "Hand Tools>Measuring>Tape Measures": "27112501",
    "Hand Tools>Measuring>Levels": "27112502",
    "Hand Tools>Measuring>Squares": "27112503",
    "Hand Tools>Measuring>Pencils": "27112504",
    "Hand Tools>Measuring>Line": "27112505",
    "Hand Tools>Wrenches>Ratchets": "27111501",
    "Hand Tools>Wrenches>Allen": "27111502",
    "Hand Tools>Wrenches>Hex Keys": "27111503",
    "Hand Tools>Screwdrivers>Torx": "27111401",
    "Hand Tools>Test Equipment>Multimeters": "27112800",
    "Hand Tools>Test Equipment>Stud Finders": "27112801",
    "Hand Tools>Test Equipment": "27112800",
    "Hand Tools>Storage": "27112900",
    "Hand Tools>Accessories>Holsters": "27113000",
    "Safety Products>Heated Apparel": "46182000",
    "Safety Products>Fire Extinguishers": "46182100",
    "Safety Products>Smoke Detectors": "46182200",
    "Safety Products>Hearing Protection": "46181800",
    "Safety Products>Eyewear": "46181500",
    "Safety Products>Hand Protection": "46181600",
    "Safety Products>Head Protection": "46181700",
    "Safety Products>Respiratory Protection": "46181900",
    "Safety Products>Body Protection": "46182000",
    "Safety Products>Body Protection>Heated Apparel": "46182001",
    "Safety Products>Body Protection>Phone Cases": "46182002",
    "Safety Products>Fall Protection": "46182300",
    "Electrical>Load Centers": "39121601",
    "Electrical>Power Supplies": "39121900",
    "Electrical>Hangers": "39122000",
    "Electrical>Boxes": "39122100",
    "Electrical>Wire>Conduit": "26121700",
    "Automotive>Tire>Accessories": "48100000",
    "Automotive>Fluids & Chemicals": "48110000",
    "Fans>Exhaust Fans": "39111800",
    "Fans>Exhaust Fans>Bathroom": "39111801",
    "Fans>Range Hood Fans": "39111802",
    "Fans>Inline Fans": "39111803",
    "Fans>Ventilation": "39111804",
    "Fans>Attic Fans": "39111805",
    "Fans>Whole House": "39111806",
    "Fans>Portable>Tower": "39111807",
    "Fans>Portable>Box": "39111808",
    "Fans>Portable>Pedestal": "39111809",
    "Fans>Portable>Desk": "39111810",
    "Fans>Industrial": "39111811",
    "Building Materials & Hardscape>Caulks & Sealants>Sealants": "30131600",
    "Building Materials & Hardscape>Building Envelope>Rainscreen": "30152000",
    "Appliances & Consumer Electronics>Kitchen Appliances>Dryers": "52141602",
    "Appliances & Consumer Electronics>Kitchen Appliances>Washers": "52141601",
    "Safety Products>Gloves": "46181600",
    "Safety Products>Gloves>Work Gloves": "46181601",
    "Safety Products>Gloves>Chemical Gloves": "46181602",
    "Safety Products>Gloves>Welding Gloves": "46181603",
    "Lighting>Recessed Lighting": "39111604",
    "Lighting>Recessed Lighting>LED": "39111604",
    "Power Tools>Impact Drivers": "27111902",
    "Power Tools>Saws>Recip Saws": "27111505",
    "Power Tools>Saws>Band Saws": "27111504",
    "Power Tools>Saws>Miter Saws": "27111502",
    "Power Tools>Saws>Table Saws": "27111503",
    "Power Tools>Saws>Circular Saws": "27111501",
    "Power Tools>Saws>Jigsaws": "27111506",
    "Power Tools>Saws": "27111500",
    "Power Tools>Drills>Hammer Drills": "27111901",
    "Power Tools>Drills>Drill Drivers": "27111901",
    "Power Tools>Drills": "27111901",
    "Safety>Body Protection>Heated Apparel": "46182001",
    "Safety>Body Protection": "46182000",
    "Lighting>Fixtures>Undercabinet": "39111610",
    "Lighting>Fixtures>Under Cabinet": "39111610",
    "Lighting>Fixtures>Pendant": "39111601",
    "Lighting>Fixtures>Recessed": "39111604",
    "Lighting>Fixtures>Track": "39111605",
    "Lighting>Fixtures>Flood": "39111606",
    "Lighting>Fixtures>Wall": "39111603",
    "Lighting>Fixtures>Flush Mount": "39111600",
    "Lighting>Fixtures>Chandeliers": "39111602",
    "Lighting>Fixtures>Pendants": "39111601",
    "Building Materials & Hardscape>Decking>Composite Decking": "30161701",
    "Building Materials & Hardscape>Decking>PVC Decking": "30161702",
    "Building Materials & Hardscape>Decking>Wood Decking": "30161703",
    "Building Materials & Hardscape>Decking": "30161700",
    "Building Materials & Hardscape>Lumber & Sheathing": "30111500",
    "Building Materials & Hardscape>Windows & Doors": "30151500",
    "Building Materials & Hardscape>Trim & Moulding": "30121500",
    "Building Materials & Hardscape>Roofing": "30151900",
    "Building Materials & Hardscape>Concrete & Masonry": "30140000",
    "Building Materials & Hardscape>Plumbing": "40141700",
    "Electrical>Wire>Electrical Wire": "26121600",
    "Electrical>Wire>Thermostat Wire": "26121603",
    "Electrical>Wire>Low Voltage Wire": "26121604",
    "Electrical>Wire>Speaker Wire": "26121605",
    "Electrical>Wire>Extension Cord": "26121606",
    "Electrical>Wire>Wire Nuts": "26121607",
    "Electrical>Outlets>Wall Plate": "39121401",
    "Electrical>Outlets>Receptacle": "39121402",
    "Electrical>Switches>Toggle Switch": "39121501",
    "Electrical>Switches>Dimmer Switch": "39121501",
    "Electrical>Switches>Wall Switch": "39121502",
    "Electrical>Conduit>EMT": "26121701",
    "Electrical>Conduit>PVC": "26121702",
    "Electrical>Conduit>Flex": "26121703",
    "Hand Tools>Wrenches>Open End": "27111504",
    "Hand Tools>Wrenches>Box End": "27111505",
    "Hand Tools>Wrenches>Adjustable": "27111506",
    "Hand Tools>Pliers>Slip Joint": "27111301",
    "Hand Tools>Pliers>Needle Nose": "27111302",
    "Hand Tools>Pliers>Locking": "27111303",
    "Hand Tools>Pliers>Linesman": "27111304",
    "Hand Tools>Screwdrivers>Phillips": "27111401",
    "Hand Tools>Screwdrivers>Flathead": "27111402",
    "Hand Tools>Screwdrivers>Multi Bit": "27111403",
    "Hand Tools>Hammers>Claw Hammer": "27111201",
    "Hand Tools>Hammers>Ball Peen": "27111202",
    "Hand Tools>Hammers>Framing Hammer": "27111203",
    "Hand Tools>Measuring>Tape": "27112501",
    "Hand Tools>Measuring>Level": "27112502",
    "Fasteners>Screws>Deck Screws": "31161701",
    "Fasteners>Screws>Wood Screws": "31161702",
    "Fasteners>Screws>Sheet Metal Screws": "31161703",
    "Fasteners>Screws>Machine Screws": "31161704",
    "Fasteners>Screws>Concrete Screws": "31161705",
    "Fasteners>Nails>Finish Nails": "31161601",
    "Fasteners>Nails>Framing Nails": "31161602",
    "Fasteners>Nails>Casing Nails": "31161603",
    "Fasteners>Nails>Roofing Nails": "31161604",
    "Fasteners>Anchors>Toggle Bolts": "31161201",
    "Fasteners>Anchors>Wedge Anchors": "31161202",
    "Fasteners>Anchors>Sleeve Anchors": "31161203",
    "Fasteners>Anchors>Plastic Anchors": "31161204",
    "Abrasives>Brushes>Wire Brushes": "31191901",
    "Abrasives>Brushes>Nylon Brushes": "31191902",
    "Abrasives>Brushes>Brass Brushes": "31191903",
    "Power Tools>Accessories": "27113000",
    "Power Tools>Accessories>Blades": "27111507",
    "Power Tools>Accessories>Bits": "27111903",
    "Power Tools>Accessories>Chucks": "27113001",
    "Power Tools>Accessories>Batteries": "27111905",
    "Power Tools>Accessories>Chargers": "27111906",
    "Power Tools>Accessories>Guard": "27113002",
    "Power Tools>Accessories>Fence": "27113003",
    "Power Tools>Accessories>Guide": "27113004",
    "Power Tools>Accessories>Stand": "27113005",
    "Appliances & Consumer Electronics>Kitchen Appliances>Dishwashers": "52141501",
    "Appliances & Consumer Electronics>Kitchen Appliances>Disposals": "52141505",
    "Appliances & Consumer Electronics>Kitchen Appliances>Hoods": "52141506",
    "Appliances & Consumer Electronics>Laundry>Dryer": "52141602",
    "Appliances & Consumer Electronics>Laundry>Washer": "52141601",
    "Electrical>Switches>Timers": "39121503",
    "Electrical>Panels": "39121601",
    "Electrical>Load Centers>Panel": "39121601",
    "Electrical>Load Centers>Breaker Panel": "39121601",
    "Power Tools>Wrenches>Impact Wrenches": "27111507",
    "Power Tools>Nailers>Brad": "27112101",
    "Power Tools>Nailers>Framing": "27112102",
    "Power Tools>Nailers>Finish": "27112103",
    "Power Tools>Nailers>Staple": "27112104",
    "Building Materials & Hardscape>Spot Lights": "39111607",
    "Building Materials & Hardscape>Spot Lights>Outdoor": "39111607",
    "Safety Products>Fall Protection>Harness": "46182301",
    "Safety Products>Fall Protection>Lanyard": "46182302",
    "Safety Products>Fall Protection>Anchor": "46182303",
    "Electrical>Boxes>Outlet Box": "39122101",
    "Electrical>Boxes>Switch Box": "39122102",
    "Electrical>Boxes>Junction Box": "39122103",
    "Electrical>Hangers>Conduit Strap": "39122001",
    "Electrical>Hangers>Cable Clamp": "39122002",
    "Lighting>Fixtures>Commercial": "39111600",
    "Lighting>Fixtures>Industrial": "39111600",
    "Lighting>Fixtures>Residential": "39111600",
    "Lighting>Fixtures>Outdoor": "39111600",
    "Lighting>Fixtures>Garage": "39111600",
    "Lighting>Fixtures>Barn": "39111600",
    "Building Materials & Hardscape>Decking>Accessories": "30161700",
    "Building Materials & Hardscape>Decking>Lighting": "39111615",
    "Building Materials & Hardscape>Decking>Hardware": "30161900",
    "Building Materials & Hardscape>Lumber & Sheathing>Treated Lumber": "30111501",
    "Building Materials & Hardscape>Lumber & Sheathing>Cedar": "30111502",
    "Building Materials & Hardscape>Lumber & Sheathing>Pine": "30111503",
    "Building Materials & Hardscape>Lumber & Sheathing>Hardwood": "30111504",
    "Building Materials & Hardscape>Lumber & Sheathing>MDF": "30111505",
    "Building Materials & Hardscape>Windows & Doors>Entry Doors": "30151610",
    "Building Materials & Hardscape>Windows & Doors>Interior Doors": "30151609",
    "Building Materials & Hardscape>Windows & Doors>Exterior Doors": "30151610",
    "Building Materials & Hardscape>Trim & Moulding>Door Casing": "30121504",
    "Building Materials & Hardscape>Trim & Moulding>Window Casing": "30121504",
    "Building Materials & Hardscape>Trim & Moulding>Chair Rail": "30121505",
    "Building Materials & Hardscape>Trim & Moulding>Wainscoting": "30121506",
    "Abrasives>Pads>Hook and Loop Pads": "31191701",
    "Abrasives>Pads>Adhesive Pads": "31191702",
    "Abrasives>Sheets>Sandpaper": "31192001",
    "Abrasives>Sheets>Wet Dry": "31192002",
    "Safety Products>Eye Protection": "46181500",
    "Safety Products>Eye Protection>Safety Glasses": "46181501",
    "Safety Products>Eye Protection>Safety Goggles": "46181502",
    "Safety Products>Hearing Protection>Earmuffs": "46181802",
    "Safety Products>Hearing Protection>Ear Plugs": "46181801",
    "Lighting": "39111600",
    "Power Tools": "27111901",
    "Building Materials & Hardscape": "30000000",
    "Appliances & Consumer Electronics": "52141500",
    "Building Materials & Hardscape>Drywall & Insulation>Drywall": "30131901",
    "Building Materials & Hardscape>Drywall & Insulation>Insulation": "30132000",
    "Building Materials & Hardscape>Drywall & Insulation": "30131900",
    "Electrical": "39120000",
    "Fasteners": "31160000",
    "Hand Tools": "27110000",
    "Hand Tools>Snips": "27113100",
    "Safety>Smoke Detectors": "46182200",
    "Safety>Fire Extinguishers": "46182100",
    "Power Tools>Rotary Tools": "27112800",
    "Power Tools>Grinders>Angle Grinders": "27111801",
    "Power Tools>Grinders": "27111800",
    "Lighting>Clips": "39111600",
    "Safety>Body Protection>Knee Pads": "46182001",
    "Building Materials & Hardscape>Windows & Doors>Hardware>Latches": "30151608",
    "Appliances & Consumer Electronics>Kitchen Appliances>Ovens": "52141504",
    "Safety>Body Protection>Phone Cases": "46182002",
    "General": "99990000",
    "Fasteners>Screws>Drywall": "31161706",
    "Hand Tools>Levels": "27112502",
    "Power Tools>Drivers": "27111902",
    "Power Tools>Nailers>Staplers": "27112104",
    "Hand Tools>Ratchets": "27111501",
    "Abrasives": "31190000",
    "Building Materials & Hardscape>Windows & Doors>Glass": "30151500",
    "Power Tools>Miter Saws": "27111502",
}


class ProductPipeline:
    def __init__(self, data_dir=None):
        """Initialize all components"""
        _ensure_modules()
        self.data_loader = _DataLoader(data_dir)
        self.brand_normalizer = _BrandNormalizer(self.data_loader)
        self.brand_learner = _BrandLearner()
        self.classifier_learner = _ClassifierLearner()
        self.parser = _DescriptionParser()
        self.generator = _DescriptionGenerator()
        self.web_enricher = _WebEnricher()
        self._initialized = False

    def initialize(self, input_data=None):
        """
        Load all reference data and learn from input data.
        Skips if already initialized (fast path for repeated requests).
        
        Args:
            input_data: Optional list of dicts to learn brand mappings from
        """
        if self._initialized:
            return
        
        self.data_loader.load_all()
        
        # Learn brand mappings from input data if provided
        if input_data:
            self.brand_learner.learn_from_data(input_data)
            self.classifier_learner.learn_from_data(input_data)
        
        self._initialized = True

    @staticmethod
    def _recalc_confidence(row: Dict[str, Any]) -> int:
        score = 0
        classpath = row.get('Classpath', '')
        brand_name = row.get('BRAND_NAME', '')
        mobile_desc = row.get('MOBILE_DESC', '')
        mfg_part_num = row.get('Mfg_Part_Num', '')
        if classpath and classpath != 'General':
            depth = classpath.count('>') + 1
            score += min(30, 10 * depth)
        if brand_name:
            brand_lower = brand_name.lower().strip().rstrip('\u00ae')
            known = {'3m','dewalt','milwaukee','makita','bosch','ridgid','ryobi','stanley','craftsman','irwin','diablo','freud','mirka','leviton','lutron','philips','ge','whirlpool','frigidaire','lg','samsung','maytag','speed queen','electrolux','siemens','trex','azek','timbertech','fiberon','moen','kohler','honeywell','panasonic','hunter','broan','nutone','southwire','satco','kichler','lithonia','cree','feit','senco','streamlight','klein','snap-on','gearwrench','knipex','wiha','wera','hilti','festool','metabo','rheem','a.o. smith','bradford white','rinnai','navien','simpson strong-tie','grk','fastenmaster','lenox','channellock','vise-grip','leatherman','gerber'}
            score += 20 if brand_lower in known else 10
        if mobile_desc:
            mob_len = len(str(mobile_desc))
            if 60 <= mob_len <= 80:
                score += 15
            elif 40 <= mob_len < 60:
                score += 8
            elif mob_len > 80:
                score += 10
        attr_count = sum(1 for k in row if k.startswith('ATTRIBUTE_LABEL') and row[k])
        if attr_count >= 5:
            score += 15
        elif attr_count >= 3:
            score += 10
        elif attr_count >= 1:
            score += 5
        if mfg_part_num and len(str(mfg_part_num).strip()) > 2:
            score += 5
        return min(99, score)

    def process_row(self, row: Dict[str, Any], deep_sourcing: bool = False, row_index: int = 0) -> Dict[str, Any]:
        """
        Process a single input row and return a dict with all 252 output columns.

        Args:
            row: dict with keys Mfg_Part_Num, Part_Desc, E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf
            deep_sourcing: if True, search web for missing specs (all rows, throttled to 5 concurrent)
            row_index: current row index

        Returns:
            dict with all 252 output column values
        """
        mfg_part_num = (row.get("Mfg_Part_Num") or "").strip()
        part_desc = (row.get("Part_Desc") or "").strip()
        e1_brand = (row.get("E1_Brand") or "").strip()
        unilog_brand = (row.get("Unilog_Brand") or "").strip()
        dib_brand = (row.get("DIB_Brand") or "").strip()
        part_manuf = (row.get("Part_Manuf") or "").strip()

        for val in ["-- Unbranded --", "-- No Unilog Brand --", "-- No DIB Brand --", "-- No Unilog Brand --", "--", "-"]:
            if e1_brand == val:
                e1_brand = ""
            if unilog_brand == val:
                unilog_brand = ""
            if dib_brand == val:
                dib_brand = ""
            if part_manuf == val:
                part_manuf = ""

        brand_info = self.brand_normalizer.normalize(
            part_manuf=part_manuf,
            e1_brand=e1_brand,
            unilog_brand=unilog_brand,
            dib_brand=dib_brand,
            part_desc=part_desc,
            mpn=mfg_part_num,
        )
        manufacturer_name = brand_info.get("manufacturer_name", "")
        brand_name = brand_info.get("brand_name", "")
        brand_confidence = brand_info.get("confidence", 0)
        brand_method = brand_info.get("method", "")
        trade_name = brand_name
        
        # Only use learner if normalizer didn't find a confident brand
        if part_desc and part_manuf and (not brand_name or brand_confidence < 0.7 or brand_method == 'fallback'):
            learned_brand, learned_manuf, confidence = self.brand_learner.get_brand_for_product(
                part_desc, part_manuf
            )
            if confidence > 0.8:
                brand_name = learned_brand
                manufacturer_name = learned_manuf

        parsed = self.parser.parse(
            mpn=mfg_part_num,
            part_desc=part_desc,
            brand_info=brand_name,
        )
        
        # Use brand from description if found (overrides manufacturer-based brand)
        brand_in_desc = parsed.get("brand_in_desc", "")
        if brand_in_desc:
            brand_name = brand_in_desc
            if not trade_name:
                trade_name = brand_in_desc
        
        product_type = parsed.get("product_type", "")
        category = parsed.get("category", "")
        classpath = parsed.get("classpath", "")
        
        # Use classifier learner if parser didn't find a good classification
        if (not classpath or classpath == 'General') and part_desc:
            learned_category, confidence = self.classifier_learner.classify_product(part_desc, part_manuf)
            if learned_category and learned_category != 'General' and confidence > 0.3:
                classpath = learned_category
                category = classpath.split(">")[0] if ">" in classpath else classpath
        
        dimensions = parsed.get("dimensions", {})
        features = parsed.get("features", [])
        material = parsed.get("material", "")
        color = parsed.get("color", "")
        quantity_raw = parsed.get("quantity", None)
        if isinstance(quantity_raw, dict):
            selling_qty = quantity_raw.get("qty", "")
            selling_uom = quantity_raw.get("uom", "")
        elif quantity_raw is not None:
            selling_qty = str(quantity_raw)
            selling_uom = ""
        else:
            selling_qty = ""
            selling_uom = ""
        attributes = parsed.get("attributes", [])

        try:
            grammar_attrs = _extract_grammar(part_desc, classpath, dimensions)
            for ga in grammar_attrs:
                already = any(a["label"].lower() == ga["label"].lower() for a in attributes)
                if not already:
                    attributes.append(ga)
                if ga["label"].lower() == "voltage" and not dimensions.get("voltage"):
                    dimensions["voltage"] = ga["value"]
                elif ga["label"].lower() == "amperage" and not dimensions.get("amperage"):
                    dimensions["amperage"] = ga["value"]
                elif ga["label"].lower() == "wattage" and not dimensions.get("wattage"):
                    dimensions["wattage"] = ga["value"]
        except Exception as e:
            import traceback; traceback.print_exc()

        MPN_COLOR_MAP = {
            "SS": "Stainless Steel", "BSS": "Black Stainless Steel",
            "BK": "Black", "WH": "White", "BL": "Blue", "RD": "Red",
            "GR": "Green", "GY": "Gray", "DG": "Dark Gray", "BO": "Bisque",
            "SL": "Slate", "PT": "Platinum", "SN": "Silver",
            "BIS": "Bisque", "WHT": "White", "BLK": "Black",
            "GLD": "Gold", "CP": "Chrome", "BRZ": "Bronze",
            "PR": "Panel Ready", "YLW": "Yellow",
        }
        if not any(a["label"].lower() == "color" for a in attributes):
            mpn_upper = mfg_part_num.upper()
            mpn_color = MPN_COLOR_MAP.get(mpn_upper[-2:])
            if not mpn_color:
                for suffix, clr in MPN_COLOR_MAP.items():
                    if mpn_upper.endswith(suffix) and len(mpn_upper) > len(suffix):
                        mpn_color = clr
                        break
            if mpn_color:
                attributes.append({"label": "Color", "value": mpn_color, "uom": ""})

        ref_url = ""
        web_specs = {}
        needs_web = (
            deep_sourcing
            and self.web_enricher.is_available
            and mfg_part_num
            and len(mfg_part_num) > 2
        )
        if needs_web:
            try:
                ref_url, web_specs = self.web_enricher.search_and_scrape(brand_name or manufacturer_name, mfg_part_num)
                ref_url = ref_url or ""
                if web_specs:
                    for key, val in web_specs.items():
                        if key.startswith("_"):
                            continue
                        already_has = False
                        for attr in attributes:
                            if attr.get("label", "").lower() == key.lower():
                                already_has = True
                                break
                        if not already_has:
                            attributes.append({"label": key, "value": val, "uom": ""})
                        if key.lower() == "voltage" and not any(d.get("voltage") for d in [dimensions] if d):
                            dimensions["voltage"] = val
                        elif key.lower() == "amperage" and not any(d.get("amperage") for d in [dimensions] if d):
                            dimensions["amperage"] = val
                        elif key.lower() == "wattage" and not any(d.get("wattage") for d in [dimensions] if d):
                            dimensions["wattage"] = val
                        elif key.lower() == "sound level" and not any(d.get("sound_level") for d in [dimensions] if d):
                            dimensions["sound_level"] = val
                        elif key.lower() == "capacity" and not any(d.get("capacity") for d in [dimensions] if d):
                            dimensions["capacity"] = val
                        elif key.lower() == "finish" and not color:
                            color = val
                        elif key.lower() == "mounting":
                            dimensions["mounting"] = val
                        elif key.lower() == "wash cycles":
                            dimensions["wash_cycles"] = val
            except Exception as e:
                logger.warning(f"Web enrichment failed for {mfg_part_num}: {e}")

        # Spec inference: fill in missing specs from MPN pattern database
        _inferred_series = ""
        if not dimensions.get("voltage") and product_type:
            try:
                from src.spec_inference import infer_specs, get_spec_value
                inferred = infer_specs(mfg_part_num, part_desc, brand_name, product_type)
                for key in ["voltage", "amperage", "sound_level", "capacity", "mounting", "wash_cycles",
                            "width", "depth", "depth_open", "fuel", "material"]:
                    if not dimensions.get(key) and inferred.get(key):
                        val = get_spec_value(inferred, key)
                        if val:
                            dimensions[key] = val
                if not material and inferred.get("material"):
                    material = get_spec_value(inferred, "material")
                if not color and inferred.get("color"):
                    color = get_spec_value(inferred, "color")
                # Store series for later use
                if inferred.get("series"):
                    _inferred_series = get_spec_value(inferred, "series")
                else:
                    _inferred_series = ""
            except Exception:
                _inferred_series = ""

        class_parts = [p.strip() for p in classpath.split(">") if p.strip()] if classpath else []
        dept = category
        class_level = class_parts[1] if len(class_parts) > 1 else ""
        fine_level = class_parts[2] if len(class_parts) > 2 else ""

        gen_input = {
            "part_desc": part_desc,
            "mfg_part_num": mfg_part_num,
            "brand_name": brand_name,
            "manufacturer_name": manufacturer_name,
            "product_type": product_type,
            "category": category,
            "classpath": classpath,
            "dimensions": dimensions,
            "features": features,
            "material": material,
            "color": color,
        }

        mobile_desc = self.generator.generate_mobile_desc(
            brand=brand_name,
            product_type=product_type,
            series=parsed.get("series", "") or _inferred_series,
            mpn=mfg_part_num,
            features_list=features,
            material=material,
            color=color,
            part_desc=part_desc,
            grit=parsed.get("grit", ""),
            quantity=selling_qty or (str(parsed.get("quantity", "")) if parsed.get("quantity") else ""),
            raw_dimensions=parsed.get("raw_dimensions", ""),
        )

        try:
            engine_mobile_desc = _engine_mobile(
                manufacturer=manufacturer_name,
                brand=brand_name,
                product_type=product_type,
                series=parsed.get("series", "") or _inferred_series,
                mpn=mfg_part_num,
                mounting=dimensions.get("mounting", ""),
                attributes=attributes,
                raw_dimensions=parsed.get("raw_dimensions", ""),
                classpath=classpath,
                part_desc=part_desc,
                grit=parsed.get("grit", ""),
                quantity=selling_qty,
                color=color,
                material=material,
            )
            engine_in_range = 60 <= len(engine_mobile_desc) <= 80
            old_in_range = 60 <= len(mobile_desc) <= 80
            if engine_in_range or (not old_in_range and len(engine_mobile_desc) > len(mobile_desc)):
                mobile_desc = engine_mobile_desc
        except Exception:
            pass

        web_desc = ""
        if web_specs:
            web_desc = web_specs.get("_description", "")

        if len(mobile_desc) < 60 and web_desc:
            clean_web = web_desc.strip().rstrip(".")
            if len(clean_web) > 20:
                test = f"{mobile_desc.rstrip(',')}, {clean_web}"
                if len(test) <= 80:
                    mobile_desc = test
                else:
                    truncated = _smart_truncate(test, 80)
                    if len(truncated) >= 60:
                        mobile_desc = truncated

        invoice_desc = self.generator.generate_invoice_desc(
            product_type=product_type,
            attributes_dict=dimensions,
            part_desc=part_desc,
            grit=parsed.get("grit", ""),
            material=material,
            color=color,
            raw_dimensions=parsed.get("raw_dimensions", ""),
        )

        try:
            engine_inv_desc = _engine_invoice(
                product_type=product_type,
                attributes=attributes,
                dimensions=dimensions,
                classpath=classpath,
                grit=parsed.get("grit", ""),
                quantity=selling_qty,
                raw_dimensions=parsed.get("raw_dimensions", ""),
            )
            if len(engine_inv_desc) <= 40 and len(engine_inv_desc) > len(invoice_desc) * 0.5:
                invoice_desc = engine_inv_desc
        except Exception:
            pass
        short_desc = self.generator.generate_short_desc(
            brand=brand_name,
            series=parsed.get("series", "") or _inferred_series,
            mpn=mfg_part_num,
            product_type=product_type,
            features_list=features,
        )
        long_desc1 = self.generator.generate_long_desc(
            brand=brand_name,
            product_type=product_type,
            series=parsed.get("series", "") or _inferred_series,
            attributes_dict=dimensions,
            features_list=features,
        )
        retail_desc = self.generator.generate_retail_desc(
            series=parsed.get("series", ""),
            product_type=product_type,
            features_list=features,
        )
        marketing_desc = self.generator.generate_marketing_desc(
            brand=brand_name,
            product_type=product_type,
            features_list=features,
        )
        item_features = self.generator.generate_item_features(
            features_list=features,
        )

        with_clause = ""
        if features:
            with_clause = "With " + ", ".join(features)

        all_attributes = []
        for attr in attributes:
            all_attributes.append({
                "label": attr.get("label", ""),
                "value": attr.get("value", ""),
                "uom": attr.get("uom", ""),
            })
        
        # Map internal dimension keys to proper Unilog attribute labels
        DIMENSION_LABEL_MAP = {
            'voltage': 'Voltage Rating',
            'amperage': 'Amperage Rating',
            'wattage': 'Wattage Rating',
            'sound_level': 'Sound Level',
            'mounting': 'Mounting Type',
            'wash_cycles': 'Number of Wash Cycles',
            'capacity': 'Capacity',
            'width': 'Width',
            'depth': 'Depth',
            'depth_open': 'Depth With Door Open',
            'height': 'Height',
            'fuel': 'Fuel Type',
        }
        
        if dimensions:
            for dim_name, dim_val in dimensions.items():
                dim_uom = ""
                if isinstance(dim_val, dict):
                    dim_value = dim_val.get("value", "")
                    dim_uom = dim_val.get("uom", "")
                else:
                    dim_value = str(dim_val)
                label = DIMENSION_LABEL_MAP.get(dim_name, dim_name)
                already = any(a["label"].lower() == label.lower() for a in all_attributes)
                if not already:
                    all_attributes.append({
                        "label": label,
                        "value": dim_value,
                        "uom": dim_uom,
                    })
        if material:
            already = any(a["label"].lower() == "material" for a in all_attributes)
            if not already:
                all_attributes.append({"label": "Material", "value": material, "uom": ""})
        if color:
            already = any(a["label"].lower() == "color" for a in all_attributes)
            if not already:
                all_attributes.append({"label": "Color", "value": color, "uom": ""})
        for feat in features:
            all_attributes.append({"label": "Feature", "value": feat, "uom": ""})

        attr_labels = []
        attr_values = []
        attr_uoms = []
        for i in range(50):
            if i < len(all_attributes):
                attr_labels.append(all_attributes[i].get("label", ""))
                attr_values.append(all_attributes[i].get("value", ""))
                attr_uoms.append(all_attributes[i].get("uom", ""))
            else:
                attr_labels.append("")
                attr_values.append("")
                attr_uoms.append("")

        length_val = ""
        length_uom = ""
        height_val = ""
        height_uom = ""
        width_val = ""
        width_uom = ""
        weight_val = ""
        weight_uom = ""
        volume_val = ""
        volume_uom = ""

        if "length" in dimensions:
            d = dimensions["length"]
            if isinstance(d, dict):
                length_val = d.get("value", "")
                length_uom = d.get("uom", "")
            else:
                length_val = str(d)
        if "height" in dimensions:
            d = dimensions["height"]
            if isinstance(d, dict):
                height_val = d.get("value", "")
                height_uom = d.get("uom", "")
            else:
                height_val = str(d)
        if "width" in dimensions:
            d = dimensions["width"]
            if isinstance(d, dict):
                width_val = d.get("value", "")
                width_uom = d.get("uom", "")
            else:
                width_val = str(d)
        if "weight" in dimensions:
            d = dimensions["weight"]
            if isinstance(d, dict):
                weight_val = d.get("value", "")
                weight_uom = d.get("uom", "")
            else:
                weight_val = str(d)
        if "volume" in dimensions:
            d = dimensions["volume"]
            if isinstance(d, dict):
                volume_val = d.get("value", "")
                volume_uom = d.get("uom", "")
            else:
                volume_val = str(d)

        if not length_val and "length" in [a.get("label", "").lower() for a in all_attributes]:
            for a in all_attributes:
                if a.get("label", "").lower() == "length":
                    length_val = a.get("value", "")
                    length_uom = a.get("uom", "")
                    break
        if not height_val and "height" in [a.get("label", "").lower() for a in all_attributes]:
            for a in all_attributes:
                if a.get("label", "").lower() == "height":
                    height_val = a.get("value", "")
                    height_uom = a.get("uom", "")
                    break
        if not width_val and "width" in [a.get("label", "").lower() for a in all_attributes]:
            for a in all_attributes:
                if a.get("label", "").lower() == "width":
                    width_val = a.get("value", "")
                    width_uom = a.get("uom", "")
                    break
        if not weight_val and "weight" in [a.get("label", "").lower() for a in all_attributes]:
            for a in all_attributes:
                if a.get("label", "").lower() == "weight":
                    weight_val = a.get("value", "")
                    weight_uom = a.get("uom", "")
                    break
        if not volume_val and "volume" in [a.get("label", "").lower() for a in all_attributes]:
            for a in all_attributes:
                if a.get("label", "").lower() == "volume":
                    volume_val = a.get("value", "")
                    volume_uom = a.get("uom", "")
                    break

        brand_safe = brand_name.replace(" ", "_") if brand_name else "Unknown"
        mpn_safe = mfg_part_num.replace(" ", "_") if mfg_part_num else "Unknown"
        product_image = f"{brand_safe}_{mpn_safe}.jpg" if brand_name and mfg_part_num else ""
        spec_sheet = ""

        has_info = bool(product_type or category or features or dimensions)
        actual_image = ""

        output = {}
        output["MFR URL"] = ""
        output["Ref URL 1"] = ref_url
        output["Ref URL 2"] = ""
        output["Ref URL 3"] = ""
        output["Ref URL 4"] = ""
        output["Ref URL 5"] = ""
        output["PART_NUMBER"] = ""
        output["Dept"] = dept
        output["Class"] = class_level
        output["Fine"] = fine_level
        output["SKU - MY_PART_NUMBER"] = ""
        output["Mfg_Part_Num"] = mfg_part_num
        output["Part_Desc"] = part_desc
        output["E1_Brand"] = e1_brand
        output["Unilog_Brand"] = unilog_brand
        output["DIB_Brand"] = dib_brand
        output["Part_Manuf"] = part_manuf
        output["MANUFACTURER_NAME"] = manufacturer_name
        output["BRAND_NAME"] = self.generator._apply_trademark(brand_name) if brand_name else brand_name
        output["TRADE_NAME"] = self.generator._apply_trademark(trade_name) if trade_name else trade_name
        output["MANUFACTURER_PART_NUMBER"] = mfg_part_num
        output["ALTERNATE_PART_NUMBER"] = ""
        output["Classpath"] = classpath
        output["MOBILE_DESC"] = mobile_desc
        output["INVOICE_DESC"] = invoice_desc

        # Enforce MOBILE_DESC length 60-80
        mob = output["MOBILE_DESC"]
        if len(mob) < 60:
            pad_parts = []
            if product_type:
                pad_parts.append(product_type)
            if classpath:
                for cp in classpath.split('>'):
                    cp = cp.strip()
                    if cp and cp.lower() not in mob.lower():
                        pad_parts.append(cp)
            if material:
                pad_parts.append(material)
            if color:
                pad_parts.append(color)
            for a in all_attributes[:5]:
                tag = "%s %s" % (a['label'], a['value'])
                if tag.lower() not in mob.lower():
                    pad_parts.append(tag)
            for pad in pad_parts:
                if len(mob) >= 60:
                    break
                test = "%s, %s" % (mob, pad) if mob else pad
                if len(test) <= 80:
                    mob = test
            output["MOBILE_DESC"] = mob
        output["SHORT_DESC"] = short_desc
        output["LONG_DESC1"] = long_desc1
        output["RETAIL_DESC"] = retail_desc
        output["MARKETING_DESCRIPTION"] = marketing_desc

        for i in range(1, 21):
            key = f"ITEM_FEATURES_{i}"
            output[key] = item_features.get(key, "")

        output["With"] = with_clause
        output["Standard/Approvals"] = ""
        output["Prop 65"] = ""
        output["Application"] = product_type
        output["Includes"] = ""
        output["Product Name"] = product_type

        for i in range(1, 51):
            output[f"ATTRIBUTE_LABEL {i}"] = attr_labels[i - 1]
            output[f"ATTRIBUTE_VALUE {i}"] = attr_values[i - 1]
            output[f"ATTRIBUTE_UOM {i}"] = attr_uoms[i - 1]

        output["UPC"] = ""
        output["EAN"] = ""
        output["GTIN"] = ""
        output["UNSPSC"] = CLASSPATH_TO_UNSPSC.get(classpath, "")
        output["Warranty"] = ""
        output["List Price"] = ""
        output["Selling Qty"] = selling_qty
        output["Selling UOM"] = selling_uom
        output["LENGTH"] = length_val
        output["LENGTH_UOM"] = length_uom
        output["HEIGHT"] = height_val
        output["HEIGHT_UOM"] = height_uom
        output["WIDTH"] = width_val
        output["WIDTH_UOM"] = width_uom
        output["WEIGHT"] = weight_val
        output["WEIGHT_UOM"] = weight_uom
        output["VOLUME"] = volume_val
        output["VOLUME_UOM"] = volume_uom
        output["Product Image"] = product_image
        output["Specification Sheet"] = spec_sheet
        output["Actual Image (Yes/No)"] = actual_image

        review_reasons = []
        if not brand_name:
            review_reasons.append("No Brand Found")
        if not classpath or classpath == "General":
            review_reasons.append("Unclassified")
        if not any(a.get("value") for a in all_attributes):
            review_reasons.append("No Attributes")
        if len(part_desc) < 20:
            review_reasons.append("Short Description")
        review_reason = " + ".join(review_reasons) if review_reasons else ""
        output["REVIEW_REASON"] = review_reason

        score = 0

        if classpath and classpath != 'General':
            depth = classpath.count('>') + 1
            score += min(30, 10 * depth)

        if brand_name:
            brand_lower = brand_name.lower().strip()
            known_brands = {'3m', 'dewalt', 'milwaukee', 'makita', 'bosch', 'ridgid', 'ryobi',
                'stanley', 'craftsman', 'irwin', 'diablo', 'freud', 'mirka',
                'leviton', 'lutron', 'philips', 'ge', 'whirlpool', 'frigidaire',
                'lg', 'samsung', 'maytag', 'speed queen', 'electrolux', 'siemens',
                'trex', 'azek', 'timbertech', 'fiberon', 'moen', 'kohler',
                'honeywell', 'panasonic', 'hunter', 'broan', 'nutone',
                'southwire', 'satco', 'kichler', 'lithonia', 'cree', 'feit',
                'senco', 'streamlight', 'klein', 'snap-on', 'gearwrench',
                'knipex', 'wiha', 'wera', 'hilti', 'festool', 'metabo',
                'rheem', 'a.o. smith', 'bradford white', 'rinnai', 'navien',
                'simpson strong-tie', 'grk', 'fastenmaster', 'lenox',
                'channellock', 'vise-grip', 'leatherman', 'gerber'}
            if brand_lower in known_brands:
                score += 20
            else:
                score += 10

        if mobile_desc:
            mob_len = len(str(mobile_desc))
            if 60 <= mob_len <= 80:
                score += 15
            elif 40 <= mob_len < 60:
                score += 8
            elif mob_len > 80:
                score += 10

        attr_count = sum(1 for k in output if k.startswith('ATTRIBUTE_LABEL') and output[k])
        if attr_count >= 5:
            score += 15
        elif attr_count >= 3:
            score += 10
        elif attr_count >= 1:
            score += 5

        if mfg_part_num and len(str(mfg_part_num).strip()) > 2:
            score += 5

        score = min(99, score)
        output["CONFIDENCE_SCORE"] = f"{score}%"
        if score < 60:
            if review_reason:
                review_reason += " + Low Confidence"
            else:
                review_reason = "Low Confidence"
            output["REVIEW_REASON"] = review_reason
        output["NEEDS_REVIEW"] = "Yes" if score < 50 else "No"

        return output

    def process_csv(self, input_path: str, output_path: str, progress_callback=None, deep_sourcing: bool = False):
        """
        Read input CSV, process all rows, write output CSV with all 252 columns.

        Args:
            input_path: path to input CSV
            output_path: path to output CSV
            progress_callback: optional function(current, total, status) for progress updates
            deep_sourcing: if True, search web for missing specs (all rows, throttled to 5 concurrent)
        """
        _ensure_deps()
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
        total = len(df)
        results = []
        for idx, row in enumerate(df.itertuples(index=False)):
            row_dict = dict(zip(df.columns, row))
            output_row = self.process_row(row_dict, deep_sourcing=False, row_index=idx)
            results.append(output_row)
            if progress_callback:
                progress_callback(idx + 1, total, f"Phase 1: Processing row {idx + 1} of {total}")

        if deep_sourcing and self.web_enricher and self.web_enricher.is_available:
            candidates = []
            for i, r in enumerate(results):
                brand = r.get('BRAND_NAME', '')
                mpn = r.get('Mfg_Part_Num', '')
                attr_count = sum(1 for k in r if k.startswith('ATTRIBUTE_LABEL') and r[k])
                conf_str = r.get('CONFIDENCE_SCORE', '0%')
                try:
                    conf = int(conf_str.rstrip('%'))
                except (ValueError, AttributeError):
                    conf = 0
                needs_web = (
                    (conf < 50 or (not brand and attr_count < 2))
                    and attr_count < 5
                    and mpn and len(str(mpn).strip()) > 2
                    and str(mpn).strip() != '-'
                    and i < 20  # Cap web sourcing to first 20 rows
                )
                if needs_web:
                    candidates.append(i)

            if candidates and progress_callback:
                progress_callback(total, total, f"Phase 2: Web sourcing {len(candidates)} rows...")

            batch_size = 10
            for batch_start in range(0, len(candidates), batch_size):
                batch = candidates[batch_start:batch_start + batch_size]
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {}
                    for i in batch:
                        r = results[i]
                        brand = r.get('BRAND_NAME', '') or r.get('MANUFACTURER_NAME', '')
                        mpn = r.get('Mfg_Part_Num', '')
                        if brand and mpn:
                            fut = executor.submit(self.web_enricher.search_and_scrape, brand, mpn)
                            futures[fut] = i
                    for fut in as_completed(futures):
                        idx = futures[fut]
                        try:
                            ref_url, web_specs = fut.result()
                            if web_specs:
                                for key, val in web_specs.items():
                                    if key.startswith('_'):
                                        continue
                                    attr_key = None
                                    for k in results[idx]:
                                        if k.startswith('ATTRIBUTE_LABEL') and results[idx][k].lower() == key.lower():
                                            attr_key = k
                                            break
                                    if not attr_key:
                                        for k in range(1, 51):
                                            lbl = results[idx].get('ATTRIBUTE_LABEL %d' % k, '')
                                            if not lbl:
                                                results[idx]['ATTRIBUTE_LABEL %d' % k] = key
                                                results[idx]['ATTRIBUTE_VALUE %d' % k] = val
                                                results[idx]['ATTRIBUTE_UOM %d' % k] = ''
                                                break
                                if ref_url:
                                    results[idx]['Ref URL 1'] = ref_url
                                brand = results[idx].get('BRAND_NAME', '')
                                if not brand and 'Brand' in web_specs:
                                    results[idx]['BRAND_NAME'] = web_specs['Brand']
                                web_desc = web_specs.get('_description', '')
                                if web_desc:
                                    mob = results[idx].get('MOBILE_DESC', '')
                                    if len(str(mob)) < 60:
                                        clean = web_desc.strip().rstrip('.')
                                        test = '%s, %s' % (mob.rstrip(','), clean)
                                        if len(test) <= 80:
                                            results[idx]['MOBILE_DESC'] = test
                        except Exception:
                            pass

            for i in candidates:
                results[i]["CONFIDENCE_SCORE"] = f"{self._recalc_confidence(results[i])}%"
                results[i]["NEEDS_REVIEW"] = "Yes" if self._recalc_confidence(results[i]) < 50 else "No"

            if progress_callback:
                progress_callback(total, total, "Phase 2 complete")

        output_df = pd.DataFrame(results)

        all_columns = []
        all_columns.append("MFR URL")
        all_columns.append("Ref URL 1")
        all_columns.append("Ref URL 2")
        all_columns.append("Ref URL 3")
        all_columns.append("Ref URL 4")
        all_columns.append("Ref URL 5")
        all_columns.append("PART_NUMBER")
        all_columns.append("Dept")
        all_columns.append("Class")
        all_columns.append("Fine")
        all_columns.append("SKU - MY_PART_NUMBER")
        all_columns.append("Mfg_Part_Num")
        all_columns.append("Part_Desc")
        all_columns.append("E1_Brand")
        all_columns.append("Unilog_Brand")
        all_columns.append("DIB_Brand")
        all_columns.append("Part_Manuf")
        all_columns.append("MANUFACTURER_NAME")
        all_columns.append("BRAND_NAME")
        all_columns.append("TRADE_NAME")
        all_columns.append("MANUFACTURER_PART_NUMBER")
        all_columns.append("ALTERNATE_PART_NUMBER")
        all_columns.append("Classpath")
        all_columns.append("MOBILE_DESC")
        all_columns.append("INVOICE_DESC")
        all_columns.append("SHORT_DESC")
        all_columns.append("LONG_DESC1")
        all_columns.append("RETAIL_DESC")
        all_columns.append("MARKETING_DESCRIPTION")
        for i in range(1, 21):
            all_columns.append(f"ITEM_FEATURES_{i}")
        all_columns.append("With")
        all_columns.append("Standard/Approvals")
        all_columns.append("Prop 65")
        all_columns.append("Application")
        all_columns.append("Includes")
        all_columns.append("Product Name")
        for i in range(1, 51):
            all_columns.append(f"ATTRIBUTE_LABEL {i}")
            all_columns.append(f"ATTRIBUTE_VALUE {i}")
            all_columns.append(f"ATTRIBUTE_UOM {i}")
        all_columns.append("UPC")
        all_columns.append("EAN")
        all_columns.append("GTIN")
        all_columns.append("UNSPSC")
        all_columns.append("Warranty")
        all_columns.append("List Price")
        all_columns.append("Selling Qty")
        all_columns.append("Selling UOM")
        all_columns.append("Standard Packaging Information")
        all_columns.append("LENGTH")
        all_columns.append("LENGTH_UOM")
        all_columns.append("HEIGHT")
        all_columns.append("HEIGHT_UOM")
        all_columns.append("WIDTH")
        all_columns.append("WIDTH_UOM")
        all_columns.append("WEIGHT")
        all_columns.append("WEIGHT_UOM")
        all_columns.append("VOLUME")
        all_columns.append("VOLUME_UOM")
        all_columns.append("Product Image")
        all_columns.append("Alternate Image 1")
        all_columns.append("Alternate Image 2")
        all_columns.append("Alternate Image 3")
        all_columns.append("Alternate Image 4")
        all_columns.append("SDS")
        all_columns.append("SDS_1")
        all_columns.append("Warranty Information")
        all_columns.append("Catalog")
        all_columns.append("Specification Sheet")
        all_columns.append("Instruction/Installation Manual")
        all_columns.append("Service Manual")
        all_columns.append("Owners/User Manual")
        all_columns.append("Line Drawing")
        all_columns.append("MTR")
        all_columns.append("RoHS")
        all_columns.append("Full Engineering Drawing")
        all_columns.append("Energy Star Guide")
        all_columns.append("Technical Bulletin")
        all_columns.append("Submittal")
        all_columns.append("Compatibility Chart")
        all_columns.append("Size Chart")
        all_columns.append("Product Label/Insert")
        all_columns.append("Video Link")
        all_columns.append("Video Link 1")
        all_columns.append("Country Of Origin")
        all_columns.append("Discontinued")
        all_columns.append("Actual Image (Yes/No)")
        all_columns.append("CONFIDENCE_SCORE")
        all_columns.append("NEEDS_REVIEW")
        all_columns.append("REVIEW_REASON")
        all_columns.append("IS_DUPLICATE")
        all_columns.append("DUPLICATE_OF")

        for col in all_columns:
            if col not in output_df.columns:
                output_df[col] = ""

        output_df = output_df[all_columns]
        output_df = output_df.fillna("")

        output_df['_mpn_clean'] = output_df['Mfg_Part_Num'].str.strip().str.upper()
        output_df['IS_DUPLICATE'] = output_df.duplicated(subset=['_mpn_clean'], keep='first')
        output_df['DUPLICATE_OF'] = ''
        dup_mask = output_df['IS_DUPLICATE'] == True
        for idx in output_df[dup_mask].index:
            mpn = output_df.at[idx, '_mpn_clean']
            first_idx = output_df[output_df['_mpn_clean'] == mpn].index[0]
            output_df.at[idx, 'DUPLICATE_OF'] = output_df.at[first_idx, 'Mfg_Part_Num']
        output_df['IS_DUPLICATE'] = output_df['IS_DUPLICATE'].map({True: 'True', False: 'False'})
        output_df = output_df.drop(columns=['_mpn_clean'])

        import os
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        output_df.to_csv(output_path, index=False)
        print(f"Processed {len(results)} rows. Output written to {output_path}")
        return output_df

    def process_dataframe(self, input_df: pd.DataFrame, progress_callback=None, deep_sourcing: bool = False) -> pd.DataFrame:
        """
        Process a DataFrame and return enriched DataFrame.

        Args:
            input_df: pandas DataFrame with input data
            progress_callback: optional function(current, total, status)
            deep_sourcing: if True, search web for missing specs (all rows, throttled to 5 concurrent)

        Returns:
            pandas DataFrame with all 252 output columns
        """
        total = len(input_df)
        _ensure_deps()
        results = []
        for idx, row in enumerate(input_df.itertuples(index=False)):
            row_dict = dict(zip(input_df.columns, row))
            output_row = self.process_row(row_dict, deep_sourcing=False, row_index=idx)
            results.append(output_row)
            if progress_callback:
                progress_callback(idx + 1, total, f"Phase 1: Processing row {idx + 1} of {total}")

        if deep_sourcing and self.web_enricher and self.web_enricher.is_available:
            candidates = []
            for i, r in enumerate(results):
                brand = r.get('BRAND_NAME', '')
                mpn = r.get('Mfg_Part_Num', '')
                attr_count = sum(1 for k in r if k.startswith('ATTRIBUTE_LABEL') and r[k])
                conf_str = r.get('CONFIDENCE_SCORE', '0%')
                try:
                    conf = int(conf_str.rstrip('%'))
                except (ValueError, AttributeError):
                    conf = 0
                needs_web = (
                    (conf < 50 or (not brand and attr_count < 2))
                    and attr_count < 5
                    and mpn and len(str(mpn).strip()) > 2
                    and str(mpn).strip() != '-'
                    and i < 20
                )
                if needs_web:
                    candidates.append(i)

            if candidates and progress_callback:
                progress_callback(total, total, f"Phase 2: Web sourcing {len(candidates)} rows...")

            batch_size = 10
            for batch_start in range(0, len(candidates), batch_size):
                batch = candidates[batch_start:batch_start + batch_size]
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {}
                    for i in batch:
                        r = results[i]
                        brand = r.get('BRAND_NAME', '') or r.get('MANUFACTURER_NAME', '')
                        mpn = r.get('Mfg_Part_Num', '')
                        if brand and mpn:
                            fut = executor.submit(self.web_enricher.search_and_scrape, brand, mpn)
                            futures[fut] = i
                    for fut in as_completed(futures):
                        idx = futures[fut]
                        try:
                            ref_url, web_specs = fut.result()
                            if web_specs:
                                for key, val in web_specs.items():
                                    if key.startswith('_'):
                                        continue
                                    found = False
                                    for k in range(1, 51):
                                        lbl = results[idx].get('ATTRIBUTE_LABEL %d' % k, '')
                                        if lbl and lbl.lower() == key.lower():
                                            found = True
                                            break
                                        if not lbl:
                                            results[idx]['ATTRIBUTE_LABEL %d' % k] = key
                                            results[idx]['ATTRIBUTE_VALUE %d' % k] = val
                                            results[idx]['ATTRIBUTE_UOM %d' % k] = ''
                                            break
                                if ref_url:
                                    results[idx]['Ref URL 1'] = ref_url
                                brand = results[idx].get('BRAND_NAME', '')
                                if not brand and 'Brand' in web_specs:
                                    results[idx]['BRAND_NAME'] = web_specs['Brand']
                        except Exception:
                            pass

            for i in candidates:
                results[i]["CONFIDENCE_SCORE"] = f"{self._recalc_confidence(results[i])}%"
                results[i]["NEEDS_REVIEW"] = "Yes" if self._recalc_confidence(results[i]) < 50 else "No"

            if progress_callback:
                progress_callback(total, total, "Phase 2 complete")

        output_df = pd.DataFrame(results)

        all_columns = [
            "MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5",
            "PART_NUMBER", "Dept", "Class", "Fine", "SKU - MY_PART_NUMBER",
            "Mfg_Part_Num", "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf",
            "MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME", "MANUFACTURER_PART_NUMBER",
            "ALTERNATE_PART_NUMBER", "Classpath", "MOBILE_DESC", "INVOICE_DESC",
            "SHORT_DESC", "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION",
        ]
        for i in range(1, 21):
            all_columns.append(f"ITEM_FEATURES_{i}")
        all_columns.extend([
            "With", "Standard/Approvals", "Prop 65", "Application", "Includes", "Product Name",
        ])
        for i in range(1, 51):
            all_columns.append(f"ATTRIBUTE_LABEL {i}")
            all_columns.append(f"ATTRIBUTE_VALUE {i}")
            all_columns.append(f"ATTRIBUTE_UOM {i}")
        all_columns.extend([
            "UPC", "EAN", "GTIN", "UNSPSC", "Warranty", "List Price",
            "Selling Qty", "Selling UOM", "Standard Packaging Information",
            "LENGTH", "LENGTH_UOM", "HEIGHT", "HEIGHT_UOM", "WIDTH", "WIDTH_UOM",
            "WEIGHT", "WEIGHT_UOM", "VOLUME", "VOLUME_UOM",
            "Product Image", "Alternate Image 1", "Alternate Image 2",
            "Alternate Image 3", "Alternate Image 4", "SDS", "SDS_1",
            "Warranty Information", "Catalog", "Specification Sheet",
            "Instruction/Installation Manual", "Service Manual", "Owners/User Manual",
            "Line Drawing", "MTR", "RoHS", "Full Engineering Drawing", "Energy Star Guide",
            "Technical Bulletin", "Submittal", "Compatibility Chart", "Size Chart",
            "Product Label/Insert", "Video Link", "Video Link 1", "Country Of Origin",
            "Discontinued", "Actual Image (Yes/No)",
            "CONFIDENCE_SCORE", "NEEDS_REVIEW", "REVIEW_REASON", "IS_DUPLICATE", "DUPLICATE_OF",
        ])

        for col in all_columns:
            if col not in output_df.columns:
                output_df[col] = ""

        output_df = output_df[all_columns]
        output_df = output_df.fillna("")

        output_df['_mpn_clean'] = output_df['Mfg_Part_Num'].str.strip().str.upper()
        output_df['IS_DUPLICATE'] = output_df.duplicated(subset=['_mpn_clean'], keep='first')
        output_df['DUPLICATE_OF'] = ''
        dup_mask = output_df['IS_DUPLICATE'] == True
        for idx in output_df[dup_mask].index:
            mpn = output_df.at[idx, '_mpn_clean']
            first_idx = output_df[output_df['_mpn_clean'] == mpn].index[0]
            output_df.at[idx, 'DUPLICATE_OF'] = output_df.at[first_idx, 'Mfg_Part_Num']
        output_df['IS_DUPLICATE'] = output_df['IS_DUPLICATE'].map({True: 'True', False: 'False'})
        output_df = output_df.drop(columns=['_mpn_clean'])

        return output_df

    def get_unilog_export(self, enriched_df: pd.DataFrame) -> pd.DataFrame:
        """
        Export enriched data in strict 252-column Unilog format.
        Strips all QA columns (CONFIDENCE_SCORE, NEEDS_REVIEW, etc.)
        """
        UNILOG_252 = [
            'MFR URL', 'Ref URL 1', 'Ref URL 2', 'Ref URL 3', 'Ref URL 4', 'Ref URL 5',
            'PART_NUMBER', 'Dept', 'Class', 'Fine', 'SKU - MY_PART_NUMBER',
            'Mfg_Part_Num', 'Part_Desc', 'E1_Brand', 'Unilog_Brand', 'DIB_Brand',
            'Part_Manuf', 'MANUFACTURER_NAME', 'BRAND_NAME', 'TRADE_NAME',
            'MANUFACTURER_PART_NUMBER', 'ALTERNATE_PART_NUMBER',
            'Classpath', 'MOBILE_DESC', 'INVOICE_DESC', 'SHORT_DESC', 'LONG_DESC1',
            'RETAIL_DESC', 'MARKETING_DESCRIPTION',
        ]
        for i in range(1, 21):
            UNILOG_252.append(f'ITEM_FEATURES_{i}')
        UNILOG_252 += [
            'With', 'Standard/Approvals', 'Prop 65', 'Application', 'Includes', 'Product Name',
        ]
        for i in range(1, 51):
            UNILOG_252 += [f'ATTRIBUTE_LABEL {i}', f'ATTRIBUTE_VALUE {i}', f'ATTRIBUTE_UOM {i}']
        UNILOG_252 += [
            'UPC', 'EAN', 'GTIN', 'UNSPSC', 'Warranty', 'List Price',
            'Selling Qty', 'Selling UOM', 'Standard Packaging Information',
            'LENGTH', 'LENGTH_UOM', 'HEIGHT', 'HEIGHT_UOM',
            'WIDTH', 'WIDTH_UOM', 'WEIGHT', 'WEIGHT_UOM',
            'VOLUME', 'VOLUME_UOM',
            'Product Image', 'Alternate Image 1', 'Alternate Image 2',
            'Alternate Image 3', 'Alternate Image 4',
            'SDS', 'SDS_1', 'Warranty Information', 'Catalog',
            'Specification Sheet', 'Instruction/Installation Manual',
            'Service Manual', 'Owners/User Manual', 'Line Drawing',
            'MTR', 'RoHS', 'Full Engineering Drawing', 'Energy Star Guide',
            'Technical Bulletin', 'Submittal', 'Compatibility Chart', 'Size Chart',
            'Product Label/Insert', 'Video Link', 'Video Link 1',
            'Country Of Origin', 'Discontinued', 'Actual Image (Yes/No)',
        ]
        export_df = enriched_df.copy()
        qa_cols = [c for c in export_df.columns if c not in UNILOG_252]
        export_df = export_df.drop(columns=qa_cols, errors='ignore')
        for col in UNILOG_252:
            if col not in export_df.columns:
                export_df[col] = ''
        export_df = export_df[UNILOG_252].fillna('')
        return export_df


if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Gauri\Downloads\Unihack_ Sample Dataset - Input.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else r"C:\Hackathon\Unilog\output\enriched_output.csv"
    
    # Load input data for learning
    input_df = pd.read_csv(input_file, dtype=str, keep_default_na=False)
    input_data = input_df.to_dict('records')
    
    pipeline = ProductPipeline()
    pipeline.initialize(input_data=input_data)
    pipeline.process_csv(input_file, output_file)
