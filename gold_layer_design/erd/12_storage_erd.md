# Storage Domain ERD

## Overview
Storage optimization operations.

## Tables
- `fact_predictive_optimization` - Predictive optimization operations

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_predictive_optimization : "workspace_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    fact_predictive_optimization {
        STRING workspace_id PK
        STRING table_catalog
        STRING table_schema
        STRING table_name
        STRING operation_type
        TIMESTAMP start_time PK
        TIMESTAMP end_time
        STRING status
        BIGINT bytes_written
        BIGINT files_added
        BIGINT files_removed
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_workspace | fact_predictive_optimization | 1:N | workspace_id |

