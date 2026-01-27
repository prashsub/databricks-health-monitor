#!/usr/bin/env python3
"""
Fix Metric View Benchmark Questions with Proper MEASURE() Syntax.

The MEASURE() function requires EXACTLY ONE measure column name and typically a GROUP BY.
Reference: https://learn.microsoft.com/en-us/azure/databricks/metric-views/#query-measures

Proper syntax:
  SELECT dimension, MEASURE(measure_col) FROM metric_view GROUP BY dimension

This script creates meaningful business questions that test real Genie functionality.
"""

import json
import re
from pathlib import Path
import uuid

GENIE_DIR = Path("src/genie")

# Define meaningful questions for each metric view with proper SQL
METRIC_VIEW_QUESTIONS = {
    "mv_cost_analytics": {
        "question": "What is the total cost by workspace?",
        "sql": "SELECT workspace_name, MEASURE(total_cost) AS total_cost FROM ${catalog}.${gold_schema}.mv_cost_analytics GROUP BY workspace_name ORDER BY total_cost DESC LIMIT 20;",
        "alt_question": "Show total cost breakdown by SKU",
        "alt_sql": "SELECT sku_name, MEASURE(total_cost) AS total_cost FROM ${catalog}.${gold_schema}.mv_cost_analytics GROUP BY sku_name ORDER BY total_cost DESC LIMIT 20;"
    },
    "mv_commit_tracking": {
        "question": "What is the monthly cost trend for commit tracking?",
        "sql": "SELECT usage_month, MEASURE(total_cost) AS monthly_cost FROM ${catalog}.${gold_schema}.mv_commit_tracking GROUP BY usage_month ORDER BY usage_month LIMIT 12;",
        "alt_question": "Show commit utilization by workspace",
        "alt_sql": "SELECT workspace_name, MEASURE(total_cost) AS workspace_cost FROM ${catalog}.${gold_schema}.mv_commit_tracking GROUP BY workspace_name ORDER BY workspace_cost DESC LIMIT 20;"
    },
    "mv_job_performance": {
        "question": "What is the job success rate by workspace?",
        "sql": "SELECT workspace_name, MEASURE(success_rate) AS success_rate FROM ${catalog}.${gold_schema}.mv_job_performance GROUP BY workspace_name ORDER BY success_rate ASC LIMIT 20;",
        "alt_question": "Show total job runs by outcome state",
        "alt_sql": "SELECT result_state, MEASURE(total_runs) AS total_runs FROM ${catalog}.${gold_schema}.mv_job_performance GROUP BY result_state ORDER BY total_runs DESC;"
    },
    "mv_query_performance": {
        "question": "What is the average query duration by warehouse?",
        "sql": "SELECT warehouse_name, MEASURE(avg_duration_seconds) AS avg_duration FROM ${catalog}.${gold_schema}.mv_query_performance GROUP BY warehouse_name ORDER BY avg_duration DESC LIMIT 20;",
        "alt_question": "Show query count by statement type",
        "alt_sql": "SELECT statement_type, MEASURE(total_queries) AS query_count FROM ${catalog}.${gold_schema}.mv_query_performance GROUP BY statement_type ORDER BY query_count DESC LIMIT 10;"
    },
    "mv_cluster_utilization": {
        "question": "What is the average CPU utilization by cluster?",
        "sql": "SELECT cluster_name, MEASURE(avg_cpu_utilization) AS avg_cpu FROM ${catalog}.${gold_schema}.mv_cluster_utilization GROUP BY cluster_name ORDER BY avg_cpu DESC LIMIT 20;",
        "alt_question": "Show memory utilization trends by node type",
        "alt_sql": "SELECT node_type, MEASURE(avg_memory_utilization) AS avg_memory FROM ${catalog}.${gold_schema}.mv_cluster_utilization GROUP BY node_type ORDER BY avg_memory DESC LIMIT 10;"
    },
    "mv_security_events": {
        "question": "What is the event count by action name?",
        "sql": "SELECT action_name, MEASURE(total_events) AS event_count FROM ${catalog}.${gold_schema}.mv_security_events GROUP BY action_name ORDER BY event_count DESC LIMIT 20;",
        "alt_question": "Show failed events by user identity",
        "alt_sql": "SELECT user_identity, MEASURE(failed_events) AS failures FROM ${catalog}.${gold_schema}.mv_security_events GROUP BY user_identity ORDER BY failures DESC LIMIT 20;"
    },
    "mv_governance_analytics": {
        "question": "What are the data access events by source table?",
        "sql": "SELECT source_table_name, MEASURE(total_events) AS access_count FROM ${catalog}.${gold_schema}.mv_governance_analytics GROUP BY source_table_name ORDER BY access_count DESC LIMIT 20;",
        "alt_question": "Show lineage events by pipeline name",
        "alt_sql": "SELECT pipeline_name, MEASURE(total_events) AS events FROM ${catalog}.${gold_schema}.mv_governance_analytics WHERE pipeline_name IS NOT NULL GROUP BY pipeline_name ORDER BY events DESC LIMIT 10;"
    },
    "mv_data_quality": {
        "question": "What is the table freshness status by schema?",
        "sql": "SELECT table_schema, MEASURE(total_tables) AS table_count, MEASURE(fresh_tables) AS fresh_count FROM ${catalog}.${gold_schema}.mv_data_quality GROUP BY table_schema ORDER BY table_count DESC LIMIT 20;",
        "alt_question": "Show stale tables by domain",
        "alt_sql": "SELECT domain, MEASURE(stale_tables) AS stale_count FROM ${catalog}.${gold_schema}.mv_data_quality GROUP BY domain ORDER BY stale_count DESC LIMIT 10;"
    },
    "mv_ml_intelligence": {
        "question": "What is the anomaly count by workspace?",
        "sql": "SELECT workspace_name, MEASURE(anomaly_count) AS anomalies FROM ${catalog}.${gold_schema}.mv_ml_intelligence GROUP BY workspace_name ORDER BY anomalies DESC LIMIT 20;",
        "alt_question": "Show anomaly rate by SKU",
        "alt_sql": "SELECT sku_name, MEASURE(anomaly_rate) AS anomaly_rate FROM ${catalog}.${gold_schema}.mv_ml_intelligence GROUP BY sku_name ORDER BY anomaly_rate DESC LIMIT 10;"
    },
    "mv_data_classification": {
        "question": "What is the table count by classification level?",
        "sql": "SELECT classification_level, MEASURE(total_tables) AS table_count FROM ${catalog}.${gold_schema}.mv_data_classification GROUP BY classification_level ORDER BY table_count DESC;",
        "alt_question": "Show PII column count by schema",
        "alt_sql": "SELECT table_schema, MEASURE(pii_column_count) AS pii_columns FROM ${catalog}.${gold_schema}.mv_data_classification GROUP BY table_schema ORDER BY pii_columns DESC LIMIT 10;"
    }
}

def generate_uuid():
    """Generate a 32-character hex UUID without dashes."""
    return uuid.uuid4().hex

def fix_genie_space_benchmarks(file_path: Path) -> int:
    """Fix metric view benchmarks in a single Genie Space JSON file."""
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    benchmarks = data.get('benchmarks', {}).get('questions', [])
    
    changes_made = 0
    
    for q in benchmarks:
        answer_content = q.get('answer', [{}])
        if not answer_content:
            continue
            
        sql = answer_content[0].get('content', [''])[0] if answer_content[0].get('content') else ''
        question_text = q.get('question', [''])[0] if q.get('question') else ''
        
        # Check if this is a metric view query
        for mv_name, mv_config in METRIC_VIEW_QUESTIONS.items():
            if mv_name in sql:
                # Check if it's using invalid syntax (SELECT * or multiple MEASURE columns)
                if 'SELECT *' in sql or 'SELECT 1' in sql or sql.count('MEASURE') == 0:
                    # Replace with proper question and SQL
                    q['question'] = [mv_config['question']]
                    q['answer'][0]['content'] = [mv_config['sql']]
                    changes_made += 1
                    print(f"  ✅ Fixed {mv_name}")
                    print(f"     Q: {mv_config['question']}")
                    print(f"     SQL: {mv_config['sql'][:80]}...")
                elif 'MEASURE(' in sql:
                    # Check for MEASURE with multiple columns (invalid)
                    measure_match = re.search(r'MEASURE\s*\(([^)]+)\)', sql)
                    if measure_match:
                        measure_content = measure_match.group(1)
                        # If it has commas, it's multiple columns (invalid)
                        if ',' in measure_content or measure_content == '*':
                            q['question'] = [mv_config['question']]
                            q['answer'][0]['content'] = [mv_config['sql']]
                            changes_made += 1
                            print(f"  ✅ Fixed {mv_name} (had multiple columns in MEASURE)")
                            print(f"     Q: {mv_config['question']}")
                            print(f"     SQL: {mv_config['sql'][:80]}...")
                break
    
    if changes_made > 0:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return changes_made

def main():
    """Fix all metric view benchmarks across all Genie Spaces."""
    
    genie_files = [
        "cost_intelligence_genie_export.json",
        "job_health_monitor_genie_export.json",
        "performance_genie_export.json",
        "security_auditor_genie_export.json",
        "unified_health_monitor_genie_export.json",
        "data_quality_monitor_genie_export.json",
    ]
    
    total_fixed = 0
    
    print("=" * 70)
    print("Fixing Metric View Benchmarks with Proper MEASURE() Syntax")
    print("=" * 70)
    
    for file_name in genie_files:
        file_path = GENIE_DIR / file_name
        if not file_path.exists():
            print(f"\n⚠️ {file_name} not found. Skipping.")
            continue
        
        print(f"\n📝 Processing {file_name}...")
        changes = fix_genie_space_benchmarks(file_path)
        total_fixed += changes
        
        if changes == 0:
            print(f"  ℹ️  No metric view benchmarks needed fixing")
    
    print(f"\n{'=' * 70}")
    print(f"✅ Total fixed: {total_fixed} metric view benchmarks")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
