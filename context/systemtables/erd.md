erDiagram

    WORKSPACES {
        string workspace_id PK
        string account_id
    }

    BILLING_USAGE {
        string record_id PK
        string workspace_id
        string sku_name
    }

    BILLING_LIST_PRICES {
        string sku_name PK
    }

    CLUSTERS {
        string cluster_id PK
        string workspace_id
    }

    NODE_TYPES {
        string node_type PK
    }

    NODE_TIMELINE {
        string cluster_id
        string instance_id
        datetime start_time
    }

    WAREHOUSES {
        string warehouse_id PK
        string workspace_id
    }

    WAREHOUSE_EVENTS {
        string warehouse_id
        datetime event_time
    }

    QUERY_HISTORY {
        string statement_id PK
        string workspace_id
        string warehouse_id
        string cluster_id
        string job_id
    }

    JOBS {
        string job_id PK
        string workspace_id
    }

    JOB_TASKS {
        string job_id
        string task_id
    }

    JOB_RUN_TIMELINE {
        string job_run_id PK
        string job_id
        string workspace_id
    }

    JOB_TASK_RUN_TIMELINE {
        string job_run_id
        string task_id
        string cluster_id
    }

    PIPELINES {
        string pipeline_id PK
        string workspace_id
    }

    PIPELINE_UPDATE_TIMELINE {
        string pipeline_update_id PK
        string pipeline_id
        string cluster_id
    }

    TABLE_LINEAGE {
        string lineage_id PK
        string workspace_id
        string table_full_name
    }

    COLUMN_LINEAGE {
        string column_lineage_id PK
        string workspace_id
        string table_full_name
        string column_name
    }

    DQ_RESULTS {
        string result_id PK
        string workspace_id
        string table_full_name
    }

    DATA_CLASSIFICATION {
        string classification_id PK
        string workspace_id
        string table_full_name
        string column_name
    }

    PREDICTIVE_OPT {
        string operation_id PK
        string workspace_id
        string table_full_name
    }

    AUDIT {
        string audit_id PK
        string workspace_id
    }

    INBOUND_NETWORK {
        string event_id PK
        string workspace_id
    }

    OUTBOUND_NETWORK {
        string event_id PK
        string workspace_id
    }

    ASSISTANT_EVENTS {
        string assistant_event_id PK
        string workspace_id
    }

    MARKETPLACE_FUNNEL {
        string funnel_event_id PK
    }

    MARKETPLACE_ACCESS {
        string access_event_id PK
    }

    SERVED_ENTITIES {
        string endpoint_id PK
        string workspace_id
    }

    ENDPOINT_USAGE {
        string request_id PK
        string endpoint_id
        string workspace_id
    }

    MLFLOW_EXPERIMENTS {
        string experiment_id PK
        string workspace_id
    }

    MLFLOW_RUNS {
        string run_id PK
        string experiment_id
        string workspace_id
    }

    MLFLOW_METRICS {
        string run_id
        string metric_key
    }

    WORKSPACES ||--o{ BILLING_USAGE : "workspace_id"
    BILLING_USAGE }o--|| BILLING_LIST_PRICES : "sku_name"

    WORKSPACES ||--o{ CLUSTERS : "workspace_id"
    CLUSTERS ||--o{ NODE_TIMELINE : "cluster_id"
    CLUSTERS ||--o{ JOB_TASK_RUN_TIMELINE : "cluster_id"
    CLUSTERS ||--o{ PIPELINE_UPDATE_TIMELINE : "cluster_id"

    NODE_TYPES ||--o{ CLUSTERS : "driver/worker_node_type"
    NODE_TYPES ||--o{ NODE_TIMELINE : "node_type"

    WORKSPACES ||--o{ WAREHOUSES : "workspace_id"
    WAREHOUSES ||--o{ WAREHOUSE_EVENTS : "warehouse_id"
    WAREHOUSES ||--o{ QUERY_HISTORY : "warehouse_id"

    WORKSPACES ||--o{ JOBS : "workspace_id"
    JOBS ||--o{ JOB_TASKS : "job_id"
    JOBS ||--o{ JOB_RUN_TIMELINE : "job_id"
    JOB_RUN_TIMELINE ||--o{ JOB_TASK_RUN_TIMELINE : "job_run_id"
    JOB_TASKS ||--o{ JOB_TASK_RUN_TIMELINE : "task_id"

    WORKSPACES ||--o{ PIPELINES : "workspace_id"
    PIPELINES ||--o{ PIPELINE_UPDATE_TIMELINE : "pipeline_id"

    WORKSPACES ||--o{ TABLE_LINEAGE : "workspace_id"
    WORKSPACES ||--o{ COLUMN_LINEAGE : "workspace_id"
    TABLE_LINEAGE ||--o{ COLUMN_LINEAGE : "table_full_name"

    WORKSPACES ||--o{ DQ_RESULTS : "workspace_id"
    WORKSPACES ||--o{ DATA_CLASSIFICATION : "workspace_id"
    WORKSPACES ||--o{ PREDICTIVE_OPT : "workspace_id"

    WORKSPACES ||--o{ AUDIT : "workspace_id"
    WORKSPACES ||--o{ INBOUND_NETWORK : "workspace_id"
    WORKSPACES ||--o{ OUTBOUND_NETWORK : "workspace_id"
    WORKSPACES ||--o{ ASSISTANT_EVENTS : "workspace_id"

    WORKSPACES ||--o{ SERVED_ENTITIES : "workspace_id"
    SERVED_ENTITIES ||--o{ ENDPOINT_USAGE : "endpoint_id"

    WORKSPACES ||--o{ MLFLOW_EXPERIMENTS : "workspace_id"
    MLFLOW_EXPERIMENTS ||--o{ MLFLOW_RUNS : "experiment_id"
    MLFLOW_RUNS ||--o{ MLFLOW_METRICS : "run_id"
