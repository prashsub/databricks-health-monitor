#!/usr/bin/env python3
"""
Fix Security Auditor Genie Space benchmark errors.

Errors to fix:
1. Q4: get_security_events_timeline - requires 3 params but got 4
2. Q6: get_failed_actions - requires 3 params but got 4
3. Q9: mv_security_events - needs MEASURE()
4. Q10: mv_governance_analytics - needs MEASURE()
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"
JSON_PATH = GENIE_DIR / "security_auditor_genie_export.json"

# Date values
TODAY = datetime.now()
START_DATE = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")

GOLD_PREFIX = "${catalog}.${gold_schema}"
ML_PREFIX = "${catalog}.${feature_schema}"
MON_PREFIX = "${catalog}.${gold_schema}_monitoring"


def generate_id():
    return uuid.uuid4().hex


def get_correct_tvf_benchmarks():
    """Generate TVF benchmarks with correct parameters.
    
    Security TVF signatures:
    - get_user_activity_summary(start_date, end_date, top_n) - 3 params
    - get_sensitive_table_access(start_date, end_date, table_pattern) - 3 params
    - get_failed_actions(start_date, end_date, user_filter) - 3 params
    - get_permission_changes(start_date, end_date) - 2 params
    - get_off_hours_activity(start_date, end_date, business_hours_start, business_hours_end) - 4 params
    - get_security_events_timeline(start_date, end_date, user_filter) - 3 params
    - get_ip_address_analysis(start_date, end_date) - 2 params
    - get_table_access_audit(start_date, end_date, table_pattern) - 3 params
    """
    
    tvf_benchmarks = [
        {
            "question": "Show user activity summary",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_user_activity_summary("{START_DATE}", "{END_DATE}", 20) LIMIT 20;'
        },
        {
            "question": "Show sensitive table access",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_sensitive_table_access("{START_DATE}", "{END_DATE}", "%") LIMIT 20;'
        },
        {
            "question": "What are the failed actions?",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_failed_actions("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "Show permission changes",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_permission_changes("{START_DATE}", "{END_DATE}") LIMIT 20;'
        },
        {
            "question": "Show off-hours activity",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_off_hours_activity("{START_DATE}", "{END_DATE}", 9, 18) LIMIT 20;'
        },
        {
            "question": "Show security events timeline",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_security_events_timeline("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;'
        },
        {
            "question": "Show IP address analysis",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_ip_address_analysis("{START_DATE}", "{END_DATE}") LIMIT 20;'
        },
        {
            "question": "Show table access audit",
            "sql": f'SELECT * FROM {GOLD_PREFIX}.get_table_access_audit("{START_DATE}", "{END_DATE}", "%") LIMIT 20;'
        },
    ]
    
    return [
        {
            "id": generate_id(),
            "question": [t["question"]],
            "answer": [{"format": "SQL", "content": [t["sql"]]}]
        }
        for t in tvf_benchmarks
    ]


def get_correct_mv_benchmarks():
    """Generate metric view benchmarks with correct MEASURE() syntax."""
    
    mv_benchmarks = [
        {
            "question": "Show security events summary",
            "sql": f"SELECT event_date, service_name, MEASURE(total_events) as total_events, MEASURE(failed_events) as failed_events FROM {GOLD_PREFIX}.mv_security_events GROUP BY ALL LIMIT 20;"
        },
        {
            "question": "Show governance analytics summary",
            "sql": f"SELECT event_date, MEASURE(total_events) as total_events, MEASURE(read_events) as read_events FROM {GOLD_PREFIX}.mv_governance_analytics GROUP BY ALL LIMIT 20;"
        },
    ]
    
    return [
        {
            "id": generate_id(),
            "question": [t["question"]],
            "answer": [{"format": "SQL", "content": [t["sql"]]}]
        }
        for t in mv_benchmarks
    ]


def get_correct_table_benchmarks():
    """Generate table benchmarks (ML, monitoring, fact, dim)."""
    
    benchmarks = []
    
    # ML tables
    ml_tables = [
        "ml_security_risk_predictions",
        "ml_anomaly_detection_predictions",
        "ml_access_pattern_predictions"
    ]
    for table in ml_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"What are the latest predictions from {table}?"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {ML_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Monitoring tables
    mon_tables = [
        "fact_audit_logs_profile_metrics",
        "fact_audit_logs_drift_metrics"
    ]
    for table in mon_tables:
        benchmarks.append({
            "id": generate_id(),
            "question": [f"Show monitoring data from {table}"],
            "answer": [{"format": "SQL", "content": [f"SELECT * FROM {MON_PREFIX}.{table} LIMIT 20;"]}]
        })
    
    # Fact tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show recent audit logs"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_audit_logs LIMIT 20;"]}]
    })
    
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show data lineage events"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.fact_data_lineage LIMIT 20;"]}]
    })
    
    # Dim tables
    benchmarks.append({
        "id": generate_id(),
        "question": ["Show user dimension"],
        "answer": [{"format": "SQL", "content": [f"SELECT * FROM {GOLD_PREFIX}.dim_user LIMIT 20;"]}]
    })
    
    return benchmarks


def get_deep_research_benchmarks():
    """Generate deep research benchmarks."""
    
    return [
        {
            "id": generate_id(),
            "question": ["Analyze security event patterns over time"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Complex security event analysis' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Identify high-risk user activity"],
            "answer": [{"format": "SQL", "content": ["SELECT 'High-risk user identification' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Compare access patterns across users"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Cross-user access comparison' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["Provide executive security summary"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Executive security summary' AS deep_research;"]}]
        },
        {
            "id": generate_id(),
            "question": ["What are the security compliance gaps?"],
            "answer": [{"format": "SQL", "content": ["SELECT 'Security compliance gap analysis' AS deep_research;"]}]
        },
    ]


def main():
    print("=" * 80)
    print("FIXING SECURITY AUDITOR BENCHMARKS")
    print("=" * 80)
    
    # Load existing JSON
    with open(JSON_PATH, 'r') as f:
        genie_data = json.load(f)
    
    # Generate correct benchmarks
    benchmarks = []
    
    # TVFs with correct parameters (8)
    tvf_benchmarks = get_correct_tvf_benchmarks()
    benchmarks.extend(tvf_benchmarks)
    print(f"✅ TVF benchmarks: {len(tvf_benchmarks)}")
    
    # Metric views with MEASURE() (2)
    mv_benchmarks = get_correct_mv_benchmarks()
    benchmarks.extend(mv_benchmarks)
    print(f"✅ Metric view benchmarks: {len(mv_benchmarks)}")
    
    # Tables (ML, monitoring, fact, dim)
    table_benchmarks = get_correct_table_benchmarks()
    benchmarks.extend(table_benchmarks)
    print(f"✅ Table benchmarks: {len(table_benchmarks)}")
    
    # Deep research (5)
    deep_benchmarks = get_deep_research_benchmarks()
    benchmarks.extend(deep_benchmarks)
    print(f"✅ Deep research benchmarks: {len(deep_benchmarks)}")
    
    print(f"\n📊 Total benchmarks: {len(benchmarks)}")
    
    # Update JSON
    genie_data['benchmarks'] = {'questions': benchmarks}
    
    with open(JSON_PATH, 'w') as f:
        json.dump(genie_data, f, indent=2)
    
    print(f"\n✅ Updated: {JSON_PATH.name}")
    
    # Show corrected TVF SQL for verification
    print("\n" + "=" * 80)
    print("CORRECTED TVF SQL (Q4, Q6)")
    print("=" * 80)
    print(f"\nget_security_events_timeline (3 params):")
    print(f'   SELECT * FROM {GOLD_PREFIX}.get_security_events_timeline("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;')
    print(f"\nget_failed_actions (3 params):")
    print(f'   SELECT * FROM {GOLD_PREFIX}.get_failed_actions("{START_DATE}", "{END_DATE}", "ALL") LIMIT 20;')


if __name__ == "__main__":
    main()
