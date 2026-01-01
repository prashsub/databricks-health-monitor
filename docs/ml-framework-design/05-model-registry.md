# 05 - Model Registry

## Overview

Unity Catalog Model Registry provides enterprise-grade model governance with:
- **Versioning**: Automatic version management for all models
- **Lineage**: Full tracking from data to predictions
- **Governance**: Access control, audit logging
- **Discovery**: Searchable model catalog
- **Staging**: Development, staging, production lifecycle

## Model Registration

### Automatic Registration via fe.log_model

When using Feature Engineering, models are automatically registered:

```python
from databricks.feature_engineering import FeatureEngineeringClient
import mlflow

fe = FeatureEngineeringClient()
mlflow.set_registry_uri("databricks-uc")

# This registers the model in Unity Catalog
fe.log_model(
    model=trained_model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,
    registered_model_name=f"{catalog}.{schema}.{model_name}",  # UC path
    signature=signature,
    input_example=input_example
)
```

### Model Naming Convention

```
{catalog}.{schema}.{model_name}

Examples:
prashanth_catalog.gold_features.cost_anomaly_detector
prashanth_catalog.gold_features.budget_forecaster
prashanth_catalog.gold_features.failure_predictor
```

### Registration Requirements

| Requirement | Description |
|---|---|
| **Signature** | Must include both input and output schemas |
| **Input Example** | Required for signature inference |
| **Catalog Permissions** | CREATE MODEL permission required |
| **Unique Name** | Model name must be unique within schema |

## Model Versioning

### Automatic Version Increment

Each `fe.log_model()` or `mlflow.register_model()` call creates a new version:

```
cost_anomaly_detector
├── Version 1 (2025-12-01)
├── Version 2 (2025-12-15)
├── Version 3 (2026-01-01)  ← Latest
```

### Querying Model Versions

```python
from mlflow import MlflowClient

client = MlflowClient()
model_name = f"{catalog}.{schema}.{model_name}"

# Get all versions
versions = client.search_model_versions(f"name='{model_name}'")

for v in versions:
    print(f"Version {v.version}")
    print(f"  Created: {v.creation_timestamp}")
    print(f"  Run ID: {v.run_id}")
    print(f"  Status: {v.status}")
```

### Getting Latest Version

```python
def get_latest_model_version(model_name: str) -> int:
    """Get the latest version number for a model."""
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    
    if not versions:
        raise ValueError(f"No versions found for {model_name}")
    
    return max(int(v.version) for v in versions)

# Usage
latest = get_latest_model_version(f"{catalog}.{schema}.cost_anomaly_detector")
model_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector/{latest}"
```

## Model Aliases

### Setting Aliases

Aliases provide stable references to specific versions:

```python
client = MlflowClient()
model_name = f"{catalog}.{schema}.cost_anomaly_detector"

# Set alias for current production version
client.set_registered_model_alias(
    name=model_name,
    alias="Production",
    version=3
)

# Set alias for champion model
client.set_registered_model_alias(
    name=model_name,
    alias="Champion",
    version=3
)
```

### Using Aliases

```python
# Load by alias instead of version number
model_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector@Production"
model = mlflow.pyfunc.load_model(model_uri)
```

### Common Aliases

| Alias | Purpose |
|---|---|
| `Production` | Currently deployed model |
| `Champion` | Best-performing model |
| `Challenger` | Candidate for A/B testing |
| `Latest` | Most recent version (auto) |

## Model Lineage

### Viewing Lineage in UI

1. Navigate to **Data** → **Models**
2. Select your model
3. Click **Lineage** tab

### Lineage Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MODEL LINEAGE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCE DATA                FEATURE TABLE               MODEL                │
│  ┌───────────┐             ┌───────────────┐           ┌──────────────┐    │
│  │fact_usage │────────────▶│ cost_features │──────────▶│cost_anomaly_ │    │
│  │           │  transform  │               │  training │ detector     │    │
│  └───────────┘             └───────────────┘           └──────────────┘    │
│                                                              │              │
│                                                              │ inference    │
│                                                              ▼              │
│                                              ┌─────────────────────────┐   │
│                                              │ cost_anomaly_predictions│   │
│                                              └─────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Programmatic Lineage

```python
# Get lineage information from model
model_info = client.get_model_version(model_name, version)

# Feature Engineering metadata is stored in the model
# and automatically creates lineage to feature tables
```

## Model Metadata

### Description and Tags

```python
from mlflow import MlflowClient

client = MlflowClient()
model_name = f"{catalog}.{schema}.cost_anomaly_detector"

# Update model description
client.update_registered_model(
    name=model_name,
    description="""
    Cost Anomaly Detector
    
    Purpose: Detect unusual spending patterns in Databricks usage
    Algorithm: Isolation Forest (unsupervised)
    Features: Daily DBU, cost trends, z-scores
    Output: Anomaly score (-1 to 1) and is_anomaly flag
    
    Usage:
    - is_anomaly = 1 indicates unusual pattern
    - Lower anomaly_score = more anomalous
    """
)

# Set model tags
client.set_registered_model_tag(
    name=model_name,
    key="domain",
    value="cost"
)

client.set_registered_model_tag(
    name=model_name,
    key="model_type",
    value="anomaly_detection"
)

client.set_registered_model_tag(
    name=model_name,
    key="algorithm",
    value="isolation_forest"
)
```

### Version Description

```python
client.update_model_version(
    name=model_name,
    version=3,
    description="Retrained with 30-day lookback features. Improved anomaly rate from 8% to 5%."
)
```

## Permissions

### Required Permissions

| Action | Required Permission |
|---|---|
| Create model | CREATE MODEL on schema |
| Read model | USE MODEL on model |
| Update model | USE MODEL on model |
| Delete model | Owner or admin |
| Load for inference | USE MODEL on model |

### Granting Permissions

```sql
-- Grant permission to create models
GRANT CREATE MODEL ON SCHEMA catalog.schema TO `user@company.com`;

-- Grant permission to use a specific model
GRANT USE MODEL ON MODEL catalog.schema.model_name TO `group_name`;

-- Grant permission to use all models in schema
GRANT USE MODEL ON SCHEMA catalog.schema TO `group_name`;
```

## Model Comparison

### Comparing Versions

```python
from mlflow import MlflowClient

client = MlflowClient()
model_name = f"{catalog}.{schema}.cost_anomaly_detector"

# Get runs for different versions
version_1 = client.get_model_version(model_name, "1")
version_3 = client.get_model_version(model_name, "3")

# Get metrics from runs
run_1 = client.get_run(version_1.run_id)
run_3 = client.get_run(version_3.run_id)

print("Version Comparison:")
print("-" * 60)
print(f"{'Metric':<25} {'Version 1':<15} {'Version 3':<15}")
print("-" * 60)

metrics_1 = run_1.data.metrics
metrics_3 = run_3.data.metrics

for metric in metrics_1:
    v1 = metrics_1.get(metric, "N/A")
    v3 = metrics_3.get(metric, "N/A")
    print(f"{metric:<25} {v1:<15.4f} {v3:<15.4f}")
```

### A/B Testing Setup

```python
# Register challenger model
fe.log_model(
    model=new_model,
    artifact_path="model",
    flavor=mlflow.sklearn,
    training_set=training_set,
    registered_model_name=f"{catalog}.{schema}.cost_anomaly_detector",
    signature=signature,
    input_example=input_example
)

# Get new version number
new_version = get_latest_model_version(f"{catalog}.{schema}.cost_anomaly_detector")

# Set as challenger
client.set_registered_model_alias(
    name=f"{catalog}.{schema}.cost_anomaly_detector",
    alias="Challenger",
    version=new_version
)

# Compare in inference
champion_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector@Champion"
challenger_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector@Challenger"

champion_preds = fe.score_batch(model_uri=champion_uri, df=scoring_df)
challenger_preds = fe.score_batch(model_uri=challenger_uri, df=scoring_df)
```

## Model Loading

### Load Latest Version

```python
import mlflow

model_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector"
model = mlflow.pyfunc.load_model(model_uri)
```

### Load Specific Version

```python
model_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector/3"
model = mlflow.pyfunc.load_model(model_uri)
```

### Load by Alias

```python
model_uri = f"models:/{catalog}.{schema}.cost_anomaly_detector@Production"
model = mlflow.pyfunc.load_model(model_uri)
```

### Load with Feature Engineering

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# This uses the embedded feature lookup metadata
predictions = fe.score_batch(
    model_uri=f"models:/{catalog}.{schema}.cost_anomaly_detector",
    df=scoring_df  # Only needs lookup keys!
)
```

## Model Archival

### Archiving Old Versions

```python
client = MlflowClient()
model_name = f"{catalog}.{schema}.cost_anomaly_detector"

# Archive versions older than 30 days
import datetime

versions = client.search_model_versions(f"name='{model_name}'")
cutoff = datetime.datetime.now() - datetime.timedelta(days=30)

for v in versions:
    created = datetime.datetime.fromtimestamp(v.creation_timestamp / 1000)
    if created < cutoff and v.version != get_latest_model_version(model_name):
        client.transition_model_version_stage(
            name=model_name,
            version=v.version,
            stage="Archived"
        )
        print(f"Archived version {v.version}")
```

### Deleting Models

```python
# Delete a specific version (careful!)
client.delete_model_version(
    name=model_name,
    version="1"
)

# Delete entire model (very careful!)
client.delete_registered_model(name=model_name)
```

## Unity Catalog UI Navigation

### Finding Models

1. Navigate to **Data** tab
2. Select **Models** in left sidebar
3. Browse to `{catalog} > {schema} > {model_name}`

### Model Details Page

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Model: prashanth_catalog.gold_features.cost_anomaly_detector               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ [Overview] [Lineage] [Permissions] [Tags]                                  │
│                                                                             │
│ DESCRIPTION                                                                 │
│ Cost Anomaly Detector - Detects unusual spending patterns                  │
│                                                                             │
│ ALIASES                                                                     │
│ • Production → Version 3                                                    │
│ • Champion → Version 3                                                      │
│                                                                             │
│ VERSIONS                                                                    │
│ ┌──────────┬────────────────┬────────────┬───────────────────────────────┐ │
│ │ Version  │ Created        │ Run ID     │ Description                   │ │
│ ├──────────┼────────────────┼────────────┼───────────────────────────────┤ │
│ │ 3        │ Jan 1, 2026    │ abc123...  │ Retrained with 30-day...     │ │
│ │ 2        │ Dec 15, 2025   │ def456...  │ Added z-score features       │ │
│ │ 1        │ Dec 1, 2025    │ ghi789...  │ Initial version              │ │
│ └──────────┴────────────────┴────────────┴───────────────────────────────┘ │
│                                                                             │
│ SIGNATURE                                                                   │
│ Inputs:                                                                     │
│   daily_dbu: double                                                         │
│   daily_cost: double                                                        │
│   avg_dbu_7d: double                                                        │
│   ...                                                                       │
│ Outputs:                                                                    │
│   prediction: double                                                        │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

## Best Practices

### Model Registration

| Practice | Description |
|---|---|
| Always include signature | Required for UC, enables validation |
| Use consistent naming | `{domain}_{use_case}_{type}` |
| Add descriptions | Document purpose, algorithm, usage |
| Tag with metadata | domain, algorithm, model_type |
| Version descriptions | Document changes between versions |

### Model Lifecycle

| Stage | Action |
|---|---|
| **Development** | Train and iterate locally |
| **Staging** | Register, validate signature |
| **Production** | Set Production alias |
| **Archival** | Archive old versions after 30 days |

### Governance

| Practice | Description |
|---|---|
| Restrict CREATE MODEL | Only ML engineers |
| Grant USE MODEL | To inference pipelines |
| Audit model access | Via Unity Catalog logs |
| Document lineage | Automatic via FE |

## Validation Checklist

### Registration
- [ ] Model has input AND output signature
- [ ] Model name follows convention
- [ ] Model has description
- [ ] Model has tags (domain, algorithm, type)
- [ ] Version has description

### Permissions
- [ ] CREATE MODEL granted to ML team
- [ ] USE MODEL granted to inference jobs
- [ ] USE MODEL granted to dashboards

### Lifecycle
- [ ] Production alias set
- [ ] Old versions archived
- [ ] Version history documented

## Next Steps

- **[06-Batch Inference](06-batch-inference.md)**: Using registered models
- **[12-MLflow Experiments](12-mlflow-experiments.md)**: Experiment tracking
- **[13-Model Monitoring](13-model-monitoring.md)**: Production monitoring

