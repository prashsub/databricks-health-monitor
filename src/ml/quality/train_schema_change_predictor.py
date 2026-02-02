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
TRAINING MATERIAL: Proactive Schema Change Prediction
=====================================================

This model predicts which tables are likely to have schema changes
in the next 7 days, enabling proactive governance.

SCHEMA CHANGE DETECTION:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  PROBLEM: Schema changes often break downstream pipelines               │
│                                                                         │
│  Day 0: Table has schema V1                                             │
│  Day 3: Schema change to V2 (column added/renamed)                      │
│  Day 3: Downstream pipelines fail ❌                                    │
│  Day 4: On-call engineer pages, debugging starts                        │
│                                                                         │
│  WITH PREDICTION:                                                        │
│                                                                         │
│  Day 0: Model predicts 85% chance of schema change in 7 days            │
│  Day 1: Alert sent, team reviews upcoming changes                       │
│  Day 3: Schema change happens (expected)                                │
│  Day 3: Pipelines handle change gracefully ✅                           │
└─────────────────────────────────────────────────────────────────────────┘

LABEL: schema_changes_7d (binary)
---------------------------------

| Value | Meaning |
|-------|---------|
| 1 | Schema will change in next 7 days |
| 0 | Schema will remain stable |

PREDICTIVE FEATURES:
--------------------

Historical patterns that indicate upcoming changes:
- Recent schema change frequency
- Table activity patterns (write frequency)
- Owner activity (active development)
- Column count (more columns = more likely to change)

Problem: Classification
Algorithm: RANDOM_FOREST
Domain: Quality

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
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

import mlflow
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Configuration
MODEL_NAME = "schema_change_predictor"
DOMAIN = "quality"
FEATURE_TABLE = "quality_features"
LABEL_COLUMN = "schema_changes_7d"
ALGORITHM = "random_forest"

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
        
        # Minimum sample check - need at least 2 samples for train/test split
        sample_count = training_df.count()
        MIN_SAMPLES = 2
        if sample_count < MIN_SAMPLES:
            msg = f"Insufficient data: {sample_count} samples (need {MIN_SAMPLES}+). Skipping training."
            print(f"⚠ {msg}")
            dbutils.notebook.exit(json.dumps({"status": "SKIPPED", "reason": msg}))
        print(f"✓ Found {sample_count} samples for training")
        
        # LABEL BINARIZATION: schema_changes_7d (count) → has_schema_changes (0/1)
        # XGBClassifier requires binary labels, not continuous counts
        # Must cast to int explicitly for XGBoost
        from pyspark.sql.types import IntegerType
        BINARY_LABEL = "has_schema_changes"
        training_df = training_df.withColumn(
            BINARY_LABEL, when(col(LABEL_COLUMN) > 0, 1).otherwise(0).cast(IntegerType())
        )
        
        # Check label distribution - XGBClassifier needs at least 2 classes
        label_counts = training_df.groupBy(BINARY_LABEL).count().collect()
        label_dist = {r[BINARY_LABEL]: r['count'] for r in label_counts}
        print(f"✓ Binarized label: {LABEL_COLUMN} > 0 → {BINARY_LABEL}")
        print(f"  Label distribution: {label_dist}")
        
        # SINGLE-CLASS CHECK: XGBClassifier cannot train on single-class data
        if len(label_dist) < 2:
            msg = f"Single-class data: all {sum(label_dist.values())} samples have label={list(label_dist.keys())[0]}. Cannot train classifier."
            print(f"⚠ {msg}")
            dbutils.notebook.exit(json.dumps({"status": "SKIPPED", "reason": msg}))
        
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, available_features, BINARY_LABEL, cast_label_to="int", stratify=True
        )
        
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        result = log_model_with_features(
            fe, model, training_set, X_train, metrics, hyperparams,
            MODEL_NAME, DOMAIN, "classification", ALGORITHM, "schema_change_prediction",
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
