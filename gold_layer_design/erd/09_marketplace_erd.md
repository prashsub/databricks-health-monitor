# Marketplace Domain ERD

## Overview
Databricks Marketplace listing analytics.

## Tables
- `fact_listing_access` - Listing data access events
- `fact_listing_funnel` - Listing engagement funnel

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_listing_access : "workspace_id"
    dim_workspace ||--o{ fact_listing_funnel : "workspace_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    fact_listing_access {
        STRING workspace_id PK
        STRING listing_id PK
        STRING consumer_account_id
        STRING consumer_metastore_id
        TIMESTAMP access_time PK
        STRING access_type
    }

    fact_listing_funnel {
        STRING workspace_id PK
        STRING listing_id PK
        STRING event_type PK
        DATE event_date PK
        BIGINT event_count
        STRING consumer_account_id
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_workspace | fact_listing_access | 1:N | workspace_id |
| dim_workspace | fact_listing_funnel | 1:N | workspace_id |

