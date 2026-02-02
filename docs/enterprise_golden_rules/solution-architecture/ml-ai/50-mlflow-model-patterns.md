# MLflow Model Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-ML-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | ML Engineering Team |
| **Status** | Approved |

---

## Executive Summary

This document defines patterns for ML model development using MLflow on Databricks, including experiment organization, model logging with Unity Catalog, feature engineering, and batch inference. Special attention is given to common pitfalls that cause training success but inference failure.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| ML-01 | Feature tables in Unity Catalog | 🔴 Critical |
| ML-02 | output_schema required for UC models | 🔴 Critical |
| ML-03 | NaN handling at feature table creation | 🔴 Critical |
| ML-04 | MLflow experiment organization (3 experiments) | 🟡 Required |
| ML-05 | Label binarization for classifiers | 🔴 Critical |
| ML-06 | Exclude label column from features | 🔴 Critical |

---

## Rule ML-01: Feature Tables in Unity Catalog

### The Pattern

All feature tables must be created in Unity Catalog with proper documentation:

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Create feature table
fe.create_table(
    name=f"{catalog}.{schema}.cost_prediction_features",
    primary_keys=["workspace_id", "date"],
    timestamp_keys=["date"],
    df=features_df,
    description="Features for workspace cost prediction model. Business: Predicts next-day cost. Technical: Rolling 7/30 day aggregations.",
    tags={"domain": "cost", "model": "cost_predictor"}
)
```

---

## Rule ML-02: output_schema for Unity Catalog Models

### The Problem

Unity Catalog requires explicit output schema. Missing `output_schema` causes registration failures.

### The Pattern

```python
from mlflow.models.signature import ColSpec, Schema, DataType
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Define output schema based on model type
if model_type == "regression":
    output_schema = Schema([ColSpec(DataType.double)])
elif model_type == "classification":
    output_schema = Schema([ColSpec(DataType.long)])
elif model_type == "anomaly_detection":
    output_schema = Schema([ColSpec(DataType.long)])  # -1 or 1

# Log model with Feature Engineering client
fe.log_model(
    model=trained_model,
    artifact_path="model",
    flavor=mlflow.sklearn,  # ✅ Required flavor parameter
    training_set=training_set,
    infer_input_example=True,
    output_schema=output_schema,  # ✅ Required for UC models
    registered_model_name=f"{catalog}.{schema}.{model_name}"
)
```

### Output Schema Reference

| Model Type | Output DataType | Example |
|------------|-----------------|---------|
| Regression | `DataType.double` | Cost prediction |
| Binary Classification | `DataType.long` | Churn prediction |
| Multi-class Classification | `DataType.long` | Category prediction |
| Anomaly Detection | `DataType.long` | -1/1 for anomaly |
| Probability | `DataType.double` | Score 0-1 |

---

## Rule ML-03: NaN Handling at Feature Table Creation

### The Problem

Training may succeed because preprocessing fills NaN, but batch inference (`fe.score_batch()`) passes raw feature table data. sklearn models crash on NaN; XGBoost handles it natively.

```python
# Training works (preprocessing fills NaN)
X_train = prepare_training_data(df)  # Fills NaN
model.fit(X_train, y_train)  # Works!

# Inference fails (raw data has NaN)
predictions = fe.score_batch(model_uri, feature_table)
# Error: ValueError: Input X contains NaN (sklearn GradientBoostingRegressor)
```

### The Solution: Clean at Source

**Always clean NaN/Inf at feature table creation, not just training:**

```python
from pyspark.sql import functions as F

def create_clean_features(df, numeric_columns, default_values=None):
    """
    Create feature table with NaN/Inf cleaned at source.
    
    CRITICAL: Clean here, not in training preprocessing.
    """
    default_values = default_values or {}
    
    for col in numeric_columns:
        default = default_values.get(col, 0.0)
        df = df.withColumn(
            col,
            F.when(
                F.col(col).isNull() | 
                F.isnan(F.col(col)) | 
                F.col(col).isin([float('inf'), float('-inf')]),
                F.lit(default)
            ).otherwise(F.col(col))
        )
    
    return df


# Usage
features_df = create_clean_features(
    raw_features_df,
    numeric_columns=["cost_7d", "cost_30d", "dbu_avg"],
    default_values={"cost_7d": 0.0, "cost_30d": 0.0, "dbu_avg": 0.0}
)

# Now safe to create feature table
fe.create_table(
    name=f"{catalog}.{schema}.cost_features",
    df=features_df,
    ...
)
```

---

## Rule ML-05: Label Binarization for Classifiers

### The Problem

XGBClassifier requires 0/1 integer labels, not continuous rates (0.0-1.0).

```python
# ❌ WRONG: Continuous labels
df = df.withColumn("high_cost", col("cost_growth_rate"))  # 0.0 to 1.0
model.fit(X, df["high_cost"])
# Error: base_score must be in (0,1) for objective binary:logistic
```

### The Solution

```python
# ✅ CORRECT: Binary labels
THRESHOLD = 0.10  # 10% growth = high cost

df = df.withColumn(
    "high_cost_label",
    F.when(F.col("cost_growth_rate") > THRESHOLD, 1).otherwise(0)
)

# Check label distribution before training
label_dist = df.groupBy("high_cost_label").count().collect()
print(f"Label distribution: {label_dist}")

# Skip if single class
if len(label_dist) < 2:
    print("⚠ Skipping model: single class in data")
    return None

model.fit(X, df["high_cost_label"])  # ✅ Works
```

---

## Rule ML-06: Exclude Label from Features

### The Problem

Including the label column in features causes data leakage and inference failure.

```python
# ❌ WRONG: Label included in features
features = df.select("feature1", "feature2", "label_column")  # Label leaks!
model.fit(features, labels)

# At inference time, label column doesn't exist!
# Error: Column 'label_column' not found
```

### The Solution

```python
def get_feature_columns(df, exclude_columns: list) -> list:
    """Get feature columns excluding labels and non-features."""
    exclude = set(exclude_columns + [
        "primary_key_col",
        "timestamp_col",
        "label_column"  # ✅ Always exclude
    ])
    return [c for c in df.columns if c not in exclude]


# Usage
LABEL_COLUMN = "high_cost_label"

feature_columns = get_feature_columns(
    features_df,
    exclude_columns=[LABEL_COLUMN, "workspace_id", "date"]
)

X = features_df.select(feature_columns).toPandas()
y = features_df.select(LABEL_COLUMN).toPandas()[LABEL_COLUMN]

model.fit(X, y)
```

---

## Rule ML-04: MLflow Experiment Organization

### The Pattern: Three Experiments

| Experiment | Naming Pattern | Purpose |
|------------|----------------|---------|
| **Development** | `/Shared/{project}_ml_{model}_development` | Feature engineering, model iteration |
| **Evaluation** | `/Shared/{project}_ml_{model}_evaluation` | Formal evaluation runs |
| **Deployment** | `/Shared/{project}_ml_{model}_deployment` | Production model tracking |

```python
def setup_experiment(project: str, model_name: str, stage: str) -> str:
    """
    Set up MLflow experiment with proper naming.
    
    stage: 'development', 'evaluation', or 'deployment'
    """
    experiment_name = f"/Shared/{project}_ml_{model_name}_{stage}"
    
    mlflow.set_experiment(experiment_name)
    
    return experiment_name


# Usage
setup_experiment("health_monitor", "cost_predictor", "development")

with mlflow.start_run(run_name="feature_engineering_v2"):
    # Development work
    ...
```

---

## Complete Training Pattern

```python
import mlflow
from mlflow.models.signature import ColSpec, Schema, DataType
from databricks.feature_engineering import FeatureEngineeringClient
from xgboost import XGBClassifier
from pyspark.sql import functions as F


def train_cost_predictor(
    spark,
    catalog: str,
    schema: str,
    model_name: str = "cost_predictor"
):
    """
    Complete training pattern following all ML rules.
    """
    fe = FeatureEngineeringClient()
    
    # Step 1: Set up experiment
    experiment_name = f"/Shared/health_monitor_ml_{model_name}_development"
    mlflow.set_experiment(experiment_name)
    
    # Step 2: Load feature table (already NaN-cleaned per Rule ML-03)
    feature_table = f"{catalog}.{schema}.cost_prediction_features"
    features_df = spark.table(feature_table)
    
    # Step 3: Define label with binarization (Rule ML-05)
    LABEL_COLUMN = "high_cost_label"
    THRESHOLD = 0.10
    
    features_df = features_df.withColumn(
        LABEL_COLUMN,
        F.when(F.col("cost_growth_rate") > THRESHOLD, 1).otherwise(0)
    )
    
    # Step 4: Check label distribution
    label_dist = features_df.groupBy(LABEL_COLUMN).count().collect()
    if len(label_dist) < 2:
        print(f"⚠ Skipping: single class in data")
        return None
    
    # Step 5: Get feature columns (exclude label per Rule ML-06)
    PRIMARY_KEYS = ["workspace_id", "date"]
    EXCLUDE_COLS = PRIMARY_KEYS + [LABEL_COLUMN, "cost_growth_rate"]
    
    feature_columns = [c for c in features_df.columns if c not in EXCLUDE_COLS]
    
    # Step 6: Prepare training data
    pdf = features_df.select(feature_columns + [LABEL_COLUMN]).toPandas()
    X = pdf[feature_columns]
    y = pdf[LABEL_COLUMN]
    
    # Step 7: Train model
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    model.fit(X, y)
    
    # Step 8: Create FeatureLookup for inference
    from databricks.feature_engineering import FeatureLookup
    
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_columns,
            lookup_key=PRIMARY_KEYS
        )
    ]
    
    # Step 9: Create training set (for feature lineage)
    training_set = fe.create_training_set(
        df=features_df.select(PRIMARY_KEYS + [LABEL_COLUMN]),
        feature_lookups=feature_lookups,
        label=LABEL_COLUMN,
        exclude_columns=[]
    )
    
    # Step 10: Log model with output_schema (Rule ML-02)
    with mlflow.start_run(run_name=f"{model_name}_training"):
        mlflow.log_param("threshold", THRESHOLD)
        mlflow.log_param("n_features", len(feature_columns))
        mlflow.log_metric("accuracy", model.score(X, y))
        
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            infer_input_example=True,
            output_schema=Schema([ColSpec(DataType.long)]),  # Classification
            registered_model_name=f"{catalog}.{schema}.{model_name}"
        )
        
        print(f"✅ Model logged: {catalog}.{schema}.{model_name}")
    
    return model
```

---

## Batch Inference Pattern

```python
def run_batch_inference(
    spark,
    fe: FeatureEngineeringClient,
    catalog: str,
    schema: str,
    model_name: str
):
    """
    Batch inference using feature table.
    
    Note: fe.score_batch passes raw feature table data.
    NaN handling must be at feature table level.
    """
    # Get latest model version
    model_uri = f"models:/{catalog}.{schema}.{model_name}@champion"
    
    # Load scoring data (just primary keys)
    scoring_df = spark.table(f"{catalog}.{schema}.scoring_data")
    
    # Score using feature table lookup
    predictions = fe.score_batch(
        model_uri=model_uri,
        df=scoring_df
    )
    
    # Write predictions
    predictions.write.mode("overwrite").saveAsTable(
        f"{catalog}.{schema}.{model_name}_predictions"
    )
    
    return predictions
```

---

## Validation Checklist

### Feature Engineering
- [ ] Feature table in Unity Catalog
- [ ] NaN/Inf cleaned at table creation (not training)
- [ ] Primary keys defined
- [ ] Table documented with business context

### Model Training
- [ ] Label binarized for classifiers (0/1 integers)
- [ ] Label column excluded from features
- [ ] Label distribution checked (not single class)
- [ ] output_schema defined for model type
- [ ] flavor parameter included in fe.log_model()

### Inference
- [ ] Model registered in Unity Catalog
- [ ] Champion alias assigned
- [ ] fe.score_batch tested successfully
- [ ] Predictions written to output table

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Input X contains NaN` | NaN in feature table | Clean at table creation |
| `base_score must be in (0,1)` | Continuous labels | Binarize labels (0/1) |
| `Column not found` during inference | Label in features | Exclude label column |
| `Model contains only inputs` | Missing output_schema | Add output_schema parameter |
| `Missing flavor` | No flavor in log_model | Add flavor=mlflow.sklearn |
| Experiment not found | Path issue | Use `/Shared/` prefix |

---

## Related Documents

- [GenAI Agent Patterns](51-genai-agent-patterns.md)
- [Feature Engineering Patterns](52-feature-engineering.md)
- [Lakehouse Monitoring](../monitoring/41-lakehouse-monitoring.md)

---

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Databricks Feature Engineering](https://docs.databricks.com/machine-learning/feature-store/)
- [Unity Catalog Model Registry](https://docs.databricks.com/machine-learning/model-registry-uc/)
