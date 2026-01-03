# 04 - Model Training

## Overview

Model training on Databricks follows a standardized pattern that ensures:
- Consistent feature usage via Feature Engineering
- Proper model signatures for Unity Catalog
- Full experiment tracking with MLflow
- Reproducible training runs

## Training Script Template

Every training script follows this structure:

```python
# Databricks notebook source

"""
Model: {model_name}
Domain: {domain}
Type: {regression|classification|anomaly_detection}
Description: {purpose}
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingRegressor  # or other algorithm
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

mlflow.set_registry_uri("databricks-uc")

# =============================================================================
# PARAMETERS
# =============================================================================

def get_parameters():
    """Get job parameters from widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Configuration:")
    print(f"  Catalog: {catalog}")
    print(f"  Gold Schema: {gold_schema}")
    print(f"  Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema

# =============================================================================
# MLFLOW SETUP
# =============================================================================

def setup_mlflow(catalog: str, feature_schema: str, model_name: str) -> str:
    """Set up MLflow experiment."""
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    
    try:
        mlflow.set_experiment(experiment_name)
    except:
        mlflow.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)
    
    print(f"  ✓ Experiment: {experiment_name}")
    return experiment_name

# =============================================================================
# TRAINING SET CREATION
# =============================================================================

def create_training_set_with_features(
    spark: SparkSession,
    fe: FeatureEngineeringClient,
    catalog: str,
    gold_schema: str,
    feature_schema: str
):
    """
    Create training set using Feature Engineering.
    
    CRITICAL PATTERN:
    1. base_df contains ONLY: primary keys + label
    2. Label MUST be cast to DOUBLE (regression) or INT (classification)
    3. Features are looked up automatically
    """
    feature_table = f"{catalog}.{feature_schema}.{FEATURE_TABLE_NAME}"
    
    print(f"\nCreating training set...")
    print(f"  Feature table: {feature_table}")
    
    # =================================================================
    # STEP 1: Create base DataFrame with PKs + label
    # CRITICAL: Cast label to correct type HERE
    # =================================================================
    base_df = (spark.table(feature_table)
               .select(
                   PRIMARY_KEY_COLUMNS[0],
                   PRIMARY_KEY_COLUMNS[1],
                   F.col(LABEL_COLUMN).cast("double").alias(LABEL_COLUMN)  # CRITICAL!
               )
               .filter(F.col(PRIMARY_KEY_COLUMNS[0]).isNotNull())
               .filter(F.col(PRIMARY_KEY_COLUMNS[1]).isNotNull())
               .filter(F.col(LABEL_COLUMN).isNotNull())
               .distinct())
    
    record_count = base_df.count()
    print(f"  Records with label: {record_count:,}")
    
    if record_count == 0:
        raise ValueError("No records found for training!")
    
    # =================================================================
    # STEP 2: Define feature lookups
    # =================================================================
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=FEATURE_NAMES,
            lookup_key=PRIMARY_KEY_COLUMNS
        )
    ]
    
    # =================================================================
    # STEP 3: Create training set
    # =================================================================
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label=LABEL_COLUMN,
        exclude_columns=PRIMARY_KEY_COLUMNS
    )
    
    training_df = training_set.load_df()
    print(f"  ✓ Training set created with {len(FEATURE_NAMES)} features")
    
    return training_set, training_df

# =============================================================================
# MODEL TRAINING
# =============================================================================

def prepare_and_train(training_df, feature_names, label_column):
    """
    Prepare features and train model.
    
    Returns: (model, metrics, hyperparams, X_train)
    """
    print("\nPreparing training data...")
    
    # Convert to pandas
    pdf = training_df.select(feature_names + [label_column]).toPandas()
    
    # Handle data types
    for col in feature_names:
        pdf[col] = pd.to_numeric(pdf[col], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    # Split features and label
    X = pdf[feature_names].astype('float64')  # Ensure float64
    y = pdf[label_column].astype('float64')   # CRITICAL: Cast label!
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"  Training samples: {len(X_train):,}")
    print(f"  Test samples: {len(X_test):,}")
    
    # =================================================================
    # TRAIN MODEL
    # =================================================================
    print("\nTraining model...")
    
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "random_state": 42
    }
    
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    # =================================================================
    # EVALUATE
    # =================================================================
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    y_pred = model.predict(X_test)
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    mae = np.mean(np.abs(y_test - y_pred))
    
    metrics = {
        "train_r2": train_score,
        "test_r2": test_score,
        "rmse": rmse,
        "mae": mae,
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    print(f"  ✓ Training complete")
    print(f"    Train R²: {train_score:.4f}")
    print(f"    Test R²: {test_score:.4f}")
    print(f"    RMSE: {rmse:.4f}")
    
    return model, metrics, hyperparams, X_train

# =============================================================================
# MODEL LOGGING
# =============================================================================

def log_model_with_feature_engineering(
    fe: FeatureEngineeringClient,
    model,
    training_set,
    X_train: pd.DataFrame,
    metrics: dict,
    hyperparams: dict,
    catalog: str,
    feature_schema: str,
    model_name: str,
    domain: str,
    algorithm: str
):
    """
    Log model to Unity Catalog with Feature Engineering metadata.
    
    CRITICAL: Must include:
    - training_set: Embeds feature lookup metadata
    - signature: Required for Unity Catalog
    - input_example: Helps with signature inference
    """
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=f"{model_name}_{algorithm}") as run:
        # =================================================================
        # SET TAGS
        # =================================================================
        mlflow.set_tags({
            "project": "databricks_health_monitor",
            "domain": domain,
            "model_name": model_name,
            "algorithm": algorithm,
            "feature_engineering": "unity_catalog"
        })
        
        # =================================================================
        # LOG PARAMETERS AND METRICS
        # =================================================================
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        # =================================================================
        # CREATE SIGNATURE (CRITICAL!)
        # =================================================================
        input_example = X_train.head(5).astype('float64')
        sample_predictions = model.predict(input_example)
        signature = infer_signature(input_example, sample_predictions)
        
        # =================================================================
        # LOG MODEL WITH FEATURE METADATA
        # =================================================================
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,  # CRITICAL: Embeds feature lookups
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"  ✓ Model logged")
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Registered: {registered_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "metrics": metrics
        }

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 80)
    print(f"{MODEL_NAME.upper()} - TRAINING")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    
    # Setup MLflow
    setup_mlflow(catalog, feature_schema, MODEL_NAME)
    
    # Create training set
    training_set, training_df = create_training_set_with_features(
        spark, fe, catalog, gold_schema, feature_schema
    )
    
    # Train model
    model, metrics, hyperparams, X_train = prepare_and_train(
        training_df, FEATURE_NAMES, LABEL_COLUMN
    )
    
    # Log model
    result = log_model_with_feature_engineering(
        fe, model, training_set, X_train, metrics, hyperparams,
        catalog, feature_schema, MODEL_NAME, DOMAIN, ALGORITHM
    )
    
    print("\n" + "=" * 80)
    print(f"✓ {MODEL_NAME} TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    dbutils.notebook.exit("SUCCESS")

if __name__ == "__main__":
    main()
```

## Algorithm Selection

### By Model Type

| Model Type | Algorithm | When to Use |
|---|---|---|
| **Regression** | Gradient Boosting Regressor | Continuous target, need feature importance |
| **Binary Classification** | XGBoost Classifier | 0/1 target, imbalanced data OK |
| **Multi-class Classification** | Random Forest Classifier | Multiple classes, interpretability needed |
| **Anomaly Detection** | Isolation Forest | No labels, detect outliers |
| **Multi-label Classification** | XGBoost MultiOutput | Multiple binary targets |

### Algorithm Configurations

#### Gradient Boosting Regressor (Regression)

```python
from sklearn.ensemble import GradientBoostingRegressor

hyperparams = {
    "n_estimators": 100,      # Number of boosting stages
    "max_depth": 6,           # Maximum tree depth
    "learning_rate": 0.1,     # Shrinkage parameter
    "min_samples_split": 10,  # Min samples to split node
    "min_samples_leaf": 5,    # Min samples in leaf
    "random_state": 42        # Reproducibility
}

model = GradientBoostingRegressor(**hyperparams)
model.fit(X_train, y_train)

# Metrics
metrics = {
    "train_r2": model.score(X_train, y_train),
    "test_r2": model.score(X_test, y_test),
    "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
    "mae": mean_absolute_error(y_test, y_pred)
}
```

#### XGBoost Classifier (Classification)

> ⚠️ **CRITICAL: Label Binarization Required**
> 
> XGBClassifier requires **binary labels (0 or 1)**. If your label column contains 
> continuous values (rates, ratios), you MUST binarize them first!

**Common Continuous Labels That Need Binarization:**

| Label Column | Type | Binarization Needed |
|-------------|------|---------------------|
| `failure_rate` | Continuous (0-1) | ✅ Yes → `high_failure_rate` |
| `success_rate` | Continuous (0-1) | ✅ Yes → `high_success_rate` |
| `spill_rate` | Continuous (0-1) | ✅ Yes → `high_spill_rate` |
| `is_failed` | Already binary (0/1) | ❌ No |
| `class_label` | Integer classes | ❌ No |

**Label Binarization Pattern:**

```python
from pyspark.sql.functions import when, col

# STEP 1: Identify continuous rate/ratio columns
LABEL_COLUMN = "failure_rate"  # Original continuous column (0.0-1.0)

# STEP 2: Create binary label BEFORE training
training_df = training_df.withColumn(
    "high_failure_rate",  # New binary column name
    when(col(LABEL_COLUMN) > 0.2, 1).otherwise(0)  # Threshold binarization
)

# STEP 3: Use binary column for training
X_train, X_test, y_train, y_test = prepare_training_data(
    training_df, 
    available_features, 
    "high_failure_rate",  # Use the binary column!
    cast_label_to="int", 
    stratify=True
)
```

**Standard Thresholds by Use Case:**

| Use Case | Threshold | Meaning |
|----------|-----------|---------|
| Failure prediction | > 0.2 | High failure risk |
| Success prediction | > 0.7 | High success likelihood |
| SLA compliance | > 0.1 | At-risk for breach |
| Cache efficiency | > 0.3 | Poor cache hit rate |
| Serverless adoption | > 0.5 | Good serverless candidate |

**XGBoost Classifier Configuration:**

```python
from xgboost import XGBClassifier

hyperparams = {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "objective": "binary:logistic",
    "eval_metric": "logloss",  # Use logloss for binary classification
    "random_state": 42
}

model = XGBClassifier(**hyperparams)
model.fit(X_train, y_train)  # y_train MUST be 0/1 values!

# Metrics
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "precision": precision_score(y_test, y_pred),
    "recall": recall_score(y_test, y_pred),
    "f1": f1_score(y_test, y_pred),
    "auc_roc": roc_auc_score(y_test, y_prob)
}
```

#### Isolation Forest (Anomaly Detection)

```python
from sklearn.ensemble import IsolationForest

hyperparams = {
    "n_estimators": 100,
    "contamination": 0.05,   # Expected anomaly ratio
    "max_samples": "auto",
    "random_state": 42
}

model = IsolationForest(**hyperparams)
model.fit(X_train)  # No labels needed!

# Predictions: -1 = anomaly, 1 = normal
predictions = model.predict(X_train)
scores = model.decision_function(X_train)

# Metrics
anomaly_rate = (predictions == -1).mean()

metrics = {
    "anomaly_rate": anomaly_rate,
    "training_samples": len(X_train),
    "avg_anomaly_score": scores[predictions == -1].mean() if anomaly_rate > 0 else 0
}
```

#### Random Forest Classifier (Multi-class)

```python
from sklearn.ensemble import RandomForestClassifier

hyperparams = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "class_weight": "balanced",  # Handle imbalance
    "random_state": 42
}

model = RandomForestClassifier(**hyperparams)
model.fit(X_train, y_train)

# Metrics
y_pred = model.predict(X_test)

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "weighted_f1": f1_score(y_test, y_pred, average='weighted'),
    "macro_f1": f1_score(y_test, y_pred, average='macro')
}
```

## Handling Imbalanced Data

### Class Imbalance Detection

```python
def check_class_balance(y_train):
    """Check and report class distribution."""
    class_counts = pd.Series(y_train).value_counts()
    imbalance_ratio = class_counts.max() / class_counts.min()
    
    print(f"\nClass distribution:")
    for cls, count in class_counts.items():
        print(f"  Class {cls}: {count:,} ({count/len(y_train)*100:.1f}%)")
    
    if imbalance_ratio > 10:
        print(f"  ⚠ Severe imbalance detected (ratio: {imbalance_ratio:.1f})")
        return True
    return False
```

### Handling Strategies

```python
# Strategy 1: Class weights
model = XGBClassifier(scale_pos_weight=imbalance_ratio)

# Strategy 2: Balanced class weights
model = RandomForestClassifier(class_weight="balanced")

# Strategy 3: DummyClassifier for extreme cases
from sklearn.dummy import DummyClassifier

if positive_rate < 0.01:  # < 1% positive class
    print("⚠ Using DummyClassifier due to extreme imbalance")
    model = DummyClassifier(strategy="stratified")
```

## MLflow Model Signatures

### Why Signatures Matter

Unity Catalog requires explicit model signatures for:
- Input validation at inference
- Documentation of model interface
- API generation for model serving

### Creating Signatures

```python
from mlflow.models.signature import infer_signature

# CRITICAL: Create input_example from actual training data
input_example = X_train.head(5).astype('float64')

# CRITICAL: Generate sample predictions for output schema
sample_predictions = model.predict(input_example)

# CRITICAL: Infer signature from both
signature = infer_signature(input_example, sample_predictions)

# Signature structure:
# inputs:
#   - name: feature1, type: double
#   - name: feature2, type: double
#   - ...
# outputs:
#   - type: double  (for regression)
#   OR
#   - type: integer (for classification)
```

### Common Signature Errors

| Error | Cause | Solution |
|---|---|---|
| "signature contains only inputs" | Label column has unsupported type | Cast label to DOUBLE/INT in base_df |
| "DECIMAL type not supported" | Spark DECIMAL in features | Cast to DOUBLE before Pandas |
| "signature metadata missing" | fe.log_model missing params | Add signature and input_example |

## Experiment Organization

### Naming Convention

```
/Shared/health_monitor_ml_{model_name}

Examples:
/Shared/health_monitor_ml_cost_anomaly_detector
/Shared/health_monitor_ml_budget_forecaster
/Shared/health_monitor_ml_failure_predictor
```

### Run Naming

```python
run_name = f"{model_name}_{algorithm}_v{version}_{timestamp}"

# Examples:
"cost_anomaly_detector_isolation_forest_v1_20260101_030000"
"budget_forecaster_gradient_boosting_v1_20260101_030500"
```

### Tags

Every run should include these tags:

```python
mlflow.set_tags({
    "project": "databricks_health_monitor",
    "domain": "cost|security|performance|reliability|quality",
    "model_name": "model_name",
    "model_type": "regression|classification|anomaly_detection",
    "algorithm": "gradient_boosting|isolation_forest|xgboost|random_forest",
    "use_case": "specific_use_case",
    "feature_engineering": "unity_catalog",
    "training_data": "feature_table_name"
})
```

## Hyperparameter Logging

### Standard Parameters

```python
mlflow.log_params({
    # Algorithm hyperparameters
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    
    # Data parameters
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "feature_count": len(feature_names),
    
    # Feature Engineering
    "feature_table": feature_table_name,
    "primary_keys": str(primary_keys),
    
    # Reproducibility
    "random_state": 42,
    "test_size": 0.2
})
```

## Metrics Logging

### By Model Type

```python
# Regression
mlflow.log_metrics({
    "train_r2": train_r2,
    "test_r2": test_r2,
    "rmse": rmse,
    "mae": mae,
    "mape": mape  # If applicable
})

# Classification
mlflow.log_metrics({
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1_score,
    "auc_roc": auc_roc,
    "log_loss": log_loss
})

# Anomaly Detection
mlflow.log_metrics({
    "anomaly_rate": anomaly_rate,
    "avg_anomaly_score": avg_score,
    "training_samples": len(X_train)
})
```

## Complete Training Examples

### Regression Example: Budget Forecaster

```python
# Configuration
MODEL_NAME = "budget_forecaster"
DOMAIN = "cost"
ALGORITHM = "gradient_boosting"
FEATURE_TABLE_NAME = "cost_features"
PRIMARY_KEY_COLUMNS = ["workspace_id", "usage_date"]
LABEL_COLUMN = "daily_cost"
FEATURE_NAMES = [
    "daily_dbu", "avg_dbu_7d", "avg_dbu_30d",
    "dbu_change_pct_1d", "dbu_change_pct_7d", "z_score_7d",
    "serverless_adoption_ratio", "jobs_on_all_purpose_cost",
    "is_weekend", "day_of_week"
]

# base_df with label cast to DOUBLE
base_df = (spark.table(feature_table)
           .select(
               "workspace_id", "usage_date",
               F.col("daily_cost").cast("double").alias("daily_cost")
           )
           .filter(F.col("daily_cost").isNotNull()))
```

### Classification Example: Failure Predictor

```python
# Configuration
MODEL_NAME = "failure_predictor"
DOMAIN = "reliability"
ALGORITHM = "xgboost"
FEATURE_TABLE_NAME = "reliability_features"
PRIMARY_KEY_COLUMNS = ["job_id", "run_date"]
LABEL_COLUMN = "prev_day_failed"
FEATURE_NAMES = [
    "total_runs", "avg_duration_sec", "success_rate", "failure_rate",
    "duration_cv", "rolling_failure_rate_30d", "is_weekend", "day_of_week"
]

# base_df with label cast to INT (binary classification)
base_df = (spark.table(feature_table)
           .select(
               "job_id", "run_date",
               F.col("prev_day_failed").cast("int").alias("prev_day_failed")
           )
           .filter(F.col("prev_day_failed").isNotNull()))
```

### Anomaly Detection Example: Cost Anomaly

```python
# Configuration
MODEL_NAME = "cost_anomaly_detector"
DOMAIN = "cost"
ALGORITHM = "isolation_forest"
FEATURE_TABLE_NAME = "cost_features"
PRIMARY_KEY_COLUMNS = ["workspace_id", "usage_date"]
LABEL_COLUMN = None  # Unsupervised!
FEATURE_NAMES = [
    "daily_dbu", "daily_cost", "avg_dbu_7d", "avg_dbu_30d",
    "dbu_change_pct_1d", "dbu_change_pct_7d", "z_score_7d"
]

# base_df with NO label (unsupervised)
base_df = (spark.table(feature_table)
           .select("workspace_id", "usage_date")
           .distinct())

# Note: For unsupervised, signature inference is different
input_example = X_train.head(5).astype('float64')
predictions = model.predict(input_example)  # Returns -1 or 1
scores = model.decision_function(input_example)  # Returns continuous score

# Use scores for signature (more informative)
signature = infer_signature(input_example, scores)
```

## Validation Checklist

### Before Training
- [ ] Feature table exists with PRIMARY KEY
- [ ] Feature names match actual columns
- [ ] Label column exists and has correct type
- [ ] MLflow experiment is set

### During Training
- [ ] base_df has label cast to DOUBLE/INT
- [ ] NULLs filtered from primary keys
- [ ] Feature lookups use correct lookup_key
- [ ] Training set excludes primary keys

### After Training
- [ ] Model has signature (check MLflow UI)
- [ ] Model registered in Unity Catalog
- [ ] Metrics logged and reasonable
- [ ] Run tagged with metadata

## Next Steps

- **[05-Model Registry](05-model-registry.md)**: Model versioning and staging
- **[06-Batch Inference](06-batch-inference.md)**: Using trained models
- **[12-MLflow Experiments](12-mlflow-experiments.md)**: UI navigation

