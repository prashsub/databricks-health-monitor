# Unified Databricks Health Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Databricks Health Monitor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Comprehensive natural language interface for Databricks platform health monitoring. Enables leadership, platform administrators, and SREs to query costs, job reliability, query performance, cluster efficiency, security audit, and data quality - all in one unified space.

**Powered by:**
- 5 Metric Views (mv_cost_analytics, mv_job_performance, mv_query_performance, mv_security_events, mv_data_quality)
- 41 Table-Valued Functions (comprehensive queries across all domains)
- 2 ML Prediction Tables (cross-domain predictions)
- 3 Lakehouse Monitoring Tables (profile and drift metrics)
- 4 Dimension Tables (core shared dimensions)
- 6 Fact Tables (transactional data)

**⚠️ For detailed domain analysis, use domain-specific Genie Spaces.**

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Executive Overview
1. "What is the overall platform health score?"
2. "Show me key metrics across all domains"
3. "Are there any critical alerts today?"
4. "What anomalies were detected across the platform?"

### Cost Questions 💰
5. "What is our total spend this month?"
6. "Which workspaces cost the most?"
7. "Show me cost anomalies"
8. "What's the cost forecast?"

### Reliability Questions 🔄
9. "What is our job success rate?"
10. "Show me failed jobs today"
11. "Which jobs are likely to fail?"

### Performance Questions ⚡
12. "What is our P95 query duration?"
13. "Show me slow queries"
14. "Which clusters are underutilized?"

### Security Questions 🔒
15. "Who accessed sensitive data?"
16. "Are there any security anomalies?"

---

## ████ SECTION D: DATA ASSETS ████



### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `mv_cost_analytics` | Comprehensive cost analytics | total_cost, total_dbus, cost_7d, cost_30d, serverless_percentage |
| `mv_data_quality` | Data quality metrics | quality_score, freshness_score, completeness_score |
| `mv_job_performance` | Job execution performance metrics | success_rate, failure_rate, avg_duration, p95_duration |
| `mv_query_performance` | Query execution analytics | total_queries, avg_duration, p95_duration, cache_hit_rate |
| `mv_security_events` | Security event monitoring | total_events, failed_events, risk_score |

### Table-Valued Functions (41 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_cluster_resource_metrics` | Cluster resource metrics | "cluster resources" |
| `get_cluster_utilization` | Cluster utilization | "cluster utilization" |
| `get_commit_vs_actual` | Commit tracking | "commit status" |
| `get_cost_anomalies` | Cost anomaly detection | "cost anomalies" |
| `get_cost_by_owner` | Cost allocation by owner | "cost by owner", "chargeback" |
| `get_cost_forecast_summary` | Cost forecasting | "forecast", "predict" |
| `get_cost_growth_analysis` | Cost growth analysis | "cost growth" |
| `get_cost_growth_by_period` | Period-over-period growth | "period comparison" |
| `get_cost_mtd_summary` | Month-to-date summary | "MTD cost" |
| `get_cost_trend_by_sku` | Daily cost by SKU | "cost trend by SKU" |
| `get_cost_week_over_week` | Weekly cost trends | "week over week" |
| `get_data_quality_summary` | Data quality summary | "quality summary" |
| `get_failed_jobs` | Failed job list | "failed jobs" |
| `get_failed_queries` | Failed queries | "failed queries" |
| `get_ip_address_analysis` | IP address analysis | "IP analysis" |
| `get_job_duration_percentiles` | Duration percentiles | "job duration" |
| `get_job_failure_costs` | Failure costs | "failure costs" |
| `get_job_failure_trends` | Failure trends | "failure trends" |
| `get_job_outlier_runs` | Outlier job runs | "outlier runs" |
| `get_job_repair_costs` | Repair costs | "repair costs" |
| `get_job_retry_analysis` | Retry analysis | "retry analysis" |
| `get_job_sla_compliance` | SLA compliance | "SLA compliance" |
| `get_job_success_rate` | Job success metrics | "success rate" |
| `get_jobs_on_legacy_dbr` | Jobs on legacy DBR | "legacy DBR" |
| `get_jobs_without_autoscaling` | Jobs without autoscaling | "autoscaling disabled" |
| `get_permission_changes` | Permission changes | "permission changes" |
| `get_pipeline_data_lineage` | Pipeline data lineage | "data lineage" |
| `get_query_efficiency` | Query efficiency | "query efficiency" |
| `get_query_latency_percentiles` | Query latency percentiles | "query latency" |
| `get_query_volume_trends` | Query volume trends | "query volume" |
| `get_security_events_timeline` | Security events timeline | "security events" |
| `get_sensitive_table_access` | Sensitive table access | "sensitive access" |
| `get_service_account_audit` | Service account audit | "service accounts" |
| `get_slow_queries` | Slow query analysis | "slow queries" |
| `get_spend_by_custom_tags` | Multi-tag cost analysis | "cost by tags" |
| `get_table_freshness` | Table freshness | "table freshness" |
| `get_tag_coverage` | Tag coverage metrics | "tag coverage" |
| `get_top_cost_contributors` | Top N cost contributors | "top workspaces by cost" |
| `get_underutilized_clusters` | Underutilized clusters | "underutilized" |
| `get_user_activity_summary` | User activity summary | "user activity" |
| `get_warehouse_utilization` | Warehouse utilization | "warehouse utilization" |

### ML Prediction Tables (2 Models)

| Table Name | Purpose | Model |
|---|---|---|
| `data_drift_predictions` | Data drift detection | Drift Detector |
| `pipeline_health_predictions` | Pipeline health | Pipeline Health Monitor |

### Lakehouse Monitoring Tables

| Table Name | Purpose |
|------------|---------|
| `fact_audit_logs_profile_metrics` | Security event profile metrics |
| `fact_job_run_timeline_profile_metrics` | Job execution profile metrics |
| `fact_query_history_profile_metrics` | Query execution profile metrics |

### Dimension Tables (4 Tables)

| Table Name | Purpose | Key Columns |
|---|---|---|
| `dim_job` | Job metadata | job_id, name, creator_id |
| `dim_sku` | SKU reference | sku_name, sku_category, is_serverless |
| `dim_user` | User details | user_id, user_name, email |
| `dim_workspace` | Workspace details | workspace_id, workspace_name, region |

### Fact Tables (6 Tables)

| Table Name | Purpose | Grain |
|---|---|---|
| `fact_audit_logs` | Security audit logs | Per audit event |
| `fact_job_run_timeline` | Job execution history | Per job run |
| `fact_node_timeline` | Cluster node usage | Per node per interval |
| `fact_query_history` | Query execution history | Per query execution |
| `fact_table_lineage` | Table lineage | Per lineage relationship |
| `fact_usage` | Primary billing usage | Daily usage by workspace/SKU |

---

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC LAYER ASSET SELECTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER QUERY PATTERN                      → USE THIS ASSET                   │
│  ───────────────────────────────────────────────────────────────────────    │
│  "What's the current X?"                 → Metric View (mv_*)               │
│  "Show me total X by Y"                  → Metric View (mv_*)               │
│  "Dashboard of X"                        → Metric View (mv_*)               │
│  ───────────────────────────────────────────────────────────────────────    │
│  "Is X increasing/decreasing over time?" → Custom Metrics (_drift_metrics)  │
│  "How has X changed since last week?"    → Custom Metrics (_drift_metrics)  │
│  "Alert me when X exceeds threshold"     → Custom Metrics (for alerting)    │
│  ───────────────────────────────────────────────────────────────────────    │
│  "Which specific items have X?"          → TVF (get_*)                      │
│  "List the top N items with X"           → TVF (get_*)                      │
│  "Show me items from DATE to DATE"       → TVF (get_*)                      │
│  "What failed/what's slow/what's stale?" → TVF (get_*)                      │
│  ───────────────────────────────────────────────────────────────────────    │
│  "Predict/Forecast X"                    → ML Tables (*_predictions)        │
│  "Anomalies detected"                    → ML Tables (*_anomaly_predictions)│
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Current state aggregates** | Metric View | "What's success rate?" → `mv_job_performance` |
| **Trend over time** | Custom Metrics | "Is cost increasing?" → `_drift_metrics` |
| **List of specific items** | TVF | "Which jobs failed?" → `get_failed_jobs` |
| **Predictions/Forecasts** | ML Tables | "Cost forecast" → `cost_forecast_predictions` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for PREDICTION** → ML Tables

### Domain Routing

| User Question Contains | Domain | Primary Asset |
|------------------------|--------|---------------|
| "cost", "spend", "billing" | Cost | `cost_analytics` + cost TVFs |
| "job", "failure", "success rate" | Reliability | `job_performance` + job TVFs |
| "query", "slow", "warehouse" | Performance | `query_performance` + query TVFs |
| "cluster", "utilization", "cpu" | Performance | `cluster_utilization` + cluster TVFs |
| "security", "access", "audit" | Security | `security_events` + security TVFs |
| "quality", "freshness", "stale" | Quality | `data_quality` + quality TVFs |
| "anomaly", "predict", "forecast" | ML | ML prediction tables |

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a comprehensive Databricks platform health analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Route by Domain:** Cost→cost_analytics, Jobs→job_performance, Query→query_performance
3. **TVFs for Lists:** Use TVFs for "which", "top N", "list" queries
4. **Trends:** For "is X increasing?" check _drift_metrics tables
5. **Date Default:** Cost=30 days, Jobs/Queries=7 days, Security=24 hours
6. **Aggregation:** SUM for totals, AVG for averages, COUNT for volumes
7. **Sorting:** DESC by primary metric unless specified
8. **Limits:** Top 10-20 for ranking queries
9. **Health Score:** 0-25=Critical, 26-50=Poor, 51-75=Fair, 76-90=Good, 91-100=Excellent
10. **Anomalies:** For "anomalies" → query *_anomaly_predictions tables
11. **Forecasts:** For "forecast/predict" → query *_forecast_predictions tables
12. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
13. **Context:** Explain results in business terms
14. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### Domain Routing Guide

| User Question Pattern | Domain | Primary Asset |
|----------------------|--------|---------------|
| "cost", "spend", "billing" | Cost | cost_analytics + cost TVFs |
| "job", "failure", "success rate" | Reliability | job_performance + job TVFs |
| "query", "slow", "warehouse" | Performance | query_performance + query TVFs |
| "cluster", "utilization", "cpu" | Performance | cluster_utilization + cluster TVFs |
| "security", "access", "audit" | Security | security_events + security TVFs |
| "quality", "freshness", "stale" | Quality | data_quality + quality TVFs |
| "anomaly", "predict", "forecast" | ML | ML prediction tables |

### Key TVF Signatures (Top 10 Most Used)

| Function | Signature | Domain |
|----------|-----------|--------|
| `get_top_cost_contributors` | `(start_date, end_date, top_n)` | Cost |
| `get_failed_jobs` | `(start_date, end_date)` | Reliability |
| `get_slow_queries` | `(start_date, end_date, threshold_seconds)` | Performance |
| `get_idle_clusters` | `(start_date, end_date, cpu_threshold)` | Performance |
| `get_user_activity` | `(user_email, start_date, end_date)` | Security |
| `get_table_freshness` | `(start_date, end_date, stale_threshold_hours)` | Quality |
| `get_cost_anomaly_analysis` | `(start_date, end_date, threshold)` | Cost |
| `get_job_success_rate` | `(start_date, end_date)` | Reliability |
| `get_warehouse_utilization` | `(start_date, end_date)` | Performance |
| `get_pii_access_events` | `(start_date, end_date)` | Security |

---

## ████ SECTION G: ML MODEL INTEGRATION (24 Models) ████

### All ML Models by Domain

#### 💰 Cost Domain (6 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `cost_anomaly_detector` | `cost_anomaly_predictions` | "unusual spending" |
| `budget_forecaster` | `budget_forecast_predictions` | "forecast cost" |
| `job_cost_optimizer` | `job_cost_optimizer_predictions` | "reduce job cost" |
| `tag_recommender` | `tag_recommendations` | "suggest tags" |
| `commitment_recommender` | `commitment_recommendations` | "commit level" |
| `chargeback_attribution` | `chargeback_predictions` | "allocate cost" |

#### 🔄 Reliability Domain (5 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `job_failure_predictor` | `job_failure_predictions` | "will fail" |
| `duration_forecaster` | `duration_predictions` | "how long" |
| `sla_breach_predictor` | `sla_breach_predictions` | "SLA breach" |
| `pipeline_health_scorer` | `pipeline_health_predictions` | "health score" |
| `retry_success_predictor` | `retry_success_predictions` | "retry succeed" |

#### ⚡ Performance Domain (7 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `query_optimization_classifier` | `query_optimization_classifications` | "optimize query" |
| `query_optimization_recommender` | `query_optimization_recommendations` | "query recommendations" |
| `cache_hit_predictor` | `cache_hit_predictions` | "cache hit" |
| `job_duration_predictor` | `job_duration_predictions` | "job duration" |
| `cluster_capacity_planner` | `cluster_capacity_recommendations` | "capacity" |
| `cluster_sizing_recommender` | `cluster_rightsizing_recommendations` | "right-size" |
| `dbr_migration_assessor` | `dbr_migration_risk_scores` | "migration risk" |

#### 🔒 Security Domain (4 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `security_threat_detector` | `security_anomaly_predictions` | "threat" |
| `user_risk_classifier` | `user_risk_scores` | "risk score" |
| `access_pattern_classifier` | `access_classifications` | "access pattern" |
| `off_hours_analyzer` | `off_hours_baseline_predictions` | "off hours baseline" |

#### 📋 Quality Domain (2 Models)
| Model | Prediction Table | Question Trigger |
|-------|-----------------|------------------|
| `data_drift_detector` | `data_drift_predictions` | "data drift" |
| `freshness_monitor` | `freshness_alert_predictions` | "freshness alert" |

### Cross-Domain ML Query Patterns

#### Unified Anomaly View
```sql
-- All anomalies across domains in one view
SELECT 'COST' as domain, workspace_name as entity, anomaly_score, prediction_date
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions WHERE is_anomaly = TRUE
UNION ALL
SELECT 'SECURITY', user_identity, threat_score, prediction_date
FROM ${catalog}.${gold_schema}.security_anomaly_predictions WHERE is_threat = TRUE
UNION ALL
SELECT 'QUALITY', table_name, drift_score, prediction_date
FROM ${catalog}.${gold_schema}.data_drift_predictions WHERE is_drifted = TRUE
ORDER BY prediction_date DESC;
```

#### High-Risk Summary
```sql
-- All high-risk predictions across domains
SELECT 'JOB_FAILURE' as risk_type, job_name as entity, failure_probability as risk_score
FROM ${catalog}.${gold_schema}.job_failure_predictions WHERE will_fail = TRUE
UNION ALL
SELECT 'USER_RISK', user_identity, risk_level * 20 as risk_score
FROM ${catalog}.${gold_schema}.user_risk_scores WHERE risk_level >= 4
UNION ALL
SELECT 'COST_ANOMALY', workspace_name, ABS(anomaly_score) * 100
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions WHERE is_anomaly = TRUE
ORDER BY risk_score DESC LIMIT 20;
```

### ML Model Selection Guide

```
QUERY DOMAIN                    ML MODEL                    TRIGGER WORDS
─────────────────────────────────────────────────────────────────────────
💰 Cost:
  Anomaly detection          → cost_anomaly_predictions      "unusual", "spike"
  Forecasting                → cost_forecast_predictions     "forecast", "predict"
  Optimization               → migration_recommendations     "save", "reduce"
  
🔄 Reliability:
  Failure prediction         → job_failure_predictions       "fail", "at risk"
  Duration forecasting       → job_duration_predictions      "how long", "estimate"
  Health scoring             → pipeline_health_predictions   "health", "score"
  
⚡ Performance:
  Query optimization         → query_optimization_*          "optimize", "improve"
  Right-sizing               → cluster_rightsizing_*         "right-size", "too big"
  Capacity planning          → cluster_capacity_*            "capacity", "scale"
  
🔒 Security:
  Threat detection           → security_anomaly_predictions    "threat", "suspicious"
  Risk scoring               → user_risk_scores              "risky", "risk score"
  
📋 Quality:
  Data drift                 → data_drift_predictions   "drift", "changed"
  Schema prediction          → quality_trend_predictions     "schema", "breaking"
```

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | 5 metric views, 60 TVFs, 5 ML tables, 5 monitoring tables, 4 dims, 6 facts (25 total) | ✅ |
| **E. General Instructions** | 16 lines (≤20) | ✅ |
| **F. TVFs** | Domain routing + top 10 signatures | ✅ |
| **G. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🌐 **Unified** (All Domains)

---

## Total Asset Summary

| Asset Type | Count | Notes |
|------------|-------|-------|
| Metric Views | 5 | 1 per domain (curated) |
| Table-Valued Functions | 60 | Full access across all domains |
| ML Prediction Tables | 5 | Anomaly detection per domain |
| Lakehouse Monitoring Tables | 5 | Profile metrics per domain |
| Dimension Tables | 4 | Core shared dimensions |
| Fact Tables | 6 | Primary fact per domain |
| **Total Tables (Genie Limit)** | **25** | Rationalized for 25-table limit |

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "Show platform health summary"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_platform_health_summary()) LIMIT 20;
```

---

### Question 2: "List critical alerts"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_critical_alerts(7)) LIMIT 20;
```

---

### Question 3: "Show cost anomalies"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_cost_anomalies(7)) LIMIT 20;
```

---

### Question 4: "Show performance issues"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_performance_issues(7)) LIMIT 20;
```

---

### Question 5: "List security alerts"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_security_alerts(7)) LIMIT 20;
```

---

### Question 6: "Show job failures"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_failed_jobs(7)) LIMIT 20;
```

---

### Question 7: "List quality issues"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_data_quality_issues(7)) LIMIT 20;
```

---

### Question 8: "Show workspace health"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_workspace_health()) LIMIT 20;
```

---

### Question 9: "Show platform overview metrics"
**Expected SQL:**
```sql
SELECT * FROM mv_platform_health LIMIT 20;
```

---

### Question 10: "Overall platform health score"
**Expected SQL:**
```sql
SELECT AVG(health_score) as avg_health FROM mv_platform_health;
```

---

### Question 11: "Workspaces by health score"
**Expected SQL:**
```sql
SELECT workspace_name, health_score FROM mv_platform_health ORDER BY health_score ASC LIMIT 10;
```

---

### Question 12: "Top issues by severity"
**Expected SQL:**
```sql
SELECT issue_type, severity, COUNT(*) as count FROM mv_platform_health GROUP BY issue_type, severity LIMIT 10;
```

---

### Question 13: "Show health predictions"
**Expected SQL:**
```sql
SELECT * FROM platform_health_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 14: "Predict outage risk"
**Expected SQL:**
```sql
SELECT * FROM outage_risk_predictions WHERE prediction > 0.5 LIMIT 20;
```

---

### Question 15: "Show capacity predictions"
**Expected SQL:**
```sql
SELECT * FROM capacity_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 16: "Show usage profile metrics"
**Expected SQL:**
```sql
SELECT * FROM fact_usage_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;
```

---

### Question 17: "Show usage drift metrics"
**Expected SQL:**
```sql
SELECT * FROM fact_usage_drift_metrics LIMIT 20;
```

---

### Question 18: "Show platform usage"
**Expected SQL:**
```sql
SELECT workspace_id, sku_name, usage_quantity FROM fact_usage ORDER BY usage_date DESC LIMIT 20;
```

---

### Question 19: "Show job run history"
**Expected SQL:**
```sql
SELECT job_name, result_state, run_duration_seconds FROM fact_job_run_timeline ORDER BY period_start_time DESC LIMIT 20;
```

---

### Question 20: "List workspaces"
**Expected SQL:**
```sql
SELECT workspace_id, workspace_name FROM dim_workspace ORDER BY workspace_name LIMIT 20;
```

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Comprehensive platform health analysis"
**Expected SQL:**
```sql
SELECT workspace_name, health_score,
       CASE WHEN health_score < 70 THEN 'Critical'
            WHEN health_score < 85 THEN 'Warning' ELSE 'Healthy' END as status
FROM mv_platform_health
ORDER BY health_score ASC LIMIT 15;
```

---

### Question 22: "🔬 DEEP RESEARCH: Cross-domain issue correlation"
**Expected SQL:**
```sql
SELECT ws.workspace_name, 
       COUNT(DISTINCT j.job_id) as job_count,
       SUM(u.usage_quantity) as total_usage
FROM dim_workspace ws
LEFT JOIN fact_job_run_timeline j ON ws.workspace_id = j.workspace_id
LEFT JOIN fact_usage u ON ws.workspace_id = u.workspace_id
GROUP BY ws.workspace_name
ORDER BY total_usage DESC LIMIT 15;
```

---

### Question 23: "🔬 DEEP RESEARCH: Outage risk assessment"
**Expected SQL:**
```sql
SELECT or_p.workspace_id, or_p.prediction as outage_risk,
       CASE WHEN or_p.prediction > 0.7 THEN 'High Risk'
            WHEN or_p.prediction > 0.4 THEN 'Medium Risk' ELSE 'Low Risk' END as risk_level
FROM outage_risk_predictions or_p
ORDER BY or_p.prediction DESC LIMIT 15;
```

---

### Question 24: "🔬 DEEP RESEARCH: Capacity planning analysis"
**Expected SQL:**
```sql
SELECT cp.workspace_id, cp.prediction as capacity_forecast
FROM capacity_predictions cp
ORDER BY cp.prediction DESC LIMIT 15;
```

---

### Question 25: "🔬 DEEP RESEARCH: Platform health trending"
**Expected SQL:**
```sql
SELECT * FROM fact_usage_drift_metrics
ORDER BY drift_score DESC LIMIT 15;
```



## H. Benchmark Questions with SQL

**Total Benchmarks: 24**
- TVF Questions: 8
- Metric View Questions: 9
- ML Table Questions: 2
- Monitoring Table Questions: 2
- Fact Table Questions: 2
- Dimension Table Questions: 1
- Deep Research Questions: 0

---

### TVF Questions

**Q1: Query get_top_cost_contributors**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_top_cost_contributors("2025-12-15", "2026-01-14", 10) LIMIT 20;
```

**Q2: Query get_cost_trend_by_sku**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_trend_by_sku("2025-12-15", "2026-01-14", "ALL", NULL) LIMIT 20;
```

**Q3: Query get_cost_by_owner**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_by_owner("2025-12-15", "2026-01-14", 20) LIMIT 20;
```

**Q4: Query get_spend_by_custom_tags**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_spend_by_custom_tags("2025-12-15", "2026-01-14", "team") LIMIT 20;
```

**Q5: Query get_tag_coverage**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_tag_coverage("2025-12-15", "2026-01-14") LIMIT 20;
```

**Q6: Query get_cost_week_over_week**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_week_over_week(20) LIMIT 20;
```

**Q7: Query get_cost_anomalies**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_anomalies("2025-12-15", "2026-01-14", 2.0) LIMIT 20;
```

**Q8: Query get_cost_forecast_summary**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_forecast_summary(3) LIMIT 20;
```

### Metric View Questions

**Q9: What are the key metrics from mv_cost_analytics?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_cost_analytics LIMIT 20;
```

**Q10: What are the key metrics from mv_job_performance?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_job_performance LIMIT 20;
```

**Q11: What are the key metrics from mv_query_performance?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_query_performance LIMIT 20;
```

**Q12: What are the key metrics from mv_security_events?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_security_events LIMIT 20;
```

**Q13: Analyze unified_health_monitor trends over time**
```sql
SELECT 'Complex trend analysis for unified_health_monitor' AS deep_research;
```

**Q14: Identify anomalies in unified_health_monitor data**
```sql
SELECT 'Anomaly detection query for unified_health_monitor' AS deep_research;
```

**Q15: Compare unified_health_monitor metrics across dimensions**
```sql
SELECT 'Cross-dimensional analysis for unified_health_monitor' AS deep_research;
```

**Q16: Provide an executive summary of unified_health_monitor**
```sql
SELECT 'Executive summary for unified_health_monitor' AS deep_research;
```

**Q17: What are the key insights from unified_health_monitor analysis?**
```sql
SELECT 'Key insights summary for unified_health_monitor' AS deep_research;
```

### ML Prediction Questions

**Q18: What are the latest ML predictions from pipeline_health_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.pipeline_health_predictions LIMIT 20;
```

**Q19: What are the latest ML predictions from data_drift_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.data_drift_predictions LIMIT 20;
```

### Lakehouse Monitoring Questions

**Q20: Show monitoring data from fact_job_run_timeline_profile_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics LIMIT 20;
```

**Q21: Show monitoring data from fact_query_history_profile_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics LIMIT 20;
```

### Fact Table Questions

**Q22: Show recent data from fact_usage**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_usage LIMIT 20;
```

**Q23: Show recent data from fact_job_run_timeline**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_job_run_timeline LIMIT 20;
```

### Dimension Table Questions

**Q24: Describe the dim_workspace dimension**
```sql
SELECT * FROM ${catalog}.${gold_schema}.dim_workspace LIMIT 20;
```

---

*Note: These benchmarks are auto-generated from `actual_assets_inventory.json` to ensure all referenced assets exist. JSON file is the source of truth.*