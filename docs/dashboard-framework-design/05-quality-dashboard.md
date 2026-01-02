# Quality Dashboard Specification

## Overview

**Purpose:** Data quality monitoring, governance compliance, table health, and data freshness tracking.

**Existing Dashboards to Consolidate:**
- `table_health.lvdash.json` (7 datasets)
- `governance_hub.lvdash.json` (16 datasets) - quality aspects

**Target Dataset Count:** ~50 datasets (well within 100 limit after enrichment)

---

## Page Structure

### Page 1: Quality Overview (Overview Page for Unified)
**Purpose:** Executive summary of data quality health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Avg Quality Score | KPI | ds_kpi_quality | Monitor: avg_quality_score |
| Critical Violations | KPI | ds_kpi_critical | Monitor: critical_violation_count |
| Tables Monitored | KPI | ds_kpi_tables | - |
| Tag Coverage % | Gauge | ds_kpi_tag_coverage | - |
| Quality Trend | Line | ds_quality_trend | Monitor: quality score trend |
| Tables with Issues | Table | ds_tables_issues | - |

### Page 2: Data Quality Rules
**Purpose:** Rule evaluation results and violations

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Rules Evaluated | KPI | ds_rules_total | Monitor: total_rules_evaluated |
| Rule Pass Rate | Gauge | ds_rule_pass_rate | Monitor: rule_pass_rate |
| Critical Violations Trend | Line | ds_critical_trend | Monitor: critical_violation_count |
| Violations by Severity | Pie | ds_violations_severity | - |
| Failed Rules Table | Table | ds_failed_rules | - |
| Tables with Critical | Table | ds_tables_critical | Monitor: tables_with_critical |

### Page 3: Data Drift
**Purpose:** Data drift detection and alerts

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Drift Alerts (7d) | KPI | ds_drift_alerts | ML: data_drift_detector |
| High Drift Tables | Table | ds_high_drift | ML: drift_detector |
| Drift Score Distribution | Histogram | ds_drift_dist | - |
| Drift by Column | Table | ds_drift_columns | - |
| Drift Trend | Line | ds_drift_trend | Monitor: drift metrics |
| Schema Change Alerts | Table | ds_ml_schema_change | ML: schema_evolution_predictor |

### Page 4: Data Freshness
**Purpose:** Data freshness and staleness tracking

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Stale Tables | KPI | ds_stale_tables | - |
| Freshness Score | Gauge | ds_freshness_score | ML: freshness_predictor |
| Tables by Freshness | Bar | ds_tables_freshness | - |
| Freshness Predictions | Table | ds_ml_freshness | ML: freshness_predictor |
| Late Arriving Data | Table | ds_late_data | - |
| Freshness Trend | Line | ds_freshness_trend | - |

### Page 5: Governance Compliance
**Purpose:** Tag compliance and documentation

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Tables | KPI | ds_total_tables | - |
| Tagged Tables % | Gauge | ds_tagged_pct | - |
| Documented Tables % | Gauge | ds_documented_pct | - |
| Tables by Catalog | Pie | ds_tables_catalog | - |
| Undocumented Tables | Table | ds_undocumented | - |
| Tag Recommendations | Table | ds_ml_tag_recs | ML: tag_recommender |

### Page 6: Table Health
**Purpose:** Table-level health metrics

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Large Tables | Table | ds_large_tables | - |
| Tables by Size | Bar | ds_tables_size | - |
| Storage Growth Trend | Line | ds_storage_trend | - |
| Table Lineage Coverage | KPI | ds_lineage_coverage | - |
| Tables with No Lineage | Table | ds_no_lineage | - |
| Table Health Score | Table | ds_table_health | - |

### Page 7: Quality Drift
**Purpose:** Monitor-based quality drift

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Quality Score Drift | KPI | ds_quality_drift | Monitor: quality_score_drift |
| Violation Rate Drift | KPI | ds_violation_drift | Monitor: critical_violation_drift |
| Quality Profile Metrics | Table | ds_quality_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_monitor_drift | Monitor: drift metrics |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_quality
SELECT ROUND(AVG(quality_score), 2) AS avg_quality_score
FROM ${catalog}.${gold_schema}.fact_data_quality_results
WHERE evaluation_time >= CURRENT_DATE() - INTERVAL 7 DAYS

-- ds_total_tables
SELECT COUNT(*) AS total_tables
FROM ${catalog}.${gold_schema}.fact_table_lineage
WHERE table_type = 'TABLE'
```

### ML Datasets

```sql
-- ds_ml_drift
SELECT 
    table_name,
    drift_score,
    drift_type,
    affected_columns,
    detection_time,
    recommended_action
FROM ${catalog}.${gold_schema}.data_drift_alerts
WHERE detection_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND drift_score > 0.3
ORDER BY drift_score DESC
LIMIT 20

-- ds_ml_schema_change
SELECT 
    table_name,
    predicted_change_type,
    confidence,
    affected_columns,
    prediction_date
FROM ${catalog}.${gold_schema}.schema_evolution_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND confidence > 0.7
ORDER BY confidence DESC

-- ds_ml_freshness
SELECT 
    table_name,
    expected_refresh_time,
    predicted_delay_minutes,
    confidence,
    prediction_date
FROM ${catalog}.${gold_schema}.freshness_predictions
WHERE prediction_date = CURRENT_DATE()
ORDER BY predicted_delay_minutes DESC
```

### Monitor Datasets

```sql
-- ds_quality_profile
SELECT 
    window.start AS period_start,
    avg_quality_score,
    total_rules_evaluated,
    rule_pass_rate * 100 AS rule_pass_rate_pct,
    critical_violation_count,
    tables_with_critical
FROM ${catalog}.${gold_schema}_monitoring.fact_data_quality_results_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_quality_drift
SELECT 
    window.start AS period_start,
    quality_score_drift,
    critical_violation_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_data_quality_results_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30
```

---

## ML Model Integration Summary

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| drift_detector | Drift alerts, trend | drift_detection_results |
| data_drift_detector | Combined drift view | data_drift_alerts |
| schema_evolution_predictor | Schema change alerts | schema_evolution_predictions |
| schema_change_predictor | Change predictions | schema_change_alerts |
| freshness_predictor | Freshness forecasts | freshness_predictions |
| tag_recommender | Tag suggestions | quality_tag_recommendations |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_data_quality_results_profile_metrics | avg_quality_score, total_rules_evaluated, rule_pass_rate, critical_violation_count, tables_with_critical, total_evaluations, distinct_tables |
| fact_data_quality_results_drift_metrics | quality_score_drift, critical_violation_drift |

