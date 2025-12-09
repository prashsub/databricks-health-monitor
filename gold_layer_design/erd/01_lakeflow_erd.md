# Lakeflow Domain ERD

## Overview
Job and pipeline orchestration tracking.

## Tables
- `dim_job` - Job definitions
- `dim_job_task` - Task definitions within jobs
- `dim_pipeline` - DLT pipeline metadata
- `fact_job_run_timeline` - Job execution metrics
- `fact_job_task_run_timeline` - Task-level execution
- `fact_pipeline_update_timeline` - Pipeline update events

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ dim_job : "workspace_id"
    dim_workspace ||--o{ dim_pipeline : "workspace_id"
    dim_job ||--o{ dim_job_task : "workspace_id, job_id"
    dim_job ||--o{ fact_job_run_timeline : "workspace_id, job_id"
    dim_job_task ||--o{ fact_job_task_run_timeline : "workspace_id, job_id, task_key"
    dim_pipeline ||--o{ fact_pipeline_update_timeline : "workspace_id, pipeline_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    dim_job {
        STRING workspace_id PK
        STRING job_id PK
        STRING job_name
        STRING creator_user_name
        TIMESTAMP create_time
        STRING run_as_user_name
    }

    dim_job_task {
        STRING workspace_id PK
        STRING job_id PK
        STRING task_key PK
        STRING task_type
        STRING notebook_path
    }

    dim_pipeline {
        STRING workspace_id PK
        STRING pipeline_id PK
        STRING pipeline_name
        STRING pipeline_type
        STRING creator_user_name
    }

    fact_job_run_timeline {
        STRING workspace_id PK
        STRING run_id PK
        STRING job_id FK
        TIMESTAMP period_start_time
        TIMESTAMP period_end_time
        STRING result_state
        STRING trigger_type
    }

    fact_job_task_run_timeline {
        STRING workspace_id PK
        STRING run_id PK
        STRING task_run_id PK
        STRING job_id FK
        STRING task_key FK
        TIMESTAMP period_start_time
        STRING result_state
    }

    fact_pipeline_update_timeline {
        STRING workspace_id PK
        STRING pipeline_id FK
        STRING update_id PK
        TIMESTAMP period_start_time
        STRING state
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_job | fact_job_run_timeline | 1:N | workspace_id, job_id |
| dim_job_task | fact_job_task_run_timeline | 1:N | workspace_id, job_id, task_key |
| dim_pipeline | fact_pipeline_update_timeline | 1:N | workspace_id, pipeline_id |

