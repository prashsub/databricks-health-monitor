# Databricks notebook source
"""
Train Budget Forecaster Model
=============================

Problem: Regression (Time Series)
Algorithm: Gradient Boosting Regressor
Domain: Cost

Forecasts future daily costs based on historical patterns.

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Uses fe.log_model() for automatic feature lookup at inference time

CRITICAL: Unity Catalog requires models with BOTH input AND output signatures.
All numeric columns are cast to float64 (MLflow doesn't support DECIMAL).

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

def create_training_set_with_features(spark, fe, catalog, feature_schema):
    """
    Create training set using Feature Engineering in Unity Catalog.
    
    Key Pattern from Databricks docs:
    1. Base DataFrame has ONLY lookup keys + label
    2. FeatureLookup specifies features (NOT the label)
    3. create_training_set joins features using lookup keys
    """
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    # Features to retrieve from feature table (excludes label)
    feature_names = [
        "avg_dbu_7d", "avg_dbu_30d", "std_dbu_7d", "std_dbu_30d",
        "dow_sin", "dow_cos", "is_weekend", "is_month_end",
        "day_of_week", "day_of_month", "dbu_change_pct_1d", "dbu_change_pct_7d",
        "serverless_adoption_ratio", "all_purpose_inefficiency_ratio",
        "jobs_on_all_purpose_cost", "serverless_cost", "dlt_cost", "model_serving_cost"
    ]
    
    label_col = "daily_cost"
    
    # FeatureLookup specifies which features to pull and how to join
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["workspace_id", "usage_date"]
        )
    ]
    
    # Base DataFrame: lookup keys + label ONLY
    base_df = (spark.table(feature_table)
               .select("workspace_id", "usage_date", label_col)
               .filter(F.col(label_col).isNotNull())
               .distinct())
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table}!")
    
    # Create training set - joins features to base DataFrame
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label=label_col,
        exclude_columns=["workspace_id", "usage_date"]
    )
    
    training_df = training_set.load_df()
    print(f"✓ Training set: {training_df.count()} rows, {len(feature_names)} features")
    
    return training_set, training_df, feature_names, label_col

# COMMAND ----------

def prepare_and_train(training_df, feature_names, label_col):
    """Prepare data and train the model."""
    print("\nPreparing data and training model...")
    
    pdf = training_df.toPandas()
    
    # Handle missing features gracefully
    available_features = [f for f in feature_names if f in pdf.columns]
    missing_features = [f for f in feature_names if f not in pdf.columns]
    if missing_features:
        print(f"  ⚠ Missing features: {missing_features}")
    
    X_train = pdf[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    y = pdf[label_col].fillna(0)
    
    # CRITICAL: Cast all columns to float64 (MLflow doesn't support DECIMAL)
    for col in X.columns:
        X[col] = X[col].astype('float64')
    y = y.astype('float64')
    
    X_train, X_test, y_train, y_test = train_test_split(X_train, y, test_size=0.2, random_state=42)
    
    print(f"  Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    hyperparams = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1, "random_state": 42}
    model = GradientBoostingRegressor(**hyperparams)
    model.fit(X_train, y_train)
    
    metrics = {
        "train_r2": round(float(model.score(X_train, y_train)), 4),
        "test_r2": round(float(model.score(X_test, y_test)), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features_count": len(available_features)
    }
    
    print(f"✓ Model trained: R² = {metrics['test_r2']:.4f}")
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(fe, model, training_set, metrics, hyperparams, catalog, feature_schema, feature_table, X_train):
    """
    Log model with Feature Engineering for automatic feature lookup at inference.
    
    CRITICAL: Unity Catalog requires BOTH input AND output signatures.
    We must provide input_example and explicit signature.
    """
    model_name = "budget_forecaster"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    # Create input example (first 5 rows, ensure float64)
    input_example = X_train.head(5).astype('float64')
    
    # Create sample predictions for output signature
    sample_predictions = model.predict(input_example)
    
    # Infer signature with BOTH input AND output (REQUIRED for Unity Catalog)
    signature = infer_signature(input_example, sample_predictions)
    print(f"  Signature: {len(input_example.columns)} inputs → float64 output")
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(
            model_name, "cost", "regression", "gradient_boosting",
            "budget_forecasting", feature_table
        ))
        mlflow.log_params(hyperparams)
        mlflow.log_params({"feature_engineering": "unity_catalog"})
        mlflow.log_metrics(metrics)
        
        # Log model with feature metadata for inference
        # input_example and signature are REQUIRED for Unity Catalog
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
    print("BUDGET FORECASTER - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("budget_forecaster")
    
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    try:
        training_set, training_df, feature_names, label_col = create_training_set_with_features(
            spark, fe, catalog, feature_schema
        )
        model, metrics, hyperparams, X_train = prepare_and_train(training_df, feature_names, label_col)
        result = log_model_with_feature_engineering(
            fe, model, training_set, metrics, hyperparams, 
            catalog, feature_schema, feature_table, X_train
        )
        
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print(f"  Model: {result['model_name']}")
        print(f"  R²: {result['metrics']['test_r2']}")
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
