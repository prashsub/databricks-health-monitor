# Databricks notebook source
"""
Security Threat Detector - MLflow 3.0 Training Script
=====================================================

Model 2.1: Security Threat Detector
Problem Type: Anomaly Detection + Classification
Business Value: Early threat detection, compliance monitoring, incident prevention

Features:
- User behavior patterns (login, access, activity)
- Off-hours and weekend activity rates
- Sensitive data access patterns
- Peer comparison metrics

MLflow 3.0 Best Practices:
- LoggedModel with signature required for Unity Catalog
- Feature Engineering integration for lineage
"""

# COMMAND ----------

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mlflow_utils import (
    MLflowConfig, setup_mlflow_experiment, log_model_with_signature
)
from common.training_utils import TrainingConfig, evaluate_model

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def prepare_security_features(spark, catalog: str, feature_schema: str) -> pd.DataFrame:
    """Load security features from feature store."""
    feature_table = f"{catalog}.{feature_schema}.security_features"
    
    df = spark.table(feature_table).toPandas()
    df = df.fillna(0)
    
    print(f"Security features shape: {df.shape}")
    return df

# COMMAND ----------

def train_threat_detector(df: pd.DataFrame) -> tuple:
    """
    Train Isolation Forest for threat detection.
    
    Two-stage approach:
    1. Unsupervised anomaly detection with Isolation Forest
    2. Semi-supervised refinement with pseudo-labels
    """
    feature_columns = [
        "event_count", "tables_accessed", "off_hours_events",
        "weekend_events", "sensitive_access", "off_hours_rate",
        "weekend_rate", "sensitive_access_rate", "event_7day_avg",
        "event_z_score"
    ]
    
    X = df[feature_columns]
    
    # Stage 1: Isolation Forest for anomaly detection
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("isolation_forest", IsolationForest(
            n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1
        ))
    ])
    
    model.fit(X)
    
    # Get predictions
    predictions = model.predict(X)
    anomaly_scores = model.named_steps["isolation_forest"].decision_function(
        model.named_steps["scaler"].transform(X)
    )
    
    df["threat_score"] = -anomaly_scores  # Higher = more suspicious
    df["is_threat"] = (predictions == -1).astype(int)
    
    threat_count = (predictions == -1).sum()
    print(f"Threats detected: {threat_count} ({threat_count/len(X)*100:.2f}%)")
    
    return model, X, df, feature_columns

# COMMAND ----------

def main():
    """Main training pipeline."""
    catalog, gold_schema, feature_schema = get_parameters()
    
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("Security Threat Detector").getOrCreate()
    
    config = MLflowConfig(catalog=catalog, schema=feature_schema, model_prefix="health_monitor")
    setup_mlflow_experiment(config, "security", "security_threat_detector")
    
    try:
        df = prepare_security_features(spark, catalog, feature_schema)
        model, X, df_with_scores, feature_columns = train_threat_detector(df)
        
        # Create pseudo-labels for evaluation
        pseudo_labels = (df_with_scores["event_z_score"].abs() > 3).astype(int)
        metrics = evaluate_model(model, X, pseudo_labels, problem_type="anomaly_detection")
        
        metrics["threat_rate"] = float(df_with_scores["is_threat"].mean())
        metrics["mean_threat_score"] = float(df_with_scores["threat_score"].mean())
        
        log_model_with_signature(
            model=model, model_name="security_threat_detector", config=config,
            flavor="sklearn", X_sample=X, metrics=metrics,
            params={"n_estimators": 100, "contamination": 0.05},
            custom_tags={"agent_domain": "security", "model_type": "threat_detection"}
        )
        
        print("✓ Security Threat Detector Training Complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

