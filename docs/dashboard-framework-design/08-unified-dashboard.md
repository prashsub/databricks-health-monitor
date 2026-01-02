# Unified Health Monitor Dashboard Specification

## Overview

**Purpose:** Single pane of glass for executive overview across all domains (Cost, Performance, Quality, Security, Reliability).

**Design Philosophy:** 
- Include ONLY the "Overview" page from each domain dashboard
- Stay strictly under 100 datasets
- Provide high-level KPIs and trends
- Link to domain dashboards for deep dives

**Target Dataset Count:** ~85-95 datasets (rationalized from 300+ across domains)

---

## Page Structure

### Page 1: Global Filters
**Purpose:** Universal filters that apply to all pages

**Widgets:**
| Widget | Type | Parameter |
|--------|------|-----------|
| Time Window | Dropdown | time_window |
| Workspace | Dropdown | workspace_filter |
| SKU Type | Dropdown | sku_type |
| Compute Type | Dropdown | compute_type |
| Job Status | Dropdown | job_status |

**Filter Options:**
```yaml
time_window:
  - Last 7 Days
  - Last 30 Days
  - Last 90 Days
  - Last 6 Months
  - Last Year

workspace_filter:
  - All
  - <dynamic from dim_workspace>

sku_type:
  - All
  - JOBS
  - SQL
  - DLT
  - SERVERLESS

compute_type:
  - All
  - Serverless
  - Classic

job_status:
  - All
  - Success
  - Failed
```

---

### Page 2: Executive Summary
**Purpose:** Platform-wide health at a glance

**Layout:** 6-column grid, 4 rows

**Row 1: Key KPIs (6 widgets)**
| Widget | Type | Source | Metric |
|--------|------|--------|--------|
| Total Spend (30d) | KPI | Cost | SUM(list_cost) |
| Success Rate (7d) | KPI | Reliability | success_rate |
| Query P95 (7d) | KPI | Performance | P95(duration) |
| Active Threats | KPI | Security | threat count |
| Quality Score | KPI | Quality | AVG(quality_score) |
| Platform Health | KPI | Composite | weighted health |

**Row 2: Trend Charts (3 widgets, 2 cols each)**
| Widget | Type | Source | Description |
|--------|------|--------|-------------|
| Cost Trend | Line | Cost | Daily cost over 30d |
| Reliability Trend | Line | Reliability | Success rate over 30d |
| Performance Trend | Line | Performance | P95 duration over 30d |

**Row 3: Top Issues (3 widgets, 2 cols each)**
| Widget | Type | Source | Description |
|--------|------|--------|-------------|
| Cost Anomalies | Table | ML | Recent anomalies |
| Failed Jobs | Table | Reliability | Recent failures |
| Security Alerts | Table | ML | Recent threats |

**Row 4: Health Summary (2 widgets, 3 cols each)**
| Widget | Type | Source | Description |
|--------|------|--------|-------------|
| Domain Health | Bar | Composite | Health by domain |
| Critical Actions | Table | Multi | Top 5 urgent actions |

---

### Page 3: Cost Overview (from Cost Dashboard)
**Purpose:** Cost health executive view

**Datasets Included (rationalized):**
- ds_kpi_mtd_spend
- ds_kpi_budget_variance
- ds_cost_trend_30d
- ds_ml_anomaly_count
- ds_tag_coverage
- ds_top_cost_drivers
- ds_ytd_vs_commit
- ds_projected_year_end

**Widgets:** 8 (from Cost Dashboard Page 1 + key commit tracking)

---

### Page 4: Reliability Overview (from Reliability Dashboard)
**Purpose:** Reliability health executive view

**Datasets Included (rationalized):**
- ds_kpi_success
- ds_kpi_failed
- ds_kpi_duration
- ds_kpi_runs
- ds_success_trend
- ds_ml_high_risk
- ds_reliability_profile (subset)

**Widgets:** 6 (from Reliability Dashboard Page 1)

---

### Page 5: Performance Overview (from Performance Dashboard)
**Purpose:** Performance health executive view

**Datasets Included (rationalized):**
- ds_kpi_query_p95
- ds_kpi_sla_breach
- ds_kpi_avg_cpu
- ds_kpi_efficiency
- ds_performance_trend
- ds_top_slow_queries

**Widgets:** 6 (from Performance Dashboard Page 1)

---

### Page 6: Security Overview (from Security Dashboard)
**Purpose:** Security health executive view

**Datasets Included (rationalized):**
- ds_kpi_events
- ds_kpi_high_risk
- ds_kpi_denied
- ds_kpi_users
- ds_event_trend
- ds_ml_threats

**Widgets:** 6 (from Security Dashboard Page 1)

---

### Page 7: Quality Overview (from Quality Dashboard)
**Purpose:** Quality health executive view

**Datasets Included (rationalized):**
- ds_kpi_quality
- ds_kpi_critical
- ds_kpi_tables
- ds_kpi_tag_coverage
- ds_quality_trend
- ds_tables_issues

**Widgets:** 6 (from Quality Dashboard Page 1)

---

### Page 8: ML Intelligence
**Purpose:** Cross-domain ML insights

**Datasets (6-8):**
- ds_ml_cost_anomalies
- ds_ml_job_failure_risk
- ds_ml_security_threats
- ds_ml_capacity_forecast
- ds_ml_data_drift
- ds_ml_sla_risk

**Widgets:**
| Widget | Type | Model Source |
|--------|------|--------------|
| Cost Anomalies | Table | cost_anomaly_detector |
| Failure Risk | Table | job_failure_predictor |
| Security Threats | Table | threat_detector |
| Capacity Forecast | Line | cluster_capacity_planner |
| Data Drift | Table | data_drift_detector |
| SLA Risk | Table | sla_breach_predictor |

---

### Page 9: Monitor Drift Alerts
**Purpose:** Cross-domain drift detection

**Datasets (5-6):**
- ds_cost_drift
- ds_reliability_drift
- ds_query_drift
- ds_security_drift
- ds_quality_drift

**Widgets:**
| Widget | Type | Source Monitor |
|--------|------|----------------|
| Cost Drift % | KPI | fact_usage_drift_metrics |
| Success Rate Drift | KPI | fact_job_run_timeline_drift_metrics |
| Query P95 Drift | KPI | fact_query_history_drift_metrics |
| Event Volume Drift | KPI | fact_audit_logs_drift_metrics |
| Quality Score Drift | KPI | fact_data_quality_drift_metrics |
| Drift Trend | Line | All drift metrics |

---

## Dataset Rationalization Strategy

### Selection Criteria
1. **Overview pages only** - Deep dive pages excluded
2. **KPI priority** - Aggregate KPIs over detailed tables
3. **ML summary** - Top N results, not full tables
4. **Monitor summary** - Latest window, not full history

### Dataset Count by Page

| Page | Datasets | Source |
|------|----------|--------|
| Global Filters | 5 | Dynamic lookups |
| Executive Summary | 15 | Composite |
| Cost Overview | 10 | Cost Dashboard |
| Reliability Overview | 10 | Reliability Dashboard |
| Performance Overview | 10 | Performance Dashboard |
| Security Overview | 10 | Security Dashboard |
| Quality Overview | 10 | Quality Dashboard |
| ML Intelligence | 8 | ML prediction tables |
| Monitor Drift | 6 | Drift metrics |
| **Total** | **~85** | Under 100 limit |

---

## Global Filter Integration

All datasets must include these parameter bindings:

```sql
WHERE 
  -- Time Window Filter
  (CASE 
    WHEN :time_window = 'Last 7 Days' THEN date_column >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN date_column >= CURRENT_DATE() - INTERVAL 30 DAYS
    WHEN :time_window = 'Last 90 Days' THEN date_column >= CURRENT_DATE() - INTERVAL 90 DAYS
    WHEN :time_window = 'Last 6 Months' THEN date_column >= CURRENT_DATE() - INTERVAL 6 MONTHS
    WHEN :time_window = 'Last Year' THEN date_column >= CURRENT_DATE() - INTERVAL 1 YEAR
    ELSE TRUE
  END)
  -- Workspace Filter
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
  -- SKU Type Filter (for cost/compute datasets)
  AND (:sku_type = 'All' OR sku_name LIKE CONCAT('%', :sku_type, '%'))
  -- Compute Type Filter
  AND (:compute_type = 'All' OR 
       (CASE WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless' ELSE 'Classic' END) = :compute_type)
  -- Job Status Filter (for job datasets)
  AND (:job_status = 'All' OR 
       (CASE WHEN termination_code = 'SUCCESS' THEN 'Success' ELSE 'Failed' END) = :job_status)
```

---

## Implementation Notes

### 1. Runtime Assembly
The unified dashboard is assembled at runtime by `build_unified_dashboard.py`:
```python
def build_unified_dashboard(domain_dashboards, config):
    unified = {"displayName": "Health Monitor Unified", "pages": []}
    
    # Add global filters page
    unified["pages"].append(create_filters_page())
    
    # Add overview page from each domain
    for domain_key, dashboard in domain_dashboards.items():
        overview_page = extract_overview_page(dashboard)
        unified["pages"].append(overview_page)
    
    # Rationalize datasets to stay under 100
    unified["datasets"] = rationalize_datasets(unified)
    
    return unified
```

### 2. Dataset Deduplication
Shared datasets are defined once and referenced by multiple widgets:
```python
SHARED_DATASETS = {
    "gf_ds_time_windows": "Time window options",
    "gf_ds_workspaces": "Workspace list",
    "ds_dim_workspace": "Workspace dimension",
}
```

### 3. Prefixing Strategy
Datasets are prefixed by source dashboard to avoid conflicts:
```
cost_ds_kpi_mtd_spend
rel_ds_kpi_success
perf_ds_kpi_query_p95
sec_ds_kpi_events
qual_ds_kpi_quality
```

---

## Links to Domain Dashboards

Each overview page should include navigation hints:
```
"For detailed analysis, open [Domain] Dashboard"
```

This keeps the unified dashboard lean while providing paths to deep dives.

