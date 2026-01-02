# 03 - Custom Metrics

## Overview

Custom metrics are the core of the Lakehouse Monitoring system. They transform raw data in Gold layer tables into **business-meaningful KPIs** that can be tracked over time and compared across periods.

This document explains the three metric types, their patterns, and best practices for implementation.

## Metric Types

Lakehouse Monitoring supports three types of custom metrics:

| Type | Purpose | Storage | Example |
|------|---------|---------|---------|
| **AGGREGATE** | Base measurements from source data | `_profile_metrics` | `SUM(list_cost)` |
| **DERIVED** | Calculated from other metrics | `_profile_metrics` | `success_rate = success_count / total_runs * 100` |
| **DRIFT** | Period-over-period comparison | `_drift_metrics` | `current_cost - baseline_cost` |

### Metric Type Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOURCE TABLE (Gold)                                │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  fact_usage                                                          │  │
│   │  • list_cost (DOUBLE)                                                │  │
│   │  • usage_quantity (DOUBLE)                                           │  │
│   │  • is_tagged (BOOLEAN)                                               │  │
│   │  • sku_name (STRING)                                                 │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGGREGATE METRICS                                    │
│                         (Base measurements)                                  │
│                                                                              │
│   total_daily_cost = SUM(list_cost)                                         │
│   total_daily_dbu = SUM(usage_quantity)                                     │
│   tagged_cost = SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END)          │
│   record_count = COUNT(*)                                                   │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DERIVED METRICS                                      │
│                         (Calculated ratios)                                  │
│                                                                              │
│   tag_coverage_pct = tagged_cost * 100.0 / NULLIF(total_daily_cost, 0)      │
│   avg_cost_per_record = total_daily_cost / NULLIF(record_count, 0)          │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DRIFT METRICS                                       │
│                          (Period comparison)                                 │
│                                                                              │
│   cost_drift_pct = ((current.total_daily_cost - base.total_daily_cost)      │
│                    / NULLIF(base.total_daily_cost, 0)) * 100                │
│   tag_coverage_drift = current.tag_coverage_pct - base.tag_coverage_pct     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AGGREGATE Metrics

AGGREGATE metrics are **base measurements** computed directly from source table columns using SQL aggregation functions.

### Syntax

```python
from monitor_utils import create_aggregate_metric

metric = create_aggregate_metric(
    name="total_daily_cost",      # Metric name (becomes column in output)
    definition="SUM(list_cost)",  # SQL aggregation expression
    output_type="DOUBLE"          # DOUBLE or LONG
)
```

### Helper Function

```python
def create_aggregate_metric(name: str, definition: str, output_type: str = "DOUBLE"):
    """
    Helper to create an AGGREGATE custom metric.

    Args:
        name: Metric name (column name in profile_metrics)
        definition: SQL aggregation expression
        output_type: Output data type (DOUBLE, LONG)
    """
    if output_type == "DOUBLE":
        data_type = T.StructField("output", T.DoubleType()).json()
    elif output_type == "LONG":
        data_type = T.StructField("output", T.LongType()).json()
    else:
        raise ValueError(f"Unknown output type: {output_type}")

    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
        name=name,
        input_columns=[":table"],  # Table-level aggregation
        definition=definition,
        output_data_type=data_type
    )
```

### Common Patterns

#### Count Metrics

```python
# Total records
create_aggregate_metric("record_count", "COUNT(*)", "LONG")

# Distinct counts
create_aggregate_metric("distinct_users", "COUNT(DISTINCT user_id)", "LONG")

# Conditional counts
create_aggregate_metric(
    "failed_count",
    "SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END)",
    "LONG"
)
```

#### Sum Metrics

```python
# Simple sum
create_aggregate_metric("total_cost", "SUM(list_cost)", "DOUBLE")

# Conditional sum
create_aggregate_metric(
    "serverless_cost",
    "SUM(CASE WHEN is_serverless = TRUE THEN list_cost ELSE 0 END)",
    "DOUBLE"
)
```

#### Average Metrics

```python
# Simple average
create_aggregate_metric("avg_duration_ms", "AVG(duration_ms)", "DOUBLE")

# Null-safe average
create_aggregate_metric("avg_cost_per_dbu", "AVG(NULLIF(list_price, 0))", "DOUBLE")
```

#### Percentile Metrics

```python
# P50 (median)
create_aggregate_metric("p50_duration_ms", "PERCENTILE(duration_ms, 0.50)", "DOUBLE")

# P95
create_aggregate_metric("p95_duration_ms", "PERCENTILE(duration_ms, 0.95)", "DOUBLE")

# P99
create_aggregate_metric("p99_duration_ms", "PERCENTILE(duration_ms, 0.99)", "DOUBLE")
```

#### Min/Max Metrics

```python
create_aggregate_metric("max_duration_ms", "MAX(duration_ms)", "DOUBLE")
create_aggregate_metric("min_duration_ms", "MIN(duration_ms)", "DOUBLE")
```

#### Standard Deviation

```python
create_aggregate_metric("stddev_duration", "STDDEV(duration_ms)", "DOUBLE")
```

## DERIVED Metrics

DERIVED metrics are **calculated from other metrics** using simple expressions. They reference AGGREGATE metrics by name.

### Syntax

```python
from monitor_utils import create_derived_metric

metric = create_derived_metric(
    name="success_rate",
    definition="success_count * 100.0 / NULLIF(total_runs, 0)"
)
```

### Helper Function

```python
def create_derived_metric(name: str, definition: str):
    """
    Helper to create a DERIVED custom metric.

    Args:
        name: Metric name (column name in profile_metrics)
        definition: SQL expression referencing other metrics
    """
    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
        name=name,
        input_columns=[":table"],  # Must match AGGREGATE metrics
        definition=definition,
        output_data_type=T.StructField("output", T.DoubleType()).json()
    )
```

### Common Patterns

#### Percentage/Rate Metrics

```python
# Success rate
create_derived_metric(
    "success_rate",
    "success_count * 100.0 / NULLIF(total_runs, 0)"
)

# Failure rate
create_derived_metric(
    "failure_rate",
    "failure_count * 100.0 / NULLIF(total_runs, 0)"
)

# Coverage percentage
create_derived_metric(
    "tag_coverage_pct",
    "tagged_cost * 100.0 / NULLIF(total_cost, 0)"
)
```

#### Ratio Metrics

```python
# Average per entity
create_derived_metric(
    "avg_runs_per_job",
    "total_runs * 1.0 / NULLIF(distinct_jobs, 0)"
)

# Coefficient of variation
create_derived_metric(
    "duration_cv",
    "stddev_duration / NULLIF(avg_duration, 0)"
)

# P90/P50 skew ratio
create_derived_metric(
    "duration_skew_ratio",
    "p90_duration / NULLIF(p50_duration, 0)"
)
```

#### Composite Metrics

```python
# Total of multiple metrics
create_derived_metric(
    "total_network_gb",
    "network_sent_gb + network_received_gb"
)

# Combined CPU utilization
create_derived_metric(
    "avg_cpu_total_pct",
    "avg_cpu_user_pct + avg_cpu_system_pct"
)
```

### ⚠️ Important: NULLIF for Division

Always use `NULLIF(denominator, 0)` to prevent division by zero errors:

```python
# ❌ WRONG: May cause division by zero
create_derived_metric("rate", "count_a / count_b")

# ✅ CORRECT: Safe division
create_derived_metric("rate", "count_a * 100.0 / NULLIF(count_b, 0)")
```

## DRIFT Metrics

DRIFT metrics **compare values between periods** using special placeholders for current and baseline data.

### Syntax

```python
from monitor_utils import create_drift_metric

metric = create_drift_metric(
    name="cost_drift_pct",
    definition="(({{current_df}}.total_cost - {{base_df}}.total_cost) / NULLIF({{base_df}}.total_cost, 0)) * 100"
)
```

### Helper Function

```python
def create_drift_metric(name: str, definition: str):
    """
    Helper to create a DRIFT custom metric.

    Args:
        name: Metric name (column name in drift_metrics)
        definition: SQL expression with {{current_df}} and {{base_df}}
    """
    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
        name=name,
        input_columns=[":table"],  # Must match AGGREGATE metrics
        definition=definition,
        output_data_type=T.StructField("output", T.DoubleType()).json()
    )
```

### Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{current_df}}` | Current period's metrics | `{{current_df}}.total_cost` |
| `{{base_df}}` | Baseline period's metrics | `{{base_df}}.total_cost` |

### Common Patterns

#### Percentage Change

```python
# Percentage change from baseline
create_drift_metric(
    "cost_drift_pct",
    "(({{current_df}}.total_cost - {{base_df}}.total_cost) / NULLIF({{base_df}}.total_cost, 0)) * 100"
)
```

#### Absolute Difference

```python
# Absolute change
create_drift_metric(
    "success_rate_drift",
    "{{current_df}}.success_rate - {{base_df}}.success_rate"
)
```

#### Ratio Change

```python
# Current to baseline ratio
create_drift_metric(
    "volume_ratio",
    "{{current_df}}.record_count / NULLIF({{base_df}}.record_count, 0)"
)
```

## Table-Level Aggregation

### Why `input_columns=[":table"]`?

All custom metrics use `input_columns=[":table"]` to enable **cross-column business KPIs**:

```python
# ✅ CORRECT: Table-level aggregation
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
    name="total_cost",
    input_columns=[":table"],  # Enables SUM(list_cost)
    definition="SUM(list_cost)",
    output_data_type=data_type
)
```

### Why Not Column-Level?

Column-level aggregation (`input_columns=["column_name"]`) only allows per-column statistics:
- Built-in statistics (mean, stddev, nulls)
- Cannot combine multiple columns
- Cannot use CASE expressions

### Cross-Column Examples

These require table-level aggregation:

```python
# Cost where tagged (two columns)
"SUM(CASE WHEN is_tagged = TRUE THEN list_cost ELSE 0 END)"

# Duration when successful (two columns)
"AVG(CASE WHEN status = 'SUCCESS' THEN duration_ms END)"

# Conditional count (column + value)
"COUNT(DISTINCT CASE WHEN sku_name LIKE '%JOBS%' THEN job_id END)"
```

## Output Data Types

### Supported Types

| Type | PySpark | Use For |
|------|---------|---------|
| `DOUBLE` | `T.DoubleType()` | Decimals, percentages, averages |
| `LONG` | `T.LongType()` | Counts, integers |

### Type Selection Guide

```python
# Counts → LONG
create_aggregate_metric("record_count", "COUNT(*)", "LONG")
create_aggregate_metric("distinct_users", "COUNT(DISTINCT user_id)", "LONG")
create_aggregate_metric("failure_count", "SUM(CASE WHEN ... THEN 1 ELSE 0 END)", "LONG")

# Sums of numeric → DOUBLE
create_aggregate_metric("total_cost", "SUM(list_cost)", "DOUBLE")
create_aggregate_metric("total_bytes", "SUM(read_bytes)", "DOUBLE")

# Averages → DOUBLE
create_aggregate_metric("avg_duration", "AVG(duration_ms)", "DOUBLE")

# Percentiles → DOUBLE
create_aggregate_metric("p95_latency", "PERCENTILE(latency_ms, 0.95)", "DOUBLE")

# Derived metrics → Always DOUBLE
create_derived_metric("success_rate", "...")  # Implicitly DOUBLE
```

## Complete Example

Here's a complete monitor definition showing all three metric types:

```python
def get_job_custom_metrics():
    """Define custom metrics for job reliability monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Core counts
        create_aggregate_metric("total_runs", "COUNT(*)", "LONG"),
        create_aggregate_metric(
            "success_count",
            "SUM(CASE WHEN is_success = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "failure_count",
            "SUM(CASE WHEN result_state IN ('FAILED', 'ERROR') THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Duration metrics
        create_aggregate_metric(
            "avg_duration_minutes",
            "AVG(run_duration_minutes)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p95_duration_minutes",
            "PERCENTILE(run_duration_minutes, 0.95)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "stddev_duration_minutes",
            "STDDEV(run_duration_minutes)",
            "DOUBLE"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "success_rate",
            "success_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "failure_rate",
            "failure_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "duration_cv",
            "stddev_duration_minutes / NULLIF(avg_duration_minutes, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "success_rate_drift",
            "{{current_df}}.success_rate - {{base_df}}.success_rate"
        ),
        create_drift_metric(
            "duration_drift_pct",
            "(({{current_df}}.avg_duration_minutes - {{base_df}}.avg_duration_minutes) / NULLIF({{base_df}}.avg_duration_minutes, 0)) * 100"
        ),
    ]
```

## Validation Checklist

Before deploying custom metrics:

### AGGREGATE Metrics
- [ ] Uses valid SQL aggregation function (SUM, COUNT, AVG, MAX, MIN, PERCENTILE, STDDEV)
- [ ] Output type matches expected values (LONG for counts, DOUBLE for decimals)
- [ ] Column names exist in source table
- [ ] CASE expressions have ELSE clause for conditional aggregations

### DERIVED Metrics
- [ ] References only AGGREGATE metrics by exact name
- [ ] Uses NULLIF for all division operations
- [ ] Produces meaningful business ratio

### DRIFT Metrics
- [ ] Uses `{{current_df}}` and `{{base_df}}` placeholders correctly
- [ ] References AGGREGATE or DERIVED metrics that exist
- [ ] Uses NULLIF for percentage change calculations

## Best Practices

### Do's ✅

- Use descriptive metric names (`success_rate` not `sr`)
- Group metrics by type in code (AGGREGATE, DERIVED, DRIFT)
- Add comments explaining business purpose
- Use NULLIF for all divisions
- Test metrics with sample data first

### Don'ts ❌

- Don't reference columns in DERIVED metrics (use AGGREGATE names)
- Don't forget `input_columns=[":table"]`
- Don't mix DOUBLE counts (use LONG for counts)
- Don't use raw column names in DRIFT metrics (use metric names)

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Metric returns NULL | Division by zero | Add `NULLIF(denominator, 0)` |
| Column not found | Wrong column name | Verify column exists in source table |
| Type mismatch | Wrong output_type | Use LONG for counts, DOUBLE for decimals |
| Drift always NULL | Wrong placeholder | Use `{{current_df}}.metric_name` format |
| DERIVED not computed | Reference wrong name | Use exact AGGREGATE metric name |

---

## Custom Metrics Reference by Domain

This section documents all **213+ custom metrics** implemented across 8 monitors, organized by the five operational domains.

### Domain Overview

| Domain | Focus Area | Primary Monitors | Total Metrics |
|--------|------------|------------------|---------------|
| **Cost** | FinOps, spend optimization | Cost Monitor | 35 |
| **Quality** | Data quality, governance | Quality Monitor, Governance Monitor | 24 |
| **Security** | Access control, audit | Security Monitor | 13 |
| **Reliability** | Job success, availability | Job Monitor, Inference Monitor | 65 |
| **Performance** | Duration, latency, efficiency | Query Monitor, Cluster Monitor | 28 |

---

### COST Domain

**Source:** `fact_usage` (billing/usage data)  
**Primary KPIs:** Total cost, tag coverage, cost per SKU

#### Core Cost Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_daily_cost` | DOUBLE | `SUM(list_cost)` | Primary FinOps metric for budgeting and forecasting |
| `total_daily_dbu` | DOUBLE | `SUM(usage_quantity)` | Usage volume independent of pricing |
| `avg_cost_per_dbu` | DOUBLE | `AVG(list_price)` | Unit economics indicator for pricing efficiency |
| `record_count` | LONG | `COUNT(*)` | Data completeness indicator |

#### Data Completeness Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `distinct_workspaces` | LONG | `COUNT(DISTINCT workspace_id)` | Platform utilization breadth |
| `distinct_skus` | LONG | `COUNT(DISTINCT sku_name)` | Product mix indicator |
| `null_sku_count` | LONG | `COUNT where sku_name IS NULL` | Data quality issue requiring investigation |
| `null_price_count` | LONG | `COUNT where list_price IS NULL` | Billing data quality indicator |

#### Tag Hygiene Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `tagged_record_count` | LONG | `COUNT where is_tagged = TRUE` | FinOps maturity indicator |
| `untagged_record_count` | LONG | `COUNT where is_tagged = FALSE` | Unattributable spend requiring attention |
| `tagged_cost_total` | DOUBLE | `SUM(list_cost) where is_tagged = TRUE` | Attributable spend amount |
| `untagged_cost_total` | DOUBLE | `SUM(list_cost) where is_tagged = FALSE` | Unattributable spend requiring investigation |

#### SKU Breakdown Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `jobs_compute_cost` | DOUBLE | `SUM(list_cost) for JOBS SKUs` | Workflow automation spend |
| `sql_compute_cost` | DOUBLE | `SUM(list_cost) for SQL SKUs` | Analytics workload spend |
| `all_purpose_cost` | DOUBLE | `SUM(list_cost) for ALL_PURPOSE SKUs` | Interactive compute spend (often higher cost) |
| `serverless_cost` | DOUBLE | `SUM(list_cost) where is_serverless = TRUE` | Modern compute pattern adoption |
| `dlt_cost` | DOUBLE | `SUM(list_cost) for DLT SKUs` | Data pipeline infrastructure spend |
| `model_serving_cost` | DOUBLE | `SUM(list_cost) for MODEL_SERVING SKUs` | ML production serving spend |

#### Workflow Advisor Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `jobs_on_all_purpose_cost` | DOUBLE | Jobs cost on ALL_PURPOSE clusters | Inefficient pattern causing ~40% overspend |
| `jobs_on_all_purpose_count` | LONG | Job count on ALL_PURPOSE clusters | Optimization candidates for JOB cluster migration |
| `potential_job_cluster_savings` | DOUBLE | Estimated 40% savings | Actionable optimization opportunity |

#### Derived Cost Ratios (DERIVED)

| Metric | Definition | Business Purpose | Target |
|--------|------------|------------------|--------|
| `null_sku_rate` | `null_sku_count / record_count * 100` | Data quality score | < 1% |
| `null_price_rate` | `null_price_count / record_count * 100` | Billing completeness score | 0% |
| `tag_coverage_pct` | `tagged_cost / total_cost * 100` | FinOps maturity KPI | > 90% |
| `untagged_usage_pct` | `untagged_cost / total_cost * 100` | Cost attribution gap | < 10% |
| `serverless_ratio` | `serverless_cost / total_cost * 100` | Modern architecture adoption | Growing |
| `jobs_cost_share` | `jobs_cost / total_cost * 100` | Workflow cost proportion | - |
| `sql_cost_share` | `sql_cost / total_cost * 100` | Analytics cost proportion | - |
| `all_purpose_cost_ratio` | `all_purpose_cost / total_cost * 100` | Interactive compute overhead | Decreasing |
| `jobs_on_all_purpose_ratio` | `jobs_on_AP_cost / total_jobs_cost * 100` | Optimization priority score | < 5% |
| `dlt_cost_share` | `dlt_cost / total_cost * 100` | Data engineering proportion | - |
| `model_serving_cost_share` | `model_serving_cost / total_cost * 100` | ML inference proportion | - |

#### Cost Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose | Alert Threshold |
|--------|------------|------------------|-----------------|
| `cost_drift_pct` | `((current - baseline) / baseline) * 100` | Budget variance indicator | > 10% |
| `dbu_drift_pct` | `((current - baseline) / baseline) * 100` | Usage trend (price-independent) | > 15% |
| `tag_coverage_drift` | `current_coverage - baseline_coverage` | FinOps maturity trend | < -5% |

---

### QUALITY Domain

**Sources:** `fact_table_quality`, `fact_governance_metrics`  
**Primary KPIs:** Quality score, freshness, governance coverage

#### Data Quality Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_tables` | LONG | `COUNT(DISTINCT table_name)` | Data estate coverage |
| `tables_with_issues` | LONG | `COUNT where quality_score < threshold` | Data quality problem scope |
| `avg_quality_score` | DOUBLE | `AVG(quality_score)` | Overall data quality KPI (0-100) |
| `null_violation_count` | LONG | `COUNT of NULL violations` | Data completeness issues |
| `schema_drift_count` | LONG | `COUNT of schema changes` | Schema stability indicator |
| `freshness_violations` | LONG | `COUNT where data_age > SLA` | Data currency issues |
| `quality_score_below_threshold` | LONG | `COUNT where quality_score < 80` | Quality attention required |

#### Derived Quality Ratios (DERIVED)

| Metric | Definition | Business Purpose | Target |
|--------|------------|------------------|--------|
| `quality_issue_rate` | `tables_with_issues / total_tables * 100` | Quality coverage indicator | < 5% |
| `avg_freshness_hours` | `AVG(hours_since_update)` | Data currency indicator | < 24h |

#### Quality Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `quality_drift` | `current - baseline avg_quality_score` | Quality trend indicator |

#### Governance Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_assets` | LONG | `COUNT(DISTINCT asset_id)` | Governance coverage scope |
| `documented_assets` | LONG | `COUNT where has_documentation = TRUE` | Documentation coverage |
| `tagged_assets` | LONG | `COUNT where is_tagged = TRUE` | Tagging coverage |
| `access_controlled_assets` | LONG | `COUNT where has_acl = TRUE` | Security coverage |
| `lineage_tracked_assets` | LONG | `COUNT where has_lineage = TRUE` | Data provenance coverage |

#### Derived Governance Ratios (DERIVED)

| Metric | Definition | Business Purpose | Target |
|--------|------------|------------------|--------|
| `documentation_rate` | `documented / total * 100` | Governance maturity indicator | > 80% |
| `tagging_rate` | `tagged / total * 100` | Metadata quality indicator | > 90% |
| `access_control_rate` | `controlled / total * 100` | Security governance indicator | 100% |
| `lineage_coverage_rate` | `tracked / total * 100` | Data provenance maturity | > 70% |
| `governance_score` | Weighted average of coverage rates | Overall governance maturity KPI | > 80 |

#### Governance Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `governance_drift` | `current - baseline governance_score` | Governance improvement trend |

---

### SECURITY Domain

**Source:** `fact_audit_logs`  
**Primary KPIs:** Failed auth rate, admin action rate, event volume

#### Security Event Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_events` | LONG | `COUNT(*)` | Security activity volume |
| `distinct_users` | LONG | `COUNT(DISTINCT user_id)` | User base active size |
| `failed_auth_count` | LONG | `COUNT of auth failures` | Security incident indicator |
| `sensitive_actions` | LONG | `COUNT of privileged operations` | Security audit priority events |
| `data_access_events` | LONG | `COUNT of SELECT/READ operations` | Data consumption activity |
| `admin_actions` | LONG | `COUNT of ADMIN operations` | Privileged activity for audit |

#### Derived Security Ratios (DERIVED)

| Metric | Definition | Business Purpose | Alert Threshold |
|--------|------------|------------------|-----------------|
| `failed_auth_rate` | `failed_auth / total_auth * 100` | Security risk indicator | > 1% |
| `admin_action_rate` | `admin_actions / total_events * 100` | Privileged activity proportion | Unusual spike |
| `events_per_user` | `total_events / distinct_users` | User activity level | - |

#### Security Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `auth_failure_drift` | `current - baseline failed_auth` | Security posture trend |

---

### RELIABILITY Domain

**Sources:** `fact_job_run_timeline`, `fact_model_serving`  
**Primary KPIs:** Success rate, failure rate, availability

#### Job Reliability Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_runs` | LONG | `COUNT(*)` | Workload volume indicator |
| `success_count` | LONG | `COUNT where is_success = TRUE` | Reliability numerator |
| `failure_count` | LONG | `COUNT where result_state IN (FAILED, ERROR)` | Reliability issues |
| `timeout_count` | LONG | `COUNT where result_state = TIMED_OUT` | Resource constraint issues |
| `cancelled_count` | LONG | `COUNT where result_state = CANCELED` | Manual intervention issues |
| `skipped_count` | LONG | `COUNT where result_state = SKIPPED` | Dependency issues |
| `upstream_failed_count` | LONG | `COUNT where result_state = UPSTREAM_FAILED` | Dependency chain failures |
| `distinct_jobs` | LONG | `COUNT(DISTINCT job_id)` | Workload diversity |
| `distinct_runs` | LONG | `COUNT(DISTINCT run_id)` | Execution count including retries |

#### Trigger Breakdown Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `scheduled_runs` | LONG | `COUNT where trigger_type = SCHEDULE` | Automated workload proportion |
| `manual_runs` | LONG | `COUNT where trigger_type = MANUAL` | Ad-hoc workload proportion |
| `retry_runs` | LONG | `COUNT where trigger_type = RETRY` | Recovery activity indicator |

#### Termination Breakdown Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `user_cancelled_count` | LONG | `COUNT where termination_code = USER_CANCELED` | Manual intervention frequency |
| `internal_error_count` | LONG | `COUNT where termination_code = INTERNAL_ERROR` | Platform stability issues |
| `driver_error_count` | LONG | `COUNT where termination_code = DRIVER_ERROR` | Code or configuration issues |

#### Derived Job Reliability Ratios (DERIVED)

| Metric | Definition | Business Purpose | Target |
|--------|------------|------------------|--------|
| `success_rate` | `success_count / total_runs * 100` | Primary reliability KPI | > 95% |
| `failure_rate` | `failure_count / total_runs * 100` | Reliability issue indicator | < 3% |
| `timeout_rate` | `timeout_count / total_runs * 100` | Resource constraint indicator | < 1% |
| `cancellation_rate` | `cancelled_count / total_runs * 100` | Intervention frequency | < 2% |
| `repair_rate` | `retry_runs / distinct_runs * 100` | Recovery activity level | < 5% |
| `scheduled_ratio` | `scheduled_runs / total_runs * 100` | Automation maturity | > 80% |
| `avg_runs_per_job` | `total_runs / distinct_jobs` | Execution frequency | - |
| `skipped_rate` | `skipped_count / total_runs * 100` | Dependency issue frequency | < 1% |
| `upstream_failed_rate` | `upstream_failed / total_runs * 100` | Dependency chain health | < 2% |

#### Job Reliability Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `success_rate_drift` | `current - baseline success_rate` | Reliability trend (negative = degrading) |
| `failure_count_drift` | `current - baseline failure_count` | Problem emergence indicator |
| `run_count_drift_pct` | `((current - baseline) / baseline) * 100` | Workload volume trend |

#### Model Serving Reliability Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_requests` | LONG | `COUNT(*)` | ML serving volume |
| `successful_requests` | LONG | `COUNT where status = SUCCESS` | ML reliability numerator |
| `failed_requests` | LONG | `COUNT where status = FAILED` | ML reliability issues |
| `total_tokens` | LONG | `SUM(token_count)` | LLM usage volume (for LLMs) |

#### Derived ML Reliability Ratios (DERIVED)

| Metric | Definition | Business Purpose | Target |
|--------|------------|------------------|--------|
| `request_success_rate` | `successful / total * 100` | ML reliability KPI | > 99% |
| `error_rate` | `failed / total * 100` | ML reliability issue indicator | < 1% |
| `avg_tokens_per_request` | `total_tokens / total_requests` | Request complexity indicator | - |

#### ML Reliability Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `error_rate_drift` | `current - baseline error_rate` | ML reliability trend |

---

### PERFORMANCE Domain

**Sources:** `fact_job_run_timeline`, `fact_query_history`, `fact_cluster_timeline`, `fact_model_serving`  
**Primary KPIs:** Duration, latency percentiles, utilization

#### Job Performance Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `avg_duration_minutes` | DOUBLE | `AVG(run_duration_minutes)` | Baseline performance indicator |
| `total_duration_minutes` | DOUBLE | `SUM(run_duration_minutes)` | Compute time consumption |
| `max_duration_minutes` | DOUBLE | `MAX(run_duration_minutes)` | Worst-case performance |
| `min_duration_minutes` | DOUBLE | `MIN(run_duration_minutes)` | Best-case performance |
| `p50_duration_minutes` | DOUBLE | `PERCENTILE(0.50)` | Typical performance indicator |
| `p90_duration_minutes` | DOUBLE | `PERCENTILE(0.90)` | Outlier threshold for SLA |
| `p95_duration_minutes` | DOUBLE | `PERCENTILE(0.95)` | Performance SLA target |
| `p99_duration_minutes` | DOUBLE | `PERCENTILE(0.99)` | Critical SLA threshold |
| `stddev_duration_minutes` | DOUBLE | `STDDEV(run_duration_minutes)` | Performance consistency |
| `long_running_count` | LONG | `COUNT where duration > 60 min` | Optimization candidates |
| `very_long_running_count` | LONG | `COUNT where duration > 240 min` | Resource-intensive jobs |

#### Derived Job Performance Ratios (DERIVED)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `duration_cv` | `stddev / avg duration` | Performance consistency score (lower is better) |
| `long_running_rate` | `long_running_count / total_runs * 100` | Optimization opportunity scope |
| `very_long_running_rate` | `very_long_running_count / total_runs * 100` | Resource-intensive workload proportion |
| `duration_skew_ratio` | `p90_duration / p50_duration` | Performance distribution (1 = perfect, >2 = skewed) |
| `tail_ratio` | `p99_duration / p95_duration` | Tail latency indicator |

#### Job Performance Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `duration_drift_pct` | `((current - baseline) / baseline) * 100` | Performance regression indicator |
| `p99_duration_drift_pct` | `((current - baseline) / baseline) * 100` | SLA compliance trend |
| `p90_duration_drift_pct` | `((current - baseline) / baseline) * 100` | Outlier trend indicator |
| `duration_cv_drift` | `current - baseline CV` | Consistency trend |
| `long_running_drift` | `current - baseline count` | Performance degradation indicator |

#### Query Performance Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_queries` | LONG | `COUNT(*)` | Query workload volume |
| `avg_query_duration_seconds` | DOUBLE | `AVG(duration_seconds)` | Query performance baseline |
| `p50_duration_seconds` | DOUBLE | `PERCENTILE(0.50)` | Typical query performance |
| `p95_duration_seconds` | DOUBLE | `PERCENTILE(0.95)` | SLA threshold for slow queries |
| `p99_duration_seconds` | DOUBLE | `PERCENTILE(0.99)` | Worst-case query performance |
| `failed_queries` | LONG | `COUNT where status = FAILED` | Query reliability issues |
| `cancelled_queries` | LONG | `COUNT where status = CANCELED` | Timeout issues |
| `successful_queries` | LONG | `COUNT where status = FINISHED` | Query reliability numerator |
| `total_rows_read` | LONG | `SUM(rows_read)` | Data access volume |
| `total_bytes_read` | LONG | `SUM(bytes_read)` | IO efficiency indicator |

#### Derived Query Performance Ratios (DERIVED)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `query_success_rate` | `successful / total * 100` | Query reliability KPI |
| `query_failure_rate` | `failed / total * 100` | Query reliability issues |
| `avg_rows_per_query` | `total_rows / total_queries` | Query scope indicator |

#### Query Performance Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `query_duration_drift_pct` | `((current - baseline) / baseline) * 100` | Performance trend indicator |

#### Cluster Utilization Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `total_clusters` | LONG | `COUNT(DISTINCT cluster_id)` | Compute infrastructure breadth |
| `total_cluster_hours` | DOUBLE | `SUM(cluster_hours)` | Compute resource consumption |
| `avg_cluster_uptime_hours` | DOUBLE | `AVG(uptime_hours)` | Cluster utilization duration |
| `idle_cluster_hours` | DOUBLE | `SUM(idle_hours)` | Wasted compute time (optimization target) |
| `active_cluster_hours` | DOUBLE | `SUM(active_hours)` | Productive compute time |
| `idle_cost_estimate` | DOUBLE | `idle_hours * avg_cost_per_hour` | FinOps optimization opportunity |
| `autoscale_events` | LONG | `COUNT of scale up/down` | Elastic scaling activity |
| `cluster_start_count` | LONG | `COUNT of start events` | Cluster lifecycle activity |
| `cluster_terminate_count` | LONG | `COUNT of terminate events` | Cluster lifecycle completions |

#### Derived Cluster Utilization Ratios (DERIVED)

| Metric | Definition | Business Purpose | Target |
|--------|------------|------------------|--------|
| `cluster_utilization_pct` | `active_hours / total_hours * 100` | Compute efficiency KPI | > 60% |

#### Model Serving Performance Metrics (AGGREGATE)

| Metric | Type | Definition | Business Purpose |
|--------|------|------------|------------------|
| `avg_latency_ms` | DOUBLE | `AVG(latency_ms)` | ML performance baseline |
| `p50_latency_ms` | DOUBLE | `PERCENTILE(0.50)` | Typical ML performance |
| `p95_latency_ms` | DOUBLE | `PERCENTILE(0.95)` | ML SLA threshold |
| `p99_latency_ms` | DOUBLE | `PERCENTILE(0.99)` | Worst-case ML performance |
| `throughput_per_second` | DOUBLE | `total_requests / time_window_seconds` | ML serving capacity utilization |

#### ML Performance Drift Metrics (DRIFT)

| Metric | Definition | Business Purpose |
|--------|------------|------------------|
| `latency_drift_pct` | `((current - baseline) / baseline) * 100` | ML performance trend |

---

### Metric Count Summary by Monitor

| Monitor | Source Table | AGGREGATE | DERIVED | DRIFT | Total |
|---------|--------------|-----------|---------|-------|-------|
| Cost Monitor | `fact_usage` | 18 | 12 | 3 | **35** |
| Job Monitor | `fact_job_run_timeline` | 25 | 17 | 8 | **50** |
| Query Monitor | `fact_query_history` | 10 | 3 | 1 | **14** |
| Cluster Monitor | `fact_cluster_timeline` | 9 | 1 | 0 | **10** |
| Security Monitor | `fact_audit_logs` | 6 | 3 | 1 | **13** |
| Quality Monitor | `fact_table_quality` | 7 | 2 | 1 | **10** |
| Governance Monitor | `fact_governance_metrics` | 5 | 5 | 1 | **11** |
| Inference Monitor | `fact_model_serving` | 8 | 4 | 2 | **15** |
| **Total** | | **88** | **47** | **17** | **~155+** |

> Note: Some metrics may be shared across monitors or have variations for different dimensions.

---

## References

- [Lakehouse Monitoring Custom Metrics](https://docs.databricks.com/lakehouse-monitoring/custom-metrics.html)
- [MonitorMetric API Reference](https://docs.databricks.com/api/workspace/qualitymonitors)
- [Cursor Rule: Lakehouse Monitoring](../../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

---

**Version:** 1.1  
**Last Updated:** January 2026

