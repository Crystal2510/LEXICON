import sys
sys.path.append("..")  # so it can find the src folder
from src.vector_store import add_product

known_bearings = [
    {"id": "626",  "bore_mm": 6,  "outer_mm": 19, "width_mm": 6,  "material": "chrome steel"},
    {"id": "608",  "bore_mm": 8,  "outer_mm": 22, "width_mm": 7,  "material": "chrome steel"},
    {"id": "6000", "bore_mm": 10, "outer_mm": 26, "width_mm": 8,  "material": "chrome steel"},
    {"id": "6200", "bore_mm": 10, "outer_mm": 30, "width_mm": 9,  "material": "chrome steel"},
    {"id": "6300", "bore_mm": 10, "outer_mm": 35, "width_mm": 11, "material": "chrome steel"},
]

for b in known_bearings:
    text = f"bearing {b['id']}: bore {b['bore_mm']}mm, outer diameter {b['outer_mm']}mm, width {b['width_mm']}mm, material {b['material']}"
    add_product("ball_bearings", b["id"], text, b)

print(f"Saved {len(known_bearings)} bearings into memory.")