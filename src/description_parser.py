import re
from math import gcd
from typing import Dict, List, Optional, Tuple, Union


class DescriptionParser:
    """Extracts structured attributes from messy Part_Desc strings."""

    DECIMAL_TO_FRACTION: Dict[str, str] = {
        ".0625": "1/16",
        ".125": "1/8",
        ".1875": "3/16",
        ".25": "1/4",
        ".3125": "5/16",
        ".375": "3/8",
        ".4375": "7/16",
        ".5": "1/2",
        ".5625": "9/16",
        ".625": "5/8",
        ".6875": "11/16",
        ".75": "3/4",
        ".8125": "13/16",
        ".875": "7/8",
        ".9375": "15/16",
    }

    UPPERCASE_ABBREVIATIONS: set = {
        "SS", "LED", "HVAC", "BR", "TBI", "TBIK", "TSC", "TSB", "SKU", "UPC",
        "GFI", "GFCI", "GFC", "AC", "DC", "BTU", "CFM", "RPM", "HP", "MPH",
        "GPH", "PSI", "Hz", "VAC", "AWG", "CAT", "CAT5", "CAT5E", "CAT6",
        "USB", "HDMI", "RCA", "LCD", "OLED", "CFL", "T8", "T12",
        "E26", "E27", "GU10", "MR16", "BR30", "BR40", "PAR20", "PAR30",
        "PAR38", "GU24", "K4", "K5", "K6", "DIY", "LSC", "PVC", "ABS",
        "OSB", "MDF", "Ply", "HDH", "SWR", "MIP", "FIP", "NPT",
        "IPS", "OD", "ID", "RO", "WF", "HVLP", "LX", "SAE", "ISO",
        "ANSI", "UL", "ETL", "CSA", "IPX", "IP65", "IP67", "IP68",
    }

    product_type_keywords: Dict[str, Tuple[str, str, str]] = {
        # Abrasives
        "sanding belt": ("Sanding Belt", "Abrasives", "Abrasives>Belts>Sanding Belts"),
        "belt sander": ("Sanding Belt", "Abrasives", "Abrasives>Belts>Sanding Belts"),
        "sanding disc": ("Sanding Disc", "Abrasives", "Abrasives>Discs>Sanding Discs"),
        "cut off disc": ("Cut Off Disc", "Abrasives", "Abrasives>Discs>Cut Off Discs"),
        "cut-off disc": ("Cut Off Disc", "Abrasives", "Abrasives>Discs>Cut Off Discs"),
        "cut off wheel": ("Cut Off Wheel", "Abrasives", "Abrasives>Wheels>Cut Off Wheels"),
        "cutting disc": ("Cutting Disc", "Abrasives", "Abrasives>Discs>Cutting Discs"),
        "grinding disc": ("Grinding Disc", "Abrasives", "Abrasives>Discs>Grinding Discs"),
        "grinding wheel": ("Grinding Wheel", "Abrasives", "Abrasives>Wheels>Grinding Wheels"),
        "metal grinding": ("Grinding Wheel", "Abrasives", "Abrasives>Wheels>Grinding Wheels"),
        "stikit film": ("Film Disc", "Abrasives", "Abrasives>Discs>Film Discs"),
        "film disc": ("Film Disc", "Abrasives", "Abrasives>Discs>Film Discs"),
        "cubitron": ("Film Disc", "Abrasives", "Abrasives>Discs>Film Discs"),
        "flap disc": ("Flap Disc", "Abrasives", "Abrasives>Discs>Flap Discs"),
        "flap wheel": ("Flap Wheel", "Abrasives", "Abrasives>Wheels>Flap Wheels"),
        "sanding pad": ("Sanding Pad", "Abrasives", "Abrasives>Pads>Sanding Pads"),
        "hook loop": ("Hook and Loop Disc", "Abrasives", "Abrasives>Discs>Hook and Loop Discs"),
        "sponge pad": ("Sanding Sponge", "Abrasives", "Abrasives>Sponges>Sanding Sponges"),
        "sanding sponge": ("Sanding Sponge", "Abrasives", "Abrasives>Sponges>Sanding Sponges"),
        "rolling drum": ("Sanding Drum", "Abrasives", "Abrasives>Drums>Sanding Drums"),
        "sanding drum": ("Sanding Drum", "Abrasives", "Abrasives>Drums>Sanding Drums"),
        "wire brush": ("Wire Brush", "Abrasives", "Abrasives>Brushes>Wire Brushes"),
        "wire wheel": ("Wire Wheel", "Abrasives", "Abrasives>Wheels>Wire Wheels"),
        "abrasive": ("Abrasive", "Abrasives", "Abrasives>General"),
        "polishing pad": ("Polishing Pad", "Abrasives", "Abrasives>Pads>Polishing Pads"),
        "buffing pad": ("Buffing Pad", "Abrasives", "Abrasives>Pads>Buffing Pads"),

        # Appliances
        "dishwasher": ("Dishwasher", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers"),
        "refrigerator": ("Refrigerator", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Refrigerators"),
        "fridge": ("Refrigerator", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Refrigerators"),
        "freezer": ("Freezer", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Freezers"),
        "range": ("Range", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Ranges"),
        "oven": ("Oven", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Ovens"),
        "microwave": ("Microwave", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Microwaves"),
        "washer": ("Washer", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Washers"),
        "dryer": ("Dryer", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Dryers"),
        "water heater": ("Water Heater", "Appliances", "Appliances & Consumer Electronics>Heating & Cooling>Water Heaters"),
        "disposal": ("Garbage Disposal", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Garbage Disposals"),
        "garbage disposal": ("Garbage Disposal", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Garbage Disposals"),
        "range hood": ("Range Hood", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Range Hoods"),
        "cooktop": ("Cooktop", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Cooktops"),
        "wall oven": ("Wall Oven", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Wall Ovens"),
        "compact refrigerator": ("Compact Refrigerator", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Compact Refrigerators"),
        "ice maker": ("Ice Maker", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Ice Makers"),
        "wine cooler": ("Wine Cooler", "Appliances", "Appliances & Consumer Electronics>Kitchen Appliances>Wine Coolers"),

        # Decking
        "decking": ("Decking", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "deck board": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "decking board": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "post sleeve": ("Post Sleeve", "Decking", "Building Materials & Hardscape>Decking>Railing>Post Sleeves"),
        "post cap": ("Post Cap", "Decking", "Building Materials & Hardscape>Decking>Railing>Post Caps"),
        "post skirt": ("Post Skirt", "Decking", "Building Materials & Hardscape>Decking>Railing>Post Skirts"),
        "fascia": ("Fascia", "Decking", "Building Materials & Hardscape>Decking>Fascia"),
        "railing": ("Railing", "Decking", "Building Materials & Hardscape>Decking>Railing"),
        "railing kit": ("Railing Kit", "Decking", "Building Materials & Hardscape>Decking>Railing>Railing Kits"),
        "t-rail kit": ("Railing Kit", "Decking", "Building Materials & Hardscape>Decking>Railing>Railing Kits"),
        "baluster": ("Baluster", "Decking", "Building Materials & Hardscape>Decking>Railing>Balusters"),
        "balusters": ("Baluster", "Decking", "Building Materials & Hardscape>Decking>Railing>Balusters"),
        "deck fastener": ("Deck Fastener", "Decking", "Building Materials & Hardscape>Decking>Fasteners"),
        "deck screws": ("Deck Screws", "Decking", "Building Materials & Hardscape>Decking>Fasteners>Deck Screws"),
        "deck screw": ("Deck Screws", "Decking", "Building Materials & Hardscape>Decking>Fasteners>Deck Screws"),
        "joist": ("Joist", "Decking", "Building Materials & Hardscape>Decking>Structural>Joists"),
        "joist tape": ("Joist Tape", "Decking", "Building Materials & Hardscape>Decking>Structural>Joist Tape"),
        "ledger board": ("Ledger Board", "Decking", "Building Materials & Hardscape>Decking>Structural>Ledger Boards"),
        "tropical": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "composite": ("Composite Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards>Composite"),
        "trex": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "azek": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "timbertech": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "sq edge": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),
        "radius edge": ("Deck Board", "Decking", "Building Materials & Hardscape>Decking>Deck Boards"),

        # Lighting
        "led": ("LED", "Lighting", "Lighting>LED"),
        "bulb": ("Light Bulb", "Lighting", "Lighting>Bulbs"),
        "light bulb": ("Light Bulb", "Lighting", "Lighting>Bulbs"),
        "lamp": ("Lamp", "Lighting", "Lighting>Lamps"),
        "fixture": ("Light Fixture", "Lighting", "Lighting>Fixtures"),
        "ceiling fan": ("Ceiling Fan", "Lighting", "Lighting>Ceiling Fans"),
        "pendant": ("Pendant Light", "Lighting", "Lighting>Fixtures>Pendant Lights"),
        "chandelier": ("Chandelier", "Lighting", "Lighting>Fixtures>Chandeliers"),
        "sconce": ("Wall Sconce", "Lighting", "Lighting>Fixtures>Wall Sconces"),
        "recessed": ("Recessed Light", "Lighting", "Lighting>Fixtures>Recessed Lights"),
        "recessed light": ("Recessed Light", "Lighting", "Lighting>Fixtures>Recessed Lights"),
        "track light": ("Track Light", "Lighting", "Lighting>Fixtures>Track Lights"),
        "under cabinet": ("Under Cabinet Light", "Lighting", "Lighting>Fixtures>Under Cabinet Lights"),
        "flood light": ("Flood Light", "Lighting", "Lighting>Fixtures>Flood Lights"),
        "floodlight": ("Flood Light", "Lighting", "Lighting>Fixtures>Flood Lights"),
        "spot light": ("Spot Light", "Lighting", "Lighting>Fixtures>Spot Lights"),
        "spotlight": ("Spot Light", "Lighting", "Lighting>Fixtures>Spot Lights"),
        "area light": ("Area Light", "Lighting", "Lighting>Fixtures>Area Lights"),
        "wall pack": ("Wall Pack", "Lighting", "Lighting>Fixtures>Wall Packs"),
        "motion sensor": ("Motion Sensor Light", "Lighting", "Lighting>Fixtures>Motion Sensor Lights"),
        "night light": ("Night Light", "Lighting", "Lighting>Fixtures>Night Lights"),
        "emergency light": ("Emergency Light", "Lighting", "Lighting>Fixtures>Emergency Lights"),
        "exit sign": ("Exit Sign", "Lighting", "Lighting>Fixtures>Exit Signs"),
        "step light": ("Step Light", "Lighting", "Lighting>Fixtures>Step Lights"),
        "landscape": ("Landscape Light", "Lighting", "Lighting>Fixtures>Landscape Lights"),
        "path light": ("Path Light", "Lighting", "Lighting>Fixtures>Path Lights"),
        "well light": ("Well Light", "Lighting", "Lighting>Fixtures>Well Lights"),
        "br40": ("BR40 Light", "Lighting", "Lighting>Bulbs>BR40"),
        "br30": ("BR30 Light", "Lighting", "Lighting>Bulbs>BR30"),
        "par38": ("PAR38 Light", "Lighting", "Lighting>Bulbs>PAR38"),
        "par30": ("PAR30 Light", "Lighting", "Lighting>Bulbs>PAR30"),
        "par20": ("PAR20 Light", "Lighting", "Lighting>Bulbs>PAR20"),
        "mr16": ("MR16 Light", "Lighting", "Lighting>Bulbs>MR16"),
        "gu10": ("GU10 Light", "Lighting", "Lighting>Bulbs>GU10"),

        # Electrical
        "outlet": ("Outlet", "Electrical", "Electrical>Outlets"),
        "receptacle": ("Receptacle", "Electrical", "Electrical>Outlets>Receptacles"),
        "switch": ("Switch", "Electrical", "Electrical>Switches"),
        "dimmer": ("Dimmer Switch", "Electrical", "Electrical>Switches>Dimmers"),
        "gfci": ("GFCI Outlet", "Electrical", "Electrical>Outlets>GFCI"),
        "gfi": ("GFCI Outlet", "Electrical", "Electrical>Outlets>GFCI"),
        "breaker": ("Circuit Breaker", "Electrical", "Electrical>Breakers"),
        "panel": ("Electrical Panel", "Electrical", "Electrical>Panels"),
        "fuse": ("Fuse", "Electrical", "Electrical>Fuses"),
        "wire": ("Wire", "Electrical", "Electrical>Wire"),
        "cable": ("Cable", "Electrical", "Electrical>Wire>Cable"),
        "conduit": ("Conduit", "Electrical", "Electrical>Conduit"),
        "cover plate": ("Cover Plate", "Electrical", "Electrical>Cover Plates"),
        "wall plate": ("Wall Plate", "Electrical", "Electrical>Cover Plates"),
        "ceiling fan switch": ("Ceiling Fan Switch", "Electrical", "Electrical>Switches>Ceiling Fan"),
        "timer": ("Timer Switch", "Electrical", "Electrical>Switches>Timers"),
        "occupancy sensor": ("Occupancy Sensor", "Electrical", "Electrical>Sensors>Occupancy"),
        "doorbell": ("Doorbell", "Electrical", "Electrical>Doorbells"),

        # Power Tools
        "drill": ("Drill", "Power Tools", "Power Tools>Drills"),
        "impact driver": ("Impact Driver", "Power Tools", "Power Tools>Drivers>Impact Drivers"),
        "impact wrench": ("Impact Wrench", "Power Tools", "Power Tools>Wrenches>Impact Wrenches"),
        "circular saw": ("Circular Saw", "Power Tools", "Power Tools>Saws>Circular Saws"),
        "reciprocating saw": ("Reciprocating Saw", "Power Tools", "Power Tools>Saws>Reciprocating Saws"),
        "jigsaw": ("Jigsaw", "Power Tools", "Power Tools>Saws>Jigsaws"),
        "miter saw": ("Miter Saw", "Power Tools", "Power Tools>Saws>Miter Saws"),
        "table saw": ("Table Saw", "Power Tools", "Power Tools>Saws>Table Saws"),
        "band saw": ("Band Saw", "Power Tools", "Power Tools>Saws>Band Saws"),
        "scroll saw": ("Scroll Saw", "Power Tools", "Power Tools>Saws>Scroll Saws"),
        "grinder": ("Grinder", "Power Tools", "Power Tools>Grinders"),
        "angle grinder": ("Angle Grinder", "Power Tools", "Power Tools>Grinders>Angle Grinders"),
        "sander": ("Sander", "Power Tools", "Power Tools>Sanders"),
        "orbital sander": ("Orbital Sander", "Power Tools", "Power Tools>Sanders>Orbital"),
        "belt sander": ("Belt Sander", "Power Tools", "Power Tools>Sanders>Belt"),
        "router": ("Router", "Power Tools", "Power Tools>Routers"),
        "planer": ("Planer", "Power Tools", "Power Tools>Planers"),
        "nail gun": ("Nail Gun", "Power Tools", "Power Tools>Nailers"),
        "nailer": ("Nailer", "Power Tools", "Power Tools>Nailers"),
        "brad nailer": ("Brad Nailer", "Power Tools", "Power Tools>Nailers>Brad"),
        "finish nailer": ("Finish Nailer", "Power Tools", "Power Tools>Nailers>Finish"),
        "framing nailer": ("Framing Nailer", "Power Tools", "Power Tools>Nailers>Framing"),
        "stapler": ("Stapler", "Power Tools", "Power Tools>Nailers>Staplers"),
        "rotary tool": ("Rotary Tool", "Power Tools", "Power Tools>Rotary Tools"),
        "oscillating": ("Oscillating Tool", "Power Tools", "Power Tools>Oscillating Tools"),
        "heat gun": ("Heat Gun", "Power Tools", "Power Tools>Heat Guns"),
        "blower": ("Blower", "Power Tools", "Power Tools>Blowers"),
        "chainsaw": ("Chainsaw", "Power Tools", "Power Tools>Chainsaws"),
        "string trimmer": ("String Trimmer", "Power Tools", "Power Tools>Outdoor>String Trimmers"),
        "lawn mower": ("Lawn Mower", "Power Tools", "Power Tools>Outdoor>Lawn Mowers"),
        "leaf blower": ("Leaf Blower", "Power Tools", "Power Tools>Outdoor>Leaf Blowers"),
        "hedge trimmer": ("Hedge Trimmer", "Power Tools", "Power Tools>Outdoor>Hedge Trimmers"),

        # Hand Tools
        "wrench": ("Wrench", "Hand Tools", "Hand Tools>Wrenches"),
        "socket": ("Socket", "Hand Tools", "Hand Tools>Sockets"),
        "ratchet": ("Ratchet", "Hand Tools", "Hand Tools>Ratchets"),
        "screwdriver": ("Screwdriver", "Hand Tools", "Hand Tools>Screwdrivers"),
        "hammer": ("Hammer", "Hand Tools", "Hand Tools>Hammers"),
        "pliers": ("Pliers", "Hand Tools", "Hand Tools>Pliers"),
        "tape measure": ("Tape Measure", "Hand Tools", "Hand Tools>Measuring>Tape Measures"),
        "level": ("Level", "Hand Tools", "Hand Tools>Measuring>Levels"),
        "square": ("Square", "Hand Tools", "Hand Tools>Measuring>Squares"),
        "utility knife": ("Utility Knife", "Hand Tools", "Hand Tools>Knives>Utility"),
        "hacksaw": ("Hacksaw", "Hand Tools", "Hand Tools>Saws>Hacksaws"),
        "hand saw": ("Hand Saw", "Hand Tools", "Hand Tools>Saws>Hand Saws"),
        "file": ("File", "Hand Tools", "Hand Tools>Files"),
        "chisel": ("Chisel", "Hand Tools", "Hand Tools>Chisels"),
        "clamp": ("Clamp", "Hand Tools", "Hand Tools>Clamps"),
        "vise": ("Vise", "Hand Tools", "Hand Tools>Vises"),
        "allen wrench": ("Allen Wrench", "Hand Tools", "Hand Tools>Wrenches>Allen"),
        "hex key": ("Hex Key", "Hand Tools", "Hand Tools>Wrenches>Hex Keys"),
        "torx": ("Torx Driver", "Hand Tools", "Hand Tools>Screwdrivers>Torx"),
        "multimeter": ("Multimeter", "Hand Tools", "Hand Tools>Test Equipment>Multimeters"),
        "stud finder": ("Stud Finder", "Hand Tools", "Hand Tools>Test Equipment>Stud Finders"),

        # Safety
        "safety glasses": ("Safety Glasses", "Safety", "Safety>Eye Protection>Glasses"),
        "goggles": ("Safety Goggles", "Safety", "Safety>Eye Protection>Goggles"),
        "gloves": ("Gloves", "Safety", "Safety>Hand Protection>Gloves"),
        "ear plugs": ("Ear Plugs", "Safety", "Safety>Hearing Protection>Ear Plugs"),
        "ear muffs": ("Ear Muffs", "Safety", "Safety>Hearing Protection>Ear Muffs"),
        "respirator": ("Respirator", "Safety", "Safety>Respiratory>Respirators"),
        "dust mask": ("Dust Mask", "Safety", "Safety>Respiratory>Dust Masks"),
        "hard hat": ("Hard Hat", "Safety", "Safety>Head Protection>Hard Hats"),
        "knee pad": ("Knee Pads", "Safety", "Safety>Body Protection>Knee Pads"),
        "safety vest": ("Safety Vest", "Safety", "Safety>Body Protection>Vests"),
        "fall protection": ("Fall Protection", "Safety", "Safety>Fall Protection"),

        # Windows & Doors
        "window": ("Window", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Windows"),
        "door": ("Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors"),
        "hinge": ("Hinge", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Hardware>Hinges"),
        "doorknob": ("Doorknob", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Hardware>Knobs"),
        "deadbolt": ("Deadbolt", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Hardware>Deadbolts"),
        "lockset": ("Lockset", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Hardware>Locksets"),
        "handle": ("Handle", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Hardware>Handles"),
        "latch": ("Latch", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Hardware>Latches"),
        "weatherstrip": ("Weatherstrip", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Accessories>Weatherstripping"),
        "threshold": ("Threshold", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Accessories>Thresholds"),
        "door stop": ("Door Stop", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Accessories>Door Stops"),
        "sliding door": ("Sliding Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>Sliding"),
        "french door": ("French Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>French"),
        "entry door": ("Entry Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>Entry"),
        "garage door": ("Garage Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>Garage"),

        # Building Materials
        "lumber": ("Lumber", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Lumber"),
        "plywood": ("Plywood", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Plywood"),
        "osb": ("OSB", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>OSB"),
        "drywall": ("Drywall", "Building Materials", "Building Materials & Hardscape>Drywall & Insulation>Drywall"),
        "insulation": ("Insulation", "Building Materials", "Building Materials & Hardscape>Drywall & Insulation>Insulation"),
        "concrete": ("Concrete", "Building Materials", "Building Materials & Hardscape>Concrete & Masonry>Concrete"),
        "mortar": ("Mortar", "Building Materials", "Building Materials & Hardscape>Concrete & Masonry>Mortar"),
        "grout": ("Grout", "Building Materials", "Building Materials & Hardscape>Concrete & Masonry>Grout"),
        "cement": ("Cement", "Building Materials", "Building Materials & Hardscape>Concrete & Masonry>Cement"),
        "adhesive": ("Adhesive", "Building Materials", "Building Materials & Hardscape>Adhesives"),
        "caulk": ("Caulk", "Building Materials", "Building Materials & Hardscape>Caulks & Sealants>Caulks"),
        "silicone": ("Silicone Caulk", "Building Materials", "Building Materials & Hardscape>Caulks & Sealants>Silicone"),
        "sealant": ("Sealant", "Building Materials", "Building Materials & Hardscape>Caulks & Sealants>Sealants"),
        "foam": ("Foam", "Building Materials", "Building Materials & Hardscape>Foam"),
        "furring strip": ("Furring Strip", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Furring Strips"),
        "molding": ("Molding", "Building Materials", "Building Materials & Hardscape>Trim & Moulding>Moulding"),
        "trim": ("Trim", "Building Materials", "Building Materials & Hardscape>Trim & Moulding>Trim"),
        "baseboard": ("Baseboard", "Building Materials", "Building Materials & Hardscape>Trim & Moulding>Baseboards"),
        "crown molding": ("Crown Molding", "Building Materials", "Building Materials & Hardscape>Trim & Moulding>Crown Moulding"),
        "casing": ("Casing", "Building Materials", "Building Materials & Hardscape>Trim & Moulding>Casing"),
        "stud": ("Stud", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Studs"),
        "beam": ("Beam", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Beams"),
        "post": ("Post", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Posts"),

        # Fasteners
        "screw": ("Screw", "Fasteners", "Fasteners>Screws"),
        "bolt": ("Bolt", "Fasteners", "Fasteners>Bolts"),
        "nut": ("Nut", "Fasteners", "Fasteners>Nuts"),
        "washer": ("Washer", "Fasteners", "Fasteners>Washers"),
        "anchor": ("Anchor", "Fasteners", "Fasteners>Anchors"),
        "nail": ("Nail", "Fasteners", "Fasteners>Nails"),
        "rivet": ("Rivet", "Fasteners", "Fasteners>Rivets"),
        "toggle bolt": ("Toggle Bolt", "Fasteners", "Fasteners>Bolts>Toggle"),
        "lag screw": ("Lag Screw", "Fasteners", "Fasteners>Screws>Lag"),
        "wood screw": ("Wood Screw", "Fasteners", "Fasteners>Screws>Wood"),
        "machine screw": ("Machine Screw", "Fasteners", "Fasteners>Screws>Machine"),
        "sheet metal screw": ("Sheet Metal Screw", "Fasteners", "Fasteners>Screws>Sheet Metal"),
        "self tapping": ("Self-Tapping Screw", "Fasteners", "Fasteners>Screws>Self-Tapping"),
        "drywall screw": ("Drywall Screw", "Fasteners", "Fasteners>Screws>Drywall"),
        "concrete screw": ("Concrete Screw", "Fasteners", "Fasteners>Screws>Concrete"),
        "carriage bolt": ("Carriage Bolt", "Fasteners", "Fasteners>Bolts>Carriage"),
        "hex bolt": ("Hex Bolt", "Fasteners", "Fasteners>Bolts>Hex"),
        "eye bolt": ("Eye Bolt", "Fasteners", "Fasteners>Bolts>Eye"),
        "u-bolt": ("U-Bolt", "Fasteners", "Fasteners>Bolts>U-Bolts"),

        # Plumbing
        "faucet": ("Faucet", "Plumbing", "Building Materials & Hardscape>Plumbing>Faucets"),
        "toilet": ("Toilet", "Plumbing", "Building Materials & Hardscape>Plumbing>Toilets"),
        "sink": ("Sink", "Plumbing", "Building Materials & Hardscape>Plumbing>Sinks"),
        "shower": ("Shower", "Plumbing", "Building Materials & Hardscape>Plumbing>Showers"),
        "valve": ("Valve", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves"),
        "pipe": ("Pipe", "Plumbing", "Building Materials & Hardscape>Plumbing>Pipes"),
        "fitting": ("Fitting", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings"),
        "elbow": ("Elbow", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings>Elbows"),
        "tee": ("Tee Fitting", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings>Tees"),
        "coupling": ("Coupling", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings>Couplings"),
        "connector": ("Connector", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings>Connectors"),
        "adapter": ("Adapter", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings>Adapters"),
        "trap": ("Trap", "Plumbing", "Building Materials & Hardscape>Plumbing>Traps"),
        "supply line": ("Supply Line", "Plumbing", "Building Materials & Hardscape>Plumbing>Supply Lines"),
        "flexible connector": ("Flexible Connector", "Plumbing", "Building Materials & Hardscape>Plumbing>Fittings>Flexible Connectors"),
        "ball valve": ("Ball Valve", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves>Ball"),
        "check valve": ("Check Valve", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves>Check"),
        "stop valve": ("Stop Valve", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves>Stop"),
        "angle stop": ("Angle Stop", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves>Angle Stops"),
        "pop-up": ("Pop-Up Drain", "Plumbing", "Building Materials & Hardscape>Plumbing>Drains>Pop-Up"),
        "drain": ("Drain", "Plumbing", "Building Materials & Hardscape>Plumbing>Drains"),
        "overflow": ("Overflow Drain", "Plumbing", "Building Materials & Hardscape>Plumbing>Drains>Overflow"),
        "flush valve": ("Flush Valve", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves>Flush"),
        "fill valve": ("Fill Valve", "Plumbing", "Building Materials & Hardscape>Plumbing>Valves>Fill"),
        "flush handle": ("Flush Handle", "Plumbing", "Building Materials & Hardscape>Plumbing>Toilet Parts>Flush Handles"),
        "wax ring": ("Wax Ring", "Plumbing", "Building Materials & Hardscape>Plumbing>Toilet Parts>Wax Rings"),
        "toilet seat": ("Toilet Seat", "Plumbing", "Building Materials & Hardscape>Plumbing>Toilet Parts>Seats"),

        # Fans
        "exhaust fan": ("Exhaust Fan", "Fans", "Fans>Exhaust Fans"),
        "bath fan": ("Bathroom Exhaust Fan", "Fans", "Fans>Exhaust Fans>Bathroom"),
        "range hood fan": ("Range Hood Fan", "Fans", "Fans>Range Hood Fans"),
        "inline fan": ("Inline Fan", "Fans", "Fans>Inline Fans"),
        "vent fan": ("Ventilation Fan", "Fans", "Fans>Ventilation"),
        "attic fan": ("Attic Fan", "Fans", "Fans>Attic Fans"),
        "whole house fan": ("Whole House Fan", "Fans", "Fans>Whole House"),
        "tower fan": ("Tower Fan", "Fans", "Fans>Portable>Tower"),
        "box fan": ("Box Fan", "Fans", "Fans>Portable>Box"),
        "pedestal fan": ("Pedestal Fan", "Fans", "Fans>Portable>Pedestal"),
        "desk fan": ("Desk Fan", "Fans", "Fans>Portable>Desk"),
        "industrial fan": ("Industrial Fan", "Fans", "Fans>Industrial"),
        
        # Additional keywords for better classification
        "cut and grind": ("Cut and Grind Disc", "Abrasives", "Abrasives>Discs>Cut Off Discs"),
        "dual metal": ("Cut and Grind Disc", "Abrasives", "Abrasives>Discs>Cut Off Discs"),
        "perform+": ("Cut and Grind Disc", "Abrasives", "Abrasives>Discs>Cut Off Discs"),
        "hicolit": ("Sanding Belt", "Abrasives", "Abrasives>Belts>Sanding Belts"),
        "hiolit": ("Sanding Belt", "Abrasives", "Abrasives>Belts>Sanding Belts"),
        "abranet": ("Sanding Belt", "Abrasives", "Abrasives>Belts>Sanding Belts"),
        "vinyl tape": ("Vinyl Tape", "Electrical", "Electrical>Wire>Tape"),
        "elect tape": ("Electrical Tape", "Electrical", "Electrical>Wire>Tape"),
        "emseal": ("Sealant Tape", "Building Materials", "Building Materials & Hardscape>Caulks & Sealants>Sealants"),
        "heater kit": ("Heater Kit", "Appliances", "Appliances & Consumer Electronics>Heating & Cooling>Heaters"),
        "laundry center": ("Laundry Center", "Appliances", "Appliances & Consumer Electronics>Laundry>Laundry Centers"),
        "kneeling pad": ("Knee Pads", "Safety", "Safety>Body Protection>Knee Pads"),
        "tire pressure": ("Tire Gauge", "Automotive", "Automotive>Tire>Accessories"),
        "inflator": ("Tire Inflator", "Automotive", "Automotive>Tire>Accessories"),
        "rail kit": ("Railing Kit", "Decking", "Building Materials & Hardscape>Decking>Railing>Railing Kits"),
        "rail": ("Railing", "Decking", "Building Materials & Hardscape>Decking>Railing"),
        "finyline": ("Railing Kit", "Decking", "Building Materials & Hardscape>Decking>Railing>Railing Kits"),
        "gate": ("Gate", "Decking", "Building Materials & Hardscape>Decking>Railing>Gates"),
        "baluster": ("Baluster", "Decking", "Building Materials & Hardscape>Decking>Railing>Balusters"),
        "led strip": ("LED Strip", "Lighting", "Lighting>LED>Strips"),
        "tape light": ("LED Strip", "Lighting", "Lighting>LED>Strips"),
        "under cabinet": ("Under Cabinet Light", "Lighting", "Lighting>Fixtures>Under Cabinet Lights"),
        "puck light": ("Puck Light", "Lighting", "Lighting>Fixtures>Puck Lights"),
        "night light": ("Night Light", "Lighting", "Lighting>Fixtures>Night Lights"),
        "step light": ("Step Light", "Lighting", "Lighting>Fixtures>Step Lights"),
        "path light": ("Path Light", "Lighting", "Lighting>Fixtures>Path Lights"),
        "landscape": ("Landscape Light", "Lighting", "Lighting>Fixtures>Landscape Lights"),
        "spot light": ("Spot Light", "Lighting", "Lighting>Fixtures>Spot Lights"),
        "flood light": ("Flood Light", "Lighting", "Lighting>Fixtures>Flood Lights"),
        "wall pack": ("Wall Pack", "Lighting", "Lighting>Fixtures>Wall Packs"),
        "area light": ("Area Light", "Lighting", "Lighting>Fixtures>Area Lights"),
        "patio door": ("Patio Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>Patio"),
        "gliding patio": ("Patio Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>Patio"),
        "sliding patio": ("Patio Door", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Doors>Patio"),
        "skylight": ("Skylight", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Skylights"),
        "skylt": ("Skylight", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Skylights"),
        "basement window": ("Basement Window", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Windows>Basement"),
        "bsmt": ("Basement Window", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Windows>Basement"),
        "hopper": ("Hopper Window", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Windows>Hopper"),
        "ecolite": ("Basement Window", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Windows>Basement"),
        "slider": ("Sliding Window", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Windows>Sliding"),
        "metal roof": ("Metal Roof Panel", "Building Materials", "Building Materials & Hardscape>Roofing>Metal Panels"),
        "roof panel": ("Roof Panel", "Building Materials", "Building Materials & Hardscape>Roofing>Panels"),
        "rib": ("Metal Roof Panel", "Building Materials", "Building Materials & Hardscape>Roofing>Metal Panels"),
        "rainscreen": ("Rainscreen", "Building Materials", "Building Materials & Hardscape>Building Envelope>Rainscreen"),
        "zip system": ("Sheathing", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Sheathing"),
        "doug fir": ("Lumber", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Lumber"),
        "sub floor": ("Subfloor", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Subfloor"),
        "subfloor": ("Subfloor", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Subfloor"),
        "t&g": ("Tongue and Groove", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Sheathing"),
        "tongue and groove": ("Tongue and Groove", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Sheathing"),
        "so cord": ("Wire", "Electrical", "Electrical>Wire"),
        "cord": ("Wire", "Electrical", "Electrical>Wire"),
        "jumpstart": ("Power Supply", "Electrical", "Electrical>Power Supplies"),
        "power supply": ("Power Supply", "Electrical", "Electrical>Power Supplies"),
        "phone holster": ("Phone Case", "Safety", "Safety>Body Protection>Phone Cases"),
        "holster": ("Tool Holster", "Hand Tools", "Hand Tools>Accessories>Holsters"),
        "leather": ("Leather", "Building Materials", "Building Materials & Hardscape>General"),
        "weathr": ("Weatherstrip", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Accessories>Weatherstripping"),
        "weather": ("Weatherstrip", "Windows & Doors", "Building Materials & Hardscape>Windows & Doors>Accessories>Weatherstripping"),
        "ice guard": ("Ice Guard", "Building Materials", "Building Materials & Hardscape>Roofing>Ice & Water"),
        "hole drilling": ("Hole Saw", "Power Tools", "Power Tools>Drill Bits>Hole Saws"),
        "disc": ("Sanding Disc", "Abrasives", "Abrasives>Discs>Sanding Discs"),
        "flashlight": ("Flashlight", "Lighting", "Lighting>Flashlights"),
        "flash light": ("Flashlight", "Lighting", "Lighting>Flashlights"),
        "flash lt": ("Flashlight", "Lighting", "Lighting>Flashlights"),
        "flashlt": ("Flashlight", "Lighting", "Lighting>Flashlights"),
        "slyde king": ("Flashlight", "Lighting", "Lighting>Flashlights"),
        "headlamp": ("Headlamp", "Lighting", "Lighting>Headlamps"),
        "headlight": ("Headlamp", "Lighting", "Lighting>Headlamps"),
        "battery": ("Battery", "Power Tools", "Power Tools>Batteries & Chargers"),
        "charger": ("Charger", "Power Tools", "Power Tools>Batteries & Chargers"),
        "speaker": ("Speaker", "Appliances", "Appliances & Consumer Electronics>Electronics>Speakers"),
        "planer": ("Planer", "Power Tools", "Power Tools>Planers"),
        "fire extinguisher": ("Fire Extinguisher", "Safety", "Safety>Fire Extinguishers"),
        "smoke alarm": ("Smoke Detector", "Safety", "Safety>Smoke Detectors"),
        "smoke & co": ("Smoke/CO Detector", "Safety", "Safety>Smoke Detectors"),
        "heated hoodie": ("Heated Apparel", "Safety", "Safety>Body Protection>Heated Apparel"),
        "heated gear": ("Heated Apparel", "Safety", "Safety>Body Protection>Heated Apparel"),
        "mason line": ("Mason Line", "Hand Tools", "Hand Tools>Measuring>Line"),
        "rafter square": ("Rafter Square", "Hand Tools", "Hand Tools>Measuring>Squares"),
        "plug cutter": ("Plug Cutter", "Power Tools", "Power Tools>Drill Bits"),
        "drive bit": ("Driver Bit", "Power Tools", "Power Tools>Drill Bits"),
        "phillips": ("Phillips Bit", "Power Tools", "Power Tools>Drill Bits"),
        "torx": ("Torx Bit", "Power Tools", "Power Tools>Drill Bits"),
        "hole saw": ("Hole Saw", "Power Tools", "Power Tools>Drill Bits>Hole Saws"),
        "hole dozer": ("Hole Saw", "Power Tools", "Power Tools>Drill Bits>Hole Saws"),
        "tile blade": ("Tile Blade", "Power Tools", "Power Tools>Saws>Blades"),
        "framing blade": ("Framing Blade", "Power Tools", "Power Tools>Saws>Blades"),
        "diamond blade": ("Diamond Blade", "Power Tools", "Power Tools>Saws>Blades"),
        "ratchet": ("Ratchet", "Hand Tools", "Hand Tools>Ratchets"),
        "universal joint": ("Universal Joint", "Hand Tools", "Hand Tools>Wrenches"),
        "voltage detector": ("Voltage Detector", "Hand Tools", "Hand Tools>Test Equipment"),
        "shears": ("Shears", "Power Tools", "Power Tools>Shears"),
        "pruning": ("Pruning Shears", "Power Tools", "Power Tools>Shears"),
        "cover plate": ("Cover Plate", "Electrical", "Electrical>Cover Plates"),
        "decor plate": ("Decor Plate", "Electrical", "Electrical>Cover Plates"),
        "load center": ("Load Center", "Electrical", "Electrical>Load Centers"),
        "load cntr": ("Load Center", "Electrical", "Electrical>Load Centers"),
        "welder outlet": ("Welder Outlet", "Electrical", "Electrical>Outlets"),
        "heater kit": ("Heater Kit", "Appliances", "Appliances & Consumer Electronics>Heating & Cooling>Heaters"),
        "insulated r-sheathing": ("Insulated Sheathing", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Sheathing"),
        "r-sheathing": ("Insulated Sheathing", "Building Materials", "Building Materials & Hardscape>Lumber & Sheathing>Sheathing"),
        "table assembly": ("Table Assembly", "Power Tools", "Power Tools>Table Saws"),
        "organizer": ("Organizer", "Hand Tools", "Hand Tools>Storage"),
        "mechanical pencil": ("Mechanical Pencil", "Hand Tools", "Hand Tools>Measuring>Pencils"),
        "starter kit": ("Starter Kit", "Power Tools", "Power Tools>Batteries & Chargers"),
        "pencil": ("Pencil", "Hand Tools", "Hand Tools>Measuring>Pencils"),
    }

    material_keywords: Dict[str, str] = {
        "SS": "Stainless Steel",
        "Stl": "Steel",
        "Stainless": "Stainless Steel",
        "Stainless Stl": "Stainless Steel",
        "Alum": "Aluminum",
        "Al": "Aluminum",
        "Brass": "Brass",
        "Cu": "Copper",
        "Copper": "Copper",
        "Bronze": "Bronze",
        "Zinc": "Zinc",
        "Plastic": "Plastic",
        "Nylon": "Nylon",
        "PVC": "PVC",
        "ABS": "ABS",
        "Poly": "Polyethylene",
        "Polypropylene": "Polypropylene",
        "Rubber": "Rubber",
        "Neoprene": "Neoprene",
        "Silicone": "Silicone",
        "Fiberglass": "Fiberglass",
        "Glass": "Glass",
        "Ceramic": "Ceramic",
        "Porcelain": "Porcelain",
        "Concrete": "Concrete",
        "Wood": "Wood",
        "Oak": "Oak",
        "Pine": "Pine",
        "Cedar": "Cedar",
        "Redwood": "Redwood",
        "Teak": "Teak",
        "Composite": "Composite",
        "WPC": "Wood-Plastic Composite",
        "Vinyl": "Vinyl",
        "Fiber Cement": "Fiber Cement",
        "Cast Iron": "Cast Iron",
        "CI": "Cast Iron",
        "Galv": "Galvanized",
        "Galvanized": "Galvanized",
        "Zinc Plated": "Zinc Plated",
        "Zinc-Plated": "Zinc Plated",
        "Chrome": "Chrome",
        "Nickel": "Nickel",
        "Powder Coated": "Powder Coated",
        "Anodized": "Anodized",
        "Black Oxide": "Black Oxide",
        "Copper Clad": "Copper Clad",
        "Tinned": "Tinned",
        "PEX": "PEX",
        "CPVC": "CPVC",
        "HDPE": "High-Density Polyethylene",
        "LDPE": "Low-Density Polyethylene",
        "EPDM": "EPDM Rubber",
        "TPE": "Thermoplastic Elastomer",
        "Polycarbonate": "Polycarbonate",
        "Lexan": "Polycarbonate",
        "Acrylic": "Acrylic",
    }

    color_keywords: Dict[str, str] = {
        "Wh": "White",
        "White": "White",
        "Bk": "Black",
        "Black": "Black",
        "Blk": "Black",
        "Bl": "Blue",
        "Blue": "Blue",
        "Navy": "Navy",
        "Lt Bl": "Light Blue",
        "Dk Bl": "Dark Blue",
        "Rd": "Red",
        "Red": "Red",
        "Gr": "Green",
        "Green": "Green",
        "Dk Grn": "Dark Green",
        "Lt Grn": "Light Green",
        "Gray": "Gray",
        "Grey": "Gray",
        "Gry": "Gray",
        "SS": "Stainless Steel",
        "S/S": "Stainless Steel",
        "Stl": "Steel",
        "Stainless": "Stainless Steel",
        "BSS": "Black Stainless Steel",
        "Black Stainless": "Black Stainless Steel",
        "DG": "Dark Gray",
        "BO": "Bisque",
        "Bisque": "Bisque",
        "Sl": "Slate",
        "Slate": "Slate",
        "Platinum": "Platinum",
        "Graphite": "Graphite",
        "PR": "Panel Ready",
        "Panel Ready": "Panel Ready",
        "YLW": "Yellow",
        "YL": "Yellow",
        "Silver": "Silver",
        "Slv": "Silver",
        "YL": "Yellow",
        "Yellow": "Yellow",
        "Or": "Orange",
        "Orange": "Orange",
        "Pr": "Purple",
        "Purple": "Purple",
        "Violet": "Violet",
        "Pk": "Pink",
        "Pink": "Pink",
        "Brown": "Brown",
        "Brn": "Brown",
        "Tan": "Tan",
        "Beige": "Beige",
        "Ivory": "Ivory",
        "Cream": "Cream",
        "Copper": "Copper",
        "Cpr": "Copper",
        "Bronze": "Bronze",
        "Brz": "Bronze",
        "Gold": "Gold",
        "Natural": "Natural",
        "Nat": "Natural",
        "Clear": "Clear",
        "Clr": "Clear",
        "Sand": "Sand",
        "Tide Pool": "Tide Pool",
        "Tidepool": "Tide Pool",
        "Rustic": "Rustic",
        "Walnut": "Walnut",
        "Mahogany": "Mahogany",
        "Espresso": "Espresso",
        "Charcoal": "Charcoal",
        "Slate": "Slate",
        "Stone": "Stone",
        "Clay": "Clay",
        "Terracotta": "Terracotta",
        "Rust": "Rust",
        "Oxide": "Oxide",
        "Matte": "Matte",
        "Satin": "Satin",
        "Gloss": "Gloss",
        "Semi-Gloss": "Semi-Gloss",
    }

    known_brands: Dict[str, str] = {
        "diablo": "Diablo",
        "milwaukee": "Milwaukee",
        "milw": "Milwaukee",
        "makita": "Makita",
        "dewalt": "DeWalt",
        "dew": "DeWalt",
        "bosch": "Bosch",
        "ryobi": "Ryobi",
        "ridgid": "Ridgid",
        "rigid": "Ridgid",
        "craftsman": "Craftsman",
        "kobalt": "Kobalt",
        "husky": "Husky",
        "stanley": "Stanley",
        "irwin": "Irwin",
        "lenox": "Lenox",
        "starrett": "Starrett",
        "estwing": "Estwing",
        "channellock": "Channellock",
        "klein": "Klein",
        "southwire": "Southwire",
        "leviton": "Leviton",
        "lutron": "Lutron",
        "siemens": "Siemens",
        "square d": "Square D",
        "philips": "Philips",
        "cree": "Cree",
        "feit": "Feit",
        "sylvania": "Sylvania",
        "ge": "GE",
        "trex": "Trex",
        "azek": "AZEK",
        "timbertech": "TimberTech",
        "fiberon": "Fiberon",
        "deckorators": "Deckorators",
        "gemini": "Gemini",
        "symple": "Symple",
        "national": "National Hardware",
        "hillman": "Hillman",
        "everbilt": "Everbilt",
        "gorilla": "Gorilla",
        "loctite": "Loctite",
        "3m": "3M",
        "pace": "Pace",
        "lincoln": "Lincoln Electric",
        "hobart": "Hobart",
        "eastwood": "Eastwood",
        "festool": "Festool",
        "hitachi": "Hitachi",
        "hikoki": "HiKoki",
        "metabo": "Metabo",
        "porter cable": "Porter-Cable",
        "porter-cable": "Porter-Cable",
        "delta": "Delta",
        "jet": "Jet",
        "grizzly": "Grizzly",
        "sharkbite": "SharkBite",
        "shark bite": "SharkBite",
        "oatey": "Oatey",
        "watts": "Watts",
        "symmons": "Symmons",
        "moen": "Moen",
        "delta faucets": "Delta Faucets",
        "kohler": "Kohler",
        "toto": "Toto",
        "american standard": "American Standard",
        "gerber": "Gerber",
        "aquasource": "AquaSource",
        "pfister": "Pfister",
        "peerless": "Peerless",
        "grohe": "Grohe",
        "hansgrohe": "Hansgrohe",
    }

    _NUM_PAT = r'(?:\d+\.?\d*|\.\d+)(?:/\d+)?'
    _QUOTE_SEP = r'["\u201d\u2019\'\s]*[xX\u00d7\u00d8]["\u201d\u2019\'\s]*'

    DIMENSION_PATTERN = re.compile(
        r'(' + _NUM_PAT + r')'
        + _QUOTE_SEP
        + r'(' + _NUM_PAT + r')'
        + r'(?:' + _QUOTE_SEP + r'(' + _NUM_PAT + r'))?'
    )

    SINGLE_DIM_PATTERN = re.compile(
        r'(' + _NUM_PAT + r')(?:\s+|(?<=\d)|(?<="))'
        r'(in(?:ch(?:es)?)?|"|\'\'|\'|ft|feet|mm|cm)\b',
        re.IGNORECASE
    )

    # Pattern for lumber dimensions like "1nx6" (means 1x6)
    LUMBER_DIM_PATTERN = re.compile(
        r'(\d+)n[xX](\d+)'
    )

    FRACTION_PATTERN = re.compile(r'(\d+)\s*/\s*(\d+)')

    QUANTITY_PATTERN = re.compile(
        r'(\d+)\s*(?:Pack|Box|Box/|Carton|Pair|Set|Roll|Case|Sheet|Disc)\b',
        re.IGNORECASE
    )

    GRIT_PATTERN = re.compile(
        r'(?:#\s*)?(\d{1,4})\s*[-]?\s*grit\b|(?:P|GRIT)\s*(\d{1,4})\b',
        re.IGNORECASE
    )

    WATTAGE_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*[Ww](?:\b|att)',
        re.IGNORECASE
    )

    VOLTAGE_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*[Vv](?:\b|olt(?:s)?)',
        re.IGNORECASE
    )

    AMPERAGE_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*[Aa](?:\b|mp(?:s)?)',
        re.IGNORECASE
    )

    COLOR_TEMP_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*[Kk]\b',
        re.IGNORECASE
    )

    LUMEN_PATTERN = re.compile(
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*[Ll](?:m(?:en)?)?\b',
        re.IGNORECASE
    )

    def __init__(self) -> None:
        self._brand_patterns = [
            (re.compile(r'\b' + re.escape(brand_key) + r'\b'), brand_name)
            for brand_key, brand_name in self.known_brands.items()
        ]
        self._product_type_single_word = [
            (re.compile(r'\b' + re.escape(keyword) + r'\b'), value)
            for keyword, value in self.product_type_keywords.items()
            if " " not in keyword
        ]
        self._material_patterns = []
        for abbr, full_name in self.material_keywords.items():
            if len(abbr) <= 2:
                self._material_patterns.append((re.compile(r'\b' + re.escape(abbr.lower()) + r'\b', re.IGNORECASE), full_name, True))
            else:
                self._material_patterns.append((None, full_name, False))
        self._color_patterns = []
        for abbr, full_name in self.color_keywords.items():
            if len(abbr) > 2:
                self._color_patterns.append((None, full_name, False))
            else:
                self._color_patterns.append((re.compile(r'\b' + re.escape(abbr) + r'\b', re.IGNORECASE), full_name, True))
        self._series_patterns = [
            re.compile(r'series\s+([\w\-]+)', re.IGNORECASE),
            re.compile(r'([\w\-]+)\s+series', re.IGNORECASE),
            re.compile(r'#\s*([\w\-]+)', re.IGNORECASE),
            re.compile(r'(Cubitron\s*(?:I{1,3}|IV|V)?)', re.IGNORECASE),
            re.compile(r'(Stikit)', re.IGNORECASE),
            re.compile(r'(HIOLIT)', re.IGNORECASE),
            re.compile(r'(Abranet)', re.IGNORECASE),
            re.compile(r'(Perform\+?)', re.IGNORECASE),
            re.compile(r'(\d{3,4}[A-Z])\s+(?:Stikit|Film|Disc|Grit)', re.IGNORECASE),
        ]

    def normalize_dimensions(self, value_str: str, unit_str: str) -> str:
        normalized_value = value_str.strip()

        if "/" in normalized_value:
            match = self.FRACTION_PATTERN.match(normalized_value)
            if match:
                numerator, denominator = match.group(1), match.group(2)
                normalized_value = f"{numerator}/{denominator}"
        else:
            try:
                decimal_val = float(normalized_value)
                sixteenths = round(decimal_val * 16)
                if sixteenths > 0 and sixteenths % 1 == 0:
                    sixteenths = int(sixteenths)
                    common = gcd(sixteenths, 16)
                    num = sixteenths // common
                    den = 16 // common
                    if den == 1:
                        normalized_value = str(num)
                    else:
                        normalized_value = f"{num}/{den}"
                else:
                    normalized_value = str(decimal_val)
            except ValueError:
                pass

        unit_map = {
            '"': "in",
            "''": "in",
            "in": "in",
            "inch": "in",
            "inches": "in",
            "'": "ft",
            "ft": "ft",
            "feet": "ft",
            "mm": "mm",
            "cm": "cm",
            "m": "m",
        }
        unit_lower = unit_str.lower().strip()
        normalized_unit = unit_map.get(unit_lower, unit_lower)

        return f"{normalized_value} {normalized_unit}"

    def title_case_preserve(self, text: str) -> str:
        words = text.split()
        result = []
        for word in words:
            upper_word = word.upper()
            if upper_word in self.UPPERCASE_ABBREVIATIONS:
                result.append(upper_word)
            elif word.lower() in ("x", "by"):
                result.append(word.lower())
            else:
                result.append(word.capitalize())
        return " ".join(result)

    def _detect_brand_in_desc(self, part_desc: str, brand_info: Optional[str] = None) -> str:
        desc_lower = part_desc.lower()

        if brand_info:
            bi_lower = brand_info.lower().strip()
            for brand_key in self.known_brands:
                if brand_key == bi_lower:
                    return self.known_brands[brand_key]

        for pattern, brand_name in self._brand_patterns:
            if pattern.search(desc_lower):
                return brand_name

        return ""

    def _detect_product_type(self, part_desc: str) -> Tuple[str, str, str]:
        desc_lower = part_desc.lower()

        multi_word_matches = []
        for keyword, value in self.product_type_keywords.items():
            if " " in keyword and keyword in desc_lower:
                multi_word_matches.append((keyword, value))

        if multi_word_matches:
            multi_word_matches.sort(key=lambda x: len(x[0]), reverse=True)
            return multi_word_matches[0][1]

        for pattern, value in self._product_type_single_word:
            if pattern.search(desc_lower):
                return value

        return ("", "General", "General")

    def _extract_dimensions(self, part_desc: str) -> Tuple[Dict[str, str], str]:
        dims = {}
        raw_dims = ""

        # Try x-separated dimensions first: 1/2"x18", 5"x.045"x7/8"
        dim_match = self.DIMENSION_PATTERN.search(part_desc)
        if dim_match:
            raw_dims = dim_match.group(0).strip()
            groups = [g for g in dim_match.groups() if g is not None]

            unit_key = "in"
            if "'" in raw_dims or "ft" in raw_dims.lower() or "feet" in raw_dims.lower():
                unit_key = "ft"

            if len(groups) == 1:
                value = groups[0]
                if "/" in value:
                    dims["diameter"] = self.normalize_dimensions(value, unit_key)
                else:
                    dims["width"] = self.normalize_dimensions(value, unit_key)
            elif len(groups) == 2:
                dims["width"] = self.normalize_dimensions(groups[0], unit_key)
                dims["length"] = self.normalize_dimensions(groups[1], unit_key)
            elif len(groups) >= 3:
                dims["width"] = self.normalize_dimensions(groups[0], unit_key)
                dims["length"] = self.normalize_dimensions(groups[1], unit_key)
                dims["height"] = self.normalize_dimensions(groups[2], unit_key)

        # Try lumber dimensions like "1nx6" (means 1x6)
        if not dims:
            lumber_match = self.LUMBER_DIM_PATTERN.search(part_desc)
            if lumber_match:
                raw_dims = lumber_match.group(0).strip()
                dims["width"] = self.normalize_dimensions(lumber_match.group(1), "in")
                dims["length"] = self.normalize_dimensions(lumber_match.group(2), "in")

        # Try single dimension patterns like 8', 5", etc.
        if not dims:
            single_matches = list(self.SINGLE_DIM_PATTERN.finditer(part_desc))
            if len(single_matches) == 1:
                m = single_matches[0]
                val = m.group(1)
                unit_raw = m.group(2)
                if unit_raw in ("'", "ft", "feet"):
                    unit_key = "ft"
                else:
                    unit_key = "in"
                dims["length"] = self.normalize_dimensions(val, unit_key)
                raw_dims = m.group(0).strip()
            elif len(single_matches) >= 2:
                for i, m in enumerate(single_matches):
                    val = m.group(1)
                    unit_raw = m.group(2)
                    if unit_raw in ("'", "ft", "feet"):
                        unit_key = "ft"
                    else:
                        unit_key = "in"
                    if i == 0:
                        dims["width"] = self.normalize_dimensions(val, unit_key)
                    elif i == 1:
                        dims["length"] = self.normalize_dimensions(val, unit_key)
                    elif i == 2:
                        dims["height"] = self.normalize_dimensions(val, unit_key)
                raw_dims = " x ".join(m.group(0) for m in single_matches)

        return dims, raw_dims

    def _extract_quantity(self, part_desc: str) -> Optional[int]:
        match = self.QUANTITY_PATTERN.search(part_desc)
        if match:
            return int(match.group(1))
        return None

    def _extract_grit(self, part_desc: str) -> Optional[str]:
        match = self.GRIT_PATTERN.search(part_desc)
        if match:
            return match.group(1) or match.group(2)
        return None

    def _extract_material(self, part_desc: str) -> Optional[str]:
        desc_lower = part_desc.lower()
        for pattern, full_name, use_regex in self._material_patterns:
            if use_regex and pattern.search(desc_lower):
                return full_name
        for abbr, full_name in self.material_keywords.items():
            if len(abbr) > 2 and abbr.lower() in desc_lower:
                return full_name
        return None

    def _extract_color(self, part_desc: str) -> Optional[str]:
        desc_lower = part_desc.lower()
        # Check short abbreviations first (SS, BSS, Bk, Wh, DG, BO, etc.)
        for pattern, full_name, use_regex in self._color_patterns:
            if use_regex and pattern.search(part_desc):
                return full_name
        # Then check full words and longer abbreviations (use word boundary)
        for abbr, full_name in self.color_keywords.items():
            if len(abbr) > 2:
                import re as _re
                if _re.search(r'\b' + _re.escape(abbr.lower()) + r'\b', desc_lower):
                    return full_name
        return None

    def _extract_wattage(self, part_desc: str) -> Optional[str]:
        match = self.WATTAGE_PATTERN.search(part_desc)
        if match:
            return match.group(0).strip()
        return None

    def _extract_voltage(self, part_desc: str) -> Optional[str]:
        match = self.VOLTAGE_PATTERN.search(part_desc)
        if match:
            return match.group(0).strip()
        return None

    def _extract_amperage(self, part_desc: str) -> Optional[str]:
        match = self.AMPERAGE_PATTERN.search(part_desc)
        if match:
            return match.group(0).strip()
        return None

    def _extract_color_temp(self, part_desc: str) -> Optional[str]:
        match = self.COLOR_TEMP_PATTERN.search(part_desc)
        if match:
            value = match.group(1)
            try:
                temp = float(value)
                if temp < 100:
                    return f"{int(temp)}K"
                return f"{int(temp)}K"
            except ValueError:
                return match.group(0).strip()
        return None

    def _extract_series(self, part_desc: str) -> Optional[str]:
        for pattern in self._series_patterns:
            match = pattern.search(part_desc)
            if match:
                return match.group(1)
        return None

    def _extract_features(self, part_desc: str) -> List[str]:
        features = []
        feature_keywords = [
            "rechargeable", "cordless", "corded", "brushless", "brushed",
            "LED", "LCD", "digital", "analog", "smart", "wifi", "bluetooth",
            "waterproof", "water resistant", "weather resistant", "rust resistant",
            "anti-vibration", "ergonomic", "lightweight", "heavy duty",
            "quick change", "quick-release", "tool-free", "adjustable",
            "variable speed", "multi-speed", "reversible", "lock-on",
            "diamond", "carbide", "tungsten", "ceramic", "hss",
            "wet/dry", "wet or dry", "dry use", "wet use",
            "anti-kickback", "spindle lock", "dust collection", "vacuum ready",
            "fuel gage", "battery indicator", "charge indicator",
            "impact rated", "impact resistant", "shock resistant",
            "rated for", "UL listed", "ETL listed", "CSA certified",
            "energy star", "dimmable", "non-dimmable",
        ]
        desc_lower = part_desc.lower()
        for feature in feature_keywords:
            if feature.lower() in desc_lower:
                features.append(self.title_case_preserve(feature))
        return features

    def parse(self, mpn: str, part_desc: str, brand_info: Optional[str] = None) -> Dict[str, Union[str, int, None, List[str], Dict[str, str]]]:
        brand_in_desc = self._detect_brand_in_desc(part_desc, brand_info)
        product_type, category, classpath = self._detect_product_type(part_desc)
        dimensions, raw_dimensions = self._extract_dimensions(part_desc)
        quantity = self._extract_quantity(part_desc)
        grit = self._extract_grit(part_desc)
        material = self._extract_material(part_desc)
        color = self._extract_color(part_desc)
        wattage = self._extract_wattage(part_desc)
        voltage = self._extract_voltage(part_desc)
        amperage = self._extract_amperage(part_desc)
        color_temp = self._extract_color_temp(part_desc)
        series = self._extract_series(part_desc)
        features = self._extract_features(part_desc)

        return {
            "brand_in_desc": brand_in_desc,
            "product_type": product_type,
            "category": category,
            "classpath": classpath,
            "dimensions": dimensions,
            "quantity": quantity,
            "grit": grit,
            "material": material,
            "color": color,
            "wattage": wattage,
            "voltage": voltage,
            "amperage": amperage,
            "color_temp": color_temp,
            "series": series,
            "features": features,
            "raw_dimensions": raw_dimensions,
        }
