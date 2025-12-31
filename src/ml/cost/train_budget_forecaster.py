# Databricks notebook source
"""
Train Budget Forecaster Model
=============================

Problem: Regression (Time Series Forecasting)
Algorithm: Gradient Boosting Regressor
Domain: Cost

This model predicts future monthly DBU costs to help:
- Budget planning and allocation
- Alert on projected overages
- Capacity planning
- Contract negotiation

MLflow 3.1+ Best Practices Applied
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# MLflow Configuration (at module level)
# =============================================================================
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# =============================================================================
# INLINE HELPER FUNCTIONS (Required - do not import)
# =============================================================================

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema


def setup_mlflow_experiment(model_name: str) -> str:
    """Set up MLflow experiment using /Shared/ path."""
    experiment_name = f"/Shared/health_monitor_ml_{model_name}"
    try:
        experiment = mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment: {experiment_name}")
        return experiment_name
    except Exception as e:
        print(f"⚠ Experiment setup: {e}")
        return experiment_name


def log_training_dataset(spark, catalog: str, schema: str, table_name: str) -> bool:
    """Log training dataset - MUST be inside mlflow.start_run()."""
    full_table_name = f"{catalog}.{schema}.{table_name}"
    try:
        training_df = spark.table(full_table_name)
        dataset = mlflow.data.from_spark(df=training_df, table_name=full_table_name, version="latest")
        mlflow.log_input(dataset, context="training")
        print(f"  ✓ Dataset logged: {full_table_name}")
        return True
    except Exception as e:
        print(f"  ⚠ Dataset logging: {e}")
        return False


def get_run_name(model_name: str, algorithm: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_v1_{timestamp}"


def get_standard_tags(model_name: str, domain: str, model_type: str, algorithm: str, use_case: str, training_table: str) -> dict:
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
    print(f"✓ Loaded {features_df.count()} rows")
    return features_df

# COMMAND ----------

def prepare_training_data(features_df):
    """
    Prepare features for budget forecasting.

    Includes blog-derived features for better cost prediction:
    - Serverless adoption trends (Workflow Advisor Blog)
    - ALL_PURPOSE inefficiency patterns
    - SKU breakdown indicators
    """
    feature_columns = [
        # Core statistics
        "avg_dbu_7d", "avg_dbu_30d", "std_dbu_7d", "std_dbu_30d",
        # Time features
        "dow_sin", "dow_cos", "is_weekend", "is_month_end",
        "day_of_week", "day_of_month",
        # Lag features for trend detection
        "dbu_change_pct_1d", "dbu_change_pct_7d",
        # =============================================================================
        # WORKFLOW ADVISOR BLOG FEATURES (NEW)
        # =============================================================================
        "serverless_adoption_ratio",       # Trend toward serverless
        "all_purpose_inefficiency_ratio",  # Inefficient spending pattern
        "jobs_on_all_purpose_cost",        # Potential migration savings
        "serverless_cost",                 # Serverless component
        "dlt_cost",                         # DLT pipeline costs
        "model_serving_cost",               # ML inference costs
    ]
    target_column = "daily_cost"  # Target: daily cost (not just DBU)

    pandas_df = features_df.select(feature_columns + [target_column]).toPandas()

    # Convert types and handle missing values
    for col in feature_columns + [target_column]:
        pandas_df[col] = pd.to_numeric(pandas_df[col], errors='coerce')
    pandas_df = pandas_df.fillna(0).replace([np.inf, -np.inf], 0)

    X = pandas_df[feature_columns]
    y = pandas_df[target_column]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"✓ Data: {X_train.shape[0]} train, {X_test.shape[0]} test samples")

    return X_train, X_test, y_train, y_test, feature_columns

# COMMAND ----------

def train_model(X_train, y_train, X_test, y_test):
    """Train Gradient Boosting Regressor."""
    print("\nTraining Gradient Boosting Regressor...")
    
    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Calculate metrics
    y_pred = model.predict(X_test)
    metrics = {
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "r2": r2_score(y_test, y_pred),
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    print(f"✓ Model trained - MAE: {metrics['mae']:.4f}, R2: {metrics['r2']:.4f}")
    
    return model, metrics

# COMMAND ----------

def log_model_to_mlflow(model, X_train, metrics, feature_columns, catalog, feature_schema, experiment_name, spark):
    """Log model with MLflow 3.1+ best practices."""
    model_name = "budget_forecaster"
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    run_name = get_run_name(model_name, "gradient_boosting")
    
    mlflow.autolog(disable=True)
    
    with mlflow.start_run(run_name=run_name) as run:
        # 1. Tags
        mlflow.set_tags(get_standard_tags(
            model_name=model_name, domain="cost", model_type="regression",
            algorithm="gradient_boosting", use_case="budget_forecasting",
            training_table=f"{catalog}.{feature_schema}.cost_features"
        ))
        
        # 2. Dataset (inside run context)
        log_training_dataset(spark, catalog, feature_schema, "cost_features")
        
        # 3. Parameters
        mlflow.log_params({
            "n_estimators": 100, "max_depth": 5, "learning_rate": 0.1,
            "feature_count": len(feature_columns)
        })
        
        # 4. Metrics
        mlflow.log_metrics(metrics)
        
        # 5. Signature with BOTH input AND output
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # 6. Log and register model
        mlflow.sklearn.log_model(
            sk_model=model, artifact_path="model", signature=signature,
            input_example=sample_input, registered_model_name=registered_model_name
        )
        
        print(f"✓ Model registered: {registered_model_name}")
        return run.info.run_id, registered_model_name

# COMMAND ----------

def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("BUDGET FORECASTER - TRAINING (MLflow 3.1+)")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    experiment_name = setup_mlflow_experiment("budget_forecaster")
    
    try:
        features_df = load_features(spark, catalog, feature_schema)
        X_train, X_test, y_train, y_test, feature_columns = prepare_training_data(features_df)
        model, metrics = train_model(X_train, y_train, X_test, y_test)
        run_id, model_name = log_model_to_mlflow(
            model, X_train, metrics, feature_columns, catalog, feature_schema, experiment_name, spark
        )
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE")
        print("=" * 60)
        print(f"  Model:       budget_forecaster")
        print(f"  Registered:  {model_name}")
        print(f"  MLflow Run:  {run_id}")
        print("\n  Metrics:")
        for k, v in metrics.items():
            print(f"    - {k}: {v:.4f}" if isinstance(v, float) else f"    - {k}: {v}")
        print("=" * 60)
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}\n{traceback.format_exc()}")
        import json
        exit_summary = json.dumps({"status": "FAILED", "model": "budget_forecaster", "error": str(e)[:500]})
        dbutils.notebook.exit(exit_summary)
        raise  # Re-raise to fail the job
    
    import json
    hyperparams = {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1}
    exit_summary = json.dumps({
            "status": "SUCCESS",
            "model": "budget_forecaster",
            "registered_as": model_name,
            "run_id": run_id,
            "algorithm": "GradientBoostingRegressor",
            "hyperparameters": hyperparams,
            "metrics": {k: round(v, 4) if isinstance(v, float) else v for k, v in metrics.items()}
        })
    dbutils.notebook.exit(exit_summary)

# COMMAND ----------

if __name__ == "__main__":
    main()
