# Databricks notebook source
"""
Query Performance Forecaster - MLflow 3.0 Training Script
=========================================================

Model 3.1: Query Performance Forecaster
Problem Type: Regression
Business Value: Accurate SLA commitments, better capacity planning

Features:
- Query characteristics (length, joins, aggregations)
- Historical query performance
- Warehouse features (size, load, queue depth)
- Time features (peak hours, day of week)

MLflow 3.0 Features:
- Model signature for Unity Catalog registration
- Feature Engineering integration
"""

# COMMAND ----------

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mlflow_utils import (
    MLflowConfig, setup_mlflow_experiment, log_model_with_signature
)
from common.training_utils import TrainingConfig, split_data, evaluate_model

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def prepare_query_features(spark, catalog: str, gold_schema: str) -> pd.DataFrame:
    """
    Prepare features for query performance prediction.
    """
    fact_query = f"{catalog}.{gold_schema}.fact_query_history"
    dim_warehouse = f"{catalog}.{gold_schema}.dim_warehouse"
    
    df = spark.sql(f"""
        SELECT 
            q.query_id,
            q.warehouse_id,
            w.name AS warehouse_name,
            w.cluster_size,
            q.duration_ms AS target_duration_ms,
            -- Query features
            LENGTH(q.statement_text) AS query_length,
            q.read_bytes,
            q.spill_to_disk_bytes,
            q.result_fetch_time_ms,
            -- Time features
            HOUR(q.start_time) AS hour_of_day,
            DAYOFWEEK(q.start_time) AS day_of_week,
            CASE WHEN HOUR(q.start_time) BETWEEN 9 AND 17 
                AND DAYOFWEEK(q.start_time) NOT IN (1, 7) THEN 1 ELSE 0 END AS is_business_hours,
            -- Error flag
            CASE WHEN q.error_message IS NOT NULL THEN 1 ELSE 0 END AS has_error
        FROM {fact_query} q
        LEFT JOIN {dim_warehouse} w ON q.warehouse_id = w.warehouse_id
        WHERE q.duration_ms IS NOT NULL 
            AND q.duration_ms > 0
            AND q.duration_ms < 3600000  -- Filter extreme outliers (1 hour)
            AND q.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    """).toPandas()
    
    df = df.fillna(0)
    
    # Encode warehouse size
    size_map = {'2X-Small': 1, 'X-Small': 2, 'Small': 3, 'Medium': 4, 'Large': 5, 'X-Large': 6, '2X-Large': 7}
    df['warehouse_size_encoded'] = df['cluster_size'].map(size_map).fillna(3)
    
    print(f"Query features shape: {df.shape}")
    return df

# COMMAND ----------

def train_query_forecaster(df: pd.DataFrame) -> tuple:
    """Train model to predict query duration."""
    feature_columns = [
        "query_length", "read_bytes", "spill_to_disk_bytes",
        "hour_of_day", "day_of_week", "is_business_hours",
        "warehouse_size_encoded"
    ]
    
    X = df[feature_columns]
    y = df["target_duration_ms"]
    
    # Log transform target for better distribution
    y_log = np.log1p(y)
    
    config = TrainingConfig(test_size=0.2, validation_size=0.1)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y_log, config)
    
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", GradientBoostingRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
        ))
    ])
    
    model.fit(X_train, y_train)
    
    return model, X_train, y_train, X_test, y_test, feature_columns

# COMMAND ----------

def main():
    """Main training pipeline."""
    catalog, gold_schema, feature_schema = get_parameters()
    
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("Query Performance Forecaster").getOrCreate()
    
    config = MLflowConfig(catalog=catalog, schema=feature_schema, model_prefix="health_monitor")
    setup_mlflow_experiment(config, "performance", "query_forecaster")
    
    try:
        df = prepare_query_features(spark, catalog, gold_schema)
        model, X_train, y_train, X_test, y_test, feature_columns = train_query_forecaster(df)
        
        metrics = evaluate_model(model, X_test, y_test, problem_type="regression")
        
        log_model_with_signature(
            model=model, model_name="query_forecaster", config=config,
            flavor="sklearn", X_sample=X_train, y_sample=y_train,
            metrics=metrics, params={"n_estimators": 100, "max_depth": 6},
            custom_tags={"agent_domain": "performance", "model_type": "duration_prediction"}
        )
        
        print("✓ Query Performance Forecaster Training Complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

