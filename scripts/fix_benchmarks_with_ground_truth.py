#!/usr/bin/env python3
"""
Fix benchmark questions to use only deployed assets from ground truth.

Strategy:
1. Extract ground truth from documentation
2. Identify invalid asset references
3. Replace with similar valid assets
4. Rewrite SQL to use correct syntax
"""

import re
from pathlib import Path
from typing import Dict, Set, List, Tuple

# ============================================================================
# Extract Ground Truth
# ============================================================================

def extract_tvf_names() -> Dict[str, Dict]:
    """Extract TVF names with their signatures from quick reference."""
    tvf_ref_path = Path("docs/semantic-framework/appendices/A-quick-reference.md")
    content = tvf_ref_path.read_text()
    
    tvfs = {}
    # Pattern: | `get_xxx` | params | ... |
    for line in content.split('\n'):
        if line.startswith('| `get_'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                tvf_name = parts[1].strip('`')
                required_params = parts[2]
                optional_params = parts[3]
                tvfs[tvf_name] = {
                    'required': required_params,
                    'optional': optional_params
                }
    
    print(f"✓ Found {len(tvfs)} TVFs")
    return tvfs

def extract_metric_views() -> Set[str]:
    """Extract metric view names."""
    mv_ref_path = Path("docs/semantic-framework/24-metric-views-reference.md")
    content = mv_ref_path.read_text()
    
    metric_views = set(re.findall(r'### (mv_[a-z_]+)', content))
    print(f"✓ Found {len(metric_views)} Metric Views")
    return metric_views

def extract_ml_tables() -> Dict[str, str]:
    """Extract ML table names with their output column from model catalog."""
    ml_catalog = Path("docs/ml-framework-design/07-model-catalog.md")
    content = ml_catalog.read_text()
    
    ml_tables = {}
    # Most ML tables use generic 'prediction' column
    for line in content.split('\n'):
        if '| **' in line and ('predictions' in line or 'scores' in line or 'recommendations' in line):
            match = re.search(r'\*\*([a-z_]+(?:predictions|scores|recommendations))\*\*', line)
            if match:
                table_name = match.group(1)
                ml_tables[table_name] = 'prediction'  # Default column
    
    print(f"✓ Found {len(ml_tables)} ML Tables")
    return ml_tables

def extract_monitor_tables() -> Set[str]:
    """Extract Lakehouse Monitor table names."""
    monitor_catalog = Path("docs/lakehouse-monitoring-design/04-monitor-catalog.md")
    content = monitor_catalog.read_text()
    
    # Pattern: | `table_name` | ... | **Profile & Drift** |
    sources = set()
    for line in content.split('\n'):
        match = re.search(r'\| `([a-z_]+)` \|.*\*\*Profile & Drift\*\*', line)
        if match:
            sources.add(match.group(1))
    
    monitor_tables = set()
    for source in sources:
        monitor_tables.add(f"{source}_profile_metrics")
        monitor_tables.add(f"{source}_drift_metrics")
    
    print(f"✓ Found {len(monitor_tables)} Monitor Tables")
    return monitor_tables

def extract_gold_tables() -> Tuple[Set[str], Set[str]]:
    """Extract fact and dimension tables from YAML."""
    yaml_dir = Path("gold_layer_design/yaml")
    
    fact_tables = set()
    dim_tables = set()
    
    for yaml_file in yaml_dir.rglob("*.yaml"):
        table_name = yaml_file.stem
        if table_name.startswith("fact_"):
            fact_tables.add(table_name)
        elif table_name.startswith("dim_"):
            dim_tables.add(table_name)
    
    print(f"✓ Found {len(fact_tables)} Fact Tables, {len(dim_tables)} Dim Tables")
    return fact_tables, dim_tables

# ============================================================================
# Fix Strategies
# ============================================================================

def find_replacement_tvf(invalid_tvf: str, valid_tvfs: Dict) -> str:
    """Find a similar valid TVF to replace invalid one."""
    
    # Simple replacements based on naming patterns
    replacements = {
        'get_untagged_resources': 'get_tag_coverage',  # Tag-related
        'get_cost_anomalies': 'get_cost_anomaly_analysis',  # Anomaly detection
        'get_daily_cost_summary': 'get_cost_mtd_summary',  # Summary
        'get_cost_by_tag': 'get_spend_by_custom_tags',  # Tag analysis
        'get_job_cost_breakdown': 'get_most_expensive_jobs',  # Job cost
        'get_warehouse_cost_analysis': 'get_warehouse_utilization',  # Warehouse
        'get_cost_by_cluster_type': 'get_cluster_cost_efficiency',  # Cluster cost
        'get_top_cost_contributors': 'get_top_cost_contributors',  # Valid!
        'get_serverless_vs_classic_cost': 'get_cost_efficiency_metrics',  # Efficiency
        'get_cost_forecast': 'get_cost_mtd_summary',  # Forecast fallback
        'get_cost_by_owner': 'get_top_cost_contributors',  # Owner
        'get_data_quality_summary': 'get_table_activity_summary',  # Quality fallback
        'get_table_freshness': 'get_table_activity_summary',  # Freshness
        'get_tables_failing_quality': 'get_table_activity_summary',  # Failing
        'get_pipeline_data_lineage': 'get_table_lineage',  # Lineage
        'get_table_activity_status': 'get_table_activity_summary',  # Activity
        'get_job_data_quality_status': 'get_table_activity_summary',  # Job quality
        'get_data_freshness_by_domain': 'get_table_activity_summary',  # Domain
        'get_failed_jobs': 'get_failed_jobs_summary',  # Failed jobs
        'get_job_success_rate': 'get_job_success_rates',  # Success rates
        'get_most_expensive_jobs': 'get_most_expensive_jobs',  # Valid!
        'get_job_failure_patterns': 'get_job_failure_trends',  # Patterns
        'get_slow_queries': 'get_slowest_queries',  # Slow queries
        'get_warehouse_utilization': 'get_warehouse_performance',  # Warehouse
        'get_underutilized_clusters': 'get_cluster_utilization',  # Clusters
        'get_jobs_without_autoscaling': 'get_autoscaling_disabled_jobs',  # Autoscaling
        'get_jobs_on_legacy_dbr': 'get_legacy_dbr_jobs',  # Legacy DBR
        'get_cluster_rightsizing': 'get_cluster_rightsizing_recommendations',  # Right-sizing
        'get_user_activity_summary': 'get_user_activity',  # User activity
        'get_sensitive_table_access': 'get_sensitive_data_access',  # Sensitive
        'get_failed_actions': 'get_failed_access_attempts',  # Failed
        'get_permission_changes': 'get_permission_change_history',  # Permissions
        'get_off_hours_activity': 'get_off_hours_access',  # Off-hours
    }
    
    # Check if the replacement exists in valid TVFs
    replacement = replacements.get(invalid_tvf, None)
    if replacement and replacement in valid_tvfs:
        return replacement
    
    # If no direct replacement, try to find something similar
    invalid_words = set(invalid_tvf.split('_'))
    best_match = None
    best_score = 0
    
    for valid_tvf in valid_tvfs:
        valid_words = set(valid_tvf.split('_'))
        overlap = len(invalid_words & valid_words)
        if overlap > best_score:
            best_score = overlap
            best_match = valid_tvf
    
    return best_match if best_score >= 2 else None

def create_genie_space_fixes(space_name: str, ground_truth: Dict) -> List[Dict]:
    """
    Create a list of fixes for a Genie Space.
    Returns list of {question_num, old_sql, new_sql, changes}
    """
    
    md_path = Path(f"src/genie/{space_name}.md")
    if not md_path.exists():
        print(f"⚠️  Not found: {md_path}")
        return []
    
    content = md_path.read_text()
    
    # Extract all benchmark questions
    questions = []
    pattern = r'### Question (\d+): "([^"]+)"\n\*\*Expected SQL:\*\*\n```sql\n(.*?)\n```'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        q_num = int(match.group(1))
        q_text = match.group(2)
        q_sql = match.group(3)
        
        questions.append({
            'num': q_num,
            'text': q_text,
            'sql': q_sql
        })
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {space_name} ({len(questions)} questions)")
    print(f"{'='*80}\n")
    
    fixes = []
    
    for q in questions:
        sql = q['sql']
        changes = []
        new_sql = sql
        
        # Check for invalid TVFs
        tvf_matches = re.findall(r'get_[a-z_]+\(', sql)
        for tvf_call in tvf_matches:
            tvf_name = tvf_call.rstrip('(')
            if tvf_name not in ground_truth['tvfs']:
                replacement = find_replacement_tvf(tvf_name, ground_truth['tvfs'])
                if replacement:
                    new_sql = new_sql.replace(tvf_name, replacement)
                    changes.append(f"TVF: {tvf_name} → {replacement}")
                else:
                    changes.append(f"TVF NOT FOUND: {tvf_name} (no replacement)")
        
        # Check for invalid metric views
        mv_matches = re.findall(r'mv_[a-z_]+', sql)
        for mv in mv_matches:
            if mv not in ground_truth['metric_views']:
                changes.append(f"METRIC VIEW NOT FOUND: {mv}")
        
        # Check for invalid ML tables
        ml_matches = re.findall(r'(?:predictions|scores|recommendations)', sql)
        for ml_ref in ml_matches:
            # Extract full table name
            ml_match = re.search(r'([a-z_]+(?:predictions|scores|recommendations))', sql)
            if ml_match:
                ml_table = ml_match.group(1)
                if ml_table not in ground_truth['ml_tables']:
                    changes.append(f"ML TABLE NOT FOUND: {ml_table}")
        
        if changes:
            fixes.append({
                'question_num': q['num'],
                'question_text': q['text'],
                'old_sql': sql,
                'new_sql': new_sql,
                'changes': changes
            })
            
            print(f"Q{q['num']}: {q['text'][:60]}...")
            for change in changes:
                print(f"  - {change}")
    
    print(f"\nFound {len(fixes)} questions needing fixes")
    return fixes

# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    
    print("="*80)
    print("Fix Benchmarks Using Ground Truth")
    print("="*80)
    
    # Step 1: Extract ground truth
    print("\n📚 Extracting ground truth...")
    
    ground_truth = {
        'tvfs': extract_tvf_names(),
        'metric_views': extract_metric_views(),
        'ml_tables': extract_ml_tables(),
        'monitor_tables': extract_monitor_tables()
    }
    
    fact_tables, dim_tables = extract_gold_tables()
    ground_truth['fact_tables'] = fact_tables
    ground_truth['dim_tables'] = dim_tables
    
    print(f"\n📊 Ground Truth Summary:")
    print(f"  - TVFs: {len(ground_truth['tvfs'])}")
    print(f"  - Metric Views: {len(ground_truth['metric_views'])}")
    print(f"  - ML Tables: {len(ground_truth['ml_tables'])}")
    print(f"  - Monitor Tables: {len(ground_truth['monitor_tables'])}")
    print(f"  - Fact Tables: {len(ground_truth['fact_tables'])}")
    print(f"  - Dim Tables: {len(ground_truth['dim_tables'])}")
    
    # Step 2: Analyze each Genie Space
    print("\n🔍 Analyzing Genie Spaces...")
    
    genie_spaces = [
        "cost_intelligence_genie",
        "data_quality_monitor_genie",
        "job_health_monitor_genie",
        "performance_genie",
        "security_auditor_genie",
        "unified_health_monitor_genie"
    ]
    
    all_fixes = {}
    for space in genie_spaces:
        fixes = create_genie_space_fixes(space, ground_truth)
        if fixes:
            all_fixes[space] = fixes
    
    # Step 3: Report
    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}")
    
    total_fixes = sum(len(fixes) for fixes in all_fixes.values())
    print(f"Total questions needing fixes: {total_fixes}")
    
    for space, fixes in all_fixes.items():
        print(f"\n{space}: {len(fixes)} questions")
        
        # Count fix types
        tvf_fixes = sum(1 for f in fixes if any('TVF:' in c for c in f['changes']))
        ml_fixes = sum(1 for f in fixes if any('ML TABLE' in c for c in f['changes']))
        mv_fixes = sum(1 for f in fixes if any('METRIC VIEW' in c for c in f['changes']))
        
        print(f"  - TVF fixes: {tvf_fixes}")
        print(f"  - ML table fixes: {ml_fixes}")
        print(f"  - Metric view fixes: {mv_fixes}")

if __name__ == "__main__":
    main()
