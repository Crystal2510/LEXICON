import sys
sys.path.append(".")

from src.vector_store import find_similar

query = "bearing 625: outer diameter 16mm, width 5mm, material chrome steel"
results = find_similar("ball_bearings", query)

print("Closest matches found in memory:")
for doc in results["documents"][0]:
    print(" -", doc)