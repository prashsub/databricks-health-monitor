# Databricks notebook source
"""
Train Chargeback Attribution Model
==================================

Problem: Multi-output Regression
Algorithm: Gradient Boosting
Domain: Cost

Attributes costs to teams/projects for chargeback and FinOps.

MLflow 3.1+ Best Practices Applied
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd
import numpy as np
from datetime import datetime

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

def setup_mlflow_experiment(model_name: str) -> str:
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    mlflow.set_experiment(experiment_name)
    return experiment_name

def log_training_dataset(spark, catalog, schema, table_name):
    try:
        df = spark.table(f"{catalog}.{schema}.{table_name}")
        dataset = mlflow.data.from_spark(df=df, table_name=f"{catalog}.{schema}.{table_name}", version="latest")
        mlflow.log_input(dataset, context="training")
    except: pass

def get_run_name(model_name, algorithm):
    return f"{model_name}_{algorithm}_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def get_standard_tags(model_name, domain, model_type, algorithm, use_case, training_table):
    return {"project": "databricks_health_monitor", "domain": domain, "model_name": model_name,
            "model_type": model_type, "algorithm": algorithm, "use_case": use_case, "training_data": training_table}

# COMMAND ----------

def load_and_prepare_data(spark, catalog, feature_schema):
    df = spark.table(f"{catalog}.{feature_schema}.cost_features")
    feature_cols = ["daily_dbu", "avg_dbu_7d", "avg_dbu_30d", "dow_sin", "dow_cos", "is_weekend"]
    target = "daily_cost"
    
    pdf = df.select(feature_cols + [target]).toPandas()
    for c in pdf.columns:
        pdf[c] = pd.to_numeric(pdf[c], errors='coerce')
    pdf = pdf.fillna(0).replace([np.inf, -np.inf], 0)
    
    return train_test_split(pdf[feature_cols], pdf[target], test_size=0.2, random_state=42) + [feature_cols]

# COMMAND ----------

def train_and_log(X_train, X_test, y_train, y_test, feature_cols, catalog, feature_schema, spark):
    model_name = "chargeback_attribution"
    registered_name = f"{catalog}.{feature_schema}.{model_name}"
    
    model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    metrics = {"mae": mean_absolute_error(y_test, y_pred), "r2": r2_score(y_test, y_pred)}
    
    mlflow.autolog(disable=True)
    with mlflow.start_run(run_name=get_run_name(model_name, "gradient_boosting")) as run:
        mlflow.set_tags(get_standard_tags(model_name, "cost", "regression", "gradient_boosting",
                                          "chargeback_attribution", f"{catalog}.{feature_schema}.cost_features"))
        log_training_dataset(spark, catalog, feature_schema, "cost_features")
        mlflow.log_params({"n_estimators": 100, "max_depth": 5})
        mlflow.log_metrics(metrics)
        
        signature = infer_signature(X_train.head(5), model.predict(X_train.head(5)))
        mlflow.sklearn.log_model(model, "model", signature=signature, input_example=X_train.head(5),
                                 registered_model_name=registered_name)
        return run.info.run_id

# COMMAND ----------

def main():
    print("\n" + "=" * 60 + "\nCHARGEBACK ATTRIBUTION - TRAINING\n" + "=" * 60)
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    setup_mlflow_experiment("chargeback_attribution")
    
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
