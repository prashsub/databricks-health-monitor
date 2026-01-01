# 10 - Troubleshooting Guide

## Overview

This guide documents common errors encountered during ML pipeline development and their solutions. Each error includes the exact error message, root cause, and fix.

## Feature Engineering Errors

### UNRESOLVED_COLUMN

**Error:**
```
AnalysisException: [UNRESOLVED_COLUMN.WITH_SUGGESTION] A column or function parameter 
with name `sku_name` cannot be resolved. Did you mean one of the following? 
[`workspace_id`, `usage_date`, `daily_dbu`, `daily_cost`, ...]
```

**Cause:** Column name doesn't exist in feature table. Common when:
- Feature table schema changed
- Using Gold layer column name instead of feature table name
- Column aggregated away (e.g., `sku_name` aggregated to workspace level)

**Solution:**
```python
# 1. Check actual feature table schema
spark.table(feature_table).printSchema()

# 2. Use correct column names in feature_names list
feature_names = [
    "daily_dbu",          # ✓ Exists
    "daily_cost",         # ✓ Exists
    # "sku_name",         # ✗ Aggregated away
]
```

---

### Unable to find feature

**Error:**
```
ValueError: Unable to find feature 'daily_dbu' in table 'catalog.schema.cost_features'
```

**Cause:** Feature name doesn't match column name in feature table.

**Solution:**
```python
# Check available columns
available = spark.table(feature_table).columns
print(f"Available: {available}")

# Update feature_names to match
feature_names = [c for c in desired_features if c in available]
```

---

### Table does not have a primary key

**Error:**
```
AnalysisException: Table 'cost_features' does not have a primary key constraint
```

**Cause:** Feature table missing PRIMARY KEY required for feature lookups.

**Solution:**
```python
# Add primary key after table creation
spark.sql(f"""
    ALTER TABLE {catalog}.{schema}.cost_features
    ADD CONSTRAINT pk_cost_features PRIMARY KEY (workspace_id, usage_date)
""")
```

---

## MLflow Signature Errors

### Model signature contains only inputs

**Error:**
```
MlflowException: Model passed for registration contained a signature that includes only inputs.
Unity Catalog requires both input AND output signature.
```

**Cause:** Label column has unsupported data type (usually DECIMAL), preventing output signature inference.

**Solution:**
```python
# Cast label to DOUBLE or INT in base_df BEFORE create_training_set
base_df = (spark.table(feature_table)
           .select(
               "workspace_id",
               "usage_date",
               F.col("daily_cost").cast("double").alias("daily_cost")  # CRITICAL!
           ))
```

---

### DECIMAL type not supported

**Warning:**
```
WARNING databricks.ml_features.utils.signature_utils: The following features will not 
be included in the input schema because their data types are not supported by MLflow 
model signatures: ['daily_cost', 'avg_dbu_7d'] (DecimalType)
```

**Cause:** MLflow signatures don't support Spark DECIMAL type.

**Solution:**
```python
# Cast to float64 when creating input_example
input_example = X_train.head(5).astype('float64')  # Not just float
```

---

### Model did not contain any signature metadata

**Error:**
```
MlflowException: Model passed for registration did not contain any signature metadata.
```

**Cause:** `signature` and `input_example` not provided to `fe.log_model()`.

**Solution:**
```python
# ALWAYS include signature and input_example
input_example = X_train.head(5).astype('float64')
sample_predictions = model.predict(input_example)
signature = infer_signature(input_example, sample_predictions)

fe.log_model(
    model=model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,
    registered_model_name=registered_name,
    input_example=input_example,  # REQUIRED
    signature=signature           # REQUIRED
)
```

---

## Variable Name Errors

### name 'X' is not defined

**Error:**
```
NameError: name 'X' is not defined
```

**Cause:** Using `X` instead of `X_train` inconsistently. Common after train/test split.

**Solution:**
```python
# Consistent naming after split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Use X_train everywhere after split
model.fit(X_train, y_train)                    # ✓
input_example = X_train.head(5).astype('float64')  # ✓
# NOT: input_example = X.head(5)               # ✗
```

---

### name 'X_train' is not defined

**Error:**
```
NameError: name 'X_train' is not defined
```

**Cause:** `X_train` not returned from function or not in scope.

**Solution:**
```python
def prepare_and_train(training_df, feature_names, label_column):
    # ... training logic ...
    
    # MUST return X_train for signature creation
    return model, metrics, hyperparams, X_train  # Include X_train!

# Use returned X_train
model, metrics, hyperparams, X_train = prepare_and_train(...)
```

---

## Function Signature Errors

### takes X positional arguments but Y were given

**Error:**
```
TypeError: log_model_with_feature_engineering() takes 8 positional arguments but 9 were given
```

**Cause:** Function signature doesn't match call.

**Solution:**
```python
# Ensure function signature matches call
def log_model_with_feature_engineering(
    fe,
    model,
    training_set,
    X_train,           # Added parameter
    metrics,
    hyperparams,
    catalog,
    feature_schema
):
    ...

# Call with all parameters
log_model_with_feature_engineering(
    fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema
)
```

---

## Column Mapping Errors

### warehouse_id vs compute_warehouse_id

**Error:**
```
AnalysisException: Column 'warehouse_id' does not exist
```

**Cause:** Gold layer uses `compute_warehouse_id`, but feature table uses `warehouse_id`.

**Solution:**
```python
# Map Gold column to feature table column name
base_df = (spark.table(fact_table)
           .filter(F.col("compute_warehouse_id").isNotNull())
           .withColumn("warehouse_id", F.col("compute_warehouse_id"))  # Rename
           .select("warehouse_id", "query_date", label_column))
```

---

## Feature Table Errors

### Cannot create primary key because column is nullable

**Error:**
```
AnalysisException: Cannot add PRIMARY KEY constraint. Column 'workspace_id' is nullable.
```

**Cause:** NULL values exist in primary key columns.

**Solution:**
```python
# Filter NULLs before creating table
df = (source_df
      .filter(F.col("workspace_id").isNotNull())
      .filter(F.col("usage_date").isNotNull()))

# Or add NOT NULL to column definitions
spark.sql(f"""
    CREATE TABLE {table} (
        workspace_id STRING NOT NULL,
        usage_date DATE NOT NULL,
        ...
    )
""")
```

---

## Inference Errors

### Model not found in registry

**Error:**
```
mlflow.exceptions.MlflowException: Model 'catalog.schema.model_name' not found
```

**Cause:** Model not registered or name misspelled.

**Solution:**
```python
from mlflow import MlflowClient

client = MlflowClient()

# List all models to verify name
models = client.search_registered_models()
for m in models:
    print(m.name)

# Check exact name format
full_name = f"{catalog}.{schema}.{model_name}"
print(f"Looking for: {full_name}")
```

---

### fe.score_batch fails for non-FE models

**Error:**
```
ValueError: Model was not logged with feature table metadata
```

**Cause:** Model logged with `mlflow.sklearn.log_model` instead of `fe.log_model`.

**Solution:**
```python
# Use fallback scoring for non-FE models
def score_model(model_uri, scoring_df, config, fe):
    try:
        # Try FE scoring first
        return fe.score_batch(model_uri=model_uri, df=scoring_df)
    except Exception:
        # Fall back to manual scoring
        model = mlflow.pyfunc.load_model(model_uri)
        features_df = spark.table(config['feature_table'])
        X = features_df.select(config['feature_columns']).toPandas()
        predictions = model.predict(X)
        return predictions
```

---

## Job Execution Errors

### Notebook exit with error not failing job

**Symptom:** Job shows SUCCESS even when notebook printed error.

**Cause:** Using `dbutils.notebook.exit("FAILED")` instead of `raise`.

**Solution:**
```python
# DON'T do this - job will show SUCCESS
if error:
    print(f"Error: {error}")
    dbutils.notebook.exit("FAILED")

# DO this - job will show FAILED
if error:
    raise RuntimeError(f"Error: {error}")
```

---

### Widget parameter missing

**Error:**
```
IllegalArgumentException: Widget 'catalog' is not found
```

**Cause:** Job YAML `base_parameters` don't match `dbutils.widgets.get()` calls.

**Solution:**
```yaml
# YAML
base_parameters:
  catalog: ${var.catalog}
  gold_schema: ${var.gold_schema}
  feature_schema: ${var.feature_schema}
```

```python
# Python - names must match exactly
catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
feature_schema = dbutils.widgets.get("feature_schema")
```

---

## Data Quality Errors

### Empty DataFrame

**Error:**
```
ValueError: No records found for training!
```

**Cause:** Filters too restrictive or data not loaded.

**Solution:**
```python
# Debug with counts at each step
print(f"Feature table count: {spark.table(feature_table).count()}")

base_df = spark.table(feature_table).filter(F.col("label").isNotNull())
print(f"After NULL filter: {base_df.count()}")

# If 0, check why
spark.table(feature_table).select("label").show()
```

---

### Imbalanced classes

**Warning:**
```
UserWarning: The least populated class in y has only 3 samples
```

**Cause:** Severe class imbalance.

**Solution:**
```python
from sklearn.dummy import DummyClassifier

# Check class distribution
print(f"Class distribution: {pd.Series(y).value_counts()}")

# Use DummyClassifier for extreme imbalance
if min(pd.Series(y).value_counts()) < 10:
    print("⚠ Using DummyClassifier due to extreme imbalance")
    model = DummyClassifier(strategy="stratified")
else:
    model = XGBClassifier(scale_pos_weight=imbalance_ratio)
```

---

## Quick Debugging Checklist

### Feature Pipeline Issues
- [ ] Check feature table exists
- [ ] Check primary key constraint exists
- [ ] Check column names match expected
- [ ] Check no NULL values in PKs

### Training Issues
- [ ] Check base_df has label cast to correct type
- [ ] Check feature_names exist in feature table
- [ ] Check X_train consistently used after split
- [ ] Check function signatures match calls

### MLflow Issues
- [ ] Check signature includes outputs (not just inputs)
- [ ] Check input_example is float64
- [ ] Check registered_model_name format: `catalog.schema.name`

### Inference Issues
- [ ] Check model exists in registry
- [ ] Check scoring_df has only lookup keys
- [ ] Check feature tables have data

## Error Resolution Workflow

```
1. Read exact error message
2. Identify error category (FE, MLflow, Column, etc.)
3. Find matching section in this guide
4. Apply solution
5. If new error, add to this guide
```

## Next Steps

- **[11-Model Monitoring](11-model-monitoring.md)**: Track model health
- **[12-MLflow UI Guide](12-mlflow-ui-guide.md)**: Navigate experiments
- **[09-Deployment](09-deployment.md)**: Job configuration

