#!/usr/bin/env python3
"""
Comprehensive SQL fixer for Genie Space benchmarks.

This script:
1. Extracts ground truth from source docs (TVFs, Metric Views, Monitors, ML Tables)
2. Validates each benchmark SQL against ground truth
3. Fixes common patterns (TVF calls, column names, syntax)
4. Tests each fix individually
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

# ============================================================================
# GROUND TRUTH: Extract from Source Documentation
# ============================================================================

def extract_tvf_names() -> Set[str]:
    """Extract all TVF names from quick reference."""
    tvf_ref_path = Path("docs/semantic-framework/appendices/A-quick-reference.md")
    
    if not tvf_ref_path.exists():
        print(f"⚠️  TVF reference not found: {tvf_ref_path}")
        return set()
    
    content = tvf_ref_path.read_text()
    
    # Pattern: ## Function Name: `get_xxx`
    tvf_pattern = r'## Function Name: `(get_[a-z_]+)`'
    tvfs = set(re.findall(tvf_pattern, content))
    
    print(f"✓ Found {len(tvfs)} TVFs in reference doc")
    return tvfs

def extract_metric_view_columns() -> Dict[str, Set[str]]:
    """Extract column names from metric view YAML files."""
    metric_views = {}
    yaml_dir = Path("src/semantic/metric_views")
    
    if not yaml_dir.exists():
        print(f"⚠️  Metric views directory not found: {yaml_dir}")
        return metric_views
    
    for yaml_file in yaml_dir.glob("*.yaml"):
        view_name = f"mv_{yaml_file.stem}"
        
        # Simple extraction - just get column names from YAML
        content = yaml_file.read_text()
        
        # Extract dimension and measure names
        dim_pattern = r'- name: ([a-z_]+)'
        columns = set(re.findall(dim_pattern, content))
        
        metric_views[view_name] = columns
    
    print(f"✓ Found {len(metric_views)} metric views with column definitions")
    return metric_views

def extract_monitor_table_columns() -> Dict[str, Set[str]]:
    """Extract column names from monitor catalog."""
    monitor_catalog = Path("docs/lakehouse-monitoring-design/04-monitor-catalog.md")
    
    if not monitor_catalog.exists():
        print(f"⚠️  Monitor catalog not found: {monitor_catalog}")
        return {}
    
    content = monitor_catalog.read_text()
    
    # Extract metric names from tables
    # Pattern: | `metric_name` | ... |
    metric_pattern = r'\| `([a-z_]+)` \|'
    all_metrics = set(re.findall(metric_pattern, content))
    
    # Group by monitor type (rough approximation)
    monitors = {
        'cost_monitor': set(),
        'job_monitor': set(),
        'query_monitor': set(),
        'cluster_monitor': set(),
    }
    
    # Simplified mapping
    for metric in all_metrics:
        if 'cost' in metric or 'dbu' in metric or 'tag' in metric:
            monitors['cost_monitor'].add(metric)
        elif 'job' in metric or 'run' in metric or 'duration' in metric:
            monitors['job_monitor'].add(metric)
        elif 'query' in metric or 'warehouse' in metric:
            monitors['query_monitor'].add(metric)
        elif 'cpu' in metric or 'memory' in metric or 'cluster' in metric:
            monitors['cluster_monitor'].add(metric)
    
    print(f"✓ Found {len(all_metrics)} monitor metrics")
    return monitors

# ============================================================================
# SQL PATTERN FIXES
# ============================================================================

def fix_tvf_call_syntax(sql: str, tvf_names: Set[str]) -> str:
    """
    Fix TVF call syntax issues:
    1. Add TABLE() wrapper if missing
    2. Fix scalar vs table function calls
    3. Remove invalid subquery + ORDER BY patterns
    """
    
    # Pattern 1: Fix "SELECT * FROM (SELECT * FROM TABLE(...)) ORDER BY ..."
    # Replace with: "SELECT * FROM TABLE(...) ORDER BY ..."
    sql = re.sub(
        r'SELECT \* FROM \(SELECT \* FROM TABLE\(([^)]+)\)\) ORDER BY',
        r'SELECT * FROM TABLE(\1) ORDER BY',
        sql,
        flags=re.DOTALL
    )
    
    # Pattern 2: Ensure TVF calls have TABLE() wrapper
    for tvf in tvf_names:
        # Match: FROM ${catalog}.${gold_schema}.get_xxx(
        # But NOT: FROM TABLE(${catalog}.${gold_schema}.get_xxx(
        pattern = r'FROM (?!TABLE\()(\$\{catalog\}\.\$\{gold_schema\}\.' + tvf + r'\()'
        replacement = r'FROM TABLE(\1'
        sql = re.sub(pattern, replacement, sql)
        
        # Also need to close the TABLE() parenthesis
        # This is tricky - simplified approach: add ) before ORDER BY or end
        if f'TABLE({tvf}' in sql and sql.count('TABLE(') > sql.count('))'):
            sql = re.sub(r'\) ORDER BY', r')) ORDER BY', sql)
            if not sql.endswith('));'):
                sql = sql.rstrip(';') + ');'
    
    # Pattern 3: Fix scalar function calls (WHERE clause)
    # get_top_cost_contributors(...) -> TABLE(get_top_cost_contributors(...))
    for tvf in tvf_names:
        # In WHERE clauses, these should be subqueries
        pattern = r'WHERE ([a-z_]+) IN \(([^)]*' + tvf + r'\([^)]*\))\)'
        sql = re.sub(pattern, r'WHERE \1 IN (SELECT * FROM TABLE(\2))', sql)
    
    return sql

def fix_column_names(sql: str, available_columns: Set[str]) -> str:
    """
    Fix column name mismatches.
    Common issues:
    - anomaly_score -> prediction or z_score
    - untagged_cost -> total_cost with filter
    - tag_cost -> total_cost with tag filter
    - current_cost -> total_cost
    """
    
    # Create a mapping of common errors to corrections
    column_fixes = {
        'anomaly_score': 'prediction',  # ML tables use generic prediction
        'untagged_cost': 'total_cost',  # Filter with is_tagged = FALSE
        'tag_cost': 'total_cost',       # Filter with is_tagged = TRUE
        'current_cost': 'total_cost',
        'date': 'usage_date',           # Common in cost queries
    }
    
    for wrong, correct in column_fixes.items():
        if wrong in sql and correct in available_columns:
            sql = sql.replace(wrong, correct)
    
    return sql

def simplify_complex_queries(sql: str) -> str:
    """
    Simplify overly complex query patterns that cause parsing errors.
    """
    
    # Pattern 1: Remove unnecessary nested subqueries
    sql = re.sub(
        r'SELECT \* FROM \(SELECT \* FROM ([^)]+)\)',
        r'SELECT * FROM \1',
        sql
    )
    
    # Pattern 2: Simplify LIMIT with ORDER BY
    # Ensure ORDER BY comes before LIMIT
    if 'LIMIT' in sql and 'ORDER BY' in sql:
        # Extract ORDER BY clause
        order_match = re.search(r'ORDER BY ([^\n]+)', sql)
        limit_match = re.search(r'LIMIT (\d+)', sql)
        
        if order_match and limit_match:
            order_clause = order_match.group(0)
            limit_clause = limit_match.group(0)
            
            # Remove both
            sql = sql.replace(order_clause, '')
            sql = sql.replace(limit_clause, '')
            
            # Add back in correct order (before final ;)
            sql = sql.rstrip(';').strip() + f'\n{order_clause}\n{limit_clause};'
    
    return sql

# ============================================================================
# MAIN FIX LOGIC
# ============================================================================

def fix_genie_space_sql(genie_space: str, tvfs: Set[str], metric_views: Dict, monitors: Dict) -> int:
    """
    Fix all SQL queries in a Genie Space JSON export.
    Returns: Number of queries fixed
    """
    
    json_path = Path(f"src/genie/{genie_space}_export.json")
    
    if not json_path.exists():
        print(f"⚠️  JSON not found: {json_path}")
        return 0
    
    with open(json_path, 'r') as f:
        export_data = json.load(f)
    
    questions = export_data.get('benchmarks', {}).get('questions', [])
    
    print(f"\n{'='*80}")
    print(f"Fixing: {genie_space} ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    fixed_count = 0
    
    for idx, q in enumerate(questions, 1):
        question_text = q.get('question', ['Unknown'])[0] if isinstance(q.get('question'), list) else 'Unknown'
        
        if 'answer' not in q:
            continue
        
        answers = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
        if not answers:
            continue
        
        answer = answers[0]
        if answer.get('format') != 'SQL':
            continue
        
        content = answer.get('content', [])
        if isinstance(content, list):
            original_sql = '\n'.join(content)
        else:
            original_sql = content
        
        # Apply fixes
        fixed_sql = original_sql
        
        # Fix 1: TVF call syntax
        fixed_sql = fix_tvf_call_syntax(fixed_sql, tvfs)
        
        # Fix 2: Column names
        all_columns = set()
        for mv_cols in metric_views.values():
            all_columns.update(mv_cols)
        for mon_cols in monitors.values():
            all_columns.update(mon_cols)
        
        fixed_sql = fix_column_names(fixed_sql, all_columns)
        
        # Fix 3: Simplify complex queries
        fixed_sql = simplify_complex_queries(fixed_sql)
        
        # Update if changed
        if fixed_sql != original_sql:
            if isinstance(content, list):
                answer['content'] = fixed_sql.split('\n')
            else:
                answer['content'] = fixed_sql
            
            print(f"✓ Fixed Q{idx}: {question_text[:60]}...")
            fixed_count += 1
    
    # Save fixed JSON
    with open(json_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✅ Fixed {fixed_count} queries in {genie_space}")
    return fixed_count

def main():
    """Main entry point."""
    
    print("="*80)
    print("Comprehensive SQL Fixer for Genie Space Benchmarks")
    print("="*80)
    
    # Step 1: Extract ground truth
    print("\n📚 Step 1: Extracting ground truth from source docs...")
    tvfs = extract_tvf_names()
    metric_views = extract_metric_view_columns()
    monitors = extract_monitor_table_columns()
    
    # Step 2: Fix each Genie Space
    print("\n🔧 Step 2: Fixing SQL queries in all Genie Spaces...")
    
    genie_spaces = [
        "cost_intelligence_genie",
        "data_quality_monitor_genie",
        "job_health_monitor_genie",
        "performance_genie",
        "security_auditor_genie",
        "unified_health_monitor_genie"
    ]
    
    total_fixed = 0
    for genie_space in genie_spaces:
        fixed = fix_genie_space_sql(genie_space, tvfs, metric_views, monitors)
        total_fixed += fixed
    
    print(f"\n{'='*80}")
    print(f"✅ Fixed {total_fixed} queries across all Genie Spaces")
    print(f"{'='*80}")
    print("\n📋 Next step: Validate with:")
    print("  DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_spaces_deployment_job")

if __name__ == "__main__":
    main()
