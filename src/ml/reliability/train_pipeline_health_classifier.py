# Databricks notebook source
"""
Train Pipeline Health Classifier Model
======================================

Problem: Multi-class Classification
Algorithm: Random Forest
Domain: Reliability

Classifies pipeline health status based on metrics.
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
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
        "total_runs", "failed_runs", "success_rate", "avg_duration_seconds",
        "std_duration_seconds", "avg_task_count", "hour_of_day", "day_of_week",
        "failure_rate_7d", "duration_change_pct"
    ]
    
    label_col = "health_class"
    
    df = spark.table(feature_table)
    available_cols = set(df.columns)
    feature_cols = [c for c in feature_cols if c in available_cols]
    
    # Create synthetic label if not present
    from pyspark.sql import functions as F
    if label_col not in available_cols:
        print(f"  Creating synthetic label: {label_col}")
        if "success_rate" in available_cols:
            df = df.withColumn(label_col, 
                F.when(F.col("success_rate") >= 0.95, 2)  # Healthy
                .when(F.col("success_rate") >= 0.80, 1)  # Warning
                .otherwise(0))  # Critical
        else:
            df = df.withColumn(label_col, F.lit(2))  # Default healthy
    
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
    y = pdf[label_col].fillna(0).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    unique_classes = y_train.nunique()
    if unique_classes < 2:
        print("  ⚠ Single class - using DummyClassifier")
        hyperparams = {"strategy": "most_frequent"}
        model = DummyClassifier(**hyperparams)
        algorithm = "dummy"
    else:
        hyperparams = {"n_estimators": 100, "max_depth": 10, "random_state": 42}
        model = RandomForestClassifier(**hyperparams)
        algorithm = "random_forest"
    
    model.fit(X_train, y_train)
    
    metrics = {
        "train_accuracy": round(float(model.score(X_train, y_train)), 4),
        "test_accuracy": round(float(model.score(X_test, y_test)), 4),
        "training_samples": len(X_train),
        "features_count": len(feature_cols)
    }
    
    print(f"✓ Model trained: Accuracy = {metrics['test_accuracy']:.4f}")
    return model, X_train, metrics, hyperparams, algorithm

# COMMAND ----------

def log_model(model, X, metrics, hyperparams, catalog, feature_schema, feature_table, algorithm):
    """Log model."""
    model_name = "pipeline_health_classifier"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, algorithm)) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "reliability", "classification", algorithm,
            "pipeline_health_classification", feature_table
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
    print("PIPELINE HEALTH CLASSIFIER - TRAINING")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("pipeline_health_classifier")
    
    try:
        df, feature_cols, label_col, feature_table = load_training_data(spark, catalog, feature_schema)
        model, X, metrics, hyperparams, algorithm = prepare_and_train(df, feature_cols, label_col)
        result = log_model(model, X, metrics, hyperparams, catalog, feature_schema, feature_table, algorithm)
        
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

