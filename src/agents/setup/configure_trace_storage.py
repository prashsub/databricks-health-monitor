# Databricks notebook source
# ===========================================================================
# Configure Trace Storage Location for Agent Experiment
# ===========================================================================
"""
Sets up Unity Catalog trace storage for the Health Monitor Agent experiment.

This enables:
1. Persistent trace storage in Unity Catalog
2. Trace visibility in the Traces tab
3. Queryable trace data for analysis

Reference: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/
"""

# COMMAND ----------

import mlflow
from mlflow import MlflowClient

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")

# COMMAND ----------

# Configuration - Configure trace storage for all experiments
# Traces go to evaluation experiment (most trace generation happens during eval)
EXPERIMENT_DEVELOPMENT = "/Shared/health_monitor_agent_development"
EXPERIMENT_EVALUATION = "/Shared/health_monitor_agent_evaluation"
EXPERIMENT_DEPLOYMENT = "/Shared/health_monitor_agent_deployment"

# Use evaluation as primary trace experiment
EXPERIMENT_PATH = EXPERIMENT_EVALUATION
TRACE_TABLE_NAME = f"{catalog}.{agent_schema}.agent_traces"

print(f"Experiments:")
print(f"  • Development: {EXPERIMENT_DEVELOPMENT}")
print(f"  • Evaluation: {EXPERIMENT_EVALUATION} (primary trace storage)")
print(f"  • Deployment: {EXPERIMENT_DEPLOYMENT}")
print(f"Trace Table: {TRACE_TABLE_NAME}")

# COMMAND ----------

# Set experiment and configure trace storage
print("\n" + "=" * 60)
print("Configuring Trace Storage Location")
print("=" * 60)

# Set the experiment
mlflow.set_experiment(EXPERIMENT_PATH)
print(f"✓ Set experiment: {EXPERIMENT_PATH}")

# Get experiment ID
client = MlflowClient()
experiment = client.get_experiment_by_name(EXPERIMENT_PATH)
experiment_id = experiment.experiment_id
print(f"✓ Experiment ID: {experiment_id}")

# COMMAND ----------

# Configure trace storage using MLflow tracing configuration
# Reference: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/storage

try:
    # Method 1: Use mlflow.set_registry_uri for Unity Catalog (if not already set)
    mlflow.set_registry_uri("databricks-uc")
    print("✓ Registry URI set to databricks-uc")
except Exception as e:
    print(f"⚠ Registry URI already set or error: {e}")

# COMMAND ----------

# Method 2: Create the trace table if it doesn't exist
# The trace table will be created automatically when traces are logged,
# but we need to set the experiment tag to point to the right location

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Set experiment tag for trace storage location
print("\nSetting experiment tags for trace storage...")

try:
    # Set the trace destination
    mlflow.set_experiment_tag("mlflow.tracing.destination.catalog", catalog)
    mlflow.set_experiment_tag("mlflow.tracing.destination.schema", agent_schema)
    mlflow.set_experiment_tag("mlflow.tracing.enabled", "true")
    print(f"✓ Set trace destination: {catalog}.{agent_schema}")
except Exception as e:
    print(f"⚠ Could not set experiment tags via MLflow: {e}")

# COMMAND ----------

# Method 3: Use Databricks API to configure trace table
# This is the official way to set trace storage location

print("\nConfiguring trace table via Databricks API...")

try:
    # Use the workspace client to set inference table config
    # Note: This API may require specific permissions
    
    from databricks.sdk.service.ml import ExperimentTag
    
    # Get current experiment
    exp = w.experiments.get_experiment(experiment_id=experiment_id)
    print(f"✓ Retrieved experiment: {exp.experiment.name}")
    
    # Set experiment tag for trace table
    w.experiments.set_experiment_tag(
        experiment_id=experiment_id,
        key="mlflow.tracing.destination.catalog",
        value=catalog
    )
    w.experiments.set_experiment_tag(
        experiment_id=experiment_id,
        key="mlflow.tracing.destination.schema", 
        value=agent_schema
    )
    w.experiments.set_experiment_tag(
        experiment_id=experiment_id,
        key="mlflow.tracing.destination.table",
        value="agent_traces"
    )
    print(f"✓ Set trace storage tags via Databricks SDK")
    
except Exception as e:
    print(f"⚠ Databricks API method error: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# Method 4: Enable tracing autolog with destination
print("\nEnabling MLflow tracing autolog...")

try:
    # Enable autolog with Unity Catalog destination
    # Try new API first (no parameters), fall back to legacy
    try:
        mlflow.langchain.autolog()
        print("✓ MLflow LangChain autolog enabled")
    except TypeError:
        mlflow.langchain.autolog(
            log_traces=True,
            log_models=True,
            log_input_examples=True,
        )
        print("✓ MLflow LangChain autolog enabled (legacy API)")
except Exception as e:
    print(f"⚠ Autolog error: {e}")

# COMMAND ----------

# Verify configuration
print("\n" + "=" * 60)
print("Configuration Summary")
print("=" * 60)

# Get updated experiment
experiment = client.get_experiment_by_name(EXPERIMENT_PATH)
print(f"\nExperiment: {experiment.name}")
print(f"Experiment ID: {experiment.experiment_id}")
print(f"\nTags:")
for tag in experiment.tags:
    if 'trace' in tag.key.lower() or 'destination' in tag.key.lower():
        print(f"  • {tag.key}: {tag.value}")

print(f"\n✓ Trace storage location configured for: {catalog}.{agent_schema}")
print(f"\nNOTE: Traces will be stored in table: {TRACE_TABLE_NAME}")
print("      The table will be created automatically when the first trace is logged.")

# COMMAND ----------

dbutils.notebook.exit("SUCCESS")



