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
| `fact_query_history_profile_metrics` | Custom query metrics (p99_duration_ms, sla_breach_rate, queries_per_second) |
| `fact_query_history_drift_metrics` | Performance drift (duration_drift, qps_drift) |
| `fact_node_timeline_profile_metrics` | Custom cluster metrics (p95_cpu_total_pct, cpu_saturation_hours) |
| `fact_node_timeline_drift_metrics` | Resource drift (cpu_drift_pct, memory_drift_pct) |

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**Always include these filters when querying Lakehouse Monitoring tables:**

```sql
-- ✅ CORRECT: Get query performance metrics
SELECT 
  window.start AS window_start,
  p99_duration_ms,
  sla_breach_rate,
  queries_per_second
FROM ${catalog}.${gold_schema}.fact_query_history_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
  AND slice_key IS NULL          -- For overall metrics
ORDER BY window.start DESC;

-- ✅ CORRECT: Get cluster utilization metrics
SELECT 
  window.start AS window_start,
  p95_cpu_total_pct,
  cpu_saturation_hours,
  cpu_idle_hours
FROM ${catalog}.${gold_schema}.fact_node_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window.start DESC;

-- ✅ CORRECT: Get performance by warehouse (sliced)
SELECT 
  slice_value AS warehouse_id,
  AVG(p99_duration_ms) AS avg_p99_duration
FROM ${catalog}.${gold_schema}.fact_query_history_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'compute_warehouse_id'
GROUP BY slice_value;

-- ✅ CORRECT: Get performance drift
SELECT 
  window.start AS window_start,
  duration_drift,
  qps_drift
FROM ${catalog}.${gold_schema}.fact_query_history_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC;
```

#### Available Slicing Dimensions

**Query Monitor:**
| Slice Key | Use Case |
|-----------|----------|
| `workspace_id` | Performance by workspace |
| `compute_warehouse_id` | Performance by warehouse |
| `execution_status` | Status breakdown |
| `statement_type` | Query type analysis |
| `executed_by` | Queries by user |

**Cluster Monitor:**
| Slice Key | Use Case |
|-----------|----------|
| `workspace_id` | Utilization by workspace |
| `cluster_id` | Per-cluster metrics |
| `node_type` | By node type |
| `cluster_name` | By cluster name |
| `driver` | Driver vs worker |

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

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSET SELECTION DECISION TREE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER QUERY PATTERN                → USE THIS ASSET             │
│  ─────────────────────────────────────────────────────────────  │
│  "What's the P95 latency?"         → Metric View (query_performance)│
│  "Average CPU utilization"         → Metric View (cluster_utilization)│
│  ─────────────────────────────────────────────────────────────  │
│  "Is latency increasing?"          → Custom Metrics (_drift_metrics)│
│  "Query performance trend"         → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "List slow queries today"         → TVF (get_slow_queries)      │
│  "Underutilized clusters"          → TVF (get_underutilized_clusters)│
│  "Queries with high spill"         → TVF (get_high_spill_queries)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Current P95/P99 latency** | Metric View | "Query latency" → `query_performance` |
| **Latency trend** | Custom Metrics | "Is latency degrading?" → `_drift_metrics` |
| **List of slow queries** | TVF | "Slow queries >30s" → `get_slow_queries` |
| **Right-sizing recs** | TVF/ML | "Cluster recommendations" → `get_cluster_rightsizing` |
| **Optimization suggestions** | ML Tables | "Optimize queries" → `query_optimization_recommendations` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for RECOMMENDATION** → TVF or ML Tables

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks performance analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Query Questions:** Use query_performance metric view for dashboard KPIs
3. **Cluster Questions:** Use cluster_utilization or cluster_efficiency for aggregates
4. **TVFs for Lists:** Use TVFs for "slow queries", "underutilized", "spill" queries
5. **Trends:** For "is latency increasing?" check _drift_metrics tables
6. **Date Default:** Queries=last 24h, Clusters=last 7 days
7. **Duration Units:** Queries in seconds, jobs in minutes
8. **Sorting:** Sort by duration DESC for slow queries, cpu ASC for underutilized
9. **Limits:** Top 20 for performance lists
10. **Percentiles:** P50=median, P95=tail, P99=extreme
11. **SLA Threshold:** 60 seconds default, high spill = any spill > 0
12. **ML Optimization:** For "optimize queries" → query query_optimization_recommendations
13. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
14. **Synonyms:** query=statement=SQL, cluster=compute, warehouse=endpoint
15. **Performance:** Never scan Bronze/Silver tables
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

## ████ SECTION G: ML MODEL INTEGRATION (7 Models) ████

### Performance ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `query_performance_forecaster` | `query_optimization_recommendations` | `predicted_p99_ms` | "Predict query latency" |
| `warehouse_optimizer` | `cluster_capacity_recommendations` | `size_recommendation` | "Optimal warehouse size" |
| `cache_hit_predictor` | `cache_hit_predictions` | `cache_hit_probability` | "Will cache hit?" |
| `query_optimization_recommender` | `query_optimization_classifications` | `optimization_flags` | "How to optimize?" |
| `cluster_sizing_recommender` | `cluster_rightsizing_recommendations` | `recommended_action`, `potential_savings` | "Right-size clusters" |
| `cluster_capacity_planner` | `cluster_capacity_recommendations` | `predicted_peak_utilization` | "Capacity planning" |
| `regression_detector` | — | `regression_score`, `is_regression` | "Performance regression?" |

### ML Model Usage Patterns

#### query_optimization_recommender (Optimization Suggestions)
- **Question Triggers:** "how to optimize", "improve query", "optimization suggestions", "tune query"
- **Query Pattern:**
```sql
SELECT query_id, statement_text, 
       needs_partition_pruning, needs_caching, needs_join_reorder,
       estimated_improvement_pct
FROM ${catalog}.${gold_schema}.query_optimization_classifications
WHERE optimization_flags > 0
ORDER BY estimated_improvement_pct DESC
LIMIT 20;
```

#### cluster_rightsizing_recommendations (Right-Sizing)
- **Question Triggers:** "right-size", "optimize cluster", "savings", "too big", "too small"
- **Query Pattern:**
```sql
SELECT cluster_name, current_size, recommended_size, 
       recommended_action, potential_savings_usd
FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations
WHERE recommended_action != 'NO_CHANGE'
ORDER BY potential_savings_usd DESC;
```

#### cache_hit_predictor (Cache Efficiency)
- **Question Triggers:** "cache", "cache hit", "caching", "result cache"
- **Query Pattern:**
```sql
SELECT warehouse_id, predicted_cache_hit_rate,
       cache_optimization_potential
FROM ${catalog}.${gold_schema}.cache_hit_predictions
ORDER BY cache_optimization_potential DESC;
```

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"How to optimize queries?"              → ML: query_optimization_classifications
"Right-size our clusters"               → ML: cluster_rightsizing_recommendations
"Predict cache performance"             → ML: cache_hit_predictions
"Capacity planning"                     → ML: cluster_capacity_recommendations
────────────────────────────────────────────────────
"What is P95 latency?"                  → Metric View: query_performance
"Is latency trending up?"               → Custom Metrics: _drift_metrics
"Show slow queries"                     → TVF: get_slow_queries
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

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

---

## References

### 📊 Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - **START HERE**: Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### 📈 Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Query and Cluster Monitors
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 80+ performance-specific custom metrics

### 📁 Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 16 Performance TVFs (Query + Cluster)
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 3 Performance Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 7 Performance ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting

