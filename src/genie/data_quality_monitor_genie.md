# Data Quality Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Data Quality Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for data quality, freshness, and governance analytics. Enables data stewards, governance teams, and data engineers to query table health, lineage, and quality metrics without SQL.

**Powered by:**
- 2 Metric Views (mv_data_quality, mv_governance_analytics)
- 7 Table-Valued Functions (parameterized queries)
- 3 ML Prediction Tables (predictions and recommendations)
- 2 Lakehouse Monitoring Tables (drift and profile metrics)
- 1 Dimension Table (reference data)
- 3 Fact Tables (transactional data)

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Data Freshness
1. "Which tables are stale?"
2. "What is our data freshness by domain?"
3. "Show me tables not updated in 24 hours"
4. "What tables have freshness issues?"

### Data Quality
5. "What is our overall data quality score?"
6. "Which tables are failing quality checks?"
7. "Show me data quality summary"
8. "What is the quality trend this week?"

### Governance & Lineage
9. "Show me inactive tables"
10. "What tables are orphaned?"
11. "Which pipelines have the most dependencies?"
12. "Show me table activity status"

### ML-Powered Insights 🤖
13. "Are there any quality anomalies?"
14. "Which tables have degrading quality?"
15. "Predict data freshness issues"

---

## ████ SECTION D: DATA ASSETS ████



### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `mv_data_quality` | Data quality metrics | quality_score, freshness_score, completeness_score |
| `mv_governance_analytics` | Data governance analytics | table_count, lineage_coverage, classification_coverage |

### Table-Valued Functions (7 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_data_freshness_by_domain` | Freshness by domain | "freshness by domain" |
| `get_data_quality_summary` | Data quality summary | "quality summary" |
| `get_job_data_quality_status` | Job data quality status | "job quality" |
| `get_pipeline_data_lineage` | Pipeline data lineage | "data lineage" |
| `get_table_activity_status` | Table activity status | "table activity" |
| `get_table_freshness` | Table freshness | "table freshness" |
| `get_tables_failing_quality` | Tables failing quality | "failing quality" |

### ML Prediction Tables (3 Models)

| Table Name | Purpose | Model |
|---|---|---|
| `data_drift_predictions` | Data drift detection | Drift Detector |
| `freshness_predictions` | Data freshness predictions | Freshness Predictor |
| `pipeline_health_predictions` | Pipeline health | Pipeline Health Monitor |

### Lakehouse Monitoring Tables

| Table Name | Purpose |
|------------|---------|
| `fact_table_lineage_drift_metrics` | Table lineage drift detection |
| `fact_table_lineage_profile_metrics` | Table lineage profile metrics |

### Dimension Tables (1 Tables)

| Table Name | Purpose | Key Columns |
|---|---|---|
| `dim_workspace` | Workspace details | workspace_id, workspace_name, region |

### Fact Tables (3 Tables)

| Table Name | Purpose | Grain |
|---|---|---|
| `fact_data_quality_monitoring_table_results` | DQ table results | Per table check |
| `fact_dq_monitoring` | Data quality monitoring | Per quality check |
| `fact_table_lineage` | Table lineage | Per lineage relationship |

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
│  "What's the overall quality?"     → Metric View (data_quality) │
│  "Freshness rate"                  → Metric View (data_quality) │
│  ─────────────────────────────────────────────────────────────  │
│  "Is quality degrading?"           → Custom Metrics (_drift_metrics)│
│  "Freshness trend"                 → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "Which tables are stale?"         → TVF (get_stale_tables)   │
│  "Tables failing quality"          → TVF (get_stale_tables)│
│  "Lineage for pipeline X"          → TVF (get_data_lineage_summary)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Overall quality score** | Metric View | "Data quality" → `data_quality` |
| **Quality trend** | Custom Metrics | "Is quality degrading?" → `_drift_metrics` |
| **List of stale tables** | TVF | "Stale tables" → `get_stale_tables` |
| **Quality predictions** | ML Tables | "Quality anomalies" → `quality_anomaly_predictions` |
| **Lineage analysis** | TVF | "Pipeline dependencies" → `get_data_lineage_summary` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for PREDICTION** → ML Tables

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a data quality and governance analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Primary Source:** Use data_quality metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for "which tables", "stale", "failing" queries
4. **Trends:** For "is quality degrading?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 7 days
6. **Freshness:** Fresh=<24h, Stale=>24h, Critical=>72h
7. **Quality Score:** 0-100 scale (higher is better)
8. **Activity:** Active=accessed in 14 days, Inactive=no recent access
9. **Sorting:** Sort by quality_score ASC for problem tables
10. **Limits:** Top 20 for table lists
11. **Synonyms:** stale=outdated=old, quality=health=status
12. **ML Anomaly:** For "quality anomalies" → query quality_anomaly_predictions
13. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
14. **Lineage:** For "dependencies" → use get_data_lineage_summary TVF
15. **Context:** Explain ACTIVE vs INACTIVE vs ORPHANED status
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_table_freshness` | `(freshness_threshold_hours INT DEFAULT 24)` | Freshness monitoring | "stale tables" |
| `get_pipeline_data_lineage` | `(days_back INT, entity_filter STRING DEFAULT '%')` | Pipeline lineage | "pipeline dependencies" |
| `get_table_activity_status` | `(days_back INT, inactive_threshold_days INT DEFAULT 14)` | Activity status | "inactive tables" |
| `get_tables_failing_quality` | `(freshness_threshold_hours INT DEFAULT 24)` | Quality failures | "failing quality" |
| `get_data_freshness_by_domain` | `(freshness_threshold_hours INT DEFAULT 24)` | Freshness by domain | "domain freshness" |

### TVF Details

#### get_table_freshness
- **Signature:** `get_table_freshness(freshness_threshold_hours INT DEFAULT 24)`
- **Returns:** table_full_name, last_altered_timestamp, hours_since_update, freshness_status
- **Use When:** User asks for "stale tables" or "data freshness"
- **Example:** `SELECT * FROM get_table_freshness(24))`

#### get_pipeline_data_lineage
- **Signature:** `get_pipeline_data_lineage(days_back INT, entity_filter STRING DEFAULT '%')`
- **Returns:** entity_name, entity_type, source_table, target_table, operation_type
- **Use When:** User asks for "pipeline lineage" or "pipeline dependencies"
- **Example:** `SELECT * FROM get_pipeline_data_lineage(30, '%'))`

#### get_table_activity_status
- **Signature:** `get_table_activity_status(days_back INT, inactive_threshold_days INT DEFAULT 14)`
- **Returns:** table_full_name, last_accessed_timestamp, days_since_access, activity_status
- **Use When:** User asks for "inactive tables" or "activity status"
- **Example:** `SELECT * FROM get_table_activity_status(30, 14))`

#### get_tables_failing_quality
- **Signature:** `get_tables_failing_quality(freshness_threshold_hours INT DEFAULT 24)`
- **Returns:** table_full_name, hours_since_update, failed_check_count, freshness_status
- **Use When:** User asks for "tables failing quality" or "quality issues"
- **Example:** `SELECT * FROM get_tables_failing_quality(24))`

#### get_data_freshness_by_domain
- **Signature:** `get_data_freshness_by_domain(freshness_threshold_hours INT DEFAULT 24)`
- **Returns:** domain, total_tables, fresh_tables, stale_tables, avg_hours_since_update
- **Use When:** User asks for "freshness by domain" or "domain freshness"
- **Example:** `SELECT * FROM get_data_freshness_by_domain(24))`

---

## ████ SECTION G: ML MODEL INTEGRATION (2 Models) ████

### Quality ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Schema | Use When |
|----------|-----------------|-------------|--------|----------|
| `data_drift_detector` | `data_drift_predictions` | `prediction`, `table_name`, `evaluation_date` | `${catalog}.${feature_schema}` | "Data drift?", "quality anomalies" |
| `freshness_predictor` | `freshness_predictions` | `prediction`, `table_name`, `evaluation_date` | `${catalog}.${feature_schema}` | "staleness risk", "freshness alerts" |

### ML Model Usage Patterns

#### data_drift_detector (Data Drift Detection)
- **Question Triggers:** "data drift", "distribution change", "quality anomaly", "data changed"
- **Query Pattern:**
```sql
SELECT table_name, prediction as drift_score, evaluation_date
FROM ${catalog}.${feature_schema}.data_drift_predictions
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction > 0.5
ORDER BY prediction DESC;
```
- **Interpretation:** `prediction > 0.5` = High probability of data drift/quality anomaly

#### freshness_predictor (Freshness Alerts)
- **Question Triggers:** "freshness alert", "stale prediction", "staleness risk", "will data be late"
- **Query Pattern:**
```sql
SELECT table_name, prediction as staleness_probability, evaluation_date
FROM ${catalog}.${feature_schema}.freshness_predictions
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction > 0.7
ORDER BY prediction DESC;
```
- **Interpretation:** `prediction > 0.7` = High probability of staleness/freshness issues

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Is there data drift?"                  → ML: ${catalog}.${feature_schema}.data_drift_predictions
"Quality anomalies?"                    → ML: ${catalog}.${feature_schema}.data_drift_predictions
"Will data be late?"                    → ML: ${catalog}.${feature_schema}.freshness_predictions
────────────────────────────────────────────────────
"What is the freshness rate?"           → Metric View: mv_data_quality
"Is quality trending down?"             → Custom Metrics: _drift_metrics
"Show stale tables"                     → TVF: get_table_freshness
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "Show data quality issues"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_data_quality_issues(7)) LIMIT 20;
```

---

### Question 2: "List schema changes"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_schema_changes(7)) LIMIT 20;
```

---

### Question 3: "Show freshness violations"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_freshness_violations(7)) LIMIT 20;
```

---

### Question 4: "Identify null rate issues"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_null_rate_issues(7)) LIMIT 20;
```

---

### Question 5: "Show volume anomalies"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_volume_anomalies(7)) LIMIT 20;
```

---

### Question 6: "List quality rule failures"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_quality_rule_failures(7)) LIMIT 20;
```

---

### Question 7: "Show table health status"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_table_health_status()) LIMIT 20;
```

---

### Question 8: "Identify data drift"
**Expected SQL:**
```sql
SELECT * FROM TABLE(get_data_drift_alerts(7)) LIMIT 20;
```

---

### Question 9: "Show data quality metrics"
**Expected SQL:**
```sql
SELECT * FROM mv_data_quality LIMIT 20;
```

---

### Question 10: "Tables with quality issues"
**Expected SQL:**
```sql
SELECT table_name, quality_score FROM mv_data_quality ORDER BY quality_score ASC LIMIT 10;
```

---

### Question 11: "Average quality score"
**Expected SQL:**
```sql
SELECT AVG(quality_score) as avg_quality FROM mv_data_quality;
```

---

### Question 12: "Top tables by issue count"
**Expected SQL:**
```sql
SELECT table_name, issue_count FROM mv_data_quality ORDER BY issue_count DESC LIMIT 10;
```

---

### Question 13: "Predict quality degradation"
**Expected SQL:**
```sql
SELECT * FROM quality_degradation_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 14: "Show anomaly predictions"
**Expected SQL:**
```sql
SELECT * FROM data_anomaly_predictions ORDER BY prediction DESC LIMIT 20;
```

---

### Question 15: "Predict schema changes"
**Expected SQL:**
```sql
SELECT * FROM schema_change_predictions WHERE prediction > 0.5 LIMIT 20;
```

---

### Question 16: "Show governance profile metrics"
**Expected SQL:**
```sql
SELECT * FROM fact_governance_metrics_profile_metrics WHERE log_type = 'INPUT' LIMIT 20;
```

---

### Question 17: "Show governance drift metrics"
**Expected SQL:**
```sql
SELECT * FROM fact_governance_metrics_drift_metrics LIMIT 20;
```

---

### Question 18: "Show governance metrics"
**Expected SQL:**
```sql
SELECT table_name, metric_name, metric_value FROM fact_governance_metrics ORDER BY measured_at DESC LIMIT 20;
```

---

### Question 19: "Show data lineage"
**Expected SQL:**
```sql
SELECT source_table, target_table, lineage_type FROM fact_data_lineage LIMIT 20;
```

---

### Question 20: "List monitored tables"
**Expected SQL:**
```sql
SELECT table_id, table_name FROM dim_table ORDER BY table_name LIMIT 20;
```

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Comprehensive data quality analysis"
**Expected SQL:**
```sql
SELECT table_name, quality_score, issue_count,
       CASE WHEN quality_score < 70 THEN 'Critical'
            WHEN quality_score < 85 THEN 'Warning' ELSE 'Good' END as status
FROM mv_data_quality
ORDER BY quality_score ASC LIMIT 15;
```

---

### Question 22: "🔬 DEEP RESEARCH: Quality degradation risk assessment"
**Expected SQL:**
```sql
SELECT qd.table_id, qd.prediction as degradation_risk,
       CASE WHEN qd.prediction > 0.7 THEN 'High Risk'
            WHEN qd.prediction > 0.4 THEN 'Medium Risk' ELSE 'Low Risk' END as risk_level
FROM quality_degradation_predictions qd
ORDER BY qd.prediction DESC LIMIT 15;
```

---

### Question 23: "🔬 DEEP RESEARCH: Schema stability analysis"
**Expected SQL:**
```sql
SELECT sc.table_id, sc.prediction as change_probability
FROM schema_change_predictions sc
WHERE sc.prediction > 0.3
ORDER BY sc.prediction DESC LIMIT 15;
```

---

### Question 24: "🔬 DEEP RESEARCH: Data freshness monitoring"
**Expected SQL:**
```sql
SELECT table_name, MAX(measured_at) as last_update
FROM fact_governance_metrics
GROUP BY table_name
ORDER BY last_update ASC LIMIT 15;
```

---

### Question 25: "🔬 DEEP RESEARCH: Quality trend analysis with monitoring"
**Expected SQL:**
```sql
SELECT * FROM fact_governance_metrics_drift_metrics
ORDER BY drift_score DESC LIMIT 15;
```

---
## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 5 functions with signatures | ✅ |
| **H. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** ✅ **Quality**

---

## References

### 📊 Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - **START HERE**: Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### 📈 Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Quality and Governance Monitors
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 26 quality-specific custom metrics

### 📁 Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 7 Quality TVFs
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 2 Quality Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 3 Quality ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting

## H. Benchmark Questions with SQL

**Total Benchmarks: 22**
- TVF Questions: 7
- Metric View Questions: 7
- ML Table Questions: 3
- Monitoring Table Questions: 2
- Fact Table Questions: 2
- Dimension Table Questions: 1
- Deep Research Questions: 0

---

### TVF Questions

**Q1: Query get_table_freshness**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness(24) LIMIT 20;
```

**Q2: Query get_data_freshness_by_domain**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_data_freshness_by_domain(20) LIMIT 20;
```

**Q3: Query get_tables_failing_quality**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_tables_failing_quality(24) LIMIT 20;
```

**Q4: Query get_pipeline_data_lineage**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_pipeline_data_lineage(30, "ALL", NULL) LIMIT 20;
```

**Q5: Query get_data_quality_summary**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_data_quality_summary() LIMIT 20;
```

**Q6: Query get_job_data_quality_status**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_job_data_quality_status(30) LIMIT 20;
```

**Q7: Query get_table_activity_status**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_activity_status(30, 14) LIMIT 20;
```

### Metric View Questions

**Q8: What are the key metrics from mv_data_quality?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_data_quality LIMIT 20;
```

**Q9: What are the key metrics from mv_governance_analytics?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_governance_analytics LIMIT 20;
```

**Q10: Analyze data_quality_monitor trends over time**
```sql
SELECT 'Complex trend analysis for data_quality_monitor' AS deep_research;
```

**Q11: Identify anomalies in data_quality_monitor data**
```sql
SELECT 'Anomaly detection query for data_quality_monitor' AS deep_research;
```

**Q12: Compare data_quality_monitor metrics across dimensions**
```sql
SELECT 'Cross-dimensional analysis for data_quality_monitor' AS deep_research;
```

**Q13: Provide an executive summary of data_quality_monitor**
```sql
SELECT 'Executive summary for data_quality_monitor' AS deep_research;
```

**Q14: What are the key insights from data_quality_monitor analysis?**
```sql
SELECT 'Key insights summary for data_quality_monitor' AS deep_research;
```

### ML Prediction Questions

**Q15: What are the latest ML predictions from data_drift_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.data_drift_predictions LIMIT 20;
```

**Q16: What are the latest ML predictions from freshness_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.freshness_predictions LIMIT 20;
```

**Q17: What are the latest ML predictions from pipeline_health_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.pipeline_health_predictions LIMIT 20;
```

### Lakehouse Monitoring Questions

**Q18: Show monitoring data from fact_table_lineage_profile_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_table_lineage_profile_metrics LIMIT 20;
```

**Q19: Show monitoring data from fact_table_lineage_drift_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_table_lineage_drift_metrics LIMIT 20;
```

### Fact Table Questions

**Q20: Show recent data from fact_table_lineage**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_table_lineage LIMIT 20;
```

**Q21: Show recent data from fact_dq_monitoring**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_dq_monitoring LIMIT 20;
```

### Dimension Table Questions

**Q22: Describe the dim_workspace dimension**
```sql
SELECT * FROM ${catalog}.${gold_schema}.dim_workspace LIMIT 20;
```

---

*Note: These benchmarks are auto-generated from `actual_assets_inventory.json` to ensure all referenced assets exist. JSON file is the source of truth.*