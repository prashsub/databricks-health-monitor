#!/usr/bin/env python3
"""
Local Dashboard SQL Validator

Validates dashboard SQL queries locally before deployment.
This script performs static analysis and basic syntax checking without needing Databricks.

For full schema validation, use the Databricks notebook version.

Usage:
    python scripts/validate_dashboard_sql_local.py

Requirements:
    pip install sqlparse
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import sqlparse
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False
    print("Warning: sqlparse not installed. Install with: pip install sqlparse")
    print("Proceeding with basic validation only.\n")


# Known columns in each table (based on Gold layer schema)
KNOWN_COLUMNS = {
    'fact_usage': [
        'usage_date', 'workspace_id', 'sku_name', 'list_cost', 'list_price',
        'usage_quantity', 'usage_unit', 'cloud', 'account_id', 'custom_tags',
        'is_tagged', 'tag_team', 'tag_project', 'tag_cost_center', 'usage_metadata'
    ],
    'fact_job_run_timeline': [
        'run_id', 'job_id', 'workspace_id', 'run_date', 'run_name', 'run_type',
        'result_state', 'termination_code', 'is_success', 'run_duration_seconds',
        'run_duration_minutes', 'period_start_time', 'period_end_time', 'compute_ids',
        'account_id'
    ],
    'fact_query_history': [
        'query_id', 'query_hash', 'workspace_id', 'statement_id', 'status',
        'statement_type', 'executed_by', 'executed_as', 'executed_as_user_id',
        'execution_status', 'start_time', 'end_time', 'execution_duration_ms',
        'total_duration_ms', 'result_rows', 'result_bytes', 'query_tags',
        'warehouse_id', 'compute_type', 'read_partitions', 'read_rows', 'read_bytes',
        'account_id', 'update_time'
    ],
    'fact_audit_logs': [
        'event_id', 'event_time', 'event_date', 'workspace_id', 'account_id',
        'action_name', 'service_name', 'request_id', 'request_params',
        'response', 'user_identity_email', 'source_ip_address', 'user_agent',
        'session_id', 'version'
    ],
    'fact_node_timeline': [
        'cluster_id', 'workspace_id', 'account_id', 'start_time', 'end_time',
        'driver', 'node_type', 'spot', 'cloud'
    ],
    'fact_table_lineage': [
        'record_id', 'event_id', 'event_time', 'event_type', 'entity_type',
        'entity_id', 'workspace_id', 'account_id', 'entity_metadata_job_id',
        'entity_metadata_notebook_id', 'entity_metadata_pipeline_id'
    ],
    'dim_workspace': [
        'workspace_id', 'workspace_name', 'workspace_url', 'status',
        'cloud', 'region', 'account_id'
    ],
    'dim_job': [
        'job_id', 'workspace_id', 'name', 'creator_id', 'run_as',
        'job_type', 'account_id', 'created_time', 'settings'
    ],
    'dim_cluster': [
        'cluster_id', 'workspace_id', 'cluster_name', 'cluster_source',
        'dbr_version', 'node_type_id', 'driver_node_type_id', 'num_workers',
        'autoscale_min_workers', 'autoscale_max_workers', 'account_id',
        'change_date', 'change_time', 'owned_by'
    ],
    'dim_sku': [
        'sku_id', 'sku_name', 'sku_category', 'pricing_unit', 'is_serverless'
    ],
    'dim_date': [
        'date', 'year', 'quarter', 'month', 'month_name', 'week_of_year',
        'day_of_week', 'day_of_week_name', 'day_of_month', 'day_of_year',
        'is_weekend', 'is_holiday', 'fiscal_year', 'fiscal_quarter'
    ]
}

# Common column name mistakes and their corrections
COLUMN_CORRECTIONS = {
    'is_serverless': "Use: sku_name LIKE '%SERVERLESS%' (fact_usage doesn't have is_serverless)",
    'query_start_time': "Use: start_time (in fact_query_history)",
    'user_name': "Use: user_identity_email (in fact_audit_logs)",
    'user_identity': "Use: user_identity_email (in fact_audit_logs)",
    'duration_seconds': "Use: run_duration_seconds (in fact_job_run_timeline)",
    'execution_start_time': "Use: start_time (in fact_query_history)",
    'node_id': "Use: cluster_id (in fact_node_timeline)",
    'warehouse_type': "Use: compute_type (in fact_query_history)"
}


def extract_queries_from_dashboard(dashboard_path: Path) -> List[Dict]:
    """Extract all SQL queries from a dashboard JSON file."""
    
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    
    queries = []
    dashboard_name = dashboard_path.stem
    
    for dataset in dashboard.get('datasets', []):
        ds_name = dataset.get('name', 'unknown')
        query = dataset.get('query', '')
        
        if not query:
            continue
        
        queries.append({
            'dashboard': dashboard_name,
            'dataset': ds_name,
            'query': query
        })
    
    return queries


def check_column_references(query: str, dashboard: str, dataset: str) -> List[Dict]:
    """Check for known column reference issues."""
    issues = []
    
    # Check for known incorrect column names
    for wrong_col, correction in COLUMN_CORRECTIONS.items():
        # Use word boundary to avoid partial matches
        pattern = rf'\b{wrong_col}\b'
        if re.search(pattern, query, re.IGNORECASE):
            issues.append({
                'type': 'KNOWN_COLUMN_ERROR',
                'dashboard': dashboard,
                'dataset': dataset,
                'column': wrong_col,
                'fix': correction
            })
    
    return issues


def check_sql_syntax(query: str, dashboard: str, dataset: str) -> List[Dict]:
    """Check for common SQL syntax issues."""
    issues = []
    
    # Check for multiple WHERE clauses (but allow if query has CTEs)
    where_count = len(re.findall(r'\bWHERE\b', query, re.IGNORECASE))
    has_cte = bool(re.search(r'\bWITH\b', query, re.IGNORECASE))
    
    # Multiple WHERE is OK if there's a CTE (each subquery can have its own WHERE)
    if where_count > 1 and not has_cte:
        issues.append({
            'type': 'MULTIPLE_WHERE',
            'dashboard': dashboard,
            'dataset': dataset,
            'message': f'Found {where_count} WHERE clauses - merge with AND',
            'fix': 'Combine multiple WHERE clauses into one using AND'
        })
    
    # Check for WHERE followed by AND (missing condition)
    if re.search(r'\bWHERE\s+AND\b', query, re.IGNORECASE):
        issues.append({
            'type': 'WHERE_AND',
            'dashboard': dashboard,
            'dataset': dataset,
            'message': 'Found WHERE AND pattern',
            'fix': 'Remove the AND after WHERE or add a condition before AND'
        })
    
    # Check for AND AND pattern
    if re.search(r'\bAND\s+AND\b', query, re.IGNORECASE):
        issues.append({
            'type': 'DOUBLE_AND',
            'dashboard': dashboard,
            'dataset': dataset,
            'message': 'Found AND AND pattern',
            'fix': 'Remove duplicate AND'
        })
    
    # Check for FROM ... AND (missing WHERE)
    if re.search(r'\bFROM\s+\S+\s+AND\b', query, re.IGNORECASE):
        issues.append({
            'type': 'MISSING_WHERE',
            'dashboard': dashboard,
            'dataset': dataset,
            'message': 'Found FROM table AND pattern - missing WHERE?',
            'fix': 'Add WHERE before the condition'
        })
    
    # Check for unsubstituted variables
    if '${' in query:
        unsubbed = re.findall(r'\$\{[^}]+\}', query)
        issues.append({
            'type': 'UNSUBSTITUTED_VARIABLE',
            'dashboard': dashboard,
            'dataset': dataset,
            'message': f'Found unsubstituted variables: {unsubbed}',
            'fix': 'These will be substituted at deployment time - OK if intentional'
        })
    
    return issues


def check_ambiguous_references(query: str, dashboard: str, dataset: str) -> List[Dict]:
    """Check for potentially ambiguous column references in JOINs."""
    issues = []
    
    # Check if query has JOINs
    has_join = bool(re.search(r'\bJOIN\b', query, re.IGNORECASE))
    if not has_join:
        return issues
    
    # Common columns that are often ambiguous in joins
    ambiguous_columns = ['workspace_id', 'account_id', 'cluster_id', 'job_id']
    
    for col in ambiguous_columns:
        # Check if column is used without table alias
        # Look for patterns like:
        # - "WHERE workspace_id" (not "WHERE f.workspace_id")
        # - "= workspace_id" (not "= f.workspace_id")
        
        # Skip if column is properly qualified (has alias.column)
        qualified_pattern = rf'\b\w+\.{col}\b'
        unqualified_pattern = rf'(?<![.\w])\b{col}\b(?!\s*\.)'
        
        qualified_matches = re.findall(qualified_pattern, query, re.IGNORECASE)
        unqualified_matches = re.findall(unqualified_pattern, query, re.IGNORECASE)
        
        # If there are unqualified uses in a JOIN query, it might be ambiguous
        if unqualified_matches and len(qualified_matches) < len(unqualified_matches):
            issues.append({
                'type': 'POTENTIALLY_AMBIGUOUS',
                'dashboard': dashboard,
                'dataset': dataset,
                'column': col,
                'message': f'Column `{col}` may be ambiguous in JOIN - found {len(unqualified_matches)} unqualified references',
                'fix': f'Qualify with table alias (e.g., f.{col}, j.{col})'
            })
    
    return issues


def validate_dashboard(dashboard_path: Path) -> List[Dict]:
    """Validate all queries in a dashboard."""
    all_issues = []
    
    queries = extract_queries_from_dashboard(dashboard_path)
    
    for query_info in queries:
        query = query_info['query']
        dashboard = query_info['dashboard']
        dataset = query_info['dataset']
        
        # Run all checks
        all_issues.extend(check_column_references(query, dashboard, dataset))
        all_issues.extend(check_sql_syntax(query, dashboard, dataset))
        all_issues.extend(check_ambiguous_references(query, dashboard, dataset))
    
    return all_issues


def generate_report(issues: List[Dict], dashboard_count: int, query_count: int) -> str:
    """Generate validation report."""
    
    report = []
    report.append("=" * 80)
    report.append("LOCAL DASHBOARD SQL VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"\nDashboards scanned: {dashboard_count}")
    report.append(f"Queries analyzed: {query_count}")
    report.append(f"Issues found: {len(issues)}")
    report.append("")
    
    if not issues:
        report.append("✅ No issues detected in static analysis!")
        report.append("\nNote: Full schema validation requires running on Databricks.")
        return "\n".join(report)
    
    # Group by type
    issues_by_type = {}
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)
    
    report.append("-" * 80)
    report.append("ISSUES BY TYPE")
    report.append("-" * 80)
    
    for issue_type, type_issues in sorted(issues_by_type.items()):
        report.append(f"\n### {issue_type} ({len(type_issues)} issues)")
        report.append("")
        
        for issue in type_issues:
            report.append(f"  📋 {issue['dashboard']} -> {issue['dataset']}")
            if 'column' in issue:
                report.append(f"     Column: `{issue['column']}`")
            if 'message' in issue:
                report.append(f"     Message: {issue['message']}")
            if 'fix' in issue:
                report.append(f"     Fix: {issue['fix']}")
            report.append("")
    
    return "\n".join(report)


def main():
    """Main function."""
    
    # Find dashboard directory
    script_dir = Path(__file__).parent.parent
    dashboard_dir = script_dir / "src" / "dashboards"
    
    if not dashboard_dir.exists():
        print(f"Error: Dashboard directory not found: {dashboard_dir}")
        sys.exit(1)
    
    print(f"📁 Dashboard directory: {dashboard_dir}")
    
    # Get all dashboard files
    dashboard_files = list(dashboard_dir.glob("*.lvdash.json"))
    print(f"📊 Found {len(dashboard_files)} dashboard files\n")
    
    # Validate each dashboard
    all_issues = []
    total_queries = 0
    
    for dash_file in dashboard_files:
        queries = extract_queries_from_dashboard(dash_file)
        total_queries += len(queries)
        
        issues = validate_dashboard(dash_file)
        all_issues.extend(issues)
        
        status = "✓" if not issues else f"⚠ {len(issues)} issues"
        print(f"  {dash_file.name}: {len(queries)} queries - {status}")
    
    # Generate report
    report = generate_report(all_issues, len(dashboard_files), total_queries)
    print("\n" + report)
    
    # Exit with error if critical issues found
    critical_types = {'KNOWN_COLUMN_ERROR', 'MULTIPLE_WHERE', 'WHERE_AND', 'DOUBLE_AND'}
    critical_issues = [i for i in all_issues if i['type'] in critical_types]
    
    if critical_issues:
        print(f"\n❌ Found {len(critical_issues)} critical issues that will cause deployment failures!")
        print("Fix these before deploying.")
        sys.exit(1)
    elif all_issues:
        print(f"\n⚠️ Found {len(all_issues)} potential issues. Review before deploying.")
        sys.exit(0)
    else:
        print("\n✅ All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

