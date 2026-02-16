# Data Quality Standards

> **Document Owner:** Platform Architecture Team | **Status:** Approved | **Last Updated:** February 2026

## Overview

This document establishes enterprise-wide data quality standards using Databricks native capabilities. Data quality is enforced at three levels:

| Level | Technology | Use Case |
|-------|------------|----------|
| **Pipeline** | DLT Expectations | Real-time validation in streaming/batch pipelines |
| **Classic Jobs** | DQX Library | Quality checks in non-DLT Spark jobs |
| **Monitoring** | Lakehouse Monitor | Time-series trends, drift detection, profiling |

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **DQ-01** | All DLT pipelines must have data quality expectations | Critical |
| **DQ-02** | Classic Spark jobs must use DQX for quality validation | High |
| **DQ-03** | Gold layer tables must have Lakehouse Monitors | Critical |
| **DQ-04** | Quality failures must be captured, not silently dropped | Critical |

---

## DQ-01: DLT Expectations (Declarative Pipelines)

Delta Live Tables (DLT) provides built-in data quality expectations for real-time validation during pipeline execution.

### Expectation Types

| Decorator | Behavior | Use For |
|-----------|----------|---------|
| `@dlt.expect` | Logs warning, keeps row | Soft validation, monitoring |
| `@dlt.expect_or_drop` | Drops invalid rows silently | Non-critical filters |
| `@dlt.expect_or_fail` | Fails pipeline | Critical data integrity |
| `@dlt.expect_all` | Multiple expectations, log | Combined soft checks |
| `@dlt.expect_all_or_drop` | Multiple expectations, drop | Combined filters |
| `@dlt.expect_all_or_fail` | Multiple expectations, fail | Combined critical checks |

### Standard Expectations by Layer

**Silver Layer (Cleansing):**
```python
import dlt
from pyspark.sql.functions import col

@dlt.table(
    name="silver_orders",
    comment="Cleansed orders with data quality expectations"
)
@dlt.expect("valid_order_id", "order_id IS NOT NULL")
@dlt.expect("valid_amount", "order_amount >= 0")
@dlt.expect_or_drop("valid_date", "order_date IS NOT NULL")
@dlt.expect_or_fail("valid_customer", "customer_id IS NOT NULL")
def silver_orders():
    return dlt.read_stream("bronze_orders")
```

**Gold Layer (Business Rules):**
```python
@dlt.table(name="gold_daily_sales")
@dlt.expect_all_or_fail({
    "valid_revenue": "total_revenue >= 0",
    "valid_units": "units_sold >= 0",
    "valid_date": "sales_date IS NOT NULL"
})
def gold_daily_sales():
    return dlt.read("silver_orders").groupBy("sales_date").agg(...)
```

### Quarantine Pattern

Capture failed records instead of dropping them:

```python
# Main table - valid records only
@dlt.table(name="silver_orders")
@dlt.expect_all_or_drop({
    "valid_order_id": "order_id IS NOT NULL",
    "valid_amount": "order_amount >= 0"
})
def silver_orders():
    return dlt.read_stream("bronze_orders")

# Quarantine table - invalid records for review
@dlt.table(
    name="silver_orders_quarantine",
    comment="Invalid orders for data steward review"
)
def silver_orders_quarantine():
    return (
        dlt.read_stream("bronze_orders")
        .filter("order_id IS NULL OR order_amount < 0")
        .withColumn("quarantine_reason", 
            when(col("order_id").isNull(), "NULL_ORDER_ID")
            .when(col("order_amount") < 0, "NEGATIVE_AMOUNT")
            .otherwise("UNKNOWN"))
        .withColumn("quarantine_timestamp", current_timestamp())
    )
```

### Viewing Expectation Results

```sql
-- Query DLT event log for expectation results
SELECT
    timestamp,
    details:flow_name AS pipeline_name,
    details:expectation_name AS expectation,
    details:passed_records AS passed,
    details:failed_records AS failed
FROM event_log(TABLE(my_catalog.my_schema.__event_log))
WHERE event_type = 'flow_progress'
  AND details:expectation_name IS NOT NULL
ORDER BY timestamp DESC;
```

---

## DQ-02: DQX Library (Classic Spark Jobs)

For non-DLT Spark jobs (Bronze setup, Gold merge), use **DQX** (Databricks Labs Data Quality eXtensions) for validation with detailed diagnostics.

### Installation

```python
%pip install databricks-labs-dqx
```

### DQX vs DLT Expectations

| Feature | DLT Expectations | DQX |
|---------|------------------|-----|
| Environment | DLT pipelines only | Any Spark job |
| Configuration | Python decorators | YAML or Python |
| Failure detail | Pass/fail counts | Row-level diagnostics |
| Quarantine | Manual pattern | Built-in split |
| Custom checks | Limited | Extensible |

### Basic Usage

```python
from databricks.labs.dqx.engine import DQEngine
from databricks.labs.dqx.col_functions import is_not_null, is_not_less_than

# Initialize engine
dq_engine = DQEngine(spark)

# Define checks
checks = [
    is_not_null("order_id"),
    is_not_null("customer_id"),
    is_not_less_than("order_amount", limit=0),
]

# Apply checks and split valid/invalid
valid_df, invalid_df = dq_engine.apply_checks_by_metadata_and_split(
    df=source_df,
    checks=checks
)

# Write valid records to Gold
valid_df.write.format("delta").mode("append").saveAsTable("gold.orders")

# Write invalid records to quarantine
invalid_df.write.format("delta").mode("append").saveAsTable("gold.orders_quarantine")
```

### YAML Configuration

Store rules in YAML for maintainability:

```yaml
# quality_rules/orders.yaml
checks:
  - name: valid_order_id
    check: is_not_null
    column: order_id
    criticality: error
    
  - name: valid_amount
    check: is_not_less_than
    column: order_amount
    params:
      limit: 0
    criticality: error
    
  - name: valid_customer
    check: is_not_null
    column: customer_id
    criticality: error
```

```python
from databricks.labs.dqx.engine import DQEngine

dq_engine = DQEngine(spark)

# Load checks from YAML
valid_df, invalid_df = dq_engine.apply_checks_by_metadata_and_split(
    df=source_df,
    checks_file="quality_rules/orders.yaml"
)
```

### Gold Layer Pre-Merge Validation

```python
def merge_with_quality_checks(spark, silver_df, gold_table):
    """Merge Silver to Gold with DQX validation."""
    
    from databricks.labs.dqx.engine import DQEngine
    from databricks.labs.dqx.col_functions import is_not_null, is_not_less_than
    
    dq_engine = DQEngine(spark)
    
    # Define quality checks
    checks = [
        is_not_null("customer_key"),
        is_not_null("order_date"),
        is_not_less_than("order_amount", limit=0),
    ]
    
    # Split valid/invalid
    valid_df, invalid_df = dq_engine.apply_checks_by_metadata_and_split(
        df=silver_df,
        checks=checks
    )
    
    # Log quality metrics
    total = silver_df.count()
    valid_count = valid_df.count()
    invalid_count = invalid_df.count()
    print(f"Quality: {valid_count}/{total} passed ({100*valid_count/total:.1f}%)")
    
    # Quarantine invalid records
    if invalid_count > 0:
        invalid_df.write.format("delta").mode("append").saveAsTable(f"{gold_table}_quarantine")
        print(f"Quarantined {invalid_count} records")
    
    # Merge valid records
    from delta.tables import DeltaTable
    delta_gold = DeltaTable.forName(spark, gold_table)
    delta_gold.alias("target").merge(
        valid_df.alias("source"),
        "target.customer_key = source.customer_key"
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    
    return valid_count, invalid_count
```

### Available DQX Check Functions

| Function | Description | Example |
|----------|-------------|---------|
| `is_not_null` | Column is not null | `is_not_null("id")` |
| `is_not_less_than` | Value >= limit | `is_not_less_than("amount", limit=0)` |
| `is_not_greater_than` | Value <= limit | `is_not_greater_than("age", limit=150)` |
| `is_in_list` | Value in allowed set | `is_in_list("status", ["A", "B", "C"])` |
| `matches_regex` | Matches pattern | `matches_regex("email", r".*@.*\\..*")` |
| `is_unique` | No duplicates | `is_unique("order_id")` |

---

## DQ-03: Lakehouse Monitoring (Time-Series Trends)

Lakehouse Monitor provides automated profiling, drift detection, and anomaly detection for Gold layer tables.

### When to Use Lakehouse Monitoring

| Capability | Description |
|------------|-------------|
| **Data Profiling** | Summary statistics, null rates, distributions |
| **Drift Detection** | Compare current data to baseline or previous window |
| **Anomaly Detection** | Detect freshness and completeness issues |
| **Custom Metrics** | Business KPIs tracked over time |

### Creating a Monitor

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import MonitorTimeSeries

w = WorkspaceClient()

# Create time-series monitor
monitor = w.quality_monitors.create(
    table_name="catalog.gold.fact_daily_sales",
    assets_dir="/Shared/monitors/fact_daily_sales",
    output_schema_name="catalog.gold_monitoring",
    time_series=MonitorTimeSeries(
        timestamp_col="sales_date",
        granularities=["1 day"]
    ),
    schedule=MonitorCronSchedule(
        quartz_cron_expression="0 0 8 * * ?",  # Daily at 8 AM
        timezone_id="America/Los_Angeles"
    ),
    custom_metrics=[
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="daily_revenue",
            input_columns=["total_revenue"],
            definition="sum(total_revenue)",
            output_data_type="DOUBLE"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="null_customer_rate",
            input_columns=["customer_id"],
            definition="sum(case when customer_id is null then 1 else 0 end) / count(*)",
            output_data_type="DOUBLE"
        )
    ]
)
```

### Monitor Output Tables

Each monitor creates three output tables:

| Table | Content |
|-------|---------|
| `{table}_profile_metrics` | Column statistics per time window |
| `{table}_drift_metrics` | Drift scores vs baseline or previous window |
| `{table}_analysis` | Anomaly detection results |

### Querying Monitor Results

**Check null rate trends:**
```sql
SELECT 
    window_start,
    column_name,
    percent_null
FROM catalog.gold_monitoring.fact_daily_sales_profile_metrics
WHERE column_name = 'customer_id'
ORDER BY window_start DESC
LIMIT 30;
```

**Check drift scores:**
```sql
SELECT 
    window_start,
    column_name,
    drift_type,
    statistic,
    drift_score
FROM catalog.gold_monitoring.fact_daily_sales_drift_metrics
WHERE drift_score > 0.1  -- Significant drift
ORDER BY window_start DESC;
```

**Check anomalies:**
```sql
SELECT 
    detection_time,
    anomaly_type,
    severity,
    description
FROM catalog.gold_monitoring.fact_daily_sales_analysis
WHERE severity IN ('HIGH', 'CRITICAL')
ORDER BY detection_time DESC;
```

### Standard Monitors by Table Type

**Fact Tables:**
- Timestamp column: Transaction date
- Granularity: 1 day
- Custom metrics: Revenue totals, transaction counts, null rates

**Dimension Tables (SCD2):**
- Timestamp column: `effective_from`
- Granularity: 1 day
- Custom metrics: Active record counts, version distributions

### Alerting on Monitor Results

```sql
-- Create alert for high null rates
SELECT 
    window_start,
    column_name,
    percent_null
FROM catalog.gold_monitoring.fact_daily_sales_profile_metrics
WHERE column_name = 'customer_id'
  AND percent_null > 0.05  -- Alert if >5% nulls
  AND window_start >= current_date() - INTERVAL 1 DAY;
```

---

## DQ-04: Failure Capture Requirements

**Never silently drop invalid data.** Always capture failures for analysis.

### Quarantine Table Pattern

Every table with quality rules must have a corresponding quarantine table:

| Main Table | Quarantine Table |
|------------|------------------|
| `gold.dim_customer` | `gold.dim_customer_quarantine` |
| `gold.fact_orders` | `gold.fact_orders_quarantine` |

### Quarantine Table Schema

```sql
CREATE TABLE gold.fact_orders_quarantine (
    -- Original columns
    order_id STRING,
    customer_id STRING,
    order_amount DECIMAL(18,2),
    order_date DATE,
    
    -- Quality metadata
    quarantine_reason STRING NOT NULL,
    failed_checks ARRAY<STRING>,
    quarantine_timestamp TIMESTAMP NOT NULL,
    source_file STRING
)
USING DELTA
COMMENT 'Quarantined orders that failed quality checks for data steward review.';
```

### Quarantine Review Process

1. **Daily Review:** Data stewards review quarantine tables
2. **Root Cause:** Identify source system issues
3. **Remediation:** Fix upstream or adjust rules
4. **Reprocessing:** Move corrected records to main table

---

## Validation Checklist

### DLT Pipelines
- [ ] All Silver tables have `@dlt.expect` or `@dlt.expect_or_drop` decorators
- [ ] Critical validations use `@dlt.expect_or_fail`
- [ ] Quarantine tables capture dropped records
- [ ] Expectation results are monitored via event log

### Classic Spark Jobs
- [ ] DQX library installed in job environment
- [ ] Quality checks defined in YAML or Python
- [ ] `apply_checks_by_metadata_and_split` used for valid/invalid separation
- [ ] Invalid records written to quarantine table
- [ ] Quality metrics logged

### Lakehouse Monitoring
- [ ] All Gold fact tables have monitors
- [ ] Monitors have appropriate timestamp columns
- [ ] Custom metrics defined for business KPIs
- [ ] Drift detection enabled
- [ ] Alerts configured for anomalies

### Quarantine Management
- [ ] Every validated table has a quarantine table
- [ ] Quarantine includes failure reason
- [ ] Quarantine includes timestamp
- [ ] Review process documented
- [ ] Retention policy defined

---

## Quick Reference

### Expectation Decision Tree

```
Is this a DLT pipeline?
├── Yes → Use @dlt.expect decorators
│   ├── Non-critical → @dlt.expect (log only)
│   ├── Filter bad data → @dlt.expect_or_drop + quarantine
│   └── Critical → @dlt.expect_or_fail
└── No → Use DQX library
    ├── Define checks (YAML or Python)
    ├── Split valid/invalid
    └── Write invalid to quarantine
```

### Monitor Decision Tree

```
What type of table?
├── Gold Fact Table → Time-series monitor on transaction date
├── Gold Dimension (SCD2) → Time-series on effective_from
├── Inference Table → Time-series on request timestamp
└── Aggregate Table → Snapshot monitor (no timestamp)
```

### Quality Metrics to Track

| Metric | Threshold | Action |
|--------|-----------|--------|
| Null rate | < 1% (critical cols) | Alert data steward |
| Duplicate rate | 0% (PKs) | Fail pipeline |
| Out-of-range | < 0.1% | Review business rules |
| Drift score | < 0.1 | Investigate root cause |
| Freshness | Within SLA | Page on-call |

---

## Related Documents

- [Data Governance](01-data-governance.md)
- [Data Modeling](04-data-modeling.md)
- [Naming & Comment Standards](05-naming-comment-standards.md)
- [Silver Layer Patterns](../solution-architecture/data-pipelines/11-silver-layer-patterns.md)
- [Gold Layer Patterns](../solution-architecture/data-pipelines/12-gold-layer-patterns.md)
- [Lakehouse Monitoring](../solution-architecture/monitoring/41-lakehouse-monitoring.md)

---

## References

- [Data Quality Monitoring Overview](https://learn.microsoft.com/en-us/azure/databricks/data-quality-monitoring/)
- [DLT Expectations](https://docs.databricks.com/en/delta-live-tables/expectations.html)
- [DQX Library (Databricks Labs)](https://databrickslabs.github.io/dqx/)
- [Lakehouse Monitoring](https://docs.databricks.com/en/lakehouse-monitoring/index.html)
- [Monitor Custom Metrics](https://docs.databricks.com/en/lakehouse-monitoring/custom-metrics.html)
