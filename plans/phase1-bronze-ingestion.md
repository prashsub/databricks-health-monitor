# Phase 1: Bronze Layer Ingestion from System Tables

## Overview

**Status:** ✅ Implemented  
**Purpose:** Ingest Databricks system tables into a Bronze layer using Delta Live Tables (DLT) streaming pipelines with comprehensive data quality rules.

---

## Architecture Summary

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATABRICKS SYSTEM TABLES                              │
│                                                                              │
│  system.access.*    system.billing.*    system.compute.*    system.lakeflow.*│
│  system.mlflow.*    system.serving.*    system.marketplace.*                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DLT STREAMING PIPELINE (Serverless)                       │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Access    │  │   Billing   │  │   Compute   │  │  Lakeflow   │        │
│  │  3 tables   │  │  2 tables   │  │  4 tables   │  │  5 tables   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │   MLflow    │  │   Serving   │  │ Marketplace │                         │
│  │  3 tables   │  │  2 tables   │  │  2 tables   │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│                                                                              │
│                        Data Quality Expectations                             │
│                     (Critical + Warning severity)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRONZE SCHEMA (Unity Catalog)                        │
│                                                                              │
│           21 Streaming Tables + DQ Rules Configuration Table                 │
│                     (CDF enabled, auto-optimized)                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Tables Coverage

### Streaming-Compatible Tables (21 Active)

| Domain | Table | System Path | Retention |
|--------|-------|-------------|-----------|
| **Access** | audit | system.access.audit | 365 days |
| **Access** | column_lineage | system.access.column_lineage | 365 days |
| **Access** | table_lineage | system.access.table_lineage | 365 days |
| **Access** | outbound_network | system.access.outbound_network | 365 days |
| **Access** | clean_room_events | system.access.clean_room_events | 365 days |
| **Billing** | usage | system.billing.usage | 365 days |
| **Compute** | clusters | system.compute.clusters | 365 days |
| **Compute** | node_timeline | system.compute.node_timeline | 90 days |
| **Compute** | warehouse_events | system.compute.warehouse_events | 365 days |
| **Compute** | warehouses | system.compute.warehouses | 365 days |
| **Lakeflow** | jobs | system.lakeflow.jobs | 365 days |
| **Lakeflow** | job_tasks | system.lakeflow.job_tasks | 365 days |
| **Lakeflow** | job_run_timeline | system.lakeflow.job_run_timeline | 365 days |
| **Lakeflow** | job_task_run_timeline | system.lakeflow.job_task_run_timeline | 365 days |
| **Lakeflow** | pipelines | system.lakeflow.pipelines | 365 days |
| **Marketplace** | listing_funnel_events | system.marketplace.listing_funnel_events | 365 days |
| **Marketplace** | listing_access_events | system.marketplace.listing_access_events | 365 days |
| **MLflow** | experiments_latest | system.mlflow.experiments_latest | 180 days |
| **MLflow** | runs_latest | system.mlflow.runs_latest | 180 days |
| **MLflow** | run_metrics_history | system.mlflow.run_metrics_history | 180 days |
| **Serving** | served_entities | system.serving.served_entities | 365 days |
| **Serving** | endpoint_usage | system.serving.endpoint_usage | 90 days |

### Disabled Tables (3)

| Table | Reason |
|-------|--------|
| inbound_network | Deletion Vectors incompatible with DLT streaming |
| pipeline_update_timeline | Deletion Vectors incompatible with DLT streaming |
| materialization_history | Table doesn't exist in account |

### Non-Streaming Tables (Handled Separately)

| Domain | Table | System Path | Notes |
|--------|-------|-------------|-------|
| Billing | list_prices | system.billing.list_prices | Non-streaming |
| Compute | node_types | system.compute.node_types | Non-streaming |
| Access | workspaces_latest | system.access.workspaces_latest | Non-streaming |
| Storage | predictive_optimization | system.storage.predictive_optimization_operations_history | Non-streaming |
| Query | history | system.query.history | Non-streaming |

---

## Implementation Details

### Asset Bundle Structure

```
resources/bronze/
├── bronze_streaming_pipeline.yml    # DLT pipeline definition
├── bronze_setup_job.yml             # Non-streaming table setup
├── bronze_refresh_job.yml           # Manual refresh job
└── dq_rules_setup_job.yml           # DQ rules configuration

src/bronze/
├── streaming/
│   ├── access_tables.py             # Access domain DLT notebook
│   ├── billing_tables.py            # Billing domain DLT notebook
│   ├── compute_tables.py            # Compute domain DLT notebook
│   ├── lakeflow_tables.py           # Lakeflow domain DLT notebook
│   ├── marketplace_tables.py        # Marketplace domain DLT notebook
│   ├── mlflow_tables.py             # MLflow domain DLT notebook
│   ├── serving_tables.py            # Serving domain DLT notebook
│   ├── dq_rules_loader.py           # Dynamic DQ rules loader
│   └── static_dq_rules.py           # Fallback static rules
├── nonstreaming/
│   ├── setup.py                     # Create non-streaming tables
│   └── merge.py                     # MERGE updates for non-streaming
├── setup_dq_rules.py                # DQ rules table setup
└── setup/
    ├── create_dq_rules_table.py     # Table DDL
    └── populate_dq_rules.py         # Rule population
```

### DLT Pipeline Configuration

```yaml
# Key Settings
serverless: true
photon: true
edition: ADVANCED
continuous: false
development: true

# Direct Publishing Mode
catalog: ${var.catalog}
schema: ${var.system_bronze_schema}

# Table Properties (via notebooks)
delta.enableChangeDataFeed: true
delta.autoOptimize.optimizeWrite: true
delta.autoOptimize.autoCompact: true
```

### Data Quality Strategy

#### Rule Severity Levels

| Severity | Behavior | Use Case |
|----------|----------|----------|
| **Critical** | Drop records on failure | Required fields, data integrity |
| **Warning** | Log but pass records | Business logic, reasonableness |

#### Rule Categories

1. **Identity Rules**: Primary key/identifier presence
   - `workspace_id IS NOT NULL`
   - `job_id IS NOT NULL AND LENGTH(job_id) > 0`

2. **Temporal Rules**: Timestamp validity
   - `event_time IS NOT NULL`
   - `event_time <= CURRENT_TIMESTAMP()`

3. **Enum Validation**: Value constraint checking
   - `audit_level IN ('ACCOUNT_LEVEL', 'WORKSPACE_LEVEL')`
   - `cloud IN ('AWS', 'AZURE', 'GCP')`

4. **Business Rules**: Logical constraints
   - `usage_end_time >= usage_start_time`
   - `usage_quantity >= 0`

#### Rule Storage

```sql
-- dq_rules table schema
CREATE TABLE dq_rules (
  table_name STRING NOT NULL,
  rule_name STRING NOT NULL,
  rule_constraint STRING NOT NULL,
  severity STRING NOT NULL,
  enabled BOOLEAN NOT NULL,
  description STRING,
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_dq_rules PRIMARY KEY (table_name, rule_name) NOT ENFORCED
)
```

---

## Deployment

### Prerequisites

1. Unity Catalog enabled
2. System tables enabled for account
3. Serverless compute available
4. Service principal with system table access

### Deployment Commands

```bash
# Validate bundle
databricks bundle validate

# Deploy to dev
databricks bundle deploy -t dev

# Create DQ rules table
databricks bundle run -t dev dq_rules_setup_job

# Start streaming pipeline
databricks bundle run -t dev bronze_streaming_pipeline

# Setup non-streaming tables
databricks bundle run -t dev bronze_setup_job
```

### Monitoring

- DLT pipeline runs automatically on schedule
- CDF enabled for downstream incremental processing
- DQ metrics available in pipeline event log

---

## Table Properties

All Bronze tables include:

```sql
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'layer' = 'bronze',
  'source_system' = 'databricks_system_tables',
  'domain' = '<domain_name>'
)
```

---

## Success Criteria

- [ ] 21 streaming tables ingesting successfully
- [ ] DQ rules applied with critical/warning separation
- [ ] CDF enabled for downstream processing
- [ ] < 15 minute latency from source
- [ ] 99.9% pipeline uptime

---

## References

- [Databricks System Tables Overview](https://docs.databricks.com/en/admin/system-tables/)
- [Delta Live Tables Documentation](https://docs.databricks.com/en/dlt/)
- [DLT Expectations](https://docs.databricks.com/en/dlt/expectations.html)

