# Data Classification Domain ERD

## Overview
Data classification detection results.

## Tables
- `fact_data_classification` - Classification events
- `fact_data_classification_results` - Classification outcomes

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_data_classification : "workspace_id"
    dim_workspace ||--o{ fact_data_classification_results : "workspace_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    fact_data_classification {
        STRING workspace_id PK
        STRING table_catalog
        STRING table_schema
        STRING table_name
        TIMESTAMP event_time PK
        STRING classification_status
    }

    fact_data_classification_results {
        STRING workspace_id PK
        STRING table_catalog
        STRING table_schema
        STRING table_name
        STRING column_name
        TIMESTAMP event_time PK
        STRING classification_result
        STRING pii_type
        DOUBLE confidence_score
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_workspace | fact_data_classification | 1:N | workspace_id |
| dim_workspace | fact_data_classification_results | 1:N | workspace_id |

