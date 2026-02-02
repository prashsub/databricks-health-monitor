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
TRAINING MATERIAL: Query Cache Performance Prediction
====================================================

This model predicts cache hit probability for queries, enabling
proactive caching strategies and performance optimization.

CACHING IMPACT:
---------------

┌─────────────────────────────────────────────────────────────────────────┐
│  QUERY EXECUTION PATHS                                                   │
│                                                                         │
│  Cache HIT:                                                              │
│  └── Query → Cache → Result (milliseconds)                              │
│  └── No compute cost, instant response                                  │
│                                                                         │
│  Cache MISS:                                                             │
│  └── Query → Compute → Storage → Result (seconds-minutes)               │
│  └── Full compute cost, user waits                                      │
│                                                                         │
│  PREDICTION VALUE:                                                       │
│  └── Predict which queries will miss → Pre-warm cache                   │
│  └── Predict high-miss patterns → Optimize warehouse config             │
└─────────────────────────────────────────────────────────────────────────┘

LABEL: spill_rate (proxy for cache performance)
-----------------------------------------------

High spill rate indicates queries exceeding memory, causing:
- Disk spills (slow)
- Cache misses
- Poor performance

We classify:
- spill_rate > threshold → Poor cache performance (1)
- spill_rate <= threshold → Good cache performance (0)

FEATURES FOR CACHE PREDICTION:
------------------------------

| Feature | Impact on Cache |
|---------|-----------------|
| Data size | Larger = more misses |
| Query complexity | Complex = harder to cache |
| Data freshness | Recent changes = invalidation |
| Warehouse size | Smaller = more spills |

Problem: Classification
Algorithm: XGBOOST
Domain: Performance

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
    log_model_with_features,
    calculate_classification_metrics,
)

# COMMAND ----------

# Configuration
MODEL_NAME = "cache_hit_predictor"
DOMAIN = "performance"
FEATURE_TABLE = "performance_features"
LABEL_COLUMN = "spill_rate"
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
        
        # Convert continuous spill_rate (0-1) to binary classification label
        # High spill rate (>0.3) = 1 (bad cache performance), else 0 (good)
        from pyspark.sql.functions import when, col
        training_df = training_df.withColumn(
            "high_spill_rate",
            when(col(LABEL_COLUMN) > 0.3, 1).otherwise(0)
        )
        
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, available_features, "high_spill_rate", cast_label_to="int", stratify=True
        )
        
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        result = log_model_with_features(
            fe, model, training_set, X_train, metrics, hyperparams,
            MODEL_NAME, DOMAIN, "classification", ALGORITHM, "cache_hit_prediction",
            catalog, feature_schema, feature_table_full
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
