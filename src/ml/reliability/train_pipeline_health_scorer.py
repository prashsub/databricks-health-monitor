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
TRAINING MATERIAL: Health Score Regression Pattern
==================================================

This script demonstrates predicting a continuous "health score"
(0.0 to 1.0) for pipeline reliability assessment.

HEALTH SCORE CONCEPT:
---------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  Pipeline Health Score = f(success_rate, duration_stability, ...)      │
│                                                                         │
│  Score Range:                                                           │
│  ─────────────                                                          │
│  1.0  ████████████████████  Perfect health                             │
│  0.8  ████████████████      Good health                                │
│  0.6  ████████████          Needs attention                            │
│  0.4  ████████              At risk                                    │
│  0.2  ████                  Critical                                   │
│  0.0                        Failed state                               │
│                                                                         │
│  Used for:                                                              │
│  - Dashboard health indicators                                          │
│  - Alerting thresholds                                                  │
│  - Prioritization of maintenance                                        │
└─────────────────────────────────────────────────────────────────────────┘

LABEL: success_rate
-------------------

The target variable is success_rate - the proportion of successful runs
over a rolling window. We predict this from other reliability features.

WHY REGRESSION FOR HEALTH:
--------------------------

| Approach | Output | Use Case |
|---|---|---|
| Classification | Good/Bad | Simple alerts |
| Regression ✅ | 0.0-1.0 score | Nuanced dashboard |

Regression allows:
- Tracking improvement/degradation trends
- Setting custom alert thresholds
- Ranking pipelines by health

GRADIENT BOOSTING FOR RELIABILITY:
----------------------------------

GradientBoostingRegressor chosen because:
1. Handles feature interactions (job type × duration)
2. Robust to missing data (tree-based)
3. Feature importance for explainability
4. Good balance of accuracy and interpretability

Problem: Regression
Algorithm: Gradient Boosting Regressor
Domain: Reliability

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
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

# COMMAND ----------

# Configuration
MODEL_NAME = "pipeline_health_scorer"
DOMAIN = "reliability"
FEATURE_TABLE = "reliability_features"
LABEL_COLUMN = "success_rate"
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
    hyperparams = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42}
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
            MODEL_NAME, DOMAIN, "regression", ALGORITHM, "pipeline_health_scoring",
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

if __name__ == "__main__":
    main()
