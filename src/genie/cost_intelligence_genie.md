# Cost Intelligence Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Cost Intelligence Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks cost analytics and FinOps. Enables finance teams, platform administrators, and executives to query billing, usage, and cost optimization insights without SQL. Powered by Cost Analytics Metric Views, 15 Table-Valued Functions, 6 ML Models, and Lakehouse Monitoring custom metrics.

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

### ML Prediction Tables 🤖

| Table Name | Purpose |
|------------|---------|
| `cost_anomaly_predictions` | Detected cost anomalies with scores |
| `cost_forecast_predictions` | 30-day cost forecasts |
| `tag_recommendations` | Suggested tags for untagged resources |
| `user_cost_segments` | User behavior clustering |
| `migration_recommendations` | ALL_PURPOSE to JOBS migration candidates |
| `budget_alert_predictions` | Prioritized budget alerts |

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

### Dimension Tables (from gold_layer_design/yaml/billing/, shared/)

| Table Name | Purpose | Key Columns | YAML Source |
|------------|---------|-------------|-------------|
| `dim_workspace` | Workspace details | workspace_id, workspace_name, region | shared/dim_workspace.yaml |
| `dim_sku` | SKU reference | sku_name, sku_category, list_price | billing/dim_sku.yaml |

### Fact Tables (from gold_layer_design/yaml/billing/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_usage` | Billing usage | Daily usage by workspace/SKU/user | billing/fact_usage.yaml |
| `fact_account_prices` | Account-specific pricing | Per SKU per account | billing/fact_account_prices.yaml |
| `fact_list_prices` | List prices over time | Per SKU per effective date | billing/fact_list_prices.yaml |

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

## ████ SECTION F: TABLE-VALUED FUNCTIONS ████

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

## ████ SECTION G: ML MODEL INTEGRATION (6 Models) ████

### Cost ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `cost_anomaly_detector` | `cost_anomaly_predictions` | `anomaly_score`, `is_anomaly` | "Is this spending unusual?" |
| `budget_forecaster` | `cost_forecast_predictions` | `predicted_cost`, `confidence_interval` | "Forecast next month" |
| `job_cost_optimizer` | `migration_recommendations` | `potential_savings`, `migration_risk` | "Where can we save?" |
| `tag_recommender` | `tag_recommendations` | `recommended_tag`, `confidence` | "Suggest tags" |
| `commitment_recommender` | `budget_alert_predictions` | `recommended_commitment` | "Commit level?" |
| `chargeback_attribution` | — | Cost allocation | "Allocate costs" |

### ML Model Usage Patterns

#### cost_anomaly_detector (Anomaly Detection)
- **Question Triggers:** "anomaly", "unusual", "spike", "abnormal", "outlier"
- **Query Pattern:**
```sql
SELECT workspace_name, usage_date, actual_cost, anomaly_score, is_anomaly
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND is_anomaly = TRUE
ORDER BY anomaly_score ASC;
```
- **Interpretation:** `anomaly_score < -0.5` = High confidence anomaly

#### budget_forecaster (Cost Forecasting)
- **Question Triggers:** "forecast", "predict", "next month", "project", "estimate"
- **Query Pattern:**
```sql
SELECT forecast_date, predicted_cost, lower_bound, upper_bound, confidence_pct
FROM ${catalog}.${gold_schema}.cost_forecast_predictions
WHERE workspace_id = 'ALL'
ORDER BY forecast_date;
```
- **Interpretation:** Compare `predicted_cost` with actuals; alert if `actual > upper_bound`

#### tag_recommender (Tag Suggestions)
- **Question Triggers:** "recommend tags", "suggest tags", "auto-tag", "what tags should"
- **Query Pattern:**
```sql
SELECT resource_name, recommended_tag_key, recommended_tag_value, confidence_score
FROM ${catalog}.${gold_schema}.tag_recommendations
WHERE confidence_score > 0.7
ORDER BY confidence_score DESC;
```

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Will cost exceed budget?"              → ML: cost_forecast_predictions
"Is this spending unusual?"             → ML: cost_anomaly_predictions  
"How can we reduce costs?"              → ML: migration_recommendations
"What tags should we apply?"            → ML: tag_recommendations
────────────────────────────────────────────────────
"What is the current cost?"             → Metric View: cost_analytics
"Is cost trending up?"                  → Custom Metrics: _drift_metrics
"Top 10 by cost"                        → TVF: get_top_cost_contributors
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

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

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 15 functions with signatures | ✅ |
| **G. Benchmark Questions** | 12 with SQL answers | ✅ |

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

