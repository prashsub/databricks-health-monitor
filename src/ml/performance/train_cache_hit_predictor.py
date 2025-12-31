# Databricks notebook source
"""
Train Cache Hit Predictor Model
===============================

Problem: Binary Classification
Algorithm: XGBoost Classifier
Domain: Performance

Predicts likelihood of query cache hits.

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
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
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

def create_training_set_with_features(spark, fe, catalog, feature_schema, gold_schema):
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.performance_features"
    fact_query = f"{catalog}.{gold_schema}.fact_query_history"
    
    feature_names = ["query_count", "avg_duration_ms", "p50_duration_ms", "p95_duration_ms",
                     "spill_rate", "error_rate", "avg_query_count_7d", "is_weekend"]
    
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["warehouse_id", "query_date"]
        )
    ]
    
    # Create label: cache hit proxy based on read_bytes being significantly lower than avg
    # NOTE: Gold table has compute_warehouse_id, feature table has warehouse_id - need to rename
    base_df = (spark.table(fact_query)
               .filter(F.col("compute_warehouse_id").isNotNull())
               .withColumn("warehouse_id", F.col("compute_warehouse_id"))  # Map Gold column to feature table PK
               .withColumn("query_date", F.to_date("start_time"))
               .withColumn("cache_hit", F.when(F.col("read_bytes") < 1000000, 1).otherwise(0))
               .select("warehouse_id", "query_date", "cache_hit")
               .groupBy("warehouse_id", "query_date")
               .agg(F.max("cache_hit").alias("cache_hit")))
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    if record_count == 0:
        raise ValueError(f"No data found!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="cache_hit",
        exclude_columns=["warehouse_id", "query_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_and_train(training_df, feature_names):
    print("\nPreparing data and training model...")
    
    pdf = training_df.toPandas()
    X_train = pdf[feature_names].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf["cache_hit"].fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    hyperparams = {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1, 
                   "random_state": 42, "use_label_encoder": False, "eval_metric": "logloss"}
    model = XGBClassifier(**hyperparams)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if len(model.classes_) > 1 else y_pred
    
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4) if len(np.unique(y_test)) > 1 else 0.5,
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    print(f"✓ Accuracy: {metrics['accuracy']:.4f}, AUC: {metrics['roc_auc']:.4f}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, X_train):
    model_name = "cache_hit_predictor"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "xgboost")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "performance", "classification", "xgboost",
            "cache_hit_prediction", f"{catalog}.{feature_schema}.performance_features"
        ))
        mlflow.log_params(hyperparams)
        mlflow.log_params({"feature_engineering": "unity_catalog"})
        mlflow.log_metrics(metrics)
        
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.xgboost,
            training_set=training_set,
            registered_model_name=registered_name
        )
        
        print(f"✓ Model logged with Feature Engineering")
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": "XGBClassifier",
            "hyperparameters": hyperparams,
            "metrics": metrics
        }

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("CACHE HIT PREDICTOR - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("cache_hit_predictor")
    
    try:
        training_set, training_df, feature_names = create_training_set_with_features(spark, fe, catalog, feature_schema, gold_schema)
        model, metrics, hyperparams, X_train = prepare_and_train(training_df, feature_names)
        result = log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, X_train)
        
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
