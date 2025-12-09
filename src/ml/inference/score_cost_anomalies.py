# Databricks notebook source
"""
Cost Anomaly Scoring - Batch Inference
======================================

Scores cost data using the trained cost anomaly detection model.
Results are stored in an inference table for dashboards and alerting.

MLflow 3.0 Features:
- Load model from Unity Catalog with alias
- Feature lookup from Feature Engineering tables
- Store predictions in inference table

Reference: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-inference/
"""

# COMMAND ----------

import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from datetime import datetime

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def load_model_from_uc(catalog: str, schema: str, model_name: str, alias: str = "champion"):
    """
    Load a model from Unity Catalog using alias.
    
    MLflow 3.0: Models use aliases instead of stages.
    'champion' is the production-ready model.
    
    Args:
        catalog: Unity Catalog name
        schema: Schema name
        model_name: Short model name
        alias: Model alias (default: champion)
        
    Returns:
        Loaded model
    """
    mlflow.set_registry_uri("databricks-uc")
    
    full_model_name = f"{catalog}.{schema}.health_monitor_{model_name}"
    model_uri = f"models:/{full_model_name}@{alias}"
    
    print(f"Loading model: {model_uri}")
    model = mlflow.pyfunc.load_model(model_uri)
    
    return model

# COMMAND ----------

def load_features_for_scoring(spark, catalog: str, feature_schema: str) -> pd.DataFrame:
    """
    Load recent features for anomaly scoring.
    
    Scores the last 24 hours of data for real-time anomaly detection.
    """
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    df = spark.sql(f"""
        SELECT *
        FROM {feature_table}
        WHERE usage_date >= CURRENT_DATE() - INTERVAL 1 DAY
    """).toPandas()
    
    print(f"Features loaded: {len(df)} rows")
    return df

# COMMAND ----------

def score_anomalies(model, df: pd.DataFrame) -> pd.DataFrame:
    """
    Score data for cost anomalies.
    
    Args:
        model: Loaded MLflow model
        df: DataFrame with features
        
    Returns:
        DataFrame with predictions added
    """
    feature_columns = [
        "daily_dbu", "job_count", "cluster_count", "warehouse_count",
        "dow_sin", "dow_cos", "dom_sin", "dom_cos",
        "is_weekend", "is_month_end",
        "dbu_7day_avg", "dbu_7day_std", "dbu_30day_avg",
        "z_score", "pct_change_7day"
    ]
    
    # Ensure all columns exist and fill missing
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_columns].fillna(0)
    
    # Get predictions
    predictions = model.predict(X)
    
    # Isolation Forest returns -1 for anomaly, 1 for normal
    df["anomaly_prediction"] = predictions
    df["is_anomaly"] = (predictions == -1).astype(int)
    df["scored_at"] = datetime.now()
    
    anomaly_count = df["is_anomaly"].sum()
    print(f"Anomalies detected: {anomaly_count} ({anomaly_count/len(df)*100:.2f}%)")
    
    return df

# COMMAND ----------

def save_predictions(
    spark,
    df: pd.DataFrame,
    catalog: str,
    schema: str,
    table_name: str = "cost_anomaly_predictions"
):
    """
    Save predictions to an inference table in Unity Catalog.
    
    Uses MERGE to update existing records and insert new ones.
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    # Convert to Spark DataFrame
    spark_df = spark.createDataFrame(df)
    
    # Create table if not exists
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {full_table_name} (
            workspace_id STRING,
            sku_name STRING,
            usage_date DATE,
            daily_dbu DOUBLE,
            is_anomaly INT,
            anomaly_prediction INT,
            z_score DOUBLE,
            pct_change_7day DOUBLE,
            scored_at TIMESTAMP
        )
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'layer' = 'inference',
            'model' = 'cost_anomaly_detector'
        )
        COMMENT 'Cost anomaly detection predictions from ML model'
    """)
    
    # Create temp view for merge
    spark_df.createOrReplaceTempView("new_predictions")
    
    # Merge predictions
    spark.sql(f"""
        MERGE INTO {full_table_name} AS target
        USING new_predictions AS source
        ON target.workspace_id = source.workspace_id
           AND target.sku_name = source.sku_name
           AND target.usage_date = source.usage_date
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    
    print(f"Predictions saved to {full_table_name}")

# COMMAND ----------

def main():
    """Main inference pipeline."""
    print("\n" + "=" * 80)
    print("Cost Anomaly Scoring - Batch Inference")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Cost Anomaly Scoring").getOrCreate()
    
    try:
        # Load model
        model = load_model_from_uc(
            catalog=catalog,
            schema=feature_schema,
            model_name="cost_anomaly_detector"
        )
        
        # Load features
        df = load_features_for_scoring(spark, catalog, feature_schema)
        
        if len(df) == 0:
            print("No data to score. Exiting.")
            return
        
        # Score anomalies
        scored_df = score_anomalies(model, df)
        
        # Save predictions
        save_predictions(
            spark=spark,
            df=scored_df,
            catalog=catalog,
            schema=feature_schema,
            table_name="cost_anomaly_predictions"
        )
        
        # Log high-severity anomalies
        high_severity = scored_df[
            (scored_df["is_anomaly"] == 1) & 
            (scored_df["z_score"].abs() > 3)
        ]
        
        if len(high_severity) > 0:
            print(f"\n⚠️ HIGH-SEVERITY ANOMALIES: {len(high_severity)}")
            print(high_severity[["workspace_id", "sku_name", "usage_date", "daily_dbu", "z_score"]].to_string())
        
        print("\n" + "=" * 80)
        print("✓ Cost Anomaly Scoring Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during scoring: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

