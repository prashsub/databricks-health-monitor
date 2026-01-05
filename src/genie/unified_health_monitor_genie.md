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
| `get_cost_by_tag` | Tag allocation |
| `get_untagged_resources` | Tag gaps |
| `get_tag_coverage` | Tag hygiene |
| `get_cost_week_over_week` | WoW comparison |
| `get_cost_anomalies` | Anomaly detection |
| `get_cost_forecast_summary` | Forecasting |
| `get_cost_mtd_summary` | MTD summary |
| `get_commit_vs_actual` | Commit tracking |
| `get_spend_by_custom_tags` | Multi-tag analysis |
| `get_cost_growth_analysis` | Growth drivers |
| `get_cost_growth_by_period` | Period comparison |
| `get_all_purpose_cluster_cost` | AP cluster costs |

#### Reliability TVFs (12)
| Function | Purpose |
|----------|---------|
| `get_failed_jobs` | Failed jobs |
| `get_job_success_rate` | Success rates |
| `get_job_duration_percentiles` | Duration stats |
| `get_job_failure_trends` | Failure trends |
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
| `get_slow_queries` | Slow queries |
| `get_warehouse_utilization` | Warehouse metrics |
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
| `get_jobs_without_autoscaling` | No autoscale |
| `get_jobs_on_legacy_dbr` | Legacy DBR |
| `get_cluster_right_sizing_recommendations` | Right-sizing |

#### Security TVFs (10)
| Function | Purpose |
|----------|---------|
| `get_user_activity_summary` | User activity |
| `get_sensitive_table_access` | Sensitive access |
| `get_failed_actions` | Failed ops |
| `get_permission_changes` | Perm changes |
| `get_off_hours_activity` | Off-hours |
| `get_security_events_timeline` | Timeline |
| `get_ip_address_analysis` | IP analysis |
| `get_table_access_audit` | Access audit |
| `get_user_activity_patterns` | Patterns |
| `get_service_account_audit` | Service accounts |

#### Quality TVFs (7)
| Function | Purpose |
|----------|---------|
| `get_table_freshness` | Freshness |
| `get_job_data_quality_status` | Job quality |
| `get_data_freshness_by_domain` | Domain freshness |
| `get_data_quality_summary` | Quality summary |
| `get_tables_failing_quality` | Failing tables |
| `get_table_activity_status` | Activity status |
| `get_pipeline_data_lineage` | Lineage |

### ML Prediction Tables (5 - Key Anomaly & Health Tables)

| Table Name | Domain | Purpose | Key Columns |
|---|---|---|---|
| `cost_anomaly_predictions` | 💰 Cost | Detect unusual spending patterns | `anomaly_score`, `is_anomaly`, `workspace_id` |
| `job_failure_predictions` | 🔄 Reliability | Predict job failure probability | `failure_probability`, `will_fail`, `risk_factors` |
| `pipeline_health_scores` | 🔄 Reliability | Overall pipeline health (0-100) | `health_score`, `health_status`, `trend` |
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
| **List of specific items** | TVF | "Which jobs failed?" → `get_failed_jobs` |
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
| `get_failed_jobs` | `(start_date, end_date)` | Reliability |
| `get_slow_queries` | `(start_date, end_date, threshold_seconds)` | Performance |
| `get_underutilized_clusters` | `(start_date, end_date, cpu_threshold)` | Performance |
| `get_user_activity_summary` | `(user_email, start_date, end_date)` | Security |
| `get_table_freshness` | `(start_date, end_date, stale_threshold_hours)` | Quality |
| `get_cost_anomalies` | `(start_date, end_date, threshold)` | Cost |
| `get_job_success_rate` | `(start_date, end_date)` | Reliability |
| `get_warehouse_utilization` | `(start_date, end_date)` | Performance |
| `get_sensitive_table_access` | `(start_date, end_date)` | Security |

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
| `pipeline_health_scorer` | `pipeline_health_scores` | "health score" |
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
  Health scoring             → pipeline_health_scores        "health", "score"
  
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

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "What is our overall platform health?"
**Expected SQL:**
```sql
SELECT
  'Cost' as domain, MEASURE(tag_coverage_percentage) as health_score FROM ${catalog}.${gold_schema}.cost_analytics WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
UNION ALL
SELECT
  'Jobs' as domain, MEASURE(success_rate) as health_score FROM ${catalog}.${gold_schema}.job_performance WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
UNION ALL
SELECT
  'Queries' as domain, 100 - MEASURE(sla_breach_rate) as health_score FROM ${catalog}.${gold_schema}.query_performance WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Multi-domain health summary

---

### Question 2: "What is our total spend this month?"
**Expected SQL:**
```sql
SELECT MEASURE(total_cost) as total_spend
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());
```
**Expected Result:** Single cost value

---

### Question 3: "What is our job success rate this week?"
**Expected SQL:**
```sql
SELECT MEASURE(success_rate) as success_rate_pct
FROM ${catalog}.${gold_schema}.job_performance
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single percentage

---

### Question 4: "Show me failed jobs today"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_jobs(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY duration_minutes DESC
LIMIT 20;
```
**Expected Result:** Table of failed jobs

---

### Question 5: "What is our P95 query duration?"
**Expected SQL:**
```sql
SELECT MEASURE(p95_duration_ms) / 1000.0 as p95_duration_seconds
FROM ${catalog}.${gold_schema}.query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single value in seconds

---

### Question 6: "Which clusters are underutilized?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_underutilized_clusters(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  30.0
)
ORDER BY potential_savings DESC
LIMIT 20;
```
**Expected Result:** Clusters with low utilization

---

### Question 7: "Are there any security anomalies?"
**Expected SQL:**
```sql
SELECT user_identity, anomaly_score, is_anomaly, reason
FROM ${catalog}.${gold_schema}.access_anomaly_predictions
WHERE prediction_date = CURRENT_DATE() AND is_anomaly = TRUE
ORDER BY anomaly_score DESC
LIMIT 20;
```
**Expected Result:** Detected anomalous access

---

### Question 8: "Which tables are stale?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  24
)
WHERE freshness_status IN ('STALE', 'CRITICAL')
ORDER BY hours_since_update DESC
LIMIT 20;
```
**Expected Result:** Tables not updated recently

---

### Question 9: "Show me cost forecast for next month"
**Expected SQL:**
```sql
SELECT forecast_date, predicted_cost, lower_bound, upper_bound
FROM ${catalog}.${gold_schema}.cost_forecast_predictions
WHERE forecast_date >= DATE_TRUNC('month', CURRENT_DATE() + INTERVAL 1 MONTH)
  AND forecast_date < DATE_TRUNC('month', CURRENT_DATE() + INTERVAL 2 MONTHS)
ORDER BY forecast_date;
```
**Expected Result:** Daily forecasts for next month

---

### Question 10: "Which jobs are likely to fail?"
**Expected SQL:**
```sql
SELECT job_name, failure_probability, risk_factors
FROM ${catalog}.${gold_schema}.job_failure_predictions
WHERE failure_probability > 0.3
ORDER BY failure_probability DESC
LIMIT 20;
```
**Expected Result:** High-risk jobs

---

### Question 11: "Show me top 5 workspaces by cost"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_top_cost_contributors(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  5
);
```
**Expected Result:** Top 5 cost contributors

---

### Question 12: "What is our query cache hit rate?"
**Expected SQL:**
```sql
SELECT MEASURE(cache_hit_rate) as cache_hit_rate_pct
FROM ${catalog}.${gold_schema}.query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single percentage value

---

### Question 13: "Show me data quality alerts"
**Expected SQL:**
```sql
SELECT table_name, quality_score, completeness, freshness_status
FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
WHERE window_end >= CURRENT_DATE() - INTERVAL 1 DAY
  AND column_name = ':table'
  AND log_type = 'INPUT'
  AND quality_score < 80
ORDER BY quality_score ASC
LIMIT 20;
```
**Expected Result:** Tables with quality issues

---

### Question 14: "What are our top cost drivers this week?"
**Expected SQL:**
```sql
SELECT workspace_name, sku_name, MEASURE(total_cost) as cost
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY workspace_name, sku_name
ORDER BY cost DESC
LIMIT 10;
```
**Expected Result:** Top cost drivers by workspace and SKU

---

### Question 15: "Show me cluster utilization"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cluster_utilization(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY avg_cpu_percent DESC
LIMIT 15;
```
**Expected Result:** Cluster utilization metrics

---

### Question 16: "What is our tag coverage percentage?"
**Expected SQL:**
```sql
SELECT MEASURE(tag_coverage_percentage) as tag_coverage_pct
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```
**Expected Result:** Single percentage showing tag coverage

---

### Question 17: "Show me long-running queries"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_slow_queries(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  60.0
)
ORDER BY duration_seconds DESC
LIMIT 20;
```
**Expected Result:** Queries exceeding 60 seconds

---

### Question 18: "Who accessed sensitive data recently?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_sensitive_table_access(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY access_timestamp DESC
LIMIT 20;
```
**Expected Result:** Recent sensitive data access events

---

### Question 19: "What is our job retry success rate?"
**Expected SQL:**
```sql
SELECT job_name, success_rate_on_retry, total_retries
FROM ${catalog}.${gold_schema}.get_job_retry_analysis(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
WHERE total_retries > 5
ORDER BY success_rate_on_retry DESC
LIMIT 20;
```
**Expected Result:** Jobs with retry patterns and success rates

---

### Question 20: "Show me cost week-over-week comparison"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_week_over_week(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 14 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY cost_change_pct DESC
LIMIT 15;
```
**Expected Result:** Cost comparison between current and previous week

---

### Question 21: "What is the overall platform health across all domains with trend indicators and actionable insights?"
**Deep Research Complexity:** Aggregates health metrics from all 5 domains (cost, reliability, performance, security, quality) with trends and recommendations.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Cost domain health
WITH cost_health AS (
  SELECT 
    'Cost' as domain,
    MEASURE(tag_coverage_percentage) as primary_metric,
    'Tag Coverage' as metric_name
  FROM ${catalog}.${gold_schema}.cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
-- Step 2: Reliability domain health
reliability_health AS (
  SELECT 
    'Reliability' as domain,
    MEASURE(success_rate) as primary_metric,
    'Job Success Rate' as metric_name
  FROM ${catalog}.${gold_schema}.job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 3: Performance domain health
performance_health AS (
  SELECT 
    'Performance' as domain,
    100 - MEASURE(sla_breach_rate) as primary_metric,
    'SLA Compliance' as metric_name
  FROM ${catalog}.${gold_schema}.query_performance
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 4: Security domain health
security_health AS (
  SELECT 
    'Security' as domain,
    100 - (COUNT(CASE WHEN is_threat THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)) as primary_metric,
    'Threat-Free Rate' as metric_name
  FROM ${catalog}.${gold_schema}.access_anomaly_predictions
  WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 5: Quality domain health
quality_health AS (
  SELECT 
    'Quality' as domain,
    AVG(quality_score) as primary_metric,
    'Avg Quality Score' as metric_name
  FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
  WHERE window_end >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND column_name = ':table'
    AND log_type = 'INPUT'
),
-- Combine all domains
combined AS (
  SELECT * FROM cost_health
  UNION ALL SELECT * FROM reliability_health
  UNION ALL SELECT * FROM performance_health
  UNION ALL SELECT * FROM security_health
  UNION ALL SELECT * FROM quality_health
)
SELECT 
  domain,
  metric_name,
  ROUND(primary_metric, 1) as health_score,
  CASE 
    WHEN primary_metric >= 90 THEN '🟢 EXCELLENT'
    WHEN primary_metric >= 75 THEN '🟡 GOOD'
    WHEN primary_metric >= 50 THEN '🟠 NEEDS ATTENTION'
    ELSE '🔴 CRITICAL'
  END as status,
  CASE 
    WHEN domain = 'Cost' AND primary_metric < 80 THEN 'Improve tag coverage for better chargeback'
    WHEN domain = 'Reliability' AND primary_metric < 95 THEN 'Investigate failing jobs and add retries'
    WHEN domain = 'Performance' AND primary_metric < 90 THEN 'Optimize slow queries and scale warehouses'
    WHEN domain = 'Security' AND primary_metric < 95 THEN 'Review threat alerts and access patterns'
    WHEN domain = 'Quality' AND primary_metric < 80 THEN 'Fix data freshness and validation issues'
    ELSE 'Maintain current monitoring'
  END as recommendation
FROM combined
ORDER BY primary_metric ASC;
```
**Expected Result:** Platform health dashboard across all domains with status and recommendations.

---

### Question 22: "What are the top cross-domain issues impacting multiple areas of the platform, and what's the root cause analysis?"
**Deep Research Complexity:** Correlates issues across domains to identify common root causes (e.g., a failing job causing cost spikes and data quality issues).

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify high-cost workspaces
WITH cost_issues AS (
  SELECT 
    workspace_name,
    SUM(usage_cost) as total_cost,
    'COST' as domain
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY workspace_name
  HAVING SUM(usage_cost) > (SELECT AVG(total) * 2 FROM (SELECT SUM(usage_cost) as total FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS GROUP BY workspace_name))
),
-- Step 2: Identify reliability issues
reliability_issues AS (
  SELECT 
    workspace_id as workspace_name,
    COUNT(CASE WHEN result_state = 'FAILED' THEN 1 END) as failure_count,
    'RELIABILITY' as domain
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY workspace_id
  HAVING COUNT(CASE WHEN result_state = 'FAILED' THEN 1 END) > 10
),
-- Step 3: Identify security issues
security_issues AS (
  SELECT 
    workspace_id as workspace_name,
    COUNT(*) as threat_count,
    'SECURITY' as domain
  FROM ${catalog}.${gold_schema}.access_anomaly_predictions
  WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND is_threat = TRUE
  GROUP BY workspace_id
  HAVING COUNT(*) > 0
),
-- Step 4: Find workspaces with multi-domain issues
multi_domain_issues AS (
  SELECT 
    COALESCE(c.workspace_name, r.workspace_name, s.workspace_name) as workspace,
    CASE WHEN c.workspace_name IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN r.workspace_name IS NOT NULL THEN 1 ELSE 0 END +
    CASE WHEN s.workspace_name IS NOT NULL THEN 1 ELSE 0 END as domains_affected,
    COALESCE(c.total_cost, 0) as cost_impact,
    COALESCE(r.failure_count, 0) as reliability_impact,
    COALESCE(s.threat_count, 0) as security_impact
  FROM cost_issues c
  FULL OUTER JOIN reliability_issues r ON c.workspace_name = r.workspace_name
  FULL OUTER JOIN security_issues s ON COALESCE(c.workspace_name, r.workspace_name) = s.workspace_name
)
SELECT 
  workspace,
  domains_affected,
  ROUND(cost_impact, 2) as cost_usd,
  reliability_impact as failed_jobs,
  security_impact as threat_alerts,
  CASE 
    WHEN domains_affected >= 3 THEN '🔴 CRITICAL: Multi-domain impact - investigate immediately'
    WHEN domains_affected = 2 THEN '🟠 HIGH: Cross-domain correlation detected'
    ELSE '🟡 MEDIUM: Single domain issue'
  END as severity,
  CASE 
    WHEN reliability_impact > 20 AND cost_impact > 1000 THEN 'ROOT CAUSE: Job failures driving costs - fix jobs first'
    WHEN security_impact > 5 AND cost_impact > 500 THEN 'ROOT CAUSE: Potential unauthorized activity - security review'
    WHEN reliability_impact > 10 THEN 'ROOT CAUSE: Job reliability - add retries and monitoring'
    ELSE 'INVESTIGATE: Manual root cause analysis needed'
  END as root_cause_hypothesis
FROM multi_domain_issues
WHERE domains_affected >= 2
ORDER BY domains_affected DESC, cost_impact DESC
LIMIT 15;
```
**Expected Result:** Cross-domain issues with correlation analysis and root cause hypotheses.

---

### Question 23: "What would be the total ROI if we addressed all ML-identified optimization opportunities across cost, performance, and reliability?"
**Deep Research Complexity:** Aggregates all ML recommendations across domains to calculate total potential ROI from optimization.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Cost optimization ROI
WITH cost_roi AS (
  SELECT 
    'Cost Optimization' as category,
    COUNT(*) as recommendations,
    SUM(potential_savings_usd) as monthly_savings,
    SUM(potential_savings_usd) * 12 as annual_savings,
    AVG(confidence) as avg_confidence
  FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations
  WHERE potential_savings_usd > 0
),
-- Step 2: Performance optimization ROI (time saved = cost saved)
performance_roi AS (
  SELECT 
    'Performance Optimization' as category,
    COUNT(*) as recommendations,
    SUM(expected_time_saved_seconds) / 3600 * 50 as monthly_savings,  -- $50/hour
    SUM(expected_time_saved_seconds) / 3600 * 50 * 12 as annual_savings,
    AVG(confidence) as avg_confidence
  FROM ${catalog}.${gold_schema}.query_optimization_recommendations
  WHERE expected_time_saved_seconds > 0
),
-- Step 3: Reliability optimization ROI (prevented failures)
reliability_roi AS (
  SELECT 
    'Reliability Improvement' as category,
    COUNT(*) as recommendations,
    SUM(expected_failure_cost * failure_probability) as monthly_savings,
    SUM(expected_failure_cost * failure_probability) * 12 as annual_savings,
    AVG(1 - failure_probability) as avg_confidence
  FROM ${catalog}.${gold_schema}.job_failure_predictions
  WHERE failure_probability > 0.3
),
-- Combine all ROI
combined_roi AS (
  SELECT * FROM cost_roi
  UNION ALL SELECT * FROM performance_roi
  UNION ALL SELECT * FROM reliability_roi
)
SELECT 
  category,
  recommendations as actionable_items,
  ROUND(monthly_savings, 2) as monthly_savings_usd,
  ROUND(annual_savings, 2) as annual_savings_usd,
  ROUND(avg_confidence * 100, 1) as confidence_pct,
  CASE 
    WHEN annual_savings > 100000 THEN '🔴 HIGH ROI: Priority implementation'
    WHEN annual_savings > 50000 THEN '🟠 MEDIUM ROI: Schedule implementation'
    ELSE '🟢 LOW ROI: Opportunistic'
  END as priority
FROM combined_roi
UNION ALL
SELECT 
  'TOTAL ROI' as category,
  SUM(recommendations) as actionable_items,
  ROUND(SUM(monthly_savings), 2) as monthly_savings_usd,
  ROUND(SUM(annual_savings), 2) as annual_savings_usd,
  ROUND(AVG(avg_confidence) * 100, 1) as confidence_pct,
  '📊 TOTAL' as priority
FROM combined_roi
ORDER BY annual_savings_usd DESC;
```
**Expected Result:** Total ROI breakdown across all optimization categories with confidence levels and implementation priorities.

---

### Question 24: "What are the emerging trends across all platform metrics that require attention before they become critical issues?"
**Deep Research Complexity:** Analyzes drift metrics and trends across all domains to identify emerging issues before they become critical.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Cost trend analysis
WITH cost_trends AS (
  SELECT 
    'Cost' as domain,
    'Total Spend' as metric,
    drift_value as trend_value,
    consecutive_drift_count as trend_duration,
    CASE WHEN drift_value > 0.1 THEN 'INCREASING' WHEN drift_value < -0.1 THEN 'DECREASING' ELSE 'STABLE' END as direction
  FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window_end >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 2: Reliability trend analysis
reliability_trends AS (
  SELECT 
    'Reliability' as domain,
    'Failure Rate' as metric,
    drift_value as trend_value,
    consecutive_drift_count as trend_duration,
    CASE WHEN drift_value > 0.05 THEN 'INCREASING' WHEN drift_value < -0.05 THEN 'DECREASING' ELSE 'STABLE' END as direction
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window_end >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 3: Performance trend analysis
performance_trends AS (
  SELECT 
    'Performance' as domain,
    'Query Duration' as metric,
    drift_value as trend_value,
    consecutive_drift_count as trend_duration,
    CASE WHEN drift_value > 0.1 THEN 'DEGRADING' WHEN drift_value < -0.1 THEN 'IMPROVING' ELSE 'STABLE' END as direction
  FROM ${catalog}.${gold_schema}.fact_query_history_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window_end >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 4: Security trend analysis
security_trends AS (
  SELECT 
    'Security' as domain,
    'Threat Events' as metric,
    drift_value as trend_value,
    consecutive_drift_count as trend_duration,
    CASE WHEN drift_value > 0.05 THEN 'INCREASING' WHEN drift_value < -0.05 THEN 'DECREASING' ELSE 'STABLE' END as direction
  FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window_end >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Combine all trends
all_trends AS (
  SELECT * FROM cost_trends
  UNION ALL SELECT * FROM reliability_trends
  UNION ALL SELECT * FROM performance_trends
  UNION ALL SELECT * FROM security_trends
)
SELECT 
  domain,
  metric,
  direction,
  ROUND(trend_value * 100, 1) as change_pct,
  trend_duration as weeks_trending,
  CASE 
    WHEN direction IN ('INCREASING', 'DEGRADING') AND ABS(trend_value) > 0.2 THEN '🔴 CRITICAL: Immediate attention required'
    WHEN direction IN ('INCREASING', 'DEGRADING') AND trend_duration >= 3 THEN '🟠 WARNING: Sustained negative trend'
    WHEN direction IN ('DECREASING', 'IMPROVING') THEN '🟢 POSITIVE: Trend improving'
    ELSE '🟡 MONITOR: Stable but watch closely'
  END as alert_level,
  CASE 
    WHEN domain = 'Cost' AND direction = 'INCREASING' THEN 'Review spend by SKU and implement cost controls'
    WHEN domain = 'Reliability' AND direction = 'INCREASING' THEN 'Investigate new failure patterns and add retry logic'
    WHEN domain = 'Performance' AND direction = 'DEGRADING' THEN 'Scale resources and optimize slow queries'
    WHEN domain = 'Security' AND direction = 'INCREASING' THEN 'Review access patterns and threat alerts'
    ELSE 'Continue monitoring'
  END as recommended_action
FROM all_trends
WHERE direction != 'STABLE'
ORDER BY 
  CASE WHEN direction IN ('INCREASING', 'DEGRADING') THEN 1 ELSE 2 END,
  ABS(trend_value) DESC;
```
**Expected Result:** Emerging trends across all domains with alert levels and recommended actions.

---

### Question 25: "Create an executive summary of platform health including key metrics, active incidents, ML predictions, and recommended priorities for the leadership team."
**Deep Research Complexity:** Synthesizes data from all sources to create a comprehensive executive summary with business context.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Current month spend and trend
WITH monthly_spend AS (
  SELECT 
    SUM(CASE WHEN usage_date >= DATE_TRUNC('month', CURRENT_DATE()) THEN usage_cost ELSE 0 END) as mtd_spend,
    SUM(CASE WHEN usage_date >= DATE_TRUNC('month', CURRENT_DATE() - INTERVAL 1 MONTH) 
             AND usage_date < DATE_TRUNC('month', CURRENT_DATE()) THEN usage_cost ELSE 0 END) as last_month_spend
  FROM ${catalog}.${gold_schema}.fact_usage
),
-- Step 2: Active incidents
active_incidents AS (
  SELECT 
    COUNT(CASE WHEN result_state = 'FAILED' THEN 1 END) as failed_jobs_24h,
    COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) as anomalies_detected
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline j
  FULL OUTER JOIN ${catalog}.${gold_schema}.cost_anomaly_predictions c 
    ON j.run_date = c.prediction_date
  WHERE j.run_date >= CURRENT_DATE() - INTERVAL 1 DAY
     OR c.prediction_date >= CURRENT_DATE() - INTERVAL 1 DAY
),
-- Step 3: Key health metrics
health_metrics AS (
  SELECT 
    (SELECT MEASURE(success_rate) FROM ${catalog}.${gold_schema}.job_performance 
     WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS) as job_success_rate,
    (SELECT MEASURE(tag_coverage_percentage) FROM ${catalog}.${gold_schema}.cost_analytics 
     WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS) as tag_coverage,
    (SELECT 100 - MEASURE(sla_breach_rate) FROM ${catalog}.${gold_schema}.query_performance 
     WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS) as query_sla_compliance
),
-- Step 4: ML predictions summary
ml_predictions AS (
  SELECT 
    (SELECT COUNT(*) FROM ${catalog}.${gold_schema}.job_failure_predictions 
     WHERE failure_probability > 0.5 AND prediction_date = CURRENT_DATE()) as high_risk_jobs,
    (SELECT SUM(potential_savings_usd) FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations) as optimization_opportunity
),
-- Step 5: Top priorities
executive_summary AS (
  SELECT 
    'FINANCIAL' as category,
    ROUND(s.mtd_spend, 0) as current_value,
    ROUND((s.mtd_spend - s.last_month_spend) / NULLIF(s.last_month_spend, 0) * 100, 1) as trend_pct,
    'USD' as unit
  FROM monthly_spend s
  UNION ALL
  SELECT 'RELIABILITY', ROUND(h.job_success_rate, 1), NULL, '%' FROM health_metrics h
  UNION ALL
  SELECT 'PERFORMANCE', ROUND(h.query_sla_compliance, 1), NULL, '%' FROM health_metrics h
  UNION ALL
  SELECT 'GOVERNANCE', ROUND(h.tag_coverage, 1), NULL, '%' FROM health_metrics h
  UNION ALL
  SELECT 'INCIDENTS', i.failed_jobs_24h, i.anomalies_detected, 'count' FROM active_incidents i
  UNION ALL
  SELECT 'AT_RISK_JOBS', p.high_risk_jobs, NULL, 'count' FROM ml_predictions p
  UNION ALL
  SELECT 'SAVINGS_OPPORTUNITY', ROUND(p.optimization_opportunity, 0), NULL, 'USD' FROM ml_predictions p
)
SELECT 
  category,
  current_value,
  COALESCE(CAST(trend_pct AS STRING), '-') as trend,
  unit,
  CASE 
    WHEN category = 'FINANCIAL' AND trend_pct > 20 THEN '🔴 Cost increasing significantly'
    WHEN category = 'RELIABILITY' AND current_value < 95 THEN '🟠 Job reliability needs attention'
    WHEN category = 'PERFORMANCE' AND current_value < 90 THEN '🟠 Query SLAs being breached'
    WHEN category = 'GOVERNANCE' AND current_value < 80 THEN '🟡 Improve tagging for chargeback'
    WHEN category = 'INCIDENTS' AND current_value > 10 THEN '🔴 Active incidents require attention'
    WHEN category = 'AT_RISK_JOBS' AND current_value > 5 THEN '🟠 ML predicts job failures - take action'
    WHEN category = 'SAVINGS_OPPORTUNITY' AND current_value > 10000 THEN '💰 Significant savings available'
    ELSE '✅ On track'
  END as executive_insight
FROM executive_summary
ORDER BY 
  CASE category 
    WHEN 'INCIDENTS' THEN 1 
    WHEN 'AT_RISK_JOBS' THEN 2
    WHEN 'FINANCIAL' THEN 3
    WHEN 'RELIABILITY' THEN 4
    WHEN 'PERFORMANCE' THEN 5
    WHEN 'GOVERNANCE' THEN 6
    WHEN 'SAVINGS_OPPORTUNITY' THEN 7
  END;
```
**Expected Result:** Executive summary with key metrics, trends, incidents, ML predictions, and actionable insights for leadership.

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

