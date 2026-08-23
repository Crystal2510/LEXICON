import sys
sys.path.insert(0, '.')
from src.pipeline import ProductPipeline
import pandas as pd

pipeline = ProductPipeline()
input_df = pd.read_csv('data/sample_input.csv', dtype=str, keep_default_na=False)
input_data = input_df.to_dict('records')
pipeline.initialize(input_data=input_data)

# Process ALL 1000 rows for full picture
print("Processing all 1000 rows...")
out = pipeline.process_dataframe(input_df)
print(f"Done. Output: {out.shape}")

total = len(out)

# ---- METRIC 1: Brand Fill Rate ----
brand_filled = (out['BRAND_NAME'] != '').sum()
print(f"\n[1] BRAND FILL RATE:       {brand_filled}/{total} = {brand_filled/total*100:.1f}%")

# ---- METRIC 2: Classpath NOT General/Empty ----
classified = out['Classpath'].apply(lambda x: str(x).strip() not in ('', 'General')).sum()
print(f"[2] CLASSIFIED (non-generic): {classified}/{total} = {classified/total*100:.1f}%")

# ---- METRIC 3: Classpath distribution ----
print(f"\n[3] TOP CLASSPATHS:")
for cp, cnt in out['Classpath'].value_counts().head(12).items():
    print(f"     {cnt:4d}x  {cp}")

# ---- METRIC 4: Invoice Desc ALL CAPS + <=40 ----
inv_ok = out['INVOICE_DESC'].apply(lambda x: bool(x.strip()) and x == x.upper() and len(x) <= 40).sum()
inv_empty = (out['INVOICE_DESC'].str.strip() == '').sum()
print(f"\n[4] INVOICE DESC OK (CAPS+<=40): {inv_ok}/{total} = {inv_ok/total*100:.1f}%  (empty: {inv_empty})")

# ---- METRIC 5: Mobile Desc 60-80 ----
mob_ok = out['MOBILE_DESC'].apply(lambda x: 60 <= len(x) <= 80).sum()
mob_empty = (out['MOBILE_DESC'].str.strip() == '').sum()
print(f"[5] MOBILE DESC OK (60-80 chars): {mob_ok}/{total} = {mob_ok/total*100:.1f}%  (empty: {mob_empty})")

# ---- METRIC 6: Short Desc filled ----
short_filled = (out['SHORT_DESC'].str.strip() != '').sum()
print(f"[6] SHORT DESC FILLED:     {short_filled}/{total} = {short_filled/total*100:.1f}%")

# ---- METRIC 7: Attributes >=3 ----
def attr_count(row):
    return sum(1 for j in range(1,11) if str(row.get(f'ATTRIBUTE_VALUE {j}','')).strip())
attrs = out.apply(attr_count, axis=1)
attr3 = (attrs >= 3).sum()
attr1 = (attrs >= 1).sum()
print(f"[7] ATTRS >= 1: {attr1}/{total} = {attr1/total*100:.1f}%   >= 3: {attr3}/{total} = {attr3/total*100:.1f}%")
print(f"    Avg attrs per row: {attrs.mean():.1f}")

# ---- METRIC 8: UNSPSC filled ----
unspsc_filled = (out['UNSPSC'].str.strip() != '').sum()
print(f"[8] UNSPSC FILLED:         {unspsc_filled}/{total} = {unspsc_filled/total*100:.1f}%")

# ---- METRIC 9: Confidence distribution ----
scores = out['CONFIDENCE_SCORE'].str.replace('%','',regex=False).astype(float)
high = (scores >= 80).sum()
mid  = ((scores >= 50) & (scores < 80)).sum()
low  = (scores < 50).sum()
print(f"\n[9] CONFIDENCE SCORES:")
print(f"    High (>=80%):    {high}/{total} = {high/total*100:.1f}%")
print(f"    Mid  (50-79%):   {mid}/{total}  = {mid/total*100:.1f}%")
print(f"    Low  (<50%):     {low}/{total}  = {low/total*100:.1f}%")
print(f"    Average: {scores.mean():.1f}%")

needs_review = (out['NEEDS_REVIEW'] == 'Yes').sum()
print(f"    Needs Review:    {needs_review}/{total} = {needs_review/total*100:.1f}%")

# ---- METRIC 10: Compare against expected output ----
print("\n[10] EXACT MATCH vs EXPECTED OUTPUT (2 ground truth rows):")
exp = pd.read_csv('data/expected_output.csv', dtype=str, keep_default_na=False)
for ei in range(len(exp)):
    exp_row = exp.iloc[ei]
    exp_mpn = exp_row.get('Mfg_Part_Num','').strip()
    matched = out[out['Mfg_Part_Num'].str.strip() == exp_mpn]
    print(f"\n  MPN: {exp_mpn}")
    if len(matched) > 0:
        got = matched.iloc[0]
        fields = ['BRAND_NAME','MANUFACTURER_NAME','Classpath','INVOICE_DESC','MOBILE_DESC','SHORT_DESC']
        for field in fields:
            exp_val = str(exp_row.get(field,'')).strip()
            got_val = str(got.get(field,'')).strip()
            exact = exp_val.lower() == got_val.lower()
            fuzzy_ok = exp_val.lower()[:30] in got_val.lower() or got_val.lower()[:30] in exp_val.lower()
            flag = '[EXACT  ]' if exact else ('[PARTIAL]' if fuzzy_ok else '[WRONG  ]')
            print(f"    {flag} | {field}")
            if not exact:
                print(f"           EXPECTED: {exp_val[:75]!r}")
                print(f"           GOT:      {got_val[:75]!r}")
    else:
        # Process that specific row directly
        exp_input_mpn_row = input_df[input_df['Mfg_Part_Num'].str.strip() == exp_mpn]
        if len(exp_input_mpn_row) > 0:
            row_out = pipeline.process_row(exp_input_mpn_row.iloc[0].to_dict())
            fields = ['BRAND_NAME','MANUFACTURER_NAME','Classpath','INVOICE_DESC','MOBILE_DESC','SHORT_DESC']
            for field in fields:
                exp_val = str(exp_row.get(field,'')).strip()
                got_val = str(row_out.get(field,'')).strip()
                exact = exp_val.lower() == got_val.lower()
                fuzzy_ok = len(exp_val) > 5 and (exp_val.lower()[:25] in got_val.lower() or got_val.lower()[:25] in exp_val.lower())
                flag = '[EXACT  ]' if exact else ('[PARTIAL]' if fuzzy_ok else '[WRONG  ]')
                print(f"    {flag} | {field}")
                if not exact:
                    print(f"           EXPECTED: {exp_val[:75]!r}")
                    print(f"           GOT:      {got_val[:75]!r}")
        else:
            print(f"  MPN {exp_mpn} not found in input at all")

print("\n=== DONE ===")
