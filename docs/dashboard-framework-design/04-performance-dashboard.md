# Performance Dashboard Specification

## Overview

**Purpose:** Query performance analytics, cluster utilization, resource optimization, and DBR migration tracking for the Databricks platform.

**Existing Dashboards to Consolidate:**
- `query_performance.lvdash.json` (23 datasets)
- `cluster_utilization.lvdash.json` (23 datasets)
- `dbr_migration.lvdash.json` (6 datasets)
- `job_optimization.lvdash.json` (7 datasets)

**Target Dataset Count:** ~80 datasets (within 100 limit after consolidation)

---

## Page Structure

### Page 1: Performance Overview (Overview Page for Unified)
**Purpose:** Executive summary of performance health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Queries (24h) | KPI | ds_kpi_queries | Monitor: total_queries |
| P95 Duration (s) | KPI | ds_kpi_p95 | Monitor: p95_duration_seconds |
| Query Success Rate | KPI | ds_kpi_success | Monitor: query_success_rate |
| Cluster Utilization | KPI | ds_kpi_utilization | Monitor: cluster_utilization_pct |
| Query Duration Trend | Line | ds_query_trend | - |
| Performance Regressions | Table | ds_ml_regressions | ML: regression_detector |

### Page 2: Query Performance
**Purpose:** Detailed query analytics

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Query Duration Distribution | Histogram | ds_query_dist | - |
| P50/P95/P99 Trend | Line | ds_percentile_trend | Monitor: p50, p95, p99 |
| Top Slow Queries | Table | ds_slow_queries | - |
| Queries by Status | Pie | ds_query_status | - |
| Query Forecasts | Table | ds_ml_query_forecast | ML: query_performance_forecaster |
| Cache Hit Rate | KPI | ds_cache_hit | ML: cache_hit_predictor |

### Page 3: Query Optimization
**Purpose:** Query tuning recommendations

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Optimization Candidates | Table | ds_ml_query_opt | ML: query_optimization_recommender |
| Query Patterns | Table | ds_query_patterns | - |
| Warehouse Recommendations | Table | ds_ml_warehouse_opt | ML: warehouse_optimizer |
| Spilling Queries | Table | ds_spilling_queries | - |
| Long Running Queries | Table | ds_long_queries | - |
| Query Cost Estimate | KPI | ds_query_cost | - |

### Page 4: Cluster Utilization
**Purpose:** Cluster resource utilization

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| CPU Utilization | Gauge | ds_cpu_util | Monitor: avg_cpu_utilization |
| Memory Utilization | Gauge | ds_memory_util | Monitor: avg_memory_utilization |
| Cluster Uptime | KPI | ds_uptime | Monitor: total_cluster_hours |
| Idle Cluster Hours | KPI | ds_idle_hours | Monitor: idle_cluster_hours |
| Utilization Trend | Line | ds_util_trend | - |
| Cluster Sizing Recommendations | Table | ds_ml_cluster_sizing | ML: cluster_sizing_recommender |

### Page 5: Resource Optimization
**Purpose:** Right-sizing and capacity planning

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Under-Provisioned Clusters | Table | ds_under_provisioned | - |
| Over-Provisioned Clusters | Table | ds_over_provisioned | - |
| Capacity Forecast | Line | ds_ml_capacity | ML: cluster_capacity_planner |
| Savings Opportunities | Table | ds_savings | - |
| Autoscale Events | Line | ds_autoscale | Monitor: autoscale_events |
| Cluster Recommendations | Table | ds_ml_cluster_recs | ML: cluster_sizing_recommender |

### Page 6: DBR Migration
**Purpose:** DBR version tracking and migration

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Legacy DBR Count | KPI | ds_legacy_count | - |
| DBR Distribution | Pie | ds_dbr_dist | - |
| Legacy Jobs | Table | ds_legacy_jobs | - |
| Migration Progress | Line | ds_migration_progress | - |
| DBR Compatibility | Table | ds_dbr_compat | - |
| Migration Recommendations | Table | ds_migration_recs | - |

### Page 7: Job Optimization
**Purpose:** Job performance optimization

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Stale Datasets | Table | ds_stale_datasets | - |
| Large Scans | Table | ds_large_scans | - |
| Job Performance Trend | Line | ds_job_perf_trend | - |
| Resource Usage by Job | Table | ds_job_resources | - |
| Optimization Score | KPI | ds_opt_score | - |
| Job Tuning Recommendations | Table | ds_job_tuning | - |

### Page 8: Performance Drift
**Purpose:** Monitor-based performance drift

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Query Duration Drift | KPI | ds_duration_drift | Monitor: query_duration_drift_pct |
| Utilization Drift | KPI | ds_util_drift | - |
| Performance Profile | Table | ds_perf_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_perf_drift_trend | Monitor: drift metrics |
| Regression Alerts | Table | ds_ml_regression_alerts | ML: regression_detector |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_queries
SELECT COUNT(*) AS total_queries
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 1 DAY

-- ds_kpi_p95
SELECT ROUND(PERCENTILE(total_duration_ms / 1000.0, 0.95), 2) AS p95_duration_seconds
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 1 DAY
  AND execution_status = 'FINISHED'

-- ds_slow_queries
SELECT 
    statement_id,
    query_text,
    total_duration_ms / 1000.0 AS duration_seconds,
    rows_read,
    bytes_read,
    user_name,
    start_time
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND execution_status = 'FINISHED'
ORDER BY total_duration_ms DESC
LIMIT 20
```

### ML Datasets

```sql
-- ds_ml_query_forecast
SELECT 
    warehouse_id,
    forecast_date,
    predicted_p95_duration_ms,
    predicted_query_volume,
    confidence
FROM ${catalog}.${gold_schema}.query_performance_forecasts
WHERE forecast_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), 7)
ORDER BY forecast_date

-- ds_ml_warehouse_opt
SELECT 
    warehouse_id,
    warehouse_name,
    current_size,
    recommended_size,
    optimization_type,
    expected_improvement_pct,
    justification
FROM ${catalog}.${gold_schema}.warehouse_optimizations
WHERE recommendation_date = CURRENT_DATE()
ORDER BY expected_improvement_pct DESC
LIMIT 20

-- ds_ml_query_opt
SELECT 
    query_pattern_id,
    query_type,
    optimization_recommendations,
    expected_speedup_pct,
    affected_queries_count,
    recommendation_priority
FROM ${catalog}.${gold_schema}.query_optimization_recs
WHERE recommendation_date = CURRENT_DATE()
ORDER BY recommendation_priority
LIMIT 20

-- ds_ml_cluster_sizing
SELECT 
    cluster_id,
    cluster_name,
    current_node_type,
    recommended_node_type,
    current_workers,
    recommended_workers,
    potential_savings_pct,
    recommendation_reason
FROM ${catalog}.${gold_schema}.cluster_sizing_recs
WHERE recommendation_date = CURRENT_DATE()
  AND potential_savings_pct > 10
ORDER BY potential_savings_pct DESC
LIMIT 20

-- ds_ml_capacity
SELECT 
    cluster_id,
    forecast_date,
    predicted_cpu_utilization,
    predicted_memory_utilization,
    predicted_disk_utilization,
    capacity_sufficient,
    scale_recommendation
FROM ${catalog}.${gold_schema}.cluster_capacity_plans
WHERE forecast_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), 7)
ORDER BY cluster_id, forecast_date

-- ds_ml_regressions
SELECT 
    query_pattern_id,
    warehouse_id,
    baseline_p95_ms,
    current_p95_ms,
    regression_pct,
    detection_date,
    probable_cause
FROM ${catalog}.${gold_schema}.query_regression_alerts
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND regression_pct > 50
ORDER BY regression_pct DESC
LIMIT 20

-- ds_cache_hit
SELECT 
    warehouse_id,
    prediction_date,
    predicted_cache_hit_rate,
    current_cache_hit_rate,
    optimization_opportunity
FROM ${catalog}.${gold_schema}.cache_hit_predictions
WHERE prediction_date = CURRENT_DATE()
ORDER BY optimization_opportunity DESC
```

### Monitor Datasets

```sql
-- ds_perf_profile (Query)
SELECT 
    window.start AS period_start,
    total_queries,
    p50_duration_seconds,
    p95_duration_seconds,
    p99_duration_seconds,
    query_success_rate * 100 AS success_rate_pct,
    failed_queries,
    total_rows_read,
    total_bytes_read
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_cluster_profile
SELECT 
    window.start AS period_start,
    total_clusters,
    total_cluster_hours,
    avg_cluster_uptime_hours,
    idle_cluster_hours,
    active_cluster_hours,
    cluster_utilization_pct * 100 AS utilization_pct
FROM ${catalog}.${gold_schema}_monitoring.fact_node_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_perf_drift
SELECT 
    window.start AS period_start,
    query_duration_drift_pct * 100 AS duration_drift_pct
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30
```

---

## Global Filter Integration

All datasets must include:
```sql
WHERE 
  (CASE 
    WHEN :time_window = 'Last 7 Days' THEN start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    -- ... other time windows
  END)
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
  AND (:compute_type = 'All' OR compute_type = :compute_type)
```

---

## ML Model Integration Summary (7 Models)

> **Source of Truth:** [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| query_performance_forecaster | Query duration predictions | query_performance_forecasts |
| warehouse_optimizer | Warehouse sizing recommendations | warehouse_optimizations |
| cache_hit_predictor | Cache effectiveness analysis | cache_hit_predictions |
| query_optimization_recommender | Query tuning suggestions | query_optimization_recs |
| cluster_sizing_recommender | Right-sizing recommendations | cluster_sizing_recs |
| cluster_capacity_planner | Capacity forecasts | cluster_capacity_plans |
| regression_detector | Performance regression alerts | query_regression_alerts |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_query_history_profile_metrics | total_queries, p50_duration_seconds, p95_duration_seconds, p99_duration_seconds, query_success_rate, failed_queries, total_rows_read, total_bytes_read |
| fact_query_history_drift_metrics | query_duration_drift_pct |
| fact_node_timeline_profile_metrics | total_clusters, total_cluster_hours, avg_cluster_uptime_hours, idle_cluster_hours, active_cluster_hours, cluster_utilization_pct |

