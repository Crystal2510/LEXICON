import pandas as pd
import re
from collections import Counter

df = pd.read_csv('data/sample_input.csv', dtype=str, keep_default_na=False)
exp = pd.read_csv('data/expected_output.csv', dtype=str, keep_default_na=False)

print("=== PART_MANUF CODE PATTERNS ===")
# Extract code from parentheses dynamically
def extract_code_name(manuf):
    m = re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', manuf.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return manuf.strip(), ''

for manuf in df['Part_Manuf'].unique():
    name, code = extract_code_name(manuf)
    print(f"  '{manuf}' -> name='{name}' code='{code}'")

print("\n=== BRAND APPEARING IN PART_DESC ===")
# Detect if brand appears as first word in Part_Desc
first_words = Counter()
for desc in df['Part_Desc']:
    words = desc.split()
    if words:
        first_words[words[0]] += 1
print("Top first words in Part_Desc:")
for word, count in first_words.most_common(20):
    print(f"  '{word}': {count}")

print("\n=== E1_BRAND NON-PLACEHOLDER VALUES ===")
non_placeholder = df[~df['E1_Brand'].isin(['-- Unbranded --', '-- No Unilog Brand --', '-- No DIB Brand --', '--', '-', ''])]
print(f"Rows with real E1_Brand: {len(non_placeholder)}")
for brand in non_placeholder['E1_Brand'].unique():
    print(f"  '{brand}'")

print("\n=== EXPECTED OUTPUT - INVOICE DESC PATTERN ===")
for i in range(len(exp)):
    row = exp.iloc[i]
    print(f"  Input:   {row['Part_Desc'][:60]}")
    print(f"  Invoice: {row.get('INVOICE_DESC','')}")
    print(f"  Mobile:  {row.get('MOBILE_DESC','')}")
    print(f"  Short:   {row.get('SHORT_DESC','')[:80]}")
    print(f"  Long:    {row.get('LONG_DESC1','')[:100]}")
    print(f"  Retail:  {row.get('RETAIL_DESC','')[:80]}")
    print(f"  Manuf:   {row.get('MANUFACTURER_NAME','')}")
    print(f"  Brand:   {row.get('BRAND_NAME','')}")
    print(f"  Trade:   {row.get('TRADE_NAME','')}")
    print(f"  Class:   {row.get('Classpath','')}")
    print()

print("\n=== PART_DESC PATTERN ANALYSIS ===")
patterns = {
    'starts_with_mpn_then_brand': 0,
    'starts_with_brand': 0,
    'all_abbreviated': 0,
    'has_dimension': 0,
    'has_number': 0,
}
for desc in df['Part_Desc']:
    if re.match(r'^[A-Z0-9\-]{5,}', desc):
        patterns['starts_with_mpn_then_brand'] += 1
    if re.search(r'\d+["\']', desc):
        patterns['has_dimension'] += 1
    if re.search(r'\d', desc):
        patterns['has_number'] += 1

print(patterns)
