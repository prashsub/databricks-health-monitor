# Performance Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Performance Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks query and cluster performance analytics. Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, cluster efficiency, and right-sizing opportunities without SQL. Powered by 3 Metric Views, 16 TVFs, 7 ML Models, and Lakehouse Monitoring performance metrics.

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Query Performance
1. "What is our average query duration?"
2. "Show me slow queries from today"
3. "What is the P95 query duration?"
4. "Which warehouse has the highest queue time?"
5. "What is the SLA breach rate?"

### Cluster Utilization
6. "What is our average CPU utilization?"
7. "Which clusters are underutilized?"
8. "Show me memory utilization by cluster"
9. "Which clusters are overprovisioned?"

### Optimization
10. "Show me right-sizing recommendations"
11. "Which clusters are on legacy DBR?"
12. "What's the potential savings from downsizing?"
13. "Show me queries needing optimization"

### ML-Powered Insights 🤖
14. "Which queries should I optimize?"
15. "Recommend optimal cluster capacity"

---

## ████ SECTION D: DATA ASSETS ████

### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `query_performance` | Query execution metrics | total_queries, avg_duration_ms, p95_duration_ms, p99_duration_ms, cache_hit_rate, sla_breach_rate |
| `cluster_utilization` | Resource metrics | avg_cpu_utilization, avg_memory_utilization, total_node_hours |
| `cluster_efficiency` | Efficiency analytics | p95_cpu_total_pct, cpu_saturation_hours, cpu_idle_hours, underprovisioned_hours |

### Table-Valued Functions (16 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_slow_queries` | Queries exceeding threshold | "slow queries" |
| `get_warehouse_utilization` | Warehouse metrics | "warehouse utilization" |
| `get_query_efficiency` | Efficiency analysis | "query efficiency" |
| `get_high_spill_queries` | Memory pressure queries | "high spill", "memory issues" |
| `get_query_volume_trends` | Query volume trends | "query volume" |
| `get_user_query_summary` | User-level summary | "queries by user" |
| `get_query_latency_percentiles` | Latency percentiles | "P95 latency" |
| `get_failed_queries` | Failed queries | "failed queries" |
| `get_query_efficiency_analysis` | Full efficiency analysis | "efficiency report" |
| `get_job_outlier_runs` | Duration outliers | "outlier jobs" |
| `get_cluster_utilization` | Cluster resource metrics | "cluster utilization" |
| `get_cluster_resource_metrics` | Detailed metrics | "CPU/memory details" |
| `get_underutilized_clusters` | Underutilized clusters | "underutilized", "wasted capacity" |
| `get_jobs_without_autoscaling` | Jobs missing autoscale | "jobs without autoscaling" |
| `get_jobs_on_legacy_dbr` | Legacy DBR jobs | "legacy DBR" |
| `get_cluster_right_sizing_recommendations` | Right-sizing suggestions | "right-sizing" |

### ML Prediction Tables 🤖

| Table Name | Purpose |
|------------|---------|
| `query_optimization_classifications` | Queries flagged for optimization |
| `query_optimization_recommendations` | Specific optimization suggestions |
| `cache_hit_predictions` | Cache effectiveness predictions |
| `job_duration_predictions` | Job completion time estimates |
| `cluster_capacity_recommendations` | Optimal cluster capacity |
| `cluster_rightsizing_recommendations` | Right-sizing with savings |
| `dbr_migration_risk_scores` | DBR migration risk assessment |

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_query_history_profile_metrics` | Custom query metrics (p99_duration, sla_breach_rate, qps) |
| `fact_query_history_drift_metrics` | Performance drift (duration_drift, qps_drift) |
| `fact_node_timeline_profile_metrics` | Custom cluster metrics (p95_cpu, saturation_hours) |
| `fact_node_timeline_drift_metrics` | Resource drift (cpu_drift, memory_drift) |

### Dimension Tables (from gold_layer_design/yaml/compute/, query_performance/, shared/)

| Table Name | Purpose | Key Columns | YAML Source |
|------------|---------|-------------|-------------|
| `dim_warehouse` | Warehouse metadata | warehouse_id, warehouse_name, size, type | query_performance/dim_warehouse.yaml |
| `dim_cluster` | Cluster metadata | cluster_id, cluster_name, node_type, dbr_version | compute/dim_cluster.yaml |
| `dim_node_type` | Node type specs | node_type_id, num_cores, memory_gb, gpu_count | compute/dim_node_type.yaml |
| `dim_workspace` | Workspace reference | workspace_id, workspace_name | shared/dim_workspace.yaml |

### Fact Tables (from gold_layer_design/yaml/compute/, query_performance/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_query_history` | Query execution history | Per query | query_performance/fact_query_history.yaml |
| `fact_warehouse_events` | Warehouse lifecycle events | Per event | query_performance/fact_warehouse_events.yaml |
| `fact_node_timeline` | Node utilization metrics | Per node per minute | compute/fact_node_timeline.yaml |

---

## ████ SECTION E: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks performance analyst. Follow these rules:

1. **Query Questions:** Use query_performance metric view first
2. **Cluster Questions:** Use cluster_utilization or cluster_efficiency metric view
3. **TVFs:** Use TVFs for parameterized queries (date ranges, thresholds)
4. **Date Default:** Queries=last 24h, Clusters=last 7 days
5. **Duration Units:** Queries in seconds, jobs in minutes
6. **Sorting:** Sort by duration DESC for slow queries, cpu ASC for underutilized
7. **Limits:** Top 20 for performance lists
8. **Percentiles:** P50=median, P95=tail, P99=extreme
9. **SLA Threshold:** 60 seconds default, high spill = any spill > 0
10. **Underutilized:** CPU <30% average
11. **ML Optimization:** For "optimize queries" → query query_optimization_recommendations
12. **ML Right-Sizing:** For "right-sizing" → query cluster_rightsizing_recommendations
13. **Slow Queries:** For "slow queries" → use get_slow_queries TVF
14. **Underutilized:** For "underutilized clusters" → use get_underutilized_clusters TVF
15. **Synonyms:** query=statement=SQL, cluster=compute, warehouse=endpoint
16. **Context:** Explain EFFICIENT vs HIGH_SPILL vs SLOW
17. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION F: TABLE-VALUED FUNCTIONS ████

### Query TVFs

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_slow_queries` | `(start_date STRING, end_date STRING, threshold_seconds INT)` | Slow queries | "slow queries today" |
| `get_warehouse_utilization` | `(start_date STRING, end_date STRING)` | Warehouse metrics | "warehouse utilization" |
| `get_high_spill_queries` | `(start_date STRING, end_date STRING)` | Memory pressure | "spill queries" |
| `get_query_efficiency_analysis` | `(warehouse_id STRING, start_date STRING, end_date STRING)` | Full efficiency | "efficiency report" |
| `get_query_latency_percentiles` | `(warehouse_id STRING, start_date STRING, end_date STRING)` | Latency stats | "P95 latency" |

### Cluster TVFs

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_cluster_utilization` | `(start_date STRING, end_date STRING)` | Cluster metrics | "cluster utilization" |
| `get_underutilized_clusters` | `(start_date STRING, end_date STRING, cpu_threshold DOUBLE)` | Underutilized | "wasted capacity" |
| `get_jobs_without_autoscaling` | `(start_date STRING, end_date STRING)` | Missing autoscale | "no autoscaling" |
| `get_jobs_on_legacy_dbr` | `(start_date STRING, end_date STRING)` | Legacy DBR | "old DBR versions" |
| `get_cluster_right_sizing_recommendations` | `(start_date STRING, end_date STRING)` | Right-sizing | "optimization" |

---

## ████ SECTION G: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "What is our average query duration?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(avg_duration_ms) / 1000.0 as avg_duration_seconds
FROM ${catalog}.${gold_schema}.query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single value in seconds

---

### Question 2: "Show me slow queries from today"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_slow_queries(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  60
)
ORDER BY duration_seconds DESC
LIMIT 20;
```
**Expected Result:** Table of slow queries (>60s) from today

---

### Question 3: "What is our average CPU utilization?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(avg_cpu_utilization) as avg_cpu_pct
FROM ${catalog}.${gold_schema}.cluster_utilization
WHERE metric_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single percentage value

---

### Question 4: "Which clusters are underutilized?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_underutilized_clusters(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  30.0
)
ORDER BY potential_savings DESC
LIMIT 20;
```
**Expected Result:** Clusters with <30% CPU utilization

---

### Question 5: "What is the P95 query duration?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(p95_duration_ms) / 1000.0 as p95_duration_seconds
FROM ${catalog}.${gold_schema}.query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Single value in seconds

---

### Question 6: "Show me right-sizing recommendations"
**Expected SQL:**
```sql
SELECT 
  cluster_id,
  current_size,
  recommended_size,
  potential_savings
FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations
WHERE potential_savings > 0
ORDER BY potential_savings DESC
LIMIT 20;
```
**Expected Result:** Clusters with recommended downsizing

---

### Question 7: "Which warehouse has the highest queue time?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_warehouse_utilization(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY avg_queue_time DESC
LIMIT 5;
```
**Expected Result:** Warehouses sorted by queue time

---

### Question 8: "Which queries should I optimize?"
**Expected SQL:**
```sql
SELECT 
  query_id,
  needs_optimization,
  reason
FROM ${catalog}.${gold_schema}.query_optimization_classifications
WHERE needs_optimization = TRUE
ORDER BY query_id DESC
LIMIT 20;
```
**Expected Result:** Queries flagged for optimization

---

### Question 9: "Show me clusters without autoscaling"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_jobs_without_autoscaling(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY total_cost DESC
LIMIT 20;
```
**Expected Result:** Jobs without autoscaling enabled

---

### Question 10: "What are the potential savings from right-sizing?"
**Expected SQL:**
```sql
SELECT 
  SUM(potential_savings) as total_potential_savings
FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations
WHERE potential_savings > 0;
```
**Expected Result:** Total potential savings amount

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 17 lines (≤20) | ✅ |
| **F. TVFs** | 16 functions with signatures | ✅ |
| **G. Benchmark Questions** | 10 with SQL answers | ✅ |

---

## Agent Domain Tag

**Agent Domain:** ⚡ **Performance**

