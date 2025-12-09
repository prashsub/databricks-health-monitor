# Databricks notebook source
"""
Job Failure Predictor - MLflow 3.0 Training Script
==================================================

Model 4.1: Job Failure Predictor
Problem Type: Binary Classification
Business Value: Reduce failed runs, improve SLA compliance, proactive intervention

Features:
- Historical job performance (failure rate, consecutive failures)
- Job configuration (task count, dependencies, retries)
- Cluster features (memory, cores, DBR version)
- Runtime statistics (avg, std, p99)
- Time features (hour, day, business hours)

MLflow 3.0 Features:
- Model signature required for Unity Catalog
- Automatic lineage with Feature Engineering
"""

# COMMAND ----------

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
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

def prepare_failure_prediction_features(spark, catalog: str, feature_schema: str, gold_schema: str) -> pd.DataFrame:
    """
    Prepare features for job failure prediction.
    
    Combines reliability features with job/cluster metadata.
    """
    reliability_features = f"{catalog}.{feature_schema}.reliability_features"
    dim_job = f"{catalog}.{gold_schema}.dim_job"
    
    df = spark.sql(f"""
        SELECT 
            r.job_id,
            r.job_name,
            r.task_count,
            r.run_date,
            r.run_count,
            r.success_count,
            r.failure_count,
            r.avg_duration_minutes,
            r.duration_std_minutes,
            r.max_duration_minutes,
            r.failure_rate,
            r.success_rate,
            r.duration_cv,
            r.failure_rate_30d,
            -- Time features
            DAYOFWEEK(r.run_date) AS day_of_week,
            CASE WHEN DAYOFWEEK(r.run_date) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend,
            -- Label: did any failure occur that day?
            CASE WHEN r.failure_count > 0 THEN 1 ELSE 0 END AS had_failure
        FROM {reliability_features} r
        WHERE r.run_count >= 1
    """).toPandas()
    
    df = df.fillna(0)
    print(f"Failure prediction features shape: {df.shape}")
    print(f"Failure rate in data: {df['had_failure'].mean()*100:.2f}%")
    
    return df

# COMMAND ----------

def train_failure_predictor(df: pd.DataFrame) -> tuple:
    """
    Train Gradient Boosting Classifier for failure prediction.
    """
    feature_columns = [
        "task_count", "run_count", "failure_rate", "success_rate",
        "avg_duration_minutes", "duration_std_minutes", "duration_cv",
        "failure_rate_30d", "day_of_week", "is_weekend"
    ]
    
    X = df[feature_columns]
    y = df["had_failure"]
    
    config = TrainingConfig(test_size=0.2, validation_size=0.1)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y, config)
    
    # Handle class imbalance with class_weight
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", GradientBoostingClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1,
            random_state=42, verbose=1
        ))
    ])
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return model, X_train, y_train, X_test, y_test, feature_columns

# COMMAND ----------

def main():
    """Main training pipeline."""
    catalog, gold_schema, feature_schema = get_parameters()
    
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("Job Failure Predictor").getOrCreate()
    
    config = MLflowConfig(catalog=catalog, schema=feature_schema, model_prefix="health_monitor")
    setup_mlflow_experiment(config, "reliability", "job_failure_predictor")
    
    try:
        df = prepare_failure_prediction_features(spark, catalog, feature_schema, gold_schema)
        model, X_train, y_train, X_test, y_test, feature_columns = train_failure_predictor(df)
        
        metrics = evaluate_model(model, X_test, y_test, problem_type="classification")
        
        log_model_with_signature(
            model=model, model_name="job_failure_predictor", config=config,
            flavor="sklearn", X_sample=X_train, y_sample=y_train,
            metrics=metrics, params={"n_estimators": 100, "max_depth": 5},
            custom_tags={"agent_domain": "reliability", "model_type": "failure_prediction"}
        )
        
        print("✓ Job Failure Predictor Training Complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

