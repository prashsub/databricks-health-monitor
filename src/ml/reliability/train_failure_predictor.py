# Databricks notebook source
"""
Train Job Failure Predictor Model
=================================

Problem: Classification
Algorithm: Gradient Boosting Classifier
Domain: Reliability

Predicts job failures before they happen.

MLflow 3.1+ Best Practices Applied
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import numpy as np
from datetime import datetime

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    return (dbutils.widgets.get("catalog"), dbutils.widgets.get("gold_schema"), dbutils.widgets.get("feature_schema"))

def setup_mlflow_experiment(model_name):
    mlflow.set_experiment(f"/Shared/health_monitor_ml_{model_name}")

def log_training_dataset(spark, catalog, schema, table_name):
    try:
        df = spark.table(f"{catalog}.{schema}.{table_name}")
        mlflow.log_input(mlflow.data.from_spark(df=df, table_name=f"{catalog}.{schema}.{table_name}", version="latest"), context="training")
    except: pass

def get_run_name(model_name, algorithm):
    return f"{model_name}_{algorithm}_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def get_standard_tags(model_name, domain, model_type, algorithm, use_case, training_table):
    return {"project": "databricks_health_monitor", "domain": domain, "model_name": model_name,
            "model_type": model_type, "algorithm": algorithm, "use_case": use_case, "training_data": training_table}

# COMMAND ----------

def load_and_prepare_data(spark, catalog, feature_schema):
    df = spark.table(f"{catalog}.{feature_schema}.reliability_features")
    # Actual columns: total_runs, avg_duration_sec, success_rate, total_failures_30d, duration_cv, rolling_avg_duration_30d
    feature_cols = ["total_runs", "avg_duration_sec", "success_rate", "total_failures_30d",
                    "duration_cv", "rolling_avg_duration_30d", "is_weekend", "day_of_week"]
    target = "prev_day_failed"  # Using prev_day_failed as target
    
    pdf = df.select(feature_cols + [target]).toPandas()
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    X = pdf[feature_cols]
    y = (pdf[target] > 0).astype(int)  # Binary classification
    
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if y.sum() > 1 else None) + [feature_cols]

# COMMAND ----------

def train_and_log(X_train, X_test, y_train, y_test, feature_cols, catalog, feature_schema, spark):
    """Train model and return comprehensive training summary."""
    model_name = "job_failure_predictor"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    # Define hyperparameters
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 5,
        "random_state": 42
    }
    
    model = GradientBoostingClassifier(**hyperparams)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    # Metrics
    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features_count": len(feature_cols)
    }
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(model_name, "reliability", "classification", "gradient_boosting",
                                          "failure_prediction", f"{catalog}.{feature_schema}.reliability_features"))
        log_training_dataset(spark, catalog, feature_schema, "reliability_features")
        mlflow.log_params(hyperparams)
        mlflow.log_metrics(metrics)
        
        signature = infer_signature(X_train.head(5), model.predict(X_train.head(5)))
        mlflow.sklearn.log_model(model, "model", signature=signature, input_example=X_train.head(5), registered_model_name=registered_name)
        
        # Return comprehensive summary
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": "GradientBoostingClassifier",
            "hyperparameters": hyperparams,
            "metrics": metrics,
            "features": feature_cols
        }

# COMMAND ----------

def main():
    import json
    print("\n" + "=" * 60 + "\nJOB FAILURE PREDICTOR - TRAINING\n" + "=" * 60)
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    setup_mlflow_experiment("job_failure_predictor")
    
    try:
        X_train, X_test, y_train, y_test, feature_cols = load_and_prepare_data(spark, catalog, feature_schema)
        result = train_and_log(X_train, X_test, y_train, y_test, feature_cols, catalog, feature_schema, spark)
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print("=" * 60)
        print(f"  Model:       {result['model_name']}")
        print(f"  Algorithm:   {result['algorithm']}")
        print(f"  Registered:  {result['registered_as']}")
        print(f"  MLflow Run:  {result['run_id']}")
        print("\n  Hyperparameters:")
        for k, v in result['hyperparameters'].items():
            print(f"    - {k}: {v}")
        print("\n  Metrics:")
        for k, v in result['metrics'].items():
            print(f"    - {k}: {v}")
        print(f"\n  Features ({len(result['features'])}):")
        for f in result['features'][:5]:
            print(f"    - {f}")
        if len(result['features']) > 5:
            print(f"    ... and {len(result['features']) - 5} more")
        print("=" * 60)
        
        # Exit with comprehensive JSON summary
        exit_summary = json.dumps({
            "status": "SUCCESS",
            "model": result['model_name'],
            "registered_as": result['registered_as'],
            "run_id": result['run_id'],
            "algorithm": result['algorithm'],
            "hyperparameters": result['hyperparameters'],
            "metrics": result['metrics']
        })
        dbutils.notebook.exit(exit_summary)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"\n❌ ERROR: {error_msg}")
        print(traceback.format_exc())
        
        exit_summary = json.dumps({
            "status": "FAILED",
            "model": "job_failure_predictor",
            "error": error_msg[:500],
            "error_type": type(e).__name__
        })
        dbutils.notebook.exit(exit_summary)
        raise  # Re-raise to fail the job

if __name__ == "__main__":
    main()
