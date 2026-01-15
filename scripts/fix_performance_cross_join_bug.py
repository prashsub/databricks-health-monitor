#!/usr/bin/env python3
"""
Fix CROSS JOIN concatenation bug in performance_genie_export.json.

Issue: Same as cost_intelligence - previous regex replacement incorrectly 
       concatenated alias with CROSS keyword.
"""

import json

def fix_performance_cross_join():
    """Fix qhCROSS alias bug in performance Q23."""
    
    json_file = "src/genie/performance_genie_export.json"
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Find Q23 (id for performance deep research query)
    benchmarks = data.get("benchmarks", {}).get("questions", [])
    
    fixed_count = 0
    for q in benchmarks:
        question_text = q["question"][0]
        
        if "End-to-end performance health dashboard" in question_text:
            print(f"Found Q (performance deep research): {question_text[:80]}...")
            
            # Get SQL
            sql = q["answer"][0]["content"][0]
            
            # Show issue
            if "qhCROSS" in sql:
                print("❌ BEFORE: Contains 'qhCROSS' (invalid alias)")
                
                # Fix: qhCROSS → qh (with proper spacing for CROSS JOIN)
                sql = sql.replace("qhCROSS.", "qh.")
                sql = sql.replace("query_health qhCROSS", "query_health qh CROSS")
                
                print("✅ AFTER: Fixed to 'qh' alias with 'CROSS JOIN'")
                
                # Update
                q["answer"][0]["content"][0] = sql
                fixed_count += 1
    
    if fixed_count == 0:
        print("⚠ No 'qhCROSS' found - may have been fixed already")
        return
    
    # Write back
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated: {json_file}")


if __name__ == "__main__":
    fix_performance_cross_join()
    print("\n✅ All fixes complete!")
    print("   This prevents the same BAD_REQUEST error in performance space")
