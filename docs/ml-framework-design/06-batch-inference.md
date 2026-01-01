# 06 - Batch Inference

## Overview

Batch inference generates predictions for large datasets using trained models. With Unity Catalog Feature Engineering, inference automatically retrieves the correct features without manual feature computation.

> **Key Principle**: At inference time, you provide ONLY the lookup keys. Features are automatically retrieved from feature tables using the metadata embedded during `fe.log_model()`.

## fe.score_batch() Pattern

### Basic Usage

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Scoring DataFrame contains ONLY lookup keys (no features!)
scoring_df = spark.table(feature_table).select(
    "workspace_id",    # Primary key 1
    "usage_date"       # Primary key 2
).distinct()

# fe.score_batch automatically:
# 1. Loads model from Unity Catalog
# 2. Reads feature lookup metadata from model
# 3. Joins features from feature tables
# 4. Applies model
predictions = fe.score_batch(
    model_uri=f"models:/{catalog}.{schema}.{model_name}",
    df=scoring_df
)
```

### What Happens Under the Hood

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    fe.score_batch() INTERNALS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT: scoring_df (keys only)      MODEL METADATA                          │
│  ┌───────────────────────────┐     ┌─────────────────────────────────────┐ │
│  │ workspace_id │ usage_date │     │ Feature Lookup Specification:       │ │
│  │──────────────┼────────────│     │                                     │ │
│  │ ws_001       │ 2026-01-01 │     │ table: cost_features                │ │
│  │ ws_002       │ 2026-01-01 │     │ features: [daily_dbu, avg_dbu_7d...] │ │
│  │ ws_003       │ 2026-01-01 │     │ lookup_key: [workspace_id, usage...] │ │
│  └───────────────────────────┘     └─────────────────────────────────────┘ │
│                │                                  │                         │
│                └────────────┬────────────────────┘                         │
│                             ▼                                               │
│              ┌─────────────────────────────────────┐                       │
│              │ 1. JOIN features from feature table │                       │
│              └─────────────────────────────────────┘                       │
│                             │                                               │
│                             ▼                                               │
│              ┌─────────────────────────────────────┐                       │
│              │ 2. APPLY model.predict(features)    │                       │
│              └─────────────────────────────────────┘                       │
│                             │                                               │
│                             ▼                                               │
│  OUTPUT: predictions_df                                                     │
│  ┌───────────────────────────┬────────────────────┐                        │
│  │ workspace_id │ usage_date │ prediction         │                        │
│  │──────────────┼────────────┼────────────────────│                        │
│  │ ws_001       │ 2026-01-01 │ 0.15 (normal)      │                        │
│  │ ws_002       │ 2026-01-01 │ -0.82 (anomaly!)   │                        │
│  │ ws_003       │ 2026-01-01 │ 0.23 (normal)      │                        │
│  └───────────────────────────┴────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Inference Pipeline Script

### Complete Example

```python
# Databricks notebook source

"""
Batch Inference Pipeline
Generates predictions for all 25 models using fe.score_batch()
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from databricks.feature_engineering import FeatureEngineeringClient
import mlflow
from mlflow import MlflowClient
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import time

mlflow.set_registry_uri("databricks-uc")

# =============================================================================
# PARAMETERS
# =============================================================================

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

def get_model_configs(catalog: str, schema: str) -> List[Dict]:
    """
    Define all 25 model configurations.
    
    Each config specifies:
    - model_name: Name in Unity Catalog
    - feature_table: Source feature table
    - id_columns: Lookup keys (primary keys)
    - output_table: Where to save predictions
    - model_type: For post-processing predictions
    """
    return [
        # COST DOMAIN (6 models)
        {
            "model_name": "cost_anomaly_detector",
            "domain": "COST",
            "feature_table": "cost_features",
            "id_columns": ["workspace_id", "usage_date"],
            "output_table": "cost_anomaly_predictions",
            "model_type": "anomaly_detection",
            "catalog": catalog,
            "schema": schema
        },
        {
            "model_name": "budget_forecaster",
            "domain": "COST",
            "feature_table": "cost_features",
            "id_columns": ["workspace_id", "usage_date"],
            "output_table": "budget_forecast_predictions",
            "model_type": "regression",
            "catalog": catalog,
            "schema": schema
        },
        # ... (20+ more model configs)
    ]

# =============================================================================
# MODEL LOADING
# =============================================================================

def load_model(catalog: str, schema: str, model_name: str) -> Tuple[str, int, str]:
    """
    Get model URI and version from Unity Catalog.
    
    Returns: (model_uri, version, error_message)
    """
    full_model_name = f"{catalog}.{schema}.{model_name}"
    client = MlflowClient()
    
    try:
        versions = client.search_model_versions(f"name='{full_model_name}'")
        
        if not versions:
            return None, 0, f"Model not found: {full_model_name}"
        
        # Get latest version
        latest = max(versions, key=lambda v: int(v.version))
        model_uri = f"models:/{full_model_name}/{latest.version}"
        
        return model_uri, int(latest.version), None
        
    except Exception as e:
        return None, 0, f"Model load error: {str(e)}"

# =============================================================================
# SCORING
# =============================================================================

def score_with_feature_engineering(
    fe: FeatureEngineeringClient,
    spark: SparkSession,
    config: Dict
) -> Tuple[DataFrame, str]:
    """
    Score using fe.score_batch() for automatic feature retrieval.
    
    Returns: (predictions_df, error_message)
    """
    model_name = config["model_name"]
    catalog = config["catalog"]
    schema = config["schema"]
    feature_table = f"{catalog}.{schema}.{config['feature_table']}"
    id_columns = config["id_columns"]
    model_type = config["model_type"]
    
    print(f"    Scoring {model_name}...")
    
    try:
        # Get model URI
        model_uri, version, error = load_model(catalog, schema, model_name)
        if error:
            return None, error
        
        print(f"      Model: v{version}")
        
        # Prepare scoring DataFrame with ONLY lookup keys
        scoring_df = spark.table(feature_table).select(*id_columns).distinct()
        
        row_count = scoring_df.count()
        print(f"      Records to score: {row_count:,}")
        
        if row_count == 0:
            return None, "No records to score"
        
        # =================================================================
        # SCORE WITH fe.score_batch()
        # =================================================================
        predictions_df = fe.score_batch(
            model_uri=model_uri,
            df=scoring_df
        )
        
        # =================================================================
        # POST-PROCESS BASED ON MODEL TYPE
        # =================================================================
        if model_type == "anomaly_detection":
            # Isolation Forest returns scores where negative = anomaly
            predictions_df = (predictions_df
                .withColumn("anomaly_score", F.col("prediction"))
                .withColumn("is_anomaly", 
                    F.when(F.col("prediction") < 0, 1).otherwise(0)))
        
        elif model_type == "classification":
            predictions_df = (predictions_df
                .withColumn("probability", F.col("prediction"))
                .withColumn("predicted_class", 
                    F.when(F.col("prediction") > 0.5, 1).otherwise(0)))
        
        # Add metadata
        predictions_df = (predictions_df
            .withColumn("model_version", F.lit(version))
            .withColumn("model_name", F.lit(model_name))
            .withColumn("scored_at", F.current_timestamp()))
        
        return predictions_df, None
        
    except Exception as e:
        return None, f"Scoring error: {str(e)}"

# =============================================================================
# SAVE PREDICTIONS
# =============================================================================

def save_predictions(
    spark: SparkSession,
    predictions_df: DataFrame,
    catalog: str,
    schema: str,
    table_name: str
) -> Tuple[str, int, str]:
    """
    Save predictions to Delta table.
    
    Returns: (full_table_name, rows_saved, error_message)
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    try:
        # Overwrite table
        (predictions_df
            .write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(full_table_name))
        
        rows_saved = spark.table(full_table_name).count()
        
        return full_table_name, rows_saved, None
        
    except Exception as e:
        return full_table_name, 0, f"Save error: {str(e)}"

# =============================================================================
# SINGLE MODEL INFERENCE
# =============================================================================

def run_inference_for_model(
    spark: SparkSession,
    fe: FeatureEngineeringClient,
    config: Dict
) -> Dict:
    """Run inference for a single model."""
    model_name = config["model_name"]
    domain = config.get("domain", "UNKNOWN")
    
    start_time = time.time()
    
    result = {
        "model_name": model_name,
        "domain": domain,
        "status": "FAILED",
        "records_scored": 0,
        "model_version": 0,
        "output_table": None,
        "error": None,
        "duration_sec": 0
    }
    
    print(f"\n  [{domain}] {model_name}")
    print(f"  {'-' * 50}")
    
    # Score
    predictions_df, error = score_with_feature_engineering(fe, spark, config)
    
    if error:
        result["error"] = error
        print(f"    ❌ {error}")
        result["duration_sec"] = round(time.time() - start_time, 2)
        return result
    
    # Save
    output_table, rows_saved, error = save_predictions(
        spark, predictions_df,
        config["catalog"], config["schema"], config["output_table"]
    )
    
    if error:
        result["error"] = error
        print(f"    ❌ {error}")
    else:
        result["status"] = "SUCCESS"
        result["records_scored"] = rows_saved
        result["output_table"] = output_table
        print(f"    ✓ Saved {rows_saved:,} predictions to {output_table}")
    
    result["duration_sec"] = round(time.time() - start_time, 2)
    print(f"    Duration: {result['duration_sec']}s")
    
    return result

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 80)
    print("BATCH INFERENCE - ALL ML MODELS")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    
    print(f"\nConfiguration:")
    print(f"  Catalog: {catalog}")
    print(f"  Feature Schema: {feature_schema}")
    
    # Get all model configs
    model_configs = get_model_configs(catalog, feature_schema)
    print(f"\nModels to score: {len(model_configs)}")
    
    # Group by domain
    domains = {}
    for config in model_configs:
        domain = config.get("domain", "UNKNOWN")
        domains.setdefault(domain, []).append(config)
    
    # Run inference for each model
    results = []
    start_time = time.time()
    
    for domain in ["COST", "SECURITY", "PERFORMANCE", "RELIABILITY", "QUALITY"]:
        if domain not in domains:
            continue
        
        print(f"\n{'=' * 80}")
        print(f"DOMAIN: {domain} ({len(domains[domain])} models)")
        print("=" * 80)
        
        for config in domains[domain]:
            result = run_inference_for_model(spark, fe, config)
            results.append(result)
    
    # =================================================================
    # SUMMARY
    # =================================================================
    total_time = round(time.time() - start_time, 2)
    
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    
    print("\n" + "=" * 80)
    print("INFERENCE SUMMARY")
    print("=" * 80)
    print(f"\nTotal models: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total time: {total_time}s")
    print(f"Total records scored: {sum(r['records_scored'] for r in successful):,}")
    
    if failed:
        print("\n❌ FAILED MODELS:")
        for r in failed:
            print(f"  - {r['model_name']}: {r['error']}")
    
    print("\n✓ SUCCESSFUL MODELS:")
    for r in successful:
        print(f"  - {r['model_name']}: {r['records_scored']:,} records")
    
    # Exit with status
    if len(failed) == 0:
        dbutils.notebook.exit("SUCCESS")
    elif len(successful) > 0:
        dbutils.notebook.exit(f"PARTIAL: {len(successful)}/{len(results)} succeeded")
    else:
        raise RuntimeError(f"All {len(failed)} models failed")

if __name__ == "__main__":
    main()
```

## Fallback for Non-FE Models

Some models (like `tag_recommender`) use runtime features that aren't in feature tables. These require manual scoring:

```python
def score_without_feature_engineering(
    spark: SparkSession,
    model_uri: str,
    feature_table: str,
    feature_columns: List[str],
    id_columns: List[str]
) -> DataFrame:
    """
    Score models that don't use fe.log_model().
    
    Must manually:
    1. Load full feature data
    2. Prepare feature matrix
    3. Apply model
    """
    import mlflow
    
    # Load model
    model = mlflow.pyfunc.load_model(model_uri)
    
    # Load features
    features_df = spark.table(feature_table).select(id_columns + feature_columns)
    
    # Convert to pandas
    pdf = features_df.toPandas()
    
    # Prepare features
    X = pdf[feature_columns].copy()
    for col in feature_columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(0).replace([np.inf, -np.inf], 0).astype('float64')
    
    # Score
    predictions = model.predict(X)
    
    # Combine with IDs
    pdf["prediction"] = predictions
    
    return spark.createDataFrame(pdf)
```

## Prediction Table Schema

### Standard Columns

All prediction tables include:

| Column | Type | Description |
|---|---|---|
| `{pk_1}` | varies | First primary key |
| `{pk_2}` | varies | Second primary key |
| `prediction` | DOUBLE | Raw model output |
| `model_version` | INT | Model version used |
| `model_name` | STRING | Model name |
| `scored_at` | TIMESTAMP | When scored |

### Model-Type Specific Columns

#### Anomaly Detection

```sql
cost_anomaly_predictions (
    workspace_id STRING,
    usage_date DATE,
    prediction DOUBLE,       -- Raw decision_function output
    anomaly_score DOUBLE,    -- Same as prediction
    is_anomaly INT,          -- 1 if prediction < 0, else 0
    model_version INT,
    model_name STRING,
    scored_at TIMESTAMP
)
```

#### Classification

```sql
failure_predictions (
    job_id STRING,
    run_date DATE,
    prediction DOUBLE,       -- Probability (0-1)
    probability DOUBLE,      -- Same as prediction
    predicted_class INT,     -- 1 if probability > 0.5
    model_version INT,
    model_name STRING,
    scored_at TIMESTAMP
)
```

#### Regression

```sql
budget_forecast_predictions (
    workspace_id STRING,
    usage_date DATE,
    prediction DOUBLE,       -- Predicted value
    predicted_cost DOUBLE,   -- Alias for clarity
    model_version INT,
    model_name STRING,
    scored_at TIMESTAMP
)
```

## Querying Predictions

### Basic Query

```sql
-- Get today's anomalies
SELECT *
FROM ${catalog}.${schema}.cost_anomaly_predictions
WHERE scored_at >= current_date()
  AND is_anomaly = 1
ORDER BY anomaly_score ASC;  -- Most anomalous first
```

### Join with Gold Layer

```sql
-- Anomalies with actual cost data
SELECT 
    p.workspace_id,
    p.usage_date,
    p.anomaly_score,
    f.daily_cost AS actual_cost,
    f.daily_dbu AS actual_dbu
FROM ${catalog}.${schema}.cost_anomaly_predictions p
JOIN ${catalog}.${schema}.fact_usage f
    ON p.workspace_id = f.workspace_id
    AND p.usage_date = f.usage_date
WHERE p.is_anomaly = 1
  AND p.scored_at >= current_date()
ORDER BY p.anomaly_score ASC;
```

### Cross-Model Analysis

```sql
-- Workspaces with both cost anomalies and high failure rates
SELECT 
    c.workspace_id,
    c.anomaly_score AS cost_anomaly_score,
    r.failure_probability
FROM ${catalog}.${schema}.cost_anomaly_predictions c
JOIN ${catalog}.${schema}.failure_predictions r
    ON c.workspace_id = r.workspace_id  -- If applicable
WHERE c.is_anomaly = 1
  AND r.failure_probability > 0.5;
```

## Performance Optimization

### Sampling Large Tables

```python
MAX_INFERENCE_SAMPLES = 100_000

scoring_df = spark.table(feature_table).select(*id_columns).distinct()
total_rows = scoring_df.count()

if total_rows > MAX_INFERENCE_SAMPLES:
    sample_fraction = MAX_INFERENCE_SAMPLES / total_rows
    scoring_df = scoring_df.sample(fraction=sample_fraction, seed=42)
    print(f"Sampled {MAX_INFERENCE_SAMPLES:,} from {total_rows:,} rows")
```

### Parallel Model Scoring

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def score_models_parallel(configs: List[Dict], max_workers: int = 4):
    """Score multiple models in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_inference_for_model, spark, fe, config): config
            for config in configs
        }
        
        for future in as_completed(futures):
            config = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "model_name": config["model_name"],
                    "status": "FAILED",
                    "error": str(e)
                })
    
    return results
```

### Incremental Scoring

```python
def get_incremental_scoring_df(
    spark: SparkSession,
    feature_table: str,
    predictions_table: str,
    id_columns: List[str]
) -> DataFrame:
    """Score only new records since last run."""
    
    # Check if predictions table exists
    if spark.catalog.tableExists(predictions_table):
        last_scored = spark.sql(f"""
            SELECT MAX(scored_at) FROM {predictions_table}
        """).collect()[0][0]
        
        # Get records not yet scored
        return spark.table(feature_table).select(*id_columns).filter(
            f"last_updated > '{last_scored}'"
        )
    else:
        # First run - score all
        return spark.table(feature_table).select(*id_columns)
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|---|---|---|
| "Model not found" | Model not registered | Run training pipeline first |
| "Unable to find feature" | Feature table missing | Run feature pipeline first |
| "Column mismatch" | Different features at inference | Ensure model uses fe.log_model |
| "Timeout" | Too many records | Implement sampling |

### Graceful Degradation

```python
def run_inference_with_fallback(config: Dict) -> Dict:
    """Try fe.score_batch, fall back to manual scoring."""
    
    try:
        # Try Feature Engineering scoring first
        predictions_df, error = score_with_feature_engineering(fe, spark, config)
        if not error:
            return {"status": "SUCCESS", "method": "fe.score_batch"}
    except Exception as e:
        print(f"FE scoring failed: {e}")
    
    try:
        # Fall back to manual scoring
        predictions_df = score_without_feature_engineering(...)
        return {"status": "SUCCESS", "method": "manual"}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}
```

## Validation Checklist

### Before Inference
- [ ] Feature tables exist and have data
- [ ] Models registered in Unity Catalog
- [ ] Models have feature metadata (used fe.log_model)
- [ ] Predictions tables can be created

### During Inference
- [ ] Scoring DataFrame has ONLY lookup keys
- [ ] No manual feature computation
- [ ] Post-processing matches model type

### After Inference
- [ ] Predictions saved successfully
- [ ] Record counts match expectations
- [ ] No NULL predictions
- [ ] scored_at timestamp is recent

## Next Steps

- **[07-11: Model Catalog](07-model-catalog-cost.md)**: Detailed model documentation
- **[13-Model Monitoring](13-model-monitoring.md)**: Tracking prediction quality
- **[14-Debugging Guide](14-debugging-guide.md)**: Troubleshooting inference issues

