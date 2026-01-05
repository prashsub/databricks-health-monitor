# Data Quality Monitor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Data Quality Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for data quality, freshness, and governance analytics. Enables data stewards, governance teams, and data engineers to query table health, lineage, and quality metrics without SQL.

**Powered by:**
- 2 Metric Views (data_quality, ml_intelligence)
- 7 Table-Valued Functions (freshness, quality, lineage queries)
- 3 ML Prediction Tables (drift detection, schema prediction, freshness alerts)
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

### ML Prediction Tables 🤖 (3 Models)

| Table Name | Purpose | Model | Key Columns |
|---|---|---|---|
| `quality_anomaly_predictions` | Data drift and quality anomaly detection | Data Drift Detector | `drift_score`, `is_drifted`, `drift_columns`, `table_name` |
| `quality_trend_predictions` | Schema change probability and quality forecasts | Schema Change Predictor | `change_probability`, `predicted_change_type`, `risk_factors` |
| `freshness_alert_predictions` | Staleness probability predictions | Schema Evolution Predictor | `staleness_probability`, `predicted_delay_hours`, `expected_stale_date` |

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

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

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

### Question 11: "What is the completeness rate by schema?"
**Expected SQL:**
```sql
SELECT 
  slice_value AS schema_name,
  AVG(completeness_rate) AS avg_completeness_rate
FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'schema_name'
GROUP BY slice_value
ORDER BY avg_completeness_rate ASC
LIMIT 20;
```
**Expected Result:** Completeness rates by schema

---

### Question 12: "Show me tables with data drift"
**Expected SQL:**
```sql
SELECT 
  table_name,
  drift_score,
  is_drifted,
  drift_columns
FROM ${catalog}.${gold_schema}.quality_anomaly_predictions
WHERE is_drifted = TRUE
ORDER BY drift_score DESC
LIMIT 20;
```
**Expected Result:** Tables with detected data drift

---

### Question 13: "What is the quality trend this week?"
**Expected SQL:**
```sql
SELECT 
  window.start as window_start,
  quality_score,
  completeness_rate,
  validity_rate
FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY window.start;
```
**Expected Result:** Daily quality metrics for the week

---

### Question 14: "Which tables have the highest write activity?"
**Expected SQL:**
```sql
SELECT 
  target_table as table_name,
  COUNT(*) as write_count
FROM ${catalog}.${gold_schema}.fact_table_lineage
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND event_type = 'WRITE'
GROUP BY target_table
ORDER BY write_count DESC
LIMIT 20;
```
**Expected Result:** Tables with most write operations

---

### Question 15: "Show me orphaned tables"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_activity_status(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 90 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  30
)
WHERE activity_status = 'ORPHANED'
ORDER BY days_inactive DESC
LIMIT 20;
```
**Expected Result:** Tables not accessed in 30+ days

---

### Question 16: "What DQ checks are failing most often?"
**Expected SQL:**
```sql
SELECT 
  check_name,
  table_name,
  COUNT(*) as failure_count
FROM ${catalog}.${gold_schema}.fact_dq_monitoring
WHERE check_result = 'FAILED'
  AND check_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY check_name, table_name
ORDER BY failure_count DESC
LIMIT 20;
```
**Expected Result:** Most frequently failing DQ checks

---

### Question 17: "Which tables have schema change predictions?"
**Expected SQL:**
```sql
SELECT 
  table_name,
  change_probability,
  predicted_change_type,
  risk_factors
FROM ${catalog}.${gold_schema}.quality_trend_predictions
WHERE change_probability > 0.5
ORDER BY change_probability DESC
LIMIT 20;
```
**Expected Result:** Tables at risk of schema changes

---

### Question 18: "Show me tables with critical freshness issues"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_freshness(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  72
)
WHERE freshness_status = 'CRITICAL'
ORDER BY hours_since_update DESC;
```
**Expected Result:** Tables not updated in 72+ hours

---

### Question 19: "What is the governance coverage?"
**Expected SQL:**
```sql
SELECT 
  window.start AS window_start,
  tag_coverage,
  lineage_coverage
FROM ${catalog}.${gold_schema}.fact_governance_metrics_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 7;
```
**Expected Result:** Governance metrics over time

---

### Question 20: "Which pipelines have the most dependencies?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_pipeline_data_lineage(
  NULL,
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY dependency_count DESC
LIMIT 10;
```
**Expected Result:** Pipelines with highest dependency counts

---

### 🔬 DEEP RESEARCH QUESTIONS (Complex Multi-Source Analysis)

### Question 21: "Which critical business tables are showing quality degradation AND are predicted to have schema changes, and what is the downstream impact on dependent pipelines?"
**Deep Research Complexity:** Combines quality trend analysis, ML schema change predictions, lineage analysis, and downstream impact assessment across multiple data sources.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify tables with declining quality scores
WITH quality_decline AS (
  SELECT 
    table_name,
    AVG(CASE WHEN window.start >= CURRENT_DATE() - INTERVAL 7 DAYS THEN quality_score END) as recent_quality,
    AVG(CASE WHEN window.start >= CURRENT_DATE() - INTERVAL 30 DAYS 
             AND window.start < CURRENT_DATE() - INTERVAL 7 DAYS THEN quality_score END) as prev_quality
  FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
  WHERE column_name = ':table' AND log_type = 'INPUT'
  GROUP BY table_name
  HAVING recent_quality < prev_quality * 0.95  -- 5%+ decline
),
-- Step 2: Cross-reference with schema change predictions
schema_risk AS (
  SELECT 
    table_name,
    change_probability,
    predicted_change_type,
    risk_factors
  FROM ${catalog}.${gold_schema}.quality_trend_predictions
  WHERE change_probability > 0.5
),
-- Step 3: Get downstream dependencies from lineage
downstream_impact AS (
  SELECT 
    source_table,
    COUNT(DISTINCT target_table) as downstream_table_count,
    COUNT(DISTINCT pipeline_name) as dependent_pipeline_count
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY source_table
)
SELECT 
  q.table_name,
  q.recent_quality,
  q.prev_quality,
  ROUND((q.prev_quality - q.recent_quality) / q.prev_quality * 100, 1) as quality_decline_pct,
  s.change_probability as schema_change_risk,
  s.predicted_change_type,
  d.downstream_table_count,
  d.dependent_pipeline_count,
  CASE 
    WHEN d.dependent_pipeline_count > 5 THEN 'CRITICAL - HIGH BLAST RADIUS'
    WHEN d.dependent_pipeline_count > 2 THEN 'HIGH - MULTIPLE DEPENDENCIES'
    ELSE 'MEDIUM - LIMITED IMPACT'
  END as impact_severity
FROM quality_decline q
JOIN schema_risk s ON q.table_name = s.table_name
LEFT JOIN downstream_impact d ON q.table_name = d.source_table
ORDER BY d.dependent_pipeline_count DESC, s.change_probability DESC
LIMIT 15;
```
**Expected Result:** Critical tables with both quality issues AND predicted schema changes, with full downstream impact assessment.

---

### Question 22: "What is the correlation between data freshness issues and downstream job failures, and which tables should be prioritized for monitoring based on their blast radius?"
**Deep Research Complexity:** Combines freshness analysis, job failure correlation, lineage-based blast radius calculation, and monitoring prioritization.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Get tables with freshness issues
WITH stale_tables AS (
  SELECT 
    table_name,
    hours_since_update,
    freshness_status
  FROM ${catalog}.${gold_schema}.get_table_freshness(
    DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
    DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
    24
  )
  WHERE freshness_status IN ('STALE', 'CRITICAL')
),
-- Step 2: Find jobs that read from these tables
dependent_jobs AS (
  SELECT 
    l.source_table as table_name,
    j.job_name,
    j.result_state,
    j.run_date
  FROM ${catalog}.${gold_schema}.fact_table_lineage l
  JOIN ${catalog}.${gold_schema}.fact_job_run_timeline j 
    ON l.job_id = j.job_id
  WHERE l.event_type = 'READ'
    AND j.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 3: Calculate failure correlation
failure_correlation AS (
  SELECT 
    d.table_name,
    COUNT(DISTINCT d.job_name) as dependent_job_count,
    SUM(CASE WHEN d.result_state = 'FAILED' THEN 1 ELSE 0 END) as job_failures,
    SUM(CASE WHEN d.result_state = 'SUCCESS' THEN 1 ELSE 0 END) as job_successes,
    SUM(CASE WHEN d.result_state = 'FAILED' THEN 1 ELSE 0 END) * 1.0 / 
      NULLIF(COUNT(*), 0) * 100 as failure_rate_when_stale
  FROM dependent_jobs d
  JOIN stale_tables s ON d.table_name = s.table_name
  GROUP BY d.table_name
),
-- Step 4: Calculate blast radius from lineage
blast_radius AS (
  SELECT 
    source_table as table_name,
    COUNT(DISTINCT target_table) as downstream_tables,
    COUNT(DISTINCT user_identity) as data_consumers
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY source_table
)
SELECT 
  s.table_name,
  s.hours_since_update,
  s.freshness_status,
  f.dependent_job_count,
  f.job_failures,
  f.failure_rate_when_stale,
  b.downstream_tables,
  b.data_consumers,
  (f.dependent_job_count * 2 + b.downstream_tables + b.data_consumers) as monitoring_priority_score,
  CASE 
    WHEN f.failure_rate_when_stale > 50 AND b.downstream_tables > 5 THEN '🔴 CRITICAL - IMMEDIATE ACTION'
    WHEN f.failure_rate_when_stale > 25 OR b.downstream_tables > 3 THEN '🟠 HIGH - PRIORITIZE'
    ELSE '🟡 MEDIUM - MONITOR'
  END as priority_recommendation
FROM stale_tables s
LEFT JOIN failure_correlation f ON s.table_name = f.table_name
LEFT JOIN blast_radius b ON s.table_name = b.table_name
ORDER BY monitoring_priority_score DESC
LIMIT 15;
```
**Expected Result:** Correlation analysis between stale tables and job failures, with blast radius assessment and prioritized monitoring recommendations.

---

### Question 23: "What's the end-to-end data quality SLA compliance across our entire data platform, showing which domains and tables are meeting vs. missing SLAs, with root cause attribution?"
**Deep Research Complexity:** Combines freshness SLAs, quality score thresholds, drift tolerances, and ML anomaly detection across all domains to produce a comprehensive SLA compliance report.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Define SLA thresholds by domain (could be parameterized)
WITH sla_definitions AS (
  SELECT 'gold' as domain, 24 as freshness_sla_hours, 80 as quality_sla_score, 0.1 as drift_sla_threshold
  UNION ALL SELECT 'silver', 12, 90, 0.15
  UNION ALL SELECT 'bronze', 6, 70, 0.2
),
-- Step 2: Get current freshness status
freshness_status AS (
  SELECT 
    table_name,
    CASE 
      WHEN table_name LIKE '%gold%' THEN 'gold'
      WHEN table_name LIKE '%silver%' THEN 'silver'
      ELSE 'bronze'
    END as domain,
    hours_since_update,
    freshness_status
  FROM ${catalog}.${gold_schema}.get_table_freshness(
    DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
    DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
    24
  )
),
-- Step 3: Get quality scores from monitoring
quality_scores AS (
  SELECT 
    table_name,
    CASE 
      WHEN table_name LIKE '%gold%' THEN 'gold'
      WHEN table_name LIKE '%silver%' THEN 'silver'
      ELSE 'bronze'
    END as domain,
    quality_score,
    completeness_rate,
    validity_rate
  FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
  WHERE window_end >= CURRENT_DATE() - INTERVAL 1 DAY
    AND column_name = ':table'
    AND log_type = 'INPUT'
),
-- Step 4: Get drift alerts
drift_alerts AS (
  SELECT 
    table_name,
    drift_score,
    is_drifted
  FROM ${catalog}.${gold_schema}.quality_anomaly_predictions
  WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
-- Step 5: Calculate SLA compliance
sla_compliance AS (
  SELECT 
    COALESCE(f.domain, q.domain) as domain,
    COALESCE(f.table_name, q.table_name) as table_name,
    f.hours_since_update,
    s.freshness_sla_hours,
    CASE WHEN f.hours_since_update <= s.freshness_sla_hours THEN 1 ELSE 0 END as freshness_sla_met,
    q.quality_score,
    s.quality_sla_score,
    CASE WHEN q.quality_score >= s.quality_sla_score THEN 1 ELSE 0 END as quality_sla_met,
    d.drift_score,
    s.drift_sla_threshold,
    CASE WHEN COALESCE(d.drift_score, 0) <= s.drift_sla_threshold THEN 1 ELSE 0 END as drift_sla_met
  FROM freshness_status f
  FULL OUTER JOIN quality_scores q ON f.table_name = q.table_name
  LEFT JOIN drift_alerts d ON COALESCE(f.table_name, q.table_name) = d.table_name
  LEFT JOIN sla_definitions s ON COALESCE(f.domain, q.domain) = s.domain
)
SELECT 
  domain,
  COUNT(*) as total_tables,
  SUM(freshness_sla_met) as freshness_compliant,
  SUM(quality_sla_met) as quality_compliant,
  SUM(drift_sla_met) as drift_compliant,
  ROUND(SUM(freshness_sla_met) * 100.0 / COUNT(*), 1) as freshness_compliance_pct,
  ROUND(SUM(quality_sla_met) * 100.0 / COUNT(*), 1) as quality_compliance_pct,
  ROUND(SUM(drift_sla_met) * 100.0 / COUNT(*), 1) as drift_compliance_pct,
  ROUND((SUM(freshness_sla_met) + SUM(quality_sla_met) + SUM(drift_sla_met)) * 100.0 / (COUNT(*) * 3), 1) as overall_sla_compliance_pct,
  COUNT(*) - SUM(freshness_sla_met) as freshness_violations,
  COUNT(*) - SUM(quality_sla_met) as quality_violations,
  COUNT(*) - SUM(drift_sla_met) as drift_violations,
  CASE 
    WHEN (SUM(freshness_sla_met) + SUM(quality_sla_met) + SUM(drift_sla_met)) * 100.0 / (COUNT(*) * 3) >= 95 THEN '🟢 EXCELLENT'
    WHEN (SUM(freshness_sla_met) + SUM(quality_sla_met) + SUM(drift_sla_met)) * 100.0 / (COUNT(*) * 3) >= 80 THEN '🟡 ACCEPTABLE'
    ELSE '🔴 NEEDS ATTENTION'
  END as sla_status
FROM sla_compliance
GROUP BY domain
ORDER BY overall_sla_compliance_pct DESC;
```
**Expected Result:** SLA compliance summary by domain showing freshness, quality, and drift compliance percentages with violation counts and overall status.

---

### Question 24: "Which data quality issues are causing the most downstream impact in terms of failed jobs, user complaints, and data product degradation, and what's the estimated business cost?"
**Deep Research Complexity:** Correlates quality issues with job failures, user activity drops, and lineage impact to quantify the business impact of quality problems.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Get tables with quality issues
WITH quality_issues AS (
  SELECT 
    table_name,
    quality_score,
    completeness_rate,
    validity_rate,
    CASE 
      WHEN quality_score < 50 THEN 'CRITICAL'
      WHEN quality_score < 70 THEN 'WARNING'
      ELSE 'OK'
    END as severity
  FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
  WHERE window_end >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND column_name = ':table'
    AND log_type = 'INPUT'
    AND quality_score < 80
),
-- Step 2: Find downstream jobs that failed after reading these tables
job_impact AS (
  SELECT 
    l.source_table as table_name,
    COUNT(DISTINCT j.job_id) as affected_jobs,
    SUM(CASE WHEN j.result_state = 'FAILED' THEN 1 ELSE 0 END) as failed_runs,
    SUM(j.compute_cost_usd) as wasted_compute_cost
  FROM ${catalog}.${gold_schema}.fact_table_lineage l
  JOIN ${catalog}.${gold_schema}.fact_job_run_timeline j ON l.job_id = j.job_id
  WHERE l.event_type = 'READ'
    AND j.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND j.result_state = 'FAILED'
  GROUP BY l.source_table
),
-- Step 3: Find user activity drops (fewer queries on problematic tables)
user_impact AS (
  SELECT 
    source_table as table_name,
    COUNT(DISTINCT executed_by) as users_affected,
    COUNT(*) as queries_7d,
    LAG(COUNT(*), 1, COUNT(*)) OVER (PARTITION BY source_table ORDER BY DATE_TRUNC('week', execution_date)) as queries_prev_week
  FROM ${catalog}.${gold_schema}.fact_query_history q
  JOIN ${catalog}.${gold_schema}.fact_table_lineage l ON q.statement_id = l.statement_id
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 14 DAYS
  GROUP BY source_table, DATE_TRUNC('week', execution_date)
),
-- Step 4: Calculate blast radius from lineage
blast_radius AS (
  SELECT 
    source_table as table_name,
    COUNT(DISTINCT target_table) as downstream_tables,
    COUNT(DISTINCT workspace_id) as workspaces_affected
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY source_table
)
SELECT 
  q.table_name,
  q.quality_score,
  q.severity as quality_severity,
  ROUND(q.completeness_rate * 100, 1) as completeness_pct,
  ROUND(q.validity_rate * 100, 1) as validity_pct,
  COALESCE(j.affected_jobs, 0) as downstream_jobs_affected,
  COALESCE(j.failed_runs, 0) as failed_job_runs,
  ROUND(COALESCE(j.wasted_compute_cost, 0), 2) as wasted_compute_usd,
  COALESCE(u.users_affected, 0) as users_impacted,
  COALESCE(b.downstream_tables, 0) as downstream_tables,
  COALESCE(b.workspaces_affected, 0) as workspaces_affected,
  -- Calculate composite business impact score
  (COALESCE(j.failed_runs, 0) * 10 + 
   COALESCE(u.users_affected, 0) * 5 + 
   COALESCE(b.downstream_tables, 0) * 3 +
   (100 - q.quality_score) * 2) as business_impact_score,
  -- Estimated business cost (heuristic: $50/failed job + $10/affected user + compute waste)
  ROUND(COALESCE(j.failed_runs, 0) * 50 + COALESCE(u.users_affected, 0) * 10 + COALESCE(j.wasted_compute_cost, 0), 2) as estimated_business_cost_usd,
  CASE 
    WHEN q.severity = 'CRITICAL' AND j.failed_runs > 10 THEN '🔴 CRITICAL: Causing significant downstream failures'
    WHEN q.severity = 'CRITICAL' OR j.failed_runs > 5 THEN '🟠 HIGH: Review and remediate within 24h'
    ELSE '🟡 MEDIUM: Schedule remediation'
  END as remediation_priority
FROM quality_issues q
LEFT JOIN job_impact j ON q.table_name = j.table_name
LEFT JOIN user_impact u ON q.table_name = u.table_name
LEFT JOIN blast_radius b ON q.table_name = b.table_name
ORDER BY business_impact_score DESC
LIMIT 20;
```
**Expected Result:** Tables with quality issues ranked by business impact including failed jobs, wasted compute, affected users, and estimated cost.

---

### Question 25: "What's the predicted quality trajectory for each critical table over the next 7 days based on historical patterns and ML models, and which tables need proactive intervention?"
**Deep Research Complexity:** Uses ML quality predictions, historical trends, and drift detection to forecast quality trajectory and identify tables needing proactive attention.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Get current quality baseline
WITH current_quality AS (
  SELECT 
    table_name,
    quality_score as current_score,
    completeness_rate as current_completeness,
    validity_rate as current_validity,
    window_end as measurement_time
  FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
  WHERE window_end >= CURRENT_DATE() - INTERVAL 1 DAY
    AND column_name = ':table'
    AND log_type = 'INPUT'
),
-- Step 2: Get historical quality trend (30 days)
historical_trend AS (
  SELECT 
    table_name,
    -- Calculate 30-day trend
    CORR(DATEDIFF(window_end, CURRENT_DATE()), quality_score) as quality_trend_slope,
    AVG(quality_score) as avg_quality_30d,
    STDDEV(quality_score) as quality_volatility,
    MIN(quality_score) as min_quality_30d,
    MAX(quality_score) as max_quality_30d
  FROM ${catalog}.${gold_schema}.fact_table_quality_profile_metrics
  WHERE window_end >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND column_name = ':table'
    AND log_type = 'INPUT'
  GROUP BY table_name
),
-- Step 3: Get ML quality predictions
ml_predictions AS (
  SELECT 
    table_name,
    drift_score,
    is_drifted,
    prediction_confidence
  FROM ${catalog}.${gold_schema}.quality_anomaly_predictions
  WHERE prediction_date = CURRENT_DATE()
),
-- Step 4: Get quality trend predictions
trend_predictions AS (
  SELECT 
    table_name,
    predicted_quality_score,
    trend_direction,
    confidence
  FROM ${catalog}.${gold_schema}.quality_trend_predictions
  WHERE prediction_date BETWEEN CURRENT_DATE() AND CURRENT_DATE() + INTERVAL 7 DAYS
),
-- Step 5: Combine and predict trajectory
predictions AS (
  SELECT 
    c.table_name,
    c.current_score,
    h.quality_trend_slope,
    h.avg_quality_30d,
    h.quality_volatility,
    m.drift_score,
    m.is_drifted,
    t.predicted_quality_score as ml_predicted_score,
    t.trend_direction,
    -- Calculate predicted score (weighted: 60% ML, 40% trend extrapolation)
    COALESCE(t.predicted_quality_score, c.current_score + (h.quality_trend_slope * 7)) * 0.6 +
    (c.current_score + (h.quality_trend_slope * 7)) * 0.4 as weighted_predicted_score,
    -- Risk assessment
    CASE 
      WHEN m.is_drifted AND h.quality_trend_slope < -1 THEN 'HIGH_RISK'
      WHEN h.quality_trend_slope < -0.5 OR c.current_score < 70 THEN 'MEDIUM_RISK'
      ELSE 'LOW_RISK'
    END as risk_level
  FROM current_quality c
  LEFT JOIN historical_trend h ON c.table_name = h.table_name
  LEFT JOIN ml_predictions m ON c.table_name = m.table_name
  LEFT JOIN trend_predictions t ON c.table_name = t.table_name
)
SELECT 
  table_name,
  ROUND(current_score, 1) as current_quality_score,
  ROUND(weighted_predicted_score, 1) as predicted_7d_score,
  ROUND(weighted_predicted_score - current_score, 1) as predicted_change,
  ROUND(quality_trend_slope, 2) as daily_trend_slope,
  ROUND(quality_volatility, 2) as volatility,
  COALESCE(is_drifted, FALSE) as drift_detected,
  ROUND(drift_score, 3) as drift_score,
  risk_level,
  CASE 
    WHEN weighted_predicted_score < 60 AND current_score >= 60 THEN '🔴 PREDICTED DEGRADATION: Quality will drop below threshold'
    WHEN weighted_predicted_score < current_score - 10 THEN '🟠 DECLINING: Significant quality drop expected'
    WHEN weighted_predicted_score > current_score + 5 THEN '🟢 IMPROVING: Quality trending upward'
    ELSE '🟡 STABLE: Minor fluctuation expected'
  END as trajectory_status,
  CASE 
    WHEN risk_level = 'HIGH_RISK' THEN 'IMMEDIATE: Review data sources and pipeline health'
    WHEN risk_level = 'MEDIUM_RISK' THEN 'THIS WEEK: Schedule quality check and root cause analysis'
    ELSE 'MONITOR: Continue standard monitoring'
  END as intervention_recommendation
FROM predictions
WHERE risk_level IN ('HIGH_RISK', 'MEDIUM_RISK') OR weighted_predicted_score < 80
ORDER BY weighted_predicted_score ASC, risk_level DESC
LIMIT 20;
```
**Expected Result:** Tables with predicted quality trajectory showing current vs. predicted scores, trend analysis, and proactive intervention recommendations.

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

