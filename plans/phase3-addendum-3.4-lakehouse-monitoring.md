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
        "definition": "SUM(usage_quantity * list_price)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "avg_cost_per_dbu",
        "definition": "AVG(list_price)",
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
            (SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN usage_quantity * list_price ELSE 0 END) -
             SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN usage_quantity * list_price ELSE 0 END)) /
            NULLIF(SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN usage_quantity * list_price ELSE 0 END), 0) * 100
        """,
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    # ==== TAG HYGIENE METRICS ====
    # Critical for cost attribution - tracks tagging practices
    # Reference: https://docs.databricks.com/aws/en/admin/system-tables/billing
    {
        "name": "untagged_usage_pct",
        "definition": "SUM(CASE WHEN custom_tags IS NULL OR size(custom_tags) = 0 THEN usage_quantity * list_price ELSE 0 END) / NULLIF(SUM(usage_quantity * list_price), 0) * 100",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "tagged_cost_total",
        "definition": "SUM(CASE WHEN custom_tags IS NOT NULL AND size(custom_tags) > 0 THEN usage_quantity * list_price ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "untagged_cost_total",
        "definition": "SUM(CASE WHEN custom_tags IS NULL OR size(custom_tags) = 0 THEN usage_quantity * list_price ELSE 0 END)",
        "type": "AGGREGATE",
        "input_columns": [":table"],
        "output_data_type": "DOUBLE"
    },
    {
        "name": "tag_coverage_pct",
        "definition": "SUM(CASE WHEN custom_tags IS NOT NULL AND size(custom_tags) > 0 THEN usage_quantity * list_price ELSE 0 END) / NULLIF(SUM(usage_quantity * list_price), 0) * 100",
        "type": "AGGREGATE",
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

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Monitors Created | 7 monitors (1 per domain + 1 inference) |
| Custom Metrics | 50+ total across all domains |
| Alert Coverage | 100% of critical metrics |
| Dashboard Integration | All monitors visualized in domain dashboards |
| Response Time | Alerts triggered within 15 minutes |

---

## References

### Official Databricks Documentation
- [Lakehouse Monitoring Overview](https://docs.databricks.com/lakehouse-monitoring)
- [Custom Metrics](https://docs.databricks.com/lakehouse-monitoring/custom-metrics)
- [Inference Table Monitoring](https://docs.databricks.com/mlflow/inference-tables)

### Microsoft Learn Documentation
- [Azure Databricks Lakehouse Monitoring](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-monitoring/)
- [Create Monitor API](https://learn.microsoft.com/en-us/azure/databricks/lakehouse-monitoring/create-monitor-api)

### Cursor Rules Reference
- [Cursor Rule 17 - Lakehouse Monitoring Comprehensive](mdc:.cursor/rules/17-lakehouse-monitoring-comprehensive.mdc)
