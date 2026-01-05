# Performance Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Performance Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks query and cluster performance analytics. Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, cluster efficiency, and right-sizing opportunities without SQL.

**Powered by:**
- 3 Metric Views (query_performance, cluster_utilization, cluster_efficiency)
- 16 Table-Valued Functions (query analysis, cluster utilization, right-sizing)
- 7 ML Prediction Tables (optimization, capacity planning, right-sizing)
- 4 Lakehouse Monitoring Tables (query and cluster drift/profile metrics)
- 5 Dimension Tables (warehouse, cluster, node_type, workspace, date)
- 3 Fact Tables (query history, warehouse events, node timeline)

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

### ML Prediction Tables 🤖 (7 Models)

| Table Name | Purpose | Model | Key Columns |
|---|---|---|---|
| `query_optimization_classifications` | Queries flagged for optimization (multi-label) | Query Performance Optimizer | `needs_partition_pruning`, `needs_caching`, `needs_broadcast_join`, `optimization_flags` |
| `query_optimization_recommendations` | Specific optimization suggestions | Query Optimization Recommender | `optimization_categories`, `estimated_improvement_pct`, `priority` |
| `cache_hit_predictions` | Cache effectiveness predictions | Cache Hit Predictor | `cache_hit_probability`, `cache_optimization_potential` |
| `job_duration_predictions` | Job completion time estimates with confidence | Job Duration Predictor | `predicted_duration_sec`, `confidence_interval_lower`, `confidence_interval_upper` |
| `cluster_capacity_recommendations` | Optimal cluster capacity planning | Cluster Capacity Planner | `predicted_peak_utilization`, `recommended_nodes`, `scaling_recommendation` |
| `cluster_rightsizing_recommendations` | Right-sizing with savings estimates | Cluster Right-Sizing Recommender | `current_size`, `recommended_size`, `recommended_action`, `potential_savings_usd` |
| `dbr_migration_risk_scores` | DBR migration risk assessment | DBR Migration Risk Scorer | `risk_level`, `risk_score`, `migration_recommendation`, `testing_requirements` |

**Training Source:** `src/ml/performance/` | **Inference:** `src/ml/inference/batch_inference_all_models.py`

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

### Dimension Tables (5 Tables)

**Sources:** `gold_layer_design/yaml/compute/`, `query_performance/`, `shared/`

| Table Name | Purpose | Key Columns | YAML Source |
|---|---|---|---|
| `dim_warehouse` | Warehouse metadata | `warehouse_id`, `warehouse_name`, `cluster_size`, `warehouse_type` | query_performance/dim_warehouse.yaml |
| `dim_cluster` | Cluster metadata | `cluster_id`, `cluster_name`, `node_type_id`, `dbr_version`, `autoscale_config` | compute/dim_cluster.yaml |
| `dim_node_type` | Node type specs | `node_type_id`, `vcpus`, `memory_mb`, `hourly_dbu_rate` | compute/dim_node_type.yaml |
| `dim_workspace` | Workspace reference | `workspace_id`, `workspace_name`, `region`, `cloud_provider` | shared/dim_workspace.yaml |
| `dim_date` | Date dimension for time analysis | `date_key`, `day_of_week`, `month`, `quarter`, `year`, `is_weekend` | shared/dim_date.yaml |

### Fact Tables (from gold_layer_design/yaml/compute/, query_performance/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_query_history` | Query execution history | Per query | query_performance/fact_query_history.yaml |
| `fact_warehouse_events` | Warehouse lifecycle events | Per event | query_performance/fact_warehouse_events.yaml |
| `fact_node_timeline` | Node utilization metrics | Per node per minute | compute/fact_node_timeline.yaml |

### Data Model Relationships 🔗

**Foreign Key Constraints** (extracted from `gold_layer_design/yaml/`)

| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_query_history` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_query_history` | → | `dim_warehouse` | `(workspace_id, warehouse_id)` = `(workspace_id, warehouse_id)` | LEFT |
| `fact_warehouse_events` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_warehouse_events` | → | `dim_warehouse` | `(workspace_id, warehouse_id)` = `(workspace_id, warehouse_id)` | LEFT |
| `fact_node_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_node_timeline` | → | `dim_cluster` | `(workspace_id, cluster_id)` = `(workspace_id, cluster_id)` | LEFT |
| `fact_node_timeline` | → | `dim_node_type` | `node_type_id` = `node_type_id` | LEFT |

**Join Patterns:**
- **Single Key:** `ON fact.key = dim.key`
- **Composite Key (workspace-scoped):** `ON fact.workspace_id = dim.workspace_id AND fact.fk = dim.pk`

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

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

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

### Question 11: "Show me queries with high spill"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_high_spill_queries(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY spill_to_disk_bytes DESC
LIMIT 20;
```
**Expected Result:** Queries with memory pressure issues

---

### Question 12: "What is the query volume trend?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_query_volume_trends(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY query_date;
```
**Expected Result:** Daily query volume over 30 days

---

### Question 13: "Show me failed queries today"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_queries(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY execution_time DESC
LIMIT 20;
```
**Expected Result:** Failed queries with error details

---

### Question 14: "What is the cache hit rate by warehouse?"
**Expected SQL:**
```sql
SELECT 
  warehouse_id,
  MEASURE(cache_hit_rate) as cache_hit_rate
FROM ${catalog}.${gold_schema}.query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY warehouse_id
ORDER BY cache_hit_rate ASC;
```
**Expected Result:** Cache performance by warehouse

---

### Question 15: "Show me cluster capacity recommendations"
**Expected SQL:**
```sql
SELECT 
  cluster_id,
  cluster_name,
  predicted_peak_utilization,
  recommended_nodes,
  scaling_recommendation
FROM ${catalog}.${gold_schema}.cluster_capacity_recommendations
ORDER BY predicted_peak_utilization DESC
LIMIT 20;
```
**Expected Result:** Capacity planning recommendations

---

### Question 16: "What is the SLA breach rate?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(sla_breach_rate) as sla_breach_rate,
  MEASURE(total_queries) as total_queries
FROM ${catalog}.${gold_schema}.query_performance
WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** SLA breach percentage

---

### Question 17: "Show me jobs on legacy DBR versions"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_jobs_on_legacy_dbr(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY dbr_version ASC
LIMIT 20;
```
**Expected Result:** Jobs needing DBR upgrade

---

### Question 18: "What is the DBR migration risk?"
**Expected SQL:**
```sql
SELECT 
  cluster_name,
  current_dbr,
  risk_level,
  risk_score,
  migration_recommendation
FROM ${catalog}.${gold_schema}.dbr_migration_risk_scores
WHERE risk_level IN ('HIGH', 'MEDIUM')
ORDER BY risk_score DESC
LIMIT 20;
```
**Expected Result:** DBR upgrade risk assessment

---

### Question 19: "Show me query performance by user"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_user_query_summary(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY total_query_time DESC
LIMIT 20;
```
**Expected Result:** Query metrics by user

---

### Question 20: "What is the memory utilization by cluster?"
**Expected SQL:**
```sql
SELECT 
  cluster_name,
  MEASURE(avg_memory_utilization) as avg_memory_pct,
  MEASURE(p95_memory_utilization) as p95_memory_pct
FROM ${catalog}.${gold_schema}.cluster_utilization
WHERE metric_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY cluster_name
ORDER BY avg_memory_pct DESC
LIMIT 20;
```
**Expected Result:** Memory usage by cluster

---

### 🔬 DEEP RESEARCH QUESTIONS (Complex Multi-Source Analysis)

### Question 21: "Which queries are causing the most resource contention, and what would be the cluster-wide performance improvement if we applied all ML-recommended optimizations?"
**Deep Research Complexity:** Combines query resource analysis, contention detection, ML optimization recommendations, and projected improvement estimation.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify high-resource queries causing contention
WITH resource_heavy_queries AS (
  SELECT 
    query_id,
    warehouse_id,
    statement_type,
    total_duration_ms,
    spill_to_disk_bytes,
    rows_produced,
    bytes_scanned,
    CASE 
      WHEN spill_to_disk_bytes > 0 THEN 'MEMORY_PRESSURE'
      WHEN total_duration_ms > 300000 THEN 'LONG_RUNNING'
      WHEN bytes_scanned > 10737418240 THEN 'LARGE_SCAN' -- 10GB
      ELSE 'NORMAL'
    END as contention_type
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND execution_status = 'FINISHED'
),
-- Step 2: Aggregate contention by warehouse
warehouse_contention AS (
  SELECT 
    warehouse_id,
    COUNT(*) as total_queries,
    SUM(CASE WHEN contention_type != 'NORMAL' THEN 1 ELSE 0 END) as contention_queries,
    SUM(CASE WHEN contention_type = 'MEMORY_PRESSURE' THEN 1 ELSE 0 END) as memory_pressure_count,
    SUM(CASE WHEN contention_type = 'LONG_RUNNING' THEN 1 ELSE 0 END) as long_running_count,
    AVG(total_duration_ms) as avg_duration_ms
  FROM resource_heavy_queries
  GROUP BY warehouse_id
),
-- Step 3: Get ML optimization recommendations
ml_optimizations AS (
  SELECT 
    query_id,
    needs_partition_pruning,
    needs_caching,
    needs_broadcast_join,
    estimated_improvement_pct
  FROM ${catalog}.${gold_schema}.query_optimization_classifications
  WHERE estimated_improvement_pct > 0
),
-- Step 4: Calculate projected improvements
projected_improvements AS (
  SELECT 
    r.warehouse_id,
    COUNT(DISTINCT m.query_id) as optimizable_queries,
    AVG(m.estimated_improvement_pct) as avg_improvement_pct,
    SUM(r.total_duration_ms * m.estimated_improvement_pct / 100) as projected_time_savings_ms
  FROM resource_heavy_queries r
  JOIN ml_optimizations m ON r.query_id = m.query_id
  GROUP BY r.warehouse_id
)
SELECT 
  wc.warehouse_id,
  wc.total_queries,
  wc.contention_queries,
  ROUND(wc.contention_queries * 100.0 / wc.total_queries, 1) as contention_rate_pct,
  wc.memory_pressure_count,
  wc.long_running_count,
  wc.avg_duration_ms / 1000 as avg_duration_sec,
  COALESCE(pi.optimizable_queries, 0) as queries_with_ml_recommendations,
  COALESCE(pi.avg_improvement_pct, 0) as avg_predicted_improvement_pct,
  COALESCE(pi.projected_time_savings_ms / 1000 / 60, 0) as projected_time_savings_minutes,
  CASE 
    WHEN wc.contention_queries > 100 AND pi.avg_improvement_pct > 30 THEN '🔴 HIGH IMPACT - OPTIMIZE IMMEDIATELY'
    WHEN wc.contention_queries > 50 OR pi.avg_improvement_pct > 20 THEN '🟠 MEDIUM IMPACT - PRIORITIZE'
    ELSE '🟢 LOW IMPACT - MONITOR'
  END as optimization_priority
FROM warehouse_contention wc
LEFT JOIN projected_improvements pi ON wc.warehouse_id = pi.warehouse_id
ORDER BY wc.contention_queries DESC
LIMIT 10;
```
**Expected Result:** Warehouse-level contention analysis with ML-predicted performance improvements from applying optimizations.

---

### Question 22: "What is the correlation between cluster underutilization and query queue times, and what right-sizing changes would improve both cost efficiency and query performance?"
**Deep Research Complexity:** Combines utilization analysis, queue time correlation, right-sizing recommendations, and dual-optimization (cost + performance) assessment.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Get cluster utilization metrics
WITH cluster_utilization AS (
  SELECT 
    cluster_id,
    cluster_name,
    AVG(cpu_utilization_pct) as avg_cpu_util,
    AVG(memory_utilization_pct) as avg_memory_util,
    SUM(CASE WHEN cpu_utilization_pct < 30 THEN uptime_hours ELSE 0 END) as idle_hours,
    SUM(uptime_hours) as total_hours
  FROM ${catalog}.${gold_schema}.fact_node_timeline
  WHERE metric_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY cluster_id, cluster_name
),
-- Step 2: Get warehouse queue times (warehouses often run on clusters)
queue_analysis AS (
  SELECT 
    compute_warehouse_id as warehouse_id,
    AVG(queue_time_ms) as avg_queue_time_ms,
    PERCENTILE(queue_time_ms, 0.95) as p95_queue_time_ms,
    COUNT(*) as total_queries,
    SUM(CASE WHEN queue_time_ms > 5000 THEN 1 ELSE 0 END) as queries_with_wait
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY compute_warehouse_id
),
-- Step 3: Get ML right-sizing recommendations
rightsizing AS (
  SELECT 
    cluster_id,
    cluster_name,
    current_size,
    recommended_size,
    recommended_action,
    potential_savings_usd
  FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations
),
-- Step 4: Correlate underutilization with queue times
correlation_analysis AS (
  SELECT 
    cu.cluster_name,
    cu.avg_cpu_util,
    cu.idle_hours,
    cu.total_hours,
    cu.idle_hours / cu.total_hours * 100 as idle_pct,
    qa.avg_queue_time_ms,
    qa.p95_queue_time_ms,
    qa.queries_with_wait,
    CASE 
      WHEN cu.avg_cpu_util < 30 AND qa.avg_queue_time_ms < 1000 THEN 'OVERPROVISIONED_NO_QUEUE'
      WHEN cu.avg_cpu_util < 30 AND qa.avg_queue_time_ms >= 1000 THEN 'MISCONFIGURED_IDLE_BUT_QUEUING'
      WHEN cu.avg_cpu_util >= 70 AND qa.avg_queue_time_ms >= 5000 THEN 'UNDERPROVISIONED_HIGH_QUEUE'
      ELSE 'BALANCED'
    END as utilization_queue_pattern
  FROM cluster_utilization cu
  LEFT JOIN queue_analysis qa ON cu.cluster_name LIKE CONCAT('%', qa.warehouse_id, '%')
)
SELECT 
  ca.cluster_name,
  ROUND(ca.avg_cpu_util, 1) as avg_cpu_util_pct,
  ROUND(ca.idle_pct, 1) as idle_time_pct,
  ROUND(ca.avg_queue_time_ms / 1000, 2) as avg_queue_time_sec,
  ROUND(ca.p95_queue_time_ms / 1000, 2) as p95_queue_time_sec,
  ca.utilization_queue_pattern,
  rs.current_size,
  rs.recommended_size,
  rs.recommended_action,
  rs.potential_savings_usd,
  CASE ca.utilization_queue_pattern
    WHEN 'OVERPROVISIONED_NO_QUEUE' THEN '💰 DOWNSIZE: Save $' || ROUND(rs.potential_savings_usd) || ' with no performance impact'
    WHEN 'MISCONFIGURED_IDLE_BUT_QUEUING' THEN '⚙️ RECONFIGURE: Autoscaling or concurrency settings issue'
    WHEN 'UNDERPROVISIONED_HIGH_QUEUE' THEN '⬆️ UPSIZE: Performance suffering, consider larger cluster'
    ELSE '✅ OPTIMAL: Current sizing is appropriate'
  END as optimization_recommendation
FROM correlation_analysis ca
LEFT JOIN rightsizing rs ON ca.cluster_name = rs.cluster_name
ORDER BY rs.potential_savings_usd DESC NULLS LAST
LIMIT 15;
```
**Expected Result:** Correlation analysis between utilization and queue times, with specific right-sizing recommendations that balance cost and performance.

---

### Question 23: "What's the total platform performance debt - cumulative slow query time, suboptimal cluster configurations, and missed optimization opportunities - and what's the prioritized remediation plan?"
**Deep Research Complexity:** Aggregates all performance inefficiencies across queries, clusters, and warehouses to quantify total performance debt and prioritize improvements.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Calculate query performance debt
WITH query_debt AS (
  SELECT 
    'Query Optimization' as debt_category,
    COUNT(*) as items,
    SUM(CASE WHEN duration_ms > 30000 THEN duration_ms - 30000 ELSE 0 END) / 1000.0 as excess_duration_seconds,
    SUM(CASE WHEN total_bytes_spilled > 0 THEN total_bytes_spilled ELSE 0 END) / 1e9 as spill_gb,
    COUNT(CASE WHEN total_bytes_spilled > 1e9 THEN 1 END) as high_spill_queries,
    SUM(CASE WHEN rows_produced_per_second_scanned < 1000 THEN 1 ELSE 0 END) as inefficient_scan_queries
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
-- Step 2: Calculate cluster configuration debt
cluster_debt AS (
  SELECT 
    'Cluster Configuration' as debt_category,
    COUNT(*) as items,
    SUM(CASE WHEN cpu_percent < 30 THEN (30 - cpu_percent) * duration_hours ELSE 0 END) as underutilization_hours,
    SUM(CASE WHEN memory_percent > 90 THEN (memory_percent - 90) * duration_hours ELSE 0 END) as overcommit_hours,
    COUNT(CASE WHEN autoscale_enabled = FALSE AND worker_count > 2 THEN 1 END) as no_autoscale_fixed_clusters
  FROM ${catalog}.${gold_schema}.fact_node_timeline
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
-- Step 3: Calculate warehouse debt
warehouse_debt AS (
  SELECT 
    'Warehouse Configuration' as debt_category,
    COUNT(DISTINCT warehouse_id) as items,
    SUM(CASE WHEN avg_queue_time_ms > 5000 THEN avg_queue_time_ms - 5000 ELSE 0 END) / 1000.0 as excess_queue_seconds,
    COUNT(CASE WHEN num_queued_queries > 10 THEN 1 END) as high_queue_events,
    SUM(CASE WHEN cluster_count > 1 AND active_queries < cluster_count THEN cluster_count - active_queries ELSE 0 END) as wasted_cluster_capacity
  FROM ${catalog}.${gold_schema}.fact_warehouse_events
  WHERE event_time >= CURRENT_DATE() - INTERVAL 30 DAYS
),
-- Step 4: Get ML optimization potential
optimization_potential AS (
  SELECT 
    SUM(potential_improvement_pct) as total_improvement_potential,
    COUNT(*) as actionable_recommendations,
    SUM(CASE WHEN confidence > 0.8 THEN 1 ELSE 0 END) as high_confidence_recs
  FROM ${catalog}.${gold_schema}.query_optimization_recommendations
  WHERE recommendation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 5: Summarize total debt
debt_summary AS (
  SELECT 
    debt_category,
    items,
    excess_duration_seconds / 3600.0 as performance_debt_hours,
    CAST(NULL AS DOUBLE) as efficiency_debt_score
  FROM query_debt
  UNION ALL
  SELECT 
    debt_category,
    items,
    underutilization_hours as performance_debt_hours,
    overcommit_hours as efficiency_debt_score
  FROM cluster_debt
  UNION ALL
  SELECT 
    debt_category,
    items,
    excess_queue_seconds / 3600.0 as performance_debt_hours,
    wasted_cluster_capacity as efficiency_debt_score
  FROM warehouse_debt
)
SELECT 
  debt_category,
  items as affected_items,
  ROUND(performance_debt_hours, 1) as wasted_hours_30d,
  ROUND(performance_debt_hours * 50, 2) as estimated_cost_impact_usd,  -- $50/hour estimate
  CASE 
    WHEN performance_debt_hours > 100 THEN '🔴 HIGH DEBT: Immediate optimization needed'
    WHEN performance_debt_hours > 50 THEN '🟠 MEDIUM DEBT: Schedule optimization sprint'
    ELSE '🟢 LOW DEBT: Continuous improvement'
  END as debt_severity,
  CASE debt_category
    WHEN 'Query Optimization' THEN 'Run query analyzer, add caching, optimize joins'
    WHEN 'Cluster Configuration' THEN 'Enable autoscaling, right-size instances'
    ELSE 'Tune warehouse concurrency, add auto-resume'
  END as remediation_action
FROM debt_summary
ORDER BY performance_debt_hours DESC;
```
**Expected Result:** Total performance debt quantified across queries, clusters, and warehouses with estimated cost impact and prioritized remediation plan.

---

### Question 24: "Which users or teams are experiencing the worst performance degradation over the past month, and what specific resources or configurations are causing their bottlenecks?"
**Deep Research Complexity:** Combines user-level performance trending, bottleneck attribution, and resource contention analysis to identify and diagnose user-specific performance issues.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Calculate user performance trends
WITH user_performance_baseline AS (
  SELECT 
    executed_by as user_identity,
    DATE_TRUNC('week', execution_date) as week,
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE(duration_ms, 0.95) as p95_duration_ms,
    COUNT(*) as query_count,
    SUM(total_bytes_read) / 1e9 as data_scanned_gb
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY executed_by, DATE_TRUNC('week', execution_date)
),
-- Step 2: Calculate week-over-week performance change
performance_trends AS (
  SELECT 
    user_identity,
    MAX(CASE WHEN week = DATE_TRUNC('week', CURRENT_DATE()) THEN avg_duration_ms END) as current_week_avg,
    MAX(CASE WHEN week = DATE_TRUNC('week', CURRENT_DATE() - INTERVAL 7 DAYS) THEN avg_duration_ms END) as prev_week_avg,
    MAX(CASE WHEN week = DATE_TRUNC('week', CURRENT_DATE()) THEN p95_duration_ms END) as current_p95,
    MAX(CASE WHEN week = DATE_TRUNC('week', CURRENT_DATE() - INTERVAL 7 DAYS) THEN p95_duration_ms END) as prev_p95,
    SUM(query_count) as total_queries
  FROM user_performance_baseline
  GROUP BY user_identity
),
-- Step 3: Identify bottleneck resources per user
bottleneck_analysis AS (
  SELECT 
    executed_by as user_identity,
    compute_warehouse_id as primary_warehouse,
    AVG(CASE WHEN total_bytes_spilled > 0 THEN 1 ELSE 0 END) * 100 as spill_rate_pct,
    AVG(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100 as failure_rate_pct,
    AVG(queue_time_ms) as avg_queue_time_ms,
    MODE(cluster_name) as most_used_cluster,
    COUNT(DISTINCT cluster_name) as clusters_used
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY executed_by, compute_warehouse_id
),
-- Step 4: Identify resource contention
resource_contention AS (
  SELECT 
    executed_by as user_identity,
    COUNT(*) as contention_events,
    AVG(TIMESTAMPDIFF(SECOND, queue_start_time, execution_start_time)) as avg_wait_seconds
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE queue_time_ms > 5000  -- Queued for more than 5 seconds
    AND execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY executed_by
)
SELECT 
  t.user_identity,
  t.total_queries,
  ROUND(t.current_week_avg / 1000.0, 2) as current_avg_duration_sec,
  ROUND(t.prev_week_avg / 1000.0, 2) as prev_week_avg_sec,
  ROUND((t.current_week_avg - COALESCE(t.prev_week_avg, t.current_week_avg)) / NULLIF(t.prev_week_avg, 0) * 100, 1) as duration_change_pct,
  ROUND(t.current_p95 / 1000.0, 2) as current_p95_sec,
  b.primary_warehouse,
  ROUND(b.spill_rate_pct, 1) as memory_spill_rate_pct,
  ROUND(b.failure_rate_pct, 1) as query_failure_rate_pct,
  ROUND(b.avg_queue_time_ms / 1000.0, 2) as avg_queue_time_sec,
  COALESCE(c.contention_events, 0) as queue_contention_events,
  CASE 
    WHEN (t.current_week_avg - COALESCE(t.prev_week_avg, t.current_week_avg)) / NULLIF(t.prev_week_avg, 0) > 0.5 THEN '🔴 SIGNIFICANT DEGRADATION'
    WHEN (t.current_week_avg - COALESCE(t.prev_week_avg, t.current_week_avg)) / NULLIF(t.prev_week_avg, 0) > 0.2 THEN '🟠 MODERATE DEGRADATION'
    WHEN (t.current_week_avg - COALESCE(t.prev_week_avg, t.current_week_avg)) / NULLIF(t.prev_week_avg, 0) < -0.1 THEN '🟢 IMPROVED'
    ELSE '🟡 STABLE'
  END as performance_trend,
  CASE 
    WHEN b.spill_rate_pct > 30 THEN 'MEMORY: High spill rate - increase cluster memory'
    WHEN c.contention_events > 20 THEN 'CONTENTION: High queue times - scale warehouse'
    WHEN b.failure_rate_pct > 10 THEN 'RELIABILITY: High failure rate - review query patterns'
    WHEN b.avg_queue_time_ms > 10000 THEN 'QUEUE: Long wait times - add warehouse capacity'
    ELSE 'OPTIMIZE: Review specific slow queries'
  END as bottleneck_diagnosis
FROM performance_trends t
LEFT JOIN bottleneck_analysis b ON t.user_identity = b.user_identity
LEFT JOIN resource_contention c ON t.user_identity = c.user_identity
WHERE t.total_queries > 10  -- Filter out inactive users
ORDER BY (t.current_week_avg - COALESCE(t.prev_week_avg, t.current_week_avg)) / NULLIF(t.prev_week_avg, 0) DESC
LIMIT 20;
```
**Expected Result:** Users with performance degradation including trend analysis, specific bottleneck diagnosis, and recommended remediation per user.

---

### Question 25: "What's the optimal cache strategy for our workload based on query patterns, data access frequency, and cache hit analysis, and what would be the performance impact of implementing it?"
**Deep Research Complexity:** Analyzes query patterns, data access frequency, current cache utilization, and ML cache predictions to recommend optimal caching strategy with projected impact.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Analyze query repeatability (cache candidates)
WITH query_patterns AS (
  SELECT 
    statement_id,
    query_hash,
    COUNT(*) as execution_count,
    AVG(duration_ms) as avg_duration_ms,
    SUM(total_bytes_read) / COUNT(*) as avg_bytes_per_query,
    AVG(CASE WHEN cache_hit THEN 1 ELSE 0 END) * 100 as current_cache_hit_rate
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY statement_id, query_hash
  HAVING COUNT(*) > 5  -- Repeated queries
),
-- Step 2: Analyze data access patterns
data_access AS (
  SELECT 
    source_table,
    COUNT(*) as access_count,
    COUNT(DISTINCT executed_by) as unique_users,
    COUNT(DISTINCT DATE_TRUNC('hour', execution_date)) as active_hours,
    AVG(total_bytes_read) / 1e9 as avg_data_read_gb
  FROM ${catalog}.${gold_schema}.fact_query_history q
  JOIN ${catalog}.${gold_schema}.fact_table_lineage l ON q.statement_id = l.statement_id
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND l.event_type = 'READ'
  GROUP BY source_table
),
-- Step 3: Get ML cache predictions
cache_predictions AS (
  SELECT 
    query_pattern,
    predicted_cache_hit_rate,
    recommended_cache_policy,
    expected_performance_improvement_pct
  FROM ${catalog}.${gold_schema}.cache_hit_predictions
  WHERE prediction_date = CURRENT_DATE()
),
-- Step 4: Calculate cache strategy metrics
cache_strategy AS (
  SELECT 
    'RESULT_CACHE' as cache_type,
    COUNT(CASE WHEN p.execution_count > 10 AND p.current_cache_hit_rate < 50 THEN 1 END) as cacheable_queries,
    SUM(CASE WHEN p.execution_count > 10 AND p.current_cache_hit_rate < 50 
        THEN p.avg_duration_ms * p.execution_count END) / 1000.0 as potential_time_saved_seconds,
    'Enable result caching for repeated analytical queries' as recommendation
  FROM query_patterns p
  UNION ALL
  SELECT 
    'DATA_CACHE' as cache_type,
    COUNT(CASE WHEN access_count > 20 AND unique_users > 3 THEN 1 END) as cacheable_tables,
    SUM(CASE WHEN access_count > 20 THEN avg_data_read_gb * access_count * 0.3 END) as potential_io_saved_gb,
    'Enable SSD caching for frequently accessed tables' as recommendation
  FROM data_access
  UNION ALL
  SELECT 
    'DELTA_CACHE' as cache_type,
    COUNT(*) as hot_tables,
    SUM(avg_data_read_gb * access_count * 0.5) as potential_io_saved_gb,
    'Pre-warm Delta cache for hot data' as recommendation
  FROM data_access
  WHERE access_count > 100
),
-- Step 5: Project performance impact
performance_projection AS (
  SELECT 
    'CURRENT' as scenario,
    AVG(duration_ms) / 1000.0 as avg_query_duration_sec,
    AVG(CASE WHEN cache_hit THEN 1 ELSE 0 END) * 100 as cache_hit_rate_pct,
    SUM(total_bytes_read) / 1e12 as total_data_read_tb
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  UNION ALL
  SELECT 
    'PROJECTED' as scenario,
    AVG(duration_ms) * 0.6 / 1000.0 as avg_query_duration_sec,  -- 40% improvement estimate
    75.0 as cache_hit_rate_pct,  -- Target 75% cache hit
    SUM(total_bytes_read) * 0.5 / 1e12 as total_data_read_tb  -- 50% IO reduction
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT 
  s.cache_type,
  s.cacheable_queries as cache_candidates,
  ROUND(s.potential_time_saved_seconds / 3600, 1) as potential_hours_saved_30d,
  s.recommendation,
  CASE 
    WHEN s.cache_type = 'RESULT_CACHE' AND s.potential_time_saved_seconds > 10000 THEN '🔴 HIGH IMPACT: Enable immediately'
    WHEN s.cache_type = 'DATA_CACHE' AND s.cacheable_queries > 50 THEN '🟠 MEDIUM IMPACT: Plan implementation'
    ELSE '🟢 LOW IMPACT: Nice to have'
  END as priority,
  CASE s.cache_type
    WHEN 'RESULT_CACHE' THEN 'SET spark.databricks.io.cache.enabled = true'
    WHEN 'DATA_CACHE' THEN 'ALTER TABLE SET TBLPROPERTIES ("delta.dataSkippingNumIndexedCols" = 32)'
    ELSE 'dbutils.fs.cache(path) for hot datasets'
  END as implementation_command
FROM cache_strategy s
ORDER BY potential_time_saved_seconds DESC NULLS LAST;
```
**Expected Result:** Cache strategy analysis showing cache type recommendations, potential performance improvements, implementation commands, and prioritized action plan.

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
| **H. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

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

