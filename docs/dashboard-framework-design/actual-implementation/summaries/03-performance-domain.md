# Performance Domain - Actual Implementation

## Overview

**Dashboard:** `performance.lvdash.json`  
**Total Datasets:** 75  
**Primary Tables:**
- `fact_query_history` (SQL query performance)
- `fact_node_timeline` (cluster node metrics)
- `fact_cluster_timeline` (cluster-level metrics)
- `dim_workspace` (workspace metadata)
- `dim_user` (user lookup)

---

## 📊 Key Metrics

### Query Performance Metrics
- **Avg Duration (ms)**: Average query execution time
- **P95 Duration (ms)**: 95th percentile query latency
- **Total Queries**: Query volume count
- **Failed Queries**: Count of failed queries
- **Slow Query Threshold**: Queries >10 seconds

### Cluster Resource Metrics
- **Avg CPU Utilization %**: Cluster CPU usage
- **Avg Memory Utilization %**: Cluster memory usage
- **Peak CPU %**: Maximum CPU usage observed
- **Peak Memory %**: Maximum memory usage observed

### Optimization Metrics
- **Right-Sizing Opportunities**: Clusters with consistently low utilization
- **Savings Potential $**: Estimated savings from right-sizing
- **Warehouse Utilization %**: SQL Warehouse usage efficiency

---

## 🔑 Key Datasets

### ds_slowest_queries
**Purpose:** Top 50 slowest queries for optimization  
**Source:** `fact_query_history`  
**Key Query:**
```sql
SELECT 
  query_id,
  query_text,
  CAST(executed_by_user_id AS STRING) AS user_id,
  compute_type,
  ROUND(duration_ms / 1000.0, 2) AS duration_seconds,
  start_time
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time BETWEEN :time_range.min AND :time_range.max
  AND status = 'FINISHED'
ORDER BY duration_ms DESC
LIMIT 50
```

### ds_monitor_cpu_trend
**Purpose:** Daily CPU utilization trend from cluster metrics  
**Source:** `fact_node_timeline`  
**Key Query:**
```sql
SELECT 
  DATE(timestamp) AS date,
  AVG(cpu_utilization_percent) AS avg_cpu,
  MAX(cpu_utilization_percent) AS peak_cpu
FROM ${catalog}.${gold_schema}.fact_node_timeline
WHERE timestamp >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE(timestamp)
ORDER BY date
```

### ds_rightsizing_recommendations
**Purpose:** Clusters candidates for downsizing  
**Source:** `fact_node_timeline` + cost  
**Key Query:**
```sql
WITH cluster_utilization AS (
  SELECT 
    cluster_id,
    AVG(cpu_utilization_percent) AS avg_cpu,
    AVG(memory_utilization_percent) AS avg_memory,
    COUNT(*) AS sample_count
  FROM ${catalog}.${gold_schema}.fact_node_timeline
  WHERE timestamp >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY cluster_id
  HAVING sample_count > 100  -- Sufficient data
)
SELECT 
  cluster_id,
  ROUND(avg_cpu, 1) AS avg_cpu_pct,
  ROUND(avg_memory, 1) AS avg_memory_pct,
  CASE 
    WHEN avg_cpu < 30 AND avg_memory < 40 THEN 'Downsize 50%'
    WHEN avg_cpu < 50 AND avg_memory < 60 THEN 'Downsize 25%'
    ELSE 'Monitor'
  END AS recommendation
FROM cluster_utilization
WHERE avg_cpu < 50 OR avg_memory < 60
ORDER BY avg_cpu, avg_memory
```

---

## 📑 Data Sources

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `fact_query_history` | query_id, duration_ms, executed_by_user_id, compute_type | Query performance analytics |
| `fact_node_timeline` | cluster_id, cpu_utilization_percent, memory_utilization_percent | Resource utilization |
| `fact_cluster_timeline` | cluster_id, node_count, is_photon_enabled | Cluster configuration |

---

## 🔍 Common Query Patterns

### Percentile Calculation
```sql
PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_duration_ms
```

### Resource Utilization
```sql
AVG(cpu_utilization_percent) AS avg_cpu,
MAX(cpu_utilization_percent) AS peak_cpu
```

### Right-Sizing Logic
```sql
CASE 
  WHEN avg_cpu < 30 THEN 'Underutilized'
  WHEN avg_cpu BETWEEN 30 AND 70 THEN 'Optimal'
  ELSE 'High Utilization'
END AS sizing_category
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial documentation |

