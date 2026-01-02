# Performance Dashboard Specification

## Overview

**Purpose:** Query performance, cluster utilization, resource optimization, and DBR migration tracking.

**Existing Dashboards to Consolidate:**
- `query_performance.lvdash.json` (23 datasets)
- `cluster_utilization.lvdash.json` (23 datasets)
- `dbr_migration.lvdash.json` (6 datasets)
- `job_optimization.lvdash.json` (7 datasets)

**Target Dataset Count:** ~80 datasets (within 100 limit after enrichment)

---

## Page Structure

### Page 1: Performance Overview (Overview Page for Unified)
**Purpose:** Executive summary of performance health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Query P95 Duration | KPI | ds_kpi_query_p95 | Monitor: p95_duration_sec |
| SLA Breach Rate | KPI | ds_kpi_sla_breach | Monitor: sla_breach_rate |
| Avg CPU Utilization | KPI | ds_kpi_avg_cpu | Monitor: avg_cpu_total_pct |
| Cluster Efficiency | Gauge | ds_kpi_efficiency | Monitor: efficiency_score |
| Performance Trend | Line | ds_performance_trend | - |
| Top Slow Queries | Table | ds_top_slow_queries | - |

### Page 2: Query Performance
**Purpose:** Detailed query analysis

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Query Volume Trend | Line | ds_query_volume | Monitor: query_count |
| Query Success Rate | Gauge | ds_query_success | Monitor: query_success_rate |
| Duration Distribution | Histogram | ds_duration_dist | - |
| Queries with Spill | KPI | ds_spill_count | Monitor: spill_rate |
| Cache Hit Rate | Gauge | ds_cache_hit | Monitor: cache_hit_count |
| Query by Statement Type | Pie | ds_query_by_type | - |
| Slow Query Trend | Line | ds_slow_trend | Monitor: sla_breach_count |
| Performance Regressions | Table | ds_ml_regressions | ML: regression_detector |

### Page 3: Cluster Utilization
**Purpose:** Cluster resource usage

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| CPU Utilization Trend | Line | ds_cpu_trend | Monitor: avg_cpu_user_pct, avg_cpu_system_pct |
| Memory Utilization Trend | Line | ds_memory_trend | Monitor: avg_memory_pct |
| P95 CPU | KPI | ds_p95_cpu | Monitor: p95_cpu_total_pct |
| Underutilized Hours | KPI | ds_underutil | Monitor: underutilized_hours |
| Overutilized Hours | KPI | ds_overutil | Monitor: overutilized_hours |
| Utilization Heatmap | Heatmap | ds_util_heatmap | - |
| Rightsizing Opportunities | Table | ds_ml_rightsizing | ML: cluster_sizing_recommender |
| Capacity Forecast | Line | ds_ml_capacity | ML: cluster_capacity_planner |

### Page 4: Query Optimization
**Purpose:** Optimization recommendations

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Inefficient Queries | Table | ds_inefficient | - |
| Spill Analysis | Table | ds_spill_analysis | Monitor: queries_with_spill |
| Long-Running Queries | Table | ds_long_running | - |
| Query Optimization Recs | Table | ds_ml_query_opts | ML: query_performance_forecaster |
| Warehouse Recommendations | Table | ds_ml_warehouse | ML: warehouse_optimizer |
| Cache Recommendations | Table | ds_ml_cache | ML: cache_hit_predictor |

### Page 5: DBR Migration
**Purpose:** Databricks Runtime migration tracking

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Legacy DBR Count | KPI | ds_legacy_count | - |
| Serverless Adoption % | Gauge | ds_serverless_adopt | - |
| DBR Distribution | Pie | ds_dbr_dist | - |
| Jobs on Legacy DBR | Table | ds_legacy_jobs | - |
| Migration Risk Scores | Table | ds_ml_migration_risk | ML: dbr_migration_risk_scorer |
| Compute Type Breakdown | Pie | ds_compute_type | - |

### Page 6: Resource Optimization
**Purpose:** Resource efficiency and rightsizing

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Jobs on All-Purpose | Table | ds_jobs_on_ap | - |
| Stale Datasets | Table | ds_stale_datasets | - |
| Cluster Efficiency Recs | Table | ds_ml_efficiency | ML: cluster_efficiency_optimizer |
| Resource Rightsizing | Table | ds_ml_rightsizer | ML: resource_rightsizer |
| Capacity Planning | Line | ds_ml_capacity_plan | ML: cluster_capacity_planner |

### Page 7: Performance Drift
**Purpose:** Monitor-based drift detection

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Query P95 Drift | KPI | ds_query_drift | Monitor: p95_duration_drift_pct |
| CPU Drift | KPI | ds_cpu_drift | Monitor: cpu_utilization_drift |
| Efficiency Drift | KPI | ds_efficiency_drift | Monitor: efficiency_score_drift |
| Query Profile Metrics | Table | ds_query_profile | Monitor: profile metrics |
| Cluster Profile Metrics | Table | ds_cluster_profile | Monitor: profile metrics |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_query_p95
SELECT ROUND(PERCENTILE(total_duration_ms/1000, 0.95), 2) AS p95_duration
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS

-- ds_cpu_trend
SELECT 
    DATE(start_time) AS date,
    AVG(cpu_user_percent) AS avg_cpu_user,
    AVG(cpu_system_percent) AS avg_cpu_system,
    AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu_total
FROM ${catalog}.${gold_schema}.fact_node_timeline
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE(start_time)
ORDER BY date
```

### ML Datasets

```sql
-- ds_ml_regressions
SELECT 
    query_id,
    query_text,
    current_p95,
    baseline_p95,
    regression_pct,
    detection_date
FROM ${catalog}.${gold_schema}.query_regressions
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND regression_pct > 50
ORDER BY regression_pct DESC
LIMIT 20

-- ds_ml_rightsizing
SELECT 
    cluster_id,
    cluster_name,
    current_node_type,
    recommended_node_type,
    current_cost_per_hour,
    recommended_cost_per_hour,
    potential_savings_pct
FROM ${catalog}.${gold_schema}.cluster_sizing_recs
WHERE recommendation_date = CURRENT_DATE()
  AND potential_savings_pct > 10
ORDER BY potential_savings_pct DESC
```

### Monitor Datasets

```sql
-- ds_query_profile
SELECT 
    window.start AS period_start,
    query_count,
    query_success_rate * 100 AS success_rate_pct,
    p95_duration_sec,
    sla_breach_rate * 100 AS sla_breach_pct,
    efficiency_rate * 100 AS efficiency_pct,
    spill_rate * 100 AS spill_pct
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_cluster_profile
SELECT 
    window.start AS period_start,
    avg_cpu_total_pct * 100 AS avg_cpu_pct,
    avg_memory_pct * 100 AS avg_memory_pct,
    efficiency_score * 100 AS efficiency_pct,
    rightsizing_opportunity_pct * 100 AS rightsizing_pct,
    underutilized_hours,
    overutilized_hours
FROM ${catalog}.${gold_schema}_monitoring.fact_node_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30
```

---

## ML Model Integration Summary

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| query_performance_forecaster | Query optimization recs | query_performance_forecasts |
| warehouse_optimizer | Warehouse sizing recs | warehouse_optimizations |
| cluster_capacity_planner | Capacity forecast chart | cluster_capacity_plans |
| cluster_efficiency_optimizer | Efficiency recs | cluster_efficiency_recs |
| cluster_sizing_recommender | Rightsizing table | cluster_sizing_recs |
| dbr_migration_risk_scorer | Migration risk scores | dbr_migration_risks |
| resource_rightsizer | Resource optimization | resource_rightsizing_recs |
| cache_hit_predictor | Cache recommendations | cache_hit_predictions |
| regression_detector | Performance regressions | query_regressions |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_query_history_profile_metrics | query_count, query_success_rate, p95_duration_sec, sla_breach_rate, sla_breach_count, efficiency_rate, spill_rate, queries_with_spill, cache_hit_count |
| fact_query_history_drift_metrics | p95_duration_drift_pct |
| fact_node_timeline_profile_metrics | avg_cpu_user_pct, avg_cpu_system_pct, avg_cpu_total_pct, avg_memory_pct, p95_cpu_total_pct, p95_memory_pct, underutilized_hours, overutilized_hours, efficiency_score, rightsizing_opportunity_pct |
| fact_node_timeline_drift_metrics | cpu_utilization_drift, efficiency_score_drift |

