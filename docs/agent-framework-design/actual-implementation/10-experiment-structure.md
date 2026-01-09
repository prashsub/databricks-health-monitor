# MLflow Experiment Structure

## Overview

The Health Monitor Agent uses three separate MLflow experiments for clean organization:

| Experiment | Path | Purpose |
|------------|------|---------|
| **Development** | `/Shared/health_monitor_agent_development` | Model logging, registration |
| **Evaluation** | `/Shared/health_monitor_agent_evaluation` | Agent evaluation runs |
| **Deployment** | `/Shared/health_monitor_agent_deployment` | Pre-deployment validation |

## Why Separate Experiments?

### Before (Single Experiment)
```
/Shared/health_monitor/agent
├── run: create_evaluation_dataset (dataset_creation)
├── run: prompt_registration (prompt_registry)
├── run: agent_registration_v1 (model_logging)
├── run: agent_evaluation (evaluation)
├── run: deployment_v2_staging (deployment)
└── ... mixed activities, hard to compare
```

**Problems:**
- Dataset creation and prompt registration clutter the experiment
- Different activities have different metrics, making comparison hard
- No clear separation between development, testing, and deployment

### After (Separate Experiments)
```
/Shared/health_monitor_agent_development
├── run: dev_model_registration_20260107_1430 (model_logging)
└── ... model development runs only

/Shared/health_monitor_agent_evaluation
├── run: eval_cost_20260107_1445 (evaluation)
├── run: eval_comprehensive_20260107_1500 (evaluation)
└── ... evaluation runs only (comparable metrics)

/Shared/health_monitor_agent_deployment
├── run: pre_deploy_validation_20260107_1530 (deployment)
└── ... deployment validation runs only
```

**Benefits:**
- Clean separation of concerns
- Evaluation runs are directly comparable
- No clutter from data prep or config management
- Clear audit trail per activity type

## Run Naming Conventions

### Development Experiment
```python
# Pattern: dev_{feature}_{timestamp}
run_name = f"dev_model_registration_{timestamp}"
run_name = f"dev_feature_test_{timestamp}"
```

### Evaluation Experiment
```python
# Pattern: eval_{domain}_{timestamp}
run_name = f"eval_cost_{timestamp}"
run_name = f"eval_comprehensive_{timestamp}"
run_name = f"eval_pipeline_{timestamp}"
```

### Deployment Experiment
```python
# Pattern: pre_deploy_validation_{timestamp}
run_name = f"pre_deploy_validation_{timestamp}"
```

## Standard Tags

**Every run must include these tags for filtering:**

```python
mlflow.set_tags({
    "domain": "<cost|security|performance|reliability|quality|all>",
    "agent_version": "v4.0",
    "dataset_type": "<synthetic|manual|evaluation|none>",
    "evaluation_type": "<comprehensive|domain_specific|smoke|regression|none>",
})
```

### Tag Values by Run Type

| Run Type | domain | dataset_type | evaluation_type |
|----------|--------|--------------|-----------------|
| Model logging | all | none | none |
| Evaluation (full) | all | evaluation | comprehensive |
| Evaluation (domain) | cost/security/etc | evaluation | domain_specific |
| Deployment validation | all | evaluation | pre_deploy_validation |

## What Is NOT Logged as Runs

The following activities **do not create MLflow runs**:

1. **Dataset Creation** (`create_evaluation_dataset.py`)
   - Datasets are saved to Unity Catalog
   - Referenced in evaluation runs via `mlflow.log_input()`
   
2. **Prompt Registration** (`register_prompts.py`)
   - Prompts go to MLflow Prompt Registry
   - This is configuration management, not experimentation

3. **Scorer Registration** (`register_scorers.py`)
   - Scorers are registered for use in evaluation
   - No experimental activity occurs

## Code Examples

### Dataset Creation (No Run)
```python
# ❌ Old pattern - Don't do this
with mlflow.start_run(run_name="create_evaluation_dataset"):
    mlflow.set_tag("run_type", "dataset_creation")
    mlflow_dataset = mlflow.data.from_pandas(df)
    mlflow.log_input(mlflow_dataset)

# ✅ New pattern - Just create the dataset
mlflow_dataset = mlflow.data.from_pandas(df, name="eval_dataset")
# Dataset will be linked to evaluation runs later
```

### Evaluation Run (With Dataset Reference)
```python
mlflow.set_experiment("/Shared/health_monitor_agent_evaluation")

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
run_name = f"eval_{domain}_{timestamp}"

with mlflow.start_run(run_name=run_name):
    # Standard tags
    mlflow.set_tags({
        "domain": domain,
        "agent_version": "v4.0",
        "dataset_type": "evaluation",
        "evaluation_type": "domain_specific",
    })
    
    # Link dataset to this run
    mlflow.log_input(eval_dataset, context="eval")
    
    # Run evaluation
    results = mlflow.genai.evaluate(
        model=agent,
        data=eval_df,
        scorers=scorers,
    )
```

### Model Logging Run
```python
mlflow.set_experiment("/Shared/health_monitor_agent_development")

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
run_name = f"dev_model_registration_{timestamp}"

with mlflow.start_run(run_name=run_name):
    mlflow.set_tags({
        "run_type": "model_logging",
        "domain": "all",
        "agent_version": "v4.0",
        "dataset_type": "none",
        "evaluation_type": "none",
    })
    
    logged_model = mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=agent,
        registered_model_name=model_name,
    )
```

### Deployment Validation Run
```python
mlflow.set_experiment("/Shared/health_monitor_agent_deployment")

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
run_name = f"pre_deploy_validation_{timestamp}"

with mlflow.start_run(run_name=run_name):
    mlflow.set_tags({
        "run_type": "deployment",
        "evaluation_type": "pre_deploy_validation",
        "agent_version": f"v{version}",
        "domain": "all",
        "dataset_type": "evaluation",
    })
    
    # Log deployment parameters
    mlflow.log_params({
        "model_version": version,
        "promotion_target": "staging",
        "evaluation_passed": True,
    })
```

## Accessing Experiments

### From Code
```python
from agents import (
    EXPERIMENT_DEVELOPMENT,
    EXPERIMENT_EVALUATION,
    EXPERIMENT_DEPLOYMENT,
)

# Set the appropriate experiment
mlflow.set_experiment(EXPERIMENT_EVALUATION)
```

### Constants
```python
EXPERIMENT_DEVELOPMENT = "/Shared/health_monitor_agent_development"
EXPERIMENT_EVALUATION = "/Shared/health_monitor_agent_evaluation"
EXPERIMENT_DEPLOYMENT = "/Shared/health_monitor_agent_deployment"
```

## Validation Checklist

After implementation, verify:

- [ ] Three experiments exist in `/Shared/` directory
- [ ] No dataset creation runs appear in experiments
- [ ] No prompt registration runs appear in experiments
- [ ] All evaluation runs use naming: `eval_{domain}_{timestamp}`
- [ ] All runs have proper tags (domain, agent_version, dataset_type, evaluation_type)
- [ ] Each evaluation run references its dataset via `mlflow.log_input()`
- [ ] Deployment experiment only contains pre-deployment validation runs
- [ ] Model logging runs are in development experiment only

## Migration Notes

### Files Updated
- `src/agents/__init__.py` - New experiment constants
- `src/agents/setup/deployment_job.py` - Uses EVALUATION + DEPLOYMENT experiments
- `src/agents/setup/log_agent_model.py` - Uses DEVELOPMENT experiment
- `src/agents/setup/create_evaluation_dataset.py` - No longer creates runs
- `src/agents/setup/register_prompts.py` - No longer creates runs
- `src/agents/evaluation/evaluator.py` - Uses EVALUATION experiment
- `src/agents/evaluation/runner.py` - Uses EVALUATION experiment
- `src/agents/notebooks/*.py` - Updated experiment paths
- `src/agents/orchestrator/agent.py` - Uses DEVELOPMENT experiment

### Backward Compatibility
The old experiment `/Shared/health_monitor/agent` still exists with historical runs.
New runs will go to the appropriate new experiment based on activity type.


