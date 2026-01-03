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
Train Budget Forecaster Model
===================================

Uses LOCAL log_model function to avoid training_base signature issues.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingRegressor
import json
from datetime import datetime

from databricks.feature_engineering import FeatureEngineeringClient

from src.ml.config.feature_registry import FeatureRegistry
from src.ml.utils.training_base import (
    setup_training_environment,
    create_feature_lookup_training_set,
    prepare_training_data,
    calculate_regression_metrics,
    get_run_name,
    get_standard_tags,
)

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

MODEL_NAME = "budget_forecaster"
DOMAIN = "cost"
FEATURE_TABLE = "cost_features"
LABEL_COLUMN = "daily_cost"
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

def log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full):
    """Log regression model using fe.log_model with output_schema (explicit output type)."""
    from mlflow.types import ColSpec, DataType, Schema
    
    registered_name = f"{catalog}.{feature_schema}.{MODEL_NAME}"
    print(f"\nLogging model: {registered_name}")
    
    # Use output_schema to explicitly define output type (same approach as anomaly detection)
    # Per docs: https://api-docs.databricks.com/python/feature-engineering/latest/feature_engineering.client.html
    output_schema = Schema([ColSpec(DataType.double)])  # Regression returns double
    
    print(f"  Using output_schema with DataType.double for regression output")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(MODEL_NAME, ALGORITHM)) as run:
        mlflow.set_tags(get_standard_tags(MODEL_NAME, DOMAIN, "regression", ALGORITHM, "budget_forecasting", feature_table_full))
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
        
        result = log_model(fe, model, training_set, X_train, metrics, hyperparams, catalog, feature_schema, feature_table_full)
        
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
