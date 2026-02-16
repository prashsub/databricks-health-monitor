# Bronze Layer Ingestion Strategy

## Decision Framework

Every Databricks system table is assigned to one of two ingestion strategies based on a decision tree:

```
Is the table streaming-capable (per Databricks docs)?
  |
  +-- YES --> STRATEGY A: SDP Streaming + Delta Sink (24 tables)
  |           Note: Tables with DeletionVectors need responseFormat=delta
  |
  +-- NO  --> STRATEGY B: Batch MERGE on Natural Keys (9 tables)
              Some tables pre-deduplicate source before MERGE
```

## Strategy A: SDP Streaming + Delta Sink

**When to use**: Table supports `readStream` via Delta Sharing.

**How it works**:
1. SDP pipeline registers a **Delta sink** per table — a persistent archive table outside the pipeline lifecycle.
2. An `append_flow` reads incrementally from the source with `skipChangeCommits=true`.
3. Tables with upstream DeletionVectors additionally set `responseFormat=delta`.
4. New rows are appended to the sink. Existing data is never modified or deleted.
5. `bronze_ingestion_timestamp` is added to every row for downstream Gold dedup.
6. Checkpoints track exactly where the stream left off.

**Why this is preferred**:
- **Exactly-once semantics**: Checkpoint-based recovery prevents duplicates under normal operation.
- **Minimal compute**: Only reads new data since last checkpoint.
- **No key/watermark guessing**: The stream handles incremental logic automatically.
- **Safe full refresh**: Re-appends to sinks, never deletes. Dedup cleans up automatically.

**Risk**: If the pipeline falls >7 days behind, Delta Sharing VACUUMs the source and checkpoints become unrecoverable. Recovery requires a Full Refresh (which is safe).

**Post-pipeline processing**:
1. **Dedup** — Checks for duplicate key groups first (`GROUP BY ... HAVING COUNT(*) > 1 LIMIT 1`). If a table is clean, skips the expensive rewrite. If duplicates exist, atomically rewrites with `INSERT OVERWRITE` using `ROW_NUMBER()`.
2. **CLUSTER BY AUTO** — Ensures automatic liquid clustering on every table.
3. **TBLPROPERTIES** — Applies governance tags (layer, domain, entity_type, PII, CDF, auto-optimize).
4. **DQX Validation** — Applies declarative quality checks from YAML; quarantines invalid records.

### Delta Format for DeletionVectors

2 streaming tables have `delta.enableDeletionVectors` enabled upstream. Without `responseFormat=delta`, Delta Sharing returns a `DS_UNSUPPORTED_DELTA_TABLE_FEATURES` error. These tables are flagged with `"delta_format": True` in the streaming config:

- `system.access.inbound_network`
- `system.lakeflow.pipeline_update_timeline`

### Streaming Tables (24)

| Domain | Table | Natural Keys (Dedup) | Tiebreaker | DeletionVectors? |
|--------|-------|---------------------|------------|------------------|
| **access** | `audit` | `event_id` | `event_time` | No |
| | `clean_room_events` | `event_id` | `event_time` | No |
| | `column_lineage` | `record_id` | `event_time` | No |
| | `inbound_network` | `event_id` | `event_time` | **Yes** |
| | `outbound_network` | `event_id` | `event_time` | No |
| | `table_lineage` | `record_id` | `event_time` | No |
| **billing** | `usage` | `record_id` | `usage_date` | No |
| **compute** | `clusters` | `workspace_id`, `cluster_id`, `change_time` | `change_time` | No |
| | `node_timeline` | `cluster_id`, `instance_id`, `start_time` | `start_time` | No |
| | `warehouse_events` | `workspace_id`, `warehouse_id`, `event_type`, `event_time` | `event_time` | No |
| | `warehouses` | `workspace_id`, `warehouse_id`, `change_time` | `change_time` | No |
| **lakeflow** | `job_run_timeline` | `workspace_id`, `run_id`, `period_start_time` | `period_start_time` | No |
| | `job_task_run_timeline` | `workspace_id`, `run_id`, `period_start_time` | `period_start_time` | No |
| | `job_tasks` | `workspace_id`, `job_id`, `task_key`, `change_time` | `change_time` | No |
| | `jobs` | `workspace_id`, `job_id`, `change_time` | `change_time` | No |
| | `pipelines` | `workspace_id`, `pipeline_id`, `change_time` | `change_time` | No |
| | `pipeline_update_timeline` | `workspace_id`, `update_id`, `period_start_time` | `period_start_time` | **Yes** |
| **marketplace** | `listing_funnel_events` | `listing_id`, `event_type`, `event_time`, `consumer_cloud`, `consumer_region` | `event_time` | No |
| | `listing_access_events` | `listing_id`, `event_type`, `event_time`, `consumer_email` | `event_time` | No |
| **mlflow** | `experiments_latest` | `workspace_id`, `experiment_id` | `update_time` | No |
| | `runs_latest` | `workspace_id`, `run_id` | `update_time` | No |
| | `run_metrics_history` | `record_id` | `insert_time` | No |
| **serving** | `served_entities` | `served_entity_id`, `change_time` | `change_time` | No |
| | `endpoint_usage` | `databricks_request_id` | `request_time` | No |

### Natural Key Categories

| Category | Pattern | Tables |
|----------|---------|--------|
| **Event tables with unique ID** | Single `event_id` or `record_id` | `audit`, `clean_room_events`, `column_lineage`, `inbound_network`, `outbound_network`, `table_lineage`, `usage`, `endpoint_usage`, `run_metrics_history` |
| **Snapshot / `_latest` tables** | `workspace_id` + entity ID | `experiments_latest`, `runs_latest` |
| **SCD tables** | Entity ID + `change_time` | `clusters`, `warehouses`, `jobs`, `job_tasks`, `pipelines`, `served_entities` |
| **Timeline tables** | Run/update ID + `period_start_time` | `job_run_timeline`, `job_task_run_timeline`, `pipeline_update_timeline` |
| **Composite key (no unique ID)** | Multiple event attributes | `warehouse_events`, `listing_funnel_events`, `listing_access_events`, `node_timeline` |

---

## Strategy B: Batch MERGE on Natural Keys

**When to use**: Table does not support `readStream` via Delta Sharing, or has characteristics that make streaming impractical.

**How it works**:
1. Read the full source system table.
2. Add `bronze_ingestion_timestamp` column.
3. For tables with potential source duplicates: pre-deduplicate using `ROW_NUMBER()` window function before MERGE.
4. MERGE into the archive table on natural keys with `whenMatchedUpdateAll()` and `whenNotMatchedInsertAll()`.

**Table creation**: Non-streaming tables must be pre-created by the **Bronze Setup Job** (using `CREATE TABLE AS SELECT ... LIMIT 0` or explicit DDL). Unlike streaming sinks which auto-create on first write, MERGE requires the target table to exist.

**Error handling**: Each table is wrapped in try/except. Failures are counted and reported. The job raises `RuntimeError` at the end if any table failed.

### Non-Streaming Tables (9)

| Table | Source | Natural Keys | MERGE Strategy | Notes |
|-------|--------|-------------|----------------|-------|
| `assistant_events` | `system.access.assistant_events` | `event_id` | Standard MERGE | Event table not streaming-capable |
| `workspaces_latest` | `system.access.workspaces_latest` | `workspace_id` | Standard MERGE (SCD1) | Snapshot table, no history |
| `list_prices` | `system.billing.list_prices` | `sku_name`, `cloud`, `price_start_time` | Composite key MERGE | Reference data, infrequent changes |
| `node_types` | `system.compute.node_types` | `account_id`, `node_type` | Composite key MERGE | VM type enumeration, rarely changes |
| `predictive_optimization_operations_history` | `system.storage.predictive_optimization_operations_history` | `operation_id` | Standard MERGE | Optimization event log |
| `data_classification_results` | `system.data_classification.results` | `catalog_name`, `schema_name`, `table_name`, `column_name`, `class_tag` | **Pre-dedup** + composite MERGE | Source has duplicates; keeps latest by `latest_detected_time` |
| `data_quality_monitoring_table_results` | `system.data_quality_monitoring.table_results` | `catalog_name`, `schema_name`, `table_name`, `event_time` | Composite key MERGE | DQ monitoring results |
| `query_history` | `system.query.history` | `statement_id` | MERGE with `update_time` check | Largest table; only updates rows where `source.update_time > target.update_time` |
| `pipeline_update_timeline` | `system.lakeflow.pipeline_update_timeline` | `workspace_id`, `update_id` | **Pre-dedup** + composite MERGE | Has DeletionVectors — incompatible with streaming; keeps latest by `period_end_time` |

### Pre-Dedup Pattern

Two tables require source-side deduplication before MERGE because the source can have multiple rows per natural key:

```python
# Pattern used for data_classification_results and pipeline_update_timeline
window_spec = Window.partitionBy(*natural_key_cols).orderBy(col(tiebreaker).desc())

source_df = (
    spark.table(source_table)
    .withColumn("_row_num", row_number().over(window_spec))
    .filter(col("_row_num") == 1)
    .drop("_row_num")
    .withColumn("bronze_ingestion_timestamp", current_timestamp())
)
```

---

## Why Not Streaming for Everything?

1. **Some tables don't support streaming** — Databricks explicitly documents certain tables as batch-only (e.g., `query.history`, `workspaces_latest`, `node_types`).
2. **DeletionVectors complications** — `pipeline_update_timeline` has DeletionVectors AND source duplicates, making streaming unreliable. A non-streaming MERGE with pre-dedup is more predictable.
3. **Reference tables don't benefit from streaming** — For a table with 200 rows that changes monthly, checkpoint overhead exceeds the cost of a daily full MERGE.

## Why Not Batch for Everything?

1. **Cost**: A full table scan of `system.access.audit` or `system.billing.usage` (millions to billions of rows) every day would be extremely expensive.
2. **Complexity**: MERGE requires knowing the correct natural keys. Incorrect keys cause duplicates (too narrow) or missed updates (too broad).
3. **Correctness**: Streaming provides checkpoint-based incremental reads. MERGE requires full source scans and relies on key correctness.

## Data Quality Strategy

### DQX Checks (Post-Dedup)

All Bronze tables (both streaming and non-streaming) are validated by the DQX framework after dedup:

- **Check definitions**: Declarative YAML (`bronze_dqx_checks.yaml`) — one entry per table with named checks.
- **Check types**: `is_not_null` (critical columns), `is_not_null_and_not_empty` (string columns).
- **Criticality levels**: `error` (quarantine) vs `warning` (log only).
- **Quarantine**: Invalid records written to `{table}_quarantine` tables with `_quarantine_timestamp` and `_quarantine_source` metadata.
- **Fallback**: If `databricks-labs-dqx` is unavailable, SQL-based NULL checks run as a degraded alternative.

### DQ Rules Table

A separate `dq_rules` table (130+ rules for 26 tables) provides a queryable registry of all data quality expectations. This table is seeded by the Bronze Setup Job and can be used for reporting and governance.

## Summary

| Strategy | Tables | Cost Profile | Complexity | Correctness |
|----------|--------|-------------|------------|-------------|
| **A: SDP Streaming** | 24 | Minimal (incremental) | Low (automatic) | High (exactly-once + dedup) |
| **B: Batch MERGE** | 9 | Low–moderate (full scan) | Medium (keys + pre-dedup) | Good (MERGE idempotency) |
| **Total** | **33** | | | |
