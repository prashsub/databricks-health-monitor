#!/usr/bin/env python3
"""
Fix cost_intelligence missing data_sources.tables field.

Issue: API requires data_sources.tables even if empty.
Error: BAD_REQUEST: Invalid JSON in field 'serialized_space'
"""

import json

def fix_missing_tables():
    """Add empty tables array if missing."""
    
    json_file = "src/genie/cost_intelligence_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Ensure data_sources exists
    if "data_sources" not in data:
        data["data_sources"] = {}
    
    # Add tables if missing
    if "tables" not in data["data_sources"]:
        data["data_sources"]["tables"] = []
        print("✓ Added empty data_sources.tables array")
    else:
        print("  Already has data_sources.tables")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_missing_tables()
    print("\n✅ All fixes complete!")
    print("   data_sources.tables is now present (empty array)")
    print("   Deploy: databricks bundle deploy -t dev")
