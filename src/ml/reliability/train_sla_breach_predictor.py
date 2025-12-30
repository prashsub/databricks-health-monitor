# Databricks notebook source
"""
Train SLA Breach Predictor Model
================================

Problem: Classification
Algorithm: Gradient Boosting Classifier
Domain: Reliability

Predicts likelihood of SLA breaches for proactive alerting.

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
                    "duration_cv", "rolling_avg_duration_30d", "max_duration_sec", "is_weekend"]
    target = "failure_rate"  # Using failure_rate as proxy for SLA breach risk
    
    pdf = df.select(feature_cols + [target]).toPandas()
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    X = pdf[feature_cols]
    y = (pdf[target] > 0).astype(int)
    
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if y.sum() > 1 else None) + [feature_cols]

# COMMAND ----------

def train_and_log(X_train, X_test, y_train, y_test, feature_cols, catalog, feature_schema, spark):
    model_name = "sla_breach_predictor"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0)
    }
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(model_name, "reliability", "classification", "gradient_boosting",
                                          "sla_breach_prediction", f"{catalog}.{feature_schema}.reliability_features"))
        log_training_dataset(spark, catalog, feature_schema, "reliability_features")
        mlflow.log_params({"n_estimators": 100, "max_depth": 5})
        mlflow.log_metrics(metrics)
        
        signature = infer_signature(X_train.head(5), model.predict(X_train.head(5)))
        mlflow.sklearn.log_model(model, "model", signature=signature, input_example=X_train.head(5), registered_model_name=registered_name)
            # Return comprehensive summary
        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "registered_as": registered_name,
            "algorithm": "GradientBoostingClassifier",
            "hyperparameters": {"n_estimators": 100, "max_depth": 5, "random_state": 42},
            "metrics": dict(metrics, training_samples=len(X_train), test_samples=len(X_test), features=len(feature_cols)),
            "features": feature_cols
        }

# COMMAND ----------

def main():
    print("\n" + "=" * 60 + "\nSLA BREACH PREDICTOR - TRAINING\n" + "=" * 60)
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    setup_mlflow_experiment("sla_breach_predictor")
    
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
        print("=" * 60)
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        import json
        exit_summary = json.dumps({"status": "FAILED", "model": "sla_breach_predictor", "error": str(e)[:500]})
        dbutils.notebook.exit(exit_summary)
        raise  # Re-raise to fail the job
    
    import json
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

if __name__ == "__main__":
    main()
