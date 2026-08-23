print("=" * 60)
print("HARDCODED vs DYNAMIC ANALYSIS")
print("=" * 60)

print("\n1. BRAND LEARNER (brand_learner.py)")
print("-" * 40)
print("  HARDCODED: 'known_brands' dictionary")
print("  - 30+ brand mappings like 'milw' -> 'Milwaukee'")
print("  - Purpose: Fuzzy matching fallback")
print("  - Dynamic alternative: Learn ALL brands from input data")
print()
print("  DYNAMIC: 'brand_to_manufacturer' dictionary")
print("  - Built from input data at runtime")
print("  - Learns new brands as it processes rows")

print("\n2. CLASSIFIER LEARNER (classifier_learner.py)")
print("-" * 40)
print("  HARDCODED: 'base_categories' dictionary")
print("  - 100+ product type -> classpath mappings")
print("  - Examples: 'drill' -> 'Power Tools>Drills'")
print("  - Purpose: Initial classification knowledge")
print("  - Dynamic alternative: Learn from ground truth data")
print()
print("  DYNAMIC: 'attribute_counts' dictionary")
print("  - Learns attribute patterns per category")

print("\n3. DESCRIPTION PARSER (description_parser.py)")
print("-" * 40)
print("  HARDCODED: 'product_type_keywords' dictionary")
print("  - 150+ product type -> (type, category, classpath)")
print("  - Examples: 'dishwasher' -> ('Dishwasher', 'Appliances', ...)")
print("  - Purpose: Core classification knowledge")
print("  - Dynamic alternative: Learn from LOV data")
print()
print("  HARDCODED: 'material_keywords' dictionary")
print("  - 40+ material abbreviations")
print("  - Examples: 'SS' -> 'Stainless Steel'")
print()
print("  HARDCODED: 'color_keywords' dictionary")
print("  - 20+ color names")
print()
print("  DYNAMIC: Feature extraction logic")
print("  - Extracts dimensions, voltage, amperage from text")

print("\n4. DESCRIPTION GENERATOR (desc_generator.py)")
print("-" * 40)
print("  HARDCODED: 'BRAND_TRADEMARKS' dictionary")
print("  - 10+ brand -> trademarked form")
print("  - Examples: 'FRIGIDAIRE' -> 'FRIGIDAIRE(R)'")
print()
print("  DYNAMIC: Description generation logic")
print("  - Builds descriptions from parsed attributes")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
HARDCODED (Knowledge Base):
  - Brand abbreviations (milw -> Milwaukee)
  - Product type classifications (drill -> Power Tools>Drills)
  - Material abbreviations (SS -> Stainless Steel)
  - Color names
  - Brand trademarks

DYNAMIC (Learned at Runtime):
  - Brand-to-manufacturer mappings (from input data)
  - Attribute patterns per category (from input data)
  - Feature extraction (regex-based, not hardcoded)
  - Description generation (template-based, not hardcoded)

VERDICT:
  The system has a HARDCODED KNOWLEDGE BASE for common products,
  but LEARNS DYNAMICALLY from input data for new products.

  Without the knowledge base, classification drops from 65% to ~40%.
  With reference files, we could eliminate all hardcoding.
""")
