# Databricks notebook source
"""
Train Compliance Risk Classifier Model
======================================

Problem: Binary Classification  
Algorithm: Random Forest
Domain: Security

Classifies workspaces by compliance risk level.
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
    
    feature_table = f"{catalog}.{feature_schema}.security_features"
    
    feature_cols = [
        "event_count", "unique_users", "unique_service_names", "unique_action_names",
        "avg_events_7d", "std_events_7d", "high_risk_actions", "failed_actions"
    ]
    
    label_col = "is_high_risk"
    
    df = spark.table(feature_table)
    available_cols = set(df.columns)
    feature_cols = [c for c in feature_cols if c in available_cols]
    
    # Create synthetic label if not present
    if label_col not in available_cols:
        print(f"  Creating synthetic label: {label_col}")
        if "high_risk_actions" in available_cols:
            df = df.withColumn(label_col, (df["high_risk_actions"] > 0).cast("int"))
        else:
            df = df.withColumn(label_col, F.lit(0))
    
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
    from pyspark.sql import functions as F
    print("\nPreparing data and training model...")
    
    pdf = df.toPandas()
    X_train = pdf[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf[label_col].fillna(0).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # Check class balance
    unique_classes = y_train.nunique()
    if unique_classes < 2:
        print("  ⚠ Single class in training data - using DummyClassifier")
        hyperparams = {"strategy": "most_frequent"}
        model = DummyClassifier(**hyperparams)
        algorithm = "dummy"
    else:
        hyperparams = {"n_estimators": 100, "max_depth": 10, "random_state": 42}
        model = RandomForestClassifier(**hyperparams)
        algorithm = "random_forest"
    
    model.fit(X_train, y_train)
    
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    
    metrics = {
        "train_accuracy": round(float(train_acc), 4),
        "test_accuracy": round(float(test_acc), 4),
        "training_samples": len(X_train),
        "features_count": len(feature_cols)
    }
    
    print(f"✓ Model trained: Accuracy = {test_acc:.4f}")
    return model, X_train, metrics, hyperparams, algorithm

# COMMAND ----------

def log_model(model, X, metrics, hyperparams, catalog, feature_schema, feature_table, algorithm):
    """Log model."""
    model_name = "compliance_risk_classifier"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, algorithm)) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "security", "classification", algorithm,
            "compliance_risk_classification", feature_table
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
    from pyspark.sql import functions as F
    print("\n" + "=" * 60)
    print("COMPLIANCE RISK CLASSIFIER - TRAINING")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("compliance_risk_classifier")
    
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

