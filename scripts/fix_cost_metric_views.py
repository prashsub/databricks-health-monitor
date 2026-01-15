#!/usr/bin/env python3
"""
Fix cost_intelligence metric_views format.

Issue: metric_views have {id, name, full_name, description} instead of {identifier, description}
Reference: context/genie/genie_space_export.json shows correct format
"""

import json

def fix_metric_views():
    """Transform metric_views from custom format to API format."""
    
    json_file = "src/genie/cost_intelligence_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Fix data_sources.metric_views
    if "data_sources" in data and "metric_views" in data["data_sources"]:
        mvs = data["data_sources"]["metric_views"]
        
        fixed_count = 0
        for i, mv in enumerate(mvs):
            if "full_name" in mv:
                # Transform: full_name → identifier
                new_mv = {
                    "identifier": mv["full_name"]
                }
                
                # Keep description if it exists (optional field)
                if "description" in mv:
                    desc = mv["description"]
                    # Ensure description is array
                    if isinstance(desc, str):
                        new_mv["description"] = [desc]
                    else:
                        new_mv["description"] = desc
                
                # Keep column_configs if exists
                if "column_configs" in mv:
                    new_mv["column_configs"] = mv["column_configs"]
                
                # Show what we're removing
                removed = [k for k in mv.keys() if k not in ["full_name", "description", "column_configs"]]
                if removed:
                    print(f"  Metric View [{i}]: Removing fields: {removed}")
                
                data["data_sources"]["metric_views"][i] = new_mv
                fixed_count += 1
        
        if fixed_count > 0:
            print(f"✓ Fixed {fixed_count} metric views")
            print(f"\n❌ BEFORE: {{'id': '...', 'name': '...', 'full_name': 'catalog.schema.mv', ...}}")
            print(f"✅ AFTER: {{'identifier': 'catalog.schema.mv', ...}}")
        else:
            print("✓ metric_views already in correct format")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_metric_views()
    print("\n✅ Fix complete!")
    print("   Reference: context/genie/genie_space_export.json")
