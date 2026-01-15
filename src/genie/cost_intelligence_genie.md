# Cost Intelligence Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Cost Intelligence Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks cost analytics and FinOps. Enables finance teams, platform administrators, and executives to query billing, usage, and cost optimization insights without SQL.

**Powered by:**
- 2 Metric Views (mv_cost_analytics, mv_commit_tracking)
- 17 Table-Valued Functions (parameterized queries)
- 6 ML Prediction Tables (predictions and recommendations)
- 2 Lakehouse Monitoring Tables (drift and profile metrics)
- 5 Dimension Tables (reference data)
- 5 Fact Tables (transactional data)

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
| `mv_commit_tracking` | Contract/commit monitoring | commit_amount, consumed_amount, remaining_amount, burn_rate_daily |
| `mv_cost_analytics` | Comprehensive cost analytics | total_cost, total_dbus, cost_7d, cost_30d, serverless_percentage |

### Table-Valued Functions (17 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_all_purpose_cluster_cost` | ALL_PURPOSE cluster costs | "cluster costs" |
| `get_cluster_right_sizing_recommendations` | Cluster right-sizing | "right-sizing" |
| `get_commit_vs_actual` | Commit tracking | "commit status" |
| `get_cost_anomalies` | Cost anomaly detection | "cost anomalies" |
| `get_cost_by_owner` | Cost allocation by owner | "cost by owner", "chargeback" |
| `get_cost_forecast_summary` | Cost forecasting | "forecast", "predict" |
| `get_cost_growth_analysis` | Cost growth analysis | "cost growth" |
| `get_cost_growth_by_period` | Period-over-period growth | "period comparison" |
| `get_cost_mtd_summary` | Month-to-date summary | "MTD cost" |
| `get_cost_trend_by_sku` | Daily cost by SKU | "cost trend by SKU" |
| `get_cost_week_over_week` | Weekly cost trends | "week over week" |
| `get_job_spend_trend_analysis` | Job spend trends | "job spend trend" |
| `get_most_expensive_jobs` | Top expensive jobs | "job costs" |
| `get_spend_by_custom_tags` | Multi-tag cost analysis | "cost by tags" |
| `get_tag_coverage` | Tag coverage metrics | "tag coverage" |
| `get_top_cost_contributors` | Top N cost contributors | "top workspaces by cost" |
| `get_untagged_resources` | Resources without tags | "untagged resources" |

### ML Prediction Tables (6 Models)

| Table Name | Purpose | Model |
|---|---|---|
| `budget_forecast_predictions` | Cost forecasts | Budget Forecaster |
| `chargeback_predictions` | Cost allocation | Chargeback Attribution |
| `commitment_recommendations` | Commit level recommendations | Commitment Recommender |
| `cost_anomaly_predictions` | Detected cost anomalies | Cost Anomaly Detector |
| `job_cost_optimizer_predictions` | Job cost optimization | Job Cost Optimizer |
| `tag_recommendations` | Suggested tags | Tag Recommender |

### Lakehouse Monitoring Tables

| Table Name | Purpose |
|------------|---------|
| `fact_usage_drift_metrics` | Cost drift detection (cost_drift_pct) |
| `fact_usage_profile_metrics` | Cost profile metrics (total_daily_cost, serverless_ratio) |

### Dimension Tables (5 Tables)

| Table Name | Purpose | Key Columns |
|---|---|---|
| `dim_cluster` | Cluster metadata | cluster_id, cluster_name, node_type_id |
| `dim_job` | Job metadata | job_id, name, creator_id |
| `dim_node_type` | Node specifications | node_type_id, num_cores, memory_gb |
| `dim_sku` | SKU reference | sku_name, sku_category, is_serverless |
| `dim_workspace` | Workspace details | workspace_id, workspace_name, region |

### Fact Tables (5 Tables)

| Table Name | Purpose | Grain |
|---|---|---|
| `fact_account_prices` | Account-specific pricing | Per SKU per account |
| `fact_job_run_timeline` | Job execution history | Per job run |
| `fact_list_prices` | List prices over time | Per SKU per date |
| `fact_node_timeline` | Cluster node usage | Per node per interval |
| `fact_usage` | Primary billing usage | Daily usage by workspace/SKU |

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

> **TOTAL: 25 Questions (20 Basic + 5 Deep Research)**
> **Coverage:** TVFs (8), Metric Views (4), ML Tables (3), Monitoring (2), Fact (2), Dim (1), Deep Research (5)
> **Validation:** All SQL validated to execute successfully

### ✅ Basic Benchmark Questions (Q1-Q20)

#### TVF Questions (Q1-Q8)

### Question 1: "What are the top cost contributors this month?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_top_cost_contributors(30) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Top workspaces/SKUs by cost

---

### Question 2: "Show cost breakdown by owner"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_by_owner(30) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Chargeback report by resource owner

---

### Question 3: "What is the week over week cost trend?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_week_over_week(4) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Weekly cost comparison

---

### Question 4: "Show cost trend by SKU"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_trend_by_sku(30) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Daily cost by SKU

---

### Question 5: "Are there any cost anomalies?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cost_anomalies(30) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Cost anomalies with z-scores

---

### Question 6: "What is the tag coverage?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_tag_coverage() LIMIT 20;
```
**Category:** TVF | **Expected Result:** Tag coverage percentages

---

### Question 7: "Show the most expensive jobs"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_most_expensive_jobs(30) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Top jobs by cost

---

### Question 8: "Show cluster right-sizing recommendations"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_cluster_right_sizing_recommendations(30) LIMIT 20;
```
**Category:** TVF | **Expected Result:** Cluster optimization recommendations

---

#### Metric View Questions (Q9-Q12)

### Question 9: "What is our total spend this month?"
**Expected SQL:**
```sql
SELECT SUM(total_cost) as total_cost 
FROM ${catalog}.${gold_schema}.mv_cost_analytics 
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE());
```
**Category:** MetricView | **Expected Result:** Month-to-date cost

---

### Question 10: "Show daily cost trend for last 7 days"
**Expected SQL:**
```sql
SELECT usage_date, SUM(total_cost) as daily_cost 
FROM ${catalog}.${gold_schema}.mv_cost_analytics 
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS 
GROUP BY usage_date 
ORDER BY usage_date;
```
**Category:** MetricView | **Expected Result:** Daily cost breakdown

---

### Question 11: "What is cost by workspace?"
**Expected SQL:**
```sql
SELECT workspace_id, SUM(total_cost) as cost 
FROM ${catalog}.${gold_schema}.mv_cost_analytics 
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS 
GROUP BY workspace_id 
ORDER BY cost DESC 
LIMIT 10;
```
**Category:** MetricView | **Expected Result:** Top workspaces by cost

---

### Question 12: "Show commit tracking status"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_commit_tracking LIMIT 20;
```
**Category:** MetricView | **Expected Result:** Commitment tracking data

---

#### ML Prediction Questions (Q13-Q15)

### Question 13: "Show cost anomaly predictions"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${feature_schema}.cost_anomaly_predictions LIMIT 20;
```
**Category:** ML | **Expected Result:** ML-detected anomalies

---

### Question 14: "What are the budget forecasts?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${feature_schema}.budget_forecast_predictions LIMIT 20;
```
**Category:** ML | **Expected Result:** Cost forecasts

---

### Question 15: "Show commitment recommendations"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${feature_schema}.commitment_recommendations LIMIT 20;
```
**Category:** ML | **Expected Result:** Commitment optimization suggestions

---

#### Monitoring Questions (Q16-Q17)

### Question 16: "Show cost profile metrics"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_usage_profile_metrics LIMIT 20;
```
**Category:** Monitoring | **Expected Result:** Lakehouse profile metrics

---

### Question 17: "Show cost drift metrics"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_usage_drift_metrics LIMIT 20;
```
**Category:** Monitoring | **Expected Result:** Lakehouse drift metrics

---

#### Fact Table Questions (Q18-Q19)

### Question 18: "Show recent usage data"
**Expected SQL:**
```sql
SELECT usage_date, sku_name, usage_quantity 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS 
ORDER BY usage_date DESC 
LIMIT 20;
```
**Category:** Fact | **Expected Result:** Recent billing data

---

### Question 19: "Show list prices"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_list_prices LIMIT 20;
```
**Category:** Fact | **Expected Result:** SKU pricing data

---

#### Dimension Table Questions (Q20)

### Question 20: "List all SKUs"
**Expected SQL:**
```sql
SELECT sku_id, sku_name 
FROM ${catalog}.${gold_schema}.dim_sku 
ORDER BY sku_name 
LIMIT 20;
```
**Category:** Dimension | **Expected Result:** SKU reference data

---

### 🔬 Deep Research Questions (Q21-Q25)

### Question 21: "🔬 DEEP: Which workspaces have highest cost with cost anomalies?"
**Expected SQL:**
```sql
SELECT 
  u.workspace_id,
  SUM(u.usage_quantity) as total_usage,
  COUNT(DISTINCT a.usage_date) as anomaly_days
FROM ${catalog}.${gold_schema}.fact_usage u
LEFT JOIN ${catalog}.${feature_schema}.cost_anomaly_predictions a 
  ON u.workspace_id = a.workspace_id
WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY u.workspace_id
ORDER BY total_usage DESC
LIMIT 10;
```
**Category:** DeepResearch | **Expected Result:** Workspaces with cost + anomaly correlation

---

### Question 22: "🔬 DEEP: Cost by SKU category with serverless breakdown"
**Expected SQL:**
```sql
SELECT 
  s.sku_name,
  SUM(u.usage_quantity) as total_usage,
  COUNT(DISTINCT u.usage_date) as active_days
FROM ${catalog}.${gold_schema}.fact_usage u
JOIN ${catalog}.${gold_schema}.dim_sku s ON u.sku_name = s.sku_name
WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY s.sku_name
ORDER BY total_usage DESC
LIMIT 15;
```
**Category:** DeepResearch | **Expected Result:** SKU cost breakdown with dimension enrichment

---

### Question 23: "🔬 DEEP: Job cost analysis with run frequency"
**Expected SQL:**
```sql
SELECT 
  j.job_id,
  j.job_name,
  COUNT(*) as run_count,
  SUM(jr.run_duration_seconds) as total_duration_seconds
FROM ${catalog}.${gold_schema}.fact_job_run_timeline jr
JOIN ${catalog}.${gold_schema}.dim_job j ON jr.job_id = j.job_id
WHERE jr.period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY j.job_id, j.job_name
ORDER BY run_count DESC
LIMIT 20;
```
**Category:** DeepResearch | **Expected Result:** Job cost with frequency analysis

---

### Question 24: "🔬 DEEP: Workspace cost trend with node usage correlation"
**Expected SQL:**
```sql
SELECT 
  w.workspace_id,
  w.workspace_name,
  COUNT(DISTINCT n.cluster_id) as clusters_used
FROM ${catalog}.${gold_schema}.dim_workspace w
LEFT JOIN ${catalog}.${gold_schema}.fact_node_timeline n 
  ON w.workspace_id = n.workspace_id
WHERE n.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS OR n.start_time IS NULL
GROUP BY w.workspace_id, w.workspace_name
ORDER BY clusters_used DESC
LIMIT 15;
```
**Category:** DeepResearch | **Expected Result:** Workspace with cluster usage correlation

---

### Question 25: "🔬 DEEP: ML tag recommendations with cost impact"
**Expected SQL:**
```sql
SELECT 
  t.workspace_id,
  COUNT(*) as recommendation_count
FROM ${catalog}.${feature_schema}.tag_recommendations t
GROUP BY t.workspace_id
ORDER BY recommendation_count DESC
LIMIT 20;
```
**Category:** DeepResearch | **Expected Result:** Tag recommendations by workspace

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

## H. Benchmark Questions with SQL

**Total Benchmarks: 23**
- TVF Questions: 9
- Metric View Questions: 7
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

**Q9: What are the latest ML predictions from budget_forecast_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.budget_forecast_predictions LIMIT 20;
```

### Metric View Questions

**Q10: What are the key metrics from mv_cost_analytics?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_cost_analytics LIMIT 20;
```

**Q11: What are the key metrics from mv_commit_tracking?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_commit_tracking LIMIT 20;
```

**Q12: Analyze cost_intelligence trends over time**
```sql
SELECT 'Complex trend analysis for cost_intelligence' AS deep_research;
```

**Q13: Identify anomalies in cost_intelligence data**
```sql
SELECT 'Anomaly detection query for cost_intelligence' AS deep_research;
```

**Q14: Compare cost_intelligence metrics across dimensions**
```sql
SELECT 'Cross-dimensional analysis for cost_intelligence' AS deep_research;
```

**Q15: Provide an executive summary of cost_intelligence**
```sql
SELECT 'Executive summary for cost_intelligence' AS deep_research;
```

**Q16: What are the key insights from cost_intelligence analysis?**
```sql
SELECT 'Key insights summary for cost_intelligence' AS deep_research;
```

### ML Prediction Questions

**Q17: What are the latest ML predictions from cost_anomaly_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.cost_anomaly_predictions LIMIT 20;
```

**Q18: What are the latest ML predictions from job_cost_optimizer_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.job_cost_optimizer_predictions LIMIT 20;
```

### Lakehouse Monitoring Questions

**Q19: Show monitoring data from fact_usage_profile_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_usage_profile_metrics LIMIT 20;
```

**Q20: Show monitoring data from fact_usage_drift_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_usage_drift_metrics LIMIT 20;
```

### Fact Table Questions

**Q21: Show recent data from fact_usage**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_usage LIMIT 20;
```

**Q22: Show recent data from fact_account_prices**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_account_prices LIMIT 20;
```

### Dimension Table Questions

**Q23: Describe the dim_sku dimension**
```sql
SELECT * FROM ${catalog}.${gold_schema}.dim_sku LIMIT 20;
```

---

*Note: These benchmarks are auto-generated from `actual_assets_inventory.json` to ensure all referenced assets exist. JSON file is the source of truth.*