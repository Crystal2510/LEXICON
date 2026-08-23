import pandas as pd
from src.pipeline import ProductPipeline

df = pd.read_csv('data/sample_input.csv', dtype=str, keep_default_na=False)
pipe = ProductPipeline()
pipe.initialize(input_data=df.to_dict('records'))
results = []
for idx, row in enumerate(df.itertuples(index=False)):
    row_dict = dict(zip(df.columns, row))
    r = pipe.process_row(row_dict, row_index=idx)
    results.append(r)
out = pd.DataFrame(results)

# ISSUE 1: LOV - rows with < 3 attributes
print("=== ISSUE 1: LOV COMPLIANCE (rows with <3 attrs) ===")
low_attr = []
for i, r in out.iterrows():
    cnt = sum(1 for j in range(1, 21) if r.get('ATTRIBUTE_VALUE %d' % j, ''))
    if cnt < 3:
        low_attr.append((i, cnt, r['Classpath'], r['Part_Desc'][:60], r['Mfg_Part_Num'][:20]))
print("Total rows with <3 attrs: %d / 1000" % len(low_attr))
for idx, cnt, cp, desc, mpn in low_attr[:15]:
    print("  Row %d: attrs=%d | CP=%s | %s" % (idx, cnt, cp[:40], desc))

# Show what attrs ARE being extracted for sample rows
print("\n=== SAMPLE ATTRIBUTE EXTRACTION ===")
for i in [0, 1, 10, 20, 30, 40, 50]:
    if i < len(out):
        r = out.iloc[i]
        attrs = []
        for j in range(1, 21):
            label = r.get('ATTRIBUTE_LABEL %d' % j, '')
            val = r.get('ATTRIBUTE_VALUE %d' % j, '')
            if label and val:
                attrs.append("%s=%s" % (label, val))
        print("Row %d [%s]: %s" % (i, r['Classpath'][:30], " | ".join(attrs[:6]) if attrs else "NONE"))

# ISSUE 2: Trademark symbols
print("\n=== ISSUE 2: TRADEMARK SYMBOLS ===")
has_tm = out['BRAND_NAME'].apply(lambda x: chr(174) in str(x) if x else False).sum()
print("Brands with symbol: %d / 959" % has_tm)
# Show sample brands
brands_with = out[out['BRAND_NAME'].apply(lambda x: chr(174) in str(x) if x else False)]['BRAND_NAME'].head(10).tolist()
brands_without = out[(out['BRAND_NAME'] != '') & (~out['BRAND_NAME'].apply(lambda x: chr(174) in str(x) if x else False))]['BRAND_NAME'].head(10).tolist()
print("With symbol:", brands_with[:5])
print("Without symbol:", brands_without[:5])

# ISSUE 3: Distributor detection
print("\n=== ISSUE 3: DISTRIBUTOR vs BRAND ===")
distributor_rows = []
for i, r in out.iterrows():
    manuf = str(r.get('MANUFACTURER_NAME', ''))
    brand = str(r.get('BRAND_NAME', ''))
    # Check for known distributor patterns
    if any(kw in manuf.lower() for kw in ['cooperative', 'distributor', 'supply', 'wholesale', 'cascade', 'parksite', 'building materials']):
        distributor_rows.append((i, manuf[:40], brand[:20], r['Part_Desc'][:40]))
print("Rows with distributor-like manufacturers: %d" % len(distributor_rows))
for idx, manuf, brand, desc in distributor_rows[:10]:
    print("  Row %d: Manuf=%s | Brand=%s | Desc=%s" % (idx, manuf, brand, desc))

# Also check appliance rows for wrong brand
print("\n=== APPLIANCE ROWS BRAND CHECK ===")
appliance_rows = out[out['Classpath'].str.contains('Appliance', na=False)]
for i, r in appliance_rows.head(10).iterrows():
    print("Row %d: Brand=%s | Manuf=%s | Desc=%s" % (i, r['BRAND_NAME'][:20], r['MANUFACTURER_NAME'][:30], r['Part_Desc'][:50]))
