#!/usr/bin/env python3
import re

# Pattern that handles: integers, decimals (5, .045, 0.5), fractions (1/2, 7/8)
_NUM = r'(?:(?:\d+\.?\d*|\.\d+)(?:/\d+)?)'

# Pattern for "NxN" or "NxNxN" with optional quote marks
pat = re.compile(
    _NUM + r'["\u201d\u2019\x27\s]*[xX\u00d7]' + r'["\u201d\u2019\x27\s]*' + _NUM +
    r'(?:["\u201d\u2019\x27\s]*[xX\u00d7]' + r'["\u201d\u2019\x27\s]*' + _NUM + r')?'
)

tests = [
    'Diablo 1/2"x18" - Sanding Belt 6pc',
    'Milw 5"x.045"x7/8" Metal Cut Off Disc',
    '8\' Wh Select T-Rail Kit',
    '1nx6-16\' Tide Pool Sq Edge',
    '3/4"x10" Sanding Disc',
    '1/4" x 2" x 3"',
]
for t in tests:
    m = pat.search(t)
    if m:
        groups = [g for g in m.groups() if g is not None]
        print(f'"{t}" => match="{m.group(0)}" groups={groups}')
    else:
        print(f'"{t}" => No match')
