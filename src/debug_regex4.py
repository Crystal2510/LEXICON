#!/usr/bin/env python3
import re

test = 'Diablo 1/2"x18" - Sanding Belt 6pc'
# Check: does \d+(?:\s*\d+/\d+)? match 1/2?
pat = re.compile(r'\d+(?:\s*\d+/\d+)?')
m = pat.search(test)
print(f'\\d+(?:...)? matches: {m.group(0)} at pos {m.start()}')

# Test just the fraction pattern on "1/2"
pat2 = re.compile(r'\d+/\d+')
m2 = pat2.search('1/2')
print(f'\\d+/\\d+ matches "1/2": {m2.group(0) if m2 else None}')

# Test combined
pat3 = re.compile(r'\d+(?:\s*\d+/\d+)?')
m3 = pat3.search('1/2"x18"')
print(f'\\d+(?:...)? on "1/2\\"x18\\"": {m3.group(0)} at pos {m3.start()}')
