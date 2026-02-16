# Bronze Layer Architecture Overview

## Purpose

The Bronze layer ingests all Databricks System Tables into persistent Delta tables within Unity Catalog, preserving data indefinitely beyond the system tables' rolling retention windows (30–365 days depending on the table). Without archival, historical data is silently deleted by Delta Sharing VACUUM operations on the source tables.

This layer is the foundation of the Databricks Health Monitor: every Gold-layer dimension, fact table, ML feature, and metric view traces its lineage back to these Bronze tables.

## System Architecture

```
+---------------------------------------------------------------------------------+
| Databricks Workspace                                                            |
|                                                                                 |
| +--------------------------+                                                    |
| | system.* (Source Tables) | <-- Rolling retention (30-365 days)                |
| | Delivered via Delta      | <-- VACUUM after 7 days                           |
| | Sharing                  |                                                    |
| +--------+-----------------+                                                    |
|          |                                                                      |
|          | Daily triggered workflow (2am UTC)                                    |
|          |                                                                      |
| +--------v-----------------------------------------------------------------+    |
| | Workflow: Bronze Refresh Job                                             |    |
| |                                                                          |    |
| | +------------------+ +------------------+ +----------------+ +---------+ |    |
| | | Task 1: SDP      | | Task 2: Dedup    | | Task 3: DQX    | | Task 4: | |    |
| | | Pipeline         |→| Streaming Sinks  |→| Validation     |→| Batch   | |    |
| | |                  | |                  | |                | | MERGE   | |    |
| | | 24 streaming     | | Skip if clean    | | Quarantine bad | | 9 non-  | |    |
| | | tables via       | | INSERT OVERWRITE | | records via    | | stream  | |    |
| | | append_flow +    | | if dupes found   | | DQX engine     | | tables  | |    |
| | | Delta sinks      | | + CLUSTER BY AUTO| | + SQL fallback | |         | |    |
| | +------------------+ +------------------+ +----------------+ +---------+ |    |
| +-------------------------------------------------------------------+------+    |
|          |                                                                      |
| +--------v-----------------------------------------------------------------+    |
| | ${catalog}.${system_bronze_schema}   (Persistent Archive)                |    |
| |                                                                          |    |
| | 1 schema, 33 tables + quarantine tables                                  |    |
| | CLUSTER BY AUTO + Predictive Optimization enabled                        |    |
| | CDF, auto-optimize, governance tags on all tables                        |    |
| | No retention limit — data preserved indefinitely                         |    |
| +-------------------------------------------------------------------+------+    |
|                                                                                 |
| +--------------------------+    +--------------------------+                    |
| | Bronze Setup Job         |    | Master Setup Orchestrator|                    |
| | Manual trigger only      |    | References Bronze Setup  |                    |
| | Creates 9 non-streaming  |    | as first step            |                    |
| | tables + DQ rules table  |    |                          |                    |
| | + Predictive Optimization|    |                          |                    |
| +--------------------------+    +--------------------------+                    |
+---------------------------------------------------------------------------------+
```

## Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| **Bronze Setup Job** | Manual (one-time) | Creates 9 non-streaming Bronze tables, seeds DQ rules table, enables Predictive Optimization at schema level |
| **Bronze Refresh Job** | Daily 2am UTC (via orchestrator) | Streaming pipeline → Dedup → DQX validation → Non-streaming MERGE |
| **Master Setup Orchestrator** | Manual (one-time) | References Bronze Setup as first step, then Gold, Semantic, Monitoring, Alerting, ML |
| **Master Refresh Orchestrator** | Daily 2am UTC (PAUSED) | References Bronze Refresh as first step, then Gold Merge, Monitoring Refresh, ML Inference |

## Design Principles

### 1. Never Delete Archive Data

Sinks are append-only. Full Refresh re-appends — it never drops or truncates the target table. This is the fundamental safety guarantee of the archive. The dedup task cleans up any resulting duplicates automatically.

### 2. Streaming First, Batch as Fallback

Streaming via SDP Delta sinks is the preferred ingestion method because it provides checkpoint-based incremental reads with exactly-once semantics. Batch MERGE is used only when the source table does not support streaming (see [bronze-ingestion-strategy.md](bronze-ingestion-strategy.md)).

### 3. Quality Gates, Not Blockers

DQX validation runs after dedup but is **non-blocking** — it quarantines invalid records to `{table}_quarantine` tables rather than failing the pipeline. This ensures data always flows downstream while quality issues are visible and auditable.

### 4. Minimize Daily Compute Cost

- **Streaming tables**: Read only new data since last checkpoint (incremental by design).
- **Dedup step**: Checks for duplicates first; only rewrites tables that actually have dupes (scan-only on clean tables, ~3–5 min steady-state).
- **Non-streaming MERGE**: Reads full source and MERGEs on natural keys — acceptable because these are small reference tables or tables that require full-scan patterns.
- **Table optimizations**: `CLUSTER BY AUTO` and Predictive Optimization reduce scan costs for downstream Gold queries.

### 5. Fail Safe, Continue On Error

- Each streaming flow is independent; one failure does not block others.
- Non-streaming MERGE tables are wrapped in try/except; failures are logged and counted but don't stop other tables from processing.
- The job raises a `RuntimeError` at the end if any table failed, so the orchestrator correctly reports partial failure.

### 6. Governance by Default

Every table receives standard TBLPROPERTIES during the dedup step:
- `layer`, `source_system`, `domain`, `entity_type`
- `contains_pii`, `data_classification`
- `business_owner`, `technical_owner`
- `delta.enableChangeDataFeed`, `delta.autoOptimize.*`

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Streaming pipeline | SDP (`pyspark.pipelines`) | Incremental streaming with Delta sinks (`dp.create_sink` + `dp.append_flow`) |
| Dedup notebook | Databricks Notebook (Serverless) | Post-pipeline duplicate removal with skip optimization |
| DQX validation | Databricks Labs DQX | Post-dedup data quality checks with quarantine |
| Batch MERGE | Databricks Notebook (Serverless) | Full-scan MERGE for non-streaming tables |
| Packaging | Databricks Asset Bundles | Multi-environment deployment (dev/prod) |
| Compute | Serverless | No cluster management overhead |
| Storage | Delta Lake (Unity Catalog) | ACID transactions, schema evolution, CDF |
| Table optimization | Liquid Clustering + Predictive Optimization | Auto-tuned layout and maintenance |
| Quality framework | DQX + YAML check definitions | Declarative DQ rules with quarantine strategy |

## Data Flow

| Step | Component | Action |
|------|-----------|--------|
| 1 | Workflow scheduler | Triggers Bronze Refresh Job (daily or on-demand) |
| 2 | SDP Pipeline (Task 1) | Reads incrementally from 24 system tables via `readStream` with `skipChangeCommits=true`. 2 tables with DeletionVectors use `responseFormat=delta`. Adds `bronze_ingestion_timestamp` to every row. |
| 3 | Delta Sinks | Appends new rows to archive tables in `${catalog}.${system_bronze_schema}`. Tables are auto-created on first write by `dp.create_sink`. |
| 4 | Dedup Notebook (Task 2) | Runs after pipeline completes (`run_if: ALL_DONE`). |
| 5 | Duplicate check | For each of 24 streaming tables, checks for duplicate key groups via `GROUP BY ... HAVING COUNT(*) > 1 LIMIT 1`. If clean, skips the table (no rewrite). |
| 6 | Dedup rewrite | If duplicates found, uses `INSERT OVERWRITE` with `ROW_NUMBER()` to atomically remove them. Ensures `CLUSTER BY AUTO` and governance TBLPROPERTIES on all tables. |
| 7 | DQX Validation (Task 3) | Loads check definitions from `bronze_dqx_checks.yaml`. Applies DQX `apply_checks_by_metadata_and_split()` to each table. Quarantines invalid records. Falls back to SQL-based validation if DQX is unavailable. |
| 8 | Non-streaming MERGE (Task 4) | MERGEs 9 batch tables from system sources using natural keys. Adds `bronze_ingestion_timestamp` to every row. Some tables pre-deduplicate the source (e.g., `data_classification_results`, `pipeline_update_timeline`). |

## File Structure

```
src/pipelines/bronze/
├── streaming/
│   └── streaming_archive.py               # SDP pipeline: 24 Delta sinks + append flows
├── dedup/
│   └── dedup_streaming_tables.py          # Dedup + CLUSTER BY AUTO + TBLPROPERTIES
├── dqx/
│   ├── validate_bronze_tables.py          # DQX validation engine
│   └── bronze_dqx_checks.yaml            # Declarative DQ check definitions
├── nonstreaming/
│   ├── setup.py                           # Create non-streaming Bronze tables (9)
│   └── merge.py                           # MERGE non-streaming tables from sources
├── setup_dq_rules.py                      # Create and populate dq_rules table
└── setup/
    ├── create_dq_rules_table.py           # DDL for dq_rules table
    └── populate_dq_rules.py               # Seed 130+ DQ rules

resources/pipelines/bronze/
├── bronze_streaming_pipeline.yml          # SDP pipeline resource definition
├── bronze_refresh_job.yml                 # 4-task refresh workflow
├── bronze_setup_job.yml                   # One-time setup workflow
└── dq_rules_setup_job.yml                 # DQ rules table setup
```

## Integration Points

| Integration | Direction | Protocol | Notes |
|-------------|-----------|----------|-------|
| Delta Sharing (system tables) | Inbound | Delta Sharing | Source tables delivered via sharing; requires `skipChangeCommits=true`. 2 tables require `responseFormat=delta` for DeletionVectors compatibility. |
| Unity Catalog | Bidirectional | UC API | Archive tables are UC-managed Delta tables with governance metadata |
| Gold Layer | Downstream | CDF / Table reads | Gold MERGE jobs read from Bronze tables. `bronze_ingestion_timestamp` used for downstream dedup. |
| DQX Framework | Internal | Python API | `databricks-labs-dqx` library for quality validation with quarantine |
| Email notifications | Outbound | SMTP | Failure and duration-warning alerts |

## Differences from Reference Architecture

This implementation is based on [databricks-system-tables-archival](https://github.com/prashsub/databricks-system-tables-archival) with the following adaptations for the Health Monitor project:

| Aspect | Reference | Health Monitor |
|--------|-----------|----------------|
| **Schema layout** | 12 schemas (one per domain) | 1 schema (all tables in `system_bronze`) |
| **Streaming tables** | 27 (includes `sharing.materialization_history`, `lakeflow.zerobus_*`) | 24 (excludes sharing + zerobus; adds them differently or omits) |
| **Non-streaming tables** | 10 (4 watermark MERGE + 6 full overwrite) | 9 (all MERGE-based, no separate overwrite strategy) |
| **DeletionVector tables** | 4 (`inbound_network`, `pipeline_update_timeline`, `zerobus_stream`, `zerobus_ingest`) | 2 in streaming (`inbound_network`, `pipeline_update_timeline`); `pipeline_update_timeline` also has a non-streaming MERGE path |
| **Data quality** | None (no expectations on sinks) | DQX framework with YAML-defined checks and quarantine tables |
| **Governance tags** | `CLUSTER BY AUTO` only | `CLUSTER BY AUTO` + TBLPROPERTIES (CDF, auto-optimize, layer, domain, PII, classification, owner) |
| **Downstream** | Standalone archive | Feeds Gold layer (39 tables), ML models (25), dashboards (6), Genie Spaces (5) |
| **Freshness alerting** | Separate SQL alert job (48h threshold) | Not yet implemented (planned) |

## Version History

| Date | Change | Impact |
|------|--------|--------|
| Feb 2026 | Refactored from DLT `@dlt.table` to SDP `dp.create_sink` + `dp.append_flow` | Full refresh no longer destroys historical data; 24 old STREAMING_TABLE-type tables dropped and recreated as regular Delta tables |
| Feb 2026 | Added DQX validation step | Post-pipeline quality checks with quarantine, replacing DLT expectations |
| Feb 2026 | Added governance TBLPROPERTIES in dedup step | All streaming tables now tagged with domain, layer, PII classification |
| Feb 2026 | Refactored DQX `find_yaml_path()` | Replaced `os.walk("/Workspace/Users")` with deterministic path resolution for performance |
