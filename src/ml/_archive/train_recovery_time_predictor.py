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
Train Recovery Time Predictor Model
===================================

Problem: Regression
Algorithm: Gradient Boosting Regressor
Domain: Reliability

Predicts recovery time for failed jobs/pipelines.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
from datetime import datetime

from databricks.feature_engineering import FeatureEngineeringClient

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    print(f"Catalog: {catalog}, Gold Schema: {gold_schema}, Feature Schema: {feature_schema}")
    return catalog, gold_schema, feature_schema


def setup_mlflow_experiment(model_name):
    mlflow.set_experiment(f"/Shared/health_monitor_ml_{model_name}")


def get_run_name(model_name, algorithm):
    return f"{model_name}_{algorithm}_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_standard_tags(model_name, domain, model_type, algorithm, use_case, training_table):
    return {
        "project": "databricks_health_monitor", "domain": domain, "model_name": model_name,
        "model_type": model_type, "algorithm": algorithm, "use_case": use_case,
        "training_data": training_table, "feature_engineering": "unity_catalog"
    }

# COMMAND ----------

def load_training_data(spark, catalog, feature_schema):
    """Load training data directly from the feature table."""
    print("\nLoading training data from feature table...")
    
    feature_table = f"{catalog}.{feature_schema}.reliability_features"
    
    feature_cols = [
        "total_runs", "failed_runs", "success_rate",
        "std_duration_seconds", "avg_task_count", "hour_of_day", "day_of_week",
        "failure_rate_7d"
    ]
    
    label_col = "avg_duration_seconds"  # Proxy for recovery time
    
    df = spark.table(feature_table)
    available_cols = set(df.columns)
    feature_cols = [c for c in feature_cols if c in available_cols and c != label_col]
    
    if label_col not in available_cols:
        raise ValueError(f"Label column '{label_col}' not found!")
    
    if not feature_cols:
        raise ValueError(f"No valid feature columns found!")
    
    select_cols = feature_cols + [label_col]
    df = df.select(*select_cols)
    
    record_count = df.count()
    print(f"  Loaded {record_count} records, Features: {len(feature_cols)}, Label: {label_col}")
    
    if record_count == 0:
        raise ValueError(f"No data found!")
    
    return df, feature_cols, label_col, feature_table

# COMMAND ----------

def prepare_and_train(df, feature_cols, label_col):
    """Prepare data and train the model."""
    print("\nPreparing data and training model...")
    
    pdf = df.toPandas()
    X_train = pdf[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf[label_col].fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    hyperparams = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42}
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    metrics = {
        "train_r2": round(float(model.score(X_train, y_train)), 4),
        "test_r2": round(float(model.score(X_test, y_test)), 4),
        "training_samples": len(X_train),
        "features_count": len(feature_cols)
    }
    
    print(f"✓ Model trained: R² = {metrics['test_r2']:.4f}")
    return model, X_train, metrics, hyperparams

# COMMAND ----------

def log_model(model, X, metrics, hyperparams, catalog, feature_schema, feature_table):
    """Log model."""
    model_name = "recovery_time_predictor"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "reliability", "regression", "gradient_boosting",
            "recovery_time_prediction", feature_table
        ))
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        mlflow.sklearn.log_model(
            model, artifact_path="model",
            input_example=X.head(5),
            registered_model_name=registered_name
        )
        
        print(f"✓ Model logged and registered")
        return {"model_name": model_name, "registered_as": registered_name, "metrics": metrics}

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("RECOVERY TIME PREDICTOR - TRAINING")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("recovery_time_predictor")
    
    try:
        df, feature_cols, label_col, feature_table = load_training_data(spark, catalog, feature_schema)
        model, X, metrics, hyperparams = prepare_and_train(df, feature_cols, label_col)
        result = log_model(model, X, metrics, hyperparams, catalog, feature_schema, feature_table)
        
        print("\n✓ TRAINING COMPLETE")
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS", "model": result['model_name'], "metrics": result['metrics']
        }))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()

