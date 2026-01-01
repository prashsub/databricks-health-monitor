# 01 - Introduction

## Purpose

This documentation defines the architecture and implementation patterns for **Production Machine Learning on Databricks**. Using the Databricks Health Monitor as a reference implementation, it demonstrates how to build, deploy, and operate ML systems that follow industry best practices and Databricks-specific patterns.

The system includes **25 machine learning models** across **5 domains**, all built using Unity Catalog Feature Engineering for training/serving consistency and registered in Unity Catalog for governance.

## Dual Purpose

This documentation serves two distinct audiences:

### 1. Project Documentation
- Complete reference for the Databricks Health Monitor ML system
- Implementation details for all 25 models
- Operations and maintenance procedures
- Troubleshooting guides

### 2. Training Material
- Best practices for ML on Databricks
- Patterns applicable to any ML project
- Anti-patterns to avoid
- Step-by-step implementation guides

## Scope

### In Scope

| Component | Description |
|---|---|
| **Feature Engineering** | Unity Catalog Feature Engineering with FeatureLookup and create_training_set |
| **Model Training** | Scikit-learn, XGBoost, with MLflow tracking |
| **Model Registry** | Unity Catalog Model Registry for governance |
| **Batch Inference** | fe.score_batch() for automatic feature retrieval |
| **Orchestration** | Databricks Asset Bundles for job definition |
| **Monitoring** | Model quality metrics, drift detection |
| **Debugging** | Structured logging, error handling patterns |

### Out of Scope

| Component | Reason |
|---|---|
| Real-time inference | Focus on batch patterns (real-time covered in separate docs) |
| Deep learning | Focus on classical ML (PyTorch/TensorFlow covered separately) |
| AutoML | Focus on custom models (AutoML is a different pattern) |
| Feature serving | Focus on batch scoring (online serving covered separately) |

## Prerequisites

### Completed Components

The ML system requires the following components to be deployed:

| Component | Count | Status | Documentation |
|---|---|---|---|
| Gold Layer Tables | 37 | Required | [Gold Layer Design](../../gold_layer_design/) |
| Bronze Ingestion | - | Required | [Phase 1](../../plans/phase1-bronze-ingestion.md) |
| Silver Transformations | - | Required | [Silver Layer](../../src/pipelines/) |

### Infrastructure Requirements

| Requirement | Specification |
|---|---|
| Databricks Runtime | 15.4 LTS ML or higher |
| Unity Catalog | Enabled with catalog/schema permissions |
| MLflow | Version 3.0+ (mlflow>=3.0.0) |
| Python | 3.10+ |
| Serverless Compute | Enabled for jobs |

### Required Libraries

```python
# Core ML libraries (included in DBR ML)
scikit-learn>=1.3.0
xgboost>=2.0.0
pandas>=2.0.0
numpy>=1.24.0

# Databricks specific
databricks-feature-engineering  # Included in DBR
mlflow>=3.0.0

# Optional
matplotlib>=3.7.0  # For visualizations
seaborn>=0.12.0    # For visualizations
```

### Required Permissions

| Permission | Scope | Purpose |
|---|---|---|
| USE CATALOG | `${catalog}` | Access to data catalog |
| USE SCHEMA | `${gold_schema}` | Query Gold layer tables |
| USE SCHEMA | `${feature_schema}` | Create/read feature tables |
| CREATE TABLE | `${feature_schema}` | Create feature tables |
| CREATE MODEL | `${feature_schema}` | Register models |
| SELECT | Gold tables | Read training data |
| INSERT | Feature tables | Write features |
| INSERT | Prediction tables | Write predictions |

## Best Practices Matrix

This implementation showcases **14 of 14** Databricks ML Best Practices:

| # | Best Practice | Implementation | Document |
|---|---|---|---|
| 1 | **Unity Catalog Feature Engineering** | FeatureLookup + create_training_set for all models | [03-Feature Engineering](03-feature-engineering.md) |
| 2 | **Feature Table Design** | Primary keys, NOT NULL constraints, time-series features | [03-Feature Engineering](03-feature-engineering.md) |
| 3 | **MLflow Model Signatures** | Explicit input/output schemas for Unity Catalog | [04-Model Training](04-model-training.md) |
| 4 | **Label Type Casting** | DOUBLE for regression, INT for classification | [04-Model Training](04-model-training.md) |
| 5 | **Unity Catalog Model Registry** | Governance, versioning, lineage tracking | [05-Model Registry](05-model-registry.md) |
| 6 | **fe.log_model()** | Embeds feature lookup metadata with model | [04-Model Training](04-model-training.md) |
| 7 | **fe.score_batch()** | Automatic feature retrieval at inference | [06-Batch Inference](06-batch-inference.md) |
| 8 | **Serverless Compute** | Cost-efficient, auto-scaling for all jobs | [16-Implementation Guide](16-implementation-guide.md) |
| 9 | **MLflow Experiment Tracking** | Parameters, metrics, artifacts for all runs | [12-MLflow Experiments](12-mlflow-experiments.md) |
| 10 | **Structured Debug Logging** | Step-by-step progress, error context | [14-Debugging Guide](14-debugging-guide.md) |
| 11 | **Databricks Asset Bundles** | Infrastructure-as-code for all jobs | [16-Implementation Guide](16-implementation-guide.md) |
| 12 | **Column Name Mapping** | Explicit Gold → Feature table mappings | [03-Feature Engineering](03-feature-engineering.md) |
| 13 | **Model Quality Metrics** | Anomaly rate, F1, R², per model type | [13-Model Monitoring](13-model-monitoring.md) |
| 14 | **Retraining Strategy** | Schedule-based and metric-triggered | [13-Model Monitoring](13-model-monitoring.md) |

## ML System Overview

### Model Inventory

| Domain | Model Count | Model Types |
|---|:---:|---|
| 💰 **Cost** | 6 | Anomaly detection, regression, classification |
| 🔒 **Security** | 4 | Anomaly detection, classification |
| ⚡ **Performance** | 7 | Regression, anomaly detection, multi-label |
| 🔄 **Reliability** | 5 | Classification, regression |
| 📊 **Quality** | 3 | Anomaly detection, classification, regression |
| **Total** | **25** | |

### Algorithm Distribution

| Algorithm | Count | Use Cases |
|---|:---:|---|
| Isolation Forest | 6 | Anomaly detection (cost, security, quality) |
| Gradient Boosting Regressor | 8 | Time series forecasting |
| XGBoost Classifier | 6 | Binary/multi-class classification |
| Random Forest Classifier | 4 | Classification with interpretability |
| DummyClassifier | (fallback) | Imbalanced dataset handling |

### Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ML DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   GOLD LAYER                    FEATURE LAYER                TRAINING       │
│   (Source Tables)               (Feature Tables)             (Models)       │
│                                                                             │
│   ┌──────────────┐    ┌────────────────────────┐    ┌─────────────────┐    │
│   │ fact_usage   │    │ cost_features          │    │ 6 Cost Models   │    │
│   │ fact_audit   │───▶│ security_features      │───▶│ 4 Security      │    │
│   │ fact_query   │    │ performance_features   │    │ 7 Performance   │    │
│   │ fact_job_run │    │ reliability_features   │    │ 5 Reliability   │    │
│   │ info_schema  │    │ quality_features       │    │ 3 Quality       │    │
│   └──────────────┘    └────────────────────────┘    └─────────────────┘    │
│                                                              │               │
│                                                              ▼               │
│                       INFERENCE                       MODEL REGISTRY        │
│                       (Predictions)                   (Unity Catalog)       │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐ │
│   │ cost_anomaly_predictions, budget_forecast_predictions, ...           │ │
│   │ 25 prediction tables in ${catalog}.${feature_schema}                 │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Development Timeline

| Phase | Duration | Deliverables |
|---|---|---|
| 1. Feature Pipeline | 2-3 days | 5 feature tables with PKs |
| 2. First Model | 1 day | One model end-to-end |
| 3. All Models | 1-2 weeks | All 25 models trained |
| 4. Inference Pipeline | 2-3 days | Batch scoring for all models |
| 5. Monitoring Setup | 2-3 days | Quality metrics, alerts |
| 6. Production Deployment | 2-3 days | Scheduled jobs, validation |
| **Total** | **~4 weeks** | Production-ready ML system |

## Success Criteria

| Criteria | Target | Measurement |
|---|---|---|
| Models using Feature Engineering | 100% | All use FeatureLookup + fe.log_model |
| Models in Unity Catalog | 100% | All registered with signatures |
| Inference using fe.score_batch | 100% | Automatic feature retrieval |
| MLflow trace coverage | 100% | All training runs tracked |
| Model quality metrics | Defined | Per model type thresholds |
| Documentation coverage | 100% | All models documented |

## Key Concepts

### Unity Catalog Feature Engineering

**What**: A centralized feature store integrated with Unity Catalog for governance.

**Why**: 
- Training/serving consistency (same features in training and inference)
- Feature reuse across models
- Automatic feature retrieval at inference
- Full lineage tracking

**How**:
```python
# Training: Features are looked up from tables
feature_lookups = [FeatureLookup(table, features, lookup_key)]
training_set = fe.create_training_set(df, feature_lookups, label)
fe.log_model(model, training_set=training_set)

# Inference: Features are automatically retrieved
predictions = fe.score_batch(model_uri, df_with_keys_only)
```

### MLflow Model Signatures

**What**: Explicit input/output schema definitions for models.

**Why**:
- Required for Unity Catalog registration
- Enables input validation
- Documents model interface
- Supports model serving

**How**:
```python
from mlflow.models.signature import infer_signature

# Must cast label to DOUBLE/INT before training_set creation
base_df = spark.table(ft).select("pk", F.col("label").cast("double"))

# Infer signature from training data
signature = infer_signature(X_train, model.predict(X_train))

# Include in fe.log_model
fe.log_model(model, training_set=training_set, signature=signature)
```

### Databricks Asset Bundles

**What**: Infrastructure-as-code for Databricks resources.

**Why**:
- Version-controlled job definitions
- Environment management (dev/staging/prod)
- Reproducible deployments
- CI/CD integration

**How**:
```yaml
# resources/ml/ml_training_pipeline.yml
resources:
  jobs:
    ml_training_pipeline:
      name: "[${bundle.target}] ML Training Pipeline"
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      tasks:
        - task_key: train_cost_anomaly
          notebook_task:
            notebook_path: ../../src/ml/cost/train_cost_anomaly.py
```

## Document Conventions

### Code Examples

All code examples follow these conventions:

```python
# =============================================================================
# SECTION HEADER - Clear purpose statement
# =============================================================================

def function_name(
    param1: Type,
    param2: Type
) -> ReturnType:
    """
    Clear docstring explaining purpose.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    """
    # Step-by-step comments
    result = operation()
    
    # Debug logging
    print(f"✓ Operation completed: {result}")
    
    return result
```

### Configuration

All configuration uses:
- `dbutils.widgets.get()` for job parameters
- Environment variables for credentials
- Widget defaults for development

### Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Feature table | `{domain}_features` | `cost_features` |
| Model name | `{use_case}_{type}` | `cost_anomaly_detector` |
| Prediction table | `{model}_predictions` | `cost_anomaly_predictions` |
| Training script | `train_{model}.py` | `train_cost_anomaly.py` |
| Experiment | `/Shared/health_monitor_ml_{model}` | `/Shared/health_monitor_ml_cost_anomaly_detector` |

## Next Steps

1. **Read [02-Architecture Overview](02-architecture-overview.md)** to understand the system design
2. **Review [03-Feature Engineering](03-feature-engineering.md)** for the core data pattern
3. **Follow [16-Implementation Guide](16-implementation-guide.md)** for step-by-step setup

