# Data Quality Domain ERD

## Overview
Data quality monitoring and metrics.

## Tables
- `fact_data_quality_monitoring_table_results` - Table DQ results
- `fact_dq_monitoring` - DQ monitoring events

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_data_quality_monitoring_table_results : "workspace_id"
    dim_workspace ||--o{ fact_dq_monitoring : "workspace_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    fact_data_quality_monitoring_table_results {
        STRING workspace_id PK
        STRING table_catalog
        STRING table_schema
        STRING table_name
        TIMESTAMP event_time PK
        STRING status
        STRING freshness_status
        STRING completeness_status
    }

    fact_dq_monitoring {
        STRING workspace_id PK
        STRING monitor_id PK
        STRING table_full_name
        TIMESTAMP event_time PK
        STRING status
        BIGINT rows_processed
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_workspace | fact_data_quality_monitoring_table_results | 1:N | workspace_id |
| dim_workspace | fact_dq_monitoring | 1:N | workspace_id |

