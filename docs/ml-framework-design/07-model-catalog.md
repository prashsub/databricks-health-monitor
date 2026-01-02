# 07 - Model Catalog

## Overview

The Databricks Health Monitor includes **25 production ML models** across 5 domains. Each model is designed for a specific operational use case, from detecting cost anomalies to predicting job failures.

## Model Summary by Domain

| Domain | Models | Primary Use Cases |
|---|---|---|
| **COST** | 6 | Anomaly detection, forecasting, optimization |
| **SECURITY** | 4 | Threat detection, behavior analysis |
| **PERFORMANCE** | 7 | Query optimization, capacity planning |
| **RELIABILITY** | 5 | Failure prediction, duration forecasting |
| **QUALITY** | 3 | Data drift, schema changes |

---

## Quick Reference: All 25 Models

| # | Domain | Model Name | Algorithm | Model Type | Feature Table | Primary Keys |
|:---:|:---:|---|---|---|---|---|
| 1 | 💰 COST | `cost_anomaly_detector` | Isolation Forest | Anomaly Detection | `cost_features` | `workspace_id`, `usage_date` |
| 2 | 💰 COST | `budget_forecaster` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 3 | 💰 COST | `job_cost_optimizer` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 4 | 💰 COST | `chargeback_attribution` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 5 | 💰 COST | `commitment_recommender` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 6 | 💰 COST | `tag_recommender` | Random Forest + TF-IDF | Multi-class Classification | `cost_features` | `workspace_id`, `usage_date` |
| 7 | 🔒 SECURITY | `security_threat_detector` | Isolation Forest | Anomaly Detection | `security_features` | `user_id`, `event_date` |
| 8 | 🔒 SECURITY | `access_pattern_analyzer` | XGBoost | Binary Classification | `security_features` | `user_id`, `event_date` |
| 9 | 🔒 SECURITY | `compliance_risk_classifier` | Random Forest | Multi-class Classification | `security_features` | `user_id`, `event_date` |
| 10 | 🔒 SECURITY | `permission_recommender` | Random Forest | Multi-class Classification | `security_features` | `user_id`, `event_date` |
| 11 | ⚡ PERFORMANCE | `query_performance_forecaster` | Gradient Boosting | Regression | `performance_features` | `warehouse_id`, `query_date` |
| 12 | ⚡ PERFORMANCE | `warehouse_optimizer` | XGBoost | Multi-class Classification | `performance_features` | `warehouse_id`, `query_date` |
| 13 | ⚡ PERFORMANCE | `cache_hit_predictor` | XGBoost | Binary Classification | `performance_features` | `warehouse_id`, `query_date` |
| 14 | ⚡ PERFORMANCE | `query_optimization_recommender` | XGBoost | Multi-label Classification | `performance_features` | `warehouse_id`, `query_date` |
| 15 | ⚡ PERFORMANCE | `cluster_sizing_recommender` | Gradient Boosting | Regression | `performance_features` | `warehouse_id`, `query_date` |
| 16 | ⚡ PERFORMANCE | `cluster_capacity_planner` | Gradient Boosting | Regression | `performance_features` | `warehouse_id`, `query_date` |
| 17 | ⚡ PERFORMANCE | `regression_detector` | Isolation Forest | Anomaly Detection | `performance_features` | `warehouse_id`, `query_date` |
| 18 | 🔄 RELIABILITY | `job_failure_predictor` | XGBoost | Binary Classification | `reliability_features` | `job_id`, `run_date` |
| 19 | 🔄 RELIABILITY | `job_duration_forecaster` | Gradient Boosting | Regression | `reliability_features` | `job_id`, `run_date` |
| 20 | 🔄 RELIABILITY | `sla_breach_predictor` | XGBoost | Binary Classification | `reliability_features` | `job_id`, `run_date` |
| 21 | 🔄 RELIABILITY | `pipeline_health_scorer` | Gradient Boosting | Regression | `reliability_features` | `job_id`, `run_date` |
| 22 | 🔄 RELIABILITY | `retry_success_predictor` | XGBoost | Binary Classification | `reliability_features` | `job_id`, `run_date` |
| 23 | 📊 QUALITY | `data_drift_detector` | Isolation Forest | Anomaly Detection | `quality_features` | `table_name`, `check_date` |
| 24 | 📊 QUALITY | `schema_change_predictor` | XGBoost | Binary Classification | `quality_features` | `table_name`, `check_date` |
| 25 | 📊 QUALITY | `schema_evolution_predictor` | Random Forest | Multi-class Classification | `quality_features` | `table_name`, `check_date` |

### Model Type Distribution

| Model Type | Count | Models |
|---|:---:|---|
| **Anomaly Detection** | 4 | `cost_anomaly_detector`, `security_threat_detector`, `regression_detector`, `data_drift_detector` |
| **Regression** | 9 | `budget_forecaster`, `job_cost_optimizer`, `chargeback_attribution`, `commitment_recommender`, `query_performance_forecaster`, `cluster_sizing_recommender`, `cluster_capacity_planner`, `job_duration_forecaster`, `pipeline_health_scorer` |
| **Binary Classification** | 7 | `access_pattern_analyzer`, `cache_hit_predictor`, `job_failure_predictor`, `sla_breach_predictor`, `retry_success_predictor`, `schema_change_predictor` |
| **Multi-class Classification** | 4 | `tag_recommender`, `compliance_risk_classifier`, `permission_recommender`, `warehouse_optimizer`, `schema_evolution_predictor` |
| **Multi-label Classification** | 1 | `query_optimization_recommender` |

### Algorithm Distribution

| Algorithm | Count | Use Case |
|---|:---:|---|
| **Isolation Forest** | 4 | Unsupervised anomaly detection |
| **Gradient Boosting Regressor** | 9 | Continuous value prediction |
| **XGBoost Classifier** | 7 | High-performance classification |
| **Random Forest Classifier** | 5 | Robust multi-class classification |

---

## COST Domain (6 Models)

### cost_anomaly_detector

| Property | Value |
|---|---|
| **Purpose** | Detect unusual spending patterns |
| **Algorithm** | Isolation Forest (Unsupervised) |
| **Model Type** | Anomaly Detection |
| **Feature Table** | `cost_features` |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `anomaly_score` (-1 to 1), `is_anomaly` (0/1) |

**Features Used**:
- `daily_dbu`, `daily_cost`
- `avg_dbu_7d`, `avg_dbu_30d`
- `dbu_change_pct_1d`, `dbu_change_pct_7d`
- `z_score_7d`

**Interpretation**:
- `anomaly_score < 0`: Anomalous (more negative = more anomalous)
- `is_anomaly = 1`: Flag for alerting

**Use Cases**:
- Alert on unexpected cost spikes
- Identify misconfigured jobs
- Detect runaway queries

---

### budget_forecaster

| Property | Value |
|---|---|
| **Purpose** | Forecast daily Databricks costs |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `cost_features` |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `predicted_cost` (DOUBLE) |

**Features Used**:
- `daily_dbu`, `avg_dbu_7d`, `avg_dbu_30d`
- `dbu_change_pct_1d`, `dbu_change_pct_7d`
- `serverless_adoption_ratio`
- `jobs_on_all_purpose_cost`
- `is_weekend`, `day_of_week`

**Metrics**:
- Target: `daily_cost`
- R² typically > 0.85
- RMSE depends on cost scale

**Use Cases**:
- Budget planning
- Alerting when actual > forecasted
- Capacity planning

---

### job_cost_optimizer

| Property | Value |
|---|---|
| **Purpose** | Predict potential cost savings |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `cost_features` |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `optimization_savings` (DOUBLE) |

**Features Used**:
- `daily_dbu`, `daily_cost`
- `serverless_adoption_ratio`
- `jobs_on_all_purpose_cost`, `all_purpose_inefficiency_ratio`
- `potential_job_cluster_savings`

**Use Cases**:
- Identify workspaces with high savings potential
- Prioritize optimization efforts
- Track optimization progress

---

### chargeback_attribution

| Property | Value |
|---|---|
| **Purpose** | Predict cost allocation by workspace |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `cost_features` |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `predicted_chargeback` (DOUBLE) |

**Features Used**:
- `daily_dbu`, `daily_cost`
- `serverless_cost`, `dlt_cost`, `model_serving_cost`
- `jobs_on_all_purpose_count`

**Use Cases**:
- Cross-charge departments
- Budget allocation
- Cost center analysis

---

### commitment_recommender

| Property | Value |
|---|---|
| **Purpose** | Recommend commitment levels |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `cost_features` |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `recommended_commitment` (DOUBLE) |

**Features Used**:
- `daily_dbu`, `avg_dbu_7d`, `avg_dbu_30d`
- `dbu_change_pct_1d`, `dbu_change_pct_7d`
- `z_score_7d`

**Use Cases**:
- Reserved capacity planning
- Commit discount optimization
- Usage forecasting for negotiations

---

### tag_recommender

| Property | Value |
|---|---|
| **Purpose** | Recommend cost allocation tags |
| **Algorithm** | Random Forest Classifier |
| **Model Type** | Multi-class Classification |
| **Feature Table** | `cost_features` + TF-IDF |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `predicted_tag` (STRING) |

**Special**: Uses TF-IDF on job names (runtime feature)

**Features Used**:
- `daily_dbu`, `daily_cost`, `avg_dbu_7d`, `avg_dbu_30d`
- TF-IDF vectors from job names (50 features)

**Note**: Cannot use `fe.score_batch()` due to runtime TF-IDF features.

---

## SECURITY Domain (4 Models)

### security_threat_detector

| Property | Value |
|---|---|
| **Purpose** | Detect security anomalies |
| **Algorithm** | Isolation Forest (Unsupervised) |
| **Model Type** | Anomaly Detection |
| **Feature Table** | `security_features` |
| **Primary Keys** | `user_id`, `event_date` |
| **Output** | `threat_score`, `is_threat` |

**Features Used**:
- `event_count`, `tables_accessed`
- `failed_auth_count`, `unique_source_ips`
- `lateral_movement_risk`, `is_activity_burst`

**Use Cases**:
- SOC alerting
- Insider threat detection
- Compliance monitoring

---

### access_pattern_analyzer

| Property | Value |
|---|---|
| **Purpose** | Classify access patterns |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Binary Classification |
| **Feature Table** | `security_features` |
| **Primary Keys** | `user_id`, `event_date` |
| **Output** | `pattern_class`, `probability` |

**Features Used**:
- `event_count`, `tables_accessed`
- `off_hours_events`, `unique_source_ips`

**Use Cases**:
- User behavior profiling
- Anomaly contextualization
- Risk scoring

---

### compliance_risk_classifier

| Property | Value |
|---|---|
| **Purpose** | Classify compliance risk level |
| **Algorithm** | Random Forest Classifier |
| **Model Type** | Multi-class Classification |
| **Feature Table** | `security_features` |
| **Primary Keys** | `user_id`, `event_date` |
| **Output** | `risk_level` (1-5), `probability` |

**Use Cases**:
- Compliance reporting
- Audit prioritization
- Risk dashboards

---

### permission_recommender

| Property | Value |
|---|---|
| **Purpose** | Recommend permission changes |
| **Algorithm** | Random Forest Classifier |
| **Model Type** | Multi-class Classification |
| **Feature Table** | `security_features` |
| **Primary Keys** | `user_id`, `event_date` |
| **Output** | `recommended_action` |

**Use Cases**:
- Least privilege enforcement
- Access review automation
- Permission right-sizing

---

## PERFORMANCE Domain (7 Models)

### query_performance_forecaster

| Property | Value |
|---|---|
| **Purpose** | Forecast query performance |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | `predicted_p99_ms` (DOUBLE) |

**Features Used**:
- `query_count`, `avg_duration_ms`
- `p50_duration_ms`, `p95_duration_ms`
- `spill_rate`, `error_rate`
- `total_bytes_read`, `read_write_ratio`

**Use Cases**:
- SLA forecasting
- Capacity planning
- Regression detection

---

### warehouse_optimizer

| Property | Value |
|---|---|
| **Purpose** | Recommend warehouse sizing |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Multi-class Classification |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | `size_recommendation` |

**Classes**: "too_small", "optimal", "too_large"

**Use Cases**:
- Auto-scaling configuration
- Cost-performance optimization
- Right-sizing recommendations

---

### cache_hit_predictor

| Property | Value |
|---|---|
| **Purpose** | Predict cache hit rates |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Binary Classification |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | `cache_hit_probability` |

**Use Cases**:
- Cache configuration tuning
- Query routing optimization
- Performance forecasting

---

### query_optimization_recommender

| Property | Value |
|---|---|
| **Purpose** | Recommend query optimizations |
| **Algorithm** | XGBoost Multi-label |
| **Model Type** | Multi-label Classification |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | Multiple optimization flags |

**Recommendations**: partition_pruning, caching, join_reorder, etc.

---

### cluster_sizing_recommender

| Property | Value |
|---|---|
| **Purpose** | Recommend cluster configuration |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | `optimal_size_score` |

---

### cluster_capacity_planner

| Property | Value |
|---|---|
| **Purpose** | Forecast capacity needs |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | `predicted_peak_utilization` |

---

### regression_detector

| Property | Value |
|---|---|
| **Purpose** | Detect performance regressions |
| **Algorithm** | Isolation Forest |
| **Model Type** | Anomaly Detection |
| **Feature Table** | `performance_features` |
| **Primary Keys** | `warehouse_id`, `query_date` |
| **Output** | `regression_score`, `is_regression` |

---

## RELIABILITY Domain (5 Models)

### job_failure_predictor

| Property | Value |
|---|---|
| **Purpose** | Predict job failures |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Binary Classification |
| **Feature Table** | `reliability_features` |
| **Primary Keys** | `job_id`, `run_date` |
| **Output** | `failure_probability`, `will_fail` |

**Features Used**:
- `total_runs`, `avg_duration_sec`
- `success_rate`, `failure_rate`
- `duration_cv`, `rolling_failure_rate_30d`
- `prev_day_failed`

**Interpretation**:
- `failure_probability > 0.5`: High risk of failure
- Use for proactive alerting

---

### job_duration_forecaster

| Property | Value |
|---|---|
| **Purpose** | Forecast job durations |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `reliability_features` |
| **Primary Keys** | `job_id`, `run_date` |
| **Output** | `predicted_duration_sec` |

**Use Cases**:
- SLA monitoring
- Schedule optimization
- Resource allocation

---

### sla_breach_predictor

| Property | Value |
|---|---|
| **Purpose** | Predict SLA breaches |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Binary Classification |
| **Feature Table** | `reliability_features` |
| **Primary Keys** | `job_id`, `run_date` |
| **Output** | `breach_probability` |

---

### pipeline_health_scorer

| Property | Value |
|---|---|
| **Purpose** | Score pipeline health |
| **Algorithm** | Gradient Boosting Regressor |
| **Model Type** | Regression |
| **Feature Table** | `reliability_features` |
| **Primary Keys** | `job_id`, `run_date` |
| **Output** | `health_score` (0-100) |

---

### retry_success_predictor

| Property | Value |
|---|---|
| **Purpose** | Predict retry success |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Binary Classification |
| **Feature Table** | `reliability_features` |
| **Primary Keys** | `job_id`, `run_date` |
| **Output** | `retry_success_probability` |

---

## QUALITY Domain (3 Models)

### data_drift_detector

| Property | Value |
|---|---|
| **Purpose** | Detect data distribution changes |
| **Algorithm** | Isolation Forest |
| **Model Type** | Anomaly Detection |
| **Feature Table** | `quality_features` |
| **Primary Keys** | `table_name`, `check_date` |
| **Output** | `drift_score`, `is_drifted` |

**Features Used**:
- Table row counts
- Column nullability rates
- Data type distributions

---

### schema_change_predictor

| Property | Value |
|---|---|
| **Purpose** | Predict schema change risk |
| **Algorithm** | XGBoost Classifier |
| **Model Type** | Binary Classification |
| **Feature Table** | `quality_features` |
| **Primary Keys** | `table_name`, `check_date` |
| **Output** | `change_probability` |

---

### schema_evolution_predictor

| Property | Value |
|---|---|
| **Purpose** | Predict schema evolution patterns |
| **Algorithm** | Random Forest Classifier |
| **Model Type** | Multi-class Classification |
| **Feature Table** | `quality_features` |
| **Primary Keys** | `table_name`, `check_date` |
| **Output** | `evolution_type` |

---

## Model Selection Guide

### By Use Case

| Use Case | Recommended Model |
|---|---|
| Alert on cost spikes | `cost_anomaly_detector` |
| Budget planning | `budget_forecaster` |
| Security SOC | `security_threat_detector` |
| Query optimization | `query_performance_forecaster` |
| Job monitoring | `job_failure_predictor` |
| Data quality | `data_drift_detector` |

### By Model Type

| Need | Model Type | Examples |
|---|---|---|
| Detect outliers | Anomaly Detection | `cost_anomaly_detector`, `security_threat_detector` |
| Predict numbers | Regression | `budget_forecaster`, `job_duration_forecaster` |
| Predict yes/no | Classification | `job_failure_predictor`, `sla_breach_predictor` |
| Multiple categories | Multi-class | `warehouse_optimizer`, `compliance_risk_classifier` |

## Checking Model Health

### MLflow UI

1. Navigate to **Experiments** → `/Shared/health_monitor_ml_{model_name}`
2. Compare recent runs
3. Check for metric degradation

### SQL Queries

```sql
-- Check recent predictions
SELECT 
    model_name,
    COUNT(*) as predictions,
    AVG(prediction) as avg_prediction,
    MAX(scored_at) as last_scored
FROM ${catalog}.${schema}.cost_anomaly_predictions
WHERE scored_at >= current_date() - INTERVAL 7 DAYS
GROUP BY model_name;
```

### Validation Queries

```sql
-- Anomaly detection: check anomaly rate is reasonable (2-10%)
SELECT 
    DATE(scored_at) as date,
    COUNT(*) as total,
    SUM(is_anomaly) as anomalies,
    ROUND(100.0 * SUM(is_anomaly) / COUNT(*), 2) as anomaly_pct
FROM ${catalog}.${schema}.cost_anomaly_predictions
GROUP BY DATE(scored_at)
ORDER BY date DESC;

-- Should see 2-10% anomaly rate; much higher suggests model drift
```

## Next Steps

- **[08-MLflow Best Practices](08-mlflow-best-practices.md)**: Experiment management
- **[09-Deployment](09-deployment.md)**: Pipeline orchestration
- **[10-Troubleshooting](10-troubleshooting.md)**: Common issues

