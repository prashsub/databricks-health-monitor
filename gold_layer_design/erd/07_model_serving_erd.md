# Model Serving Domain ERD

## Overview
Model deployment and inference tracking.

## Tables
- `dim_served_entities` - Deployed model entities
- `fact_endpoint_usage` - Endpoint utilization
- `fact_payload_logs` - Inference request logs

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ dim_served_entities : "workspace_id"
    dim_served_entities ||--o{ fact_endpoint_usage : "workspace_id, endpoint_name, served_entity_name"
    dim_served_entities ||--o{ fact_payload_logs : "workspace_id, endpoint_name"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    dim_served_entities {
        STRING workspace_id PK
        STRING endpoint_name PK
        STRING served_entity_name PK
        STRING entity_type
        STRING entity_version
        TIMESTAMP creation_timestamp
    }

    fact_endpoint_usage {
        STRING workspace_id PK
        STRING endpoint_name FK
        STRING served_entity_name FK
        DATE usage_date PK
        BIGINT request_count
        BIGINT token_count
    }

    fact_payload_logs {
        STRING workspace_id PK
        STRING endpoint_name FK
        STRING request_id PK
        TIMESTAMP timestamp_ms
        STRING status_code
        DOUBLE execution_time_ms
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_served_entities | fact_endpoint_usage | 1:N | workspace_id, endpoint_name, served_entity_name |
| dim_served_entities | fact_payload_logs | 1:N | workspace_id, endpoint_name |

