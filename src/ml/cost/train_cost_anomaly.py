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

MLflow 3.1+ Best Practices:
- Uses /Shared/ experiment path (serverless compatible)
- Logs dataset for lineage tracking
- Registers model to Unity Catalog
- Includes comprehensive tags and metrics
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
    /Users/ paths fail silently if parent folder doesn't exist.
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


def log_training_dataset(spark, catalog: str, schema: str, table_name: str) -> bool:
    """
    Log training dataset for MLflow lineage tracking.
    
    CRITICAL: Must be called INSIDE mlflow.start_run() context!
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    try:
        print(f"  Logging dataset: {full_table_name}")
        training_df = spark.table(full_table_name)
        dataset = mlflow.data.from_spark(
            df=training_df, 
            table_name=full_table_name,
            version="latest"
        )
        mlflow.log_input(dataset, context="training")
        print(f"  ✓ Dataset logged: {full_table_name}")
        return True
    except Exception as e:
        print(f"  ⚠ Dataset logging warning: {e}")
        return False


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
        "training_data": training_table
    }

# COMMAND ----------

def load_features(spark: SparkSession, catalog: str, feature_schema: str):
    """Load cost features from feature table."""
    feature_table = f"{catalog}.{feature_schema}.cost_features"
    
    print(f"Loading features from {feature_table}...")
    
    features_df = spark.table(feature_table)
    
    row_count = features_df.count()
    print(f"✓ Loaded {row_count} rows")
    
    return features_df

# COMMAND ----------

def prepare_training_data(features_df):
    """
    Prepare features for Isolation Forest training.

    Includes blog-derived features:
    - ALL_PURPOSE cluster inefficiency (Workflow Advisor Blog)
    - Potential savings indicators
    - Serverless adoption ratio
    """
    feature_columns = [
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
        # =============================================================================
        # WORKFLOW ADVISOR BLOG FEATURES (NEW)
        # =============================================================================
        "jobs_on_all_purpose_cost",       # Cost of jobs running on ALL_PURPOSE
        "potential_job_cluster_savings",   # 40% potential savings
        "all_purpose_inefficiency_ratio",  # Ratio of inefficient spend
        "serverless_adoption_ratio",       # Serverless vs traditional
        "serverless_cost",                 # Absolute serverless cost
        "dlt_cost",                        # Delta Live Tables cost
        "model_serving_cost",              # Model serving cost
    ]

    # Convert to pandas for sklearn
    pandas_df = features_df.select(feature_columns).toPandas()

    # Convert all columns to float64 (handle Decimal types)
    for col in feature_columns:
        pandas_df[col] = pd.to_numeric(pandas_df[col], errors='coerce')

    # Fill NaN and infinite values
    pandas_df = pandas_df.fillna(0)
    pandas_df = pandas_df.replace([np.inf, -np.inf], 0)

    print(f"✓ Prepared training data with shape: {pandas_df.shape}")
    print(f"  Features: {feature_columns}")

    return pandas_df, feature_columns

# COMMAND ----------

def train_isolation_forest(X: pd.DataFrame, contamination: float = 0.05):
    """
    Train Isolation Forest model for anomaly detection.
    
    Args:
        X: Feature DataFrame
        contamination: Expected proportion of anomalies
        
    Returns:
        Trained model, predictions, and anomaly scores
        
    Raises:
        ValueError: If no training samples available
    """
    print("\nTraining Isolation Forest model...")
    print(f"  Contamination: {contamination}")
    print(f"  Training samples: {len(X)}")
    
    if len(X) == 0:
        raise ValueError("No training samples available! Ensure the feature pipeline has populated cost_features with data.")
    
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

def log_model_to_mlflow(
    model,
    X: pd.DataFrame,
    feature_columns: list,
    catalog: str,
    feature_schema: str,
    experiment_name: str,
    spark: SparkSession
):
    """
    Log model to MLflow with Unity Catalog registry.
    
    Follows MLflow 3.1+ best practices:
    - Dataset logging inside run context
    - Signature with both input AND output
    - Comprehensive tags and metrics
    - UC model registration
    """
    model_name = "cost_anomaly_detector"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "isolation_forest", "v1")
    
    print(f"\nLogging model to MLflow: {registered_model_name}")
    
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
        
        # 2. Log dataset (MUST be inside run context)
        log_training_dataset(spark, catalog, feature_schema, "cost_features")
        
        # 3. Log hyperparameters
        mlflow.log_params({
            "model_type": "IsolationForest",
            "n_estimators": 100,
            "contamination": 0.05,
            "max_samples": "auto",
            "random_state": 42,
            "feature_count": len(feature_columns),
            "training_samples": len(X),
            "features": ", ".join(feature_columns)
        })
        
        # 4. Log metrics
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
        
        # 5. Create signature with BOTH input AND output (required for UC)
        sample_input = X.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # 6. Log and register model
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            signature=signature,
            input_example=sample_input,
            registered_model_name=registered_model_name
        )
        
        run_id = run.info.run_id
        print(f"✓ Model logged successfully")
        print(f"  Run ID: {run_id}")
        print(f"  Registered Model: {registered_model_name}")
        print(f"  Experiment: {experiment_name}")
    
    return run_id, registered_model_name

# COMMAND ----------

def main():
    """Main entry point for cost anomaly detector training."""
    print("\n" + "=" * 80)
    print("COST ANOMALY DETECTOR - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    
    # Get Spark session
    spark = SparkSession.builder.getOrCreate()
    
    # Setup MLflow experiment
    experiment_name = setup_mlflow_experiment("cost_anomaly_detector")
    
    try:
        # Load features
        features_df = load_features(spark, catalog, feature_schema)
        
        # Prepare training data
        X, feature_columns = prepare_training_data(features_df)
        
        # Train model
        model, predictions, scores = train_isolation_forest(X, contamination=0.05)
        
        # Log to MLflow
        run_id, model_name = log_model_to_mlflow(
            model=model,
            X=X,
            feature_columns=feature_columns,
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
            "metrics": {"training_samples": len(X), "features": len(feature_columns)}
        })
        dbutils.notebook.exit(exit_summary)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"\n❌ Error during training: {error_msg}")
        print(traceback.format_exc())
        
        import json
        exit_summary = json.dumps({
            "status": "FAILED",
            "model": "cost_anomaly_detector",
            "error": error_msg[:500]
        })
        dbutils.notebook.exit(exit_summary)
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
