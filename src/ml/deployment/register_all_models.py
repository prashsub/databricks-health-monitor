# Databricks notebook source
"""
Register All Models to Unity Catalog
====================================

This script registers all trained models from MLflow experiments
to the Unity Catalog Model Registry.

MLflow 3.0 Key Changes:
- Default registry URI is 'databricks-uc' (Unity Catalog)
- Models registered with full three-level names: catalog.schema.model_name
- All model versions, metrics, and parameters visible in Catalog Explorer
- Automatic lineage tracking with Feature Engineering tables

Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow/model-registry-3
"""

# COMMAND ----------

import mlflow
from mlflow.tracking import MlflowClient
from typing import Dict, List, Optional
import pandas as pd

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, feature_schema

# COMMAND ----------

# Model registry configuration
MODEL_REGISTRY = {
    "cost": {
        "models": [
            "cost_anomaly_detector",
            "budget_forecaster",
            "chargeback_optimizer", 
            "job_cost_optimizer",
            "tag_recommender"
        ],
        "description": "Cost Agent - Anomaly detection, forecasting, and optimization"
    },
    "security": {
        "models": [
            "security_threat_detector",
            "exfiltration_detector",
            "privilege_escalation_detector",
            "user_behavior_baseline"
        ],
        "description": "Security Agent - Threat detection and user behavior analysis"
    },
    "performance": {
        "models": [
            "query_forecaster",
            "warehouse_optimizer",
            "query_optimization_recommender",
            "cluster_capacity_planner",
            "dbr_migration_risk_scorer",
            "cache_hit_predictor"
        ],
        "description": "Performance Agent - Query and compute optimization"
    },
    "reliability": {
        "models": [
            "job_failure_predictor",
            "job_duration_forecaster",
            "sla_breach_predictor",
            "retry_success_predictor",
            "pipeline_health_scorer"
        ],
        "description": "Reliability Agent - Failure prediction and SLA management"
    },
    "quality": {
        "models": [
            "data_freshness_predictor",
            "schema_drift_detector",
            "quality_degradation_forecaster"
        ],
        "description": "Quality Agent - Data quality monitoring and prediction"
    }
}

# COMMAND ----------

def get_registered_model_name(catalog: str, schema: str, model_name: str) -> str:
    """Get fully qualified model name for Unity Catalog."""
    return f"{catalog}.{schema}.health_monitor_{model_name}"

# COMMAND ----------

def find_latest_run(experiment_path: str, model_name: str) -> Optional[str]:
    """
    Find the latest successful run for a model in an experiment.
    
    Args:
        experiment_path: Path to MLflow experiment
        model_name: Name of the model
        
    Returns:
        Run ID of the latest successful run, or None
    """
    client = MlflowClient()
    
    try:
        experiment = client.get_experiment_by_name(experiment_path)
        if not experiment:
            print(f"  Experiment not found: {experiment_path}")
            return None
        
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="status = 'FINISHED'",
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if runs:
            return runs[0].info.run_id
        else:
            print(f"  No successful runs found in: {experiment_path}")
            return None
            
    except Exception as e:
        print(f"  Error finding run: {e}")
        return None

# COMMAND ----------

def register_model_version(
    catalog: str,
    schema: str,
    model_name: str,
    run_id: str,
    description: str
) -> Optional[int]:
    """
    Register a model version from an MLflow run to Unity Catalog.
    
    MLflow 3.0: Uses databricks-uc as default registry URI.
    Models are registered with three-level names: catalog.schema.model_name
    
    Args:
        catalog: Unity Catalog name
        schema: Schema name
        model_name: Short model name
        run_id: MLflow run ID containing the model
        description: Model description
        
    Returns:
        Version number of the registered model, or None if failed
    """
    # Ensure we're using Unity Catalog registry
    mlflow.set_registry_uri("databricks-uc")
    client = MlflowClient(registry_uri="databricks-uc")
    
    full_model_name = get_registered_model_name(catalog, schema, model_name)
    model_uri = f"runs:/{run_id}/{model_name}"
    
    try:
        # Register model (creates registered model if doesn't exist)
        result = mlflow.register_model(
            model_uri=model_uri,
            name=full_model_name,
        )
        
        # Add description to the version
        client.update_model_version(
            name=full_model_name,
            version=result.version,
            description=description
        )
        
        print(f"  ✓ Registered {full_model_name} version {result.version}")
        return int(result.version)
        
    except Exception as e:
        print(f"  ✗ Failed to register {model_name}: {e}")
        return None

# COMMAND ----------

def create_model_aliases(
    catalog: str,
    schema: str,
    model_name: str,
    version: int
):
    """
    Set model aliases for deployment stages.
    
    MLflow 3.0 uses aliases instead of stages:
    - 'champion' - current production model
    - 'challenger' - candidate for A/B testing
    
    Args:
        catalog: Unity Catalog name
        schema: Schema name
        model_name: Short model name
        version: Version number to alias
    """
    mlflow.set_registry_uri("databricks-uc")
    client = MlflowClient(registry_uri="databricks-uc")
    
    full_model_name = get_registered_model_name(catalog, schema, model_name)
    
    try:
        # Set as champion (production-ready)
        client.set_registered_model_alias(
            name=full_model_name,
            alias="champion",
            version=version
        )
        print(f"  Set 'champion' alias on version {version}")
        
    except Exception as e:
        print(f"  Warning: Could not set alias: {e}")

# COMMAND ----------

def register_all_models(catalog: str, schema: str) -> Dict[str, List[str]]:
    """
    Register all trained models to Unity Catalog.
    
    Args:
        catalog: Unity Catalog name
        schema: Schema for model registration
        
    Returns:
        Dictionary of domain -> list of registered models
    """
    print("\n" + "=" * 80)
    print("Registering All Models to Unity Catalog")
    print("=" * 80)
    
    mlflow.set_registry_uri("databricks-uc")
    
    registered = {}
    experiment_base = "/Shared/health_monitor/ml"
    
    for domain, config in MODEL_REGISTRY.items():
        print(f"\n{domain.upper()} AGENT")
        print("-" * 40)
        
        registered[domain] = []
        
        for model_name in config["models"]:
            experiment_path = f"{experiment_base}/{domain}/{model_name}"
            
            # Find latest run
            run_id = find_latest_run(experiment_path, model_name)
            
            if run_id:
                # Register model
                version = register_model_version(
                    catalog=catalog,
                    schema=schema,
                    model_name=model_name,
                    run_id=run_id,
                    description=f"{config['description']} - {model_name}"
                )
                
                if version:
                    registered[domain].append(model_name)
                    
                    # Set champion alias
                    create_model_aliases(catalog, schema, model_name, version)
            else:
                print(f"  ⊘ Skipping {model_name} (no trained model found)")
    
    return registered

# COMMAND ----------

def print_registration_summary(registered: Dict[str, List[str]], catalog: str, schema: str):
    """Print summary of model registration."""
    print("\n" + "=" * 80)
    print("Model Registration Summary")
    print("=" * 80)
    
    total = 0
    for domain, models in registered.items():
        count = len(models)
        total += count
        status = "✓" if count > 0 else "⊘"
        print(f"{status} {domain.upper()}: {count} models")
        for model in models:
            full_name = get_registered_model_name(catalog, schema, model)
            print(f"    - {full_name}")
    
    print(f"\nTotal models registered: {total}")
    print(f"Registry: databricks-uc ({catalog}.{schema})")

# COMMAND ----------

def main():
    """Main entry point for model registration."""
    catalog, feature_schema = get_parameters()
    
    try:
        registered = register_all_models(catalog, feature_schema)
        print_registration_summary(registered, catalog, feature_schema)
        
        print("\n" + "=" * 80)
        print("✓ Model Registration Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during registration: {str(e)}")
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()

