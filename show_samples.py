import pandas as pd
df = pd.read_csv('output/enriched_output.csv', dtype=str, keep_default_na=False)

# Show some sample outputs
print("Sample outputs (first 10 rows):")
for i in range(10):
    print(f"Row {i+1}:")
    pd_val = str(df.iloc[i]['Part_Desc'])
    bn = str(df.iloc[i]['BRAND_NAME'])
    cp = str(df.iloc[i]['Classpath'])
    md = str(df.iloc[i]['MOBILE_DESC'])
    sd = str(df.iloc[i]['SHORT_DESC'])[:100]
    print(f"  Part_Desc: {pd_val!r}")
    print(f"  BRAND_NAME: {bn!r}")
    print(f"  Classpath: {cp!r}")
    print(f"  MOBILE_DESC: {md!r}")
    print(f"  SHORT_DESC: {sd!r}")
    print()

# Show brand distribution
print("Brand distribution:")
print(df['BRAND_NAME'].value_counts().head(15))
print()

# Show classpath distribution
print("Classpath distribution:")
print(df['Classpath'].value_counts().head(15))
