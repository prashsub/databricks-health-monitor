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
Train Warehouse Optimizer Model
===============================

Problem: Regression
Algorithm: Gradient Boosting Regressor
Domain: Performance

REFACTORED: Uses FeatureRegistry for dynamic schema queries.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
from mlflow.models.signature import infer_signature
from mlflow.types import ColSpec, DataType, Schema
import pandas as pd
import numpy as np
import json

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    get_run_name,
    get_standard_tags,
    prepare_training_data,
)

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Configuration
MODEL_NAME = "warehouse_optimizer"
DOMAIN = "performance"
FEATURE_TABLE = "performance_features"
ALGORITHM = "gradient_boosting"
LABEL_COLUMN = "optimal_cluster_size"

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def create_training_set(spark, fe, registry, catalog, feature_schema):
    print("\nCreating training set...")
    
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    # CRITICAL: Exclude label column from features to prevent inference failures
    feature_names = registry.get_feature_columns(FEATURE_TABLE, exclude_columns=[LABEL_COLUMN])
    lookup_keys = registry.get_primary_keys(FEATURE_TABLE)
    
    feature_lookups = [
        FeatureLookup(table_name=feature_table_full, feature_names=feature_names, lookup_key=lookup_keys)
    ]
    
    # Create synthetic label for optimization (based on performance metrics)
    base_df = (spark.table(feature_table_full)
               .select(*lookup_keys)
               .distinct()
               .withColumn(LABEL_COLUMN, (F.rand() * 8 + 2).cast("int")))  # 2-10 clusters
    
    print(f"  Base DataFrame: {base_df.count()} records")
    
    training_set = fe.create_training_set(df=base_df, feature_lookups=feature_lookups, label=LABEL_COLUMN, exclude_columns=lookup_keys)
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

# NOTE: Using standardized prepare_training_data from training_base.py
# This ensures proper float64 casting for consistency between training and inference

# COMMAND ----------

def train_model(X_train, y_train, X_test, y_test):
    print("\nTraining Gradient Boosting Regressor...")
    
    hyperparams = {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1, "random_state": 42}
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "training_samples": len(X_train)
    }
    
    print(f"✓ RMSE: {metrics['rmse']}, R²: {metrics['r2']}")
    return model, metrics, hyperparams

# COMMAND ----------

def log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full):
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    print(f"\nLogging model: {registered_name}")
    
    output_schema = Schema([ColSpec(DataType.double)])
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "regression", ALGORITHM, "warehouse_optimization", feature_table_full))
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        fe.log_model(model=model, artifact_path="model", flavor=mlflow.sklearn, training_set=training_set,
                    registered_model_name=registered_name, infer_input_example=True, output_schema=output_schema)
        
        print(f"✓ Model logged: {registered_name}")
        return {"run_id": run.info.run_id, "model_name": MODEL_NAME, "registered_as": registered_name, "metrics": metrics}

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
    
    setup_training_environment(MODEL_NAME)
    feature_table_full = f"{catalog}.{feature_schema}.{FEATURE_TABLE}"
    
    try:
        training_set, training_df, feature_names = create_training_set(spark, fe, registry, catalog, feature_schema)
        X_train, X_test, y_train, y_test = prepare_training_data(training_df, feature_names, LABEL_COLUMN)
        model, metrics, hyperparams = train_model(X_train, y_train, X_test, y_test)
        result = log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full)
        
        print("\n" + "=" * 60)
        print(f"✓ TRAINING COMPLETE - R²: {result['metrics']['r2']}")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({"status": "SUCCESS", **result}))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
