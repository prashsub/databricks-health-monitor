# Alerting Framework Architecture

**Version:** 2.0  
**Last Updated:** December 30, 2025

---

## System Overview

The Alerting Framework is a **config-driven SQL alerting system** built on:

- **Delta Lake** for configuration storage
- **Databricks SQL Alerts v2** for native alerting infrastructure
- **REST API** for deployment resilience
- **Unity Catalog** for data governance

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW                                          │
└─────────────────────────────────────────────────────────────────────────────┘

 ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
 │   User/Admin  │     │  DAB Deploy   │     │  Scheduled    │
 │   INSERT/     │     │  Job          │     │  Refresh      │
 │   UPDATE      │     │               │     │               │
 └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
         │                     │                     │
         ▼                     │                     │
 ┌───────────────────┐         │                     │
 │ alert_            │         │                     │
 │ configurations    │◄────────┘                     │
 │ (Delta Table)     │                               │
 └─────────┬─────────┘                               │
           │                                         │
           │ Read enabled configs                    │
           ▼                                         │
 ┌───────────────────┐                               │
 │ Query Validator   │ ◄── SQL syntax + security    │
 └─────────┬─────────┘     checks                   │
           │                                         │
           │ If valid                                │
           ▼                                         │
 ┌───────────────────┐                               │
 │ notification_     │                               │
 │ destinations      │ ◄── Map channel IDs to UUIDs │
 └─────────┬─────────┘                               │
           │                                         │
           │ Build payload                           │
           ▼                                         │
 ┌───────────────────┐                               │
 │ Alert Sync Engine │                               │
 │ (REST API Client) │                               │
 └─────────┬─────────┘                               │
           │                                         │
           │ POST/PATCH/DELETE                       │
           ▼                                         │
 ┌───────────────────┐                               │
 │ Databricks SQL    │                               │
 │ Alerts v2 API     │                               │
 └─────────┬─────────┘                               │
           │                                         │
           │ Creates/Updates alerts                  │
           ▼                                         │
 ┌───────────────────┐     ┌───────────────────┐    │
 │ SQL Alert         │────►│ Alert Evaluator   │◄───┘
 │ (in Workspace)    │     │ (Databricks)      │
 └───────────────────┘     └─────────┬─────────┘
                                     │
                                     │ On trigger
                                     ▼
                           ┌───────────────────┐
                           │ Notification      │
                           │ Destinations      │
                           │ (Email/Slack/etc) │
                           └───────────────────┘
```

---

## Table Schema

### alert_configurations

Primary configuration table for all alert rules.

```sql
CREATE TABLE alert_configurations (
    -- Identity
    alert_id STRING NOT NULL,           -- PK: COST-001, PERF-003
    alert_name STRING NOT NULL,         -- Display name
    alert_description STRING,           -- Detailed description
    
    -- Classification
    agent_domain STRING NOT NULL,       -- COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY
    severity STRING NOT NULL,           -- CRITICAL, WARNING, INFO
    
    -- Query Configuration
    alert_query_template STRING NOT NULL,  -- SQL with ${catalog}/${gold_schema} placeholders
    query_source STRING,                   -- CUSTOM, TVF, METRIC_VIEW, MONITORING
    source_artifact_name STRING,           -- Reference to source artifact
    
    -- Threshold Configuration
    threshold_column STRING NOT NULL,      -- Column to evaluate
    threshold_operator STRING NOT NULL,    -- >, <, >=, <=, =, !=
    threshold_value_type STRING NOT NULL,  -- DOUBLE, STRING, BOOLEAN
    threshold_value_double DOUBLE,
    threshold_value_string STRING,
    threshold_value_bool BOOLEAN,
    
    -- Evaluation Configuration
    empty_result_state STRING NOT NULL,    -- OK, TRIGGERED, ERROR
    aggregation_type STRING,               -- SUM, COUNT, AVG, MIN, MAX, FIRST
    
    -- Schedule Configuration
    schedule_cron STRING NOT NULL,         -- Quartz cron expression
    schedule_timezone STRING NOT NULL,     -- IANA timezone
    pause_status STRING NOT NULL,          -- UNPAUSED, PAUSED
    is_enabled BOOLEAN NOT NULL,           -- Whether to deploy
    
    -- Notification Configuration
    notification_channels ARRAY<STRING> NOT NULL,  -- Channel IDs or emails
    notify_on_ok BOOLEAN NOT NULL,
    retrigger_seconds INT,
    
    -- Custom Templates
    use_custom_template BOOLEAN NOT NULL,
    custom_subject_template STRING,
    custom_body_template STRING,
    
    -- Ownership
    owner STRING NOT NULL,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING,
    updated_at TIMESTAMP,
    tags MAP<STRING, STRING>,
    
    -- Sync Metadata
    databricks_alert_id STRING,            -- Deployed alert UUID
    databricks_display_name STRING,        -- Deployed display name
    last_synced_at TIMESTAMP,
    last_sync_status STRING,
    last_sync_error STRING,
    
    CONSTRAINT pk_alert_configurations PRIMARY KEY (alert_id) NOT ENFORCED
);
```

### notification_destinations

Maps internal channel IDs to Databricks workspace destination UUIDs.

```sql
CREATE TABLE notification_destinations (
    destination_id STRING NOT NULL,         -- PK: Your internal ID
    destination_name STRING NOT NULL,       -- Display name
    destination_type STRING NOT NULL,       -- EMAIL, SLACK, WEBHOOK, TEAMS, PAGERDUTY
    databricks_destination_id STRING,       -- Workspace destination UUID
    config_json STRING,                     -- Type-specific config
    owner STRING NOT NULL,
    is_enabled BOOLEAN NOT NULL,
    created_by STRING NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by STRING,
    updated_at TIMESTAMP,
    tags MAP<STRING, STRING>,
    
    CONSTRAINT pk_notification_destinations PRIMARY KEY (destination_id) NOT ENFORCED
);
```

### alert_sync_metrics

Observability table for sync operations.

```sql
CREATE TABLE alert_sync_metrics (
    sync_run_id STRING NOT NULL,           -- UUID per sync operation
    sync_started_at TIMESTAMP NOT NULL,
    sync_ended_at TIMESTAMP NOT NULL,
    
    -- Counts
    total_alerts INT NOT NULL,
    success_count INT NOT NULL,
    error_count INT NOT NULL,
    created_count INT NOT NULL,
    updated_count INT NOT NULL,
    deleted_count INT NOT NULL,
    skipped_count INT NOT NULL,
    
    -- Latency
    avg_api_latency_ms DOUBLE NOT NULL,
    max_api_latency_ms DOUBLE NOT NULL,
    min_api_latency_ms DOUBLE NOT NULL,
    p95_api_latency_ms DOUBLE NOT NULL,
    total_duration_seconds DOUBLE NOT NULL,
    
    -- Context
    dry_run BOOLEAN NOT NULL,
    catalog STRING NOT NULL,
    gold_schema STRING NOT NULL,
    error_summary STRING,
    
    CONSTRAINT pk_alert_sync_metrics PRIMARY KEY (sync_run_id) NOT ENFORCED
);
```

---

## Component Architecture

### Sync Engine Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYNC ENGINE                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Load Configuration                                          │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ SELECT * FROM alert_configurations                   │     │
│     │ WHERE is_enabled = TRUE                              │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  2. Build Notification Subscriptions                            │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ Map channel_ids -> databricks_destination_id         │     │
│     │ Or use direct email addresses                        │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  3. Render Query Templates                                      │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ ${catalog} -> actual_catalog                         │     │
│     │ ${gold_schema} -> actual_schema                      │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  4. Build API Payload                                           │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ display_name, query_text, warehouse_id, schedule,    │     │
│     │ evaluation, notification                              │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  5. SDK Calls via WorkspaceClient.alerts_v2                     │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ ws.alerts_v2.create_alert(alert)                     │     │
│     │ ws.alerts_v2.update_alert(id, alert, update_mask)    │     │
│     │ ws.alerts_v2.trash_alert(id)                         │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  6. Update Config Table                                         │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ SET databricks_alert_id, last_synced_at,             │     │
│     │     last_sync_status, last_sync_error                │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  7. Log Metrics                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ INSERT INTO alert_sync_metrics (...)                 │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Query Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   QUERY VALIDATOR                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: SQL query template + catalog + schema                   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 1: Render Template                                 │     │
│  │         ${catalog} -> my_catalog                        │     │
│  │         ${gold_schema} -> gold                          │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 2: Security Check (No Spark Required)              │     │
│  │         - Detect DROP TABLE, DELETE, TRUNCATE           │     │
│  │         - Detect UPDATE SET, ALTER TABLE                │     │
│  │         - Categorize as ERROR or WARNING                │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 3: Syntax Validation (Requires Spark)              │     │
│  │         EXPLAIN <query>                                 │     │
│  │         Catches SQL syntax errors                       │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 4: Reference Validation (Requires Spark)           │     │
│  │         DESCRIBE TABLE <extracted_table>                │     │
│  │         Verifies all referenced tables exist            │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  Output: ValidationResult                                       │
│          - is_valid: bool                                       │
│          - errors: List[str]                                    │
│          - warnings: List[str]                                  │
│          - tables_referenced: Set[str]                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Job Architecture

### Hierarchical Job Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                LAYER 2: COMPOSITE JOB                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  alerting_layer_setup_job                                       │
│  ├── Task: setup_alerting_tables                                │
│  │         │                                                     │
│  │         ├──────────────────────────────┐                     │
│  │         ▼                              ▼                     │
│  ├── Task: validate_alert_queries   sync_notification_dests     │
│  │         │                              │                     │
│  │         └──────────────────────────────┘                     │
│  │                       │                                      │
│  │                       ▼                                      │
│  └── Task: deploy_sql_alerts                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                LAYER 1: ATOMIC JOBS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  alert_query_validation_job                                     │
│  └── Task: validate_alert_queries                               │
│                                                                  │
│  sql_alert_deployment_job                                       │
│  └── Task: sync_sql_alerts                                      │
│                                                                  │
│  alerting_tables_setup_job                                      │
│  └── Task: setup_alerting_tables                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### API Authentication
- Uses notebook context token (no explicit PAT required)
- Token obtained from `dbutils.notebook.entry_point.getDbutils().notebook().getContext()`

### SQL Injection Prevention
- All string values escaped with `replace("'", "''")`
- Config table updates use safe escaping

### Query Security
- Pre-deployment validation detects dangerous patterns
- DROP, DELETE, TRUNCATE are blocked
- ALTER, INSERT, UPDATE trigger warnings

### Access Control
- Tables use Unity Catalog governance
- Job permissions controlled via DAB permissions block
- Notification destination creation requires admin

---

## Performance Considerations

### Parallel Sync
- Optional parallel sync with configurable workers (default: 5)
- Uses ThreadPoolExecutor for concurrent API calls
- Config table updates remain sequential to avoid conflicts

### API Rate Limits
- Built-in retry logic with exponential backoff
- Configurable retry count (default: 3)
- Timeout protection (default: 60s)

### Large Alert Counts
- Recommended: Enable parallel sync for >10 alerts
- Pagination support for listing existing alerts

