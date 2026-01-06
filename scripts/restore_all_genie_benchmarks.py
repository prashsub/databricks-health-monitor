#!/usr/bin/env python3
"""
Restore comprehensive benchmark questions (20 normal + 5 deep research) for all 6 Genie Spaces.
Grounded in source documentation with correct column names, table names, and schemas.

Based on:
- docs/semantic-framework/24-metric-views-reference.md
- docs/lakehouse-monitoring-design/04-monitor-catalog.md
- docs/ml-framework-design/07-model-catalog.md
- docs/semantic-framework/appendices/A-quick-reference.md
"""

import re
from pathlib import Path
from typing import List, Dict

# Comprehensive benchmark questions for each Genie Space
BENCHMARKS = {
    "cost_intelligence_genie.md": {
        "section_header": "## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████",
        "questions": [
            # Q1-5: Metric View Basic Aggregations
            {
                "num": 1,
                "question": "What is our total spend this month?",
                "sql": """SELECT MEASURE(total_cost) as mtd_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());""",
                "result": "Single row with month-to-date cost"
            },
            {
                "num": 2,
                "question": "Show me cost by workspace for the last 30 days",
                "sql": """SELECT 
  workspace_name,
  MEASURE(total_cost) as total_cost,
  MEASURE(total_dbu) as total_dbus
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY workspace_name
ORDER BY total_cost DESC
LIMIT 10;""",
                "result": "Top 10 workspaces by cost with DBU consumption"
            },
            {
                "num": 3,
                "question": "What is our tag coverage percentage?",
                "sql": """SELECT MEASURE(tag_coverage_pct) as tag_coverage
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;""",
                "result": "Tag coverage percentage for last 30 days"
            },
            {
                "num": 4,
                "question": "What is our serverless adoption rate?",
                "sql": """SELECT MEASURE(serverless_ratio) as serverless_pct
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;""",
                "result": "Percentage of spend on serverless compute"
            },
            {
                "num": 5,
                "question": "Show me daily cost trend for the last 7 days",
                "sql": """SELECT 
  usage_date,
  MEASURE(total_cost) as daily_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY usage_date
ORDER BY usage_date DESC;""",
                "result": "Daily cost breakdown for last week"
            },
            
            # Q6-10: TVF List Queries
            {
                "num": 6,
                "question": "Show me the top 10 cost contributors this month",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_top_cost_contributors(
  DATE_TRUNC('month', CURRENT_DATE())::STRING,
  CURRENT_DATE()::STRING,
  10
);""",
                "result": "Top 10 workspaces/SKUs by cost with rankings"
            },
            {
                "num": 7,
                "question": "What are the cost anomalies in the last 30 days?",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_cost_anomalies(
  30,
  50.0
)
ORDER BY anomaly_score DESC
LIMIT 20;""",
                "result": "Cost anomalies with deviation scores and severity"
            },
            {
                "num": 8,
                "question": "Show me untagged resources",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_untagged_resources(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
)
ORDER BY untagged_cost DESC
LIMIT 20;""",
                "result": "Resources without tags sorted by cost impact"
            },
            {
                "num": 9,
                "question": "What is the cost breakdown by owner?",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_cost_by_owner(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  15
);""",
                "result": "Chargeback report by resource owner"
            },
            {
                "num": 10,
                "question": "Show me serverless vs classic cost comparison",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_serverless_vs_classic_cost(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING
);""",
                "result": "Compute type cost breakdown with efficiency metrics"
            },
            
            # Q11-15: More TVF Queries
            {
                "num": 11,
                "question": "What is the daily cost summary?",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_daily_cost_summary(
  (CURRENT_DATE() - INTERVAL 14 DAYS)::STRING,
  CURRENT_DATE()::STRING
)
ORDER BY usage_date DESC;""",
                "result": "Daily cost with day-over-day and week-over-week changes"
            },
            {
                "num": 12,
                "question": "Show me cost by SKU for last month",
                "sql": """SELECT 
  sku_name,
  MEASURE(total_cost) as sku_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE() - INTERVAL 1 MONTH)
  AND usage_date < DATE_TRUNC('month', CURRENT_DATE())
GROUP BY sku_name
ORDER BY sku_cost DESC;""",
                "result": "SKU-level cost breakdown for previous month"
            },
            {
                "num": 13,
                "question": "What is our week-over-week cost growth?",
                "sql": """SELECT MEASURE(week_over_week_growth_pct) as wow_growth
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS;""",
                "result": "WoW growth percentage"
            },
            {
                "num": 14,
                "question": "Show me cost by team tag",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_cost_by_tag(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  'team'
)
ORDER BY tag_cost DESC
LIMIT 15;""",
                "result": "Cost allocation by team tag with percentages"
            },
            {
                "num": 15,
                "question": "What is the job cost breakdown?",
                "sql": """SELECT * FROM ${catalog}.${gold_schema}.get_job_cost_breakdown(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  20
);""",
                "result": "Top 20 jobs by compute cost"
            },
            
            # Q16-20: ML Tables and Custom Metrics
            {
                "num": 16,
                "question": "Are there any cost anomalies detected by ML today?",
                "sql": """SELECT 
  w.workspace_name,
  ca.usage_date,
  ca.prediction as anomaly_score
FROM ${catalog}.${feature_schema}.cost_anomaly_predictions ca
JOIN ${catalog}.${gold_schema}.dim_workspace w ON ca.workspace_id = w.workspace_id
WHERE ca.usage_date = CURRENT_DATE()
ORDER BY ca.prediction DESC
LIMIT 10;""",
                "result": "Today's ML-detected cost anomalies with workspace context"
            },
            {
                "num": 17,
                "question": "What is the cost forecast for next week?",
                "sql": """SELECT 
  w.workspace_name,
  bf.usage_date,
  bf.prediction as forecast_cost
FROM ${catalog}.${feature_schema}.budget_forecasts bf
JOIN ${catalog}.${gold_schema}.dim_workspace w ON bf.workspace_id = w.workspace_id
WHERE bf.usage_date BETWEEN CURRENT_DATE() AND CURRENT_DATE() + INTERVAL 7 DAYS
ORDER BY bf.usage_date, forecast_cost DESC;""",
                "result": "7-day cost forecast by workspace from ML model"
            },
            {
                "num": 18,
                "question": "What is the cost drift percentage from Lakehouse Monitoring?",
                "sql": """SELECT 
  window.start AS period_start,
  cost_drift_pct,
  dbu_drift_pct,
  tag_coverage_drift
FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC
LIMIT 10;""",
                "result": "Recent cost drift metrics showing period-over-period changes"
            },
            {
                "num": 19,
                "question": "Show me custom cost metrics by workspace from monitoring tables",
                "sql": """SELECT 
  slice_value AS workspace_id,
  AVG(total_daily_cost) AS avg_daily_cost,
  SUM(total_daily_cost) AS total_cost,
  AVG(serverless_ratio) AS avg_serverless_ratio
FROM ${catalog}.${gold_schema}.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'workspace_id'
GROUP BY slice_value
ORDER BY total_cost DESC
LIMIT 10;""",
                "result": "Per-workspace cost metrics from Lakehouse Monitoring"
            },
            {
                "num": 20,
                "question": "Show me tag recommendations from ML for untagged resources",
                "sql": """SELECT 
  w.workspace_name,
  tr.usage_date,
  tr.prediction as recommended_tags
FROM ${catalog}.${feature_schema}.tag_recommendations tr
JOIN ${catalog}.${gold_schema}.dim_workspace w ON tr.workspace_id = w.workspace_id
WHERE tr.usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY tr.usage_date DESC
LIMIT 20;""",
                "result": "ML-recommended tags for resources with low tag coverage"
            },
        ],
        "deep_research": [
            # Q21-25: Deep Research Questions
            {
                "num": 21,
                "question": "🔬 DEEP RESEARCH: Comprehensive cost optimization analysis - identify workspaces with high cost, low tag coverage, and anomaly patterns for targeted FinOps intervention",
                "sql": """WITH workspace_costs AS (
  SELECT 
    workspace_name,
    MEASURE(total_cost) as total_cost,
    MEASURE(tag_coverage_pct) as tag_coverage,
    MEASURE(serverless_ratio) as serverless_pct
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_name
),
anomalies AS (
  SELECT 
    w.workspace_name,
    COUNT(*) as anomaly_count,
    AVG(ca.prediction) as avg_anomaly_score
  FROM ${catalog}.${feature_schema}.cost_anomaly_predictions ca
  JOIN ${catalog}.${gold_schema}.dim_workspace w ON ca.workspace_id = w.workspace_id
  WHERE ca.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY w.workspace_name
)
SELECT 
  wc.workspace_name,
  wc.total_cost,
  wc.tag_coverage,
  wc.serverless_pct,
  COALESCE(a.anomaly_count, 0) as anomaly_count,
  COALESCE(a.avg_anomaly_score, 0) as avg_anomaly_score,
  CASE 
    WHEN wc.total_cost > 10000 AND wc.tag_coverage < 50 THEN 'High Priority'
    WHEN wc.total_cost > 5000 AND wc.tag_coverage < 75 THEN 'Medium Priority'
    ELSE 'Low Priority'
  END as optimization_priority
FROM workspace_costs wc
LEFT JOIN anomalies a ON wc.workspace_name = a.workspace_name
WHERE wc.total_cost > 1000
ORDER BY wc.total_cost DESC, wc.tag_coverage ASC
LIMIT 10;""",
                "result": "Prioritized workspace optimization opportunities combining cost metrics, tag compliance, and ML anomaly detection - actionable FinOps roadmap"
            },
            {
                "num": 22,
                "question": "🔬 DEEP RESEARCH: Cross-domain cost and reliability correlation - which workspaces have both high cost AND high job failure rates",
                "sql": """WITH cost_ranking AS (
  SELECT 
    workspace_name,
    MEASURE(total_cost) as workspace_cost,
    RANK() OVER (ORDER BY MEASURE(total_cost) DESC) as cost_rank
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_name
),
reliability_ranking AS (
  SELECT 
    workspace_name,
    MEASURE(failure_rate) as failure_rate,
    MEASURE(total_runs) as total_runs,
    RANK() OVER (ORDER BY MEASURE(failure_rate) DESC) as failure_rank
  FROM ${catalog}.${gold_schema}.mv_job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_name
)
SELECT 
  c.workspace_name,
  c.workspace_cost,
  c.cost_rank,
  r.failure_rate,
  r.total_runs,
  r.failure_rank,
  (c.cost_rank + r.failure_rank) / 2.0 as combined_priority_score
FROM cost_ranking c
JOIN reliability_ranking r ON c.workspace_name = r.workspace_name
WHERE c.cost_rank <= 20 OR r.failure_rank <= 20
ORDER BY combined_priority_score ASC
LIMIT 10;""",
                "result": "Workspaces with both cost and reliability issues - indicates infrastructure problems requiring immediate attention"
            },
            {
                "num": 23,
                "question": "🔬 DEEP RESEARCH: SKU-level cost efficiency with utilization patterns - identify overprovisioned compute with low utilization but high cost",
                "sql": """WITH sku_costs AS (
  SELECT 
    sku_name,
    MEASURE(total_cost) as total_sku_cost,
    MEASURE(total_dbu) as total_dbu,
    MEASURE(total_cost) / NULLIF(MEASURE(total_dbu), 0) as cost_per_dbu
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND sku_name LIKE '%COMPUTE%'
  GROUP BY sku_name
),
cluster_util AS (
  SELECT 
    MEASURE(avg_cpu_utilization) as avg_cpu,
    MEASURE(avg_memory_utilization) as avg_memory
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT 
  sc.sku_name,
  sc.total_sku_cost,
  sc.total_dbu,
  sc.cost_per_dbu,
  cu.avg_cpu,
  cu.avg_memory,
  CASE 
    WHEN cu.avg_cpu < 30 AND sc.total_sku_cost > 5000 THEN 'Severely Underutilized'
    WHEN cu.avg_cpu < 50 AND sc.total_sku_cost > 2000 THEN 'Underutilized'
    WHEN cu.avg_cpu > 80 THEN 'Well Utilized'
    ELSE 'Normal'
  END as utilization_status,
  CASE 
    WHEN cu.avg_cpu < 30 THEN sc.total_sku_cost * 0.6
    WHEN cu.avg_cpu < 50 THEN sc.total_sku_cost * 0.3
    ELSE 0
  END as potential_savings
FROM sku_costs sc
CROSS JOIN cluster_util cu
WHERE sc.total_sku_cost > 1000
ORDER BY potential_savings DESC
LIMIT 10;""",
                "result": "SKU efficiency analysis combining cost metrics and utilization data - quantified savings opportunities from right-sizing"
            },
            {
                "num": 24,
                "question": "🔬 DEEP RESEARCH: Tag compliance and cost attribution gap - which business units have the largest unattributable spend",
                "sql": """WITH tagged_costs AS (
  SELECT 
    team_tag,
    MEASURE(total_cost) as tagged_cost
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND team_tag IS NOT NULL
  GROUP BY team_tag
),
total_costs AS (
  SELECT MEASURE(total_cost) as platform_total
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
untagged AS (
  SELECT SUM(untagged_cost) as total_untagged
  FROM ${catalog}.${gold_schema}.get_untagged_resources(
    (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
    CURRENT_DATE()::STRING
  )
)
SELECT 
  tc.team_tag,
  tc.tagged_cost,
  tc.tagged_cost / NULLIF(t.platform_total, 0) * 100 as pct_of_total,
  u.total_untagged,
  u.total_untagged / NULLIF(t.platform_total, 0) * 100 as untagged_pct,
  t.platform_total as total_platform_cost
FROM tagged_costs tc
CROSS JOIN total_costs t
CROSS JOIN untagged u
ORDER BY tc.tagged_cost DESC
LIMIT 10;""",
                "result": "Tag compliance analysis combining metric view aggregations and TVF detail - shows attribution gaps requiring FinOps action"
            },
            {
                "num": 25,
                "question": "🔬 DEEP RESEARCH: Predictive cost optimization roadmap - combine ML forecasts, anomalies, and commitments for prioritized action plan",
                "sql": """WITH cost_forecast AS (
  SELECT 
    w.workspace_name,
    AVG(bf.prediction) as projected_daily_cost
  FROM ${catalog}.${feature_schema}.budget_forecasts bf
  JOIN ${catalog}.${gold_schema}.dim_workspace w ON bf.workspace_id = w.workspace_id
  WHERE bf.usage_date BETWEEN CURRENT_DATE() AND CURRENT_DATE() + INTERVAL 7 DAYS
  GROUP BY w.workspace_name
),
anomalies AS (
  SELECT 
    w.workspace_name,
    COUNT(*) as anomaly_count
  FROM ${catalog}.${feature_schema}.cost_anomaly_predictions ca
  JOIN ${catalog}.${gold_schema}.dim_workspace w ON ca.workspace_id = w.workspace_id
  WHERE ca.usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND ca.prediction > 0.5
  GROUP BY w.workspace_name
),
commitments AS (
  SELECT 
    w.workspace_name,
    AVG(cr.prediction) as recommended_commit
  FROM ${catalog}.${feature_schema}.commitment_recommendations cr
  JOIN ${catalog}.${gold_schema}.dim_workspace w ON cr.workspace_id = w.workspace_id
  WHERE cr.usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY w.workspace_name
)
SELECT 
  cf.workspace_name,
  cf.projected_daily_cost,
  cf.projected_daily_cost * 30 as projected_monthly_cost,
  COALESCE(a.anomaly_count, 0) as recent_anomalies,
  COALESCE(c.recommended_commit, 0) as commit_recommendation,
  CASE 
    WHEN a.anomaly_count > 5 THEN 'Investigate Anomalies First'
    WHEN cf.projected_daily_cost > 1000 AND c.recommended_commit > 0 THEN 'Evaluate Commitment'
    WHEN cf.projected_daily_cost > 500 THEN 'Monitor Closely'
    ELSE 'Normal'
  END as action_priority
FROM cost_forecast cf
LEFT JOIN anomalies a ON cf.workspace_name = a.workspace_name
LEFT JOIN commitments c ON cf.workspace_name = c.workspace_name
WHERE cf.projected_daily_cost > 100
ORDER BY cf.projected_daily_cost DESC
LIMIT 15;""",
                "result": "Comprehensive ML-driven optimization roadmap combining forecasts, anomaly detection, and commitment recommendations - prioritized action plan with business context"
            }
        ]
    }
}

def format_benchmark_question(q: Dict) -> str:
    """Format a single benchmark question."""
    is_deep = "DEEP RESEARCH" in q["question"]
    marker = "🔬 " if is_deep else ""
    
    lines = [
        f"### Question {q['num']}: \"{q['question']}\"",
        "**Expected SQL:**",
        "```sql",
        q['sql'],
        "```",
        f"**Expected Result:** {q['result']}",
        "",
        "---",
        ""
    ]
    return "\n".join(lines)

def generate_benchmark_section(genie_config: Dict) -> str:
    """Generate complete benchmark section."""
    lines = [
        genie_config["section_header"],
        "",
        "> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**",
        "> **Grounded in:** Metric Views, TVFs, ML Tables, Lakehouse Monitors, Fact/Dim Tables",
        "",
        "### ✅ Normal Benchmark Questions (Q1-Q20)",
        ""
    ]
    
    # Add normal questions
    for q in genie_config["questions"]:
        lines.append(format_benchmark_question(q))
    
    # Add deep research header
    lines.append("### 🔬 Deep Research Questions (Q21-Q25)")
    lines.append("")
    
    # Add deep research questions
    for q in genie_config["deep_research"]:
        lines.append(format_benchmark_question(q))
    
    return "\n".join(lines)

def main():
    print("🔄 Restoring comprehensive benchmark questions for all Genie Spaces...")
    print("=" * 100)
    print()
    
    # Only showing cost_intelligence structure for now
    # Full implementation would include all 6 Genie Spaces
    
    genie_file = "src/genie/cost_intelligence_genie.md"
    config = BENCHMARKS["cost_intelligence_genie.md"]
    
    print(f"📝 {genie_file}")
    print(f"   - {len(config['questions'])} normal questions")
    print(f"   - {len(config['deep_research'])} deep research questions")
    print(f"   - Total: {len(config['questions']) + len(config['deep_research'])} questions")
    print()
    
    print("=" * 100)
    print()
    print("⚠️  This is a TEMPLATE SCRIPT.")
    print("    Due to the size (150 questions across 6 files), I will update files individually.")
    print()

if __name__ == "__main__":
    main()

