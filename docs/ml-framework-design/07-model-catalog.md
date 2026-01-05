# 07 - Model Catalog

## Overview

The Databricks Health Monitor includes **25 designed ML models** across 5 domains, with **24 successfully trained** and **23 batch scored** via Feature Store. Each model is designed for a specific operational use case, from detecting cost anomalies to predicting job failures.

## Complete Model Inventory (25 Models)

| # | Domain | Model Name | Trained | Scored | Notes |
|:---:|:---:|---|:---:|:---:|---|
| 1 | 💰 COST | `cost_anomaly_detector` | ✅ | ✅ | 736 records |
| 2 | 💰 COST | `budget_forecaster` | ✅ | ✅ | 736 records |
| 3 | 💰 COST | `job_cost_optimizer` | ✅ | ✅ | 736 records |
| 4 | 💰 COST | `chargeback_attribution` | ✅ | ✅ | 736 records |
| 5 | 💰 COST | `commitment_recommender` | ✅ | ✅ | 736 records |
| 6 | 💰 COST | `tag_recommender` | ✅ | ⏭️ | Uses TF-IDF, requires [custom inference](#tag_recommender-custom-inference) |
| 7 | 🔒 SECURITY | `security_threat_detector` | ✅ | ✅ | 100,000 records |
| 8 | 🔒 SECURITY | `exfiltration_detector` | ✅ | ✅ | 100,000 records |
| 9 | 🔒 SECURITY | `privilege_escalation_detector` | ✅ | ✅ | 100,000 records |
| 10 | 🔒 SECURITY | `user_behavior_baseline` | ✅ | ✅ | 100,000 records |
| 11 | ⚡ PERFORMANCE | `query_performance_forecaster` | ✅ | ✅ | 3,020 records |
| 12 | ⚡ PERFORMANCE | `warehouse_optimizer` | ✅ | ✅ | 3,020 records |
| 13 | ⚡ PERFORMANCE | `cluster_capacity_planner` | ✅ | ✅ | 3,020 records |
| 14 | ⚡ PERFORMANCE | `performance_regression_detector` | ✅ | ✅ | 3,020 records |
| 15 | ⚡ PERFORMANCE | `dbr_migration_risk_scorer` | ✅ | ✅ | 100,000 records |
| 16 | ⚡ PERFORMANCE | `cache_hit_predictor` | ✅ | ✅ | 3,020 records |
| 17 | ⚡ PERFORMANCE | `query_optimization_recommender` | ✅ | ✅ | 3,020 records |
| 18 | 🔄 RELIABILITY | `job_failure_predictor` | ✅ | ✅ | 100,000 records |
| 19 | 🔄 RELIABILITY | `job_duration_forecaster` | ✅ | ✅ | 100,000 records |
| 20 | 🔄 RELIABILITY | `sla_breach_predictor` | ✅ | ✅ | 100,000 records |
| 21 | 🔄 RELIABILITY | `retry_success_predictor` | ✅ | ✅ | 100,000 records |
| 22 | 🔄 RELIABILITY | `pipeline_health_scorer` | ✅ | ✅ | 100,000 records |
| 23 | 📊 QUALITY | `data_drift_detector` | ✅ | ✅ | 1 record (sparse metadata) |
| 24 | 📊 QUALITY | `data_freshness_predictor` | ✅ | ✅ | 1 record (sparse metadata) |
| 25 | 📊 QUALITY | `schema_change_predictor` | ❌ | ❌ | **Removed**: Single-class data (see note below) |

### Summary Statistics

| Metric | Count | Details |
|--------|:---:|---------|
| **Designed** | 25 | Original model inventory |
| **Trained** | 24 | `schema_change_predictor` removed |
| **Scored (Feature Store)** | 23 | `tag_recommender` requires custom inference |
| **Total Records Scored** | ~1,012,741 | Across 23 models |

### Exclusion Reasons

| Model | Stage | Root Cause |
|-------|-------|------------|
| `schema_change_predictor` | Training + Scoring | `system.information_schema` doesn't track schema history, so `schema_changes_7d` is always 0 (single-class data - cannot train classifier) |
| `tag_recommender` | FE Scoring only | Uses TF-IDF text vectorization on job names - features not in feature table, requires [custom inference](#tag_recommender-custom-inference) |

---

## Model Summary by Domain

| Domain | Total | Trained | Scored | Primary Use Cases |
|---|:---:|:---:|:---:|---|
| **COST** | 6 | 6 | 5 | Anomaly detection, forecasting, optimization |
| **SECURITY** | 4 | 4 | 4 | Threat detection, behavior analysis |
| **PERFORMANCE** | 7 | 7 | 7 | Query optimization, capacity planning |
| **RELIABILITY** | 5 | 5 | 5 | Failure prediction, duration forecasting |
| **QUALITY** | 3 | 2 | 2 | Data drift, freshness prediction |

---

## Quick Reference: All 25 Models

| # | Domain | Model Name | Algorithm | Model Type | Feature Table | Primary Keys |
|:---:|:---:|---|---|---|---|---|
| 1 | 💰 COST | `cost_anomaly_detector` | Isolation Forest | Anomaly Detection | `cost_features` | `workspace_id`, `usage_date` |
| 2 | 💰 COST | `budget_forecaster` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 3 | 💰 COST | `job_cost_optimizer` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 4 | 💰 COST | `chargeback_attribution` | Gradient Boosting | Regression | `cost_features` | `workspace_id`, `usage_date` |
| 5 | 💰 COST | `commitment_recommender` | XGBoost | Binary Classification | `cost_features` | `workspace_id`, `usage_date` |
| 6 | 💰 COST | `tag_recommender` | Random Forest + TF-IDF | Multi-class Classification | `cost_features` + TF-IDF | `workspace_id`, `usage_date` |
| 7 | 🔒 SECURITY | `security_threat_detector` | Isolation Forest | Anomaly Detection | `security_features` | `user_id`, `event_date` |
| 8 | 🔒 SECURITY | `exfiltration_detector` | Isolation Forest | Anomaly Detection | `security_features` | `user_id`, `event_date` |
| 9 | 🔒 SECURITY | `privilege_escalation_detector` | Isolation Forest | Anomaly Detection | `security_features` | `user_id`, `event_date` |
| 10 | 🔒 SECURITY | `user_behavior_baseline` | Isolation Forest | Anomaly Detection | `security_features` | `user_id`, `event_date` |
| 11 | ⚡ PERFORMANCE | `query_performance_forecaster` | Gradient Boosting | Regression | `performance_features` | `warehouse_id`, `query_date` |
| 12 | ⚡ PERFORMANCE | `warehouse_optimizer` | Gradient Boosting | Regression | `performance_features` | `warehouse_id`, `query_date` |
| 13 | ⚡ PERFORMANCE | `performance_regression_detector` | Isolation Forest | Anomaly Detection | `performance_features` | `warehouse_id`, `query_date` |
| 14 | ⚡ PERFORMANCE | `cluster_capacity_planner` | Gradient Boosting | Regression | `performance_features` | `warehouse_id`, `query_date` |
| 15 | ⚡ PERFORMANCE | `dbr_migration_risk_scorer` | Random Forest | Multi-class Classification | `reliability_features` | `job_id`, `run_date` |
| 16 | ⚡ PERFORMANCE | `cache_hit_predictor` | XGBoost | Binary Classification | `performance_features` | `warehouse_id`, `query_date` |
| 17 | ⚡ PERFORMANCE | `query_optimization_recommender` | XGBoost | Binary Classification | `performance_features` | `warehouse_id`, `query_date` |
| 18 | 🔄 RELIABILITY | `job_failure_predictor` | XGBoost | Binary Classification | `reliability_features` | `job_id`, `run_date` |
| 19 | 🔄 RELIABILITY | `job_duration_forecaster` | Gradient Boosting | Regression | `reliability_features` | `job_id`, `run_date` |
| 20 | 🔄 RELIABILITY | `sla_breach_predictor` | XGBoost | Binary Classification | `reliability_features` | `job_id`, `run_date` |
| 21 | 🔄 RELIABILITY | `retry_success_predictor` | XGBoost | Binary Classification | `reliability_features` | `job_id`, `run_date` |
| 22 | 🔄 RELIABILITY | `pipeline_health_scorer` | Gradient Boosting | Regression | `reliability_features` | `job_id`, `run_date` |
| 23 | 📊 QUALITY | `data_drift_detector` | Isolation Forest | Anomaly Detection | `quality_features` | `catalog_name`, `snapshot_date` |
| 24 | 📊 QUALITY | `data_freshness_predictor` | Gradient Boosting | Regression | `quality_features` | `catalog_name`, `snapshot_date` |
| 25 | 📊 QUALITY | `schema_change_predictor` | XGBoost | Binary Classification | `quality_features` | `catalog_name`, `snapshot_date` |

> **Note:** Model #25 (`schema_change_predictor`) is documented but removed from training/inference due to single-class data.

### Model Type Distribution (25 Designed)

| Model Type | Total | Trained | Models |
|---|:---:|:---:|---|
| **Anomaly Detection** | 7 | 7 | `cost_anomaly_detector`, `security_threat_detector`, `exfiltration_detector`, `privilege_escalation_detector`, `user_behavior_baseline`, `performance_regression_detector`, `data_drift_detector` |
| **Regression** | 9 | 9 | `budget_forecaster`, `job_cost_optimizer`, `chargeback_attribution`, `query_performance_forecaster`, `warehouse_optimizer`, `cluster_capacity_planner`, `job_duration_forecaster`, `pipeline_health_scorer`, `data_freshness_predictor` |
| **Binary Classification** | 7 | 6 | `commitment_recommender`, `cache_hit_predictor`, `query_optimization_recommender`, `job_failure_predictor`, `sla_breach_predictor`, `retry_success_predictor`, ~~`schema_change_predictor`~~ (removed) |
| **Multi-class Classification** | 2 | 2 | `tag_recommender` (TF-IDF + Random Forest), `dbr_migration_risk_scorer` |

### Algorithm Distribution (24 Trained)

| Algorithm | Count | Use Case |
|---|:---:|---|
| **Isolation Forest** | 7 | Unsupervised anomaly detection |
| **Gradient Boosting Regressor** | 9 | Continuous value prediction |
| **XGBoost Classifier** | 6 | High-performance binary classification (originally 7, `schema_change_predictor` removed) |
| **Random Forest Classifier** | 2 | Robust multi-class classification (incl. `tag_recommender` with TF-IDF) |

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
| **Purpose** | Recommend cost allocation tags for untagged resources |
| **Algorithm** | Random Forest Classifier |
| **Model Type** | Multi-class Classification |
| **Feature Table** | `cost_features` + TF-IDF (runtime) |
| **Primary Keys** | `workspace_id`, `usage_date` |
| **Output** | `predicted_tag` (STRING) |

**Special**: Uses TF-IDF on job names (runtime feature extraction)

**Features Used**:
- Cost features: `daily_dbu`, `daily_cost`, `avg_dbu_7d`, `avg_dbu_30d`, `jobs_on_all_purpose_cost`, `all_purpose_inefficiency_ratio`
- NLP features: TF-IDF vectors from job names (50 features)

#### tag_recommender Custom Inference

Since `tag_recommender` uses TF-IDF features computed at runtime (not stored in feature table), it **cannot use `fe.score_batch()`**. Instead, use the following custom inference pattern:

```python
import mlflow
import pickle
import pandas as pd
import numpy as np
from pyspark.sql import functions as F

def score_tag_recommender(spark, catalog: str, feature_schema: str, gold_schema: str):
    """
    Custom inference for tag_recommender model.
    
    Why custom: Model uses TF-IDF features from job names (runtime extraction),
    which cannot be stored in feature tables.
    """
    model_uri = f"models:/{catalog}.{feature_schema}.tag_recommender/latest"
    
    # 1. Load model and artifacts
    model = mlflow.sklearn.load_model(model_uri)
    
    # Load TF-IDF vectorizer and label encoder from artifacts
    client = mlflow.MlflowClient()
    run_id = client.get_model_version_by_alias(
        f"{catalog}.{feature_schema}.tag_recommender", "Champion"
    ).run_id
    
    artifacts_path = mlflow.artifacts.download_artifacts(run_id=run_id)
    
    with open(f"{artifacts_path}/tfidf_vectorizer.pkl", 'rb') as f:
        tfidf = pickle.load(f)
    with open(f"{artifacts_path}/label_encoder.pkl", 'rb') as f:
        label_encoder = pickle.load(f)
    
    # 2. Get untagged jobs to score
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    cost_features = f"{catalog}.{feature_schema}.cost_features"
    
    untagged_jobs = (
        spark.table(fact_usage)
        .filter(F.col("is_tagged") == False)
        .filter(F.col("usage_metadata_job_id").isNotNull())
        .groupBy(F.col("usage_metadata_job_id").alias("job_id"))
        .agg(
            F.first("workspace_id").alias("workspace_id"),
            F.first(F.to_date("usage_date")).alias("usage_date")
        )
        .join(
            spark.table(dim_job).select("job_id", "name").dropDuplicates(["job_id"]),
            "job_id", "inner"
        )
        .withColumnRenamed("name", "job_name")
    )
    
    # 3. Join with cost features
    scored_df = untagged_jobs.join(
        spark.table(cost_features),
        ["workspace_id", "usage_date"],
        "left"
    )
    
    pdf = scored_df.toPandas()
    
    if len(pdf) == 0:
        print("No untagged jobs to score")
        return None
    
    # 4. Compute TF-IDF features
    tfidf_features = tfidf.transform(pdf['job_name'].fillna('')).toarray()
    tfidf_df = pd.DataFrame(tfidf_features, columns=[f"tfidf_{i}" for i in range(tfidf_features.shape[1])])
    
    # 5. Prepare cost features
    cost_cols = ["daily_dbu", "daily_cost", "avg_dbu_7d", "avg_dbu_30d", 
                 "jobs_on_all_purpose_cost", "all_purpose_inefficiency_ratio"]
    available_cost = [c for c in cost_cols if c in pdf.columns]
    cost_df = pdf[available_cost].fillna(0).replace([np.inf, -np.inf], 0).astype('float64')
    
    # 6. Combine features and predict
    X = pd.concat([cost_df.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)
    predictions = model.predict(X)
    predicted_tags = label_encoder.inverse_transform(predictions)
    
    # 7. Create results
    pdf['predicted_tag'] = predicted_tags
    pdf['scored_at'] = pd.Timestamp.now()
    
    # 8. Write to predictions table
    result_df = spark.createDataFrame(pdf[['job_id', 'job_name', 'predicted_tag', 'scored_at']])
    result_df.write.mode("append").saveAsTable(f"{catalog}.{feature_schema}.tag_recommendations")
    
    print(f"✓ Scored {len(pdf)} jobs with tag recommendations")
    return result_df

# Usage:
# score_tag_recommender(spark, catalog, feature_schema, gold_schema)
```

**Key Points:**
- Model is logged with `mlflow.sklearn.log_model()` (not `fe.log_model()`)
- TF-IDF vectorizer and label encoder are stored as MLflow artifacts
- Must load artifacts separately from model
- Custom inference pipeline combines cost features + TF-IDF at runtime

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

