import pandas as pd
df = pd.read_csv('output/enriched_output.csv', dtype=str, keep_default_na=False)
general_count = len(df[df['Classpath'] == 'General'])
print(f"General: {general_count}")
print()
print("Classpath distribution:")
print(df['Classpath'].value_counts().head(20))
