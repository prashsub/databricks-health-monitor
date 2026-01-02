# 04 - Monitor Catalog

## Overview

This document provides a complete inventory of all 8 Lakehouse Monitors, organized by agent domain. Each monitor entry includes:
- Purpose and use cases
- Source table and key columns
- Complete metric inventory
- Configuration details

## Monitor Summary

| Monitor | Gold Table | Domain | Metrics | Granularity | Schedule |
|---------|------------|--------|---------|-------------|----------|
| **Cost** | `fact_usage` | 💰 Cost | 35 | 1 day | Daily 6 AM |
| **Job** | `fact_job_run_timeline` | 🔄 Reliability | 50 | 1 hour, 1 day | Hourly |
| **Query** | `fact_query_history` | ⚡ Performance | 40 | 1 hour, 1 day | Hourly |
| **Cluster** | `fact_node_timeline` | ⚡ Performance | 40 | 1 hour, 1 day | Hourly |
| **Security** | `fact_audit_logs` | 🔒 Security | 15 | 1 hour, 1 day | Hourly |
| **Quality** | `fact_table_quality` | ✅ Quality | 15 | 1 day | Daily |
| **Governance** | `fact_governance_metrics` | 📊 Quality | 15 | 1 day | Daily |
| **Inference** | `fact_model_serving` | 🤖 ML | 15 | 1 hour, 1 day | Hourly |

---

## 💰 Cost Monitor

### Purpose

Tracks billing data quality, cost trends, and tag compliance for FinOps optimization.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_usage` |
| **Timestamp Column** | `usage_date` |
| **Granularities** | `["1 day"]` |
| **Slicing Expressions** | `workspace_id`, `sku_name`, `cloud`, `is_tagged`, `product_features_is_serverless` |
| **Schedule** | Daily at 6 AM UTC |

### Metrics Inventory

#### AGGREGATE Metrics (19)

| Metric | Definition | Type | Business Purpose |
|--------|------------|------|------------------|
| `total_daily_cost` | `SUM(list_cost)` | DOUBLE | Primary FinOps KPI |
| `total_daily_dbu` | `SUM(usage_quantity)` | DOUBLE | Usage volume independent of pricing |
| `avg_cost_per_dbu` | `AVG(list_price)` | DOUBLE | Unit economics indicator |
| `record_count` | `COUNT(*)` | LONG | Data completeness indicator |
| `distinct_workspaces` | `COUNT(DISTINCT workspace_id)` | LONG | Platform utilization breadth |
| `distinct_skus` | `COUNT(DISTINCT sku_name)` | LONG | Product mix indicator |
| `null_sku_count` | `SUM(CASE WHEN sku_name IS NULL ...)` | LONG | Data quality issue |
| `null_price_count` | `SUM(CASE WHEN list_price IS NULL ...)` | LONG | Billing completeness |
| `tagged_record_count` | `SUM(CASE WHEN is_tagged = TRUE ...)` | LONG | Tag hygiene |
| `untagged_record_count` | `SUM(CASE WHEN is_tagged = FALSE ...)` | LONG | Cost attribution gap |
| `tagged_cost_total` | `SUM(CASE WHEN is_tagged = TRUE THEN list_cost ...)` | DOUBLE | Attributable spend |
| `untagged_cost_total` | `SUM(CASE WHEN is_tagged = FALSE THEN list_cost ...)` | DOUBLE | Unattributable spend |
| `jobs_compute_cost` | `SUM(CASE WHEN sku_name LIKE '%JOBS%' ...)` | DOUBLE | Workflow automation spend |
| `sql_compute_cost` | `SUM(CASE WHEN sku_name LIKE '%SQL%' ...)` | DOUBLE | Analytics workload spend |
| `all_purpose_cost` | `SUM(CASE WHEN sku_name LIKE '%ALL_PURPOSE%' ...)` | DOUBLE | Interactive compute spend |
| `serverless_cost` | `SUM(CASE WHEN is_serverless = TRUE ...)` | DOUBLE | Modern compute adoption |
| `jobs_on_all_purpose_cost` | Jobs running on ALL_PURPOSE clusters | DOUBLE | Inefficient pattern (~40% overspend) |
| `jobs_on_all_purpose_count` | Distinct jobs on ALL_PURPOSE | LONG | Optimization candidates |
| `potential_job_cluster_savings` | Estimated 40% savings | DOUBLE | Actionable optimization |
| `dlt_cost` | `SUM(CASE WHEN sku_name LIKE '%DLT%' ...)` | DOUBLE | Pipeline infrastructure |
| `model_serving_cost` | Model serving + inference | DOUBLE | ML serving spend |

#### DERIVED Metrics (13)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `null_sku_rate` | `null_sku_count * 100.0 / record_count` | Data quality score (target: <1%) |
| `null_price_rate` | `null_price_count * 100.0 / record_count` | Billing completeness (target: 0%) |
| `tag_coverage_pct` | `tagged_cost / total_cost * 100` | FinOps maturity KPI (target: >90%) |
| `untagged_usage_pct` | `untagged_cost / total_cost * 100` | Cost attribution gap |
| `serverless_ratio` | `serverless_cost / total_cost * 100` | Modern architecture adoption |
| `jobs_cost_share` | `jobs_cost / total_cost * 100` | Workflow cost proportion |
| `sql_cost_share` | `sql_cost / total_cost * 100` | Analytics cost proportion |
| `all_purpose_cost_ratio` | `all_purpose_cost / total_cost * 100` | Interactive compute overhead |
| `jobs_on_all_purpose_ratio` | Jobs on ALL_PURPOSE / total jobs | Optimization priority score |
| `dlt_cost_share` | `dlt_cost / total_cost * 100` | Pipeline spend proportion |
| `model_serving_cost_share` | `model_serving_cost / total_cost * 100` | ML inference proportion |

#### DRIFT Metrics (3)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `cost_drift_pct` | Period cost change % | Budget variance (alert if >10%) |
| `dbu_drift_pct` | Period DBU change % | Usage trend |
| `tag_coverage_drift` | Coverage change | FinOps maturity trend |

---

## 🔄 Job Monitor (Reliability)

### Purpose

Tracks job execution reliability, success rates, and duration metrics for SLA monitoring.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_job_run_timeline` |
| **Timestamp Column** | `start_time` |
| **Granularities** | `["1 hour", "1 day"]` |
| **Slicing Expressions** | `workspace_id`, `result_state`, `trigger_type`, `job_name`, `termination_code` |
| **Schedule** | Hourly |

### Metrics Inventory

#### AGGREGATE Metrics (26)

| Metric | Definition | Type | Business Purpose |
|--------|------------|------|------------------|
| `total_runs` | `COUNT(*)` | LONG | Workload volume |
| `success_count` | Runs with is_success = TRUE | LONG | Reliability numerator |
| `failure_count` | Runs with FAILED/ERROR state | LONG | Issues requiring investigation |
| `timeout_count` | Runs with TIMED_OUT state | LONG | Resource constraint issues |
| `cancelled_count` | Runs with CANCELED state | LONG | Manual interventions |
| `avg_duration_minutes` | `AVG(run_duration_minutes)` | DOUBLE | Performance baseline |
| `total_duration_minutes` | `SUM(run_duration_minutes)` | DOUBLE | Compute time consumption |
| `max_duration_minutes` | `MAX(run_duration_minutes)` | DOUBLE | Worst-case performance |
| `min_duration_minutes` | `MIN(run_duration_minutes)` | DOUBLE | Best-case performance |
| `p50_duration_minutes` | `PERCENTILE(..., 0.50)` | DOUBLE | Typical performance |
| `p90_duration_minutes` | `PERCENTILE(..., 0.90)` | DOUBLE | Outlier threshold |
| `p95_duration_minutes` | `PERCENTILE(..., 0.95)` | DOUBLE | SLA target threshold |
| `p99_duration_minutes` | `PERCENTILE(..., 0.99)` | DOUBLE | Critical SLA threshold |
| `stddev_duration_minutes` | `STDDEV(run_duration_minutes)` | DOUBLE | Consistency indicator |
| `skipped_count` | SKIPPED state | LONG | Dependency issues |
| `upstream_failed_count` | UPSTREAM_FAILED state | LONG | Dependency chain failures |
| `long_running_count` | Duration > 60 min | LONG | Optimization candidates |
| `very_long_running_count` | Duration > 240 min | LONG | Resource-intensive jobs |
| `distinct_jobs` | `COUNT(DISTINCT job_id)` | LONG | Workload diversity |
| `distinct_runs` | `COUNT(DISTINCT run_id)` | LONG | Execution count |
| `scheduled_runs` | SCHEDULE trigger | LONG | Automated proportion |
| `manual_runs` | MANUAL trigger | LONG | Ad-hoc proportion |
| `retry_runs` | RETRY trigger | LONG | Recovery activity |
| `user_cancelled_count` | USER_CANCELED termination | LONG | Manual intervention frequency |
| `internal_error_count` | INTERNAL_ERROR termination | LONG | Platform stability |
| `driver_error_count` | DRIVER_ERROR termination | LONG | Code/config issues |

#### DERIVED Metrics (15)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `success_rate` | `success_count / total_runs * 100` | Primary reliability KPI (target: >95%) |
| `failure_rate` | `failure_count / total_runs * 100` | Reliability issue indicator |
| `timeout_rate` | `timeout_count / total_runs * 100` | Resource constraint indicator |
| `cancellation_rate` | `cancelled_count / total_runs * 100` | Intervention frequency |
| `repair_rate` | `retry_runs / distinct_runs * 100` | Recovery activity level |
| `scheduled_ratio` | `scheduled_runs / total_runs * 100` | Automation maturity |
| `avg_runs_per_job` | `total_runs / distinct_jobs` | Execution frequency |
| `duration_cv` | `stddev / avg duration` | Consistency score (lower is better) |
| `skipped_rate` | `skipped_count / total_runs * 100` | Dependency issue frequency |
| `upstream_failed_rate` | `upstream_failed / total_runs * 100` | Dependency chain health |
| `long_running_rate` | `long_running / total_runs * 100` | Optimization opportunity |
| `very_long_running_rate` | `very_long_running / total_runs * 100` | Resource-intensive proportion |
| `duration_skew_ratio` | `p90 / p50 duration` | Distribution skewness (1=perfect) |
| `tail_ratio` | `p99 / p95 duration` | Tail latency indicator |

#### DRIFT Metrics (9)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `success_rate_drift` | Current - baseline success_rate | Reliability trend (negative = degrading) |
| `failure_count_drift` | Current - baseline failure_count | Problem emergence |
| `run_count_drift_pct` | Volume change % | Workload trend |
| `duration_drift_pct` | Avg duration change % | Performance regression |
| `p99_duration_drift_pct` | P99 change % | SLA compliance trend |
| `p90_duration_drift_pct` | P90 change % | Outlier trend |
| `duration_cv_drift` | CV change | Consistency trend |
| `long_running_drift` | Long running count change | Performance degradation |

---

## ⚡ Query Monitor (Performance)

### Purpose

Tracks query latency, efficiency, and warehouse utilization for SQL performance optimization.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_query_history` |
| **Timestamp Column** | `start_time` |
| **Granularities** | `["1 hour", "1 day"]` |
| **Slicing Expressions** | `workspace_id`, `compute_warehouse_id`, `execution_status`, `statement_type`, `executed_by` |
| **Schedule** | Hourly |

### Metrics Inventory

#### AGGREGATE Metrics (26)

| Metric | Definition | Type | Business Purpose |
|--------|------------|------|------------------|
| `query_count` | `COUNT(*)` | LONG | Query workload volume |
| `successful_queries` | FINISHED status | LONG | Reliability numerator |
| `failed_queries` | FAILED status | LONG | Reliability issues |
| `cancelled_queries` | CANCELED status | LONG | User intervention |
| `avg_duration_sec` | `AVG(total_duration_ms / 1000)` | DOUBLE | Performance baseline |
| `total_duration_sec` | `SUM(total_duration_ms / 1000)` | DOUBLE | Total query time |
| `p50_duration_sec` | Median duration | DOUBLE | Typical performance |
| `p95_duration_sec` | P95 duration | DOUBLE | SLA threshold |
| `p99_duration_sec` | P99 duration | DOUBLE | Worst-case |
| `max_duration_sec` | Max duration | DOUBLE | Extreme outlier |
| `avg_queue_time_sec` | Queue time average | DOUBLE | Capacity indicator |
| `total_queue_time_sec` | Total queue time | DOUBLE | Cumulative wait |
| `high_queue_count` | Queue > 10% of duration | LONG | Capacity issues |
| `slow_query_count` | Duration > 5 min | LONG | Optimization candidates |
| `very_slow_query_count` | Duration > 15 min | LONG | Critical slow queries |
| `sla_breach_count` | Duration > 60 sec | LONG | SLA breach tracking |
| `efficient_query_count` | No spill, low queue, <60s | LONG | Query efficiency |
| `high_queue_severe_count` | Queue > 30% of duration | LONG | Severe capacity issues |
| `complex_query_count` | Query text > 5000 chars | LONG | Query complexity |
| `total_bytes_read_tb` | Total TB read | DOUBLE | IO efficiency |
| `total_rows_read_b` | Total billions rows | DOUBLE | Data access volume |
| `avg_bytes_per_query` | Avg bytes per query | DOUBLE | Query scope |
| `queries_with_spill` | Queries with disk spill | LONG | Memory pressure |
| `total_spilled_bytes` | Total spilled bytes | DOUBLE | Spill volume |
| `cache_hit_count` | Result cache hits | LONG | Cache efficiency |
| `avg_compilation_sec` | Compilation time | DOUBLE | Parse efficiency |
| `distinct_users` | Unique users | LONG | User base size |
| `distinct_warehouses` | Unique warehouses | LONG | Warehouse usage |

#### DERIVED Metrics (13)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `query_success_rate` | `successful / total * 100` | Query reliability KPI |
| `query_failure_rate` | `failed / total * 100` | Query reliability issues |
| `high_queue_rate` | `high_queue / total * 100` | Capacity issues rate |
| `slow_query_rate` | `slow / total * 100` | Slow query proportion |
| `spill_rate` | `queries_with_spill / total * 100` | Memory pressure rate |
| `cache_hit_rate` | `cache_hit / total * 100` | Cache efficiency |
| `avg_queries_per_user` | `total / distinct_users` | User activity level |
| `sla_breach_rate` | `sla_breach / total * 100` | SLA compliance |
| `efficiency_rate` | `efficient / total * 100` | Query efficiency KPI |
| `severe_queue_rate` | `severe_queue / total * 100` | Severe capacity rate |
| `complex_query_rate` | `complex / total * 100` | Complexity proportion |

#### DRIFT Metrics (7)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `p95_duration_drift_pct` | P95 change % | Performance trend |
| `query_volume_drift_pct` | Volume change % | Usage trend |
| `failure_rate_drift` | Failure rate change | Reliability trend |
| `spill_rate_drift` | Spill rate change | Memory pressure trend |
| `sla_breach_rate_drift` | SLA breach change | Compliance trend |
| `efficiency_rate_drift` | Efficiency change | Optimization trend |
| `p99_duration_drift_pct` | P99 change % | Worst-case trend |

---

## ⚡ Cluster Monitor (Performance)

### Purpose

Tracks CPU, memory, and network utilization for right-sizing recommendations.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_node_timeline` |
| **Timestamp Column** | `start_time` |
| **Granularities** | `["1 hour", "1 day"]` |
| **Slicing Expressions** | `workspace_id`, `cluster_id`, `node_type`, `cluster_name`, `driver` |
| **Schedule** | Hourly |

### Key Metrics

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Node Counts** | `node_hour_count`, `distinct_nodes`, `distinct_clusters`, `driver_node_count`, `worker_node_count` | Infrastructure scale |
| **CPU** | `avg_cpu_user_pct`, `avg_cpu_system_pct`, `avg_cpu_wait_pct`, `max_cpu_*`, `p95_cpu_total_pct` | CPU utilization |
| **Memory** | `avg_memory_pct`, `max_memory_pct`, `avg_swap_pct`, `p95_memory_pct` | Memory utilization |
| **Network** | `total_network_sent_gb`, `total_network_received_gb`, `avg_network_*` | Network throughput |
| **Right-Sizing** | `underutilized_hours`, `overutilized_hours`, `optimal_util_hours`, `cpu_saturation_hours`, `cpu_idle_hours` | Optimization signals |
| **Derived** | `underutilization_rate`, `overutilization_rate`, `efficiency_score`, `rightsizing_opportunity_pct` | Actionable KPIs |
| **Drift** | `cpu_utilization_drift`, `memory_utilization_drift`, `efficiency_score_drift` | Trend detection |

---

## 🔒 Security Monitor

### Purpose

Tracks authentication events, sensitive actions, and access patterns for security monitoring.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_audit_logs` |
| **Timestamp Column** | `event_time` |
| **Granularities** | `["1 hour", "1 day"]` |
| **Slicing Expressions** | `workspace_id`, `service_name`, `audit_level`, `action_name`, `user_identity_email` |
| **Schedule** | Hourly |

### Key Metrics

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Volume** | `total_events`, `distinct_users` | Activity scale |
| **Authentication** | `failed_auth_count`, `failed_auth_rate` | Security incidents |
| **Actions** | `sensitive_actions`, `admin_actions`, `data_access_events` | Privileged activity |
| **Derived** | `admin_action_rate`, `events_per_user` | Activity patterns |
| **Drift** | `auth_failure_drift` | Security posture trend |

---

## ✅ Quality Monitor

### Purpose

Tracks data quality scores, violations, and freshness across monitored tables.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_table_quality` |
| **Timestamp Column** | `check_time` |
| **Granularities** | `["1 day"]` |
| **Slicing Expressions** | `catalog_name`, `schema_name`, `table_name`, `has_critical_violations` |
| **Schedule** | Daily |

### Key Metrics

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Coverage** | `total_tables`, `tables_with_issues` | Quality scope |
| **Scores** | `avg_quality_score`, `quality_score_below_threshold` | Quality KPIs |
| **Violations** | `null_violation_count`, `schema_drift_count`, `freshness_violations` | Issue types |
| **Derived** | `quality_issue_rate`, `avg_freshness_hours` | Quality ratios |
| **Drift** | `quality_drift` | Quality trend |

---

## 📊 Governance Monitor

### Purpose

Tracks documentation, tagging, and lineage coverage for governance maturity.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_governance_metrics` |
| **Timestamp Column** | `metric_date` |
| **Granularities** | `["1 day"]` |
| **Slicing Expressions** | `workspace_id`, `entity_type`, `created_by`, `source_catalog_name` |
| **Schedule** | Daily |

### Key Metrics

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Coverage** | `total_assets`, `documented_assets`, `tagged_assets`, `access_controlled_assets`, `lineage_tracked_assets` | Governance coverage |
| **Rates** | `documentation_rate`, `tagging_rate`, `access_control_rate`, `lineage_coverage_rate` | Coverage percentages |
| **Score** | `governance_score` | Composite maturity KPI (0-100) |
| **Drift** | `governance_drift` | Maturity trend |

---

## 🤖 Inference Monitor

### Purpose

Tracks ML model serving latency, error rates, and throughput.

### Configuration

| Property | Value |
|----------|-------|
| **Source Table** | `{catalog}.{gold_schema}.fact_cost_anomaly_predictions` / `fact_job_failure_predictions` |
| **Timestamp Column** | `prediction_date` |
| **Granularities** | `["1 day"]` |
| **Slicing Expressions** | `workspace_id`, `is_anomaly`, `anomaly_category` / `predicted_result`, `risk_level` |
| **Schedule** | Daily at 8 AM UTC |

### Key Metrics

| Category | Metrics | Purpose |
|----------|---------|---------|
| **Volume** | `total_requests`, `successful_requests`, `failed_requests` | Request scale |
| **Latency** | `avg_latency_ms`, `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms` | Performance SLAs |
| **Tokens** | `total_tokens`, `avg_tokens_per_request` | LLM usage (if applicable) |
| **Derived** | `request_success_rate`, `error_rate`, `throughput_per_second` | Performance KPIs |
| **Drift** | `latency_drift_pct`, `error_rate_drift` | Performance trends |

---

## References

- [Lakehouse Monitoring Documentation](https://docs.databricks.com/lakehouse-monitoring)
- [Custom Metrics Reference](https://docs.databricks.com/lakehouse-monitoring/custom-metrics.html)
- [Monitor Notebooks](../../src/monitoring/)

---

**Version:** 1.0  
**Last Updated:** January 2026

