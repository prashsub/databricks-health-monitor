# Archived ML Training Scripts

These scripts are **not currently used** in the ML training pipeline but are preserved for potential future use.

## Archived Date: January 3, 2026

## Why Archived?

These scripts were created but not included in the production ML training pipeline (`resources/ml/ml_training_pipeline.yml`). They represent:
- Alternative implementations of similar models
- Unique models that may be added in future phases
- Scripts that don't yet have feature tables or data to train on

## Scripts and Their Potential Use Cases

### Performance Domain

| Script | Problem Type | Potential Use Case | Similar Pipeline Model |
|--------|-------------|-------------------|----------------------|
| `train_cluster_efficiency_optimizer.py` | Regression | Optimize cluster resource efficiency | - |
| `train_cluster_sizing_recommender.py` | Classification | Recommend cluster sizes | `cluster_capacity_planner` |
| `train_query_performance_forecaster.py` | Regression | Forecast query performance | `query_forecaster` |
| `train_resource_rightsizer.py` | Regression | Right-size compute resources | `warehouse_optimizer` |

### Quality Domain

| Script | Problem Type | Potential Use Case | Similar Pipeline Model |
|--------|-------------|-------------------|----------------------|
| `train_schema_evolution_predictor.py` | Classification | Predict schema evolution patterns | `schema_change_predictor` |

### Reliability Domain

| Script | Problem Type | Potential Use Case | Similar Pipeline Model |
|--------|-------------|-------------------|----------------------|
| `train_dependency_impact_predictor.py` | Regression | Predict impact of job dependencies | - |
| `train_failure_root_cause_analyzer.py` | Multi-class Classification | Analyze failure root causes | - |
| `train_pipeline_health_classifier.py` | Multi-class Classification | Classify pipeline health states | `pipeline_health_scorer` |
| `train_recovery_time_predictor.py` | Regression | Predict recovery time after failures | - |

### Security Domain

| Script | Problem Type | Potential Use Case | Similar Pipeline Model |
|--------|-------------|-------------------|----------------------|
| `train_access_pattern_analyzer.py` | Classification | Analyze access patterns | - |
| `train_compliance_risk_classifier.py` | Classification | Classify compliance risks | - |
| `train_permission_recommender.py` | Classification | Recommend permission settings | - |

## How to Re-enable

To use any of these scripts:

1. Move the script back to its original domain folder:
   ```bash
   mv src/ml/_archive/train_<name>.py src/ml/<domain>/
   ```

2. Add a task to `resources/ml/ml_training_pipeline.yml`:
   ```yaml
   - task_key: train_<name>
     environment_key: ml_training
     notebook_task:
       notebook_path: ../../src/ml/<domain>/train_<name>.py
       base_parameters:
         catalog: ${var.catalog}
         gold_schema: ${var.gold_schema}
         feature_schema: ${var.feature_schema}
   ```

3. Add corresponding inference config to `src/ml/inference/batch_inference_all_models.py`

4. Ensure the required feature table exists in the feature schema

## Scripts Deleted (True Duplicates)

The following were **deleted** (not archived) because they were duplicates:

| Deleted Script | Kept Script | Reason |
|----------------|------------|--------|
| `quality/train_data_drift_detector.py` | `quality/train_drift_detector.py` | Same `MODEL_NAME = "data_drift_detector"` |
| `quality/train_tag_recommender.py` | `cost/train_tag_recommender.py` | Same model, different folder |
| `cost/train_cost_anomaly.py` | `cost/train_cost_anomaly_detector.py` | Old hardcoded version |
| `security/train_threat_detector.py` | `security/train_security_threat_detector.py` | Old hardcoded version |
| `reliability/train_failure_predictor.py` | `reliability/train_job_failure_predictor.py` | Old hardcoded version |
| `reliability/train_duration_forecaster.py` | `reliability/train_job_duration_forecaster.py` | Old hardcoded version |

