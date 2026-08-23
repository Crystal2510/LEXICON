#!/usr/bin/env python3
import re

test = 'Diablo 1/2"x18" - Sanding Belt 6pc'
print(f'Test string: {test}')
print(f'Test string repr: {repr(test)}')
print(f'Length: {len(test)}')

# Find position of 1/2
idx = test.find('1/2')
print(f'Position of 1/2: {idx}')

# Try a very simple pattern to match 1/2
pat = re.compile(r'1/2')
m = pat.search(test)
print(f'Simple 1/2 match: {m}')

# Try to match 1/2" 
pat2 = re.compile(r'1/2"')
m2 = pat2.search(test)
print(f'1/2" match: {m2}')

# Try to match 1/2"x18
pat3 = re.compile(r'1/2"x18')
m3 = pat3.search(test)
print(f'1/2"x18 match: {m3}')

# Now test the actual regex step by step
# Step 1: just \d+
pat4 = re.compile(r'\d+')
m4 = pat4.search(test)
print(f'Step 1 (\\d+): match={m4.group(0)} at pos={m4.start() if m4 else None}')

# Step 2: \d+(?:\s*\d+/\d+)?
pat5 = re.compile(r'\d+(?:\s*\d+/\d+)?')
m5 = pat5.search(test)
print(f'Step 2 (\\d+(?:...)?): match={m5.group(0)} at pos={m5.start() if m5 else None}')

# Step 3: \d+(?:\s*\d+/\d+)?["\s]*
pat6 = re.compile(r'\d+(?:\s*\d+/\d+)?["\s]*')
m6 = pat6.search(test)
print(f'Step 3 (with quote): match={m6.group(0)} at pos={m6.start() if m6 else None}')

# Step 4: \d+(?:\s*\d+/\d+)?["\s]*x
pat7 = re.compile(r'\d+(?:\s*\d+/\d+)?["\s]*x')
m7 = pat7.search(test)
print(f'Step 4 (with x): match={m7.group(0)} at pos={m7.start() if m7 else None}')

# Step 5: \d+(?:\s*\d+/\d+)?["\s]*x["\s]*
pat8 = re.compile(r'\d+(?:\s*\d+/\d+)?["\s]*x["\s]*')
m8 = pat8.search(test)
print(f'Step 5 (with quote after x): match={m8.group(0)} at pos={m8.start() if m8 else None}')

# Step 6: \d+(?:\s*\d+/\d+)?["\s]*x["\s]*\d+
pat9 = re.compile(r'\d+(?:\s*\d+/\d+)?["\s]*x["\s]*\d+')
m9 = pat9.search(test)
print(f'Step 6 (full): match={m9.group(0)} at pos={m9.start() if m9 else None}')

# Step 7: with groups
pat10 = re.compile(r'(\d+(?:\s*\d+/\d+)?)["\s]*x["\s]*(\d+)')
m10 = pat10.search(test)
print(f'Step 7 (with groups): match={m10.group(0)} groups={[g for g in m10.groups() if g is not None]}')
