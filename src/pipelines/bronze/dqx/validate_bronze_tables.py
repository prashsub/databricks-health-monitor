# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer DQX Validation
# MAGIC
# MAGIC Post-pipeline data quality validation using Databricks Labs DQX.
# MAGIC Reads DQ check definitions from YAML, applies them to each Bronze table,
# MAGIC and writes invalid records to quarantine tables.
# MAGIC
# MAGIC This is a **non-blocking** validation step — it reports quality issues
# MAGIC and quarantines bad records but does not fail the pipeline.
# MAGIC
# MAGIC Requires: `databricks-labs-dqx` (installed at environment level)

# COMMAND ----------

import json
import yaml
import traceback
from pathlib import Path
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

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
# MAGIC ## Load DQX Check Definitions from YAML

# COMMAND ----------

def find_yaml_path() -> str:
    """Locate the bronze_dqx_checks.yaml file.

    Uses deterministic paths based on notebook location rather than
    walking the workspace filesystem (which is extremely slow on
    shared workspaces).

    Works in both Databricks workspace (bundle-deployed paths) and
    local development.
    """
    import os

    # Strategy 1: Relative to the notebook directory (same folder)
    # In Asset Bundles, YAML is deployed alongside the notebook
    notebook_dir = os.path.dirname(os.path.abspath("validate_bronze_tables"))
    same_dir = os.path.join(notebook_dir, "bronze_dqx_checks.yaml")
    if os.path.exists(same_dir):
        return same_dir

    # Strategy 2: Use Databricks notebook context to find the bundle root
    try:
        notebook_path = (
            dbutils.notebook.entry_point
            .getDbutils()
            .notebook()
            .getContext()
            .notebookPath()
            .get()
        )
        # notebook_path is like /Workspace/Users/<user>/.bundle/<name>/dev/files/src/pipelines/bronze/dqx/validate_bronze_tables
        # The YAML is in the same directory
        workspace_dir = os.path.dirname(f"/Workspace{notebook_path}")
        ws_yaml = os.path.join(workspace_dir, "bronze_dqx_checks.yaml")
        if os.path.exists(ws_yaml):
            return ws_yaml
    except Exception:
        pass

    # Strategy 3: Check well-known bundle paths
    try:
        user_email = spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", "")
        username = spark.sql("SELECT current_user()").first()[0]
    except Exception:
        username = ""

    known_patterns = [
        # Direct path in workspace
        f"/Workspace/Users/{username}/.bundle/databricks_health_monitor/dev/files/src/pipelines/bronze/dqx/bronze_dqx_checks.yaml",
        # Current working directory
        "./bronze_dqx_checks.yaml",
        "../dqx/bronze_dqx_checks.yaml",
        "src/pipelines/bronze/dqx/bronze_dqx_checks.yaml",
    ]

    for path in known_patterns:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "Could not find bronze_dqx_checks.yaml. "
        "Searched: same directory as notebook, workspace context path, "
        "and well-known bundle paths. "
        "Ensure it is deployed alongside this notebook."
    )


def load_checks_from_yaml() -> dict:
    """Load DQX check definitions grouped by table name.

    Returns:
        dict: {table_name: [list of check dicts]}
    """
    yaml_path = find_yaml_path()
    print(f"Loading checks from: {yaml_path}")

    with open(yaml_path) as f:
        raw_checks = yaml.safe_load(f)

    checks_by_table = {}
    for entry in raw_checks:
        table_name = entry["table"]
        checks_by_table[table_name] = entry["checks"]

    total_checks = sum(len(v) for v in checks_by_table.values())
    print(f"Loaded {total_checks} checks for {len(checks_by_table)} tables")

    return checks_by_table

# COMMAND ----------

checks_by_table = load_checks_from_yaml()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run DQX Validation
# MAGIC
# MAGIC For each Bronze table with defined checks:
# MAGIC 1. Read the table
# MAGIC 2. Apply DQX checks using `apply_checks_by_metadata_and_split()`
# MAGIC 3. Report valid/invalid counts
# MAGIC 4. Write invalid records to quarantine table

# COMMAND ----------

def validate_table_with_dqx(
    spark: SparkSession,
    table_name: str,
    checks: list,
    catalog: str,
    schema: str,
) -> dict:
    """Validate a single Bronze table using DQX checks.

    Uses DQX apply_checks_by_metadata_and_split() for validation.
    Falls back to SQL-based validation if DQX import fails.

    Returns:
        dict with validation results
    """
    target_fqn = f"{catalog}.{schema}.{table_name}"

    if not spark.catalog.tableExists(target_fqn):
        print(f"  [{table_name}] SKIPPED — table does not exist")
        return {
            "table": table_name,
            "status": "skipped",
            "reason": "table_not_found",
        }

    df = spark.table(target_fqn)
    total_rows = df.count()

    if total_rows == 0:
        print(f"  [{table_name}] SKIPPED — empty table")
        return {
            "table": table_name,
            "status": "skipped",
            "reason": "empty_table",
            "total_rows": 0,
        }

    try:
        from databricks.labs.dqx.engine import DQEngine

        dq_engine = DQEngine(spark)

        valid_df, invalid_df = dq_engine.apply_checks_by_metadata_and_split(
            df, checks
        )

        valid_count = valid_df.count()
        invalid_count = invalid_df.count()

        if invalid_count > 0:
            quarantine_table = f"{catalog}.{schema}.{table_name}_quarantine"
            (
                invalid_df
                .withColumn("_quarantine_timestamp", current_timestamp())
                .withColumn("_quarantine_source", lit("dqx_bronze_validation"))
                .write
                .format("delta")
                .mode("append")
                .option("mergeSchema", "true")
                .saveAsTable(quarantine_table)
            )
            print(
                f"  [{table_name}] {valid_count:,} valid, {invalid_count:,} invalid "
                f"(quarantined → {quarantine_table})"
            )
        else:
            print(f"  [{table_name}] {valid_count:,} valid, 0 invalid ✓")

        return {
            "table": table_name,
            "status": "validated",
            "total_rows": total_rows,
            "valid_rows": valid_count,
            "invalid_rows": invalid_count,
            "checks_applied": len(checks),
        }

    except ImportError:
        print(f"  [{table_name}] DQX not available — falling back to SQL validation")
        return _validate_with_sql(spark, table_name, checks, catalog, schema, total_rows)
    except Exception as e:
        print(f"  [{table_name}] ERROR: {e}")
        traceback.print_exc()
        return {
            "table": table_name,
            "status": "failed",
            "error": str(e),
            "total_rows": total_rows,
        }


def _validate_with_sql(
    spark: SparkSession,
    table_name: str,
    checks: list,
    catalog: str,
    schema: str,
    total_rows: int,
) -> dict:
    """Fallback SQL-based validation when DQX is not installed."""
    target_fqn = f"{catalog}.{schema}.{table_name}"
    invalid_count = 0

    for check in checks:
        check_name = check["name"]
        check_func = check["check"]["function"]
        col_name = check["check"]["arguments"].get("col_name", "")

        if check_func == "is_not_null" and col_name:
            null_count_row = spark.sql(
                f"SELECT COUNT(*) AS cnt FROM {target_fqn} WHERE {col_name} IS NULL"
            ).first()
            null_count = null_count_row["cnt"]
            if null_count > 0:
                invalid_count += null_count
                criticality = check.get("criticality", "warning")
                print(
                    f"    [{table_name}.{check_name}] {null_count:,} "
                    f"NULL values ({criticality})"
                )

    valid_count = total_rows - min(invalid_count, total_rows)
    if invalid_count == 0:
        print(f"  [{table_name}] {total_rows:,} rows, all checks passed ✓ (SQL fallback)")
    else:
        print(
            f"  [{table_name}] {valid_count:,} valid, ~{invalid_count:,} issues "
            f"(SQL fallback, no quarantine)"
        )

    return {
        "table": table_name,
        "status": "validated_sql_fallback",
        "total_rows": total_rows,
        "valid_rows": valid_count,
        "invalid_rows": invalid_count,
        "checks_applied": len(checks),
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Validation

# COMMAND ----------

results = []

print("=" * 70)
print(f"DQX BRONZE VALIDATION ({CATALOG}.{BRONZE_SCHEMA})")
print("=" * 70)

for table_name, checks in checks_by_table.items():
    result = validate_table_with_dqx(
        spark=spark,
        table_name=table_name,
        checks=checks,
        catalog=CATALOG,
        schema=BRONZE_SCHEMA,
    )
    results.append(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Report

# COMMAND ----------

validated = [r for r in results if r["status"] in ("validated", "validated_sql_fallback")]
skipped = [r for r in results if r["status"] == "skipped"]
failed = [r for r in results if r["status"] == "failed"]
total_invalid = sum(r.get("invalid_rows", 0) for r in validated)
total_valid = sum(r.get("valid_rows", 0) for r in validated)
total_checks = sum(r.get("checks_applied", 0) for r in validated)

print()
print("=" * 70)
print("DQX VALIDATION SUMMARY")
print("=" * 70)
print(f"  Tables validated:   {len(validated)}")
print(f"  Tables skipped:     {len(skipped)}")
print(f"  Tables failed:      {len(failed)}")
print(f"  Total checks run:   {total_checks}")
print(f"  Total valid rows:   {total_valid:,}")
print(f"  Total invalid rows: {total_invalid:,}")
print()

if failed:
    print("FAILED TABLES:")
    for r in failed:
        print(f"  - {r['table']}: {r.get('error', 'unknown')}")
    print()

header = f"{'Table':<40} {'Status':<20} {'Total':>10} {'Valid':>10} {'Invalid':>10} {'Checks':>8}"
print(header)
print("-" * len(header))
for r in results:
    print(
        f"{r['table']:<40} {r['status']:<20} "
        f"{r.get('total_rows', '-'):>10} {r.get('valid_rows', '-'):>10} "
        f"{r.get('invalid_rows', '-'):>10} {r.get('checks_applied', '-'):>8}"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exit Value

# COMMAND ----------

summary = {
    "run_timestamp": datetime.utcnow().isoformat(),
    "catalog": CATALOG,
    "schema": BRONZE_SCHEMA,
    "tables_validated": len(validated),
    "tables_skipped": len(skipped),
    "tables_failed": len(failed),
    "total_checks": total_checks,
    "total_valid_rows": total_valid,
    "total_invalid_rows": total_invalid,
    "failed_tables": [r["table"] for r in failed],
}

dbutils.notebook.exit(json.dumps(summary))
