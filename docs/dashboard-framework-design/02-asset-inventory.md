# Asset Inventory

## Complete Inventory of Assets Available for Dashboard Integration

This document provides a comprehensive inventory of all assets available for dashboard integration, including ML Models, Lakehouse Monitors with Custom Metrics, Metric Views, and TVFs.

> **Source of Truth:** This inventory is aligned with:
> - ML Models: [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)
> - Custom Metrics: [03-custom-metrics.md](../lakehouse-monitoring-design/03-custom-metrics.md)

---

## 1. ML Models Inventory (25 Models)

### Summary by Domain

| Domain | Models | Primary Use Cases |
|--------|--------|-------------------|
| **COST** | 6 | Anomaly detection, forecasting, optimization |
| **SECURITY** | 4 | Threat detection, behavior analysis |
| **PERFORMANCE** | 7 | Query optimization, capacity planning |
| **RELIABILITY** | 5 | Failure prediction, duration forecasting |
| **QUALITY** | 3 | Data drift, schema changes |

---

### 1.1 Cost Domain Models (6)

| # | Model | Algorithm | Type | Output Table | Dashboard Use Case |
|---|-------|-----------|------|--------------|-------------------|
| 1 | `cost_anomaly_detector` | Isolation Forest | Anomaly Detection | `cost_anomaly_predictions` | Alert on unusual spend patterns |
| 2 | `budget_forecaster` | Gradient Boosting | Regression | `budget_forecast_predictions` | Predict end-of-month/year spend |
| 3 | `job_cost_optimizer` | Gradient Boosting | Regression | `job_cost_optimizations` | Identify costly jobs to optimize |
| 4 | `chargeback_attribution` | Gradient Boosting | Regression | `chargeback_attributions` | Attribution for cost allocation |
| 5 | `commitment_recommender` | Gradient Boosting | Regression | `commitment_recommendations` | Recommend optimal commit amounts |
| 6 | `tag_recommender` | Random Forest + TF-IDF | Multi-class | `tag_recommendations` | Suggest tags for untagged resources |

**Dashboard Integration:**
```sql
-- Cost Anomaly Detection
SELECT prediction_date, workspace_id, anomaly_score, is_anomaly, daily_cost
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND is_anomaly = 1
ORDER BY anomaly_score ASC

-- Budget Forecast
SELECT forecast_date, predicted_daily_cost, confidence_lower, confidence_upper
FROM ${catalog}.${gold_schema}.budget_forecast_predictions
WHERE forecast_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), 90)
ORDER BY forecast_date
```

---

### 1.2 Security Domain Models (4)

| # | Model | Algorithm | Type | Output Table | Dashboard Use Case |
|---|-------|-----------|------|--------------|-------------------|
| 7 | `security_threat_detector` | Isolation Forest | Anomaly Detection | `security_threat_predictions` | Identify security threats |
| 8 | `access_pattern_analyzer` | XGBoost | Binary Classification | `access_pattern_predictions` | Detect unusual access patterns |
| 9 | `compliance_risk_classifier` | Random Forest | Multi-class | `compliance_risk_predictions` | Risk classification |
| 10 | `permission_recommender` | Random Forest | Multi-class | `permission_recommendations` | Suggest permission optimizations |

**Dashboard Integration:**
```sql
-- Security Threat Detection
SELECT prediction_date, user_id, threat_score, threat_type, is_threat
FROM ${catalog}.${gold_schema}.security_threat_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND threat_score > 0.7
ORDER BY threat_score DESC

-- Access Pattern Anomalies
SELECT user_id, anomaly_probability, access_pattern_type, detection_date
FROM ${catalog}.${gold_schema}.access_pattern_predictions
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND anomaly_probability > 0.8
```

---

### 1.3 Performance Domain Models (7)

| # | Model | Algorithm | Type | Output Table | Dashboard Use Case |
|---|-------|-----------|------|--------------|-------------------|
| 11 | `query_performance_forecaster` | Gradient Boosting | Regression | `query_performance_forecasts` | Predict query durations |
| 12 | `warehouse_optimizer` | XGBoost | Multi-class | `warehouse_optimizations` | Warehouse sizing recs |
| 13 | `cache_hit_predictor` | XGBoost | Binary Classification | `cache_hit_predictions` | Cache effectiveness |
| 14 | `query_optimization_recommender` | XGBoost | Multi-label | `query_optimization_recs` | Query tuning suggestions |
| 15 | `cluster_sizing_recommender` | Gradient Boosting | Regression | `cluster_sizing_recs` | Right-sizing recommendations |
| 16 | `cluster_capacity_planner` | Gradient Boosting | Regression | `cluster_capacity_plans` | Capacity forecasts |
| 17 | `regression_detector` | Isolation Forest | Anomaly Detection | `query_regression_alerts` | Performance regression alerts |

**Dashboard Integration:**
```sql
-- Cluster Sizing Recommendations
SELECT cluster_id, current_node_type, recommended_node_type, 
       potential_savings_pct, recommendation_reason
FROM ${catalog}.${gold_schema}.cluster_sizing_recs
WHERE recommendation_date = CURRENT_DATE()
  AND potential_savings_pct > 10
ORDER BY potential_savings_pct DESC

-- Query Regressions
SELECT query_id, warehouse_id, baseline_p95_ms, current_p95_ms, 
       regression_pct, detection_date
FROM ${catalog}.${gold_schema}.query_regression_alerts
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND regression_pct > 50
```

---

### 1.4 Reliability Domain Models (5)

| # | Model | Algorithm | Type | Output Table | Dashboard Use Case |
|---|-------|-----------|------|--------------|-------------------|
| 18 | `job_failure_predictor` | XGBoost | Binary Classification | `job_failure_predictions` | Predict job failures |
| 19 | `job_duration_forecaster` | Gradient Boosting | Regression | `job_duration_forecasts` | Duration predictions |
| 20 | `sla_breach_predictor` | XGBoost | Binary Classification | `sla_breach_predictions` | SLA risk predictions |
| 21 | `pipeline_health_scorer` | Gradient Boosting | Regression | `pipeline_health_scores` | Pipeline health metrics |
| 22 | `retry_success_predictor` | XGBoost | Binary Classification | `retry_success_predictions` | Retry recommendation |

**Dashboard Integration:**
```sql
-- Job Failure Predictions
SELECT job_id, job_name, failure_probability, risk_factors, 
       recommended_actions, prediction_date
FROM ${catalog}.${gold_schema}.job_failure_predictions
WHERE prediction_date = CURRENT_DATE()
  AND failure_probability > 0.5
ORDER BY failure_probability DESC

-- SLA Breach Predictions
SELECT job_id, sla_threshold_minutes, predicted_duration_minutes,
       breach_probability, prediction_date
FROM ${catalog}.${gold_schema}.sla_breach_predictions
WHERE prediction_date = CURRENT_DATE()
  AND breach_probability > 0.5
```

---

### 1.5 Quality Domain Models (3)

| # | Model | Algorithm | Type | Output Table | Dashboard Use Case |
|---|-------|-----------|------|--------------|-------------------|
| 23 | `data_drift_detector` | Isolation Forest | Anomaly Detection | `data_drift_alerts` | Data drift alerts |
| 24 | `schema_change_predictor` | XGBoost | Binary Classification | `schema_change_predictions` | Change predictions |
| 25 | `schema_evolution_predictor` | Random Forest | Multi-class | `schema_evolution_predictions` | Schema change alerts |

**Dashboard Integration:**
```sql
-- Data Drift Detection
SELECT table_name, drift_score, drift_type, affected_columns, detection_date
FROM ${catalog}.${gold_schema}.data_drift_alerts
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND drift_score > 0.3
ORDER BY drift_score DESC

-- Schema Change Predictions
SELECT table_name, change_probability, predicted_change_type, 
       affected_columns, prediction_date
FROM ${catalog}.${gold_schema}.schema_change_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND change_probability > 0.7
```

---

## 2. Lakehouse Monitors - Custom Metrics (~155 Metrics)

### Summary by Monitor

| Monitor | Source Table | AGGREGATE | DERIVED | DRIFT | Total |
|---------|--------------|-----------|---------|-------|-------|
| Cost Monitor | `fact_usage` | 18 | 12 | 3 | **35** |
| Job Monitor | `fact_job_run_timeline` | 25 | 17 | 8 | **50** |
| Query Monitor | `fact_query_history` | 10 | 3 | 1 | **14** |
| Cluster Monitor | `fact_node_timeline` | 9 | 1 | 0 | **10** |
| Security Monitor | `fact_audit_logs` | 6 | 3 | 1 | **13** |
| Quality Monitor | `fact_data_quality_results` | 7 | 2 | 1 | **10** |
| Governance Monitor | `fact_governance_metrics` | 5 | 5 | 1 | **11** |
| Inference Monitor | `fact_model_serving` | 8 | 4 | 2 | **15** |
| **Total** | | **88** | **47** | **17** | **~155** |

---

### 2.1 Cost Monitor Metrics (35 metrics)

**Source:** `fact_usage` → `fact_usage_profile_metrics`, `fact_usage_drift_metrics`

#### Core Cost Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `total_daily_cost` | `SUM(list_cost)` | KPI, Trend Chart |
| `total_daily_dbu` | `SUM(usage_quantity)` | KPI |
| `avg_cost_per_dbu` | `AVG(list_price)` | KPI |
| `record_count` | `COUNT(*)` | Data completeness |
| `distinct_workspaces` | `COUNT(DISTINCT workspace_id)` | Scope indicator |
| `distinct_skus` | `COUNT(DISTINCT sku_name)` | Product mix |
| `null_sku_count` | `COUNT where sku_name IS NULL` | Data quality |
| `null_price_count` | `COUNT where list_price IS NULL` | Data quality |

#### Tag Hygiene Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `tagged_record_count` | `COUNT where is_tagged = TRUE` | Tag compliance |
| `untagged_record_count` | `COUNT where is_tagged = FALSE` | Tag gap |
| `tagged_cost_total` | `SUM(list_cost) where is_tagged` | Pie Chart |
| `untagged_cost_total` | `SUM(list_cost) where NOT is_tagged` | Pie Chart |

#### SKU Breakdown Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `jobs_compute_cost` | `SUM(list_cost) for JOBS SKUs` | Bar Chart |
| `sql_compute_cost` | `SUM(list_cost) for SQL SKUs` | Bar Chart |
| `all_purpose_cost` | `SUM(list_cost) for ALL_PURPOSE SKUs` | Bar Chart |
| `serverless_cost` | `SUM(list_cost) where is_serverless` | Pie Chart |
| `dlt_cost` | `SUM(list_cost) for DLT SKUs` | Bar Chart |
| `model_serving_cost` | `SUM(list_cost) for MODEL_SERVING SKUs` | Bar Chart |

#### Workflow Advisor Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `jobs_on_all_purpose_cost` | Jobs cost on ALL_PURPOSE clusters | Savings opportunity |
| `jobs_on_all_purpose_count` | Job count on ALL_PURPOSE clusters | Optimization candidates |
| `potential_job_cluster_savings` | Estimated 40% savings | KPI, Alert |

#### Cost Derived Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| `null_sku_rate` | `null_sku_count / record_count * 100` | < 1% |
| `null_price_rate` | `null_price_count / record_count * 100` | 0% |
| `tag_coverage_pct` | `tagged_cost / total_cost * 100` | > 90% |
| `untagged_usage_pct` | `untagged_cost / total_cost * 100` | < 10% |
| `serverless_ratio` | `serverless_cost / total_cost * 100` | Growing |
| `jobs_cost_share` | `jobs_cost / total_cost * 100` | - |
| `sql_cost_share` | `sql_cost / total_cost * 100` | - |
| `all_purpose_cost_ratio` | `all_purpose_cost / total_cost * 100` | Decreasing |
| `jobs_on_all_purpose_ratio` | `jobs_on_AP_cost / total_jobs_cost * 100` | < 5% |
| `dlt_cost_share` | `dlt_cost / total_cost * 100` | - |
| `model_serving_cost_share` | `model_serving_cost / total_cost * 100` | - |

#### Cost Drift Metrics

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `cost_drift_pct` | `((current - baseline) / baseline) * 100` | > 10% |
| `dbu_drift_pct` | `((current - baseline) / baseline) * 100` | > 15% |
| `tag_coverage_drift` | `current_coverage - baseline_coverage` | < -5% |

---

### 2.2 Job Monitor Metrics (50 metrics)

**Source:** `fact_job_run_timeline` → `fact_job_run_timeline_profile_metrics`

#### Core Reliability Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `total_runs` | `COUNT(*)` | KPI, Trend |
| `success_count` | `SUM(CASE WHEN is_success = TRUE...)` | KPI |
| `failure_count` | `SUM(CASE WHEN result_state IN ('FAILED', 'ERROR')...)` | KPI |
| `timeout_count` | `SUM(CASE WHEN result_state = 'TIMED_OUT'...)` | Alert |
| `cancelled_count` | `SUM(CASE WHEN result_state = 'CANCELED'...)` | Alert |
| `skipped_count` | `SUM(CASE WHEN result_state = 'SKIPPED'...)` | Alert |
| `upstream_failed_count` | `SUM(CASE WHEN result_state = 'UPSTREAM_FAILED'...)` | Alert |
| `distinct_jobs` | `COUNT(DISTINCT job_id)` | Scope |
| `distinct_runs` | `COUNT(DISTINCT run_id)` | Volume |

#### Trigger Breakdown (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `scheduled_runs` | `COUNT where trigger_type = 'SCHEDULE'` | Pie Chart |
| `manual_runs` | `COUNT where trigger_type = 'MANUAL'` | Pie Chart |
| `retry_runs` | `COUNT where trigger_type = 'RETRY'` | Alert |

#### Termination Breakdown (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `user_cancelled_count` | `COUNT where termination_code = 'USER_CANCELED'` | Table |
| `internal_error_count` | `COUNT where termination_code = 'INTERNAL_ERROR'` | Alert |
| `driver_error_count` | `COUNT where termination_code = 'DRIVER_ERROR'` | Alert |

#### Duration Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `avg_duration_minutes` | `AVG(run_duration_minutes)` | KPI |
| `total_duration_minutes` | `SUM(run_duration_minutes)` | KPI |
| `max_duration_minutes` | `MAX(run_duration_minutes)` | Alert |
| `min_duration_minutes` | `MIN(run_duration_minutes)` | - |
| `p50_duration_minutes` | `PERCENTILE(0.50)` | Box Plot |
| `p90_duration_minutes` | `PERCENTILE(0.90)` | SLA |
| `p95_duration_minutes` | `PERCENTILE(0.95)` | KPI, SLA |
| `p99_duration_minutes` | `PERCENTILE(0.99)` | Alert |
| `stddev_duration_minutes` | `STDDEV(run_duration_minutes)` | Stability |
| `long_running_count` | `COUNT where duration > 60 min` | Alert |
| `very_long_running_count` | `COUNT where duration > 240 min` | Alert |

#### Job Derived Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| `success_rate` | `success_count / total_runs * 100` | > 95% |
| `failure_rate` | `failure_count / total_runs * 100` | < 3% |
| `timeout_rate` | `timeout_count / total_runs * 100` | < 1% |
| `cancellation_rate` | `cancelled_count / total_runs * 100` | < 2% |
| `repair_rate` | `retry_runs / distinct_runs * 100` | < 5% |
| `scheduled_ratio` | `scheduled_runs / total_runs * 100` | > 80% |
| `avg_runs_per_job` | `total_runs / distinct_jobs` | - |
| `skipped_rate` | `skipped_count / total_runs * 100` | < 1% |
| `upstream_failed_rate` | `upstream_failed / total_runs * 100` | < 2% |
| `duration_cv` | `stddev / avg duration` | < 0.5 |
| `long_running_rate` | `long_running_count / total_runs * 100` | < 5% |
| `very_long_running_rate` | `very_long_running_count / total_runs * 100` | < 1% |
| `duration_skew_ratio` | `p90_duration / p50_duration` | < 2 |
| `tail_ratio` | `p99_duration / p95_duration` | < 1.5 |

#### Job Drift Metrics

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `success_rate_drift` | `current - baseline success_rate` | < -5% |
| `failure_count_drift` | `current - baseline failure_count` | > 10 |
| `run_count_drift_pct` | `((current - baseline) / baseline) * 100` | > 20% |
| `duration_drift_pct` | `((current - baseline) / baseline) * 100` | > 15% |
| `p99_duration_drift_pct` | `((current - baseline) / baseline) * 100` | > 20% |
| `p90_duration_drift_pct` | `((current - baseline) / baseline) * 100` | > 15% |
| `duration_cv_drift` | `current - baseline CV` | > 0.2 |
| `long_running_drift` | `current - baseline count` | > 5 |

---

### 2.3 Security Monitor Metrics (13 metrics)

**Source:** `fact_audit_logs` → `fact_audit_logs_profile_metrics`

#### Security Event Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `total_events` | `COUNT(*)` | KPI, Trend |
| `distinct_users` | `COUNT(DISTINCT user_id)` | KPI |
| `failed_auth_count` | `COUNT of auth failures` | Alert |
| `sensitive_actions` | `COUNT of privileged operations` | Alert |
| `data_access_events` | `COUNT of SELECT/READ operations` | Trend |
| `admin_actions` | `COUNT of ADMIN operations` | Table |

#### Security Derived Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| `failed_auth_rate` | `failed_auth / total_auth * 100` | < 1% |
| `admin_action_rate` | `admin_actions / total_events * 100` | Monitor |
| `events_per_user` | `total_events / distinct_users` | - |

#### Security Drift Metrics

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `auth_failure_drift` | `current - baseline failed_auth` | > 10 |

---

### 2.4 Query Monitor Metrics (14 metrics)

**Source:** `fact_query_history` → `fact_query_history_profile_metrics`

#### Query Performance Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `total_queries` | `COUNT(*)` | KPI, Trend |
| `avg_query_duration_seconds` | `AVG(duration_seconds)` | KPI |
| `p50_duration_seconds` | `PERCENTILE(0.50)` | Box Plot |
| `p95_duration_seconds` | `PERCENTILE(0.95)` | KPI, SLA |
| `p99_duration_seconds` | `PERCENTILE(0.99)` | Alert |
| `failed_queries` | `COUNT where status = FAILED` | Alert |
| `cancelled_queries` | `COUNT where status = CANCELED` | Alert |
| `successful_queries` | `COUNT where status = FINISHED` | KPI |
| `total_rows_read` | `SUM(rows_read)` | Trend |
| `total_bytes_read` | `SUM(bytes_read)` | Trend |

#### Query Derived Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| `query_success_rate` | `successful / total * 100` | > 99% |
| `query_failure_rate` | `failed / total * 100` | < 1% |
| `avg_rows_per_query` | `total_rows / total_queries` | - |

#### Query Drift Metrics

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `query_duration_drift_pct` | `((current - baseline) / baseline) * 100` | > 20% |

---

### 2.5 Cluster Monitor Metrics (10 metrics)

**Source:** `fact_node_timeline` → `fact_node_timeline_profile_metrics`

#### Cluster Utilization Metrics (AGGREGATE)

| Metric | Expression | Dashboard Widget |
|--------|------------|------------------|
| `total_clusters` | `COUNT(DISTINCT cluster_id)` | KPI |
| `total_cluster_hours` | `SUM(cluster_hours)` | KPI |
| `avg_cluster_uptime_hours` | `AVG(uptime_hours)` | KPI |
| `idle_cluster_hours` | `SUM(idle_hours)` | KPI |
| `active_cluster_hours` | `SUM(active_hours)` | KPI |
| `idle_cost_estimate` | `idle_hours * avg_cost_per_hour` | Savings |
| `autoscale_events` | `COUNT of scale up/down` | Trend |
| `cluster_start_count` | `COUNT of start events` | Trend |
| `cluster_terminate_count` | `COUNT of terminate events` | Trend |

#### Cluster Derived Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| `cluster_utilization_pct` | `active_hours / total_hours * 100` | > 60% |

---

## 3. Asset-to-Dashboard Mapping

### Cost Dashboard Assets

| Asset Type | Asset Name | Widget Type | Page |
|------------|------------|-------------|------|
| ML Model | `cost_anomaly_detector` | Table, KPI | Anomaly Detection |
| ML Model | `budget_forecaster` | Line Chart | Commit Tracking |
| ML Model | `job_cost_optimizer` | Table | Optimization |
| ML Model | `chargeback_attribution` | Table | Spend Analysis |
| ML Model | `commitment_recommender` | KPI, Table | Commit Tracking |
| ML Model | `tag_recommender` | Table | Tag Compliance |
| Monitor | `total_daily_cost` | KPI, Trend | Overview |
| Monitor | `tag_coverage_pct` | Gauge | Overview, Tag Compliance |
| Monitor | `serverless_ratio` | Gauge | Spend Analysis |
| Monitor | `jobs_on_all_purpose_cost` | KPI | Optimization |
| Monitor | `potential_job_cluster_savings` | KPI | Optimization |
| Monitor | `cost_drift_pct` | KPI, Alert | Drift |
| Monitor | `dlt_cost` | Bar Chart | Spend Analysis |
| Monitor | `model_serving_cost` | Bar Chart | Spend Analysis |

### Reliability Dashboard Assets

| Asset Type | Asset Name | Widget Type | Page |
|------------|------------|-------------|------|
| ML Model | `job_failure_predictor` | Table | Failure Predictions |
| ML Model | `job_duration_forecaster` | Table | SLA Tracking |
| ML Model | `sla_breach_predictor` | Table, KPI | SLA Tracking |
| ML Model | `pipeline_health_scorer` | Gauge, Table | Pipeline Health |
| ML Model | `retry_success_predictor` | Table | Retry & Recovery |
| Monitor | `success_rate` | KPI, Gauge, Trend | Overview |
| Monitor | `failure_rate` | KPI, Trend | Overview, Failure Analysis |
| Monitor | `p95_duration_minutes` | KPI | Overview |
| Monitor | `timeout_count` | KPI, Alert | Failure Analysis |
| Monitor | `long_running_count` | KPI | Performance |
| Monitor | `duration_cv` | KPI | Stability |
| Monitor | `success_rate_drift` | KPI, Alert | Drift |
| Monitor | `duration_drift_pct` | KPI, Alert | Drift |

### Performance Dashboard Assets

| Asset Type | Asset Name | Widget Type | Page |
|------------|------------|-------------|------|
| ML Model | `query_performance_forecaster` | Table | Query Optimization |
| ML Model | `warehouse_optimizer` | Table | Query Optimization |
| ML Model | `cache_hit_predictor` | KPI, Table | Query Performance |
| ML Model | `query_optimization_recommender` | Table | Query Optimization |
| ML Model | `cluster_sizing_recommender` | Table | Cluster Utilization |
| ML Model | `cluster_capacity_planner` | Line Chart | Resource Optimization |
| ML Model | `regression_detector` | Table, Alert | Query Performance |
| Monitor | `p95_duration_seconds` | KPI | Overview |
| Monitor | `query_success_rate` | Gauge | Query Performance |
| Monitor | `query_duration_drift_pct` | KPI, Alert | Drift |
| Monitor | `cluster_utilization_pct` | Gauge | Cluster Utilization |

### Security Dashboard Assets

| Asset Type | Asset Name | Widget Type | Page |
|------------|------------|-------------|------|
| ML Model | `security_threat_detector` | Table, KPI | Threat Detection |
| ML Model | `access_pattern_analyzer` | Table | Access Control |
| ML Model | `compliance_risk_classifier` | Gauge, Table | Compliance & Audit |
| ML Model | `permission_recommender` | Table | Access Control |
| Monitor | `total_events` | KPI, Trend | Overview |
| Monitor | `distinct_users` | KPI | Overview |
| Monitor | `failed_auth_count` | KPI, Alert | Access Control |
| Monitor | `failed_auth_rate` | Gauge | Access Control |
| Monitor | `sensitive_actions` | KPI | Compliance |
| Monitor | `admin_action_rate` | Gauge | Event Analysis |
| Monitor | `auth_failure_drift` | KPI, Alert | Drift |

### Quality Dashboard Assets

| Asset Type | Asset Name | Widget Type | Page |
|------------|------------|-------------|------|
| ML Model | `data_drift_detector` | Table, KPI | Data Drift |
| ML Model | `schema_change_predictor` | Table | Data Drift |
| ML Model | `schema_evolution_predictor` | Table | Governance |
| Monitor | `avg_quality_score` | KPI, Trend | Overview |
| Monitor | `total_evaluations` | KPI | Data Quality Rules |
| Monitor | `critical_violation_count` | KPI, Alert | Overview |
| Monitor | `rule_pass_rate` | Gauge | Data Quality Rules |
| Monitor | `violation_rate` | Gauge, Alert | Data Quality Rules |
| Monitor | `quality_score_drift` | KPI, Alert | Drift |

---

## 4. Coverage Validation

### ML Model Coverage

| Domain | Total Models | Dashboard Coverage | Gap |
|--------|--------------|-------------------|-----|
| Cost | 6 | 6 ✅ | 0 |
| Security | 4 | 4 ✅ | 0 |
| Performance | 7 | 7 ✅ | 0 |
| Reliability | 5 | 5 ✅ | 0 |
| Quality | 3 | 3 ✅ | 0 |
| **Total** | **25** | **25** | **0** |

### Monitor Metric Coverage

| Monitor | Total Metrics | High-Value Used | Visualization Types |
|---------|--------------|-----------------|---------------------|
| Cost | 35 | 20+ | KPI, Trend, Pie, Bar, Gauge |
| Job | 50 | 30+ | KPI, Trend, Gauge, Table, Box Plot |
| Security | 13 | 10+ | KPI, Trend, Gauge, Table |
| Query | 14 | 10+ | KPI, Trend, Box Plot |
| Cluster | 10 | 8+ | KPI, Gauge, Trend |
| Quality | 10 | 8+ | KPI, Gauge, Trend |

---

## 5. Implementation Checklist

### Priority 1: Complete ML Integration ✅

- [x] Cost domain: All 6 models mapped
- [x] Security domain: All 4 models mapped
- [x] Performance domain: All 7 models mapped
- [x] Reliability domain: All 5 models mapped
- [x] Quality domain: All 3 models mapped

### Priority 2: Monitor Metric Integration

- [x] Cost: Core metrics + workflow advisor metrics
- [x] Job: Reliability + duration + termination breakdown
- [x] Security: Events + auth failures + admin tracking
- [x] Query: Duration percentiles + success rates
- [x] Cluster: Utilization + idle tracking

### Priority 3: Drift Alerting

- [x] Cost drift threshold alerts
- [x] Success rate drift alerts
- [x] Duration drift alerts
- [x] Security event drift alerts
- [x] Quality score drift alerts

---

## References

- [ML Model Catalog](../ml-framework-design/07-model-catalog.md)
- [Custom Metrics Design](../lakehouse-monitoring-design/03-custom-metrics.md)
- [Lakehouse Monitoring Best Practices](../../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)
