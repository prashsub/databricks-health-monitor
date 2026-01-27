# Databricks notebook source
"""
Batch Inference - Feature Store Models (23 models)
==================================================

Uses the official Databricks pattern for batch inference with fe.score_batch():
1. Create DataFrame with lookup keys only
2. Call fe.score_batch() - it handles feature lookup automatically  
3. Save predictions

Models Scored (23 via Feature Store):
- Cost (5): anomaly, budget, job_cost, chargeback, commitment
- Security (4): threat, exfiltration, privilege, user_behavior
- Performance (7): query, warehouse, cluster_capacity, regression, dbr_risk, cache_hit, query_optimization
- Reliability (5): failure, duration, sla_breach, retry_success, pipeline_health
- Quality (2): drift, freshness

NOT Scored Here:
- tag_recommender: Uses TF-IDF (runtime features) - handled by score_tag_recommender.py
- schema_change_predictor: Removed (single-class data)

Reference: https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store
"""

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import mlflow
from mlflow import MlflowClient
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import time

from databricks.feature_engineering import FeatureEngineeringClient

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

def get_parameters():
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, gold_schema, feature_schema

# COMMAND ----------

# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================

def get_feature_table_keys(spark, full_table_name: str) -> List[str]:
    """
    Dynamically get primary keys from feature table by querying its schema.
    
    Per Databricks docs: For fe.score_batch(), pass only the lookup keys.
    We identify lookup keys as the columns that were used as primary keys
    during fe.create_table().
    
    Simple approach: Read the first row and use common key patterns.
    """
    try:
        # Get actual columns from the table
        df = spark.table(full_table_name)
        columns = df.columns
        
        # Common primary key patterns by domain (order matters - first match wins)
        key_patterns = [
            # Cost domain
            ("cost_features", ["workspace_id", "usage_date"]),
            # Security domain - actual columns are user_id, event_date
            ("security_features", ["user_id", "event_date"]),
            # Performance domain
            ("performance_features", ["warehouse_id", "query_date"]),
            # Reliability domain - job_id, run_date (used by all reliability models)
            ("reliability_features", ["job_id", "run_date"]),
            # Quality domain - actual columns are catalog_name, snapshot_date
            ("quality_features", ["catalog_name", "snapshot_date"]),
        ]
        
        # Match table name to pattern
        for pattern_table, keys in key_patterns:
            if pattern_table in full_table_name.lower():
                # Verify keys exist in table
                valid_keys = [k for k in keys if k in columns]
                if valid_keys:
                    return valid_keys
        
        # Fallback: Look for common key column names
        common_keys = []
        for col in columns:
            col_lower = col.lower()
            if col_lower.endswith('_id') or col_lower.endswith('_date') or col_lower == 'date':
                common_keys.append(col)
        
        if common_keys:
            return common_keys[:2]  # Max 2 keys
        
        # Last resort: first column
        return [columns[0]]
        
    except Exception as e:
        print(f"    ⚠ Could not determine keys: {e}")
        return ["id"]

def get_model_configs(catalog: str, feature_schema: str) -> List[Dict]:
    """Simple model configurations."""
    return [
        # COST DOMAIN
        {"model_name": "cost_anomaly_detector", "feature_table": "cost_features", "output_table": "cost_anomaly_predictions", "domain": "COST"},
        {"model_name": "budget_forecaster", "feature_table": "cost_features", "output_table": "budget_forecast_predictions", "domain": "COST"},
        {"model_name": "job_cost_optimizer", "feature_table": "cost_features", "output_table": "job_cost_optimizer_predictions", "domain": "COST"},
        {"model_name": "chargeback_attribution", "feature_table": "cost_features", "output_table": "chargeback_predictions", "domain": "COST"},
        {"model_name": "commitment_recommender", "feature_table": "cost_features", "output_table": "commitment_recommendations", "domain": "COST"},
        # NOTE: tag_recommender uses TF-IDF (runtime NLP features), not feature store.
        # Handled by separate task: score_tag_recommender.py
        # See: src/ml/inference/score_tag_recommender.py
        {"model_name": "tag_recommender", "feature_table": "cost_features", "output_table": "tag_recommendations", "domain": "COST", "skip_fe": True},
        
        # SECURITY DOMAIN
        {"model_name": "security_threat_detector", "feature_table": "security_features", "output_table": "security_threat_predictions", "domain": "SECURITY"},
        {"model_name": "exfiltration_detector", "feature_table": "security_features", "output_table": "exfiltration_predictions", "domain": "SECURITY"},
        {"model_name": "privilege_escalation_detector", "feature_table": "security_features", "output_table": "privilege_escalation_predictions", "domain": "SECURITY"},
        {"model_name": "user_behavior_baseline", "feature_table": "security_features", "output_table": "user_behavior_predictions", "domain": "SECURITY"},
        
        # PERFORMANCE DOMAIN
        {"model_name": "query_performance_forecaster", "feature_table": "performance_features", "output_table": "query_performance_predictions", "domain": "PERFORMANCE"},
        {"model_name": "warehouse_optimizer", "feature_table": "performance_features", "output_table": "warehouse_optimizer_predictions", "domain": "PERFORMANCE"},
        {"model_name": "cluster_capacity_planner", "feature_table": "performance_features", "output_table": "cluster_capacity_predictions", "domain": "PERFORMANCE"},
        {"model_name": "performance_regression_detector", "feature_table": "performance_features", "output_table": "performance_regression_predictions", "domain": "PERFORMANCE"},
        {"model_name": "dbr_migration_risk_scorer", "feature_table": "reliability_features", "output_table": "dbr_migration_predictions", "domain": "PERFORMANCE"},
        {"model_name": "cache_hit_predictor", "feature_table": "performance_features", "output_table": "cache_hit_predictions", "domain": "PERFORMANCE"},
        {"model_name": "query_optimization_recommender", "feature_table": "performance_features", "output_table": "query_optimization_predictions", "domain": "PERFORMANCE"},
        
        # RELIABILITY DOMAIN - All use reliability_features (job_id, run_date as keys)
        {"model_name": "job_failure_predictor", "feature_table": "reliability_features", "output_table": "job_failure_predictions", "domain": "RELIABILITY"},
        {"model_name": "job_duration_forecaster", "feature_table": "reliability_features", "output_table": "duration_predictions", "domain": "RELIABILITY"},
        {"model_name": "sla_breach_predictor", "feature_table": "reliability_features", "output_table": "sla_breach_predictions", "domain": "RELIABILITY"},
        {"model_name": "retry_success_predictor", "feature_table": "reliability_features", "output_table": "retry_success_predictions", "domain": "RELIABILITY"},
        {"model_name": "pipeline_health_scorer", "feature_table": "reliability_features", "output_table": "pipeline_health_predictions", "domain": "RELIABILITY"},
        
        # QUALITY DOMAIN
        # All quality models use quality_features (catalog_name, snapshot_date as keys)
        # NOTE: schema_change_predictor REMOVED - system.information_schema doesn't track schema history,
        # so schema_changes_7d is always 0 (single-class data, cannot train classifier)
        {"model_name": "data_drift_detector", "feature_table": "quality_features", "output_table": "data_drift_predictions", "domain": "QUALITY"},
        {"model_name": "data_freshness_predictor", "feature_table": "quality_features", "output_table": "freshness_predictions", "domain": "QUALITY"},
    ]

# COMMAND ----------

# =============================================================================
# PREDICTION TABLE METADATA
# =============================================================================
# Use centralized metadata from utility module for rich Genie/LLM-friendly descriptions
# Fallback to basic metadata if utility import fails (Asset Bundle compatibility)

try:
    from src.ml.utils.prediction_metadata import PREDICTION_TABLE_METADATA, apply_table_metadata as apply_prediction_metadata
    _METADATA_SOURCE = "utility_module"
    print("✓ Loaded comprehensive metadata from src.ml.utils.prediction_metadata")
except ImportError:
    _METADATA_SOURCE = "inline_fallback"
    print("⚠ Using inline fallback metadata (prediction_metadata module not found)")
    
    # Inline fallback metadata (minimal for backward compatibility)
    PREDICTION_TABLE_METADATA = {
        # COST DOMAIN
        "cost_anomaly_predictions": {
            "table_comment": "ML predictions from cost_anomaly_detector. Identifies unusual cost patterns using Isolation Forest. Prediction -1=anomaly, 1=normal. Source: cost_features | Model: Isolation Forest | Domain: Cost",
            "columns": {
                "workspace_id": {"business_description": "Workspace identifier for cost attribution.", "interpretation": "Join with dim_workspace for details."},
                "usage_date": {"business_description": "Date of the cost observation being scored.", "interpretation": "Use for time-series analysis."},
                "prediction": {"business_description": "Anomaly indicator.", "interpretation": "-1=anomaly detected, 1=normal cost pattern."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always cost_anomaly_detector."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "budget_forecast_predictions": {
            "table_comment": "ML predictions from budget_forecaster. Forecasts expected costs using gradient boosting. Source: cost_features | Model: GradientBoostingRegressor | Domain: Cost",
            "columns": {
                "workspace_id": {"business_description": "Workspace identifier for budget allocation.", "interpretation": "Aggregate by workspace for planning."},
                "usage_date": {"business_description": "Date for which budget is being forecasted.", "interpretation": "Compare with actual costs."},
                "prediction": {"business_description": "Predicted cost value in USD.", "interpretation": "Use as baseline for variance analysis."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always budget_forecaster."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "job_cost_optimizer_predictions": {
            "table_comment": "ML predictions from job_cost_optimizer. Identifies jobs with cost optimization opportunities. Higher score=more savings potential. Source: cost_features | Model: GradientBoostingRegressor | Domain: Cost",
            "columns": {
                "workspace_id": {"business_description": "Workspace containing jobs to optimize.", "interpretation": "Prioritize high-score workspaces."},
                "usage_date": {"business_description": "Date of cost data used for analysis.", "interpretation": "Use recent dates."},
                "prediction": {"business_description": "Optimization potential score (0-1).", "interpretation": ">0.7=high priority, 0.4-0.7=medium, <0.4=optimized."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always job_cost_optimizer."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "chargeback_predictions": {
            "table_comment": "ML predictions from chargeback_attribution. Attributes costs to business units. Source: cost_features | Model: GradientBoostingRegressor | Domain: Cost",
            "columns": {
                "workspace_id": {"business_description": "Workspace for cost attribution.", "interpretation": "Map to cost center."},
                "usage_date": {"business_description": "Date of the cost being attributed.", "interpretation": "Aggregate by month for billing."},
                "prediction": {"business_description": "Attributed cost amount in USD.", "interpretation": "Use directly in billing reports."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always chargeback_attribution."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "commitment_recommendations": {
            "table_comment": "ML predictions from commitment_recommender. Recommends capacity commitment levels (1=high serverless adoption). Source: cost_features | Model: XGBClassifier | Domain: Cost",
            "columns": {
                "workspace_id": {"business_description": "Workspace for commitment recommendation.", "interpretation": "Filter prediction=1 for migration candidates."},
                "usage_date": {"business_description": "Date of usage pattern analyzed.", "interpretation": "Use recent dates."},
                "prediction": {"business_description": "Binary recommendation.", "interpretation": "1=recommend serverless, 0=keep current."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always commitment_recommender."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        # SECURITY DOMAIN
        "security_threat_predictions": {
            "table_comment": "ML predictions from security_threat_detector. Identifies potential security threats. Prediction -1=threat, 1=normal. Source: security_features | Model: Isolation Forest | Domain: Security",
            "columns": {
                "user_id": {"business_description": "User identifier being monitored for threats.", "interpretation": "Investigate -1 predictions immediately."},
                "event_date": {"business_description": "Date of security activity being analyzed.", "interpretation": "Track threat patterns over time."},
                "prediction": {"business_description": "Threat indicator.", "interpretation": "-1=potential threat, 1=normal activity."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always security_threat_detector."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "exfiltration_predictions": {
            "table_comment": "ML predictions from exfiltration_detector. Identifies data exfiltration patterns. Prediction -1=risk, 1=normal. Source: security_features | Model: Isolation Forest | Domain: Security",
            "columns": {
                "user_id": {"business_description": "User identifier being monitored for exfiltration.", "interpretation": "HIGH PRIORITY: Investigate -1 immediately."},
                "event_date": {"business_description": "Date of activity being analyzed.", "interpretation": "Check data export volumes."},
                "prediction": {"business_description": "Exfiltration risk indicator.", "interpretation": "-1=potential risk, 1=normal activity."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always exfiltration_detector."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "privilege_escalation_predictions": {
            "table_comment": "ML predictions from privilege_escalation_detector. Identifies abnormal privilege usage. Prediction -1=escalation, 1=normal. Source: security_features | Model: Isolation Forest | Domain: Security",
            "columns": {
                "user_id": {"business_description": "User identifier being monitored for privilege escalation.", "interpretation": "Verify user authorization."},
                "event_date": {"business_description": "Date of privilege activity being analyzed.", "interpretation": "Correlate with org changes."},
                "prediction": {"business_description": "Escalation indicator.", "interpretation": "-1=potential escalation, 1=normal usage."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always privilege_escalation_detector."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "user_behavior_predictions": {
            "table_comment": "ML predictions from user_behavior_baseline. Establishes behavior baselines and detects deviations. Prediction -1=anomalous, 1=baseline. Source: security_features | Model: Isolation Forest | Domain: Security",
            "columns": {
                "user_id": {"business_description": "User identifier for behavior baseline analysis.", "interpretation": "May indicate compromised account."},
                "event_date": {"business_description": "Date of user activity being compared against baseline.", "interpretation": "Compare against history."},
                "prediction": {"business_description": "Behavior indicator.", "interpretation": "-1=anomalous, 1=within baseline."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always user_behavior_baseline."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        # PERFORMANCE DOMAIN
        "query_performance_predictions": {
            "table_comment": "ML predictions from query_performance_forecaster. Forecasts query execution times. Source: performance_features | Model: GradientBoostingRegressor | Domain: Performance",
            "columns": {
                "warehouse_id": {"business_description": "SQL Warehouse identifier for performance analysis.", "interpretation": "Use for per-warehouse SLA tracking."},
                "query_date": {"business_description": "Date for which performance is forecasted.", "interpretation": "Compare forecast to actual."},
                "prediction": {"business_description": "Predicted query execution time in seconds.", "interpretation": "Use as SLA baseline."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always query_performance_forecaster."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        "warehouse_optimizer_predictions": {
            "table_comment": "ML predictions from warehouse_optimizer. Recommends warehouse sizing optimizations. Source: performance_features | Model: GradientBoostingRegressor | Domain: Performance",
            "columns": {
                "warehouse_id": {"business_description": "SQL Warehouse for optimization recommendation.", "interpretation": "Join with dim_warehouse for config."},
                "query_date": {"business_description": "Date of performance data used for analysis.", "interpretation": "Use recent dates."},
                "prediction": {"business_description": "Optimization score.", "interpretation": ">0.7=needs sizing review, <0.4=well-optimized."},
                "model_name": {"business_description": "ML model that generated this prediction.", "interpretation": "Always warehouse_optimizer."},
                "scored_at": {"business_description": "Timestamp when the prediction was generated.", "interpretation": "Check freshness."}
            }
        },
        # Additional fallback entries (minimal) - full metadata in utility module
        "cluster_capacity_predictions": {"table_comment": "ML predictions from cluster_capacity_planner. Source: performance_features | Domain: Performance", "columns": {}},
        "performance_regression_predictions": {"table_comment": "ML predictions from performance_regression_detector. Source: performance_features | Domain: Performance", "columns": {}},
        "dbr_migration_predictions": {"table_comment": "ML predictions from dbr_migration_risk_scorer. Source: reliability_features | Domain: Performance", "columns": {}},
        "cache_hit_predictions": {"table_comment": "ML predictions from cache_hit_predictor. Source: performance_features | Domain: Performance", "columns": {}},
        "query_optimization_predictions": {"table_comment": "ML predictions from query_optimization_recommender. Source: performance_features | Domain: Performance", "columns": {}},
        "job_failure_predictions": {"table_comment": "ML predictions from job_failure_predictor. Source: reliability_features | Domain: Reliability", "columns": {}},
        "duration_predictions": {"table_comment": "ML predictions from job_duration_forecaster. Source: reliability_features | Domain: Reliability", "columns": {}},
        "sla_breach_predictions": {"table_comment": "ML predictions from sla_breach_predictor. Source: reliability_features | Domain: Reliability", "columns": {}},
        "retry_success_predictions": {"table_comment": "ML predictions from retry_success_predictor. Source: reliability_features | Domain: Reliability", "columns": {}},
        "pipeline_health_predictions": {"table_comment": "ML predictions from pipeline_health_scorer. Source: reliability_features | Domain: Reliability", "columns": {}},
        "data_drift_predictions": {"table_comment": "ML predictions from data_drift_detector. Source: quality_features | Domain: Quality", "columns": {}},
        "freshness_predictions": {"table_comment": "ML predictions from data_freshness_predictor. Source: quality_features | Domain: Quality", "columns": {}},
        "tag_recommendations": {"table_comment": "ML predictions from tag_recommender. Uses TF-IDF. Source: cost_features + job_names | Domain: Cost", "columns": {}}
    }
    
    # Define fallback apply function
    def apply_prediction_metadata(spark, full_table_name: str) -> bool:
        """Fallback metadata application when utility module unavailable."""
        table_name = full_table_name.split('.')[-1]
        if table_name not in PREDICTION_TABLE_METADATA:
            return False
        metadata = PREDICTION_TABLE_METADATA[table_name]
        try:
            table_comment = metadata.get("table_comment", "").replace("'", "''")
            spark.sql(f"COMMENT ON TABLE {full_table_name} IS '{table_comment}'")
            columns = metadata.get("columns", {})
            table_columns = [f.name for f in spark.table(full_table_name).schema.fields]
            for col_name, col_meta in columns.items():
                if col_name in table_columns:
                    if isinstance(col_meta, dict):
                        comment = col_meta.get("business_description", "")
                        if col_meta.get("interpretation"):
                            comment += f" {col_meta.get('interpretation')}"
                    else:
                        comment = col_meta
                    escaped_comment = comment[:1000].replace("'", "''")
                    spark.sql(f"ALTER TABLE {full_table_name} ALTER COLUMN `{col_name}` COMMENT '{escaped_comment}'")
            return True
        except Exception as e:
            print(f"    ⚠ Metadata warning: {str(e)[:80]}")
            return False


def apply_table_metadata(spark, full_table_name: str) -> bool:
    """
    Apply table and column metadata to a prediction table.
    Enables Genie Space natural language queries and AI/BI auto-complete.
    
    Uses centralized metadata from utility module if available, fallback otherwise.
    """
    # Try using the imported utility function first (has comprehensive metadata)
    if _METADATA_SOURCE == "utility_module":
        try:
            return apply_prediction_metadata(spark, full_table_name)
        except Exception as e:
            print(f"    ⚠ Utility module error, using fallback: {str(e)[:50]}")
    
    # Fallback to inline metadata
    table_name = full_table_name.split('.')[-1]
    
    if table_name not in PREDICTION_TABLE_METADATA:
        print(f"    ⚠ No metadata for {table_name}")
        return False
    
    metadata = PREDICTION_TABLE_METADATA[table_name]
    
    try:
        # Apply table comment
        table_comment = metadata.get("table_comment", "").replace("'", "''")
        spark.sql(f"COMMENT ON TABLE {full_table_name} IS '{table_comment}'")
        
        # Apply column comments (handle both dict and string formats)
        columns = metadata.get("columns", {})
        if not columns:
            print(f"    📝 Table comment added (no column metadata in fallback)")
            return True
            
        table_columns = [f.name for f in spark.table(full_table_name).schema.fields]
        columns_updated = 0
        
        for col_name, col_meta in columns.items():
            if col_name in table_columns:
                # Handle nested dict format (business_description + interpretation)
                if isinstance(col_meta, dict):
                    comment = col_meta.get("business_description", "")
                    if col_meta.get("interpretation"):
                        comment += f" {col_meta.get('interpretation')}"
                else:
                    comment = col_meta
                
                escaped_comment = comment[:1000].replace("'", "''")
                spark.sql(f"ALTER TABLE {full_table_name} ALTER COLUMN `{col_name}` COMMENT '{escaped_comment}'")
                columns_updated += 1
        
        print(f"    📝 Table comment + {columns_updated} column comments added")
        return True
        
    except Exception as e:
        print(f"    ⚠ Metadata warning: {str(e)[:80]}")
        return False

# COMMAND ----------

def check_model_exists(catalog: str, schema: str, model_name: str) -> Tuple[bool, Optional[int]]:
    """Check if model exists in Unity Catalog registry."""
    client = MlflowClient()
    full_model_name = f"{catalog}.{schema}.{model_name}"
    
    try:
        # Get latest version
        versions = client.search_model_versions(f"name='{full_model_name}'")
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            return True, int(latest.version)
        return False, None
    except Exception:
        return False, None

# COMMAND ----------

def run_inference_simple(
    fe: FeatureEngineeringClient,
    spark: SparkSession,
    catalog: str,
    feature_schema: str,
    model_name: str,
    feature_table: str,
    output_table: str,
    model_version: int
) -> Tuple[str, int, Optional[str]]:
    """
    Simple batch inference following official Databricks pattern.
    
    1. Get lookup keys DataFrame
    2. Call fe.score_batch()
    3. Write to table
    
    That's it. No caching, no conversion, just the standard pattern.
    """
    full_model_name = f"{catalog}.{feature_schema}.{model_name}"
    # Use version number, not @latest alias
    model_uri = f"models:/{full_model_name}/{model_version}"
    full_feature_table = f"{catalog}.{feature_schema}.{feature_table}"
    full_output_table = f"{catalog}.{feature_schema}.{output_table}"
    
    try:
        # Step 1: Create lookup DataFrame - dynamically get keys from table schema
        lookup_keys = get_feature_table_keys(spark, full_feature_table)
        print(f"    🔑 Lookup keys: {lookup_keys}")
        
        lookup_df = (
            spark.table(full_feature_table)
            .select(*lookup_keys)
            .distinct()
            .limit(100_000)  # Reasonable limit for batch
        )
        
        row_count = lookup_df.count()
        print(f"    📊 Scoring {row_count:,} records with model v{model_version}...")
        
        # Step 2: Score using feature engineering (THE SIMPLE PATTERN)
        # fe.score_batch() handles ALL feature lookup automatically
        predictions = fe.score_batch(
            model_uri=model_uri,
            df=lookup_df
        )
        
        # Step 3: Add metadata and save
        predictions_with_meta = (
            predictions
            .withColumn("model_name", F.lit(model_name))
            .withColumn("scored_at", F.current_timestamp())
        )
        
        # Drop and recreate to avoid schema conflicts
        spark.sql(f"DROP TABLE IF EXISTS {full_output_table}")
        predictions_with_meta.write.format("delta").mode("overwrite").saveAsTable(full_output_table)
        
        # Apply table and column metadata for Genie/AI-BI discoverability
        if apply_table_metadata(spark, full_output_table):
            print(f"    📝 Metadata applied")
        
        final_count = spark.table(full_output_table).count()
        return "SUCCESS", final_count, None
        
    except Exception as e:
        import traceback
        # Get full stack trace for debugging
        full_trace = traceback.format_exc()
        print(f"    ❌ FULL ERROR TRACE:\n{full_trace}")
        
        error_msg = str(e)
        # Truncate for summary but keep full trace in logs
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."
        return "FAILED", 0, error_msg

# COMMAND ----------

def main():
    """Run batch inference for all models."""
    
    start_time = time.time()
    
    # Get parameters
    catalog, gold_schema, feature_schema = get_parameters()
    print(f"Catalog: {catalog}")
    print(f"Feature Schema: {feature_schema}")
    print()
    
    # Initialize clients
    spark = SparkSession.builder.getOrCreate()
    fe = FeatureEngineeringClient()
    
    # Get model configs
    model_configs = get_model_configs(catalog, feature_schema)
    
    # Track results
    results = []
    
    print("=" * 80)
    print("BATCH INFERENCE - SIMPLE PATTERN")
    print("=" * 80)
    print()
    
    for i, config in enumerate(model_configs, 1):
        model_name = config["model_name"]
        feature_table = config["feature_table"]
        output_table = config["output_table"]
        domain = config["domain"]
        skip_fe = config.get("skip_fe", False)
        
        print(f"[{i}/{len(model_configs)}] {model_name}")
        print(f"    Domain: {domain}")
        print(f"    Feature Table: {feature_table}")
        
        # Skip models that don't use feature engineering (e.g., TF-IDF models)
        if skip_fe:
            print(f"    ⏭️  Skipped (uses TF-IDF, not feature store)")
            results.append({
                "model_name": model_name,
                "domain": domain,
                "status": "SKIPPED",
                "records": 0,
                "error": "Model uses TF-IDF, not feature store"
            })
            print()
            continue
        
        # Check if model exists
        exists, version = check_model_exists(catalog, feature_schema, model_name)
        if not exists:
            print(f"    ❌ Model not found in registry")
            results.append({
                "model_name": model_name,
                "domain": domain,
                "status": "NOT_FOUND",
                "records": 0,
                "error": "Model not registered"
            })
            print()
            continue
        
        print(f"    Model Version: v{version}")
        
        # Run inference
        status, records, error = run_inference_simple(
            fe, spark, catalog, feature_schema,
            model_name, feature_table, output_table, version
        )
        
        if status == "SUCCESS":
            print(f"    ✅ {records:,} predictions saved to {output_table}")
        else:
            print(f"    ❌ {error}")
        
        results.append({
            "model_name": model_name,
            "domain": domain,
            "status": status,
            "records": records,
            "error": error
        })
        print()
    
    # Summary
    total_time = time.time() - start_time
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    not_found = [r for r in results if r["status"] == "NOT_FOUND"]
    skipped = [r for r in results if r["status"] == "SKIPPED"]
    total_records = sum(r["records"] for r in results)
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Models:    {len(results)}")
    print(f"✅ Successful:    {len(successful)}")
    print(f"❌ Failed:        {len(failed)}")
    print(f"⚠️  Not Found:    {len(not_found)}")
    print(f"⏭️  Skipped:      {len(skipped)}")
    print(f"Total Records:   {total_records:,}")
    print(f"Duration:        {total_time:.1f}s")
    print()
    
    if successful:
        print("✅ SUCCESSFUL MODELS:")
        for r in successful:
            print(f"   [{r['domain']:12}] {r['model_name']:35} {r['records']:>10,} records")
        print()
    
    if failed:
        print("❌ FAILED MODELS:")
        for r in failed:
            print(f"   [{r['domain']:12}] {r['model_name']}")
            print(f"      Error: {r['error'][:100]}..." if r['error'] and len(r['error']) > 100 else f"      Error: {r['error']}")
        print()
    
    if not_found:
        print("⚠️  MODELS NOT FOUND (need training):")
        for r in not_found:
            print(f"   [{r['domain']:12}] {r['model_name']}")
        print()
    
    # Final status
    final_status = "SUCCESS" if len(failed) == 0 and len(not_found) == 0 else "PARTIAL"
    print(f"FINAL STATUS: {final_status}")
    
    # Return results for job orchestration
    return {
        "status": final_status,
        "total_models": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "not_found": len(not_found),
        "skipped": len(skipped),
        "total_records": total_records,
        "failed_models": [r["model_name"] for r in failed],
        "not_found_models": [r["model_name"] for r in not_found]
    }

# COMMAND ----------

if __name__ == "__main__":
    result = main()

# COMMAND ----------

# Exit signal for job orchestration
# IMPORTANT: Job FAILS if any model failed or not found
result = main() if 'result' not in dir() else result

if result["failed"] > 0 or result["not_found"] > 0:
    error_msg = f"FAILED: {result['failed']} model(s) failed, {result['not_found']} not found. Failed models: {result['failed_models']}"
    print(f"\n❌ {error_msg}")
    # Use raise to ensure job shows as FAILED in Databricks
    raise RuntimeError(error_msg)
else:
    print(f"\n✅ All {result['successful']} models completed successfully!")
    dbutils.notebook.exit(json.dumps(result))
