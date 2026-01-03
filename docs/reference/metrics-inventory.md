# Metrics Inventory

## Overview

This document is the **one-stop reference** for all measurements in the Databricks Health Monitor platform. Each measurement is documented once, with columns indicating which method(s) can be used to access it.

### Reading This Document

| Column | Description |
|--------|-------------|
| **Measurement** | The business metric being measured |
| **Purpose** | What business question this metric answers |
| **TVF** | Table-Valued Function name (parameterized queries) |
| **Metric View** | Metric View name + measure (dashboard aggregates) |
| **Custom Metric** | Lakehouse Monitoring metric (time series analysis) |
| **Primary Use** | Recommended primary method for this metric |

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Available via this method |
| ➡️ | Recommended primary method |
| — | Not available via this method |

---

## Summary Statistics

| Domain | Total Measurements | TVF | Metric View | Custom Metric |
|--------|-------------------|-----|-------------|---------------|
| 💰 Cost | 67 | 38 | 42 | 35 |
| 🔄 Reliability | 58 | 32 | 16 | 50 |
| ⚡ Performance (Query) | 52 | 28 | 18 | 46 |
| ⚡ Performance (Cluster) | 38 | 18 | 24 | 40 |
| 🔒 Security | 28 | 24 | 12 | 13 |
| 📋 Quality | 32 | 18 | 10 | 26 |
| **Total** | **275** | **158** | **122** | **210** |

> Note: Some measurements appear in multiple methods (e.g., success_rate is in all three), which is intentional as they serve different use cases.

---

## 💰 COST DOMAIN

### Core Cost Metrics

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 1 | **Total Daily Cost** | Primary FinOps KPI for budgeting | `get_daily_cost_summary` | `mv_cost_analytics.total_cost` | `total_daily_cost` | ➡️ Metric View |
| 2 | **Total DBUs** | Usage volume independent of pricing | `get_cost_trend_by_sku` | `mv_cost_analytics.total_dbu` | `total_daily_dbu` | ➡️ Metric View |
| 3 | **Cost per DBU** | Unit economics / effective rate | `get_cost_efficiency_metrics` | `mv_cost_analytics.cost_per_dbu` | `avg_cost_per_dbu` | ➡️ Metric View |
| 4 | **MTD Cost** | Month-to-date spending | — | `mv_cost_analytics.mtd_cost` | — | ➡️ Metric View |
| 5 | **YTD Cost** | Year-to-date spending | — | `mv_cost_analytics.ytd_cost` | — | ➡️ Metric View |
| 6 | **Projected Monthly Cost** | Budget forecasting | `get_cost_forecast` | `mv_commit_tracking.projected_monthly_cost` | — | ➡️ Metric View |
| 7 | **Daily Burn Rate** | Daily cost average | — | `mv_commit_tracking.daily_avg_cost` | — | ➡️ Metric View |
| 8 | **Day-over-Day Change %** | Daily cost variance | `get_daily_cost_summary.dod_change_pct` | `mv_cost_analytics.dod_cost_change_pct` | — | ➡️ TVF |
| 9 | **Week-over-Week Growth %** | Weekly cost trend | — | `mv_cost_analytics.week_over_week_growth_pct` | — | ➡️ Metric View |

### Cost Attribution & Breakdown

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 10 | **Top Cost Contributors** | Identify biggest spenders | `get_top_cost_contributors` | By dimension grouping | — | ➡️ TVF |
| 11 | **Cost by Workspace** | Cross-workspace comparison | `get_workspace_cost_comparison` | Group by `workspace_name` | — | ➡️ Metric View |
| 12 | **Cost by SKU** | Product mix analysis | `get_cost_trend_by_sku` | Group by `sku_name` | — | ➡️ TVF |
| 13 | **Cost by Owner** | Chargeback attribution | `get_cost_by_owner` | Group by `owner` | — | ➡️ TVF |
| 14 | **Cost by Tag** | Tag-based allocation | `get_cost_by_tag` | Group by `team_tag`, `project_tag` | — | ➡️ TVF |
| 15 | **Cost by Cluster Type** | Infrastructure analysis | `get_cost_by_cluster_type` | — | — | ➡️ TVF |
| 16 | **Storage Cost** | Storage billing analysis | `get_storage_cost_analysis` | — | — | ➡️ TVF |
| 17 | **Job Cost Breakdown** | Cost per job | `get_job_cost_breakdown` | — | — | ➡️ TVF |
| 18 | **Warehouse Cost** | SQL Warehouse spend | `get_warehouse_cost_analysis` | — | — | ➡️ TVF |

### SKU-Specific Costs

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 19 | **Jobs Compute Cost** | Workflow automation spend | `get_cost_trend_by_sku('%JOBS%')` | Filter `sku_name` | `jobs_compute_cost` | ➡️ Custom Metric |
| 20 | **SQL Compute Cost** | Analytics workload spend | `get_cost_trend_by_sku('%SQL%')` | Filter `sku_name` | `sql_compute_cost` | ➡️ Custom Metric |
| 21 | **All-Purpose Cost** | Interactive compute spend | — | Filter `sku_name` | `all_purpose_cost` | ➡️ Custom Metric |
| 22 | **Serverless Cost** | Modern compute spend | `get_serverless_vs_classic_cost` | Filter `is_serverless` | `serverless_cost` | ➡️ Metric View |
| 23 | **DLT Cost** | Pipeline infrastructure spend | — | — | `dlt_cost` | ➡️ Custom Metric |
| 24 | **Model Serving Cost** | ML serving spend | — | — | `model_serving_cost` | ➡️ Custom Metric |
| 25 | **Jobs Cost Share %** | Workflow proportion | — | — | `jobs_cost_share` | ➡️ Custom Metric |
| 26 | **SQL Cost Share %** | Analytics proportion | — | — | `sql_cost_share` | ➡️ Custom Metric |
| 27 | **Serverless Ratio %** | Modern architecture adoption | — | `mv_cost_analytics.serverless_ratio` | `serverless_ratio` | ➡️ Metric View |

### Tag Coverage & Governance

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 28 | **Tag Coverage %** | FinOps maturity KPI (>90%) | — | `mv_cost_analytics.tag_coverage_pct` | `tag_coverage_pct` | ➡️ Metric View |
| 29 | **Tagged Cost Total** | Attributable spend | — | — | `tagged_cost_total` | ➡️ Custom Metric |
| 30 | **Untagged Cost Total** | Unattributable spend | — | — | `untagged_cost_total` | ➡️ Custom Metric |
| 31 | **Untagged Resources List** | Resources needing tags | `get_untagged_resources` | — | — | ➡️ TVF |
| 32 | **Tagged Record Count** | Tag hygiene volume | — | — | `tagged_record_count` | ➡️ Custom Metric |
| 33 | **Untagged Record Count** | Unattributed records | — | — | `untagged_record_count` | ➡️ Custom Metric |

### Optimization Opportunities

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 34 | **Jobs on All-Purpose Cost** | Inefficient pattern (~40% overspend) | — | — | `jobs_on_all_purpose_cost` | ➡️ Custom Metric |
| 35 | **Jobs on All-Purpose Count** | Optimization candidates | — | — | `jobs_on_all_purpose_count` | ➡️ Custom Metric |
| 36 | **Potential Job Cluster Savings** | Actionable savings estimate | — | — | `potential_job_cluster_savings` | ➡️ Custom Metric |
| 37 | **Jobs on All-Purpose Ratio** | Priority score | — | — | `jobs_on_all_purpose_ratio` | ➡️ Custom Metric |

### Cost Anomalies & Drift

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 38 | **Cost Anomalies** | Cost spikes vs baseline | `get_cost_anomalies` | — | — | ➡️ TVF |
| 39 | **Cost Drift %** | Period cost change (alert >10%) | — | — | `cost_drift_pct` | ➡️ Custom Metric |
| 40 | **DBU Drift %** | Usage volume trend | — | — | `dbu_drift_pct` | ➡️ Custom Metric |
| 41 | **Tag Coverage Drift** | FinOps maturity trend | — | — | `tag_coverage_drift` | ➡️ Custom Metric |

### Data Quality (Cost Data)

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 42 | **Null SKU Count** | Data quality issue | — | — | `null_sku_count` | ➡️ Custom Metric |
| 43 | **Null Price Count** | Billing data quality | — | — | `null_price_count` | ➡️ Custom Metric |
| 44 | **Null SKU Rate %** | Data quality score (<1%) | — | — | `null_sku_rate` | ➡️ Custom Metric |
| 45 | **Null Price Rate %** | Billing completeness (0%) | — | — | `null_price_rate` | ➡️ Custom Metric |
| 46 | **Distinct Workspaces** | Platform utilization breadth | — | — | `distinct_workspaces` | ➡️ Custom Metric |
| 47 | **Distinct SKUs** | Product mix indicator | — | — | `distinct_skus` | ➡️ Custom Metric |
| 48 | **Record Count** | Data completeness | — | — | `record_count` | ➡️ Custom Metric |

---

## 🔄 RELIABILITY DOMAIN

### Core Reliability Metrics

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 49 | **Success Rate %** | Primary reliability KPI (>95%) | `get_job_success_rates.success_rate` | `mv_job_performance.success_rate` | `success_rate` | ➡️ Metric View |
| 50 | **Failure Rate %** | Reliability issues indicator | `get_job_success_rates.failure_rate` | `mv_job_performance.failure_rate` | `failure_rate` | ➡️ Metric View |
| 51 | **Total Runs** | Workload volume | `get_job_success_rates.total_runs` | `mv_job_performance.total_runs` | `total_runs` | ➡️ Metric View |
| 52 | **Success Count** | Reliability numerator | — | — | `success_count` | ➡️ Custom Metric |
| 53 | **Failure Count** | Issues requiring investigation | `get_failed_jobs_summary.failure_count` | `mv_job_performance.failures_today` | `failure_count` | ➡️ Custom Metric |

### Failed Jobs Analysis

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 54 | **Failed Jobs List** | Actionable failure list | `get_failed_jobs_summary` | — | — | ➡️ TVF |
| 55 | **Last Failure Time** | Recency of failure | `get_failed_jobs_summary.last_failure_time` | — | — | ➡️ TVF |
| 56 | **Last Error Message** | Root cause hint | `get_failed_jobs_summary.last_error_message` | — | — | ➡️ TVF |
| 57 | **Failure Patterns** | Error categorization | `get_job_failure_patterns` | — | — | ➡️ TVF |
| 58 | **Job Failure Cost** | Cost of failures | `get_job_failure_cost` | — | — | ➡️ TVF |

### Duration Metrics

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 59 | **Avg Duration (min)** | Performance baseline | `get_job_success_rates.avg_duration_min` | `mv_job_performance.avg_duration_minutes` | `avg_duration_minutes` | ➡️ Metric View |
| 60 | **P50 Duration (min)** | Typical performance | `get_job_duration_percentiles.p50` | — | `p50_duration_minutes` | ➡️ Custom Metric |
| 61 | **P90 Duration (min)** | Outlier threshold | `get_job_duration_percentiles.p90` | — | `p90_duration_minutes` | ➡️ Custom Metric |
| 62 | **P95 Duration (min)** | SLA target threshold | `get_job_duration_percentiles.p95` | `mv_job_performance.p95_duration_minutes` | `p95_duration_minutes` | ➡️ Metric View |
| 63 | **P99 Duration (min)** | Critical SLA threshold | `get_job_duration_percentiles.p99` | — | `p99_duration_minutes` | ➡️ Custom Metric |
| 64 | **Max Duration (min)** | Worst-case performance | `get_job_duration_percentiles.max` | — | `max_duration_minutes` | ➡️ TVF |
| 65 | **Min Duration (min)** | Best-case performance | — | — | `min_duration_minutes` | ➡️ Custom Metric |
| 66 | **Total Duration (min)** | Compute time consumption | — | — | `total_duration_minutes` | ➡️ Custom Metric |
| 67 | **Duration Std Dev** | Consistency indicator | — | — | `stddev_duration_minutes` | ➡️ Custom Metric |
| 68 | **Duration CV** | Consistency score (lower=better) | — | — | `duration_cv` | ➡️ Custom Metric |
| 69 | **Duration Skew Ratio** | Distribution skewness | — | — | `duration_skew_ratio` | ➡️ Custom Metric |
| 70 | **Tail Ratio** | P99/P95 ratio | — | — | `tail_ratio` | ➡️ Custom Metric |

### Duration Thresholds

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 71 | **Long Running Jobs (>60m)** | Optimization candidates | `get_long_running_jobs` | — | `long_running_count` | ➡️ TVF |
| 72 | **Very Long Running Jobs (>4h)** | Resource-intensive jobs | — | — | `very_long_running_count` | ➡️ Custom Metric |
| 73 | **Long Running Rate %** | Optimization opportunity | — | — | `long_running_rate` | ➡️ Custom Metric |

### Duration Trends

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 74 | **Duration Trends** | Performance trending | `get_job_duration_trends` | — | — | ➡️ TVF |
| 75 | **Duration Drift %** | Performance regression | — | — | `duration_drift_pct` | ➡️ Custom Metric |
| 76 | **P99 Duration Drift %** | SLA compliance trend | — | — | `p99_duration_drift_pct` | ➡️ Custom Metric |
| 77 | **Long Running Drift** | Performance degradation | — | — | `long_running_drift` | ➡️ Custom Metric |

### Termination Analysis

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 78 | **Timeout Count** | Resource constraint issues | — | — | `timeout_count` | ➡️ Custom Metric |
| 79 | **Cancelled Count** | Manual interventions | — | — | `cancelled_count` | ➡️ Custom Metric |
| 80 | **Skipped Count** | Dependency issues | — | — | `skipped_count` | ➡️ Custom Metric |
| 81 | **Upstream Failed Count** | Dependency chain failures | — | — | `upstream_failed_count` | ➡️ Custom Metric |
| 82 | **User Cancelled Count** | Manual intervention freq | — | — | `user_cancelled_count` | ➡️ Custom Metric |
| 83 | **Internal Error Count** | Platform stability | — | — | `internal_error_count` | ➡️ Custom Metric |
| 84 | **Driver Error Count** | Code/config issues | — | — | `driver_error_count` | ➡️ Custom Metric |
| 85 | **Timeout Rate %** | Resource constraint rate | — | — | `timeout_rate` | ➡️ Custom Metric |
| 86 | **Cancellation Rate %** | Intervention frequency | — | — | `cancellation_rate` | ➡️ Custom Metric |
| 87 | **Skipped Rate %** | Dependency issue rate | — | — | `skipped_rate` | ➡️ Custom Metric |
| 88 | **Upstream Failed Rate %** | Chain health indicator | — | — | `upstream_failed_rate` | ➡️ Custom Metric |

### Trigger & Schedule Analysis

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 89 | **Scheduled Runs** | Automated workload | — | By `trigger_type` | `scheduled_runs` | ➡️ Metric View |
| 90 | **Manual Runs** | Ad-hoc workload | — | By `trigger_type` | `manual_runs` | ➡️ Custom Metric |
| 91 | **Retry Runs** | Recovery activity | — | By `trigger_type` | `retry_runs` | ➡️ Custom Metric |
| 92 | **Scheduled Ratio %** | Automation maturity (>80%) | — | — | `scheduled_ratio` | ➡️ Custom Metric |
| 93 | **Schedule Drift** | Jobs not on schedule | `get_job_schedule_drift` | — | — | ➡️ TVF |

### SLA & Retry Analysis

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 94 | **SLA Compliance %** | SLA tracking | `get_job_sla_compliance.sla_compliance_pct` | — | — | ➡️ TVF |
| 95 | **Runs Within SLA** | SLA-compliant runs | `get_job_sla_compliance.runs_within_sla` | — | — | ➡️ TVF |
| 96 | **Runs Breaching SLA** | SLA violations | `get_job_sla_compliance.runs_breaching_sla` | — | — | ➡️ TVF |
| 97 | **Retry Effectiveness %** | Recovery success rate | `get_job_retry_analysis.retry_effectiveness_pct` | — | — | ➡️ TVF |
| 98 | **Wasted Compute (min)** | Failure compute cost | `get_job_retry_analysis.wasted_compute_min` | — | — | ➡️ TVF |
| 99 | **Repair Rate %** | Retry activity level | — | — | `repair_rate` | ➡️ Custom Metric |
| 100 | **Repair Cost Analysis** | Cost of repairs | `get_repair_cost_analysis` | — | — | ➡️ TVF |

### Pipeline Health

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 101 | **Pipeline Health** | DLT pipeline status | `get_pipeline_health` | — | — | ➡️ TVF |
| 102 | **Pipeline Success Rate** | DLT reliability | `get_pipeline_health.success_rate` | — | — | ➡️ TVF |

### Reliability Drift

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 103 | **Success Rate Drift** | Reliability trend | — | — | `success_rate_drift` | ➡️ Custom Metric |
| 104 | **Failure Count Drift** | Problem emergence | — | — | `failure_count_drift` | ➡️ Custom Metric |
| 105 | **Run Count Drift %** | Workload trend | — | — | `run_count_drift_pct` | ➡️ Custom Metric |
| 106 | **Duration CV Drift** | Consistency trend | — | — | `duration_cv_drift` | ➡️ Custom Metric |

---

## ⚡ PERFORMANCE DOMAIN - QUERY

### Query Volume & Reliability

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 107 | **Query Count** | Query workload volume | `get_query_volume_trends.query_count` | `mv_query_performance.total_queries` | `query_count` | ➡️ Metric View |
| 108 | **Successful Queries** | Reliability numerator | — | — | `successful_queries` | ➡️ Custom Metric |
| 109 | **Failed Queries** | Query failures | `get_query_error_analysis` | — | `failed_queries` | ➡️ TVF |
| 110 | **Cancelled Queries** | User interventions | — | — | `cancelled_queries` | ➡️ Custom Metric |
| 111 | **Query Success Rate %** | Query reliability KPI | — | — | `query_success_rate` | ➡️ Custom Metric |
| 112 | **Query Failure Rate %** | Query reliability issues | — | — | `query_failure_rate` | ➡️ Custom Metric |
| 113 | **Distinct Users** | User base size | `get_top_users_by_query_count` | — | `distinct_users` | ➡️ TVF |
| 114 | **Distinct Warehouses** | Warehouse usage | — | — | `distinct_warehouses` | ➡️ Custom Metric |

### Query Latency

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 115 | **Avg Duration (sec)** | Performance baseline | `get_query_latency_percentiles.avg` | `mv_query_performance.avg_duration_seconds` | `avg_duration_sec` | ➡️ Metric View |
| 116 | **P50 Duration (sec)** | Typical performance | `get_query_latency_percentiles.p50` | — | `p50_duration_sec` | ➡️ Custom Metric |
| 117 | **P95 Duration (sec)** | SLA threshold | `get_query_latency_percentiles.p95` | `mv_query_performance.p95_duration_seconds` | `p95_duration_sec` | ➡️ Metric View |
| 118 | **P99 Duration (sec)** | Worst-case | `get_query_latency_percentiles.p99` | `mv_query_performance.p99_duration_seconds` | `p99_duration_sec` | ➡️ Metric View |
| 119 | **Max Duration (sec)** | Extreme outlier | `get_query_latency_percentiles.max` | — | `max_duration_sec` | ➡️ TVF |
| 120 | **Total Duration (sec)** | Total query time | — | — | `total_duration_sec` | ➡️ Custom Metric |

### Slow Queries

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 121 | **Slow Query List** | Optimization candidates | `get_slow_queries` | — | — | ➡️ TVF |
| 122 | **Slow Query Count (>5m)** | Slow query volume | — | — | `slow_query_count` | ➡️ Custom Metric |
| 123 | **Very Slow Query Count (>15m)** | Critical slow queries | — | — | `very_slow_query_count` | ➡️ Custom Metric |
| 124 | **Slow Query Rate %** | Slow query proportion | — | — | `slow_query_rate` | ➡️ Custom Metric |
| 125 | **SLA Breach Count (>60s)** | SLA violations | — | — | `sla_breach_count` | ➡️ Custom Metric |
| 126 | **SLA Breach Rate %** | SLA compliance | — | — | `sla_breach_rate` | ➡️ Custom Metric |

### Queue & Capacity

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 127 | **Queue Time Analysis** | Queue patterns | `get_query_queue_analysis` | — | — | ➡️ TVF |
| 128 | **Avg Queue Time (sec)** | Capacity indicator | `get_query_queue_analysis.avg_queue_time` | — | `avg_queue_time_sec` | ➡️ Custom Metric |
| 129 | **Total Queue Time (sec)** | Cumulative wait | — | — | `total_queue_time_sec` | ➡️ Custom Metric |
| 130 | **High Queue Count** | Queue >10% of duration | — | — | `high_queue_count` | ➡️ Custom Metric |
| 131 | **High Queue Rate %** | Capacity issues rate | — | — | `high_queue_rate` | ➡️ Custom Metric |
| 132 | **Severe Queue Count** | Queue >30% of duration | — | — | `high_queue_severe_count` | ➡️ Custom Metric |
| 133 | **Severe Queue Rate %** | Severe capacity rate | — | — | `severe_queue_rate` | ➡️ Custom Metric |

### Efficiency & Cache

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 134 | **Efficient Query Count** | No spill, low queue, <60s | — | — | `efficient_query_count` | ➡️ Custom Metric |
| 135 | **Efficiency Rate %** | Query efficiency KPI | — | — | `efficiency_rate` | ➡️ Custom Metric |
| 136 | **Cache Hit Count** | Result cache hits | — | — | `cache_hit_count` | ➡️ Custom Metric |
| 137 | **Cache Hit Rate %** | Cache efficiency | — | `mv_query_performance.cache_hit_rate` | `cache_hit_rate` | ➡️ Metric View |

### Memory & Spill

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 138 | **Spill Analysis** | Memory pressure queries | `get_spill_analysis` | — | — | ➡️ TVF |
| 139 | **Queries with Spill** | Memory pressure count | — | — | `queries_with_spill` | ➡️ Custom Metric |
| 140 | **Total Spilled Bytes** | Spill volume | — | — | `total_spilled_bytes` | ➡️ Custom Metric |
| 141 | **Spill Rate %** | Memory pressure rate | — | `mv_query_performance.spill_rate` | `spill_rate` | ➡️ Metric View |

### I/O & Data Access

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 142 | **Total Bytes Read (TB)** | IO efficiency | — | — | `total_bytes_read_tb` | ➡️ Custom Metric |
| 143 | **Total Rows Read (B)** | Data access volume | — | — | `total_rows_read_b` | ➡️ Custom Metric |
| 144 | **Avg Bytes per Query** | Query scope | — | — | `avg_bytes_per_query` | ➡️ Custom Metric |
| 145 | **Avg Compilation (sec)** | Parse efficiency | — | — | `avg_compilation_sec` | ➡️ Custom Metric |
| 146 | **Complex Query Count** | Query >5000 chars | — | — | `complex_query_count` | ➡️ Custom Metric |
| 147 | **Complex Query Rate %** | Complexity proportion | — | — | `complex_query_rate` | ➡️ Custom Metric |

### Warehouse Utilization

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 148 | **Warehouse Utilization** | Warehouse efficiency | `get_warehouse_utilization` | — | — | ➡️ TVF |
| 149 | **Scaling Events** | Auto-scaling activity | `get_warehouse_scaling_events` | — | — | ➡️ TVF |
| 150 | **Query Cost by User** | User cost attribution | `get_query_cost_by_user` | — | — | ➡️ TVF |

### Query Performance Drift

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 151 | **P95 Duration Drift %** | Performance trend | — | — | `p95_duration_drift_pct` | ➡️ Custom Metric |
| 152 | **P99 Duration Drift %** | Worst-case trend | — | — | `p99_duration_drift_pct` | ➡️ Custom Metric |
| 153 | **Query Volume Drift %** | Usage trend | — | — | `query_volume_drift_pct` | ➡️ Custom Metric |
| 154 | **Failure Rate Drift** | Reliability trend | — | — | `failure_rate_drift` | ➡️ Custom Metric |
| 155 | **Spill Rate Drift** | Memory pressure trend | — | — | `spill_rate_drift` | ➡️ Custom Metric |
| 156 | **SLA Breach Rate Drift** | Compliance trend | — | — | `sla_breach_rate_drift` | ➡️ Custom Metric |
| 157 | **Efficiency Rate Drift** | Optimization trend | — | — | `efficiency_rate_drift` | ➡️ Custom Metric |

---

## ⚡ PERFORMANCE DOMAIN - CLUSTER

### Cluster Resource Metrics

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 158 | **Cluster Utilization** | Resource utilization | `get_cluster_utilization` | — | — | ➡️ TVF |
| 159 | **Avg CPU User %** | User CPU utilization | — | — | `avg_cpu_user_pct` | ➡️ Custom Metric |
| 160 | **Avg CPU System %** | System CPU | — | — | `avg_cpu_system_pct` | ➡️ Custom Metric |
| 161 | **Avg CPU Wait %** | IO wait time | — | — | `avg_cpu_wait_pct` | ➡️ Custom Metric |
| 162 | **Max CPU %** | Peak CPU | — | — | `max_cpu_*` | ➡️ Custom Metric |
| 163 | **P95 CPU Total %** | CPU SLA threshold | — | — | `p95_cpu_total_pct` | ➡️ Custom Metric |
| 164 | **Avg CPU Utilization %** | Overall CPU | `get_cluster_utilization.avg_cpu_pct` | `mv_cluster_utilization.avg_cpu_utilization` | — | ➡️ Metric View |
| 165 | **Avg Memory %** | Memory utilization | `get_cluster_utilization.avg_memory_pct` | `mv_cluster_utilization.avg_memory_utilization` | `avg_memory_pct` | ➡️ Metric View |
| 166 | **Max Memory %** | Peak memory | — | — | `max_memory_pct` | ➡️ Custom Metric |
| 167 | **P95 Memory %** | Memory SLA threshold | — | — | `p95_memory_pct` | ➡️ Custom Metric |
| 168 | **Avg Swap %** | Swap usage (bad) | — | — | `avg_swap_pct` | ➡️ Custom Metric |

### Network Metrics

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 169 | **Network Sent (GB)** | Egress volume | — | — | `total_network_sent_gb` | ➡️ Custom Metric |
| 170 | **Network Received (GB)** | Ingress volume | — | — | `total_network_received_gb` | ➡️ Custom Metric |
| 171 | **Avg Network Throughput** | Network efficiency | — | — | `avg_network_*` | ➡️ Custom Metric |

### Right-Sizing & Optimization

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 172 | **Underutilized Clusters** | Low utilization | `get_underutilized_clusters` | — | — | ➡️ TVF |
| 173 | **Underutilized Hours** | Wasted time | — | — | `underutilized_hours` | ➡️ Custom Metric |
| 174 | **Overutilized Hours** | Capacity issues | — | — | `overutilized_hours` | ➡️ Custom Metric |
| 175 | **Optimal Util Hours** | Right-sized time | — | — | `optimal_util_hours` | ➡️ Custom Metric |
| 176 | **CPU Saturation Hours** | CPU bottleneck | — | — | `cpu_saturation_hours` | ➡️ Custom Metric |
| 177 | **CPU Idle Hours** | Wasted CPU | — | — | `cpu_idle_hours` | ➡️ Custom Metric |
| 178 | **Underutilization Rate %** | Wasted proportion | — | — | `underutilization_rate` | ➡️ Custom Metric |
| 179 | **Overutilization Rate %** | Capacity issue rate | — | — | `overutilization_rate` | ➡️ Custom Metric |
| 180 | **Rightsizing Opportunity %** | Potential savings | — | — | `rightsizing_opportunity_pct` | ➡️ Custom Metric |
| 181 | **Cluster Rightsizing Recs** | Specific recommendations | `get_cluster_rightsizing` | — | — | ➡️ TVF |
| 182 | **Cluster Cost Efficiency** | Cost per compute | `get_cluster_cost_efficiency` | — | — | ➡️ TVF |

### Cluster Efficiency (Metric Views)

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 183 | **Efficiency Score** | Composite metric 0-100 | — | `mv_cluster_efficiency.efficiency_score` | `efficiency_score` | ➡️ Metric View |
| 184 | **Idle Percentage %** | CPU <10% time | — | `mv_cluster_efficiency.idle_percentage` | — | ➡️ Metric View |
| 185 | **Wasted Hours** | Idle node hours | — | `mv_cluster_utilization.wasted_hours` | — | ➡️ Metric View |
| 186 | **Potential Savings %** | Estimated savings | — | `mv_cluster_utilization.potential_savings_pct` | — | ➡️ Metric View |
| 187 | **Underutilized Cluster Count** | Problem cluster count | — | `mv_cluster_efficiency.underutilized_cluster_count` | — | ➡️ Metric View |
| 188 | **Idle Node Hours Total** | Total wasted hours | — | `mv_cluster_efficiency.idle_node_hours_total` | — | ➡️ Metric View |

### Node Metrics

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 189 | **Node Hour Count** | Infrastructure scale | — | — | `node_hour_count` | ➡️ Custom Metric |
| 190 | **Distinct Nodes** | Node diversity | — | — | `distinct_nodes` | ➡️ Custom Metric |
| 191 | **Distinct Clusters** | Cluster count | — | — | `distinct_clusters` | ➡️ Custom Metric |
| 192 | **Driver Node Count** | Driver nodes | — | — | `driver_node_count` | ➡️ Custom Metric |
| 193 | **Worker Node Count** | Worker nodes | — | — | `worker_node_count` | ➡️ Custom Metric |

### Compute Optimization TVFs

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 194 | **Jobs Without Autoscaling** | Autoscaling candidates | `get_jobs_without_autoscaling` | — | — | ➡️ TVF |
| 195 | **Jobs on Legacy DBR** | DBR upgrade candidates | `get_jobs_on_legacy_dbr` | — | — | ➡️ TVF |

### Cluster Drift

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 196 | **CPU Utilization Drift** | CPU trend | — | — | `cpu_utilization_drift` | ➡️ Custom Metric |
| 197 | **Memory Utilization Drift** | Memory trend | — | — | `memory_utilization_drift` | ➡️ Custom Metric |
| 198 | **Efficiency Score Drift** | Efficiency trend | — | — | `efficiency_score_drift` | ➡️ Custom Metric |

---

## 🔒 SECURITY DOMAIN

### User Activity

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 199 | **User Activity Summary** | User activity overview | `get_user_activity_summary` | — | — | ➡️ TVF |
| 200 | **Total Events** | Activity volume | `get_user_activity_summary.total_events` | `mv_security_events.total_events` | `total_events` | ➡️ Metric View |
| 201 | **Distinct Users** | User base size | — | `mv_security_events.unique_users` | `distinct_users` | ➡️ Metric View |
| 202 | **Activity Patterns** | Time-based patterns | `get_user_activity_patterns` | — | — | ➡️ TVF |
| 203 | **Events per User** | Activity level | — | — | `events_per_user` | ➡️ Custom Metric |

### Authentication

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 204 | **Failed Access Attempts** | Auth failures list | `get_failed_access_attempts` | — | — | ➡️ TVF |
| 205 | **Failed Auth Count** | Security incidents | `get_failed_access_attempts.failure_count` | `mv_security_events.failed_events` | `failed_auth_count` | ➡️ Custom Metric |
| 206 | **Failed Auth Rate %** | Security risk (>1%) | — | — | `failed_auth_rate` | ➡️ Custom Metric |
| 207 | **Auth Failure Drift** | Security posture trend | — | — | `auth_failure_drift` | ➡️ Custom Metric |

### Privileged Activity

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 208 | **Permission Changes** | Permission audit trail | `get_permission_changes` | — | — | ➡️ TVF |
| 209 | **Sensitive Actions** | Privileged operations | — | — | `sensitive_actions` | ➡️ Custom Metric |
| 210 | **Sensitive Events (24h)** | Recent sensitive activity | — | `mv_security_events.sensitive_events_24h` | — | ➡️ Metric View |
| 211 | **Admin Actions** | Admin activity | — | — | `admin_actions` | ➡️ Custom Metric |
| 212 | **Admin Action Rate %** | Privileged proportion | — | — | `admin_action_rate` | ➡️ Custom Metric |
| 213 | **Data Access Events** | Read operations | — | — | `data_access_events` | ➡️ Custom Metric |
| 214 | **Service Account Activity** | Automation audit | `get_service_account_activity` | — | — | ➡️ TVF |

### Data Access Audit

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 215 | **Table Access Audit** | Table access patterns | `get_table_access_audit` | — | — | ➡️ TVF |
| 216 | **Sensitive Data Access** | PII table access | `get_sensitive_data_access` | — | — | ➡️ TVF |
| 217 | **Data Export Events** | Download tracking | `get_data_export_events` | — | — | ➡️ TVF |

### Anomaly & Risk

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 218 | **Unusual Access Patterns** | Anomaly detection | `get_unusual_access_patterns` | — | — | ➡️ TVF |
| 219 | **User Risk Scores** | Risk assessment | `get_user_risk_scores` | — | — | ➡️ TVF |
| 220 | **Event Growth Rate %** | Activity trend | — | `mv_security_events.event_growth_rate` | — | ➡️ Metric View |

### Governance (Lineage)

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 221 | **Read Events** | Read operation counts | — | `mv_governance_analytics.read_events` | — | ➡️ Metric View |
| 222 | **Write Events** | Write operation counts | — | `mv_governance_analytics.write_events` | — | ➡️ Metric View |
| 223 | **Active Table Count** | Tables accessed (30d) | — | `mv_governance_analytics.active_table_count` | — | ➡️ Metric View |
| 224 | **Inactive Table Count** | Stale tables | — | `mv_governance_analytics.inactive_table_count` | — | ➡️ Metric View |

---

## 📋 QUALITY DOMAIN

### Data Freshness

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 225 | **Table Freshness** | When last updated | `get_table_freshness` | — | — | ➡️ TVF |
| 226 | **Stale Tables List** | Tables not updated | `get_stale_tables` | — | — | ➡️ TVF |
| 227 | **Freshness by Domain** | Portfolio freshness | `get_data_freshness_by_domain` | — | — | ➡️ TVF |
| 228 | **Freshness Rate %** | Tables <24h old | — | `mv_data_quality.freshness_rate` | — | ➡️ Metric View |
| 229 | **Staleness Rate %** | Tables >48h old | — | `mv_data_quality.staleness_rate` | — | ➡️ Metric View |
| 230 | **Fresh Tables Count** | Fresh table count | — | `mv_data_quality.fresh_tables` | — | ➡️ Metric View |
| 231 | **Stale Tables Count** | Stale table count | — | `mv_data_quality.stale_tables` | `tables_with_issues` | ➡️ Metric View |
| 232 | **Avg Hours Since Update** | Average table age | — | `mv_data_quality.avg_hours_since_update` | `avg_freshness_hours` | ➡️ Metric View |
| 233 | **Freshness Violations** | Data currency issues | — | — | `freshness_violations` | ➡️ Custom Metric |

### Data Quality Scores

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 234 | **Total Tables** | Quality scope | — | — | `total_tables` | ➡️ Custom Metric |
| 235 | **Tables with Issues** | Quality problems | — | — | `tables_with_issues` | ➡️ Custom Metric |
| 236 | **Avg Quality Score** | Overall quality (0-100) | — | — | `avg_quality_score` | ➡️ Custom Metric |
| 237 | **Quality Score Below Threshold** | Tables <80 score | — | — | `quality_score_below_threshold` | ➡️ Custom Metric |
| 238 | **Null Violation Count** | Completeness issues | — | — | `null_violation_count` | ➡️ Custom Metric |
| 239 | **Schema Drift Count** | Schema changes | — | — | `schema_drift_count` | ➡️ Custom Metric |
| 240 | **Quality Issue Rate %** | Quality coverage | — | — | `quality_issue_rate` | ➡️ Custom Metric |
| 241 | **Quality Drift** | Quality trend | — | — | `quality_drift` | ➡️ Custom Metric |

### Data Lineage

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 242 | **Lineage Summary** | Upstream/downstream deps | `get_data_lineage_summary` | — | — | ➡️ TVF |
| 243 | **Orphan Tables** | Tables with no access | `get_orphan_tables` | — | — | ➡️ TVF |

### Governance Coverage

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 244 | **Governance Compliance** | Tag compliance | `get_governance_compliance` | — | — | ➡️ TVF |
| 245 | **Table Ownership Report** | Ownership metadata | `get_table_ownership_report` | — | — | ➡️ TVF |
| 246 | **Total Assets** | Governance scope | — | — | `total_assets` | ➡️ Custom Metric |
| 247 | **Documented Assets** | Documentation coverage | — | — | `documented_assets` | ➡️ Custom Metric |
| 248 | **Tagged Assets** | Tagging coverage | — | — | `tagged_assets` | ➡️ Custom Metric |
| 249 | **Access Controlled Assets** | Security coverage | — | — | `access_controlled_assets` | ➡️ Custom Metric |
| 250 | **Lineage Tracked Assets** | Provenance coverage | — | — | `lineage_tracked_assets` | ➡️ Custom Metric |
| 251 | **Documentation Rate %** | Doc coverage (>80%) | — | — | `documentation_rate` | ➡️ Custom Metric |
| 252 | **Tagging Rate %** | Tag coverage (>90%) | — | — | `tagging_rate` | ➡️ Custom Metric |
| 253 | **Access Control Rate %** | Security coverage (100%) | — | — | `access_control_rate` | ➡️ Custom Metric |
| 254 | **Lineage Coverage Rate %** | Provenance (>70%) | — | — | `lineage_coverage_rate` | ➡️ Custom Metric |
| 255 | **Governance Score** | Composite maturity (0-100) | — | — | `governance_score` | ➡️ Custom Metric |
| 256 | **Governance Drift** | Maturity trend | — | — | `governance_drift` | ➡️ Custom Metric |

### ML Anomaly Detection

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 257 | **Total Predictions** | ML coverage | — | `mv_ml_intelligence.total_predictions` | — | ➡️ Metric View |
| 258 | **Anomaly Count** | Flagged anomalies | — | `mv_ml_intelligence.anomaly_count` | — | ➡️ Metric View |
| 259 | **Anomaly Rate %** | Anomaly proportion | — | `mv_ml_intelligence.anomaly_rate` | — | ➡️ Metric View |
| 260 | **Avg Anomaly Score** | Average score (0-1) | — | `mv_ml_intelligence.avg_anomaly_score` | — | ➡️ Metric View |
| 261 | **High Risk Count** | Score ≥0.7 | — | `mv_ml_intelligence.high_risk_count` | — | ➡️ Metric View |
| 262 | **Critical Count** | Score ≥0.9 | — | `mv_ml_intelligence.critical_count` | — | ➡️ Metric View |
| 263 | **Anomaly Cost** | Cost of anomalies | — | `mv_ml_intelligence.anomaly_cost` | — | ➡️ Metric View |

---

## 🤖 ML INFERENCE DOMAIN

### Request Volume & Reliability

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 264 | **Total Requests** | ML serving volume | — | — | `total_requests` | ➡️ Custom Metric |
| 265 | **Successful Requests** | ML reliability numerator | — | — | `successful_requests` | ➡️ Custom Metric |
| 266 | **Failed Requests** | ML reliability issues | — | — | `failed_requests` | ➡️ Custom Metric |
| 267 | **Request Success Rate %** | ML reliability KPI (>99%) | — | — | `request_success_rate` | ➡️ Custom Metric |
| 268 | **Error Rate %** | ML reliability issues (<1%) | — | — | `error_rate` | ➡️ Custom Metric |

### Latency

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 269 | **Avg Latency (ms)** | ML performance baseline | — | — | `avg_latency_ms` | ➡️ Custom Metric |
| 270 | **P50 Latency (ms)** | Typical ML performance | — | — | `p50_latency_ms` | ➡️ Custom Metric |
| 271 | **P95 Latency (ms)** | ML SLA threshold | — | — | `p95_latency_ms` | ➡️ Custom Metric |
| 272 | **P99 Latency (ms)** | Worst-case ML performance | — | — | `p99_latency_ms` | ➡️ Custom Metric |

### Throughput & Tokens

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 273 | **Throughput per Second** | ML capacity utilization | — | — | `throughput_per_second` | ➡️ Custom Metric |
| 274 | **Total Tokens** | LLM usage volume | — | — | `total_tokens` | ➡️ Custom Metric |
| 275 | **Avg Tokens per Request** | Request complexity | — | — | `avg_tokens_per_request` | ➡️ Custom Metric |

### Drift

| # | Measurement | Purpose | TVF | Metric View | Custom Metric | Primary Use |
|---|-------------|---------|-----|-------------|---------------|-------------|
| 276 | **Latency Drift %** | ML performance trend | — | — | `latency_drift_pct` | ➡️ Custom Metric |
| 277 | **Error Rate Drift** | ML reliability trend | — | — | `error_rate_drift` | ➡️ Custom Metric |

---

## 🤖 ML Model Integration (25 Models)

### ML Model to Metric Mapping

Each ML model in the platform enhances specific metrics with predictive capabilities:

| Domain | ML Model | Enhances Metric | Prediction Table | Question Type |
|--------|----------|----------------|------------------|---------------|
| **💰 Cost** | `cost_anomaly_detector` | Cost Anomalies (#38) | `cost_anomaly_predictions` | "Flag unusual spending" |
| **💰 Cost** | `budget_forecaster` | Projected Monthly Cost (#6) | `cost_forecast_predictions` | "Forecast next month's cost" |
| **💰 Cost** | `job_cost_optimizer` | Optimization Savings (#34-37) | `migration_recommendations` | "Where can we save money?" |
| **💰 Cost** | `chargeback_attribution` | Cost by Owner (#13) | — | "Allocate cost to teams" |
| **💰 Cost** | `commitment_recommender` | Projected Cost (#6) | `budget_alert_predictions` | "Recommend commitment level" |
| **💰 Cost** | `tag_recommender` | Tag Coverage (#28) | `tag_recommendations` | "Suggest tags for resources" |
| **🔄 Reliability** | `job_failure_predictor` | Failure Rate (#50) | `job_failure_predictions` | "Which jobs will fail?" |
| **🔄 Reliability** | `job_duration_forecaster` | Duration (#59-70) | `job_duration_predictions` | "How long will job take?" |
| **🔄 Reliability** | `sla_breach_predictor` | SLA Compliance (#94-96) | `incident_impact_predictions` | "Will SLA breach occur?" |
| **🔄 Reliability** | `pipeline_health_scorer` | Pipeline Health (#101-102) | `pipeline_health_scores` | "Rate pipeline health" |
| **🔄 Reliability** | `retry_success_predictor` | Retry Effectiveness (#97) | `retry_success_predictions` | "Will retry succeed?" |
| **⚡ Performance** | `query_performance_forecaster` | P99 Duration (#118) | `query_optimization_recommendations` | "Predict query latency" |
| **⚡ Performance** | `warehouse_optimizer` | Warehouse Utilization (#148) | `cluster_capacity_recommendations` | "Optimize warehouse size" |
| **⚡ Performance** | `cache_hit_predictor` | Cache Hit Rate (#137) | `cache_hit_predictions` | "Predict cache performance" |
| **⚡ Performance** | `cluster_sizing_recommender` | Cluster Efficiency (#183) | `cluster_rightsizing_recommendations` | "Right-size clusters" |
| **⚡ Performance** | `cluster_capacity_planner` | Utilization (#164-165) | `cluster_capacity_recommendations` | "Plan capacity needs" |
| **⚡ Performance** | `regression_detector` | Duration Drift (#75-77) | — | "Detect performance regression" |
| **⚡ Performance** | `query_optimization_recommender` | Slow Queries (#121-126) | `query_optimization_classifications` | "How to optimize queries?" |
| **🔒 Security** | `security_threat_detector` | Unusual Access (#218) | `access_anomaly_predictions` | "Detect security threats" |
| **🔒 Security** | `access_pattern_analyzer` | Activity Patterns (#202) | `access_classifications` | "Classify access patterns" |
| **🔒 Security** | `compliance_risk_classifier` | Risk Scores (#219) | `user_risk_scores` | "Assess compliance risk" |
| **🔒 Security** | `permission_recommender` | Permission Changes (#208) | — | "Recommend permission changes" |
| **📋 Quality** | `data_drift_detector` | Quality Drift (#241) | `quality_anomaly_predictions` | "Detect data drift" |
| **📋 Quality** | `schema_change_predictor` | Schema Drift (#239) | `quality_trend_predictions` | "Predict schema changes" |
| **📋 Quality** | `schema_evolution_predictor` | Schema Drift (#239) | `freshness_alert_predictions` | "Predict evolution patterns" |

### ML Prediction Output Reference

| Prediction Table | Key Output Columns | Threshold for Action |
|------------------|-------------------|---------------------|
| `cost_anomaly_predictions` | `anomaly_score`, `is_anomaly` | `is_anomaly = 1` or `anomaly_score < -0.5` |
| `cost_forecast_predictions` | `predicted_cost`, `confidence_interval` | When `actual > predicted * 1.2` |
| `job_failure_predictions` | `failure_probability`, `will_fail` | `failure_probability > 0.5` |
| `job_duration_predictions` | `predicted_duration_sec` | When `actual > predicted * 1.5` |
| `access_anomaly_predictions` | `threat_score`, `is_threat` | `is_threat = 1` or `threat_score < -0.5` |
| `user_risk_scores` | `risk_level` (1-5) | `risk_level >= 4` |
| `quality_anomaly_predictions` | `drift_score`, `is_drifted` | `is_drifted = 1` |
| `pipeline_health_scores` | `health_score` (0-100) | `health_score < 70` |
| `cluster_rightsizing_recommendations` | `recommended_action`, `potential_savings` | Any recommendation |
| `query_optimization_recommendations` | `optimization_flags` | Any flag = 1 |

### When to Use ML Models vs Other Methods

| Question Type | Use ML Model? | Alternative | Example |
|---------------|---------------|-------------|---------|
| **"Will X happen?"** | ✅ Yes | — | "Will this job fail?" → `job_failure_predictions` |
| **"Predict future X"** | ✅ Yes | — | "What's next month's cost?" → `cost_forecast_predictions` |
| **"Is this anomalous?"** | ✅ Yes | Custom Metrics for simple drift | "Unusual spending?" → `cost_anomaly_predictions` |
| **"Recommend action"** | ✅ Yes | TVF for simple lists | "How to optimize?" → `query_optimization_recommendations` |
| **"Score/Risk level"** | ✅ Yes | — | "User risk score?" → `user_risk_scores` |
| **"What is current X?"** | ❌ No | Metric View | "Total cost today?" → `mv_cost_analytics` |
| **"List top N"** | ❌ No | TVF | "Top 10 slow queries?" → `get_slow_queries` |
| **"Is X trending up/down?"** | ❌ No | Custom Metrics | "Is cost increasing?" → `_drift_metrics` |

---

## Appendix: Method Comparison

### When to Use Each Method

| Method | Best For | Example Query |
|--------|----------|---------------|
| **TVF** | Parameterized investigation, actionable lists | "Top 10 cost drivers this week" |
| **Metric View** | Dashboard aggregates, current state KPIs | "What's the success rate?" |
| **Custom Metric** | Time series analysis, drift detection, alerting | "Is success rate degrading?" |
| **ML Model** | Predictions, anomaly detection, recommendations | "Will this job fail?" |

### Method Capabilities

| Capability | TVF | Metric View | Custom Metric | ML Model |
|------------|:---:|:-----------:|:-------------:|:--------:|
| Date range filtering | ✅ | Limited | ❌ | ✅ |
| Top N results | ✅ | ❌ | ❌ | ✅ |
| Custom thresholds | ✅ | ❌ | ❌ | ❌ |
| Dimension grouping | ❌ | ✅ | ❌ | Limited |
| Pre-formatted output | ❌ | ✅ | ❌ | ✅ |
| Time series tracking | ❌ | ❌ | ✅ | ❌ |
| Drift detection | ❌ | ❌ | ✅ | ✅ |
| Automated alerting | ❌ | ❌ | ✅ | ✅ |
| Statistical profiling | ❌ | ❌ | ✅ | ❌ |
| Future predictions | ❌ | ❌ | ❌ | ✅ |
| Anomaly detection | ❌ | ❌ | ❌ | ✅ |
| Recommendations | ❌ | ❌ | ❌ | ✅ |
| Risk scoring | ❌ | ❌ | ❌ | ✅ |

### Asset Count Summary

| Asset Type | Count | Coverage |
|------------|:-----:|----------|
| **TVFs** | 60 | All domains |
| **Metric Views** | 10 | Dashboard KPIs |
| **Custom Metrics** | 87 | Time series + alerting |
| **ML Models** | 25 | Predictions + recommendations |
| **Total Semantic Assets** | 182 | — |
| **Total Measurements** | 277 | Across all methods |

---

**Version:** 1.1  
**Last Updated:** January 2026  
**Total Measurements:** 277  
**ML Models Integrated:** 25

