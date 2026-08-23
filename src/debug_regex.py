#!/usr/bin/env python3
import re

pat = re.compile(
    r'(\d+(?:\s*\d+/\d+|\.\d+)?)'
    r'["\u201d\u2019\'\s]*'
    r'[xX\u00d7\u00d8]'
    r'["\u201d\u2019\'\s]*'
    r'(\d+(?:\s*\d+/\d+|\.\d+)?)'
    r'(?:["\u201d\u2019\'\s]*[xX\u00d7\u00d8]["\u201d\u2019\'\s]*(\d+(?:\s*\d+/\d+|\.\d+)?))?'
)
tests = [
    'Diablo 1/2"x18" - Sanding Belt 6pc',
    'Milw 5"x.045"x7/8" Metal Cut Off Disc',
]
for t in tests:
    m = pat.search(t)
    if m:
        print(f'Input: {t}')
        print(f'  Match: {m.group(0)}')
        groups = [g for g in m.groups() if g is not None]
        print(f'  Groups: {groups}')
    else:
        print(f'Input: {t} -> No match')
    print()
