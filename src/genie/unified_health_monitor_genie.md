# Unified Databricks Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Databricks Health Monitor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Comprehensive natural language interface for Databricks platform health monitoring. Enables leadership, platform administrators, and SREs to query costs, job reliability, query performance, cluster efficiency, security audit, and data quality - all in one unified space.

**Powered by (25 tables max, curated for executive view):**
- 5 Metric Views (1 per domain - cost, job, query, security, quality)
- 60 Table-Valued Functions (full access across all domains)
- 5 ML Prediction Tables (anomaly detection per domain)
- 5 Lakehouse Monitoring Tables (profile metrics per domain)
- 4 Dimension Tables (core shared dimensions)
- 6 Fact Tables (primary fact per domain)

**⚠️ For detailed domain analysis, use domain-specific Genie Spaces.**

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Executive Overview
1. "What is the overall platform health score?"
2. "Show me key metrics across all domains"
3. "Are there any critical alerts today?"
4. "What anomalies were detected across the platform?"

### Cost Questions 💰
5. "What is our total spend this month?"
6. "Which workspaces cost the most?"
7. "Show me cost anomalies"
8. "What's the cost forecast?"

### Reliability Questions 🔄
9. "What is our job success rate?"
10. "Show me failed jobs today"
11. "Which jobs are likely to fail?"

### Performance Questions ⚡
12. "What is our P95 query duration?"
13. "Show me slow queries"
14. "Which clusters are underutilized?"

### Security Questions 🔒
15. "Who accessed sensitive data?"
16. "Are there any security anomalies?"

---

## ████ SECTION D: DATA ASSETS ████

### Metric Views (5 - One per Domain)

| Metric View | Domain | Purpose | Key Measures |
|-------------|--------|---------|--------------|
| `cost_analytics` | 💰 Cost | Comprehensive cost metrics | total_cost, total_dbus, tag_coverage_percentage |
| `job_performance` | 🔄 Reliability | Job execution metrics | success_rate, failure_rate, p95_duration |
| `query_performance` | ⚡ Performance | Query execution metrics | avg_duration, p95_duration, sla_breach_rate |
| `security_events` | 🔒 Security | Audit event metrics | total_events, failed_events, high_risk_events |
| `data_quality` | ✅ Quality | Data quality metrics | quality_score, completeness, validity |

**📌 Additional metric views available in domain-specific spaces:** `commit_tracking`, `cluster_utilization`, `cluster_efficiency`, `governance_analytics`, `ml_intelligence`

### Table-Valued Functions (60 Total)

#### Cost TVFs (15)
| Function | Purpose |
|----------|---------|
| `get_top_cost_contributors` | Top N by cost |
| `get_cost_trend_by_sku` | Cost trend |
| `get_cost_by_owner` | Chargeback |
| `get_spend_by_custom_tags` | Tag allocation |
| `get_tag_coverage` | Tag gaps |
| `get_tag_coverage` | Tag hygiene |
| `get_cost_week_over_week` | WoW comparison |
| `get_cost_anomaly_analysis` | Anomaly detection |
| `get_cost_forecast_summary_summary` | Forecasting |
| `get_cost_mtd_summary` | MTD summary |
| `get_commit_vs_actual` | Commit tracking |
| `get_spend_by_custom_tags` | Multi-tag analysis |
| `get_cost_growth_analysis` | Growth drivers |
| `get_cost_growth_by_period` | Period comparison |
| `get_cluster_cost_by_type` | AP cluster costs |

#### Reliability TVFs (12)
| Function | Purpose |
|----------|---------|
| `get_failed_jobs_summary` | Failed jobs |
| `get_job_success_rates` | Success rates |
| `get_job_duration_percentiles` | Duration stats |
| `get_job_failure_patterns` | Failure trends |
| `get_job_sla_compliance` | SLA tracking |
| `get_job_run_details` | Run history |
| `get_most_expensive_jobs` | Costly jobs |
| `get_job_retry_analysis` | Retry patterns |
| `get_job_repair_costs` | Repair costs |
| `get_job_spend_trend_analysis` | Cost trends |
| `get_job_failure_costs` | Failure impact |
| `get_job_run_duration_analysis` | Duration analysis |

#### Performance TVFs (16)
| Function | Purpose |
|----------|---------|
| `get_slowest_queries` | Slow queries |
| `get_warehouse_performance` | Warehouse metrics |
| `get_query_efficiency` | Efficiency |
| `get_high_spill_queries` | Memory issues |
| `get_query_volume_trends` | Volume trends |
| `get_user_query_summary` | User summary |
| `get_query_latency_percentiles` | Latency stats |
| `get_failed_queries` | Failed queries |
| `get_query_efficiency_analysis` | Full analysis |
| `get_job_outlier_runs` | Outliers |
| `get_cluster_utilization` | Cluster metrics |
| `get_cluster_resource_metrics` | Resource details |
| `get_underutilized_clusters` | Underutilized |
| `get_autoscaling_disabled_jobs` | No autoscale |
| `get_legacy_dbr_jobs` | Legacy DBR |
| `get_cluster_right_sizing_recommendations` | Right-sizing |

#### Security TVFs (10)
| Function | Purpose |
|----------|---------|
| `get_user_activity` | User activity |
| `get_sensitive_data_access` | Sensitive access |
| `get_failed_access_attempts` | Failed ops |
| `get_permission_change_history` | Perm changes |
| `get_off_hours_access` | Off-hours |
| `get_user_activity` | Timeline |
| `get_ip_location_analysis` | IP analysis |
| `get_table_access_audit` | Access audit |
| `get_user_activity_patterns` | Patterns |
| `get_service_account_activity` | Service accounts |

#### Quality TVFs (7)
| Function | Purpose |
|----------|---------|
| `get_stale_tables` | Freshness |
| `get_table_activity_summary` | Job quality |
| `get_table_activity_summary` | Domain freshness |
| `get_table_activity_summary` | Quality summary |
| `get_stale_tables` | Failing tables |
| `get_table_activity_summary` | Activity status |
| `get_data_lineage_summary` | Lineage |

### ML Prediction Tables (5 - Key Anomaly & Health Tables)

| Table Name | Domain | Purpose | Key Columns |
|---|---|---|---|
| `cost_anomaly_predictions` | 💰 Cost | Detect unusual spending patterns | `anomaly_score`, `is_anomaly`, `workspace_id` |
| `job_failure_predictions` | 🔄 Reliability | Predict job failure probability | `failure_probability`, `will_fail`, `risk_factors` |
| `pipeline_health_predictions` | 🔄 Reliability | Overall pipeline health (0-100) | `prediction`, `job_id`, `run_date` |
| `access_anomaly_predictions` | 🔒 Security | Detect unusual access patterns | `threat_score`, `is_threat`, `user_identity` |
| `quality_anomaly_predictions` | ✅ Quality | Detect data drift/quality issues | `drift_score`, `is_drifted`, `table_name` |

**📌 Full ML model catalog (25 models) available in domain-specific spaces:**
- **Cost:** budget_forecast, tag_recommendations, job_cost_optimizer, chargeback, commitment
- **Performance:** job_duration, query_optimization, cache_hit, cluster_capacity, rightsizing, dbr_migration
- **Reliability:** retry_success, incident_impact, self_healing
- **Security:** user_risk_scores, access_classifications, off_hours_baseline
- **Quality:** quality_trend, freshness_alert

### Lakehouse Monitoring Tables (5 - Profile Metrics Only)

| Table | Domain | Key Custom Metrics |
|-------|--------|---------|
| `fact_usage_profile_metrics` | 💰 Cost | total_daily_cost, serverless_ratio, tag_coverage_pct |
| `fact_job_run_timeline_profile_metrics` | 🔄 Reliability | success_rate, failure_count, p90_duration |
| `fact_query_history_profile_metrics` | ⚡ Performance | p99_duration_ms, sla_breach_rate, queries_per_second |
| `fact_audit_logs_profile_metrics` | 🔒 Security | sensitive_access_rate, failure_rate, off_hours_rate |
| `fact_table_quality_profile_metrics` | ✅ Quality | quality_score, completeness_rate, validity_rate |

**📌 Drift metrics (_drift_metrics) available in domain-specific spaces for trend analysis.**

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**ALL Lakehouse Monitoring tables require these filters:**

```sql
-- ✅ REQUIRED for ALL _profile_metrics tables
WHERE column_name = ':table'     -- Table-level custom metrics
  AND log_type = 'INPUT'         -- Input data statistics
  AND slice_key IS NULL          -- For overall metrics (or specify for slicing)

-- ✅ REQUIRED for ALL _drift_metrics tables  
WHERE drift_type = 'CONSECUTIVE' -- Period-over-period comparison
  AND column_name = ':table'     -- Table-level drift
```

#### Slicing Dimensions by Monitor

| Monitor | Slice Keys |
|---------|------------|
| **Cost** | `workspace_id`, `sku_name`, `cloud`, `is_tagged`, `product_features_is_serverless` |
| **Job** | `workspace_id`, `job_name`, `result_state`, `trigger_type`, `termination_code` |
| **Query** | `workspace_id`, `compute_warehouse_id`, `execution_status`, `statement_type`, `executed_by` |
| **Cluster** | `workspace_id`, `cluster_id`, `node_type`, `cluster_name`, `driver` |
| **Security** | `workspace_id`, `service_name`, `audit_level`, `action_name`, `user_identity_email` |
| **Quality** | `catalog_name`, `schema_name`, `table_name`, `has_critical_violations` |
| **Governance** | `workspace_id`, `entity_type`, `created_by`, `source_catalog_name` |
| **Inference** | `workspace_id`, `is_anomaly`, `anomaly_category` |

### Gold Layer Tables (38 Total - from gold_layer_design/yaml/)

#### 💰 Cost Tables (billing/)
| Table | Purpose | YAML Source |
|-------|---------|-------------|
| `dim_sku` | SKU reference | billing/dim_sku.yaml |
| `fact_usage` | Billing usage | billing/fact_usage.yaml |
| `fact_account_prices` | Account pricing | billing/fact_account_prices.yaml |
| `fact_list_prices` | List prices | billing/fact_list_prices.yaml |

#### ⚡ Performance Tables (compute/, query_performance/)
| Table | Purpose | YAML Source |
|-------|---------|-------------|
| `dim_cluster` | Cluster metadata | compute/dim_cluster.yaml |
| `dim_node_type` | Node type specs | compute/dim_node_type.yaml |
| `fact_node_timeline` | Node utilization | compute/fact_node_timeline.yaml |
| `dim_warehouse` | Warehouse metadata | query_performance/dim_warehouse.yaml |
| `fact_query_history` | Query history | query_performance/fact_query_history.yaml |
| `fact_warehouse_events` | Warehouse events | query_performance/fact_warehouse_events.yaml |

#### 🔄 Reliability Tables (lakeflow/)
| Table | Purpose | YAML Source |
|-------|---------|-------------|
| `dim_job` | Job metadata | lakeflow/dim_job.yaml |
| `dim_job_task` | Task metadata | lakeflow/dim_job_task.yaml |
| `dim_pipeline` | Pipeline metadata | lakeflow/dim_pipeline.yaml |
| `fact_job_run_timeline` | Job runs | lakeflow/fact_job_run_timeline.yaml |
| `fact_job_task_run_timeline` | Task runs | lakeflow/fact_job_task_run_timeline.yaml |
| `fact_pipeline_update_timeline` | Pipeline updates | lakeflow/fact_pipeline_update_timeline.yaml |

#### 🔒 Security Tables (security/, governance/)
| Table | Purpose | YAML Source |
|-------|---------|-------------|
| `fact_audit_logs` | Audit events | security/fact_audit_logs.yaml |
| `fact_assistant_events` | AI assistant | security/fact_assistant_events.yaml |
| `fact_clean_room_events` | Clean room ops | security/fact_clean_room_events.yaml |
| `fact_inbound_network` | Inbound traffic | security/fact_inbound_network.yaml |
| `fact_outbound_network` | Outbound traffic | security/fact_outbound_network.yaml |
| `fact_table_lineage` | Data lineage | governance/fact_table_lineage.yaml |
| `fact_column_lineage` | Column lineage | governance/fact_column_lineage.yaml |

#### ✅ Quality Tables (data_classification/, data_quality_monitoring/, storage/, mlflow/, model_serving/, marketplace/)
| Table | Purpose | YAML Source |
|-------|---------|-------------|
| `fact_data_classification` | Data classification | data_classification/fact_data_classification.yaml |
| `fact_data_classification_results` | Classification results | data_classification/fact_data_classification_results.yaml |
| `fact_dq_monitoring` | DQ monitoring | data_quality_monitoring/fact_dq_monitoring.yaml |
| `fact_data_quality_monitoring_table_results` | Table DQ results | data_quality_monitoring/fact_data_quality_monitoring_table_results.yaml |
| `fact_predictive_optimization` | Predictive opt | storage/fact_predictive_optimization.yaml |
| `dim_experiment` | MLflow experiments | mlflow/dim_experiment.yaml |
| `fact_mlflow_runs` | MLflow runs | mlflow/fact_mlflow_runs.yaml |
| `fact_mlflow_run_metrics_history` | MLflow metrics | mlflow/fact_mlflow_run_metrics_history.yaml |
| `dim_served_entities` | Model serving | model_serving/dim_served_entities.yaml |
| `fact_endpoint_usage` | Endpoint usage | model_serving/fact_endpoint_usage.yaml |
| `fact_payload_logs` | Payload logs | model_serving/fact_payload_logs.yaml |
| `fact_listing_access` | Marketplace access | marketplace/fact_listing_access.yaml |
| `fact_listing_funnel` | Marketplace funnel | marketplace/fact_listing_funnel.yaml |

#### 🌐 Shared Tables (shared/)
| Table | Purpose | YAML Source |
|-------|---------|-------------|
| `dim_workspace` | Workspace reference | shared/dim_workspace.yaml |
| `dim_user` | User information | shared/dim_user.yaml |
| `dim_date` | Date dimension for time analysis | shared/dim_date.yaml |

### Data Model Relationships 🔗

**Cross-Domain Foreign Key Constraints** (extracted from `gold_layer_design/yaml/`)

#### 💰 Cost Domain Relationships
| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_usage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_usage` | → | `dim_sku` | `sku_name` = `sku_name` | LEFT |
| `fact_usage` | → | `dim_cluster` | `(workspace_id, usage_metadata_cluster_id)` = `(workspace_id, cluster_id)` | LEFT |
| `fact_usage` | → | `dim_job` | `(workspace_id, usage_metadata_job_id)` = `(workspace_id, job_id)` | LEFT |
| `fact_account_prices` | → | `dim_sku` | `sku_name` = `sku_name` | LEFT |
| `fact_list_prices` | → | `dim_sku` | `sku_name` = `sku_name` | LEFT |

#### 🔄 Reliability Domain Relationships
| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_job_run_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_job_run_timeline` | → | `dim_job` | `(workspace_id, job_id)` = `(workspace_id, job_id)` | LEFT |
| `fact_job_task_run_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_job_task_run_timeline` | → | `dim_job` | `(workspace_id, job_id)` = `(workspace_id, job_id)` | LEFT |
| `fact_job_task_run_timeline` | → | `dim_job_task` | `(workspace_id, job_id, task_key)` = `(workspace_id, job_id, task_key)` | LEFT |
| `fact_pipeline_update_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_pipeline_update_timeline` | → | `dim_pipeline` | `(workspace_id, pipeline_id)` = `(workspace_id, pipeline_id)` | LEFT |

#### ⚡ Performance Domain Relationships
| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_query_history` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_query_history` | → | `dim_warehouse` | `(workspace_id, warehouse_id)` = `(workspace_id, warehouse_id)` | LEFT |
| `fact_warehouse_events` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_warehouse_events` | → | `dim_warehouse` | `(workspace_id, warehouse_id)` = `(workspace_id, warehouse_id)` | LEFT |
| `fact_node_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_node_timeline` | → | `dim_cluster` | `(workspace_id, cluster_id)` = `(workspace_id, cluster_id)` | LEFT |
| `fact_node_timeline` | → | `dim_node_type` | `node_type_id` = `node_type_id` | LEFT |

#### 🔒 Security Domain Relationships
| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_audit_logs` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_audit_logs` | → | `dim_user` | `user_identity_email` = `email` | LEFT |
| `fact_table_lineage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |

#### ✅ Quality Domain Relationships
| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_mlflow_runs` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_mlflow_runs` | → | `dim_experiment` | `(workspace_id, experiment_id)` = `(workspace_id, experiment_id)` | LEFT |
| `fact_endpoint_usage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_endpoint_usage` | → | `dim_served_entities` | `(workspace_id, endpoint_id)` = `(workspace_id, endpoint_id)` | LEFT |

**Join Patterns:**
- **Single Key:** `ON fact.key = dim.key`
- **Composite Key (workspace-scoped):** `ON fact.workspace_id = dim.workspace_id AND fact.fk = dim.pk`
- **Three-Part Key (task-level):** `ON fact.workspace_id = dim.workspace_id AND fact.job_id = dim.job_id AND fact.task_key = dim.task_key`

---

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC LAYER ASSET SELECTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER QUERY PATTERN                      → USE THIS ASSET                   │
│  ───────────────────────────────────────────────────────────────────────    │
│  "What's the current X?"                 → Metric View (mv_*)               │
│  "Show me total X by Y"                  → Metric View (mv_*)               │
│  "Dashboard of X"                        → Metric View (mv_*)               │
│  ───────────────────────────────────────────────────────────────────────    │
│  "Is X increasing/decreasing over time?" → Custom Metrics (_drift_metrics)  │
│  "How has X changed since last week?"    → Custom Metrics (_drift_metrics)  │
│  "Alert me when X exceeds threshold"     → Custom Metrics (for alerting)    │
│  ───────────────────────────────────────────────────────────────────────    │
│  "Which specific items have X?"          → TVF (get_*)                      │
│  "List the top N items with X"           → TVF (get_*)                      │
│  "Show me items from DATE to DATE"       → TVF (get_*)                      │
│  "What failed/what's slow/what's stale?" → TVF (get_*)                      │
│  ───────────────────────────────────────────────────────────────────────    │
│  "Predict/Forecast X"                    → ML Tables (*_predictions)        │
│  "Anomalies detected"                    → ML Tables (*_anomaly_predictions)│
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Current state aggregates** | Metric View | "What's success rate?" → `mv_job_performance` |
| **Trend over time** | Custom Metrics | "Is cost increasing?" → `_drift_metrics` |
| **List of specific items** | TVF | "Which jobs failed?" → `get_failed_jobs_summary` |
| **Predictions/Forecasts** | ML Tables | "Cost forecast" → `cost_forecast_predictions` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for PREDICTION** → ML Tables

### Domain Routing

| User Question Contains | Domain | Primary Asset |
|------------------------|--------|---------------|
| "cost", "spend", "billing" | Cost | `cost_analytics` + cost TVFs |
| "job", "failure", "success rate" | Reliability | `job_performance` + job TVFs |
| "query", "slow", "warehouse" | Performance | `query_performance` + query TVFs |
| "cluster", "utilization", "cpu" | Performance | `cluster_utilization` + cluster TVFs |
| "security", "access", "audit" | Security | `security_events` + security TVFs |
| "quality", "freshness", "stale" | Quality | `data_quality` + quality TVFs |
| "anomaly", "predict", "forecast" | ML | ML prediction tables |

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a comprehensive Databricks platform health analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Route by Domain:** Cost→cost_analytics, Jobs→job_performance, Query→query_performance
3. **TVFs for Lists:** Use TVFs for "which", "top N", "list" queries
4. **Trends:** For "is X increasing?" check _drift_metrics tables
5. **Date Default:** Cost=30 days, Jobs/Queries=7 days, Security=24 hours
6. **Aggregation:** SUM for totals, AVG for averages, COUNT for volumes
7. **Sorting:** DESC by primary metric unless specified
8. **Limits:** Top 10-20 for ranking queries
9. **Health Score:** 0-25=Critical, 26-50=Poor, 51-75=Fair, 76-90=Good, 91-100=Excellent
10. **Anomalies:** For "anomalies" → query *_anomaly_predictions tables
11. **Forecasts:** For "forecast/predict" → query *_forecast_predictions tables
12. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
13. **Context:** Explain results in business terms
14. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### Domain Routing Guide

| User Question Pattern | Domain | Primary Asset |
|----------------------|--------|---------------|
| "cost", "spend", "billing" | Cost | cost_analytics + cost TVFs |
| "job", "failure", "success rate" | Reliability | job_performance + job TVFs |
| "query", "slow", "warehouse" | Performance | query_performance + query TVFs |
| "cluster", "utilization", "cpu" | Performance | cluster_utilization + cluster TVFs |
| "security", "access", "audit" | Security | security_events + security TVFs |
| "quality", "freshness", "stale" | Quality | data_quality + quality TVFs |
| "anomaly", "predict", "forecast" | ML | ML prediction tables |

### Key TVF Signatures (Top 10 Most Used)

| Function | Signature | Domain |
|----------|-----------|--------|
| `get_top_cost_contributors` | `(start_date, end_date, top_n)` | Cost |
| `get_failed_jobs_summary` | `(start_date, end_date)` | Reliability |
| `get_slowest_queries` | `(start_date, end_date, threshold_seconds)` | Performance |
| `get_underutilized_clusters` | `(start_date, end_date, cpu_threshold)` | Performance |
| `get_user_activity` | `(user_email, start_date, end_date)` | Security |
| `get_stale_tables` | `(start_date, end_date, stale_threshold_hours)` | Quality |
| `get_cost_anomaly_analysis` | `(start_date, end_date, threshold)` | Cost |
| `get_job_success_rates` | `(start_date, end_date)` | Reliability |
| `get_warehouse_performance` | `(start_date, end_date)` | Performance |
| `get_sensitive_data_access` | `(start_date, end_date)` | Security |

---

## ████ SECTION G: ML MODEL INTEGRATION (25 Models) ████

### All ML Models by Domain

#### 💰 Cost Domain (6 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `cost_anomaly_detector` | `cost_anomaly_predictions` | "unusual spending" |
| `budget_forecaster` | `budget_forecast_predictions` | "forecast cost" |
| `job_cost_optimizer` | `job_cost_optimizer_predictions` | "reduce job cost" |
| `tag_recommender` | `tag_recommendations` | "suggest tags" |
| `commitment_recommender` | `commitment_recommendations` | "commit level" |
| `chargeback_attribution` | `chargeback_predictions` | "allocate cost" |

#### 🔄 Reliability Domain (5 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `job_failure_predictor` | `job_failure_predictions` | "will fail" |
| `job_duration_forecaster` | `job_duration_predictions` | "how long" |
| `sla_breach_predictor` | `incident_impact_predictions` | "SLA breach" |
| `pipeline_health_scorer` | `pipeline_health_predictions` | "health score" |
| `retry_success_predictor` | `retry_success_predictions` | "retry succeed" |

#### ⚡ Performance Domain (7 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `query_performance_forecaster` | `query_optimization_recommendations` | "predict latency" |
| `warehouse_optimizer` | `cluster_capacity_recommendations` | "warehouse size" |
| `cache_hit_predictor` | `cache_hit_predictions` | "cache hit" |
| `query_optimization_recommender` | `query_optimization_classifications` | "optimize query" |
| `cluster_sizing_recommender` | `cluster_rightsizing_recommendations` | "right-size" |
| `cluster_capacity_planner` | `cluster_capacity_recommendations` | "capacity" |
| `regression_detector` | — | "regression" |

#### 🔒 Security Domain (4 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `security_threat_detector` | `access_anomaly_predictions` | "threat" |
| `access_pattern_analyzer` | `access_classifications` | "access pattern" |
| `compliance_risk_classifier` | `user_risk_scores` | "risk score" |
| `permission_recommender` | — | "permission" |

#### 📋 Quality Domain (3 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `data_drift_detector` | `quality_anomaly_predictions` | "data drift" |
| `schema_change_predictor` | `quality_trend_predictions` | "schema change" |
| `schema_evolution_predictor` | `freshness_alert_predictions` | "freshness alert" |

### Cross-Domain ML Query Patterns

#### Unified Anomaly View
```sql
-- All anomalies across domains in one view
SELECT 'COST' as domain, workspace_name as entity, anomaly_score, prediction_date
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions WHERE is_anomaly = TRUE
UNION ALL
SELECT 'SECURITY', user_identity, threat_score, prediction_date
FROM ${catalog}.${gold_schema}.access_anomaly_predictions WHERE is_threat = TRUE
UNION ALL
SELECT 'QUALITY', table_name, drift_score, prediction_date
FROM ${catalog}.${gold_schema}.quality_anomaly_predictions WHERE is_drifted = TRUE
ORDER BY prediction_date DESC;
```

#### High-Risk Summary
```sql
-- All high-risk predictions across domains
SELECT 'JOB_FAILURE' as risk_type, job_name as entity, failure_probability as risk_score
FROM ${catalog}.${gold_schema}.job_failure_predictions WHERE will_fail = TRUE
UNION ALL
SELECT 'USER_RISK', user_identity, risk_level * 20 as risk_score
FROM ${catalog}.${gold_schema}.user_risk_scores WHERE risk_level >= 4
UNION ALL
SELECT 'COST_ANOMALY', workspace_name, ABS(anomaly_score) * 100
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions WHERE is_anomaly = TRUE
ORDER BY risk_score DESC LIMIT 20;
```

### ML Model Selection Guide

```
QUERY DOMAIN                    ML MODEL                    TRIGGER WORDS
─────────────────────────────────────────────────────────────────────────
💰 Cost:
  Anomaly detection          → cost_anomaly_predictions      "unusual", "spike"
  Forecasting                → cost_forecast_predictions     "forecast", "predict"
  Optimization               → migration_recommendations     "save", "reduce"
  
🔄 Reliability:
  Failure prediction         → job_failure_predictions       "fail", "at risk"
  Duration forecasting       → job_duration_predictions      "how long", "estimate"
  Health scoring             → pipeline_health_predictions   "health", "score"
  
⚡ Performance:
  Query optimization         → query_optimization_*          "optimize", "improve"
  Right-sizing               → cluster_rightsizing_*         "right-size", "too big"
  Capacity planning          → cluster_capacity_*            "capacity", "scale"
  
🔒 Security:
  Threat detection           → access_anomaly_predictions    "threat", "suspicious"
  Risk scoring               → user_risk_scores              "risky", "risk score"
  
📋 Quality:
  Data drift                 → quality_anomaly_predictions   "drift", "changed"
  Schema prediction          → quality_trend_predictions     "schema", "breaking"
```

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | 5 metric views, 60 TVFs, 5 ML tables, 5 monitoring tables, 4 dims, 6 facts (25 total) | ✅ |
| **E. General Instructions** | 16 lines (≤20) | ✅ |
| **F. TVFs** | Domain routing + top 10 signatures | ✅ |
| **G. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🌐 **Unified** (All Domains)

---

## Total Asset Summary

| Asset Type | Count | Notes |
|------------|-------|-------|
| Metric Views | 5 | 1 per domain (curated) |
| Table-Valued Functions | 60 | Full access across all domains |
| ML Prediction Tables | 5 | Anomaly detection per domain |
| Lakehouse Monitoring Tables | 5 | Profile metrics per domain |
| Dimension Tables | 4 | Core shared dimensions |
| Fact Tables | 6 | Primary fact per domain |
| **Total Tables (Genie Limit)** | **25** | Rationalized for 25-table limit |

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**
> **Grounded in:** All 11 Metric Views, TVFs across all domains, ML Tables

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "What is our total spend this month?"
**Expected SQL:**
```sql
SELECT MEASURE(total_cost) as mtd_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());
```
**Expected Result:** Month-to-date cost across all workspaces and SKUs

---

### Question 2: "What is our job success rate?"
**Expected SQL:**
```sql
SELECT MEASURE(success_rate) as success_pct
FROM ${catalog}.${gold_schema}.mv_job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall job execution success rate

---

### Question 3: "What is the P95 query duration?"
**Expected SQL:**
```sql
SELECT MEASURE(p95_duration_seconds) as p95_sec
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** 95th percentile query latency for performance SLA

---

### Question 4: "What is the security event success rate?"
**Expected SQL:**
```sql
SELECT MEASURE(success_rate) as auth_success_pct
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Authentication/authorization success rate

---

### Question 5: "What is our data quality score?"
**Expected SQL:**
```sql
SELECT MEASURE(quality_score) as overall_quality
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall data quality health score (0-100)

---

### Question 6: "Show me top cost drivers"
**Expected SQL:**
```sql
SELECT 
  sku_name,
  MEASURE(total_cost) as cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY sku_name
ORDER BY cost DESC
LIMIT 10;
```
**Expected Result:** Top 10 SKUs by spend for optimization focus

---

### Question 7: "Show me failed jobs today"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(
  1
))
ORDER BY failure_rate DESC
LIMIT 20;
```
**Expected Result:** Today's failed jobs with failure details

---

### Question 8: "Show me slow queries"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_slowest_queries(
  1,
  30
))
ORDER BY duration_seconds DESC
LIMIT 20;
```
**Expected Result:** Queries exceeding 30-second threshold

---

### Question 9: "Show me security threats"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  prediction as threat_score
FROM ${catalog}.${feature_schema}.access_anomaly_predictions
WHERE prediction < -0.5
ORDER BY prediction ASC
LIMIT 20;
```
**Expected Result:** ML-detected security anomalies

---

### Question 10: "Show me stale tables"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(
  7
))
WHERE freshness_status IN ('STALE', 'CRITICAL')
ORDER BY hours_since_update DESC
LIMIT 20;
```
**Expected Result:** Tables with freshness issues

---

### Question 11: "What is our cluster utilization?"
**Expected SQL:**
```sql
SELECT MEASURE(avg_cpu_utilization) as cpu_pct
FROM ${catalog}.${gold_schema}.mv_cluster_utilization
WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Average CPU utilization across all clusters

---

### Question 12: "Show me commit utilization"
**Expected SQL:**
```sql
SELECT 
  commit_type,
  MEASURE(utilization_rate) as usage_pct
FROM ${catalog}.${gold_schema}.mv_commit_tracking
WHERE usage_month = DATE_TRUNC('month', CURRENT_DATE())
GROUP BY commit_type
ORDER BY usage_pct DESC;
```
**Expected Result:** Commitment usage rates for capacity planning

---

### Question 13: "Show me warehouse utilization"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_warehouse_performance(
  7
))
ORDER BY query_count DESC
LIMIT 10;
```
**Expected Result:** Warehouse-level query volumes and concurrency

---

### Question 14: "What is the DLT pipeline health?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_pipeline_health(
  7
))
ORDER BY success_rate ASC
LIMIT 10;
```
**Expected Result:** DLT pipeline execution success rates and health metrics

---

### Question 15: "Show me underutilized clusters"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_underutilized_clusters(
  30
))
WHERE avg_cpu_pct < 30
ORDER BY potential_savings DESC
LIMIT 15;
```
**Expected Result:** Clusters with low utilization and savings opportunities

---

### Question 16: "Show me high-risk events"
**Expected SQL:**
```sql
SELECT 
  user_email,
  action_category,
  MEASURE(high_risk_events) as risk_count
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND risk_level = 'HIGH'
GROUP BY user_email, action_category
ORDER BY risk_count DESC
LIMIT 15;
```
**Expected Result:** High-risk security events requiring attention

---

### Question 17: "Show me tables failing quality checks"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(
  7
))
ORDER BY failed_checks DESC, quality_score ASC
LIMIT 20;
```
**Expected Result:** Tables with failed data quality validations

---

### Question 18: "What is our tag coverage?"
**Expected SQL:**
```sql
SELECT MEASURE(tag_coverage_percentage) as coverage_pct
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Percentage of resources with cost allocation tags

---

### Question 19: "Show me pipeline health scores"
**Expected SQL:**
```sql
SELECT 
  pipeline_name,
  prediction as health_score
FROM ${catalog}.${feature_schema}.pipeline_health_predictions
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY prediction ASC
LIMIT 20;
```
**Expected Result:** ML-predicted pipeline health scores

---

### Question 20: "Show me cluster right-sizing recommendations"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cluster_rightsizing_recommendations(
  30
))
ORDER BY potential_savings DESC
LIMIT 15;
```
**Expected Result:** ML-powered cluster sizing recommendations with cost impact

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Platform health overview - combine cost, performance, reliability, security, and quality KPIs"
**Expected SQL:**
```sql
WITH cost_health AS (
  SELECT 
    MEASURE(total_cost) as total_spend,
    MEASURE(cost_7d) as cost_7d,
    MEASURE(cost_30d) as cost_30d,
    MEASURE(tag_coverage_percentage) as tag_coverage
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
job_health AS (
  SELECT 
    MEASURE(success_rate) as job_success_rate,
    MEASURE(failure_rate) as job_failure_rate,
    MEASURE(total_runs) as total_job_runs
  FROM ${catalog}.${gold_schema}.mv_job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
query_health AS (
  SELECT 
    MEASURE(p95_duration_seconds) as p95_latency,
    MEASURE(sla_breach_rate) as sla_breach_pct,
    MEASURE(cache_hit_rate) as cache_pct
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
security_health AS (
  SELECT 
    MEASURE(success_rate) as auth_success_rate,
    MEASURE(high_risk_events) as high_risk_count,
    MEASURE(unique_users) as active_users
  FROM ${catalog}.${gold_schema}.mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
quality_health AS (
  SELECT 
    MEASURE(quality_score) as data_quality,
    MEASURE(freshness_rate) as freshness_pct,
    MEASURE(staleness_rate) as staleness_pct
  FROM ${catalog}.${gold_schema}.mv_data_quality
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
cluster_health AS (
  SELECT 
    MEASURE(avg_cpu_utilization) as avg_cpu,
    MEASURE(efficiency_score) as efficiency
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT 
  ch.total_spend,
  ch.cost_7d,
  ch.tag_coverage,
  jh.job_success_rate,
  jh.job_failure_rate,
  jh.total_job_runs,
  qh.p95_latency,
  qh.sla_breach_pct,
  qh.cache_pct,
  sh.auth_success_rate,
  sh.high_risk_count,
  sh.active_users,
  quh.data_quality,
  quh.freshness_pct,
  quh.staleness_pct,
  clh.avg_cpu,
  clh.efficiency,
  CASE 
    WHEN jh.job_failure_rate > 10 OR qh.sla_breach_pct > 5 THEN 'Critical - Reliability Issues'
    WHEN sh.high_risk_count > 20 OR sh.auth_success_rate < 95 THEN 'Critical - Security Concerns'
    WHEN quh.data_quality < 70 OR quh.staleness_pct > 20 THEN 'Critical - Data Quality Crisis'
    WHEN ch.cost_7d * 30 > ch.cost_30d * 1.2 THEN 'Warning - Cost Spike Detected'
    WHEN qh.cache_pct > 80 AND jh.job_success_rate > 95 AND quh.data_quality >= 90 THEN 'Excellent Health'
    ELSE 'Normal'
  END as overall_platform_health,
  CASE 
    WHEN jh.job_failure_rate > 10 THEN 'Investigate job failures immediately'
    WHEN qh.sla_breach_pct > 5 THEN 'Optimize slow queries and warehouse sizing'
    WHEN sh.high_risk_count > 20 THEN 'Review security events and threats'
    WHEN quh.staleness_pct > 20 THEN 'Fix data pipeline freshness issues'
    WHEN ch.cost_7d * 30 > ch.cost_30d * 1.2 THEN 'Analyze cost drivers and right-size resources'
    WHEN clh.avg_cpu < 40 THEN 'Downsize underutilized clusters'
    ELSE 'Continue monitoring'
  END as top_priority_action
FROM cost_health ch
CROSS JOIN job_health jh
CROSS JOIN query_health qh
CROSS JOIN security_health sh
CROSS JOIN quality_health quh
CROSS JOIN cluster_health clh;
```
**Expected Result:** Executive platform health dashboard with cross-domain KPIs and prioritized actions

---

### Question 22: "🔬 DEEP RESEARCH: Cost optimization opportunities - combine underutilized clusters, right-sizing, and tagging gaps"
**Expected SQL:**
```sql
WITH underutilized AS (
  SELECT
    cluster_name,
    avg_cpu_pct,
    potential_savings as savings_from_underutilization
  FROM TABLE(${catalog}.${gold_schema}.get_underutilized_clusters(30))
  WHERE avg_cpu_pct < 30
),
rightsizing AS (
  SELECT
    cluster_name,
    current_size,
    recommended_size,
    potential_savings as savings_from_rightsizing
  FROM TABLE(${catalog}.${gold_schema}.get_cluster_rightsizing_recommendations(30))
  WHERE recommended_action != 'NO_CHANGE'
),
untagged AS (
  SELECT 
    workspace_name,
    SUM(MEASURE(total_cost)) as untagged_cost
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
      AND tag_team IS NULL
  GROUP BY workspace_name
),
autoscaling_gaps AS (
  SELECT
    job_name,
    estimated_savings
  FROM TABLE(${catalog}.${gold_schema}.get_autoscaling_disabled_jobs(30))
),
legacy_dbr AS (
  SELECT
    COUNT(*) as legacy_job_count
  FROM TABLE(${catalog}.${gold_schema}.get_legacy_dbr_jobs(30))
)
SELECT 
  COALESCE(SUM(u.savings_from_underutilization), 0) as savings_underutil,
  COALESCE(SUM(r.savings_from_rightsizing), 0) as savings_rightsize,
  COALESCE(SUM(ut.untagged_cost * 0.1), 0) as estimated_waste_from_untagged,
  COALESCE(SUM(ag.estimated_savings), 0) as savings_autoscaling,
  ld.legacy_job_count,
  COALESCE(SUM(u.savings_from_underutilization), 0) + 
  COALESCE(SUM(r.savings_from_rightsizing), 0) + 
  COALESCE(SUM(ag.estimated_savings), 0) as total_monthly_savings_potential,
  CASE 
    WHEN COALESCE(SUM(u.savings_from_underutilization), 0) + COALESCE(SUM(r.savings_from_rightsizing), 0) > 10000 THEN 'Critical - Immediate Right-Sizing Required'
    WHEN COALESCE(SUM(ut.untagged_cost), 0) > 5000 THEN 'High - Improve Tagging for Accountability'
    WHEN ld.legacy_job_count > 20 THEN 'Medium - Modernize Legacy DBR Jobs'
    ELSE 'Low - Continue Monitoring'
  END as optimization_priority,
  ARRAY(
    CASE WHEN COALESCE(SUM(u.savings_from_underutilization), 0) > 5000 THEN 'Downsize or terminate underutilized clusters' END,
    CASE WHEN COALESCE(SUM(r.savings_from_rightsizing), 0) > 5000 THEN 'Apply ML right-sizing recommendations' END,
    CASE WHEN COALESCE(SUM(ut.untagged_cost), 0) > 5000 THEN 'Implement tagging policy and governance' END,
    CASE WHEN COALESCE(SUM(ag.estimated_savings), 0) > 2000 THEN 'Enable autoscaling on fixed-size jobs' END,
    CASE WHEN ld.legacy_job_count > 20 THEN 'Migrate to latest DBR versions' END
  ) as recommended_actions
FROM underutilized u
FULL OUTER JOIN rightsizing r ON u.cluster_name = r.cluster_name
FULL OUTER JOIN untagged ut ON 1=1
FULL OUTER JOIN autoscaling_gaps ag ON 1=1
CROSS JOIN legacy_dbr ld;
```
**Expected Result:** Comprehensive cost optimization analysis with quantified savings across multiple dimensions

---

### Question 23: "🔬 DEEP RESEARCH: Security and compliance posture - correlate access anomalies with high-risk users and sensitive data access"
**Expected SQL:**
```sql
WITH access_anomalies AS (
  SELECT 
    user_identity,
    COUNT(*) as anomaly_count,
    MIN(prediction) as worst_threat_score
  FROM ${catalog}.${feature_schema}.access_anomaly_predictions
  WHERE prediction < -0.3
    AND event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
),
user_risk AS (
  SELECT 
    user_identity,
    AVG(prediction) as avg_risk_level
  FROM ${catalog}.${feature_schema}.user_risk_scores
  WHERE prediction >= 3
    AND evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
),
sensitive_access AS (
  SELECT
    user_identity,
    COUNT(DISTINCT table_name) as sensitive_table_count,
    SUM(access_count) as total_sensitive_access
  FROM TABLE(${catalog}.${gold_schema}.get_sensitive_data_access(
    7
  ))
  GROUP BY user_identity
),
failed_attempts AS (
  SELECT 
    user_email as user_identity,
    MEASURE(failed_events) as failed_count
  FROM ${catalog}.${gold_schema}.mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_email
),
off_hours AS (
  SELECT
    user_identity,
    COUNT(*) as off_hours_events
  FROM TABLE(${catalog}.${gold_schema}.get_off_hours_access(
    7
  ))
  GROUP BY user_identity
)
SELECT 
  COALESCE(aa.user_identity, ur.user_identity, sa.user_identity) as user,
  COALESCE(aa.anomaly_count, 0) as detected_anomalies,
  COALESCE(aa.worst_threat_score, 0) as threat_score,
  COALESCE(ur.avg_risk_level, 0) as risk_level,
  COALESCE(sa.sensitive_table_count, 0) as sensitive_tables_accessed,
  COALESCE(sa.total_sensitive_access, 0) as sensitive_access_count,
  COALESCE(fa.failed_count, 0) as recent_failures,
  COALESCE(oh.off_hours_events, 0) as off_hours_activity,
  CASE 
    WHEN COALESCE(aa.anomaly_count, 0) > 5 AND COALESCE(ur.avg_risk_level, 0) >= 4 THEN 'Critical - Immediate Investigation'
    WHEN COALESCE(sa.sensitive_table_count, 0) > 20 AND COALESCE(ur.avg_risk_level, 0) >= 3 THEN 'High - Review Sensitive Access'
    WHEN COALESCE(oh.off_hours_events, 0) > 50 AND COALESCE(fa.failed_count, 0) > 10 THEN 'High - Suspicious Activity Pattern'
    WHEN COALESCE(ur.avg_risk_level, 0) >= 3 THEN 'Medium - Elevated Risk'
    ELSE 'Normal'
  END as security_status,
  CASE 
    WHEN COALESCE(aa.anomaly_count, 0) > 5 THEN 'Contain and investigate anomalous behavior'
    WHEN COALESCE(sa.sensitive_table_count, 0) > 20 THEN 'Audit sensitive data access permissions'
    WHEN COALESCE(oh.off_hours_events, 0) > 50 THEN 'Review off-hours activity justification'
    WHEN COALESCE(fa.failed_count, 0) > 10 THEN 'Investigate repeated access failures'
    ELSE 'Continue monitoring'
  END as recommended_action
FROM access_anomalies aa
FULL OUTER JOIN user_risk ur ON aa.user_identity = ur.user_identity
FULL OUTER JOIN sensitive_access sa ON COALESCE(aa.user_identity, ur.user_identity) = sa.user_identity
FULL OUTER JOIN failed_attempts fa ON COALESCE(aa.user_identity, ur.user_identity) = fa.user_identity
FULL OUTER JOIN off_hours oh ON COALESCE(aa.user_identity, ur.user_identity) = oh.user_identity
WHERE COALESCE(aa.anomaly_count, 0) > 0 
   OR COALESCE(ur.avg_risk_level, 0) >= 3
   OR COALESCE(sa.sensitive_table_count, 0) > 10
ORDER BY 
  COALESCE(aa.anomaly_count, 0) DESC,
  COALESCE(ur.avg_risk_level, 0) DESC,
  COALESCE(sa.total_sensitive_access, 0) DESC
LIMIT 25;
```
**Expected Result:** Comprehensive security posture analysis correlating multiple risk factors with prioritized remediation

---

### Question 24: "🔬 DEEP RESEARCH: Data platform reliability - correlate job failures with pipeline health, query performance, and data quality"
**Expected SQL:**
```sql
WITH job_failures AS (
  SELECT
    job_name,
    failure_rate,
    avg_duration_minutes,
    failure_count
  FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(7))
  WHERE failure_rate > 5
),
pipeline_health AS (
  SELECT 
    j.job_name as pipeline_name,
    AVG(ph.prediction) as avg_health_score
  FROM ${catalog}.${feature_schema}.pipeline_health_predictions ph
  JOIN ${catalog}.${gold_schema}.dim_job j ON ph.job_id = j.job_id
  WHERE ph.evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY j.job_name
),
query_performance AS (
  SELECT 
    warehouse_name,
    MEASURE(p95_duration_seconds) as p95_latency,
    MEASURE(sla_breach_rate) as sla_breach_pct
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY warehouse_name
),
data_quality AS (
  SELECT 
    domain,
    MEASURE(quality_score) as avg_quality,
    MEASURE(staleness_rate) as staleness_pct
  FROM ${catalog}.${gold_schema}.mv_data_quality
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY domain
),
cluster_utilization AS (
  SELECT 
    cluster_name,
    MEASURE(avg_cpu_utilization) as cpu_pct
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY cluster_name
)
SELECT 
  jf.job_name,
  jf.failure_rate,
  jf.failure_count,
  jf.avg_duration_minutes,
  COALESCE(ph.avg_health_score, 0) as ml_health_score,
  COALESCE(AVG(qp.p95_latency), 0) as warehouse_p95_latency,
  COALESCE(AVG(qp.sla_breach_pct), 0) as warehouse_sla_breach,
  COALESCE(AVG(dq.avg_quality), 100) as related_data_quality,
  COALESCE(AVG(dq.staleness_pct), 0) as data_staleness,
  COALESCE(AVG(cu.cpu_pct), 0) as cluster_cpu_utilization,
  CASE 
    WHEN jf.failure_rate > 20 AND COALESCE(ph.avg_health_score, 100) < 60 THEN 'Critical - Pipeline Failing with Low Health Score'
    WHEN COALESCE(AVG(dq.staleness_pct), 0) > 30 AND jf.failure_rate > 10 THEN 'High - Data Freshness Causing Failures'
    WHEN COALESCE(AVG(qp.sla_breach_pct), 0) > 10 AND jf.failure_rate > 10 THEN 'High - Query Performance Impacting Jobs'
    WHEN COALESCE(AVG(cu.cpu_pct), 0) > 85 THEN 'Medium - Resource Contention'
    ELSE 'Low - Isolated Job Issue'
  END as root_cause_category,
  CASE 
    WHEN COALESCE(ph.avg_health_score, 100) < 60 THEN 'Review pipeline configuration and dependencies'
    WHEN COALESCE(AVG(dq.staleness_pct), 0) > 30 THEN 'Fix upstream data freshness issues'
    WHEN COALESCE(AVG(qp.sla_breach_pct), 0) > 10 THEN 'Optimize queries or increase warehouse capacity'
    WHEN COALESCE(AVG(cu.cpu_pct), 0) > 85 THEN 'Scale cluster or reduce concurrency'
    ELSE 'Debug specific job code/logic'
  END as recommended_action
FROM job_failures jf
LEFT JOIN pipeline_health ph ON jf.job_name = ph.pipeline_name
LEFT JOIN query_performance qp ON 1=1
LEFT JOIN data_quality dq ON 1=1
LEFT JOIN cluster_utilization cu ON 1=1
GROUP BY 
  jf.job_name, jf.failure_rate, jf.failure_count, jf.avg_duration_minutes, ph.avg_health_score
ORDER BY 
  jf.failure_rate DESC,
  COALESCE(ph.avg_health_score, 100) ASC
LIMIT 20;
```
**Expected Result:** Reliability analysis correlating job failures with infrastructure, performance, and data quality factors

---

### Question 25: "🔬 DEEP RESEARCH: Executive FinOps dashboard - cost trends, efficiency, commit utilization, and optimization opportunities"
**Expected SQL:**
```sql
WITH cost_trends AS (
  SELECT 
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN MEASURE(total_cost) ELSE 0 END) as cost_7d,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS THEN MEASURE(total_cost) ELSE 0 END) as cost_30d,
    SUM(CASE WHEN usage_date >= DATE_TRUNC('month', CURRENT_DATE()) THEN MEASURE(total_cost) ELSE 0 END) as cost_mtd,
    AVG(MEASURE(tag_coverage_percentage)) as avg_tag_coverage
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
),
cost_by_domain AS (
  SELECT 
    domain,
    SUM(MEASURE(total_cost)) as domain_cost
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY domain
  ORDER BY domain_cost DESC
  LIMIT 5
),
commit_status AS (
  SELECT 
    commit_type,
    MEASURE(utilization_rate) as usage_pct,
    MEASURE(remaining_dbu) as remaining_capacity
  FROM ${catalog}.${gold_schema}.mv_commit_tracking
  WHERE usage_month = DATE_TRUNC('month', CURRENT_DATE())
  GROUP BY commit_type
),
efficiency AS (
  SELECT 
    AVG(MEASURE(avg_cpu_utilization)) as avg_cpu_util,
    AVG(MEASURE(efficiency_score)) as avg_efficiency
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
optimization_potential AS (
  SELECT
    SUM(potential_savings) as total_savings_potential
  FROM TABLE(${catalog}.${gold_schema}.get_cluster_rightsizing_recommendations(30))
  WHERE recommended_action != 'NO_CHANGE'
),
serverless_adoption AS (
  SELECT 
    MEASURE(serverless_percentage) as serverless_pct
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT 
  ct.cost_7d,
  ct.cost_30d,
  ct.cost_mtd,
  ct.cost_7d * 30 as projected_monthly_cost,
  ct.avg_tag_coverage,
  COALESCE(STRING_AGG(cbd.domain || ': $' || CAST(cbd.domain_cost as STRING), ', '), 'N/A') as top_5_cost_domains,
  COALESCE(AVG(cs.usage_pct), 0) as avg_commit_utilization,
  COALESCE(SUM(cs.remaining_capacity), 0) as total_remaining_commit,
  ef.avg_cpu_util,
  ef.avg_efficiency,
  COALESCE(op.total_savings_potential, 0) as monthly_optimization_potential,
  sa.serverless_pct,
  CASE 
    WHEN ct.cost_7d * 30 > ct.cost_30d * 1.3 THEN 'Critical - Cost Spike Detected'
    WHEN COALESCE(AVG(cs.usage_pct), 0) < 70 THEN 'Warning - Under-Utilizing Commitments'
    WHEN ef.avg_cpu_util < 40 THEN 'Warning - Resource Inefficiency'
    WHEN COALESCE(op.total_savings_potential, 0) > 10000 THEN 'High - Significant Optimization Opportunity'
    WHEN sa.serverless_pct < 30 THEN 'Medium - Low Serverless Adoption'
    ELSE 'Healthy FinOps Posture'
  END as finops_health_status,
  CASE 
    WHEN ct.cost_7d * 30 > ct.cost_30d * 1.3 THEN 'Investigate cost spike drivers and implement controls'
    WHEN COALESCE(AVG(cs.usage_pct), 0) < 70 THEN 'Increase workload on committed capacity'
    WHEN ef.avg_cpu_util < 40 THEN 'Right-size clusters and consolidate workloads'
    WHEN COALESCE(op.total_savings_potential, 0) > 10000 THEN 'Apply ML right-sizing recommendations'
    WHEN sa.serverless_pct < 30 THEN 'Migrate eligible workloads to serverless'
    WHEN ct.avg_tag_coverage < 80 THEN 'Implement tagging policy for cost allocation'
    ELSE 'Continue monitoring and optimizing'
  END as top_priority_action
FROM cost_trends ct
CROSS JOIN cost_by_domain cbd
CROSS JOIN commit_status cs
CROSS JOIN efficiency ef
CROSS JOIN optimization_potential op
CROSS JOIN serverless_adoption sa
GROUP BY 
  ct.cost_7d, ct.cost_30d, ct.cost_mtd, ct.avg_tag_coverage,
  ef.avg_cpu_util, ef.avg_efficiency, op.total_savings_potential, sa.serverless_pct;
```
**Expected Result:** Executive FinOps dashboard with cost trends, efficiency, commit utilization, and actionable optimization recommendations

---

## References

### Semantic Layer Documentation
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md)
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md)
- [Metrics Inventory](../../docs/reference/metrics-inventory.md) - Unified metrics (TVFs + MVs + Custom Metrics)
- [Semantic Layer Rationalization](../../docs/reference/semantic-layer-rationalization.md) - Design rationale

### Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md)

### Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md)
- [Genie Asset Selection Guide](../../docs/reference/genie-asset-selection-guide.md)
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md)

