# Databricks notebook source
"""
Cost Anomaly Detector - MLflow 3.0 Training Script
==================================================

Model 1.1: Cost Anomaly Detector
Problem Type: Anomaly Detection (Unsupervised → Semi-supervised)
Business Value: Prevent budget overruns, identify runaway jobs, detect billing errors

Algorithm Evolution:
- Phase 1: Isolation Forest (unsupervised baseline)
- Phase 2: LSTM Autoencoder (when labeled data available)

MLflow 3.0 Features:
- LoggedModel with name parameter
- Unity Catalog Model Registry
- Feature Engineering integration
- Inference tables for monitoring

Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow/mlflow-3-install
"""

# COMMAND ----------

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.mlflow_utils import (
    MLflowConfig, 
    setup_mlflow_experiment, 
    log_model_with_signature
)
from common.training_utils import (
    TrainingConfig, 
    evaluate_model, 
    get_feature_importance,
    create_binary_labels_from_zscore
)

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema

# COMMAND ----------

def prepare_training_data(spark, catalog: str, feature_schema: str) -> pd.DataFrame:
    """
    Prepare training data for cost anomaly detection.
    
    Uses Feature Engineering in Unity Catalog for automatic lineage tracking.
    """
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    # Load features from feature store
    df = spark.table(feature_table).toPandas()
    
    # Select relevant features for anomaly detection
    feature_columns = [
        "daily_dbu",
        "job_count",
        "cluster_count",
        "warehouse_count",
        "dow_sin",
        "dow_cos",
        "dom_sin",
        "dom_cos",
        "is_weekend",
        "is_month_end",
        "dbu_7day_avg",
        "dbu_7day_std",
        "dbu_30day_avg",
        "z_score",
        "pct_change_7day",
    ]
    
    # Filter to valid rows
    df = df.dropna(subset=feature_columns)
    
    print(f"Training data shape: {df.shape}")
    print(f"Features: {feature_columns}")
    
    return df, feature_columns

# COMMAND ----------

def train_isolation_forest(
    df: pd.DataFrame,
    feature_columns: list,
    contamination: float = 0.1,
    n_estimators: int = 100,
    random_state: int = 42
) -> tuple:
    """
    Train Isolation Forest for cost anomaly detection.
    
    Args:
        df: Training DataFrame
        feature_columns: List of feature column names
        contamination: Expected proportion of anomalies
        n_estimators: Number of trees in the forest
        random_state: Random seed
        
    Returns:
        Tuple of (trained_model, X_train, predictions)
    """
    print("\n" + "=" * 60)
    print("Training Isolation Forest")
    print("=" * 60)
    
    X = df[feature_columns].copy()
    
    # Create pipeline with scaler
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("isolation_forest", IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
            verbose=1
        ))
    ])
    
    # Train the model
    model.fit(X)
    
    # Get predictions (-1 for anomaly, 1 for normal)
    predictions = model.predict(X)
    anomaly_scores = model.named_steps["isolation_forest"].decision_function(
        model.named_steps["scaler"].transform(X)
    )
    
    # Add predictions to dataframe for analysis
    df["anomaly_prediction"] = predictions
    df["anomaly_score"] = anomaly_scores
    df["is_anomaly"] = (predictions == -1).astype(int)
    
    # Summary statistics
    anomaly_count = (predictions == -1).sum()
    normal_count = (predictions == 1).sum()
    
    print(f"\nTraining Results:")
    print(f"  Total samples: {len(X)}")
    print(f"  Normal: {normal_count} ({normal_count/len(X)*100:.1f}%)")
    print(f"  Anomalies: {anomaly_count} ({anomaly_count/len(X)*100:.1f}%)")
    print(f"  Mean anomaly score: {anomaly_scores.mean():.4f}")
    print(f"  Std anomaly score: {anomaly_scores.std():.4f}")
    
    return model, X, df

# COMMAND ----------

def create_pseudo_labels(df: pd.DataFrame) -> pd.Series:
    """
    Create pseudo-labels for semi-supervised learning.
    
    Uses multiple heuristics to identify likely anomalies:
    - High z-scores (>3 or <-3)
    - Extreme percentage changes (>100%)
    - Zero activity when historical average is high
    """
    is_anomaly = pd.Series(False, index=df.index)
    
    # High z-score
    is_anomaly |= (df["z_score"].abs() > 3)
    
    # Extreme percentage changes
    is_anomaly |= (df["pct_change_7day"].abs() > 100)
    
    # Zero usage when average is high
    is_anomaly |= ((df["daily_dbu"] == 0) & (df["dbu_7day_avg"] > 100))
    
    print(f"\nPseudo-labels created:")
    print(f"  Anomalies identified: {is_anomaly.sum()} ({is_anomaly.mean()*100:.1f}%)")
    
    return is_anomaly.astype(int)

# COMMAND ----------

def log_cost_anomaly_model(
    model,
    X_train: pd.DataFrame,
    df: pd.DataFrame,
    config: MLflowConfig,
    params: dict
) -> str:
    """
    Log the cost anomaly detector to MLflow with proper signature.
    
    Uses MLflow 3.0 best practices:
    - 'name' parameter instead of 'artifact_path'
    - Model signature for Unity Catalog
    - Feature importance logging
    - Custom metrics
    """
    # Create pseudo-labels for evaluation
    pseudo_labels = create_pseudo_labels(df)
    
    # Evaluate with pseudo-labels
    metrics = evaluate_model(
        model=model,
        X_test=X_train,
        y_test=pseudo_labels,
        problem_type="anomaly_detection"
    )
    
    # Add model-specific metrics
    predictions = model.predict(X_train)
    anomaly_scores = model.named_steps["isolation_forest"].decision_function(
        model.named_steps["scaler"].transform(X_train)
    )
    
    metrics["anomaly_rate"] = float((predictions == -1).mean())
    metrics["anomaly_score_mean"] = float(anomaly_scores.mean())
    metrics["anomaly_score_std"] = float(anomaly_scores.std())
    metrics["anomaly_score_min"] = float(anomaly_scores.min())
    metrics["anomaly_score_max"] = float(anomaly_scores.max())
    
    # Log the model
    model_info = log_model_with_signature(
        model=model,
        model_name="cost_anomaly_detector",
        config=config,
        flavor="sklearn",
        X_sample=X_train,
        metrics=metrics,
        params=params,
        custom_tags={
            "agent_domain": "cost",
            "model_type": "anomaly_detection",
            "algorithm": "isolation_forest",
            "problem_type": "unsupervised"
        },
        extra_pip_requirements=[
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0"
        ]
    )
    
    print("\n" + "=" * 60)
    print("Model Logged to MLflow")
    print("=" * 60)
    print(f"Model Name: cost_anomaly_detector")
    print(f"Registered: {config.get_registered_model_name('cost_anomaly_detector')}")
    print(f"\nMetrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
    
    return model_info.model_uri

# COMMAND ----------

def main():
    """Main training pipeline for cost anomaly detector."""
    print("\n" + "=" * 80)
    print("Cost Anomaly Detector - MLflow 3.0 Training")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Initialize Spark
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("Cost Anomaly Detector").getOrCreate()
    
    # Configure MLflow
    config = MLflowConfig(
        catalog=catalog,
        schema=feature_schema,
        model_prefix="health_monitor"
    )
    
    # Setup experiment
    experiment_id = setup_mlflow_experiment(
        config=config,
        agent_domain="cost",
        model_name="cost_anomaly_detector"
    )
    
    try:
        # Prepare training data
        df, feature_columns = prepare_training_data(spark, catalog, feature_schema)
        
        # Training parameters
        params = {
            "n_estimators": 100,
            "contamination": 0.1,
            "max_samples": "auto",
            "max_features": 1.0,
            "random_state": 42,
            "n_features": len(feature_columns)
        }
        
        # Train model
        model, X_train, df_with_predictions = train_isolation_forest(
            df=df,
            feature_columns=feature_columns,
            contamination=params["contamination"],
            n_estimators=params["n_estimators"],
            random_state=params["random_state"]
        )
        
        # Log to MLflow with Unity Catalog registration
        model_uri = log_cost_anomaly_model(
            model=model,
            X_train=X_train,
            df=df_with_predictions,
            config=config,
            params=params
        )
        
        print("\n" + "=" * 80)
        print("✓ Cost Anomaly Detector Training Complete!")
        print("=" * 80)
        print(f"Model URI: {model_uri}")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        raise
    finally:
        spark.stop()

# COMMAND ----------

if __name__ == "__main__":
    main()

