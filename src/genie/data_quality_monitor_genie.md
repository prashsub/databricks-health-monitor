# Data Quality Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Data Quality Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for data quality, freshness, and governance analytics. Enables data stewards, governance teams, and data engineers to query table health, lineage, and quality metrics without SQL.

**Powered by:**
- 2 Metric Views (data_quality, ml_intelligence)
- 5 Table-Valued Functions (freshness, quality, lineage queries)
- 2 ML Prediction Tables (quality anomalies, freshness alerts)
- 3 Lakehouse Monitoring Tables (quality drift and profile metrics)
- 4 Dimension Tables (experiment, served_entities, workspace, date)
- 12 Fact Tables (lineage, classification, DQ monitoring, optimization)

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

### Table-Valued Functions (5 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_stale_tables` | Table freshness metrics | "stale tables", "freshness issues" |
| `get_table_lineage` | Table-level lineage tracking | "table dependencies", "table lineage" |
| `get_table_activity_summary` | Quality summary and activity status | "quality score", "inactive tables", "activity status" |
| `get_data_lineage_summary` | Data lineage summary by catalog/schema | "lineage summary", "lineage coverage" |
| `get_pipeline_lineage_impact` | Pipeline lineage impact analysis | "pipeline dependencies", "pipeline impact" |

### ML Prediction Tables 🤖 (2 Models)

| Table Name | Purpose | Model | Key Columns | Schema |
|---|---|---|---|---|
| `quality_anomaly_predictions` | Data drift and quality anomaly detection | Data Drift Detector | `table_name`, `prediction`, `evaluation_date` | `${catalog}.${feature_schema}` |
| `freshness_alert_predictions` | Staleness probability predictions | Freshness Predictor | `table_name`, `prediction`, `evaluation_date` | `${catalog}.${feature_schema}` |

**Training Source:** `src/ml/quality/` | **Inference:** `src/ml/inference/batch_inference_all_models.py`

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

### Dimension Tables (4 Tables)

**Sources:** `gold_layer_design/yaml/mlflow/`, `model_serving/`, `shared/`

| Table Name | Purpose | Key Columns | YAML Source |
|---|---|---|---|
| `dim_experiment` | MLflow experiments | `experiment_id`, `experiment_name`, `artifact_location` | mlflow/dim_experiment.yaml |
| `dim_served_entities` | Model serving endpoints | `entity_id`, `entity_name`, `endpoint_name`, `entity_version` | model_serving/dim_served_entities.yaml |
| `dim_workspace` | Workspace reference | `workspace_id`, `workspace_name`, `region`, `cloud_provider` | shared/dim_workspace.yaml |
| `dim_date` | Date dimension for time analysis | `date_key`, `day_of_week`, `month`, `quarter`, `year`, `is_weekend` | shared/dim_date.yaml |

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

### Data Model Relationships 🔗

**Foreign Key Constraints** (extracted from `gold_layer_design/yaml/`)

| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_table_lineage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_column_lineage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_dq_monitoring` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_data_quality_monitoring_table_results` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_data_classification` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_mlflow_runs` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_mlflow_runs` | → | `dim_experiment` | `(workspace_id, experiment_id)` = `(workspace_id, experiment_id)` | LEFT |
| `fact_mlflow_run_metrics_history` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_endpoint_usage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_endpoint_usage` | → | `dim_served_entities` | `(workspace_id, endpoint_id)` = `(workspace_id, endpoint_id)` | LEFT |
| `fact_payload_logs` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_predictive_optimization` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |

**Join Patterns:**
- **Workspace scope:** All data quality facts join to `dim_workspace` on `workspace_id`
- **Experiment scope:** `fact_mlflow_runs` joins to `dim_experiment` on `(workspace_id, experiment_id)`
- **Model serving:** `fact_endpoint_usage` joins to `dim_served_entities` on `(workspace_id, endpoint_id)`

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
| `get_stale_tables` | `(days_back INT, staleness_threshold_days INT DEFAULT 7)` | Freshness | "stale tables" |
| `get_table_lineage` | `(catalog_filter STRING, schema_filter STRING DEFAULT '%')` | Table lineage | "table dependencies" |
| `get_table_activity_summary` | `(days_back INT)` | Quality summary | "quality score", "activity status" |
| `get_data_lineage_summary` | `(catalog_filter STRING, schema_filter STRING DEFAULT '%')` | Data lineage | "lineage summary" |
| `get_pipeline_lineage_impact` | `(catalog_filter STRING)` | Pipeline impact | "pipeline dependencies" |

### TVF Details

#### get_stale_tables
- **Signature:** `get_stale_tables(days_back INT, staleness_threshold_days INT DEFAULT 7)`
- **Returns:** table_name, last_update, hours_since_update, freshness_status
- **Use When:** User asks for "stale tables" or "data freshness"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(30, 7))`

#### get_table_lineage
- **Signature:** `get_table_lineage(catalog_filter STRING, schema_filter STRING DEFAULT '%')`
- **Returns:** source_table, target_table, lineage_type
- **Use When:** User asks for "table lineage" or "table dependencies"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_lineage('main', 'gold_%'))`

#### get_table_activity_summary
- **Signature:** `get_table_activity_summary(days_back INT)`
- **Returns:** table_name, quality_score, failed_checks, activity_status, days_since_last_access
- **Use When:** User asks for "quality score", "inactive tables", or "activity status"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(30))`

#### get_data_lineage_summary
- **Signature:** `get_data_lineage_summary(catalog_filter STRING, schema_filter STRING DEFAULT '%')`
- **Returns:** catalog, schema, table_count, lineage_coverage
- **Use When:** User asks for "lineage summary" or "lineage coverage"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_data_lineage_summary('main', '%'))`

#### get_pipeline_lineage_impact
- **Signature:** `get_pipeline_lineage_impact(catalog_filter STRING)`
- **Returns:** pipeline_name, source_table, target_table, dependency_depth
- **Use When:** User asks for "pipeline dependencies" or "pipeline impact"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.get_pipeline_lineage_impact('main'))`

---

## ████ SECTION G: ML MODEL INTEGRATION (2 Models) ████

### Quality ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Schema | Use When |
|----------|-----------------|-------------|--------|----------|
| `data_drift_detector` | `quality_anomaly_predictions` | `prediction`, `table_name`, `evaluation_date` | `${catalog}.${feature_schema}` | "Data drift?", "quality anomalies" |
| `freshness_predictor` | `freshness_alert_predictions` | `prediction`, `table_name`, `evaluation_date` | `${catalog}.${feature_schema}` | "staleness risk", "freshness alerts" |

### ML Model Usage Patterns

#### data_drift_detector (Data Drift Detection)
- **Question Triggers:** "data drift", "distribution change", "quality anomaly", "data changed"
- **Query Pattern:**
```sql
SELECT table_name, prediction as drift_score, evaluation_date
FROM ${catalog}.${feature_schema}.quality_anomaly_predictions
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
FROM ${catalog}.${feature_schema}.freshness_alert_predictions
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction > 0.7
ORDER BY prediction DESC;
```
- **Interpretation:** `prediction > 0.7` = High probability of staleness/freshness issues

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Is there data drift?"                  → ML: ${catalog}.${feature_schema}.quality_anomaly_predictions
"Quality anomalies?"                    → ML: ${catalog}.${feature_schema}.quality_anomaly_predictions
"Will data be late?"                    → ML: ${catalog}.${feature_schema}.freshness_alert_predictions
────────────────────────────────────────────────────
"What is the freshness rate?"           → Metric View: data_quality
"Is quality trending down?"             → Custom Metrics: _drift_metrics
"Show stale tables"                     → TVF: get_stale_tables
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**
> **Grounded in:** mv_data_quality, mv_ml_intelligence, TVFs, ML Tables

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "What is our overall data quality score?"
**Expected SQL:**
```sql
SELECT MEASURE(quality_score) as overall_quality
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall data quality score (0-100 scale)

---

### Question 2: "Show me tables with freshness issues"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(7, 24))
WHERE freshness_status IN ('STALE', 'CRITICAL')
ORDER BY hours_since_update DESC
LIMIT 20;
```
**Expected Result:** Tables not updated within expected timeframe

---

### Question 3: "What is the completeness rate?"
**Expected SQL:**
```sql
SELECT MEASURE(completeness_rate) as completeness_pct
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall data completeness percentage

---

### Question 4: "Show me tables failing quality checks"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
WHERE failed_checks > 0
ORDER BY failed_checks DESC, quality_score ASC
LIMIT 20;
```
**Expected Result:** Tables with failed data quality validations

---

### Question 5: "What is our data freshness by domain?"
**Expected SQL:**
```sql
SELECT
  domain,
  total_tables,
  stale_tables,
  avg_hours_since_update
FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
GROUP BY domain
ORDER BY stale_tables DESC
LIMIT 15;
```
**Expected Result:** Freshness metrics aggregated by domain

---

### Question 6: "Show me the data quality summary"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
ORDER BY quality_score ASC
LIMIT 20;
```
**Expected Result:** Comprehensive quality summary across all tables

---

### Question 7: "What is the validity rate?"
**Expected SQL:**
```sql
SELECT MEASURE(validity_rate) as validity_pct
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall data validity percentage

---

### Question 8: "Show me inactive tables"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(30))
WHERE activity_status IN ('INACTIVE', 'ORPHANED')
ORDER BY days_since_last_access DESC
LIMIT 20;
```
**Expected Result:** Tables with no recent activity requiring review

---

### Question 9: "What is the freshness rate?"
**Expected SQL:**
```sql
SELECT MEASURE(freshness_rate) as fresh_pct
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Percentage of tables meeting freshness SLA

---

### Question 10: "Show me pipeline data lineage"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_data_lineage_summary('main', '%'))
ORDER BY dependency_depth ASC
LIMIT 50;
```
**Expected Result:** Complete lineage graph for specified pipeline

---

### Question 11: "What is the job quality status?"
**Expected SQL:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
ORDER BY quality_score ASC
LIMIT 15;
```
**Expected Result:** Data quality health by job/pipeline

---

### Question 12: "What is the staleness rate?"
**Expected SQL:**
```sql
SELECT MEASURE(staleness_rate) as stale_pct
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Percentage of stale tables

---

### Question 13: "Show me quality score by domain"
**Expected SQL:**
```sql
SELECT 
  domain,
  MEASURE(quality_score) as avg_quality,
  MEASURE(total_tables) as table_count
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY domain
ORDER BY avg_quality ASC
LIMIT 10;
```
**Expected Result:** Quality metrics grouped by domain

---

### Question 14: "Are there any quality anomalies?"
**Expected SQL:**
```sql
SELECT 
  table_name,
  prediction as drift_score,
  evaluation_date
FROM ${catalog}.${feature_schema}.quality_anomaly_predictions
WHERE prediction > 0.5
ORDER BY prediction DESC
LIMIT 20;
```
**Expected Result:** ML-detected data quality drift and anomalies

---

### Question 15: "What is our ML model performance?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(accuracy) as ml_accuracy,
  MEASURE(drift_score) as ml_drift,
  MEASURE(prediction_count) as total_predictions
FROM ${catalog}.${gold_schema}.mv_ml_intelligence
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** ML model performance metrics across all models

---

### Question 16: "Show me tables at risk of staleness"
**Expected SQL:**
```sql
SELECT 
  table_name,
  prediction as staleness_probability,
  evaluation_date
FROM ${catalog}.${feature_schema}.freshness_alert_predictions
WHERE prediction > 0.7
ORDER BY prediction DESC
LIMIT 20;
```
**Expected Result:** Predicted freshness issues before they occur

---

### Question 17: "What is our ML prediction accuracy?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(accuracy) as model_accuracy,
  MEASURE(prediction_count) as predictions
FROM ${catalog}.${gold_schema}.mv_ml_intelligence
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** ML model performance metrics

---

### Question 18: "Show me quality drift metrics"
**Expected SQL:**
```sql
SELECT 
  window.start AS period_start,
  quality_score_drift_pct,
  completeness_drift_pct,
  validity_drift_pct
FROM ${catalog}.${gold_schema}.fact_table_quality_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC
LIMIT 10;
```
**Expected Result:** Data quality degradation trends from Lakehouse Monitoring

---

### Question 19: "What is the governance coverage?"
**Expected SQL:**
```sql
SELECT 
  window.start AS window_start,
  tag_coverage_rate,
  lineage_coverage_rate
FROM ${catalog}.${gold_schema}.fact_governance_metrics_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window.start DESC
LIMIT 10;
```
**Expected Result:** Governance metadata coverage from Lakehouse Monitoring

---

### Question 20: "Show me quality score distribution"
**Expected SQL:**
```sql
SELECT 
  CASE 
    WHEN MEASURE(quality_score) >= 90 THEN 'Excellent (90-100)'
    WHEN MEASURE(quality_score) >= 70 THEN 'Good (70-89)'
    WHEN MEASURE(quality_score) >= 50 THEN 'Fair (50-69)'
    ELSE 'Poor (<50)'
  END as quality_tier,
  COUNT(*) as table_count
FROM ${catalog}.${gold_schema}.mv_data_quality
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY quality_tier
ORDER BY MIN(MEASURE(quality_score)) DESC;
```
**Expected Result:** Distribution of tables across quality tiers

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: Comprehensive table health assessment - combine freshness, quality, activity, and ML predictions"
**Expected SQL:**
```sql
WITH freshness AS (
  SELECT
    table_name,
    hours_since_update,
    freshness_status,
    expected_update_frequency_hours
  FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(30, 24))
),
quality AS (
  SELECT
    table_name,
    quality_score,
    failed_checks,
    completeness_rate,
    validity_rate
  FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(30))
),
activity AS (
  SELECT
    table_name,
    activity_status,
    days_since_last_access,
    daily_read_count,
    daily_write_count
  FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(30))
),
ml_predictions AS (
  SELECT 
    table_name,
    AVG(CASE WHEN evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN prediction ELSE NULL END) as avg_drift_score
  FROM ${catalog}.${feature_schema}.quality_anomaly_predictions
  WHERE prediction > 0.3
  GROUP BY table_name
),
freshness_predictions AS (
  SELECT 
    table_name,
    AVG(prediction) as staleness_probability
  FROM ${catalog}.${feature_schema}.freshness_alert_predictions
  WHERE prediction > 0.5
    AND evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY table_name
)
SELECT
  f.table_name,
  f.hours_since_update,
  f.freshness_status,
  COALESCE(q.quality_score, 0) as quality_score,
  COALESCE(q.failed_checks, 0) as failed_checks,
  COALESCE(q.completeness_rate, 0) as completeness_pct,
  COALESCE(q.validity_rate, 0) as validity_pct,
  COALESCE(a.activity_status, 'UNKNOWN') as activity_status,
  COALESCE(a.daily_read_count, 0) as daily_reads,
  COALESCE(a.daily_write_count, 0) as daily_writes,
  COALESCE(ml.avg_drift_score, 0) as ml_drift_score,
  COALESCE(fp.staleness_probability, 0) as predicted_staleness,
  CASE 
    WHEN f.freshness_status = 'CRITICAL' AND q.quality_score < 50 THEN 'Critical - Data Integrity Risk'
    WHEN ml.avg_drift_score > 0.7 AND fp.staleness_probability > 0.7 THEN 'High Risk - Immediate Attention'
    WHEN f.freshness_status = 'STALE' OR q.quality_score < 70 THEN 'Medium Risk - Monitor'
    WHEN a.activity_status = 'INACTIVE' THEN 'Low Priority - Consider Archive'
    ELSE 'Healthy'
  END as health_status,
  CASE 
    WHEN f.freshness_status = 'CRITICAL' THEN 'Investigate data pipeline immediately'
    WHEN q.quality_score < 50 THEN 'Review and fix data quality rules'
    WHEN ml.avg_drift_score > 0.7 THEN 'Analyze schema or data changes'
    WHEN a.activity_status = 'INACTIVE' THEN 'Archive or decommission table'
    ELSE 'Continue monitoring'
  END as recommended_action
FROM freshness f
LEFT JOIN quality q ON f.table_name = q.table_name
LEFT JOIN activity a ON f.table_name = a.table_name
LEFT JOIN ml_predictions ml ON f.table_name = ml.table_name
LEFT JOIN freshness_predictions fp ON f.table_name = fp.table_name
ORDER BY 
  CASE 
    WHEN f.freshness_status = 'CRITICAL' AND COALESCE(q.quality_score, 0) < 50 THEN 1
    WHEN COALESCE(ml.avg_drift_score, 0) > 0.7 THEN 2
    WHEN f.freshness_status = 'STALE' THEN 3
    ELSE 4
  END,
  hours_since_update DESC
LIMIT 25;
```
**Expected Result:** Multi-dimensional table health assessment combining freshness, quality, activity, and ML insights

---

### Question 22: "🔬 DEEP RESEARCH: Domain-level data quality scorecard - aggregate quality metrics with freshness and governance"
**Expected SQL:**
```sql
WITH domain_quality AS (
  SELECT 
    domain,
    MEASURE(quality_score) as avg_quality,
    MEASURE(completeness_rate) as avg_completeness,
    MEASURE(validity_rate) as avg_validity,
    MEASURE(total_tables) as table_count
  FROM ${catalog}.${gold_schema}.mv_data_quality
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY domain
),
domain_freshness AS (
  SELECT
    domain,
    AVG(hours_since_update) as avg_hours_stale,
    SUM(CASE WHEN freshness_status = 'FRESH' THEN 1 ELSE 0 END) as fresh_count,
    SUM(CASE WHEN freshness_status IN ('STALE', 'CRITICAL') THEN 1 ELSE 0 END) as stale_count
  FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(30, 24)) tf
  JOIN ${catalog}.${gold_schema}.mv_data_quality dq
    ON tf.table_name = dq.table_full_name
  GROUP BY domain
),
domain_activity AS (
  SELECT
    domain,
    SUM(daily_read_count) as total_daily_reads,
    SUM(daily_write_count) as total_daily_writes,
    SUM(CASE WHEN activity_status = 'ACTIVE' THEN 1 ELSE 0 END) as active_tables,
    SUM(CASE WHEN activity_status IN ('INACTIVE', 'ORPHANED') THEN 1 ELSE 0 END) as inactive_tables
  FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(30)) ta
  JOIN ${catalog}.${gold_schema}.mv_data_quality dq
    ON ta.table_name = dq.table_full_name
  GROUP BY domain
),
domain_governance AS (
  SELECT 
    slice_value AS domain,
    AVG(tag_coverage_rate) as avg_tag_coverage,
    AVG(lineage_coverage_rate) as avg_lineage_coverage
  FROM ${catalog}.${gold_schema}.fact_governance_metrics_profile_metrics
  WHERE column_name = ':table'
    AND log_type = 'INPUT'
    AND slice_key = 'domain'
  GROUP BY slice_value
)
SELECT 
  dq.domain,
  dq.table_count,
  dq.avg_quality,
  dq.avg_completeness,
  dq.avg_validity,
  df.fresh_count,
  df.stale_count,
  df.stale_count * 100.0 / NULLIF(dq.table_count, 0) as staleness_pct,
  da.active_tables,
  da.inactive_tables,
  da.total_daily_reads,
  da.total_daily_writes,
  COALESCE(dg.avg_tag_coverage, 0) as tag_coverage_pct,
  COALESCE(dg.avg_lineage_coverage, 0) as lineage_coverage_pct,
  CASE 
    WHEN dq.avg_quality < 70 OR df.stale_count * 100.0 / NULLIF(dq.table_count, 0) > 20 THEN 'Critical Domain'
    WHEN dq.avg_quality < 80 OR da.inactive_tables * 100.0 / NULLIF(dq.table_count, 0) > 30 THEN 'Needs Improvement'
    WHEN dq.avg_quality >= 90 AND dg.avg_tag_coverage >= 80 THEN 'Excellent'
    ELSE 'Good'
  END as domain_health_status,
  CASE 
    WHEN dq.avg_quality < 70 THEN 'Implement stricter quality rules'
    WHEN df.stale_count * 100.0 / NULLIF(dq.table_count, 0) > 20 THEN 'Review pipeline schedules'
    WHEN dg.avg_tag_coverage < 50 THEN 'Improve metadata tagging'
    WHEN da.inactive_tables > 10 THEN 'Archive unused tables'
    ELSE 'Maintain current standards'
  END as recommended_action
FROM domain_quality dq
LEFT JOIN domain_freshness df ON dq.domain = df.domain
LEFT JOIN domain_activity da ON dq.domain = da.domain
LEFT JOIN domain_governance dg ON dq.domain = dg.domain
ORDER BY dq.avg_quality ASC, staleness_pct DESC
LIMIT 15;
```
**Expected Result:** Domain-level data quality scorecard with actionable recommendations

---

### Question 23: "🔬 DEEP RESEARCH: Pipeline data quality impact analysis - trace quality issues through lineage"
**Expected SQL:**
```sql
WITH pipeline_lineage AS (
  SELECT
    source_table,
    target_table,
    dependency_depth,
    pipeline_name
  FROM TABLE(${catalog}.${gold_schema}.get_data_lineage_summary('main', '%'))
),
table_quality AS (
  SELECT
    table_name,
    quality_score,
    failed_checks,
    completeness_rate,
    validity_rate
  FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(30))
),
freshness AS (
  SELECT
    table_name,
    hours_since_update,
    freshness_status
  FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(30, 24))
),
ml_drift AS (
  SELECT 
    table_name,
    AVG(prediction) as avg_drift_score
  FROM ${catalog}.${feature_schema}.quality_anomaly_predictions
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND prediction > 0.3
  GROUP BY table_name
)
SELECT 
  pl.source_table,
  pl.target_table,
  pl.dependency_depth,
  pl.pipeline_name,
  COALESCE(sq.quality_score, 100) as source_quality_score,
  COALESCE(sq.failed_checks, 0) as source_failed_checks,
  COALESCE(tq.quality_score, 100) as target_quality_score,
  COALESCE(tq.failed_checks, 0) as target_failed_checks,
  COALESCE(sf.freshness_status, 'UNKNOWN') as source_freshness,
  COALESCE(tf.freshness_status, 'UNKNOWN') as target_freshness,
  COALESCE(sml.avg_drift_score, 0) as source_drift,
  COALESCE(tml.avg_drift_score, 0) as target_drift,
  CASE 
    WHEN COALESCE(sq.quality_score, 100) < 50 AND COALESCE(tq.quality_score, 100) < 50 THEN 'Critical - Cascading Failure'
    WHEN COALESCE(sq.quality_score, 100) < 70 AND COALESCE(tq.quality_score, 100) < 80 THEN 'High - Quality Degradation Propagating'
    WHEN COALESCE(sf.freshness_status, 'FRESH') IN ('STALE', 'CRITICAL') AND COALESCE(tf.freshness_status, 'FRESH') IN ('STALE', 'CRITICAL') THEN 'High - Freshness Cascade'
    WHEN COALESCE(sml.avg_drift_score, 0) > 0.6 THEN 'Medium - Upstream Drift Detected'
    ELSE 'Normal'
  END as impact_status,
  CASE 
    WHEN COALESCE(sq.quality_score, 100) < 50 THEN 'Fix source data quality immediately'
    WHEN COALESCE(sf.freshness_status, 'FRESH') = 'CRITICAL' THEN 'Investigate source pipeline failure'
    WHEN COALESCE(sml.avg_drift_score, 0) > 0.6 THEN 'Review schema changes in source'
    WHEN COALESCE(tq.failed_checks, 0) > 5 THEN 'Review downstream validation rules'
    ELSE 'Monitor pipeline health'
  END as recommended_action
FROM pipeline_lineage pl
LEFT JOIN table_quality sq ON pl.source_table = sq.table_name
LEFT JOIN table_quality tq ON pl.target_table = tq.table_name
LEFT JOIN freshness sf ON pl.source_table = sf.table_name
LEFT JOIN freshness tf ON pl.target_table = tf.table_name
LEFT JOIN ml_drift sml ON pl.source_table = sml.table_name
LEFT JOIN ml_drift tml ON pl.target_table = tml.table_name
WHERE COALESCE(sq.quality_score, 100) < 80 
   OR COALESCE(tq.quality_score, 100) < 80
   OR COALESCE(sf.freshness_status, 'FRESH') IN ('STALE', 'CRITICAL')
ORDER BY 
  CASE impact_status
    WHEN 'Critical - Cascading Failure' THEN 1
    WHEN 'High - Quality Degradation Propagating' THEN 2
    WHEN 'High - Freshness Cascade' THEN 3
    ELSE 4
  END,
  pl.dependency_depth ASC
LIMIT 25;
```
**Expected Result:** Pipeline quality impact analysis showing how issues propagate through lineage

---

### Question 24: "🔬 DEEP RESEARCH: ML-powered predictive quality monitoring - identify tables at risk before failures occur"
**Expected SQL:**
```sql
WITH current_quality AS (
  SELECT
    table_name,
    quality_score,
    failed_checks,
    completeness_rate,
    validity_rate
  FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
),
ml_drift_predictions AS (
  SELECT 
    table_name,
    AVG(prediction) as avg_drift_score,
    MAX(prediction) as max_drift_score
  FROM ${catalog}.${feature_schema}.quality_anomaly_predictions
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND prediction > 0.3
  GROUP BY table_name
),
freshness_risk AS (
  SELECT 
    table_name,
    AVG(prediction) as staleness_probability
  FROM ${catalog}.${feature_schema}.freshness_alert_predictions
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND prediction > 0.5
  GROUP BY table_name
),
quality_drift AS (
  SELECT 
    table_name,
    AVG(quality_score_drift_pct) as avg_quality_drift,
    MAX(quality_score_drift_pct) as max_quality_drift
  FROM ${catalog}.${gold_schema}.fact_table_quality_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY table_name
)
SELECT
  cq.table_name,
  cq.quality_score as current_quality_score,
  cq.failed_checks,
  COALESCE(dp.avg_drift_score, 0) as ml_drift_score,
  COALESCE(fr.staleness_probability, 0) as freshness_risk,
  COALESCE(qd.avg_quality_drift, 0) as recent_quality_drift,
  COALESCE(qd.max_quality_drift, 0) as max_quality_drift,
  CASE
    WHEN COALESCE(dp.max_drift_score, 0) > 0.8 AND cq.quality_score < 70 THEN 'Critical - Imminent Failure'
    WHEN COALESCE(fr.staleness_probability, 0) > 0.7 AND COALESCE(dp.avg_drift_score, 0) > 0.5 THEN 'High - Multiple Risk Factors'
    WHEN COALESCE(qd.max_quality_drift, 0) > 30 THEN 'High - Rapid Quality Degradation'
    WHEN COALESCE(dp.avg_drift_score, 0) > 0.5 THEN 'Medium - Elevated Risk'
    WHEN cq.quality_score >= 90 THEN 'Low Risk - Healthy'
    ELSE 'Monitor'
  END as risk_status,
  CASE
    WHEN COALESCE(dp.max_drift_score, 0) > 0.8 THEN 'Immediate investigation - data drift detected'
    WHEN COALESCE(fr.staleness_probability, 0) > 0.7 THEN 'Check pipeline schedule and dependencies'
    WHEN COALESCE(qd.max_quality_drift, 0) > 30 THEN 'Analyze recent data source changes'
    WHEN cq.failed_checks > 3 THEN 'Review and update validation rules'
    ELSE 'Continue monitoring'
  END as recommended_action,
  CASE
    WHEN COALESCE(dp.max_drift_score, 0) > 0.8 OR COALESCE(qd.max_quality_drift, 0) > 50 THEN 'Today'
    WHEN COALESCE(fr.staleness_probability, 0) > 0.7 THEN 'This Week'
    WHEN COALESCE(dp.avg_drift_score, 0) > 0.5 THEN 'Next 2 Weeks'
    ELSE 'Monitor'
  END as time_to_failure_estimate
FROM current_quality cq
LEFT JOIN ml_drift_predictions dp ON cq.table_name = dp.table_name
LEFT JOIN freshness_risk fr ON cq.table_name = fr.table_name
LEFT JOIN quality_drift qd ON cq.table_name = qd.table_name
WHERE COALESCE(dp.avg_drift_score, 0) > 0.3
   OR COALESCE(fr.staleness_probability, 0) > 0.5
   OR COALESCE(qd.max_quality_drift, 0) > 20
ORDER BY
  CASE risk_status
    WHEN 'Critical - Imminent Failure' THEN 1
    WHEN 'High - Multiple Risk Factors' THEN 2
    WHEN 'High - Rapid Quality Degradation' THEN 3
    ELSE 4
  END,
  COALESCE(dp.max_drift_score, 0) DESC,
  COALESCE(qd.max_quality_drift, 0) DESC
LIMIT 25;
```
**Expected Result:** Predictive quality monitoring combining current state, ML predictions, and drift analysis with time-to-failure estimates

---

### Question 25: "🔬 DEEP RESEARCH: Executive data quality dashboard - comprehensive quality, freshness, governance, and ML intelligence"
**Expected SQL:**
```sql
WITH quality_summary AS (
  SELECT 
    MEASURE(quality_score) as avg_quality,
    MEASURE(completeness_rate) as avg_completeness,
    MEASURE(validity_rate) as avg_validity,
    MEASURE(freshness_rate) as freshness_pct,
    MEASURE(staleness_rate) as staleness_pct,
    MEASURE(total_tables) as table_count
  FROM ${catalog}.${gold_schema}.mv_data_quality
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
failing_tables AS (
  SELECT
    COUNT(*) as tables_failing_quality,
    SUM(failed_checks) as total_failed_checks
  FROM TABLE(${catalog}.${gold_schema}.get_table_activity_summary(7))
  WHERE quality_score < 70
),
stale_tables AS (
  SELECT
    COUNT(*) as stale_count,
    AVG(hours_since_update) as avg_hours_stale
  FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(7, 24))
  WHERE freshness_status IN ('STALE', 'CRITICAL')
),
ml_intelligence AS (
  SELECT 
    MEASURE(accuracy) as ml_accuracy,
    MEASURE(drift_score) as avg_drift,
    MEASURE(prediction_count) as predictions
  FROM ${catalog}.${gold_schema}.mv_ml_intelligence
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
ml_anomaly_predictions AS (
  SELECT 
    COUNT(*) as tables_with_drift,
    AVG(prediction) as avg_drift_score
  FROM ${catalog}.${feature_schema}.quality_anomaly_predictions
  WHERE prediction > 0.5
    AND evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
ml_risk_predictions AS (
  SELECT
    COUNT(DISTINCT table_name) as tables_at_risk,
    AVG(prediction) as avg_risk_score
  FROM ${catalog}.${feature_schema}.freshness_alert_predictions
  WHERE prediction > 0.7 AND evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
governance_status AS (
  SELECT 
    AVG(tag_coverage_rate) as avg_tag_coverage,
    AVG(lineage_coverage_rate) as avg_lineage_coverage
  FROM ${catalog}.${gold_schema}.fact_governance_metrics_profile_metrics
  WHERE column_name = ':table'
    AND log_type = 'INPUT'
    AND slice_key IS NULL
    AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
),
quality_drift AS (
  SELECT 
    AVG(quality_score_drift_pct) as avg_quality_drift,
    MAX(quality_score_drift_pct) as max_quality_drift
  FROM ${catalog}.${gold_schema}.fact_table_quality_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT 
  qs.table_count as total_tables,
  qs.avg_quality as overall_quality_score,
  qs.avg_completeness as completeness_pct,
  qs.avg_validity as validity_pct,
  qs.freshness_pct,
  qs.staleness_pct,
  COALESCE(ft.tables_failing_quality, 0) as failing_tables,
  COALESCE(ft.total_failed_checks, 0) as total_failed_checks,
  COALESCE(st.stale_count, 0) as stale_tables,
  COALESCE(st.avg_hours_stale, 0) as avg_hours_stale,
  COALESCE(ml.ml_accuracy, 0) as ml_model_accuracy,
  COALESCE(ml.avg_drift, 0) as ml_detected_drift,
  COALESCE(ap.tables_with_drift, 0) as tables_with_anomalies,
  COALESCE(rp.tables_at_risk, 0) as tables_at_risk,
  COALESCE(gs.avg_tag_coverage, 0) as tag_coverage_pct,
  COALESCE(gs.avg_lineage_coverage, 0) as lineage_coverage_pct,
  COALESCE(qd.avg_quality_drift, 0) as recent_quality_drift,
  COALESCE(qd.max_quality_drift, 0) as max_quality_drift,
  CASE 
    WHEN qs.avg_quality < 70 OR COALESCE(ft.tables_failing_quality, 0) > 10 THEN 'Critical Data Quality Crisis'
    WHEN qs.staleness_pct > 20 OR COALESCE(st.stale_count, 0) > 20 THEN 'Critical Freshness Issues'
    WHEN COALESCE(qd.max_quality_drift, 0) > 30 THEN 'Quality Degradation Detected'
    WHEN COALESCE(rp.tables_at_risk, 0) > 15 THEN 'High Risk - Predictive Alerts'
    WHEN qs.avg_quality >= 90 AND qs.freshness_pct >= 95 THEN 'Excellent Data Health'
    ELSE 'Normal'
  END as overall_data_health_status,
  CASE 
    WHEN qs.avg_quality < 70 THEN 'Audit and strengthen quality rules across all domains'
    WHEN COALESCE(ft.tables_failing_quality, 0) > 10 THEN 'Investigate top failing tables immediately'
    WHEN qs.staleness_pct > 20 THEN 'Review pipeline schedules and dependencies'
    WHEN COALESCE(qd.max_quality_drift, 0) > 30 THEN 'Analyze recent changes causing quality degradation'
    WHEN COALESCE(rp.tables_at_risk, 0) > 15 THEN 'Proactive monitoring of at-risk tables'
    WHEN COALESCE(gs.avg_tag_coverage, 0) < 70 THEN 'Improve metadata tagging and governance'
    ELSE 'Continue monitoring and maintain standards'
  END as top_priority_action
FROM quality_summary qs
CROSS JOIN failing_tables ft
CROSS JOIN stale_tables st
CROSS JOIN ml_intelligence ml
CROSS JOIN ml_anomaly_predictions ap
CROSS JOIN ml_risk_predictions rp
CROSS JOIN governance_status gs
CROSS JOIN quality_drift qd;
```
**Expected Result:** Executive data quality dashboard combining all quality dimensions with health status and prioritized actions

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

