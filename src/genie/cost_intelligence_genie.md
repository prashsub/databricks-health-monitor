# Cost Intelligence Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Cost Intelligence Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks cost analytics and FinOps. Enables finance teams, platform administrators, and executives to query billing, usage, and cost optimization insights without SQL.

**Powered by:**
- 2 Metric Views (cost_analytics, commit_tracking)
- 15 Table-Valued Functions (parameterized cost queries)
- 6 ML Prediction Tables (anomaly detection, forecasting, optimization, chargeback, commitments, tag recommendations)
- 2 Lakehouse Monitoring Tables (cost drift and custom metrics)
- 5 Dimension Tables (workspace, SKU, cluster, node_type, job)
- 5 Fact Tables (usage, pricing, node timeline, job runs)

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Spending Overview
1. "What is our total spend this month?"
2. "Show me the top 10 workspaces by cost"
3. "What was our daily cost trend for the last 30 days?"
4. "What percentage of our spend is tagged?"

### Cost Breakdown
5. "Which SKU costs the most?"
6. "Show me cost by owner"
7. "What is our serverless vs non-serverless spend?"
8. "Break down cost by team tag"

### Cost Optimization
9. "Which ALL_PURPOSE clusters could be migrated to JOBS clusters?"
10. "What are our cost anomalies?"
11. "Show me week-over-week cost growth"
12. "What is the cost forecast for next month?"

### ML-Powered Insights 🤖
13. "Are there any cost anomalies today?"
14. "Which resources need tags?"
15. "What's the predicted cost for next week?"

---

## ████ SECTION D: DATA ASSETS ████

### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `mv_cost_analytics` | Comprehensive cost analytics | total_cost, total_dbus, cost_7d, cost_30d, serverless_percentage, tag_coverage_percentage |
| `mv_commit_tracking` | Contract/commit monitoring | commit_amount, consumed_amount, remaining_amount, burn_rate_daily |

### Table-Valued Functions (15 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_top_cost_contributors` | Top N cost contributors | "top workspaces by cost" |
| `get_cost_trend_by_sku` | Daily cost by SKU | "cost trend by SKU" |
| `get_cost_by_owner` | Cost allocation by owner | "cost by owner", "chargeback" |
| `get_cost_by_tag` | Tag-based cost allocation | "cost by team", "cost by project" |
| `get_untagged_resources` | Resources without tags | "untagged resources" |
| `get_cost_anomalies` | Cost anomaly detection | "cost anomalies", "unusual spending" |
| `get_cost_week_over_week` | Weekly cost trends with growth analysis | "week over week", "WoW growth" |
| `get_spend_by_custom_tags` | Multi-tag cost analysis | "cost by tags" |
| `get_tag_coverage` | Tag coverage metrics | "tag gaps", "tag coverage" |
| `get_most_expensive_jobs` | Top expensive jobs | "job costs", "job spend" |
| `get_cost_growth_analysis` | Cost growth analysis by entity | "growth drivers", "cost growth" |
| `get_cost_growth_by_period` | Period-over-period cost growth | "period comparison" |
| `get_cost_forecast_summary` | Cost forecasting based on historical trends | "forecast", "predict" |
| `get_all_purpose_cluster_cost` | All-purpose cluster cost analysis | "cluster costs by type" |
| `get_commit_vs_actual` | Commit tracking vs actual spend | "commit tracking", "commit status" |

### ML Prediction Tables 🤖 (6 Models)

| Table Name | Purpose | Model | Key Columns |
|---|---|---|---|
| `cost_anomaly_predictions` | Detected cost anomalies with severity scores | Cost Anomaly Detector | `prediction`, `workspace_id`, `usage_date` |
| `budget_forecast_predictions` | 30-day cost forecasts with confidence intervals | Budget Forecaster | `prediction`, `workspace_id`, `usage_date` |
| `job_cost_optimizer_predictions` | Job right-sizing and cost optimization | Job Cost Optimizer | `prediction`, `workspace_id`, `usage_date` |
| `chargeback_predictions` | Cost allocation by team/project | Chargeback Attribution | `prediction`, `workspace_id`, `usage_date` |
| `commitment_recommendations` | Commit level recommendations for discount optimization | Commitment Recommender | `prediction`, `workspace_id`, `usage_date` |
| `tag_recommendations` | Suggested tags for untagged resources | Tag Recommender | `prediction`, `workspace_id`, `usage_date` |

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_usage_profile_metrics` | Custom cost metrics (total_daily_cost, serverless_ratio, tag_coverage_pct) |
| `fact_usage_drift_metrics` | Cost drift detection (cost_drift_pct, dbu_drift_pct, tag_coverage_drift) |

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**Always include these filters when querying Lakehouse Monitoring tables:**

```sql
-- ✅ CORRECT: Get cost metrics over time
SELECT
  window.start AS window_start,
  total_daily_cost,
  tag_coverage_pct,
  serverless_ratio
FROM ${catalog}.${gold_schema}.fact_usage_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
  AND slice_key IS NULL          -- For overall metrics
ORDER BY window.start DESC;

-- ✅ CORRECT: Get cost by workspace (sliced)
SELECT
  slice_value AS workspace_id,
  SUM(total_daily_cost) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'workspace_id'
GROUP BY slice_value
ORDER BY total_cost DESC;

-- ✅ CORRECT: Get cost drift
SELECT
  window.start AS window_start,
  cost_drift_pct
FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC;
```

#### Available Slicing Dimensions (Cost Monitor)

| Slice Key | Use Case |
|-----------|----------|
| `workspace_id` | Cost by workspace |
| `sku_name` | Cost by SKU |
| `cloud` | Cost by cloud provider |
| `is_tagged` | Tagged vs untagged |
| `product_features_is_serverless` | Serverless vs classic |

### Dimension Tables (5 Tables)

**Sources:** `gold_layer_design/yaml/billing/`, `compute/`, `lakeflow/`, `shared/`

| Table Name | Purpose | Key Columns | YAML Source |
|---|---|---|---|
| `dim_workspace` | Workspace details for cost allocation | `workspace_id`, `workspace_name`, `region`, `cloud_provider` | shared/dim_workspace.yaml |
| `dim_sku` | SKU reference for cost categorization | `sku_name`, `sku_category`, `list_price`, `is_serverless` | billing/dim_sku.yaml |
| `dim_cluster` | Cluster metadata for compute cost analysis | `cluster_id`, `cluster_name`, `node_type_id`, `cluster_source` | compute/dim_cluster.yaml |
| `dim_node_type` | Node specifications for right-sizing | `node_type_id`, `num_cores`, `memory_gb`, `hourly_cost` | compute/dim_node_type.yaml |
| `dim_job` | Job metadata for job cost attribution | `job_id`, `name`, `creator_id`, `schedule_type` | lakeflow/dim_job.yaml |

> **Note:** `dim_user` and `dim_date` are not deployed. For user info, use `usage_owner` from `fact_usage`. For date analysis, use date functions on `usage_date`.

### Fact Tables (5 Tables)

**Sources:** `gold_layer_design/yaml/billing/`, `compute/`, `lakeflow/`

| Table Name | Purpose | Grain | YAML Source |
|---|---|---|---|
| `fact_usage` | Primary billing usage table | Daily usage by workspace/SKU/user | billing/fact_usage.yaml |
| `fact_account_prices` | Account-specific pricing | Per SKU per account | billing/fact_account_prices.yaml |
| `fact_list_prices` | List prices over time | Per SKU per effective date | billing/fact_list_prices.yaml |
| `fact_node_timeline` | Cluster node usage timeline | Per node per time interval | compute/fact_node_timeline.yaml |
| `fact_job_run_timeline` | Job execution with cost | Per job run | lakeflow/fact_job_run_timeline.yaml |

### Data Model Relationships 🔗

**Foreign Key Constraints** (extracted from `gold_layer_design/yaml/`)

| Fact Table | → | Dimension Table | Join Keys | Join Type |
|------------|---|-----------------|-----------|-----------|
| `fact_usage` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_usage` | → | `dim_sku` | `sku_name` = `sku_name` | LEFT |
| `fact_usage` | → | `dim_cluster` | `(workspace_id, usage_metadata_cluster_id)` = `(workspace_id, cluster_id)` | LEFT |
| `fact_usage` | → | `dim_job` | `(workspace_id, usage_metadata_job_id)` = `(workspace_id, job_id)` | LEFT |
| `fact_account_prices` | → | `dim_sku` | `sku_name` = `sku_name` | LEFT |
| `fact_list_prices` | → | `dim_sku` | `sku_name` = `sku_name` | LEFT |
| `fact_node_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_node_timeline` | → | `dim_cluster` | `(workspace_id, cluster_id)` = `(workspace_id, cluster_id)` | LEFT |
| `fact_node_timeline` | → | `dim_node_type` | `node_type_id` = `node_type_id` | LEFT |
| `fact_job_run_timeline` | → | `dim_workspace` | `workspace_id` = `workspace_id` | LEFT |
| `fact_job_run_timeline` | → | `dim_job` | `(workspace_id, job_id)` = `(workspace_id, job_id)` | LEFT |

**Join Patterns:**
- **Single Key:** `ON fact.key = dim.key`
- **Composite Key (workspace-scoped):** `ON fact.workspace_id = dim.workspace_id AND fact.fk = dim.pk`

---

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSET SELECTION DECISION TREE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER QUERY PATTERN              → USE THIS ASSET               │
│  ─────────────────────────────────────────────────────────────  │
│  "What's the current X?"         → Metric View (cost_analytics) │
│  "Show me total X by Y"          → Metric View (cost_analytics) │
│  "Dashboard of cost metrics"     → Metric View (cost_analytics) │
│  ─────────────────────────────────────────────────────────────  │
│  "Is cost increasing over time?" → Custom Metrics (_drift_metrics) │
│  "Cost trend since last week"    → Custom Metrics (_profile_metrics) │
│  "Alert when cost exceeds X"     → Custom Metrics (for alerting) │
│  ─────────────────────────────────────────────────────────────  │
│  "Top N workspaces by cost"      → TVF (get_top_cost_contributors) │
│  "Untagged resources list"       → TVF (get_untagged_resources) │
│  "Cost from DATE to DATE"        → TVF (date range parameters)  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Current state aggregates** | Metric View | "Total cost this month" → `cost_analytics` |
| **Trend over time** | Custom Metrics | "Is cost increasing?" → `_drift_metrics` |
| **List of specific items** | TVF | "Top 10 by cost" → `get_top_cost_contributors` |
| **Parameterized investigation** | TVF | "Cost anomalies >50%" → `get_cost_anomalies` |
| **Predictions/Forecasts** | ML Tables | "Cost forecast" → `budget_forecast_predictions` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for PREDICTION** → ML Tables

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks FinOps analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists/investigation, Custom Metrics for trends
2. **Primary Source:** Use mv_cost_analytics metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for "top N", "which", "list" queries with TABLE() wrapper
4. **Trends:** For "is X increasing?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 30 days
6. **Aggregation:** Use SUM for totals, AVG for averages
7. **Sorting:** Sort by cost DESC unless specified
8. **Limits:** Top 10-20 for ranking queries
9. **Currency:** Format as USD with 2 decimals ($1,234.56)
10. **Percentages:** Show as % with 1 decimal (45.3%)
11. **Synonyms:** cost=spend=billing, workspace=environment
12. **ML Anomalies:** For "anomalies" → query ${catalog}.${feature_schema}.cost_anomaly_predictions
13. **ML Forecast:** For "forecast/predict" → query ${catalog}.${feature_schema}.budget_forecast_predictions
14. **Tag Questions:** For "untagged" → use get_untagged_resources TVF
15. **Commit:** For budget tracking → use mv_commit_tracking metric view
16. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
17. **ML Tables Schema:** Always use ${catalog}.${feature_schema} (NOT hardcoded!)
18. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_top_cost_contributors` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 10)` | Top cost contributors | "top N by cost" |
| `get_cost_trend_by_sku` | `(start_date STRING, end_date STRING, sku_filter STRING DEFAULT '%')` | Daily cost trend | "cost trend" |
| `get_cost_by_owner` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 20)` | Cost by owner | "cost by owner", "chargeback" |
| `get_cost_by_tag` | `(start_date STRING, end_date STRING, tag_key STRING DEFAULT 'team')` | Tag-based allocation | "cost by team" |
| `get_untagged_resources` | `(start_date STRING, end_date STRING)` | Untagged resources | "untagged resources" |
| `get_cost_anomalies` | `(start_date STRING, end_date STRING, z_score_threshold DOUBLE DEFAULT 2.0)` | Anomaly detection | "unusual spending" |
| `get_cost_week_over_week` | `(weeks_back INT DEFAULT 4)` | Weekly trends | "WoW growth" |
| `get_spend_by_custom_tags` | `(start_date STRING, end_date STRING, tag_keys STRING)` | Multi-tag analysis | "cost by tags" |
| `get_tag_coverage` | `(start_date STRING, end_date STRING)` | Tag coverage | "tag gaps" |
| `get_most_expensive_jobs` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 20)` | Job costs | "job spend" |
| `get_cost_growth_analysis` | `(entity_type STRING, days_back INT DEFAULT 30, top_n INT DEFAULT 10)` | Growth analysis | "cost growth" |
| `get_cost_growth_by_period` | `(entity_type STRING, top_n INT DEFAULT 10)` | Period comparison | "period growth" |
| `get_cost_forecast_summary` | `(forecast_months INT DEFAULT 3)` | Cost forecasting | "predict costs" |
| `get_all_purpose_cluster_cost` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 20)` | Cluster costs | "cluster costs" |
| `get_commit_vs_actual` | `(commit_year INT, annual_commit_amount DECIMAL, as_of_date DATE)` | Commit tracking | "commit status" |

### TVF Details

#### get_top_cost_contributors
- **Signature:** `get_top_cost_contributors(start_date STRING, end_date STRING, top_n INT DEFAULT 10)`
- **Returns:** workspace_name, sku_name, total_cost, total_dbus, pct_of_total
- **Use When:** User asks for "top N workspaces/SKUs by cost"
- **Example:** `SELECT * FROM get_top_cost_contributors('2024-12-01', '2024-12-31', 10))`

#### get_cost_trend_by_sku
- **Signature:** `get_cost_trend_by_sku(start_date STRING, end_date STRING, sku_filter STRING DEFAULT '%')`
- **Returns:** usage_date, sku_name, daily_cost, cumulative_cost
- **Use When:** User asks for "cost trend by SKU" or "daily cost breakdown"
- **Example:** `SELECT * FROM get_cost_trend_by_sku('2024-12-01', '2024-12-31', '%'))`

#### get_cost_by_owner
- **Signature:** `get_cost_by_owner(start_date STRING, end_date STRING, top_n INT DEFAULT 20)`
- **Returns:** owner, workspace_name, total_cost, pct_of_total
- **Use When:** User asks for "cost by owner" or "chargeback report"
- **Example:** `SELECT * FROM get_cost_by_owner('2024-12-01', '2024-12-31', 20))`

#### get_cost_by_tag
- **Signature:** `get_cost_by_tag(start_date STRING, end_date STRING, tag_key STRING DEFAULT 'team')`
- **Returns:** tag_value, total_cost, pct_of_total
- **Use When:** User asks for "cost by team" or "cost by project"
- **Example:** `SELECT * FROM get_cost_by_tag('2024-12-01', '2024-12-31', 'team'))`

#### get_untagged_resources
- **Signature:** `get_untagged_resources(start_date STRING, end_date STRING)`
- **Returns:** workspace_name, resource_id, total_cost, days_untagged
- **Use When:** User asks for "untagged resources" or "tag compliance"
- **Example:** `SELECT * FROM get_untagged_resources('2024-12-01', '2024-12-31'))`

#### get_cost_anomalies
- **Signature:** `get_cost_anomalies(start_date STRING, end_date STRING, z_score_threshold DOUBLE DEFAULT 2.0)`
- **Returns:** usage_date, workspace_name, actual_cost, expected_cost, deviation_pct, z_score
- **Use When:** User asks for "cost anomalies" or "unusual spending patterns"
- **Example:** `SELECT * FROM get_cost_anomalies('2024-12-01', '2024-12-31', 2.0))`

#### get_cost_week_over_week
- **Signature:** `get_cost_week_over_week(weeks_back INT DEFAULT 4)`
- **Returns:** week_start, week_end, total_cost, wow_growth_pct
- **Use When:** User asks for "week over week" or "WoW growth"
- **Example:** `SELECT * FROM get_cost_week_over_week(4))`

#### get_cost_mtd_summary
- **Signature:** `get_cost_mtd_summary()`
- **Returns:** mtd_cost, mtd_dbu, mom_growth_pct, projected_month_end_cost
- **Use When:** User asks for "month to date" or "MTD cost"
- **Example:** `SELECT * FROM get_cost_mtd_summary())`

#### get_spend_by_custom_tags
- **Signature:** `get_spend_by_custom_tags(start_date STRING, end_date STRING, tag_keys STRING)`
- **Returns:** tag_key, tag_value, total_cost, pct_of_total
- **Use When:** User asks for "cost by tags" or "multi-tag analysis"
- **Example:** `SELECT * FROM get_spend_by_custom_tags('2024-12-01', '2024-12-31', 'team,project'))`

#### get_most_expensive_jobs
- **Signature:** `get_most_expensive_jobs(start_date STRING, end_date STRING, top_n INT DEFAULT 20)`
- **Returns:** job_name, workspace_name, total_cost, run_count
- **Use When:** User asks for "job costs" or "most expensive jobs"
- **Example:** `SELECT * FROM get_most_expensive_jobs('2024-12-01', '2024-12-31', 20))`

#### get_tag_coverage
- **Signature:** `get_tag_coverage(start_date STRING, end_date STRING)`
- **Returns:** tag_key, tagged_cost, untagged_cost, coverage_pct
- **Use When:** User asks for "tag coverage" or "tag gaps"
- **Example:** `SELECT * FROM get_tag_coverage('2024-12-01', '2024-12-31'))`

#### get_cost_forecast_summary
- **Signature:** `get_cost_forecast_summary(forecast_months INT DEFAULT 3)`
- **Returns:** forecast_month, predicted_cost, confidence_lower, confidence_upper
- **Use When:** User asks for "cost forecast" or "predict future cost"
- **Example:** `SELECT * FROM get_cost_forecast_summary(3))`

#### get_all_purpose_cluster_cost
- **Signature:** `get_all_purpose_cluster_cost(start_date STRING, end_date STRING, top_n INT DEFAULT 20)`
- **Returns:** cluster_name, workspace_name, total_cost, migration_savings_potential
- **Use When:** User asks for "ALL_PURPOSE cluster costs" or "migration opportunities"
- **Example:** `SELECT * FROM get_all_purpose_cluster_cost('2024-12-01', '2024-12-31', 20))`

#### get_cost_growth_analysis
- **Signature:** `get_cost_growth_analysis(entity_type STRING, days_back INT DEFAULT 30, top_n INT DEFAULT 10)`
- **Returns:** entity_name, current_cost, previous_cost, growth_pct, growth_category
- **Use When:** User asks for "cost growth drivers" or "what's growing"
- **Example:** `SELECT * FROM get_cost_growth_analysis('workspace', 30, 10))`

#### get_commit_vs_actual
- **Signature:** `get_commit_vs_actual(commit_year INT, annual_commit_amount DECIMAL, as_of_date DATE)`
- **Returns:** commit_amount, consumed_amount, remaining_amount, burn_rate_daily, projected_year_end
- **Use When:** User asks for "commit tracking" or "commitment status"
- **Example:** `SELECT * FROM get_commit_vs_actual(2024, 1000000, CURRENT_DATE()))`

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**
> **Grounded in:** Metric Views, TVFs, ML Tables, Lakehouse Monitors, Fact/Dim Tables

### ✅ Normal Benchmark Questions (Q1-Q20)

### Question 1: "What is our total spend this month?"
**Expected SQL:**
```sql
SELECT MEASURE(total_cost) as mtd_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());
```
**Expected Result:** Single row with month-to-date cost

---

### Question 2: "Show me cost by workspace for the last 30 days"
**Expected SQL:**
```sql
SELECT
  workspace_name,
  MEASURE(total_cost) as total_cost,
  MEASURE(total_dbu) as total_dbus
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY workspace_name
ORDER BY total_cost DESC
LIMIT 10;
```
**Expected Result:** Top 10 workspaces by cost with DBU consumption

---

### Question 3: "What is our tag coverage percentage?"
**Expected SQL:**
```sql
SELECT MEASURE(tag_coverage_pct) as tag_coverage
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```
**Expected Result:** Tag coverage percentage for last 30 days

---

### Question 4: "What is our serverless adoption rate?"
**Expected SQL:**
```sql
SELECT MEASURE(serverless_ratio) as serverless_pct
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```
**Expected Result:** Percentage of spend on serverless compute

---

### Question 5: "Show me daily cost trend for the last 7 days"
**Expected SQL:**
```sql
SELECT
  usage_date,
  MEASURE(total_cost) as daily_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY usage_date
ORDER BY usage_date DESC;
```
**Expected Result:** Daily cost breakdown for last week

---

### Question 6: "Show me the top 10 cost contributors this month"
**Expected SQL:**
```sql
SELECT * FROM get_top_cost_contributors(
  DATE_TRUNC('month', CURRENT_DATE())::STRING,
  CURRENT_DATE()::STRING,
  10
));
```
**Expected Result:** Top 10 workspaces/SKUs by cost

---

### Question 7: "What are the cost anomalies in the last 30 days?"
**Expected SQL:**
```sql
SELECT * FROM get_cost_anomalies(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  2.0
))
ORDER BY z_score DESC
LIMIT 20;
```
**Expected Result:** Cost anomalies with z-scores and deviation percentages

---

### Question 8: "Show me untagged resources"
**Expected SQL:**
```sql
SELECT * FROM get_untagged_resources(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY total_cost DESC
LIMIT 20;
```
**Expected Result:** Resources without tags sorted by cost impact

---

### Question 9: "What is the cost breakdown by owner?"
**Expected SQL:**
```sql
SELECT * FROM get_cost_by_owner(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  15
));
```
**Expected Result:** Chargeback report by resource owner

---

### Question 10: "Show me serverless vs classic cost comparison"
**Expected SQL:**
```sql
SELECT 
  is_serverless,
  MEASURE(total_cost) as cost,
  MEASURE(total_dbu) as dbus,
  MEASURE(serverless_ratio) as serverless_pct
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY is_serverless
ORDER BY cost DESC;
```
**Expected Result:** Compute type cost breakdown (serverless vs classic) with efficiency metrics

---

### Question 11: "What is the daily cost summary?"
**Expected SQL:**
```sql
SELECT 
  usage_date,
  MEASURE(total_cost) as daily_cost,
  LAG(MEASURE(total_cost), 1) OVER (ORDER BY usage_date) as prev_day_cost,
  LAG(MEASURE(total_cost), 7) OVER (ORDER BY usage_date) as week_ago_cost,
  (MEASURE(total_cost) - LAG(MEASURE(total_cost), 1) OVER (ORDER BY usage_date)) / NULLIF(LAG(MEASURE(total_cost), 1) OVER (ORDER BY usage_date), 0) * 100 as dod_change_pct,
  (MEASURE(total_cost) - LAG(MEASURE(total_cost), 7) OVER (ORDER BY usage_date)) / NULLIF(LAG(MEASURE(total_cost), 7) OVER (ORDER BY usage_date), 0) * 100 as wow_change_pct
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
GROUP BY usage_date
ORDER BY usage_date DESC;
```
**Expected Result:** Daily cost with day-over-day and week-over-week growth percentages

---

### Question 12: "Show me cost by SKU for last month"
**Expected SQL:**
```sql
SELECT
  sku_name,
  MEASURE(total_cost) as sku_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE() - INTERVAL 1 MONTH)
  AND usage_date < DATE_TRUNC('month', CURRENT_DATE())
GROUP BY sku_name
ORDER BY sku_cost DESC;
```
**Expected Result:** SKU-level cost breakdown for previous month

---

### Question 13: "What is our week-over-week cost growth?"
**Expected SQL:**
```sql
SELECT MEASURE(week_over_week_growth_pct) as wow_growth
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS;
```
**Expected Result:** WoW growth percentage

---

### Question 14: "Show me cost by team tag"
**Expected SQL:**
```sql
SELECT * FROM get_cost_by_tag(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  'team'
))
ORDER BY total_cost DESC
LIMIT 15;
```
**Expected Result:** Cost allocation by team tag with percentages

---

### Question 15: "What is the job cost breakdown?"
**Expected SQL:**
```sql
SELECT * FROM get_most_expensive_jobs(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  20
));
```
**Expected Result:** Top 20 jobs by compute cost

---

### Question 16: "What is our year-to-date cost?"
**Expected SQL:**
```sql
SELECT MEASURE(ytd_cost) as ytd_total
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= DATE_TRUNC('year', CURRENT_DATE());
```
**Expected Result:** Year-to-date cost aggregation

---

### Question 17: "Show me ALL_PURPOSE cluster costs and migration opportunities"
**Expected SQL:**
```sql
SELECT * FROM get_all_purpose_cluster_cost(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  20
))
ORDER BY total_cost DESC;
```
**Expected Result:** ALL_PURPOSE clusters with potential savings from migration to JOBS clusters

---

### Question 18: "What is the cost per DBU?"
**Expected SQL:**
```sql
SELECT MEASURE(cost_per_dbu) as avg_cost_per_dbu
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS;
```
**Expected Result:** Average cost per DBU (effective rate)

---

### Question 19: "Show me warehouse cost analysis"
**Expected SQL:**
```sql
SELECT 
  warehouse_name,
  MEASURE(total_cost) as warehouse_cost,
  MEASURE(total_queries) as query_count,
  MEASURE(total_cost) / NULLIF(MEASURE(total_queries), 0) as cost_per_query
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND warehouse_name IS NOT NULL
GROUP BY warehouse_name
ORDER BY warehouse_cost DESC
LIMIT 15;
```
**Expected Result:** SQL Warehouse cost breakdown with cost-per-query efficiency metrics

---

### Question 20: "What is our commit tracking status?"
**Expected SQL:**
```sql
SELECT
  MEASURE(mtd_cost) as month_to_date,
  MEASURE(projected_monthly_cost) as projected_month_end,
  MEASURE(daily_avg_cost) as daily_burn_rate
FROM ${catalog}.${gold_schema}.mv_commit_tracking;
```
**Expected Result:** Current commitment utilization and burn rate

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP RESEARCH: ML-powered cost anomaly predictions with workspace context"
**Expected SQL:**
```sql
SELECT
  w.workspace_name,
  ca.usage_date,
  ca.prediction as deviation
FROM ${catalog}.${feature_schema}.cost_anomaly_predictions ca
JOIN ${catalog}.${gold_schema}.dim_workspace w ON ca.workspace_id = w.workspace_id
WHERE ca.usage_date = CURRENT_DATE()
ORDER BY ca.prediction DESC
LIMIT 10;
```
**Expected Result:** Today's cost anomalies detected by ML with workspace names

---

### Question 22: "🔬 DEEP RESEARCH: Cross-domain cost and reliability correlation - which workspaces have both high cost AND high job failure rates, indicating infrastructure issues"
**Expected SQL:**
```sql
WITH cost_ranking AS (
  SELECT
    workspace_name,
    MEASURE(total_cost) as workspace_cost,
    RANK() OVER (ORDER BY MEASURE(total_cost) DESC) as cost_rank
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_name
),
reliability_ranking AS (
  SELECT
    workspace_name,
    MEASURE(failure_rate) as failure_rate,
    MEASURE(total_runs) as total_runs,
    RANK() OVER (ORDER BY MEASURE(failure_rate) DESC) as failure_rank
  FROM ${catalog}.${gold_schema}.mv_job_performance
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_name
)
SELECT
  c.workspace_name,
  c.workspace_cost,
  c.cost_rank,
  r.failure_rate,
  r.total_runs,
  r.failure_rank,
  (c.cost_rank + r.failure_rank) / 2.0 as combined_priority_score
FROM cost_ranking c
JOIN reliability_ranking r ON c.workspace_name = r.workspace_name
WHERE c.cost_rank <= 20 OR r.failure_rank <= 20
ORDER BY combined_priority_score ASC
LIMIT 10;
```
**Expected Result:** Workspaces with both cost and reliability issues requiring immediate attention

---

### Question 23: "🔬 DEEP RESEARCH: SKU-level cost efficiency analysis with utilization patterns - identify overprovisioned compute types with low utilization but high cost"
**Expected SQL:**
```sql
WITH sku_costs AS (
  SELECT
    sku_name,
    MEASURE(total_cost) as total_sku_cost,
    MEASURE(total_dbu) as total_dbu,
    MEASURE(total_cost) / NULLIF(MEASURE(total_dbu), 0) as cost_per_dbu
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND sku_name LIKE '%COMPUTE%'
  GROUP BY sku_name
),
cluster_util AS (
  SELECT
    MEASURE(avg_cpu_utilization) as avg_cpu,
    MEASURE(avg_memory_utilization) as avg_memory
  FROM ${catalog}.${gold_schema}.mv_cluster_utilization
  WHERE utilization_date >= CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT
  sc.sku_name,
  sc.total_sku_cost,
  sc.total_dbu,
  sc.cost_per_dbu,
  cu.avg_cpu,
  cu.avg_memory,
  CASE
    WHEN cu.avg_cpu < 30 AND sc.total_sku_cost > 5000 THEN 'Severely Underutilized'
    WHEN cu.avg_cpu < 50 AND sc.total_sku_cost > 2000 THEN 'Underutilized'
    WHEN cu.avg_cpu > 80 THEN 'Well Utilized'
    ELSE 'Normal'
  END as utilization_status,
  CASE
    WHEN cu.avg_cpu < 30 THEN sc.total_sku_cost * 0.6
    WHEN cu.avg_cpu < 50 THEN sc.total_sku_cost * 0.3
    ELSE 0
  END as potential_savings
FROM sku_costs sc
CROSS JOIN cluster_util cu
WHERE sc.total_sku_cost > 1000
ORDER BY potential_savings DESC
LIMIT 10;
```
**Expected Result:** SKU efficiency analysis with quantified savings opportunities

---

### Question 24: "🔬 DEEP RESEARCH: Tag compliance and cost attribution gap analysis - which business units have the largest unattributable spend"
**Expected SQL:**
```sql
WITH tagged_costs AS (
  SELECT
    team_tag,
    MEASURE(total_cost) as tagged_cost
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND team_tag IS NOT NULL
  GROUP BY team_tag
),
total_costs AS (
  SELECT MEASURE(total_cost) as platform_total
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
untagged AS (
  SELECT SUM(total_cost) as total_untagged
  FROM get_untagged_resources(
    (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
    CURRENT_DATE()::STRING
  ))
)
SELECT
  tc.team_tag,
  tc.tagged_cost,
  tc.tagged_cost / NULLIF(t.platform_total, 0) * 100 as pct_of_total,
  u.total_untagged,
  u.total_untagged / NULLIF(t.platform_total, 0) * 100 as untagged_pct,
  t.platform_total as total_platform_cost
FROM tagged_costs tc
CROSS JOIN total_costs t
CROSS JOIN untagged u
ORDER BY tc.tagged_cost DESC
LIMIT 10;
```
**Expected Result:** Tag compliance analysis showing attribution gaps and untagged spend

---

### Question 25: "🔬 DEEP RESEARCH: Predictive cost optimization roadmap - combine ML forecasts, anomaly detection, and commitment recommendations to create a prioritized action plan"
**Expected SQL:**
```sql
WITH cost_forecast AS (
  SELECT
    workspace_name,
    predicted_cost as projected_monthly_cost
  FROM get_cost_forecast_summary(1))
  LIMIT 1
) AS forecast_data
CROSS JOIN (
  SELECT 
    workspace_name,
    MEASURE(total_cost) / 30.0 as projected_daily_cost
  FROM ${catalog}.${gold_schema}.mv_cost_analytics
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY workspace_name
),
anomalies AS (
  SELECT
    w.workspace_name,
    COUNT(*) as anomaly_count
  FROM ${catalog}.${feature_schema}.cost_anomaly_predictions ca
  JOIN ${catalog}.${gold_schema}.dim_workspace w ON ca.workspace_id = w.workspace_id
  WHERE ca.usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND ca.prediction > 0.5
  GROUP BY w.workspace_name
),
commitments AS (
  SELECT
    w.workspace_name,
    AVG(cr.prediction) as recommended_commit
  FROM ${catalog}.${feature_schema}.commitment_recommendations cr
  JOIN ${catalog}.${gold_schema}.dim_workspace w ON cr.workspace_id = w.workspace_id
  WHERE cr.usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY w.workspace_name
)
SELECT
  cf.workspace_name,
  cf.projected_daily_cost,
  cf.projected_daily_cost * 30 as projected_monthly_cost,
  COALESCE(a.anomaly_count, 0) as recent_anomalies,
  COALESCE(c.recommended_commit, 0) as commit_recommendation,
  CASE
    WHEN a.anomaly_count > 5 THEN 'Investigate Anomalies First'
    WHEN cf.projected_daily_cost > 1000 AND c.recommended_commit > 0 THEN 'Evaluate Commitment'
    WHEN cf.projected_daily_cost > 500 THEN 'Monitor Closely'
    ELSE 'Normal'
  END as action_priority
FROM cost_forecast cf
LEFT JOIN anomalies a ON cf.workspace_name = a.workspace_name
LEFT JOIN commitments c ON cf.workspace_name = c.workspace_name
WHERE cf.projected_daily_cost > 100
ORDER BY cf.projected_daily_cost DESC
LIMIT 15;
```
**Expected Result:** Comprehensive optimization roadmap with ML-driven recommendations and priorities

---


## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 15 functions with signatures | ✅ |
| **G. Benchmark Questions** | 25 with SQL answers (incl. 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 💰 **Cost**

---

## References

### 📊 Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - **START HERE**: Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### 📈 Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Cost Monitor
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 35 cost-specific custom metrics

### 📁 Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 15 Cost TVFs
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 2 Cost Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 6 Cost ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting
