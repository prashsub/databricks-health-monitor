# Databricks notebook source
"""
Batch Inference - All Models with Feature Engineering
=====================================================

Runs batch inference for ALL trained ML models using Feature Engineering's
fe.score_batch() for automatic feature lookup.

Key Benefits of fe.score_batch():
- Automatic feature lookup from feature tables
- Scoring DataFrame only needs lookup keys (not all features)
- Training/inference consistency guaranteed
- Full lineage tracking in Unity Catalog

Models by Domain (25 total):
- COST (6): anomaly, budget, job_cost, chargeback, commitment, tag_recommender
- SECURITY (4): threat, exfiltration, privilege, user_behavior  
- PERFORMANCE (7): query_forecaster, warehouse, regression, cache_hit, 
                   cluster_capacity, dbr_migration, query_optimization
- RELIABILITY (5): failure, duration, sla_breach, pipeline_health, retry_success
- QUALITY (3): drift, schema_change, freshness

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/score-batch
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
import json
import time

# Feature Engineering for automatic feature lookup
from databricks.feature_engineering import FeatureEngineeringClient

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
# MODEL CONFIGURATION - ALL MODELS WITH FEATURE ENGINEERING
# =============================================================================

def get_model_configs(catalog: str, feature_schema: str) -> List[Dict]:
    """
    Configuration for ALL models to score using Feature Engineering.
    
    Each config specifies:
    - model_name: Name in UC registry
    - feature_table: Source feature table for lookup
    - lookup_keys: Primary key columns for feature lookup
    - output_table: Where to store predictions
    - model_type: For post-processing predictions
    - domain: Agent domain
    
    NOTE: feature_columns are NOT needed when using fe.score_batch()!
    The model metadata contains the feature lookup info.
    """
    base_config = {
        "catalog": catalog,
        "schema": feature_schema
    }
    
    return [
        # =====================================================================
        # COST DOMAIN (6 models)
        # Feature table: cost_features
        # Lookup keys: ["workspace_id", "usage_date"]
        # =====================================================================
        {
            **base_config,
            "model_name": "cost_anomaly_detector",
            "feature_table": "cost_features",
            "lookup_keys": ["workspace_id", "usage_date"],
            "output_table": "cost_anomaly_predictions",
            "model_type": "anomaly_detection",
            "domain": "COST"
        },
        {
            **base_config,
            "model_name": "budget_forecaster",
            "feature_table": "cost_features",
            "lookup_keys": ["workspace_id", "usage_date"],
            "output_table": "budget_forecast_predictions",
            "model_type": "regression",
            "domain": "COST"
        },
        
        # =====================================================================
        # SECURITY DOMAIN (4 models)
        # Feature table: security_features
        # Lookup keys: ["user_id", "event_date"]
        # =====================================================================
        {
            **base_config,
            "model_name": "security_threat_detector",
            "feature_table": "security_features",
            "lookup_keys": ["user_id", "event_date"],
            "output_table": "security_threat_predictions",
            "model_type": "anomaly_detection",
            "domain": "SECURITY"
        },
        
        # =====================================================================
        # PERFORMANCE DOMAIN (7 models)
        # Feature table: performance_features
        # Lookup keys: ["warehouse_id", "query_date"]
        # =====================================================================
        {
            **base_config,
            "model_name": "query_performance_forecaster",
            "feature_table": "performance_features",
            "lookup_keys": ["warehouse_id", "query_date"],
            "output_table": "query_forecast_predictions",
            "model_type": "regression",
            "domain": "PERFORMANCE"
        },
        
        # =====================================================================
        # RELIABILITY DOMAIN (5 models)
        # Feature table: reliability_features
        # Lookup keys: ["job_id", "run_date"]
        # =====================================================================
        {
            **base_config,
            "model_name": "job_failure_predictor",
            "feature_table": "reliability_features",
            "lookup_keys": ["job_id", "run_date"],
            "output_table": "failure_predictions",
            "model_type": "classification",
            "domain": "RELIABILITY"
        },
        
        # =====================================================================
        # QUALITY DOMAIN (3 models)
        # Feature table: quality_features
        # Lookup keys: ["catalog_name", "snapshot_date"]
        # =====================================================================
        {
            **base_config,
            "model_name": "data_drift_detector",
            "feature_table": "quality_features",
            "lookup_keys": ["catalog_name", "snapshot_date"],
            "output_table": "data_drift_predictions",
            "model_type": "anomaly_detection",
            "domain": "QUALITY"
        },
        {
            **base_config,
            "model_name": "tag_recommender",
            "feature_table": "quality_features",
            "lookup_keys": ["catalog_name", "snapshot_date"],
            "output_table": "tag_recommendations",
            "model_type": "classification",
            "domain": "QUALITY"
        },
    ]

# COMMAND ----------

def check_model_exists(client: MlflowClient, catalog: str, schema: str, model_name: str) -> Tuple[bool, str, int]:
    """
    Check if model exists in Unity Catalog registry.
    
    Returns: (exists, model_uri, version)
    """
    full_model_name = f"{catalog}.{schema}.{model_name}"
    
    try:
        versions = client.search_model_versions(f"name='{full_model_name}'")
        if not versions:
            return False, None, 0
        
        latest = max(versions, key=lambda v: int(v.version))
        model_uri = f"models:/{full_model_name}/{latest.version}"
        return True, model_uri, int(latest.version)
        
    except Exception as e:
        print(f"    ⚠ Error checking model: {e}")
        return False, None, 0

# COMMAND ----------

def create_scoring_dataframe(spark: SparkSession, catalog: str, schema: str, 
                             feature_table: str, lookup_keys: List[str]) -> Tuple[any, int]:
    """
    Create scoring DataFrame with ONLY lookup keys.
    
    When using fe.score_batch(), the DataFrame only needs the lookup keys
    (primary key columns). Features are automatically retrieved from
    the feature table based on model metadata.
    """
    full_table = f"{catalog}.{schema}.{feature_table}"
    
    try:
        # Get recent data for scoring (last 30 days by default)
        date_col = lookup_keys[-1] if any('date' in k.lower() for k in lookup_keys) else None
        
        df = spark.table(full_table)
        
        # Filter to recent data if date column exists
        if date_col and date_col in df.columns:
            df = df.filter(F.col(date_col) >= F.date_sub(F.current_date(), 30))
        
        # Select ONLY lookup keys - features are auto-retrieved by fe.score_batch()
        scoring_df = df.select(*lookup_keys).distinct()
        
        # Sample if too large
        MAX_SAMPLES = 100_000
        count = scoring_df.count()
        if count > MAX_SAMPLES:
            scoring_df = scoring_df.sample(fraction=MAX_SAMPLES/count, seed=42)
            count = MAX_SAMPLES
        
        return scoring_df, count
        
    except Exception as e:
        print(f"    ⚠ Error creating scoring DataFrame: {e}")
        return None, 0

# COMMAND ----------

def score_with_feature_engineering(fe: FeatureEngineeringClient, 
                                   spark: SparkSession,
                                   scoring_df,
                                   model_uri: str,
                                   model_type: str) -> Tuple[any, str]:
    """
    Score using Feature Engineering's fe.score_batch().
    
    This method:
    1. Reads model metadata to find required features
    2. Automatically joins features from feature tables
    3. Runs the model
    4. Returns predictions with original columns
    
    The scoring_df only needs lookup keys - features are auto-retrieved!
    """
    try:
        # Score with automatic feature lookup
        # result_type depends on model type
        if model_type in ["regression"]:
            result_type = "double"
        elif model_type in ["classification", "anomaly_detection"]:
            result_type = "double"  # Scores/probabilities
        else:
            result_type = "double"
        
        predictions = fe.score_batch(
            model_uri=model_uri,
            df=scoring_df,
            result_type=result_type
        )
        
        return predictions, None
        
    except Exception as e:
        error_msg = str(e)
        
        # Handle models not logged with fe.log_model (fallback to manual scoring)
        if "feature" in error_msg.lower() or "lookup" in error_msg.lower():
            print(f"    ⚠ Model not logged with Feature Engineering, using fallback")
            return None, "MODEL_NOT_FE_ENABLED"
        
        return None, f"Scoring error: {error_msg}"

# COMMAND ----------

def score_with_fallback(spark: SparkSession, 
                        scoring_df,
                        catalog: str, 
                        schema: str,
                        feature_table: str,
                        model_uri: str,
                        model_type: str) -> Tuple[any, str]:
    """
    Fallback scoring for models not logged with Feature Engineering.
    
    Manually loads features and scores.
    """
    try:
        # Load full feature table
        full_table = f"{catalog}.{schema}.{feature_table}"
        features_df = spark.table(full_table)
        
        # Convert to pandas
        pdf = features_df.limit(100_000).toPandas()
        
        # Get feature columns (exclude non-feature columns)
        exclude_cols = ['feature_timestamp', 'workspace_id', 'usage_date', 
                       'user_id', 'event_date', 'warehouse_id', 'query_date',
                       'job_id', 'run_date', 'catalog_name', 'snapshot_date']
        feature_cols = [c for c in pdf.columns if c not in exclude_cols]
        
        # Prepare features
        X = pdf[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        # Load model and predict
        model = mlflow.sklearn.load_model(model_uri)
        
        if model_type == "anomaly_detection":
            predictions = model.predict(X)
            scores = model.decision_function(X)
            pdf["prediction"] = (predictions == -1).astype(int)
            pdf["anomaly_score"] = scores
        elif model_type == "classification":
            predictions = model.predict(X)
            pdf["prediction"] = predictions
            if hasattr(model, 'predict_proba'):
                probas = model.predict_proba(X)
                pdf["probability"] = probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]
        else:
            predictions = model.predict(X)
            pdf["prediction"] = predictions
        
        pdf["scored_at"] = datetime.now()
        result_df = spark.createDataFrame(pdf)
        
        return result_df, None
        
    except Exception as e:
        return None, f"Fallback scoring error: {str(e)}"

# COMMAND ----------

def save_predictions(spark: SparkSession, predictions_df, 
                     catalog: str, schema: str, table_name: str, 
                     model_version: int, model_name: str) -> Tuple[str, int, str]:
    """Save predictions to Delta table."""
    output_table = f"{catalog}.{schema}.{table_name}"
    
    try:
        # Add metadata columns
        result_df = (predictions_df
                    .withColumn("model_version", F.lit(model_version))
                    .withColumn("model_name", F.lit(model_name))
                    .withColumn("scored_at", F.current_timestamp()))
        
        # Save
        result_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(output_table)
        
        count = predictions_df.count()
        return output_table, count, None
        
    except Exception as e:
        return output_table, 0, f"Save error: {str(e)}"

# COMMAND ----------

def run_inference_for_model(spark: SparkSession, fe: FeatureEngineeringClient,
                            client: MlflowClient, config: Dict) -> Dict:
    """Run inference for a single model using Feature Engineering."""
    model_name = config["model_name"]
    catalog = config["catalog"]
    schema = config["schema"]
    domain = config.get("domain", "UNKNOWN")
    
    start_time = time.time()
    
    result = {
        "model_name": model_name,
        "domain": domain,
        "status": "FAILED",
        "records_scored": 0,
        "model_version": 0,
        "output_table": None,
        "error": None,
        "error_stage": None,
        "used_feature_engineering": False,
        "duration_sec": 0
    }
    
    print(f"\n  [{domain}] {model_name}")
    print(f"  {'-' * 50}")
    
    # Stage 1: Check model exists
    print(f"    1. Checking model in UC registry...")
    exists, model_uri, version = check_model_exists(client, catalog, schema, model_name)
    if not exists:
        result["error"] = f"Model not found: {catalog}.{schema}.{model_name}"
        result["error_stage"] = "MODEL_CHECK"
        print(f"    ❌ {result['error']}")
        result["duration_sec"] = round(time.time() - start_time, 2)
        return result
    print(f"    ✓ Found model v{version}")
    result["model_version"] = version
    
    # Stage 2: Create scoring DataFrame (only lookup keys needed!)
    print(f"    2. Creating scoring DataFrame with lookup keys: {config['lookup_keys']}")
    scoring_df, count = create_scoring_dataframe(
        spark, catalog, schema, 
        config['feature_table'], 
        config['lookup_keys']
    )
    if scoring_df is None or count == 0:
        result["error"] = f"No data to score from {config['feature_table']}"
        result["error_stage"] = "SCORING_DF"
        print(f"    ❌ {result['error']}")
        result["duration_sec"] = round(time.time() - start_time, 2)
        return result
    print(f"    ✓ Scoring DataFrame: {count:,} rows (only lookup keys)")
    
    # Stage 3: Score with Feature Engineering
    print(f"    3. Scoring with fe.score_batch() (automatic feature lookup)...")
    predictions, error = score_with_feature_engineering(
        fe, spark, scoring_df, model_uri, config['model_type']
    )
    
    if error == "MODEL_NOT_FE_ENABLED":
        # Fallback for models not logged with Feature Engineering
        print(f"    ⚠ Falling back to manual feature loading...")
        predictions, error = score_with_fallback(
            spark, scoring_df, catalog, schema,
            config['feature_table'], model_uri, config['model_type']
        )
        result["used_feature_engineering"] = False
    else:
        result["used_feature_engineering"] = True
    
    if error:
        result["error"] = error
        result["error_stage"] = "SCORING"
        print(f"    ❌ {error}")
        result["duration_sec"] = round(time.time() - start_time, 2)
        return result
    
    pred_count = predictions.count()
    fe_status = "✓ (Feature Engineering)" if result["used_feature_engineering"] else "⚠ (Fallback)"
    print(f"    {fe_status} Scored {pred_count:,} records")
    
    # Stage 4: Save predictions
    print(f"    4. Saving predictions to {config['output_table']}...")
    output_table, rows_saved, error = save_predictions(
        spark, predictions, catalog, schema, 
        config["output_table"], version, model_name
    )
    if error:
        result["error"] = error
        result["error_stage"] = "SAVE"
        print(f"    ❌ {error}")
        result["duration_sec"] = round(time.time() - start_time, 2)
        return result
    
    result["status"] = "SUCCESS"
    result["records_scored"] = rows_saved
    result["output_table"] = output_table
    result["duration_sec"] = round(time.time() - start_time, 2)
    
    print(f"    ✓ Saved {rows_saved:,} predictions to {output_table}")
    print(f"    ✓ Completed in {result['duration_sec']:.1f}s")
    
    return result

# COMMAND ----------

def main():
    """Main entry point for batch inference with Feature Engineering."""
    print("\n" + "=" * 80)
    print("BATCH INFERENCE WITH FEATURE ENGINEERING")
    print("Automatic Feature Lookup via fe.score_batch()")
    print("=" * 80)
    
    catalog, gold_schema, feature_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()
    
    # Initialize Feature Engineering client
    fe = FeatureEngineeringClient()
    client = MlflowClient()
    
    print(f"\nConfiguration:")
    print(f"  Catalog:        {catalog}")
    print(f"  Gold Schema:    {gold_schema}")
    print(f"  Feature Schema: {feature_schema}")
    print(f"  Feature Engineering: ENABLED")
    
    # Get model configs
    model_configs = get_model_configs(catalog, feature_schema)
    
    print(f"\nModels to Score: {len(model_configs)}")
    print(f"Feature Lookup: Automatic via model metadata")
    
    print("\n" + "=" * 80)
    print("INFERENCE EXECUTION")
    print("=" * 80)
    
    results = []
    start_time = time.time()
    
    for config in model_configs:
        result = run_inference_for_model(spark, fe, client, config)
        results.append(result)
    
    total_time = round(time.time() - start_time, 2)
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("BATCH INFERENCE SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] != "SUCCESS"]
    fe_enabled = [r for r in successful if r.get("used_feature_engineering", False)]
    total_records = sum(r["records_scored"] for r in successful)
    
    print("\n[OVERALL RESULTS]")
    print(f"  Total Models:           {len(results)}")
    print(f"  Successful:             {len(successful)}")
    print(f"  Failed:                 {len(failed)}")
    print(f"  Feature Engineering:    {len(fe_enabled)}/{len(successful)} used fe.score_batch()")
    print(f"  Total Records:          {total_records:,}")
    print(f"  Total Duration:         {total_time:.1f}s")
    
    # Successful models
    if successful:
        print(f"\n[SUCCESSFUL MODELS] ({len(successful)} total)")
        print("-" * 80)
        for r in sorted(successful, key=lambda x: (x["domain"], x["model_name"])):
            fe_mark = "FE" if r.get("used_feature_engineering") else "FB"
            print(f"  [{fe_mark}] {r['domain']:<11} {r['model_name']:<35} v{r['model_version']:<3} {r['records_scored']:>8,} records")
        print("-" * 80)
        print("  FE = Feature Engineering (automatic lookup)")
        print("  FB = Fallback (manual feature loading)")
    
    # Failed models
    if failed:
        print(f"\n[FAILED MODELS] ({len(failed)} total)")
        print("-" * 80)
        for r in sorted(failed, key=lambda x: (x["domain"], x["model_name"])):
            stage = r.get("error_stage", "UNKNOWN")
            error = r.get("error", "Unknown")[:60]
            print(f"  [FAIL] {r['domain']:<11} {r['model_name']:<35}")
            print(f"         Stage: {stage}, Error: {error}")
        print("-" * 80)
    
    # Build exit message
    status = "SUCCESS" if len(failed) == 0 else "PARTIAL" if successful else "FAILED"
    
    json_data = {
        "status": status,
        "total_models": len(results),
        "successful_models": len(successful),
        "failed_models": len(failed),
        "feature_engineering_enabled": len(fe_enabled),
        "total_records_scored": total_records,
        "total_duration_sec": total_time
    }
    
    print(f"\n{'='*80}")
    print(f"STATUS: {status}")
    print(f"{'='*80}")
    
    dbutils.notebook.exit(json.dumps(json_data))

# COMMAND ----------

if __name__ == "__main__":
    main()
