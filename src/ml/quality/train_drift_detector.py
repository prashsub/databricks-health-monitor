# Databricks notebook source
"""
Train Data Drift Detector Model
===============================

Problem: Anomaly Detection
Algorithm: Isolation Forest
Domain: Quality

Detects data drift and quality anomalies in data pipelines.

MLflow 3.1+ Best Practices Applied
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import IsolationForest
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
    # Quality features would come from monitoring/profiling tables
    # Using performance features as proxy for data drift indicators
    df = spark.table(f"{catalog}.{feature_schema}.performance_features")
    feature_cols = ["query_count", "avg_duration_ms", "error_rate", "spill_rate", 
                    "avg_query_count_7d", "total_bytes_read", "is_weekend"]
    
    pdf = df.select(feature_cols).toPandas()
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    return pdf.fillna(0).replace([np.inf, -np.inf], 0), feature_cols

# COMMAND ----------

def train_and_log(X, feature_cols, catalog, feature_schema, spark):
    model_name = "data_drift_detector"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X)
    
    predictions = model.predict(X)
    anomaly_rate = (predictions == -1).sum() / len(predictions)
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "isolation_forest")) as run:
        mlflow.set_tags(get_standard_tags(model_name, "quality", "anomaly_detection", "isolation_forest",
                                          "drift_detection", f"{catalog}.{feature_schema}.performance_features"))
        log_training_dataset(spark, catalog, feature_schema, "performance_features")
        mlflow.log_params({"n_estimators": 100, "contamination": 0.05})
        mlflow.log_metrics({"anomaly_rate": anomaly_rate, "training_samples": len(X)})
        
        signature = infer_signature(X.head(5), model.predict(X.head(5)))
        mlflow.sklearn.log_model(model, "model", signature=signature, input_example=X.head(5), registered_model_name=registered_name)
        return run.info.run_id

# COMMAND ----------

def main():
    print("\n" + "=" * 60 + "\nDATA DRIFT DETECTOR - TRAINING\n" + "=" * 60)
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    setup_mlflow_experiment("data_drift_detector")
    
    try:
        X, feature_cols = load_and_prepare_data(spark, catalog, feature_schema)
        run_id = train_and_log(X, feature_cols, catalog, feature_schema, spark)
        print(f"✓ COMPLETE - Run: {run_id}")
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        dbutils.notebook.exit(f"FAILED: {e}")
    
    dbutils.notebook.exit("SUCCESS")

if __name__ == "__main__":
    main()
