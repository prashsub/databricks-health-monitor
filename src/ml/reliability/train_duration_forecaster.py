# Databricks notebook source
"""
Train Job Duration Forecaster Model
===================================

Problem: Regression
Algorithm: Gradient Boosting Regressor
Domain: Reliability

Forecasts job run durations.

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
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
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
    
    feature_table = f"{catalog}.{feature_schema}.reliability_features"
    fact_job = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    
    feature_names = ["total_runs", "avg_duration_sec", "success_rate", "failure_rate",
                     "duration_cv", "rolling_failure_rate_30d", "is_weekend", "day_of_week"]
    
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["job_id", "run_date"]
        )
    ]
    
    # Target: next day's average duration
    base_df = (spark.table(feature_table)
               .withColumn("target_duration", F.col("avg_duration_sec"))
               .select("job_id", "run_date", "target_duration")
               .filter(F.col("target_duration").isNotNull() & (F.col("target_duration") > 0)))
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    if record_count == 0:
        raise ValueError(f"No data found!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="target_duration",
        exclude_columns=["job_id", "run_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_and_train(training_df, feature_names):
    print("\nPreparing data and training model...")
    
    pdf = training_df.toPandas()
    X_train = pdf[feature_names].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf["target_duration"].fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    hyperparams = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42}
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    train_r2 = model.score(X_train, y_train)
    test_r2 = model.score(X_test, y_test)
    
    metrics = {
        "train_r2": round(float(train_r2), 4),
        "test_r2": round(float(test_r2), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    print(f"✓ Test R²: {test_r2:.4f}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, X_train):
    model_name = "job_duration_forecaster"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "reliability", "regression", "gradient_boosting",
            "duration_forecasting", f"{catalog}.{feature_schema}.reliability_features"
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
            "algorithm": "GradientBoostingRegressor",
            "hyperparameters": hyperparams,
            "metrics": metrics
        }

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60)
    print("JOB DURATION FORECASTER - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("job_duration_forecaster")
    
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
