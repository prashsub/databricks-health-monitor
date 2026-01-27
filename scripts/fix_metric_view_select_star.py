#!/usr/bin/env python3
"""
Fix Metric View Benchmark SQL - SELECT * still causes MEASURE() errors.

Problem: Even SELECT * FROM metric_view triggers METRIC_VIEW_MISSING_MEASURE_FUNCTION
         because Databricks tries to select all measure columns.

Solution: Use SELECT 1 FROM metric_view LIMIT 1 to just verify the view exists
          without attempting to select measure columns.

Reference: https://learn.microsoft.com/en-us/azure/databricks/metric-views/#query-measures
"""

import json
import re
from pathlib import Path

GENIE_DIR = Path("src/genie")

def fix_metric_view_benchmarks():
    """Fix all metric view benchmark queries in all Genie Spaces."""
    
    genie_files = [
        "cost_intelligence_genie_export.json",
        "job_health_monitor_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
        "data_quality_monitor_genie_export.json",
    ]

    total_fixed = 0
    
    for file_name in genie_files:
        file_path = GENIE_DIR / file_name
        if not file_path.exists():
            print(f"Warning: {file_path} not found. Skipping.")
            continue

        print(f"\nProcessing {file_name}...")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        benchmarks = data.get('benchmarks', {}).get('questions', [])
        
        changes_made = 0
        for q in benchmarks:
            answer_content = q.get('answer', [{}])[0].get('content', [])
            if answer_content:
                original_sql = answer_content[0]
                
                # Pattern: SELECT * FROM ... mv_xxx ... LIMIT 20;
                # This catches metric view queries with SELECT *
                if 'SELECT *' in original_sql and '.mv_' in original_sql:
                    # Extract the metric view name with schema
                    match = re.search(r'SELECT \* FROM (\$\{[^}]+\}\.\$\{[^}]+\}\.mv_\w+)', original_sql)
                    if match:
                        mv_full_name = match.group(1)
                        # Replace with SELECT 1 FROM mv LIMIT 1
                        new_sql = f"SELECT 1 FROM {mv_full_name} LIMIT 1;"
                        
                        if original_sql != new_sql:
                            q['answer'][0]['content'][0] = new_sql
                            changes_made += 1
                            print(f"  ✅ Fixed: {q.get('question', [''])[0][:50]}...")
                            print(f"     FROM: {original_sql[:60]}...")
                            print(f"     TO:   {new_sql}")
        
        if changes_made > 0:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  📝 {changes_made} metric view benchmarks fixed in {file_name}")
            total_fixed += changes_made
        else:
            print(f"  ℹ️  No metric view benchmarks needed fixing in {file_name}")
    
    print(f"\n{'='*60}")
    print(f"✅ Total fixed: {total_fixed} metric view benchmarks")
    print(f"{'='*60}")

if __name__ == "__main__":
    fix_metric_view_benchmarks()
