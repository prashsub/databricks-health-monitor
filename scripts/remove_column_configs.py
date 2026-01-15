#!/usr/bin/env python3
"""
Remove column_configs from metric_views and tables in failing Genie Spaces.

Hypothesis: column_configs triggers Unity Catalog schema validation that fails.
The 3 successful spaces (cost_intelligence, performance, security_auditor) don't have column_configs.
The 3 failing spaces (job_health_monitor, data_quality_monitor, unified_health_monitor) do have them.

This script removes column_configs to test if that resolves the INTERNAL_ERROR.
"""

import json
import os

def remove_column_configs_from_file(json_file: str) -> int:
    """Remove column_configs from a single file. Returns count of configs removed."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    removed_count = 0
    
    # Remove from tables
    if "data_sources" in data and "tables" in data["data_sources"]:
        for table in data["data_sources"]["tables"]:
            if "column_configs" in table:
                count = len(table["column_configs"])
                del table["column_configs"]
                removed_count += count
                print(f"  Removed {count} column_configs from table: {table.get('identifier', 'unknown')[:60]}...")
    
    # Remove from metric_views
    if "data_sources" in data and "metric_views" in data["data_sources"]:
        for mv in data["data_sources"]["metric_views"]:
            if "column_configs" in mv:
                count = len(mv["column_configs"])
                del mv["column_configs"]
                removed_count += count
                print(f"  Removed {count} column_configs from metric_view: {mv.get('identifier', 'unknown')[:60]}...")
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return removed_count


def main():
    """Remove column_configs from the 3 failing Genie Spaces."""
    
    failing_files = [
        "src/genie/job_health_monitor_genie_export.json",
        "src/genie/data_quality_monitor_genie_export.json",
        "src/genie/unified_health_monitor_genie_export.json"
    ]
    
    print("="*100)
    print("REMOVE COLUMN_CONFIGS FROM FAILING GENIE SPACES")
    print("="*100)
    print("\nHypothesis: column_configs triggers Unity Catalog schema validation that fails")
    print("The 3 successful spaces don't have column_configs.")
    print("Let's remove them from the 3 failing spaces to test.\n")
    
    total_removed = 0
    
    for json_file in failing_files:
        print(f"\n{os.path.basename(json_file)}:")
        count = remove_column_configs_from_file(json_file)
        total_removed += count
        print(f"  ✓ Removed {count} total column_configs")
    
    print(f"\n{'='*100}")
    print(f"SUMMARY")
    print(f"{'='*100}")
    print(f"Files modified: {len(failing_files)}")
    print(f"Total column_configs removed: {total_removed}")
    print(f"\n✅ Files updated!")
    print(f"\nNext steps:")
    print(f"  1. Deploy: databricks bundle deploy -t dev")
    print(f"  2. Test: databricks bundle run -t dev genie_spaces_deployment_job")
    print(f"  3. Expect: All 6 spaces to succeed if column_configs was the issue")


if __name__ == "__main__":
    main()
