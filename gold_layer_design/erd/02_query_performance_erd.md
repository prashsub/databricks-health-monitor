# Query Performance Domain ERD

## Overview
SQL warehouse and query execution analytics.

## Tables
- `dim_warehouse` - SQL warehouse configurations
- `fact_query_history` - Query execution history
- `fact_warehouse_events` - Warehouse lifecycle events

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ dim_warehouse : "workspace_id"
    dim_warehouse ||--o{ fact_query_history : "workspace_id, warehouse_id"
    dim_warehouse ||--o{ fact_warehouse_events : "workspace_id, warehouse_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    dim_warehouse {
        STRING workspace_id PK
        STRING warehouse_id PK
        STRING warehouse_name
        STRING warehouse_type
        STRING cluster_size
        INT min_num_clusters
        INT max_num_clusters
    }

    fact_query_history {
        STRING workspace_id PK
        STRING statement_id PK
        STRING warehouse_id FK
        STRING user_name
        STRING statement_text
        TIMESTAMP start_time
        TIMESTAMP end_time
        BIGINT execution_time_ms
        STRING status
    }

    fact_warehouse_events {
        STRING workspace_id PK
        STRING warehouse_id FK
        STRING event_type PK
        TIMESTAMP event_time PK
        STRING cluster_count
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_warehouse | fact_query_history | 1:N | workspace_id, warehouse_id |
| dim_warehouse | fact_warehouse_events | 1:N | workspace_id, warehouse_id |

