#!/usr/bin/env python3
import re

# Test the corrected number pattern
# The issue was: \d+(?:\s*\d+/\d+)? doesn't match 1/2 because
# after matching 1, the optional group tries to match at / which fails
# Fix: use \d+(?:/\d+|\.\d+)? or \d+(?:\d+/\d+|\.\d+)?

pat_wrong = re.compile(r'\d+(?:\s*\d+/\d+)?')
pat_correct = re.compile(r'\d+(?:/\d+|\.\d+)?')

tests = ['1/2', '0.5', '18', '5', '.045', '7/8']
for t in tests:
    m_wrong = pat_wrong.match(t)
    m_correct = pat_correct.match(t)
    print(f'"{t}": wrong={m_wrong.group(0) if m_wrong else None}, correct={m_correct.group(0) if m_correct else None}')

# Now test with full dimension pattern
test = 'Diablo 1/2"x18" - Sanding Belt 6pc'
pat_full = re.compile(
    r'(\d+(?:/\d+|\.\d+)?)'
    r'["\s]*x["\s]*'
    r'(\d+(?:/\d+|\.\d+)?)'
)
m = pat_full.search(test)
if m:
    print(f'\nFull match on "{test}": {m.group(0)} groups={[g for g in m.groups() if g is not None]}')

test2 = 'Milw 5"x.045"x7/8" Metal Cut Off Disc'
m2 = pat_full.search(test2)
if m2:
    print(f'Full match on "{test2}": {m2.group(0)} groups={[g for g in m2.groups() if g is not None]}')
