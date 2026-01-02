# Cost Management Dashboard Specification

## Overview

**Purpose:** Comprehensive cost analytics, budget tracking, and optimization recommendations for Databricks platform spend.

**Existing Dashboards to Consolidate:**
- `cost_management.lvdash.json` (36 datasets)
- `commit_tracking.lvdash.json` (13 datasets)

**Target Dataset Count:** ~60 datasets (well within 100 limit after enrichment)

---

## Page Structure

### Page 1: Cost Overview (Overview Page for Unified)
**Purpose:** Executive summary of cost health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Spend (MTD) | KPI | ds_kpi_mtd_spend | - |
| Spend vs Budget | KPI | ds_kpi_budget_variance | ML: budget_forecaster |
| Cost Trend (30d) | Line | ds_cost_trend_30d | Monitor: total_daily_cost |
| Anomaly Alert Count | KPI | ds_ml_anomaly_count | ML: cost_anomaly_detector |
| Tag Coverage % | Gauge | ds_tag_coverage | Monitor: tag_coverage_pct |
| Top Cost Drivers | Bar | ds_top_cost_drivers | - |

### Page 2: Spend Analysis
**Purpose:** Detailed breakdown of spend

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Spend by SKU | Pie | ds_spend_by_sku | Monitor: jobs_compute_cost, sql_compute_cost |
| Spend by Workspace | Bar | ds_spend_by_workspace | - |
| Spend by Owner | Table | ds_spend_by_owner | - |
| Serverless vs Classic | Pie | ds_serverless_vs_classic | Monitor: serverless_cost, serverless_ratio |
| DLT Cost Breakdown | Bar | ds_dlt_cost | Monitor: dlt_cost |
| Model Serving Cost | Bar | ds_model_serving_cost | Monitor: model_serving_cost |

### Page 3: Cost Optimization
**Purpose:** Savings opportunities and recommendations

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Jobs on All-Purpose Clusters | KPI | ds_jobs_on_ap | Monitor: jobs_on_all_purpose_cost |
| Potential Savings | KPI | ds_potential_savings | Monitor: potential_job_cluster_savings |
| Optimization Recommendations | Table | ds_ml_optimizations | ML: job_cost_optimizer |
| Cost Anomalies | Table | ds_ml_anomalies | ML: cost_anomaly_detector |
| Budget Forecast | Line | ds_ml_budget_forecast | ML: budget_forecaster |
| Chargeback Attribution | Table | ds_chargeback | ML: chargeback_attribution |

### Page 4: Tag Compliance
**Purpose:** Tag governance and coverage

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Tagged vs Untagged Spend | Pie | ds_tagged_spend | Monitor: tagged_cost_total, untagged_cost_total |
| Tag Coverage by Team | Bar | ds_tag_coverage_team | - |
| Tag Recommendations | Table | ds_ml_tag_recs | ML: tag_recommender |
| Tag Coverage Trend | Line | ds_tag_trend | Monitor: tag_coverage_drift |
| Untagged Resources | Table | ds_untagged_resources | - |

### Page 5: Commit Tracking
**Purpose:** Commitment utilization and forecasting

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| YTD Spend vs Commit | Gauge | ds_ytd_vs_commit | - |
| Projected Year-End | KPI | ds_projected_year_end | ML: budget_forecaster |
| Monthly Burn Rate | Line | ds_monthly_burn | - |
| Commit Utilization % | KPI | ds_commit_util | - |
| Underspend/Overspend Risk | KPI | ds_spend_risk | ML: commitment_recommender |
| Cumulative Spend vs Commit | Area | ds_cumulative_spend | - |
| Monthly Detail Table | Table | ds_monthly_detail | - |

### Page 6: Cost Drift & Alerts
**Purpose:** Monitor-based drift detection

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Cost Drift % | KPI | ds_cost_drift | Monitor: cost_drift_pct |
| Tag Coverage Drift | KPI | ds_tag_drift | Monitor: tag_coverage_drift |
| Drift Trend | Line | ds_drift_trend | Monitor: drift metrics |
| Monitor Health | Table | ds_monitor_health | Monitor: all metrics |
| Cost Profile Metrics | Table | ds_profile_metrics | Monitor: profile table |

---

## Datasets Specification

### Core Datasets (from existing)

```sql
-- ds_kpi_mtd_spend
SELECT ROUND(SUM(list_cost), 2) AS mtd_spend
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())

-- ds_cost_trend_30d  
SELECT usage_date, SUM(list_cost) AS daily_cost
FROM ${catalog}.${gold_schema}.fact_usage f
JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY usage_date
ORDER BY usage_date
```

### ML Datasets

```sql
-- ds_ml_anomaly_count
SELECT COUNT(*) AS anomaly_count
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND is_anomaly = TRUE

-- ds_ml_budget_forecast
SELECT 
    forecast_date,
    predicted_spend,
    lower_bound,
    upper_bound,
    confidence
FROM ${catalog}.${gold_schema}.budget_forecast_predictions
WHERE forecast_date BETWEEN CURRENT_DATE() AND LAST_DAY(ADD_MONTHS(CURRENT_DATE(), 3))
ORDER BY forecast_date
```

### Monitor Datasets

```sql
-- ds_monitor_cost_drift
SELECT 
    window.start AS period_start,
    cost_drift_pct * 100 AS cost_drift_pct,
    tag_coverage_drift * 100 AS tag_coverage_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_usage_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30

-- ds_profile_metrics
SELECT 
    window.start AS period_start,
    total_daily_cost,
    serverless_ratio * 100 AS serverless_pct,
    tag_coverage_pct * 100 AS tag_coverage_pct,
    jobs_on_all_purpose_cost,
    potential_job_cluster_savings
FROM ${catalog}.${gold_schema}_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
```

---

## Global Filter Integration

All datasets must include:
```sql
WHERE 
  (CASE 
    WHEN :time_window = 'Last 7 Days' THEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    -- ... other time windows
  END)
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
  AND (:sku_type = 'All' OR sku_name LIKE CONCAT('%', :sku_type, '%'))
```

---

## ML Model Integration Summary

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| cost_anomaly_detector | Anomaly alerts, trend overlay | cost_anomaly_predictions |
| budget_forecaster | Forecast chart, year-end projection | budget_forecast_predictions |
| commitment_recommender | Commit risk, recommendations | commitment_recommendations |
| tag_recommender | Tag suggestions table | tag_recommendations |
| job_cost_optimizer | Optimization recommendations | job_cost_optimizations |
| chargeback_attribution | Attribution table | chargeback_attributions |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_usage_profile_metrics | total_daily_cost, tag_coverage_pct, serverless_ratio, jobs_on_all_purpose_cost, potential_job_cluster_savings, dlt_cost, model_serving_cost |
| fact_usage_drift_metrics | cost_drift_pct, tag_coverage_drift |

