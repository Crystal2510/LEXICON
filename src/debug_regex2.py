#!/usr/bin/env python3
import re

# Check what quotes are in the test strings
test = 'Diablo 1/2"x18" - Sanding Belt 6pc'
for i, ch in enumerate(test):
    if ch in ('"', '\u201d', '\u2019', "'"):
        print(f'  pos {i}: {repr(ch)} (ord={ord(ch)})')

# Try a simpler regex
pat1 = re.compile(r'(\d+(?:\s*\d+/\d+)?)')
pat2 = re.compile(r'(\d+(?:\s*\d+/\d+)?)[\"\s]*x[\"\s]*(\d+)')

m1 = pat1.search(test)
print(f'pat1 match: {m1.group(0) if m1 else None} at pos {m1.start() if m1 else None}')

m2 = pat2.search(test)
print(f'pat2 match: {m2.group(0) if m2 else None}')
if m2:
    print(f'  Groups: {[g for g in m2.groups() if g is not None]}')

# Also test with the raw pattern
pat3 = re.compile(r'(\d+(?:\s*\d+/\d+)?)[\"\u201d\u2019\'\s]*[xX][\"\u201d\u2019\'\s]*(\d+)')
m3 = pat3.search(test)
print(f'pat3 match: {m3.group(0) if m3 else None}')
if m3:
    print(f'  Groups: {[g for g in m3.groups() if g is not None]}')
