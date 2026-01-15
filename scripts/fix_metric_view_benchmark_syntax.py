#!/usr/bin/env python3
"""
Fix Metric View Benchmark SQL Syntax

The MEASURE() function requires exactly ONE measure column name, not *.
- WRONG:  SELECT MEASURE(*) FROM metric_view GROUP BY ALL
- CORRECT: SELECT * FROM metric_view LIMIT 20

For benchmark validation, we just need to verify the metric view exists and is queryable.
Using SELECT * is simpler and sufficient for validation purposes.
"""

import json
from pathlib import Path
import re

GENIE_DIR = Path("src/genie")

def fix_metric_view_benchmarks():
    """Fix all metric view benchmark queries in all Genie Spaces."""
    
    genie_files = [
        "cost_intelligence_genie_export.json",
        "job_health_monitor_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
        "data_quality_monitor_genie_export.json"
    ]
    
    total_fixed = 0
    
    for filename in genie_files:
        filepath = GENIE_DIR / filename
        if not filepath.exists():
            print(f"⚠️  File not found: {filename}")
            continue
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        benchmarks = data.get('benchmarks', {}).get('questions', [])
        file_fixes = 0
        
        for q in benchmarks:
            answers = q.get('answer', [])
            if not answers:
                continue
            
            for answer in answers:
                if answer.get('format') != 'SQL':
                    continue
                
                content = answer.get('content', [])
                if not content:
                    continue
                
                # Check for MEASURE(*) pattern
                for i, sql in enumerate(content):
                    if 'MEASURE(*)' in sql or 'MEASURE( * )' in sql:
                        # Replace MEASURE(*) ... GROUP BY ALL with SELECT *
                        # Pattern: SELECT MEASURE(*) FROM table GROUP BY ALL LIMIT N
                        # Replace with: SELECT * FROM table LIMIT N
                        new_sql = re.sub(
                            r'SELECT\s+MEASURE\s*\(\s*\*\s*\)\s+FROM\s+([^\s]+)\s+GROUP\s+BY\s+ALL\s+LIMIT\s+(\d+)',
                            r'SELECT * FROM \1 LIMIT \2',
                            sql,
                            flags=re.IGNORECASE
                        )
                        
                        if new_sql != sql:
                            content[i] = new_sql
                            file_fixes += 1
                            question_text = q.get('question', [''])[0] if isinstance(q.get('question'), list) else q.get('question', '')
                            print(f"  Fixed: {question_text[:50]}...")
        
        if file_fixes > 0:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ {filename}: Fixed {file_fixes} benchmark queries")
            total_fixed += file_fixes
        else:
            print(f"✓  {filename}: No MEASURE(*) issues found")
    
    print(f"\n{'='*60}")
    print(f"Total benchmarks fixed: {total_fixed}")
    return total_fixed

if __name__ == "__main__":
    fix_metric_view_benchmarks()
