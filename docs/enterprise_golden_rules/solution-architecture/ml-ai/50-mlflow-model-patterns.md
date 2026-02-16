# MLflow Model Patterns

> **Document Owner:** ML Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

Patterns for ML model development using MLflow on Databricks, including feature engineering, model logging, and batch inference.

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **ML-01** | Feature tables in Unity Catalog | Critical |
| **ML-02** | output_schema required for UC models | Critical |
| **ML-03** | NaN handling at feature table creation | Critical |
| **ML-04** | MLflow experiment organization | Required |
| **ML-05** | Label binarization for classifiers | Critical |
| **ML-06** | Exclude label column from features | Critical |

---

## NaN Handling at Source

**Clean NaN at feature table creation, not training.** Training preprocessing fills NaN, but `fe.score_batch()` passes raw data.

```python
from pyspark.sql import functions as F

def create_clean_features(df, numeric_columns):
    """Clean NaN/Inf at source - not just training."""
    for col in numeric_columns:
        df = df.withColumn(
            col,
            F.when(
                F.col(col).isNull() | F.isnan(F.col(col)),
                F.lit(0.0)
            ).otherwise(F.col(col))
        )
    return df
```

---

## output_schema Required

Unity Catalog models require explicit output schema.

```python
from mlflow.models.signature import ColSpec, Schema, DataType

# Define based on model type
output_schema = Schema([ColSpec(DataType.double)])  # Regression
output_schema = Schema([ColSpec(DataType.long)])    # Classification

fe.log_model(
    model=trained_model,
    artifact_path="model",
    flavor=mlflow.sklearn,  # Required
    output_schema=output_schema,  # Required
    registered_model_name=f"{catalog}.{schema}.{model_name}"
)
```

| Model Type | DataType |
|------------|----------|
| Regression | `DataType.double` |
| Classification | `DataType.long` |
| Anomaly Detection | `DataType.long` |

---

## Label Binarization

XGBClassifier requires 0/1 integers, not continuous rates.

```python
# ❌ WRONG: Continuous
df.withColumn("label", col("rate"))  # 0.0 to 1.0

# ✅ CORRECT: Binary
df.withColumn("label", 
    F.when(F.col("rate") > 0.10, 1).otherwise(0))

# Check distribution before training
if len(df.groupBy("label").count().collect()) < 2:
    print("⚠ Single class - skip training")
```

---

## Exclude Label from Features

```python
def get_feature_columns(df, exclude_columns):
    """Get features excluding labels and keys."""
    return [c for c in df.columns if c not in exclude_columns]

feature_cols = get_feature_columns(
    df, 
    exclude_columns=["label", "primary_key", "timestamp"]
)
```

---

## Experiment Organization

| Experiment | Path | Purpose |
|------------|------|---------|
| Development | `/Shared/{project}_ml_{model}_development` | Iteration |
| Evaluation | `/Shared/{project}_ml_{model}_evaluation` | Formal eval |
| Deployment | `/Shared/{project}_ml_{model}_deployment` | Production |

---

## Batch Inference

```python
def run_inference(fe, catalog, schema, model_name):
    model_uri = f"models:/{catalog}.{schema}.{model_name}@champion"
    scoring_df = spark.table(f"{catalog}.{schema}.scoring_data")
    
    predictions = fe.score_batch(model_uri=model_uri, df=scoring_df)
    predictions.write.mode("overwrite").saveAsTable(
        f"{catalog}.{schema}.{model_name}_predictions"
    )
```

---

## Validation Checklist

### Feature Engineering
- [ ] Feature table in Unity Catalog
- [ ] NaN/Inf cleaned at table creation
- [ ] Primary keys defined

### Training
- [ ] Labels binarized (0/1)
- [ ] Label excluded from features
- [ ] Label distribution checked
- [ ] output_schema defined

### Inference
- [ ] Model registered in UC
- [ ] Champion alias assigned
- [ ] fe.score_batch tested

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Input X contains NaN` | NaN in features | Clean at source |
| `base_score must be in (0,1)` | Continuous labels | Binarize (0/1) |
| `Column not found` | Label in features | Exclude label |
| `Missing output_schema` | UC requirement | Add parameter |

---

## References

- [MLflow](https://mlflow.org/docs/latest/)
- [Feature Engineering](https://docs.databricks.com/machine-learning/feature-store/)
- [UC Model Registry](https://docs.databricks.com/machine-learning/model-registry-uc/)
