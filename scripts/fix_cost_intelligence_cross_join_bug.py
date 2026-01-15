#!/usr/bin/env python3
"""
Fix CROSS JOIN concatenation bug in cost_intelligence_genie_export.json.

Issue: Previous regex replacement incorrectly concatenated alias with CROSS keyword
  Before: FROM sku_costs sc CROSS JOIN
  After: FROM sku_costs scCROSS JOIN  ❌

This causes invalid SQL which leads to BAD_REQUEST: Invalid JSON in 'serialized_space'
"""

import json
import re

def fix_cost_intelligence_cross_join():
    """Fix scCROSS alias bug in cost_intelligence Q23."""
    
    json_file = "src/genie/cost_intelligence_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Find Q23 (id: d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a6)
    benchmarks = data.get("benchmarks", {}).get("questions", [])
    
    for q in benchmarks:
        if q.get("id") == "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a6":
            print(f"Found Q23: {q['question'][0][:80]}...")
            
            # Get SQL
            sql = q["answer"][0]["content"][0]
            
            # Show issue
            if "scCROSS" in sql:
                print("❌ BEFORE: Contains 'scCROSS' (invalid alias)")
                
                # Fix: scCROSS → sc (with proper spacing for CROSS JOIN)
                # Pattern 1: scCROSS.column_name → sc.column_name
                sql = sql.replace("scCROSS.", "sc.")
                
                # Pattern 2: FROM sku_costs scCROSS JOIN → FROM sku_costs sc CROSS JOIN
                sql = sql.replace("FROM sku_costs scCROSS", "FROM sku_costs sc CROSS")
                
                print("✅ AFTER: Fixed to 'sc' alias with 'CROSS JOIN'")
                
                # Update
                q["answer"][0]["content"][0] = sql
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_cost_intelligence_cross_join()
    print("\n✅ All fixes complete!")
    print("   Deploy: databricks bundle deploy -t dev")
    print("   Test: Run genie_spaces_deployment_job")
