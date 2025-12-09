# Phase 3: Use Cases for Databricks Health Monitor

## Overview

**Status:** 📋 Planned  
**Purpose:** Implement advanced analytics, AI/BI capabilities, and semantic layer features to enable comprehensive Databricks platform observability.

---

## Phase 3 Addendums

Each addendum has its own detailed document with comprehensive implementation plans:

| Addendum | Topic | Document | Dependencies | Status |
|----------|-------|----------|--------------|--------|
| **3.1** | ML Models | [📄 phase3-addendum-3.1-ml-models.md](./phase3-addendum-3.1-ml-models.md) | Gold Layer | 🔧 **Significantly Enhanced** |
| **3.2** | Table-Valued Functions | [📄 phase3-addendum-3.2-tvfs.md](./phase3-addendum-3.2-tvfs.md) | Gold Layer | 🔧 Enhanced |
| **3.3** | UC Metric Views | [📄 phase3-addendum-3.3-metric-views.md](./phase3-addendum-3.3-metric-views.md) | Gold Layer | 🔧 Enhanced |
| **3.4** | Lakehouse Monitoring | [📄 phase3-addendum-3.4-lakehouse-monitoring.md](./phase3-addendum-3.4-lakehouse-monitoring.md) | Gold Layer, ML Models | 🔧 Enhanced |
| **3.5** | AI/BI Dashboards | [📄 phase3-addendum-3.5-ai-bi-dashboards.md](./phase3-addendum-3.5-ai-bi-dashboards.md) | Metric Views, TVFs | 🔧 **Significantly Enhanced** |
| **3.6** | Genie Spaces | [📄 phase3-addendum-3.6-genie-spaces.md](./phase3-addendum-3.6-genie-spaces.md) | Metric Views, TVFs | 🔧 Enhanced |
| **3.7** | Alerting Framework | [📄 phase3-addendum-3.7-alerting-framework.md](./phase3-addendum-3.7-alerting-framework.md) | Gold Layer, TVFs, Monitoring | 🆕 **NEW** |

---

## 🆕 Inspiration Sources & Patterns Discovered

The Phase 3 addendums have been significantly enriched based on analysis of real-world Databricks dashboards and community patterns.

### Dashboard Patterns Analyzed

| Dashboard Source | Key Patterns Extracted |
|------------------|------------------------|
| **DBSQL Warehouse Advisor v5** | Query efficiency ratios, performance flags (HighDataVolume, HighQueueing, HighResultFetch), cost allocation by query time proportion, queue time analysis |
| **Jobs System Tables Dashboard** | Most retried jobs with repair cost, stale datasets detection, job cost savings (CPU utilization), autoscaling opportunities, spend by custom tags, all-purpose cluster detection, outlier runs (P90 deviation) |
| **Serverless Cost Observability** | Most expensive notebooks, user cost breakdown (jobs + notebooks), 7-14 day growth analysis, week-over-week trends |
| **DBR Migration Dashboard** | Legacy DBR detection, version distribution, serverless adoption tracking |
| **LakeFlow Dashboard** | Top N jobs/pipelines with tag filtering, entity type classification |
| **Workflow Advisor** | Job optimization patterns, repair time tracking |
| **Governance Hub** | Security and audit patterns |

### New Query Patterns Added

| Pattern Category | Pattern Count | Example Use Cases |
|-----------------|---------------|-------------------|
| **Cost Optimization** | 8 patterns | Tag-based chargeback, growth analysis, savings opportunities |
| **Job Optimization** | 6 patterns | Stale datasets, autoscaling, AP cluster detection |
| **Query Efficiency** | 4 patterns | Efficiency ratios, performance flags, queue analysis |
| **Reliability** | 4 patterns | Retry costs, failure analysis, outlier detection |
| **Migration/Modernization** | 3 patterns | DBR version tracking, serverless adoption |
| **Total** | **25+ patterns** | |

### Key Insights for Implementation

1. **Cost Allocation**: Use proportional warehouse time to allocate query costs
2. **Right-Sizing**: CPU utilization < 50% indicates over-provisioned clusters
3. **Stale Data**: Jobs producing datasets with no downstream consumers waste compute
4. **Autoscaling**: Static clusters >1 worker without autoscaling are optimization candidates
5. **P90 Deviation**: Jobs with max cost >> P90 cost have runaway runs to investigate
6. **Tag Hygiene**: Untagged jobs prevent accurate chargeback and ownership tracking

### 🆕 Critical FinOps Use Cases Added

Based on user requirements, two critical FinOps use cases have been integrated across all Phase 3 addendums:

#### 1. 📊 Commit Amount Tracking with ML Forecast

**Use Case:** Users can configure their Databricks commit amount, and the system provides:
- Monthly run rate required to meet commit vs actual run rate
- ML-based forecast showing predicted month-end/year-end spend
- Early warning when trending toward undershoot/overshoot

**Artifacts:**
- **Configuration Table:** `commit_configurations` (stores annual commit, thresholds)
- **TVFs:** `get_commit_vs_actual`, `get_commit_forecast`
- **Metric View:** `commit_tracking_metrics`
- **Dashboard:** "Commit Tracking & Budget Forecast Dashboard"
- **Alerts:** COST-009/010/011 (Undershoot/Overshoot Risk)
- **ML Model:** Budget Forecaster (predicts monthly spend with P10/P50/P90)

#### 2. 🏷️ Tag-Based Cost Attribution

**Use Case:** Native tag support throughout the solution for fine-grained chargeback and discoverability.
Tags from `custom_tags` column in [billing table](https://docs.databricks.com/aws/en/admin/system-tables/billing) are surfaced across all artifacts.

**Key Tag Dimensions:** `team`, `project`, `cost_center`, `env`

**Artifacts:**
- **TVFs:** `get_cost_by_tag`, `get_untagged_resources`, `get_tag_coverage`
- **Metric View Dimensions:** team_tag, project_tag, cost_center_tag, env_tag, is_tagged
- **Metric View Measures:** tagged_cost, untagged_cost, tag_coverage_pct
- **Dashboard:** "Tag-Based Cost Attribution Dashboard"
- **Alerts:** COST-012/013/014 (Tag Coverage, Untagged High-Cost Jobs, New Untagged Resources)
- **Lakehouse Monitor Metrics:** tag_coverage_pct, untagged_cost_total, tag_coverage_drift

---

## 🏗️ Agent Domain Framework

All Phase 3 artifacts (TVFs, Metric Views, Dashboards, Monitors, Genie Spaces) are organized around the **5 Agent Domains** defined in Phase 4:

| Agent Domain | Purpose | Gold Tables | Key Metrics |
|--------------|---------|-------------|-------------|
| **💰 Cost** | FinOps, budgets, chargeback | `fact_usage`, `dim_sku`, `dim_workspace` | Total cost, DBU usage, cost per owner |
| **🔒 Security** | Access audit, compliance | `fact_table_lineage`, `fact_audit_events` | Access patterns, sensitive data |
| **⚡ Performance** | Query optimization, capacity | `fact_query_history`, `fact_node_timeline` | P95 duration, queue time, efficiency |
| **🔄 Reliability** | Job health, SLAs | `fact_job_run_timeline`, `dim_job` | Success rate, failure count, repair cost |
| **✅ Quality** | Data quality, governance | `fact_data_quality_monitoring_table_results` | Quality scores, violations |

### Artifacts by Agent Domain

```
Phase 3 Tools (organized by Agent Domain)
├── 💰 Cost Agent Tools
│   ├── TVFs: get_top_cost_contributors, get_cost_by_owner, get_cost_growth_analysis
│   ├── Metric View: cost_analytics_metrics
│   ├── Dashboard: Cost Management, Job Cost Savings
│   ├── Monitor: Cost Data Quality Monitor
│   ├── Alerts: COST-001 to COST-008 (8 alerts)
│   ├── ML Models: Cost Anomaly Detector, Budget Forecaster, Job Cost Optimizer
│   └── Genie Space: Cost Intelligence
│
├── 🔒 Security Agent Tools
│   ├── TVFs: get_user_activity_summary, get_sensitive_table_access
│   ├── Metric View: security_analytics_metrics
│   ├── Dashboard: Security & Audit Dashboard
│   ├── Alerts: SEC-001 to SEC-006 (6 alerts)
│   ├── ML Models: Threat Detector, Exfiltration Detector, Privilege Abuse Detector
│   └── Genie Space: Security Auditor
│
├── ⚡ Performance Agent Tools
│   ├── TVFs: get_slow_queries, get_warehouse_utilization, get_cluster_utilization
│   ├── Metric View: query_analytics_metrics, cluster_utilization_metrics
│   ├── Dashboard: Query Performance, Cluster Utilization, DBR Migration
│   ├── Monitor: Query Performance Monitor, Cluster Utilization Monitor
│   ├── Alerts: PERF-001 to PERF-008 (8 alerts)
│   ├── ML Models: Query Forecaster, Warehouse Optimizer, Capacity Planner, DBR Migration Risk
│   └── Genie Space: Query Performance Analyzer, Cluster Optimizer
│
├── 🔄 Reliability Agent Tools
│   ├── TVFs: get_failed_jobs, get_job_success_rate, get_job_repair_costs
│   ├── Metric View: job_performance_metrics
│   ├── Dashboard: Job Reliability, Job Optimization
│   ├── Monitor: Job Reliability Monitor
│   ├── Alerts: REL-001 to REL-008 (8 alerts)
│   ├── ML Models: Job Failure Predictor, SLA Breach Predictor, Retry Success Predictor
│   └── Genie Space: Job Health Monitor
│
└── ✅ Quality Agent Tools
    ├── TVFs: get_data_quality_summary, get_tables_failing_quality
    ├── Metric View: data_quality_metrics
    ├── Dashboard: Table Health Advisor
    ├── Monitor: Data Quality Monitor
    ├── Alerts: QUAL-001 to QUAL-005 (5 alerts)
    ├── ML Models: Freshness Predictor, Schema Drift Detector, Quality Degradation Forecaster
    └── Genie Space: Data Quality Analyst
```

---

## ⚠️ Gold Layer Pattern (REQUIRED)

**All queries in Phase 3 artifacts MUST use Gold layer tables, NOT system tables directly.**

### ❌ DON'T: Query system tables
```sql
SELECT * FROM system.billing.usage WHERE ...
SELECT * FROM system.lakeflow.job_run_timeline WHERE ...
```

### ✅ DO: Query Gold layer tables
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_usage WHERE ...
SELECT * FROM ${catalog}.${gold_schema}.fact_job_run_timeline WHERE ...
```

---

## Quick Reference Summary

### Addendum 3.1: ML Models for Databricks Health Monitor

**Detailed Plan:** [phase3-addendum-3.1-ml-models.md](./phase3-addendum-3.1-ml-models.md)

### Purpose

Train machine learning models on system tables data to enable predictive analytics, anomaly detection, and intelligent alerting.

### Proposed Models

| Model | Domain | Purpose | Input Features |
|-------|--------|---------|----------------|
| **Cost Anomaly Detector** | Billing | Detect unusual spending patterns | DBU usage, cluster types, time patterns |
| **Job Failure Predictor** | Lakeflow | Predict job failures before they occur | Historical run metrics, cluster health |
| **Query Performance Forecaster** | Query | Forecast query latency | Query patterns, warehouse utilization |
| **Capacity Planner** | Compute | Recommend cluster sizing | Historical utilization, workload patterns |
| **Security Threat Detector** | Security | Identify suspicious access patterns | Audit logs, access patterns |

### Implementation Approach

```
Gold Layer Facts
      │
      ▼
┌─────────────────────┐
│   Feature Store     │
│   (Unity Catalog)   │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│   MLflow Training   │
│   Experiments       │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│   Model Registry    │
│   (Unity Catalog)   │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│   Model Serving     │
│   Endpoints         │
└─────────────────────┘
```

### Feature Engineering Examples

**Cost Anomaly Detection Features:**
- `daily_dbu_usage` - Total DBUs consumed per day
- `dbu_7day_moving_avg` - 7-day rolling average
- `dbu_std_dev` - Standard deviation of recent usage
- `day_of_week` - Cyclical encoding for weekly patterns
- `hour_of_day` - For hourly cost patterns
- `workspace_count` - Active workspaces
- `cluster_count` - Active clusters

**Job Failure Prediction Features:**
- `historical_failure_rate` - Job-specific failure rate
- `avg_runtime_minutes` - Historical average runtime
- `cluster_memory_gb` - Cluster configuration
- `task_count` - Number of tasks in job
- `dependency_count` - Upstream dependencies
- `time_since_last_success` - Hours since last success

### Model Training Pipeline

```yaml
# resources/ml/model_training_job.yml
resources:
  jobs:
    health_monitor_ml_training:
      name: "[${bundle.target}] Health Monitor - ML Training"
      
      tasks:
        - task_key: prepare_features
          notebook_task:
            notebook_path: ../src/ml/prepare_features.py
        
        - task_key: train_cost_anomaly_model
          depends_on: [prepare_features]
          notebook_task:
            notebook_path: ../src/ml/train_cost_anomaly.py
        
        - task_key: train_job_failure_model
          depends_on: [prepare_features]
          notebook_task:
            notebook_path: ../src/ml/train_job_failure.py
        
        - task_key: register_models
          depends_on: [train_cost_anomaly_model, train_job_failure_model]
          notebook_task:
            notebook_path: ../src/ml/register_models.py
      
      schedule:
        quartz_cron_expression: "0 0 3 * * ?"  # Daily at 3 AM
```

### Model Serving Endpoints

| Endpoint | Model | Use Case |
|----------|-------|----------|
| `health-monitor-cost-anomaly` | Cost Anomaly Detector | Real-time cost alerts |
| `health-monitor-job-predictor` | Job Failure Predictor | Pre-run failure warnings |
| `health-monitor-query-forecast` | Query Forecaster | Capacity planning |

### Success Criteria

- [ ] 3+ ML models trained and registered
- [ ] Feature store populated from Gold layer
- [ ] Model serving endpoints deployed
- [ ] Inference tables logging predictions
- [ ] A/B testing framework for model comparison

---

### Addendum 3.2: Table-Valued Functions for Genie

**Detailed Plan:** [phase3-addendum-3.2-tvfs.md](./phase3-addendum-3.2-tvfs.md)

#### Purpose

Create parameterized SQL functions that encapsulate complex business logic and enable natural language queries through Databricks Genie.

#### Reference

See [cursor rule: Table-Valued Functions](../.cursor/rules/15-databricks-table-valued-functions.mdc)

### Proposed TVFs by Domain

#### Cost Analysis Functions

```sql
-- Top cost contributors
get_top_cost_contributors(
  start_date STRING,
  end_date STRING,
  top_n INT DEFAULT 10
) RETURNS TABLE(...)

-- Cost trend analysis
get_cost_trend_by_sku(
  start_date STRING,
  end_date STRING,
  sku_name STRING DEFAULT 'ALL'
) RETURNS TABLE(...)

-- Budget variance
get_budget_variance(
  budget_amount DOUBLE,
  start_date STRING,
  end_date STRING
) RETURNS TABLE(...)
```

#### Job Performance Functions

```sql
-- Failed jobs analysis
get_failed_jobs(
  start_date STRING,
  end_date STRING,
  workspace_id STRING DEFAULT 'ALL'
) RETURNS TABLE(...)

-- Job duration trends
get_job_duration_trends(
  job_name STRING,
  days_back INT DEFAULT 30
) RETURNS TABLE(...)

-- SLA compliance
get_job_sla_compliance(
  sla_minutes INT,
  start_date STRING,
  end_date STRING
) RETURNS TABLE(...)
```

#### Query Performance Functions

```sql
-- Slow queries
get_slow_queries(
  min_duration_seconds INT DEFAULT 300,
  start_date STRING,
  end_date STRING
) RETURNS TABLE(...)

-- Warehouse utilization
get_warehouse_utilization(
  warehouse_id STRING,
  start_date STRING,
  end_date STRING
) RETURNS TABLE(...)
```

#### Security Functions

```sql
-- Access anomalies
get_access_anomalies(
  start_date STRING,
  end_date STRING,
  anomaly_threshold DOUBLE DEFAULT 2.0
) RETURNS TABLE(...)

-- User activity summary
get_user_activity_summary(
  user_email STRING,
  days_back INT DEFAULT 30
) RETURNS TABLE(...)
```

### Implementation Pattern

```sql
CREATE OR REPLACE FUNCTION get_top_cost_contributors(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top contributors'
)
RETURNS TABLE(
  rank INT COMMENT 'Cost rank',
  workspace_name STRING COMMENT 'Workspace name',
  sku_name STRING COMMENT 'SKU name',
  total_dbu DOUBLE COMMENT 'Total DBU consumed',
  total_cost DOUBLE COMMENT 'Estimated cost (USD)',
  pct_of_total DOUBLE COMMENT 'Percentage of total cost'
)
COMMENT 'LLM: Returns top cost contributors by workspace and SKU. 
Use for cost optimization and chargeback analysis.
Example: "What are the top 10 cost drivers this month?"'
RETURN
  WITH cost_data AS (
    SELECT ...
    FROM fact_usage
    WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
  ),
  ranked_costs AS (
    SELECT ..., ROW_NUMBER() OVER (ORDER BY total_cost DESC) as rank
    FROM cost_data
  )
  SELECT * FROM ranked_costs WHERE rank <= top_n;
```

### TVF Inventory

| Domain | TVF Count | Example Functions |
|--------|-----------|-------------------|
| **Billing** | 5 | cost contributors, trends, forecasts |
| **Lakeflow** | 6 | job failures, durations, SLA |
| **Query** | 4 | slow queries, warehouse usage |
| **Security** | 4 | access anomalies, user activity |
| **Compute** | 3 | cluster utilization, scaling events |
| **MLflow** | 3 | experiment comparison, model drift |
| **Total** | 25 | |

### Success Criteria

- [ ] 25+ TVFs created across all domains
- [ ] All TVFs use STRING for date parameters (Genie compatible)
- [ ] LLM-friendly COMMENT on every function
- [ ] Tested with Genie natural language queries
- [ ] Documentation with example queries

---

### Addendum 3.3: UC Metric Views for Genie

**Detailed Plan:** [phase3-addendum-3.3-metric-views.md](./phase3-addendum-3.3-metric-views.md)

#### Purpose

Create semantic layer metric views that enable natural language analytics through Databricks Genie with pre-defined dimensions, measures, and business logic.

#### Reference

See [cursor rule: Metric Views Patterns](../.cursor/rules/14-metric-views-patterns.mdc)

### Proposed Metric Views

| Metric View | Source Fact | Key Measures | Key Dimensions |
|-------------|-------------|--------------|----------------|
| `cost_analytics` | fact_usage | total_dbu, total_cost | workspace, sku, date |
| `job_performance` | fact_job_run_timeline | success_rate, avg_duration | job, workspace, date |
| `query_performance` | fact_query_history | avg_latency, query_count | warehouse, user, date |
| `cluster_utilization` | fact_node_timeline | cpu_utilization, memory_usage | cluster, workspace, date |
| `security_events` | fact_audit_logs | event_count, unique_users | service, action, date |
| `ml_experiment_metrics` | fact_mlflow_runs | run_count, avg_metrics | experiment, user, date |

### Metric View Structure (v1.1)

```yaml
version: "1.1"

- name: cost_analytics
  comment: "Cost and usage analytics for Databricks platform. 
    Enables natural language queries about spending, DBU usage, and cost trends."
  
  source: ${catalog}.${gold_schema}.fact_usage
  
  joins:
    - name: dim_workspace
      source: ${catalog}.${gold_schema}.dim_workspace
      'on': source.workspace_id = dim_workspace.workspace_id
    
    - name: dim_sku
      source: ${catalog}.${gold_schema}.dim_sku
      'on': source.sku_name = dim_sku.sku_name
  
  dimensions:
    - name: workspace_name
      expr: dim_workspace.workspace_name
      comment: "Name of the Databricks workspace"
      display_name: "Workspace"
      synonyms: [workspace, environment]
    
    - name: sku_name
      expr: source.sku_name
      comment: "Databricks SKU (product category)"
      display_name: "SKU"
      synonyms: [product, service type]
    
    - name: usage_date
      expr: source.usage_date
      comment: "Date of usage"
      display_name: "Date"
      synonyms: [day, date]
  
  measures:
    - name: total_dbu
      expr: SUM(source.usage_quantity)
      comment: "Total DBU consumed"
      display_name: "Total DBU"
      format:
        type: number
        decimal_places:
          type: exact
          places: 2
      synonyms: [dbu, usage, consumption]
    
    - name: estimated_cost
      expr: SUM(source.usage_quantity * source.list_price)
      comment: "Estimated cost in USD"
      display_name: "Cost"
      format:
        type: currency
        currency_code: USD
      synonyms: [cost, spend, expense]
    
    - name: workspace_count
      expr: COUNT(DISTINCT source.workspace_id)
      comment: "Number of unique workspaces"
      display_name: "Workspaces"
```

### Measure Categories

| Category | Measures | Use Cases |
|----------|----------|-----------|
| **Volume** | counts, sums, totals | "How many jobs ran?" |
| **Averages** | avg_duration, avg_cost | "What's the average query time?" |
| **Rates** | success_rate, failure_rate | "What's the job success rate?" |
| **Trends** | yoy_growth, mom_change | "How did costs change?" |
| **Rankings** | top_n, percentile | "What are top cost drivers?" |

### Success Criteria

- [ ] 6+ metric views created
- [ ] All measures include format specifications
- [ ] 5+ synonyms per dimension/measure
- [ ] Joins include SCD2 filtering where needed
- [ ] Tested with Genie natural language queries

---

### Addendum 3.4: Lakehouse Monitoring

**Detailed Plan:** [phase3-addendum-3.4-lakehouse-monitoring.md](./phase3-addendum-3.4-lakehouse-monitoring.md)

#### Purpose

Implement Lakehouse Monitoring for Gold layer tables and ML inference tables to enable automatic profiling, drift detection, and custom business metrics.

#### Reference

See [cursor rule: Lakehouse Monitoring](../.cursor/rules/17-lakehouse-monitoring-comprehensive.mdc)

### Monitoring Strategy

| Table Type | Monitor Mode | Key Metrics |
|------------|--------------|-------------|
| **Fact Tables** | Time Series | Row counts, null rates, aggregates |
| **Dimension Tables** | Snapshot | Cardinality, freshness |
| **ML Inference Tables** | Inference | Prediction distribution, drift |

### Custom Metrics by Domain

#### Cost Monitoring Metrics

```python
# AGGREGATE metrics (base measurements)
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
    name="total_daily_dbu",
    input_columns=[":table"],
    definition="SUM(usage_quantity)"
),

# DERIVED metrics (business ratios)
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
    name="avg_cost_per_workspace",
    input_columns=[":table"],
    definition="total_daily_cost / NULLIF(workspace_count, 0)"
),

# DRIFT metrics (period-over-period)
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
    name="cost_drift_pct",
    input_columns=[":table"],
    definition="(({{current_df}}.total_daily_cost - {{base_df}}.total_daily_cost) / NULLIF({{base_df}}.total_daily_cost, 0)) * 100"
)
```

#### Job Performance Metrics

```python
MonitorMetric(
    name="job_success_rate",
    input_columns=[":table"],
    definition="(COUNT(CASE WHEN result_state = 'SUCCESS' THEN 1 END) / NULLIF(COUNT(*), 0)) * 100"
),

MonitorMetric(
    name="avg_job_duration_minutes",
    input_columns=[":table"],
    definition="AVG(TIMESTAMPDIFF(MINUTE, period_start_time, period_end_time))"
),

MonitorMetric(
    name="sla_breach_count",
    input_columns=[":table"],
    definition="COUNT(CASE WHEN duration_minutes > sla_threshold THEN 1 END)"
)
```

### ML Inference Monitoring

For ML models deployed in Addendum 3.1:

```python
# Cost anomaly model inference monitoring
workspace_client.quality_monitors.create(
    table_name=f"{catalog}.{schema}.cost_anomaly_predictions",
    inference_log=MonitorInferenceLog(
        model_id_col="model_version",
        prediction_col="anomaly_score",
        timestamp_col="prediction_timestamp",
        problem_type="PROBLEM_TYPE_REGRESSION"
    ),
    custom_metrics=[
        MonitorMetric(
            name="anomaly_detection_rate",
            definition="(COUNT(CASE WHEN is_anomaly THEN 1 END) / NULLIF(COUNT(*), 0)) * 100"
        )
    ]
)
```

### Monitoring Configuration

```yaml
# resources/monitoring/lakehouse_monitors.yml
resources:
  jobs:
    setup_lakehouse_monitors:
      tasks:
        - task_key: setup_cost_monitors
        - task_key: setup_job_monitors
        - task_key: setup_inference_monitors
```

### Output Tables

| Monitor | Profile Table | Drift Table |
|---------|---------------|-------------|
| fact_usage | fact_usage_profile_metrics | fact_usage_drift_metrics |
| fact_job_run | fact_job_run_profile_metrics | fact_job_run_drift_metrics |
| cost_predictions | cost_predictions_profile_metrics | cost_predictions_drift_metrics |

### Success Criteria

- [ ] Monitors created for all key Gold tables
- [ ] Custom metrics aligned with business KPIs
- [ ] Drift detection configured with thresholds
- [ ] ML inference monitoring for deployed models
- [ ] Alerting configured for anomalies

---

### Addendum 3.5: AI/BI Dashboards

**Detailed Plan:** [phase3-addendum-3.5-ai-bi-dashboards.md](./phase3-addendum-3.5-ai-bi-dashboards.md)

#### Purpose

Create production-grade AI/BI dashboards for Databricks platform observability using Lakeview dashboards with proper system table queries and layout formatting.

#### Reference

See [cursor rule: AI/BI Dashboards](../.cursor/rules/18-databricks-aibi-dashboards.mdc)

### Proposed Dashboards

| Dashboard | Primary Focus | Target Users |
|-----------|---------------|--------------|
| **Cost Intelligence** | DBU usage, spending trends | Finance, Platform Team |
| **Job Operations** | Job success, failures, SLA | Data Engineering |
| **Query Performance** | Query latency, warehouse usage | Data Engineering, Analysts |
| **Security Posture** | Audit events, access patterns | Security Team |
| **ML Operations** | Experiments, model performance | ML Engineers |
| **Executive Summary** | High-level KPIs | Leadership |

### Dashboard Structure

#### Cost Intelligence Dashboard

**Pages:**
1. **Overview** - KPIs: Total DBU, Total Cost, Workspace Count, Active SKUs
2. **Trends** - Cost over time, DBU by SKU, MoM comparison
3. **Breakdown** - Cost by workspace, by SKU, by cluster type
4. **Anomalies** - Cost spikes, unusual patterns

**Key Visualizations:**
- KPI counters (6-column grid)
- Line chart: Cost trend over time
- Stacked bar: DBU by SKU category
- Table: Top 10 cost contributors
- Pie chart: Cost distribution by workspace

**SQL Pattern:**
```sql
-- Cost trend by day
SELECT 
  usage_date,
  SUM(usage_quantity) as total_dbu,
  SUM(usage_quantity * list_price) as estimated_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= :start_date
  AND usage_date <= :end_date
GROUP BY usage_date
ORDER BY usage_date
```

#### Job Operations Dashboard

**Pages:**
1. **Overview** - KPIs: Total Runs, Success Rate, Failed Jobs, Avg Duration
2. **Failures** - Failed job list, failure reasons, impact analysis
3. **Performance** - Duration trends, SLA compliance
4. **Capacity** - Concurrent runs, cluster utilization

**Key Visualizations:**
- KPI counters: Success rate, failure count
- Line chart: Success rate trend
- Bar chart: Failures by job
- Table: Recent failures with details
- Heatmap: Job runs by hour/day

### Layout Pattern (6-Column Grid)

```json
{
  "pages": [
    {
      "name": "overview",
      "displayName": "Overview",
      "layout": [
        {"widget": "kpi_total_cost", "position": {"x": 0, "y": 0, "width": 2, "height": 2}},
        {"widget": "kpi_total_dbu", "position": {"x": 2, "y": 0, "width": 2, "height": 2}},
        {"widget": "kpi_workspaces", "position": {"x": 4, "y": 0, "width": 2, "height": 2}},
        {"widget": "chart_cost_trend", "position": {"x": 0, "y": 2, "width": 3, "height": 6}},
        {"widget": "chart_dbu_by_sku", "position": {"x": 3, "y": 2, "width": 3, "height": 6}},
        {"widget": "table_top_contributors", "position": {"x": 0, "y": 8, "width": 6, "height": 6}}
      ]
    }
  ]
}
```

### Success Criteria

- [ ] 6 dashboards created and published
- [ ] All use 6-column grid layout
- [ ] Global filters page on each dashboard
- [ ] Queries use Gold layer tables (not system tables directly)
- [ ] Mobile-responsive design
- [ ] Published to workspace folder

---

### Addendum 3.6: Genie Spaces

**Detailed Plan:** [phase3-addendum-3.6-genie-spaces.md](./phase3-addendum-3.6-genie-spaces.md)

#### Purpose

Configure Databricks Genie Spaces with comprehensive agent instructions, trusted data assets, and benchmark questions to enable natural language analytics for platform observability.

#### Reference

See [cursor rule: Genie Space Patterns](../.cursor/rules/16-genie-space-patterns.mdc)

### Proposed Genie Spaces

| Space | Focus Area | Primary Users |
|-------|------------|---------------|
| **Cost Analyst** | Billing, usage, cost optimization | Finance |
| **Platform Ops** | Jobs, clusters, performance | Platform Team |
| **Security Analyst** | Audit, access, compliance | Security |
| **ML Engineer** | Experiments, models, serving | ML Team |

### Cost Analyst Genie Space

**Description:**
```
Databricks Cost Intelligence Assistant

Analyze platform costs, DBU usage, and spending patterns across workspaces.

AVAILABLE ANALYTICS:
• Cost trends and forecasts
• DBU consumption by SKU
• Workspace cost allocation
• Cost anomaly detection
• Budget variance analysis

EXAMPLE QUESTIONS:
• "What were our top 10 cost drivers last month?"
• "How did DBU usage change compared to last quarter?"
• "Which workspaces have the highest cost growth?"
• "Show me cost anomalies in the last week"
```

**Agent Instructions:**
```
BUSINESS DOMAIN KNOWLEDGE:

1. COST STRUCTURE
   • DBU (Databricks Unit) is the billing unit
   • SKUs represent product categories (Jobs Compute, SQL, ML)
   • Pricing varies by SKU and commitment tier

2. KEY METRICS
   • Total DBU = SUM(usage_quantity)
   • Total Cost = SUM(usage_quantity * list_price)
   • Cost per Workspace = Total Cost / workspace_count

3. TIME INTELLIGENCE
   • MoM = (current_month - prior_month) / prior_month * 100
   • YoY = (current_year - prior_year) / prior_year * 100

DATA ASSETS:
• cost_analytics (Metric View) - Primary for cost queries
• get_top_cost_contributors() - For ranking queries
• get_cost_trend_by_sku() - For trend analysis

QUERY PATTERNS:
• "top N" → Use ROW_NUMBER and WHERE rank <= N
• "trend" → Order by date, use line visualization
• "compare" → Use CASE WHEN for pivoting
```

**Trusted Data Assets:**
1. `cost_analytics` (Metric View)
2. `get_top_cost_contributors(start_date, end_date, top_n)`
3. `get_cost_trend_by_sku(start_date, end_date, sku_name)`
4. `get_budget_variance(budget_amount, start_date, end_date)`

**Benchmark Questions:**
1. "What are the top 10 cost drivers this month?"
2. "How did our DBU usage change compared to last month?"
3. "Which SKU has the highest cost growth?"
4. "Show me daily cost trend for the last 30 days"
5. "What's our cost by workspace?"

### Platform Ops Genie Space

**Trusted Data Assets:**
1. `job_performance` (Metric View)
2. `cluster_utilization` (Metric View)
3. `get_failed_jobs(start_date, end_date, workspace_id)`
4. `get_job_sla_compliance(sla_minutes, start_date, end_date)`
5. `get_slow_queries(min_duration_seconds, start_date, end_date)`

**Benchmark Questions:**
1. "What's our job success rate this week?"
2. "Show me failed jobs in the last 24 hours"
3. "Which jobs have the longest average runtime?"
4. "Are there any SLA breaches today?"
5. "What's our warehouse utilization?"

### Success Criteria

- [ ] 4 Genie Spaces created
- [ ] Comprehensive agent instructions (500+ lines each)
- [ ] All metric views and TVFs added as trusted assets
- [ ] 20+ benchmark questions per space
- [ ] User training materials created
- [ ] 90%+ query success rate in testing

---

## Phase 3 Summary

| Addendum | Deliverables | Dependencies |
|----------|--------------|--------------|
| **3.1 ML Models** | 5 models, feature store, serving endpoints | Gold Layer |
| **3.2 TVFs** | 25 table-valued functions | Gold Layer |
| **3.3 Metric Views** | 6 metric views | Gold Layer |
| **3.4 Monitoring** | Profile + drift monitors, custom metrics | Gold, ML Models |
| **3.5 Dashboards** | 6 AI/BI dashboards | Metric Views |
| **3.6 Genie Spaces** | 4 Genie spaces with agent instructions | Metric Views, TVFs |

### Implementation Order

```
Phase 3.1 (ML Models) ──────────┐
                                │
Phase 3.2 (TVFs) ───────────────┤
                                │
Phase 3.3 (Metric Views) ───────┼──▶ Phase 3.4 (Monitoring)
                                │
                                ├──▶ Phase 3.5 (Dashboards)
                                │
                                └──▶ Phase 3.6 (Genie Spaces)
```

---

## References

### Cursor Rules
- [cursor rule: Table-Valued Functions](mdc:.cursor/rules/15-databricks-table-valued-functions.mdc)
- [cursor rule: Metric Views Patterns](mdc:.cursor/rules/14-metric-views-patterns.mdc)
- [cursor rule: Lakehouse Monitoring](mdc:.cursor/rules/17-lakehouse-monitoring-comprehensive.mdc)
- [cursor rule: AI/BI Dashboards](mdc:.cursor/rules/18-databricks-aibi-dashboards.mdc)
- [cursor rule: Genie Space Patterns](mdc:.cursor/rules/16-genie-space-patterns.mdc)

### Microsoft Learn System Tables Documentation
These resources provided SQL query patterns for system tables:
- [Jobs Cost Observability](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost) - Cost per job, spend trends, failure costs
- [Job Run Timeline Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs) - Duration analysis, retries, success rates
- [Compute Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute) - CPU/memory utilization, network metrics
- [Audit Logs Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs) - Table access, user activity
- [Data Engineering Observability](https://learn.microsoft.com/en-us/azure/databricks/data-engineering/observability-best-practices) - Best practices

### Inspiration GitHub Repositories
These repositories provided dashboard templates and SQL patterns:
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme/tree/main/Observability%20Dashboards%20and%20DBA%20Resources/Observability%20Lakeview%20Dashboard%20Templates/DBSQL%20Warehouse%20Advisor%20With%20Data%20Model) - Query efficiency, performance flags, cost allocation
- [Table Health Advisor](https://github.com/CodyAustinDavis/dbsql_sme/tree/main/Observability%20Dashboards%20and%20DBA%20Resources/Observability%20Lakeview%20Dashboard%20Templates/Table%20Health%20Advisor) - Delta optimization status, file distribution
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor) - Job optimization, retry analysis
- [System Tables Audit Logs](https://github.com/andyweaves/system-tables-audit-logs) - Security audit patterns, access monitoring

### Dashboard JSON References (from context/dashboards/)
These dashboard JSON files provided real-world SQL patterns:
- DBSQL Warehouse Advisor Observability Dashboard v5 - Multi-warehouse analytics, query efficiency
- Jobs System Tables Dashboard - Job run analysis, task performance, costs
- Workflow Advisor Dashboard - Workflow optimization patterns
- Governance Hub System Dashboard - Unity Catalog governance patterns

