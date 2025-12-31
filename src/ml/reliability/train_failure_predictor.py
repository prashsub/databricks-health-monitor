# Databricks notebook source
"""
Train Job Failure Predictor Model
=================================

Problem: Classification
Algorithm: Gradient Boosting Classifier
Domain: Reliability

Predicts job failures before they happen.

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Enables automatic feature lookup at inference time
- Follows official Databricks best practices

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import numpy as np
from datetime import datetime

# Feature Engineering imports
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema


def setup_mlflow_experiment(model_name):
    """Set up MLflow experiment using /Shared/ path."""
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    try:
        mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment set: {experiment_name}")
    except Exception as e:
        print(f"⚠ Experiment setup: {e}")
    return experiment_name


def get_run_name(model_name, algorithm):
    return f"{model_name}_{algorithm}_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_standard_tags(model_name, domain, model_type, algorithm, use_case, training_table):
    return {
        "project": "databricks_health_monitor", 
        "domain": domain, 
        "model_name": model_name,
        "model_type": model_type, 
        "algorithm": algorithm, 
        "use_case": use_case, 
        "training_data": training_table,
        "feature_engineering": "unity_catalog"
    }

# COMMAND ----------

def create_training_set_with_features(
    spark: SparkSession, 
    fe: FeatureEngineeringClient,
    catalog: str, 
    feature_schema: str
):
    """
    Create training set using Feature Engineering in Unity Catalog.
    
    For classification, we specify the actual label column.
    
    Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
    """
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.reliability_features"
    
    # Feature columns for failure prediction
    feature_names = [
        "total_runs", 
        "avg_duration_sec", 
        "success_rate", 
        "total_failures_30d",
        "duration_cv", 
        "rolling_avg_duration_30d", 
        "is_weekend", 
        "day_of_week"
    ]
    
    # Label column - what we're predicting (will be binarized)
    label_column = "prev_day_failed"
    
    # Create FeatureLookup
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names + [label_column],
            lookup_key=["job_id", "run_date"]  # Primary keys for reliability_features
        )
    ]
    
    # Create base DataFrame with primary keys
    base_df = spark.table(feature_table).select(
        "job_id", 
        "run_date"
    ).distinct()
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table}!")
    
    # Create training set
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label=label_column,
        exclude_columns=["job_id", "run_date"]
    )
    
    # Load the training DataFrame
    training_df = training_set.load_df()
    
    print(f"✓ Training set created with {training_df.count()} rows")
    print(f"  Feature columns: {feature_names}")
    print(f"  Label column: {label_column}")
    
    return training_set, training_df, feature_names, label_column

# COMMAND ----------

def prepare_training_data(training_df, feature_names, label_column):
    """Prepare features for classification."""
    print("\nPreparing training data...")
    
    # Convert to pandas
    pdf = training_df.select(feature_names + [label_column]).toPandas()
    
    # Convert types
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    X_train = pdf[feature_names]
    y = (pdf[label_column] > 0).astype(int)  # Binary classification
    
    # Stratified split if possible
    stratify = y if y.sum() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )
    
    print(f"✓ Data: {X_train.shape[0]} train, {X_test.shape[0]} test samples")
    print(f"  Positive rate: {y.mean()*100:.1f}%")
    
    return X_train, X_test, y_train, y_test

# COMMAND ----------

def train_model(X_train, X_test, y_train, y_test):
    """Train Gradient Boosting Classifier."""
    print("\nTraining Gradient Boosting Classifier...")
    
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 5,
        "random_state": 42
    }
    
    model = GradientBoostingClassifier(**hyperparams)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    print(f"✓ Model trained - Accuracy: {metrics['accuracy']}, F1: {metrics['f1']}")
    
    return model, metrics, hyperparams, X_train

# COMMAND ----------

def log_model_with_feature_engineering(
    fe: FeatureEngineeringClient,
    model,
    training_set,
    X_train,
    metrics,
    hyperparams,
    feature_names,
    catalog,
    feature_schema
):
    """Log model using Feature Engineering client."""
    model_name = "job_failure_predictor"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    print(f"\nLogging model with Feature Engineering: {registered_name}")
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        # Tags
        mlflow.set_tags(get_standard_tags(
            model_name, "reliability", "classification", "gradient_boosting",
            "failure_prediction", f"{catalog}.{feature_schema}.reliability_features"
        ))
        
        # Parameters
        mlflow.log_params(hyperparams)
        mlflow.log_params({
            "feature_count": len(feature_names),
            "feature_engineering": "unity_catalog"
        })
        
        # Metrics
        mlflow.log_metrics(metrics)
        
        # Log model with Feature Engineering
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
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Registered: {registered_name}")
        print(f"  Feature Store Integration: ENABLED")
        
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": "GradientBoostingClassifier",
            "hyperparameters": hyperparams,
            "metrics": metrics,
            "features": feature_names
        }

# COMMAND ----------

def main():
    import json
    
    print("\n" + "=" * 60)
    print("JOB FAILURE PREDICTOR - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 60)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    # Initialize Feature Engineering client
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    setup_mlflow_experiment("job_failure_predictor")
    
    try:
        # Create training set with Feature Engineering
        training_set, training_df, feature_names, label_column = create_training_set_with_features(
            spark, fe, catalog, feature_schema
        )
        
        # Prepare training data
        X_train, X_test, y_train, y_test = prepare_training_data(
            training_df, feature_names, label_column
        )
        
        # Train model
        model, metrics, hyperparams = train_model(X_train, X_test, y_train, y_test)
        
        # Log model with Feature Engineering
        result = log_model_with_feature_engineering(
            fe=fe,
            model=model,
            training_set=training_set,
            X_train=X_train,
            metrics=metrics,
            hyperparams=hyperparams,
            feature_names=feature_names,
            catalog=catalog,
            feature_schema=feature_schema
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print("=" * 60)
        print(f"  Model:       {result['model_name']}")
        print(f"  Registered:  {result['registered_as']}")
        print(f"  MLflow Run:  {result['run_id']}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("\n  Metrics:")
        for k, v in result['metrics'].items():
            print(f"    - {k}: {v}")
        print("=" * 60)
        
        exit_summary = json.dumps({
            "status": "SUCCESS",
            "model": result['model_name'],
            "registered_as": result['registered_as'],
            "run_id": result['run_id'],
            "algorithm": result['algorithm'],
            "hyperparameters": result['hyperparameters'],
            "metrics": result['metrics'],
            "feature_engineering": "unity_catalog"
        })
        dbutils.notebook.exit(exit_summary)
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {str(e)}")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
