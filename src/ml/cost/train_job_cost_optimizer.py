# Databricks notebook source
"""
Job Cost Optimizer - MLflow 3.0 Training Script
===============================================

Model 1.4: Job Cost Optimizer
Problem Type: Regression + Optimization
Business Value: 20-50% cost reduction through right-sizing

Features from Jobs System Tables Dashboard patterns:
- Worker count, memory, autoscaling configuration
- CPU/memory utilization metrics
- Historical cost patterns

MLflow 3.0 Features:
- LoggedModel with signature
- Unity Catalog Model Registry
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
from common.training_utils import (
    TrainingConfig, split_data, evaluate_model, get_feature_importance
)

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def prepare_job_cost_features(spark, catalog: str, gold_schema: str) -> pd.DataFrame:
    """
    Prepare features for job cost optimization.
    
    Joins job run data with node utilization to identify
    right-sizing opportunities.
    """
    fact_job_run = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    fact_usage = f"{catalog}.{gold_schema}.fact_usage"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    
    df = spark.sql(f"""
        WITH job_costs AS (
            SELECT
                u.usage_metadata_job_id AS job_id,
                j.name AS job_name,
                j.task_count,
                SUM(u.usage_quantity) AS total_dbu,
                COUNT(DISTINCT u.usage_metadata_job_run_id) AS run_count,
                AVG(u.usage_quantity) AS avg_dbu_per_run
            FROM {fact_usage} u
            LEFT JOIN {dim_job} j ON u.usage_metadata_job_id = j.job_id
            WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
                AND u.usage_metadata_job_id IS NOT NULL
            GROUP BY u.usage_metadata_job_id, j.name, j.task_count
        ),
        job_performance AS (
            SELECT
                job_id,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS success_count,
                AVG(TIMESTAMPDIFF(MINUTE, period_start_time, period_end_time)) AS avg_duration_minutes,
                STDDEV(TIMESTAMPDIFF(MINUTE, period_start_time, period_end_time)) AS duration_std
            FROM {fact_job_run}
            WHERE period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
            GROUP BY job_id
        )
        SELECT 
            jc.*,
            jp.total_runs,
            jp.success_count,
            jp.avg_duration_minutes,
            jp.duration_std,
            COALESCE(jp.success_count / NULLIF(jp.total_runs, 0), 0) AS success_rate,
            -- Cost efficiency metrics
            jc.total_dbu / NULLIF(jc.run_count, 0) AS cost_per_run,
            jc.total_dbu / NULLIF(jp.avg_duration_minutes * jc.run_count, 0) AS cost_per_minute
        FROM job_costs jc
        LEFT JOIN job_performance jp ON jc.job_id = jp.job_id
        WHERE jc.run_count >= 5  -- Minimum runs for reliable statistics
    """).toPandas()
    
    print(f"Job cost features shape: {df.shape}")
    return df

# COMMAND ----------

def train_cost_predictor(df: pd.DataFrame) -> tuple:
    """Train model to predict job cost."""
    feature_columns = [
        "task_count", "run_count", "avg_dbu_per_run",
        "total_runs", "success_rate", "avg_duration_minutes", "duration_std"
    ]
    
    df = df.fillna(0)
    df = df[df["total_dbu"] > 0]  # Valid cost data
    
    X = df[feature_columns]
    y = df["total_dbu"]
    
    config = TrainingConfig(test_size=0.2, validation_size=0.1)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y, config)
    
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", GradientBoostingRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
        ))
    ])
    
    model.fit(X_train, y_train)
    
    return model, X_train, y_train, X_test, y_test, feature_columns

# COMMAND ----------

def main():
    """Main training pipeline."""
    catalog, gold_schema, feature_schema = get_parameters()
    
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("Job Cost Optimizer").getOrCreate()
    
    config = MLflowConfig(catalog=catalog, schema=feature_schema, model_prefix="health_monitor")
    setup_mlflow_experiment(config, "cost", "job_cost_optimizer")
    
    try:
        df = prepare_job_cost_features(spark, catalog, gold_schema)
        model, X_train, y_train, X_test, y_test, feature_columns = train_cost_predictor(df)
        
        metrics = evaluate_model(model, X_test, y_test, problem_type="regression")
        
        log_model_with_signature(
            model=model, model_name="job_cost_optimizer", config=config,
            flavor="sklearn", X_sample=X_train, y_sample=y_train,
            metrics=metrics, params={"n_estimators": 100, "max_depth": 5},
            custom_tags={"agent_domain": "cost", "model_type": "cost_prediction"}
        )
        
        print("✓ Job Cost Optimizer Training Complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

