# Appendix A - Quick Reference

## Complete TVF Reference

### Cost Agent TVFs (15)

| TVF Name | Required Params | Optional Params | Returns |
|----------|-----------------|-----------------|---------|
| `get_top_cost_contributors` | start_date (STRING), end_date (STRING) | top_n (INT, default 10) | workspace, sku, costs, rank |
| `get_cost_trend_by_sku` | start_date (STRING), end_date (STRING) | sku_filter (STRING, default '%') | date, sku, daily_cost, change_pct |
| `get_cost_by_owner` | start_date (STRING), end_date (STRING) | top_n (INT, default 20) | owner, costs, rank |
| `get_cost_by_tag` | start_date (STRING), end_date (STRING) | tag_key (STRING, default 'team') | tag_value, costs, pct |
| `get_untagged_resources` | start_date (STRING), end_date (STRING) | - | workspace, resource, cost |
| `get_cost_anomalies` | days_back (INT) | threshold_pct (DOUBLE, default 50.0) | date, cost, deviation, severity |
| `get_daily_cost_summary` | start_date (STRING), end_date (STRING) | - | date, costs, dod_change, wow_change |
| `get_workspace_cost_comparison` | start_date (STRING), end_date (STRING) | - | workspace, cost, rank, pct |
| `get_serverless_vs_classic_cost` | start_date (STRING), end_date (STRING) | - | compute_type, costs, efficiency |
| `get_job_cost_breakdown` | start_date (STRING), end_date (STRING) | top_n (INT, default 20) | job, cost, runs, avg_cost |
| `get_warehouse_cost_analysis` | start_date (STRING), end_date (STRING) | - | warehouse, cost, queries, efficiency |
| `get_cost_forecast` | days_back (INT) | forecast_days (INT, default 30) | date, projected_cost, bounds |
| `get_cost_by_cluster_type` | start_date (STRING), end_date (STRING) | - | cluster_type, cost, count |
| `get_storage_cost_analysis` | start_date (STRING), end_date (STRING) | - | catalog, schema, cost, size |
| `get_cost_efficiency_metrics` | start_date (STRING), end_date (STRING) | - | metric_name, value, change |

### Reliability Agent TVFs (12)

| TVF Name | Required Params | Optional Params | Returns |
|----------|-----------------|-----------------|---------|
| `get_failed_jobs_summary` | days_back (INT) | min_failures (INT, default 1) | job, failures, success_rate, error |
| `get_job_success_rates` | start_date (STRING), end_date (STRING) | min_runs (INT, default 5) | job, runs, success_rate |
| `get_job_duration_trends` | start_date (STRING), end_date (STRING) | - | date, job, avg_duration, trend |
| `get_job_sla_compliance` | start_date (STRING), end_date (STRING) | - | job, compliance_pct, p95_duration |
| `get_job_failure_patterns` | days_back (INT) | - | error_category, count, trend |
| `get_long_running_jobs` | days_back (INT) | duration_threshold_min (INT, default 60) | job, run, duration, exceeded_by |
| `get_job_retry_analysis` | days_back (INT) | - | job, attempts, retry_effectiveness |
| `get_job_duration_percentiles` | days_back (INT) | - | job, p50, p90, p95, p99 |
| `get_job_failure_cost` | start_date (STRING), end_date (STRING) | - | job, failures, estimated_cost |
| `get_pipeline_health` | days_back (INT) | - | pipeline, success_rate, avg_duration |
| `get_job_schedule_drift` | days_back (INT) | - | job, expected_runs, actual_runs, drift |
| `get_repair_cost_analysis` | start_date (STRING), end_date (STRING) | - | job, repair_count, repair_cost |

### Performance Agent TVFs - Query (10)

| TVF Name | Required Params | Optional Params | Returns |
|----------|-----------------|-----------------|---------|
| `get_slow_queries` | days_back (INT) | duration_threshold_sec (INT, default 30) | query, user, duration, warehouse |
| `get_query_latency_percentiles` | start_date (STRING), end_date (STRING) | - | warehouse, p50, p90, p95, p99 |
| `get_warehouse_utilization` | start_date (STRING), end_date (STRING) | - | warehouse, queries, concurrency, queue_pct |
| `get_query_volume_trends` | start_date (STRING), end_date (STRING) | - | date, count, users, avg_duration |
| `get_top_users_by_query_count` | start_date (STRING), end_date (STRING) | top_n (INT, default 20) | user, queries, duration, rank |
| `get_query_error_analysis` | days_back (INT) | - | error_category, count, users |
| `get_spill_analysis` | days_back (INT) | - | query, user, spill_bytes, duration |
| `get_query_queue_analysis` | start_date (STRING), end_date (STRING) | - | warehouse, queued_count, avg_queue_time |
| `get_warehouse_scaling_events` | days_back (INT) | - | warehouse, scale_up, scale_down, avg_clusters |
| `get_query_cost_by_user` | start_date (STRING), end_date (STRING) | top_n (INT, default 20) | user, queries, estimated_cost |

### Performance Agent TVFs - Compute (6)

| TVF Name | Required Params | Optional Params | Returns |
|----------|-----------------|-----------------|---------|
| `get_cluster_utilization` | start_date (STRING), end_date (STRING) | - | cluster, cpu_pct, memory_pct, runtime |
| `get_underutilized_clusters` | days_back (INT) | - | cluster, avg_cpu, cost, potential_savings |
| `get_cluster_cost_efficiency` | start_date (STRING), end_date (STRING) | - | cluster, cost, jobs, cost_per_job |
| `get_cluster_rightsizing` | days_back (INT) | - | cluster, current_config, recommended, savings |
| `get_jobs_without_autoscaling` | days_back (INT) | - | job, runs, cost, autoscaling_potential |
| `get_jobs_on_legacy_dbr` | days_back (INT) | - | job, dbr_version, runs, recommendation |

### Security Agent TVFs (10)

| TVF Name | Required Params | Optional Params | Returns |
|----------|-----------------|-----------------|---------|
| `get_user_activity_summary` | start_date (STRING), end_date (STRING) | top_n (INT, default 50) | user, events, actions, level |
| `get_table_access_audit` | start_date (STRING), end_date (STRING) | - | table, access_count, users, reads, writes |
| `get_permission_changes` | days_back (INT) | - | timestamp, action, changed_by, target |
| `get_service_account_activity` | days_back (INT) | - | service_principal, events, actions |
| `get_failed_access_attempts` | days_back (INT) | - | user, failures, resources, risk_level |
| `get_sensitive_data_access` | start_date (STRING), end_date (STRING) | - | table, sensitivity, access_count, users |
| `get_unusual_access_patterns` | days_back (INT) | - | user, anomaly_type, deviation, risk_score |
| `get_user_activity_patterns` | days_back (INT) | - | user, events, peak_hour, after_hours |
| `get_data_export_events` | days_back (INT) | - | timestamp, user, table, rows, size |
| `get_user_risk_scores` | days_back (INT) | - | user, risk_score, level, top_factor |

### Quality Agent TVFs (7)

| TVF Name | Required Params | Optional Params | Returns |
|----------|-----------------|-----------------|---------|
| `get_table_freshness` | days_back (INT) | - | table, last_modified, hours_stale, status |
| `get_stale_tables` | days_back (INT) | staleness_threshold_days (INT, default 7) | table, last_modified, days_stale, alert_level |
| `get_data_lineage_summary` | catalog_filter (STRING) | schema_filter (STRING, default '%') | table, upstream_count, downstream_count |
| `get_orphan_tables` | days_back (INT) | - | table, last_accessed, days_since, cost |
| `get_table_ownership_report` | catalog_filter (STRING) | - | table, owner, has_description, completeness |
| `get_data_freshness_by_domain` | days_back (INT) | - | schema, total_tables, fresh, stale, score |
| `get_governance_compliance` | catalog_filter (STRING) | - | table, owner_tag, domain_tag, compliance_score |

---

## Parameter Types

| Type | Format | Example |
|------|--------|---------|
| STRING (date) | YYYY-MM-DD | '2024-12-31' |
| INT | Whole number | 30 |
| DOUBLE | Decimal number | 50.0 |

---

## Invocation Syntax

```sql
-- Basic syntax
SELECT * FROM TABLE(function_name(param1, param2));

-- With explicit parameter names
SELECT * FROM TABLE(function_name(
    start_date => '2024-12-01',
    end_date => '2024-12-31',
    top_n => 10
));

-- Filter results
SELECT * FROM TABLE(function_name(...))
WHERE column_name = 'value';

-- Order results
SELECT * FROM TABLE(function_name(...))
ORDER BY column_name DESC;

-- Limit results (external to TVF)
SELECT * FROM TABLE(function_name(...))
LIMIT 100;
```

