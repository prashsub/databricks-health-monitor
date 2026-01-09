# Databricks notebook source
# ===========================================================================
# Connect Deployment Job to Unity Catalog Model
# ===========================================================================
"""
Connects the deployment job to the Unity Catalog model so that deployment
jobs auto-trigger when new model versions are created.

Reference: https://docs.databricks.com/aws/en/mlflow/deployment-job#connect-the-deployment-job-to-a-model-using-the-mlflow-client
"""

# COMMAND ----------

import mlflow
from mlflow.tracking.client import MlflowClient

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")
dbutils.widgets.text("deployment_job_id", "526980210300018")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")
deployment_job_id = dbutils.widgets.get("deployment_job_id")

# Model name in Unity Catalog format: <catalog>.<schema>.<model>
model_name = f"{catalog}.{agent_schema}.health_monitor_agent"

print(f"Model: {model_name}")
print(f"Deployment Job ID: {deployment_job_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Connect Deployment Job to Model
# MAGIC 
# MAGIC Per [MLflow 3 Deployment Jobs](https://docs.databricks.com/aws/en/mlflow/deployment-job):
# MAGIC - The deployment job will auto-trigger on any new model versions created
# MAGIC - Historical information about each deployment job run is tracked in the activity log
# MAGIC - Metrics from evaluation appear on the model version page

# COMMAND ----------

# Initialize MLflow client with Unity Catalog registry
client = MlflowClient(registry_uri="databricks-uc")

# Connect deployment job to model
try:
    # Check if model exists
    model = client.get_registered_model(model_name)
    print(f"✓ Found existing model: {model_name}")
    
    # Update model with deployment job
    client.update_registered_model(
        name=model_name, 
        deployment_job_id=deployment_job_id
    )
    print(f"✓ Connected deployment job {deployment_job_id} to model")
    
except mlflow.exceptions.RestException as e:
    if "RESOURCE_DOES_NOT_EXIST" in str(e):
        print(f"✗ Model {model_name} does not exist. Creating with deployment job...")
        client.create_registered_model(
            name=model_name, 
            deployment_job_id=deployment_job_id
        )
        print(f"✓ Created model and connected deployment job")
    else:
        raise

# COMMAND ----------

# Verify the connection
model = client.get_registered_model(model_name)
print(f"\n{'='*60}")
print("MODEL DETAILS")
print(f"{'='*60}")
print(f"Name: {model.name}")
print(f"Description: {model.description or 'N/A'}")
print(f"Latest Versions: {len(model.latest_versions) if model.latest_versions else 0}")

# Check if deployment_job_id is accessible
if hasattr(model, 'deployment_job_id'):
    print(f"Deployment Job ID: {model.deployment_job_id}")
else:
    print("Deployment Job: Connected (verify in UI)")

print(f"{'='*60}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC 
# MAGIC 1. **Verify in UI**: Go to the model page in Unity Catalog and check the "Deployment job" section
# MAGIC 2. **Auto-trigger**: New model versions will automatically trigger the deployment job
# MAGIC 3. **Manual trigger**: You can also manually trigger on the model version page

# COMMAND ----------

print(f"""
✅ DEPLOYMENT JOB CONNECTED!

Model: {model_name}
Job ID: {deployment_job_id}

Next time you create a new model version (by running log_agent_model),
the deployment job will automatically:
1. Evaluate the new version
2. Check against thresholds
3. Promote to staging/production if approved

View model: https://e2-demo-field-eng.cloud.databricks.com/explore/data/models/{catalog}/{agent_schema}/health_monitor_agent
""")

dbutils.notebook.exit("SUCCESS")


