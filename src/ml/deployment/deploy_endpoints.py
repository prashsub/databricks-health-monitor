# Databricks notebook source
"""
TRAINING MATERIAL: Model Serving Endpoint Deployment
====================================================

This script deploys ML models to Mosaic AI Model Serving endpoints,
demonstrating the Databricks SDK pattern for endpoint management.

MODEL SERVING ARCHITECTURE:
---------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  Unity Catalog (Models)          Model Serving                          │
│  ──────────────────────          ─────────────                          │
│  catalog.schema.cost_anomaly     health-monitor-cost-anomaly endpoint   │
│  catalog.schema.security_threat  health-monitor-security-threat         │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ServedEntityInput(                                                │  │
│  │      entity_name="catalog.schema.model_name",                     │  │
│  │      entity_version="1",           # or use alias                 │  │
│  │      workload_size="Small",        # Small/Medium/Large           │  │
│  │      scale_to_zero_enabled=True,   # Cost optimization            │  │
│  │  )                                                                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  AutoCaptureConfigInput(                                           │  │
│  │      catalog=catalog,                                             │  │
│  │      schema=feature_schema,        # Inference table location     │  │
│  │      enabled=True,                                                │  │
│  │  )                                                                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

ENDPOINT CONFIGURATION PATTERN:
-------------------------------

    ENDPOINT_CONFIG = {
        "realtime": [
            {
                "name": "endpoint-name",
                "model_name": "model_in_uc",
                "scale_to_zero": True,    # Cost optimization
                "workload_size": "Small", # Small = $0.07/hr
            }
        ],
        "batch": [...]  # Scored via fe.score_batch, not endpoints
    }

SCALE-TO-ZERO DECISION:
-----------------------

| Endpoint | Scale-to-Zero | Why |
|----------|---------------|-----|
| cost-anomaly | True | Occasional scoring, cost-sensitive |
| security-threat | **False** | Always-on for security SLA |
| job-failure | True | Pre-run only, infrequent |

INFERENCE TABLES:
-----------------

AutoCaptureConfigInput enables automatic logging of:
- Input features
- Model predictions
- Latency metrics
- Timestamp

Used for drift detection and retraining triggers.

Endpoint Types:
- Real-time: cost-anomaly, security-threat, job-failure, query-perf (<100ms latency)
- Batch: budget-forecast, capacity-plan (via scheduled jobs)

Reference: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/
"""

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
    AutoCaptureConfigInput,
)
from typing import Dict, List, Optional
import time

# COMMAND ----------

def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, feature_schema

# COMMAND ----------

# Endpoint configuration for real-time serving
ENDPOINT_CONFIG = {
    # High-priority real-time endpoints
    "realtime": [
        {
            "name": "health-monitor-cost-anomaly",
            "model_name": "cost_anomaly_detector",
            "scale_to_zero": True,
            "workload_size": "Small",
            "description": "Real-time cost anomaly detection for billing alerts"
        },
        {
            "name": "health-monitor-security-threat",
            "model_name": "security_threat_detector",
            "scale_to_zero": False,  # Always-on for security
            "workload_size": "Small",
            "description": "Real-time security threat detection"
        },
        {
            "name": "health-monitor-job-failure",
            "model_name": "job_failure_predictor",
            "scale_to_zero": True,
            "workload_size": "Small",
            "description": "Pre-run job failure probability prediction"
        },
        {
            "name": "health-monitor-query-perf",
            "model_name": "query_forecaster",
            "scale_to_zero": True,
            "workload_size": "Small",
            "description": "Query duration prediction for SLA planning"
        }
    ],
    # Batch inference endpoints (lower priority)
    "batch": [
        {
            "name": "health-monitor-budget-forecast",
            "model_name": "budget_forecaster",
            "scale_to_zero": True,
            "workload_size": "Small",
            "description": "Monthly budget forecasting with confidence intervals"
        }
    ]
}

# COMMAND ----------

def get_registered_model_name(catalog: str, schema: str, model_name: str) -> str:
    """Get fully qualified model name for Unity Catalog."""
    return f"{catalog}.{schema}.health_monitor_{model_name}"

# COMMAND ----------

def create_or_update_endpoint(
    w: WorkspaceClient,
    endpoint_name: str,
    model_name: str,
    catalog: str,
    schema: str,
    scale_to_zero: bool = True,
    workload_size: str = "Small",
    description: str = ""
) -> bool:
    """
    Create or update a model serving endpoint.
    
    Configures:
    - Served model from Unity Catalog
    - Inference tables for monitoring
    - Auto-scaling configuration
    
    Args:
        w: WorkspaceClient
        endpoint_name: Name for the endpoint
        model_name: Short model name
        catalog: Unity Catalog name
        schema: Schema name
        scale_to_zero: Whether to scale to zero when idle
        workload_size: Size of the serving workload
        description: Endpoint description
        
    Returns:
        True if successful, False otherwise
    """
    full_model_name = get_registered_model_name(catalog, schema, model_name)
    
    # Configuration for served entity
    served_entity = ServedEntityInput(
        entity_name=full_model_name,
        entity_version="1",  # Use alias 'champion' in production
        workload_size=workload_size,
        scale_to_zero_enabled=scale_to_zero,
    )
    
    # Inference table configuration
    auto_capture = AutoCaptureConfigInput(
        catalog_name=catalog,
        schema_name=schema,
        table_name_prefix=f"inference_{model_name}",
        enabled=True,
    )
    
    # Endpoint configuration
    endpoint_config = EndpointCoreConfigInput(
        served_entities=[served_entity],
        auto_capture_config=auto_capture,
    )
    
    try:
        # Check if endpoint exists
        try:
            existing = w.serving_endpoints.get(endpoint_name)
            print(f"  Updating existing endpoint: {endpoint_name}")
            
            # Update endpoint
            w.serving_endpoints.update_config(
                name=endpoint_name,
                served_entities=[served_entity],
                auto_capture_config=auto_capture,
            )
            
        except Exception:
            # Create new endpoint
            print(f"  Creating new endpoint: {endpoint_name}")
            
            w.serving_endpoints.create(
                name=endpoint_name,
                config=endpoint_config,
            )
        
        print(f"  ✓ Endpoint {endpoint_name} configured")
        print(f"    Model: {full_model_name}")
        print(f"    Scale to zero: {scale_to_zero}")
        print(f"    Inference table: {catalog}.{schema}.inference_{model_name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to configure endpoint {endpoint_name}: {e}")
        return False

# COMMAND ----------

def wait_for_endpoint(w: WorkspaceClient, endpoint_name: str, timeout_minutes: int = 30) -> bool:
    """
    Wait for an endpoint to be ready.
    
    Args:
        w: WorkspaceClient
        endpoint_name: Name of the endpoint
        timeout_minutes: Maximum time to wait
        
    Returns:
        True if endpoint is ready, False if timeout
    """
    print(f"  Waiting for endpoint {endpoint_name} to be ready...")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while time.time() - start_time < timeout_seconds:
        try:
            endpoint = w.serving_endpoints.get(endpoint_name)
            state = endpoint.state.ready
            
            if state == "READY":
                print(f"  ✓ Endpoint {endpoint_name} is ready")
                return True
            elif state in ["FAILED", "UPDATE_FAILED"]:
                print(f"  ✗ Endpoint {endpoint_name} failed to deploy")
                return False
            
        except Exception as e:
            pass
        
        time.sleep(30)
    
    print(f"  ⊘ Timeout waiting for endpoint {endpoint_name}")
    return False

# COMMAND ----------

def deploy_all_endpoints(catalog: str, schema: str) -> Dict[str, List[str]]:
    """
    Deploy all model serving endpoints.
    
    Args:
        catalog: Unity Catalog name
        schema: Schema name
        
    Returns:
        Dictionary of endpoint type -> list of deployed endpoints
    """
    print("\n" + "=" * 80)
    print("Deploying Model Serving Endpoints")
    print("=" * 80)
    
    w = WorkspaceClient()
    deployed = {"realtime": [], "batch": []}
    
    # Deploy real-time endpoints
    print("\nREAL-TIME ENDPOINTS")
    print("-" * 40)
    
    for config in ENDPOINT_CONFIG["realtime"]:
        success = create_or_update_endpoint(
            w=w,
            endpoint_name=config["name"],
            model_name=config["model_name"],
            catalog=catalog,
            schema=schema,
            scale_to_zero=config["scale_to_zero"],
            workload_size=config["workload_size"],
            description=config["description"]
        )
        
        if success:
            deployed["realtime"].append(config["name"])
    
    # Deploy batch endpoints
    print("\nBATCH ENDPOINTS")
    print("-" * 40)
    
    for config in ENDPOINT_CONFIG["batch"]:
        success = create_or_update_endpoint(
            w=w,
            endpoint_name=config["name"],
            model_name=config["model_name"],
            catalog=catalog,
            schema=schema,
            scale_to_zero=config["scale_to_zero"],
            workload_size=config["workload_size"],
            description=config["description"]
        )
        
        if success:
            deployed["batch"].append(config["name"])
    
    return deployed

# COMMAND ----------

def print_deployment_summary(deployed: Dict[str, List[str]]):
    """Print summary of endpoint deployments."""
    print("\n" + "=" * 80)
    print("Endpoint Deployment Summary")
    print("=" * 80)
    
    total = 0
    for endpoint_type, endpoints in deployed.items():
        count = len(endpoints)
        total += count
        status = "✓" if count > 0 else "⊘"
        print(f"{status} {endpoint_type.upper()}: {count} endpoints")
        for endpoint in endpoints:
            print(f"    - {endpoint}")
    
    print(f"\nTotal endpoints deployed: {total}")
    print("\nNote: Endpoints may take 5-15 minutes to become ready.")
    print("Use the Serving UI to monitor deployment status.")

# COMMAND ----------

def main():
    """Main entry point for endpoint deployment."""
    catalog, feature_schema = get_parameters()
    
    try:
        deployed = deploy_all_endpoints(catalog, feature_schema)
        print_deployment_summary(deployed)
        
        print("\n" + "=" * 80)
        print("✓ Endpoint Deployment Initiated!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during deployment: {str(e)}")
        raise

# COMMAND ----------

if __name__ == "__main__":
    main()






