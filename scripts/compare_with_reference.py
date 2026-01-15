#!/usr/bin/env python3
"""
Compare cost_intelligence with reference Genie Space export to find structural differences.
"""

import json

def analyze_structure(data, prefix=""):
    """Recursively analyze JSON structure."""
    structure = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                structure[f"{prefix}{key}"] = f"dict ({len(value)} keys)"
                structure.update(analyze_structure(value, f"{prefix}{key}."))
            elif isinstance(value, list):
                structure[f"{prefix}{key}"] = f"list ({len(value)} items)"
                if len(value) > 0:
                    structure[f"{prefix}{key}[0]"] = type(value[0]).__name__
            else:
                structure[f"{prefix}{key}"] = type(value).__name__
    
    return structure

# Load reference
with open("context/genie/genie_space_export.json", "r") as f:
    ref = json.load(f)

# Parse serialized_space from reference
ref_serialized = json.loads(ref["serialized_space"])

# Load transformed cost_intelligence
with open("debug_cost_transformed.json", "r") as f:
    cost = json.load(f)

print("=" * 80)
print("REFERENCE (working example)")
print("=" * 80)
ref_structure = analyze_structure(ref_serialized)
for key in sorted(ref_structure.keys()):
    print(f"  {key}: {ref_structure[key]}")

print("\n" + "=" * 80)
print("COST_INTELLIGENCE (failing)")
print("=" * 80)
cost_structure = analyze_structure(cost)
for key in sorted(cost_structure.keys()):
    print(f"  {key}: {cost_structure[key]}")

print("\n" + "=" * 80)
print("DIFFERENCES")
print("=" * 80)

# Find keys in reference but not in cost
missing_in_cost = set(ref_structure.keys()) - set(cost_structure.keys())
if missing_in_cost:
    print("\n❌ MISSING in cost_intelligence:")
    for key in sorted(missing_in_cost):
        print(f"  - {key}: {ref_structure[key]}")

# Find keys in cost but not in reference
extra_in_cost = set(cost_structure.keys()) - set(ref_structure.keys())
if extra_in_cost:
    print("\n⚠️  EXTRA in cost_intelligence:")
    for key in sorted(extra_in_cost):
        print(f"  + {key}: {cost_structure[key]}")

# Find type mismatches
print("\n🔄 TYPE MISMATCHES:")
common_keys = set(ref_structure.keys()) & set(cost_structure.keys())
mismatches = []
for key in sorted(common_keys):
    if ref_structure[key] != cost_structure[key]:
        mismatches.append((key, ref_structure[key], cost_structure[key]))

if mismatches:
    for key, ref_type, cost_type in mismatches:
        print(f"  {key}:")
        print(f"    Reference: {ref_type}")
        print(f"    Cost:      {cost_type}")
else:
    print("  None (all common fields have matching types)")

print("\n" + "=" * 80)
print("DETAILED FIELD COMPARISON")
print("=" * 80)

# Compare specific important fields
critical_fields = [
    "version",
    "config.sample_questions",
    "data_sources.tables",
    "data_sources.metric_views",
    "instructions"
]

for field in critical_fields:
    parts = field.split(".")
    
    # Get value from reference
    ref_val = ref_serialized
    for part in parts:
        ref_val = ref_val.get(part) if isinstance(ref_val, dict) else None
    
    # Get value from cost
    cost_val = cost
    for part in parts:
        cost_val = cost_val.get(part) if isinstance(cost_val, dict) else None
    
    print(f"\n{field}:")
    print(f"  Reference exists: {ref_val is not None}")
    print(f"  Cost exists: {cost_val is not None}")
    
    if ref_val is not None and cost_val is not None:
        print(f"  Reference type: {type(ref_val).__name__}")
        print(f"  Cost type: {type(cost_val).__name__}")
        
        if isinstance(ref_val, list) and isinstance(cost_val, list):
            print(f"  Reference count: {len(ref_val)}")
            print(f"  Cost count: {len(cost_val)}")
            
            if len(ref_val) > 0 and len(cost_val) > 0:
                print(f"  Reference[0] type: {type(ref_val[0]).__name__}")
                print(f"  Cost[0] type: {type(cost_val[0]).__name__}")
                
                if isinstance(ref_val[0], dict) and isinstance(cost_val[0], dict):
                    ref_keys = set(ref_val[0].keys())
                    cost_keys = set(cost_val[0].keys())
                    
                    if ref_keys != cost_keys:
                        missing = ref_keys - cost_keys
                        extra = cost_keys - ref_keys
                        
                        if missing:
                            print(f"  Missing keys in cost[0]: {missing}")
                        if extra:
                            print(f"  Extra keys in cost[0]: {extra}")

print("\n✅ Comparison complete!")
