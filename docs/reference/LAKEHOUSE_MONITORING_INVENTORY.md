# Lakehouse Monitoring Inventory

## Overview

This document provides a comprehensive inventory of all Lakehouse Monitors implemented for the Databricks Health Monitor project. Monitors are organized by Agent Domain to align with the project's five-agent architecture.

## Monitor Summary by Agent Domain

| Agent Domain | Monitor Name | Gold Table | Key Metrics | Refresh |
|---|---|---|---|---|
| 💰 Cost | Cost Monitor | `fact_usage` | Total cost, DBU usage, tag coverage | Daily |
| 🏎 Performance | Query Monitor | `fact_query_history` | Query duration (P50/P95/P99), SLA breach rate | Hourly |
| 🏎 Performance | Cluster Monitor | `fact_node_timeline` | CPU/Memory utilization, right-sizing | Hourly |
| 🛡 Reliability | Job Monitor | `fact_job_run_timeline` | Success rate, P99 duration, failure patterns | Hourly |
| 🔐 Security | Security Monitor | `fact_audit_logs` | Event counts, user types, off-hours activity | Hourly |
| ✅ Quality | Quality Monitor | `fact_information_schema_table_storage` | Table size, row counts, growth rates | Daily |
| 📊 Governance | Governance Monitor | `fact_table_lineage` | Active tables, read/write events, consumers | Daily |
| 🤖 ML | Inference Monitor | `cost_anomaly_predictions` | MAE, MAPE, anomaly rate, drift | Daily |

---

## 💰 Cost Domain Monitors

### Cost Monitor (`cost_monitor.py`)

**Table:** `fact_usage`
**Mode:** Time Series
**Granularity:** 1 day
**Slicing:** `workspace_name`, `sku_name`, `is_serverless`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `total_cost` | AGGREGATE | `SUM(list_cost)` | Total spend in period |
| `total_dbus` | AGGREGATE | `SUM(usage_quantity)` | Total DBU consumption |
| `serverless_cost` | AGGREGATE | `SUM(CASE WHEN is_serverless THEN list_cost ELSE 0 END)` | Serverless workload cost |
| `tagged_cost` | AGGREGATE | `SUM(CASE WHEN has_tag THEN list_cost ELSE 0 END)` | Tagged resource cost |
| `distinct_workspaces` | AGGREGATE | `COUNT(DISTINCT workspace_id)` | Workspace count |
| `distinct_skus` | AGGREGATE | `COUNT(DISTINCT sku_name)` | SKU diversity |
| `jobs_on_all_purpose_cost` | AGGREGATE | Jobs running on ALL_PURPOSE clusters | Misallocated compute cost |
| `potential_job_cluster_savings` | AGGREGATE | Savings from job cluster migration | Cost optimization opportunity |
| `cost_per_dbu` | DERIVED | `total_cost / total_dbus` | Unit cost |
| `serverless_percentage` | DERIVED | `serverless_cost * 100 / total_cost` | Serverless adoption |
| `tag_coverage_percentage` | DERIVED | `tagged_cost * 100 / total_cost` | Tagging completeness |
| `cost_trend` | DRIFT | Current vs baseline cost difference | Cost anomaly detection |
| `serverless_adoption_drift` | DRIFT | Serverless percentage change | Migration tracking |

---

## 🏎 Performance Domain Monitors

### Query Monitor (`query_monitor.py`)

**Table:** `fact_query_history`
**Mode:** Time Series
**Granularity:** 1 hour
**Slicing:** `warehouse_id`, `user_name`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `total_queries` | AGGREGATE | `COUNT(*)` | Query volume |
| `p50_duration_seconds` | AGGREGATE | `PERCENTILE(duration_ms/1000, 0.5)` | Median duration |
| `p95_duration_seconds` | AGGREGATE | `PERCENTILE(duration_ms/1000, 0.95)` | Tail latency |
| `p99_duration_seconds` | AGGREGATE | `PERCENTILE(duration_ms/1000, 0.99)` | Extreme outliers |
| `avg_queue_time_seconds` | AGGREGATE | `AVG(queue_duration_ms/1000)` | Queue wait time |
| `slow_query_count` | AGGREGATE | Queries > 30 seconds | Performance issues |
| `sla_breach_count` | AGGREGATE | Queries exceeding SLA threshold | SLA tracking |
| `complex_query_count` | AGGREGATE | Queries with high computation | Complexity tracking |
| `qps` | DERIVED | Queries per second | Throughput |
| `sla_breach_rate` | DERIVED | `sla_breach_count * 100 / total_queries` | SLA compliance |
| `query_efficiency` | DERIVED | Simple queries / total queries | Efficiency metric |
| `duration_drift` | DRIFT | P95 duration change | Performance regression |
| `qps_drift` | DRIFT | QPS change | Volume trend |

### Cluster Monitor (`cluster_monitor.py`)

**Table:** `fact_node_timeline`
**Mode:** Time Series
**Granularity:** 1 hour
**Slicing:** `cluster_id`, `instance_type`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `avg_cpu_utilization` | AGGREGATE | `AVG(cpu_total_pct)` | CPU usage |
| `avg_memory_utilization` | AGGREGATE | `AVG(memory_used_pct)` | Memory usage |
| `p95_cpu_total_pct` | AGGREGATE | `PERCENTILE(cpu_total_pct, 0.95)` | Peak CPU |
| `total_node_hours` | AGGREGATE | Node uptime in hours | Capacity tracking |
| `cpu_saturation_hours` | AGGREGATE | Hours with CPU > 90% | Bottleneck detection |
| `cpu_idle_hours` | AGGREGATE | Hours with CPU < 10% | Over-provisioning |
| `underprovisioned_hours` | AGGREGATE | Hours needing more resources | Scaling needs |
| `right_sizing_opportunity` | DERIVED | Idle / total hours | Optimization potential |
| `saturation_rate` | DERIVED | Saturation / total hours | Capacity risk |
| `cpu_drift` | DRIFT | CPU utilization change | Workload shift |
| `memory_drift` | DRIFT | Memory utilization change | Resource trend |

---

## 🛡 Reliability Domain Monitors

### Job Monitor (`job_monitor.py`)

**Table:** `fact_job_run_timeline`
**Mode:** Time Series
**Granularity:** 1 hour
**Slicing:** `workspace_id`, `job_name`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `total_runs` | AGGREGATE | `COUNT(*)` | Job volume |
| `successful_runs` | AGGREGATE | Runs with SUCCESS state | Success count |
| `failed_runs` | AGGREGATE | Runs with FAILED state | Failure count |
| `avg_duration_minutes` | AGGREGATE | `AVG(duration_seconds/60)` | Average runtime |
| `p90_duration_minutes` | AGGREGATE | `PERCENTILE(duration_seconds/60, 0.9)` | Outlier detection |
| `p99_duration_minutes` | AGGREGATE | `PERCENTILE(duration_seconds/60, 0.99)` | Extreme outliers |
| `long_running_count` | AGGREGATE | Jobs > 60 minutes | Long job tracking |
| `skipped_run_count` | AGGREGATE | Skipped executions | Skip tracking |
| `upstream_failed_count` | AGGREGATE | Upstream dependency failures | Dependency issues |
| `success_rate` | DERIVED | `successful_runs * 100 / total_runs` | Reliability KPI |
| `failure_rate` | DERIVED | `failed_runs * 100 / total_runs` | Failure tracking |
| `duration_cv` | DERIVED | Duration coefficient of variation | Stability metric |
| `success_rate_drift` | DRIFT | Success rate change | Reliability trend |
| `duration_drift` | DRIFT | P90 duration change | Performance trend |

---

## 🔐 Security Domain Monitors

### Security Monitor (`security_monitor.py`)

**Table:** `fact_audit_logs`
**Mode:** Time Series
**Granularity:** 1 hour
**Slicing:** `workspace_id`, `service_name`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `total_events` | AGGREGATE | `COUNT(*)` | Event volume |
| `distinct_users` | AGGREGATE | `COUNT(DISTINCT user_identity)` | Active users |
| `sensitive_action_count` | AGGREGATE | High-risk action events | Risk tracking |
| `failed_action_count` | AGGREGATE | Failed operations | Security issues |
| `permission_change_count` | AGGREGATE | Permission modifications | Access control |
| `human_user_events` | AGGREGATE | Non-service account events | Human activity |
| `service_principal_events` | AGGREGATE | Service principal events | Automation activity |
| `system_account_events` | AGGREGATE | System account events | System activity |
| `human_off_hours_events` | AGGREGATE | Human events outside business hours | Suspicious timing |
| `sensitive_rate` | DERIVED | `sensitive_action_count * 100 / total_events` | Risk ratio |
| `failure_rate` | DERIVED | `failed_action_count * 100 / total_events` | Issue rate |
| `off_hours_rate` | DERIVED | `human_off_hours_events * 100 / human_user_events` | Suspicious timing |
| `event_volume_drift` | DRIFT | Event count change | Volume anomaly |
| `sensitive_action_drift` | DRIFT | Sensitive action change | Risk trend |

---

## ✅ Quality Domain Monitors

### Quality Monitor (`quality_monitor.py`)

**Table:** `fact_information_schema_table_storage`
**Mode:** Time Series
**Granularity:** 1 day
**Slicing:** `catalog_name`, `schema_name`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `total_tables` | AGGREGATE | `COUNT(DISTINCT table_name)` | Table inventory |
| `total_size_gb` | AGGREGATE | `SUM(storage_size_bytes) / 1e9` | Storage consumption |
| `total_rows` | AGGREGATE | `SUM(row_count)` | Row inventory |
| `large_tables` | AGGREGATE | Tables > 100GB | Large table tracking |
| `empty_tables` | AGGREGATE | Tables with 0 rows | Empty table detection |
| `unpartitioned_large_tables` | AGGREGATE | Large tables without partitioning | Optimization opportunity |
| `avg_table_size_gb` | DERIVED | Average table size | Sizing metric |
| `empty_table_rate` | DERIVED | Empty / total tables | Quality issue |
| `size_drift` | DRIFT | Storage growth | Capacity trend |
| `row_count_drift` | DRIFT | Row count change | Data volume trend |

---

## 📊 Governance Domain Monitors

### Governance Monitor (`governance_monitor.py`)

**Table:** `fact_table_lineage`
**Mode:** Time Series
**Granularity:** 1 day
**Slicing:** `source_catalog`, `target_catalog`

#### Custom Metrics

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `total_lineage_events` | AGGREGATE | `COUNT(*)` | Lineage volume |
| `active_tables` | AGGREGATE | Distinct tables with activity | Active inventory |
| `distinct_source_tables` | AGGREGATE | Unique source tables | Data origins |
| `distinct_target_tables` | AGGREGATE | Unique target tables | Data destinations |
| `read_events` | AGGREGATE | Read operations | Read patterns |
| `write_events` | AGGREGATE | Write operations | Write patterns |
| `unique_data_consumers` | AGGREGATE | Distinct consuming users/jobs | Consumer tracking |
| `cross_catalog_events` | AGGREGATE | Events crossing catalogs | Catalog boundary activity |
| `data_sharing_rate` | DERIVED | Cross-catalog / total events | Sharing metric |
| `read_write_ratio` | DERIVED | Read / write events | Access pattern |
| `activity_drift` | DRIFT | Event volume change | Activity trend |
| `consumer_drift` | DRIFT | Consumer count change | Adoption trend |

---

## 🤖 ML Domain Monitors

### Inference Monitor (`inference_monitor.py`)

**Table:** `cost_anomaly_predictions`
**Mode:** Time Series
**Granularity:** 1 day
**Slicing:** `workspace_id`

#### Custom Metrics - Cost Anomaly Model

| Metric Name | Type | Definition | Purpose |
|---|---|---|---|
| `prediction_count` | AGGREGATE | `COUNT(*)` | Prediction volume |
| `mean_absolute_error` | AGGREGATE | `AVG(ABS(daily_cost - expected_cost))` | Accuracy |
| `anomaly_count` | AGGREGATE | Detected anomalies | Anomaly volume |
| `high_confidence_anomaly_count` | AGGREGATE | Anomalies with score > 0.9 | High-confidence detection |
| `avg_anomaly_score` | AGGREGATE | Mean anomaly score | Score distribution |
| `predictions_within_10pct` | AGGREGATE | Accurate predictions | Accuracy tracking |
| `mean_absolute_percentage_error` | DERIVED | MAPE calculation | Relative accuracy |
| `anomaly_rate` | DERIVED | `anomaly_count / prediction_count` | Anomaly ratio |
| `prediction_accuracy_10pct` | DERIVED | Accurate prediction rate | Model quality |
| `mae_drift` | DRIFT | MAE change | Model degradation |
| `accuracy_drift` | DRIFT | Accuracy change | Model drift |

---

## Deployment

### Job Configuration

**File:** `resources/monitoring/lakehouse_monitors_job.yml`

```yaml
resources:
  jobs:
    lakehouse_monitoring_setup_job:
      name: "[${bundle.target}] Health Monitor - Lakehouse Monitoring Setup"
      tasks:
        - task_key: create_cost_monitor
        - task_key: create_job_monitor
        - task_key: create_query_monitor
        - task_key: create_cluster_monitor
        - task_key: create_security_monitor
        - task_key: create_quality_monitor
        - task_key: create_governance_monitor
        - task_key: create_inference_monitor
```

### Deployment Commands

```bash
# Deploy monitoring setup job
databricks bundle deploy -t dev

# Run monitoring setup
databricks bundle run lakehouse_monitoring_setup_job -t dev

# Or run all monitors via orchestration script
databricks bundle run -t dev --notebook-path src/monitoring/setup_all_monitors.py
```

---

## Monitor Output Tables

Each monitor creates two output tables in the `{gold_schema}_monitoring` schema:

| Monitor | Profile Metrics Table | Drift Metrics Table |
|---|---|---|
| Cost | `fact_usage_profile_metrics` | `fact_usage_drift_metrics` |
| Query | `fact_query_history_profile_metrics` | `fact_query_history_drift_metrics` |
| Cluster | `fact_node_timeline_profile_metrics` | `fact_node_timeline_drift_metrics` |
| Job | `fact_job_run_timeline_profile_metrics` | `fact_job_run_timeline_drift_metrics` |
| Security | `fact_audit_logs_profile_metrics` | `fact_audit_logs_drift_metrics` |
| Quality | `fact_information_schema_..._profile_metrics` | `fact_information_schema_..._drift_metrics` |
| Governance | `fact_table_lineage_profile_metrics` | `fact_table_lineage_drift_metrics` |
| Inference | `cost_anomaly_predictions_profile_metrics` | `cost_anomaly_predictions_drift_metrics` |

---

## Querying Custom Metrics

### Profile Metrics (AGGREGATE + DERIVED)

```sql
-- Query custom metrics from profile table
SELECT
  window_start,
  column_name,
  total_cost,
  serverless_percentage,
  tag_coverage_percentage
FROM {catalog}.{gold_schema}_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'  -- Table-level metrics
  AND window_start >= CURRENT_DATE - 30
ORDER BY window_start DESC
```

### Drift Metrics

```sql
-- Query drift metrics
SELECT
  window_start,
  drift_type,
  cost_trend,
  serverless_adoption_drift
FROM {catalog}.{gold_schema}_monitoring.fact_usage_drift_metrics
WHERE column_name = ':table'
  AND ABS(cost_trend) > 0.1  -- Significant drift only
ORDER BY window_start DESC
```

---

## References

- [Lakehouse Monitoring Documentation](https://docs.databricks.com/lakehouse-monitoring)
- [Custom Metrics Reference](https://docs.databricks.com/lakehouse-monitoring/custom-metrics)
- [Phase 3 Addendum 3.4](../plans/phase3-addendum-3.4-lakehouse-monitoring.md)
- [Monitoring Cursor Rule](../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

---

## Version History

| Date | Version | Changes |
|---|---|---|
| 2025-12-19 | 1.0.0 | Initial implementation with 8 monitors across 5 agent domains |





