import sys, re
sys.path.insert(0, '.')
from src.pipeline import ProductPipeline
import pandas as pd

input_df = pd.read_csv('data/sample_input.csv', dtype=str, keep_default_na=False)
pipeline = ProductPipeline()
pipeline.initialize(input_data=input_df.to_dict('records'))

out = pipeline.process_dataframe(input_df)

# ---- 1. What are the 92 General rows? ----
general = out[out['Classpath'] == 'General']
print(f"=== GENERAL ROWS ({len(general)}) ===")
for _, row in general.iterrows():
    print(f"  Manuf={row['Part_Manuf'][:30]:30s} | Brand={row['BRAND_NAME']:12s} | Desc={row['Part_Desc'][:55]}")

# ---- 2. Attribute count distribution ----
def attr_count(row):
    return sum(1 for j in range(1,51) if str(row.get(f'ATTRIBUTE_VALUE {j}','')).strip())

out['attr_count'] = out.apply(attr_count, axis=1)
print(f"\n=== ATTRIBUTE COUNT DISTRIBUTION ===")
print(out['attr_count'].value_counts().sort_index().to_string())

# ---- 3. Rows with 0 attributes by classpath ----
zero_attrs = out[out['attr_count'] == 0]
print(f"\n=== ROWS WITH 0 ATTRIBUTES by classpath ({len(zero_attrs)} rows) ===")
print(zero_attrs['Classpath'].value_counts().head(15).to_string())

# ---- 4. Sample zero-attr rows per category ----
for cp in zero_attrs['Classpath'].value_counts().head(5).index:
    sample = zero_attrs[zero_attrs['Classpath'] == cp].head(3)
    print(f"\n  [{cp}]")
    for _, r in sample.iterrows():
        print(f"    Desc: {r['Part_Desc'][:65]}")

# ---- 5. Mobile desc failures ----
mob_fail = out[~out['MOBILE_DESC'].apply(lambda x: 60 <= len(x) <= 80)]
print(f"\n=== MOBILE DESC FAILURES ({len(mob_fail)}) ===")
print(mob_fail['Classpath'].value_counts().head(10).to_string())
print("\nSamples:")
for _, r in mob_fail.head(10).iterrows():
    print(f"  len={len(r['MOBILE_DESC']):3d} cp={r['Classpath'][:30]:30s} -> {r['MOBILE_DESC'][:60]!r}")

# ---- 6. UNSPSC analysis ----
print(f"\n=== UNSPSC GAPS ===")
no_unspsc = out[out['UNSPSC'].str.strip() == '']
print(f"Rows missing UNSPSC: {len(no_unspsc)}")
print("Top classpaths missing UNSPSC:")
print(no_unspsc['Classpath'].value_counts().head(10).to_string())

# ---- 7. Partial classpath rows (broad, not leaf) ----
partial = out[out['Classpath'].apply(lambda x: 0 < x.count('>') < 2 and x != 'General')]
print(f"\n=== BROAD (non-leaf) CLASSPATHS ({len(partial)}) ===")
print(partial['Classpath'].value_counts().head(10).to_string())
for _, r in partial.head(5).iterrows():
    print(f"  cp={r['Classpath']:40s} | desc={r['Part_Desc'][:50]}")
