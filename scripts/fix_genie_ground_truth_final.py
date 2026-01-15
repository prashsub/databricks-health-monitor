#!/usr/bin/env python3
"""
Fix remaining Genie SQL bugs that can be resolved using ground truth.

Based on validation results, these are fixable:
1. Remove/fix references to non-existent columns in ML tables
2. Fix date casting issues in WHERE clauses

Session: Final Ground Truth Fixes
Date: 2026-01-09
"""

import json
import re
from pathlib import Path


def check_ml_table_columns(table_name: str, ground_truth_path: Path) -> list:
    """Read ML table columns from ground truth."""
    ml_file = ground_truth_path / "ml.md"
    if not ml_file.exists():
        return []
    
    with open(ml_file, 'r') as f:
        lines = f.readlines()
    
    columns = []
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) >= 4 and table_name in parts[2]:
            columns.append(parts[3])
    
    return list(set(columns))


def check_tvf_columns(tvf_name: str, ground_truth_path: Path) -> dict:
    """Extract TVF return columns from ground truth."""
    tvf_file = ground_truth_path / "tvfs.md"
    if not tvf_file.exists():
        return {}
    
    with open(tvf_file, 'r') as f:
        content = f.read()
    
    # Find the TVF definition
    pattern = rf'{tvf_name}.*?FUNCTION.*?TABLE_TYPE.*?"(.*?)"'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        sql_def = match.group(1)
        # Extract column names from SELECT statement
        # Look for patterns like: column_name AS alias, column_name,
        cols = re.findall(r'(\w+)\s+AS\s+\w+|,\s*(\w+)\s*(?:,|FROM)', sql_def)
        return {"found": True, "definition": sql_def[:500]}
    
    return {"found": False}


def fix_json_file(json_path: Path, ground_truth_path: Path) -> int:
    """Fix SQL queries in a JSON file using ground truth. Returns number of fixes."""
    print(f"\n{'='*80}")
    print(f"Processing: {json_path.name}")
    print(f"{'='*80}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixes_applied = 0
    questions = data.get('benchmarks', {}).get('questions', [])
    
    # Check ML table columns
    ml_tables_checked = {}
    
    for idx, question_data in enumerate(questions, 1):
        q_num = f"Q{idx}"
        
        answer_list = question_data.get('answer', [])
        if not answer_list:
            continue
            
        content_list = answer_list[0].get('content', [])
        if not content_list:
            continue
        
        original_query = ''.join(content_list)
        fixed_query = original_query
        
        # Check if query references cluster_capacity_predictions ML table
        if 'cluster_capacity_predictions' in original_query:
            if 'cluster_capacity_predictions' not in ml_tables_checked:
                cols = check_ml_table_columns('cluster_capacity_predictions', ground_truth_path)
                ml_tables_checked['cluster_capacity_predictions'] = cols
                print(f"\n📋 cluster_capacity_predictions columns: {', '.join(cols[:10])}...")
            
            # Check for non-existent columns
            if 'potential_savings_usd' in original_query and 'potential_savings_usd' not in ml_tables_checked['cluster_capacity_predictions']:
                print(f"\n  {q_num}: ⚠️  potential_savings_usd not in ML table")
                print(f"     Available columns don't include potential_savings_usd")
                print(f"     This query may need redesign (skipping auto-fix)")
        
        # Fix date casting issues in WHERE clauses
        # Pattern: WHERE DATE(column) >= '7' or similar
        date_cast_pattern = r"WHERE\s+DATE\([^)]+\)\s*>=\s*['\"](\d+)['\"]"
        if re.search(date_cast_pattern, original_query, re.IGNORECASE):
            print(f"\n  {q_num}: 🔧 Fixing date casting in WHERE clause")
            # Replace '7' with proper date expression
            fixed_query = re.sub(
                r"WHERE\s+DATE\(([^)]+)\)\s*>=\s*['\"](\d+)['\"]",
                r"WHERE DATE(\1) >= CURRENT_DATE() - INTERVAL \2 DAYS",
                fixed_query,
                flags=re.IGNORECASE
            )
            if fixed_query != original_query:
                print(f"     ✓ Fixed: '7' → CURRENT_DATE() - INTERVAL 7 DAYS")
        
        # Update if changed
        if fixed_query != original_query:
            answer_list[0]['content'] = [fixed_query]
            fixes_applied += 1
            print(f"     ✅ Applied fix to {q_num}")
    
    # Write back if fixes were made
    if fixes_applied > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n{'='*80}")
        print(f"✅ {fixes_applied} fix(es) applied to {json_path.name}")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"ℹ️  No automatic fixes applied")
        print(f"{'='*80}")
    
    return fixes_applied


def main():
    """Fix remaining Genie SQL bugs using ground truth."""
    print("="*80)
    print("GENIE GROUND TRUTH FINAL FIXES")
    print("="*80)
    print("\nUsing ground truth from: docs/reference/actual_assets/")
    print()
    
    genie_dir = Path("src/genie")
    ground_truth_dir = Path("docs/reference/actual_assets")
    
    if not ground_truth_dir.exists():
        print(f"❌ Ground truth directory not found: {ground_truth_dir}")
        return
    
    json_files = [
        "cost_intelligence_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
        "job_health_monitor_genie_export.json",
        "data_quality_monitor_genie_export.json"
    ]
    
    total_fixes = 0
    
    for filename in json_files:
        json_path = genie_dir / filename
        if json_path.exists():
            fixes = fix_json_file(json_path, ground_truth_dir)
            total_fixes += fixes
    
    print()
    print("="*80)
    if total_fixes > 0:
        print(f"✅ COMPLETE: {total_fixes} fix(es) applied!")
        print("="*80)
        print("\nNext steps:")
        print("  1. Deploy: databricks bundle deploy -t dev")
        print("  2. Validate: databricks bundle run -t dev genie_benchmark_sql_validation_job")
    else:
        print("ℹ️  No automatic fixes applied")
        print("="*80)
        print("\nNote: Some errors may require manual investigation:")
        print("  - UUID casting errors (TVF bugs)")
        print("  - Complex query redesigns")


if __name__ == "__main__":
    main()

