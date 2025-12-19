# Databricks notebook source
"""
Train Schema Change Predictor Model
===================================

Problem: Classification
Algorithm: Gradient Boosting
Domain: Quality

Predicts likelihood of schema changes impacting data pipelines.

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
    # Using performance features as proxy for schema change indicators
    df = spark.table(f"{catalog}.{feature_schema}.performance_features")
    feature_cols = ["query_count", "error_rate", "spill_rate", "avg_query_count_7d", 
                    "total_bytes_read", "is_weekend", "day_of_week"]
    target = "schema_change_likely"  # Generated based on error patterns
    
    pdf = df.select(feature_cols + [target]).toPandas()
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    X = pdf[feature_cols]
    y = (pdf[target] > 0).astype(int)
    
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if y.sum() > 1 else None) + [feature_cols]

# COMMAND ----------

def train_and_log(X_train, X_test, y_train, y_test, feature_cols, catalog, feature_schema, spark):
    model_name = "schema_change_predictor"
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
        mlflow.set_tags(get_standard_tags(model_name, "quality", "classification", "gradient_boosting",
                                          "schema_change_prediction", f"{catalog}.{feature_schema}.performance_features"))
        log_training_dataset(spark, catalog, feature_schema, "performance_features")
        mlflow.log_params({"n_estimators": 100, "max_depth": 5})
        mlflow.log_metrics(metrics)
        
        signature = infer_signature(X_train.head(5), model.predict(X_train.head(5)))
        mlflow.sklearn.log_model(model, "model", signature=signature, input_example=X_train.head(5), registered_model_name=registered_name)
        return run.info.run_id

# COMMAND ----------

def main():
    print("\n" + "=" * 60 + "\nSCHEMA CHANGE PREDICTOR - TRAINING\n" + "=" * 60)
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    setup_mlflow_experiment("schema_change_predictor")
    
    try:
        X_train, X_test, y_train, y_test, feature_cols = load_and_prepare_data(spark, catalog, feature_schema)
        run_id = train_and_log(X_train, X_test, y_train, y_test, feature_cols, catalog, feature_schema, spark)
        print(f"✓ COMPLETE - Run: {run_id}")
    except Exception as e:
        import traceback
        print(f"❌ {e}\n{traceback.format_exc()}")
        dbutils.notebook.exit(f"FAILED: {e}")
    
    dbutils.notebook.exit("SUCCESS")

if __name__ == "__main__":
    main()
