#!/usr/bin/env python3
"""
Fix ALL table references in Genie Space JSON files to use hardcoded schema paths.

Problem: Template variables ${catalog}.${gold_schema} don't work in Genie UI.
Solution: Use hardcoded prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.{table}

This is consistent with how ML and Monitoring tables work.
"""

import json
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

# Genie Space files
GENIE_FILES = [
    "src/genie/cost_intelligence_genie_export.json",
    "src/genie/security_auditor_genie_export.json",
    "src/genie/performance_genie_export.json",
    "src/genie/job_health_monitor_genie_export.json",
    "src/genie/data_quality_monitor_genie_export.json",
    "src/genie/unified_health_monitor_genie_export.json"
]

def fix_table_schemas(genie_file: str):
    """Fix all table schema references in a Genie Space JSON file."""
    path = Path(genie_file)
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    fixes = 0
    
    # Fix tables in data_sources.tables
    if 'data_sources' in data and 'tables' in data['data_sources']:
        for table in data['data_sources']['tables']:
            identifier = table['identifier']
            table_name = identifier.split('.')[-1]
            
            # Skip if already hardcoded correctly
            if SYSTEM_GOLD in identifier or SYSTEM_GOLD_ML in identifier or SYSTEM_GOLD_MONITORING in identifier:
                continue
            
            # Determine correct schema
            if '_predictions' in table_name or '_recommendations' in table_name or '_features' in table_name:
                new_schema = SYSTEM_GOLD_ML
            elif 'profile_metrics' in table_name or 'drift_metrics' in table_name:
                new_schema = SYSTEM_GOLD_MONITORING
            else:
                # Standard Gold table (dim/fact)
                new_schema = SYSTEM_GOLD
            
            old_identifier = identifier
            new_identifier = f"{new_schema}.{table_name}"
            
            if old_identifier != new_identifier:
                table['identifier'] = new_identifier
                fixes += 1
                print(f"  Fixed: {table_name}")
                print(f"    OLD: {old_identifier}")
                print(f"    NEW: {new_identifier}")
    
    if fixes > 0:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Fixed {fixes} table references in {path.name}")
    else:
        print(f"  No template variables found in {path.name} (all hardcoded)")
    
    return fixes

def main():
    """Fix table schema references in all Genie Space JSON files."""
    print("Fixing ALL table schema references to use hardcoded paths...")
    print("=" * 80)
    
    total_fixes = 0
    
    for genie_file in GENIE_FILES:
        print(f"\nProcessing {genie_file}...")
        fixes = fix_table_schemas(genie_file)
        total_fixes += fixes
    
    print("\n" + "=" * 80)
    print(f"✓ Total fixes applied: {total_fixes}")
    print("\nAll tables now use hardcoded schema paths:")
    print(f"  Standard Gold: {SYSTEM_GOLD}.table_name")
    print(f"  ML Predictions: {SYSTEM_GOLD_ML}.table_name")
    print(f"  Monitoring: {SYSTEM_GOLD_MONITORING}.table_name")

if __name__ == "__main__":
    main()