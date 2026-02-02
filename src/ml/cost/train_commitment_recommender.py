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
TRAINING MATERIAL: Commitment vs Pay-As-You-Go Recommendation
=============================================================

This model recommends whether workloads should use committed
(reserved) capacity or pay-as-you-go pricing.

COMMITMENT ECONOMICS:
---------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PRICING MODEL COMPARISON                                                │
│                                                                         │
│  Pay-As-You-Go:                                                         │
│  └── Full price per DBU                                                 │
│  └── Flexible, no commitment                                            │
│  └── Best for: Sporadic, unpredictable workloads                        │
│                                                                         │
│  Committed Capacity:                                                     │
│  └── 20-50% discount per DBU                                            │
│  └── 1-3 year commitment                                                │
│  └── Best for: Steady, predictable workloads                            │
│                                                                         │
│  PREDICTION: Which pricing model optimizes total cost?                   │
└─────────────────────────────────────────────────────────────────────────┘

LABEL: serverless_adoption_ratio
--------------------------------

Indicates the proportion of workload suitable for committed capacity:
- High ratio (>0.7): Steady workload, recommend commitment
- Low ratio (<0.3): Variable workload, stay pay-as-you-go
- Medium: Partial commitment recommended

FEATURE IMPORTANCE:
-------------------

Key features for commitment recommendations:
- Daily usage variance (low = good for commitment)
- Workload predictability (high = good for commitment)
- Total monthly spend (high = bigger savings opportunity)
- Seasonality patterns

Problem: Classification
Algorithm: XGBOOST
Domain: Cost

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from xgboost import XGBClassifier
import json

from databricks.feature_engineering import FeatureEngineeringClient
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    create_feature_lookup_training_set,
    prepare_training_data,
    get_run_name,
    get_standard_tags,
    calculate_classification_metrics,
)

import mlflow
from mlflow.models.signature import infer_signature
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Configuration
MODEL_NAME = "commitment_recommender"
DOMAIN = "cost"
FEATURE_TABLE = "cost_features"
LABEL_COLUMN = "serverless_adoption_ratio"
ALGORITHM = "xgboost"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def train_model(X_train, X_test, y_train, y_test):
    print("\nTraining model...")
    hyperparams = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42, "eval_metric": "logloss"}
    model = XGBClassifier(**hyperparams)
    model.fit(X_train, y_train)
    metrics = calculate_classification_metrics(model, X_train, X_test, y_train, y_test)
    return model, metrics, hyperparams

# COMMAND ----------

def log_model(fe, model, training_set, X_train, metrics, hyperparams,
              model_name, domain, catalog, feature_schema, feature_table):
    """Log classification model using fe.log_model with output_schema (explicit output type)."""
    from mlflow.types import ColSpec, DataType, Schema
    
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, domain)
    tags = get_standard_tags(model_name, domain, "classification", "xgboost", "commitment_recommendation", feature_table)
    
    # Use output_schema to explicitly define output type
    output_schema = Schema([ColSpec(DataType.long)])  # Classification returns integer class
    
    print(f"  Using output_schema with DataType.long for classification output")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(tags)
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            infer_input_example=True,
            output_schema=output_schema
        )
        
        print(f"✓ Logged model: {registered_name}")
        print(f"  Run ID: {run.info.run_id}")
        
        return {"model_name": registered_name, "run_id": run.info.run_id, "metrics": metrics}

# COMMAND ----------

def main():
    print("\n" + "=" * 60)
    print(f"{MODEL_NAME.upper().replace('_', ' ')} - TRAINING")
    print("Using FeatureRegistry (Dynamic Schema)")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    registry = FeatureRegistry(spark, catalog, feature_schema)
    
    feature_names = registry.get_feature_columns(FEATURE_TABLE, exclude_columns=[LABEL_COLUMN])
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    try:
        training_set, training_df, available_features = create_feature_lookup_training_set(
            spark, fe, feature_table_full, feature_names, LABEL_COLUMN, lookup_keys
        )
        
        # Convert continuous ratio (0-1) to binary classification label
        # High serverless adoption (>0.5) = 1 (recommend commitment), else 0
        from pyspark.sql.functions import when, col
        training_df = training_df.withColumn(
            "high_serverless_adoption",
            when(col(LABEL_COLUMN) > 0.5, 1).otherwise(0)
        )
        
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, available_features, "high_serverless_adoption", cast_label_to="int", stratify=True
        )
        
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        result = log_model(
            fe, model, training_set, X_train, metrics, hyperparams,
            MODEL_NAME, DOMAIN, catalog, feature_schema, feature_table_full
        )
        
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - Accuracy: {result['metrics']['accuracy']}, F1: {result['metrics']['f1']}")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
