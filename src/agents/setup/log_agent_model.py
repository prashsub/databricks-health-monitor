# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
import sys
import os

try:
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
Log Agent Model
===============

Logs the Health Monitor Agent to MLflow Model Registry with proper
configuration for deployment to Model Serving.

Schema Naming Convention:
    Dev: prashanth_subrahmanyam_catalog.dev_<user>_system_gold_agent
    Prod: main.system_gold_agent
"""

# COMMAND ----------

import mlflow
import mlflow.langchain
from mlflow import MlflowClient


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    agent_schema = dbutils.widgets.get("agent_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Agent Schema: {agent_schema}")
    
    return catalog, agent_schema


# COMMAND ----------

def log_agent_model(catalog: str, agent_schema: str):
    """Log the agent model to MLflow Model Registry."""
    from src.agents.orchestrator.agent import HealthMonitorAgent
    
    model_name = f"{catalog}.{agent_schema}.health_monitor_agent"
    experiment_path = f"/Shared/health_monitor/agent_models"
    
    print(f"Logging agent model to: {model_name}")
    print(f"Using experiment: {experiment_path}")
    
    mlflow.set_experiment(experiment_path)
    
    # Create agent instance
    agent = HealthMonitorAgent()
    
    # Set the model for logging
    mlflow.models.set_model(agent)
    
    with mlflow.start_run(run_name="health_monitor_agent_registration") as run:
        # Log parameters
        mlflow.log_params({
            "agent_type": "multi_agent_orchestrator",
            "domains": "cost,security,performance,reliability,quality",
            "memory_type": "lakebase",
            "llm_endpoint": "databricks-claude-3-7-sonnet"
        })
        
        # Log the agent
        mlflow.langchain.log_model(
            lc_model=agent.graph if hasattr(agent, 'graph') else agent,
            artifact_path="agent",
            registered_model_name=model_name,
            pip_requirements=[
                "mlflow>=3.0.0",
                "langchain>=0.3.0",
                "langgraph>=0.2.0",
                "langchain-databricks>=0.1.0",
                "databricks-sdk>=0.28.0"
            ],
            input_example={
                "messages": [
                    {"role": "user", "content": "What's my current DBU spend?"}
                ]
            }
        )
        
        print(f"  ✓ Model logged in run: {run.info.run_id}")
    
    # Set production alias
    client = MlflowClient()
    latest_versions = client.get_latest_versions(model_name)
    
    if latest_versions:
        latest_version = latest_versions[0].version
        
        client.set_registered_model_alias(
            name=model_name,
            alias="production",
            version=latest_version
        )
        print(f"  ✓ Set production alias to version {latest_version}")
    
    return model_name


def main():
    """Main entry point."""
    catalog, agent_schema = get_parameters()
    
    try:
        model_name = log_agent_model(catalog, agent_schema)
        
        print("\n" + "=" * 60)
        print("✓ Agent model logged successfully!")
        print("=" * 60)
        print(f"\nModel: {model_name}")
        print(f"Alias: production")
        
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error logging agent model: {str(e)}")
        raise


# COMMAND ----------

if __name__ == "__main__":
    main()

