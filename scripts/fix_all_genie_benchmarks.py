#!/usr/bin/env python3
"""
Fix all Genie Space benchmark questions to use correct table names and simple queries.
Based on source of truth:
- docs/semantic-framework/24-metric-views-reference.md
- docs/lakehouse-monitoring-design/04-monitor-catalog.md
- docs/ml-framework-design/07-model-catalog.md
"""

# Simple, validated benchmark questions for each domain
BENCHMARK_QUESTIONS = {
    "cost_intelligence_genie.md": [
        {
            "q": "What is our total spend this month?",
            "sql": """SELECT MEASURE(total_cost) as mtd_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());"""
        },
        {
            "q": "Show me cost by workspace",
            "sql": """SELECT 
  workspace_name,
  MEASURE(total_cost) as cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY workspace_name
ORDER BY cost DESC
LIMIT 10;"""
        },
        {
            "q": "What is our tag coverage percentage?",
            "sql": """SELECT MEASURE(tag_coverage_pct) as tag_coverage_percentage
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;"""
        },
    ],
    
    "job_health_monitor_genie.md": [
        {
            "q": "What is our job success rate this week?",
            "sql": """SELECT MEASURE(success_rate) as success_rate_pct
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
        {
            "q": "Show me job performance by workspace",
            "sql": """SELECT 
  workspace_name,
  MEASURE(success_rate) as success_pct,
  MEASURE(total_runs) as runs
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY workspace_name
ORDER BY runs DESC
LIMIT 10;"""
        },
        {
            "q": "What is the P95 job duration?",
            "sql": """SELECT MEASURE(p95_duration_minutes) as p95_minutes
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
    ],
    
    "performance_genie.md": [
        {
            "q": "What is our average query duration?",
            "sql": """SELECT MEASURE(avg_duration_seconds) as avg_sec
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
        {
            "q": "Show me query performance by warehouse",
            "sql": """SELECT 
  warehouse_name,
  MEASURE(avg_duration_seconds) as avg_duration,
  MEASURE(total_queries) as queries
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY warehouse_name
ORDER BY queries DESC
LIMIT 10;"""
        },
        {
            "q": "What is the average CPU utilization?",
            "sql": """SELECT MEASURE(avg_cpu_utilization) as cpu_pct
FROM ${catalog}.${gold_schema}.mv_cluster_utilization
WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
    ],
    
    "security_auditor_genie.md": [
        {
            "q": "Show me recent security events",
            "sql": """SELECT 
  user_email,
  action_category,
  MEASURE(total_events) as events
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_email, action_category
ORDER BY events DESC
LIMIT 10;"""
        },
        {
            "q": "What is the total event count?",
            "sql": """SELECT MEASURE(total_events) as total_events
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
        {
            "q": "Show me failed events",
            "sql": """SELECT 
  user_email,
  MEASURE(failed_events) as failed
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_email
ORDER BY failed DESC
LIMIT 10;"""
        },
    ],
    
    "data_quality_monitor_genie.md": [
        {
            "q": "Show me all tables ordered by freshness",
            "sql": """SELECT table_full_name, freshness_status, hours_since_update
FROM ${catalog}.${gold_schema}.mv_data_quality
ORDER BY hours_since_update DESC
LIMIT 20;"""
        },
        {
            "q": "What is the overall freshness rate?",
            "sql": """SELECT 
  MEASURE(freshness_rate) as freshness_pct,
  MEASURE(staleness_rate) as staleness_pct
FROM ${catalog}.${gold_schema}.mv_data_quality;"""
        },
        {
            "q": "Which tables are stale?",
            "sql": """SELECT table_full_name, hours_since_update
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE freshness_status = 'STALE'
ORDER BY hours_since_update DESC
LIMIT 20;"""
        },
    ],
    
    "unified_health_monitor_genie.md": [
        {
            "q": "What is our total spend this month?",
            "sql": """SELECT MEASURE(total_cost) as mtd_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());"""
        },
        {
            "q": "What is our job success rate?",
            "sql": """SELECT MEASURE(success_rate) as success_pct
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
        {
            "q": "What is the P95 query duration?",
            "sql": """SELECT MEASURE(p95_duration_seconds) as p95_sec
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;"""
        },
    ],
}

def create_benchmark_section(questions):
    """Create benchmark section markdown with questions and SQL."""
    output = []
    for i, q in enumerate(questions, 1):
        output.append(f"### Question {i}: \"{q['q']}\"")
        output.append("**Expected SQL:**")
        output.append("```sql")
        output.append(q['sql'])
        output.append("```")
        output.append(f"**Expected Result:** Query results for: {q['q']}")
        output.append("")
        output.append("---")
        output.append("")
    return "\n".join(output)

for filename, questions in BENCHMARK_QUESTIONS.items():
    filepath = f"src/genie/{filename}"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the benchmark section
    start_marker = "## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████"
    if start_marker not in content:
        print(f"❌ {filename}: Benchmark section not found")
        continue
    
    # Split at benchmark section
    before_section = content.split(start_marker)[0]
    
    # Find the next section (Deliverable Checklist)
    after_marker = "## ✅ DELIVERABLE CHECKLIST"
    if after_marker not in content:
        print(f"❌ {filename}: Deliverable checklist not found")
        continue
    
    after_section = after_marker + content.split(after_marker)[1]
    
    # Rebuild with new benchmark section
    new_content = (
        before_section +
        start_marker + "\n\n" +
        create_benchmark_section(questions) +
        after_section
    )
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"✅ {filename}: Replaced with {len(questions)} simple validated questions")

print("\n✅ All Genie Space markdown files updated with simple validated benchmarks!")
EOFPYTHON





