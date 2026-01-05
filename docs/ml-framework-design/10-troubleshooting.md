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

### Input X contains NaN (sklearn models fail at inference)

**Error:**
```
ValueError: Input X contains NaN.
GradientBoostingRegressor does not accept missing values encoded as NaN natively.
For supervised learning, you might want to consider sklearn.ensemble.HistGradientBoostingClassifier
and Regressor which accept missing values encoded as NaNs natively.
```

**Cause:** Training succeeds but inference fails because:
1. **Training flow**: Feature table → `prepare_training_data()` → `fillna(0)` → Model trains on clean data
2. **Inference flow**: Feature table → `fe.score_batch()` → **No NaN handling** → Model receives NaN → Crash

XGBoost handles NaN natively, but sklearn's `GradientBoostingRegressor` does NOT.

**Root Cause Discovery (Jan 2026):**
- `query_performance_forecaster`, `warehouse_optimizer`, `cluster_capacity_planner` all use sklearn regressors
- Window functions (rolling averages) can produce NaN for first rows
- Division operations can produce NaN/Inf
- Feature table had partial `fillna()` coverage but missed some columns

**Solution:** Fill NaN/Inf at the SOURCE (feature table creation) to ensure training/inference consistency:

```python
# In create_feature_table() - clean ALL numeric columns
def clean_numeric(col_name):
    """Replace NaN and Infinity with 0.0"""
    return F.when(
        F.col(col_name).isNull() | 
        F.isnan(F.col(col_name)) |
        (F.col(col_name) == float('inf')) |
        (F.col(col_name) == float('-inf')),
        F.lit(0.0)
    ).otherwise(F.col(col_name))

# Apply to all numeric columns during feature table creation
for field in df.schema.fields:
    if field.name not in non_cast_cols:
        if isinstance(field.dataType, (IntegerType, LongType, FloatType, DecimalType)):
            df = df.withColumn(field.name, F.col(field.name).cast("double"))
            df = df.withColumn(field.name, clean_numeric(field.name))
        elif isinstance(field.dataType, DoubleType):
            df = df.withColumn(field.name, clean_numeric(field.name))
```

**Verification:** After fix, feature table logs show:
```
Cleaned NaN/Inf→0.0 for 34 columns (sklearn compatibility)
```

**Impact:** Fixed 3 models, inference went from 19/24 to 23/24 successful.

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

## XGBoost Classifier Errors

### base_score must be in (0,1) for logistic loss

**Error:**
```
XGBoostError: [05:06:27] /workspace/src/objective/regression_obj.cu:119: 
Check failed: is_valid: base_score must be in (0,1) for the logistic loss.
```

**Cause:** XGBClassifier is receiving continuous values (0.0-1.0 rate/ratio) instead of binary labels (0 or 1). This commonly happens when:
- Label column is a rate like `success_rate`, `failure_rate`, `spill_rate`
- Label column is a ratio like `serverless_adoption_ratio`
- Using `cast_label_to="int"` on continuous values truncates 0.x → 0

**Solution:** Binarize continuous labels before training:

```python
# ❌ WRONG: Continuous rate passed to classifier
LABEL_COLUMN = "failure_rate"  # Values like 0.15, 0.45, 0.89
X_train, X_test, y_train, y_test = prepare_training_data(
    training_df, available_features, LABEL_COLUMN, cast_label_to="int"
)
# All values < 1.0 become 0, model gets all zeros!

# ✅ CORRECT: Binarize first, then train
from pyspark.sql.functions import when, col

# Create binary label BEFORE training
training_df = training_df.withColumn(
    "high_failure_rate",
    when(col("failure_rate") > 0.2, 1).otherwise(0)  # Threshold binarization
)

X_train, X_test, y_train, y_test = prepare_training_data(
    training_df, available_features, "high_failure_rate",  # Use binary column
    cast_label_to="int", stratify=True
)
```

**Standard Thresholds by Model Type:**

| Model Type | Label Column | Threshold | Binary Meaning |
|-----------|-------------|-----------|----------------|
| Failure predictor | failure_rate | > 0.2 | High risk of failure |
| Success predictor | success_rate | > 0.7 | High likelihood of success |
| SLA breach | breach_rate | > 0.1 | Needs attention |
| Cache performance | spill_rate | > 0.3 | Poor cache performance |
| Serverless adoption | adoption_ratio | > 0.5 | Good candidate |

---

## Schema Consistency Errors

### DELTA_FAILED_TO_MERGE_FIELDS

**Error:**
```
[DELTA_FAILED_TO_MERGE_FIELDS] Failed to merge fields 'daily_dbu' and 'daily_dbu'.
```

**Cause:** Data type mismatch between training and inference:
- Feature table has `INTEGER` or `DECIMAL` types
- Training casts to `float64` for model signature
- Inference writes predictions with original types
- Delta table schema evolution can't merge incompatible types

**Solution:** Cast all numeric features to DOUBLE in feature table creation:

```python
# In create_feature_tables.py
from pyspark.sql.types import IntegerType, LongType, FloatType, DecimalType, ShortType, ByteType

def create_feature_table(spark, df, table_name, primary_keys):
    # Cast all numeric columns to DOUBLE for MLflow compatibility
    for field in df.schema.fields:
        if field.name not in primary_keys:  # Don't cast PKs
            if isinstance(field.dataType, (IntegerType, LongType, FloatType, DecimalType)):
                df = df.withColumn(field.name, F.col(field.name).cast("double"))
    
    # Now create table with consistent types
    df.write.format("delta").mode("overwrite").saveAsTable(table_name)
```

**Type Flow for Consistency:**
```
Feature Creation (Spark)  →  Training (Pandas)  →  Inference (Spark)
      DOUBLE             →      float64        →      DOUBLE
         ✓ Compatible!         ✓ Model signature matches!
```

---

### Failed to enforce schema of data

**Error:**
```
MlflowException: Failed to enforce schema of data '... event_count  tables_accessed ...'
```

**Cause:** Model signature expects different column names or types than provided:
- Column names don't match training features
- Data types don't match (e.g., INTEGER vs DOUBLE)
- Missing columns in scoring DataFrame

**Solution:**
```python
# 1. Get expected features from model signature
model_info = mlflow.pyfunc.load_model(model_uri)
expected_features = model_info.metadata.signature.inputs.column_names()

# 2. Filter DataFrame to only those features
scoring_df = scoring_df.select(*expected_features)

# 3. Ensure types match
for col_name in expected_features:
    scoring_df = scoring_df.withColumn(col_name, F.col(col_name).cast("double"))
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

