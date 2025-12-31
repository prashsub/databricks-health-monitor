# Databricks notebook source
"""
Train Access Pattern Analyzer Model
====================================

Problem: Clustering
Algorithm: Isolation Forest (pattern detection)
Domain: Security

Analyzes user access patterns to identify anomalies.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import IsolationForest
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
    
    feature_table = f"{catalog}.{feature_schema}.security_features"
    
    feature_cols = [
        "event_count", "unique_users", "unique_service_names", "unique_action_names",
        "avg_events_7d", "std_events_7d", "hour_of_day",
        "high_risk_actions", "failed_actions"
    ]
    
    df = spark.table(feature_table)
    available_cols = set(df.columns)
    feature_cols = [c for c in feature_cols if c in available_cols]
    
    if not feature_cols:
        raise ValueError(f"No valid feature columns found!")
    
    df = df.select(*feature_cols)
    record_count = df.count()
    print(f"  Loaded {record_count} records, Features: {len(feature_cols)}")
    
    if record_count == 0:
        raise ValueError(f"No data found!")
    
    return df, feature_cols, feature_table

# COMMAND ----------

def prepare_and_train(df, feature_cols):
    """Prepare data and train the model."""
    print("\nPreparing data and training model...")
    
    pdf = df.toPandas()
    X = pdf[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
    
    print(f"  Training samples: {len(X)}")
    
    hyperparams = {"n_estimators": 100, "contamination": 0.05, "random_state": 42}
    model = IsolationForest(**hyperparams)
    model.fit(X)
    
    predictions = model.predict(X)
    anomaly_ratio = (predictions == -1).sum() / len(predictions)
    
    metrics = {
        "training_samples": len(X),
        "features_count": len(feature_cols),
        "anomaly_ratio": round(float(anomaly_ratio), 4)
    }
    
    print(f"✓ Model trained: Anomaly ratio = {anomaly_ratio:.2%}")
    return model, X, metrics, hyperparams

# COMMAND ----------

def log_model(model, X, metrics, hyperparams, catalog, feature_schema, feature_table):
    """Log model."""
    model_name = "access_pattern_analyzer"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "isolation_forest")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "security", "anomaly_detection", "isolation_forest",
            "access_pattern_analysis", feature_table
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
    print("ACCESS PATTERN ANALYZER - TRAINING")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("access_pattern_analyzer")
    
    try:
        df, feature_cols, feature_table = load_training_data(spark, catalog, feature_schema)
        model, X, metrics, hyperparams = prepare_and_train(df, feature_cols)
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

