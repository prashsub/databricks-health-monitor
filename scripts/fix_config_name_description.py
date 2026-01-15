#!/usr/bin/env python3
"""
Fix config.name and config.description in Genie Space JSON files.

Issue: config.name and config.description should NOT be in the config section.
       They should be at the top level only (title/description in API payload).
Error: BAD_REQUEST: Invalid JSON in field 'serialized_space'
"""

import json

def fix_config_fields(json_file):
    """Remove config.name and config.description fields."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    removed = []
    if "config" in data:
        if "name" in data["config"]:
            del data["config"]["name"]
            removed.append("name")
        if "description" in data["config"]:
            del data["config"]["description"]
            removed.append("description")
    
    if removed:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ {json_file}: Removed config.{', config.'.join(removed)}")
        return True
    else:
        print(f"  {json_file}: Already correct (no config.name/description)")
        return False


if __name__ == "__main__":
    files = [
        "src/genie/cost_intelligence_genie_export.json",
        "src/genie/performance_genie_export.json",
    ]
    
    fixed_count = 0
    for file in files:
        if fix_config_fields(file):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} file(s)")
    print("   These fields belong at the top level of the API payload")
    print("   (title/description), not in serialized_space.config")
