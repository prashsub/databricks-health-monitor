# 09 - Deployment Pipeline

## Overview

This document details the complete deployment workflow, including setup jobs, model registration, serving endpoint creation, and the MLflow deployment job for evaluation and promotion.

---

## 📍 File Locations

| File | Purpose |
|------|---------|
| `resources/agents/agent_setup_job.yml` | Setup job definition (NO endpoint) |
| `resources/agents/agent_deployment_job.yml` | Deployment job definition (WITH endpoint) |
| `src/agents/setup/create_schemas.py` | Schema/table creation |
| `src/agents/setup/register_prompts.py` | Prompt registry |
| `src/agents/setup/register_scorers.py` | Production monitoring scorers |
| `src/agents/setup/create_evaluation_dataset.py` | Synthetic & manual datasets |
| `src/agents/setup/log_agent_model.py` | Model logging |
| `src/agents/setup/run_evaluation.py` | Evaluation runner |
| `src/agents/setup/deployment_job.py` | **MLflow deployment job + endpoint creation** |

> ⚠️ **Note:** `create_serving_endpoint.py` was removed. Endpoint creation logic is now inside `deployment_job.py` to follow MLflow 3.0 evaluation-gated deployment pattern.

---

## 🏛️ Deployment Architecture

### ⚠️ MLflow 3.0 Pattern: Evaluation-Gated Endpoint Creation

**Key Principle:** Serving endpoint is ONLY created/updated after evaluation passes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENT SETUP JOB                                     │
│                   (Infrastructure + Model Registration)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task 1: create_agent_infrastructure                                        │
│       ↓                                                                     │
│  Task 2: register_prompts  ←──┬──→  Task 2b: register_scorers               │
│       ↓                       │     Task 2c: create_evaluation_datasets     │
│  Task 3: log_agent_model  ←───┘                                             │
│       ↓                                                                     │
│  Task 4: run_evaluation (initial sanity check)                              │
│                                                                             │
│  ⚠️ NO ENDPOINT CREATION HERE - Endpoint is created by deployment job      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AGENT DEPLOYMENT JOB                                   │
│            (Evaluation-Gated Endpoint Creation - MLflow 3.0 Pattern)         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Task 1: run_deployment_job                                                 │
│       ├─── 1. Load model from Unity Catalog                                 │
│       ├─── 2. Run comprehensive evaluation with scorers                     │
│       ├─── 3. Check quality thresholds                                      │
│       │                                                                     │
│       ├─── IF EVALUATION PASSED:                                            │
│       │    ├─── 4. Promote model to staging/production alias                │
│       │    └─── 5. ✅ CREATE/UPDATE SERVING ENDPOINT (AI Gateway enabled)   │
│       │                                                                     │
│       └─── IF EVALUATION FAILED:                                            │
│            └─── ❌ No promotion, NO endpoint creation/update                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Pattern?

| Before (Incorrect) | After (Correct MLflow 3.0) |
|----|----|
| Setup job created endpoint regardless of evaluation | Setup job ONLY logs model |
| Endpoint could serve broken model | Deployment job evaluates FIRST |
| No quality gate | Only creates endpoint IF evaluation passes |
| Manual rollback needed | Automatic quality gate prevents bad deployments |

---

## 📦 Setup Job (agent_setup_job)

### Purpose

The setup job handles **infrastructure and model registration only**. It does NOT create the serving endpoint.

### Job Definition

```yaml
# File: resources/agents/agent_setup_job.yml

resources:
  jobs:
    agent_setup_job:
      name: "[${bundle.target}] Health Monitor - Agent Setup"
      description: "Infrastructure + model registration (NO endpoint - handled by deployment job)"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      
      tasks:
        # Step 1: Create Unity Catalog schemas and tables
        - task_key: create_agent_infrastructure
          environment_key: default
          notebook_task:
            notebook_path: ../../src/agents/setup/create_schemas.py
            base_parameters:
              catalog: ${var.catalog}
              agent_schema: ${var.gold_schema}_agent
        
        # Step 2a: Register prompts to MLflow
        - task_key: register_prompts
          depends_on:
            - task_key: create_agent_infrastructure
          environment_key: default
          notebook_task:
            notebook_path: ../../src/agents/setup/register_prompts.py
        
        # Step 2b: Register scorers for production monitoring
        - task_key: register_scorers
          depends_on:
            - task_key: create_agent_infrastructure
          environment_key: default
          notebook_task:
            notebook_path: ../../src/agents/setup/register_scorers.py
        
        # Step 2c: Create evaluation datasets
        - task_key: create_evaluation_datasets
          depends_on:
            - task_key: create_agent_infrastructure
          environment_key: default
          notebook_task:
            notebook_path: ../../src/agents/setup/create_evaluation_dataset.py
        
        # Step 3: Log agent model to Unity Catalog
        - task_key: log_agent_model
          depends_on:
            - task_key: register_prompts
            - task_key: register_scorers
          environment_key: default
          notebook_task:
            notebook_path: ../../src/agents/setup/log_agent_model.py
            base_parameters:
              catalog: ${var.catalog}
              agent_schema: ${var.gold_schema}_agent
        
        # Step 4: Run initial evaluation (sanity check)
        - task_key: run_evaluation
          depends_on:
            - task_key: log_agent_model
            - task_key: create_evaluation_datasets
          environment_key: default
          notebook_task:
            notebook_path: ../../src/agents/setup/run_evaluation.py
        
        # ⚠️ NO ENDPOINT CREATION - Handled by agent_deployment_job
      
      tags:
        environment: ${bundle.target}
        project: databricks_health_monitor
        layer: agents
        job_type: setup
```

### Task Details

#### 1. create_schemas

```python
# File: src/agents/setup/create_schemas.py

def create_agent_schema(spark, catalog: str, schema: str):
    """Create Unity Catalog schema for agent."""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    
    # Create tables
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.inference_request_logs (
            request_id STRING,
            user_id STRING,
            query STRING,
            timestamp TIMESTAMP,
            thread_id STRING
        ) USING DELTA
    """)
    
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.inference_response_logs (
            request_id STRING,
            response STRING,
            confidence DOUBLE,
            domains ARRAY<STRING>,
            latency_ms DOUBLE,
            timestamp TIMESTAMP
        ) USING DELTA
    """)
    
    # Create volumes
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.runbooks")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.embeddings")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.artifacts")
```

#### 2. register_prompts

```python
# File: src/agents/setup/register_prompts.py

def register_all_prompts():
    """Register all agent prompts to MLflow."""
    mlflow.set_experiment(settings.mlflow_experiment_path)
    
    prompts = {
        "orchestrator_system": ORCHESTRATOR_SYSTEM_PROMPT,
        "intent_classifier": INTENT_CLASSIFIER_PROMPT,
        "response_synthesizer": SYNTHESIS_PROMPT,
        "cost_worker": COST_WORKER_PROMPT,
        # ... other prompts
    }
    
    with mlflow.start_run(run_name="prompt_registration"):
        mlflow.set_tag("run_type", settings.RUN_TYPE_PROMPTS)
        
        for name, content in prompts.items():
            # Log as artifact (mlflow.genai.log_prompt not available)
            with open(f"/tmp/{name}.txt", "w") as f:
                f.write(content)
            mlflow.log_artifact(f"/tmp/{name}.txt", "prompts")
            
        mlflow.log_param("prompt_count", len(prompts))
```

#### 3. log_agent_model

```python
# File: src/agents/setup/log_agent_model.py

def log_agent():
    """Log HealthMonitorAgent to Unity Catalog."""
    mlflow.set_experiment(settings.mlflow_experiment_path)
    
    with mlflow.start_run(run_name="health_monitor_agent_registration") as run:
        mlflow.set_tag("run_type", settings.RUN_TYPE_MODEL_LOGGING)
        
        # Create self-contained agent class
        # (Defined inline to avoid import issues in serving container)
        
        model_info = mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=HealthMonitorAgentWrapper(),
            registered_model_name=f"{catalog}.{schema}.health_monitor_agent",
            pip_requirements=[
                "mlflow>=3.3.2",
                "langchain>=0.3.0",
                "langgraph>=0.2.0",
                "databricks-agents>=0.16.0",
            ],
            resources=get_mlflow_resources(),
            signature=infer_signature(
                model_input=[{"role": "user", "content": "Sample query"}],
                model_output={"response": "Sample response"},
            ),
        )
        
        # Set aliases
        client = mlflow.MlflowClient(registry_uri="databricks-uc")
        client.set_registered_model_alias(
            name=f"{catalog}.{schema}.health_monitor_agent",
            alias="production",
            version=model_info.registered_model_version,
        )
        client.set_registered_model_alias(
            name=f"{catalog}.{schema}.health_monitor_agent",
            alias="staging",
            version=model_info.registered_model_version,
        )
        
        return model_info
```

#### 4. ~~create_serving_endpoint~~ → Now in Deployment Job

> ⚠️ **REMOVED:** Endpoint creation was moved to `deployment_job.py` following MLflow 3.0 pattern.
>
> **Why?** Endpoint should only be created/updated after evaluation passes.
> See [Deployment Job Script](#deployment-job-script) below for the endpoint creation code.

---

## 🔄 Deployment Job (agent_deployment_job)

### Purpose

The deployment job handles **evaluation-gated endpoint creation**. This is the MLflow 3.0 pattern where:

1. ✅ Load model from Unity Catalog
2. ✅ Run comprehensive evaluation with scorers
3. ✅ Check quality thresholds
4. **IF PASSED:** Promote model + CREATE/UPDATE serving endpoint
5. **IF FAILED:** No promotion, NO endpoint creation

### Job Definition

```yaml
# File: resources/agents/agent_deployment_job.yml

resources:
  jobs:
    agent_deployment_job:
      name: "[${bundle.target}] Health Monitor - Agent Deployment Job"
      description: "MLflow deployment job: evaluation → promotion → endpoint creation (if passed)"
      
      # Job parameters for MLflow deployment job integration
      parameters:
        - name: model_name
          default: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.health_monitor_agent
      
      environments:
        - environment_key: evaluation_env
          spec:
            environment_version: "4"
            dependencies:
              - mlflow>=3.3.2
              - pandas
              - databricks-agents>=0.16.0
      
      tasks:
        - task_key: deployment_job
          environment_key: evaluation_env
          notebook_task:
            notebook_path: ../../src/agents/setup/deployment_job.py
            base_parameters:
              model_name: "{{job.parameters.model_name}}"
              promotion_target: "production"
              relevance_threshold: "0.7"
              safety_threshold: "0.9"
      
      tags:
        environment: ${bundle.target}
        project: databricks_health_monitor
        job_type: deployment
```

### Deployment Job Script

```python
# File: src/agents/setup/deployment_job.py

# Databricks notebook source

# Widget parameters
dbutils.widgets.text("model_name", "")
dbutils.widgets.text("promotion_target", "staging")

MODEL_NAME = dbutils.widgets.get("model_name")
PROMOTION_TARGET = dbutils.widgets.get("promotion_target")

# ========== THRESHOLD CONFIGURATION ==========
# NOTE: guidelines/mean REMOVED - redundant with custom scorers
thresholds = {
    # Built-in MLflow judges
    "relevance/mean": 0.4,
    "safety/mean": 0.7,
    
    # Domain-specific LLM judges
    "cost_accuracy/mean": 0.6,
    "security_compliance/mean": 0.6,
    "reliability_accuracy/mean": 0.5,
    "performance_accuracy/mean": 0.6,
    "quality_accuracy/mean": 0.6,
    
    # Heuristic scorers
    "response_length/mean": 0.1,
    "no_errors/mean": 0.3,
    "databricks_context/mean": 0.1,
}

# Metric aliases to handle different naming conventions from MLflow
METRIC_ALIASES = {
    "relevance/mean": ["relevance/mean", "relevance_to_query/mean"],
    "databricks_context/mean": ["databricks_context/mean", "mentions_databricks_concepts/mean"],
    "cost_accuracy/mean": ["cost_accuracy/mean", "cost_accuracy_judge/mean"],
    # ... additional aliases
}

# COMMAND ----------

import mlflow
from mlflow.tracking.client import MlflowClient

# Set experiment
mlflow.set_experiment(settings.mlflow_experiment_path)

# Get model info
client = MlflowClient(registry_uri="databricks-uc")
model_info = client.get_registered_model(MODEL_NAME)

# Get latest version
versions = client.search_model_versions(f"name='{MODEL_NAME}'")
latest_version = max(v.version for v in versions)

print(f"Evaluating: {MODEL_NAME} v{latest_version}")

# COMMAND ----------

# Load model
model_uri = f"models:/{MODEL_NAME}/{latest_version}"
loaded_model = mlflow.pyfunc.load_model(model_uri)

# Create evaluation dataset
eval_data = create_evaluation_dataset()

print(f"Evaluation dataset: {len(eval_data)} samples")

# COMMAND ----------

# Run evaluation
scorers = [
    relevance_eval,
    safety_eval,
    correctness_eval,
    cost_accuracy_judge,
    security_compliance_judge,
]

def predict_fn(inputs):
    query = inputs.get("query", "")
    result = loaded_model.predict({"messages": [{"role": "user", "content": query}]})
    return {"response": result.get("content", str(result))}

with mlflow.start_run(run_name=f"deployment_v{latest_version}_{PROMOTION_TARGET}"):
    mlflow.set_tag("run_type", settings.RUN_TYPE_DEPLOYMENT)
    mlflow.log_param("model_name", MODEL_NAME)
    mlflow.log_param("model_version", latest_version)
    mlflow.log_param("promotion_target", PROMOTION_TARGET)
    
    results = mlflow.genai.evaluate(
        predict_fn=predict_fn,
        data=eval_data,
        scorers=scorers,
    )
    
    # Log metrics
    for metric, value in results.metrics.items():
        mlflow.log_metric(metric, value)

# COMMAND ----------

# Check thresholds
passed = True
failures = []

for metric, threshold in THRESHOLDS.items():
    score = results.metrics.get(f"eval_{metric}", 0.0)
    if score < threshold:
        passed = False
        failures.append(f"{metric}: {score:.2f} < {threshold}")
        print(f"❌ FAILED: {metric} = {score:.2f} (threshold: {threshold})")
    else:
        print(f"✓ PASSED: {metric} = {score:.2f} (threshold: {threshold})")

# COMMAND ----------

# Promote if passed AND create/update endpoint
if passed:
    print(f"\n✅ All thresholds passed! Promoting to @{PROMOTION_TARGET}")
    
    # Step 1: Promote model alias
    client.set_registered_model_alias(
        name=MODEL_NAME,
        alias=PROMOTION_TARGET,
        version=latest_version,
    )
    print(f"✓ Promoted {MODEL_NAME} v{latest_version} → @{PROMOTION_TARGET}")
    
    # Step 2: CREATE/UPDATE SERVING ENDPOINT (MLflow 3.0 pattern)
    print("\n🚀 Creating/updating serving endpoint...")
    create_or_update_endpoint(
        client=WorkspaceClient(),
        endpoint_name=ENDPOINT_NAME,
        model_name=MODEL_NAME,
        model_version=latest_version,
        catalog=CATALOG,
        schema=SCHEMA,
    )
    
    # Step 3: Wait for endpoint to be ready
    wait_for_endpoint_ready(ENDPOINT_NAME, timeout_minutes=30)
    print(f"✓ Endpoint {ENDPOINT_NAME} is READY")
    
else:
    print(f"\n❌ Evaluation failed. NOT promoting, NOT creating endpoint.")
    print(f"Failures: {failures}")

# COMMAND ----------

# Final status
dbutils.notebook.exit(json.dumps({
    "passed": passed,
    "promoted": passed,
    "endpoint_created": passed,  # Only created if passed
    "version": latest_version,
    "failures": failures,
    "metrics": results.metrics,
}))
```

---

## 🔗 Connecting Deployment Job to Model

### Why Connect?

Connecting a deployment job to a model enables:
- **Automatic triggering**: Deployment job runs when new model versions are created
- **Version tracking**: MLflow UI shows which job evaluates/promotes which model
- **Lineage**: Clear audit trail of model → evaluation → deployment
- **CI/CD integration**: Enables automated model deployment pipelines

**Reference:** [Connect the deployment job to a model using the MLflow client](https://docs.databricks.com/aws/en/mlflow/deployment-job#connect-the-deployment-job-to-a-model-using-the-mlflow-client)

### Prerequisites

1. **Model registered in Unity Catalog**: The model must exist before connecting
2. **Deployment job created**: The job must be deployed via Asset Bundle
3. **Job parameters configured**: Job must have `model_name` and `model_version` parameters

### Step 1: Find the Deployment Job ID

```bash
# List jobs and find the deployment job
databricks jobs list | grep "Agent Deployment"

# Example output:
# 667754679146345  [dev prashanth_subrahmanyam] [dev] Health Monitor - Agent Deployment
```

The job ID is `667754679146345` in this example.

### Step 2: Connect Using MLflow Client

```python
# File: src/agents/setup/connect_deployment_job.py

# Databricks notebook source
"""
Connect Deployment Job to Model

This script connects the MLflow deployment job to the registered model,
enabling automatic deployment workflows when new model versions are created.

Reference:
https://docs.databricks.com/aws/en/mlflow/deployment-job#connect-the-deployment-job-to-a-model-using-the-mlflow-client
"""

# COMMAND ----------

import mlflow
from mlflow.tracking.client import MlflowClient

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")
dbutils.widgets.text("job_id", "")  # Required: deployment job ID

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")
job_id = dbutils.widgets.get("job_id")

MODEL_NAME = f"{catalog}.{agent_schema}.health_monitor_agent"

if not job_id:
    raise ValueError("job_id parameter is required")

print(f"Model: {MODEL_NAME}")
print(f"Deployment Job ID: {job_id}")

# COMMAND ----------

def connect_deployment_job(model_name: str, job_id: str):
    """
    Connect an MLflow deployment job to a registered model.
    
    Args:
        model_name: Full Unity Catalog model name (catalog.schema.model)
        job_id: Databricks job ID for the deployment job
    """
    # Use Unity Catalog registry
    client = MlflowClient(registry_uri="databricks-uc")
    
    # Step 1: Verify model exists
    try:
        model = client.get_registered_model(model_name)
        print(f"✓ Found model: {model.name}")
        print(f"  Latest version: {model.latest_versions[-1].version if model.latest_versions else 'None'}")
    except Exception as e:
        raise ValueError(f"Model not found: {model_name}. Error: {e}")
    
    # Step 2: Connect deployment job to model
    print(f"\n🔗 Connecting deployment job {job_id} to model...")
    
    client.update_registered_model(
        name=model_name,
        deployment_job_id=job_id,
    )
    
    # Step 3: Verify connection
    updated_model = client.get_registered_model(model_name)
    
    print("\n" + "="*60)
    print("CONNECTION SUCCESSFUL")
    print("="*60)
    print(f"Model:              {updated_model.name}")
    print(f"Deployment Job ID:  {updated_model.deployment_job_id}")
    print(f"Deployment State:   {getattr(updated_model, 'deployment_job_state', 'N/A')}")
    print("="*60)
    
    return updated_model

# COMMAND ----------

# Execute connection
result = connect_deployment_job(MODEL_NAME, job_id)

print("\n✓ Deployment job is now connected to the model!")
print("\nNext steps:")
print("1. New model versions will trigger the deployment job automatically")
print("2. View in MLflow UI: Machine Learning → Models → health_monitor_agent → Deployment Job")

dbutils.notebook.exit("SUCCESS")
```

### Step 3: Verify in MLflow UI

1. Go to **Machine Learning** → **Models** 
2. Click on `health_monitor_agent`
3. Look for **Deployment Job** section
4. Should show the connected job with status

### Alternative: Connect via Databricks CLI

```bash
# Using databricks CLI (if available)
databricks registered-models update \
  --name "catalog.schema.health_monitor_agent" \
  --deployment-job-id "667754679146345"
```

### Job Parameter Requirements

For the deployment job to work correctly when triggered by model registration, it must have these parameters:

```yaml
# File: resources/agents/agent_deployment_job.yml

parameters:
  - name: model_name
    default: ${var.catalog}.${var.agent_schema}.health_monitor_agent
  - name: model_version
    default: ""  # Empty = latest version
  - name: promotion_target
    default: staging
```

When triggered automatically:
- `model_name` → Filled with registered model name
- `model_version` → Filled with the new version number

### Workflow After Connection

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUTOMATED WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. Developer logs new model version                           │
│      └── mlflow.pyfunc.log_model(..., registered_model_name=)   │
│                                                                 │
│   2. MLflow triggers connected deployment job                   │
│      └── job_id: 667754679146345                                │
│      └── model_version: <new_version>                           │
│                                                                 │
│   3. Deployment job runs                                        │
│      ├── Loads model version                                    │
│      ├── Runs evaluation with scorers                           │
│      ├── Checks thresholds                                      │
│      │                                                          │
│      ├── IF PASSED:                                             │
│      │   ├── Promotes to @production alias                      │
│      │   └── Creates/updates serving endpoint                   │
│      │                                                          │
│      └── IF FAILED:                                             │
│          └── Blocks deployment, notifies team                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Job not found | Wrong job ID | Use `databricks jobs list` to find correct ID |
| Permission denied | Insufficient access | Need MANAGE permission on model |
| Job doesn't trigger | Parameters missing | Ensure `model_name`, `model_version` params exist |
| Already connected | Different job connected | Update with new job ID to replace |

### Best Practices

1. **One job per model**: Each model should have its own deployment job
2. **Use staging first**: Connect to staging deployment job, then production
3. **Test manually first**: Run `agent_deployment_job` manually before connecting
4. **Monitor failures**: Set up alerts for deployment job failures

---

## 🚀 Deployment Commands

### Full Deployment

```bash
# 1. Deploy bundle (creates job definitions)
databricks bundle deploy -t dev

# 2. Run setup job (creates everything)
databricks bundle run -t dev agent_setup_job

# 3. Run deployment job (evaluate and promote)
databricks bundle run -t dev agent_deployment_job

# 4. Connect deployment job to model (one-time)
databricks bundle run -t dev connect_deployment_job
```

### Partial Updates

```bash
# Update model only
databricks bundle run -t dev agent_setup_job --task log_agent_model

# Run deployment job (evaluates → promotes → creates endpoint if passed)
databricks bundle run -t dev agent_deployment_job
```

---

## ⚠️ Serverless Compute Dependency Constraints

### The Problem

When running jobs on **serverless compute**, you may encounter dependency installation failures:

```
Library installation failed: Library installation attempted on serverless compute 
and failed. Unable to find or download the required package or its dependencies.
```

### Why This Happens

1. **Version constraints conflict**: Specifying exact versions (e.g., `langchain>=0.3.0`) may conflict with pre-installed packages
2. **Package not available**: Some packages aren't available in the serverless PyPI mirror
3. **Dependency resolution fails**: Complex dependency chains can't be satisfied

### Pre-Installed Packages on Databricks Runtime

These packages are **already available** on Databricks runtime and Model Serving:

| Package | Pre-installed? | Notes |
|---------|---------------|-------|
| `mlflow` | ✅ Yes | Core ML tracking |
| `langchain` | ✅ Yes | LangChain framework |
| `langchain-core` | ✅ Yes | LangChain core |
| `langchain-databricks` | ✅ Yes | Databricks integration (ChatDatabricks, GenieAgent) |
| `langgraph` | ✅ Yes | State machine orchestration |
| `databricks-sdk` | ✅ Yes | Databricks API client |
| `databricks-agents` | ✅ Yes | Agent framework utilities |

### ❌ Wrong: Version Constraints

```yaml
# agent_setup_job.yml
environments:
  - environment_key: agent_env
    spec:
      environment_version: "4"
      dependencies:
        - mlflow>=3.0.0              # ❌ Version constraint
        - langchain>=0.3.0           # ❌ May conflict
        - langchain-databricks>=0.2.0 # ❌ May not exist in serverless PyPI
```

**Error:**
```
Unable to find or download the required package or its dependencies
```

### ✅ Correct: No Version Constraints

```yaml
# agent_setup_job.yml
environments:
  - environment_key: agent_env
    spec:
      environment_version: "4"
      dependencies:
        - mlflow           # ✅ Uses pre-installed version
        - langchain        # ✅ Uses pre-installed version
        - langchain-core   # ✅ Uses pre-installed version
        - langgraph        # ✅ Uses pre-installed version
        - databricks-sdk   # ✅ Uses pre-installed version
```

### Environment Configuration by Task

| Task | Environment | Dependencies Needed |
|------|-------------|---------------------|
| `create_agent_infrastructure` | `sql_only` | None (SQL only) |
| `register_prompts` | `mlflow_env` | `mlflow` |
| `register_scorers` | `mlflow_env` | `mlflow` |
| `log_agent_model` | `agent_env` | `mlflow`, `langchain`, `langgraph`, etc. |
| `run_evaluation` | `mlflow_env` | `mlflow` |
| `create_evaluation_datasets` | `agents_env` | `databricks-agents`, `mlflow` |

### Model pip_requirements

The same rule applies to model logging:

```python
# log_agent_model.py
mlflow.pyfunc.log_model(
    artifact_path="agent",
    python_model=agent,
    pip_requirements=[
        # ✅ CORRECT: No version constraints
        "mlflow",
        "langchain",
        "langchain-core",
        "langchain-databricks",  # Required for ChatDatabricks
        "langgraph",
        "databricks-sdk",
        "databricks-agents",     # Required for GenieAgent
    ],
)
```

### When You DO Need Version Constraints

Only specify versions when:
1. **Testing a specific bug fix** in a newer version
2. **Security patch** requires minimum version
3. **Breaking change** in newer version you need to avoid

```yaml
# Only when absolutely necessary
dependencies:
  - my-package>=1.2.3  # Specific fix in 1.2.3
  - other-package<2.0  # Breaking change in 2.0
```

### Debugging Dependency Issues

```bash
# Check what versions are available on your cluster
%pip list | grep langchain

# Test installation locally first
pip install --dry-run langchain-databricks>=0.2.0

# Check serverless compute logs
databricks jobs get-run-output --run-id <run_id>
```

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] All Genie Spaces are configured
- [ ] LLM endpoint exists
- [ ] Lakebase instance is ready
- [ ] Unity Catalog schema exists
- [ ] SQL Warehouse is running

### Setup Job

- [ ] Schemas created successfully
- [ ] Tables created successfully
- [ ] Volumes created successfully
- [ ] Prompts registered to MLflow
- [ ] Model logged to Unity Catalog
- [ ] Model has `production` alias
- [ ] Serving endpoint created
- [ ] AI Gateway configured

### Deployment Job

- [ ] Evaluation dataset is comprehensive
- [ ] All scorers run successfully
- [ ] Threshold checks pass
- [ ] Model promoted to production
- [ ] Deployment job connected to model

### Post-Deployment

- [ ] Endpoint is healthy
- [ ] Test query succeeds
- [ ] Traces appear in MLflow
- [ ] Inference logs appear in UC tables

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Model not found | Log job didn't run | Run `agent_setup_job` |
| Endpoint creation fails | Missing permissions | Check UC grants |
| Evaluation fails | Import errors | Check pip requirements |
| Promotion fails | Threshold not met | Review metrics, adjust thresholds |
| Library installation failed | Version constraints | Remove version constraints (see above) |
| No module named 'langchain_databricks' | Missing pip requirement | Add `langchain-databricks` (no version) |
| Module not found in Model Serving | pip_requirements incomplete | Ensure all deps in `log_model()` |

### Evaluation-Specific Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Custom scorers return 0.0** | All `@scorer` functions show 0.0 | Use `_extract_response_text()` helper to handle serialized dict format from `mlflow.genai.evaluate()` |
| **Metadata type warning** | `Non-string values in metadata` | Cast numeric values to strings: `"query_length": str(len(query))` |
| **Guidelines blocking deployment** | `guidelines/mean: 0.000` fails | Remove from thresholds - redundant with custom scorers |
| **Metric name mismatch** | Threshold check can't find metric | Add metric name to `METRIC_ALIASES` dict |

### Serving Endpoint Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Agent/non-agent conflict** | `Agent endpoint cannot be updated to serve non-agent models` | Auto-handled: Deployment job deletes and recreates endpoint |
| **Endpoint not ready** | Stuck in `NOT_READY` state | Wait up to 15 minutes; check Serving Endpoints UI |
| **Permission denied** | `PERMISSION_DENIED` error | Check UC grants and service principal permissions |

### Agent Endpoint Recreation Pattern

When switching from non-agent to agent model, the endpoint must be recreated:

```python
# Automatic handling in create_or_update_serving_endpoint()
try:
    client.serving_endpoints.update_config(...)
except Exception as e:
    if "Agent endpoint cannot be updated" in str(e):
        # Delete existing non-agent endpoint
        client.serving_endpoints.delete(endpoint_name)
        time.sleep(5)
        # Create fresh agent endpoint
        client.serving_endpoints.create(...)
```

**Trigger condition:** First-time deployment of an agent model to an endpoint that previously served a non-agent model.

### Response Extraction Fix

`mlflow.genai.evaluate()` serializes `ResponsesAgentResponse` to dict:

```python
# MLflow passes this to scorers:
outputs = {
    'output': [{'content': [{'type': 'output_text', 'text': '...actual text...'}]}]
}

# Use _extract_response_text() to handle all formats:
def my_scorer(*, outputs=None, **kwargs):
    response = _extract_response_text(outputs)  # Works with both formats
    # ...
```

See [08-evaluation-and-quality.md](./08-evaluation-and-quality.md#-critical-response-extraction-for-mlflowgenaievaluate) for full implementation.

### Useful Commands

```bash
# Check job status
databricks jobs list | grep health_monitor

# Check endpoint status
databricks serving-endpoints get health_monitor_agent_dev

# View model in UC
databricks unity-catalog tables list --schema-name dev_prashanth_subrahmanyam_system_gold_agent
```

---

**← Back to:** [00-index.md](./00-index.md)

