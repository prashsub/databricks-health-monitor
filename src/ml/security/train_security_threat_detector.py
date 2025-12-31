# Databricks notebook source
"""
Train Security Threat Detector Model
=====================================

Problem: Unsupervised Anomaly Detection  
Algorithm: Isolation Forest
Domain: Security

Detects security threats and anomalous access patterns.

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Uses fe.log_model() for automatic feature lookup at inference time

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

def create_training_set_with_features(spark, fe, catalog, feature_schema):
    """Create training set with Feature Engineering."""
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.security_features"
    
    # Features matching the feature table columns
    feature_names = [
        "event_count", "tables_accessed", "off_hours_events", "unique_source_ips",
        "failed_auth_count", "unique_action_types", "unique_services_accessed",
        "avg_event_count_7d", "event_count_z_score", "off_hours_rate",
        "is_human_user", "is_service_principal", "is_system_user",
        "is_activity_burst", "lateral_movement_risk", "failed_auth_ratio",
        "is_weekend", "day_of_week"
    ]
    
    # Lookup keys match feature table PRIMARY KEY: ["user_id", "event_date"]
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["user_id", "event_date"]
        )
    ]
    
    base_df = (spark.table(feature_table)
               .select("user_id", "event_date")
               .withColumn("_dummy_label", F.lit(0))
               .distinct())
    
    record_count = base_df.count()
    print(f"  Base DataFrame: {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data in {feature_table}!")
    
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

def prepare_and_train(training_df, feature_names):
    """Prepare and train model."""
    print("\nTraining model...")
    
    pdf = training_df.toPandas()
    available_features = [f for f in feature_names if f in pdf.columns]
    X_train = pdf[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    
    print(f"  Samples: {len(X_train)}, Features: {len(available_features)}")
    
    hyperparams = {"n_estimators": 100, "max_samples": "auto", "contamination": 0.05, "random_state": 42}
    model = IsolationForest(**hyperparams)
    model.fit(X_train)
    
    scores = model.decision_function(X)
    predictions = model.predict(X_train)
    anomaly_ratio = (predictions == -1).sum() / len(predictions)
    
    metrics = {
        "training_samples": len(X_train),
        "features_count": len(available_features),
        "anomaly_ratio": round(float(anomaly_ratio), 4)
    }
    
    print(f"✓ Trained: Anomaly ratio = {anomaly_ratio:.2%}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):
    """Log model with Feature Engineering."""
    model_name = "security_threat_detector"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "isolation_forest")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "security", "anomaly_detection", "isolation_forest",
            "security_threat_detection", feature_table
        ))
        mlflow.log_params(hyperparams)
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
        return {"run_id": run.info.run_id, "model_name": model_name, "registered_as": registered_name, "metrics": metrics}

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("SECURITY THREAT DETECTOR - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("security_threat_detector")
    
    feature_table = f"{catalog}.{feature_schema}.security_features"
    
    try:
        training_set, training_df, feature_names = create_training_set_with_features(
            spark, fe, catalog, feature_schema
        )
        model, metrics, hyperparams, X_train = prepare_and_train(training_df, feature_names)
        result = log_model_with_feature_engineering(
            fe, model, training_set, metrics, hyperparams, 
            catalog, feature_schema, feature_table, X_train
        )
        
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print(f"  Model: {result['model_name']}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("=" * 60)
        
        dbutils.notebook.exit(json.dumps({
            "status": "SUCCESS", "model": result['model_name'],
            "registered_as": result['registered_as'], "run_id": result['run_id'],
            "feature_engineering": "unity_catalog"
        }))
        
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
