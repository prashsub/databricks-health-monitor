# Databricks notebook source
"""
Alerting Tables Setup (Gold)
===========================

Creates the Gold-layer tables used by the SQL Alerting Framework:
- {catalog}.{gold_schema}.alert_configurations
- {catalog}.{gold_schema}.notification_destinations
- {catalog}.{gold_schema}.alert_history

This job is intentionally idempotent.
"""

from pyspark.sql import SparkSession


def get_parameters() -> tuple[str, str]:
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    return catalog, gold_schema


def create_tables(spark: SparkSession, catalog: str, gold_schema: str) -> None:
    """Create alerting tables (idempotent)."""
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{gold_schema}")

    # ------------------------------------------------------------------
    # notification_destinations (references workspace notification destinations)
    # ------------------------------------------------------------------
    spark.sql(
        f"""
CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.notification_destinations (
  destination_id STRING NOT NULL
    COMMENT 'Internal destination identifier referenced by alert_configurations.notification_channels.',
  destination_name STRING NOT NULL
    COMMENT 'Human-readable destination name. Business: shown in UI. Technical: not required to be unique.',
  destination_type STRING NOT NULL
    COMMENT 'Destination type: EMAIL, SLACK, WEBHOOK, TEAMS, PAGERDUTY. Business: channel category. Technical: must align with workspace destination type.',
  databricks_destination_id STRING
    COMMENT 'Workspace notification destination UUID. Technical: used for SQL Alert v2 subscriptions.destination_id.',
  config_json STRING
    COMMENT 'Type-specific configuration as JSON (optional). Business: UI-managed settings. Technical: may store webhook URL references (prefer secrets).',
  owner STRING NOT NULL
    COMMENT 'Owner (user or group) responsible for this destination.',
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE
    COMMENT 'Whether this destination is active for subscriptions.',
  created_by STRING NOT NULL
    COMMENT 'Who created this destination row.',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
    COMMENT 'Creation timestamp.',
  updated_by STRING
    COMMENT 'Who last updated this destination row.',
  updated_at TIMESTAMP
    COMMENT 'Last update timestamp.',
  tags MAP<STRING, STRING>
    COMMENT 'Free-form tags for filtering and governance.',

  CONSTRAINT pk_notification_destinations PRIMARY KEY (destination_id) NOT ENFORCED,
  CONSTRAINT chk_destination_type CHECK (destination_type IN ('EMAIL', 'SLACK', 'WEBHOOK', 'TEAMS', 'PAGERDUTY'))
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'Alert notification destinations. Maps internal channel IDs to workspace notification destination UUIDs for Databricks SQL Alerts.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'layer' = 'gold',
  'domain' = 'alerting',
  'entity_type' = 'configuration'
)
"""
    )

    # ------------------------------------------------------------------
    # alert_configurations (central config table)
    # ------------------------------------------------------------------
    spark.sql(
        f"""
CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.alert_configurations (
  alert_id STRING NOT NULL
    COMMENT 'Unique alert identifier. Business: stable id for UI and audit. Technical: PK, recommended format COST-001, PERF-009, etc.',

  alert_name STRING NOT NULL
    COMMENT 'Human-readable alert name. Business: shown in UI and notifications. Technical: used to build Databricks display_name with severity prefix.',
  alert_description STRING
    COMMENT 'Detailed description of what this alert monitors.',

  agent_domain STRING NOT NULL
    COMMENT 'Agent domain: COST, SECURITY, PERFORMANCE, RELIABILITY, QUALITY. Business: routes alert ownership. Technical: used for filtering.',
  severity STRING NOT NULL DEFAULT 'WARNING'
    COMMENT 'Alert severity: CRITICAL, WARNING, INFO. Business: urgency. Technical: used in display_name prefix.',

  alert_query_template STRING NOT NULL
    COMMENT 'SQL query template for the alert. Technical: must be rendered to fully-qualified names (SQL alerts do not support query parameters). Supports ${catalog} and ${gold_schema}.',
  query_source STRING DEFAULT 'CUSTOM'
    COMMENT 'Query source: CUSTOM, TVF, METRIC_VIEW, MONITORING. Technical: lineage metadata only.',
  source_artifact_name STRING
    COMMENT 'Name of TVF/Metric View/Monitor backing this alert (optional).',

  threshold_column STRING NOT NULL
    COMMENT 'Column name in query results used for evaluation.',
  threshold_operator STRING NOT NULL
    COMMENT 'Comparison operator: >, <, >=, <=, =, ==, !=, <>.',
  threshold_value_type STRING NOT NULL
    COMMENT 'Threshold value type: DOUBLE, STRING, BOOLEAN. Technical: controls evaluation.threshold.value payload.',
  threshold_value_double DOUBLE
    COMMENT 'Numeric threshold value (required when threshold_value_type=DOUBLE).',
  threshold_value_string STRING
    COMMENT 'String threshold value (required when threshold_value_type=STRING).',
  threshold_value_bool BOOLEAN
    COMMENT 'Boolean threshold value (required when threshold_value_type=BOOLEAN).',

  empty_result_state STRING NOT NULL DEFAULT 'OK'
    COMMENT 'State when query returns empty: OK, TRIGGERED, ERROR. Technical: maps to alerts v2 empty_result_state.',
  aggregation_type STRING DEFAULT 'NONE'
    COMMENT 'Aggregation for evaluation source: NONE, SUM, COUNT, COUNT_DISTINCT, AVG, MEDIAN, MIN, MAX, STDDEV.',

  schedule_cron STRING NOT NULL DEFAULT '0 */5 * * * ?'
    COMMENT 'Quartz cron expression for schedule.',
  schedule_timezone STRING NOT NULL DEFAULT 'America/Los_Angeles'
    COMMENT 'Timezone for schedule (Java timezone id).',
  pause_status STRING NOT NULL DEFAULT 'UNPAUSED'
    COMMENT 'Schedule pause status: UNPAUSED or PAUSED.',
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE
    COMMENT 'Whether this configuration should be deployed as an alert.',

  notification_channels ARRAY<STRING> NOT NULL
    COMMENT 'List of notification channel IDs. Each element can be either: (a) notification_destinations.destination_id or (b) a user email address.',
  notify_on_ok BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT 'Whether to notify when the alert returns to OK.',
  retrigger_seconds INT
    COMMENT 'Cooldown before re-notifying after triggered. If 0/NULL, no further notifications after first trigger.',

  use_custom_template BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT 'Whether to use custom templates. Technical: mapped to custom_summary/custom_description in alerts v2.',
  custom_subject_template STRING
    COMMENT 'Custom subject template (mustache variables allowed in SQL alerts).',
  custom_body_template STRING
    COMMENT 'Custom body template (HTML allowed for email destinations only).',

  owner STRING NOT NULL
    COMMENT 'Alert owner (user or group).',
  created_by STRING NOT NULL
    COMMENT 'User who created the configuration.',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
    COMMENT 'Creation timestamp.',
  updated_by STRING
    COMMENT 'User who last updated the configuration.',
  updated_at TIMESTAMP
    COMMENT 'Update timestamp.',
  tags MAP<STRING, STRING>
    COMMENT 'Free-form tags for organization (queryable).',

  -- Sync metadata (Databricks SQL Alerts v2)
  databricks_alert_id STRING
    COMMENT 'Databricks SQL Alert (v2) id for the deployed alert.',
  databricks_display_name STRING
    COMMENT 'Deployed Databricks alert display name.',
  last_synced_at TIMESTAMP
    COMMENT 'When this configuration was last synced to Databricks SQL Alerts.',
  last_sync_status STRING
    COMMENT 'Last sync status: CREATED, UPDATED, UNCHANGED, SKIPPED, ERROR.',
  last_sync_error STRING
    COMMENT 'Last sync error message (if any).',

  CONSTRAINT pk_alert_configurations PRIMARY KEY (alert_id) NOT ENFORCED,
  CONSTRAINT chk_agent_domain CHECK (agent_domain IN ('COST','SECURITY','PERFORMANCE','RELIABILITY','QUALITY')),
  CONSTRAINT chk_severity CHECK (severity IN ('CRITICAL','WARNING','INFO')),
  CONSTRAINT chk_operator CHECK (threshold_operator IN ('>','<','>=','<=','=','==','!=','<>')),
  CONSTRAINT chk_threshold_type CHECK (threshold_value_type IN ('DOUBLE','STRING','BOOLEAN')),
  CONSTRAINT chk_empty_result CHECK (empty_result_state IN ('OK','TRIGGERED','ERROR')),
  CONSTRAINT chk_pause_status CHECK (pause_status IN ('UNPAUSED','PAUSED'))
)
USING DELTA
CLUSTER BY AUTO
COMMENT 'Central alert configuration table. Alerts are deployed from this table into Databricks SQL Alerts (v2).'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'layer' = 'gold',
  'domain' = 'alerting',
  'entity_type' = 'configuration'
)
"""
    )

    # ------------------------------------------------------------------
    # alert_history (fact table)
    # ------------------------------------------------------------------
    spark.sql(
        f"""
CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.alert_history (
  evaluation_id STRING NOT NULL
    COMMENT 'Unique evaluation identifier (UUID).',

  alert_id STRING NOT NULL
    COMMENT 'Reference to alert_configurations.alert_id.',
  alert_name STRING NOT NULL
    COMMENT 'Alert name at time of evaluation (denormalized).',
  agent_domain STRING NOT NULL
    COMMENT 'Agent domain at time of evaluation (denormalized).',
  severity STRING NOT NULL
    COMMENT 'Severity at time of evaluation (denormalized).',

  evaluation_timestamp TIMESTAMP NOT NULL
    COMMENT 'When the alert was evaluated.',
  evaluation_date DATE NOT NULL
    COMMENT 'Date partition for evaluation_timestamp (derived at write time).',
  evaluation_status STRING NOT NULL
    COMMENT 'Evaluation result: OK, TRIGGERED, ERROR.',
  previous_status STRING
    COMMENT 'Previous status for state change detection.',

  query_result_value_double DOUBLE
    COMMENT 'Numeric value returned by query (if applicable).',
  query_result_value_string STRING
    COMMENT 'String value returned by query (if applicable).',

  threshold_operator STRING NOT NULL
    COMMENT 'Operator used for comparison (snapshot).',
  threshold_value_type STRING NOT NULL
    COMMENT 'Threshold value type at evaluation time (snapshot).',
  threshold_value_double DOUBLE
    COMMENT 'Threshold numeric value snapshot.',
  threshold_value_string STRING
    COMMENT 'Threshold string value snapshot.',
  threshold_value_bool BOOLEAN
    COMMENT 'Threshold boolean value snapshot.',

  query_duration_ms BIGINT
    COMMENT 'How long the query took to execute (ms).',
  error_message STRING
    COMMENT 'Error details if evaluation_status=ERROR.',

  ml_score DOUBLE
    COMMENT 'Optional ML anomaly score (0-1).',
  ml_suppressed BOOLEAN
    COMMENT 'Whether ML suppressed this alert (optional).',

  notification_sent BOOLEAN
    COMMENT 'Whether a notification was sent by this framework (optional).',
  notification_channels_used ARRAY<STRING>
    COMMENT 'Notification channels used (optional).',

  record_created_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
    COMMENT 'Insert timestamp.',

  CONSTRAINT pk_alert_history PRIMARY KEY (evaluation_id) NOT ENFORCED,
  CONSTRAINT chk_eval_status CHECK (evaluation_status IN ('OK','TRIGGERED','ERROR'))
)
USING DELTA
PARTITIONED BY (evaluation_date)
CLUSTER BY AUTO
COMMENT 'Alert evaluation history for analytics and audit. This table is populated by optional evaluator jobs (separate from native SQL alert history).'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'layer' = 'gold',
  'domain' = 'alerting',
  'entity_type' = 'fact'
)
"""
    )

    # FK constraints must be applied AFTER both tables exist (UC constraint timing best practice)
    try:
        spark.sql(
            f"""
ALTER TABLE {catalog}.{gold_schema}.alert_history
ADD CONSTRAINT fk_alert_history_alert
FOREIGN KEY (alert_id)
REFERENCES {catalog}.{gold_schema}.alert_configurations(alert_id)
NOT ENFORCED
"""
        )
    except Exception as e:
        # Idempotency: constraint already exists
        print(f"⚠ Could not add FK constraint (may already exist): {e}")


def seed_minimal_defaults(spark: SparkSession, catalog: str, gold_schema: str) -> None:
    """
    Insert a minimal set of default destinations and alerts if tables are empty.
    This keeps the framework usable out-of-the-box without committing to all 50+ planned alerts.
    """
    dest_table = f"{catalog}.{gold_schema}.notification_destinations"
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"

    dest_count = spark.table(dest_table).limit(1).count()
    if dest_count == 0:
        spark.sql(
            f"""
INSERT INTO {dest_table} (
  destination_id, destination_name, destination_type, databricks_destination_id,
  config_json, owner, is_enabled, created_by, tags
) VALUES
  ('default_email', 'Default Email (users)', 'EMAIL', NULL, NULL, 'data-engineering@company.com', TRUE, 'system',
    map('purpose','default','managed_by','setup_alerting_tables'))
"""
        )

    cfg_count = spark.table(cfg_table).limit(1).count()
    if cfg_count == 0:
        # Example alert: Tag coverage drop (aligned with phase3 addendum)
        spark.sql(
            f"""
INSERT INTO {cfg_table} (
  alert_id, alert_name, alert_description, agent_domain, severity,
  alert_query_template, query_source, source_artifact_name,
  threshold_column, threshold_operator, threshold_value_type, threshold_value_double,
  empty_result_state, aggregation_type,
  schedule_cron, schedule_timezone, pause_status, is_enabled,
  notification_channels, notify_on_ok, retrigger_seconds,
  use_custom_template, custom_subject_template, custom_body_template,
  owner, created_by, tags
) VALUES (
  'COST-012',
  'Tag Coverage Drop',
  'Alerts when tag coverage over the last 7 days drops below 80%. Business: Enforces chargeback/FinOps hygiene. Technical: based on fact_usage.is_tagged + list_cost aggregation.',
  'COST',
  'WARNING',
  $$
  WITH tagged_analysis AS (
    SELECT
      CASE
        WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
        ELSE 'TAGGED'
      END AS tag_status,
      SUM(list_cost) AS cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY CASE
      WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
      ELSE 'TAGGED'
    END
  )
  SELECT
    SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 AS tag_coverage_pct,
    'Tag coverage ' || ROUND(SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100, 1)
      || '% is below threshold (80%)' AS alert_message
  FROM tagged_analysis
  $$,
  'CUSTOM',
  NULL,
  'tag_coverage_pct',
  '<',
  'DOUBLE',
  80.0,
  'OK',
  'NONE',
  '0 0 8 * * ?',
  'America/Los_Angeles',
  'PAUSED',
  TRUE,
  array('default_email'),
  TRUE,
  3600,
  FALSE,
  NULL,
  NULL,
  'finops-team@company.com',
  'system',
  map('seed','true','pattern','tag_hygiene')
)
"""
        )


def main() -> None:
    dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
    dbutils.widgets.text("gold_schema", "gold", "Gold Schema")

    catalog, gold_schema = get_parameters()
    spark = SparkSession.builder.getOrCreate()

    print("=" * 80)
    print("ALERTING TABLES SETUP")
    print("=" * 80)
    print(f"Target: {catalog}.{gold_schema}")

    create_tables(spark, catalog, gold_schema)
    seed_minimal_defaults(spark, catalog, gold_schema)

    print("✓ Alerting tables ready")
    dbutils.notebook.exit("SUCCESS: Alerting tables created/verified")


if __name__ == "__main__":
    main()


