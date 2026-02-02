# Databricks notebook source
"""
TRAINING MATERIAL: Model Registration and Alias Management Pattern
===================================================================

This script verifies ML model registration and manages model aliases in
Unity Catalog. It's a post-training step that ensures all models are
properly registered and accessible for inference.

WHY SEPARATE REGISTRATION VERIFICATION:
---------------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  TRAINING PIPELINE                     │  REGISTRATION VERIFICATION      │
├────────────────────────────────────────┼─────────────────────────────────┤
│  25 training scripts run in parallel   │  Single verification job after  │
│  Each logs with registered_model_name  │  Verifies ALL 25 models exist   │
│  May fail silently on registration     │  Catches any registration fails │
│  No alias assignment                   │  Assigns 'champion' alias       │
│                                        │  Provides summary report        │
└────────────────────────────────────────┴─────────────────────────────────┘

MODEL ALIASES (MLflow 3.0):
---------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  ALIASES vs STAGES                                                       │
│                                                                         │
│  MLflow 2.x: Model Stages (Staging, Production, Archived)               │
│  MLflow 3.0: Model Aliases (custom, flexible)  ✅                        │
│                                                                         │
│  Common Aliases:                                                        │
│  - "champion": Current production model                                 │
│  - "challenger": Model being evaluated for promotion                    │
│  - "baseline": Reference model for comparison                           │
│                                                                         │
│  Usage in inference:                                                    │
│  model_uri = f"models:/{model_name}@champion"                           │
│  model = mlflow.pyfunc.load_model(model_uri)                            │
│                                                                         │
│  Benefits:                                                              │
│  - Multiple models can have different aliases                           │
│  - Aliases are human-readable                                           │
│  - Easy to change without version numbers                               │
│  - Supports A/B testing patterns                                        │
└─────────────────────────────────────────────────────────────────────────┘

MODEL INVENTORY:
----------------

This project has 25 ML models across 5 agent domains:

Cost Agent (6):
- cost_anomaly_detector, budget_forecaster, job_cost_optimizer
- chargeback_attribution, commitment_recommender, tag_recommender

Security Agent (4):
- security_threat_detector, exfiltration_detector
- privilege_escalation_detector, user_behavior_baseline

Performance Agent (7):
- query_performance_forecaster, warehouse_optimizer
- performance_regression_detector, cluster_capacity_planner
- dbr_migration_risk_scorer, cache_hit_predictor
- query_optimization_recommender

Reliability Agent (5):
- job_failure_predictor, job_duration_forecaster
- sla_breach_predictor, retry_success_predictor
- pipeline_health_scorer

Quality Agent (3):
- data_drift_detector, schema_change_predictor
- data_freshness_predictor

VERIFICATION WORKFLOW:
----------------------

1. Iterate through all 25 model names
2. Query Unity Catalog for each model
3. If found: Print version info, assign 'champion' alias
4. If not found: Log as missing (training may have failed)
5. Generate summary report

MLflow 3.0 Best Practices:
- Models are registered during training with registered_model_name
- This script verifies registration and adds model aliases
"""

# COMMAND ----------

from pyspark.sql import SparkSession
import mlflow
from mlflow import MlflowClient

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    feature_schema = dbutils.widgets.get("feature_schema")
    return catalog, feature_schema

# COMMAND ----------

def set_mlflow_registry():
    """Configure MLflow to use Unity Catalog Model Registry."""
    mlflow.set_registry_uri("databricks-uc")
    print("✓ MLflow registry set to Unity Catalog")

# COMMAND ----------

def verify_and_promote_models(catalog: str, feature_schema: str):
    """Verify all models are registered and add aliases."""
    
    # All 25 models from ML Training Pipeline
    # IMPORTANT: These names MUST match the model_name in each training script!
    models = [
        # Cost Agent (6 models)
        "cost_anomaly_detector",
        "budget_forecaster", 
        "job_cost_optimizer",
        "chargeback_attribution",
        "commitment_recommender",
        "tag_recommender",
        # Security Agent (4 models)
        "security_threat_detector",
        "exfiltration_detector",
        "privilege_escalation_detector",
        "user_behavior_baseline",
        # Performance Agent (7 models)
        "query_performance_forecaster",      # Was: query_forecaster
        "warehouse_optimizer",
        "performance_regression_detector",
        "cluster_capacity_planner",
        "dbr_migration_risk_scorer",
        "cache_hit_predictor",
        "query_optimization_recommender",
        # Reliability Agent (5 models)
        "job_failure_predictor",             # Was: failure_predictor
        "job_duration_forecaster",           # Was: duration_forecaster
        "sla_breach_predictor",
        "retry_success_predictor",
        "pipeline_health_scorer",
        # Quality Agent (3 models)
        "data_drift_detector",               # Was: drift_detector
        "schema_change_predictor",
        "data_freshness_predictor"           # Was: freshness_predictor
    ]
    
    client = MlflowClient()
    
    print("\n" + "=" * 80)
    print("MODEL REGISTRATION VERIFICATION")
    print("=" * 80)
    
    registered_count = 0
    
    for model in models:
        model_name = f"{catalog}.{feature_schema}.{model}"
        
        try:
            # Get model versions
            versions = client.search_model_versions(f"name='{model_name}'")
            
            if versions:
                latest_version = max(v.version for v in versions)
                print(f"\n✓ {model}")
                print(f"  Full Name: {model_name}")
                print(f"  Latest Version: {latest_version}")
                print(f"  Status: REGISTERED")
                
                # Add 'champion' alias to latest version
                try:
                    client.set_registered_model_alias(
                        name=model_name,
                        alias="champion",
                        version=latest_version
                    )
                    print(f"  Alias 'champion' → Version {latest_version}")
                except Exception as e:
                    print(f"  Could not set alias: {e}")
                
                registered_count += 1
            else:
                print(f"\n⚠ {model}")
                print(f"  Full Name: {model_name}")
                print(f"  Status: NOT FOUND")
                
        except Exception as e:
            print(f"\n❌ {model}")
            print(f"  Full Name: {model_name}")
            print(f"  Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {registered_count}/{len(models)} models registered")
    print("=" * 80)
    
    return registered_count

# COMMAND ----------

def list_all_models(catalog: str, feature_schema: str):
    """List all registered models in the schema."""
    
    client = MlflowClient()
    
    print("\n" + "=" * 80)
    print("ALL REGISTERED MODELS IN UNITY CATALOG")
    print("=" * 80)
    
    try:
        # Search for models in the catalog.schema
        models = client.search_registered_models(
            filter_string=f"name LIKE '{catalog}.{feature_schema}.%'"
        )
        
        for model in models:
            print(f"\n• {model.name}")
            print(f"  Description: {model.description or 'N/A'}")
            
            # Get latest version info
            versions = client.search_model_versions(f"name='{model.name}'")
            if versions:
                latest = max(versions, key=lambda v: int(v.version))
                print(f"  Latest Version: {latest.version}")
                print(f"  Created: {latest.creation_timestamp}")
                
                # Get aliases
                aliases = [alias for alias in model.aliases]
                if aliases:
                    print(f"  Aliases: {', '.join(aliases)}")
                    
    except Exception as e:
        print(f"Error listing models: {e}")

# COMMAND ----------

def main():
    """Main entry point for model registration verification."""
    print("\n" + "=" * 80)
    print("ML MODEL REGISTRATION")
    print("=" * 80)
    
    catalog, feature_schema = get_parameters()
    set_mlflow_registry()
    
    try:
        # Verify and promote models
        registered_count = verify_and_promote_models(catalog, feature_schema)
        
        # List all models
        list_all_models(catalog, feature_schema)
        
        print("\n" + "=" * 80)
        print("✓ MODEL REGISTRATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()
