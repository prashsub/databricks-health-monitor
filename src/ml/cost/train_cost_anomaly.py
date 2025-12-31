# Databricks notebook source
"""
Train Cost Anomaly Detector Model
=================================

Problem: Anomaly Detection (Unsupervised)
Algorithm: Isolation Forest
Domain: Cost

This model detects unusual DBU consumption patterns that may indicate:
- Runaway jobs consuming excessive resources
- Misconfigured clusters
- Unexpected spikes in serverless compute
- Unauthorized or wasteful usage

Feature Engineering in Unity Catalog:
- Uses FeatureLookup for automatic lineage tracking
- Enables automatic feature lookup at inference time
- Follows official Databricks best practices

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
from datetime import datetime

# Feature Engineering imports
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

# =============================================================================
# MLflow Configuration (at module level, before any MLflow calls)
# =============================================================================
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# =============================================================================
# INLINE HELPER FUNCTIONS (Required - do not import from modules)
# =============================================================================

def get_parameters():
    """Get job parameters from dbutils widgets (NEVER use argparse)."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema


def setup_mlflow_experiment(model_name: str) -> str:
    """
    Set up MLflow experiment using /Shared/ path.
    
    CRITICAL: Always use /Shared/ path for serverless compatibility.
    """
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    
    try:
        experiment = mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment set: {experiment_name}")
        print(f"  Experiment ID: {experiment.experiment_id}")
        return experiment_name
    except Exception as e:
        print(f"⚠ Experiment setup warning: {e}")
        return experiment_name


def get_run_name(model_name: str, algorithm: str, version: str = "v1") -> str:
    """Generate descriptive run name for MLflow tracking."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_{version}_{timestamp}"


def get_standard_tags(model_name: str, domain: str, model_type: str, 
                      algorithm: str, use_case: str, training_table: str) -> dict:
    """Get standard MLflow run tags for consistent organization."""
    return {
        "project": "databricks_health_monitor",
        "domain": domain,
        "model_name": model_name,
        "model_type": model_type,
        "algorithm": algorithm,
        "layer": "ml",
        "team": "data_engineering",
        "use_case": use_case,
        "training_data": training_table,
        "feature_engineering": "unity_catalog"
    }

# COMMAND ----------

def create_training_set_with_features(
    spark: SparkSession, 
    fe: FeatureEngineeringClient,
    catalog: str, 
    feature_schema: str
):
    """
    Create training set using Feature Engineering in Unity Catalog.
    
    This uses FeatureLookup to:
    - Automatically track lineage (visible in Unity Catalog)
    - Enable automatic feature lookup at inference
    - Support point-in-time correctness
    
    Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
    """
    print("\nCreating training set with Feature Engineering...")
    
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    # Feature columns to use for training
    feature_names = [
        # Core cost metrics
        "daily_dbu",
        "daily_cost",
        "avg_dbu_7d",
        "avg_dbu_30d",
        "z_score_7d",
        "z_score_30d",
        "dbu_change_pct_1d",
        "dbu_change_pct_7d",
        # Time features
        "dow_sin",
        "dow_cos",
        "is_weekend",
        "is_month_end",
        # Workflow Advisor Blog features
        "jobs_on_all_purpose_cost",
        "potential_job_cluster_savings",
        "all_purpose_inefficiency_ratio",
        "serverless_adoption_ratio",
        "serverless_cost",
        "dlt_cost",
        "model_serving_cost",
    ]
    
    # Create FeatureLookup - specifies which features to use and how to join
    # Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
    # NOTE: cost_features PK is [workspace_id, usage_date] - sku_name was aggregated away
    feature_lookups = [
        FeatureLookup(
            table_name=feature_table,
            feature_names=feature_names,
            lookup_key=["workspace_id", "usage_date"]  # Primary keys
        )
    ]
    
    # Create base DataFrame with primary keys for joining
    # This DataFrame defines which records to train on
    base_df = spark.table(feature_table).select(
        "workspace_id", 
        "usage_date"
    ).distinct()
    
    record_count = base_df.count()
    print(f"  Base DataFrame has {record_count} records")
    
    if record_count == 0:
        raise ValueError(f"No data found in {feature_table}!")
    
    # For unsupervised learning (anomaly detection), we don't have a label
    # We create a dummy label column that will be excluded
    base_df = base_df.withColumn("_dummy_label", F.lit(0))
    
    # Create training set using Feature Engineering client
    # This automatically tracks lineage in Unity Catalog
    training_set = fe.create_training_set(
        df=base_df,
        feature_lookups=feature_lookups,
        label="_dummy_label",  # Dummy label for unsupervised
        exclude_columns=["workspace_id", "usage_date"]  # Exclude keys from features
    )
    
    # Load the training DataFrame
    training_df = training_set.load_df()
    
    print(f"✓ Training set created with {training_df.count()} rows")
    print(f"  Columns: {training_df.columns}")
    
    return training_set, training_df, feature_names

# COMMAND ----------

def prepare_training_data(training_df, feature_names):
    """
    Prepare features for Isolation Forest training.
    
    Converts Spark DataFrame to pandas and handles type conversions.
    """
    print("\nPreparing training data...")
    
    # Convert to pandas for sklearn (exclude the dummy label)
    pandas_df = training_df.select(feature_names).toPandas()
    
    # Convert all columns to float64 (handle Decimal types)
    for col in feature_names:
        pandas_df[col] = pd.to_numeric(pandas_df[col], errors='coerce')
    
    # Fill NaN and infinite values
    pandas_df = pandas_df.fillna(0)
    pandas_df = pandas_df.replace([np.inf, -np.inf], 0)
    
    print(f"✓ Prepared training data with shape: {pandas_df.shape}")
    print(f"  Features: {feature_names}")
    
    return pandas_df

# COMMAND ----------

def train_isolation_forest(X: pd.DataFrame, contamination: float = 0.05):
    """
    Train Isolation Forest model for anomaly detection.
    
    Args:
        X: Feature DataFrame
        contamination: Expected proportion of anomalies
        
    Returns:
        Trained model, predictions, and anomaly scores
    """
    print("\nTraining Isolation Forest model...")
    print(f"  Contamination: {contamination}")
    print(f"  Training samples: {len(X)}")
    
    if len(X) == 0:
        raise ValueError("No training samples available!")
    
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X)
    
    predictions = model.predict(X)
    anomaly_scores = model.decision_function(X)
    
    n_anomalies = (predictions == -1).sum()
    anomaly_rate = n_anomalies / len(predictions) * 100
    
    print(f"✓ Model trained successfully")
    print(f"  Detected anomalies: {n_anomalies} ({anomaly_rate:.1f}%)")
    
    return model, predictions, anomaly_scores

# COMMAND ----------

def log_model_with_feature_engineering(
    fe: FeatureEngineeringClient,
    model,
    training_set,
    X: pd.DataFrame,
    feature_names: list,
    catalog: str,
    feature_schema: str,
    experiment_name: str,
    spark: SparkSession
):
    """
    Log model using Feature Engineering client for automatic feature lookup.
    
    Using fe.log_model() instead of mlflow.sklearn.log_model() enables:
    - Automatic feature lookup at inference time
    - Full lineage tracking in Unity Catalog
    - Model serving with automatic feature retrieval
    
    Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
    """
    model_name = "cost_anomaly_detector"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "isolation_forest", "v1")
    
    print(f"\nLogging model with Feature Engineering: {registered_model_name}")
    
    # Disable autolog for explicit control
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Set tags first
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="cost",
            model_type="anomaly_detection",
            algorithm="isolation_forest",
            use_case="cost_anomaly_detection",
            training_table=f"{catalog}.{feature_schema}.cost_features"
        ))
        
        # 2. Log hyperparameters
        mlflow.log_params({
            "model_type": "IsolationForest",
            "n_estimators": 100,
            "contamination": 0.05,
            "max_samples": "auto",
            "random_state": 42,
            "feature_count": len(feature_names),
            "training_samples": len(X),
            "features": ", ".join(feature_names),
            "feature_engineering": "unity_catalog"
        })
        
        # 3. Log metrics
        predictions = model.predict(X)
        anomaly_scores = model.decision_function(X)
        anomaly_rate = (predictions == -1).sum() / len(predictions)
        
        mlflow.log_metrics({
            "anomaly_rate": anomaly_rate,
            "training_samples": len(X),
            "n_anomalies": int((predictions == -1).sum()),
            "avg_anomaly_score": float(anomaly_scores.mean()),
            "min_anomaly_score": float(anomaly_scores.min()),
            "max_anomaly_score": float(anomaly_scores.max())
        })
        
        # 4. Log model using Feature Engineering client
        # This enables automatic feature lookup at inference time
        fe.log_model(
            model=model,
            artifact_path="model",
            flavor=mlflow.sklearn,
            training_set=training_set,
            registered_model_name=registered_model_name
        )
        
        run_id = run.info.run_id
        print(f"✓ Model logged with Feature Engineering")
        print(f"  Run ID: {run_id}")
        print(f"  Registered Model: {registered_model_name}")
        print(f"  Experiment: {experiment_name}")
        print(f"  Feature Store Integration: ENABLED")
    
    return run_id, registered_model_name

# COMMAND ----------

def main():
    """Main entry point for cost anomaly detector training."""
    print("\n" + "=" * 80)
    print("COST ANOMALY DETECTOR - TRAINING")
    print("Feature Engineering in Unity Catalog")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Initialize Feature Engineering client
    fe = FeatureEngineeringClient()
    print("✓ Feature Engineering client initialized")
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("cost_anomaly_detector")
    
    try:
        # Create training set with Feature Engineering
        training_set, training_df, feature_names = create_training_set_with_features(
            spark, fe, catalog, feature_schema
        )
        
        # Prepare training data (convert to pandas)
        X = prepare_training_data(training_df, feature_names)
        
        # Train model
        model, predictions, scores = train_isolation_forest(X, contamination=0.05)
        
        # Log model with Feature Engineering (enables automatic feature lookup)
        run_id, model_name = log_model_with_feature_engineering(
            fe=fe,
            model=model,
            training_set=training_set,
            X=X,
            feature_names=feature_names,
            catalog=catalog,
            feature_schema=feature_schema,
            experiment_name=experiment_name,
            spark=spark
        )
        
        print("\n" + "=" * 80)
        print("✓ COST ANOMALY DETECTOR TRAINING COMPLETE")
        print(f"  Model: {model_name}")
        print(f"  MLflow Run: {run_id}")
        print(f"  Training samples: {len(X)}")
        print(f"  Feature Engineering: Unity Catalog ENABLED")
        print("=" * 80)
        
        # Exit with detailed summary
        import json
        hyperparams = {"n_estimators": 100, "contamination": 0.05, "random_state": 42}
        exit_summary = json.dumps({
            "status": "SUCCESS",
            "model": "cost_anomaly_detector",
            "registered_as": model_name,
            "run_id": run_id,
            "algorithm": "IsolationForest",
            "hyperparameters": hyperparams,
            "metrics": {"training_samples": len(X), "features": len(feature_names)},
            "feature_engineering": "unity_catalog"
        })
        dbutils.notebook.exit(exit_summary)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"\n❌ Error during training: {error_msg}")
        print(traceback.format_exc())
        # Don't call dbutils.notebook.exit() here - it prevents raise from executing
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
