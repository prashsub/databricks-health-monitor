# Unified Databricks Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Databricks Health Monitor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Comprehensive natural language interface for Databricks platform health monitoring. Enables leadership, platform administrators, and SREs to query costs, job reliability, query performance, cluster efficiency, security audit, and data quality - all in one unified space. Powered by 10 Metric Views, 60 Table-Valued Functions, 25 ML Models, and 8 Lakehouse Monitors with 87 custom metrics.

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

### Metric Views (10 Total - PRIMARY Source)

| Metric View | Domain | Purpose | Key Measures |
|-------------|--------|---------|--------------|
| `cost_analytics` | 💰 Cost | Comprehensive cost metrics | total_cost, total_dbus, tag_coverage_percentage |
| `commit_tracking` | 💰 Cost | Budget tracking | commit_amount, consumed_amount, burn_rate |
| `job_performance` | 🔄 Reliability | Job execution | success_rate, failure_rate, p95_duration |
| `query_performance` | ⚡ Performance | Query metrics | avg_duration, p95_duration, sla_breach_rate |
| `cluster_utilization` | ⚡ Performance | Resource metrics | avg_cpu, avg_memory, total_node_hours |
| `cluster_efficiency` | ⚡ Performance | Efficiency metrics | p95_cpu, saturation_hours, idle_hours |
| `security_events` | 🔒 Security | Audit metrics | total_events, failed_events, high_risk_events |
| `governance_analytics` | 🔒 Security | Lineage metrics | read_events, write_events, active_tables |
| `data_quality` | ✅ Quality | Quality metrics | quality_score, completeness, validity |
| `ml_intelligence` | 🤖 ML | Inference metrics | prediction_count, accuracy, drift_score |

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

### ML Prediction Tables (25 Models)

#### Cost ML (6)
- `cost_anomaly_predictions` - Anomaly detection
- `cost_forecast_predictions` - 30-day forecast
- `tag_recommendations` - Tag suggestions
- `user_cost_segments` - User clustering
- `migration_recommendations` - AP migration
- `budget_alert_predictions` - Budget alerts

#### Performance ML (7)
- `job_duration_predictions` - Duration estimates
- `query_optimization_classifications` - Optimization flags
- `query_optimization_recommendations` - Optimization suggestions
- `cache_hit_predictions` - Cache predictions
- `cluster_capacity_recommendations` - Capacity planning
- `cluster_rightsizing_recommendations` - Right-sizing
- `dbr_migration_risk_scores` - Migration risk

#### Reliability ML (5)
- `job_failure_predictions` - Failure probability
- `retry_success_predictions` - Retry success
- `pipeline_health_scores` - Health scores
- `incident_impact_predictions` - Blast radius
- `self_healing_recommendations` - Self-healing

#### Security ML (4)
- `access_anomaly_predictions` - Access anomalies
- `user_risk_scores` - User risk
- `access_classifications` - Access classification
- `off_hours_baseline_predictions` - Baseline

#### Quality ML (3)
- `quality_anomaly_predictions` - Quality anomalies
- `quality_trend_predictions` - Quality forecast
- `freshness_alert_predictions` - Freshness alerts

### Lakehouse Monitoring Tables (16)

| Table | Domain | Metrics |
|-------|--------|---------|
| `fact_usage_profile_metrics` | Cost | 13 metrics |
| `fact_usage_drift_metrics` | Cost | Drift |
| `fact_job_run_timeline_profile_metrics` | Reliability | 14 metrics |
| `fact_job_run_timeline_drift_metrics` | Reliability | Drift |
| `fact_query_history_profile_metrics` | Performance | 13 metrics |
| `fact_query_history_drift_metrics` | Performance | Drift |
| `fact_node_timeline_profile_metrics` | Performance | 11 metrics |
| `fact_node_timeline_drift_metrics` | Performance | Drift |
| `fact_audit_logs_profile_metrics` | Security | 14 metrics |
| `fact_audit_logs_drift_metrics` | Security | Drift |
| `fact_information_schema_table_storage_profile_metrics` | Quality | 10 metrics |
| `fact_table_lineage_profile_metrics` | Quality | 12 metrics |
| `fact_table_lineage_drift_metrics` | Quality | Drift |
| `cost_anomaly_predictions_profile_metrics` | ML | Inference metrics |
| `cost_anomaly_predictions_drift_metrics` | ML | Drift |

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

---

## ████ SECTION E: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a comprehensive Databricks platform health analyst. Follow these rules:

1. **Route by Domain:** Cost→cost_analytics, Jobs→job_performance, Query→query_performance, Cluster→cluster_utilization, Security→security_events, Quality→data_quality
2. **TVFs for Specific:** Use TVFs for parameterized queries
3. **ML for Predictions:** Use ML tables for forecasts, anomalies, risk scores
4. **Date Default:** Cost=30 days, Jobs/Queries=7 days, Security=24 hours
5. **Aggregation:** SUM for totals, AVG for averages, COUNT for volumes
6. **Sorting:** DESC by primary metric unless specified
7. **Limits:** Top 10-20 for ranking queries
8. **Currency:** USD with 2 decimals
9. **Percentages:** Show as % with 1 decimal
10. **Health Score:** 0-25=Critical, 26-50=Poor, 51-75=Fair, 76-90=Good, 91-100=Excellent
11. **Anomalies:** For "anomalies" → query *_anomaly_predictions tables
12. **Forecasts:** For "forecast/predict" → query *_forecast_predictions tables
13. **Risk:** For "risk score" → query *_risk_scores tables
14. **Context:** Explain results in business terms
15. **Cross-Domain:** Start with metric view, drill down with TVFs
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION F: TABLE-VALUED FUNCTIONS ████

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

## ████ SECTION G: BENCHMARK QUESTIONS WITH SQL ████

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

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All 10 metric views, 60 TVFs, 25 ML tables, 16 monitoring tables | ✅ |
| **E. General Instructions** | 16 lines (≤20) | ✅ |
| **F. TVFs** | Domain routing + top 10 signatures | ✅ |
| **G. Benchmark Questions** | 12 with SQL answers | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🌐 **Unified** (All Domains)

---

## Total Asset Summary

| Asset Type | Count |
|------------|-------|
| Metric Views | 10 |
| Table-Valued Functions | 60 |
| ML Prediction Tables | 25 |
| Lakehouse Monitoring Tables | 16 |
| Custom Metrics | 87 |
| **Total Semantic Assets** | 198 |

