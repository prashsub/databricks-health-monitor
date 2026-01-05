# Job Architecture: Hierarchical Job Structure

## Overview

The Databricks Health Monitor uses a **3-layer hierarchical job architecture** that ensures:
- ✅ No notebooks are repeated across jobs
- ✅ Atomic job layers for independent testing and monitoring
- ✅ Clear dependency chains via `run_job_task` references
- ✅ Single source of truth for each functionality

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        LAYER 3: MASTER ORCHESTRATORS                          │
├──────────────────────────────────────────────────────────────────────────────┤
│  master_setup_orchestrator                master_refresh_orchestrator         │
│  (One-time setup)                         (Daily refresh)                     │
│         │                                         │                           │
│         ▼                                         ▼                           │
│  ┌─────────────┐                          ┌─────────────┐                    │
│  │ bronze_setup│                          │bronze_refresh│                    │
│  └──────┬──────┘                          └──────┬──────┘                    │
│         ▼                                         ▼                           │
│  ┌─────────────┐                          ┌─────────────┐                    │
│  │ gold_setup  │                          │ gold_merge  │                    │
│  └──────┬──────┘                          └──────┬──────┘                    │
│         │                                         │                           │
│    ┌────┴────┬────────────┐              ┌───────┴────────┐                  │
│    ▼         ▼            ▼              ▼                ▼                  │
│ semantic  monitoring   ml_layer    monitoring_ref   ml_inference             │
│  _setup    _setup      _setup         resh                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        LAYER 2: COMPOSITE JOBS                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  semantic_layer_setup_job        monitoring_layer_setup_job                  │
│         │                                │                                   │
│    ┌────┴────┐                          │                                   │
│    ▼         ▼                          ▼                                   │
│  tvf_job  metric_view_job      lakehouse_monitoring_setup_job                │
│                                                                              │
│  ml_layer_setup_job              monitoring_layer_refresh_job                │
│         │                                │                                   │
│    ┌────┴────┐                          ▼                                   │
│    ▼         ▼               lakehouse_monitoring_refresh_job                │
│ feature_job  training_job                                                    │
│                                                                              │
│  ml_layer_inference_job                                                      │
│         │                                                                    │
│         ▼                                                                    │
│   ml_inference_pipeline                                                      │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        LAYER 1: ATOMIC JOBS                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Bronze Layer:          Gold Layer:           Semantic Layer:                │
│  - bronze_setup_job     - gold_setup_job      - tvf_deployment_job           │
│  - bronze_refresh_job   - gold_merge_job      - metric_view_deployment_job   │
│                         - gold_backfill_job                                  │
│                                                                              │
│  Monitoring:                       ML:                                       │
│  - lakehouse_monitoring_setup_job  - ml_feature_pipeline                     │
│  - lakehouse_monitoring_refresh_job- ml_training_pipeline                    │
│                                    - ml_inference_pipeline                   │
│                                                                              │
│  Each atomic job runs ONE notebook (or small set of related notebooks)       │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Job Hierarchy

### Layer 3: Master Orchestrators

| Job | Purpose | References |
|-----|---------|------------|
| `master_setup_orchestrator` | Complete infrastructure setup | Bronze → Gold → Semantic → Monitoring → ML |
| `master_refresh_orchestrator` | Daily data pipeline | Bronze → Gold → Monitoring Refresh → ML Inference |

### Layer 2: Composite Jobs

| Job | Purpose | References |
|-----|---------|------------|
| `semantic_layer_setup_job` | Deploy all semantic assets | TVF + Metric View jobs |
| `monitoring_layer_setup_job` | Setup monitoring | Lakehouse Monitoring Setup job |
| `monitoring_layer_refresh_job` | Refresh monitors | Lakehouse Monitoring Refresh job |
| `ml_layer_setup_job` | Train ML models | Feature + Training jobs |
| `ml_layer_inference_job` | Run ML predictions | ML Inference job |

### Layer 1: Atomic Jobs

| Job | Purpose | Notebook(s) |
|-----|---------|-------------|
| `tvf_deployment_job` | Deploy 60 TVFs | `deploy_tvfs.py` |
| `metric_view_deployment_job` | Deploy 10 metric views | `deploy_metric_views.py` |
| `lakehouse_monitoring_setup_job` | Create 8 monitors | Monitor notebooks |
| `lakehouse_monitoring_refresh_job` | Refresh monitors | `refresh_monitors.py` |
| `ml_feature_pipeline` | Create feature tables | `create_feature_tables.py` |
| `ml_training_pipeline` | Train models | Training notebooks |
| `ml_inference_pipeline` | Run inference | `batch_inference_all_models.py` |

## Key Principles

### 1. No Notebook Duplication
Each notebook appears in **exactly ONE atomic job**. Higher-level jobs reference lower-level jobs via `run_job_task`.

### 2. Job References Pattern
```yaml
# ✅ CORRECT: Reference another job
tasks:
  - task_key: deploy_tvfs
    run_job_task:
      job_id: ${resources.jobs.tvf_deployment_job.id}

# ❌ WRONG: Duplicate notebook in multiple jobs
tasks:
  - task_key: deploy_tvfs
    notebook_task:
      notebook_path: ../src/semantic/tvfs/deploy_tvfs.py  # Don't duplicate!
```

### 3. Atomic Testing
Each layer can be tested independently:
```bash
# Test atomic job
databricks bundle run -t dev tvf_deployment_job

# Test composite job (includes atomic jobs)
databricks bundle run -t dev semantic_layer_setup_job

# Test full orchestrator
databricks bundle run -t dev master_setup_orchestrator
```

### 4. Clear Ownership
- **Layer 1**: Owned by feature teams (Bronze team, Gold team, etc.)
- **Layer 2**: Owned by domain leads (Semantic layer owner, ML owner)
- **Layer 3**: Owned by platform team (orchestration)

## Usage

### Initial Setup (Run Once)
```bash
# Complete setup
databricks bundle run -t dev master_setup_orchestrator

# Or step-by-step:
databricks bundle run -t dev bronze_setup_job
databricks bundle run -t dev gold_setup_job
databricks bundle run -t dev semantic_layer_setup_job
databricks bundle run -t dev monitoring_layer_setup_job
databricks bundle run -t dev ml_layer_setup_job
```

### Daily Refresh (Scheduled)
```bash
# Enable schedule
# Edit master_refresh_orchestrator.yml: pause_status: UNPAUSED

# Or manual run:
databricks bundle run -t dev master_refresh_orchestrator
```

### Testing Individual Components
```bash
# Test TVFs only
databricks bundle run -t dev tvf_deployment_job

# Test Metric Views only
databricks bundle run -t dev metric_view_deployment_job

# Test Monitoring Setup only
databricks bundle run -t dev lakehouse_monitoring_setup_job
```

## Benefits

1. **Modularity**: Change one job without affecting others
2. **Debugging**: Isolate failures to specific atomic jobs
3. **Monitoring**: Track success/failure at granular level
4. **Flexibility**: Run any subset of the pipeline
5. **Maintainability**: Clear ownership and responsibility
6. **Scalability**: Add new jobs without restructuring

## Related Files

- `resources/orchestrators/master_setup_orchestrator.yml`
- `resources/orchestrators/master_refresh_orchestrator.yml`
- `resources/semantic/semantic_layer_setup_job.yml`
- `resources/monitoring/monitoring_layer_setup_job.yml`
- `resources/monitoring/monitoring_layer_refresh_job.yml`
- `resources/ml/ml_layer_setup_job.yml`
- `resources/ml/ml_layer_inference_job.yml`





