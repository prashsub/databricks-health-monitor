# Databricks notebook source
"""
Train Query Performance Forecaster Model
========================================

Problem: Regression
Algorithm: Gradient Boosting Regressor
Domain: Performance

Forecasts query execution times based on historical patterns.

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
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
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
    
    feature_table = f"{catalog}.{feature_schema}.performance_features"
    
    # Features matching the feature table columns (from create_feature_tables.py)
    feature_names = [
        "query_count", "total_duration_ms", "p50_duration_ms", "p95_duration_ms", "p99_duration_ms",
        "total_bytes_read", "total_bytes_written", "error_count", "spill_count",
        "sla_breach_count", "efficient_query_count", "high_queue_count", "large_query_count",
        "total_queue_time_ms", "active_minutes", "avg_duration_ms",
        "avg_query_count_7d", "avg_duration_7d", "avg_p99_duration_7d",
        "error_rate", "spill_rate", "avg_bytes_per_query", "read_write_ratio",
        "sla_breach_rate", "query_efficiency_rate", "high_queue_rate", "large_query_rate",
        "avg_queue_time_ms", "queries_per_minute", "is_duration_regressing",
        "is_weekend", "day_of_week"
    ]
    
    # Lookup keys match feature table PRIMARY KEY: ["warehouse_id", "query_date"]
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["warehouse_id", "query_date"]
        )
    ]
    
    # Label: predict p95 duration
    base_df = (spark.table(feature_table)
               .withColumn("target_duration_ms", F.col("p95_duration_ms"))
               .select("warehouse_id", "query_date", "target_duration_ms")
               .filter(F.col("target_duration_ms").isNotNull())
               .filter(F.col("target_duration_ms") > 0))
    
    record_count = base_df.count()
    print(f"  Base DataFrame: {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data in {feature_table}!")
    
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="target_duration_ms",
        exclude_columns=["warehouse_id", "query_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_and_train(training_df, feature_names):
    """Prepare and train model."""
    print("\nTraining Gradient Boosting model...")
    
    pdf = training_df.toPandas()
    available_features = [f for f in feature_names if f in pdf.columns]
    X_train = pdf[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    
    # CRITICAL: Cast to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    y = pdf["target_duration_ms"].fillna(0).replace([np.inf, -np.inf], 0)
    
    print(f"  Samples: {len(X_train)}, Features: {len(available_features)}")
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    hyperparams = {
        "n_estimators": 100, "max_depth": 5, "learning_rate": 0.1, "random_state": 42
    }
    
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    metrics = {
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    print(f"✓ Trained: RMSE={metrics['rmse']:.2f}, R²={metrics['r2']:.3f}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):
    """Log model with Feature Engineering."""
    model_name = "query_performance_forecaster"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model: {registered_name}")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "performance", "regression", "gradient_boosting",
            "query_performance_forecasting", feature_table
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
    print("QUERY PERFORMANCE FORECASTER - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    setup_mlflow_experiment("query_performance_forecaster")
    
    feature_table = f"{catalog}.{feature_schema}.performance_features"
    
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
        print(f"  R²: {result['metrics']['r2']:.3f}")
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
