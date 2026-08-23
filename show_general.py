import pandas as pd
df = pd.read_csv('output/enriched_output.csv', dtype=str, keep_default_na=False)
general = df[df['Classpath'] == 'General']
print(f"Products classified as General: {len(general)} out of {len(df)}")
print()
print("Sample General products:")
for i in range(min(20, len(general))):
    desc = str(general.iloc[i]['Part_Desc'])
    print(f"  {desc!r}")
