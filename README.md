# Databricks Health Monitor

Medallion architecture pipeline for Databricks system tables ingestion into Unity Catalog for health monitoring and observability.

## Overview

This project implements a **Bronze → Gold** direct transformation architecture for Databricks system tables, eliminating the Silver layer for simplified observability:

- **🥉 Bronze Layer** (Complete): Raw ingestion of **35 system tables**
  - **8 DLT Streaming Pipelines** for streaming-capable tables (27 tables)
  - **MERGE operations** for non-streaming tables (8 tables)
  - **Orchestrated execution** via single coordinated workflow

- **🥇 Gold Layer** (Planned - 5 Phases): Star schema dimensional model with analytics and ML
  - **Phase 1**: Core infrastructure (catalog, permissions, alert config)
  - **Phase 2**: Gold dimensional model (~38-40 tables from 35 Bronze)
  - **Phase 3**: Analytics & ML layer (20+ metric views, 7 ML models)
  - **Phase 4**: Mosaic AI Agent framework (5 specialized agents, 40+ tools)
  - **Phase 5**: Alert framework & frontend (Databricks App)

> 📚 **See [Implementation Plans](.cursor/plans/)** for actionable phase-by-phase plans  
> 📐 **See [Architecture Documentation](docs/architecture/)** for comprehensive design specifications

### Architecture

```
Databricks System Tables (system.*)
        ↓
    🥉 Bronze Layer (system_bronze schema) ✅ Complete
        ├── Streaming Ingestion (8 DLT Pipelines)
        │   ├── access (6 tables)
        │   ├── billing (2 tables)
        │   ├── compute (3 tables)
        │   ├── lakeflow (2 tables)
        │   ├── marketplace (1 table)
        │   ├── mlflow (2 tables)
        │   ├── serving (2 tables)
        │   └── sharing (3 tables)
        └── Non-Streaming Ingestion (MERGE operations)
            └── 8 tables (assistant_events, workspaces_latest, etc.)
        ↓
    🥇 Gold Layer (observability.gold schema) 🚧 Planned (5 Phases)
        ├── Phase 1: Core Infrastructure
        │   ├── Unity Catalog setup
        │   ├── Permissions model
        │   └── Alert config table
        ├── Phase 2: Dimensional Model (~38-40 tables)
        │   ├── 23 dimensions (SCD Type 2)
        │   └── 12-15 facts (transaction + aggregate)
        ├── Phase 3: Analytics & ML
        │   ├── 20+ metric views
        │   └── 7 ML models (UC model registry)
        ├── Phase 4: AI Agents
        │   ├── Router + 5 specialized agents
        │   └── 40+ tools (SQL, ML, Action)
        └── Phase 5: Alerts & Frontend
            ├── Lakehouse Monitoring
            ├── SQL Alerts (metadata-driven)
            └── Databricks App (React, 7 pages)
```

## System Tables Ingested

### Streaming Tables (27 tables)

**Access Schema (6 tables):**
- `audit` - All audit events from workspaces
- `clean_room_events` - Clean room lifecycle events
- `column_lineage` - Column-level data lineage
- `inbound_network` - Inbound access denial events
- `outbound_network` - Outbound access denial events
- `table_lineage` - Table-level data lineage

**Billing Schema (1 table):**
- `usage` - Billable usage across account

**Compute Schema (4 tables):**
- `clusters` - Cluster configuration history
- `node_timeline` - Node utilization metrics
- `warehouse_events` - SQL warehouse lifecycle events
- `warehouses` - SQL warehouse configuration history

**Lakeflow Schema (6 tables):**
- `job_run_timeline` - Job run execution timeline
- `job_task_run_timeline` - Task-level execution timeline
- `job_tasks` - Job task definitions
- `jobs` - Job metadata
- `pipeline_update_timeline` - DLT pipeline update timeline
- `pipelines` - DLT pipeline metadata

**Marketplace Schema (2 tables):**
- `listing_funnel_events` - Marketplace listing funnel analytics
- `listing_access_events` - Consumer data access events

**MLflow Schema (3 tables):**
- `experiments_latest` - MLflow experiment metadata
- `runs_latest` - MLflow run metadata
- `run_metrics_history` - MLflow metrics timeseries

**Serving Schema (2 tables):**
- `served_entities` - Model serving endpoint metadata
- `endpoint_usage` - Model serving usage metrics

**Sharing Schema (1 table):**
- `materialization_history` - Delta Sharing materialization events

### Non-Streaming Tables (8 tables)

- `assistant_events` - Databricks Assistant usage
- `workspaces_latest` - Workspace metadata (SCD Type 1)
- `list_prices` - SKU pricing history
- `node_types` - Available node types
- `predictive_optimization_operations_history` - Predictive optimization operations
- `data_classification_results` - Data classification detections
- `data_quality_monitoring_table_results` - Data quality monitoring results
- `query_history` - SQL query execution history

## Project Structure

Organized by **medallion architecture layers** for clear separation:

```
DatabricksHealthMonitor/
├── databricks.yml                   # Main bundle configuration
│
├── src/                             # Source code organized by layer
│   ├── bronze_streaming/            # 🥉 Bronze Layer
│   │   ├── system_access_streaming/
│   │   ├── system_billing_streaming/
│   │   ├── system_compute_streaming/
│   │   ├── system_lakeflow_streaming/
│   │   ├── system_marketplace_streaming/
│   │   ├── system_mlflow_streaming/
│   │   ├── system_serving_streaming/
│   │   ├── system_sharing_streaming/
│   │   ├── system_nonstreaming_setup/
│   │   └── system_nonstreaming_merge/
│   ├── silver_transform/            # 🥈 Silver Layer (reserved)
│   └── gold_aggregates/             # 🥇 Gold Layer (reserved)
│
├── resources/                       # Asset Bundle resources by layer
│   ├── schemas.yml                 # UC schema definitions (all layers)
│   ├── system_tables_orchestrator.yml  # Master orchestrator
│   ├── bronze/                     # 🥉 Bronze resources
│   │   ├── *_streaming_pipeline.yml   # 8 DLT pipeline configs
│   │   ├── nonstreaming_setup_job.yml
│   │   └── nonstreaming_merge_job.yml
│   ├── silver/                     # 🥈 Silver resources (reserved)
│   └── gold/                       # 🥇 Gold resources (reserved)
│
├── .cursor/plans/                 # Cursor buildable implementation plans
│   ├── README.md                  # Plans overview & navigation
│   ├── phase1_core_setup.md       # Phase 1: Core infrastructure
│   ├── phase2_gold_layer.md       # Phase 2: Dimensional model
│   ├── phase3_analytics_ml.md     # Phase 3: Analytics & ML
│   ├── phase4_agent_framework.md  # Phase 4: AI agents
│   └── phase5_alerts_frontend.md  # Phase 5: Alerts & frontend
│
├── docs/                          # Comprehensive design documentation
│   ├── architecture/              # Detailed architecture specs
│   │   ├── README.md              # Architecture docs index
│   │   ├── phase1_core_setup_design.md       # (767 lines)
│   │   ├── phase2_gold_layer_design.md       # (1,988 lines)
│   │   ├── phase3_analytics_ml_design.md     # (542 lines)
│   │   ├── phase4_agent_layer_design.md      # (206 lines)
│   │   ├── phase5_alert_framework_design.md  # (1,218 lines)
│   │   ├── agents/                # Agent-specific designs
│   │   │   ├── cost_agent_design.md
│   │   │   ├── security_agent_design.md
│   │   │   ├── performance_agent_design.md
│   │   │   └── reliability_agent_design.md
│   │   └── frontend/              # Frontend design
│   │       └── app_design.md
│   ├── deployment/
│   ├── operations/
│   └── reference/
│
└── context/                       # Reference materials
    ├── dashboards/               # Pre-built Lakeview dashboards
    ├── prompts/                  # AI agent context
    └── systemtables/             # System table schemas
```

## Prerequisites

- Unity Catalog enabled workspace
- Account admin and metastore admin privileges (for grant access)
- Databricks CLI installed and configured
- Access to system tables granted via Unity Catalog

## Configuration

### 1. Update `databricks.yml`

Edit catalog and warehouse_id variables:

```yaml
variables:
  catalog:
    default: main  # Change to your catalog
  warehouse_id:
    default: ""  # Add your SQL warehouse ID
```

### 2. Update Email Notifications

Edit all YAML files in `resources/` to replace `data-engineering@company.com` with your team's email.

## Deployment

### Initial Deployment (Dev)

```bash
# Validate bundle configuration
databricks bundle validate

# Deploy to dev environment
databricks bundle deploy -t dev

# Run orchestrator manually (first time)
databricks bundle run -t dev system_tables_orchestrator
```

### Production Deployment

```bash
# Deploy to production
databricks bundle deploy -t prod

# Run orchestrator manually (first time)
databricks bundle run -t prod system_tables_orchestrator

# Enable daily schedule in Databricks UI
# Or update resources/system_tables_orchestrator.yml to set pause_status: UNPAUSED
```

## Orchestrator Workflow

The `system_tables_orchestrator` executes in this sequence:

1. **Setup Phase** (1 task)
   - Create/verify 8 non-streaming table structures

2. **Streaming Phase** (8 tasks - parallel execution)
   - Run all 8 DLT pipelines simultaneously
   - Ingest 27 streaming tables

3. **MERGE Phase** (1 task)
   - Sync 8 non-streaming tables via MERGE operations

**Schedule:** Daily at 2 AM UTC (paused by default in dev)

## Individual Job Execution

For testing or manual runs of specific components:

```bash
# Setup non-streaming tables
databricks bundle run -t dev nonstreaming_setup_job

# Run specific DLT pipeline
databricks pipelines start-update --pipeline-name "[dev] System Access Streaming Pipeline"

# Run MERGE for non-streaming tables
databricks bundle run -t dev nonstreaming_merge_job
```

## Monitoring

### Check Orchestrator Status

```sql
-- Job run history
SELECT * FROM system.lakeflow.job_run_timeline
WHERE job_id = '<orchestrator_job_id>'
ORDER BY period_start_time DESC;

-- Task-level details
SELECT * FROM system.lakeflow.job_task_run_timeline
WHERE job_id = '<orchestrator_job_id>'
ORDER BY period_start_time DESC;
```

### Verify Table Ingestion

```sql
-- Check row counts
SELECT 
    'audit' as table_name, COUNT(*) as row_count 
FROM main.system_bronze.audit
UNION ALL
SELECT 
    'usage' as table_name, COUNT(*) as row_count 
FROM main.system_bronze.usage
-- ... repeat for other tables
;

-- Check latest ingestion timestamp
SELECT 
    'audit' as table_name, 
    MAX(bronze_ingestion_timestamp) as latest_ingestion
FROM main.system_bronze.audit
GROUP BY 1
;
```

## Key Features

- ✅ **Serverless-first**: All compute uses serverless for automatic scaling
- ✅ **Schema evolution**: Streaming tables handle schema changes automatically
- ✅ **DLT Direct Publishing Mode**: Modern Unity Catalog integration
- ✅ **Automatic liquid clustering**: All tables use `CLUSTER BY AUTO`
- ✅ **Comprehensive metadata**: All tables have proper governance tags
- ✅ **Error handling**: MERGE jobs continue on failure and report errors
- ✅ **Orchestrated execution**: Single workflow coordinates all ingestion
- ✅ **Daily schedule**: Automated nightly refresh (configurable)

## Table Properties

All tables include standardized properties:
- `layer: bronze`
- `source_system: databricks_system_tables`
- `domain: <access|billing|compute|etc>`
- `entity_type: <fact|dimension>`
- `contains_pii: <true|false>`
- `data_classification: <confidential|internal>`
- `business_owner: Platform Operations`
- `technical_owner: Data Engineering`

## Troubleshooting

### Issue: Schema doesn't exist

```bash
# Manually create schema
databricks bundle deploy -t dev
# This creates the schema automatically via schemas.yml
```

### Issue: DLT pipeline fails with "skipChangeCommits" error

This is expected for system tables. The pattern is already implemented correctly in all DLT notebooks.

### Issue: MERGE fails for specific table

Check the merge_tables.py output for specific error. Common issues:
- Natural key column name mismatch
- Source table empty or unavailable
- Permissions issue

### Issue: Orchestrator timeout

Default timeout is 4 hours. For initial full refresh, this may need adjustment in `resources/system_tables_orchestrator.yml`:

```yaml
timeout_seconds: 21600  # 6 hours
```

## Cleanup

To remove all resources:

```bash
# WARNING: This deletes all tables and pipelines
databricks bundle destroy -t dev
```

To keep data but remove jobs/pipelines:

```bash
# Manually delete jobs/pipelines via UI
# Tables remain in Unity Catalog
```

## Implementation Roadmap

### Current Status: Phase 0 Complete ✅

Bronze layer ingestion is operational. Ready to proceed with Gold layer implementation.

### Next Steps: 5-Phase Implementation

Each phase has a **concise actionable plan** in `.cursor/plans/` and **comprehensive design documentation** in `docs/architecture/`:

| Phase | Focus | Duration | Plan | Design Doc |
|-------|-------|----------|------|------------|
| Phase 1 | Core Infrastructure | Weeks 1-4 | [phase1_core_setup.md](.cursor/plans/phase1_core_setup.md) | [phase1_core_setup_design.md](docs/architecture/phase1_core_setup_design.md) |
| Phase 2 | Gold Dimensional Model | Weeks 5-12 | [phase2_gold_layer.md](.cursor/plans/phase2_gold_layer.md) | [phase2_gold_layer_design.md](docs/architecture/phase2_gold_layer_design.md) |
| Phase 3 | Analytics & ML | Weeks 9-12 | [phase3_analytics_ml.md](.cursor/plans/phase3_analytics_ml.md) | [phase3_analytics_ml_design.md](docs/architecture/phase3_analytics_ml_design.md) |
| Phase 4 | AI Agent Framework | Weeks 13-16 | [phase4_agent_framework.md](.cursor/plans/phase4_agent_framework.md) | [phase4_agent_layer_design.md](docs/architecture/phase4_agent_layer_design.md) |
| Phase 5 | Alerts & Frontend | Weeks 13-16 | [phase5_alerts_frontend.md](.cursor/plans/phase5_alerts_frontend.md) | [phase5_alert_framework_design.md](docs/architecture/phase5_alert_framework_design.md) |

**How to Use:**

1. **Review Plan:** Start with the concise plan (e.g., `phase1_core_setup.md`)
2. **Deep Dive:** Reference the comprehensive design doc for full specifications
3. **Build:** Use Cursor's "Build" option on the plan file
4. **Validate:** Complete the validation checklist in each plan
5. **Iterate:** Move to next phase upon completion

**Documentation Structure:**

- **`.cursor/plans/`** - Concise, actionable implementation steps (<200 lines each)
- **`docs/architecture/`** - Comprehensive design specs (700-2,000 lines each)

## References

- [System Tables Documentation](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Streaming System Tables](https://docs.databricks.com/aws/en/admin/system-tables/#considerations-for-streaming-system-tables)
- [DLT Direct Publishing Mode](https://docs.databricks.com/aws/en/delta-live-tables/unity-catalog.html)
- [Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)

## Support

For questions or issues:
1. Check Databricks system tables documentation
2. Review DLT pipeline event logs in Databricks UI
3. Check orchestrator job run history
4. Contact: data-engineering@company.com

## License

Internal use only - Platform Operations team.

