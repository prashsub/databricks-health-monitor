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
TRAINING MATERIAL: Query Duration Prediction
============================================

This model predicts query execution time before the query runs,
enabling capacity planning and SLA management.

QUERY FORECASTING VALUE:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  USE CASES                                                               │
│                                                                         │
│  1. SLA MANAGEMENT                                                       │
│     └── User submits query                                              │
│     └── Model predicts: "~45 seconds"                                   │
│     └── If SLA is 30s: warn user before running                         │
│                                                                         │
│  2. QUEUE PRIORITIZATION                                                 │
│     └── Short predicted queries → high priority                         │
│     └── Long predicted queries → background queue                       │
│                                                                         │
│  3. COST ESTIMATION                                                      │
│     └── Predicted duration × cluster cost/second                        │
│     └── User sees estimated cost before running                         │
└─────────────────────────────────────────────────────────────────────────┘

LABEL: avg_duration_ms
----------------------

The target variable is average query duration in milliseconds.
We predict this from query and warehouse features.

PREDICTION FEATURES:
--------------------

| Feature | Impact |
|---------|--------|
| Data size | Larger = slower |
| Query complexity | More joins = slower |
| Warehouse size | Bigger = faster |
| Time of day | Peak hours = queueing |

Problem: Regression
Algorithm: Gradient Boosting
Domain: Performance

REFACTORED: Uses FeatureRegistry and training_base utilities.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from sklearn.ensemble import GradientBoostingRegressor
import json

from databricks.feature_engineering import FeatureEngineeringClient

from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    create_feature_lookup_training_set,
    prepare_training_data,
    log_model_with_features,
    calculate_regression_metrics,
)

import mlflow
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Configuration
MODEL_NAME = "query_performance_forecaster"
DOMAIN = "performance"
FEATURE_TABLE = "performance_features"
LABEL_COLUMN = "avg_duration_ms"  # Use avg_duration_ms instead of p99 (more likely to have data)
ALGORITHM = "gradient_boosting"

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
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "random_state": 42
    }
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    metrics = calculate_regression_metrics(model, X_train, X_test, y_train, y_test)
    return model, metrics, hyperparams

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
        
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, available_features, LABEL_COLUMN, cast_label_to="float64"
        )
        
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        result = log_model_with_features(
            fe, model, training_set, X_train, metrics, hyperparams,
            MODEL_NAME, DOMAIN, "regression", ALGORITHM, "query_performance_forecasting",
            catalog, feature_schema, feature_table_full
        )
        
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - R²: {result['metrics']['test_r2']}")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
