# Databricks notebook source
"""
Register All ML Models to Unity Catalog
=======================================

This script registers all trained models to the Unity Catalog Model Registry
and optionally promotes them to the appropriate stage.

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
        "query_forecaster",
        "warehouse_optimizer",
        "performance_regression_detector",
        "cluster_capacity_planner",
        "dbr_migration_risk_scorer",
        "cache_hit_predictor",
        "query_optimization_recommender",
        # Reliability Agent (5 models)
        "failure_predictor",
        "duration_forecaster",
        "sla_breach_predictor",
        "retry_success_predictor",
        "pipeline_health_scorer",
        # Quality Agent (3 models)
        "drift_detector",
        "schema_change_predictor",
        "freshness_predictor"
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
