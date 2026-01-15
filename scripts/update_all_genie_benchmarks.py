#!/usr/bin/env python3
"""
Update ALL remaining Genie Space benchmarks (Performance, Security, Data Quality, Unified Health)
Each gets 25 questions: 20 basic + 5 deep research

Based on actual_assets_inventory.json
"""

import json
import uuid
import re
from pathlib import Path

def generate_id():
    """Generate a 32-char hex ID without dashes."""
    return uuid.uuid4().hex

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GENIE_DIR = PROJECT_ROOT / "src/genie"

# Load inventory
with open(PROJECT_ROOT / "src/genie/actual_assets_inventory.json") as f:
    INVENTORY = json.load(f)

def get_domain_assets(domain_name):
    """Get assets for a specific domain."""
    return INVENTORY['domain_mapping'].get(domain_name, {})


def build_benchmark_questions(domain_name, benchmarks_config):
    """Build benchmark questions from config."""
    questions = []
    for category, items in benchmarks_config.items():
        for question_text, sql in items:
            questions.append({
                "id": generate_id(),
                "question": [question_text],
                "answer": [{
                    "format": "SQL",
                    "content": [sql]
                }]
            })
    return questions


def generate_spec_section_h(questions):
    """Generate Section H markdown."""
    lines = [
        "## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████",
        "",
        "> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**",
        "",
        "### ✅ Normal Benchmark Questions (Q1-Q20)",
        ""
    ]
    
    q_num = 1
    for q in questions[:20]:
        question_text = q['question'][0]
        sql = q['answer'][0]['content'][0]
        lines.extend([
            f"### Question {q_num}: \"{question_text}\"",
            "**Expected SQL:**",
            "```sql",
            sql,
            "```",
            "",
            "---",
            ""
        ])
        q_num += 1
    
    lines.append("### 🔬 Deep Research Questions (Q21-Q25)")
    lines.append("")
    
    for q in questions[20:]:
        question_text = q['question'][0]
        sql = q['answer'][0]['content'][0]
        lines.extend([
            f"### Question {q_num}: \"{question_text}\"",
            "**Expected SQL:**",
            "```sql",
            sql,
            "```",
            "",
            "---",
            ""
        ])
        q_num += 1
    
    return "\n".join(lines)


def update_genie_space(json_file, spec_file, benchmarks_config, space_name):
    """Update a single Genie Space."""
    print(f"\n{'='*60}")
    print(f"Updating: {space_name}")
    print(f"{'='*60}")
    
    # Update JSON
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    questions = build_benchmark_questions(space_name, benchmarks_config)
    data['benchmarks'] = {'questions': questions}
    
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Updated {json_file.name}")
    print(f"   Total benchmarks: {len(questions)}")
    counts = {k: len(v) for k, v in benchmarks_config.items()}
    print(f"   Distribution: {counts}")
    
    # Update spec file
    with open(spec_file, 'r') as f:
        content = f.read()
    
    section_h_pattern = r'## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████.*?(?=## ✅ DELIVERABLE CHECKLIST|## Agent Domain Tag|$)'
    new_section_h = generate_spec_section_h(questions)
    
    if re.search(section_h_pattern, content, re.DOTALL):
        content = re.sub(section_h_pattern, new_section_h, content, flags=re.DOTALL)
        with open(spec_file, 'w') as f:
            f.write(content)
        print(f"✅ Updated {spec_file.name}")
    else:
        print(f"⚠️ Could not find Section H in {spec_file.name}")


# ============================================================
# PERFORMANCE GENIE
# ============================================================
PERFORMANCE_BENCHMARKS = {
    "tvf": [
        ("Show slow running queries", "SELECT * FROM TABLE(get_slow_queries(30)) LIMIT 20;"),
        ("Identify expensive queries", "SELECT * FROM TABLE(get_expensive_queries(30)) LIMIT 20;"),
        ("Show cluster utilization", "SELECT * FROM TABLE(get_cluster_utilization(30)) LIMIT 20;"),
        ("Analyze query patterns", "SELECT * FROM TABLE(get_query_patterns(30)) LIMIT 20;"),
        ("Show warehouse performance", "SELECT * FROM TABLE(get_warehouse_performance(30)) LIMIT 20;"),
        ("Identify idle clusters", "SELECT * FROM TABLE(get_idle_clusters(30)) LIMIT 20;"),
        ("Show query queue times", "SELECT * FROM TABLE(get_query_queue_times(30)) LIMIT 20;"),
        ("Analyze cluster sizing", "SELECT * FROM TABLE(get_cluster_sizing_recommendations()) LIMIT 20;"),
    ],
    "metric_view": [
        ("Show query performance metrics", "SELECT * FROM mv_query_performance LIMIT 20;"),
        ("What are the slowest queries?", "SELECT query_id, duration_seconds FROM mv_query_performance ORDER BY duration_seconds DESC LIMIT 10;"),
        ("Show average query duration", "SELECT AVG(duration_seconds) as avg_duration FROM mv_query_performance;"),
        ("Top queries by cost", "SELECT query_id, total_dbu_cost FROM mv_query_performance ORDER BY total_dbu_cost DESC LIMIT 10;"),
    ],
    "ml": [
        ("Predict query durations", "SELECT * FROM query_duration_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Show query cost predictions", "SELECT * FROM query_cost_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Identify queries likely to timeout", "SELECT * FROM query_timeout_predictions WHERE prediction > 0.5 LIMIT 20;"),
    ],
    "monitoring": [
        ("Show query profile metrics", "SELECT * FROM fact_query_history_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;"),
        ("Show query drift metrics", "SELECT * FROM fact_query_history_drift_metrics LIMIT 20;"),
    ],
    "fact": [
        ("Show recent queries", "SELECT query_id, duration_ms, total_task_duration_ms FROM fact_query_history ORDER BY start_time DESC LIMIT 20;"),
        ("Show cluster events", "SELECT cluster_id, event_type, timestamp FROM fact_cluster_timeline ORDER BY timestamp DESC LIMIT 20;"),
    ],
    "dim": [
        ("List all clusters", "SELECT cluster_id, cluster_name FROM dim_cluster ORDER BY cluster_name LIMIT 20;"),
    ],
    "deep_research": [
        ("🔬 DEEP RESEARCH: Comprehensive query performance analysis",
         """SELECT query_id, duration_seconds, total_dbu_cost,
       CASE WHEN duration_seconds > 300 THEN 'Slow' 
            WHEN duration_seconds > 60 THEN 'Medium' ELSE 'Fast' END as speed_tier
FROM mv_query_performance
ORDER BY duration_seconds DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Query cost optimization opportunities",
         """SELECT q.query_id, q.total_dbu_cost, qc.prediction as predicted_cost
FROM mv_query_performance q
JOIN query_cost_predictions qc ON q.query_id = qc.query_id
WHERE q.total_dbu_cost > 1
ORDER BY q.total_dbu_cost DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Cluster utilization efficiency",
         """SELECT c.cluster_name, COUNT(DISTINCT q.query_id) as query_count
FROM dim_cluster c
JOIN fact_query_history q ON c.cluster_id = q.cluster_id
GROUP BY c.cluster_name
ORDER BY query_count DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Query timeout risk assessment",
         """SELECT qt.query_id, qt.prediction as timeout_risk,
       CASE WHEN qt.prediction > 0.7 THEN 'High Risk'
            WHEN qt.prediction > 0.4 THEN 'Medium Risk' ELSE 'Low Risk' END as risk_level
FROM query_timeout_predictions qt
ORDER BY qt.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Performance trend analysis with monitoring",
         """SELECT * FROM fact_query_history_drift_metrics
ORDER BY drift_score DESC LIMIT 15;"""),
    ]
}

# ============================================================
# SECURITY AUDITOR GENIE
# ============================================================
SECURITY_BENCHMARKS = {
    "tvf": [
        ("Show recent security events", "SELECT * FROM TABLE(get_security_events(7)) LIMIT 20;"),
        ("List permission changes", "SELECT * FROM TABLE(get_permission_changes(7)) LIMIT 20;"),
        ("Show access denied events", "SELECT * FROM TABLE(get_access_denied_events(7)) LIMIT 20;"),
        ("Identify suspicious activity", "SELECT * FROM TABLE(get_suspicious_activity(7)) LIMIT 20;"),
        ("Show admin actions", "SELECT * FROM TABLE(get_admin_actions(7)) LIMIT 20;"),
        ("List data access patterns", "SELECT * FROM TABLE(get_data_access_patterns(7)) LIMIT 20;"),
        ("Show authentication failures", "SELECT * FROM TABLE(get_auth_failures(7)) LIMIT 20;"),
        ("Audit table access", "SELECT * FROM TABLE(get_table_access_audit(7)) LIMIT 20;"),
    ],
    "metric_view": [
        ("Show security metrics overview", "SELECT * FROM mv_security_metrics LIMIT 20;"),
        ("Top users by security events", "SELECT user_name, event_count FROM mv_security_metrics ORDER BY event_count DESC LIMIT 10;"),
        ("Show access denied summary", "SELECT user_name, denied_count FROM mv_security_metrics ORDER BY denied_count DESC LIMIT 10;"),
        ("Security events by type", "SELECT event_type, COUNT(*) as count FROM mv_security_metrics GROUP BY event_type LIMIT 10;"),
    ],
    "ml": [
        ("Show anomaly predictions", "SELECT * FROM security_anomaly_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Identify insider threat risk", "SELECT * FROM insider_threat_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Predict data exfiltration risk", "SELECT * FROM data_exfiltration_predictions WHERE prediction > 0.5 LIMIT 20;"),
    ],
    "monitoring": [
        ("Show audit log profile metrics", "SELECT * FROM fact_audit_logs_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;"),
        ("Show audit log drift metrics", "SELECT * FROM fact_audit_logs_drift_metrics LIMIT 20;"),
    ],
    "fact": [
        ("Show recent audit logs", "SELECT event_time, action_name, user_identity, service_name FROM fact_audit_logs ORDER BY event_time DESC LIMIT 20;"),
        ("Show workspace activity", "SELECT workspace_id, action_name, event_time FROM fact_audit_logs ORDER BY event_time DESC LIMIT 20;"),
    ],
    "dim": [
        ("List all workspaces", "SELECT workspace_id, workspace_name FROM dim_workspace ORDER BY workspace_name LIMIT 20;"),
    ],
    "deep_research": [
        ("🔬 DEEP RESEARCH: Comprehensive security audit analysis",
         """SELECT action_name, COUNT(*) as event_count,
       COUNT(DISTINCT user_identity) as unique_users
FROM fact_audit_logs
WHERE event_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY action_name
ORDER BY event_count DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: User behavior risk assessment",
         """SELECT sa.user_id, sa.prediction as anomaly_score,
       CASE WHEN sa.prediction > 0.7 THEN 'High Risk'
            WHEN sa.prediction > 0.4 THEN 'Medium Risk' ELSE 'Low Risk' END as risk_level
FROM security_anomaly_predictions sa
ORDER BY sa.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Access pattern analysis",
         """SELECT user_identity, service_name, COUNT(*) as access_count
FROM fact_audit_logs
WHERE event_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_identity, service_name
ORDER BY access_count DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Insider threat detection",
         """SELECT it.user_id, it.prediction as threat_score
FROM insider_threat_predictions it
WHERE it.prediction > 0.3
ORDER BY it.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Security posture trending",
         """SELECT * FROM fact_audit_logs_drift_metrics
ORDER BY drift_score DESC LIMIT 15;"""),
    ]
}

# ============================================================
# DATA QUALITY MONITOR GENIE
# ============================================================
DATA_QUALITY_BENCHMARKS = {
    "tvf": [
        ("Show data quality issues", "SELECT * FROM TABLE(get_data_quality_issues(7)) LIMIT 20;"),
        ("List schema changes", "SELECT * FROM TABLE(get_schema_changes(7)) LIMIT 20;"),
        ("Show freshness violations", "SELECT * FROM TABLE(get_freshness_violations(7)) LIMIT 20;"),
        ("Identify null rate issues", "SELECT * FROM TABLE(get_null_rate_issues(7)) LIMIT 20;"),
        ("Show volume anomalies", "SELECT * FROM TABLE(get_volume_anomalies(7)) LIMIT 20;"),
        ("List quality rule failures", "SELECT * FROM TABLE(get_quality_rule_failures(7)) LIMIT 20;"),
        ("Show table health status", "SELECT * FROM TABLE(get_table_health_status()) LIMIT 20;"),
        ("Identify data drift", "SELECT * FROM TABLE(get_data_drift_alerts(7)) LIMIT 20;"),
    ],
    "metric_view": [
        ("Show data quality metrics", "SELECT * FROM mv_data_quality LIMIT 20;"),
        ("Tables with quality issues", "SELECT table_name, quality_score FROM mv_data_quality ORDER BY quality_score ASC LIMIT 10;"),
        ("Average quality score", "SELECT AVG(quality_score) as avg_quality FROM mv_data_quality;"),
        ("Top tables by issue count", "SELECT table_name, issue_count FROM mv_data_quality ORDER BY issue_count DESC LIMIT 10;"),
    ],
    "ml": [
        ("Predict quality degradation", "SELECT * FROM quality_degradation_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Show anomaly predictions", "SELECT * FROM data_anomaly_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Predict schema changes", "SELECT * FROM schema_change_predictions WHERE prediction > 0.5 LIMIT 20;"),
    ],
    "monitoring": [
        ("Show governance profile metrics", "SELECT * FROM fact_governance_metrics_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;"),
        ("Show governance drift metrics", "SELECT * FROM fact_governance_metrics_drift_metrics LIMIT 20;"),
    ],
    "fact": [
        ("Show governance metrics", "SELECT table_name, metric_name, metric_value FROM fact_governance_metrics ORDER BY measured_at DESC LIMIT 20;"),
        ("Show data lineage", "SELECT source_table, target_table, lineage_type FROM fact_data_lineage LIMIT 20;"),
    ],
    "dim": [
        ("List monitored tables", "SELECT table_id, table_name FROM dim_table ORDER BY table_name LIMIT 20;"),
    ],
    "deep_research": [
        ("🔬 DEEP RESEARCH: Comprehensive data quality analysis",
         """SELECT table_name, quality_score, issue_count,
       CASE WHEN quality_score < 70 THEN 'Critical'
            WHEN quality_score < 85 THEN 'Warning' ELSE 'Good' END as status
FROM mv_data_quality
ORDER BY quality_score ASC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Quality degradation risk assessment",
         """SELECT qd.table_id, qd.prediction as degradation_risk,
       CASE WHEN qd.prediction > 0.7 THEN 'High Risk'
            WHEN qd.prediction > 0.4 THEN 'Medium Risk' ELSE 'Low Risk' END as risk_level
FROM quality_degradation_predictions qd
ORDER BY qd.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Schema stability analysis",
         """SELECT sc.table_id, sc.prediction as change_probability
FROM schema_change_predictions sc
WHERE sc.prediction > 0.3
ORDER BY sc.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Data freshness monitoring",
         """SELECT table_name, MAX(measured_at) as last_update
FROM fact_governance_metrics
GROUP BY table_name
ORDER BY last_update ASC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Quality trend analysis with monitoring",
         """SELECT * FROM fact_governance_metrics_drift_metrics
ORDER BY drift_score DESC LIMIT 15;"""),
    ]
}

# ============================================================
# UNIFIED HEALTH MONITOR GENIE
# ============================================================
UNIFIED_BENCHMARKS = {
    "tvf": [
        ("Show platform health summary", "SELECT * FROM TABLE(get_platform_health_summary()) LIMIT 20;"),
        ("List critical alerts", "SELECT * FROM TABLE(get_critical_alerts(7)) LIMIT 20;"),
        ("Show cost anomalies", "SELECT * FROM TABLE(get_cost_anomalies(7)) LIMIT 20;"),
        ("Show performance issues", "SELECT * FROM TABLE(get_performance_issues(7)) LIMIT 20;"),
        ("List security alerts", "SELECT * FROM TABLE(get_security_alerts(7)) LIMIT 20;"),
        ("Show job failures", "SELECT * FROM TABLE(get_failed_jobs(7)) LIMIT 20;"),
        ("List quality issues", "SELECT * FROM TABLE(get_data_quality_issues(7)) LIMIT 20;"),
        ("Show workspace health", "SELECT * FROM TABLE(get_workspace_health()) LIMIT 20;"),
    ],
    "metric_view": [
        ("Show platform overview metrics", "SELECT * FROM mv_platform_health LIMIT 20;"),
        ("Overall platform health score", "SELECT AVG(health_score) as avg_health FROM mv_platform_health;"),
        ("Workspaces by health score", "SELECT workspace_name, health_score FROM mv_platform_health ORDER BY health_score ASC LIMIT 10;"),
        ("Top issues by severity", "SELECT issue_type, severity, COUNT(*) as count FROM mv_platform_health GROUP BY issue_type, severity LIMIT 10;"),
    ],
    "ml": [
        ("Show health predictions", "SELECT * FROM platform_health_predictions ORDER BY prediction DESC LIMIT 20;"),
        ("Predict outage risk", "SELECT * FROM outage_risk_predictions WHERE prediction > 0.5 LIMIT 20;"),
        ("Show capacity predictions", "SELECT * FROM capacity_predictions ORDER BY prediction DESC LIMIT 20;"),
    ],
    "monitoring": [
        ("Show usage profile metrics", "SELECT * FROM fact_usage_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;"),
        ("Show usage drift metrics", "SELECT * FROM fact_usage_drift_metrics LIMIT 20;"),
    ],
    "fact": [
        ("Show platform usage", "SELECT workspace_id, sku_name, usage_quantity FROM fact_usage ORDER BY usage_date DESC LIMIT 20;"),
        ("Show job run history", "SELECT job_name, result_state, run_duration_seconds FROM fact_job_run_timeline ORDER BY period_start_time DESC LIMIT 20;"),
    ],
    "dim": [
        ("List workspaces", "SELECT workspace_id, workspace_name FROM dim_workspace ORDER BY workspace_name LIMIT 20;"),
    ],
    "deep_research": [
        ("🔬 DEEP RESEARCH: Comprehensive platform health analysis",
         """SELECT workspace_name, health_score,
       CASE WHEN health_score < 70 THEN 'Critical'
            WHEN health_score < 85 THEN 'Warning' ELSE 'Healthy' END as status
FROM mv_platform_health
ORDER BY health_score ASC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Cross-domain issue correlation",
         """SELECT ws.workspace_name, 
       COUNT(DISTINCT j.job_id) as job_count,
       SUM(u.usage_quantity) as total_usage
FROM dim_workspace ws
LEFT JOIN fact_job_run_timeline j ON ws.workspace_id = j.workspace_id
LEFT JOIN fact_usage u ON ws.workspace_id = u.workspace_id
GROUP BY ws.workspace_name
ORDER BY total_usage DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Outage risk assessment",
         """SELECT or_p.workspace_id, or_p.prediction as outage_risk,
       CASE WHEN or_p.prediction > 0.7 THEN 'High Risk'
            WHEN or_p.prediction > 0.4 THEN 'Medium Risk' ELSE 'Low Risk' END as risk_level
FROM outage_risk_predictions or_p
ORDER BY or_p.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Capacity planning analysis",
         """SELECT cp.workspace_id, cp.prediction as capacity_forecast
FROM capacity_predictions cp
ORDER BY cp.prediction DESC LIMIT 15;"""),
        ("🔬 DEEP RESEARCH: Platform health trending",
         """SELECT * FROM fact_usage_drift_metrics
ORDER BY drift_score DESC LIMIT 15;"""),
    ]
}


def main():
    print("\n" + "=" * 70)
    print("UPDATING ALL REMAINING GENIE SPACE BENCHMARKS")
    print("=" * 70)
    
    # Performance
    update_genie_space(
        GENIE_DIR / "performance_genie_export.json",
        GENIE_DIR / "performance_genie.md",
        PERFORMANCE_BENCHMARKS,
        "Performance"
    )
    
    # Security Auditor
    update_genie_space(
        GENIE_DIR / "security_auditor_genie_export.json",
        GENIE_DIR / "security_auditor_genie.md",
        SECURITY_BENCHMARKS,
        "Security Auditor"
    )
    
    # Data Quality Monitor
    update_genie_space(
        GENIE_DIR / "data_quality_monitor_genie_export.json",
        GENIE_DIR / "data_quality_monitor_genie.md",
        DATA_QUALITY_BENCHMARKS,
        "Data Quality Monitor"
    )
    
    # Unified Health Monitor
    update_genie_space(
        GENIE_DIR / "unified_health_monitor_genie_export.json",
        GENIE_DIR / "unified_health_monitor_genie.md",
        UNIFIED_BENCHMARKS,
        "Unified Health Monitor"
    )
    
    print("\n" + "=" * 70)
    print("✅ ALL GENIE SPACE BENCHMARKS UPDATED")
    print("=" * 70)
    print("\nNext: Deploy bundle and run validation")


if __name__ == "__main__":
    main()
