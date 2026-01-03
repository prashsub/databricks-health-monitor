# Data Quality Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Data Quality Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for data quality, freshness, and governance analytics. Enables data stewards, governance teams, and data engineers to query table health, lineage, and quality metrics without SQL. Powered by Data Quality Metric Views, 7 Quality TVFs, 3 ML Models for quality prediction, and Lakehouse Monitoring profile metrics.

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
| `data_quality` | Quality monitoring | total_tables, quality_score, completeness_rate, validity_rate |
| `ml_intelligence` | ML model inference | prediction_count, accuracy, drift_score |

### Table-Valued Functions (7 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_table_freshness` | Table freshness metrics | "stale tables" |
| `get_job_data_quality_status` | Job quality status | "job quality" |
| `get_data_freshness_by_domain` | Freshness by domain | "freshness by domain" |
| `get_data_quality_summary` | Quality summary | "quality score" |
| `get_tables_failing_quality` | Failed quality checks | "failing quality" |
| `get_table_activity_status` | Activity status | "inactive tables" |
| `get_pipeline_data_lineage` | Pipeline lineage | "pipeline dependencies" |

### ML Prediction Tables 🤖

| Table Name | Purpose |
|------------|---------|
| `quality_anomaly_predictions` | Quality anomaly detection |
| `quality_trend_predictions` | Quality score forecasts |
| `freshness_alert_predictions` | Staleness probability predictions |

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_table_quality_profile_metrics` | Table quality metrics (quality_score, completeness_rate, validity_rate) |
| `fact_governance_metrics_profile_metrics` | Governance metrics (tag_coverage, lineage_coverage) |
| `fact_table_quality_drift_metrics` | Quality drift (quality_score_drift) |

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**Always include these filters when querying Lakehouse Monitoring tables:**

```sql
-- ✅ CORRECT: Get data quality metrics
SELECT 
  window.start AS window_start,
  quality_score,
  completeness_rate,
  validity_rate
FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
  AND slice_key IS NULL          -- For overall metrics
ORDER BY window.start DESC;

-- ✅ CORRECT: Get quality by schema (sliced)
SELECT 
  slice_value AS schema_name,
  AVG(quality_score) AS avg_quality_score
FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'schema_name'
GROUP BY slice_value
ORDER BY avg_quality_score ASC;

-- ✅ CORRECT: Get quality drift
SELECT 
  window.start AS window_start,
  quality_score_drift
FROM ${catalog}.${gold_schema}.fact_table_quality_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC;
```

#### Available Slicing Dimensions (Quality Monitor)

| Slice Key | Use Case |
|-----------|----------|
| `catalog_name` | Quality by catalog |
| `schema_name` | Quality by schema |
| `table_name` | Per-table metrics |
| `has_critical_violations` | Critical issues filter |

### Dimension Tables (from gold_layer_design/yaml/mlflow/, model_serving/, shared/)

| Table Name | Purpose | Key Columns | YAML Source |
|------------|---------|-------------|-------------|
| `dim_experiment` | MLflow experiments | experiment_id, experiment_name | mlflow/dim_experiment.yaml |
| `dim_served_entities` | Model serving endpoints | entity_id, entity_name, endpoint_name | model_serving/dim_served_entities.yaml |
| `dim_workspace` | Workspace reference | workspace_id, workspace_name | shared/dim_workspace.yaml |

### Fact Tables (from gold_layer_design/yaml/governance/, data_classification/, data_quality_monitoring/, storage/, mlflow/, model_serving/, marketplace/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_table_lineage` | Lineage events | Per access event | governance/fact_table_lineage.yaml |
| `fact_column_lineage` | Column-level lineage | Per column access | governance/fact_column_lineage.yaml |
| `fact_data_classification` | Data classification tags | Per table/column | data_classification/fact_data_classification.yaml |
| `fact_data_classification_results` | Classification scan results | Per scan | data_classification/fact_data_classification_results.yaml |
| `fact_dq_monitoring` | DQ monitoring results | Per check | data_quality_monitoring/fact_dq_monitoring.yaml |
| `fact_data_quality_monitoring_table_results` | Table-level DQ results | Per table per run | data_quality_monitoring/fact_data_quality_monitoring_table_results.yaml |
| `fact_predictive_optimization` | Predictive optimization events | Per optimization | storage/fact_predictive_optimization.yaml |
| `fact_mlflow_runs` | MLflow run history | Per run | mlflow/fact_mlflow_runs.yaml |
| `fact_mlflow_run_metrics_history` | MLflow metrics over time | Per metric per step | mlflow/fact_mlflow_run_metrics_history.yaml |
| `fact_endpoint_usage` | Model serving usage | Per request | model_serving/fact_endpoint_usage.yaml |
| `fact_payload_logs` | Model serving payloads | Per inference | model_serving/fact_payload_logs.yaml |
| `fact_listing_access` | Marketplace listing access | Per access | marketplace/fact_listing_access.yaml |
| `fact_listing_funnel` | Marketplace funnel events | Per funnel event | marketplace/fact_listing_funnel.yaml |

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
│  "Which tables are stale?"         → TVF (get_table_freshness)   │
│  "Tables failing quality"          → TVF (get_tables_failing_quality)│
│  "Lineage for pipeline X"          → TVF (get_pipeline_data_lineage)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Overall quality score** | Metric View | "Data quality" → `data_quality` |
| **Quality trend** | Custom Metrics | "Is quality degrading?" → `_drift_metrics` |
| **List of stale tables** | TVF | "Stale tables" → `get_table_freshness` |
| **Quality predictions** | ML Tables | "Quality anomalies" → `quality_anomaly_predictions` |
| **Lineage analysis** | TVF | "Pipeline dependencies" → `get_pipeline_data_lineage` |

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
14. **Lineage:** For "dependencies" → use get_pipeline_data_lineage TVF
15. **Context:** Explain ACTIVE vs INACTIVE vs ORPHANED status
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION F: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_table_freshness` | `(start_date STRING, end_date STRING, stale_threshold_hours INT)` | Freshness | "stale tables" |
| `get_data_quality_summary` | `(start_date STRING, end_date STRING)` | Quality summary | "quality score" |
| `get_tables_failing_quality` | `(start_date STRING, end_date STRING)` | Failed checks | "failing quality" |
| `get_table_activity_status` | `(start_date STRING, end_date STRING, activity_days INT)` | Activity status | "inactive tables" |
| `get_pipeline_data_lineage` | `(pipeline_name STRING, start_date STRING, end_date STRING)` | Lineage | "dependencies" |

### TVF Details

#### get_table_freshness
- **Signature:** `get_table_freshness(start_date STRING, end_date STRING, stale_threshold_hours INT)`
- **Returns:** table_name, last_update, hours_since_update, freshness_status
- **Use When:** User asks for "stale tables" or "data freshness"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness('2024-12-01', '2024-12-31', 24)`

#### get_data_quality_summary
- **Signature:** `get_data_quality_summary(start_date STRING, end_date STRING)`
- **Returns:** domain, table_count, avg_quality_score, completeness_rate, validity_rate
- **Use When:** User asks for "quality score" or "data quality summary"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_data_quality_summary('2024-12-01', '2024-12-31')`

#### get_table_activity_status
- **Signature:** `get_table_activity_status(start_date STRING, end_date STRING, activity_days INT)`
- **Returns:** table_name, last_access, activity_status, days_inactive
- **Use When:** User asks for "inactive tables" or "orphaned tables"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_table_activity_status('2024-12-01', '2024-12-31', 14)`

---

## ████ SECTION G: ML MODEL INTEGRATION (3 Models) ████

### Quality ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `data_drift_detector` | `quality_anomaly_predictions` | `drift_score`, `is_drifted` | "Data drift?" |
| `schema_change_predictor` | `quality_trend_predictions` | `change_probability` | "Schema risk?" |
| `schema_evolution_predictor` | `freshness_alert_predictions` | `evolution_type` | "Evolution patterns" |

### ML Model Usage Patterns

#### data_drift_detector (Data Drift Detection)
- **Question Triggers:** "data drift", "distribution change", "quality anomaly", "data changed"
- **Query Pattern:**
```sql
SELECT table_name, check_date, drift_score, is_drifted, drift_columns
FROM ${catalog}.${gold_schema}.quality_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND is_drifted = TRUE
ORDER BY drift_score ASC;
```
- **Interpretation:** `is_drifted = TRUE` = Data distribution has significantly changed

#### schema_change_predictor (Schema Risk)
- **Question Triggers:** "schema change", "schema risk", "will schema change", "breaking change"
- **Query Pattern:**
```sql
SELECT table_name, change_probability, predicted_change_type, risk_factors
FROM ${catalog}.${gold_schema}.quality_trend_predictions
WHERE change_probability > 0.5
ORDER BY change_probability DESC;
```

#### freshness_alert_predictions (Freshness Alerts)
- **Question Triggers:** "freshness alert", "stale prediction", "will data be late"
- **Query Pattern:**
```sql
SELECT table_name, predicted_delay_hours, alert_probability, last_update
FROM ${catalog}.${gold_schema}.freshness_alert_predictions
WHERE alert_probability > 0.7
ORDER BY predicted_delay_hours DESC;
```

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Is there data drift?"                  → ML: quality_anomaly_predictions
"Schema change risk?"                   → ML: quality_trend_predictions
"Will data be late?"                    → ML: freshness_alert_predictions
────────────────────────────────────────────────────
"What is the freshness rate?"           → Metric View: data_quality
"Is quality trending down?"             → Custom Metrics: _drift_metrics
"Show stale tables"                     → TVF: get_stale_tables
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "Which tables are stale?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  24
)
WHERE freshness_status IN ('STALE', 'CRITICAL')
ORDER BY hours_since_update DESC
LIMIT 20;
```
**Expected Result:** Tables not updated in 24+ hours

---

### Question 2: "What is our overall data quality score?"
**Expected SQL:**
```sql
SELECT 
  AVG(avg_quality_score) as overall_quality_score
FROM ${catalog}.${gold_schema}.get_data_quality_summary(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
);
```
**Expected Result:** Single quality score (0-100)

---

### Question 3: "Which tables are failing quality checks?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_tables_failing_quality(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY failure_count DESC
LIMIT 20;
```
**Expected Result:** Tables with quality failures

---

### Question 4: "Show me inactive tables"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_activity_status(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  14
)
WHERE activity_status = 'INACTIVE'
ORDER BY days_inactive DESC
LIMIT 20;
```
**Expected Result:** Tables not accessed in 14+ days

---

### Question 5: "Are there any quality anomalies?"
**Expected SQL:**
```sql
SELECT 
  table_name,
  anomaly_score,
  is_anomaly,
  dimension
FROM ${catalog}.${gold_schema}.quality_anomaly_predictions
WHERE is_anomaly = TRUE
ORDER BY anomaly_score DESC
LIMIT 20;
```
**Expected Result:** Tables with detected quality anomalies

---

### Question 6: "Which tables have degrading quality?"
**Expected SQL:**
```sql
SELECT 
  table_name,
  predicted_quality_score,
  forecast_date
FROM ${catalog}.${gold_schema}.quality_trend_predictions
WHERE predicted_quality_score < 70
ORDER BY predicted_quality_score ASC
LIMIT 20;
```
**Expected Result:** Tables predicted to have low quality

---

### Question 7: "What is the data freshness by domain?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_data_freshness_by_domain(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY stale_table_count DESC;
```
**Expected Result:** Freshness summary by domain

---

### Question 8: "Predict data freshness issues"
**Expected SQL:**
```sql
SELECT 
  table_name,
  staleness_probability,
  expected_stale_date
FROM ${catalog}.${gold_schema}.freshness_alert_predictions
WHERE staleness_probability > 0.5
ORDER BY staleness_probability DESC
LIMIT 20;
```
**Expected Result:** Tables likely to become stale

---

### Question 9: "Show me pipeline data lineage"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_pipeline_data_lineage(
  NULL,
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY dependency_count DESC
LIMIT 20;
```
**Expected Result:** Pipelines with their data dependencies

---

### Question 10: "What tables have the most reads?"
**Expected SQL:**
```sql
SELECT 
  entity_name as table_name,
  MEASURE(read_events) as read_count
FROM ${catalog}.${gold_schema}.fact_table_lineage_profile_metrics
WHERE column_name = ':table'
  AND window_start >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY entity_name
ORDER BY read_count DESC
LIMIT 20;
```
**Expected Result:** Most frequently accessed tables

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 7 functions with signatures | ✅ |
| **G. Benchmark Questions** | 10 with SQL answers | ✅ |

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

