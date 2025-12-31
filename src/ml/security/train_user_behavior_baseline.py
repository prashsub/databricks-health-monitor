# Databricks notebook source
"""
Train User Behavior Baseline Model
==================================

Problem: Anomaly Detection
Algorithm: Isolation Forest
Domain: Security

Establishes baseline user behavior for anomaly detection.

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Enables automatic feature lookup at inference time

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
from datetime import datetime

from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

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

def create_training_set_with_features(spark, fe, catalog, feature_schema, X_train):
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.security_features"
    
    feature_names = ["event_count", "tables_accessed", "off_hours_events", "unique_source_ips",
                     "avg_event_count_7d", "event_count_z_score", "off_hours_rate"]
    
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["user_id", "event_date"]
        )
    ]
    
    base_df = spark.table(feature_table).select("user_id", "event_date").distinct()
    base_df = base_df.withColumn("_dummy_label", F.lit(0))
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table}!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="_dummy_label",
        exclude_columns=["user_id", "event_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_training_data(training_df, feature_names):
    pdf = training_df.select(feature_names).toPandas()
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    return pdf.fillna(0).replace([np.inf, -np.inf], 0)

# COMMAND ----------

def train_model(X, feature_names):
    print("\nTraining Isolation Forest for user behavior baseline...")
    
    hyperparams = {"n_estimators": 100, "contamination": 0.05, "random_state": 42}
    model = IsolationForest(**hyperparams, n_jobs=-1)
    model.fit(X)
    
    predictions = model.predict(X)
    anomaly_rate = (predictions == -1).sum() / len(predictions)
    
    metrics = {
        "anomaly_rate": round(float(anomaly_rate), 4),
        "training_samples": len(X),
        "features_count": len(feature_names)
    }
    
    print(f"✓ Anomaly rate: {anomaly_rate*100:.1f}%")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, feature_names, catalog, feature_schema, X_train):
    model_name = "user_behavior_baseline"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "isolation_forest")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "security", "anomaly_detection", "isolation_forest",
            "user_behavior_baseline", f"{catalog}.{feature_schema}.security_features"
        ))
        mlflow.log_params(hyperparams)
        mlflow.log_params({"feature_engineering": "unity_catalog"})
        mlflow.log_metrics(metrics)
        
        # Create input example and signature (REQUIRED for Unity Catalog)
        input_example = X_train.head(5).astype('float64')
        sample_predictions = model.predict(input_example)
        signature = infer_signature(input_example, sample_predictions)
        
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_name,
            input_example=input_example,
            signature=signature
        )
        
        print(f"✓ Model logged with Feature Engineering")
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": "IsolationForest",
            "hyperparameters": hyperparams,
            "metrics": metrics
        }

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("USER BEHAVIOR BASELINE - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("user_behavior_baseline")
    
    try:
        training_set, training_df, feature_names = create_training_set_with_features(spark, fe, catalog, feature_schema)
        X = prepare_training_data(training_df, feature_names)
        model, metrics, hyperparams = train_model(X, feature_names)
        result = log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, feature_names, catalog, feature_schema, X_train)
        
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print(f"  Model: {result['model_name']}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS", "model": result['model_name'],
            "registered_as": result['registered_as'], "run_id": result['run_id'],
            "metrics": result['metrics'], "feature_engineering": "unity_catalog"
        }))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
