# Compute Domain ERD

## Overview
Cluster and compute resource management.

## Tables
- `dim_cluster` - Cluster configurations
- `dim_node_type` - Available node types
- `fact_node_timeline` - Node utilization metrics

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ dim_cluster : "workspace_id"
    dim_cluster ||--o{ fact_node_timeline : "workspace_id, cluster_id"
    dim_node_type ||--o{ dim_cluster : "node_type_id"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    dim_node_type {
        STRING node_type_id PK
        STRING category
        INT num_cores
        DOUBLE memory_mb
        DOUBLE num_gpus
    }

    dim_cluster {
        STRING workspace_id PK
        STRING cluster_id PK
        STRING cluster_name
        STRING cluster_source
        STRING node_type_id FK
        STRING driver_node_type_id
        STRING spark_version
        STRING creator_user_name
    }

    fact_node_timeline {
        STRING workspace_id PK
        STRING cluster_id FK
        TIMESTAMP start_time PK
        TIMESTAMP end_time
        STRING node_id
        STRING instance_id
        STRING state
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_cluster | fact_node_timeline | 1:N | workspace_id, cluster_id |
| dim_node_type | dim_cluster | 1:N | node_type_id |

