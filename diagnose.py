import sys, re
sys.path.insert(0, '.')
from src.pipeline import ProductPipeline
import pandas as pd

input_df = pd.read_csv('data/sample_input.csv', dtype=str, keep_default_na=False)
exp = pd.read_csv('data/expected_output.csv', dtype=str, keep_default_na=False)

# ---- 1. Show ALL appliance rows from input to understand brand-in-desc pattern ----
print("=== APPLIANCE ROWS (Part_Manuf contains Appliance/APPDE/VVAPP) ===")
appliance_rows = input_df[input_df['Part_Manuf'].str.contains('Appliance|APPDE|VVAPP', case=False, na=False)]
print(f"Total appliance rows: {len(appliance_rows)}")
for _, row in appliance_rows.head(20).iterrows():
    desc = row['Part_Desc']
    # Extract first meaningful token after MPN
    tokens = desc.split()
    print(f"  MPN={row['Mfg_Part_Num'][:12]:12s} | Desc={desc[:65]}")

# ---- 2. Analyze what 312 "General" rows look like ----
print("\n=== SAMPLE DESCRIPTIONS THAT FAIL CLASSIFICATION ===")
pipeline = ProductPipeline()
input_data = input_df.to_dict('records')
pipeline.initialize(input_data=input_data)

# Run quick parse on random sample
import random
random.seed(42)
hard_rows = []
for _, row in input_df.iterrows():
    row_dict = row.to_dict()
    parsed = pipeline.parser.parse(
        mpn=row_dict.get('Mfg_Part_Num',''),
        part_desc=row_dict.get('Part_Desc',''),
        brand_info=''
    )
    if not parsed.get('classpath') or parsed.get('classpath') == 'General':
        hard_rows.append((row_dict.get('Part_Desc',''), row_dict.get('Part_Manuf','')))

print(f"Rows failing keyword classification: {len(hard_rows)}")
print("Sample hard rows:")
for desc, manuf in hard_rows[:25]:
    print(f"  Manuf={manuf[:30]:30s} | Desc={desc[:55]}")

# ---- 3. Mobile desc analysis - what's wrong ----
print("\n=== MOBILE DESC FAILURES (not 60-80 chars) ===")
sample_out = pipeline.process_dataframe(input_df.head(50))
fails = sample_out[~sample_out['MOBILE_DESC'].apply(lambda x: 60 <= len(x) <= 80)]
print(f"Failures in first 50: {len(fails)}")
for _, row in fails.head(15).iterrows():
    mob = row['MOBILE_DESC']
    print(f"  len={len(mob):3d} cp={row['Classpath'][:30]:30s} -> {mob!r}")

# ---- 4. Attribute analysis - what are we missing? ----
print("\n=== ROWS WITH 0 ATTRIBUTES (first 50) ===")
for _, row in sample_out[sample_out['ATTRIBUTE_VALUE 1'].str.strip() == ''].head(15).iterrows():
    print(f"  cp={row['Classpath'][:35]:35s} | desc={row['Part_Desc'][:55]}")

# ---- 5. What does the expected invoice desc really need? ----
print("\n=== EXPECTED INVOICE DESC ANALYSIS ===")
for ei in range(len(exp)):
    row = exp.iloc[ei]
    print(f"  Part_Desc:    {row.get('Part_Desc','')[:60]}")
    print(f"  INVOICE_DESC: {row.get('INVOICE_DESC','')}")
    print(f"  Breakdown: TYPE=Dishwasher, MOUNTING=LEG/BLTLN, SPEC1=5/-, MATERIAL=SST, VOLT=120V, AMP=15A/10A, DIM=50-1/4IN/-")
    print()

# ---- 6. What short desc format does expected show? ----
print("=== EXPECTED SHORT/LONG/RETAIL DESC FORMAT ===")
for ei in range(len(exp)):
    row = exp.iloc[ei]
    print(f"BRAND_NAME: {row.get('BRAND_NAME','')}")
    print(f"TRADE_NAME: {row.get('TRADE_NAME','')}")
    print(f"SHORT_DESC: {row.get('SHORT_DESC','')}")
    print(f"LONG_DESC1: {row.get('LONG_DESC1','')[:120]}")
    print(f"MARKETING_DESCRIPTION: {row.get('MARKETING_DESCRIPTION','')[:80]}")
    print()
    # Show all 15 attributes
    for i in range(1, 16):
        label = row.get(f'ATTRIBUTE_LABEL {i}', '')
        value = row.get(f'ATTRIBUTE_VALUE {i}', '')
        uom = row.get(f'ATTRIBUTE_UOM {i}', '')
        if label or value:
            print(f"  Attr{i:2d}: {label:30s} = {value:25s} | UOM={uom}")
    print()
