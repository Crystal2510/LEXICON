#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Hackathon\Unilog\src')
from description_parser import DescriptionParser

parser = DescriptionParser()

tests = [
    ('DCB518ASTS06G', 'Diablo 1/2"x18" - Sanding Belt 6pc'),
    ('49-94-0013', 'Milw 5"x.045"x7/8" Metal Cut Off Disc'),
    ('576512', '65W Led BR40 Med 27k'),
    ('543302146', "8' Wh Select T-Rail Kit Horiz - w/Sq Composite Balusters"),
    ('1nx6-16', 'Tide Pool Sq Edge - Trex Enhance Basics Decking'),
]

for mpn, desc in tests:
    result = parser.parse(mpn, desc)
    print(f'--- {mpn}: {desc} ---')
    for k, v in result.items():
        print(f'  {k}: {v}')
    print()
