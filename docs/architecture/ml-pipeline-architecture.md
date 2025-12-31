# ML Pipeline Architecture: Feature Engineering, Training, and Inference

This document explains the complete ML pipeline architecture for the Databricks Health Monitor, including how Feature Engineering in Unity Catalog connects the Feature, Training, and Inference pipelines.

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW ARCHITECTURE                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐                    │
│   │  Gold Layer │────▶│ Feature Pipeline │────▶│ Feature Tables  │                    │
│   │   Tables    │     │  (Daily/Hourly)  │     │  (with PKs)     │                    │
│   └─────────────┘     └─────────────────┘     └────────┬────────┘                    │
│                                                         │                             │
│                              ┌──────────────────────────┼──────────────────────────┐ │
│                              │                          │                          │ │
│                              ▼                          ▼                          │ │
│                    ┌─────────────────┐        ┌─────────────────┐                  │ │
│                    │Training Pipeline│        │Inference Pipeline│                  │ │
│                    │  (On-demand/    │        │  (Daily/Real-   │                  │ │
│                    │   Scheduled)    │        │   time)         │                  │ │
│                    └────────┬────────┘        └────────┬────────┘                  │ │
│                             │                          │                           │ │
│                             ▼                          ▼                           │ │
│                    ┌─────────────────┐        ┌─────────────────┐                  │ │
│                    │  Model Registry │◀──────▶│  Predictions    │                  │ │
│                    │  (Unity Catalog)│        │  Output Table   │                  │ │
│                    └─────────────────┘        └─────────────────┘                  │ │
│                                                                                     │ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Components

### 1. Feature Pipeline (`ml_feature_pipeline`)

**Purpose**: Transforms Gold layer data into ML-ready features with PRIMARY KEY constraints.

**Script**: `src/ml/features/create_feature_tables.py`

**What It Does**:
1. Reads from Gold layer tables (fact_usage, fact_audit_logs, fact_query_history, etc.)
2. Computes aggregations, rolling windows, and derived metrics
3. Creates feature tables with PRIMARY KEY constraints (required for Feature Engineering)
4. Enables automatic feature lookup at inference time

**Feature Tables Created**:

| Feature Table | Rows | Primary Keys | Source |
|---|---:|---|---|
| `cost_features` | ~2,740 | `workspace_id`, `usage_date` | fact_usage |
| `security_features` | ~625,782 | `user_id`, `event_date` | fact_audit_logs |
| `performance_features` | ~10,308 | `warehouse_id`, `query_date` | fact_query_history |
| `reliability_features` | ~434,739 | `job_id`, `run_date` | fact_job_run_timeline |
| `quality_features` | ~1 | `catalog_name`, `snapshot_date` | information_schema |

**Schedule**: Daily at 2 AM (after Gold layer refresh)

---

### 2. Training Pipeline (`ml_training_pipeline`)

**Purpose**: Trains ML models using Feature Engineering with automatic lineage tracking.

**Scripts**: `src/ml/{domain}/train_*.py` (25 models across 5 domains)

**Key Pattern - FeatureLookup**:

```python
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

fe = FeatureEngineeringClient()

# Step 1: Define feature lookups
feature_lookups = [
    FeatureLookup(
        table_name="catalog.features.cost_features",
        feature_names=["daily_dbu", "avg_dbu_7d", "z_score_7d", ...],
        lookup_key=["workspace_id", "usage_date"]  # Must match table PRIMARY KEY
    )
]

# Step 2: Create base DataFrame with lookup keys + label
base_df = (
    spark.table("catalog.features.cost_features")
    .select("workspace_id", "usage_date")
    .withColumn("label", ...)
)

# Step 3: Create training set (FE joins features automatically)
training_set = fe.create_training_set(
    df=base_df,
    feature_lookups=feature_lookups,
    label="label",
    exclude_columns=["workspace_id", "usage_date"]
)

# Step 4: Train model
training_df = training_set.load_df()
model = train_model(training_df.toPandas())

# Step 5: Log model WITH training_set (CRITICAL!)
fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,  # Enables auto feature lookup at inference
    registered_model_name="catalog.features.cost_anomaly_detector"
)
```

**Why `fe.log_model()` with `training_set`?**
- Stores feature lookup metadata in the model
- Enables automatic feature retrieval at inference time
- Creates lineage from features → model → predictions

**Schedule**: Weekly or on-demand

---

### 3. Inference Pipeline (`ml_inference_pipeline`)

**Purpose**: Scores new data using trained models with automatic feature lookup.

**Script**: `src/ml/inference/batch_inference.py`

**Key Pattern - `fe.score_batch()`**:

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Step 1: Create scoring DataFrame with ONLY lookup keys
# No features needed - FE retrieves them automatically!
scoring_df = (
    spark.table("catalog.gold_schema.fact_usage")
    .select("workspace_id", "usage_date")
    .filter("usage_date >= current_date() - 1")
)

# Step 2: Score with automatic feature lookup
predictions = fe.score_batch(
    model_uri="models:/catalog.features.cost_anomaly_detector/Production",
    df=scoring_df,  # Only needs lookup keys!
    result_type="double"
)

# Step 3: Write predictions
predictions.write.mode("overwrite").saveAsTable("catalog.features.cost_anomaly_predictions")
```

**How `fe.score_batch()` Works**:
1. Reads model metadata to find required features
2. Automatically joins features from feature tables using lookup keys
3. Runs the model on the joined data
4. Returns predictions with original columns

**Schedule**: Daily at 3 AM (after features are refreshed)

---

## Pipeline Orchestration

### Recommended: Single Master Orchestrator

```yaml
# resources/ml/ml_master_orchestrator.yml
resources:
  jobs:
    ml_master_orchestrator:
      name: "ML Master Orchestrator"
      
      tasks:
        # Step 1: Refresh features (runs daily)
        - task_key: refresh_features
          run_job_task:
            job_id: ${resources.jobs.ml_feature_pipeline.id}
        
        # Step 2: Train models (optional, triggered by condition)
        - task_key: train_models
          depends_on:
            - task_key: refresh_features
          run_job_task:
            job_id: ${resources.jobs.ml_training_pipeline.id}
          # Condition: only run weekly or on trigger
        
        # Step 3: Run batch inference (daily)
        - task_key: batch_inference
          depends_on:
            - task_key: refresh_features
          run_job_task:
            job_id: ${resources.jobs.ml_inference_pipeline.id}
      
      schedule:
        quartz_cron_expression: "0 0 3 * * ?"  # Daily at 3 AM
```

### Alternative: Independent Schedules

| Pipeline | Schedule | Dependencies |
|---|---|---|
| Feature Pipeline | Daily 2 AM | Gold layer refresh complete |
| Training Pipeline | Weekly Sunday 4 AM | Feature pipeline |
| Inference Pipeline | Daily 3 AM | Feature pipeline (same day) |

---

## Feature Engineering Benefits

### 1. Training/Inference Consistency
- Same features used in training and inference
- No feature computation code duplication
- Eliminates training/serving skew

### 2. Automatic Feature Lookup
- Inference only needs lookup keys (e.g., workspace_id, usage_date)
- Features automatically retrieved from feature tables
- No manual joins required

### 3. Lineage Tracking
- Full lineage from Gold tables → Features → Models → Predictions
- Visible in Unity Catalog
- Supports compliance and debugging

### 4. Feature Reuse
- Same features can power multiple models
- Centralized feature definitions
- Consistent calculations across the organization

---

## Model Catalog

### Cost Domain (6 models)
| Model | Type | Algorithm | Feature Table |
|---|---|---|---|
| `budget_forecaster` | Regression | Gradient Boosting | cost_features |
| `cost_anomaly_detector` | Anomaly Detection | Isolation Forest | cost_features |
| `resource_optimizer` | Classification | XGBoost | cost_features |
| `chargeback_allocator` | Regression | Linear Regression | cost_features |
| `commitment_analyzer` | Classification | Random Forest | cost_features |
| `savings_recommender` | Regression | Gradient Boosting | cost_features |

### Security Domain (4 models)
| Model | Type | Algorithm | Feature Table |
|---|---|---|---|
| `security_threat_detector` | Anomaly Detection | Isolation Forest | security_features |
| `access_pattern_analyzer` | Clustering | K-Means | security_features |
| `compliance_risk_classifier` | Classification | XGBoost | security_features |
| `permission_recommender` | Classification | Random Forest | security_features |

### Performance Domain (7 models)
| Model | Type | Algorithm | Feature Table |
|---|---|---|---|
| `query_performance_forecaster` | Regression | Gradient Boosting | performance_features |
| `query_optimization_recommender` | Multi-label | XGBoost | performance_features |
| `cluster_efficiency_optimizer` | Regression | Gradient Boosting | performance_features |
| `cluster_sizing_recommender` | Classification | Random Forest | performance_features |
| `resource_rightsizer` | Regression | Gradient Boosting | performance_features |
| `warehouse_scaler` | Regression | Gradient Boosting | performance_features |
| `workload_predictor` | Regression | LSTM | performance_features |

### Reliability Domain (5 models)
| Model | Type | Algorithm | Feature Table |
|---|---|---|---|
| `job_failure_predictor` | Classification | XGBoost | reliability_features |
| `pipeline_health_classifier` | Classification | Random Forest | reliability_features |
| `job_duration_forecaster` | Regression | Gradient Boosting | reliability_features |
| `failure_root_cause_analyzer` | Multi-class | XGBoost | reliability_features |
| `recovery_time_predictor` | Regression | Gradient Boosting | reliability_features |

### Quality Domain (3 models)
| Model | Type | Algorithm | Feature Table |
|---|---|---|---|
| `data_drift_detector` | Anomaly Detection | Isolation Forest | quality_features |
| `schema_change_predictor` | Classification | Random Forest | quality_features |
| `tag_recommender` | Classification | Random Forest | quality_features |

---

## Critical: Unity Catalog Signature Requirements

### The Problem

**Unity Catalog models MUST have BOTH input AND output signatures.**

Without a proper signature, registration fails with:
```
MlflowException: Model passed for registration contained a signature that includes only inputs.
All models in the Unity Catalog must be logged with a model signature containing both 
input and output type specifications.
```

### The Solution

1. **Cast DECIMAL to float64** - MLflow doesn't support DECIMAL types in signatures
2. **Provide input_example** - Enables MLflow to infer signature
3. **Provide explicit signature** - Include both input and output

```python
from mlflow.models.signature import infer_signature

# CRITICAL: Cast all features to float64 before training
for col in X.columns:
    X[col] = X[col].astype('float64')

# Train model...
model.fit(X_train, y_train)

# Create signature with BOTH input AND output
input_example = X_train.head(5).astype('float64')
sample_predictions = model.predict(input_example)
signature = infer_signature(input_example, sample_predictions)

# Log with Feature Engineering
fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,
    registered_model_name=registered_name,
    input_example=input_example,  # REQUIRED
    signature=signature  # REQUIRED
)
```

---

## Troubleshooting

### Feature Table Issues

**Error**: "Cannot create PRIMARY KEY - column is nullable"
- **Cause**: Primary key columns contain NULL values
- **Fix**: Filter NULL rows before creating table, define columns as NOT NULL

**Error**: "Feature lookup failed - table not found"
- **Cause**: Feature table doesn't exist or wrong name
- **Fix**: Run feature pipeline first, verify table name matches

### Training Issues

**Error**: "No data in training set"
- **Cause**: Feature table is empty or filter too restrictive
- **Fix**: Check feature table row count, verify date filters

**Error**: "Feature column not found"
- **Cause**: Feature name mismatch between lookup and table
- **Fix**: Verify feature_names match actual column names in feature table

### Inference Issues

**Error**: "Model not found"
- **Cause**: Model not registered or wrong URI
- **Fix**: Verify model exists in Unity Catalog, check model URI format

**Error**: "Feature lookup failed during inference"
- **Cause**: Feature table missing or lookup keys don't match
- **Fix**: Ensure feature table has required lookup key values

---

## References

- [Feature Engineering in Unity Catalog](https://docs.databricks.com/aws/en/machine-learning/feature-store)
- [Train Models with Feature Store](https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store)
- [Score Batch with Feature Engineering](https://docs.databricks.com/aws/en/machine-learning/feature-store/score-batch)
- [Feature Store Taxi Example](https://docs.databricks.com/aws/en/notebooks/source/machine-learning/feature-store-with-uc-taxi-example.html)

