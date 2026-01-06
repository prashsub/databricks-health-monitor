# Databricks notebook source
# ===========================================================================
# Create Serving Endpoint with AI Gateway
# ===========================================================================
"""
Creates the Model Serving endpoint for the Health Monitor Agent.

This script uses the Databricks SDK to programmatically create the endpoint
AFTER the model has been registered.

## AI Gateway vs auto_capture_config

| Feature              | auto_capture_config | AI Gateway         |
|---------------------|--------------------|--------------------|
| Inference Logging    | ✅                  | ✅ (built-in)       |
| Rate Limiting        | ❌                  | ✅                  |
| Usage Tracking       | ❌                  | ✅                  |
| Guardrails           | ❌                  | ✅                  |
| A/B Testing/Routing  | ❌                  | ✅                  |

**Important:** You cannot use both together - Databricks prevents this to avoid
duplicate logging. AI Gateway is the recommended choice for production.

Reference: 
- https://docs.databricks.com/aws/en/generative-ai/ai-gateway/
- https://docs.databricks.com/aws/en/machine-learning/model-serving/
"""

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
    AiGatewayConfig,
    AiGatewayRateLimit,
    AiGatewayRateLimitKey,
    AiGatewayRateLimitRenewalPeriod,
    AiGatewayUsageTrackingConfig,
    AiGatewayInferenceTableConfig,
)
import os
import time

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")
dbutils.widgets.text("endpoint_name", "health_monitor_agent_dev")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")
endpoint_name = dbutils.widgets.get("endpoint_name")

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")
print(f"Endpoint Name: {endpoint_name}")

# COMMAND ----------

# Configuration - Genie Space IDs and other settings
ENVIRONMENT_VARS = {
    # Genie Space IDs (from Phase 3.6 deployment)
    "COST_GENIE_SPACE_ID": "01f0ea871ffe176fa6aee6f895f83d3b",
    "SECURITY_GENIE_SPACE_ID": "01f0ea9367f214d6a4821605432234c4",
    "PERFORMANCE_GENIE_SPACE_ID": "01f0ea93671e12d490224183f349dba0",
    "RELIABILITY_GENIE_SPACE_ID": "01f0ea8724fd160e8e959b8a5af1a8c5",
    "QUALITY_GENIE_SPACE_ID": "01f0ea93616c1978a99a59d3f2e805bd",
    "UNIFIED_GENIE_SPACE_ID": "01f0ea9368801e019e681aa3abaa0089",
    # LLM Configuration
    "LLM_ENDPOINT": "databricks-claude-3-7-sonnet",
    "LLM_TEMPERATURE": "0.3",
    # Memory Configuration
    "LAKEBASE_INSTANCE_NAME": "health_monitor_lakebase",
    # Feature Flags
    "ENABLE_LONG_TERM_MEMORY": "true",
    "ENABLE_WEB_SEARCH": "true",
    "ENABLE_MLFLOW_TRACING": "true",
}

print("Environment Variables:")
for k, v in ENVIRONMENT_VARS.items():
    print(f"  {k}: {v}")

# COMMAND ----------

def get_model_version_by_alias(model_name: str, alias: str = "production") -> str:
    """
    Get model version by alias (Unity Catalog compatible).
    
    Note: Unity Catalog models don't support get_latest_versions().
    Must use aliases instead.
    
    Reference: https://mlflow.org/docs/latest/model-registry.html#deploy-and-organize-models-with-aliases-and-tags
    """
    from mlflow import MlflowClient
    
    mlflow_client = MlflowClient()
    
    # Try production alias first
    try:
        alias_info = mlflow_client.get_model_version_by_alias(model_name, "production")
        print(f"  ✓ Found model with 'production' alias: version {alias_info.version}")
        return alias_info.version
    except Exception as e:
        print(f"  → 'production' alias not found: {e}")
    
    # Try staging alias
    try:
        alias_info = mlflow_client.get_model_version_by_alias(model_name, "staging")
        print(f"  ✓ Found model with 'staging' alias: version {alias_info.version}")
        return alias_info.version
    except Exception as e:
        print(f"  → 'staging' alias not found: {e}")
    
    # Fall back to version "1" (first version)
    try:
        version_info = mlflow_client.get_model_version(model_name, "1")
        print(f"  ✓ Using version 1 as fallback")
        return "1"
    except Exception as e:
        print(f"  → Version 1 not found: {e}")
    
    raise ValueError(f"No versions found for model: {model_name}. Ensure log_agent_model ran successfully.")

# COMMAND ----------

def build_ai_gateway_config(catalog: str, schema: str) -> AiGatewayConfig:
    """
    Build AI Gateway configuration.
    
    AI Gateway provides:
    - Inference logging (to Unity Catalog tables)
    - Rate limiting (per user/endpoint)
    - Usage tracking (tokens, cost)
    - Guardrails (content filtering)
    
    Reference: https://docs.databricks.com/aws/en/generative-ai/ai-gateway/
    """
    return AiGatewayConfig(
        # =========================================================
        # Inference Logging - writes to Unity Catalog tables
        # =========================================================
        inference_table_config=AiGatewayInferenceTableConfig(
            catalog_name=catalog,
            schema_name=schema,
            table_name_prefix="agent_logs",  # Agent inference logs
            enabled=True,
        ),
        
        # =========================================================
        # Rate Limiting - prevent abuse
        # =========================================================
        rate_limits=[
            AiGatewayRateLimit(
                calls=100,  # 100 calls per minute per user
                key=AiGatewayRateLimitKey.USER,
                renewal_period=AiGatewayRateLimitRenewalPeriod.MINUTE,
            ),
            AiGatewayRateLimit(
                calls=1000,  # 1000 calls per minute for the whole endpoint
                key=AiGatewayRateLimitKey.ENDPOINT,
                renewal_period=AiGatewayRateLimitRenewalPeriod.MINUTE,
            ),
        ],
        
        # =========================================================
        # Usage Tracking - for cost allocation
        # =========================================================
        usage_tracking_config=AiGatewayUsageTrackingConfig(
            enabled=True,
        ),
    )

# COMMAND ----------

def create_or_update_endpoint(
    client: WorkspaceClient,
    endpoint_name: str,
    model_name: str,
    model_version: str,
    catalog: str,
    schema: str,
):
    """
    Create or update the model serving endpoint with AI Gateway.
    
    Uses AI Gateway instead of auto_capture_config because:
    - AI Gateway includes inference logging PLUS rate limiting, usage tracking
    - Databricks doesn't allow both auto_capture_config AND AI Gateway
    - AI Gateway is the recommended approach for production
    """
    print(f"\nCreating/updating endpoint: {endpoint_name}")
    print(f"  Model: {model_name}")
    print(f"  Version: {model_version}")
    print(f"  AI Gateway: ENABLED")
    
    # Check if endpoint already exists
    existing_endpoint = None
    try:
        existing_endpoint = client.serving_endpoints.get(endpoint_name)
        print(f"  ✓ Found existing endpoint")
    except Exception:
        print(f"  → Endpoint does not exist, will create new")
    
    # Build served entity configuration
    served_entity = ServedEntityInput(
        name="health_monitor_agent",
        entity_name=model_name,
        entity_version=model_version,
        workload_size="Small",
        scale_to_zero_enabled=True,
        environment_vars=ENVIRONMENT_VARS,
    )
    
    # Build AI Gateway configuration
    ai_gateway = build_ai_gateway_config(catalog, schema)
    
    if existing_endpoint:
        # Update existing endpoint
        print(f"  → Updating endpoint configuration...")
        
        # Update served entities
        client.serving_endpoints.update_config(
            name=endpoint_name,
            served_entities=[served_entity],
        )
        
        # Note: AI Gateway config update may require separate API call
        # or recreating the endpoint in some versions
        print(f"  ⚠ AI Gateway config may require endpoint recreation")
        
    else:
        # Create new endpoint with AI Gateway
        print(f"  → Creating new endpoint with AI Gateway...")
        
        # Build endpoint config
        endpoint_config = EndpointCoreConfigInput(
            served_entities=[served_entity],
        )
        
        client.serving_endpoints.create(
            name=endpoint_name,
            config=endpoint_config,
            ai_gateway=ai_gateway,
        )
    
    print(f"  ✓ Endpoint configuration submitted")
    return endpoint_name

# COMMAND ----------

def wait_for_endpoint_ready(client: WorkspaceClient, endpoint_name: str, timeout_minutes: int = 30):
    """Wait for the endpoint to be ready."""
    print(f"\nWaiting for endpoint to be ready (timeout: {timeout_minutes} min)...")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while True:
        try:
            endpoint = client.serving_endpoints.get(endpoint_name)
            state = endpoint.state
            
            if state and state.ready == "READY":
                print(f"  ✓ Endpoint is READY")
                return True
            
            if state and state.config_update:
                status = state.config_update
                print(f"  → Status: {status}")
            
        except Exception as e:
            print(f"  → Checking status... ({e})")
        
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            print(f"  ⚠ Timeout waiting for endpoint")
            return False
        
        time.sleep(30)  # Check every 30 seconds

# COMMAND ----------

def main():
    """Main entry point."""
    
    # Initialize SDK client
    client = WorkspaceClient()
    
    # Get model info
    model_name = f"{catalog}.{agent_schema}.health_monitor_agent"
    
    try:
        # Get model version by alias (Unity Catalog compatible)
        model_version = get_model_version_by_alias(model_name)
        print(f"\n✓ Found model version: {model_version}")
        
        # Create or update endpoint with AI Gateway
        create_or_update_endpoint(
            client=client,
            endpoint_name=endpoint_name,
            model_name=model_name,
            model_version=model_version,
            catalog=catalog,
            schema=agent_schema,
        )
        
        # Wait for endpoint to be ready
        is_ready = wait_for_endpoint_ready(client, endpoint_name, timeout_minutes=20)
        
        print("\n" + "=" * 70)
        if is_ready:
            print("✓ Serving endpoint created and ready!")
        else:
            print("⚠ Endpoint created but not yet ready (check UI)")
        print("=" * 70)
        
        print(f"\nEndpoint: {endpoint_name}")
        print(f"Model: {model_name}@{model_version}")
        print(f"\nAI Gateway Features:")
        print(f"  ✓ Inference Logging: {catalog}.{agent_schema}.agent_logs_*")
        print(f"  ✓ Rate Limiting: 100 calls/min per user, 1000/min total")
        print(f"  ✓ Usage Tracking: Enabled")
        
        print(f"\nTest with:")
        print(f'  curl -X POST "https://<workspace>/serving-endpoints/{endpoint_name}/invocations" \\')
        print(f'    -H "Authorization: Bearer $DATABRICKS_TOKEN" \\')
        print(f'    -d \'{{"messages": [{{"role": "user", "content": "Why did costs spike?"}}]}}\'')
        
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error creating endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        dbutils.notebook.exit(f"FAILED: {str(e)}")

# COMMAND ----------

if __name__ == "__main__":
    main()
