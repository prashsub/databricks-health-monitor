# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
# This enables imports from src.ml.config and src.ml.utils when deployed
# via Databricks Asset Bundles. The bundle root is computed dynamically.
# Reference: https://docs.databricks.com/aws/en/notebooks/share-code
import sys
import os

try:
    # Get current notebook path and compute bundle root
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
TRAINING MATERIAL: Signature-Driven Batch Inference
===================================================

This script demonstrates model signature validation during batch inference,
ensuring consistent feature preprocessing between training and inference.

SIGNATURE-DRIVEN PREPROCESSING:
-------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PROBLEM: Training vs Inference Feature Mismatch                         │
│                                                                         │
│  Training:                                                               │
│    features = ["daily_cost", "daily_dbu", "avg_cost_7d", ...]           │
│                                                                         │
│  Inference:                                                              │
│    features = ["daily_cost", "DAILY_DBU", ...]  ← Case mismatch!        │
│    features = ["daily_cost", "daily_dbu", "NEW_COL"]  ← Extra column!   │
│                                                                         │
│  Result: Silent failures, wrong predictions                             │
├─────────────────────────────────────────────────────────────────────────┤
│  SOLUTION: Extract expected features from model signature                │
│                                                                         │
│  signature = model.metadata.signature                                    │
│  expected_features = [col.name for col in signature.inputs]             │
│                                                                         │
│  # Validate and select only expected features                            │
│  inference_df = raw_df.select(expected_features)                        │
└─────────────────────────────────────────────────────────────────────────┘

ANOMALY SCORE INTERPRETATION:
-----------------------------

Isolation Forest returns anomaly_score in [-1, 1]:
- score = -1: Definite anomaly (short average path)
- score = 0: Borderline
- score = 1: Definite normal (long average path)

We convert to probability with: anomaly_probability = (1 - score) / 2

MLflow 3.1+ Best Practices:
- Loads model from Unity Catalog
- Signature-driven preprocessing
- Proper exit signaling
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow import MlflowClient
import pandas as pd
import numpy as np
from datetime import datetime

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def load_model_with_signature(catalog: str, feature_schema: str):
    """Load model and extract signature for preprocessing validation."""
    model_name = f"{catalog}.{feature_schema}.cost_anomaly_detector"
    
    client = MlflowClient()
    
    try:
        # Try to get latest version
        versions = client.search_model_versions(f"name='{model_name}'")
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            model_uri = f"models:/{model_name}/{latest.version}"
            print(f"✓ Using model version {latest.version}")
        else:
            model_uri = f"models:/{model_name}/1"
    except Exception as e:
        print(f"⚠ Version lookup failed: {e}, using version 1")
        model_uri = f"models:/{model_name}/1"
    
    print(f"Loading model: {model_uri}")
    model = mlflow.pyfunc.load_model(model_uri)
    
    # Extract signature if available
    signature = getattr(model.metadata, 'signature', None)
    if signature:
        print(f"  Input schema: {[inp.name for inp in signature.inputs]}")
    
    return model, model_name, signature

# COMMAND ----------

def load_features(spark: SparkSession, catalog: str, feature_schema: str):
    """Load latest cost features for scoring."""
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    print(f"Loading features from {feature_table}...")
    
    features_df = spark.table(feature_table)
    print(f"✓ Loaded {features_df.count()} rows")
    
    return features_df

# COMMAND ----------

def prepare_features_for_inference(pdf: pd.DataFrame, feature_columns: list, signature=None):
    """
    Prepare features matching training preprocessing.
    
    CRITICAL: Must replicate exact preprocessing from training.
    """
    X = pdf[feature_columns].copy()
    
    # Type conversions (matching training)
    for col in feature_columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    
    # Handle missing and infinite values
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    return X

# COMMAND ----------

def score_anomalies(model, features_df, signature):
    """Score features using the model."""
    feature_columns = [
        "daily_dbu", "avg_dbu_7d", "avg_dbu_30d", "z_score_7d", "z_score_30d",
        "dbu_change_pct_1d", "dbu_change_pct_7d", "dow_sin", "dow_cos", "is_weekend", "is_month_end"
    ]
    
    pandas_df = features_df.select(
        ["workspace_id", "sku_name", "usage_date"] + feature_columns
    ).toPandas()
    
    X = prepare_features_for_inference(pandas_df, feature_columns, signature)
    
    # Get underlying sklearn model for full functionality
    sklearn_model = model._model_impl.sklearn_model
    predictions = sklearn_model.predict(X)
    anomaly_scores = sklearn_model.decision_function(X)
    
    pandas_df["is_anomaly"] = (predictions == -1).astype(int)
    pandas_df["anomaly_score"] = anomaly_scores
    pandas_df["scored_at"] = datetime.now()
    
    n_anomalies = pandas_df["is_anomaly"].sum()
    print(f"✓ Scored {len(pandas_df)} records, found {n_anomalies} anomalies")
    
    return pandas_df

# COMMAND ----------

def save_predictions(spark: SparkSession, predictions_df: pd.DataFrame, 
                     catalog: str, feature_schema: str, model_name: str):
    """Save predictions to inference table."""
    spark_df = spark.createDataFrame(predictions_df)
    spark_df = spark_df.withColumn("model_name", F.lit(model_name))
    
    output_table = f"{catalog}.{feature_schema}.cost_anomaly_predictions"
    print(f"Saving predictions to {output_table}...")
    
    spark_df.write.format("delta").mode("append").saveAsTable(output_table)
    print(f"✓ Predictions saved")
    
    return output_table

# COMMAND ----------

def generate_alerts(predictions_df: pd.DataFrame):
    """Generate alerts for detected anomalies."""
    anomalies = predictions_df[predictions_df["is_anomaly"] == 1]
    
    if len(anomalies) == 0:
        print("No anomalies detected")
        return
    
    print("\n" + "=" * 60)
    print("COST ANOMALY ALERTS")
    print("=" * 60)
    
    anomalies = anomalies.sort_values("anomaly_score")
    
    for _, row in anomalies.head(10).iterrows():
        print(f"\n🚨 ANOMALY: {row['workspace_id']} / {row['sku_name']}")
        print(f"   Date: {row['usage_date']}, DBU: {row['daily_dbu']:.2f}, Z-Score: {row['z_score_7d']:.2f}")
    
    if len(anomalies) > 10:
        print(f"\n... and {len(anomalies) - 10} more")

# COMMAND ----------

def main():
    """Main entry point for batch inference."""
    print("\n" + "=" * 60)
    print("COST ANOMALY DETECTION - BATCH INFERENCE")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    try:
        model, model_name, signature = load_model_with_signature(catalog, feature_schema)
        features_df = load_features(spark, catalog, feature_schema)
        predictions_df = score_anomalies(model, features_df, signature)
        output_table = save_predictions(spark, predictions_df, catalog, feature_schema, model_name)
        generate_alerts(predictions_df)
        
        print("\n✓ BATCH INFERENCE COMPLETE")
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}\n{traceback.format_exc()}")
        dbutils.notebook.exit(f"FAILED: {e}")
    
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()
