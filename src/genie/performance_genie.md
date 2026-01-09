# Performance Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Performance Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks query and cluster performance analytics. Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, cluster efficiency, and right-sizing opportunities without SQL.

**Powered by:**
- 3 Metric Views (query_performance, cluster_utilization, cluster_efficiency)
- 21 Table-Valued Functions (10 query analysis, 11 cluster utilization)
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

### Table-Valued Functions (21 TVFs)

#### Query TVFs (10)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_slow_queries` | Queries exceeding threshold | "slow queries" |
| `get_query_duration_percentiles` | Duration percentiles | "P95 duration", "percentiles" |
| `get_warehouse_utilization` | Warehouse metrics | "warehouse utilization" |
| `get_query_volume_by_hour` | Query volume trends | "query volume" |
| `get_top_query_users` | Top users by query count | "queries by user", "top users" |
| `get_user_query_efficiency` | User-level efficiency | "user efficiency" |
| `get_warehouse_queue_analysis` | Queue time analysis | "queue time", "queueing" |
| `get_failed_queries` | Failed queries | "failed queries", "errors" |
| `get_query_cache_analysis` | Cache effectiveness | "cache hit", "caching" |
| `get_query_spill_analysis` | Memory pressure queries | "spill", "memory issues" |

#### Cluster TVFs (11)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_cluster_resource_utilization` | Cluster resource metrics | "cluster utilization" |
| `get_cluster_efficiency_score` | Detailed efficiency metrics | "efficiency score" |
| `get_idle_clusters` | Underutilized clusters | "underutilized", "wasted capacity" |
| `get_jobs_without_autoscaling` | Jobs missing autoscale | "jobs without autoscaling" |
| `get_jobs_on_old_dbr` | Legacy DBR jobs | "legacy DBR", "old runtime" |
| `get_cluster_cost_analysis` | Cost breakdown by type | "cluster costs", "cost by type" |
| `get_cluster_uptime` | Uptime patterns | "uptime", "cluster hours" |
| `get_autoscaling_events` | Autoscaling events | "scaling events", "autoscale history" |
| `get_cluster_memory_pressure` | Memory pressure detection | "memory issues" |
| `get_cluster_cpu_saturation` | CPU saturation events | "CPU saturation" |
| `get_cluster_node_efficiency` | Per-node efficiency | "node efficiency" |

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
│  "Underutilized clusters"          → TVF (get_idle_clusters)│
│  "Queries with high spill"         → TVF (get_query_spill_analysis)│
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
| **Right-sizing recs** | ML Table | "Cluster recommendations" → `cluster_rightsizing_recommendations` |
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
4. **TVFs for Lists:** Use TVFs with TABLE() wrapper for "slow queries", "underutilized", "spill" queries
5. **Trends:** For "is latency increasing?" check _drift_metrics tables
6. **Date Default:** Queries=last 24h, Clusters=last 7 days
7. **Duration Units:** Queries in seconds, jobs in minutes
8. **Sorting:** Sort by duration DESC for slow queries, cpu ASC for underutilized
9. **Limits:** Top 20 for performance lists
10. **Percentiles:** P50=median, P95=tail, P99=extreme
11. **SLA Threshold:** 60 seconds default, high spill = any spill > 0
12. **ML Tables:** Use ${catalog}.${feature_schema} for ML prediction tables
13. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
14. **Synonyms:** query=statement=SQL, cluster=compute, warehouse=endpoint
15. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### Query TVFs (10 Functions)

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_slow_queries` | `(start_date STRING, end_date STRING, duration_threshold_seconds INT DEFAULT 30, top_n INT DEFAULT 50)` | Slow queries | "slow queries today" |
| `get_query_duration_percentiles` | `(days_back INT, warehouse_filter STRING DEFAULT '%')` | Duration percentiles | "P95 duration" |
| `get_warehouse_utilization` | `(start_date STRING, end_date STRING)` | Warehouse metrics | "warehouse utilization" |
| `get_query_volume_by_hour` | `(start_date STRING, end_date STRING)` | Query volume trends | "query volume" |
| `get_top_query_users` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 20)` | Top users by queries | "top users" |
| `get_user_query_efficiency` | `(start_date STRING, end_date STRING, min_queries INT DEFAULT 10)` | User efficiency | "user efficiency" |
| `get_warehouse_queue_analysis` | `(start_date STRING, end_date STRING)` | Queue time analysis | "queue time" |
| `get_failed_queries` | `(start_date STRING, end_date STRING, workspace_filter STRING DEFAULT NULL)` | Failed queries | "failed queries" |
| `get_query_cache_analysis` | `(start_date STRING, end_date STRING)` | Cache effectiveness | "cache hit rate" |
| `get_query_spill_analysis` | `(start_date STRING, end_date STRING, min_spill_gb DOUBLE DEFAULT 1.0)` | Memory pressure | "spill queries" |

### Cluster TVFs (11 Functions)

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_cluster_resource_utilization` | `(start_date STRING, end_date STRING, cluster_filter STRING DEFAULT '%')` | Cluster metrics | "cluster utilization" |
| `get_cluster_efficiency_score` | `(start_date STRING, end_date STRING, min_hours INT DEFAULT 4)` | Efficiency scores | "efficiency metrics" |
| `get_idle_clusters` | `(start_date STRING, end_date STRING, idle_threshold_pct DOUBLE DEFAULT 20.0)` | Underutilized clusters | "wasted capacity" |
| `get_jobs_without_autoscaling` | `(days_back INT DEFAULT 7)` | Missing autoscale | "no autoscaling" |
| `get_jobs_on_legacy_dbr` | `(days_back INT)` | Legacy DBR jobs | "old DBR versions" |
| `get_cluster_cost_by_type` | `(start_date STRING, end_date STRING)` | Cost by cluster type | "cluster costs" |
| `get_cluster_uptime_analysis` | `(start_date STRING, end_date STRING)` | Uptime patterns | "uptime" |
| `get_cluster_scaling_events` | `(days_back INT)` | Scaling events | "autoscale history" |
| `get_cluster_efficiency_metrics` | `(start_date STRING, end_date STRING)` | Efficiency scores | "efficiency metrics" |
| `get_node_utilization_by_cluster` | `(start_date STRING, end_date STRING)` | Per-node utilization | "node utilization" |

---

## ████ SECTION H: ML MODEL INTEGRATION (7 Models) ████

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
FROM ${catalog}.${feature_schema}.query_optimization_classifications
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
FROM ${catalog}.${feature_schema}.cluster_rightsizing_recommendations
WHERE recommended_action != 'NO_CHANGE'
ORDER BY potential_savings_usd DESC;
```

#### cache_hit_predictor (Cache Efficiency)
- **Question Triggers:** "cache", "cache hit", "caching", "result cache"
- **Query Pattern:**
```sql
SELECT warehouse_id, predicted_cache_hit_rate,
       cache_optimization_potential
FROM ${catalog}.${feature_schema}.cache_hit_predictions
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

## ████ SECTION I: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**
> **Grounded in:** mv_query_performance, mv_cluster_utilization, mv_cluster_efficiency, TVFs, ML Tables

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "What is our average query duration?"
**Expected SQL:**
```sql
SELECT MEASURE(avg_duration_seconds) as avg_sec
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Average query execution time in seconds for last 7 days

---

### Question 2: "Show me query performance by warehouse"
**Expected SQL:**
```sql
SELECT
  warehouse_name,
  MEASURE(avg_duration_seconds) as avg_duration,
  MEASURE(p95_duration_seconds) as p95_duration,
  MEASURE(total_queries) as queries
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY warehouse_name
ORDER BY queries DESC
LIMIT 10;
```
**Expected Result:** Top 10 warehouses by query volume with latency metrics

---

### Question 3: "What is the average CPU utilization?"
**Expected SQL:**
```sql
SELECT MEASURE(avg_cpu_utilization) as cpu_pct
FROM ${catalog}.${gold_schema}.mv_cluster_utilization
WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Average CPU utilization percentage across all clusters

---

### Question 4: "What is the P95 query duration?"
**Expected SQL:**
```sql
SELECT MEASURE(p95_duration_seconds) as p95_sec
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** P95 query latency for SLA tracking

---

### Question 5: "Show me slow queries from today"
**Expected SQL:**
```sql
SELECT * FROM get_slow_queries(
  CURRENT_DATE()::STRING,
  CURRENT_DATE()::STRING,
  30,
  50
))
ORDER BY duration_seconds DESC
LIMIT 20;
```
**Expected Result:** Queries exceeding 30-second threshold with execution details

---

### Question 6: "What is the query cache hit rate?"
**Expected SQL:**
```sql
SELECT MEASURE(cache_hit_rate) as cache_pct
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall cache efficiency percentage

---

### Question 7: "Show me warehouse utilization metrics"
**Expected SQL:**
```sql
SELECT * FROM get_warehouse_utilization(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY query_count DESC
LIMIT 10;
```
**Expected Result:** Warehouse-level query volumes, concurrency, and queue times

---

### Question 8: "Which queries have high disk spill?"
**Expected SQL:**
```sql
SELECT * FROM get_query_spill_analysis(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  1.0
))
ORDER BY spill_bytes DESC
LIMIT 15;
```
**Expected Result:** Memory-pressure queries with spill-to-disk metrics

---

### Question 9: "What is the cluster efficiency score?"
**Expected SQL:**
```sql
SELECT MEASURE(efficiency_score) as efficiency
FROM ${catalog}.${gold_schema}.mv_cluster_efficiency
WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Combined cluster efficiency metric (0-100 scale)

---

### Question 10: "Show me underutilized clusters"
**Expected SQL:**
```sql
SELECT * FROM get_idle_clusters(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  20.0
))
WHERE avg_cpu_pct < 30
ORDER BY potential_savings DESC
LIMIT 15;
```
**Expected Result:** Clusters with low utilization and quantified savings opportunities

---

### Question 11: "What is the SLA breach rate for queries?"
**Expected SQL:**
```sql
SELECT MEASURE(sla_breach_rate) as breach_pct
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Percentage of queries exceeding 60-second SLA

---

### Question 12: "Show me query volume trends"
**Expected SQL:**
```sql
SELECT * FROM get_query_volume_trends(
  (CURRENT_DATE() - INTERVAL 14 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY query_date DESC;
```
**Expected Result:** Daily query counts with user and duration trends

---

### Question 13: "Which clusters are overprovisioned?"
**Expected SQL:**
```sql
SELECT
  cluster_name,
  MEASURE(avg_cpu_utilization) as cpu_pct,
  MEASURE(avg_memory_utilization) as memory_pct,
  MEASURE(potential_savings_pct) as savings_pct
FROM ${catalog}.${gold_schema}.mv_cluster_utilization
WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND provisioning_status = 'OVERPROVISIONED'
GROUP BY cluster_name
ORDER BY savings_pct DESC
LIMIT 10;
```
**Expected Result:** Overprovisioned clusters with sizing recommendations

---

### Question 14: "Show me query latency percentiles by warehouse"
**Expected SQL:**
```sql
SELECT * FROM get_query_duration_percentiles(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY p99_duration DESC
LIMIT 10;
```
**Expected Result:** Detailed percentile breakdown (P50/P90/P95/P99) per warehouse

---

### Question 15: "Which jobs don't have autoscaling enabled?"
**Expected SQL:**
```sql
SELECT * FROM get_jobs_without_autoscaling(30))
ORDER BY estimated_savings DESC
LIMIT 15;
```
**Expected Result:** Jobs with fixed cluster sizes and autoscaling potential

---

### Question 16: "Show me cluster right-sizing recommendations"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${feature_schema}.cluster_rightsizing_recommendations
WHERE recommended_action IN ('DOWNSIZE', 'UPSIZE')
ORDER BY potential_savings_usd DESC
LIMIT 20;
ORDER BY potential_savings DESC
LIMIT 15;
```
**Expected Result:** ML-powered cluster sizing recommendations with cost impact

---

### Question 17: "What queries need optimization based on ML?"
**Expected SQL:**
```sql
SELECT
  query_hash,
  prediction as optimization_score
FROM ${catalog}.${feature_schema}.query_optimization_classifications
WHERE prediction > 0.7
ORDER BY prediction DESC
LIMIT 20;
```
**Expected Result:** Queries flagged for optimization by ML classifier

---

### Question 18: "What is the P99 query duration?"
**Expected SQL:**
```sql
SELECT MEASURE(p99_duration_seconds) as p99_sec
FROM ${catalog}.${gold_schema}.mv_query_performance
WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** P99 query latency for worst-case analysis

---

### Question 19: "Show me query performance drift"
**Expected SQL:**
```sql
SELECT
  window.start AS period_start,
  p95_duration_drift_pct,
  p99_duration_drift_pct,
  query_volume_drift_pct
FROM ${catalog}.${gold_schema}.fact_query_history_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC
LIMIT 10;
```
**Expected Result:** Query performance degradation metrics from Lakehouse Monitoring

---

### Question 20: "Show me cluster utilization by slice"
**Expected SQL:**
```sql
SELECT
  slice_value AS cluster_name,
  AVG(p95_cpu_total_pct) AS avg_p95_cpu,
  SUM(cpu_saturation_hours) AS saturation_hours,
  SUM(cpu_idle_hours) AS idle_hours
FROM ${catalog}.${gold_schema}.fact_node_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'cluster_name'
GROUP BY slice_value
ORDER BY saturation_hours DESC
LIMIT 10;
```
**Expected Result:** Per-cluster resource metrics from Lakehouse Monitoring

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Query performance bottleneck analysis - identify slow queries with spill, low cache hit, and high queue time for optimization prioritization"
**Expected SQL:**
```sql
WITH slow_queries AS (
  SELECT
    warehouse_name,
    statement_type,
    MEASURE(avg_duration_seconds) as avg_duration,
    MEASURE(p95_duration_seconds) as p95_duration,
    MEASURE(total_queries) as query_count
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND query_efficiency_status IN ('SLOW', 'HIGH_QUEUE', 'HIGH_SPILL')
  GROUP BY warehouse_name, statement_type
),
spill_detail AS (
  SELECT
    warehouse_id,
    COUNT(*) as spill_query_count,
    AVG(spill_bytes) as avg_spill_bytes
  FROM get_query_spill_analysis(
    (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
    CURRENT_DATE()::STRING,
    1.0
  ))
  GROUP BY warehouse_id
),
cache_metrics AS (
  SELECT
    warehouse_name,
    MEASURE(cache_hit_rate) as cache_pct
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY warehouse_name
)
SELECT
  sq.warehouse_name,
  sq.statement_type,
  sq.query_count,
  sq.avg_duration,
  sq.p95_duration,
  COALESCE(sd.spill_query_count, 0) as queries_with_spill,
  COALESCE(sd.avg_spill_bytes, 0) / 1024 / 1024 as avg_spill_mb,
  cm.cache_pct,
  CASE
    WHEN sd.spill_query_count > 100 AND cm.cache_pct < 30 THEN 'Critical - Memory & Cache Issues'
    WHEN sq.p95_duration > 60 AND cm.cache_pct < 50 THEN 'High Priority - Cache Optimization'
    WHEN sd.spill_query_count > 50 THEN 'Medium Priority - Memory Tuning'
    ELSE 'Low Priority'
  END as optimization_priority
FROM slow_queries sq
LEFT JOIN spill_detail sd ON sq.warehouse_name = sd.warehouse_id
JOIN cache_metrics cm ON sq.warehouse_name = cm.warehouse_name
WHERE sq.query_count > 10
ORDER BY sq.p95_duration DESC, queries_with_spill DESC
LIMIT 15;
```
**Expected Result:** Multi-dimensional query bottleneck analysis combining latency, spill, and cache metrics for targeted optimization

---

### Question 22: "🔬 DEEP RESEARCH: Cluster resource efficiency with ML right-sizing recommendations - compare actual utilization vs optimal configuration"
**Expected SQL:**
```sql
WITH cluster_actual AS (
  SELECT
    cluster_name,
    MEASURE(avg_cpu_utilization) as actual_cpu,
    MEASURE(avg_memory_utilization) as actual_memory,
    MEASURE(total_node_hours) as node_hours,
    MEASURE(wasted_hours) as wasted_hours
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY cluster_name
),
ml_sizing_recommendations AS (
  SELECT
    c.cluster_name,
    AVG(crr.prediction) as recommended_size_score
  FROM ${catalog}.${feature_schema}.cluster_rightsizing_recommendations crr
  JOIN ${catalog}.${gold_schema}.dim_cluster c ON crr.cluster_id = c.cluster_id
  WHERE crr.utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY c.cluster_name
),
efficiency_metrics AS (
  SELECT
    cluster_name,
    MEASURE(efficiency_score) as efficiency,
    MEASURE(idle_percentage) as idle_pct
  FROM ${catalog}.${gold_schema}.mv_cluster_efficiency
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY cluster_name
)
SELECT
  ca.cluster_name,
  ca.actual_cpu,
  ca.actual_memory,
  ca.node_hours,
  ca.wasted_hours,
  ca.wasted_hours * 100.0 / NULLIF(ca.node_hours, 0) as waste_pct,
  em.efficiency,
  em.idle_pct,
  COALESCE(ml.recommended_size_score, 0) as ml_sizing_score,
  CASE
    WHEN ca.actual_cpu < 20 AND ca.wasted_hours > 100 THEN 'Downsize 50%'
    WHEN ca.actual_cpu < 40 AND ca.wasted_hours > 50 THEN 'Downsize 25%'
    WHEN ca.actual_cpu > 80 AND em.idle_pct < 10 THEN 'Consider Upsize'
    ELSE 'Optimal'
  END as sizing_recommendation,
  ca.wasted_hours * 0.5 as estimated_monthly_savings_hours
FROM cluster_actual ca
JOIN efficiency_metrics em ON ca.cluster_name = em.cluster_name
LEFT JOIN ml_sizing_recommendations ml ON ca.cluster_name = ml.cluster_name
WHERE ca.node_hours > 10
ORDER BY estimated_monthly_savings_hours DESC
LIMIT 15;
```
**Expected Result:** Comprehensive cluster sizing analysis combining utilization metrics, efficiency scores, and ML recommendations with quantified savings

---

### Question 23: "🔬 DEEP RESEARCH: Cross-warehouse query performance comparison - identify performance inconsistencies and migration opportunities"
**Expected SQL:**
```sql
WITH warehouse_metrics AS (
  SELECT
    warehouse_name,
    MEASURE(avg_duration_seconds) as avg_duration,
    MEASURE(p95_duration_seconds) as p95_duration,
    MEASURE(total_queries) as query_count,
    MEASURE(cache_hit_rate) as cache_pct,
    MEASURE(spill_rate) as spill_pct
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY warehouse_name
),
platform_baseline AS (
  SELECT
    AVG(MEASURE(avg_duration_seconds)) as platform_avg_duration,
    AVG(MEASURE(cache_hit_rate)) as platform_avg_cache
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT
  wm.warehouse_name,
  wm.query_count,
  wm.avg_duration,
  wm.p95_duration,
  wm.cache_pct,
  wm.spill_pct,
  pb.platform_avg_duration,
  pb.platform_avg_cache,
  (wm.avg_duration - pb.platform_avg_duration) / NULLIF(pb.platform_avg_duration, 0) * 100 as duration_variance_pct,
  (pb.platform_avg_cache - wm.cache_pct) as cache_gap,
  CASE
    WHEN wm.avg_duration > pb.platform_avg_duration * 1.5 AND wm.cache_pct < pb.platform_avg_cache * 0.5 THEN 'Underperforming - Investigate'
    WHEN wm.spill_pct > 10 THEN 'Memory Pressure - Resize'
    WHEN wm.avg_duration < pb.platform_avg_duration * 0.8 THEN 'Best Practice - Model'
    ELSE 'Normal'
  END as performance_status
FROM warehouse_metrics wm
CROSS JOIN platform_baseline pb
WHERE wm.query_count > 100
ORDER BY duration_variance_pct DESC
LIMIT 15;
```
**Expected Result:** Cross-warehouse performance analysis identifying outliers and best practices for standardization

---

### Question 24: "🔬 DEEP RESEARCH: Query optimization recommendations with ML classification - prioritize queries for manual tuning based on improvement potential"
**Expected SQL:**
```sql
WITH query_candidates AS (
  SELECT
    statement_type,
    COUNT(*) as query_count,
    AVG(MEASURE(avg_duration_seconds)) as avg_duration,
    AVG(MEASURE(spill_rate)) as avg_spill_rate
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND query_efficiency_status IN ('SLOW', 'HIGH_SPILL')
  GROUP BY statement_type
),
ml_query_classifications AS (
  SELECT
    statement_type,
    COUNT(*) as ml_flagged_count,
    AVG(prediction) as avg_optimization_score
  FROM ${catalog}.${feature_schema}.query_optimization_classifications
  WHERE prediction > 0.5
  GROUP BY statement_type
),
ml_sizing_recommendations AS (
  SELECT
    statement_type,
    COUNT(*) as recommendation_count,
    AVG(prediction) as avg_improvement_potential
  FROM ${catalog}.${feature_schema}.query_optimization_recommendations
  WHERE prediction > 0.3
  GROUP BY statement_type
)
SELECT
  qc.statement_type,
  qc.query_count,
  qc.avg_duration,
  qc.avg_spill_rate,
  COALESCE(mo.ml_flagged_count, 0) as ml_flagged,
  COALESCE(mo.avg_optimization_score, 0) as optimization_score,
  COALESCE(mr.recommendation_count, 0) as has_recommendations,
  COALESCE(mr.avg_improvement_potential, 0) as improvement_potential_pct,
  CASE
    WHEN qc.avg_duration > 30 AND mr.avg_improvement_potential > 50 THEN 'High ROI - Optimize Now'
    WHEN mo.ml_flagged_count > 50 THEN 'Medium ROI - Review'
    ELSE 'Low Priority'
  END as optimization_priority
FROM query_candidates qc
LEFT JOIN ml_query_classifications mo ON qc.statement_type = mo.statement_type
LEFT JOIN ml_sizing_recommendations mr ON qc.statement_type = mr.statement_type
ORDER BY improvement_potential_pct DESC, qc.avg_duration DESC
LIMIT 15;
```
**Expected Result:** ML-driven query optimization roadmap with ROI prioritization combining performance metrics and improvement potential

---

### Question 25: "🔬 DEEP RESEARCH: End-to-end performance health dashboard - combine query latency, cluster utilization, cache efficiency, and ML predictions for executive performance review"
**Expected SQL:**
```sql
WITH query_health AS (
  SELECT
    MEASURE(avg_duration_seconds) as avg_query_duration,
    MEASURE(p95_duration_seconds) as p95_query_duration,
    MEASURE(sla_breach_rate) as sla_breach_pct,
    MEASURE(cache_hit_rate) as cache_pct,
    MEASURE(total_queries) as query_volume
  FROM ${catalog}.${gold_schema}.mv_query_performance
  WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
cluster_health AS (
  SELECT
    MEASURE(avg_cpu_utilization) as avg_cpu,
    MEASURE(avg_memory_utilization) as avg_memory,
    MEASURE(efficiency_score) as efficiency,
    MEASURE(wasted_hours) as wasted_hours
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
ml_insights AS (
  SELECT
    COUNT(*) as queries_needing_optimization,
    AVG(prediction) as avg_optimization_potential
  FROM ${catalog}.${feature_schema}.query_optimization_classifications
  WHERE prediction > 0.5
),
drift_status AS (
  SELECT
    AVG(p95_duration_drift_pct) as query_drift,
    AVG(cpu_utilization_drift) as cpu_drift
  FROM ${catalog}.${gold_schema}.fact_query_history_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
)
SELECT
  qh.query_volume,
  qh.avg_query_duration,
  qh.p95_query_duration,
  qh.sla_breach_pct,
  qh.cache_pct,
  ch.avg_cpu,
  ch.avg_memory,
  ch.efficiency,
  ch.wasted_hours,
  mi.queries_needing_optimization,
  mi.avg_optimization_potential,
  ds.query_drift,
  ds.cpu_drift,
  CASE
    WHEN qh.sla_breach_pct > 5 OR ch.efficiency < 50 THEN 'Critical Performance Issues'
    WHEN ds.query_drift > 20 OR ds.cpu_drift > 15 THEN 'Performance Degradation Detected'
    WHEN qh.cache_pct > 80 AND ch.avg_cpu BETWEEN 60 AND 80 THEN 'Optimal Performance'
    ELSE 'Normal'
  END as overall_health_status,
  CASE
    WHEN qh.sla_breach_pct > 5 THEN 'Investigate slow queries immediately'
    WHEN mi.queries_needing_optimization > 100 THEN 'Run ML-recommended optimizations'
    WHEN ch.wasted_hours > 1000 THEN 'Right-size clusters'
    WHEN qh.cache_pct < 50 THEN 'Improve caching strategy'
    ELSE 'Continue monitoring'
  END as recommended_action
FROM query_health qh
CROSS JOIN cluster_health ch
CROSS JOIN ml_insights mi
CROSS JOIN drift_status ds;
```
**Expected Result:** Executive performance dashboard combining all performance dimensions (query, cluster, cache, ML) with health status and prioritized recommendations

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **F. General Instructions** | 15 lines (≤20) | ✅ |
| **G. TVFs** | 21 functions with signatures | ✅ |
| **I. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

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
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 21 Performance TVFs (Query + Cluster)
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 3 Performance Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 7 Performance ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting
