# 11 - Implementation Guide

## Overview

This guide provides a **step-by-step implementation** of the alerting framework from scratch. Follow these phases in order to build a production-ready config-driven alerting system.

## Prerequisites

Before starting, ensure you have:

- [ ] Databricks workspace with Unity Catalog enabled
- [ ] Databricks CLI installed and authenticated
- [ ] Target catalog and schema created
- [ ] Gold layer tables deployed (data sources for alerts)
- [ ] SQL Warehouse available (ID noted)

## Phase 1: Project Structure (Day 1)

### 1.1 Create Directory Structure

```
src/
└── alerting/
    ├── __init__.py              # Package marker
    ├── alerting_config.py       # Configuration helpers
    ├── setup_alerting_tables.py # Table creation
    ├── seed_all_alerts.py       # Alert seeding
    ├── validate_alert_queries.py # Query validation
    ├── sync_notification_destinations.py # Destination sync
    └── sync_sql_alerts.py       # SDK-based sync

resources/
└── alerting/
    ├── alerting_setup_orchestrator_job.yml    # Composite orchestrator
    ├── alerting_tables_job.yml   # Atomic: table creation
    ├── alerting_seed_job.yml         # Atomic: alert seeding
    ├── alerting_validation_job.yml  # Atomic: query validation
    ├── alerting_notifications_job.yml  # Atomic: destinations
    └── alerting_deploy_job.yml    # Atomic: SDK deployment
```

### 1.2 Create alerting_config.py

```python
# src/alerting/alerting_config.py
"""Configuration helpers for the alerting framework."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AlertConfigRow:
    """Represents a row from alert_configurations table."""
    alert_id: str
    alert_name: str
    alert_description: Optional[str]
    agent_domain: str
    severity: str
    alert_query_template: str
    query_source: Optional[str]
    source_artifact_name: Optional[str]
    threshold_column: str
    threshold_operator: str
    threshold_value_type: str
    threshold_value_double: Optional[float]
    threshold_value_string: Optional[str]
    threshold_value_bool: Optional[bool]
    empty_result_state: str
    aggregation_type: Optional[str]
    schedule_cron: str
    schedule_timezone: str
    pause_status: str
    is_enabled: bool
    notification_channels: Optional[List[str]]
    notify_on_ok: bool
    retrigger_seconds: Optional[int]
    use_custom_template: bool
    custom_subject_template: Optional[str]
    custom_body_template: Optional[str]
    owner: str


def render_query_template(
    template: str, 
    catalog: str, 
    gold_schema: str
) -> str:
    """Replace placeholders in query template."""
    return template.replace(
        "${catalog}", catalog
    ).replace(
        "${gold_schema}", gold_schema
    )


def map_operator(operator: str) -> str:
    """Map configuration operator to SDK operator."""
    mapping = {
        ">": "GREATER_THAN",
        "<": "LESS_THAN",
        ">=": "GREATER_THAN_OR_EQUAL",
        "<=": "LESS_THAN_OR_EQUAL",
        "=": "EQUAL",
        "==": "EQUAL",
        "!=": "NOT_EQUAL",
        "<>": "NOT_EQUAL",
    }
    return mapping.get(operator, "GREATER_THAN")


def normalize_aggregation(aggregation_type: Optional[str]) -> Optional[str]:
    """Normalize aggregation type for SDK."""
    if not aggregation_type or aggregation_type.upper() in ("NONE", ""):
        return None
    
    valid = {"SUM", "COUNT", "COUNT_DISTINCT", "AVG", "MEDIAN", 
             "MIN", "MAX", "STDDEV", "FIRST"}
    
    upper = aggregation_type.upper()
    if upper in valid:
        return None if upper == "FIRST" else upper
    
    raise ValueError(f"Unsupported aggregation_type: {aggregation_type}")


def build_notification_subscriptions(
    channels: Optional[List[str]],
    destination_map: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Build notification subscriptions from channel list."""
    if not channels:
        return []
    
    subscriptions = []
    for channel in channels:
        if "@" in channel:
            subscriptions.append({"user_email": channel})
        elif channel in destination_map:
            subscriptions.append({"destination_id": destination_map[channel]})
        else:
            print(f"⚠️ Unknown channel: {channel}")
    
    return subscriptions
```

## Phase 2: Table Creation (Day 1)

### 2.1 Create setup_alerting_tables.py

```python
# Databricks notebook source
# src/alerting/setup_alerting_tables.py
"""Creates Unity Catalog tables for the alerting framework."""

from pyspark.sql import SparkSession


def create_tables(spark: SparkSession, catalog: str, gold_schema: str) -> None:
    """Create all alerting configuration tables."""
    
    # Ensure schema exists
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{gold_schema}")
    
    # alert_configurations table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.alert_configurations (
            alert_id STRING NOT NULL,
            alert_name STRING NOT NULL,
            alert_description STRING,
            agent_domain STRING NOT NULL,
            severity STRING NOT NULL,
            alert_query_template STRING NOT NULL,
            query_source STRING,
            source_artifact_name STRING,
            threshold_column STRING NOT NULL,
            threshold_operator STRING NOT NULL,
            threshold_value_type STRING NOT NULL,
            threshold_value_double DOUBLE,
            threshold_value_string STRING,
            threshold_value_bool BOOLEAN,
            empty_result_state STRING NOT NULL,
            aggregation_type STRING,
            schedule_cron STRING NOT NULL,
            schedule_timezone STRING NOT NULL,
            pause_status STRING NOT NULL,
            is_enabled BOOLEAN NOT NULL,
            notification_channels ARRAY<STRING>,
            notify_on_ok BOOLEAN NOT NULL,
            retrigger_seconds INT,
            use_custom_template BOOLEAN NOT NULL,
            custom_subject_template STRING,
            custom_body_template STRING,
            owner STRING NOT NULL,
            created_by STRING NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_by STRING,
            updated_at TIMESTAMP,
            tags MAP<STRING, STRING>,
            databricks_alert_id STRING,
            databricks_display_name STRING,
            last_synced_at TIMESTAMP,
            last_sync_status STRING,
            last_sync_error STRING,
            CONSTRAINT pk_alert_configurations PRIMARY KEY (alert_id) NOT ENFORCED
        )
        USING DELTA
        COMMENT 'Config-driven alert rules for Databricks SQL Alerts'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true'
        )
    """)
    
    # notification_destinations table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.notification_destinations (
            destination_id STRING NOT NULL,
            destination_name STRING NOT NULL,
            destination_type STRING NOT NULL,
            databricks_destination_id STRING,
            config_json STRING,
            owner STRING NOT NULL,
            is_enabled BOOLEAN NOT NULL,
            created_by STRING NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_by STRING,
            updated_at TIMESTAMP,
            tags MAP<STRING, STRING>,
            CONSTRAINT pk_notification_destinations PRIMARY KEY (destination_id) NOT ENFORCED
        )
        USING DELTA
    """)
    
    # alert_validation_results table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.alert_validation_results (
            alert_id STRING NOT NULL,
            is_valid BOOLEAN NOT NULL,
            error_message STRING,
            validation_timestamp TIMESTAMP NOT NULL
        )
        USING DELTA
    """)
    
    # alert_sync_metrics table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{gold_schema}.alert_sync_metrics (
            sync_run_id STRING NOT NULL,
            sync_started_at TIMESTAMP NOT NULL,
            sync_ended_at TIMESTAMP NOT NULL,
            total_alerts INT NOT NULL,
            success_count INT NOT NULL,
            error_count INT NOT NULL,
            created_count INT NOT NULL,
            updated_count INT NOT NULL,
            deleted_count INT NOT NULL,
            skipped_count INT NOT NULL,
            avg_api_latency_ms DOUBLE NOT NULL,
            max_api_latency_ms DOUBLE NOT NULL,
            min_api_latency_ms DOUBLE NOT NULL,
            p95_api_latency_ms DOUBLE NOT NULL,
            total_duration_seconds DOUBLE NOT NULL,
            dry_run BOOLEAN NOT NULL,
            catalog STRING NOT NULL,
            gold_schema STRING NOT NULL,
            error_summary STRING,
            CONSTRAINT pk_alert_sync_metrics PRIMARY KEY (sync_run_id) NOT ENFORCED
        )
        USING DELTA
    """)
    
    print(f"✓ Created all alerting tables in {catalog}.{gold_schema}")


def main():
    spark = SparkSession.builder.getOrCreate()
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    create_tables(spark, catalog, gold_schema)
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()
```

### 2.2 Create Job YAML

```yaml
# resources/alerting/alerting_tables_job.yml
resources:
  jobs:
    alerting_tables_job:
      name: "[${bundle.target}] Health Monitor - Alerting Tables Setup"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      
      tasks:
        - task_key: setup_tables
          environment_key: default
          notebook_task:
            notebook_path: ../../src/alerting/setup_alerting_tables.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
      
      tags:
        job_level: atomic
        layer: alerting
```

## Phase 3: Alert Seeding (Day 2)

### 3.1 Create seed_all_alerts.py

Use **DataFrame insertion** to avoid SQL escaping issues:

```python
# Databricks notebook source
# src/alerting/seed_all_alerts.py
"""Seeds all pre-built alerts into the configuration table."""

from datetime import datetime
from typing import Any, Dict, List
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, BooleanType, 
    IntegerType, DoubleType, TimestampType, ArrayType, MapType
)

# Schema for alert_configurations
ALERT_CONFIG_SCHEMA = StructType([
    StructField("alert_id", StringType(), False),
    StructField("alert_name", StringType(), False),
    StructField("alert_description", StringType(), True),
    StructField("agent_domain", StringType(), False),
    StructField("severity", StringType(), False),
    StructField("alert_query_template", StringType(), False),
    StructField("query_source", StringType(), True),
    StructField("source_artifact_name", StringType(), True),
    StructField("threshold_column", StringType(), False),
    StructField("threshold_operator", StringType(), False),
    StructField("threshold_value_type", StringType(), False),
    StructField("threshold_value_double", DoubleType(), True),
    StructField("threshold_value_string", StringType(), True),
    StructField("threshold_value_bool", BooleanType(), True),
    StructField("empty_result_state", StringType(), False),
    StructField("aggregation_type", StringType(), True),
    StructField("schedule_cron", StringType(), False),
    StructField("schedule_timezone", StringType(), False),
    StructField("pause_status", StringType(), False),
    StructField("is_enabled", BooleanType(), False),
    StructField("notification_channels", ArrayType(StringType()), True),
    StructField("notify_on_ok", BooleanType(), False),
    StructField("retrigger_seconds", IntegerType(), True),
    StructField("use_custom_template", BooleanType(), False),
    StructField("custom_subject_template", StringType(), True),
    StructField("custom_body_template", StringType(), True),
    StructField("owner", StringType(), False),
    StructField("created_by", StringType(), False),
    StructField("created_at", TimestampType(), False),
    StructField("updated_by", StringType(), True),
    StructField("updated_at", TimestampType(), True),
    StructField("tags", MapType(StringType(), StringType()), True),
    StructField("databricks_alert_id", StringType(), True),
    StructField("databricks_display_name", StringType(), True),
    StructField("last_synced_at", TimestampType(), True),
    StructField("last_sync_status", StringType(), True),
    StructField("last_sync_error", StringType(), True),
])

# Define alerts (see 10-alert-templates.md for full list)
COST_ALERTS = [
    {
        "alert_id": "COST-001",
        "alert_name": "Daily Cost Spike Alert",
        "alert_description": "Alerts when daily spend exceeds $5000",
        "agent_domain": "COST",
        "severity": "WARNING",
        "alert_query_template": """SELECT SUM(list_cost) as daily_cost, 'Daily cost $' || ROUND(SUM(list_cost), 2) || ' exceeds threshold' as alert_message FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date = CURRENT_DATE() - 1 HAVING SUM(list_cost) > 5000""",
        "threshold_column": "daily_cost",
        "threshold_operator": ">",
        "threshold_value_type": "DOUBLE",
        "threshold_value_double": 5000.0,
        "empty_result_state": "OK",
        "schedule_cron": "0 0 6 * * ?",
        "schedule_timezone": "America/Los_Angeles",
        "pause_status": "UNPAUSED",
        "is_enabled": True,
        "notification_channels": ["default_email"],
        "notify_on_ok": False,
        "use_custom_template": False,
        "owner": "finops@company.com",
    },
    # ... more alerts
]

def insert_alerts(spark: SparkSession, catalog: str, gold_schema: str, alerts: List[Dict]) -> int:
    """Insert alerts using DataFrame."""
    table = f"{catalog}.{gold_schema}.alert_configurations"
    
    rows = []
    for alert in alerts:
        rows.append({
            **alert,
            "query_source": alert.get("query_source", "CUSTOM"),
            "source_artifact_name": alert.get("source_artifact_name"),
            "aggregation_type": alert.get("aggregation_type"),
            "retrigger_seconds": alert.get("retrigger_seconds"),
            "custom_subject_template": alert.get("custom_subject_template"),
            "custom_body_template": alert.get("custom_body_template"),
            "created_by": "seed_all_alerts",
            "created_at": datetime.now(),
            "updated_by": None,
            "updated_at": None,
            "tags": alert.get("tags", {}),
            "databricks_alert_id": None,
            "databricks_display_name": None,
            "last_synced_at": None,
            "last_sync_status": None,
            "last_sync_error": None,
        })
    
    df = spark.createDataFrame(rows, schema=ALERT_CONFIG_SCHEMA)
    df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(table)
    
    return len(rows)


def main():
    spark = SparkSession.builder.getOrCreate()
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    force_reseed = dbutils.widgets.get("force_reseed") == "true"
    
    table = f"{catalog}.{gold_schema}.alert_configurations"
    
    if force_reseed:
        spark.sql(f"DELETE FROM {table}")
        print("Cleared existing alerts (force_reseed=true)")
    
    # Insert all alerts
    all_alerts = COST_ALERTS  # + SECURITY_ALERTS + ... 
    count = insert_alerts(spark, catalog, gold_schema, all_alerts)
    
    print(f"✓ Seeded {count} alerts into {table}")
    dbutils.notebook.exit(f"SUCCESS: {count} alerts seeded")


if __name__ == "__main__":
    main()
```

## Phase 4: Query Validation (Day 2)

See [07-query-validation.md](07-query-validation.md) for complete implementation.

## Phase 5: SDK Deployment (Day 3-4)

### 5.1 Create sync_sql_alerts.py

```python
# Databricks notebook source
# COMMAND ----------
# MAGIC %pip install --upgrade databricks-sdk>=0.40.0 --quiet
# MAGIC %restart_python
# COMMAND ----------

# src/alerting/sync_sql_alerts.py
"""Syncs alert configurations to Databricks SQL Alerts using SDK."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    AlertV2,
    AlertV2Condition,
    AlertV2ConditionOperand,
    AlertV2ConditionThreshold,
    AlertV2ConditionThresholdValue,
    AlertV2Notification,
    AlertV2NotificationSubscription,
    AlertV2Schedule,
)
from databricks.sdk.errors import ResourceAlreadyExists
from pyspark.sql import SparkSession

from alerting.alerting_config import (
    AlertConfigRow,
    render_query_template,
    map_operator,
    normalize_aggregation,
    build_notification_subscriptions,
)


def load_alert_configs(spark: SparkSession, catalog: str, gold_schema: str) -> List[AlertConfigRow]:
    """Load enabled alert configurations from Delta table."""
    df = spark.sql(f"""
        SELECT * FROM {catalog}.{gold_schema}.alert_configurations
        WHERE is_enabled = TRUE
    """)
    
    return [AlertConfigRow(**row.asDict()) for row in df.collect()]


def build_alert_v2(
    config: AlertConfigRow,
    warehouse_id: str,
    catalog: str,
    gold_schema: str,
    destination_map: Dict[str, str]
) -> AlertV2:
    """Build AlertV2 object from configuration."""
    
    query_text = render_query_template(config.alert_query_template, catalog, gold_schema)
    
    # Build condition based on value type
    threshold_value = AlertV2ConditionThresholdValue()
    if config.threshold_value_type == "DOUBLE":
        threshold_value.double_value = config.threshold_value_double
    elif config.threshold_value_type == "STRING":
        threshold_value.string_value = config.threshold_value_string
    elif config.threshold_value_type == "BOOLEAN":
        threshold_value.bool_value = config.threshold_value_bool
    
    condition = AlertV2Condition(
        operand=AlertV2ConditionOperand(column={"name": config.threshold_column}),
        op=map_operator(config.threshold_operator),
        threshold=AlertV2ConditionThreshold(value=threshold_value),
        empty_result_state=config.empty_result_state,
    )
    
    # Build notification
    subscriptions = []
    for channel in (config.notification_channels or []):
        if "@" in channel:
            subscriptions.append(AlertV2NotificationSubscription(user_email=channel))
        elif channel in destination_map:
            subscriptions.append(AlertV2NotificationSubscription(destination_id=destination_map[channel]))
    
    notification = AlertV2Notification(
        subscriptions=subscriptions,
        notify_on_ok=config.notify_on_ok,
    )
    
    schedule = AlertV2Schedule(
        quartz_cron_schedule=config.schedule_cron,
        timezone_id=config.schedule_timezone,
        pause_status=config.pause_status,
    )
    
    return AlertV2(
        display_name=config.alert_name,
        query_text=query_text,
        warehouse_id=warehouse_id,
        condition=condition,
        notification=notification,
        schedule=schedule,
    )


def sync_alerts(
    spark: SparkSession,
    ws: WorkspaceClient,
    catalog: str,
    gold_schema: str,
    warehouse_id: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Sync alerts with partial success handling."""
    
    configs = load_alert_configs(spark, catalog, gold_schema)
    destination_map = {}  # Load from notification_destinations if needed
    
    successes = []
    errors = []
    
    for config in configs:
        try:
            alert = build_alert_v2(config, warehouse_id, catalog, gold_schema, destination_map)
            
            if dry_run:
                print(f"[DRY RUN] {config.alert_id}: {config.alert_name}")
                successes.append(config.alert_id)
                continue
            
            # Try to create
            try:
                result = ws.alerts_v2.create_alert(alert)
                action = "CREATED"
            except ResourceAlreadyExists:
                # Find and update
                existing = None
                for a in ws.alerts_v2.list_alerts():
                    if a.display_name == alert.display_name:
                        existing = a
                        break
                
                if existing:
                    ws.alerts_v2.update_alert(
                        id=existing.id,
                        alert=alert,
                        update_mask="display_name,query_text,warehouse_id,condition,notification,schedule"
                    )
                    action = "UPDATED"
                    result = existing
                else:
                    raise RuntimeError(f"Alert exists but cannot find: {alert.display_name}")
            
            successes.append(config.alert_id)
            print(f"✓ {config.alert_id}: {action}")
            
        except Exception as e:
            errors.append((config.alert_id, str(e)[:200]))
            print(f"✗ {config.alert_id}: {e}")
    
    # Evaluate success rate
    total = len(configs)
    success_rate = len(successes) / total if total > 0 else 0
    
    print(f"\nSummary: {len(successes)}/{total} ({success_rate:.1%})")
    
    if errors:
        print(f"\nFailed ({len(errors)}):")
        for aid, msg in errors[:10]:
            print(f"  - {aid}: {msg}")
    
    if success_rate < 0.90:
        raise RuntimeError(f"Too many failures ({len(errors)}/{total})")
    elif errors:
        print(f"\n⚠️ WARNING: {len(errors)} failures (continuing)")
    
    return {"success": len(successes), "errors": len(errors)}


def main():
    spark = SparkSession.builder.getOrCreate()
    ws = WorkspaceClient()
    
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    warehouse_id = dbutils.widgets.get("warehouse_id")
    dry_run = dbutils.widgets.get("dry_run") == "true"
    
    results = sync_alerts(spark, ws, catalog, gold_schema, warehouse_id, dry_run)
    
    dbutils.notebook.exit(f"SUCCESS: {results}")


if __name__ == "__main__":
    main()
```

## Phase 6: Job Orchestration (Day 4)

### 6.1 Create Composite Job

See [08-hierarchical-job-architecture.md](08-hierarchical-job-architecture.md) for complete YAML.

### 6.2 Update databricks.yml

```yaml
# databricks.yml
include:
  - resources/*.yml
  - resources/alerting/*.yml  # Add alerting jobs
```

## Phase 7: Deployment (Day 5)

### 7.1 Deploy Bundle

```bash
# Validate
databricks bundle validate -t dev

# Deploy
databricks bundle deploy -t dev
```

### 7.2 Run Setup

```bash
# Run complete alerting setup
databricks bundle run -t dev alerting_setup_orchestrator_job
```

### 7.3 Verify

```sql
-- Check alerts created
SELECT alert_id, alert_name, last_sync_status
FROM my_catalog.gold.alert_configurations
WHERE is_enabled = TRUE;

-- Check validation results
SELECT * FROM my_catalog.gold.alert_validation_results
WHERE is_valid = FALSE;
```

## Checklist Summary

- [ ] **Phase 1**: Directory structure created
- [ ] **Phase 2**: Tables created in Unity Catalog
- [ ] **Phase 3**: Alerts seeded (29 alerts)
- [ ] **Phase 4**: Query validation passes
- [ ] **Phase 5**: SDK sync engine implemented
- [ ] **Phase 6**: Hierarchical jobs configured
- [ ] **Phase 7**: Deployed and verified

## Next Steps

- **[12-Deployment and Operations](12-deployment-and-operations.md)**: Production deployment
- **[Appendix D](appendices/D-troubleshooting.md)**: Troubleshooting common issues


