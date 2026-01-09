# Quick Reference - All Domains

## Overview

This document provides a **quick lookup** for finding specific metrics, queries, and data sources across all dashboard domains.

---

## 📊 Metric Quick Finder

### Financial Metrics
| Metric | Domain | Formula | Source Table |
|--------|--------|---------|--------------|
| MTD Spend | Cost | `SUM(list_cost)` month-to-date | fact_usage |
| Tag Coverage % | Cost | `(tagged_cost / total_cost) * 100` | fact_usage |
| Serverless Adoption % | Cost | `(serverless_cost / total_cost) * 100` | fact_usage |
| Total DBUs | Cost | `SUM(usage_quantity)` | fact_usage |
| Savings Potential | Cost | ML prediction | ML model |

### Reliability Metrics
| Metric | Domain | Formula | Source Table |
|--------|--------|---------|--------------|
| Success Rate % | Reliability | `(success_count / total_runs) * 100` | fact_job_run_timeline |
| MTTR (hours) | Reliability | Avg time from failure to next success | fact_job_run_timeline |
| Avg Duration | Reliability | `AVG(duration_seconds)` | fact_job_run_timeline |
| P95 Duration | Reliability | `PERCENTILE_CONT(0.95)` | fact_job_run_timeline |
| Failure Rate % | Reliability | `(failure_count / total_runs) * 100` | fact_job_run_timeline |

### Performance Metrics
| Metric | Domain | Formula | Source Table |
|--------|--------|---------|--------------|
| Avg Query Duration | Performance | `AVG(duration_ms)` | fact_query_history |
| P95 Query Latency | Performance | `PERCENTILE_CONT(0.95)` | fact_query_history |
| Avg CPU % | Performance | `AVG(cpu_utilization_percent)` | fact_node_timeline |
| Avg Memory % | Performance | `AVG(memory_utilization_percent)` | fact_node_timeline |
| Slow Query Count | Performance | `COUNT WHERE duration_ms > 10000` | fact_query_history |

### Security Metrics
| Metric | Domain | Formula | Source Table |
|--------|--------|---------|--------------|
| Total Events | Security | `COUNT(*)` | fact_audit_logs |
| Failed Events | Security | `COUNT WHERE status_code >= 400` | fact_audit_logs |
| High-Risk Events | Security | `COUNT WHERE risk_level IN ('High', 'Critical')` | fact_audit_logs |
| Unique Users | Security | `COUNT(DISTINCT user_identity_email)` | fact_audit_logs |
| Event Success Rate % | Security | `(success_count / total_events) * 100` | fact_audit_logs |

### Quality Metrics
| Metric | Domain | Formula | Source Table |
|--------|--------|---------|--------------|
| Total Tables | Quality | `COUNT(*)` | system.information_schema.tables |
| Tagged Tables % | Quality | `(tagged_count / total_count) * 100` | system.information_schema.table_tags |
| Documented Tables % | Quality | `(documented_count / total_count) * 100` | system.information_schema.tables |
| Active Tables | Quality | Tables accessed in last 30 days | fact_query_history |
| Stale Tables | Quality | Tables not accessed >90 days | fact_query_history |

---

## 🗃️ Table Quick Reference

| Table Name | Domain(s) Using | Row Count | Primary Use | Key Columns |
|------------|----------------|-----------|-------------|-------------|
| **fact_usage** | Cost, Unified | ~millions | Cost analytics | usage_date, list_cost, sku_name, workspace_id |
| **fact_job_run_timeline** | Reliability, Unified | ~millions | Job reliability | period_start_time, job_id, result_state, duration_seconds |
| **fact_query_history** | Performance, Quality | ~millions | Query performance, usage | start_time, duration_ms, executed_by_user_id, query_text |
| **fact_node_timeline** | Performance | ~millions | Cluster metrics | timestamp, cluster_id, cpu_utilization_percent, memory_utilization_percent |
| **fact_audit_logs** | Security, Unified | ~millions | Audit events | event_date, user_identity_email, action_name, response_status_code |
| **system.information_schema.tables** | Quality, Unified | ~thousands | Table metadata | table_catalog, table_schema, table_name, comment |
| **system.information_schema.columns** | Quality | ~hundreds of thousands | Column metadata | table_name, column_name, comment |
| **system.information_schema.table_tags** | Quality | ~thousands | Governance tags | catalog_name, schema_name, table_name, tag_name, tag_value |
| **dim_workspace** | All | ~hundreds | Workspace names | workspace_id, workspace_name, workspace_url |
| **dim_job** | Cost, Reliability | ~thousands | Job metadata | job_id, job_name, creator_id |
| **dim_user** | All | ~thousands | User lookup | user_id, email, display_name |

---

## 🔍 Common Query Patterns by Use Case

### Use Case: Find Top Cost Drivers
**Domains:** Cost  
**Tables:** fact_usage + dim_workspace + dim_user  
**Pattern:**
```sql
SELECT 
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace,
  COALESCE(u.email, f.identity_metadata_run_as) AS owner,
  ROUND(SUM(f.list_cost), 2) AS total_cost
FROM fact_usage f
LEFT JOIN dim_workspace w ON f.workspace_id = w.workspace_id
LEFT JOIN dim_user u ON f.identity_metadata_run_as = u.user_id
WHERE usage_date BETWEEN :start AND :end
GROUP BY 1, 2
ORDER BY total_cost DESC
LIMIT 20
```

### Use Case: Identify Unreliable Jobs
**Domains:** Reliability  
**Tables:** fact_job_run_timeline + dim_job + dim_user  
**Pattern:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)) AS job_name,
  COALESCE(u.email, j.run_as, 'Unknown') AS owner,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
  ROUND(100.0 * SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_rate
FROM fact_job_run_timeline r
LEFT JOIN dim_job j ON r.job_id = j.job_id
LEFT JOIN dim_user u ON COALESCE(j.run_as, j.creator_id) = u.user_id
WHERE period_start_time BETWEEN :start AND :end
GROUP BY 1, 2
HAVING success_rate < 80.0
ORDER BY success_rate, total_runs DESC
```

### Use Case: Find Slow Queries
**Domains:** Performance  
**Tables:** fact_query_history  
**Pattern:**
```sql
SELECT 
  query_id,
  LEFT(query_text, 100) AS query_preview,
  CAST(executed_by_user_id AS STRING) AS user_id,
  compute_type,
  ROUND(duration_ms / 1000.0, 2) AS duration_seconds,
  start_time
FROM fact_query_history
WHERE start_time BETWEEN :start AND :end
  AND status = 'FINISHED'
  AND duration_ms > 10000  -- >10 seconds
ORDER BY duration_ms DESC
LIMIT 50
```

### Use Case: Identify Security Risks
**Domains:** Security  
**Tables:** fact_audit_logs  
**Pattern:**
```sql
SELECT 
  event_date,
  user_identity_email,
  service_name,
  action_name,
  risk_level,
  response_status_code,
  error_message
FROM fact_audit_logs
WHERE event_date BETWEEN :start AND :end
  AND (
    risk_level IN ('High', 'Critical')
    OR response_status_code >= 400
  )
ORDER BY event_date DESC, risk_level DESC
LIMIT 100
```

### Use Case: Find Untagged High-Cost Resources
**Domains:** Cost  
**Tables:** fact_usage + dim_workspace  
**Pattern:**
```sql
SELECT 
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace,
  COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name,
  ROUND(SUM(f.list_cost), 2) AS total_cost,
  'No Tags' AS tag_status
FROM fact_usage f
LEFT JOIN dim_workspace w ON f.workspace_id = w.workspace_id
LEFT JOIN dim_job j ON f.usage_metadata_job_id = j.job_id
WHERE usage_date BETWEEN :start AND :end
  AND NOT f.is_tagged
  AND f.usage_metadata_job_id IS NOT NULL
GROUP BY 1, 2
HAVING total_cost > 100  -- Focus on high-value resources
ORDER BY total_cost DESC
LIMIT 50
```

### Use Case: Find Undocumented Tables
**Domains:** Quality  
**Tables:** system.information_schema.tables, system.information_schema.columns, fact_query_history  
**Pattern:**
```sql
WITH table_docs AS (
  SELECT 
    table_catalog,
    table_schema,
    table_name,
    comment
  FROM system.information_schema.tables
  WHERE table_type IN ('MANAGED', 'EXTERNAL', 'VIEW')
),
usage AS (
  SELECT 
    CONCAT(catalog, '.', schema, '.', table_name) AS full_name,
    COUNT(*) AS query_count
  FROM fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 90 DAYS
  GROUP BY 1
)
SELECT 
  t.table_catalog,
  t.table_schema,
  t.table_name,
  COALESCE(u.query_count, 0) AS query_count,
  CASE 
    WHEN t.comment IS NULL OR TRIM(t.comment) = '' THEN 'Missing Documentation'
    ELSE 'Documented'
  END AS status
FROM table_docs t
LEFT JOIN usage u ON CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) = u.full_name
WHERE t.comment IS NULL OR TRIM(t.comment) = ''
ORDER BY query_count DESC NULLS LAST
LIMIT 50
```

---

## 📈 Lakehouse Monitoring Table Reference

| Monitor Table | Source Fact Table | Contains |
|---------------|-------------------|----------|
| `fact_usage_profile_metrics` | fact_usage | Aggregated cost metrics (sum, avg, max, min) |
| `fact_usage_drift_metrics` | fact_usage | Week-over-week cost changes |
| `fact_job_run_timeline_profile_metrics` | fact_job_run_timeline | Aggregated reliability metrics |
| `fact_job_run_timeline_drift_metrics` | fact_job_run_timeline | Week-over-week reliability changes |
| `fact_audit_logs_profile_metrics` | fact_audit_logs | Aggregated security metrics |
| `fact_audit_logs_drift_metrics` | fact_audit_logs | Week-over-week security changes |

**Common Query Pattern for Profile Metrics:**
```sql
SELECT 
  column_name AS metric_name,
  CAST(column_values.aggregate_metrics['sum'] AS DOUBLE) AS sum_value,
  CAST(column_values.aggregate_metrics['avg'] AS DOUBLE) AS avg_value,
  window_start_time AS date
FROM <fact_table>_profile_metrics
WHERE column_name = ':table'  -- Table-level metrics
  AND window_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY window_start_time DESC
```

**Common Query Pattern for Drift Metrics:**
```sql
SELECT 
  column_name AS metric_name,
  CAST(drift_values.drift_metrics['absolute_diff'] AS DOUBLE) AS absolute_change,
  CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE) AS percent_change,
  drift_type,
  window_start_time
FROM <fact_table>_drift_metrics
WHERE window_start_time = (SELECT MAX(window_start_time) FROM <fact_table>_drift_metrics)
ORDER BY ABS(CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE)) DESC
```

---

## 🎯 ML Model Reference

| Model Name | Domain | Predicts | Input Features | Output Columns |
|------------|--------|----------|----------------|----------------|
| **cost_anomaly_detector** | Cost | Cost anomalies | Historical cost, job patterns | anomaly_score, anomaly_severity |
| **budget_forecaster** | Cost | Budget exhaustion | Spend trends, run rate | predicted_mtd, days_to_budget |
| **tag_recommender** | Cost | Tag suggestions | Job patterns, team patterns | recommended_tag_key, recommended_tag_value, confidence_score |
| **job_failure_risk** | Reliability | Failure probability | Job history, error patterns | failure_probability, risk_category, contributing_factors |
| **retry_success_predictor** | Reliability | Retry likelihood | Failure type, timing | retry_success_probability, recommended_wait_hours |
| **duration_forecaster** | Reliability | Job duration | Historical durations, resource config | predicted_duration_seconds, confidence_interval |
| **query_optimizer** | Performance | Optimization opportunities | Query patterns, resource usage | optimization_type, estimated_savings |

---

## 🔧 Parameter Reference

### Time Range Parameters
- **`:time_range.min`** - Start date for filtering (used in most queries)
- **`:time_range.max`** - End date for filtering (used in most queries)

### Filter Parameters
- **`:param_catalog`** - Multi-select catalog filter (Quality dashboard)
- **`:param_workspace`** - Workspace filter (across dashboards)
- **`:param_sku`** - SKU/Billing Origin Product filter (Cost dashboard)
- **`:param_job_status`** - Job result state filter (Reliability dashboard)

### Configuration Parameters
- **`:commitment_amount`** - Annual commitment value (Cost dashboard)
- **`${catalog}`** - Catalog variable from bundle (all queries)
- **`${gold_schema}`** - Gold schema variable from bundle (all queries)
- **`${feature_schema}`** - Feature store schema for ML predictions

---

## 📚 Document Navigation

| Topic | Document | Key Sections |
|-------|----------|--------------|
| **Index & Overview** | [00-index.md](00-index.md) | Organization, metadata summary |
| **Cost Metrics** | [01-cost-domain.md](01-cost-domain.md) | 61 datasets, financial KPIs, tag compliance |
| **Reliability Metrics** | [02-reliability-domain.md](02-reliability-domain.md) | 49 datasets, success rates, MTTR, duration |
| **Performance Metrics** | [03-performance-domain.md](03-performance-domain.md) | 75 datasets, query performance, cluster utilization |
| **Quality Metrics** | [04-quality-domain.md](04-quality-domain.md) | 32 datasets, governance, documentation, lineage |
| **Security Metrics** | [05-security-domain.md](05-security-domain.md) | 36 datasets, audit events, access control |
| **Unified Dashboard** | [06-unified-domain.md](06-unified-domain.md) | 63 datasets, health scores, cross-domain alerts |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial quick reference guide |

