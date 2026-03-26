# Bronze to Gold Layer Lineage Document

## Overview

This document provides comprehensive column-level lineage from Bronze system tables to Gold dimensional model tables. **This is the single source of truth for all Gold MERGE operations.**

**Purpose:** Prevent schema mismatch bugs by documenting every column transformation explicitly.

**Total Tables:**
- Bronze Source: 20 streaming tables from `system.*`
- Gold Target: 38 tables (23 dimensions, 15 facts) across 13 domains

---

## Critical Patterns (From Cursor Rules)

### 1. Always Deduplicate Before MERGE
```python
# From 11-gold-delta-merge-deduplication.mdc
bronze_df = (
    spark.table(bronze_table)
    .orderBy(col("bronze_ingestion_timestamp").desc())  # Latest first
    .dropDuplicates([business_key])  # Business key matches MERGE key
)
```

### 2. Explicit Column Mapping
```python
# From 10-gold-layer-merge-patterns.mdc
# NEVER assume column names match - use explicit .withColumn()
updates_df = (
    bronze_df
    .withColumn("gold_column_name", col("bronze_column_name"))
)
```

### 3. DDL as Source of Truth
```python
# From 23-gold-layer-schema-validation.mdc
# Always validate DataFrame against actual DDL before MERGE
validate_merge_schema(spark, updates_df, catalog, gold_schema, table_name)
```

### 4. Grain Validation for Facts
```python
# From 24-fact-table-grain-validation.mdc
# Single PK = Transaction grain (no aggregation)
# Composite PK = Aggregated grain (requires GROUP BY)
```

---

## Domain 1: Shared (1 table)

### dim_workspace

**Bronze Source:** `system.access.workspaces_latest` → Bronze: `workspaces_latest`
**Gold Table:** `dim_workspace`
**Primary Key:** `workspace_id`
**Grain:** One row per workspace (SCD Type 1)
**Deduplication Key:** `workspace_id`

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `workspace_id` | STRING NOT NULL | `workspace_id` | Direct copy | Business key (PK) |
| `account_id` | STRING | `account_id` | Direct copy | |
| `workspace_name` | STRING | `workspace_name` | Direct copy | Human-readable name |
| `workspace_url` | STRING | `workspace_url` | Direct copy | |
| `create_time` | TIMESTAMP | `create_time` | Direct copy | |
| `status` | STRING | `status` | Direct copy | NOT_PROVISIONED, PROVISIONING, RUNNING, FAILED, BANNED |

**⚠️ Note:** `workspaces_latest` does NOT support streaming. Use batch MERGE pattern.

---

## Domain 2: Billing (3 tables)

### dim_sku

**Bronze Source:** `system.billing.usage` (DISTINCT sku_name values)
**Gold Table:** `dim_sku`
**Primary Key:** `sku_name`
**Grain:** One row per unique SKU (SCD Type 1)
**Deduplication Key:** `sku_name`

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `sku_name` | STRING NOT NULL | `sku_name` | Direct copy | Business key (PK) |
| `cloud` | STRING | `cloud` | Direct copy | AWS, AZURE, GCP |
| `usage_unit` | STRING | `usage_unit` | Direct copy | DBU, GB, etc. |

**Merge Logic:**
```python
# Extract distinct SKUs from usage table
sku_df = spark.table(bronze_usage).select("sku_name", "cloud", "usage_unit").distinct()
```

### fact_usage

**Bronze Source:** `system.billing.usage` → Bronze: `usage`
**Gold Table:** `fact_usage`
**Primary Key:** `record_id` (transaction grain)
**Grain:** One row per usage record
**Deduplication Key:** `record_id`

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `record_id` | STRING NOT NULL | `record_id` | Direct copy | PK - unique per record |
| `account_id` | STRING | `account_id` | Direct copy | |
| `workspace_id` | STRING | `workspace_id` | Direct copy | FK to dim_workspace |
| `sku_name` | STRING | `sku_name` | Direct copy | FK to dim_sku |
| `cloud` | STRING | `cloud` | Direct copy | AWS, AZURE, GCP |
| `usage_start_time` | TIMESTAMP | `usage_start_time` | Direct copy | |
| `usage_end_time` | TIMESTAMP | `usage_end_time` | Direct copy | |
| `usage_date` | DATE | `usage_date` | Direct copy | |
| `usage_unit` | STRING | `usage_unit` | Direct copy | |
| `usage_quantity` | DECIMAL | `usage_quantity` | Direct copy | |
| `record_type` | STRING | `record_type` | Direct copy | ORIGINAL, RETRACTION, RESTATEMENT |
| `ingestion_date` | DATE | `ingestion_date` | Direct copy | |
| `billing_origin_product` | STRING | `billing_origin_product` | Direct copy | |
| `usage_type` | STRING | `usage_type` | Direct copy | |
| **Flattened: usage_metadata** |
| `usage_metadata_cluster_id` | STRING | `usage_metadata.cluster_id` | `.getField("cluster_id")` | FK to dim_cluster |
| `usage_metadata_job_id` | STRING | `usage_metadata.job_id` | `.getField("job_id")` | FK to dim_job |
| `usage_metadata_warehouse_id` | STRING | `usage_metadata.warehouse_id` | `.getField("warehouse_id")` | FK to dim_warehouse |
| `usage_metadata_instance_pool_id` | STRING | `usage_metadata.instance_pool_id` | `.getField("instance_pool_id")` | |
| `usage_metadata_node_type` | STRING | `usage_metadata.node_type` | `.getField("node_type")` | |
| `usage_metadata_job_run_id` | STRING | `usage_metadata.job_run_id` | `.getField("job_run_id")` | FK to fact_job_run |
| `usage_metadata_notebook_id` | STRING | `usage_metadata.notebook_id` | `.getField("notebook_id")` | |
| `usage_metadata_dlt_pipeline_id` | STRING | `usage_metadata.dlt_pipeline_id` | `.getField("dlt_pipeline_id")` | FK to dim_pipeline |
| `usage_metadata_endpoint_name` | STRING | `usage_metadata.endpoint_name` | `.getField("endpoint_name")` | |
| `usage_metadata_endpoint_id` | STRING | `usage_metadata.endpoint_id` | `.getField("endpoint_id")` | |
| `usage_metadata_dlt_update_id` | STRING | `usage_metadata.dlt_update_id` | `.getField("dlt_update_id")` | |
| `usage_metadata_dlt_maintenance_id` | STRING | `usage_metadata.dlt_maintenance_id` | `.getField("dlt_maintenance_id")` | |
| `usage_metadata_run_name` | STRING | `usage_metadata.run_name` | `.getField("run_name")` | |
| `usage_metadata_job_name` | STRING | `usage_metadata.job_name` | `.getField("job_name")` | |
| `usage_metadata_notebook_path` | STRING | `usage_metadata.notebook_path` | `.getField("notebook_path")` | |
| `usage_metadata_central_clean_room_id` | STRING | `usage_metadata.central_clean_room_id` | `.getField("central_clean_room_id")` | |
| `usage_metadata_source_region` | STRING | `usage_metadata.source_region` | `.getField("source_region")` | |
| `usage_metadata_destination_region` | STRING | `usage_metadata.destination_region` | `.getField("destination_region")` | |
| `usage_metadata_app_id` | STRING | `usage_metadata.app_id` | `.getField("app_id")` | |
| `usage_metadata_app_name` | STRING | `usage_metadata.app_name` | `.getField("app_name")` | |
| `usage_metadata_metastore_id` | STRING | `usage_metadata.metastore_id` | `.getField("metastore_id")` | |
| `usage_metadata_private_endpoint_name` | STRING | `usage_metadata.private_endpoint_name` | `.getField("private_endpoint_name")` | |
| `usage_metadata_storage_api_type` | STRING | `usage_metadata.storage_api_type` | `.getField("storage_api_type")` | |
| `usage_metadata_budget_policy_id` | STRING | `usage_metadata.budget_policy_id` | `.getField("budget_policy_id")` | |
| `usage_metadata_ai_runtime_pool_id` | STRING | `usage_metadata.ai_runtime_pool_id` | `.getField("ai_runtime_pool_id")` | |
| `usage_metadata_ai_runtime_workload_id` | STRING | `usage_metadata.ai_runtime_workload_id` | `.getField("ai_runtime_workload_id")` | |
| `usage_metadata_uc_table_catalog` | STRING | `usage_metadata.uc_table_catalog` | `.getField("uc_table_catalog")` | |
| `usage_metadata_uc_table_schema` | STRING | `usage_metadata.uc_table_schema` | `.getField("uc_table_schema")` | |
| `usage_metadata_uc_table_name` | STRING | `usage_metadata.uc_table_name` | `.getField("uc_table_name")` | |
| `usage_metadata_database_instance_id` | STRING | `usage_metadata.database_instance_id` | `.getField("database_instance_id")` | |
| `usage_metadata_sharing_materialization_id` | STRING | `usage_metadata.sharing_materialization_id` | `.getField("sharing_materialization_id")` | |
| `usage_metadata_schema_id` | STRING | `usage_metadata.schema_id` | `.getField("schema_id")` | |
| `usage_metadata_usage_policy_id` | STRING | `usage_metadata.usage_policy_id` | `.getField("usage_policy_id")` | |
| `usage_metadata_base_environment_id` | STRING | `usage_metadata.base_environment_id` | `.getField("base_environment_id")` | |
| `usage_metadata_agent_bricks_id` | STRING | `usage_metadata.agent_bricks_id` | `.getField("agent_bricks_id")` | |
| `usage_metadata_index_id` | STRING | `usage_metadata.index_id` | `.getField("index_id")` | |
| `usage_metadata_catalog_id` | STRING | `usage_metadata.catalog_id` | `.getField("catalog_id")` | |
| **Flattened: identity_metadata** |
| `identity_metadata_run_as` | STRING | `identity_metadata.run_as` | `.getField("run_as")` | |
| `identity_metadata_created_by` | STRING | `identity_metadata.created_by` | `.getField("created_by")` | |
| `identity_metadata_owned_by` | STRING | `identity_metadata.owned_by` | `.getField("owned_by")` | |
| **Flattened: product_features** |
| `product_features_jobs_tier` | STRING | `product_features.jobs_tier` | `.getField("jobs_tier")` | |
| `product_features_sql_tier` | STRING | `product_features.sql_tier` | `.getField("sql_tier")` | |
| `product_features_dlt_tier` | STRING | `product_features.dlt_tier` | `.getField("dlt_tier")` | |
| `product_features_is_serverless` | BOOLEAN | `product_features.is_serverless` | `.getField("is_serverless")` | |
| `product_features_is_photon` | BOOLEAN | `product_features.is_photon` | `.getField("is_photon")` | |
| `product_features_serving_type` | STRING | `product_features.serving_type` | `.getField("serving_type")` | |
| `product_features_networking` | STRING | `product_features.networking` | `.getField("networking")` | |
| `product_features_ai_runtime` | STRING | `product_features.ai_runtime` | `.getField("ai_runtime")` | |
| `product_features_model_serving` | STRING | `product_features.model_serving` | `.getField("model_serving")` | |
| `product_features_ai_gateway` | STRING | `product_features.ai_gateway` | `.getField("ai_gateway")` | |
| `product_features_performance_target` | STRING | `product_features.performance_target` | `.getField("performance_target")` | |
| `product_features_serverless_gpu` | STRING | `product_features.serverless_gpu` | `.getField("serverless_gpu")` | |
| `product_features_agent_bricks` | STRING | `product_features.agent_bricks` | `.getField("agent_bricks")` | |
| `product_features_ai_functions` | STRING | `product_features.ai_functions` | `.getField("ai_functions")` | |
| `product_features_apps` | STRING | `product_features.apps` | `.getField("apps")` | |
| `product_features_lakeflow_connect` | STRING | `product_features.lakeflow_connect` | `.getField("lakeflow_connect")` | |
| **MAP Type: custom_tags** |
| `custom_tags` | MAP&lt;STRING,STRING&gt; | `custom_tags` | Direct copy (already MAP) | Query: `custom_tags['key']` |
| **Derived: from list_prices join** |
| `list_price` | DECIMAL(18,6) | JOIN `system.billing.list_prices` | See below | |
| `list_cost` | DECIMAL(18,6) | DERIVED | `usage_quantity * list_price` | |
| **Derived: tag governance** |
| `is_tagged` | BOOLEAN NOT NULL | DERIVED | `size(custom_tags) > 0` | |
| `tag_count` | INT | DERIVED | `size(custom_tags)` | |

**list_price Enrichment Logic:**
```python
# Join with list_prices to get price at time of usage
list_prices_df = spark.table("system.billing.list_prices")

enriched_df = (
    bronze_df
    .join(
        list_prices_df.select("sku_name", "cloud", "effective_start_time", "effective_end_time", "pricing.default"),
        on=[
            (col("usage.sku_name") == col("prices.sku_name")) &
            (col("usage.cloud") == col("prices.cloud")) &
            (col("usage.usage_start_time") >= col("prices.effective_start_time")) &
            ((col("prices.effective_end_time").isNull()) | (col("usage.usage_start_time") < col("prices.effective_end_time")))
        ],
        how="left"
    )
    .withColumn("list_price", col("pricing.default"))
    .withColumn("list_cost", col("usage_quantity") * col("list_price"))
)
```

### fact_list_prices

**Bronze Source:** `system.billing.list_prices` (non-streaming)
**Gold Table:** `fact_list_prices`
**Primary Key:** `sku_name, cloud, effective_start_time`
**Grain:** One row per price change event

| Gold Column | Type | Bronze Source | Transformation |
|-------------|------|---------------|----------------|
| `sku_name` | STRING NOT NULL | `sku_name` | Direct copy |
| `cloud` | STRING NOT NULL | `cloud` | Direct copy |
| `effective_start_time` | TIMESTAMP NOT NULL | `effective_start_time` | Direct copy |
| `effective_end_time` | TIMESTAMP | `effective_end_time` | Direct copy |
| `currency_code` | STRING | `currency_code` | Direct copy |
| `usage_unit` | STRING | `usage_unit` | Direct copy |
| `list_price_default` | DECIMAL(18,6) | `pricing.default` | `.getField("default")` |

---

## Domain 3: Lakeflow (6 tables)

### dim_job

**Bronze Source:** `system.lakeflow.jobs` → Bronze: `jobs`
**Gold Table:** `dim_job`
**Primary Key:** `workspace_id, job_id` (composite)
**Grain:** One row per job per workspace (SCD Type 2)
**Deduplication Key:** `workspace_id, job_id` (take latest by `change_time`)

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `workspace_id` | STRING NOT NULL | `workspace_id` | Direct copy | Part of composite PK |
| `job_id` | STRING NOT NULL | `job_id` | Direct copy | Part of composite PK |
| `account_id` | STRING | `account_id` | Direct copy | |
| `name` | STRING | `name` | Direct copy | Job name |
| `creator_id` | STRING | `creator_id` | Direct copy | |
| `run_as` | STRING | `run_as` | Direct copy | Service principal or user |
| `change_time` | TIMESTAMP | `change_time` | Direct copy | Last modification time |
| `delete_time` | TIMESTAMP | `delete_time` | Direct copy | NULL if not deleted |
| `description` | STRING | `description` | Direct copy | Not populated before Aug 2024 |
| `tags_json` | STRING | `tags` | `to_json(tags)` | Preserve as JSON string |

**Deduplication:**
```python
bronze_df = (
    spark.table(bronze_jobs)
    .orderBy(col("change_time").desc())  # Latest version first
    .dropDuplicates(["workspace_id", "job_id"])
)
```

### dim_job_task

**Bronze Source:** `system.lakeflow.job_tasks` → Bronze: `job_tasks`
**Gold Table:** `dim_job_task`
**Primary Key:** `workspace_id, job_id, task_key`
**Grain:** One row per task per job

| Gold Column | Type | Bronze Source | Transformation |
|-------------|------|---------------|----------------|
| `workspace_id` | STRING NOT NULL | `workspace_id` | Direct copy |
| `job_id` | STRING NOT NULL | `job_id` | Direct copy |
| `task_key` | STRING NOT NULL | `task_key` | Direct copy |
| `account_id` | STRING | `account_id` | Direct copy |
| `change_time` | TIMESTAMP | `change_time` | Direct copy |
| `delete_time` | TIMESTAMP | `delete_time` | Direct copy |

### dim_pipeline

**Bronze Source:** `system.lakeflow.pipelines` → Bronze: `pipelines`
**Gold Table:** `dim_pipeline`
**Primary Key:** `workspace_id, dlt_pipeline_id`
**Grain:** One row per pipeline per workspace

| Gold Column | Type | Bronze Source | Transformation |
|-------------|------|---------------|----------------|
| `workspace_id` | STRING NOT NULL | `workspace_id` | Direct copy |
| `dlt_pipeline_id` | STRING NOT NULL | `pipeline_id` | **RENAME** from `pipeline_id` |
| `account_id` | STRING | `account_id` | Direct copy |
| `name` | STRING | `name` | Direct copy |
| `pipeline_type` | STRING | `pipeline_type` | Direct copy |
| `creator_id` | STRING | `creator_id` | Direct copy |
| `run_as` | STRING | `run_as` | Direct copy |
| `change_time` | TIMESTAMP | `change_time` | Direct copy |
| `delete_time` | TIMESTAMP | `delete_time` | Direct copy |

### fact_job_run_timeline

**Bronze Source:** `system.lakeflow.job_run_timeline` → Bronze: `job_run_timeline`
**Gold Table:** `fact_job_run_timeline`
**Primary Key:** `workspace_id, run_id` (transaction grain)
**Grain:** One row per job run (with hourly slicing for long jobs)
**Deduplication Key:** `workspace_id, run_id`

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `workspace_id` | STRING NOT NULL | `workspace_id` | Direct copy | Part of PK |
| `run_id` | STRING NOT NULL | `run_id` | Direct copy | Part of PK |
| `account_id` | STRING | `account_id` | Direct copy | |
| `job_id` | STRING | `job_id` | Direct copy | FK to dim_job |
| `period_start_time` | TIMESTAMP | `period_start_time` | Direct copy | |
| `period_end_time` | TIMESTAMP | `period_end_time` | Direct copy | |
| `trigger_type` | STRING | `trigger_type` | Direct copy | MANUAL, SCHEDULED, etc. |
| `result_state` | STRING | `result_state` | Direct copy | SUCCESS, FAILED, etc. |
| `run_type` | STRING | `run_type` | Direct copy | WORKFLOW_RUN, REPAIR_RUN |
| `run_name` | STRING | `run_name` | Direct copy | |
| `termination_code` | STRING | `termination_code` | Direct copy | Not before Aug 2024 |
| **ARRAY Type** |
| `compute_ids` | ARRAY&lt;STRING&gt; | `compute_ids` | Direct copy | Already ARRAY in source |
| **MAP Type** |
| `job_parameters` | MAP&lt;STRING,STRING&gt; | `job_parameters` | Direct copy | Already MAP in source |
| **Derived** |
| `run_date` | DATE | DERIVED | `DATE(period_start_time)` | For partitioning |
| `run_duration_seconds` | BIGINT | DERIVED | `UNIX_TIMESTAMP(period_end_time) - UNIX_TIMESTAMP(period_start_time)` | NULL if in progress |
| `run_duration_minutes` | DOUBLE | DERIVED | `run_duration_seconds / 60.0` | |
| `is_success` | BOOLEAN NOT NULL | DERIVED | `result_state = 'SUCCESS'` | |

**Derivation Logic:**
```python
updates_df = (
    bronze_df
    # Derived columns
    .withColumn("run_date", to_date(col("period_start_time")))
    .withColumn("run_duration_seconds",
                when(col("period_end_time").isNotNull(),
                     unix_timestamp(col("period_end_time")) - unix_timestamp(col("period_start_time")))
                .otherwise(None))
    .withColumn("run_duration_minutes",
                col("run_duration_seconds") / 60.0)
    .withColumn("is_success",
                col("result_state") == "SUCCESS")
)
```

### fact_job_task_run_timeline

**Bronze Source:** `system.lakeflow.job_task_run_timeline` → Bronze: `job_task_run_timeline`
**Gold Table:** `fact_job_task_run_timeline`
**Primary Key:** `workspace_id, run_id, task_run_id`
**Grain:** One row per task run

Similar structure to fact_job_run_timeline but at task level.

### fact_pipeline_update_timeline

**Bronze Source:** `system.lakeflow.pipeline_update_timeline` (non-streaming due to Deletion Vectors)
**Gold Table:** `fact_pipeline_update_timeline`
**Primary Key:** `workspace_id, pipeline_update_id`

---

## Domain 4: Security (5 tables)

### fact_audit_logs

**Bronze Source:** `system.access.audit` → Bronze: `audit`
**Gold Table:** `fact_audit_logs`
**Primary Key:** `event_id` (transaction grain)
**Grain:** One row per audit event
**Deduplication Key:** `event_id`

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `event_id` | STRING NOT NULL | `event_id` | Direct copy | PK |
| `account_id` | STRING | `account_id` | Direct copy | |
| `workspace_id` | STRING | `workspace_id` | Direct copy | FK to dim_workspace |
| `version` | STRING | `version` | Direct copy | Schema version |
| `event_time` | TIMESTAMP | `event_time` | Direct copy | |
| `event_date` | DATE | `event_date` | Direct copy | |
| `source_ip_address` | STRING | `source_ip_address` | Direct copy | |
| `user_agent` | STRING | `user_agent` | Direct copy | |
| `session_id` | STRING | `session_id` | Direct copy | |
| `service_name` | STRING | `service_name` | Direct copy | |
| `action_name` | STRING | `action_name` | Direct copy | |
| `request_id` | STRING | `request_id` | Direct copy | |
| `audit_level` | STRING | `audit_level` | Direct copy | ACCOUNT_LEVEL or WORKSPACE_LEVEL |
| **Flattened: user_identity** |
| `user_identity_email` | STRING | `user_identity.email` | `.getField("email")` | |
| `user_identity_subject_name` | STRING | `user_identity.subject_name` | `.getField("subject_name")` | |
| **MAP Type: request_params** |
| `request_params` | MAP&lt;STRING,STRING&gt; | `request_params` | Direct copy | Query: `request_params['key']` |
| **Flattened: response** |
| `response_status_code` | INT | `response.status_code` | `.getField("status_code")` | |
| `response_error_message` | STRING | `response.error_message` | `.getField("error_message")` | |
| `response_result` | STRING | `response.result` | `.getField("result")` | |
| **Flattened: identity_metadata** |
| `identity_metadata_run_by` | STRING | `identity_metadata.run_by` | `.getField("run_by")` | |
| `identity_metadata_run_as` | STRING | `identity_metadata.run_as` | `.getField("run_as")` | |
| `identity_metadata_acting_resource` | STRING | `identity_metadata.acting_resource` | `.getField("acting_resource")` | |
| **Derived** |
| `is_sensitive_action` | BOOLEAN NOT NULL | DERIVED | See below | Security flag |
| `is_failed_action` | BOOLEAN NOT NULL | DERIVED | `response_status_code >= 400 OR response_error_message IS NOT NULL` | |

**Sensitive Action Derivation:**
```python
sensitive_actions = ['grant', 'revoke', 'delete', 'getSecret', 'putSecret', 'createServicePrincipal', 'deleteServicePrincipal']

.withColumn("is_sensitive_action",
            lower(col("action_name")).rlike("|".join(sensitive_actions)))
.withColumn("is_failed_action",
            (col("response_status_code") >= 400) | col("response_error_message").isNotNull())
```

### fact_clean_room_events

**Bronze Source:** `system.access.clean_room_events` → Bronze: `clean_room_events`
**Gold Table:** `fact_clean_room_events`
**Primary Key:** `event_id`

### fact_inbound_network

**Bronze Source:** `system.access.inbound_network` (non-streaming - Deletion Vectors)
**Gold Table:** `fact_inbound_network`

### fact_outbound_network

**Bronze Source:** `system.access.outbound_network` → Bronze: `outbound_network`
**Gold Table:** `fact_outbound_network`

### fact_assistant_events

**Bronze Source:** `system.access.assistant_events`
**Gold Table:** `fact_assistant_events`

---

## Domain 5: Query Performance (3 tables)

### dim_warehouse

**Bronze Source:** `system.compute.warehouses` → Bronze: `warehouses`
**Gold Table:** `dim_warehouse`
**Primary Key:** `workspace_id, warehouse_id`
**Grain:** One row per warehouse per workspace

| Gold Column | Type | Bronze Source | Transformation |
|-------------|------|---------------|----------------|
| `workspace_id` | STRING NOT NULL | `workspace_id` | Direct copy |
| `warehouse_id` | STRING NOT NULL | `warehouse_id` | Direct copy |
| `account_id` | STRING | `account_id` | Direct copy |
| `name` | STRING | `warehouse_name` | **RENAME** |
| `warehouse_type` | STRING | `warehouse_type` | Direct copy |
| `cluster_size` | STRING | `cluster_size` | Direct copy |
| `min_num_clusters` | INT | `min_num_clusters` | Direct copy |
| `max_num_clusters` | INT | `max_num_clusters` | Direct copy |
| `auto_stop_mins` | INT | `auto_stop_mins` | Direct copy |
| `creator_id` | STRING | `creator_id` | Direct copy |
| `change_time` | TIMESTAMP | `change_time` | Direct copy |
| `delete_time` | TIMESTAMP | `delete_time` | Direct copy |

### fact_query_history

**Bronze Source:** `system.query.history` (non-streaming)
**Gold Table:** `fact_query_history`
**Primary Key:** `statement_id` (transaction grain)
**Grain:** One row per query execution

| Gold Column | Type | Bronze Source | Transformation | Notes |
|-------------|------|---------------|----------------|-------|
| `statement_id` | STRING NOT NULL | `statement_id` | Direct copy | PK |
| `account_id` | STRING | `account_id` | Direct copy | |
| `workspace_id` | STRING | `workspace_id` | Direct copy | FK |
| `executed_by` | STRING | `executed_by` | Direct copy | |
| `session_id` | STRING | `session_id` | Direct copy | |
| `execution_status` | STRING | `execution_status` | Direct copy | FINISHED, FAILED, CANCELED |
| `executed_by_user_id` | STRING | `executed_by_user_id` | Direct copy | |
| `statement_text` | STRING | `statement_text` | Direct copy | |
| `statement_type` | STRING | `statement_type` | Direct copy | ALTER, COPY, INSERT, etc. |
| `error_message` | STRING | `error_message` | Direct copy | |
| `client_application` | STRING | `client_application` | Direct copy | |
| `client_driver` | STRING | `client_driver` | Direct copy | |
| `total_duration_ms` | BIGINT | `total_duration_ms` | Direct copy | |
| `waiting_for_compute_duration_ms` | BIGINT | `waiting_for_compute_duration_ms` | Direct copy | |
| `waiting_at_capacity_duration_ms` | BIGINT | `waiting_at_capacity_duration_ms` | Direct copy | |
| `execution_duration_ms` | BIGINT | `execution_duration_ms` | Direct copy | |
| `compilation_duration_ms` | BIGINT | `compilation_duration_ms` | Direct copy | |
| `total_task_duration_ms` | BIGINT | `total_task_duration_ms` | Direct copy | |
| `result_fetch_duration_ms` | BIGINT | `result_fetch_duration_ms` | Direct copy | |
| `start_time` | TIMESTAMP | `start_time` | Direct copy | |
| `end_time` | TIMESTAMP | `end_time` | Direct copy | |
| `update_time` | TIMESTAMP | `update_time` | Direct copy | |
| `read_partitions` | BIGINT | `read_partitions` | Direct copy | |
| `pruned_files` | BIGINT | `pruned_files` | Direct copy | |
| `read_files` | BIGINT | `read_files` | Direct copy | |
| `read_rows` | BIGINT | `read_rows` | Direct copy | |
| `produced_rows` | BIGINT | `produced_rows` | Direct copy | |
| `read_bytes` | BIGINT | `read_bytes` | Direct copy | |
| `read_io_cache_percent` | STRING | `read_io_cache_percent` | Direct copy | |
| `from_result_cache` | BOOLEAN | `from_result_cache` | Direct copy | |
| `spilled_local_bytes` | BIGINT | `spilled_local_bytes` | Direct copy | |
| `written_bytes` | BIGINT | `written_bytes` | Direct copy | |
| `shuffle_read_bytes` | BIGINT | `shuffle_read_bytes` | Direct copy | |
| `executed_as_user_id` | STRING | `executed_as_user_id` | Direct copy | |
| `executed_as` | STRING | `executed_as` | Direct copy | |
| `written_rows` | BIGINT | `written_rows` | Direct copy | |
| `written_files` | BIGINT | `written_files` | Direct copy | |
| `cache_origin_statement_id` | STRING | `cache_origin_statement_id` | Direct copy | |
| **Flattened: compute** |
| `compute_type` | STRING | `compute.type` | `.getField("type")` | WAREHOUSE |
| `compute_cluster_id` | STRING | `compute.cluster_id` | `.getField("cluster_id")` | |
| `compute_warehouse_id` | STRING | `compute.warehouse_id` | `.getField("warehouse_id")` | FK to dim_warehouse |
| **Flattened: query_source** |
| `query_source_job_info` | STRING | `query_source.job_info` | `.getField("job_info")` | |
| `query_source_legacy_dashboard_id` | STRING | `query_source.legacy_dashboard_id` | `.getField("legacy_dashboard_id")` | |
| `query_source_dashboard_id` | STRING | `query_source.dashboard_id` | `.getField("dashboard_id")` | |
| `query_source_alert_id` | STRING | `query_source.alert_id` | `.getField("alert_id")` | |
| `query_source_notebook_id` | STRING | `query_source.notebook_id` | `.getField("notebook_id")` | |
| `query_source_sql_query_id` | STRING | `query_source.sql_query_id` | `.getField("sql_query_id")` | |
| `query_source_genie_space_id` | STRING | `query_source.genie_space_id` | `.getField("genie_space_id")` | |
| `query_source_pipeline_info` | STRING | `query_source.pipeline_info` | `.getField("pipeline_info")` | |
| **Flattened: query_parameters** |
| `query_parameters_named_parameters` | STRING | `query_parameters.named_parameters` | `.getField("named_parameters")` | |
| `query_parameters_pos_parameters` | STRING | `query_parameters.pos_parameters` | `.getField("pos_parameters")` | |
| `query_parameters_truncated` | BOOLEAN | `query_parameters.truncated` | `.getField("truncated")` | |
| **MAP Type** |
| `query_tags` | MAP&lt;STRING,STRING&gt; | `query_tags` | Direct copy | |

### fact_warehouse_events

**Bronze Source:** `system.compute.warehouse_events` → Bronze: `warehouse_events`
**Gold Table:** `fact_warehouse_events`

---

## Domain 6: Compute (3 tables)

### dim_cluster

**Bronze Source:** `system.compute.clusters` → Bronze: `clusters`
**Gold Table:** `dim_cluster`
**Primary Key:** `workspace_id, cluster_id`

### dim_node_type

**Bronze Source:** `system.compute.node_types` (non-streaming)
**Gold Table:** `dim_node_type`
**Primary Key:** `node_type_id`

### fact_node_timeline

**Bronze Source:** `system.compute.node_timeline` → Bronze: `node_timeline`
**Gold Table:** `fact_node_timeline`

---

## Domain 7: Governance (2 tables)

### fact_table_lineage

**Bronze Source:** `system.access.table_lineage` → Bronze: `table_lineage`
**Gold Table:** `fact_table_lineage`

### fact_column_lineage

**Bronze Source:** `system.access.column_lineage` → Bronze: `column_lineage`
**Gold Table:** `fact_column_lineage`

---

## Domain 8: MLflow (3 tables)

### dim_experiment

**Bronze Source:** `system.mlflow.experiments_latest` → Bronze: `experiments_latest`
**Gold Table:** `dim_experiment`

### fact_mlflow_runs

**Bronze Source:** `system.mlflow.runs_latest` → Bronze: `runs_latest`
**Gold Table:** `fact_mlflow_runs`

### fact_mlflow_run_metrics_history

**Bronze Source:** `system.mlflow.run_metrics_history` → Bronze: `run_metrics_history`
**Gold Table:** `fact_mlflow_run_metrics_history`

---

## Domain 9: Model Serving (3 tables)

### dim_served_entities

**Bronze Source:** `system.serving.served_entities` → Bronze: `served_entities`
**Gold Table:** `dim_served_entities`

### fact_endpoint_usage

**Bronze Source:** `system.serving.endpoint_usage` → Bronze: `endpoint_usage`
**Gold Table:** `fact_endpoint_usage`

### fact_payload_logs

**Bronze Source:** Model serving inference logs
**Gold Table:** `fact_payload_logs`

---

## Domain 10: Data Quality Monitoring (2 tables)

### fact_data_quality_monitoring_table_results

**Bronze Source:** `system.data_quality_monitoring.table_results` (non-streaming)
**Gold Table:** `fact_data_quality_monitoring_table_results`

### fact_data_classification_results

**Bronze Source:** `system.data_classification.results` (non-streaming)
**Gold Table:** `fact_data_classification_results`

---

## Domain 11: Marketplace (2 tables)

### fact_listing_funnel

**Bronze Source:** `system.marketplace.listing_funnel_events` → Bronze: `listing_funnel_events`
**Gold Table:** `fact_listing_funnel`

### fact_listing_access

**Bronze Source:** `system.marketplace.listing_access_events` → Bronze: `listing_access_events`
**Gold Table:** `fact_listing_access`

---

## Domain 12: Storage (1 table)

### fact_predictive_optimization

**Bronze Source:** `system.storage.predictive_optimization_operations_history` (non-streaming)
**Gold Table:** `fact_predictive_optimization`

---

## Standard PySpark Transformations

### Flattening Nested Structs

```python
from pyspark.sql.functions import col

def flatten_struct(df, struct_column, fields):
    """Flatten a struct column into individual columns."""
    for field in fields:
        df = df.withColumn(f"{struct_column}_{field}", col(struct_column).getField(field))
    return df

# Example: Flatten usage_metadata
fields = ["cluster_id", "job_id", "warehouse_id", "notebook_id", ...]
bronze_df = flatten_struct(bronze_df, "usage_metadata", fields)
```

### Converting JSON to MAP

```python
from pyspark.sql.functions import from_json, map_type, string_type

# If custom_tags is JSON string, convert to MAP
df = df.withColumn("custom_tags", 
    from_json(col("custom_tags_json"), map_type(string_type(), string_type())))
```

### Handling NULL Timestamps for Duration

```python
.withColumn("duration_seconds",
    when(col("end_time").isNotNull(),
         unix_timestamp(col("end_time")) - unix_timestamp(col("start_time")))
    .otherwise(None))
```

---

## Validation Checklist for Each Table

Before deploying any merge script:

- [ ] Deduplicate on correct business key
- [ ] Order by timestamp DESC before deduplication
- [ ] Every Gold column has explicit mapping
- [ ] Nested fields use `.getField()` not `["field"]`
- [ ] Data types match DDL exactly
- [ ] Derived columns use `when().otherwise()` for NULL handling
- [ ] MAP/ARRAY types preserved, not converted to JSON
- [ ] Schema validation runs before MERGE
- [ ] Primary key matches DDL
- [ ] Foreign keys reference correct dimension columns

---

## References

- Cursor Rules:
  - [10-gold-layer-merge-patterns.mdc](mdc:.cursor/rules/10-gold-layer-merge-patterns.mdc)
  - [11-gold-delta-merge-deduplication.mdc](mdc:.cursor/rules/11-gold-delta-merge-deduplication.mdc)
  - [23-gold-layer-schema-validation.mdc](mdc:.cursor/rules/23-gold-layer-schema-validation.mdc)
  - [24-fact-table-grain-validation.mdc](mdc:.cursor/rules/24-fact-table-grain-validation.mdc)
- Gold YAML Schemas: `gold_layer_design/yaml/`
- Bronze DLT Pipeline: `src/bronze/streaming/`

---

**Last Updated:** December 9, 2025
**Created By:** AI Agent for Gold Layer Pipeline Development

