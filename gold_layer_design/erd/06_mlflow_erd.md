# MLflow Domain ERD

## Overview
ML experiment tracking and run metrics.

## Tables
- `dim_experiment` - Experiment definitions
- `fact_mlflow_runs` - Training run records
- `fact_mlflow_run_metrics_history` - Metric timeseries

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ dim_experiment : "workspace_id"
    dim_experiment ||--o{ fact_mlflow_runs : "workspace_id, experiment_id"
    fact_mlflow_runs ||--o{ fact_mlflow_run_metrics_history : "workspace_id, run_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    dim_experiment {
        STRING workspace_id PK
        STRING experiment_id PK
        STRING experiment_name
        STRING artifact_location
        STRING lifecycle_stage
        TIMESTAMP creation_time
        TIMESTAMP last_update_time
    }

    fact_mlflow_runs {
        STRING workspace_id PK
        STRING run_id PK
        STRING experiment_id FK
        STRING run_name
        STRING user_id
        STRING status
        TIMESTAMP start_time
        TIMESTAMP end_time
        STRING artifact_uri
    }

    fact_mlflow_run_metrics_history {
        STRING workspace_id PK
        STRING run_id FK
        STRING metric_key PK
        TIMESTAMP timestamp PK
        DOUBLE metric_value
        BIGINT step
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_experiment | fact_mlflow_runs | 1:N | workspace_id, experiment_id |
| fact_mlflow_runs | fact_mlflow_run_metrics_history | 1:N | workspace_id, run_id |

