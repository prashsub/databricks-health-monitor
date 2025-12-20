# Metric Views Inventory

> **Total: 10 Metric Views** organized by 5 Agent Domains

This document catalogs all Unity Catalog Metric Views for the Databricks Health Monitor project.

## Summary by Agent Domain

| Agent Domain | Metric Views | Source Tables |
|--------------|-------------|---------------|
| 💰 **Cost** | 2 | fact_usage, fact_commit_usage |
| ⚡ **Performance** | 3 | fact_query_history, fact_node_timeline |
| 🔄 **Reliability** | 1 | fact_job_run_timeline |
| 🔒 **Security** | 2 | fact_audit_logs, fact_table_lineage |
| ✅ **Quality** | 2 | fact_data_classification, fact_model_inference |

---

## 💰 Cost Domain (2 Metric Views)

### 1. `cost_analytics`

**Purpose:** Comprehensive cost analytics metrics for Databricks billing and usage analysis.

**Source Table:** `fact_usage` (billing domain)

**Key Business Questions:**
- What is our total spend this month?
- Show cost by workspace
- Which SKU costs the most?
- Daily cost trend for last 30 days
- What percentage of our spend is tagged?
- Show cost by team/project tag

**Dimensions (20):**
- usage_date, year, month, quarter, week_of_year
- workspace_id, workspace_name, sku_name, sku_category
- pricing_model, billing_type, cloud_provider
- owner, usage_unit
- tag_team, tag_project, tag_environment, tag_cost_center
- has_tags, is_serverless

**Measures (18):**
- total_cost, total_dbus, usage_quantity
- avg_daily_cost, max_daily_cost, min_daily_cost
- cost_7d, cost_30d, cost_mtd
- total_list_cost, total_discount, discount_percentage
- tagged_cost, untagged_cost, tag_coverage_percentage
- serverless_cost, non_serverless_cost, serverless_percentage

---

### 2. `commit_tracking`

**Purpose:** Databricks commit/contract tracking for financial planning.

**Source Table:** `fact_commit_usage` (billing domain)

**Key Business Questions:**
- What is our commit utilization?
- Are we on track to meet our commit?
- Show commit burn rate
- Projected commit end date
- Monthly commit vs actual usage

**Dimensions (10):**
- usage_date, year, month, quarter
- workspace_id, workspace_name
- commitment_period, commit_type, commit_status
- is_over_committed

**Measures (12):**
- commit_amount, consumed_amount, remaining_amount
- commit_utilization_pct, burn_rate_daily
- projected_end_date, days_remaining
- overage_amount, overage_percentage
- monthly_avg_consumption, monthly_projected

---

## ⚡ Performance Domain (3 Metric Views)

### 3. `query_performance`

**Purpose:** SQL Warehouse query performance and efficiency metrics for optimization.

**Source Table:** `fact_query_history` (query_performance domain)

**Key Business Questions:**
- Average query duration
- Slowest queries today
- Warehouse query count
- Query efficiency by user
- P95/P99 latency metrics
- Queries with high spill

**Dimensions (18):**
- execution_date, year, month, quarter, week_of_year
- warehouse_id, warehouse_name
- user_name, statement_type, execution_status
- query_complexity_tier, efficiency_tier, spill_tier
- is_cached, is_incremental
- hour_of_day, day_of_week

**Measures (25):**
- total_queries, successful_queries, failed_queries
- success_rate, error_rate
- avg_duration_ms, median_duration_ms, p95_duration_ms, p99_duration_ms
- max_duration_ms, min_duration_ms
- total_duration_ms, avg_rows_produced, total_rows_produced
- avg_bytes_read, total_bytes_read_gb
- avg_bytes_spilled, total_bytes_spilled_gb
- cache_hit_rate, queries_with_spill
- queries_per_minute, queries_per_hour
- unique_users, unique_warehouses

---

### 4. `cluster_utilization`

**Purpose:** Cluster resource utilization metrics for capacity planning and optimization.

**Source Table:** `fact_node_timeline` (compute domain)

**Key Business Questions:**
- Cluster CPU utilization
- Underutilized clusters
- Memory usage by cluster
- Most expensive clusters
- Which clusters are overprovisioned?
- Show potential cost savings

**Dimensions (15):**
- date, year, month, quarter, week_of_year
- cluster_id, cluster_name, cluster_type
- workspace_id, workspace_name
- node_type, is_driver, node_role, state
- utilization_tier

**Measures (18):**
- avg_cpu_utilization, avg_memory_utilization
- max_cpu_utilization, max_memory_utilization
- total_node_hours, running_hours, idle_hours
- total_nodes, unique_clusters, driver_nodes, worker_nodes
- efficiency_score, idle_percentage
- underutilized_node_count, overprovisioned_node_count
- avg_network_mbps, avg_disk_mbps

---

### 5. `cluster_efficiency`

**Purpose:** Advanced cluster efficiency and optimization analytics for cost reduction.

**Source Table:** `fact_node_timeline` (compute domain)

**Key Business Questions:**
- Which clusters have ALL_PURPOSE workloads on interactive clusters?
- Show clusters that could be migrated to jobs clusters
- What's the right-sizing opportunity?
- Which clusters are overprovisioned?
- Show node utilization efficiency by cluster type
- What would we save with serverless?

**Dimensions (18):**
- date, year, month, week_of_year
- cluster_id, cluster_name, cluster_type
- workspace_id, workspace_name
- node_type, is_driver, node_role, state
- cpu_utilization_tier, memory_utilization_tier
- is_underutilized, is_overprovisioned

**Measures (25):**
- avg_cpu_utilization, avg_memory_utilization
- max_cpu_utilization, max_memory_utilization
- total_node_hours, running_hours, idle_hours
- total_nodes, unique_clusters, driver_nodes, worker_nodes
- efficiency_score, idle_percentage, underutilized_percentage
- underutilized_node_count, overprovisioned_node_count
- underutilized_cluster_count
- idle_node_hours, low_utilization_node_hours
- avg_network_sent_mbps, avg_network_received_mbps
- avg_disk_read_mbps, avg_disk_write_mbps

---

## 🔄 Reliability Domain (1 Metric View)

### 6. `job_performance`

**Purpose:** Job execution performance metrics for reliability and efficiency analysis.

**Source Table:** `fact_job_run_timeline` (lakeflow domain)

**Key Business Questions:**
- What is our job success rate?
- Show failed jobs today
- Which jobs are slowest?
- Job failure rate by workspace
- What's the average job duration?
- Show jobs with performance regression

**Dimensions (18):**
- run_date, year, month, quarter, week_of_year
- job_id, job_name, run_id
- workspace_id, workspace_name
- result_state, termination_type, trigger_type
- job_cluster_type, is_scheduled
- duration_tier, error_category

**Measures (22):**
- total_runs, successful_runs, failed_runs, cancelled_runs
- success_rate, failure_rate
- avg_duration_seconds, median_duration_seconds
- p95_duration_seconds, p99_duration_seconds
- max_duration_seconds, min_duration_seconds
- total_duration_hours
- avg_setup_time_seconds, avg_execution_time_seconds
- runs_today, runs_7d, runs_30d
- unique_jobs, unique_workspaces
- jobs_with_failures, avg_retries

---

## 🔒 Security Domain (2 Metric Views)

### 7. `security_events`

**Purpose:** Security and audit event analytics for compliance and access monitoring.

**Source Table:** `fact_audit_logs` (security domain)

**Key Business Questions:**
- Who accessed this resource?
- Security events by user
- Failed access attempts today
- Sensitive actions in last 24 hours
- Most active users by security events
- Event trend over time

**Dimensions (18):**
- event_date, year, month, quarter, week_of_year
- workspace_id, workspace_name
- service_name, action_name
- user_identity, user_type
- source_ip_address, request_method
- response_status_code, is_success
- event_category, risk_level, hour_of_day

**Measures (20):**
- total_events, successful_events, failed_events
- success_rate, failure_rate
- events_today, events_24h, events_7d, events_30d
- unique_users, unique_services, unique_actions
- unique_source_ips
- failed_logins, permission_denials
- sensitive_data_accesses, admin_actions
- high_risk_events, medium_risk_events

---

### 8. `governance_analytics`

**Purpose:** Data lineage and governance analytics for compliance and impact analysis.

**Source Table:** `fact_table_lineage` (governance domain)

**Key Business Questions:**
- Who accessed this table?
- What tables are most frequently accessed?
- Which jobs read from this table?
- Show me the data lineage for table X
- What tables haven't been accessed in 30 days?
- Show read/write activity by user

**Dimensions (20):**
- event_date, year, month, week_of_year
- source_table_full_name, source_catalog, source_schema, source_table_name, source_type
- target_table_full_name, target_catalog, target_schema, target_table_name, target_type
- entity_type, entity_id, created_by
- workspace_id, workspace_name
- operation_type, activity_status

**Measures (18):**
- total_events, read_events, write_events, read_write_ratio
- active_table_count, inactive_table_count
- unique_source_tables, unique_target_tables, unique_tables
- unique_users, unique_jobs, unique_pipelines, unique_notebooks
- events_today, events_7d, events_30d
- job_events, notebook_events, pipeline_events, dashboard_events

---

## ✅ Quality Domain (2 Metric Views)

### 9. `data_quality`

**Purpose:** Data quality monitoring metrics for governance and compliance.

**Source Table:** `fact_data_classification` (data_quality_monitoring domain)

**Key Business Questions:**
- What is our data quality score?
- Tables with quality issues
- PII data distribution
- Schema change frequency
- Tables without documentation
- Quality trend over time

**Dimensions (15):**
- classification_date, year, month, quarter
- catalog_name, schema_name, table_name
- classification_type, sensitivity_level
- has_pii, has_documentation, is_compliant
- quality_tier, owner

**Measures (15):**
- total_tables, classified_tables, unclassified_tables
- classification_coverage
- pii_tables, sensitive_tables, public_tables
- tables_with_issues, quality_score
- documented_tables, undocumented_tables
- compliant_tables, non_compliant_tables
- avg_quality_score, min_quality_score

---

### 10. `ml_intelligence`

**Purpose:** ML model inference monitoring and performance analytics.

**Source Table:** `fact_model_inference` (mlflow domain)

**Key Business Questions:**
- Model inference latency
- Model prediction accuracy
- Inference volume by model
- Model drift detection
- Feature importance changes
- Model serving cost

**Dimensions (15):**
- inference_date, year, month, quarter
- model_name, model_version, model_stage
- endpoint_name, workspace_id, workspace_name
- prediction_type, is_batch, is_realtime
- latency_tier, drift_status

**Measures (18):**
- total_inferences, successful_inferences, failed_inferences
- success_rate, error_rate
- avg_latency_ms, p95_latency_ms, p99_latency_ms
- max_latency_ms, min_latency_ms
- inferences_today, inferences_7d, inferences_30d
- unique_models, unique_endpoints
- avg_confidence_score, drift_score
- serving_cost

---

## Deployment

Deploy all metric views using the provided script:

```bash
databricks bundle run -t dev metric_views_deployment_job
```

Or manually:

```python
%run ./deploy_metric_views
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `catalog` | health_monitor | Target Unity Catalog |
| `gold_schema` | gold | Gold layer schema for source tables |

### Output Schema

All metric views are deployed to: `{catalog}.metric_views.{view_name}`

---

## Genie Space Integration

These metric views are designed to be consumed by Databricks Genie Spaces:

| Genie Space | Metric Views |
|-------------|-------------|
| Cost Intelligence | cost_analytics, commit_tracking |
| Performance Hub | query_performance, cluster_utilization, cluster_efficiency |
| Reliability Center | job_performance |
| Security Operations | security_events, governance_analytics |
| Data Quality | data_quality, ml_intelligence |

---

## Related Documentation

- [Phase 3 Addendum: Metric Views Plan](../../../plans/phase3-addendum-3.3-metric-views.md)
- [Metric Views Patterns Rule](../../../.cursor/rules/semantic-layer/14-metric-views-patterns.mdc)
- [Genie Space Patterns Rule](../../../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc)

---

*Last Updated: December 2025*

