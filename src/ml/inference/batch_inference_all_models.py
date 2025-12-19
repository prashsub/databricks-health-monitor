# Databricks notebook source
"""
Batch Inference - All Models
============================

Runs batch inference for ALL trained ML models and stores predictions
in the ML schema for monitoring and alerting.

Models Scored:
- Cost: anomaly, budget, job_cost, chargeback, commitment
- Security: threat, exfiltration, privilege, user_behavior  
- Performance: query_forecaster, warehouse, regression
- Reliability: failure, duration, sla_breach
- Quality: drift, schema_change, freshness

MLflow 3.1+ Best Practices Applied
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import mlflow
from mlflow import MlflowClient
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

def get_model_configs(catalog: str, feature_schema: str) -> List[Dict]:
    """
    Configuration for all models to score.
    
    Each config specifies:
    - model_name: Name in UC registry
    - feature_table: Source feature table
    - feature_columns: Columns to use for inference
    - output_table: Where to store predictions
    - model_type: anomaly_detection, classification, or regression
    - id_columns: Columns to preserve in output
    """
    base_config = {
        "catalog": catalog,
        "schema": feature_schema
    }
    
    return [
        # =====================================================================
        # COST DOMAIN
        # =====================================================================
        {
            **base_config,
            "model_name": "cost_anomaly_detector",
            "feature_table": "cost_features",
            "feature_columns": ["daily_dbu", "avg_dbu_7d", "avg_dbu_30d", "z_score_7d", "z_score_30d",
                               "dbu_change_pct_1d", "dbu_change_pct_7d", "dow_sin", "dow_cos", 
                               "is_weekend", "is_month_end"],
            "id_columns": ["workspace_id", "sku_name", "usage_date"],
            "output_table": "cost_anomaly_predictions",
            "model_type": "anomaly_detection"
        },
        {
            **base_config,
            "model_name": "budget_forecaster",
            "feature_table": "cost_features",
            "feature_columns": ["avg_dbu_7d", "avg_dbu_30d", "std_dbu_7d", "std_dbu_30d",
                               "dow_sin", "dow_cos", "is_weekend", "is_month_end",
                               "day_of_week", "day_of_month"],
            "id_columns": ["workspace_id", "sku_name", "usage_date"],
            "output_table": "budget_forecast_predictions",
            "model_type": "regression"
        },
        {
            **base_config,
            "model_name": "job_cost_optimizer",
            "feature_table": "cost_features",
            "feature_columns": ["daily_dbu", "avg_dbu_7d", "avg_dbu_30d", "z_score_7d", 
                               "dow_sin", "dow_cos", "is_weekend"],
            "id_columns": ["workspace_id", "sku_name", "usage_date"],
            "output_table": "job_cost_optimizer_predictions",
            "model_type": "regression"
        },
        {
            **base_config,
            "model_name": "chargeback_attribution",
            "feature_table": "cost_features",
            "feature_columns": ["daily_dbu", "avg_dbu_7d", "avg_dbu_30d", "dow_sin", 
                               "dow_cos", "is_weekend"],
            "id_columns": ["workspace_id", "sku_name", "usage_date"],
            "output_table": "chargeback_predictions",
            "model_type": "regression"
        },
        {
            **base_config,
            "model_name": "commitment_recommender",
            "feature_table": "cost_features",
            "feature_columns": ["avg_dbu_7d", "avg_dbu_30d", "std_dbu_7d", "std_dbu_30d",
                               "dow_sin", "dow_cos"],
            "id_columns": ["workspace_id", "sku_name", "usage_date"],
            "output_table": "commitment_recommendations",
            "model_type": "regression"
        },
        
        # =====================================================================
        # SECURITY DOMAIN
        # Actual columns: event_count, tables_accessed, off_hours_events, unique_source_ips,
        #   failed_auth_count, sensitive_data_access, avg_event_count_7d, std_event_count_7d,
        #   avg_tables_accessed_7d, event_count_z_score, off_hours_rate, sensitive_access_rate,
        #   is_weekend, day_of_week
        # =====================================================================
        {
            **base_config,
            "model_name": "security_threat_detector",
            "feature_table": "security_features",
            "feature_columns": ["event_count", "tables_accessed", "off_hours_events", "unique_source_ips",
                               "failed_auth_count", "avg_event_count_7d", "event_count_z_score", "off_hours_rate"],
            "id_columns": ["user_id", "event_date"],
            "output_table": "security_threat_predictions",
            "model_type": "anomaly_detection"
        },
        {
            **base_config,
            "model_name": "exfiltration_detector",
            "feature_table": "security_features",
            "feature_columns": ["event_count", "tables_accessed", "off_hours_events", 
                               "unique_source_ips", "sensitive_data_access"],
            "id_columns": ["user_id", "event_date"],
            "output_table": "exfiltration_predictions",
            "model_type": "anomaly_detection"
        },
        {
            **base_config,
            "model_name": "privilege_escalation_detector",
            "feature_table": "security_features",
            "feature_columns": ["event_count", "tables_accessed", "off_hours_events", 
                               "failed_auth_count", "event_count_z_score"],
            "id_columns": ["user_id", "event_date"],
            "output_table": "privilege_escalation_predictions",
            "model_type": "anomaly_detection"
        },
        {
            **base_config,
            "model_name": "user_behavior_baseline",
            "feature_table": "security_features",
            "feature_columns": ["event_count", "tables_accessed", "off_hours_events", "unique_source_ips",
                               "avg_event_count_7d", "avg_tables_accessed_7d"],
            "id_columns": ["user_id", "event_date"],
            "output_table": "user_behavior_predictions",
            "model_type": "clustering"
        },
        
        # =====================================================================
        # PERFORMANCE DOMAIN
        # =====================================================================
        {
            **base_config,
            "model_name": "query_performance_forecaster",
            "feature_table": "performance_features",
            "feature_columns": ["query_count", "avg_duration_ms", "p50_duration_ms", "p95_duration_ms",
                               "error_rate", "spill_rate", "avg_query_count_7d", "is_weekend"],
            "id_columns": ["warehouse_id", "query_date"],
            "output_table": "query_forecast_predictions",
            "model_type": "regression"
        },
        {
            **base_config,
            "model_name": "warehouse_optimizer",
            "feature_table": "performance_features",
            "feature_columns": ["query_count", "avg_duration_ms", "total_bytes_read", "error_rate",
                               "spill_rate", "avg_query_count_7d", "is_weekend", "day_of_week"],
            "id_columns": ["warehouse_id", "query_date"],
            "output_table": "warehouse_optimizer_predictions",
            "model_type": "regression"
        },
        {
            **base_config,
            "model_name": "performance_regression_detector",
            "feature_table": "performance_features",
            "feature_columns": ["avg_duration_ms", "p50_duration_ms", "p95_duration_ms", "p99_duration_ms",
                               "error_rate", "spill_rate", "avg_query_count_7d", "avg_duration_7d"],
            "id_columns": ["warehouse_id", "query_date"],
            "output_table": "performance_regression_predictions",
            "model_type": "anomaly_detection"
        },
        
        # =====================================================================
        # RELIABILITY DOMAIN
        # Actual columns: job_id, run_date, total_runs, successful_runs, failed_runs,
        #   avg_duration_sec, std_duration_sec, max_duration_sec, min_duration_sec,
        #   success_rate, failure_rate, duration_cv, rolling_failure_rate_30d,
        #   rolling_avg_duration_30d, total_failures_30d, prev_day_success_rate,
        #   prev_day_failed, success_rate_trend, is_weekend, day_of_week
        # =====================================================================
        {
            **base_config,
            "model_name": "job_failure_predictor",
            "feature_table": "reliability_features",
            "feature_columns": ["total_runs", "avg_duration_sec", "success_rate", "total_failures_30d",
                               "duration_cv", "rolling_avg_duration_30d", "is_weekend", "day_of_week"],
            "id_columns": ["job_id", "run_date"],
            "output_table": "failure_predictions",
            "model_type": "classification"
        },
        {
            **base_config,
            "model_name": "job_duration_forecaster",
            "feature_table": "reliability_features",
            "feature_columns": ["total_runs", "avg_duration_sec", "success_rate", "duration_cv",
                               "rolling_avg_duration_30d", "min_duration_sec", "max_duration_sec",
                               "is_weekend", "day_of_week"],
            "id_columns": ["job_id", "run_date"],
            "output_table": "duration_forecast_predictions",
            "model_type": "regression"
        },
        {
            **base_config,
            "model_name": "sla_breach_predictor",
            "feature_table": "reliability_features",
            "feature_columns": ["total_runs", "avg_duration_sec", "success_rate", "total_failures_30d",
                               "duration_cv", "rolling_avg_duration_30d", "max_duration_sec", "is_weekend"],
            "id_columns": ["job_id", "run_date"],
            "output_table": "sla_breach_predictions",
            "model_type": "classification"
        },
        
        # =====================================================================
        # QUALITY DOMAIN
        # =====================================================================
        {
            **base_config,
            "model_name": "data_drift_detector",
            "feature_table": "performance_features",  # Using performance as proxy
            "feature_columns": ["query_count", "avg_duration_ms", "error_rate", "spill_rate",
                               "avg_query_count_7d", "total_bytes_read", "is_weekend"],
            "id_columns": ["warehouse_id", "query_date"],
            "output_table": "data_drift_predictions",
            "model_type": "anomaly_detection"
        },
        {
            **base_config,
            "model_name": "schema_change_predictor",
            "feature_table": "performance_features",
            "feature_columns": ["query_count", "error_rate", "spill_rate", "avg_query_count_7d",
                               "total_bytes_read", "is_weekend", "day_of_week"],
            "id_columns": ["warehouse_id", "query_date"],
            "output_table": "schema_change_predictions",
            "model_type": "classification"
        },
        {
            **base_config,
            "model_name": "data_freshness_predictor",
            "feature_table": "reliability_features",
            "feature_columns": ["total_runs", "avg_duration_sec", "success_rate",
                               "rolling_avg_duration_30d", "max_duration_sec", "is_weekend", "day_of_week"],
            "id_columns": ["job_id", "run_date"],
            "output_table": "freshness_predictions",
            "model_type": "regression"
        },
    ]

# COMMAND ----------

def load_model(catalog: str, schema: str, model_name: str) -> Tuple[any, str, int]:
    """Load model from Unity Catalog."""
    full_model_name = f"{catalog}.{schema}.{model_name}"
    client = MlflowClient()
    
    try:
        versions = client.search_model_versions(f"name='{full_model_name}'")
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            model_uri = f"models:/{full_model_name}/{latest.version}"
            model = mlflow.pyfunc.load_model(model_uri)
            return model, model_uri, int(latest.version)
    except Exception as e:
        print(f"  ⚠ Model load failed: {e}")
    
    return None, None, 0

# COMMAND ----------

def score_model(model, features_df, config: Dict) -> pd.DataFrame:
    """Score features using model."""
    feature_cols = config["feature_columns"]
    id_cols = config["id_columns"]
    model_type = config["model_type"]
    
    # Get available columns
    available_cols = features_df.columns
    actual_feature_cols = [c for c in feature_cols if c in available_cols]
    actual_id_cols = [c for c in id_cols if c in available_cols]
    
    if not actual_feature_cols:
        raise ValueError(f"No feature columns found in {config['feature_table']}")
    
    # Convert to pandas
    pdf = features_df.select(actual_id_cols + actual_feature_cols).toPandas()
    
    # Prepare features
    X = pdf[actual_feature_cols].copy()
    for col in actual_feature_cols:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(0).replace([np.inf, -np.inf], 0)
    
    # Score based on model type
    try:
        sklearn_model = model._model_impl.sklearn_model
        
        if model_type == "anomaly_detection":
            predictions = sklearn_model.predict(X)
            scores = sklearn_model.decision_function(X)
            pdf["prediction"] = (predictions == -1).astype(int)
            pdf["anomaly_score"] = scores
            pdf["is_anomaly"] = (predictions == -1).astype(int)
            
        elif model_type == "classification":
            predictions = sklearn_model.predict(X)
            if hasattr(sklearn_model, 'predict_proba'):
                try:
                    probas = sklearn_model.predict_proba(X)
                    pdf["probability"] = probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]
                except:
                    pdf["probability"] = predictions.astype(float)
            else:
                pdf["probability"] = predictions.astype(float)
            pdf["prediction"] = predictions.astype(int)
            
        elif model_type == "regression":
            predictions = sklearn_model.predict(X)
            pdf["prediction"] = predictions
            
        elif model_type == "clustering":
            predictions = sklearn_model.predict(X)
            pdf["cluster"] = predictions
            pdf["prediction"] = predictions
            
    except Exception as e:
        # Fallback to pyfunc predict
        predictions = model.predict(X)
        pdf["prediction"] = predictions
    
    pdf["scored_at"] = datetime.now()
    pdf["model_name"] = config["model_name"]
    
    return pdf

# COMMAND ----------

def save_predictions(spark: SparkSession, predictions_df: pd.DataFrame, 
                     catalog: str, schema: str, table_name: str, model_version: int):
    """Save predictions to Delta table."""
    spark_df = spark.createDataFrame(predictions_df)
    spark_df = spark_df.withColumn("model_version", F.lit(model_version))
    
    output_table = f"{catalog}.{schema}.{table_name}"
    
    # Create or append
    spark_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(output_table)
    
    return output_table

# COMMAND ----------

def run_inference_for_model(spark: SparkSession, config: Dict) -> Dict:
    """Run inference for a single model."""
    model_name = config["model_name"]
    catalog = config["catalog"]
    schema = config["schema"]
    
    result = {
        "model_name": model_name,
        "status": "FAILED",
        "records_scored": 0,
        "error": None
    }
    
    try:
        # Load model
        model, model_uri, version = load_model(catalog, schema, model_name)
        if model is None:
            result["error"] = "Model not found"
            return result
        
        # Load features
        feature_table = f"{catalog}.{schema}.{config['feature_table']}"
        features_df = spark.table(feature_table)
        
        # Score
        predictions_df = score_model(model, features_df, config)
        
        # Save
        output_table = save_predictions(
            spark, predictions_df, catalog, schema, 
            config["output_table"], version
        )
        
        result["status"] = "SUCCESS"
        result["records_scored"] = len(predictions_df)
        result["output_table"] = output_table
        result["model_version"] = version
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

# COMMAND ----------

def main():
    """Main entry point for batch inference."""
    print("\n" + "=" * 80)
    print("BATCH INFERENCE - ALL MODELS")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    # Get all model configs
    model_configs = get_model_configs(catalog, feature_schema)
    
    print(f"\nScoring {len(model_configs)} models...")
    print(f"Feature Schema: {catalog}.{feature_schema}")
    
    results = []
    success_count = 0
    
    for config in model_configs:
        model_name = config["model_name"]
        print(f"\n{'='*60}")
        print(f"Model: {model_name}")
        print(f"{'='*60}")
        
        result = run_inference_for_model(spark, config)
        results.append(result)
        
        if result["status"] == "SUCCESS":
            success_count += 1
            print(f"  ✓ Scored {result['records_scored']} records → {result['output_table']}")
        else:
            print(f"  ❌ Failed: {result['error']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("BATCH INFERENCE SUMMARY")
    print("=" * 80)
    print(f"Total Models: {len(model_configs)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(model_configs) - success_count}")
    
    # Print failed models
    failed = [r for r in results if r["status"] != "SUCCESS"]
    if failed:
        print("\nFailed Models:")
        for r in failed:
            print(f"  - {r['model_name']}: {r['error']}")
    
    if success_count == 0:
        dbutils.notebook.exit("FAILED: No models scored successfully")
    elif success_count < len(model_configs):
        dbutils.notebook.exit(f"PARTIAL: {success_count}/{len(model_configs)} models scored")
    else:
        dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()

