#!/usr/bin/env python3
"""
Convert ALL hardcoded paths back to template variables in ALL Genie Space JSON files.

Converts:
- prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold → ${catalog}.${gold_schema}
- prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml → ${catalog}.${feature_schema}
- prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring → ${catalog}.${gold_schema}_monitoring
"""

import json
import re
from pathlib import Path

# Hardcoded patterns
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def convert_identifier(identifier: str) -> str:
    """Convert hardcoded identifier to template variable."""
    # Convert monitoring tables
    if SYSTEM_GOLD_MONITORING in identifier:
        return identifier.replace(SYSTEM_GOLD_MONITORING, "${catalog}.${gold_schema}_monitoring")
    # Convert ML tables
    elif SYSTEM_GOLD_ML in identifier:
        return identifier.replace(SYSTEM_GOLD_ML, "${catalog}.${feature_schema}")
    # Convert Gold tables
    elif SYSTEM_GOLD in identifier:
        return identifier.replace(SYSTEM_GOLD, "${catalog}.${gold_schema}")
    # Already template
    return identifier

def convert_json_recursively(obj):
    """Recursively convert all identifiers in JSON structure."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'identifier' and isinstance(value, str):
                obj[key] = convert_identifier(value)
            else:
                convert_json_recursively(value)
    elif isinstance(obj, list):
        for item in obj:
            convert_json_recursively(item)

def convert_genie_space(json_file: Path):
    """Convert a single Genie Space JSON file."""
    data = json.load(open(json_file))
    
    # Convert all identifiers recursively
    convert_json_recursively(data)
    
    # Save
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return json_file.stem

def main():
    """Convert all Genie Space JSON files."""
    
    genie_files = [
        Path("src/genie/cost_intelligence_genie_export.json"),
        Path("src/genie/security_auditor_genie_export.json"),
        Path("src/genie/performance_genie_export.json"),
        Path("src/genie/job_health_monitor_genie_export.json"),
        Path("src/genie/data_quality_monitor_genie_export.json"),
        Path("src/genie/unified_health_monitor_genie_export.json")
    ]
    
    print("=" * 80)
    print("CONVERTING HARDCODED PATHS TO TEMPLATE VARIABLES")
    print("=" * 80)
    print()
    
    total_fixed = 0
    
    for json_file in genie_files:
        # Count hardcoded paths before
        data_before = json.load(open(json_file))
        before_str = json.dumps(data_before)
        before_count = before_str.count(SYSTEM_GOLD)
        
        # Convert
        name = convert_genie_space(json_file)
        
        # Count after
        data_after = json.load(open(json_file))
        after_str = json.dumps(data_after)
        after_count = after_str.count(SYSTEM_GOLD)
        
        converted_count = before_count - after_count
        total_fixed += converted_count
        
        print(f"✅ {name:35s} | Converted: {converted_count:3d} hardcoded paths")
    
    print()
    print("=" * 80)
    print(f"✅ CONVERSION COMPLETE: {total_fixed} total paths converted")
    print("=" * 80)
    print()
    print("Template Variables Used:")
    print("  - ${catalog}.${gold_schema}.table_name")
    print("  - ${catalog}.${feature_schema}.ml_table_name")
    print("  - ${catalog}.${gold_schema}_monitoring.monitoring_table_name")

if __name__ == "__main__":
    main()
