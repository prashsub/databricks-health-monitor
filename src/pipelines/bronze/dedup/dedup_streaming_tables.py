# Databricks notebook source
# MAGIC %md
# MAGIC # Deduplicate Bronze Streaming Sink Tables
# MAGIC
# MAGIC After a **Full Refresh** of the streaming pipeline, Delta sinks accumulate
# MAGIC duplicate rows (the pipeline re-reads the full source and appends again).
# MAGIC
# MAGIC This notebook:
# MAGIC 1. Removes duplicates from all streaming sink tables using `INSERT OVERWRITE`
# MAGIC 2. Enforces `CLUSTER BY AUTO` on every sink table
# MAGIC 3. Applies required `TBLPROPERTIES` (CDF, auto-optimize, governance tags)
# MAGIC
# MAGIC **Safety**: Each table is overwritten atomically. If the notebook fails
# MAGIC mid-way, already-processed tables are clean and unprocessed tables still
# MAGIC have their (duplicated) data intact.

# COMMAND ----------

import json
import time
import traceback
from datetime import datetime

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Catalog")
dbutils.widgets.text("system_bronze_schema", "", "Bronze Schema")

# COMMAND ----------

CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("system_bronze_schema")

print(f"Catalog: {CATALOG}")
print(f"Schema:  {BRONZE_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Natural Key Registry
# MAGIC
# MAGIC Each entry defines:
# MAGIC - `keys`: Natural key columns (dedup PARTITION BY)
# MAGIC - `tiebreaker`: Ordering column to keep the latest row
# MAGIC - `domain`: System table domain for governance tagging
# MAGIC - `entity_type`: dimension or fact
# MAGIC - `contains_pii`: Whether the table contains PII data

# COMMAND ----------

DEDUP_KEYS = {
    # ── access domain ──────────────────────────────────────────────────────
    "audit": {
        "keys": ["event_id"],
        "tiebreaker": "event_time",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "true",
    },
    "clean_room_events": {
        "keys": ["event_id"],
        "tiebreaker": "event_time",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "column_lineage": {
        "keys": ["record_id"],
        "tiebreaker": "event_time",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "inbound_network": {
        "keys": ["event_id"],
        "tiebreaker": "event_time",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "outbound_network": {
        "keys": ["event_id"],
        "tiebreaker": "event_time",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "table_lineage": {
        "keys": ["record_id"],
        "tiebreaker": "event_time",
        "domain": "access",
        "entity_type": "fact",
        "contains_pii": "false",
    },

    # ── billing domain ─────────────────────────────────────────────────────
    "usage": {
        "keys": ["record_id"],
        "tiebreaker": "usage_date",
        "domain": "billing",
        "entity_type": "fact",
        "contains_pii": "false",
    },

    # ── compute domain ─────────────────────────────────────────────────────
    "clusters": {
        "keys": ["workspace_id", "cluster_id", "change_time"],
        "tiebreaker": "change_time",
        "domain": "compute",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "node_timeline": {
        "keys": ["cluster_id", "instance_id", "start_time"],
        "tiebreaker": "start_time",
        "domain": "compute",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "warehouse_events": {
        "keys": ["workspace_id", "warehouse_id", "event_type", "event_time"],
        "tiebreaker": "event_time",
        "domain": "compute",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "warehouses": {
        "keys": ["workspace_id", "warehouse_id", "change_time"],
        "tiebreaker": "change_time",
        "domain": "compute",
        "entity_type": "dimension",
        "contains_pii": "false",
    },

    # ── lakeflow domain ────────────────────────────────────────────────────
    "job_run_timeline": {
        "keys": ["workspace_id", "run_id", "period_start_time"],
        "tiebreaker": "period_start_time",
        "domain": "lakeflow",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "job_task_run_timeline": {
        "keys": ["workspace_id", "run_id", "period_start_time"],
        "tiebreaker": "period_start_time",
        "domain": "lakeflow",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "job_tasks": {
        "keys": ["workspace_id", "job_id", "task_key", "change_time"],
        "tiebreaker": "change_time",
        "domain": "lakeflow",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "jobs": {
        "keys": ["workspace_id", "job_id", "change_time"],
        "tiebreaker": "change_time",
        "domain": "lakeflow",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "pipelines": {
        "keys": ["workspace_id", "pipeline_id", "change_time"],
        "tiebreaker": "change_time",
        "domain": "lakeflow",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "pipeline_update_timeline": {
        "keys": ["workspace_id", "update_id", "period_start_time"],
        "tiebreaker": "period_start_time",
        "domain": "lakeflow",
        "entity_type": "fact",
        "contains_pii": "false",
    },

    # ── marketplace domain ─────────────────────────────────────────────────
    "listing_funnel_events": {
        "keys": ["listing_id", "event_type", "event_time", "consumer_cloud", "consumer_region"],
        "tiebreaker": "event_time",
        "domain": "marketplace",
        "entity_type": "fact",
        "contains_pii": "false",
    },
    "listing_access_events": {
        "keys": ["listing_id", "event_type", "event_time", "consumer_email"],
        "tiebreaker": "event_time",
        "domain": "marketplace",
        "entity_type": "fact",
        "contains_pii": "true",
    },

    # ── mlflow domain ──────────────────────────────────────────────────────
    "experiments_latest": {
        "keys": ["workspace_id", "experiment_id"],
        "tiebreaker": "update_time",
        "domain": "mlflow",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "runs_latest": {
        "keys": ["workspace_id", "run_id"],
        "tiebreaker": "update_time",
        "domain": "mlflow",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "run_metrics_history": {
        "keys": ["record_id"],
        "tiebreaker": "insert_time",
        "domain": "mlflow",
        "entity_type": "fact",
        "contains_pii": "false",
    },

    # ── serving domain ─────────────────────────────────────────────────────
    "served_entities": {
        "keys": ["served_entity_id", "change_time"],
        "tiebreaker": "change_time",
        "domain": "serving",
        "entity_type": "dimension",
        "contains_pii": "false",
    },
    "endpoint_usage": {
        "keys": ["databricks_request_id"],
        "tiebreaker": "request_time",
        "domain": "serving",
        "entity_type": "fact",
        "contains_pii": "false",
    },
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dedup Logic

# COMMAND ----------

def dedup_table(table_name: str, natural_keys: list, tiebreaker: str) -> dict:
    """Remove duplicates from a single sink table using ROW_NUMBER window function.

    Optimization: checks for duplicate key groups first. If none exist, skips the
    expensive INSERT OVERWRITE entirely.
    """
    target_fqn = f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}"
    start_ts = time.time()

    if not spark.catalog.tableExists(target_fqn):
        elapsed = time.time() - start_ts
        print(f"  [{table_name}] SKIPPED — table does not exist")
        return {
            "table": table_name,
            "status": "skipped",
            "reason": "table_not_found",
            "elapsed_s": round(elapsed, 1),
        }

    partition_cols = ", ".join(natural_keys)
    dup_check_sql = f"""
    SELECT COUNT(*) AS dup_groups FROM (
        SELECT {partition_cols}
        FROM {target_fqn}
        GROUP BY {partition_cols}
        HAVING COUNT(*) > 1
        LIMIT 1
    )
    """
    dup_groups = spark.sql(dup_check_sql).first()["dup_groups"]

    if dup_groups == 0:
        elapsed = time.time() - start_ts
        print(f"  [{table_name}] CLEAN — no duplicates ({elapsed:.1f}s)")
        return {
            "table": table_name,
            "status": "clean",
            "duplicates_removed": 0,
            "elapsed_s": round(elapsed, 1),
        }

    count_before = spark.table(target_fqn).count()

    dedup_sql = f"""
    INSERT OVERWRITE {target_fqn}
    SELECT * EXCEPT (_row_num)
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY {partition_cols}
                ORDER BY {tiebreaker} DESC
            ) AS _row_num
        FROM {target_fqn}
    )
    WHERE _row_num = 1
    """
    spark.sql(dedup_sql)

    count_after = spark.table(target_fqn).count()
    duplicates_removed = count_before - count_after
    elapsed = time.time() - start_ts

    print(f"  [{table_name}] removed {duplicates_removed:,} duplicates "
          f"({count_before:,} → {count_after:,}) ({elapsed:.1f}s)")

    return {
        "table": table_name,
        "status": "deduped",
        "count_before": count_before,
        "count_after": count_after,
        "duplicates_removed": duplicates_removed,
        "elapsed_s": round(elapsed, 1),
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Dedup

# COMMAND ----------

results = []

print("=" * 70)
print(f"DEDUP STREAMING SINK TABLES ({CATALOG}.{BRONZE_SCHEMA})")
print("=" * 70)

for table_name, key_config in DEDUP_KEYS.items():
    try:
        result = dedup_table(
            table_name=table_name,
            natural_keys=key_config["keys"],
            tiebreaker=key_config["tiebreaker"],
        )
        results.append(result)
    except Exception as e:
        print(f"  [ERROR] {table_name}: {e}")
        traceback.print_exc()
        results.append({
            "table": table_name,
            "status": "failed",
            "error": str(e),
        })

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ensure Table Optimizations
# MAGIC
# MAGIC Apply `CLUSTER BY AUTO` and governance TBLPROPERTIES to all sink tables.
# MAGIC These are idempotent — safe to run on every refresh.

# COMMAND ----------

print()
print("=" * 70)
print("ENSURE CLUSTER BY AUTO + TBLPROPERTIES")
print("=" * 70)

for table_name, key_config in DEDUP_KEYS.items():
    target_fqn = f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}"
    if not spark.catalog.tableExists(target_fqn):
        continue

    domain = key_config["domain"]
    entity_type = key_config["entity_type"]
    contains_pii = key_config["contains_pii"]

    try:
        spark.sql(f"ALTER TABLE {target_fqn} CLUSTER BY AUTO")

        spark.sql(f"""
            ALTER TABLE {target_fqn} SET TBLPROPERTIES (
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
        """)

        print(f"  [{table_name}] CLUSTER BY AUTO + TBLPROPERTIES ✓")
    except Exception as e:
        print(f"  [{table_name}] optimization failed: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Report

# COMMAND ----------

deduped = [r for r in results if r["status"] == "deduped"]
clean = [r for r in results if r["status"] == "clean"]
skipped = [r for r in results if r["status"] == "skipped"]
failed = [r for r in results if r["status"] == "failed"]
total_dupes = sum(r.get("duplicates_removed", 0) for r in deduped)
total_elapsed = sum(r.get("elapsed_s", 0) for r in results)

print()
print("=" * 70)
print("DEDUP SUMMARY")
print("=" * 70)
print(f"  Tables deduped:     {len(deduped)}")
print(f"  Tables clean:       {len(clean)}")
print(f"  Tables skipped:     {len(skipped)}")
print(f"  Tables failed:      {len(failed)}")
print(f"  Total dupes removed:{total_dupes:>10,}")
print(f"  Total elapsed:      {total_elapsed:.1f}s")
print()

if failed:
    print("FAILED TABLES:")
    for r in failed:
        print(f"  - {r['table']}: {r.get('error', 'unknown')}")
    print()

header = f"{'Table':<40} {'Status':<10} {'Before':>12} {'After':>12} {'Removed':>10} {'Time':>8}"
print(header)
print("-" * len(header))
for r in results:
    print(
        f"{r['table']:<40} {r['status']:<10} "
        f"{r.get('count_before', '-'):>12} {r.get('count_after', '-'):>12} "
        f"{r.get('duplicates_removed', '-'):>10} {r.get('elapsed_s', '-'):>7}s"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exit Value

# COMMAND ----------

summary = {
    "run_timestamp": datetime.utcnow().isoformat(),
    "catalog": CATALOG,
    "schema": BRONZE_SCHEMA,
    "total_tables": len(results),
    "deduped": len(deduped),
    "clean": len(clean),
    "skipped": len(skipped),
    "failed": len(failed),
    "total_duplicates_removed": total_dupes,
    "total_elapsed_s": round(total_elapsed, 1),
    "failed_tables": [r["table"] for r in failed],
}

dbutils.notebook.exit(json.dumps(summary))
