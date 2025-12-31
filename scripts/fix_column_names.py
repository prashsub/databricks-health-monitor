#!/usr/bin/env python3
"""
Fix Column Names in Training Scripts
=====================================

Maps incorrect column names to actual feature table columns.

Feature Table Schemas (from create_feature_tables.py):

COST_FEATURES (PK: workspace_id, usage_date):
  - daily_dbu, daily_cost, jobs_on_all_purpose_cost, jobs_on_all_purpose_count
  - serverless_cost, dlt_cost, model_serving_cost
  - avg_dbu_7d, std_dbu_7d, avg_dbu_30d, std_dbu_30d
  - z_score_7d, z_score_30d
  - day_of_week, is_weekend, day_of_month, is_month_end
  - dow_sin, dow_cos
  - dbu_change_pct_1d, dbu_change_pct_7d
  - potential_job_cluster_savings, all_purpose_inefficiency_ratio, serverless_adoption_ratio

SECURITY_FEATURES (PK: user_id, event_date):
  - event_count, tables_accessed, off_hours_events, unique_source_ips
  - failed_auth_count, sensitive_data_access
  - avg_event_count_7d, std_event_count_7d, avg_tables_accessed_7d
  - event_count_z_score, off_hours_rate, sensitive_access_rate
  - is_human_user, is_service_principal, is_system_user
  - is_activity_burst, lateral_movement_risk, failed_auth_ratio
  - is_weekend, day_of_week

PERFORMANCE_FEATURES (PK: warehouse_id, query_date):
  - query_count, total_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms
  - total_bytes_read, total_bytes_written, error_count, spill_count
  - sla_breach_count, efficient_query_count, high_queue_count, large_query_count
  - total_queue_time_ms, active_minutes
  - avg_duration_ms, avg_query_count_7d, avg_duration_7d, avg_p99_duration_7d
  - error_rate, spill_rate, avg_bytes_per_query, read_write_ratio
  - sla_breach_rate, query_efficiency_rate, high_queue_rate, large_query_rate
  - avg_queue_time_ms, queries_per_minute
  - is_weekend, day_of_week

RELIABILITY_FEATURES (PK: job_id, run_date):
  - total_runs, successful_runs, failed_runs
  - avg_duration_sec, std_duration_sec, min_duration_sec, max_duration_sec
  - p50_duration_sec, p95_duration_sec, p99_duration_sec
  - success_rate, failure_rate, duration_cv
  - rolling_failure_rate_30d, rolling_avg_duration_30d
  - total_failures_30d, total_repairs_30d
  - duration_trend_7d, is_duration_regressing
  - repair_cost_efficiency
  - is_weekend, day_of_week

QUALITY_FEATURES (PK: catalog_name, snapshot_date):
  - total_tables, total_columns, tables_with_pk, tables_with_comments
  - columns_with_comments, tag_coverage
"""

import re
from pathlib import Path

ML_DIR = Path(__file__).parent.parent / "src" / "ml"

# Column name mappings (wrong -> correct)
COLUMN_REPLACEMENTS = {
    # Cost features
    '"sku_name"': '# "sku_name" - NOT IN FEATURE TABLE',
    "'sku_name'": "# 'sku_name' - NOT IN FEATURE TABLE",
    '"job_count"': '"jobs_on_all_purpose_count"',
    "'job_count'": "'jobs_on_all_purpose_count'",
    
    # Performance features - LOOKUP KEY FIX
    '"compute_warehouse_id"': '"warehouse_id"',
    "'compute_warehouse_id'": "'warehouse_id'",
    '"total_read_bytes"': '"total_bytes_read"',
    "'total_read_bytes'": "'total_bytes_read'",
    
    # Reliability features  
    '"rolling_avg_failure_rate_30d"': '"rolling_failure_rate_30d"',
    "'rolling_avg_failure_rate_30d'": "'rolling_failure_rate_30d'",
}

# Lookup key fixes (in create_training_set_with_features)
LOOKUP_KEY_FIXES = {
    # Performance: compute_warehouse_id -> warehouse_id
    'lookup_key=["compute_warehouse_id", "query_date"]': 'lookup_key=["warehouse_id", "query_date"]',
    "lookup_key=['compute_warehouse_id', 'query_date']": "lookup_key=['warehouse_id', 'query_date']",
}

# Feature name list fixes
FEATURE_LIST_FIXES = [
    # Remove non-existent features from feature_names lists
    (r'"job_count",?\s*', ''),
    (r"'job_count',?\s*", ''),
    (r'"total_read_bytes",?\s*', '"total_bytes_read", '),
    (r"'total_read_bytes',?\s*", "'total_bytes_read', "),
    (r'"rolling_avg_failure_rate_30d",?\s*', '"rolling_failure_rate_30d", '),
    (r"'rolling_avg_failure_rate_30d',?\s*", "'rolling_failure_rate_30d', "),
]

# Base DataFrame column fixes (for .select() calls)
BASE_DF_FIXES = [
    # Cost features: remove sku_name from base_df
    (r'\.select\("workspace_id", "sku_name", "usage_date"', '.select("workspace_id", "usage_date"'),
    (r"\.select\('workspace_id', 'sku_name', 'usage_date'", ".select('workspace_id', 'usage_date'"),
    
    # Performance features: compute_warehouse_id -> warehouse_id
    (r'\.select\("compute_warehouse_id", "query_date"', '.select("warehouse_id", "query_date"'),
    (r"\.select\('compute_warehouse_id', 'query_date'", ".select('warehouse_id', 'query_date'"),
    
    # F.col references
    (r'F\.col\("compute_warehouse_id"\)', 'F.col("warehouse_id")'),
    (r"F\.col\('compute_warehouse_id'\)", "F.col('warehouse_id')"),
]


def fix_script(script_path: Path):
    """Apply column name fixes to a training script."""
    content = script_path.read_text()
    original = content
    
    # Apply direct replacements
    for old, new in COLUMN_REPLACEMENTS.items():
        content = content.replace(old, new)
    
    # Apply lookup key fixes
    for old, new in LOOKUP_KEY_FIXES.items():
        content = content.replace(old, new)
    
    # Apply regex-based feature list fixes
    for pattern, replacement in FEATURE_LIST_FIXES:
        content = re.sub(pattern, replacement, content)
    
    # Apply base DataFrame fixes
    for pattern, replacement in BASE_DF_FIXES:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        script_path.write_text(content)
        return True
    return False


def main():
    print("=" * 60)
    print("Fixing Column Names in Training Scripts")
    print("=" * 60)
    
    scripts = []
    for domain in ["cost", "security", "performance", "reliability", "quality"]:
        domain_dir = ML_DIR / domain
        if domain_dir.exists():
            scripts.extend(domain_dir.glob("train_*.py"))
    
    print(f"\nFound {len(scripts)} training scripts")
    
    fixed = 0
    for script in sorted(scripts):
        modified = fix_script(script)
        symbol = "✓" if modified else "·"
        print(f"  {symbol} {script.parent.name}/{script.name}")
        if modified:
            fixed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Fixed {fixed}/{len(scripts)} scripts")
    print("=" * 60)


if __name__ == "__main__":
    main()

