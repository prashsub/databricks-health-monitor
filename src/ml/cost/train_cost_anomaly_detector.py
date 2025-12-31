# Databricks notebook source
"""
Train Cost Anomaly Detector Model
=================================

Problem: Unsupervised Anomaly Detection
Algorithm: Isolation Forest
Domain: Cost

Detects unusual spending patterns and cost anomalies.

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
    """
    Create training set using Feature Engineering in Unity Catalog.
    
    For unsupervised learning (anomaly detection), we use a dummy label.
    
    Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
    """
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    # Features matching the feature table columns (from create_feature_tables.py)
    feature_names = [
        "daily_dbu", "daily_cost", "jobs_on_all_purpose_cost", "jobs_on_all_purpose_count",
        "serverless_cost", "dlt_cost", "model_serving_cost",
        "avg_dbu_7d", "std_dbu_7d", "avg_dbu_30d", "std_dbu_30d",
        "z_score_7d", "z_score_30d", "day_of_week", "is_weekend", "day_of_month", "is_month_end",
        "dow_sin", "dow_cos", "dbu_change_pct_1d", "dbu_change_pct_7d",
        "potential_job_cluster_savings", "all_purpose_inefficiency_ratio", "serverless_adoption_ratio"
    ]
    
    # FeatureLookup: lookup_key MUST match feature table PRIMARY KEY ["workspace_id", "usage_date"]
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["workspace_id", "usage_date"]
        )
    ]
    
    # Base DataFrame with dummy label for unsupervised learning
    base_df = (spark.table(feature_table)
               .select("workspace_id", "usage_date")
               .withColumn("_dummy_label", F.lit(0))  # Dummy for unsupervised
               .distinct())
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table}!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="_dummy_label",
        exclude_columns=["workspace_id", "usage_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows, {len(feature_names)} features")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_and_train(training_df, feature_names):
    """Prepare data and train the model."""
    print("\nPreparing data and training model...")
    
    pdf = training_df.toPandas()
    
    # Handle missing features
    available_features = [f for f in feature_names if f in pdf.columns]
    X_train = pdf[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    
    print(f"  Training samples: {len(X_train)}, Features: {len(available_features)}")
    
    hyperparams = {"n_estimators": 100, "max_samples": "auto", "contamination": 0.05, "random_state": 42}
    model = IsolationForest(**hyperparams)
    model.fit(X_train)
    
    # Get anomaly scores
    scores = model.decision_function(X)
    predictions = model.predict(X_train)
    anomaly_ratio = (predictions == -1).sum() / len(predictions)
    
    metrics = {
        "training_samples": len(X_train),
        "features_count": len(available_features),
        "anomaly_ratio": round(float(anomaly_ratio), 4),
        "mean_score": round(float(scores.mean()), 4),
        "std_score": round(float(scores.std()), 4)
    }
    
    print(f"✓ Model trained: Anomaly ratio = {anomaly_ratio:.2%}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):
    """Log model with Feature Engineering."""
    model_name = "cost_anomaly_detector"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "isolation_forest")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "cost", "anomaly_detection", "isolation_forest",
            "cost_anomaly_detection", feature_table
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
            "metrics": metrics
        }

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("COST ANOMALY DETECTOR - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("cost_anomaly_detector")
    
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
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
        print(f"  Anomaly Ratio: {result['metrics']['anomaly_ratio']:.2%}")
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
