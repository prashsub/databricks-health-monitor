#!/usr/bin/env python3
"""
COMPREHENSIVE FIX: Hardcode ALL template variables in ALL sections of ALL Genie Space JSON files.

Previous fix only addressed data_sources.tables.
This fix addresses:
1. data_sources.metric_views[*].identifier
2. instructions.sql_functions[*].identifier
3. instructions.join_specs[*].left.identifier
4. instructions.join_specs[*].right.identifier
5. ${feature_schema} → system_gold_ml
"""

import json
from pathlib import Path

# Hardcoded schema paths
SYSTEM_GOLD = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold"
SYSTEM_GOLD_ML = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_ml"
SYSTEM_GOLD_MONITORING = "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring"

def hardcode_identifier(identifier: str) -> str:
    """Convert template variable identifier to hardcoded path."""
    if not identifier:
        return identifier
    
    # Replace ${catalog}.${gold_schema} with hardcoded path
    identifier = identifier.replace("${catalog}.${gold_schema}", SYSTEM_GOLD)
    
    # Replace ${catalog}.${feature_schema} with ML schema
    identifier = identifier.replace("${catalog}.${feature_schema}", SYSTEM_GOLD_ML)
    
    # Replace ${catalog}.${gold_schema}_monitoring with monitoring schema
    identifier = identifier.replace("${catalog}.${gold_schema}_monitoring", SYSTEM_GOLD_MONITORING)
    
    return identifier

def fix_genie_space_comprehensive(json_path: Path) -> int:
    """Fix ALL template variables in a Genie Space JSON file."""
    
    data = json.load(open(json_path))
    fix_count = 0
    
    print(f"\n{'=' * 80}")
    print(f"FIXING: {json_path.name}")
    print(f"{'=' * 80}")
    
    # 1. Fix data_sources.metric_views
    print("\n1. Fixing metric_views identifiers...")
    for mv in data.get('data_sources', {}).get('metric_views', []):
        old_id = mv.get('identifier', '')
        new_id = hardcode_identifier(old_id)
        if old_id != new_id:
            mv['identifier'] = new_id
            fix_count += 1
            print(f"   ✓ Fixed: {old_id.split('.')[-1]}")
    
    # 2. Fix instructions.sql_functions
    print("\n2. Fixing sql_functions identifiers...")
    for tvf in data.get('instructions', {}).get('sql_functions', []):
        old_id = tvf.get('identifier', '')
        new_id = hardcode_identifier(old_id)
        if old_id != new_id:
            tvf['identifier'] = new_id
            fix_count += 1
            print(f"   ✓ Fixed: {old_id.split('.')[-1]}")
    
    # 3. Fix instructions.join_specs
    print("\n3. Fixing join_specs identifiers...")
    for join in data.get('instructions', {}).get('join_specs', []):
        # Fix left.identifier
        left = join.get('left', {})
        old_id = left.get('identifier', '')
        new_id = hardcode_identifier(old_id)
        if old_id != new_id:
            left['identifier'] = new_id
            fix_count += 1
            print(f"   ✓ Fixed left: {old_id.split('.')[-1]}")
        
        # Fix right.identifier
        right = join.get('right', {})
        old_id = right.get('identifier', '')
        new_id = hardcode_identifier(old_id)
        if old_id != new_id:
            right['identifier'] = new_id
            fix_count += 1
            print(f"   ✓ Fixed right: {old_id.split('.')[-1]}")
    
    # Save the fixed JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Total fixes: {fix_count}")
    return fix_count

def main():
    """Fix all 6 Genie Space JSON files."""
    
    genie_files = [
        "src/genie/cost_intelligence_genie_export.json",
        "src/genie/security_auditor_genie_export.json",
        "src/genie/performance_genie_export.json",
        "src/genie/job_health_monitor_genie_export.json",
        "src/genie/data_quality_monitor_genie_export.json",
        "src/genie/unified_health_monitor_genie_export.json"
    ]
    
    total_fixes = 0
    
    print("=" * 80)
    print("COMPREHENSIVE TEMPLATE VARIABLE FIX")
    print("=" * 80)
    print("\nFixing ALL sections:")
    print("  1. data_sources.metric_views[*].identifier")
    print("  2. instructions.sql_functions[*].identifier")
    print("  3. instructions.join_specs[*].left.identifier")
    print("  4. instructions.join_specs[*].right.identifier")
    
    for file_path in genie_files:
        path = Path(file_path)
        if path.exists():
            fixes = fix_genie_space_comprehensive(path)
            total_fixes += fixes
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print("\n" + "=" * 80)
    print(f"COMPLETE: Fixed {total_fixes} template variables across all Genie Spaces")
    print("=" * 80)

if __name__ == "__main__":
    main()
