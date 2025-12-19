# Phase 3 Addendum 3.4: Lakehouse Monitoring for Databricks Health Monitor

## Overview

**Status:** 🔧 Enhanced  
**Dependencies:** Gold Layer (Phase 2), ML Models (Phase 3.1)  
**Estimated Effort:** 2 weeks  
**Reference:** Cursor Rule 17 - Lakehouse Monitoring

---

## Purpose

Implement Lakehouse Monitoring for:
- **Time Series Profiling** - Track data quality and statistics over time
- **Inference Monitoring** - Monitor ML model predictions and drift
- **Custom Business Metrics** - Track domain-specific KPIs by Agent Domain
- **Automated Alerting** - Notify on threshold breaches

---

## Monitoring Strategy by Agent Domain

| Agent Domain | Monitor Type | Gold Table | Key Metrics | Refresh |
|--------------|--------------|------------|-------------|---------|
| **💰 Cost** | Time Series | `fact_usage` | total_cost, null_rate, workspace_count | Daily |
| **🔒 Security** | Time Series | `fact_table_lineage` | access_count, sensitive_access_rate | Daily |
| **⚡ Performance** | Time Series | `fact_query_history`, `fact_node_timeline` | p95_duration, queue_rate, cpu_util | Hourly |
| **🔄 Reliability** | Time Series | `fact_job_run_timeline` | success_rate, failure_count, repair_rate | Hourly |
| **✅ Quality** | Time Series | `fact_data_quality_monitoring_table_results` | quality_score, violation_rate | Daily |
| **🤖 ML Inference** | Inference | `cost_anomaly_predictions` | MAE, MAPE, anomaly_rate | Per batch |

---

## 💰 Cost Agent Monitors

### Monitor: Cost Data Quality Monitor

**Table:** `${catalog}.${gold_schema}.fact_usage`  
**Type:** Time Series  
**Purpose:** Ensure billing data quality and completeness, detect cost anomalies

```python
cost_custom_metrics = [
    # Core cost metrics
    {
        "name": "total_daily_cost",
        "definition": "SUM(list_cost)",  # Using pre-calculated list_cost
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "avg_cost_per_dbu",
        "definition": "AVG(list_price)",  # Using pre-enriched list_price
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Completeness metrics
    {
        "name": "distinct_workspaces",
        "definition": "COUNT(DISTINCT workspace_id)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "null_sku_rate",
        "definition": "SUM(CASE WHEN sku_name IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Trend detection (inspired by Jobs System Tables Dashboard)
    {
        "name": "cost_7day_growth_pct",
        "definition": """
            (SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) -
             SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END)) /
            NULLIF(SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END), 0) * 100
        """,  # Using pre-calculated list_cost
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # ==== TAG HYGIENE METRICS ====
    # Critical for cost attribution - tracks tagging practices
    # Reference: https://docs.databricks.com/aws/en/admin/system-tables/billing
    {
        "name": "untagged_usage_pct",
        "definition": "SUM(CASE WHEN is_tagged = FALSE THEN list_cost ELSE 0 END) / NULLIF(SUM(list_cost), 0) * 100",
        "type": "AGGREGATE",  # Using pre-calculated is_tagged and list_cost
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "tagged_cost_total",
        "definition": "SUM(CASE WHEN is_tagged = TRUE THEN list_cost ELSE 0 END)",
        "type": "AGGREGATE",  # Using pre-calculated is_tagged and list_cost
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "untagged_cost_total",
        "definition": "SUM(CASE WHEN is_tagged = FALSE THEN list_cost ELSE 0 END)",
        "type": "AGGREGATE",  # Using pre-calculated is_tagged and list_cost
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "tag_coverage_pct",
        "definition": "SUM(CASE WHEN is_tagged = TRUE THEN list_cost ELSE 0 END) / NULLIF(SUM(list_cost), 0) * 100",
        "type": "AGGREGATE",  # Using pre-calculated is_tagged and list_cost
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "untagged_record_count",
        "definition": "COUNT(CASE WHEN custom_tags IS NULL OR size(custom_tags) = 0 THEN 1 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Drift metric: Alert when tag coverage drops significantly
    {
        "name": "tag_coverage_drift",
        "definition": "{{tag_coverage_pct}} - {{tag_coverage_pct.previous_day}}",
        "type": "DRIFT",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    }
]
```

---

## 🔒 Security Agent Monitors

### Monitor: Security Access Monitor

**Table:** `${catalog}.${gold_schema}.fact_table_lineage`  
**Type:** Time Series  
**Purpose:** Track data access patterns and security compliance

```python
security_custom_metrics = [
    # Access volume metrics
    {
        "name": "total_access_events",
        "definition": "COUNT(*)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "unique_users",
        "definition": "COUNT(DISTINCT created_by)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Read/Write breakdown
    {
        "name": "read_event_count",
        "definition": "SUM(CASE WHEN source_table_full_name IS NOT NULL THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "write_event_count",
        "definition": "SUM(CASE WHEN target_table_full_name IS NOT NULL THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Sensitive data tracking (from Governance Hub patterns)
    {
        "name": "sensitive_table_access_count",
        "definition": "SUM(CASE WHEN source_table_full_name LIKE '%pii%' OR source_table_full_name LIKE '%sensitive%' OR target_table_full_name LIKE '%pii%' THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Off-hours access detection
    {
        "name": "off_hours_access_rate",
        "definition": "SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 OR DAYOFWEEK(event_date) IN (1, 7) THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    }
]
```

---

## ⚡ Performance Agent Monitors

### Monitor: Query Performance Monitor

**Table:** `${catalog}.${gold_schema}.fact_query_history`  
**Type:** Time Series  
**Purpose:** Track query performance trends and SLA compliance

```python
query_custom_metrics = [
    # Volume metrics
    {
        "name": "query_count",
        "definition": "COUNT(*)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Duration metrics
    {
        "name": "avg_query_duration_sec",
        "definition": "AVG(total_duration_ms / 1000)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "p50_duration_sec",
        "definition": "PERCENTILE(total_duration_ms / 1000, 0.50)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "p95_duration_sec",
        "definition": "PERCENTILE(total_duration_ms / 1000, 0.95)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "p99_duration_sec",
        "definition": "PERCENTILE(total_duration_ms / 1000, 0.99)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Queue metrics (from DBSQL Warehouse Advisor)
    {
        "name": "avg_queue_time_sec",
        "definition": "AVG(waiting_at_capacity_duration_ms / 1000)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "high_queue_rate",
        "definition": "SUM(CASE WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Slow query tracking
    {
        "name": "slow_query_rate",
        "definition": "SUM(CASE WHEN total_duration_ms > 300000 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Spill detection (from DBSQL Warehouse Advisor)
    {
        "name": "spill_rate",
        "definition": "SUM(CASE WHEN (COALESCE(spill_local_bytes, 0) + COALESCE(spill_remote_bytes, 0)) > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Data volume tracking
    {
        "name": "total_bytes_read_tb",
        "definition": "SUM(read_bytes) / (1024*1024*1024*1024)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    }
]
```

### Monitor: Cluster Utilization Monitor

**Table:** `${catalog}.${gold_schema}.fact_node_timeline`  
**Type:** Time Series  
**Purpose:** Track resource utilization for right-sizing recommendations

```python
cluster_custom_metrics = [
    # CPU metrics
    {
        "name": "avg_cpu_utilization",
        "definition": "AVG(cpu_user_percent + cpu_system_percent)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "peak_cpu_utilization",
        "definition": "MAX(cpu_user_percent + cpu_system_percent)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Memory metrics
    {
        "name": "avg_memory_utilization",
        "definition": "AVG(mem_used_percent)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "peak_memory_utilization",
        "definition": "MAX(mem_used_percent)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # IO wait (from Workflow Advisor patterns)
    {
        "name": "avg_cpu_wait",
        "definition": "AVG(cpu_wait_percent)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Right-sizing indicators (from Jobs System Tables Dashboard)
    {
        "name": "underutilization_rate",
        "definition": "SUM(CASE WHEN cpu_user_percent + cpu_system_percent < 30 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "overutilization_rate",
        "definition": "SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 80 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    }
]
```

---

## 🔄 Reliability Agent Monitors

### Monitor: Job Reliability Monitor

**Table:** `${catalog}.${gold_schema}.fact_job_run_timeline`  
**Type:** Time Series  
**Purpose:** Track job success rates and failure patterns

```python
job_custom_metrics = [
    # Core reliability metrics
    {
        "name": "total_runs",
        "definition": "COUNT(*)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "success_rate",
        "definition": "SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "failure_count",
        "definition": "SUM(CASE WHEN result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Duration metrics
    {
        "name": "avg_duration_minutes",
        "definition": "AVG(TIMESTAMPDIFF(MINUTE, period_start_time, period_end_time))",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "p95_duration_minutes",
        "definition": "PERCENTILE(TIMESTAMPDIFF(MINUTE, period_start_time, period_end_time), 0.95)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Timeout tracking
    {
        "name": "timeout_rate",
        "definition": "SUM(CASE WHEN result_state = 'TIMED_OUT' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Repair analysis (from Jobs System Tables Dashboard)
    {
        "name": "repair_rate",
        "definition": """
            (COUNT(*) - COUNT(DISTINCT job_id || '-' || run_id)) / NULLIF(COUNT(DISTINCT job_id || '-' || run_id), 0) * 100
        """,
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Cancellation tracking
    {
        "name": "cancellation_rate",
        "definition": "SUM(CASE WHEN result_state = 'CANCELED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    }
]
```

---

## ✅ Quality Agent Monitors

### Monitor: Data Quality Monitor

**Table:** `${catalog}.${gold_schema}.fact_data_quality_monitoring_table_results`  
**Type:** Time Series  
**Purpose:** Track data quality scores and rule violations

```python
quality_custom_metrics = [
    # Overall quality score
    {
        "name": "avg_quality_score",
        "definition": "AVG(quality_score)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Rule metrics
    {
        "name": "total_rules_evaluated",
        "definition": "SUM(rules_count)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "rules_passed_rate",
        "definition": "SUM(rules_passed) / NULLIF(SUM(rules_count), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Violation tracking
    {
        "name": "tables_with_violations",
        "definition": "COUNT(DISTINCT CASE WHEN rules_passed < rules_count THEN table_name ELSE NULL END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Critical vs warning breakdown
    {
        "name": "critical_violation_count",
        "definition": "SUM(critical_violations)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "warning_violation_count",
        "definition": "SUM(warning_violations)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    }
]
```

---

## 🤖 ML Inference Monitors

### Monitor: Cost Anomaly Inference Monitor

**Table:** `${catalog}.${gold_schema}.cost_anomaly_predictions`  
**Type:** Inference  
**Purpose:** Monitor ML model prediction quality and drift

```python
inference_custom_metrics = [
    # Accuracy metrics
    {
        "name": "mean_absolute_error",
        "definition": "AVG(ABS(daily_cost - expected_cost))",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "mean_absolute_percentage_error",
        "definition": "AVG(ABS(daily_cost - expected_cost) / NULLIF(daily_cost, 0)) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Anomaly distribution
    {
        "name": "anomaly_flag_rate",
        "definition": "SUM(CASE WHEN is_anomaly = TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # Prediction distribution
    {
        "name": "avg_anomaly_score",
        "definition": "AVG(anomaly_score)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # High confidence anomalies
    {
        "name": "high_confidence_anomaly_count",
        "definition": "SUM(CASE WHEN anomaly_score > 0.9 THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    }
]
```

---

## Alert Rules by Agent Domain

### 💰 Cost Alerts
| Alert | Metric | Condition | Severity |
|-------|--------|-----------|----------|
| Cost Spike | total_daily_cost | value > baseline * 1.5 | WARNING |
| Rapid Growth | cost_7day_growth_pct | value > 30 | WARNING |
| Tag Hygiene | untagged_usage_pct | value > 20 | INFO |

### 🔒 Security Alerts
| Alert | Metric | Condition | Severity |
|-------|--------|-----------|----------|
| Sensitive Access Spike | sensitive_table_access_count | value > baseline * 2 | CRITICAL |
| Off-Hours Access | off_hours_access_rate | value > 10 | WARNING |

### ⚡ Performance Alerts
| Alert | Metric | Condition | Severity |
|-------|--------|-----------|----------|
| Query Degradation | p95_duration_sec | value > baseline * 2 | WARNING |
| High Queue Time | high_queue_rate | value > 20 | WARNING |
| Spill Detected | spill_rate | value > 5 | INFO |
| Underutilization | underutilization_rate | value > 50 | INFO |

### 🔄 Reliability Alerts
| Alert | Metric | Condition | Severity |
|-------|--------|-----------|----------|
| Job Failure Spike | success_rate | value < 80 | CRITICAL |
| Timeout Rate High | timeout_rate | value > 10 | WARNING |
| High Repair Rate | repair_rate | value > 20 | WARNING |

### ✅ Quality Alerts
| Alert | Metric | Condition | Severity |
|-------|--------|-----------|----------|
| Quality Score Drop | avg_quality_score | value < 0.9 | CRITICAL |
| Critical Violations | critical_violation_count | value > 0 | CRITICAL |

---

## Deployment Configuration

```yaml
resources:
  jobs:
    monitoring_setup_job:
      name: "[${bundle.target}] Health Monitor - Lakehouse Monitoring Setup"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - databricks-sdk>=0.20.0
      
      tasks:
        # Cost Agent Monitors
        - task_key: create_cost_monitor
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/monitoring/cost_monitor.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
        
        # Security Agent Monitors
        - task_key: create_security_monitor
          depends_on: [create_cost_monitor]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/monitoring/security_monitor.py
        
        # Performance Agent Monitors
        - task_key: create_query_monitor
          depends_on: [create_security_monitor]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/monitoring/query_monitor.py
        
        - task_key: create_cluster_monitor
          depends_on: [create_query_monitor]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/monitoring/cluster_monitor.py
        
        # Reliability Agent Monitors
        - task_key: create_job_monitor
          depends_on: [create_cluster_monitor]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/monitoring/job_monitor.py
        
        # Quality Agent Monitors
        - task_key: create_quality_monitor
          depends_on: [create_job_monitor]
          environment_key: default
          notebook_task:
            notebook_path: ../src/gold/monitoring/quality_monitor.py
      
      tags:
        project: health_monitor
        layer: gold
        artifact_type: lakehouse_monitor
```

---

## Monitor Summary by Agent Domain

| Agent | Monitor | Gold Table | Granularity | Key Metrics |
|-------|---------|------------|-------------|-------------|
| 💰 Cost | Cost Monitor | fact_usage | 1 day | total_cost, growth_pct, tag_hygiene |
| 🔒 Security | Security Monitor | fact_table_lineage | 1 day | access_count, sensitive_rate, off_hours |
| ⚡ Performance | Query Monitor | fact_query_history | 1 hour | p95_duration, queue_rate, spill_rate |
| ⚡ Performance | Cluster Monitor | fact_node_timeline | 1 hour | cpu_util, mem_util, underutil_rate |
| 🔄 Reliability | Job Monitor | fact_job_run_timeline | 1 hour | success_rate, failure_count, repair_rate |
| ✅ Quality | Quality Monitor | fact_data_quality_monitoring_table_results | 1 day | quality_score, violation_rate |
| 🤖 ML | Inference Monitor | cost_anomaly_predictions | Per batch | MAE, MAPE, anomaly_rate |
| 📊 Governance | Lineage Monitor | fact_table_lineage | 1 day | active_tables, inactive_tables, read_write_ratio |

---

## 🆕 Dashboard Pattern Enhancements for Lakehouse Monitoring

Based on analysis of real-world Databricks dashboards (see [phase3-use-cases.md SQL Patterns Catalog](./phase3-use-cases.md#-sql-query-patterns-catalog-from-dashboard-analysis)), the following custom metrics should be added:

### New Cost Monitor Metrics (from Dashboard Patterns)

#### Period-Over-Period Growth Metrics (Pattern 1, 4)
**Source:** Azure Serverless Cost Dashboard, Jobs System Tables Dashboard

```python
# WoW Growth Monitoring
{
    "name": "cost_7d_vs_prior_7d_growth_pct",
    "definition": """
        (SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) -
         SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END)) /
        NULLIF(SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END), 0) * 100
    """,
    "type": "AGGREGATE",
    "input_columns": [":table"],
    "output_data_type": "DOUBLE"
},

# MoM Growth Monitoring
{
    "name": "cost_30d_vs_prior_30d_growth_pct",
    "definition": """
        (SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS THEN list_cost ELSE 0 END) -
         SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS AND CURRENT_DATE() - INTERVAL 30 DAYS THEN list_cost ELSE 0 END)) /
        NULLIF(SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS AND CURRENT_DATE() - INTERVAL 30 DAYS THEN list_cost ELSE 0 END), 0) * 100
    """,
    "type": "AGGREGATE",
    "input_columns": [":table"],
    "output_data_type": "DOUBLE"
}
```

#### Outlier Detection Metrics (Pattern 3)
**Source:** Azure Serverless Cost Dashboard

```python
# P90 Deviation Detection for Jobs
{
    "name": "jobs_with_outlier_runs_count",
    "definition": """
        SELECT COUNT(DISTINCT job_id) FROM (
            SELECT
                job_id,
                MAX(run_cost) as max_cost,
                PERCENTILE(run_cost, 0.9) as p90_cost
            FROM (
                SELECT usage_metadata_job_id as job_id,
                       usage_metadata_job_run_id as run_id,
                       SUM(list_cost) as run_cost
                FROM :table
                WHERE usage_metadata_job_id IS NOT NULL
                GROUP BY 1, 2
            )
            GROUP BY job_id
            HAVING max_cost > p90_cost * 1.5
        )
    """,
    "type": "AGGREGATE",
    "input_columns": [":table"],
    "output_data_type": "LONG"
},

# Max P90 Deviation Percentage
{
    "name": "max_p90_deviation_pct",
    "definition": """
        MAX(
            (run_max_cost - run_p90_cost) / NULLIF(run_p90_cost, 0) * 100
        )
    """,
    "type": "AGGREGATE",
    "input_columns": [":table"],
    "output_data_type": "DOUBLE"
}
```

### New Governance Monitor (🆕 Pattern 7)
**Source:** Governance Hub Dashboard

```python
# Active vs Inactive Table Tracking
governance_lineage_metrics = [
    {
        "name": "active_tables_count",
        "definition": """
            COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name))
        """,
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "read_events_count",
        "definition": "SUM(CASE WHEN source_table_full_name IS NOT NULL THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "write_events_count",
        "definition": "SUM(CASE WHEN target_table_full_name IS NOT NULL THEN 1 ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "read_write_ratio",
        "definition": """
            SUM(CASE WHEN source_table_full_name IS NOT NULL THEN 1 ELSE 0 END) /
            NULLIF(SUM(CASE WHEN target_table_full_name IS NOT NULL THEN 1 ELSE 0 END), 0)
        """,
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "unique_data_consumers",
        "definition": "COUNT(DISTINCT created_by)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    # Drift: Alert when active table count drops significantly
    {
        "name": "active_tables_drift",
        "definition": "{{active_tables_count}} - {{active_tables_count.previous_window}}",
        "type": "DRIFT",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    }
]
```

### New Reliability Monitor Metrics (from Dashboard Patterns)

#### Job Cost Efficiency Metrics (Pattern 5, 6)
**Source:** Jobs System Tables Dashboard, Azure Serverless Cost Dashboard

```python
{
    "name": "most_expensive_job_cost",
    "definition": """
        MAX(job_total_cost) FROM (
            SELECT usage_metadata_job_id, SUM(list_cost) as job_total_cost
            FROM :table
            WHERE usage_metadata_job_id IS NOT NULL
            GROUP BY usage_metadata_job_id
        )
    """,
    "type": "AGGREGATE",
    "input_columns": [":table"],
    "output_data_type": "DOUBLE"
},
{
    "name": "top_10_jobs_cost_concentration",
    "definition": """
        SUM(top_10_cost) / NULLIF(SUM(total_cost), 0) * 100 FROM (
            SELECT
                SUM(list_cost) as total_cost,
                SUM(CASE WHEN job_rank <= 10 THEN job_cost ELSE 0 END) as top_10_cost
            FROM (
                SELECT *, ROW_NUMBER() OVER (ORDER BY job_cost DESC) as job_rank
                FROM (
                    SELECT usage_metadata_job_id, SUM(list_cost) as job_cost
                    FROM :table WHERE usage_metadata_job_id IS NOT NULL
                    GROUP BY usage_metadata_job_id
                )
            )
        )
    """,
    "type": "AGGREGATE",
    "input_columns": [":table"],
    "output_data_type": "DOUBLE"
}
```

### Alert Thresholds from Dashboard Patterns

| Metric | Threshold | Alert Severity | Pattern Source |
|--------|-----------|----------------|----------------|
| `cost_7d_vs_prior_7d_growth_pct` | > 30% | WARNING | Azure Serverless |
| `cost_7d_vs_prior_7d_growth_pct` | > 50% | CRITICAL | Azure Serverless |
| `cost_30d_vs_prior_30d_growth_pct` | > 20% | WARNING | Azure Serverless |
| `jobs_with_outlier_runs_count` | > 5 | WARNING | Serverless Cost |
| `max_p90_deviation_pct` | > 100% | CRITICAL | Serverless Cost |
| `tag_coverage_pct` | < 80% | WARNING | Jobs System Tables |
| `tag_coverage_pct` | < 50% | CRITICAL | Jobs System Tables |
| `active_tables_drift` | < -10 | WARNING | Governance Hub |

---

## 🆕 GitHub Repository Pattern Enhancements for Lakehouse Monitoring

Based on analysis of open-source Databricks repositories, the following monitoring enhancements should be incorporated:

### From system-tables-audit-logs Repository

#### Time-Windowed Anomaly Detection Metrics
**Pattern:** 24-hour and 90-day rolling windows for baseline comparison

```python
# Time-windowed security monitoring metrics (from audit logs repo)
audit_time_window_metrics = [
    {
        "name": "events_24h_vs_90d_baseline",
        "definition": """
            (COUNT(*) - AVG(historical_24h_count)) / NULLIF(STDDEV(historical_24h_count), 0)
        """,
        "type": "DRIFT",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE",
        "comment": "Z-score comparing current 24h events to 90-day baseline"
    },
    {
        "name": "sensitive_access_24h_rolling",
        "definition": """
            SUM(CASE WHEN source_table_full_name LIKE '%pii%' OR source_table_full_name LIKE '%sensitive%' THEN 1 ELSE 0 END)
        """,
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    },
    {
        "name": "unique_tables_24h",
        "definition": "COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name))",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "LONG"
    }
]
```

#### Temporal Clustering Metrics (60-minute buckets)
**Pattern:** Detect concentrated activity bursts

```python
# Temporal clustering for burst detection (from audit logs repo)
temporal_clustering_metrics = [
    {
        "name": "activity_burst_score",
        "definition": """
            MAX(hourly_event_count) / NULLIF(AVG(hourly_event_count), 0)
        """,
        "type": "AGGREGATE",
        "comment": "Ratio of peak hour to average hour - high values indicate bursts"
    },
    {
        "name": "off_hours_event_ratio",
        "definition": """
            SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END) /
            NULLIF(COUNT(*), 0) * 100
        """,
        "type": "AGGREGATE",
        "comment": "Percentage of events outside business hours (6 AM - 10 PM)"
    }
]
```

#### System Account Exclusion Pattern
```python
# Exclude system accounts from anomaly detection (from audit logs repo)
system_account_exclusion = {
    "name": "human_user_event_count",
    "definition": """
        COUNT(CASE
            WHEN created_by NOT LIKE 'system.%'
             AND created_by NOT LIKE 'databricks-%'
             AND created_by NOT LIKE '%service-principal%'
            THEN 1
        END)
    """,
    "type": "AGGREGATE",
    "comment": "Events from human users only, excluding system and service accounts"
}
```

### From Workflow Advisor Repository

#### Resource Utilization Monitoring
**Pattern:** Under/over-provisioning detection metrics

```python
# Cluster efficiency monitoring (from Workflow Advisor repo)
cluster_efficiency_metrics = [
    # Under-provisioning indicators
    {
        "name": "cpu_saturation_rate",
        "definition": """
            SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 90 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of time CPU is saturated (>90%) - high values indicate under-provisioning"
    },
    {
        "name": "memory_pressure_rate",
        "definition": """
            SUM(CASE WHEN mem_used_percent > 85 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of time memory under pressure (>85%)"
    },
    # Over-provisioning indicators
    {
        "name": "cpu_idle_rate",
        "definition": """
            SUM(CASE WHEN cpu_user_percent + cpu_system_percent < 20 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of time CPU is idle (<20%) - high values indicate over-provisioning"
    },
    {
        "name": "wasted_capacity_pct",
        "definition": """
            (100 - AVG(cpu_user_percent + cpu_system_percent)) *
            (100 - AVG(mem_used_percent)) / 10000
        """,
        "type": "AGGREGATE",
        "comment": "Combined CPU and memory waste indicator"
    },
    # Cost efficiency
    {
        "name": "cost_efficiency_score",
        "definition": """
            AVG(cpu_user_percent + cpu_system_percent) * AVG(mem_used_percent) / 100
        """,
        "type": "AGGREGATE",
        "comment": "Higher score = better resource utilization"
    }
]
```

#### Right-Sizing Alert Thresholds
```python
# Alert thresholds from Workflow Advisor patterns
rightsizing_thresholds = {
    "cpu_saturation_rate": {
        "warning": 20,   # >20% time at CPU saturation
        "critical": 40   # >40% time at CPU saturation
    },
    "cpu_idle_rate": {
        "info": 50,      # >50% time CPU idle
        "warning": 70    # >70% time CPU idle (significant waste)
    },
    "memory_pressure_rate": {
        "warning": 15,   # >15% time memory pressured
        "critical": 30   # >30% time memory pressured
    },
    "wasted_capacity_pct": {
        "info": 30,      # >30% combined waste
        "warning": 50    # >50% combined waste
    }
}
```

### From DBSQL Warehouse Advisor Repository

#### Query Efficiency Monitoring
**Pattern:** Materialized view layer and query performance flags

```python
# Query efficiency metrics (from DBSQL Warehouse Advisor repo)
query_efficiency_metrics = [
    {
        "name": "high_queue_rate",
        "definition": """
            SUM(CASE WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.1 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% queries where queue time > 10% of total time"
    },
    {
        "name": "complex_query_rate",
        "definition": """
            SUM(CASE
                WHEN LENGTH(statement_text) > 5000
                  OR (REGEXP_COUNT(UPPER(statement_text), 'JOIN') > 5)
                  OR (REGEXP_COUNT(UPPER(statement_text), 'SELECT') > 3)
                THEN 1 ELSE 0
            END) * 100.0 / NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of complex queries (long, many joins, subqueries)"
    },
    {
        "name": "inefficient_query_rate",
        "definition": """
            SUM(CASE
                WHEN (COALESCE(spill_local_bytes, 0) + COALESCE(spill_remote_bytes, 0)) > 0
                  OR waiting_at_capacity_duration_ms > 30000
                  OR total_duration_ms > 300000
                THEN 1 ELSE 0
            END) * 100.0 / NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% queries with efficiency issues (spills, high queue, slow)"
    },
    {
        "name": "avg_result_fetch_ratio",
        "definition": """
            AVG(
                COALESCE(result_fetch_time_ms, 0) * 100.0 /
                NULLIF(total_duration_ms, 0)
            )
        """,
        "type": "AGGREGATE",
        "comment": "Avg % of query time spent fetching results (high = network bottleneck)"
    }
]
```

### New Monitor: Cluster Right-Sizing Monitor (🆕)
**Source:** Workflow Advisor Repository

**Table:** `${catalog}.${gold_schema}.fact_node_timeline`
**Type:** Time Series
**Purpose:** Detect under/over-provisioned clusters for cost optimization

```python
# Full monitor definition with Workflow Advisor patterns
rightsizing_monitor_metrics = [
    # Utilization metrics
    {
        "name": "avg_cpu_utilization",
        "definition": "AVG(cpu_user_percent + cpu_system_percent)",
        "type": "AGGREGATE"
    },
    {
        "name": "p95_cpu_utilization",
        "definition": "PERCENTILE(cpu_user_percent + cpu_system_percent, 0.95)",
        "type": "AGGREGATE"
    },
    {
        "name": "avg_memory_utilization",
        "definition": "AVG(mem_used_percent)",
        "type": "AGGREGATE"
    },
    {
        "name": "p95_memory_utilization",
        "definition": "PERCENTILE(mem_used_percent, 0.95)",
        "type": "AGGREGATE"
    },
    # Provisioning indicators
    {
        "name": "underprovisioned_clusters",
        "definition": """
            COUNT(DISTINCT CASE
                WHEN cpu_user_percent + cpu_system_percent > 90
                  OR mem_used_percent > 85
                THEN cluster_id
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Count of clusters with saturation issues"
    },
    {
        "name": "overprovisioned_clusters",
        "definition": """
            COUNT(DISTINCT CASE
                WHEN cpu_user_percent + cpu_system_percent < 20
                 AND mem_used_percent < 30
                THEN cluster_id
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Count of significantly underutilized clusters"
    },
    # Cost impact
    {
        "name": "potential_savings_clusters",
        "definition": """
            COUNT(DISTINCT CASE
                WHEN cpu_user_percent + cpu_system_percent < 30
                 AND mem_used_percent < 40
                THEN cluster_id
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Clusters that could potentially be downsized"
    }
]
```

### Monitor Summary with GitHub Repo Enhancements

| Agent | Monitor | New Metrics from Repos | Source |
|-------|---------|------------------------|--------|
| 💰 Cost | Cost Monitor | time_windowed_growth, baseline_comparison | Audit Logs |
| 🔒 Security | Security Monitor | temporal_clustering, system_account_filter | Audit Logs |
| ⚡ Performance | Query Monitor | query_efficiency_score, complex_query_rate | DBSQL Advisor |
| ⚡ Performance | Cluster Monitor | rightsizing_indicators, provisioning_status | Workflow Advisor |
| 🔄 Reliability | Job Monitor | execution_efficiency, repair_cost_ratio | Workflow Advisor |
| ✅ Quality | Quality Monitor | drift_baseline_comparison | Audit Logs |
| 🤖 ML | Inference Monitor | prediction_accuracy_trend | - |
| 📊 Governance | Lineage Monitor | activity_temporal_patterns | Audit Logs |
| **🆕 Right-Sizing** | Cluster Efficiency | under/over_provisioning | **Workflow Advisor** |

---

## 🆕 Blog Post Pattern Enhancements

Based on analysis of Databricks blog posts and documentation, the following monitoring enhancements should be incorporated:

### From DBSQL Warehouse Advisor v5 Blog

**Key Insight:** P99 percentiles are more important than P95 for SLA monitoring; queries exceeding 60 seconds are flagged as slow.

```python
# Enhanced query metrics from DBSQL Warehouse Advisor v5 blog
warehouse_advisor_metrics = [
    # P99 percentile (critical for SLA)
    {
        "name": "p99_duration_sec",
        "definition": "PERCENTILE(total_duration_ms / 1000.0, 0.99)",
        "type": "AGGREGATE",
        "comment": "P99 latency - critical for SLA monitoring (from DBSQL Advisor blog)"
    },
    # QPS (Queries Per Second) - throughput metric
    {
        "name": "queries_per_minute",
        "definition": """
            COUNT(*) / NULLIF(
                TIMESTAMPDIFF(MINUTE, MIN(start_time), MAX(end_time)), 0
            )
        """,
        "type": "AGGREGATE",
        "comment": "Query throughput rate - capacity planning metric"
    },
    # 60-second SLA threshold (from blog)
    {
        "name": "sla_breach_rate",
        "definition": """
            SUM(CASE WHEN total_duration_ms > 60000 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% queries exceeding 60-second SLA threshold (from blog)"
    },
    # Warehouse tier efficiency
    {
        "name": "warehouse_tier_efficiency",
        "definition": """
            CASE
                WHEN warehouse_tier = 'SERVERLESS' THEN
                    AVG(total_duration_ms) / NULLIF(AVG(read_bytes / 1073741824.0), 0)
                ELSE
                    AVG(total_duration_ms) / NULLIF(AVG(read_bytes / 1073741824.0), 0) * 1.2
            END
        """,
        "type": "AGGREGATE",
        "comment": "Duration per GB read, adjusted by warehouse tier"
    }
]
```

### From Real-Time Query Monitoring Blog

**Key Insight:** Duration regression detection compares current query duration to historical baseline.

```python
# Duration regression metrics from Real-Time Query Monitoring blog
regression_detection_metrics = [
    {
        "name": "duration_regression_pct",
        "definition": """
            (AVG(total_duration_ms) - {{avg_duration_ms.baseline_30d}}) /
            NULLIF({{avg_duration_ms.baseline_30d}}, 0) * 100
        """,
        "type": "DRIFT",
        "comment": "% change in duration vs 30-day baseline - detects regressions"
    },
    {
        "name": "query_complexity_score",
        "definition": """
            AVG(
                CASE
                    WHEN LENGTH(statement_text) > 10000 THEN 5
                    WHEN LENGTH(statement_text) > 5000 THEN 4
                    WHEN REGEXP_COUNT(UPPER(statement_text), 'JOIN') > 5 THEN 4
                    WHEN REGEXP_COUNT(UPPER(statement_text), 'JOIN') > 3 THEN 3
                    WHEN REGEXP_COUNT(UPPER(statement_text), 'SUBQUERY|SELECT.*SELECT') > 2 THEN 3
                    ELSE 1
                END
            )
        """,
        "type": "AGGREGATE",
        "comment": "Average query complexity score (1-5 scale)"
    },
    {
        "name": "high_complexity_query_rate",
        "definition": """
            SUM(CASE
                WHEN LENGTH(statement_text) > 5000
                  OR REGEXP_COUNT(UPPER(statement_text), 'JOIN') > 3
                THEN 1 ELSE 0
            END) * 100.0 / NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of queries with high complexity"
    }
]
```

### From Workflow Advisor Blog

**Key Insight:** ALL_PURPOSE clusters are less cost-efficient than JOB clusters; identifying this pattern saves significant cost.

```python
# ALL_PURPOSE cluster inefficiency metrics from Workflow Advisor blog
cluster_efficiency_blog_metrics = [
    {
        "name": "all_purpose_cost_ratio",
        "definition": """
            SUM(CASE WHEN sku_name LIKE '%ALL_PURPOSE%' THEN list_cost ELSE 0 END) /
            NULLIF(SUM(list_cost), 0) * 100
        """,
        "type": "AGGREGATE",
        "comment": "% of total cost from ALL_PURPOSE clusters (should be minimized)"
    },
    {
        "name": "jobs_on_all_purpose_count",
        "definition": """
            COUNT(DISTINCT CASE
                WHEN sku_name LIKE '%ALL_PURPOSE%'
                 AND usage_metadata['job_id'] IS NOT NULL
                THEN usage_metadata['job_id']
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Jobs running on ALL_PURPOSE (should use JOB clusters)"
    },
    {
        "name": "potential_savings_from_job_clusters",
        "definition": """
            SUM(CASE
                WHEN sku_name LIKE '%ALL_PURPOSE%'
                 AND usage_metadata['job_id'] IS NOT NULL
                THEN list_cost * 0.4  -- ~40% savings with JOB clusters
                ELSE 0
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Estimated savings if jobs moved to JOB clusters"
    }
]
```

### New Monitor: Audit Log Security Monitor (🆕)

**Source:** system-tables-audit-logs GitHub repo + Security Blog
**Table:** `${catalog}.${gold_schema}.fact_audit_logs`
**Type:** Time Series
**Purpose:** Monitor security events with user type classification and burst detection

```python
# Security monitor metrics from audit logs repo patterns
audit_security_metrics = [
    # User type classification (from audit logs repo pattern)
    {
        "name": "human_user_events",
        "definition": """
            COUNT(CASE
                WHEN user_identity_email LIKE '%@%'
                 AND user_identity_email NOT LIKE 'System-%'
                 AND user_identity_email NOT LIKE '%spn@%'
                 AND user_identity_email NOT LIKE '%iam.gserviceaccount.com'
                THEN 1
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Events from human users (excludes system/service accounts)"
    },
    {
        "name": "service_principal_events",
        "definition": """
            COUNT(CASE
                WHEN user_identity_email LIKE '%spn@%'
                  OR user_identity_email LIKE '%iam.gserviceaccount.com'
                  OR user_identity_email NOT LIKE '%@%'
                THEN 1
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Events from service principals"
    },
    {
        "name": "system_account_events",
        "definition": """
            COUNT(CASE
                WHEN user_identity_email LIKE 'System-%'
                  OR user_identity_email LIKE 'DBX_%'
                  OR user_identity_email IN ('Unity Catalog', 'Delta Sharing')
                THEN 1
            END)
        """,
        "type": "AGGREGATE",
        "comment": "Events from Databricks system accounts"
    },
    # Burst detection (from audit logs repo temporal clustering)
    {
        "name": "activity_burst_ratio",
        "definition": """
            MAX(hourly_count) / NULLIF(AVG(hourly_count), 0)
        """,
        "type": "AGGREGATE",
        "comment": "Peak hour vs average hour ratio - >3x indicates burst"
    },
    # Off-hours activity (from security monitoring patterns)
    {
        "name": "off_hours_human_activity_rate",
        "definition": """
            SUM(CASE
                WHEN (HOUR(event_time) < 7 OR HOUR(event_time) >= 19)
                 AND user_identity_email LIKE '%@%'
                 AND user_identity_email NOT LIKE 'System-%'
                THEN 1 ELSE 0
            END) * 100.0 /
            NULLIF(COUNT(CASE WHEN user_identity_email LIKE '%@%' THEN 1 END), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of human user events outside business hours (7am-7pm)"
    },
    # Failed action monitoring
    {
        "name": "failed_action_rate",
        "definition": """
            SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of actions that failed - high rate may indicate attack"
    },
    {
        "name": "sensitive_action_rate",
        "definition": """
            SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)
        """,
        "type": "AGGREGATE",
        "comment": "% of actions flagged as sensitive"
    }
]
```

### Enhanced Alert Thresholds from Blog Patterns

| Metric | Threshold | Severity | Source |
|--------|-----------|----------|--------|
| `p99_duration_sec` | > 60 | WARNING | DBSQL Advisor Blog |
| `p99_duration_sec` | > 120 | CRITICAL | DBSQL Advisor Blog |
| `sla_breach_rate` | > 5% | WARNING | DBSQL Advisor Blog |
| `sla_breach_rate` | > 10% | CRITICAL | DBSQL Advisor Blog |
| `duration_regression_pct` | > 50% | WARNING | Real-Time Monitoring Blog |
| `duration_regression_pct` | > 100% | CRITICAL | Real-Time Monitoring Blog |
| `all_purpose_cost_ratio` | > 30% | WARNING | Workflow Advisor Blog |
| `all_purpose_cost_ratio` | > 50% | CRITICAL | Workflow Advisor Blog |
| `activity_burst_ratio` | > 5 | WARNING | Audit Logs Repo |
| `activity_burst_ratio` | > 10 | CRITICAL | Audit Logs Repo |
| `off_hours_human_activity_rate` | > 20% | WARNING | Security Blog |
| `failed_action_rate` | > 10% | WARNING | Audit Logs Repo |
| `failed_action_rate` | > 25% | CRITICAL | Audit Logs Repo |

---

## Monitor Summary with All Enhancements

| Agent | Monitor | Gold Table | Key Metrics Added | Source |
|-------|---------|------------|-------------------|--------|
| 💰 Cost | Cost Monitor | fact_usage | all_purpose_cost_ratio, potential_savings | Workflow Advisor Blog |
| 🔒 Security | **Audit Log Monitor** (🆕) | fact_audit_logs | user_type_events, burst_ratio, off_hours_rate | Audit Logs Repo |
| 🔒 Security | Lineage Monitor | fact_table_lineage | active_tables_drift, read_write_ratio | Dashboard Patterns |
| ⚡ Performance | Query Monitor | fact_query_history | p99_duration, sla_breach_rate, qpm | DBSQL Advisor Blog |
| ⚡ Performance | Cluster Monitor | fact_node_timeline | rightsizing_indicators, efficiency_score | Workflow Advisor Repo |
| 🔄 Reliability | Job Monitor | fact_job_run_timeline | duration_regression, repair_cost_ratio | Dashboard Patterns |
| ✅ Quality | Quality Monitor | fact_data_quality_* | quality_score, violation_rate | Standard |
| 🤖 ML | Inference Monitor | cost_anomaly_predictions | MAE, MAPE, anomaly_rate | Standard |

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Monitors Created | 10 monitors (7 standard + 1 inference + 1 right-sizing + 1 audit log) |
| Custom Metrics | 90+ total across all domains |
| Alert Coverage | 100% of critical metrics |
| Dashboard Integration | All monitors visualized in domain dashboards |
| Response Time | Alerts triggered within 15 minutes |
| Right-Sizing Detection | Identify 100% of over/under-provisioned clusters |
| SLA Breach Detection | Detect 100% of queries exceeding 60-second threshold |
| Security Burst Detection | Identify activity bursts within 1 hour |

---

## References

### Official Databricks Documentation
- [Lakehouse Monitoring Overview](https://docs.databricks.com/lakehouse-monitoring)
- [Custom Metrics](https://docs.databricks.com/lakehouse-monitoring/custom-metrics)
- [Inference Table Monitoring](https://docs.databricks.com/mlflow/inference-tables)

### Microsoft Learn Documentation
- [Azure Databricks Lakehouse Monitoring](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-monitoring/)
- [Create Monitor API](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-monitoring/create-monitor-api)

### GitHub Repository References (🆕)
- [system-tables-audit-logs](https://github.com/andyweaves/system-tables-audit-logs) - Time-windowed anomaly detection, temporal clustering
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme) - Query efficiency metrics, complex query detection
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Under/over-provisioning detection, right-sizing metrics

### Cursor Rules Reference
- [Cursor Rule 17 - Lakehouse Monitoring Comprehensive](mdc:.cursor/rules/17-lakehouse-monitoring-comprehensive.mdc)
