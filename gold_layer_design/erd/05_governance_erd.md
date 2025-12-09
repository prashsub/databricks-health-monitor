# Governance Domain ERD

## Overview
Data lineage and metadata tracking.

## Tables
- `fact_table_lineage` - Table-level lineage
- `fact_column_lineage` - Column-level lineage

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_table_lineage : "workspace_id"
    dim_workspace ||--o{ fact_column_lineage : "workspace_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    fact_table_lineage {
        STRING workspace_id PK
        STRING entity_type
        STRING source_table_full_name
        STRING source_table_catalog
        STRING source_table_schema
        STRING source_table_name
        STRING target_table_full_name
        STRING target_table_catalog
        STRING target_table_schema
        STRING target_table_name
        TIMESTAMP event_time PK
    }

    fact_column_lineage {
        STRING workspace_id PK
        STRING source_table_full_name
        STRING source_column_name
        STRING target_table_full_name
        STRING target_column_name
        TIMESTAMP event_time PK
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_workspace | fact_table_lineage | 1:N | workspace_id |
| dim_workspace | fact_column_lineage | 1:N | workspace_id |

