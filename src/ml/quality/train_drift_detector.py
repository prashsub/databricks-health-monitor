# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
import sys
import os

try:
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
TRAINING MATERIAL: Unsupervised Anomaly Detection with Isolation Forest
=======================================================================

This script demonstrates the **unsupervised anomaly detection** pattern using
Isolation Forest, used for drift/anomaly detection without labeled data.

WHY UNSUPERVISED FOR DRIFT DETECTION:
-------------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  SUPERVISED                         │  UNSUPERVISED ✅                   │
├─────────────────────────────────────┼────────────────────────────────────┤
│  Requires labeled "drift" examples  │  No labels needed                  │
│  "What is drift?" subjective        │  Learns "normal" from data         │
│  Labels expensive to obtain         │  Works immediately                 │
│  Limited to known drift types       │  Detects any deviation             │
└─────────────────────────────────────┴────────────────────────────────────┘

ISOLATION FOREST ALGORITHM:
---------------------------

How it works:
1. Build random trees by randomly selecting feature and split value
2. "Isolate" each point by splitting until alone
3. Anomalies require FEWER splits (easier to isolate)
4. Normal points require MORE splits (similar to neighbors)

    Anomaly Score = Average path length to isolate the point
    Low score = Anomaly (easy to isolate)
    High score = Normal (hard to isolate)

KEY PARAMETERS:
---------------

    model = IsolationForest(
        n_estimators=100,      # Number of trees (more = more stable)
        contamination=0.1,     # Expected anomaly rate (10%)
        max_samples="auto",    # Samples per tree
        random_state=42,       # Reproducibility
    )

CONTAMINATION PARAMETER:
------------------------

`contamination` is the expected proportion of anomalies.
- Too low: Misses real anomalies
- Too high: False positives (normal data flagged)
- Default: 0.1 (10%) is reasonable starting point

LABEL=NONE PATTERN:
-------------------

For anomaly detection, training_set has NO label:

    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label=None,  # ← No label for unsupervised!
        exclude_columns=lookup_keys
    )

Uses LOCAL log_model function (like train_cost_anomaly_detector).
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import IsolationForest
import json
from datetime import datetime

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    prepare_anomaly_detection_data,
    get_run_name,
    get_standard_tags,
)

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

MODEL_NAME = "data_drift_detector"
DOMAIN = "quality"
FEATURE_TABLE = "quality_features"
ALGORITHM = "isolation_forest"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def create_training_set(spark, fe, feature_table, feature_names, lookup_keys):
    """Create training set for anomaly detection."""
    print("\nCreating training set...")
    
    feature_lookups = [
        FeatureLookup(table_name=feature_table, feature_names=feature_names, lookup_key=lookup_keys)
    ]
    
    base_df = spark.table(feature_table).select(*lookup_keys).distinct()
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table}!")
    
    training_set = fe.create_training_set(df=base_df, feature_lookups=feature_lookups, label=None, exclude_columns=lookup_keys)
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df

# COMMAND ----------

def train_model(X_train, feature_names):
    """Train Isolation Forest."""
    print("\nTraining Isolation Forest...")
    
    hyperparams = {"n_estimators": 100, "contamination": 0.05, "random_state": 42}
    model = IsolationForest(**hyperparams)
    model.fit(X_train)
    
    predictions = model.predict(X_train)
    anomaly_rate = (predictions == -1).sum() / len(predictions)
    
    metrics = {
        "anomaly_rate": round(float(anomaly_rate), 4),
        "training_samples": len(X_train),
        "features_count": len(feature_names)
    }
    
    print(f"✓ Anomaly rate: {anomaly_rate*100:.1f}%")
    return model, metrics, hyperparams

# COMMAND ----------

def log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full):
    """Log anomaly detection model using fe.log_model with output_schema (required for label=None)."""
    from mlflow.types import ColSpec, DataType, Schema
    
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    print(f"\nLogging model: {registered_name}")
    
    # For anomaly detection (no labels), we MUST use output_schema per official docs:
    # https://api-docs.databricks.com/python/feature-engineering/latest/feature_engineering.client.html
    output_schema = Schema([ColSpec(DataType.long)])  # Isolation Forest returns -1 or 1
    
    print(f"  Using output_schema (required for label=None training sets)")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "anomaly_detection", ALGORITHM, "data_drift_detection", feature_table_full))
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        # Use fe.log_model with output_schema (NOT signature) for anomaly detection
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            infer_input_example=True,
            output_schema=output_schema
        )
        
        print(f"✓ Model logged: {registered_name}")
        return {"run_id": run.info.run_id, "model_name": MODEL_NAME, "registered_as": registered_name, "metrics": metrics}

# COMMAND ----------

def main():
    print("\n" + "=" * 60)
    print(f"{MODEL_NAME.upper().replace('_', ' ')} - TRAINING")
    print("Using FeatureRegistry + LOCAL log_model")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    feature_names = registry.get_feature_columns(FEATURE_TABLE)
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    try:
        training_set, training_df = create_training_set(spark, fe, feature_table_full, feature_names, lookup_keys)
        X_train = prepare_anomaly_detection_data(training_df, feature_names)
        model, metrics, hyperparams = train_model(X_train, feature_names)
        result = log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full)
        
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Anomaly Rate: {metrics['anomaly_rate']*100:.1f}%")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
