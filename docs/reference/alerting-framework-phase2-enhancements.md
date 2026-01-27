# Alerting Framework Phase 2 Enhancements - Detailed Specifications

**Date:** December 30, 2025  
**Status:** 📋 Planning Phase  
**Prerequisites:** Phase 1 (Core Framework) must be deployed and validated

---

## Overview

Phase 1 delivered a **production-ready config-driven alerting framework**. Phase 2 focuses on **intelligence, scale, and operational excellence** through 11 enhancement tracks.

**Timeline:** 4-6 weeks after Phase 1 validation  
**Effort:** ~80-120 hours total  
**Team:** 2-3 engineers

---

## Enhancement Tracks

### Priority Tier 1: Critical for Production Scale (4 weeks)

1. [Integration Tests](#1-integration-tests)
2. [Query Validation](#2-query-validation)
3. [Monitoring Metrics](#3-monitoring-metrics)
4. [Alert Templates](#4-alert-templates)

### Priority Tier 2: Intelligence & Performance (2-3 weeks)

5. [ML-Based Alert Suppression](#5-ml-based-alert-suppression)
6. [Parallel Sync](#6-parallel-sync)
7. [Incremental Sync](#7-incremental-sync)

### Priority Tier 3: Advanced Features (2-3 weeks)

8. [Alert History Analytics](#8-alert-history-analytics)
9. [Notification Destination Management](#9-notification-destination-management)
10. [Custom Template Testing](#10-custom-template-testing)
11. [Advanced Operators](#11-advanced-operators)

---

## Detailed Specifications

---

## 1. Integration Tests

### Problem
Unit tests validate helpers, but we need end-to-end validation of:
- Alert creation via API
- Query execution in SQL warehouse
- Notification delivery
- Config table sync accuracy

### Current State
```python
# Only unit tests exist
pytest -m unit tests/alerting/test_alerting_config.py
```

### Solution Architecture

```python
# tests/alerting/test_integration_sync_alerts.py

import pytest
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

@pytest.fixture(scope="module")
def test_catalog():
    """Test catalog for integration tests."""
    return "health_monitor_test"

@pytest.fixture(scope="module")
def cleanup_alerts(ws: WorkspaceClient, test_catalog):
    """Cleanup test alerts after test run."""
    yield
    # Cleanup logic
    alerts = ws.alerts.list()
    for alert in alerts:
        if alert.name.startswith("[TEST]"):
            ws.alerts.delete(alert.id)

@pytest.mark.integration
class TestAlertSync:
    """Integration tests for alert sync workflow."""
    
    def test_create_alert_end_to_end(self, spark, ws, test_catalog):
        """
        Test: Insert config → Run sync → Verify alert exists in workspace
        """
        # 1. Setup: Insert test alert config
        spark.sql(f"""
        INSERT INTO {test_catalog}.gold.alert_configurations
        VALUES (
            'TEST-001',
            'Integration Test Alert',
            'Test for CI/CD validation',
            'SELECT COUNT(*) as value FROM range(10)',
            'value',
            'WARNING',
            ...
        )
        """)
        
        # 2. Execute: Run sync_alerts
        from src.alerting.sync_sql_alerts import sync_alerts
        sync_alerts(
            spark=spark,
            catalog=test_catalog,
            gold_schema="gold",
            warehouse_id="test_warehouse_id",
            dry_run=False,
            api_base="/api/2.0/sql/alerts-v2",
            delete_disabled=False,
        )
        
        # 3. Verify: Alert exists in Databricks
        alerts = ws.alerts.list()
        alert_names = [a.name for a in alerts]
        assert "[WARNING] Integration Test Alert" in alert_names
        
        # 4. Verify: Config table updated correctly
        config = spark.sql(f"""
        SELECT databricks_alert_id, last_sync_status
        FROM {test_catalog}.gold.alert_configurations
        WHERE alert_id = 'TEST-001'
        """).first()
        
        assert config["databricks_alert_id"] is not None
        assert config["last_sync_status"] == "CREATED"
        
    def test_update_alert(self, spark, ws, test_catalog):
        """
        Test: Modify config → Run sync → Verify alert updated
        """
        # Update query in config
        spark.sql(f"""
        UPDATE {test_catalog}.gold.alert_configurations
        SET alert_query_template = 'SELECT COUNT(*) * 2 as value FROM range(10)'
        WHERE alert_id = 'TEST-001'
        """)
        
        # Run sync
        sync_alerts(...)
        
        # Verify status
        config = spark.sql(...).first()
        assert config["last_sync_status"] == "UPDATED"
        
    def test_delete_disabled_alert(self, spark, ws, test_catalog):
        """
        Test: Disable config → Run sync with delete_disabled=true → Verify removed
        """
        # Disable alert
        spark.sql(f"""
        UPDATE {test_catalog}.gold.alert_configurations
        SET is_enabled = false
        WHERE alert_id = 'TEST-001'
        """)
        
        # Run sync with delete enabled
        sync_alerts(..., delete_disabled=True)
        
        # Verify alert deleted from workspace
        alerts = ws.alerts.list()
        alert_names = [a.name for a in alerts]
        assert "[WARNING] Integration Test Alert" not in alert_names
        
        # Verify status
        config = spark.sql(...).first()
        assert config["last_sync_status"] == "DELETED"
        assert config["databricks_alert_id"] is None
```

### Implementation Steps

1. **Create test fixtures** (`tests/conftest.py`)
   ```python
   @pytest.fixture(scope="session")
   def ws() -> WorkspaceClient:
       """Workspace client for integration tests."""
       return WorkspaceClient()
   
   @pytest.fixture(scope="session")
   def spark() -> SparkSession:
       """Spark session for integration tests."""
       return SparkSession.builder.getOrCreate()
   ```

2. **Create test catalog/schema**
   ```python
   @pytest.fixture(scope="session", autouse=True)
   def setup_test_environment(spark):
       """Create test catalog and schema."""
       spark.sql("CREATE CATALOG IF NOT EXISTS health_monitor_test")
       spark.sql("CREATE SCHEMA IF NOT EXISTS health_monitor_test.gold")
       # Create test tables
       yield
       # Cleanup
   ```

3. **Add CI/CD integration**
   ```yaml
   # .github/workflows/test-integration.yml
   name: Integration Tests
   
   on:
     pull_request:
       branches: [main]
   
   jobs:
     test-integration:
       runs-on: ubuntu-latest
       steps:
         - uses: databricks/setup-cli@v1
         - name: Run integration tests
           run: |
             databricks bundle deploy -t test
             pytest -m integration tests/alerting/
   ```

**Effort:** 1 week  
**Value:** High - Prevents regression and validates end-to-end flow

---

## 2. Query Validation

### Problem
Alert queries stored in config table are **not validated** before deployment. Invalid SQL causes runtime failures.

**Example:**
```sql
-- Stored in alert_configurations.alert_query_template
SELECT invalid_column FROM non_existent_table
-- ❌ Deploys successfully but fails at evaluation time
```

### Current State
No validation - queries stored as-is in config table.

### Solution Architecture

```python
# src/alerting/query_validator.py

from pyspark.sql import SparkSession
from typing import Tuple, Optional
import re

def validate_query_syntax(
    spark: SparkSession,
    query_text: str,
    catalog: str,
    gold_schema: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validate SQL query syntax without executing it.
    
    Returns:
        (is_valid, error_message)
    """
    # 1. Render template with dummy values
    rendered = query_text.replace("${catalog}", catalog)
    rendered = rendered.replace("${gold_schema}", gold_schema)
    
    # 2. Use EXPLAIN to validate syntax
    try:
        spark.sql(f"EXPLAIN {rendered}").collect()
        return True, None
    except Exception as e:
        return False, str(e)


def validate_query_security(query_text: str) -> Tuple[bool, Optional[str]]:
    """
    Check for potentially dangerous SQL patterns.
    
    Returns:
        (is_safe, warning_message)
    """
    dangerous_patterns = [
        (r"DROP\s+TABLE", "DROP TABLE detected"),
        (r"DELETE\s+FROM", "DELETE FROM detected"),
        (r"TRUNCATE", "TRUNCATE detected"),
        (r"ALTER\s+TABLE", "ALTER TABLE detected"),
        (r"CREATE\s+OR\s+REPLACE", "CREATE OR REPLACE detected"),
    ]
    
    query_upper = query_text.upper()
    for pattern, message in dangerous_patterns:
        if re.search(pattern, query_upper):
            return False, message
    
    return True, None


def validate_query_references(
    spark: SparkSession,
    query_text: str,
    catalog: str,
    gold_schema: str,
) -> Tuple[bool, list]:
    """
    Extract and validate all table references exist.
    
    Returns:
        (all_exist, missing_tables)
    """
    # Render template
    rendered = query_text.replace("${catalog}", catalog)
    rendered = rendered.replace("${gold_schema}", gold_schema)
    
    # Extract table names using regex
    # Pattern: FROM|JOIN <catalog>.<schema>.<table>
    pattern = r"(?:FROM|JOIN)\s+([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)"
    table_refs = re.findall(pattern, rendered, re.IGNORECASE)
    
    missing = []
    for table_fqn in table_refs:
        try:
            spark.sql(f"DESCRIBE TABLE {table_fqn}").collect()
        except Exception:
            missing.append(table_fqn)
    
    return len(missing) == 0, missing


def validate_alert_query(
    spark: SparkSession,
    query_text: str,
    catalog: str,
    gold_schema: str,
) -> Tuple[bool, str]:
    """
    Comprehensive query validation.
    
    Returns:
        (is_valid, validation_message)
    """
    # Check 1: Security
    is_safe, warning = validate_query_security(query_text)
    if not is_safe:
        return False, f"Security check failed: {warning}"
    
    # Check 2: Syntax
    is_valid, error = validate_query_syntax(spark, query_text, catalog, gold_schema)
    if not is_valid:
        return False, f"Syntax error: {error}"
    
    # Check 3: Table references
    all_exist, missing = validate_query_references(spark, query_text, catalog, gold_schema)
    if not all_exist:
        return False, f"Missing tables: {', '.join(missing)}"
    
    return True, "Query validation passed"
```

### Integration with Setup Script

```python
# src/alerting/setup_alerting_tables.py

def add_validation_trigger():
    """Add trigger to validate queries on INSERT/UPDATE."""
    
    # Note: Databricks doesn't support triggers, so we use a separate validation job
    pass


# src/alerting/validate_all_queries.py

from src.alerting.query_validator import validate_alert_query

def validate_all_alert_queries(spark: SparkSession, catalog: str, gold_schema: str):
    """Validate all enabled alert queries."""
    
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    
    configs = (
        spark.table(cfg_table)
        .where(col("is_enabled") == True)
        .select("alert_id", "alert_query_template")
        .collect()
    )
    
    invalid_alerts = []
    
    for row in configs:
        is_valid, message = validate_alert_query(
            spark,
            row["alert_query_template"],
            catalog,
            gold_schema,
        )
        
        if not is_valid:
            invalid_alerts.append((row["alert_id"], message))
            print(f"❌ {row['alert_id']}: {message}")
        else:
            print(f"✅ {row['alert_id']}: Valid")
    
    if invalid_alerts:
        print(f"\n❌ {len(invalid_alerts)} invalid queries found!")
        raise RuntimeError("Query validation failed")
    
    print(f"\n✅ All {len(configs)} queries validated successfully!")
```

### Add to Job Workflow

```yaml
# resources/alerting/alerting_validation_job.yml

resources:
  jobs:
    alerting_validation_job:
      name: "[${bundle.target}] Health Monitor - Alert Query Validation"
      description: "Validates all alert queries before deployment"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      
      tasks:
        - task_key: validate_queries
          environment_key: default
          notebook_task:
            notebook_path: ../../src/alerting/validate_all_queries.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
      
      tags:
        job_level: atomic
        layer: alerting
        job_type: validation
```

### Integration with Composite Job

```yaml
# resources/alerting/alerting_setup_orchestrator_job.yml

tasks:
  - task_key: setup_tables
    run_job_task:
      job_id: ${resources.jobs.alerting_tables_job.id}
  
  # NEW: Validate queries before deployment
  - task_key: validate_queries
    depends_on:
      - task_key: setup_tables
    run_job_task:
      job_id: ${resources.jobs.alerting_validation_job.id}
  
  - task_key: deploy_alerts
    depends_on:
      - task_key: validate_queries  # ✅ Only deploy if validation passes
    run_job_task:
      job_id: ${resources.jobs.alerting_deploy_job.id}
```

**Effort:** 1 week  
**Value:** High - Prevents deployment of broken queries

---

## 3. Monitoring Metrics

### Problem
No observability into alerting system health:
- How many alerts are firing?
- What's the sync success rate?
- How long does sync take?
- Are there recurring failures?

### Current State
Only console logs - no structured metrics or dashboards.

### Solution Architecture

#### Step 1: Metrics Collection

```python
# src/alerting/alerting_metrics.py

from dataclasses import dataclass
from datetime import datetime
from pyspark.sql import SparkSession
import time

@dataclass
class AlertSyncMetrics:
    """Metrics for alert sync operation."""
    sync_run_id: str
    sync_started_at: datetime
    sync_ended_at: datetime
    total_alerts: int
    success_count: int
    error_count: int
    created_count: int
    updated_count: int
    deleted_count: int
    avg_api_latency_ms: float
    max_api_latency_ms: float
    total_duration_seconds: float
    

def log_sync_metrics(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    metrics: AlertSyncMetrics,
):
    """Log sync metrics to metrics table."""
    
    metrics_table = f"{catalog}.{gold_schema}.alert_sync_metrics"
    
    # Create metrics table if not exists
    spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {metrics_table} (
      sync_run_id STRING NOT NULL,
      sync_started_at TIMESTAMP NOT NULL,
      sync_ended_at TIMESTAMP NOT NULL,
      total_alerts INT NOT NULL,
      success_count INT NOT NULL,
      error_count INT NOT NULL,
      created_count INT NOT NULL,
      updated_count INT NOT NULL,
      deleted_count INT NOT NULL,
      avg_api_latency_ms DOUBLE NOT NULL,
      max_api_latency_ms DOUBLE NOT NULL,
      total_duration_seconds DOUBLE NOT NULL,
      CONSTRAINT pk_alert_sync_metrics PRIMARY KEY (sync_run_id) NOT ENFORCED
    )
    USING DELTA
    CLUSTER BY AUTO
    COMMENT 'Alert sync operation metrics for monitoring and analytics'
    TBLPROPERTIES (
      'delta.enableChangeDataFeed' = 'true',
      'layer' = 'gold',
      'domain' = 'alerting'
    )
    """)
    
    # Insert metrics
    spark.sql(f"""
    INSERT INTO {metrics_table} VALUES (
      '{metrics.sync_run_id}',
      '{metrics.sync_started_at}',
      '{metrics.sync_ended_at}',
      {metrics.total_alerts},
      {metrics.success_count},
      {metrics.error_count},
      {metrics.created_count},
      {metrics.updated_count},
      {metrics.deleted_count},
      {metrics.avg_api_latency_ms},
      {metrics.max_api_latency_ms},
      {metrics.total_duration_seconds}
    )
    """)
```

#### Step 2: Integrate into Sync Script

```python
# src/alerting/sync_sql_alerts.py

import uuid
from datetime import datetime

def sync_alerts(...):
    """Sync alerts with metrics tracking."""
    
    # Generate run ID
    sync_run_id = str(uuid.uuid4())
    started_at = datetime.now()
    
    # Track metrics
    api_latencies = []
    created_count = 0
    updated_count = 0
    deleted_count = 0
    error_count = 0
    
    # ... existing sync logic ...
    
    for cfg in configs:
        start_api = time.time()
        try:
            if not existing_alert:
                create_alert(...)
                created_count += 1
            else:
                update_alert(...)
                updated_count += 1
            
            api_latencies.append((time.time() - start_api) * 1000)  # ms
        except Exception:
            error_count += 1
    
    # Delete phase
    for disabled_cfg in disabled_configs:
        try:
            delete_alert(...)
            deleted_count += 1
        except Exception:
            error_count += 1
    
    # Log metrics
    ended_at = datetime.now()
    metrics = AlertSyncMetrics(
        sync_run_id=sync_run_id,
        sync_started_at=started_at,
        sync_ended_at=ended_at,
        total_alerts=len(configs),
        success_count=success,
        error_count=error_count,
        created_count=created_count,
        updated_count=updated_count,
        deleted_count=deleted_count,
        avg_api_latency_ms=sum(api_latencies) / len(api_latencies) if api_latencies else 0,
        max_api_latency_ms=max(api_latencies) if api_latencies else 0,
        total_duration_seconds=(ended_at - started_at).total_seconds(),
    )
    
    log_sync_metrics(spark, catalog, gold_schema, metrics)
```

#### Step 3: Monitoring Dashboard

```sql
-- Metric View for AI/BI Dashboard
CREATE VIEW ${catalog}.${gold_schema}.alert_sync_performance_metrics
WITH METRICS
LANGUAGE YAML
AS $$
version: "1.1"
comment: >
  Alert sync performance and reliability metrics.
  BEST FOR: Sync success rate | API latency trends | Error rates | Sync duration
  
source: ${catalog}.${gold_schema}.alert_sync_metrics

dimensions:
  - name: sync_date
    expr: DATE(source.sync_started_at)
    comment: Date of sync operation
    display_name: Sync Date
  
  - name: sync_hour
    expr: HOUR(source.sync_started_at)
    comment: Hour of sync operation
    display_name: Sync Hour

measures:
  - name: total_syncs
    expr: COUNT(source.sync_run_id)
    comment: Total number of sync operations
    display_name: Total Syncs
    format:
      type: number
  
  - name: success_rate
    expr: AVG(CAST(source.success_count AS DOUBLE) / NULLIF(source.total_alerts, 0))
    comment: Percentage of successful alert syncs
    display_name: Success Rate
    format:
      type: percentage
      decimal_places:
        type: exact
        places: 1
  
  - name: avg_duration
    expr: AVG(source.total_duration_seconds)
    comment: Average sync operation duration
    display_name: Avg Duration (s)
    format:
      type: number
      decimal_places:
        type: exact
        places: 2
  
  - name: avg_api_latency
    expr: AVG(source.avg_api_latency_ms)
    comment: Average API call latency
    display_name: Avg API Latency (ms)
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
$$
```

**Effort:** 3-4 days  
**Value:** High - Essential for production operations

---

## 4. Alert Templates

### Problem
Users must manually write SQL queries for common alert patterns. This is error-prone and time-consuming.

### Current State
Only 1 seed alert (Tag Coverage Drop). Users must write all other alerts from scratch.

### Solution: Alert Template Library

```python
# src/alerting/alert_templates.py

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class AlertTemplate:
    """Template for common alert patterns."""
    template_id: str
    template_name: str
    description: str
    required_params: List[str]
    query_template: str
    operator: str
    aggregation_column: str
    aggregation_type: str
    default_threshold_value: float
    severity: str
    notification_channels: List[str]


# Template Catalog
ALERT_TEMPLATES = {
    
    # Cost Monitoring Templates
    "COST_SPIKE": AlertTemplate(
        template_id="COST_SPIKE",
        template_name="Cost Spike Detection",
        description="Detect when daily cost exceeds threshold",
        required_params=["threshold_usd"],
        query_template="""
        SELECT SUM(list_cost) as daily_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date = CURRENT_DATE()
        """,
        operator="GREATER_THAN",
        aggregation_column="daily_cost",
        aggregation_type="SUM",
        default_threshold_value=5000.0,
        severity="WARNING",
        notification_channels=["cost_alerts"],
    ),
    
    "UNTAGGED_RESOURCES": AlertTemplate(
        template_id="UNTAGGED_RESOURCES",
        template_name="Untagged Resources",
        description="Alert when percentage of untagged resources exceeds threshold",
        required_params=["threshold_pct"],
        query_template="""
        WITH tagged_analysis AS (
          SELECT
            CASE WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 
                 THEN 'UNTAGGED' ELSE 'TAGGED' END AS tag_status,
            SUM(list_cost) AS cost
          FROM ${catalog}.${gold_schema}.fact_usage
          WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
          GROUP BY 1
        )
        SELECT 
          (SUM(CASE WHEN tag_status = 'UNTAGGED' THEN cost ELSE 0 END) / 
           NULLIF(SUM(cost), 0) * 100) AS untagged_pct
        FROM tagged_analysis
        """,
        operator="GREATER_THAN",
        aggregation_column="untagged_pct",
        aggregation_type=None,  # Already aggregated
        default_threshold_value=20.0,
        severity="WARNING",
        notification_channels=["governance_alerts"],
    ),
    
    # Reliability Templates
    "JOB_FAILURE_RATE": AlertTemplate(
        template_id="JOB_FAILURE_RATE",
        template_name="Job Failure Rate",
        description="Alert when job failure rate exceeds threshold",
        required_params=["threshold_pct", "lookback_hours"],
        query_template="""
        SELECT 
          (SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
           COUNT(*)) AS failure_rate_pct
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL {lookback_hours} HOURS
        """,
        operator="GREATER_THAN",
        aggregation_column="failure_rate_pct",
        aggregation_type=None,
        default_threshold_value=10.0,
        severity="CRITICAL",
        notification_channels=["reliability_alerts"],
    ),
    
    "LONG_RUNNING_JOBS": AlertTemplate(
        template_id="LONG_RUNNING_JOBS",
        template_name="Long Running Jobs",
        description="Alert on jobs exceeding duration threshold",
        required_params=["threshold_minutes"],
        query_template="""
        SELECT COUNT(*) as long_job_count
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE 
          start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
          AND duration_seconds > ({threshold_minutes} * 60)
          AND result_state != 'FAILED'
        """,
        operator="GREATER_THAN",
        aggregation_column="long_job_count",
        aggregation_type="COUNT",
        default_threshold_value=0,  # Alert on any occurrence
        severity="WARNING",
        notification_channels=["performance_alerts"],
    ),
    
    # Security Templates
    "FAILED_ACCESS_ATTEMPTS": AlertTemplate(
        template_id="FAILED_ACCESS_ATTEMPTS",
        template_name="Failed Access Attempts",
        description="Alert on spike in failed access attempts",
        required_params=["threshold_count", "lookback_hours"],
        query_template="""
        SELECT COUNT(*) as failed_attempts
        FROM ${catalog}.${gold_schema}.fact_audit_logs
        WHERE 
          event_date >= CURRENT_DATE() - INTERVAL {lookback_hours} HOURS
          AND action_result = 'FAILURE'
          AND action_name IN ('accessTable', 'accessCatalog', 'accessSchema')
        """,
        operator="GREATER_THAN",
        aggregation_column="failed_attempts",
        aggregation_type="COUNT",
        default_threshold_value=50,
        severity="CRITICAL",
        notification_channels=["security_alerts"],
    ),
    
    # Quality Templates
    "DATA_FRESHNESS": AlertTemplate(
        template_id="DATA_FRESHNESS",
        template_name="Data Freshness",
        description="Alert when table hasn't been updated recently",
        required_params=["table_name", "threshold_hours"],
        query_template="""
        SELECT 
          TIMESTAMPDIFF(HOUR, 
            (SELECT MAX(record_updated_timestamp) 
             FROM ${catalog}.${gold_schema}.{table_name}),
            CURRENT_TIMESTAMP()
          ) AS hours_since_update
        """,
        operator="GREATER_THAN",
        aggregation_column="hours_since_update",
        aggregation_type=None,
        default_threshold_value=24,
        severity="WARNING",
        notification_channels=["quality_alerts"],
    ),
}


def render_template(
    template: AlertTemplate,
    params: Dict[str, Any],
    catalog: str,
    gold_schema: str,
) -> Dict[str, Any]:
    """
    Render alert template with user-provided parameters.
    
    Args:
        template: AlertTemplate to render
        params: User-provided parameter values
        catalog: Target catalog
        gold_schema: Target schema
    
    Returns:
        Dict suitable for inserting into alert_configurations table
    """
    # Validate required params
    for param in template.required_params:
        if param not in params:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Render query with params
    query = template.query_template
    query = query.replace("${catalog}", catalog)
    query = query.replace("${gold_schema}", gold_schema)
    for param, value in params.items():
        query = query.replace(f"{{{param}}}", str(value))
    
    return {
        "alert_query_template": query,
        "operator": template.operator,
        "aggregation_column": template.aggregation_column,
        "aggregation_type": template.aggregation_type,
        "threshold_value_double": params.get("threshold_value", template.default_threshold_value),
        "severity": template.severity,
        "notification_channels": template.notification_channels,
    }


def list_templates() -> List[AlertTemplate]:
    """List all available alert templates."""
    return list(ALERT_TEMPLATES.values())


def get_template(template_id: str) -> AlertTemplate:
    """Get template by ID."""
    if template_id not in ALERT_TEMPLATES:
        raise ValueError(f"Unknown template: {template_id}")
    return ALERT_TEMPLATES[template_id]
```

#### Usage Example

```python
# Create alert from template
from src.alerting.alert_templates import get_template, render_template

# 1. Select template
template = get_template("COST_SPIKE")

# 2. Provide parameters
params = {
    "threshold_usd": 10000.0,  # Alert when daily cost > $10k
}

# 3. Render template
alert_config = render_template(
    template=template,
    params=params,
    catalog="health_monitor",
    gold_schema="gold",
)

# 4. Insert into config table
spark.sql(f"""
INSERT INTO {catalog}.{gold_schema}.alert_configurations
VALUES (
  'COST-{next_id}',
  '{template.template_name}',
  '{template.description}',
  '{alert_config["alert_query_template"]}',
  '{alert_config["aggregation_column"]}',
  '{alert_config["severity"]}',
  ...
)
""")
```

#### Add Template Seeding to Setup

```python
# src/alerting/setup_alerting_tables.py

def seed_template_alerts(spark: SparkSession, catalog: str, gold_schema: str):
    """Seed alert configurations from templates."""
    from src.alerting.alert_templates import ALERT_TEMPLATES, render_template
    
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    
    # Example: Create all default alerts
    templates_to_seed = [
        ("COST_SPIKE", {"threshold_usd": 5000}),
        ("UNTAGGED_RESOURCES", {"threshold_pct": 20}),
        ("JOB_FAILURE_RATE", {"threshold_pct": 10, "lookback_hours": 24}),
        ("FAILED_ACCESS_ATTEMPTS", {"threshold_count": 50, "lookback_hours": 24}),
    ]
    
    for i, (template_id, params) in enumerate(templates_to_seed, 1):
        template = ALERT_TEMPLATES[template_id]
        config = render_template(template, params, catalog, gold_schema)
        
        alert_id = f"{template.severity[:4].upper()}-{i:03d}"
        
        spark.sql(f"""
        INSERT INTO {cfg_table} VALUES (
          '{alert_id}',
          '{template.template_name}',
          '{template.description}',
          '{config["alert_query_template"]}',
          '{config["aggregation_column"]}',
          '{template.severity}',
          ...
        )
        """)
```

**Effort:** 1 week  
**Value:** Medium-High - Accelerates alert creation for users

---

## 5. ML-Based Alert Suppression

### Problem
Static thresholds cause **false positives** when:
- Normal variance triggers alerts
- Seasonal patterns (weekend vs weekday)
- Expected spikes (deployments, marketing campaigns)

### Current State
All alerts use static thresholds. No intelligent filtering.

### Solution Architecture

#### Phase 1: Anomaly Detection Model

```python
# src/ml/reliability/train_alert_anomaly_detector.py

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml import Pipeline
import mlflow

def train_anomaly_detector(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Train anomaly detection model for alert suppression.
    
    Model predicts: Is this alert value expected given context?
    """
    # Historical alert evaluations
    history = spark.table(f"{catalog}.{gold_schema}.alert_history")
    
    # Feature engineering
    features = (
        history
        .withColumn("hour_of_day", hour("evaluated_at"))
        .withColumn("day_of_week", dayofweek("evaluated_at"))
        .withColumn("is_weekend", dayofweek("evaluated_at").isin([1, 7]).cast("int"))
        .withColumn("month", month("evaluated_at"))
        
        # Rolling statistics (last 7 days)
        .withColumn("value_7d_avg", avg("query_result_value").over(
            Window.partitionBy("alert_id")
            .orderBy("evaluated_at")
            .rowsBetween(-7*24, -1)
        ))
        .withColumn("value_7d_stddev", stddev("query_result_value").over(
            Window.partitionBy("alert_id")
            .orderBy("evaluated_at")
            .rowsBetween(-7*24, -1)
        ))
        
        # Is this value an anomaly? (Z-score > 3)
        .withColumn("is_anomaly", 
            when(
                abs((col("query_result_value") - col("value_7d_avg")) / col("value_7d_stddev")) > 3,
                1.0
            ).otherwise(0.0)
        )
    )
    
    # Train model
    feature_cols = [
        "hour_of_day", "day_of_week", "is_weekend", "month",
        "value_7d_avg", "value_7d_stddev", "query_result_value"
    ]
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features"
    )
    
    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol="is_anomaly",
        predictionCol="anomaly_score",
        numTrees=100,
    )
    
    pipeline = Pipeline(stages=[assembler, rf])
    
    # Split data
    train, test = features.randomSplit([0.8, 0.2], seed=42)
    
    # Train
    with mlflow.start_run():
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("num_trees", 100)
        
        model = pipeline.fit(train)
        
        # Evaluate
        predictions = model.transform(test)
        from pyspark.ml.evaluation import BinaryClassificationEvaluator
        evaluator = BinaryClassificationEvaluator(
            labelCol="is_anomaly",
            rawPredictionCol="anomaly_score",
        )
        auc = evaluator.evaluate(predictions)
        mlflow.log_metric("auc", auc)
        
        # Log model
        mlflow.spark.log_model(
            model,
            "model",
            registered_model_name=f"{catalog}.{gold_schema}.alert_anomaly_detector",
        )
```

#### Phase 2: Integrate with Sync Script

```python
# src/alerting/sync_sql_alerts.py

def should_suppress_alert(
    spark: SparkSession,
    cfg: AlertConfigRow,
    current_value: float,
    catalog: str,
    gold_schema: str,
) -> Tuple[bool, float]:
    """
    Use ML model to determine if alert should be suppressed.
    
    Returns:
        (should_suppress, ml_score)
    """
    if not cfg.ml_model_enabled or not cfg.ml_model_name:
        return False, 0.0
    
    # Load model
    import mlflow
    model_uri = f"models:/{cfg.ml_model_name}/Production"
    model = mlflow.spark.load_model(model_uri)
    
    # Prepare features
    from datetime import datetime
    now = datetime.now()
    features_df = spark.createDataFrame([{
        "hour_of_day": now.hour,
        "day_of_week": now.isoweekday(),
        "is_weekend": 1 if now.isoweekday() in [6, 7] else 0,
        "month": now.month,
        "query_result_value": current_value,
        # TODO: Fetch historical stats
        "value_7d_avg": 0.0,
        "value_7d_stddev": 0.0,
    }])
    
    # Predict
    prediction = model.transform(features_df).select("anomaly_score").first()
    ml_score = prediction["anomaly_score"]
    
    # Suppress if score < threshold
    should_suppress = ml_score < cfg.ml_threshold
    
    return should_suppress, ml_score


def sync_alerts(...):
    """Sync alerts with ML suppression."""
    
    for cfg in configs:
        # ... create/update alert ...
        
        # Check if should suppress
        if cfg.ml_model_enabled:
            current_value = get_current_alert_value(spark, cfg)
            suppress, ml_score = should_suppress_alert(
                spark, cfg, current_value, catalog, gold_schema
            )
            
            if suppress:
                print(f"  🤖 ML suppressed (score: {ml_score:.3f})")
                # Mark alert as suppressed in history
                log_alert_evaluation(
                    spark, catalog, gold_schema,
                    alert_id=cfg.alert_id,
                    status="SUPPRESSED",
                    ml_score=ml_score,
                )
                continue
```

**Effort:** 2 weeks  
**Value:** High - Reduces false positive rate by 40-60%

---

## 6. Parallel Sync

### Problem
Current sync is **sequential**: Create/update one alert at a time.

**Performance:**
- 50 alerts × 500ms/alert = ~25 seconds
- 100 alerts × 500ms/alert = ~50 seconds

### Solution: Parallel API Calls

```python
# src/alerting/sync_sql_alerts.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

def sync_alert_parallel(
    cfg: AlertConfigRow,
    existing: Dict[str, dict],
    session: requests.Session,
    host: str,
    token: str,
    api_base: str,
    warehouse_id: str,
    subscriptions: List[dict],
    catalog: str,
    gold_schema: str,
) -> Tuple[str, bool, Optional[str], float]:
    """
    Sync single alert (called in parallel).
    
    Returns:
        (alert_id, success, error_message, latency_seconds)
    """
    display_name = f"[{cfg.severity}] {cfg.alert_name}"
    
    payload = build_alert_payload(
        cfg, catalog, gold_schema, warehouse_id, subscriptions
    )
    
    existing_alert = existing.get(display_name)
    started = time.time()
    
    try:
        if not existing_alert:
            created = create_alert(session, host, token, api_base, payload)
            deployed_id = created.get("id")
            action = "CREATED"
        else:
            alert_id = existing_alert.get("id")
            update_alert(session, host, token, api_base, alert_id, payload)
            deployed_id = alert_id
            action = "UPDATED"
        
        latency = time.time() - started
        return cfg.alert_id, True, None, latency
        
    except Exception as e:
        latency = time.time() - started
        return cfg.alert_id, False, str(e), latency


def sync_alerts_parallel(
    spark: SparkSession,
    configs: List[AlertConfigRow],
    existing: Dict[str, dict],
    warehouse_id: str,
    catalog: str,
    gold_schema: str,
    max_workers: int = 5,  # Tune based on rate limits
) -> Tuple[int, List[Tuple[str, str]]]:
    """
    Sync alerts in parallel.
    
    Returns:
        (success_count, errors)
    """
    session = _create_session()
    host, token = _get_api_host_and_token()
    
    # Build subscriptions once
    destination_map = _load_destination_map(spark, catalog, gold_schema)
    
    # Submit all tasks
    success_count = 0
    errors = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all alerts
        futures = {}
        for cfg in configs:
            subscriptions = build_subscriptions(
                cfg.notification_channels, destination_map
            )
            
            future = executor.submit(
                sync_alert_parallel,
                cfg, existing, session, host, token, api_base,
                warehouse_id, subscriptions, catalog, gold_schema,
            )
            futures[future] = cfg.alert_id
        
        # Collect results
        for future in as_completed(futures):
            alert_id = futures[future]
            try:
                aid, success, error, latency = future.result()
                
                if success:
                    print(f"✓ {aid} ({latency:.2f}s)")
                    success_count += 1
                else:
                    print(f"✗ {aid}: {error[:100]}")
                    errors.append((aid, error))
                
                # Update config table
                update_sync_status(
                    spark, f"{catalog}.{gold_schema}.alert_configurations",
                    aid, None, None, "CREATED" if success else "ERROR", error
                )
                
            except Exception as e:
                print(f"✗ {alert_id}: Unexpected error: {e}")
                errors.append((alert_id, str(e)))
    
    return success_count, errors
```

**Performance Improvement:**
- Sequential: 50 alerts × 500ms = 25s
- Parallel (5 workers): 50 alerts / 5 × 500ms = ~5s
- **5x speedup**

**Rate Limit Considerations:**
- Databricks API has rate limits (~100 req/min)
- `max_workers=5` stays well below limits
- Exponential backoff handles transient rate limit errors

**Effort:** 3-4 days  
**Value:** Medium - Significant for >50 alerts

---

## 7. Incremental Sync

### Problem
Current sync reads **all enabled configs** every run, even if nothing changed.

### Solution: Change Data Feed (CDF)

```python
# src/alerting/sync_sql_alerts_incremental.py

def get_changed_configs_since_last_sync(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    last_sync_timestamp: str,
) -> List[AlertConfigRow]:
    """
    Get only configs that changed since last sync using CDF.
    """
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    
    # Read changes from CDF
    changes = (
        spark.readStream
        .format("delta")
        .option("readChangeFeed", "true")
        .option("startingTimestamp", last_sync_timestamp)
        .table(cfg_table)
    )
    
    # Filter to INSERT and UPDATE operations
    changed_configs = (
        changes
        .where(col("_change_type").isin(["insert", "update_postimage"]))
        .where(col("is_enabled") == True)
        .select("alert_id", "alert_name", ...)  # All config columns
        .collect()
    )
    
    return [AlertConfigRow.from_spark_row(r) for r in changed_configs]


def sync_alerts_incremental(...):
    """Incremental sync using CDF."""
    
    # Get last sync timestamp
    last_sync = spark.sql(f"""
    SELECT MAX(sync_ended_at) as last_sync
    FROM {catalog}.{gold_schema}.alert_sync_metrics
    """).first()["last_sync"]
    
    if not last_sync:
        # First run - sync all
        print("First sync - processing all alerts")
        return sync_alerts(...)
    
    # Get changed configs
    changed = get_changed_configs_since_last_sync(
        spark, catalog, gold_schema, last_sync
    )
    
    if not changed:
        print("No changes detected - skipping sync")
        return
    
    print(f"Detected {len(changed)} changed alerts since {last_sync}")
    
    # Sync only changed
    # ... (same logic as sync_alerts but with changed configs only)
```

**Performance Improvement:**
- Full sync: ~30s for 50 alerts
- Incremental: ~2s for 3 changed alerts
- **15x speedup for typical updates**

**Effort:** 1 week  
**Value:** Medium - Most valuable when alert count >100

---

## 8. Alert History Analytics

### Problem
`alert_history` table exists but not populated. No analytics on:
- Which alerts fire most frequently?
- What's the false positive rate?
- How quickly are alerts resolved?

### Solution

#### Step 1: Populate Alert History

```python
# src/alerting/evaluate_alerts.py

def evaluate_all_alerts(spark: SparkSession, catalog: str, gold_schema: str):
    """Evaluate all enabled alerts and log results to history."""
    
    cfg_table = f"{catalog}.{gold_schema}.alert_configurations"
    history_table = f"{catalog}.{gold_schema}.alert_history"
    
    configs = spark.table(cfg_table).where(col("is_enabled") == True).collect()
    
    for cfg in configs:
        try:
            # Execute query
            query = render_query_template(
                cfg.alert_query_template, catalog, gold_schema
            )
            result = spark.sql(query).first()
            
            value = result[cfg.aggregation_column] if result else None
            
            # Check threshold
            threshold_met = evaluate_threshold(
                value,
                cfg.operator,
                cfg.threshold_value_double or cfg.threshold_value_string,
            )
            
            # Log to history
            spark.sql(f"""
            INSERT INTO {history_table} VALUES (
              uuid(),
              '{cfg.alert_id}',
              CURRENT_TIMESTAMP(),
              {value if value is not None else 'NULL'},
              {threshold_met},
              NULL,  # ml_score
              FALSE,  # ml_suppressed
              NULL   # resolution_time
            )
            """)
            
        except Exception as e:
            print(f"Error evaluating {cfg.alert_id}: {e}")
```

#### Step 2: Alert Analytics Views

```sql
-- Alert effectiveness metrics
CREATE VIEW ${catalog}.${gold_schema}.alert_analytics AS
SELECT 
  cfg.alert_id,
  cfg.alert_name,
  cfg.severity,
  cfg.agent_domain,
  
  -- Evaluation stats
  COUNT(*) as total_evaluations,
  SUM(CASE WHEN h.threshold_met THEN 1 ELSE 0 END) as times_triggered,
  (SUM(CASE WHEN h.threshold_met THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as trigger_rate_pct,
  
  -- Resolution stats
  AVG(h.resolution_time_seconds) as avg_resolution_time_seconds,
  MAX(h.resolution_time_seconds) as max_resolution_time_seconds,
  
  -- ML suppression stats
  SUM(CASE WHEN h.ml_suppressed THEN 1 ELSE 0 END) as ml_suppressed_count,
  
  -- Recency
  MAX(h.evaluated_at) as last_evaluated_at,
  MIN(h.evaluated_at) as first_evaluated_at

FROM ${catalog}.${gold_schema}.alert_configurations cfg
LEFT JOIN ${catalog}.${gold_schema}.alert_history h
  ON cfg.alert_id = h.alert_id

WHERE h.evaluated_at >= CURRENT_DATE() - INTERVAL 30 DAYS

GROUP BY 
  cfg.alert_id, cfg.alert_name, cfg.severity, cfg.agent_domain
```

#### Step 3: Dashboard

Create AI/BI dashboard with:
- **Alert Leaderboard** - Most frequently triggered alerts
- **False Positive Tracker** - Alerts with high trigger rate but low resolution
- **Response Time Analysis** - MTTR by severity/domain
- **ML Suppression Effectiveness** - Before/after false positive rate

**Effort:** 1 week  
**Value:** High - Critical for tuning alert quality

---

## 9. Notification Destination Management

### Problem
Administrators must manually create notification destinations in Databricks UI, then populate `databricks_destination_id` in the config table.

### Solution: Auto-Create Destinations

```python
# src/alerting/sync_notification_destinations.py

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import NotificationDestination, NotificationDestinationType

def sync_notification_destinations(
    spark: SparkSession,
    ws: WorkspaceClient,
    catalog: str,
    gold_schema: str,
):
    """Auto-create or update notification destinations."""
    
    dest_table = f"{catalog}.{gold_schema}.notification_destinations"
    
    dests = spark.table(dest_table).where(col("is_enabled") == True).collect()
    
    for dest in dests:
        if dest["databricks_destination_id"]:
            # Already exists - verify or update
            try:
                existing = ws.notification_destinations.get(dest["databricks_destination_id"])
                print(f"✓ {dest['destination_name']} already exists")
            except Exception:
                print(f"⚠ Destination {dest['destination_id']} has invalid UUID - recreating")
                dest["databricks_destination_id"] = None
        
        if not dest["databricks_destination_id"]:
            # Create new
            if dest["destination_type"] == "EMAIL":
                created = ws.notification_destinations.create(
                    name=dest["destination_name"],
                    destination_type=NotificationDestinationType.EMAIL,
                    config={
                        "addresses": dest["email_addresses"].split(","),
                    },
                )
            elif dest["destination_type"] == "SLACK":
                created = ws.notification_destinations.create(
                    name=dest["destination_name"],
                    destination_type=NotificationDestinationType.SLACK,
                    config={
                        "url": dest["slack_webhook_url"],
                    },
                )
            
            # Update config table with UUID
            spark.sql(f"""
            UPDATE {dest_table}
            SET databricks_destination_id = '{created.id}'
            WHERE destination_id = '{dest["destination_id"]}'
            """)
            
            print(f"✓ Created {dest['destination_name']} (ID: {created.id})")
```

**Effort:** 3-4 days  
**Value:** Medium - Convenience feature for deployment automation

---

## 10. Custom Template Testing

### Problem
Custom notification templates (`custom_subject_template`, `custom_body_template`) are not validated before deployment.

### Solution

```python
# src/alerting/template_validator.py

import re
from typing import Tuple, Optional

def validate_template_syntax(template: str) -> Tuple[bool, Optional[str]]:
    """Validate template placeholder syntax."""
    
    # Valid placeholders
    valid_placeholders = {
        "{{ALERT_ID}}",
        "{{ALERT_NAME}}",
        "{{SEVERITY}}",
        "{{QUERY_RESULT_VALUE}}",
        "{{THRESHOLD_VALUE}}",
        "{{OPERATOR}}",
        "{{TIMESTAMP}}",
    }
    
    # Find all placeholders
    found = re.findall(r"\{\{[A-Z_]+\}\}", template)
    
    for placeholder in found:
        if placeholder not in valid_placeholders:
            return False, f"Invalid placeholder: {placeholder}"
    
    return True, None


def render_test_template(template: str) -> str:
    """Render template with test values."""
    
    test_values = {
        "{{ALERT_ID}}": "TEST-001",
        "{{ALERT_NAME}}": "Test Alert",
        "{{SEVERITY}}": "WARNING",
        "{{QUERY_RESULT_VALUE}}": "42.5",
        "{{THRESHOLD_VALUE}}": "40.0",
        "{{OPERATOR}}": "GREATER_THAN",
        "{{TIMESTAMP}}": "2025-12-30 12:00:00",
    }
    
    rendered = template
    for placeholder, value in test_values.items():
        rendered = rendered.replace(placeholder, value)
    
    return rendered


# Integration test
@pytest.mark.unit
def test_custom_templates():
    """Test custom template validation and rendering."""
    
    # Valid template
    valid = "[{{SEVERITY}}] {{ALERT_NAME}} triggered at {{TIMESTAMP}}"
    is_valid, error = validate_template_syntax(valid)
    assert is_valid
    assert error is None
    
    # Invalid template
    invalid = "[{{UNKNOWN_FIELD}}] Alert"
    is_valid, error = validate_template_syntax(invalid)
    assert not is_valid
    assert "Invalid placeholder" in error
    
    # Render test
    rendered = render_test_template(valid)
    assert rendered == "[WARNING] Test Alert triggered at 2025-12-30 12:00:00"
```

**Effort:** 2 days  
**Value:** Low-Medium - Nice to have for custom template users

---

## 11. Advanced Operators

### Problem
Only basic operators supported: `>`, `>=`, `<`, `<=`, `==`, `!=`

Users may want:
- `BETWEEN` - Value in range
- `IN` - Value in set
- `MATCHES` - Regex pattern matching
- `CHANGES_BY` - Percentage change

### Solution

```python
# src/alerting/alerting_config.py

# Extended operator mapping
def map_operator_extended(operator: str) -> str:
    """Map config operator to Alerts v2 operator (extended)."""
    
    operator_map = {
        # Basic (existing)
        "GREATER_THAN": "GREATER_THAN",
        "GREATER_THAN_OR_EQUAL": "GREATER_THAN_OR_EQUAL",
        "LESS_THAN": "LESS_THAN",
        "LESS_THAN_OR_EQUAL": "LESS_THAN_OR_EQUAL",
        "EQUAL": "EQUAL",
        "NOT_EQUAL": "NOT_EQUAL",
        
        # Extended (new)
        "BETWEEN": "BETWEEN",  # Requires min/max thresholds
        "NOT_BETWEEN": "NOT_BETWEEN",
        "IN": "IN",  # Requires list of values
        "NOT_IN": "NOT_IN",
        "IS_NULL": "IS_NULL",
        "IS_NOT_NULL": "IS_NOT_NULL",
    }
    
    return operator_map.get(operator.upper(), "GREATER_THAN")


# Schema change for alert_configurations
def add_extended_operator_columns():
    """
    Add columns to support extended operators:
    - threshold_value_min DOUBLE (for BETWEEN)
    - threshold_value_max DOUBLE (for BETWEEN)
    - threshold_value_list ARRAY<STRING> (for IN)
    """
    pass
```

**Effort:** 1 week  
**Value:** Low - Nice to have for power users

---

## Implementation Roadmap

### Sprint 1 (Week 1-2): Foundation
- ✅ Integration Tests
- ✅ Query Validation
- ✅ Monitoring Metrics (partial)

### Sprint 2 (Week 3-4): Intelligence
- ✅ Alert Templates
- ✅ ML Suppression (training pipeline)
- ✅ Monitoring Metrics (dashboards)

### Sprint 3 (Week 5-6): Scale & Polish
- ✅ Parallel Sync
- ✅ Incremental Sync
- ✅ Alert Analytics
- ⚠️ Destination Management (optional)
- ⚠️ Custom Template Testing (optional)
- ⚠️ Advanced Operators (optional)

---

## Success Metrics

| Enhancement | Success Metric | Target |
|-------------|----------------|--------|
| Integration Tests | Test coverage | >80% |
| Query Validation | Invalid query detection rate | >95% |
| Monitoring Metrics | Dashboard availability | 99.9% |
| Alert Templates | % alerts using templates | >60% |
| ML Suppression | False positive reduction | 40-60% |
| Parallel Sync | Sync time for 100 alerts | <10s |
| Incremental Sync | Unnecessary syncs avoided | >80% |
| Alert Analytics | Alerts with analytics | 100% |

---

## Cost Estimation

| Enhancement | Compute Cost | Notes |
|-------------|--------------|-------|
| Integration Tests | ~$5/month | Runs in CI/CD |
| Query Validation | <$1/month | Lightweight SQL EXPLAIN |
| Monitoring Metrics | ~$10/month | Small metrics tables |
| Alert Templates | $0 | No additional compute |
| ML Suppression | ~$50/month | Model training + inference |
| Parallel Sync | $0 | Same API calls, faster |
| Incremental Sync | ~$5/month | CDF reads |
| Alert Analytics | ~$20/month | Additional history storage |

**Total:** ~$90/month additional cost

---

## Dependencies

### Required MLflow Version
- MLflow 3.0+ for GenAI integrations (ML Suppression)

### Required SDK Versions
- `databricks-sdk>=0.25.0` for notification destination management
- `requests>=2.31.0` (already required)

### Required Unity Catalog Features
- Change Data Feed (for Incremental Sync)
- Metric Views (for Analytics dashboards)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ML model drift | Medium | High | Monthly retraining, monitoring |
| API rate limits (parallel) | Low | Medium | Tune max_workers, exponential backoff |
| CDF storage costs | Low | Low | Configure retention policy |
| Template complexity | Low | Low | Comprehensive documentation |

---

## References

- [Databricks SQL Alerts API](https://docs.databricks.com/api/workspace/alerts)
- [Change Data Feed](https://docs.databricks.com/delta/delta-change-data-feed.html)
- [MLflow 3.0](https://mlflow.org/docs/latest/index.html)
- [ThreadPoolExecutor Best Practices](https://docs.python.org/3/library/concurrent.futures.html)

---

## Next Steps

1. **Review with Stakeholders** - Prioritize enhancements based on business value
2. **Spike ML Suppression** - 2-day proof of concept
3. **Create Jira Epics** - Break into trackable work items
4. **Allocate Resources** - Assign 2-3 engineers for 6-week sprint
5. **Set Up Test Environment** - Dedicated catalog for integration tests

