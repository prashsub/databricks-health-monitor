# Bronze Layer Operational Considerations

## The 7-Day VACUUM Window

The single most critical operational constraint of this system.

Databricks System Tables are delivered via **Delta Sharing**. The sharing provider runs `VACUUM` on the source tables with a **7-day retention**. This means:

- Data files older than 7 days are permanently deleted from the source.
- Streaming checkpoints reference specific data file versions.
- If the streaming pipeline falls >7 days behind, checkpoints reference deleted files and become **unrecoverable**.

### Recovery When Checkpoint is Stale

1. Run a **Full Refresh** of the SDP pipeline (set `full_refresh: true` in the job or use `databricks pipelines start-update --full-refresh`).
2. This is **safe** — Full Refresh re-appends all currently available data to the sinks. It never drops or truncates existing archive data.
3. The `dedup_streaming_sinks` task runs automatically after the pipeline and removes the resulting duplicates.

### Prevention

- Pipeline runs daily (via the Master Refresh Orchestrator or Bronze Refresh Job).
- Email notifications fire on any task failure.
- **Planned**: Freshness check alert job (48h threshold) to provide 5-day buffer before the 168h VACUUM window.

---

## `skipChangeCommits` Explained

All `readStream` calls use `.option("skipChangeCommits", "true")`. This is required because:

- Delta Sharing source tables undergo rolling deletes (old data is removed as the retention window moves forward).
- Without `skipChangeCommits`, Spark Structured Streaming treats these deletes as change events and fails with an error.
- With `skipChangeCommits`, the stream ignores delete operations and only processes appends — which is exactly what we want for archival.

**Trade-off**: Source-side compaction (OPTIMIZE/VACUUM) can cause a small number of re-inserted rows (~1K) that appear as "new" data. The dedup task catches these automatically.

---

## `responseFormat=delta` for DeletionVectors

2 system tables have `delta.enableDeletionVectors` enabled upstream:

- `system.access.inbound_network`
- `system.lakeflow.pipeline_update_timeline`

Without the `responseFormat=delta` option, Delta Sharing returns a `DS_UNSUPPORTED_DELTA_TABLE_FEATURES` error during `readStream`.

The streaming archive selectively applies this option only to the tables that need it (flagged with `"delta_format": True` in the config).

**Note**: `pipeline_update_timeline` is ingested via BOTH streaming (with `responseFormat=delta`) AND non-streaming MERGE. The non-streaming path exists as a more reliable alternative that also handles source-side deduplication.

---

## Duplicate Handling

Duplicates can occur in three scenarios:

### 1. After Full Refresh (Streaming Tables)

A Full Refresh re-reads all available data and appends it to the sink. Data already in the archive gets appended again.

**Mitigation**: The `dedup_streaming_sinks` task runs automatically after every streaming pipeline execution. It removes duplicates from all 24 streaming sink tables using:

```sql
INSERT OVERWRITE {table}
SELECT * EXCEPT (_row_num)
FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY {natural_keys}
            ORDER BY {tiebreaker} DESC
        ) AS _row_num
    FROM {table}
)
WHERE _row_num = 1
```

**Skip optimization**: The dedup checks for duplicate key groups first using `GROUP BY ... HAVING COUNT(*) > 1 LIMIT 1`. If a table is clean (no duplicates), the expensive `INSERT OVERWRITE` is skipped entirely. This reduces steady-state runtime from ~15 min (full rewrite of all tables) to ~3–5 min (scan-only).

| Scenario | Dedup Runtime | Action Taken |
|----------|--------------|--------------|
| After Full Refresh | ~30+ min | Full `INSERT OVERWRITE` on affected tables |
| Steady state (no/few dupes) | ~3–5 min | Scan-only; skip rewrite on clean tables |

### 2. Source-Side Compaction (skipChangeCommits)

Even on normal incremental runs, a small number of duplicates can appear. This is caused by `skipChangeCommits=true` behavior when Databricks runs OPTIMIZE/VACUUM on source tables:

1. Source table files are compacted (rows deleted from old files, re-inserted into new files).
2. `skipChangeCommits` correctly ignores the delete operations.
3. But the re-inserts from compaction appear as "new" data to the streaming reader.
4. These rows get re-appended to the sink, creating duplicates.

The dedup task catches and removes these automatically. The cost is negligible.

### 3. Non-Streaming MERGE Tables

MERGE operations with `whenMatchedUpdateAll().whenNotMatchedInsertAll()` are idempotent by design — matching rows are updated in-place, new rows are inserted. No duplicates occur as long as natural keys are correct.

**Special case**: Two tables (`data_classification_results`, `pipeline_update_timeline`) pre-deduplicate the source with `ROW_NUMBER()` before MERGE to handle source-side duplicates.

---

## DQX Validation: Non-Blocking Quality Gates

### Design Philosophy

DQX validation is **non-blocking** — it reports quality issues and quarantines bad records but does not fail the pipeline. This ensures data always flows to the Gold layer while quality issues are visible and auditable.

### How It Works

1. **Load checks** from `bronze_dqx_checks.yaml` (declarative YAML).
2. For each table with defined checks:
   - Read the Bronze table.
   - Apply DQX `apply_checks_by_metadata_and_split()` to split valid/invalid records.
   - Write invalid records to `{table}_quarantine` with metadata columns.
3. **Summary report** printed at the end (tables validated, checks run, valid/invalid counts).

### Quarantine Tables

Invalid records are written to quarantine tables with additional metadata:

| Column | Value | Purpose |
|--------|-------|---------|
| `_quarantine_timestamp` | `current_timestamp()` | When the record was quarantined |
| `_quarantine_source` | `"dqx_bronze_validation"` | Which validation step caught it |
| All original columns | Preserved | Full record for investigation |

Quarantine tables use `mode("append")` with `mergeSchema=true`, so they accumulate over time and handle schema changes.

### SQL Fallback

If `databricks-labs-dqx` is not installed (e.g., library installation failure), the validation falls back to SQL-based NULL checks:

```python
# SQL fallback: only checks is_not_null conditions
spark.sql(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
```

This is a degraded mode — no quarantine, no detailed diagnostics — but ensures the pipeline always completes.

### YAML Check Definitions

Checks are defined in `bronze_dqx_checks.yaml` with this structure:

```yaml
- table: audit
  checks:
    - name: audit_event_id_not_null
      criticality: error
      check:
        function: is_not_null
        arguments:
          col_name: event_id
    - name: audit_event_time_not_null
      criticality: error
      check:
        function: is_not_null
        arguments:
          col_name: event_time
```

Checks cover all 7 domains (access, billing, compute, lakeflow, marketplace, mlflow, serving) with ~130 individual check definitions.

### DQX YAML Path Resolution

**Critical operational note**: The `find_yaml_path()` function uses deterministic path resolution (not filesystem walking). It tries, in order:

1. Same directory as the notebook (default for Asset Bundle deployments).
2. Databricks notebook context path (derived from `dbutils.notebook.entry_point`).
3. Well-known bundle paths based on current user.

**Never use `os.walk("/Workspace/Users")`** — this is extremely slow on shared workspaces and caused a 30+ minute hang during initial deployment.

---

## Table Optimizations

### CLUSTER BY AUTO

Automatic liquid clustering is ensured on all 24 streaming tables during the dedup step:

```sql
ALTER TABLE {table} CLUSTER BY AUTO
```

This is idempotent — no-op if already enabled. Delta automatically selects optimal clustering columns based on query patterns.

### Predictive Optimization

Enabled at the schema level during Bronze Setup:

```sql
ALTER SCHEMA {catalog}.{schema} ENABLE PREDICTIVE OPTIMIZATION
```

Databricks automatically runs OPTIMIZE, VACUUM, and ZORDER based on usage patterns.

### Governance TBLPROPERTIES

Applied to all streaming tables during dedup:

```sql
ALTER TABLE {table} SET TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'layer' = 'bronze',
    'source_system' = 'databricks_system_tables',
    'domain' = '{domain}',
    'entity_type' = '{entity_type}',
    'contains_pii' = '{contains_pii}',
    'data_classification' = 'confidential',
    'business_owner' = 'Platform Operations',
    'technical_owner' = 'Data Engineering'
)
```

---

## Checkpoint and State Management

### Checkpoint Corruption After Failed Runs

If the streaming pipeline fails mid-run (e.g., driver crash, OOM), some flow checkpoints may become corrupted.

**Symptom**: Errors like "Delta sharing table null doesn't exist. Please delete your streaming query checkpoint and restart."

**Fix**: Run a **Full Refresh** of the pipeline to clear all checkpoints and re-read from the source.

### Table Type Incompatibility

**Critical lesson from initial deployment**: The SDP `dp.create_sink` pattern creates regular Delta tables. If the workspace previously had tables of type `STREAMING_TABLE` (from the old DLT `@dlt.table` pattern), the new pipeline will fail with:

```
AnalysisException: Table ... doesn't support streaming write - StreamingTable
```

**Fix**: Drop the incompatible tables first, then let `dp.create_sink` recreate them:

```bash
# Drop all old STREAMING_TABLE type tables
databricks api post /api/2.0/sql/statements \
    --json '{"warehouse_id": "...", "statement": "DROP TABLE IF EXISTS catalog.schema.table_name"}'
```

**Prevention**: This is a one-time migration issue. Once tables are created as regular Delta tables by `dp.create_sink`, they remain compatible indefinitely.

---

## Adding a New System Table

When Databricks releases a new system table:

1. Check the [system tables documentation](https://docs.databricks.com/aws/en/admin/system-tables/) for streaming support.

2. **If streaming-capable**:
   - Add to `STREAMING_TABLES` list in `streaming_archive.py`. If the table has DeletionVectors, set `"delta_format": True`.
   - Add natural keys to `DEDUP_KEYS` registry in `dedup_streaming_tables.py`.
   - Add DQX checks to `bronze_dqx_checks.yaml`.

3. **If batch-only**:
   - Add a `CREATE TABLE` statement to `nonstreaming/setup.py`.
   - Add a `merge_{table}()` function to `nonstreaming/merge.py`.
   - Add DQX checks to `bronze_dqx_checks.yaml`.

4. Redeploy: `databricks bundle deploy`.

5. For streaming tables: Run the pipeline once to create the sink and backfill.
   For non-streaming tables: Run the Bronze Setup Job first, then Bronze Refresh.

---

## Removing / Excluding a Table

Currently, table exclusion requires editing source code (removing from `STREAMING_TABLES` or MERGE functions). A future enhancement would add an `exclude_tables` bundle variable (as in the reference architecture).

**Important**: Never `DROP` a Bronze table that feeds the Gold layer without updating Gold MERGE scripts first.

---

## Schema Evolution

| Strategy | Schema Evolution Behavior |
|----------|--------------------------|
| Streaming (SDP sinks) | New columns flow automatically (Delta schema evolution). No action needed. |
| Non-streaming MERGE | `whenMatchedUpdateAll().whenNotMatchedInsertAll()` handles new columns if the target table schema is updated. For new source columns, run `ALTER TABLE ADD COLUMN` on the target first. |
| DQX validation | New columns are ignored unless checks are added to `bronze_dqx_checks.yaml`. Quarantine tables use `mergeSchema=true` so they adapt automatically. |

---

## Cost Profile

### Typical Daily Runtime

| Task | Steady State | After Full Refresh |
|------|-------------|-------------------|
| Streaming pipeline (24 tables) | ~2–5 min | ~10–15 min |
| Dedup streaming sinks | ~3–5 min (scan-only) | ~30+ min (full rewrite) |
| DQX validation | ~3–5 min | ~5–10 min |
| Non-streaming MERGE (9 tables) | ~5–10 min | ~5–10 min |
| **Total** | **~13–25 min** | **~50–70 min** |

### Cost Optimization Features

| Feature | Impact |
|---------|--------|
| Serverless compute | No idle cluster costs; pay per query |
| Streaming (incremental) | Reads only new data since checkpoint |
| Dedup skip optimization | Scan-only on clean tables |
| CLUSTER BY AUTO | Reduces scan costs for downstream Gold queries |
| Predictive Optimization | Auto OPTIMIZE/VACUUM/ZORDER reduces storage cost |
| DQX non-blocking | No pipeline restarts from quality issues |

---

## Failure Recovery Runbook

### Scenario 1: Streaming Pipeline Fails

**Symptoms**: Task 1 (`run_streaming_pipeline`) fails. Tasks 2-4 still run (`run_if: ALL_DONE` on dedup; dependency chain for rest).

**Recovery**:
1. Check pipeline logs for the specific flow(s) that failed.
2. If checkpoint corruption: Run Full Refresh.
3. If table type incompatibility: Drop affected tables, then rerun.
4. If transient error: Rerun the Bronze Refresh Job.

### Scenario 2: Dedup Task Fails

**Symptoms**: Task 2 (`dedup_streaming_sinks`) fails. DQX and MERGE tasks still pending.

**Recovery**:
1. Check for table-level errors in the dedup output.
2. Common issue: Schema mismatch if upstream added columns. Fix: Let the streaming pipeline run again to update the sink schema.
3. Rerun the Bronze Refresh Job.

### Scenario 3: DQX Validation Fails

**Symptoms**: Task 3 (`validate_bronze_dqx`) fails.

**Recovery**:
1. Check if `databricks-labs-dqx` installed correctly (environment dependency).
2. Check `find_yaml_path()` — ensure `bronze_dqx_checks.yaml` is deployed alongside the notebook.
3. Common issue: YAML file not found. Fix: Redeploy the bundle (`databricks bundle deploy`).

### Scenario 4: Non-Streaming MERGE Fails

**Symptoms**: Task 4 (`merge_nonstreaming_tables`) fails. Some tables may have succeeded.

**Recovery**:
1. Check the error log for which specific table(s) failed.
2. Common issue: Target table doesn't exist. Fix: Run Bronze Setup Job first.
3. Common issue: Schema mismatch. Fix: `ALTER TABLE ADD COLUMN` on the target.
4. Rerun the Bronze Refresh Job (MERGE is idempotent).

### Scenario 5: Authentication Expired

**Symptoms**: All Databricks CLI/API calls fail with 403 or "Invalid access token".

**Recovery**:
```bash
databricks auth login --host <workspace-url> --profile health_monitor
databricks bundle deploy -t dev
databricks bundle run -t dev bronze_refresh_job
```

---

## Monitoring Checklist

| Check | Frequency | Method |
|-------|-----------|--------|
| Bronze Refresh Job success | Daily | Workflow notifications (email on failure) |
| Dedup summary (dupes removed) | Daily | Check notebook output / exit value |
| DQX validation summary | Daily | Check notebook output / quarantine table row counts |
| Table row counts | Weekly | Query `information_schema.tables` for `last_altered` and row counts |
| Quarantine table growth | Weekly | `SELECT COUNT(*) FROM {table}_quarantine` |
| Checkpoint staleness | Weekly | Check if streaming pipeline last ran within 7 days |
| Storage cost | Monthly | `system.billing.usage` filtered by job ID |

---

## Lessons Learned (Feb 2026 Refactoring)

| # | Issue | Root Cause | Fix | Prevention |
|---|-------|-----------|-----|------------|
| 1 | `STREAMING_TABLE` type incompatible with `dp.create_sink` | Old DLT pipeline created tables as `STREAMING_TABLE` type; new SDP pattern requires regular Delta tables | Dropped all 24 old tables, let `dp.create_sink` recreate them | One-time migration; document for future reference |
| 2 | DQX validation hung for 30+ minutes | `find_yaml_path()` used `os.walk("/Workspace/Users")`, traversing entire workspace filesystem | Replaced with deterministic path resolution using notebook context | Never use `os.walk` on workspace paths; always use deterministic paths |
| 3 | Authentication token expired during deployment | Default Databricks tokens expire; IP ACL blocks can also occur | Re-authenticate with `databricks auth login --profile health_monitor` | Use named profiles; re-authenticate before deployments |
| 4 | Bash table-drop script failed | `for tbl in $TABLES` expanded incorrectly — passed all names as single string | Rewrote as individual function calls per table | Test bash scripts with `echo` before executing destructive operations |
