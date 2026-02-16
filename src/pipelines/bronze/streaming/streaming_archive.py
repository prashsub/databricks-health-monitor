"""
System Tables Streaming Archive — SDP Pipeline Transformations

Incrementally copies all streaming-capable system tables into persistent
Delta sink tables using append_flow + Delta sinks.

Key properties:
- Full refresh is safe: re-appends to sinks, never deletes historical data.
- skipChangeCommits = true: handles upstream rolling deletes from Delta Sharing.
- Triggered mode: scheduled daily via Databricks Workflow.
- bronze_ingestion_timestamp added to every row for downstream Gold dedup.

Pipeline configuration parameters (set in pipeline YAML):
- catalog: Unity Catalog catalog for archived tables
- bronze_schema: Schema within the catalog for Bronze tables

Reference: https://github.com/prashsub/databricks-system-tables-archival
"""

from pyspark.sql.functions import current_timestamp
from pyspark import pipelines as dp

TARGET_CATALOG = spark.conf.get("catalog")
BRONZE_SCHEMA = spark.conf.get("bronze_schema")

# ---------------------------------------------------------------------------
# Streaming Table Registry
#
# All streaming-capable Databricks system tables.
# Each entry maps a source system table to a Bronze sink table.
#
# Fields:
#   source       - Fully qualified system table name
#   table        - Target table name in Bronze schema (preserves existing names)
#   delta_format - Set True for tables with Deletion Vectors (requires
#                  responseFormat=delta to read via Delta Sharing streaming)
# ---------------------------------------------------------------------------

STREAMING_TABLES = [
    # ── access domain ──────────────────────────────────────────────────────
    {"source": "system.access.audit", "table": "audit"},
    {"source": "system.access.clean_room_events", "table": "clean_room_events"},
    {"source": "system.access.column_lineage", "table": "column_lineage"},
    {"source": "system.access.inbound_network", "table": "inbound_network", "delta_format": True},
    {"source": "system.access.outbound_network", "table": "outbound_network"},
    {"source": "system.access.table_lineage", "table": "table_lineage"},

    # ── billing domain ─────────────────────────────────────────────────────
    {"source": "system.billing.usage", "table": "usage"},

    # ── compute domain ─────────────────────────────────────────────────────
    {"source": "system.compute.clusters", "table": "clusters"},
    {"source": "system.compute.node_timeline", "table": "node_timeline"},
    {"source": "system.compute.warehouse_events", "table": "warehouse_events"},
    {"source": "system.compute.warehouses", "table": "warehouses"},

    # ── lakeflow domain ────────────────────────────────────────────────────
    {"source": "system.lakeflow.job_run_timeline", "table": "job_run_timeline"},
    {"source": "system.lakeflow.job_task_run_timeline", "table": "job_task_run_timeline"},
    {"source": "system.lakeflow.job_tasks", "table": "job_tasks"},
    {"source": "system.lakeflow.jobs", "table": "jobs"},
    {"source": "system.lakeflow.pipelines", "table": "pipelines"},
    {"source": "system.lakeflow.pipeline_update_timeline", "table": "pipeline_update_timeline", "delta_format": True},

    # ── marketplace domain ─────────────────────────────────────────────────
    {"source": "system.marketplace.listing_funnel_events", "table": "listing_funnel_events"},
    {"source": "system.marketplace.listing_access_events", "table": "listing_access_events"},

    # ── mlflow domain ──────────────────────────────────────────────────────
    {"source": "system.mlflow.experiments_latest", "table": "experiments_latest"},
    {"source": "system.mlflow.runs_latest", "table": "runs_latest"},
    {"source": "system.mlflow.run_metrics_history", "table": "run_metrics_history"},

    # ── serving domain ─────────────────────────────────────────────────────
    {"source": "system.serving.served_entities", "table": "served_entities"},
    {"source": "system.serving.endpoint_usage", "table": "endpoint_usage"},
]


# ---------------------------------------------------------------------------
# Register Sinks & Flows
#
# Each streaming table gets:
# 1. A Delta sink (persistent table outside pipeline lifecycle — survives
#    full refresh without data loss)
# 2. An append_flow that reads incrementally with skipChangeCommits = true
#    and adds bronze_ingestion_timestamp for downstream dedup
# ---------------------------------------------------------------------------


def register_sink_and_flow(config: dict) -> None:
    """Register a Delta sink and append_flow for a single system table."""
    table_name = config["table"]
    sink_name = f"{table_name}_sink"
    flow_name = f"{table_name}_flow"
    target_table = f"{TARGET_CATALOG}.{BRONZE_SCHEMA}.{table_name}"
    source_table = config["source"]
    needs_delta_format = config.get("delta_format", False)

    dp.create_sink(
        name=sink_name,
        format="delta",
        options={"tableName": target_table},
    )

    @dp.append_flow(name=flow_name, target=sink_name)
    def _flow(src=source_table, delta_fmt=needs_delta_format):
        reader = spark.readStream.option("skipChangeCommits", "true")
        if delta_fmt:
            reader = reader.option("responseFormat", "delta")
        return reader.table(src).withColumn(
            "bronze_ingestion_timestamp", current_timestamp()
        )


for _cfg in STREAMING_TABLES:
    register_sink_and_flow(_cfg)

print(f"Registered {len(STREAMING_TABLES)} streaming sinks → {TARGET_CATALOG}.{BRONZE_SCHEMA}")
