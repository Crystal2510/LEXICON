import pandas as pd
import re

df = pd.read_csv('data/sample_input.csv', dtype=str, keep_default_na=False)

print('=== ALL MANUFACTURERS ===')
for m in sorted(df['Part_Manuf'].unique()):
    print(' ', m)

print('\n=== GRIT PATTERNS ===')
grit_pattern = re.compile(r'P(\d{2,3})\b', re.IGNORECASE)
grit_found = df['Part_Desc'].apply(lambda x: bool(grit_pattern.search(x)))
print('Rows with grit (P80, P120, etc):', grit_found.sum())
for desc in df[grit_found]['Part_Desc'].head(5):
    print(' ', desc[:80])

print('\n=== QUANTITY PATTERNS ===')
qty_pattern = re.compile(r'(\d+)\s*(?:pc|pack|pcs|piece|ea|ct|count|disc|disk)s?\b', re.IGNORECASE)
qty_found = df['Part_Desc'].apply(lambda x: bool(qty_pattern.search(x)))
print('Rows with quantity:', qty_found.sum())

print('\n=== SAMPLE LIGHTING PRODUCTS ===')
lighting = df[df['Part_Manuf'].str.contains('Philips|Kichler|Satco|Leviton', case=False, na=False)]
print('Lighting/electrical rows:', len(lighting))
for desc in lighting['Part_Desc'].head(10):
    print(' ', desc[:100])

print('\n=== SAMPLE APPLIANCE PRODUCTS ===')
appliance = df[df['Part_Manuf'].str.contains('Appliance', case=False, na=False)]
print('Appliance rows:', len(appliance))
for desc in appliance['Part_Desc'].head(8):
    print(' ', desc[:100])

print('\n=== SAMPLE BUILDING MATERIAL PRODUCTS ===')
building = df[df['Part_Manuf'].str.contains('Boise|Parksite|Lumber', case=False, na=False)]
print('Building material rows:', len(building))
for desc in building['Part_Desc'].head(8):
    print(' ', desc[:100])

print('\n=== EXPECTED OUTPUT FIELDS ===')
exp = pd.read_csv('data/expected_output.csv', dtype=str, keep_default_na=False)
row = exp.iloc[1]
key_fields = ['MANUFACTURER_NAME','BRAND_NAME','TRADE_NAME','Classpath',
              'MOBILE_DESC','INVOICE_DESC','SHORT_DESC','LONG_DESC1',
              'RETAIL_DESC','MARKETING_DESCRIPTION',
              'ATTRIBUTE_LABEL 1','ATTRIBUTE_VALUE 1','ATTRIBUTE_UOM 1',
              'ATTRIBUTE_LABEL 2','ATTRIBUTE_VALUE 2','ATTRIBUTE_UOM 2',
              'ATTRIBUTE_LABEL 3','ATTRIBUTE_VALUE 3','ATTRIBUTE_UOM 3',
              'Series','Product Name','Application','With','Standard/Approvals']
for f in key_fields:
    if f in row.index:
        print(f'  {f}: {row[f][:80]}')

print('\n=== EXPECTED CLASSPATH FORMAT ===')
for i in range(len(exp)):
    print(exp.iloc[i]['Classpath'])

print('\n=== EXPECTED ATTRIBUTES PATTERN ===')
row2 = exp.iloc[1]
for i in range(1, 20):
    label = row2.get(f'ATTRIBUTE_LABEL {i}', '')
    value = row2.get(f'ATTRIBUTE_VALUE {i}', '')
    uom = row2.get(f'ATTRIBUTE_UOM {i}', '')
    if label:
        print(f'  Attr{i}: {label} = {value} {uom}')
    else:
        break
