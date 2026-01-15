#!/usr/bin/env python3
"""
Fix final 2 Genie Space deployment issues - Session 24.

Issues:
1. data_quality_monitor: Table 'fact_governance_metrics_profile_metrics' does not exist
2. unified_health_monitor: Exceeded maximum (50) certified answer inputs (sql_functions)
"""

import json
from pathlib import Path


def fix_data_quality_monitor():
    """Remove non-existent fact_governance_metrics_profile_metrics table."""
    json_path = Path("src/genie/data_quality_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    original_count = len(data['data_sources']['tables'])
    
    # Remove the non-existent table
    data['data_sources']['tables'] = [
        t for t in data['data_sources']['tables']
        if 'fact_governance_metrics_profile_metrics' not in t.get('identifier', '')
    ]
    
    removed = original_count - len(data['data_sources']['tables'])
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"data_quality_monitor: Removed {removed} non-existent table(s)")
    return removed


def fix_unified_health_monitor():
    """Reduce sql_functions to 50 (maximum certified answer inputs)."""
    json_path = Path("src/genie/unified_health_monitor_genie_export.json")
    
    with open(json_path) as f:
        data = json.load(f)
    
    sql_funcs = data['instructions']['sql_functions']
    original_count = len(sql_funcs)
    
    if original_count <= 50:
        print(f"unified_health_monitor: Already has {original_count} sql_functions (≤50)")
        return 0
    
    # Remove the last 3 functions to get to 50
    # These are the lowest priority functions (added last)
    to_remove = original_count - 50
    data['instructions']['sql_functions'] = sql_funcs[:50]
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"unified_health_monitor: Removed {to_remove} sql_functions ({original_count} → 50)")
    return to_remove


def main():
    """Fix both remaining deployment issues."""
    print("=" * 80)
    print("SESSION 24 FINAL FIXES")
    print("=" * 80)
    print()
    
    fixes1 = fix_data_quality_monitor()
    fixes2 = fix_unified_health_monitor()
    
    print()
    print(f"Total fixes: {fixes1 + fixes2}")
    print("=" * 80)


if __name__ == "__main__":
    main()
