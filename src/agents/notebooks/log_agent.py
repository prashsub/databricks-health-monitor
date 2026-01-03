# Databricks notebook source
# MAGIC %md
# MAGIC # Log Agent to Model Registry
# MAGIC
# MAGIC Logs the Health Monitor orchestrator agent to Unity Catalog Model Registry.

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0.0 langchain>=0.3.0 langgraph>=0.2.0 langchain-databricks databricks-langchain databricks-sdk
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "health_monitor")
dbutils.widgets.text("schema", "agents")
dbutils.widgets.text("model_name", "health_monitor_agent")
dbutils.widgets.text("llm_endpoint", "databricks-claude-3-7-sonnet")
dbutils.widgets.text("lakebase_instance", "health_monitor_memory")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
model_name = dbutils.widgets.get("model_name")
llm_endpoint = dbutils.widgets.get("llm_endpoint")
lakebase_instance = dbutils.widgets.get("lakebase_instance")

# COMMAND ----------

import os

# Set environment variables for agent configuration
os.environ["DATABRICKS_HOST"] = dbutils.notebook.entry_point.getDbutils().notebook().getContext().browserHostName().get()
os.environ["LLM_ENDPOINT"] = llm_endpoint
os.environ["LAKEBASE_INSTANCE_NAME"] = lakebase_instance

# COMMAND ----------

import mlflow
from databricks_langchain import DatabricksServingEndpoint, DatabricksLakebase

# Set experiment
experiment_name = f"/Shared/health_monitor/agent_models"
mlflow.set_experiment(experiment_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Agent

# COMMAND ----------

# Import the agent module
import sys
sys.path.insert(0, "/Workspace/Repos/health_monitor/src")

from agents.orchestrator.agent import HealthMonitorAgent

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create and Log Agent

# COMMAND ----------

# Create agent instance
agent = HealthMonitorAgent()

# Define resource dependencies for auth passthrough
resources = [
    DatabricksServingEndpoint(llm_endpoint),
    DatabricksLakebase(database_instance_name=lakebase_instance),
]

# Input example for signature inference
input_example = {
    "messages": [
        {"role": "user", "content": "Why did costs spike yesterday?"}
    ],
    "custom_inputs": {
        "user_id": "example@company.com"
    },
}

# COMMAND ----------

# Set model for logging (per MLflow GenAI patterns)
mlflow.models.set_model(agent)

# Registered model name
registered_model_name = f"{catalog}.{schema}.{model_name}"

with mlflow.start_run(run_name=f"agent_registration_v1") as run:
    # Log parameters
    mlflow.log_params({
        "agent_type": "multi_agent_orchestrator",
        "llm_endpoint": llm_endpoint,
        "lakebase_instance": lakebase_instance,
        "catalog": catalog,
        "schema": schema,
    })

    # Log the agent model
    logged_model = mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=agent,
        input_example=input_example,
        resources=resources,
        registered_model_name=registered_model_name,
        pip_requirements=[
            "mlflow>=3.0.0",
            "langchain>=0.3.0",
            "langgraph>=0.2.0",
            "langchain-databricks>=0.1.0",
            "databricks-sdk>=0.30.0",
            "databricks-langchain>=0.1.0",
            "pydantic>=2.0.0",
        ],
    )

    print(f"Model logged: {logged_model.model_uri}")
    print(f"Registered as: {registered_model_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set Production Alias

# COMMAND ----------

from mlflow import MlflowClient

client = MlflowClient()

# Get latest version
versions = client.search_model_versions(f"name='{registered_model_name}'")
if versions:
    latest_version = max(versions, key=lambda v: int(v.version)).version

    # Set aliases
    client.set_registered_model_alias(
        name=registered_model_name,
        alias="champion",
        version=latest_version,
    )
    print(f"Set 'champion' alias to version {latest_version}")

# COMMAND ----------

print(f"""
Agent Registration Complete
===========================
Model: {registered_model_name}
Version: {latest_version}
Alias: champion

To deploy to Model Serving:
1. Go to Serving in Databricks UI
2. Create endpoint from {registered_model_name}@champion
3. Enable GPU for faster inference
""")

dbutils.notebook.exit("SUCCESS")
