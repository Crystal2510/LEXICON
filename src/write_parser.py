#!/usr/bin/env python3
"""Script to generate description_parser.py"""

import os

FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "description_parser.py")

content = r'''import re
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
        "sanding belt": ("Sanding Belt", "Abrasives", "Abrasives > Belts > Sanding Belts"),
        "belt sander": ("Sanding Belt", "Abrasives", "Abrasives > Belts > Sanding Belts"),
        "sanding disc": ("Sanding Disc", "Abrasives", "Abrasives > Discs > Sanding Discs"),
        "cut off disc": ("Cut Off Disc", "Abrasives", "Abrasives > Discs > Cut Off Discs"),
        "cut-off disc": ("Cut Off Disc", "Abrasives", "Abrasives > Discs > Cut Off Discs"),
        "cut off wheel": ("Cut Off Wheel", "Abrasives", "Abrasives > Wheels > Cut Off Wheels"),
        "cutting disc": ("Cutting Disc", "Abrasives", "Abrasives > Discs > Cutting Discs"),
        "grinding disc": ("Grinding Disc", "Abrasives", "Abrasives > Discs > Grinding Discs"),
        "flap disc": ("Flap Disc", "Abrasives", "Abrasives > Discs > Flap Discs"),
        "flap wheel": ("Flap Wheel", "Abrasives", "Abrasives > Wheels > Flap Wheels"),
        "sanding pad": ("Sanding Pad", "Abrasives", "Abrasives > Pads > Sanding Pads"),
        "hook loop": ("Hook and Loop Disc", "Abrasives", "Abrasives > Discs > Hook and Loop Discs"),
        "sponge pad": ("Sanding Sponge", "Abrasives", "Abrasives > Sponges > Sanding Sponges"),
        "sanding sponge": ("Sanding Sponge", "Abrasives", "Abrasives > Sponges > Sanding Sponges"),
        "rolling drum": ("Sanding Drum", "Abrasives", "Abrasives > Drums > Sanding Drums"),
        "sanding drum": ("Sanding Drum", "Abrasives", "Abrasives > Drums > Sanding Drums"),
        "wire brush": ("Wire Brush", "Abrasives", "Abrasives > Brushes > Wire Brushes"),
        "wire wheel": ("Wire Wheel", "Abrasives", "Abrasives > Wheels > Wire Wheels"),
        "abrasive": ("Abrasive", "Abrasives", "Abrasives > General"),
        "polishing pad": ("Polishing Pad", "Abrasives", "Abrasives > Pads > Polishing Pads"),
        "buffing pad": ("Buffing Pad", "Abrasives", "Abrasives > Pads > Buffing Pads"),

        # Appliances
        "dishwasher": ("Dishwasher", "Appliances", "Appliances > Kitchen > Dishwashers"),
        "refrigerator": ("Refrigerator", "Appliances", "Appliances > Kitchen > Refrigerators"),
        "fridge": ("Refrigerator", "Appliances", "Appliances > Kitchen > Refrigerators"),
        "freezer": ("Freezer", "Appliances", "Appliances > Kitchen > Freezers"),
        "range": ("Range", "Appliances", "Appliances > Kitchen > Ranges"),
        "oven": ("Oven", "Appliances", "Appliances > Kitchen > Ovens"),
        "microwave": ("Microwave", "Appliances", "Appliances > Kitchen > Microwaves"),
        "washer": ("Washer", "Appliances", "Appliances > Laundry > Washers"),
        "dryer": ("Dryer", "Appliances", "Appliances > Laundry > Dryers"),
        "water heater": ("Water Heater", "Appliances", "Appliances > Water Heaters"),
        "disposal": ("Garbage Disposal", "Appliances", "Appliances > Kitchen > Garbage Disposals"),
        "garbage disposal": ("Garbage Disposal", "Appliances", "Appliances > Kitchen > Garbage Disposals"),
        "range hood": ("Range Hood", "Appliances", "Appliances > Kitchen > Range Hoods"),
        "cooktop": ("Cooktop", "Appliances", "Appliances > Kitchen > Cooktops"),
        "wall oven": ("Wall Oven", "Appliances", "Appliances > Kitchen > Wall Ovens"),
        "compact refrigerator": ("Compact Refrigerator", "Appliances", "Appliances > Kitchen > Compact Refrigerators"),
        "ice maker": ("Ice Maker", "Appliances", "Appliances > Kitchen > Ice Makers"),
        "wine cooler": ("Wine Cooler", "Appliances", "Appliances > Kitchen > Wine Coolers"),

        # Decking
        "decking": ("Decking", "Decking", "Decking > Deck Boards"),
        "deck board": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "decking board": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "post sleeve": ("Post Sleeve", "Decking", "Decking > Railing > Post Sleeves"),
        "post cap": ("Post Cap", "Decking", "Decking > Railing > Post Caps"),
        "post skirt": ("Post Skirt", "Decking", "Decking > Railing > Post Skirts"),
        "fascia": ("Fascia", "Decking", "Decking > Fascia"),
        "railing": ("Railing", "Decking", "Decking > Railing"),
        "railing kit": ("Railing Kit", "Decking", "Decking > Railing > Railing Kits"),
        "t-rail kit": ("Railing Kit", "Decking", "Decking > Railing > Railing Kits"),
        "baluster": ("Baluster", "Decking", "Decking > Railing > Balusters"),
        "balusters": ("Baluster", "Decking", "Decking > Railing > Balusters"),
        "deck fastener": ("Deck Fastener", "Decking", "Decking > Fasteners"),
        "deck screws": ("Deck Screws", "Decking", "Decking > Fasteners > Deck Screws"),
        "deck screw": ("Deck Screws", "Decking", "Decking > Fasteners > Deck Screws"),
        "joist": ("Joist", "Decking", "Decking > Structural > Joists"),
        "joist tape": ("Joist Tape", "Decking", "Decking > Structural > Joist Tape"),
        "ledger board": ("Ledger Board", "Decking", "Decking > Structural > Ledger Boards"),
        "tropical": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "composite": ("Composite Deck Board", "Decking", "Decking > Deck Boards > Composite"),
        "trex": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "azek": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "timbertech": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "sq edge": ("Deck Board", "Decking", "Decking > Deck Boards"),
        "radius edge": ("Deck Board", "Decking", "Decking > Deck Boards"),

        # Lighting
        "led": ("LED", "Lighting", "Lighting > LED"),
        "bulb": ("Light Bulb", "Lighting", "Lighting > Bulbs"),
        "light bulb": ("Light Bulb", "Lighting", "Lighting > Bulbs"),
        "lamp": ("Lamp", "Lighting", "Lighting > Lamps"),
        "fixture": ("Light Fixture", "Lighting", "Lighting > Fixtures"),
        "ceiling fan": ("Ceiling Fan", "Lighting", "Lighting > Ceiling Fans"),
        "pendant": ("Pendant Light", "Lighting", "Lighting > Fixtures > Pendant Lights"),
        "chandelier": ("Chandelier", "Lighting", "Lighting > Fixtures > Chandeliers"),
        "sconce": ("Wall Sconce", "Lighting", "Lighting > Fixtures > Wall Sconces"),
        "recessed": ("Recessed Light", "Lighting", "Lighting > Fixtures > Recessed Lights"),
        "recessed light": ("Recessed Light", "Lighting", "Lighting > Fixtures > Recessed Lights"),
        "track light": ("Track Light", "Lighting", "Lighting > Fixtures > Track Lights"),
        "under cabinet": ("Under Cabinet Light", "Lighting", "Lighting > Fixtures > Under Cabinet Lights"),
        "flood light": ("Flood Light", "Lighting", "Lighting > Fixtures > Flood Lights"),
        "floodlight": ("Flood Light", "Lighting", "Lighting > Fixtures > Flood Lights"),
        "spot light": ("Spot Light", "Lighting", "Lighting > Fixtures > Spot Lights"),
        "spotlight": ("Spot Light", "Lighting", "Lighting > Fixtures > Spot Lights"),
        "area light": ("Area Light", "Lighting", "Lighting > Fixtures > Area Lights"),
        "wall pack": ("Wall Pack", "Lighting", "Lighting > Fixtures > Wall Packs"),
        "motion sensor": ("Motion Sensor Light", "Lighting", "Lighting > Fixtures > Motion Sensor Lights"),
        "night light": ("Night Light", "Lighting", "Lighting > Fixtures > Night Lights"),
        "emergency light": ("Emergency Light", "Lighting", "Lighting > Fixtures > Emergency Lights"),
        "exit sign": ("Exit Sign", "Lighting", "Lighting > Fixtures > Exit Signs"),
        "step light": ("Step Light", "Lighting", "Lighting > Fixtures > Step Lights"),
        "landscape": ("Landscape Light", "Lighting", "Lighting > Fixtures > Landscape Lights"),
        "path light": ("Path Light", "Lighting", "Lighting > Fixtures > Path Lights"),
        "well light": ("Well Light", "Lighting", "Lighting > Fixtures > Well Lights"),
        "br40": ("BR40 Light", "Lighting", "Lighting > Bulbs > BR40"),
        "br30": ("BR30 Light", "Lighting", "Lighting > Bulbs > BR30"),
        "par38": ("PAR38 Light", "Lighting", "Lighting > Bulbs > PAR38"),
        "par30": ("PAR30 Light", "Lighting", "Lighting > Bulbs > PAR30"),
        "par20": ("PAR20 Light", "Lighting", "Lighting > Bulbs > PAR20"),
        "mr16": ("MR16 Light", "Lighting", "Lighting > Bulbs > MR16"),
        "gu10": ("GU10 Light", "Lighting", "Lighting > Bulbs > GU10"),

        # Electrical
        "outlet": ("Outlet", "Electrical", "Electrical > Outlets"),
        "receptacle": ("Receptacle", "Electrical", "Electrical > Outlets > Receptacles"),
        "switch": ("Switch", "Electrical", "Electrical > Switches"),
        "dimmer": ("Dimmer Switch", "Electrical", "Electrical > Switches > Dimmers"),
        "gfci": ("GFCI Outlet", "Electrical", "Electrical > Outlets > GFCI"),
        "gfi": ("GFCI Outlet", "Electrical", "Electrical > Outlets > GFCI"),
        "breaker": ("Circuit Breaker", "Electrical", "Electrical > Breakers"),
        "panel": ("Electrical Panel", "Electrical", "Electrical > Panels"),
        "fuse": ("Fuse", "Electrical", "Electrical > Fuses"),
        "wire": ("Wire", "Electrical", "Electrical > Wire"),
        "cable": ("Cable", "Electrical", "Electrical > Wire > Cable"),
        "conduit": ("Conduit", "Electrical", "Electrical > Conduit"),
        "cover plate": ("Cover Plate", "Electrical", "Electrical > Cover Plates"),
        "wall plate": ("Wall Plate", "Electrical", "Electrical > Cover Plates"),
        "ceiling fan switch": ("Ceiling Fan Switch", "Electrical", "Electrical > Switches > Ceiling Fan"),
        "timer": ("Timer Switch", "Electrical", "Electrical > Switches > Timers"),
        "occupancy sensor": ("Occupancy Sensor", "Electrical", "Electrical > Sensors > Occupancy"),
        "doorbell": ("Doorbell", "Electrical", "Electrical > Doorbells"),

        # Power Tools
        "drill": ("Drill", "Power Tools", "Power Tools > Drills"),
        "impact driver": ("Impact Driver", "Power Tools", "Power Tools > Drivers > Impact Drivers"),
        "impact wrench": ("Impact Wrench", "Power Tools", "Power Tools > Wrenches > Impact Wrenches"),
        "circular saw": ("Circular Saw", "Power Tools", "Power Tools > Saws > Circular Saws"),
        "reciprocating saw": ("Reciprocating Saw", "Power Tools", "Power Tools > Saws > Reciprocating Saws"),
        "jigsaw": ("Jigsaw", "Power Tools", "Power Tools > Saws > Jigsaws"),
        "miter saw": ("Miter Saw", "Power Tools", "Power Tools > Saws > Miter Saws"),
        "table saw": ("Table Saw", "Power Tools", "Power Tools > Saws > Table Saws"),
        "band saw": ("Band Saw", "Power Tools", "Power Tools > Saws > Band Saws"),
        "scroll saw": ("Scroll Saw", "Power Tools", "Power Tools > Saws > Scroll Saws"),
        "grinder": ("Grinder", "Power Tools", "Power Tools > Grinders"),
        "angle grinder": ("Angle Grinder", "Power Tools", "Power Tools > Grinders > Angle Grinders"),
        "sander": ("Sander", "Power Tools", "Power Tools > Sanders"),
        "orbital sander": ("Orbital Sander", "Power Tools", "Power Tools > Sanders > Orbital"),
        "belt sander": ("Belt Sander", "Power Tools", "Power Tools > Sanders > Belt"),
        "router": ("Router", "Power Tools", "Power Tools > Routers"),
        "planer": ("Planer", "Power Tools", "Power Tools > Planers"),
        "nail gun": ("Nail Gun", "Power Tools", "Power Tools > Nailers"),
        "nailer": ("Nailer", "Power Tools", "Power Tools > Nailers"),
        "brad nailer": ("Brad Nailer", "Power Tools", "Power Tools > Nailers > Brad"),
        "finish nailer": ("Finish Nailer", "Power Tools", "Power Tools > Nailers > Finish"),
        "framing nailer": ("Framing Nailer", "Power Tools", "Power Tools > Nailers > Framing"),
        "stapler": ("Stapler", "Power Tools", "Power Tools > Nailers > Staplers"),
        "rotary tool": ("Rotary Tool", "Power Tools", "Power Tools > Rotary Tools"),
        "oscillating": ("Oscillating Tool", "Power Tools", "Power Tools > Oscillating Tools"),
        "heat gun": ("Heat Gun", "Power Tools", "Power Tools > Heat Guns"),
        "blower": ("Blower", "Power Tools", "Power Tools > Blowers"),
        "chainsaw": ("Chainsaw", "Power Tools", "Power Tools > Chainsaws"),
        "string trimmer": ("String Trimmer", "Power Tools", "Power Tools > Outdoor > String Trimmers"),
        "lawn mower": ("Lawn Mower", "Power Tools", "Power Tools > Outdoor > Lawn Mowers"),
        "leaf blower": ("Leaf Blower", "Power Tools", "Power Tools > Outdoor > Leaf Blowers"),
        "hedge trimmer": ("Hedge Trimmer", "Power Tools", "Power Tools > Outdoor > Hedge Trimmers"),

        # Hand Tools
        "wrench": ("Wrench", "Hand Tools", "Hand Tools > Wrenches"),
        "socket": ("Socket", "Hand Tools", "Hand Tools > Sockets"),
        "ratchet": ("Ratchet", "Hand Tools", "Hand Tools > Ratchets"),
        "screwdriver": ("Screwdriver", "Hand Tools", "Hand Tools > Screwdrivers"),
        "hammer": ("Hammer", "Hand Tools", "Hand Tools > Hammers"),
        "pliers": ("Pliers", "Hand Tools", "Hand Tools > Pliers"),
        "tape measure": ("Tape Measure", "Hand Tools", "Hand Tools > Measuring > Tape Measures"),
        "level": ("Level", "Hand Tools", "Hand Tools > Measuring > Levels"),
        "square": ("Square", "Hand Tools", "Hand Tools > Measuring > Squares"),
        "utility knife": ("Utility Knife", "Hand Tools", "Hand Tools > Knives > Utility"),
        "hacksaw": ("Hacksaw", "Hand Tools", "Hand Tools > Saws > Hacksaws"),
        "hand saw": ("Hand Saw", "Hand Tools", "Hand Tools > Saws > Hand Saws"),
        "file": ("File", "Hand Tools", "Hand Tools > Files"),
        "chisel": ("Chisel", "Hand Tools", "Hand Tools > Chisels"),
        "clamp": ("Clamp", "Hand Tools", "Hand Tools > Clamps"),
        "vise": ("Vise", "Hand Tools", "Hand Tools > Vises"),
        "allen wrench": ("Allen Wrench", "Hand Tools", "Hand Tools > Wrenches > Allen"),
        "hex key": ("Hex Key", "Hand Tools", "Hand Tools > Wrenches > Hex Keys"),
        "torx": ("Torx Driver", "Hand Tools", "Hand Tools > Screwdrivers > Torx"),
        "multimeter": ("Multimeter", "Hand Tools", "Hand Tools > Test Equipment > Multimeters"),
        "stud finder": ("Stud Finder", "Hand Tools", "Hand Tools > Test Equipment > Stud Finders"),

        # Safety
        "safety glasses": ("Safety Glasses", "Safety", "Safety > Eye Protection > Glasses"),
        "goggles": ("Safety Goggles", "Safety", "Safety > Eye Protection > Goggles"),
        "gloves": ("Gloves", "Safety", "Safety > Hand Protection > Gloves"),
        "ear plugs": ("Ear Plugs", "Safety", "Safety > Hearing Protection > Ear Plugs"),
        "ear muffs": ("Ear Muffs", "Safety", "Safety > Hearing Protection > Ear Muffs"),
        "respirator": ("Respirator", "Safety", "Safety > Respiratory > Respirators"),
        "dust mask": ("Dust Mask", "Safety", "Safety > Respiratory > Dust Masks"),
        "hard hat": ("Hard Hat", "Safety", "Safety > Head Protection > Hard Hats"),
        "knee pad": ("Knee Pads", "Safety", "Safety > Body Protection > Knee Pads"),
        "safety vest": ("Safety Vest", "Safety", "Safety > Body Protection > Vests"),
        "fall protection": ("Fall Protection", "Safety", "Safety > Fall Protection"),

        # Windows & Doors
        "window": ("Window", "Windows & Doors", "Windows & Doors > Windows"),
        "door": ("Door", "Windows & Doors", "Windows & Doors > Doors"),
        "hinge": ("Hinge", "Windows & Doors", "Windows & Doors > Hardware > Hinges"),
        "doorknob": ("Doorknob", "Windows & Doors", "Windows & Doors > Hardware > Knobs"),
        "deadbolt": ("Deadbolt", "Windows & Doors", "Windows & Doors > Hardware > Deadbolts"),
        "lockset": ("Lockset", "Windows & Doors", "Windows & Doors > Hardware > Locksets"),
        "handle": ("Handle", "Windows & Doors", "Windows & Doors > Hardware > Handles"),
        "latch": ("Latch", "Windows & Doors", "Windows & Doors > Hardware > Latches"),
        "weatherstrip": ("Weatherstrip", "Windows & Doors", "Windows & Doors > Accessories > Weatherstripping"),
        "threshold": ("Threshold", "Windows & Doors", "Windows & Doors > Accessories > Thresholds"),
        "door stop": ("Door Stop", "Windows & Doors", "Windows & Doors > Accessories > Door Stops"),
        "sliding door": ("Sliding Door", "Windows & Doors", "Windows & Doors > Doors > Sliding"),
        "french door": ("French Door", "Windows & Doors", "Windows & Doors > Doors > French"),
        "entry door": ("Entry Door", "Windows & Doors", "Windows & Doors > Doors > Entry"),
        "garage door": ("Garage Door", "Windows & Doors", "Windows & Doors > Doors > Garage"),

        # Building Materials
        "lumber": ("Lumber", "Building Materials", "Building Materials > Lumber"),
        "plywood": ("Plywood", "Building Materials", "Building Materials > Sheet Goods > Plywood"),
        "osb": ("OSB", "Building Materials", "Building Materials > Sheet Goods > OSB"),
        "drywall": ("Drywall", "Building Materials", "Building Materials > Drywall"),
        "insulation": ("Insulation", "Building Materials", "Building Materials > Insulation"),
        "concrete": ("Concrete", "Building Materials", "Building Materials > Concrete"),
        "mortar": ("Mortar", "Building Materials", "Building Materials > Mortar"),
        "grout": ("Grout", "Building Materials", "Building Materials > Grout"),
        "cement": ("Cement", "Building Materials", "Building Materials > Cement"),
        "adhesive": ("Adhesive", "Building Materials", "Building Materials > Adhesives"),
        "caulk": ("Caulk", "Building Materials", "Building Materials > Caulks > General"),
        "silicone": ("Silicone Caulk", "Building Materials", "Building Materials > Caulks > Silicone"),
        "sealant": ("Sealant", "Building Materials", "Building Materials > Sealants"),
        "foam": ("Foam", "Building Materials", "Building Materials > Foam"),
        "furring strip": ("Furring Strip", "Building Materials", "Building Materials > Lumber > Furring Strips"),
        "molding": ("Molding", "Building Materials", "Building Materials > Trim > Molding"),
        "trim": ("Trim", "Building Materials", "Building Materials > Trim"),
        "baseboard": ("Baseboard", "Building Materials", "Building Materials > Trim > Baseboards"),
        "crown molding": ("Crown Molding", "Building Materials", "Building Materials > Trim > Crown Molding"),
        "casing": ("Casing", "Building Materials", "Building Materials > Trim > Casing"),
        "stud": ("Stud", "Building Materials", "Building Materials > Lumber > Studs"),
        "beam": ("Beam", "Building Materials", "Building Materials > Lumber > Beams"),
        "post": ("Post", "Building Materials", "Building Materials > Lumber > Posts"),

        # Fasteners
        "screw": ("Screw", "Fasteners", "Fasteners > Screws"),
        "bolt": ("Bolt", "Fasteners", "Fasteners > Bolts"),
        "nut": ("Nut", "Fasteners", "Fasteners > Nuts"),
        "washer": ("Washer", "Fasteners", "Fasteners > Washers"),
        "anchor": ("Anchor", "Fasteners", "Fasteners > Anchors"),
        "nail": ("Nail", "Fasteners", "Fasteners > Nails"),
        "rivet": ("Rivet", "Fasteners", "Fasteners > Rivets"),
        "toggle bolt": ("Toggle Bolt", "Fasteners", "Fasteners > Bolts > Toggle"),
        "lag screw": ("Lag Screw", "Fasteners", "Fasteners > Screws > Lag"),
        "wood screw": ("Wood Screw", "Fasteners", "Fasteners > Screws > Wood"),
        "machine screw": ("Machine Screw", "Fasteners", "Fasteners > Screws > Machine"),
        "sheet metal screw": ("Sheet Metal Screw", "Fasteners", "Fasteners > Screws > Sheet Metal"),
        "self tapping": ("Self-Tapping Screw", "Fasteners", "Fasteners > Screws > Self-Tapping"),
        "drywall screw": ("Drywall Screw", "Fasteners", "Fasteners > Screws > Drywall"),
        "concrete screw": ("Concrete Screw", "Fasteners", "Fasteners > Screws > Concrete"),
        "carriage bolt": ("Carriage Bolt", "Fasteners", "Fasteners > Bolts > Carriage"),
        "hex bolt": ("Hex Bolt", "Fasteners", "Fasteners > Bolts > Hex"),
        "eye bolt": ("Eye Bolt", "Fasteners", "Fasteners > Bolts > Eye"),
        "u-bolt": ("U-Bolt", "Fasteners", "Fasteners > Bolts > U-Bolts"),

        # Plumbing
        "faucet": ("Faucet", "Plumbing", "Plumbing > Faucets"),
        "toilet": ("Toilet", "Plumbing", "Plumbing > Toilets"),
        "sink": ("Sink", "Plumbing", "Plumbing > Sinks"),
        "shower": ("Shower", "Plumbing", "Plumbing > Showers"),
        "valve": ("Valve", "Plumbing", "Plumbing > Valves"),
        "pipe": ("Pipe", "Plumbing", "Plumbing > Pipes"),
        "fitting": ("Fitting", "Plumbing", "Plumbing > Fittings"),
        "elbow": ("Elbow", "Plumbing", "Plumbing > Fittings > Elbows"),
        "tee": ("Tee Fitting", "Plumbing", "Plumbing > Fittings > Tees"),
        "coupling": ("Coupling", "Plumbing", "Plumbing > Fittings > Couplings"),
        "connector": ("Connector", "Plumbing", "Plumbing > Fittings > Connectors"),
        "adapter": ("Adapter", "Plumbing", "Plumbing > Fittings > Adapters"),
        "trap": ("Trap", "Plumbing", "Plumbing > Traps"),
        "supply line": ("Supply Line", "Plumbing", "Plumbing > Supply Lines"),
        "flexible connector": ("Flexible Connector", "Plumbing", "Plumbing > Fittings > Flexible Connectors"),
        "ball valve": ("Ball Valve", "Plumbing", "Plumbing > Valves > Ball"),
        "check valve": ("Check Valve", "Plumbing", "Plumbing > Valves > Check"),
        "stop valve": ("Stop Valve", "Plumbing", "Plumbing > Valves > Stop"),
        "angle stop": ("Angle Stop", "Plumbing", "Plumbing > Valves > Angle Stops"),
        "pop-up": ("Pop-Up Drain", "Plumbing", "Plumbing > Drains > Pop-Up"),
        "drain": ("Drain", "Plumbing", "Plumbing > Drains"),
        "overflow": ("Overflow Drain", "Plumbing", "Plumbing > Drains > Overflow"),
        "flush valve": ("Flush Valve", "Plumbing", "Plumbing > Valves > Flush"),
        "fill valve": ("Fill Valve", "Plumbing", "Plumbing > Valves > Fill"),
        "flush handle": ("Flush Handle", "Plumbing", "Plumbing > Toilet Parts > Flush Handles"),
        "wax ring": ("Wax Ring", "Plumbing", "Plumbing > Toilet Parts > Wax Rings"),
        "toilet seat": ("Toilet Seat", "Plumbing", "Plumbing > Toilet Parts > Seats"),

        # Fans
        "exhaust fan": ("Exhaust Fan", "Fans", "Fans > Exhaust Fans"),
        "bath fan": ("Bathroom Exhaust Fan", "Fans", "Fans > Exhaust Fans > Bathroom"),
        "range hood fan": ("Range Hood Fan", "Fans", "Fans > Range Hood Fans"),
        "inline fan": ("Inline Fan", "Fans", "Fans > Inline Fans"),
        "vent fan": ("Ventilation Fan", "Fans", "Fans > Ventilation"),
        "attic fan": ("Attic Fan", "Fans", "Fans > Attic Fans"),
        "whole house fan": ("Whole House Fan", "Fans", "Fans > Whole House"),
        "tower fan": ("Tower Fan", "Fans", "Fans > Portable > Tower"),
        "box fan": ("Box Fan", "Fans", "Fans > Portable > Box"),
        "pedestal fan": ("Pedestal Fan", "Fans", "Fans > Portable > Pedestal"),
        "desk fan": ("Desk Fan", "Fans", "Fans > Portable > Desk"),
        "industrial fan": ("Industrial Fan", "Fans", "Fans > Industrial"),
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

    DIMENSION_PATTERN = re.compile(
        r'(\d+(?:\s*\d+/\d+|\.\d+)?)'
        r'\s*[xX\u00d7]\s*'
        r'(\d+(?:\s*\d+/\d+|\.\d+)?)'
        r'(?:\s*[xX\u00d7]\s*'
        r'(\d+(?:\s*\d+/\d+|\.\d+)?))?'
    )

    SINGLE_DIM_PATTERN = re.compile(
        r'(\d+(?:\s*\d+/\d+|\.\d+)?)\s*'
        r'(in(?:ch(?:es)?)?|"|\'\'|\'|ft|feet|mm|cm|m)\b',
        re.IGNORECASE
    )

    FRACTION_PATTERN = re.compile(r'(\d+)\s*/\s*(\d+)')

    QUANTITY_PATTERN = re.compile(
        r'(\d+)\s*(?:pc|pk|pack|ct|count|pcs?|ea|each|set|sets?|pair|pairs?)\b',
        re.IGNORECASE
    )

    GRIT_PATTERN = re.compile(
        r'(?:#\s*)?(\d{1,4})\s*[-]?\s*grit\b',
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
        pass

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
            for brand_key in self.known_brands:
                if brand_key in brand_info.lower():
                    return self.known_brands[brand_key]

        for brand_key, brand_name in self.known_brands.items():
            pattern = r'\b' + re.escape(brand_key) + r'\b'
            if re.search(pattern, desc_lower):
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

        for keyword, value in self.product_type_keywords.items():
            if " " not in keyword:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, desc_lower):
                    return value

        return ("", "General", "General")

    def _extract_dimensions(self, part_desc: str) -> Tuple[Dict[str, str], str]:
        dims = {}
        raw_dims = ""

        dim_match = self.DIMENSION_PATTERN.search(part_desc)
        if dim_match:
            raw_dims = dim_match.group(0).strip()
            groups = [g for g in dim_match.groups() if g is not None]

            unit = "in"

            if len(groups) == 1:
                value = groups[0]
                if "/" in value:
                    dims["diameter"] = self.normalize_dimensions(value, unit)
                else:
                    dims["width"] = self.normalize_dimensions(value, unit)
            elif len(groups) == 2:
                dims["width"] = self.normalize_dimensions(groups[0], unit)
                dims["length"] = self.normalize_dimensions(groups[1], unit)
            elif len(groups) >= 3:
                dims["width"] = self.normalize_dimensions(groups[0], unit)
                dims["length"] = self.normalize_dimensions(groups[1], unit)
                dims["height"] = self.normalize_dimensions(groups[2], unit)

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
            return match.group(1)
        return None

    def _extract_material(self, part_desc: str) -> Optional[str]:
        desc_lower = part_desc.lower()
        for abbr, full_name in self.material_keywords.items():
            if abbr.lower() in desc_lower:
                return full_name
        return None

    def _extract_color(self, part_desc: str) -> Optional[str]:
        for abbr, full_name in self.color_keywords.items():
            if abbr in part_desc or abbr.lower() in part_desc.lower():
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
        series_patterns = [
            re.compile(r'series\s+([\w\-]+)', re.IGNORECASE),
            re.compile(r'([\w\-]+)\s+series', re.IGNORECASE),
            re.compile(r'#\s*([\w\-]+)', re.IGNORECASE),
        ]
        for pattern in series_patterns:
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
'''

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Written {len(content)} characters to {FILE_PATH}")
