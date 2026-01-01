# 08 - MLflow Best Practices

## Overview

MLflow is the backbone of ML lifecycle management on Databricks. This document covers best practices for experiment tracking, model logging, and MLOps.

## Experiment Organization

### Naming Convention

```python
# Pattern: /Shared/{project}_ml_{model_name}
experiment_name = f"/Shared/health_monitor_ml_{model_name}"

# Examples:
/Shared/health_monitor_ml_cost_anomaly_detector
/Shared/health_monitor_ml_budget_forecaster
/Shared/health_monitor_ml_failure_predictor
```

### Why `/Shared/`?

| Location | Visibility | Use Case |
|---|---|---|
| `/Shared/` | All workspace users | Production experiments |
| `/Users/{user}/` | Individual user | Development/exploration |
| `/Repos/{user}/` | Repo context | CI/CD pipelines |

**Best Practice**: Always use `/Shared/` for production models to ensure team access.

### Creating Experiments

```python
import mlflow

def setup_mlflow(experiment_name: str) -> str:
    """Set up MLflow experiment with error handling."""
    try:
        # Try to set existing experiment
        mlflow.set_experiment(experiment_name)
    except Exception:
        # Create if doesn't exist
        mlflow.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)
    
    print(f"✓ Experiment: {experiment_name}")
    return experiment_name
```

## Run Naming

### Convention

```python
# Pattern: {model_name}_{algorithm}_v{version}_{timestamp}
run_name = f"{model_name}_{algorithm}_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Examples:
"cost_anomaly_detector_isolation_forest_v1_20260101_030000"
"budget_forecaster_gradient_boosting_v1_20260101_030500"
```

### Why Include Timestamp?

- Enables quick identification of runs
- Prevents name collisions
- Supports chronological sorting

## Tagging Strategy

### Required Tags

Every run should include:

```python
mlflow.set_tags({
    # Project identification
    "project": "databricks_health_monitor",
    
    # Domain classification
    "domain": "cost|security|performance|reliability|quality",
    
    # Model identification
    "model_name": "cost_anomaly_detector",
    "model_type": "regression|classification|anomaly_detection",
    "algorithm": "gradient_boosting|isolation_forest|xgboost|random_forest",
    
    # Use case
    "use_case": "specific_use_case",
    
    # Feature Engineering
    "feature_engineering": "unity_catalog",
    "training_data": "cost_features"
})
```

### Queryable Tags

Use tags for filtering in MLflow UI:

```python
# In MLflow UI, filter by:
# tags.domain = "cost"
# tags.model_type = "anomaly_detection"
```

## Parameter Logging

### Standard Parameters

```python
mlflow.log_params({
    # ===========================================
    # Algorithm Hyperparameters
    # ===========================================
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "random_state": 42,
    
    # ===========================================
    # Data Parameters
    # ===========================================
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "feature_count": len(feature_names),
    
    # ===========================================
    # Feature Engineering
    # ===========================================
    "feature_table": "cost_features",
    "primary_keys": "workspace_id,usage_date",
    "feature_engineering_version": "1.0",
    
    # ===========================================
    # Reproducibility
    # ===========================================
    "test_size": 0.2,
    "stratify": str(use_stratify)
})
```

### Handling Long Values

```python
# For lists or long strings
features_str = ",".join(feature_names[:20])  # Truncate if needed
if len(feature_names) > 20:
    features_str += f"...and {len(feature_names) - 20} more"

mlflow.log_param("features_sample", features_str)
mlflow.log_param("total_features", len(feature_names))
```

## Metrics Logging

### By Model Type

#### Regression

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

y_pred = model.predict(X_test)

metrics = {
    "train_r2": model.score(X_train, y_train),
    "test_r2": r2_score(y_test, y_pred),
    "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
    "mae": mean_absolute_error(y_test, y_pred),
    "mape": np.mean(np.abs((y_test - y_pred) / y_test)) * 100,  # If y_test > 0
    
    # Sample sizes
    "training_samples": len(X_train),
    "test_samples": len(X_test)
}

mlflow.log_metrics(metrics)
```

#### Classification

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, log_loss
)

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "precision": precision_score(y_test, y_pred),
    "recall": recall_score(y_test, y_pred),
    "f1": f1_score(y_test, y_pred),
    "auc_roc": roc_auc_score(y_test, y_prob),
    "log_loss": log_loss(y_test, y_prob),
    
    # Class balance
    "positive_class_ratio": y_train.mean(),
    "training_samples": len(X_train)
}

mlflow.log_metrics(metrics)
```

#### Anomaly Detection

```python
predictions = model.predict(X_train)
scores = model.decision_function(X_train)

metrics = {
    "anomaly_rate": (predictions == -1).mean(),
    "avg_anomaly_score": scores[predictions == -1].mean() if (predictions == -1).any() else 0,
    "avg_normal_score": scores[predictions == 1].mean(),
    "training_samples": len(X_train),
    
    # Score distribution
    "score_min": scores.min(),
    "score_max": scores.max(),
    "score_std": scores.std()
}

mlflow.log_metrics(metrics)
```

### Step Metrics (Time Series)

```python
# Log metrics over training epochs
for epoch in range(num_epochs):
    train_loss, val_loss = train_epoch(model, data)
    
    mlflow.log_metrics({
        "train_loss": train_loss,
        "val_loss": val_loss
    }, step=epoch)
```

## Artifact Logging

### Common Artifacts

```python
import matplotlib.pyplot as plt
import json
import tempfile
import os

# 1. Feature importance plot
plt.figure(figsize=(10, 6))
plt.barh(feature_names, model.feature_importances_)
plt.title("Feature Importance")
plt.tight_layout()
mlflow.log_figure(plt.gcf(), "feature_importance.png")
plt.close()

# 2. Confusion matrix
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot()
mlflow.log_figure(plt.gcf(), "confusion_matrix.png")
plt.close()

# 3. Configuration as JSON
config = {
    "feature_names": feature_names,
    "primary_keys": primary_keys,
    "model_type": model_type
}

with tempfile.TemporaryDirectory() as tmpdir:
    config_path = os.path.join(tmpdir, "config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    mlflow.log_artifact(config_path)

# 4. Custom preprocessing objects
import pickle

with tempfile.TemporaryDirectory() as tmpdir:
    # Save TF-IDF vectorizer
    tfidf_path = os.path.join(tmpdir, "tfidf_vectorizer.pkl")
    with open(tfidf_path, 'wb') as f:
        pickle.dump(tfidf_vectorizer, f)
    mlflow.log_artifact(tfidf_path)
    
    # Save label encoder
    le_path = os.path.join(tmpdir, "label_encoder.pkl")
    with open(le_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    mlflow.log_artifact(le_path)
```

## Model Logging

### With Feature Engineering (Preferred)

```python
from databricks.feature_engineering import FeatureEngineeringClient
import mlflow
from mlflow.models.signature import infer_signature

fe = FeatureEngineeringClient()

# Create input example and signature (REQUIRED for UC)
input_example = X_train.head(5).astype('float64')
sample_predictions = model.predict(input_example)
signature = infer_signature(input_example, sample_predictions)

# Log with Feature Engineering metadata
fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,  # CRITICAL: Embeds feature lookup spec
    registered_model_name=f"{catalog}.{schema}.{model_name}",
    input_example=input_example,
    signature=signature
)
```

### Without Feature Engineering

```python
import mlflow

# Create signature
input_example = X_train.head(5).astype('float64')
sample_predictions = model.predict(input_example)
signature = infer_signature(input_example, sample_predictions)

# Log directly with MLflow
mlflow.sklearn.log_model(
    model,
    artifact_path="model",
    signature=signature,
    input_example=input_example,
    registered_model_name=f"{catalog}.{schema}.{model_name}"
)
```

## Model Signatures

### Why Signatures Matter

| Reason | Description |
|---|---|
| **Unity Catalog Requirement** | UC models MUST have signatures |
| **Input Validation** | Prevents wrong inputs at inference |
| **Documentation** | Self-documenting model interface |
| **API Generation** | Enables automatic API schemas |

### Signature Types

```python
from mlflow.models.signature import infer_signature, ModelSignature
from mlflow.types import ColSpec, DataType, Schema

# 1. Inferred signature (RECOMMENDED)
input_example = X_train.head(5).astype('float64')
predictions = model.predict(input_example)
signature = infer_signature(input_example, predictions)

# 2. Explicit signature (if infer doesn't work)
input_schema = Schema([
    ColSpec(DataType.double, "daily_dbu"),
    ColSpec(DataType.double, "daily_cost"),
    ColSpec(DataType.double, "avg_dbu_7d")
])
output_schema = Schema([ColSpec(DataType.double)])
signature = ModelSignature(inputs=input_schema, outputs=output_schema)
```

### Common Signature Errors

| Error | Cause | Solution |
|---|---|---|
| "signature contains only inputs" | Label type unsupported | Cast label to DOUBLE/INT in base_df |
| "DECIMAL not supported" | Spark DECIMAL type | Cast to float64 before creating input_example |
| "no signature metadata" | Missing signature param | Add signature to fe.log_model() |

## Autolog Management

### When to Use Autolog

```python
# Development: Enable for convenience
mlflow.sklearn.autolog()
mlflow.xgboost.autolog()

# Production: Disable for control
mlflow.autolog(disable=True)
```

### Why Disable in Production?

- **Control**: Log only what you need
- **Performance**: Avoid unnecessary logging
- **Clarity**: Consistent metric/param names
- **Feature Engineering**: Autolog doesn't work with fe.log_model()

## Experiment Comparison

### MLflow UI

1. Navigate to **Experiments**
2. Select experiment
3. Check multiple runs
4. Click **Compare**

### Programmatic Comparison

```python
from mlflow import MlflowClient
import pandas as pd

client = MlflowClient()

# Get runs from experiment
experiment = client.get_experiment_by_name(experiment_name)
runs = client.search_runs(experiment.experiment_id)

# Convert to DataFrame
runs_df = pd.DataFrame([{
    "run_id": r.info.run_id,
    "start_time": r.info.start_time,
    **r.data.params,
    **r.data.metrics
} for r in runs])

# Compare test_r2 across runs
runs_df[["run_id", "n_estimators", "max_depth", "test_r2"]].sort_values("test_r2", ascending=False)
```

## Best Practices Summary

### Do's

| Practice | Description |
|---|---|
| ✅ Use `/Shared/` | Team visibility |
| ✅ Include signatures | Unity Catalog requirement |
| ✅ Tag comprehensively | Enables filtering |
| ✅ Log input examples | Helps with debugging |
| ✅ Use fe.log_model | Embeds feature metadata |
| ✅ Disable autolog | Control what's logged |

### Don'ts

| Anti-pattern | Reason |
|---|---|
| ❌ `/Users/` for production | Limited visibility |
| ❌ Skip signatures | UC registration fails |
| ❌ Minimal tags | Hard to find runs |
| ❌ DECIMAL in signatures | Not supported |
| ❌ Missing input_example | Signature inference fails |

## Complete Training Script Pattern

```python
import mlflow
from mlflow.models.signature import infer_signature
from databricks.feature_engineering import FeatureEngineeringClient

# Setup
mlflow.set_registry_uri("databricks-uc")
mlflow.autolog(disable=True)  # Control logging

fe = FeatureEngineeringClient()
experiment_name = f"/Shared/health_monitor_ml_{model_name}"
mlflow.set_experiment(experiment_name)

# Training logic...
model, X_train, y_train = train_model(...)

# Log everything in one run
with mlflow.start_run(run_name=f"{model_name}_{algorithm}") as run:
    # Tags
    mlflow.set_tags({
        "project": "databricks_health_monitor",
        "domain": domain,
        "model_name": model_name,
        "algorithm": algorithm,
        "feature_engineering": "unity_catalog"
    })
    
    # Parameters
    mlflow.log_params(hyperparams)
    mlflow.log_params({
        "training_samples": len(X_train),
        "feature_count": len(feature_names),
        "feature_table": feature_table
    })
    
    # Metrics
    mlflow.log_metrics(metrics)
    
    # Signature (REQUIRED)
    input_example = X_train.head(5).astype('float64')
    predictions = model.predict(input_example)
    signature = infer_signature(input_example, predictions)
    
    # Model with Feature Engineering
    fe.log_model(
        model=model,
        artifact_path="model",
        flavor=mlflow.sklearn,
        training_set=training_set,
        registered_model_name=f"{catalog}.{schema}.{model_name}",
        input_example=input_example,
        signature=signature
    )
    
    print(f"✓ Model logged: {run.info.run_id}")
```

## Validation Checklist

### Before Logging
- [ ] MLflow registry URI set to `databricks-uc`
- [ ] Autolog disabled for production
- [ ] Experiment in `/Shared/`

### During Logging
- [ ] Run name follows convention
- [ ] All required tags set
- [ ] Hyperparameters logged
- [ ] Metrics logged
- [ ] Input example created (float64!)
- [ ] Signature inferred

### After Logging
- [ ] Model visible in MLflow UI
- [ ] Model registered in Unity Catalog
- [ ] Signature shows inputs AND outputs
- [ ] Tags searchable in UI

## Next Steps

- **[09-Deployment](09-deployment.md)**: Job orchestration
- **[10-Troubleshooting](10-troubleshooting.md)**: Common issues
- **[11-Model Monitoring](11-model-monitoring.md)**: Production tracking

