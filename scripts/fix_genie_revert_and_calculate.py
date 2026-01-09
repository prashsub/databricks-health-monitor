#!/usr/bin/env python3
"""
Fix two manual errors from previous session:
1. Revert performance Q18: p99_seconds → p99_duration_seconds
2. Fix job_health_monitor Q14: Calculate duration_minutes from timestamps
"""
import json
import re
from pathlib import Path

def fix_performance_q18(json_file: Path) -> bool:
    """Revert the incorrect fix: p99_seconds → p99_duration_seconds"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = False
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Check if this is Q18 (P99 query duration)
            # Match based on SQL content and question text
            if 'MEASURE(p99_seconds)' in sql and 'P99 query duration' in question_text:
                # Revert: p99_seconds → p99_duration_seconds
                new_sql = sql.replace('p99_seconds', 'p99_duration_seconds')
                if new_sql != sql:
                    q['answer'][0]['content'][0] = new_sql
                    print(f"✅ performance Q18: Reverted MEASURE(p99_seconds) → MEASURE(p99_duration_seconds)")
                    fixed = True
    
    if fixed:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixed

def fix_job_health_monitor_q14(json_file: Path) -> bool:
    """Fix duration_minutes calculation from timestamps"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    fixed = False
    questions = data.get('benchmarks', {}).get('questions', [])
    for q in questions:
        if 'answer' in q and q['answer']:
            sql = q['answer'][0]['content'][0]
            question_text = ''.join(q.get('question', []))
            
            # Check if this is Q14 (pipeline health)
            if 'f.duration_minutes' in sql and 'pipeline health' in question_text:
                # Replace AVG(f.duration_minutes) with calculated duration
                new_sql = sql.replace(
                    'AVG(f.duration_minutes)',
                    'AVG((UNIX_TIMESTAMP(f.period_end_time) - UNIX_TIMESTAMP(f.period_start_time)) / 60)'
                )
                if new_sql != sql:
                    q['answer'][0]['content'][0] = new_sql
                    print(f"✅ job_health_monitor Q14: Calculate duration_minutes from period_start_time/period_end_time")
                    fixed = True
    
    if fixed:
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return fixed

def main():
    base_dir = Path('src/genie')
    
    # Fix 1: Revert performance Q18
    perf_file = base_dir / 'performance_genie_export.json'
    if fix_performance_q18(perf_file):
        print(f"✓ Fixed {perf_file.name}")
    
    # Fix 2: job_health_monitor Q14
    job_file = base_dir / 'job_health_monitor_genie_export.json'
    if fix_job_health_monitor_q14(job_file):
        print(f"✓ Fixed {job_file.name}")
    
    print("\n✅ All manual fixes applied!")

if __name__ == '__main__':
    main()

