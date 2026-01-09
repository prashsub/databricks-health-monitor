# Unified Domain - Actual Implementation

## Overview

**Dashboard:** `unified.lvdash.json`  
**Total Datasets:** 63  
**Purpose:** Executive overview aggregating metrics across all domains  

**Primary Tables:**
- Aggregates from all domain fact tables:
  - `fact_usage` (Cost)
  - `fact_job_run_timeline` (Reliability)
  - `fact_query_history` (Performance)
  - `fact_audit_logs` (Security)
  - `system.information_schema.tables` (Quality)

---

## 📊 Health Score Framework

### Overall Health Score
**Calculation:** Weighted average of domain scores
```sql
(cost_score * 0.25) + 
(reliability_score * 0.25) + 
(performance_score * 0.20) + 
(security_score * 0.20) + 
(quality_score * 0.10)
```

### Domain Health Scores

| Domain | Weight | Score Calculation |
|--------|--------|-------------------|
| **Cost** | 25% | Tag coverage (40%) + Serverless adoption (30%) + Budget adherence (30%) |
| **Reliability** | 25% | Success rate (60%) + MTTR score (40%) |
| **Performance** | 20% | Query performance (50%) + Resource utilization (50%) |
| **Security** | 20% | Event success rate (50%) + Risk event score (50%) |
| **Quality** | 10% | Documentation coverage (60%) + Tag coverage (40%) |

---

## 🔑 Key Unified Datasets

### ds_health_summary
**Purpose:** Overall health status across all domains  
**Type:** Multi-domain KPI  
**Query:**
```sql
WITH cost_score AS (
  SELECT 
    LEAST(
      (SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) / SUM(list_cost)) * 40 +
      (SUM(CASE WHEN sku_name LIKE '%SERVERLESS%' THEN list_cost ELSE 0 END) / SUM(list_cost)) * 30 +
      30,  -- Budget score (simplified)
    100) AS score
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
reliability_score AS (
  SELECT 
    (SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.6 +
    40 AS score  -- MTTR score (simplified)
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
),
security_score AS (
  SELECT 
    (SUM(CASE WHEN response_status_code < 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.5 +
    50 AS score  -- Risk score (simplified)
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT 
  ROUND(c.score * 0.25 + r.score * 0.25 + s.score * 0.20 + 70, 1) AS overall_health_score,
  ROUND(c.score, 1) AS cost_score,
  ROUND(r.score, 1) AS reliability_score,
  ROUND(s.score, 1) AS security_score
FROM cost_score c, reliability_score r, security_score s
```

### ds_cost_overview
**Purpose:** Cost KPIs for unified view  
**Source:** `fact_usage`  
**Query:**
```sql
SELECT 
  CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS mtd_spend,
  CONCAT(
    ROUND(
      SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) * 100.0 / SUM(list_cost),
    1), '%'
  ) AS tag_coverage,
  CONCAT(
    ROUND(
      SUM(CASE WHEN sku_name LIKE '%SERVERLESS%' THEN list_cost ELSE 0 END) * 100.0 / SUM(list_cost),
    1), '%'
  ) AS serverless_adoption
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
```

### ds_reliability_overview
**Purpose:** Reliability KPIs for unified view  
**Source:** `fact_job_run_timeline`  
**Query:**
```sql
SELECT 
  CONCAT(
    ROUND(
      SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
    1), '%'
  ) AS success_rate,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN result_state IN ('FAILED', 'TIMEDOUT') THEN 1 ELSE 0 END) AS failed_runs,
  ROUND(AVG(duration_seconds), 0) AS avg_duration_seconds
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time >= DATE_TRUNC('month', CURRENT_DATE())
```

### ds_security_overview
**Purpose:** Security KPIs for unified view  
**Source:** `fact_audit_logs`  
**Query:**
```sql
SELECT 
  COUNT(*) AS total_events,
  SUM(CASE WHEN response_status_code >= 400 THEN 1 ELSE 0 END) AS failed_events,
  SUM(CASE WHEN risk_level IN ('High', 'Critical') THEN 1 ELSE 0 END) AS high_risk_events,
  COUNT(DISTINCT user_identity_email) AS unique_users
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= DATE_TRUNC('month', CURRENT_DATE())
```

### ds_quality_overview
**Purpose:** Quality KPIs for unified view  
**Source:** `system.information_schema.tables`, `system.information_schema.table_tags`  
**Query:**
```sql
WITH all_tables AS (
  SELECT 
    table_catalog,
    table_schema,
    table_name,
    comment
  FROM system.information_schema.tables
  WHERE table_catalog NOT IN ('system', '__databricks_internal', 'samples')
    AND table_type IN ('MANAGED', 'EXTERNAL', 'VIEW')
),
tagged AS (
  SELECT DISTINCT
    catalog_name,
    schema_name,
    table_name
  FROM system.information_schema.table_tags
)
SELECT 
  COUNT(*) AS total_tables,
  SUM(CASE WHEN t.tag_name IS NOT NULL THEN 1 ELSE 0 END) AS tagged_tables,
  SUM(CASE WHEN a.comment IS NOT NULL AND TRIM(a.comment) != '' THEN 1 ELSE 0 END) AS documented_tables,
  ROUND(
    SUM(CASE WHEN t.tag_name IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
  1) AS tag_coverage_pct
FROM all_tables a
LEFT JOIN tagged t
  ON a.table_catalog = t.catalog_name
  AND a.table_schema = t.schema_name
  AND a.table_name = t.table_name
```

### ds_critical_alerts
**Purpose:** Cross-domain critical issues requiring immediate attention  
**Type:** Aggregated alerts  
**Query:**
```sql
-- Cost anomalies
SELECT 
  'Cost Anomaly' AS alert_type,
  'High' AS severity,
  workspace_name,
  CONCAT('Unexpected cost spike: $', ROUND(actual_cost - expected_cost, 0)) AS message,
  detection_time
FROM ${catalog}.${feature_schema}.cost_anomaly_predictions
WHERE detection_time >= CURRENT_DATE() - INTERVAL 1 DAY
  AND anomaly_score > 0.8

UNION ALL

-- Failed jobs
SELECT 
  'Job Failure' AS alert_type,
  'Critical' AS severity,
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)) AS workspace_name,
  CONCAT('Job failed: ', COALESCE(j.job_name, CAST(r.job_id AS STRING))) AS message,
  r.period_start_time AS detection_time
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON r.workspace_id = w.workspace_id
WHERE r.period_start_time >= CURRENT_DATE() - INTERVAL 1 DAY
  AND r.result_state = 'FAILED'

UNION ALL

-- Security high-risk events
SELECT 
  'Security Event' AS alert_type,
  risk_level AS severity,
  CAST(workspace_id AS STRING) AS workspace_name,
  CONCAT(user_identity_email, ' performed ', action_name) AS message,
  TIMESTAMP(CONCAT(event_date, ' ', event_time)) AS detection_time
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY
  AND risk_level = 'Critical'

ORDER BY detection_time DESC
LIMIT 50
```

### ds_domain_trends
**Purpose:** 7-day sparkline trends for each domain  
**Type:** Time series for sparklines  
**Query:**
```sql
WITH daily_metrics AS (
  -- Cost
  SELECT 
    DATE(usage_date) AS metric_date,
    'Cost' AS domain,
    SUM(list_cost) AS value
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY DATE(usage_date)
  
  UNION ALL
  
  -- Reliability
  SELECT 
    DATE(period_start_time) AS metric_date,
    'Reliability' AS domain,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS value
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE period_start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY DATE(period_start_time)
  
  UNION ALL
  
  -- Security
  SELECT 
    event_date AS metric_date,
    'Security' AS domain,
    SUM(CASE WHEN response_status_code < 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS value
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY event_date
)
SELECT 
  domain,
  metric_date,
  ROUND(value, 2) AS value
FROM daily_metrics
ORDER BY domain, metric_date
```

---

## 🎯 Dashboard Layout

### Page 1: Executive Overview
**Purpose:** Single-pane view of platform health  

**Widgets:**
- Overall Health Score (large gauge)
- Domain Health Scores (5 smaller gauges)
- Critical Alerts (scrolling table)
- 7-Day Trend Sparklines (5 mini charts)

### Page 2: Cost at a Glance
**Purpose:** Quick cost insights without navigating to Cost dashboard  

**Widgets:**
- MTD Spend (KPI)
- Tag Coverage % (gauge)
- Serverless Adoption % (gauge)
- Daily Cost Trend (line chart)
- Top Workspaces (bar chart)

### Page 3: Operations Summary
**Purpose:** Combined Reliability + Performance view  

**Widgets:**
- Success Rate (KPI)
- Failed Jobs Today (KPI)
- Avg Query Duration (KPI)
- Slow Queries (table)
- Job Failures (table)

### Page 4: Security & Quality
**Purpose:** Governance overview  

**Widgets:**
- Failed Access Attempts (KPI)
- High-Risk Events (KPI)
- Tag Coverage (gauge)
- Documentation Coverage (gauge)
- Recent Security Events (table)
- Untagged Tables (table)

---

## 📑 Cross-Domain Data Integration

| Unified Metric | Cost Source | Reliability Source | Performance Source | Security Source | Quality Source |
|----------------|-------------|--------------------|--------------------|-----------------|----------------|
| **Health Score** | Tag coverage, Serverless % | Success rate, MTTR | Query perf, Utilization | Event success, Risk events | Doc coverage, Tags |
| **Workspace Activity** | Cost by workspace | Jobs by workspace | Queries by workspace | Events by workspace | Tables by catalog |
| **User Activity** | Cost by owner | Jobs by owner | Queries by user | Events by user | Table owners |
| **Trend Analysis** | Daily cost | Daily success rate | Daily query count | Daily event count | Weekly table growth |

---

## 🔍 Aggregation Patterns

### Cross-Domain Health Score
```sql
SELECT 
  (cost_score * 0.25 + 
   reliability_score * 0.25 + 
   performance_score * 0.20 + 
   security_score * 0.20 + 
   quality_score * 0.10) AS overall_health_score
```

### Domain-Specific Score (Example: Cost)
```sql
SELECT 
  (tag_coverage_pct * 0.40 + 
   serverless_adoption_pct * 0.30 + 
   budget_adherence_pct * 0.30) AS cost_score
```

### Multi-Domain Alerts
```sql
SELECT alert_type, severity, message, detection_time
FROM (
  SELECT ... FROM cost_anomalies
  UNION ALL
  SELECT ... FROM failed_jobs
  UNION ALL
  SELECT ... FROM security_events
)
ORDER BY detection_time DESC, severity DESC
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial documentation |

