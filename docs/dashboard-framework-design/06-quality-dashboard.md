# Quality Dashboard Specification

## Overview

**Purpose:** Data quality analytics, governance monitoring, table health tracking, and lineage analysis for the Databricks platform.

**Existing Dashboards to Consolidate:**
- `table_health.lvdash.json` (7 datasets)
- `governance_hub.lvdash.json` (16 datasets)

**Target Dataset Count:** ~50 datasets (within 100 limit after enrichment)

---

## Page Structure

### Page 1: Quality Overview (Overview Page for Unified)
**Purpose:** Executive summary of data quality health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Quality Score | KPI | ds_kpi_quality | Monitor: avg_quality_score |
| Tables Monitored | KPI | ds_kpi_tables | - |
| Critical Violations | KPI | ds_kpi_violations | Monitor: critical_violation_count |
| Data Drift Alerts | KPI | ds_kpi_drift_alerts | ML: data_drift_detector |
| Quality Trend | Line | ds_quality_trend | - |
| Tables at Risk | Table | ds_tables_at_risk | ML: data_drift_detector |

### Page 2: Data Quality Rules
**Purpose:** Rule evaluation and violation tracking

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Rules Evaluated | KPI | ds_rules_evaluated | Monitor: total_rules_evaluated |
| Rule Pass Rate | Gauge | ds_rule_pass_rate | Monitor: rule_pass_rate |
| Violations by Severity | Pie | ds_violations_severity | - |
| Failing Rules | Table | ds_failing_rules | - |
| Rule Coverage | Bar | ds_rule_coverage | - |
| Violation Trend | Line | ds_violation_trend | - |

### Page 3: Data Drift
**Purpose:** Data drift detection and analysis

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Drift Alerts (7d) | KPI | ds_drift_alert_count | ML: data_drift_detector |
| Drift Score Distribution | Histogram | ds_drift_dist | ML: data_drift_detector |
| Drift Alerts Table | Table | ds_ml_drift_alerts | ML: data_drift_detector |
| Drift by Column | Table | ds_drift_by_column | ML: data_drift_detector |
| Drift Trend | Line | ds_drift_trend | - |
| Schema Change Predictions | Table | ds_ml_schema_changes | ML: schema_change_predictor |

### Page 4: Table Health
**Purpose:** Table-level health monitoring

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Tables by Catalog | Pie | ds_tables_catalog | - |
| Table Size Distribution | Histogram | ds_table_sizes | - |
| Largest Tables | Table | ds_largest_tables | - |
| Stale Tables | Table | ds_stale_tables | - |
| Table Growth Trend | Line | ds_table_growth | - |
| Table Health Scores | Table | ds_table_health | - |

### Page 5: Governance & Lineage
**Purpose:** Data governance and lineage tracking

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Lineage Coverage | KPI | ds_lineage_coverage | - |
| Tables with Lineage | KPI | ds_tables_lineage | - |
| Schema Evolution | Table | ds_ml_schema_evolution | ML: schema_evolution_predictor |
| Lineage Graph | Table | ds_lineage_detail | - |
| Governance Tags | Pie | ds_governance_tags | - |
| Ownership Coverage | Gauge | ds_ownership | - |

### Page 6: Quality Drift
**Purpose:** Monitor-based quality drift detection

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Quality Score Drift | KPI | ds_quality_drift | Monitor: quality_score_drift |
| Violation Rate Drift | KPI | ds_violation_drift | - |
| Quality Profile | Table | ds_quality_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_quality_drift_trend | Monitor: drift metrics |
| Monitor Alerts | Table | ds_quality_alerts | - |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_tables
SELECT COUNT(DISTINCT table_name) AS monitored_tables
FROM ${catalog}.${gold_schema}.fact_data_quality_results
WHERE check_date >= CURRENT_DATE() - INTERVAL 7 DAYS

-- ds_tables_catalog
SELECT 
    catalog_name,
    COUNT(*) AS table_count
FROM ${catalog}.${gold_schema}.dim_table
GROUP BY catalog_name
ORDER BY table_count DESC

-- ds_largest_tables
SELECT 
    table_name,
    catalog_name,
    schema_name,
    size_bytes,
    row_count,
    last_modified_time
FROM ${catalog}.${gold_schema}.dim_table
ORDER BY size_bytes DESC
LIMIT 20
```

### ML Datasets

```sql
-- ds_ml_drift_alerts
SELECT 
    table_name,
    drift_score,
    drift_type,
    affected_columns,
    baseline_stats,
    current_stats,
    detection_date,
    severity
FROM ${catalog}.${gold_schema}.data_drift_alerts
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND drift_score > 0.3
ORDER BY drift_score DESC
LIMIT 20

-- ds_ml_schema_changes
SELECT 
    table_name,
    change_probability,
    predicted_change_type,
    affected_columns,
    prediction_date,
    confidence
FROM ${catalog}.${gold_schema}.schema_change_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND change_probability > 0.7
ORDER BY change_probability DESC
LIMIT 20

-- ds_ml_schema_evolution
SELECT 
    table_name,
    evolution_type,
    predicted_columns,
    impact_assessment,
    recommendation,
    prediction_date
FROM ${catalog}.${gold_schema}.schema_evolution_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY prediction_date DESC
LIMIT 20
```

### Monitor Datasets

```sql
-- ds_quality_profile
SELECT 
    window.start AS period_start,
    avg_quality_score * 100 AS quality_score_pct,
    total_rules_evaluated,
    critical_violation_count,
    rule_pass_rate * 100 AS pass_rate_pct,
    violation_rate * 100 AS violation_rate_pct
FROM ${catalog}.${gold_schema}_monitoring.fact_data_quality_results_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_quality_drift
SELECT 
    window.start AS period_start,
    quality_score_drift * 100 AS quality_drift_pct
FROM ${catalog}.${gold_schema}_monitoring.fact_data_quality_results_drift_metrics
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
    WHEN :time_window = 'Last 7 Days' THEN check_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN check_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    -- ... other time windows
  END)
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
```

---

## ML Model Integration Summary (3 Models)

> **Source of Truth:** [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| data_drift_detector | Data drift detection and alerts | data_drift_alerts |
| schema_change_predictor | Schema change predictions | schema_change_predictions |
| schema_evolution_predictor | Schema evolution tracking | schema_evolution_predictions |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_data_quality_results_profile_metrics | avg_quality_score, total_rules_evaluated, critical_violation_count, rule_pass_rate, violation_rate |
| fact_data_quality_results_drift_metrics | quality_score_drift |

