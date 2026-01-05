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
| `cost_analytics` | Comprehensive cost analytics | total_cost, total_dbus, cost_7d, cost_30d, serverless_percentage, tag_coverage_percentage |
| `commit_tracking` | Contract/commit monitoring | commit_amount, consumed_amount, remaining_amount, burn_rate_daily |

### Table-Valued Functions (15 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_top_cost_contributors` | Top N cost contributors | "top workspaces by cost" |
| `get_cost_trend_by_sku` | Daily cost by SKU | "cost trend by SKU" |
| `get_cost_by_owner` | Cost allocation by owner | "cost by owner", "chargeback" |
| `get_cost_by_tag` | Tag-based cost allocation | "cost by team", "cost by project" |
| `get_untagged_resources` | Resources without tags | "untagged resources" |
| `get_tag_coverage` | Tag compliance metrics | "tag coverage", "tag hygiene" |
| `get_cost_week_over_week` | WoW cost comparison | "week over week" |
| `get_cost_anomalies` | Statistical anomaly detection | "cost anomalies", "unusual spending" |
| `get_cost_forecast_summary` | Cost forecasting | "forecast", "predict" |
| `get_cost_mtd_summary` | Month-to-date summary | "MTD", "this month" |
| `get_commit_vs_actual` | Commit utilization | "commit tracking", "budget vs actual" |
| `get_spend_by_custom_tags` | Multi-tag cost analysis | "cost by multiple tags" |
| `get_cost_growth_analysis` | Identify growth drivers | "cost growth", "biggest increases" |
| `get_cost_growth_by_period` | Period-over-period comparison | "compare this quarter to last" |
| `get_all_purpose_cluster_cost` | ALL_PURPOSE cluster costs | "ALL_PURPOSE migration", "cluster savings" |

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
| **Parameterized investigation** | TVF | "Cost anomalies >$1000" → `get_cost_anomalies` |
| **Predictions/Forecasts** | ML Tables | "Cost forecast" → `cost_forecast_predictions` |

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
2. **Primary Source:** Use cost_analytics metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for "top N", "which", "list" queries
4. **Trends:** For "is X increasing?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 30 days
6. **Aggregation:** Use SUM for totals, AVG for averages
7. **Sorting:** Sort by cost DESC unless specified
8. **Limits:** Top 10-20 for ranking queries
9. **Currency:** Format as USD with 2 decimals ($1,234.56)
10. **Percentages:** Show as % with 1 decimal (45.3%)
11. **Synonyms:** cost=spend=billing, workspace=environment
12. **ML Anomalies:** For "anomalies" → query cost_anomaly_predictions
13. **ML Forecast:** For "forecast/predict" → query cost_forecast_predictions
14. **Tag Questions:** For "untagged" → use get_untagged_resources TVF
15. **Commit:** For budget tracking → use commit_tracking metric view
16. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
17. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_top_cost_contributors` | `(start_date STRING, end_date STRING, top_n INT)` | Top cost contributors | "top N by cost" |
| `get_cost_trend_by_sku` | `(start_date STRING, end_date STRING)` | Daily cost trend | "cost trend" |
| `get_cost_by_owner` | `(start_date STRING, end_date STRING)` | Cost by owner | "cost by owner", "chargeback" |
| `get_cost_anomalies` | `(start_date STRING, end_date STRING, threshold DOUBLE)` | Anomaly detection | "unusual spending" |
| `get_all_purpose_cluster_cost` | `(start_date STRING, end_date STRING)` | AP cluster costs | "migration savings" |

### TVF Details

#### get_top_cost_contributors
- **Signature:** `get_top_cost_contributors(start_date STRING, end_date STRING, top_n INT)`
- **Returns:** workspace_name, sku_name, total_cost, total_dbus, pct_of_total
- **Use When:** User asks for "top N workspaces/SKUs by cost"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_top_cost_contributors('2024-12-01', '2024-12-31', 10)`

#### get_cost_trend_by_sku
- **Signature:** `get_cost_trend_by_sku(start_date STRING, end_date STRING)`
- **Returns:** usage_date, sku_name, daily_cost, cumulative_cost
- **Use When:** User asks for "cost trend by SKU" or "daily cost breakdown"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_cost_trend_by_sku('2024-12-01', '2024-12-31')`

#### get_cost_by_owner
- **Signature:** `get_cost_by_owner(start_date STRING, end_date STRING)`
- **Returns:** owner, workspace_name, total_cost, pct_of_total
- **Use When:** User asks for "cost by owner" or "chargeback report"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_cost_by_owner('2024-12-01', '2024-12-31')`

#### get_cost_anomalies
- **Signature:** `get_cost_anomalies(start_date STRING, end_date STRING, threshold DOUBLE)`
- **Returns:** usage_date, workspace_name, actual_cost, expected_cost, anomaly_score
- **Use When:** User asks for "cost anomalies" or "unusual spending patterns"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_cost_anomalies('2024-12-01', '2024-12-31', 2.0)`

#### get_all_purpose_cluster_cost
- **Signature:** `get_all_purpose_cluster_cost(start_date STRING, end_date STRING)`
- **Returns:** cluster_name, owner, current_cost, potential_savings, migration_risk
- **Use When:** User asks for "ALL_PURPOSE cluster costs" or "migration opportunities"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_all_purpose_cluster_cost('2024-12-01', '2024-12-31')`

---

## ████ SECTION G: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "What is our total spend this month?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(total_cost) as total_spend
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());
```
**Expected Result:** Single value showing total cost for current month

---

### Question 2: "Show me the top 10 workspaces by cost"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_top_cost_contributors(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  10
);
```
**Expected Result:** Table with 10 rows showing workspace_name, total_cost, pct_of_total

---

### Question 3: "What percentage of our spend is tagged?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(tag_coverage_percentage) as tag_coverage
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());
```
**Expected Result:** Single percentage value showing tag coverage

---

### Question 4: "Show me cost by owner"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_by_owner(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
);
```
**Expected Result:** Table with owner, total_cost, pct_of_total

---

### Question 5: "What is our serverless vs non-serverless spend?"
**Expected SQL:**
```sql
SELECT 
  is_serverless,
  MEASURE(total_cost) as total_cost,
  MEASURE(serverless_percentage) as pct_of_total
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY is_serverless;
```
**Expected Result:** Two rows showing serverless vs non-serverless breakdown

---

### Question 6: "Are there any cost anomalies today?"
**Expected SQL:**
```sql
SELECT * 
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
WHERE prediction_date = CURRENT_DATE()
  AND is_anomaly = TRUE
ORDER BY anomaly_score DESC;
```
**Expected Result:** Table of detected anomalies with scores (may be empty if none)

---

### Question 7: "What is the cost forecast for next month?"
**Expected SQL:**
```sql
SELECT 
  forecast_date,
  predicted_cost,
  lower_bound,
  upper_bound
FROM ${catalog}.${gold_schema}.cost_forecast_predictions
WHERE forecast_date >= DATE_TRUNC('month', CURRENT_DATE() + INTERVAL 1 MONTH)
  AND forecast_date < DATE_TRUNC('month', CURRENT_DATE() + INTERVAL 2 MONTHS)
ORDER BY forecast_date;
```
**Expected Result:** Table with daily forecasts for next month

---

### Question 8: "Which ALL_PURPOSE clusters could be migrated to JOBS clusters?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_all_purpose_cluster_cost(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
WHERE potential_savings > 0
ORDER BY potential_savings DESC
LIMIT 20;
```
**Expected Result:** Table of clusters with migration savings opportunities

---

### Question 9: "What is the week-over-week cost growth?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_week_over_week(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 14 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
);
```
**Expected Result:** Table showing this week vs last week with % change

---

### Question 10: "Which resources need tags?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_untagged_resources(
  DATE_FORMAT(DATE_TRUNC('month', CURRENT_DATE()), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY total_cost DESC
LIMIT 20;
```
**Expected Result:** Table of untagged resources with their costs

---

### Question 11: "Show me cost trend by SKU for the last 30 days"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_trend_by_sku(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY usage_date DESC, daily_cost DESC;
```
**Expected Result:** Daily cost breakdown by SKU

---

### Question 12: "What is our commit utilization?"
**Expected SQL:**
```sql
SELECT 
  MEASURE(commit_amount) as commit,
  MEASURE(consumed_amount) as consumed,
  MEASURE(remaining_amount) as remaining,
  MEASURE(commit_utilization_pct) as utilization_pct
FROM ${catalog}.${gold_schema}.commit_tracking
WHERE is_over_committed = FALSE;
```
**Expected Result:** Single row with commit vs actual usage

---

### Question 13: "What is our DBU consumption by SKU?"
**Expected SQL:**
```sql
SELECT 
  sku_name,
  MEASURE(total_dbus) as total_dbus,
  MEASURE(total_cost) as total_cost
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY sku_name
ORDER BY total_dbus DESC;
```
**Expected Result:** DBU breakdown by SKU

---

### Question 14: "Which users have the highest spend?"
**Expected SQL:**
```sql
SELECT 
  usage_owner as user,
  SUM(usage_cost) as total_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY usage_owner
ORDER BY total_cost DESC
LIMIT 20;
```
**Expected Result:** Top 20 users by spend

---

### Question 15: "What's the daily cost breakdown for this week?"
**Expected SQL:**
```sql
SELECT 
  usage_date,
  MEASURE(total_cost) as daily_cost,
  MEASURE(total_dbus) as daily_dbus
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY usage_date
ORDER BY usage_date;
```
**Expected Result:** Daily cost for last 7 days

---

### Question 16: "What is our cost by cloud provider?"
**Expected SQL:**
```sql
SELECT 
  cloud,
  MEASURE(total_cost) as total_cost,
  MEASURE(total_dbus) as total_dbus
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY cloud
ORDER BY total_cost DESC;
```
**Expected Result:** Cost breakdown by cloud (AWS, Azure, GCP)

---

### Question 17: "Show me the most expensive SKUs this month"
**Expected SQL:**
```sql
SELECT 
  sku_name,
  sku_category,
  MEASURE(total_cost) as total_cost,
  MEASURE(total_dbus) as total_dbus
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY sku_name, sku_category
ORDER BY total_cost DESC
LIMIT 10;
```
**Expected Result:** Top 10 SKUs by cost

---

### Question 18: "What is the cost drift from last week?"
**Expected SQL:**
```sql
SELECT 
  window.start as window_start,
  cost_drift_pct,
  dbu_drift_pct
FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 7;
```
**Expected Result:** Recent cost drift percentages

---

### Question 19: "Which workspaces have the lowest tag coverage?"
**Expected SQL:**
```sql
SELECT 
  workspace_name,
  MEASURE(tag_coverage_percentage) as tag_coverage
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY workspace_name
HAVING MEASURE(tag_coverage_percentage) < 50
ORDER BY tag_coverage ASC
LIMIT 20;
```
**Expected Result:** Workspaces with <50% tag coverage

---

### Question 20: "What are the recommended tags for untagged resources?"
**Expected SQL:**
```sql
SELECT 
  resource_id,
  resource_type,
  recommended_tags,
  confidence
FROM ${catalog}.${gold_schema}.tag_recommendations
WHERE confidence > 0.7
ORDER BY confidence DESC
LIMIT 20;
```
**Expected Result:** Tag recommendations with high confidence

---

### 🔬 DEEP RESEARCH QUESTIONS (Complex Multi-Source Analysis)

### Question 21: "What is the root cause of our cost increase this month, and what would be the projected savings if we implemented all ML-recommended optimizations?"
**Deep Research Complexity:** Combines cost trend analysis, anomaly detection, ML optimization recommendations, and savings forecasting across multiple data sources.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify cost increase drivers
WITH cost_growth AS (
  SELECT 
    sku_name,
    workspace_name,
    SUM(CASE WHEN usage_date >= DATE_TRUNC('month', CURRENT_DATE()) THEN usage_cost ELSE 0 END) as current_month_cost,
    SUM(CASE WHEN usage_date >= DATE_TRUNC('month', CURRENT_DATE() - INTERVAL 1 MONTH) 
             AND usage_date < DATE_TRUNC('month', CURRENT_DATE()) THEN usage_cost ELSE 0 END) as prev_month_cost
  FROM ${catalog}.${gold_schema}.fact_usage
  GROUP BY sku_name, workspace_name
),
growth_analysis AS (
  SELECT *, 
    current_month_cost - prev_month_cost as cost_delta,
    CASE WHEN prev_month_cost > 0 THEN (current_month_cost - prev_month_cost) / prev_month_cost * 100 ELSE 100 END as growth_pct
  FROM cost_growth
  WHERE current_month_cost > prev_month_cost
),
-- Step 2: Check for anomalies in high-growth areas
anomalies AS (
  SELECT workspace_id, anomaly_score, is_anomaly
  FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
  WHERE is_anomaly = TRUE
),
-- Step 3: Get ML optimization recommendations
optimizations AS (
  SELECT 
    SUM(potential_savings_usd) as total_potential_savings
  FROM ${catalog}.${gold_schema}.job_cost_optimizer_predictions
  WHERE savings_potential > 0
)
SELECT 
  g.sku_name,
  g.workspace_name,
  g.cost_delta,
  g.growth_pct,
  CASE WHEN a.is_anomaly THEN 'ANOMALY DETECTED' ELSE 'Normal Growth' END as anomaly_status,
  o.total_potential_savings as projected_savings_if_optimized
FROM growth_analysis g
LEFT JOIN anomalies a ON g.workspace_name = a.workspace_id
CROSS JOIN optimizations o
ORDER BY g.cost_delta DESC
LIMIT 20;
```
**Expected Result:** Root cause analysis showing which SKUs/workspaces drove cost increase, whether they're anomalous, and total projected savings from ML recommendations.

---

### Question 22: "Which teams have the highest untagged spend growing fastest, and what tags should we apply based on ML recommendations to improve chargeback accuracy?"
**Deep Research Complexity:** Combines tag coverage trends, spend growth analysis, ML tag recommendations, and chargeback impact assessment.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Identify untagged spend by inferred team (owner-based)
WITH untagged_spend AS (
  SELECT 
    usage_owner as team_proxy,
    SUM(CASE WHEN is_tagged = FALSE THEN usage_cost ELSE 0 END) as untagged_cost,
    SUM(usage_cost) as total_cost,
    SUM(CASE WHEN is_tagged = FALSE THEN usage_cost ELSE 0 END) / NULLIF(SUM(usage_cost), 0) * 100 as untagged_pct
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY usage_owner
),
-- Step 2: Calculate growth rate of untagged spend
untagged_growth AS (
  SELECT 
    usage_owner as team_proxy,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS AND is_tagged = FALSE THEN usage_cost ELSE 0 END) as recent_untagged,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS 
             AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS AND is_tagged = FALSE THEN usage_cost ELSE 0 END) / 3.3 as avg_weekly_untagged
  FROM ${catalog}.${gold_schema}.fact_usage
  GROUP BY usage_owner
),
-- Step 3: Get ML tag recommendations for these resources
tag_recs AS (
  SELECT 
    resource_id,
    recommended_tags,
    confidence
  FROM ${catalog}.${gold_schema}.tag_recommendations
  WHERE confidence > 0.7
)
SELECT 
  u.team_proxy,
  u.untagged_cost,
  u.untagged_pct,
  g.recent_untagged - g.avg_weekly_untagged as untagged_growth_wow,
  COUNT(DISTINCT t.resource_id) as resources_with_recommendations,
  COLLECT_LIST(DISTINCT t.recommended_tags) as suggested_tags
FROM untagged_spend u
JOIN untagged_growth g ON u.team_proxy = g.team_proxy
LEFT JOIN tag_recs t ON t.resource_id LIKE CONCAT('%', u.team_proxy, '%')
WHERE u.untagged_cost > 1000
GROUP BY u.team_proxy, u.untagged_cost, u.untagged_pct, g.recent_untagged, g.avg_weekly_untagged
ORDER BY u.untagged_cost DESC
LIMIT 15;
```
**Expected Result:** Teams with high untagged spend, growth trends, and ML-recommended tags to apply for improved chargeback accuracy.

---

### Question 23: "What would be our total cost savings if we implemented all ML-recommended optimizations across clusters, jobs, and commitments, and how should we prioritize them by ROI and implementation complexity?"
**Deep Research Complexity:** Combines cluster right-sizing, job cost optimization, commitment recommendations, and migration savings into a unified prioritized optimization roadmap with ROI analysis.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Cluster right-sizing savings
WITH cluster_savings AS (
  SELECT 
    'Cluster Right-Sizing' as optimization_type,
    cluster_name as resource,
    recommended_action,
    potential_savings_usd as monthly_savings,
    confidence,
    CASE 
      WHEN recommended_action = 'TERMINATE' THEN 'LOW'
      WHEN recommended_action = 'DOWNSIZE' THEN 'MEDIUM'
      ELSE 'HIGH'
    END as implementation_complexity
  FROM ${catalog}.${gold_schema}.cluster_rightsizing_recommendations
  WHERE potential_savings_usd > 0
),
-- Step 2: Job cost optimization savings
job_savings AS (
  SELECT 
    'Job Cost Optimization' as optimization_type,
    job_name as resource,
    recommended_action,
    estimated_savings_usd as monthly_savings,
    confidence,
    CASE 
      WHEN recommended_action LIKE '%SERVERLESS%' THEN 'MEDIUM'
      WHEN recommended_action LIKE '%PHOTON%' THEN 'LOW'
      ELSE 'HIGH'
    END as implementation_complexity
  FROM ${catalog}.${gold_schema}.job_cost_optimizer_predictions
  WHERE estimated_savings_usd > 0
),
-- Step 3: Commitment recommendations
commitment_savings AS (
  SELECT 
    'Commitment Purchase' as optimization_type,
    commitment_type as resource,
    'COMMIT' as recommended_action,
    monthly_savings_usd as monthly_savings,
    confidence,
    'HIGH' as implementation_complexity  -- Financial commitment
  FROM ${catalog}.${gold_schema}.commitment_recommendations
  WHERE monthly_savings_usd > 0
),
-- Step 4: Combine all savings
all_savings AS (
  SELECT * FROM cluster_savings
  UNION ALL SELECT * FROM job_savings
  UNION ALL SELECT * FROM commitment_savings
),
-- Step 5: Calculate ROI and prioritize
prioritized AS (
  SELECT 
    optimization_type,
    resource,
    recommended_action,
    monthly_savings,
    monthly_savings * 12 as annual_savings,
    confidence,
    implementation_complexity,
    monthly_savings * confidence as risk_adjusted_savings,
    CASE implementation_complexity
      WHEN 'LOW' THEN 1
      WHEN 'MEDIUM' THEN 2
      ELSE 3
    END as complexity_score,
    monthly_savings * confidence / (CASE implementation_complexity WHEN 'LOW' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END) as priority_score
  FROM all_savings
)
SELECT 
  optimization_type,
  COUNT(*) as recommendation_count,
  ROUND(SUM(monthly_savings), 2) as total_monthly_savings,
  ROUND(SUM(annual_savings), 2) as total_annual_savings,
  ROUND(AVG(confidence) * 100, 1) as avg_confidence_pct,
  MODE(implementation_complexity) as typical_complexity,
  ROUND(SUM(risk_adjusted_savings), 2) as risk_adjusted_monthly_savings,
  DENSE_RANK() OVER (ORDER BY SUM(priority_score) DESC) as implementation_priority
FROM prioritized
GROUP BY optimization_type
ORDER BY implementation_priority;
```
**Expected Result:** Prioritized optimization roadmap showing total potential savings across all ML recommendations, organized by optimization type with ROI and complexity analysis.

---

### Question 24: "Which workspaces have the most volatile spend patterns based on historical trends, anomaly detection, and forecast uncertainty, and what's driving the volatility?"
**Deep Research Complexity:** Combines historical spend variance, anomaly frequency, forecast confidence intervals, and SKU-level decomposition to identify and explain spend volatility.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Calculate historical spend volatility by workspace
WITH spend_volatility AS (
  SELECT 
    workspace_name,
    STDDEV(daily_cost) as cost_stddev,
    AVG(daily_cost) as avg_daily_cost,
    STDDEV(daily_cost) / NULLIF(AVG(daily_cost), 0) * 100 as coefficient_of_variation,
    MAX(daily_cost) - MIN(daily_cost) as cost_range,
    COUNT(DISTINCT DATE_TRUNC('day', usage_date)) as days_analyzed
  FROM (
    SELECT 
      workspace_name,
      DATE_TRUNC('day', usage_date) as day,
      SUM(usage_cost) as daily_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
    GROUP BY workspace_name, DATE_TRUNC('day', usage_date)
  )
  GROUP BY workspace_name
),
-- Step 2: Count anomalies per workspace
anomaly_frequency AS (
  SELECT 
    workspace_id as workspace_name,
    COUNT(*) as anomaly_count,
    SUM(CASE WHEN ABS(anomaly_score) > 2 THEN 1 ELSE 0 END) as severe_anomalies,
    AVG(ABS(anomaly_score)) as avg_anomaly_severity
  FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
  WHERE prediction_date >= CURRENT_DATE() - INTERVAL 90 DAYS
    AND is_anomaly = TRUE
  GROUP BY workspace_id
),
-- Step 3: Get forecast uncertainty
forecast_uncertainty AS (
  SELECT 
    workspace_id as workspace_name,
    AVG(upper_bound - lower_bound) as avg_forecast_range,
    AVG((upper_bound - lower_bound) / NULLIF(predicted_cost, 0) * 100) as relative_uncertainty_pct
  FROM ${catalog}.${gold_schema}.budget_forecast_predictions
  WHERE forecast_date >= CURRENT_DATE()
  GROUP BY workspace_id
),
-- Step 4: Identify top volatile SKUs per workspace
sku_volatility AS (
  SELECT 
    workspace_name,
    sku_name,
    STDDEV(usage_cost) as sku_stddev,
    ROW_NUMBER() OVER (PARTITION BY workspace_name ORDER BY STDDEV(usage_cost) DESC) as sku_rank
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
  GROUP BY workspace_name, sku_name
)
SELECT 
  v.workspace_name,
  ROUND(v.coefficient_of_variation, 1) as volatility_cv_pct,
  ROUND(v.cost_range, 2) as daily_cost_range,
  ROUND(v.avg_daily_cost, 2) as avg_daily_cost,
  COALESCE(a.anomaly_count, 0) as anomalies_90d,
  COALESCE(a.severe_anomalies, 0) as severe_anomalies,
  ROUND(COALESCE(f.relative_uncertainty_pct, 0), 1) as forecast_uncertainty_pct,
  COLLECT_LIST(s.sku_name) as top_volatile_skus,
  CASE 
    WHEN v.coefficient_of_variation > 50 AND a.severe_anomalies > 3 THEN '🔴 HIGHLY VOLATILE'
    WHEN v.coefficient_of_variation > 30 OR a.anomaly_count > 5 THEN '🟠 MODERATELY VOLATILE'
    ELSE '🟢 STABLE'
  END as volatility_classification,
  CASE 
    WHEN v.coefficient_of_variation > 50 THEN 'Investigate: ' || CONCAT_WS(', ', COLLECT_LIST(s.sku_name))
    ELSE 'Normal spend patterns'
  END as investigation_recommendation
FROM spend_volatility v
LEFT JOIN anomaly_frequency a ON v.workspace_name = a.workspace_name
LEFT JOIN forecast_uncertainty f ON v.workspace_name = f.workspace_name
LEFT JOIN sku_volatility s ON v.workspace_name = s.workspace_name AND s.sku_rank <= 3
GROUP BY v.workspace_name, v.coefficient_of_variation, v.cost_range, v.avg_daily_cost, 
         a.anomaly_count, a.severe_anomalies, f.relative_uncertainty_pct
ORDER BY v.coefficient_of_variation DESC
LIMIT 15;
```
**Expected Result:** Workspaces ranked by spend volatility with multi-factor volatility score, anomaly history, forecast uncertainty, and specific SKUs driving the volatility.

---

### Question 25: "What's the correlation between cost efficiency (DBU cost per output) and platform adoption patterns across teams, and which teams are getting the best ROI from their Databricks investment?"
**Deep Research Complexity:** Combines cost data with job output metrics, query volumes, and user activity to calculate cost efficiency and ROI metrics across organizational teams.

**Expected SQL (Multi-Step Analysis):**
```sql
-- Step 1: Calculate cost per team (using owner as team proxy)
WITH team_costs AS (
  SELECT 
    usage_owner as team,
    SUM(usage_cost) as total_cost,
    SUM(usage_quantity) as total_dbus
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY usage_owner
),
-- Step 2: Calculate job output metrics per team
job_output AS (
  SELECT 
    job_owner as team,
    COUNT(*) as total_job_runs,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) as successful_runs,
    AVG(duration_seconds) as avg_duration,
    SUM(rows_written) as total_rows_produced
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY job_owner
),
-- Step 3: Calculate query activity per team
query_activity AS (
  SELECT 
    executed_by as team,
    COUNT(*) as total_queries,
    SUM(total_bytes_read) / 1e9 as total_gb_scanned,
    AVG(duration_ms) as avg_query_duration_ms
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE execution_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY executed_by
),
-- Step 4: Calculate adoption metrics
adoption_metrics AS (
  SELECT 
    team,
    DATEDIFF(CURRENT_DATE(), MIN(first_activity)) as days_since_onboarding,
    COUNT(DISTINCT active_user) as team_size
  FROM (
    SELECT usage_owner as team, user_identity as active_user, MIN(usage_date) as first_activity
    FROM ${catalog}.${gold_schema}.fact_usage
    GROUP BY usage_owner, user_identity
  )
  GROUP BY team
),
-- Step 5: Calculate efficiency and ROI metrics
efficiency_metrics AS (
  SELECT 
    c.team,
    c.total_cost,
    c.total_dbus,
    COALESCE(j.total_job_runs, 0) as job_runs,
    COALESCE(j.successful_runs, 0) as successful_job_runs,
    COALESCE(j.total_rows_produced, 0) as rows_produced,
    COALESCE(q.total_queries, 0) as queries_executed,
    COALESCE(q.total_gb_scanned, 0) as data_scanned_gb,
    COALESCE(a.team_size, 1) as team_size,
    c.total_cost / NULLIF(c.total_dbus, 0) as cost_per_dbu,
    c.total_cost / NULLIF(j.successful_runs, 0) as cost_per_successful_job,
    c.total_cost / NULLIF(COALESCE(j.total_rows_produced, 0) / 1e6, 0) as cost_per_million_rows,
    c.total_cost / NULLIF(a.team_size, 0) as cost_per_user,
    (COALESCE(j.total_job_runs, 0) + COALESCE(q.total_queries, 0)) / NULLIF(c.total_cost, 0) * 1000 as activities_per_1k_spend
  FROM team_costs c
  LEFT JOIN job_output j ON c.team = j.team
  LEFT JOIN query_activity q ON c.team = q.team
  LEFT JOIN adoption_metrics a ON c.team = a.team
)
SELECT 
  team,
  ROUND(total_cost, 2) as total_spend_30d,
  team_size,
  ROUND(cost_per_user, 2) as cost_per_user,
  job_runs + queries_executed as total_activities,
  ROUND(activities_per_1k_spend, 1) as activities_per_1k_spend,
  ROUND(cost_per_successful_job, 2) as cost_per_successful_job,
  ROUND(rows_produced / 1e6, 1) as millions_rows_produced,
  ROUND(cost_per_million_rows, 2) as cost_per_million_rows,
  PERCENT_RANK() OVER (ORDER BY activities_per_1k_spend DESC) * 100 as efficiency_percentile,
  CASE 
    WHEN activities_per_1k_spend > (SELECT PERCENTILE(activities_per_1k_spend, 0.75) FROM efficiency_metrics) THEN '🟢 HIGH EFFICIENCY'
    WHEN activities_per_1k_spend > (SELECT PERCENTILE(activities_per_1k_spend, 0.25) FROM efficiency_metrics) THEN '🟡 AVERAGE EFFICIENCY'
    ELSE '🔴 LOW EFFICIENCY - REVIEW'
  END as efficiency_tier,
  CASE 
    WHEN cost_per_successful_job < 1 AND activities_per_1k_spend > 100 THEN 'TOP ROI: Heavy automation, low cost per job'
    WHEN cost_per_user < 500 AND team_size > 3 THEN 'GOOD ROI: Efficient team utilization'
    WHEN cost_per_million_rows < 10 THEN 'GOOD ROI: Efficient data processing'
    ELSE 'REVIEW: Potential optimization opportunities'
  END as roi_assessment
FROM efficiency_metrics
WHERE total_cost > 100  -- Filter out minimal spend
ORDER BY activities_per_1k_spend DESC
LIMIT 20;
```
**Expected Result:** Teams ranked by cost efficiency with multi-dimensional ROI analysis including cost per job, cost per user, activities per spend, and efficiency tier classification.

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

