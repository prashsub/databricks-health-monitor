# Phase 3 Addendum 3.5: AI/BI Dashboards for Databricks Health Monitor

## Overview

**Status:** Planned  
**Dependencies:** Gold Layer (Phase 2), Metric Views (Phase 3.3), TVFs (Phase 3.2)  
**Estimated Effort:** 2-3 weeks  
**Reference:** Cursor Rule 18 - Databricks AI/BI Dashboards

---

## Purpose

Create Databricks Lakeview AI/BI dashboards that provide:
- **Executive Overview** - High-level health metrics for leadership
- **Cost Management** - Detailed cost analysis and optimization insights
- **Reliability Monitoring** - Job and pipeline health tracking
- **Performance Analytics** - Query and compute performance analysis
- **Security Audit** - Access and compliance monitoring

---

## Dashboard Design Principles

### Lakeview Best Practices

1. **Use Metric Views** for standardized KPIs
2. **Use TVFs** for parameterized analysis
3. **Reference system tables** for real-time data
4. **Consistent time filtering** across all widgets
5. **Mobile-responsive layouts** for executive consumption

---

## 💰🔄⚡ Unified: Executive Health Overview Dashboard

### Purpose
Single-pane-of-glass view of Databricks platform health for executives.

### Agent Domains Covered
- 💰 Cost: Total spend, cost trends
- 🔄 Reliability: Job success rate
- ⚡ Performance: Query P95

### Layout (6x4 grid)

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Total Cost    │  Success Rate   │  Active Users   │
│    (KPI)        │     (KPI)       │     (KPI)       │
├─────────────────┴─────────────────┴─────────────────┤
│              Cost Trend (30 days)                    │
│              (Line Chart)                            │
├─────────────────┬─────────────────┬─────────────────┤
│  Cost by SKU    │  Job Failures   │  Query P95      │
│  (Pie Chart)    │  (Bar Chart)    │  (Trend Line)   │
├─────────────────┴─────────────────┴─────────────────┤
│              Key Metrics Summary Table               │
└─────────────────────────────────────────────────────┘
```

### Widget Queries

#### KPI 1: Total Cost (MTD)
```sql
SELECT 
    CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS metric_value,
    'Month to Date' AS metric_label
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
```

#### KPI 2: Job Success Rate
```sql
SELECT 
    CONCAT(ROUND(
        SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 1
    ), '%') AS metric_value,
    'Last 7 Days' AS metric_label
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND result_state IS NOT NULL
```

#### KPI 3: Active Users
```sql
SELECT 
    COUNT(DISTINCT identity_metadata_run_as) AS metric_value,  -- Using flattened column
    'Last 30 Days' AS metric_label
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
```

#### Chart: Cost Trend (30 days)
```sql
SELECT 
    usage_date,
    SUM(list_cost) AS daily_cost,
    SUM(SUM(list_cost)) OVER (
        ORDER BY usage_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) / 7 AS rolling_7day_avg
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY usage_date
ORDER BY usage_date
```

---

## 💰 Cost Agent: Cost Management Dashboard

### Purpose
Detailed cost analysis for FinOps teams and cost optimization.

### Agent Domain: 💰 Cost

### Inspired by: DBSQL Warehouse Advisor Dashboard, Account Usage Dashboard, Jobs System Tables Dashboard, Serverless Cost Observability Dashboard

**Reference:** [Microsoft Learn - Jobs Cost Observability](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost)

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_usage`
- `${catalog}.${gold_schema}.dim_workspace`
- `${catalog}.${gold_schema}.dim_sku`
- `${catalog}.${gold_schema}.dim_job`
- `${catalog}.${gold_schema}.commit_configurations` (for commit tracking)

---

## 💰 Cost Agent: Commit Tracking & Budget Forecast Dashboard (NEW)

### Purpose
Track actual spend against Databricks commit amount with ML-based forecasting to predict undershoot/overshoot scenarios for proactive planning.

### Agent Domain: 💰 Cost

### Key Features
- **Commit Configuration** - Set annual/monthly commit amounts
- **Run Rate Analysis** - Required monthly run rate vs actual run rate
- **ML Forecast** - Predict month-end/year-end spend using Budget Forecaster model
- **Variance Alerts** - Alert when trending to miss commit

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_usage`
- `${catalog}.${gold_schema}.commit_configurations`
- `${catalog}.${gold_schema}.budget_forecast_predictions` (ML inference table)

### Key Visualizations

| Visualization | Type | Description |
|---------------|------|-------------|
| **Commit vs Actual** | Line + Area | YTD spend vs required run rate to meet commit |
| **Monthly Burn Rate** | Bar Chart | Monthly spend with target line |
| **Forecast Cone** | Area Chart | ML prediction with P10/P50/P90 confidence intervals |
| **Commit Variance** | KPI Card | Projected overshoot/undershoot amount |
| **Monthly Pace** | Gauge | On track / Behind / Ahead indicator |

### Datasets

#### Dataset: Commit vs Actual Run Rate

```sql
-- Commit tracking with required vs actual run rate
WITH commit_config AS (
    SELECT 
        commit_year,
        annual_commit_amount,
        annual_commit_amount / 12 AS monthly_target,
        DATEDIFF(
            DATE(CONCAT(commit_year, '-12-31')), 
            DATE(CONCAT(commit_year, '-01-01'))
        ) + 1 AS days_in_year
    FROM ${catalog}.${gold_schema}.commit_configurations
    WHERE commit_year = YEAR(CURRENT_DATE())
),
monthly_spend AS (
    SELECT 
        DATE_TRUNC('month', usage_date) AS month_start,
        SUM(list_cost) AS monthly_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
    GROUP BY DATE_TRUNC('month', usage_date)
),
cumulative AS (
    SELECT 
        ms.month_start,
        ms.monthly_cost,
        SUM(ms.monthly_cost) OVER (ORDER BY ms.month_start) AS ytd_spend,
        cc.annual_commit_amount,
        cc.monthly_target,
        -- Required run rate to meet commit from current point
        (cc.annual_commit_amount - SUM(ms.monthly_cost) OVER (ORDER BY ms.month_start)) / 
            NULLIF(12 - MONTH(ms.month_start), 0) AS required_monthly_rate,
        -- Actual run rate (average of months so far)
        SUM(ms.monthly_cost) OVER (ORDER BY ms.month_start) / MONTH(ms.month_start) AS actual_run_rate
    FROM monthly_spend ms
    CROSS JOIN commit_config cc
)
SELECT 
    month_start,
    monthly_cost,
    ytd_spend,
    annual_commit_amount,
    monthly_target,
    required_monthly_rate,
    actual_run_rate,
    -- Projection
    actual_run_rate * 12 AS projected_annual_spend,
    actual_run_rate * 12 - annual_commit_amount AS projected_variance,
    CASE 
        WHEN actual_run_rate * 12 < annual_commit_amount * 0.95 THEN 'UNDERSHOOT_RISK'
        WHEN actual_run_rate * 12 > annual_commit_amount * 1.05 THEN 'OVERSHOOT_RISK'
        ELSE 'ON_TRACK'
    END AS commit_status
FROM cumulative
ORDER BY month_start
```

#### Dataset: ML Forecast with Confidence Intervals

```sql
-- ML-based budget forecast from inference table
SELECT 
    forecast_date,
    predicted_monthly_cost AS p50_forecast,
    predicted_monthly_cost_p10 AS p10_forecast,
    predicted_monthly_cost_p90 AS p90_forecast,
    -- Cumulative projections
    SUM(predicted_monthly_cost) OVER (ORDER BY forecast_date) AS cumulative_p50,
    SUM(predicted_monthly_cost_p10) OVER (ORDER BY forecast_date) AS cumulative_p10,
    SUM(predicted_monthly_cost_p90) OVER (ORDER BY forecast_date) AS cumulative_p90,
    cc.annual_commit_amount
FROM ${catalog}.${gold_schema}.budget_forecast_predictions bfp
CROSS JOIN ${catalog}.${gold_schema}.commit_configurations cc
WHERE cc.commit_year = YEAR(forecast_date)
    AND forecast_date >= CURRENT_DATE()
    AND forecast_date <= DATE(CONCAT(YEAR(CURRENT_DATE()), '-12-31'))
ORDER BY forecast_date
```

### Commit Configuration Table Schema

```sql
-- Table for storing commit configurations
CREATE TABLE IF NOT EXISTS ${catalog}.${gold_schema}.commit_configurations (
    config_id STRING NOT NULL COMMENT 'Unique configuration ID',
    commit_year INT NOT NULL COMMENT 'Year this commit applies to',
    annual_commit_amount DOUBLE NOT NULL COMMENT 'Annual commit amount in USD',
    
    -- Optional: Monthly breakdown (if non-uniform)
    monthly_breakdown ARRAY<DOUBLE> COMMENT 'Optional 12-element array for monthly targets',
    
    -- Workspace-level commits (optional)
    workspace_id STRING COMMENT 'If set, this commit applies to specific workspace',
    
    -- Alert thresholds
    undershoot_alert_pct DOUBLE DEFAULT 0.95 COMMENT 'Alert if projected < X% of commit',
    overshoot_alert_pct DOUBLE DEFAULT 1.05 COMMENT 'Alert if projected > X% of commit',
    
    -- Metadata
    created_by STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP,
    
    CONSTRAINT pk_commit_configurations PRIMARY KEY (config_id) NOT ENFORCED
)
USING DELTA
COMMENT 'Databricks commit amount configurations for budget tracking. Supports annual commits with optional monthly breakdown and workspace-level granularity.';
```

---

## 💰 Cost Agent: Tag-Based Cost Attribution Dashboard (NEW)

### Purpose
Enable fine-grained cost attribution using custom tags from [system.billing.usage](https://docs.databricks.com/aws/en/admin/system-tables/billing). Track tag hygiene and identify untagged resources.

### Agent Domain: 💰 Cost

### Key Features
- **Tag Explorer** - Browse costs by any tag key/value
- **Tag Hygiene** - Identify untagged jobs, clusters, warehouses
- **Chargeback Reports** - Generate cost reports by team/project/cost-center tags
- **Tag Coverage Trends** - Track improvement in tag adoption over time

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_usage` (contains `custom_tags` column)
- `${catalog}.${gold_schema}.dim_job`
- `${catalog}.${gold_schema}.dim_cluster`

### Key Visualizations

| Visualization | Type | Description |
|---------------|------|-------------|
| **Cost by Tag** | Treemap | Hierarchical view of cost by tag key → value |
| **Tag Coverage** | Donut | % of cost that is tagged vs untagged |
| **Untagged Resources** | Table | List of untagged jobs, clusters, warehouses |
| **Tag Adoption Trend** | Line | Tag coverage % over time |
| **Top Tag Values** | Bar | Top 10 values for selected tag key |

### Datasets

#### Dataset: Cost by Custom Tag

```sql
-- Cost breakdown by custom tags
-- Reference: https://docs.databricks.com/aws/en/admin/system-tables/billing
SELECT 
    COALESCE(tag_key, 'UNTAGGED') AS tag_key,
    COALESCE(tag_value, 'UNTAGGED') AS tag_value,
    SUM(list_cost) AS total_cost,
    COUNT(DISTINCT workspace_id) AS workspace_count,
    COUNT(DISTINCT job_id) AS job_count
FROM ${catalog}.${gold_schema}.fact_usage
LATERAL VIEW OUTER EXPLODE(custom_tags) t AS tag_key, tag_value
WHERE usage_date BETWEEN :start_date AND :end_date
GROUP BY COALESCE(tag_key, 'UNTAGGED'), COALESCE(tag_value, 'UNTAGGED')
ORDER BY total_cost DESC
```

#### Dataset: Tag Coverage Analysis

```sql
-- Tag coverage metrics
WITH tagged_analysis AS (
    SELECT 
        usage_date,
        CASE 
            WHEN is_tagged = FALSE THEN 'UNTAGGED'  -- Using pre-calculated is_tagged
            ELSE 'TAGGED'
        END AS tag_status,
        SUM(list_cost) AS cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
    GROUP BY usage_date, 
        CASE 
            WHEN is_tagged = FALSE THEN 'UNTAGGED'  -- Using pre-calculated is_tagged
            ELSE 'TAGGED'
        END
)
SELECT 
    usage_date,
    SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) AS tagged_cost,
    SUM(CASE WHEN tag_status = 'UNTAGGED' THEN cost ELSE 0 END) AS untagged_cost,
    SUM(cost) AS total_cost,
    SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 AS tag_coverage_pct
FROM tagged_analysis
GROUP BY usage_date
ORDER BY usage_date
```

#### Dataset: Untagged Jobs (from user's query, converted to Gold layer)

```sql
-- Untagged jobs that have run in last 12 months
-- Adapted from user's query to use Gold layer tables
WITH recent_runs AS (
    SELECT DISTINCT job_id, workspace_id
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline
    WHERE period_end_time > CURRENT_DATE() - INTERVAL 12 MONTHS
)
SELECT 
    j.workspace_id,
    w.workspace_name,
    j.name AS job_name,
    j.job_id,
    j.tags,
    j.run_as,
    -- Calculate cost for this job
    COALESCE(jc.total_cost, 0) AS job_cost_12m
FROM ${catalog}.${gold_schema}.dim_job j
INNER JOIN recent_runs rr ON j.job_id = rr.job_id AND j.workspace_id = rr.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
    ON j.workspace_id = w.workspace_id AND w.is_current = TRUE
LEFT JOIN (
    SELECT usage_metadata_job_id AS job_id, SUM(list_cost) AS total_cost  -- Using flattened column
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date > CURRENT_DATE() - INTERVAL 12 MONTHS
        AND usage_metadata_job_id IS NOT NULL
    GROUP BY usage_metadata_job_id
) jc ON j.job_id = jc.job_id
WHERE j.is_current = TRUE
    AND (j.tags IS NULL OR cardinality(j.tags) = 0)
ORDER BY job_cost_12m DESC
```

#### Dataset: Chargeback Report by Tag

```sql
-- Chargeback report grouped by specified tag key
-- Parameter: :tag_key (e.g., 'team', 'project', 'cost_center')
SELECT 
    custom_tags[:tag_key] AS tag_value,
    w.workspace_name,
    s.sku_name,
    DATE_TRUNC('month', usage_date) AS month,
    SUM(usage_quantity) AS total_dbu,
    SUM(list_cost) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
    ON f.workspace_id = w.workspace_id AND w.is_current = TRUE
LEFT JOIN ${catalog}.${gold_schema}.dim_sku s 
    ON f.sku_name = s.sku_name
WHERE usage_date BETWEEN :start_date AND :end_date
    AND custom_tags[:tag_key] IS NOT NULL
GROUP BY custom_tags[:tag_key], w.workspace_name, s.sku_name, DATE_TRUNC('month', usage_date)
ORDER BY month, total_cost DESC
```

### Widget Queries

#### Top Cost Contributors (Bar Chart)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_top_cost_contributors(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        10
    )
)
```

#### Most Expensive Jobs (Table) - From MS Learn Pattern
```sql
WITH list_cost_per_job AS (
    SELECT
        t1.workspace_id,
        t1.usage_metadata.job_id,
        COUNT(DISTINCT t1.usage_metadata.job_run_id) AS runs,
        SUM(t1.list_costs.pricing.default) AS list_cost,
        FIRST(identity_metadata.run_as, TRUE) AS run_as,
        MAX(t1.usage_end_time) AS last_seen_date
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
        AND t1.usage_start_time >= list_prices.price_start_time
        AND (t1.usage_end_time <= list_prices.price_end_time OR list_prices.price_end_time IS NULL)
    WHERE t1.billing_origin_product = 'JOBS'
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY ALL
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT
    t2.name AS job_name,
    t1.job_id,
    t1.workspace_id,
    t1.runs,
    t1.run_as,
    ROUND(SUM(list_cost), 2) AS list_cost,
    t1.last_seen_date
FROM list_cost_per_job t1
LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
GROUP BY ALL
ORDER BY list_cost DESC
LIMIT 25
```

#### 📊 Highest Growth Jobs (7 vs 14 Day) - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: highest_change_jobs_7_14_days
-- Shows jobs with biggest spend increase to identify potential runaway costs
WITH job_run_timeline_with_cost AS (
    SELECT
        t1.*,
        t1.usage_metadata.job_id AS job_id,
        t1.identity_metadata.run_as AS run_as,
        t1.list_costs.pricing.default AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
        AND t1.usage_start_time >= list_prices.price_start_time
        AND (t1.usage_end_time <= list_prices.price_end_time OR list_prices.price_end_time IS NULL)
    WHERE t1.sku_name LIKE '%JOBS%' 
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 14 DAY
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT
    t2.name AS job_name,
    t1.workspace_id,
    t1.job_id,
    t1.sku_name,
    t1.run_as,
    Last7DaySpend,
    Last14DaySpend,
    last7DaySpend - last14DaySpend AS Last7DayGrowth,
    try_divide((last7DaySpend - last14DaySpend), last14DaySpend) * 100 AS Last7DayGrowthPct
FROM (
    SELECT
        workspace_id,
        job_id,
        run_as,
        sku_name,
        SUM(CASE WHEN usage_end_time BETWEEN date_add(current_date(), -8) AND date_add(current_date(), -1) 
                 THEN list_cost ELSE 0 END) AS Last7DaySpend,
        SUM(CASE WHEN usage_end_time BETWEEN date_add(current_date(), -15) AND date_add(current_date(), -8) 
                 THEN list_cost ELSE 0 END) AS Last14DaySpend
    FROM job_run_timeline_with_cost
    GROUP BY ALL
) t1
LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
ORDER BY Last7DayGrowth DESC
LIMIT 20
```

#### 📊 Spend by Custom Tags (Pie Chart) - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: spend_by_tag
-- Critical for cost allocation and chargeback reporting
WITH tagraw AS (
    SELECT 
        explode(custom_tags) AS (tag_key, tag_value),
        (list_costs.pricing.default) AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
        AND t1.usage_start_time >= list_prices.price_start_time
        AND (t1.usage_end_time <= list_prices.price_end_time OR list_prices.price_end_time IS NULL)
    WHERE t1.sku_name LIKE '%JOBS%'
        AND t1.sku_name NOT ILIKE '%jobs_serverless%'
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAY
),
tagspend AS (
    SELECT CONCAT(tag_key, ': ', tag_value) AS tag_bucket, SUM(list_cost) AS list_cost
    FROM tagraw GROUP BY 1
),
untagged AS (
    SELECT 'Untagged' AS tag_bucket, SUM(list_costs.pricing.default) AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
    WHERE t1.sku_name LIKE '%JOBS%'
        AND t1.sku_name NOT ILIKE '%jobs_serverless%'
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAY
        AND cardinality(custom_tags) = 0
)
SELECT * FROM tagspend
UNION ALL
SELECT * FROM untagged
ORDER BY list_cost DESC
LIMIT 20
```

#### 📊 Job Cost Savings Opportunities (Table) - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: job_cost_savings
-- Identifies underutilized jobs based on CPU usage for right-sizing
WITH list_cost_per_job_cluster AS (
    SELECT
        t1.workspace_id,
        t1.usage_metadata.job_id,
        t1.usage_metadata.cluster_id,
        SUM(t1.list_costs.pricing.default) AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
    WHERE t1.sku_name LIKE '%JOBS%'
        AND t1.sku_name NOT ILIKE '%jobs_serverless%'
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY ALL
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
),
jobsrollingmonth AS (
    SELECT t2.name, t1.job_id, t1.workspace_id, t1.cluster_id, SUM(list_cost) AS list_cost
    FROM list_cost_per_job_cluster t1
    LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
    GROUP BY ALL
),
jobswithutil AS (
    SELECT 
        jobsrollingmonth.workspace_id, 
        jobsrollingmonth.name,
        AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu_util,
        MAX(cpu_user_percent + cpu_system_percent) AS peak_cpu_util,
        AVG(mem_used_percent) AS avg_memory_util,
        MAX(mem_used_percent) AS max_memory_util
    FROM system.compute.node_timeline 
    JOIN jobsrollingmonth ON node_timeline.cluster_id = jobsrollingmonth.cluster_id
    WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY 1, 2
)
SELECT 
    workspace_id,
    name AS job_name,
    ROUND(avg_cpu_util, 1) AS avg_cpu_pct,
    ROUND(peak_cpu_util, 1) AS peak_cpu_pct,
    ROUND(avg_memory_util, 1) AS avg_mem_pct,
    ROUND(SUM(j.list_cost), 2) AS job_cost_30d,
    ROUND((SUM(j.list_cost) * (1 - (avg_cpu_util / 100))) / 2.0, 2) AS max_savings
FROM jobswithutil u
JOIN jobsrollingmonth j USING (workspace_id, name)
GROUP BY ALL
ORDER BY max_savings DESC
LIMIT 25
```

#### Cost by SKU (Pie Chart)
```sql
SELECT 
    sku_name,
    SUM(list_cost) AS total_cost,
    ROUND(SUM(list_cost) * 100.0 / 
          SUM(SUM(list_cost)) OVER (), 1) AS pct_of_total
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY sku_name
ORDER BY total_cost DESC
```

#### Cost by Workspace (Heatmap)
```sql
SELECT 
    w.workspace_name,
    DATE_TRUNC('week', f.usage_date) AS week_start,
    SUM(f.usage_quantity * f.list_price) AS weekly_cost
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
    ON f.workspace_id = w.workspace_id AND w.is_current = TRUE
WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
GROUP BY w.workspace_name, DATE_TRUNC('week', f.usage_date)
ORDER BY week_start, weekly_cost DESC
```

#### Cost by Owner (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_cost_by_owner(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        20
    )
)
```

#### Week-over-Week Growth (Line Chart)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_cost_week_over_week(12)
)
```

#### DBU Consumption by Hour (Heatmap)
```sql
-- Hourly DBU consumption heatmap
SELECT 
    DAYOFWEEK(usage_date) AS day_of_week,
    HOUR(usage_start_time) AS hour_of_day,
    SUM(usage_quantity) AS total_dbu
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DAYOFWEEK(usage_date), HOUR(usage_start_time)
ORDER BY day_of_week, hour_of_day
```

---

## 🔄 Reliability Agent: Job Reliability Dashboard

### Purpose
Monitor job execution health, failures, and reliability trends.

### Agent Domain: 🔄 Reliability

### Inspired by: Jobs System Tables Dashboard, Workflow Advisor Dashboard

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_job_run_timeline`
- `${catalog}.${gold_schema}.dim_job`
- `${catalog}.${gold_schema}.dim_cluster`

**References:**
- [Microsoft Learn - Job Run Timeline Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs#detailed-schema-reference)
- [GitHub - Workflow Advisor](https://github.com/yati1002/Workflowadvisor)

### Widget Queries

#### Job Success Rate Trend (Line Chart)
```sql
SELECT 
    DATE(period_start_time) AS run_date,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful_runs,
    ROUND(SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) * 100.0 / 
          NULLIF(COUNT(*), 0), 1) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND result_state IS NOT NULL
GROUP BY DATE(period_start_time)
ORDER BY run_date
```

#### Daily Job Count by Result State (Stacked Bar) - From MS Learn
```sql
SELECT
    workspace_id,
    COUNT(DISTINCT run_id) AS job_count,
    result_state,
    TO_DATE(period_start_time) AS date
FROM system.lakeflow.job_run_timeline
WHERE period_start_time > CURRENT_TIMESTAMP() - INTERVAL 7 DAYS
    AND result_state IS NOT NULL
GROUP BY ALL
ORDER BY date, result_state
```

#### Jobs with Most Retries (Table) - From MS Learn
```sql
WITH repaired_runs AS (
    SELECT
        workspace_id, job_id, run_id, 
        COUNT(*) - 1 AS retries_count
    FROM system.lakeflow.job_run_timeline
    WHERE result_state IS NOT NULL
    GROUP BY ALL
    HAVING retries_count > 0
)
SELECT
    j.name AS job_name,
    r.workspace_id,
    r.job_id,
    r.run_id,
    r.retries_count
FROM repaired_runs r
LEFT JOIN system.lakeflow.jobs j USING (workspace_id, job_id)
WHERE j.change_time = (SELECT MAX(change_time) FROM system.lakeflow.jobs j2 WHERE j2.job_id = j.job_id)
ORDER BY retries_count DESC
LIMIT 20
```

#### Failed Jobs Today (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_failed_jobs(
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        'ALL'
    )
)
LIMIT 25
```

#### Jobs with Lowest Success Rate (Bar Chart)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_job_success_rate(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        10
    )
)
WHERE success_rate < 95
ORDER BY success_rate ASC
LIMIT 10
```

#### Most Expensive Jobs (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_most_expensive_jobs(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        15
    )
)
```

#### Job Duration Percentiles (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_job_duration_percentiles('ALL', 30)
)
LIMIT 20
```

#### Failure Distribution by Termination Code (Pie Chart)
```sql
SELECT 
    COALESCE(termination_code, 'UNKNOWN') AS termination_code,
    COUNT(*) AS failure_count
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE result_state IN ('FAILED', 'ERROR', 'TIMED_OUT')
    AND period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY termination_code
ORDER BY failure_count DESC
LIMIT 10
```

#### Job Repair Costs (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_job_repair_costs(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 30 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        15
    )
)
```

#### 📊 Most Retried Jobs with Cost - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: most_retry_jobs_30_days
-- Critical for identifying instable jobs that cost money through retries
WITH job_run_timeline_with_cost AS (
    SELECT
        t1.*,
        t2.job_id,
        t2.run_id,
        t1.identity_metadata.run_as AS run_as,
        t2.result_state,
        t1.list_costs.pricing.default AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.lakeflow.job_run_timeline t2
        ON t1.workspace_id = t2.workspace_id
        AND t1.usage_metadata.job_id = t2.job_id
        AND t1.usage_metadata.job_run_id = t2.run_id
        AND t1.usage_start_time >= date_trunc("Hour", t2.period_start_time)
        AND t1.usage_start_time < date_trunc("Hour", t2.period_end_time) + INTERVAL 1 HOUR
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
    WHERE t1.sku_name LIKE '%JOBS%' 
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
repaired_runs AS (
    SELECT workspace_id, job_id, run_id, COUNT(*) AS cnt
    FROM system.lakeflow.job_run_timeline
    WHERE result_state IS NOT NULL
    GROUP BY ALL
    HAVING cnt > 1
),
cost_per_unsuccessful AS (
    SELECT workspace_id, job_id, run_id, FIRST(run_as, TRUE) AS run_as, SUM(list_cost) AS list_cost
    FROM (
        SELECT workspace_id, job_id, run_id, run_as, 
               list_cost - COALESCE(LAG(list_cost) OVER (ORDER BY workspace_id, job_id, run_id, usage_end_time), 0) AS list_cost,
               result_state
        FROM (
            SELECT workspace_id, job_id, run_id, run_as, usage_end_time, result_state,
                   SUM(list_cost) OVER (ORDER BY workspace_id, job_id, run_id, usage_end_time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS list_cost
            FROM job_run_timeline_with_cost
        )
        WHERE result_state IS NOT NULL
    )
    WHERE result_state != 'SUCCEEDED'
    GROUP BY ALL
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT
    FIRST(t3.name) AS job_name,
    t1.workspace_id,
    t1.job_id,
    t1.run_id,
    FIRST(t4.run_as) AS run_as,
    FIRST(t1.cnt) - 1 AS repairs,
    ROUND(FIRST(t4.list_cost), 2) AS repair_list_cost
FROM repaired_runs t1
JOIN system.lakeflow.job_run_timeline t2 USING (workspace_id, job_id, run_id)
LEFT JOIN most_recent_jobs t3 USING (workspace_id, job_id)
LEFT JOIN cost_per_unsuccessful t4 USING (workspace_id, job_id, run_id)
WHERE t2.result_state IS NOT NULL
GROUP BY t1.workspace_id, t1.job_id, t1.run_id
ORDER BY repairs DESC
LIMIT 20
```

#### 📊 Highest Failure Jobs with Cost - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: highest_failure_jobs_30_days
WITH terminal_statuses AS (
    SELECT
        workspace_id,
        job_id,
        CASE WHEN result_state IN ('ERROR', 'FAILED', 'TIMED_OUT') THEN 1 ELSE 0 END AS is_failure,
        period_end_time AS last_seen_date
    FROM system.lakeflow.job_run_timeline
    WHERE result_state IS NOT NULL
        AND period_end_time >= CURRENT_DATE() - INTERVAL 30 DAYS
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT
    FIRST(t2.name) AS job_name,
    t1.workspace_id,
    t1.job_id,
    COUNT(*) AS runs,
    SUM(is_failure) AS failures,
    ROUND((1 - COALESCE(try_divide(SUM(is_failure), COUNT(*)), 0)) * 100, 1) AS success_ratio,
    MAX(t1.last_seen_date) AS last_seen
FROM terminal_statuses t1
LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
GROUP BY ALL
HAVING failures > 0
ORDER BY failures DESC
LIMIT 20
```

---

## 💰🔄 Cost + Reliability Agents: Job Optimization Dashboard (NEW)

### Purpose
Identify job optimization opportunities - stale datasets, autoscaling, compute right-sizing.

### Agent Domains: 💰 Cost, 🔄 Reliability

### Inspired by: Jobs System Tables Dashboard - Advanced Patterns

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_job_run_timeline`
- `${catalog}.${gold_schema}.fact_usage`
- `${catalog}.${gold_schema}.fact_table_lineage`
- `${catalog}.${gold_schema}.dim_job`
- `${catalog}.${gold_schema}.dim_cluster`

### Widget Queries

#### 📊 Jobs Producing Stale (Unused) Datasets - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: jobs_stale_datasets
-- Identifies jobs producing datasets that are never consumed downstream
WITH producers AS (
    SELECT workspace_id, entity_id AS job_id, target_table_full_name, created_by
    FROM system.access.table_lineage
    WHERE entity_type = 'JOB' 
        AND target_table_full_name IS NOT NULL
        AND event_date > CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY ALL
),
consumers AS (
    SELECT workspace_id, source_table_full_name
    FROM system.access.table_lineage
    WHERE source_table_full_name IS NOT NULL 
        AND event_date > CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY ALL
),
jobs_without_consumption AS (
    SELECT t1.*
    FROM producers t1
    LEFT OUTER JOIN consumers t2
        ON t1.target_table_full_name = t2.source_table_full_name 
        AND t1.workspace_id = t2.workspace_id
    WHERE t2.source_table_full_name IS NULL
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT 
    t1.workspace_id,
    t5.name AS job_name,
    t1.job_id,
    collect_set(target_table_full_name) AS not_used_datasets,
    COUNT(DISTINCT t2.run_id) AS runs_30d
FROM jobs_without_consumption t1
LEFT JOIN system.lakeflow.job_run_timeline t2 USING (workspace_id, job_id)
LEFT JOIN most_recent_jobs t5 USING (workspace_id, job_id)
WHERE t2.period_end_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY ALL
HAVING runs_30d > 0
ORDER BY runs_30d DESC
LIMIT 25
```

#### 📊 Jobs Without Autoscaling - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: job_no_scaling
-- Jobs with static worker counts that could benefit from autoscaling
WITH clusters AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, cluster_id ORDER BY change_time DESC) AS rn
    FROM system.compute.clusters
    WHERE cluster_source = 'JOB'
    QUALIFY rn = 1
),
job_cluster_costs AS (
    SELECT
        t1.workspace_id,
        t1.usage_metadata.job_id,
        t1.usage_metadata.cluster_id,
        SUM(t1.list_costs.pricing.default) AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
    WHERE t1.sku_name LIKE '%JOBS%'
        AND t1.sku_name NOT LIKE '%SERVERLESS'
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_metadata.cluster_id IS NOT NULL
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY ALL
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT
    c.workspace_id,
    j.job_id,
    FIRST(mr.name) AS job_name,
    FIRST(mr.run_as) AS run_as,
    ROUND(SUM(j.list_cost), 2) AS list_cost_30d,
    FIRST(c.worker_count) AS worker_count,
    FIRST(c.min_autoscale_workers) AS min_autoscale,
    FIRST(c.max_autoscale_workers) AS max_autoscale
FROM clusters c
JOIN job_cluster_costs j USING (workspace_id, cluster_id)
LEFT JOIN most_recent_jobs mr USING (workspace_id, job_id)
WHERE (c.min_autoscale_workers IS NULL OR c.max_autoscale_workers IS NULL)
    AND c.worker_count > 1
GROUP BY c.workspace_id, j.job_id
ORDER BY list_cost_30d DESC
LIMIT 20
```

#### 📊 Jobs Using All-Purpose Clusters - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: jobs_ap_clusters
-- Jobs incorrectly running on interactive/all-purpose clusters instead of job clusters
WITH clusters AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, cluster_id ORDER BY change_time DESC) AS rn
    FROM system.compute.clusters
    WHERE cluster_source = 'UI'  -- All-purpose clusters
    QUALIFY rn = 1
),
job_tasks_on_ap AS (
    SELECT
        jtr.workspace_id,
        jtr.job_id,
        EXPLODE(jtr.compute_ids) AS cluster_id
    FROM system.lakeflow.job_task_run_timeline jtr
    WHERE jtr.period_start_time >= CURRENT_DATE() - INTERVAL 30 DAY
),
ap_cluster_jobs AS (
    SELECT t1.*, t2.cluster_name, t2.owned_by, t2.dbr_version
    FROM job_tasks_on_ap t1
    INNER JOIN clusters t2 USING (workspace_id, cluster_id)
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT 
    t1.workspace_id,
    t1.job_id,
    FIRST(t2.name, TRUE) AS job_name,
    array_size(collect_list(t1.cluster_id)) AS task_runs_on_ap,
    collect_set(named_struct('cluster_id', t1.cluster_id, 'cluster_name', t1.cluster_name)) AS ap_clusters_used
FROM ap_cluster_jobs t1
LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
GROUP BY t1.workspace_id, t1.job_id
ORDER BY task_runs_on_ap DESC
LIMIT 25
```

#### 📊 Outlier Job Runs (P90 Cost Deviation) - From Jobs System Tables Dashboard
```sql
-- Pattern from Jobs System Tables Dashboard: outlier_job_runs_30_days
-- Identifies jobs with runs that significantly exceed their typical cost
WITH stats_per_job_run AS (
    SELECT
        t1.workspace_id,
        t1.usage_metadata.job_id,
        t1.usage_metadata.job_run_id AS run_id,
        SUM(t1.list_costs.pricing.default) AS list_cost,
        FIRST(identity_metadata.run_as, TRUE) AS run_as,
        MIN(t1.usage_start_time) AS first_seen
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
    WHERE t1.sku_name LIKE '%JOBS%'
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_metadata.job_run_id IS NOT NULL
        AND t1.usage_start_time >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY 1, 2, 3
),
stats_per_job AS (
    SELECT
        workspace_id,
        job_id,
        COUNT(run_id) AS runs,
        SUM(list_cost) AS total_list_cost,
        AVG(list_cost) AS avg_list_cost,
        MAX(list_cost) AS max_list_cost,
        percentile(list_cost, 0.9) AS p90
    FROM stats_per_job_run
    WHERE first_seen > CURRENT_TIMESTAMP() - INTERVAL 30 DAYS
    GROUP BY ALL
),
most_recent_jobs AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs QUALIFY rn = 1
)
SELECT
    t1.workspace_id,
    t2.name AS job_name,
    t1.job_id,
    t1.runs,
    ROUND(t1.avg_list_cost, 2) AS avg_cost,
    ROUND(t1.p90, 2) AS p90_cost,
    ROUND(t1.max_list_cost, 2) AS max_cost,
    ROUND(t1.max_list_cost - t1.p90, 2) AS cost_deviation_from_p90
FROM stats_per_job t1
LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
ORDER BY cost_deviation_from_p90 DESC
LIMIT 20
```

---

## ⚡ Performance Agent: Query Performance Dashboard (DBSQL Warehouse Advisor)

### Purpose
Monitor SQL Warehouse query performance, efficiency, and identify optimization opportunities.

### Agent Domain: ⚡ Performance

### Inspired by: DBSQL Warehouse Advisor Dashboard v5

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_query_history`
- `${catalog}.${gold_schema}.dim_warehouse`

**Key Metrics from DBSQL Warehouse Advisor:**
- **Query Efficiency Ratio** - CPU time vs runtime to detect task skew
- **Performance Flags** - HighDataVolumeFlag, HighQueueingTimeFlag, HighResultFetchTimeFlag
- **Cost Allocation** - Proportional cost by query using warehouse time ratios
- **Queue Time Analysis** - Queue proportion thresholds for detecting contention

### Widget Queries

#### Query Volume Trend (Line Chart)
```sql
SELECT 
    DATE(start_time) AS query_date,
    COUNT(*) AS query_count,
    AVG(total_duration_ms / 1000) AS avg_duration_sec
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE(start_time)
ORDER BY query_date
```

#### 📊 Query Efficiency Analysis with Performance Flags - From DBSQL Warehouse Advisor v5
```sql
-- Pattern from DBSQL Warehouse Advisor: Query History With Ratios
-- Calculates efficiency metrics and performance flags for each query
WITH warehouse_average_ratio_metrics AS (
    SELECT 
        warehouse_id,
        COALESCE(AVG(CAST(cpu_total_execution_time AS FLOAT)) / AVG(CAST(query_runtime_seconds AS FLOAT)), 0) AS warehouse_avg_task_skew_ratio
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE cpu_total_execution_time > 0 
        AND read_data_gb > 0
        AND execution_status NOT IN ('FAILED')
        AND start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY warehouse_id
),
query_with_efficiency AS (
    SELECT 
        qh.*,
        w.warehouse_avg_task_skew_ratio,
        CASE 
            WHEN qh.cpu_total_execution_time > 0 
            AND qh.read_data_gb > 0 
            AND qh.execution_status NOT IN ('FAILED')
            THEN qh.query_runtime_seconds / (qh.cpu_total_execution_time / w.warehouse_avg_task_skew_ratio)
            ELSE NULL
        END AS query_efficiency_ratio
    FROM ${catalog}.${gold_schema}.fact_query_history qh
    LEFT JOIN warehouse_average_ratio_metrics w ON w.warehouse_id = qh.warehouse_id
    WHERE qh.start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT 
    warehouse_name,
    statement_id,
    query_runtime_seconds,
    ROUND(query_efficiency_ratio, 2) AS efficiency_ratio,
    -- Performance Flags
    CASE WHEN read_data_gb > 10 THEN 'High Volume Read' ELSE 'OK' END AS data_volume_flag,
    CASE WHEN (waiting_at_capacity_ms / total_duration_ms) > 0.1 THEN 'High Queue Time' ELSE 'OK' END AS queue_flag,
    CASE WHEN (result_fetch_time_ms / total_duration_ms) > 0.1 THEN 'High Result Fetch' ELSE 'OK' END AS result_fetch_flag,
    CASE WHEN spilled_data_gb > 0 THEN 'Spilling' ELSE 'OK' END AS spill_flag
FROM query_with_efficiency qe
LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse dw ON qe.warehouse_id = dw.warehouse_id
ORDER BY query_runtime_seconds DESC
LIMIT 50
```

#### 📊 Queue Time Distribution by Warehouse (Heatmap) - From DBSQL Warehouse Advisor
```sql
-- Pattern from DBSQL Warehouse Advisor: Queue Time Analysis
SELECT 
    dw.warehouse_name,
    CASE 
        WHEN (waiting_at_capacity_ms / NULLIF(total_duration_ms, 0)) > 1 THEN 100
        ELSE ROUND((waiting_at_capacity_ms / NULLIF(total_duration_ms, 0)) * 100, 0)
    END AS queue_pct_bucket,
    COUNT(*) AS query_count
FROM ${catalog}.${gold_schema}.fact_query_history qh
LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse dw ON qh.warehouse_id = dw.warehouse_id AND dw.is_current = TRUE
WHERE qh.start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY dw.warehouse_name, 2
ORDER BY warehouse_name, queue_pct_bucket
```

#### 📊 Cost Allocation by Query Source (Table) - From DBSQL Warehouse Advisor
```sql
-- Pattern from DBSQL Warehouse Advisor: Cost by Query Source
SELECT 
    query_source_type,
    COUNT(*) AS query_count,
    ROUND(SUM(query_runtime_seconds) / 3600, 2) AS total_hours,
    ROUND(AVG(query_runtime_seconds), 2) AS avg_duration_sec,
    ROUND(SUM(read_data_gb), 2) AS total_data_read_gb
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY query_source_type
ORDER BY total_hours DESC
```

#### Warehouse Utilization (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_warehouse_utilization(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        'ALL'
    )
)
```

#### Slow Queries (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_slow_queries(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 1 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        300  -- 5 minutes threshold
    )
)
LIMIT 25
```

#### Query Duration Distribution (Histogram)
```sql
SELECT 
    CASE 
        WHEN total_duration_ms < 1000 THEN '< 1s'
        WHEN total_duration_ms < 5000 THEN '1-5s'
        WHEN total_duration_ms < 30000 THEN '5-30s'
        WHEN total_duration_ms < 60000 THEN '30-60s'
        WHEN total_duration_ms < 300000 THEN '1-5min'
        ELSE '> 5min'
    END AS duration_bucket,
    COUNT(*) AS query_count
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY 1
ORDER BY 
    CASE duration_bucket
        WHEN '< 1s' THEN 1
        WHEN '1-5s' THEN 2
        WHEN '5-30s' THEN 3
        WHEN '30-60s' THEN 4
        WHEN '1-5min' THEN 5
        ELSE 6
    END
```

#### Queue Time Analysis (Bar Chart)
```sql
SELECT 
    w.warehouse_name,
    ROUND(AVG(qh.waiting_at_capacity_duration_ms / 1000), 1) AS avg_queue_sec,
    ROUND(MAX(qh.waiting_at_capacity_duration_ms / 1000), 1) AS max_queue_sec,
    ROUND(AVG(qh.waiting_at_capacity_duration_ms) * 100.0 / 
          NULLIF(AVG(qh.total_duration_ms), 0), 1) AS queue_pct
FROM ${catalog}.${gold_schema}.fact_query_history qh
LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w 
    ON qh.warehouse_id = w.warehouse_id AND w.is_current = TRUE
WHERE qh.start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY w.warehouse_name
HAVING AVG(qh.waiting_at_capacity_duration_ms) > 0
ORDER BY queue_pct DESC
```

---

## ⚡💰 Performance + Cost Agents: Cluster Utilization Dashboard

### Purpose
Monitor cluster resource utilization for right-sizing and cost optimization.

### Agent Domains: ⚡ Performance, 💰 Cost

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_node_timeline`
- `${catalog}.${gold_schema}.fact_usage`
- `${catalog}.${gold_schema}.dim_cluster`

**References:**
- [Microsoft Learn - Compute Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute#sample-queries)
- [GitHub - Table Health Advisor](https://github.com/CodyAustinDavis/dbsql_sme/tree/main/Observability%20Dashboards%20and%20DBA%20Resources/Observability%20Lakeview%20Dashboard%20Templates/Table%20Health%20Advisor)

### Widget Queries

#### Cluster Utilization Summary (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_cluster_utilization(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        10
    )
)
```

#### Cluster Resource Metrics (Table) - From MS Learn Pattern
```sql
SELECT
    DISTINCT cluster_id,
    driver,
    ROUND(AVG(cpu_user_percent + cpu_system_percent), 1) AS `Avg CPU Utilization`,
    ROUND(MAX(cpu_user_percent + cpu_system_percent), 1) AS `Peak CPU Utilization`,
    ROUND(AVG(cpu_wait_percent), 1) AS `Avg CPU Wait`,
    ROUND(MAX(cpu_wait_percent), 1) AS `Max CPU Wait`,
    ROUND(AVG(mem_used_percent), 1) AS `Avg Memory Utilization`,
    ROUND(MAX(mem_used_percent), 1) AS `Max Memory Utilization`,
    ROUND(AVG(network_received_bytes)/(1024*1024), 2) AS `Avg Network MB Received/Min`,
    ROUND(AVG(network_sent_bytes)/(1024*1024), 2) AS `Avg Network MB Sent/Min`
FROM system.compute.node_timeline
WHERE start_time >= date_add(now(), -7)
GROUP BY cluster_id, driver
ORDER BY `Avg CPU Utilization` DESC
LIMIT 20
```

#### CPU Utilization Distribution (Box Plot)
```sql
SELECT 
    c.cluster_name,
    AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu,
    PERCENTILE(nt.cpu_user_percent + nt.cpu_system_percent, 0.25) AS p25_cpu,
    PERCENTILE(nt.cpu_user_percent + nt.cpu_system_percent, 0.50) AS median_cpu,
    PERCENTILE(nt.cpu_user_percent + nt.cpu_system_percent, 0.75) AS p75_cpu,
    PERCENTILE(nt.cpu_user_percent + nt.cpu_system_percent, 0.95) AS p95_cpu
FROM ${catalog}.${gold_schema}.fact_node_timeline nt
LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c 
    ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
WHERE nt.start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY c.cluster_name
ORDER BY avg_cpu DESC
LIMIT 15
```

#### Underutilized Clusters (Table)
```sql
SELECT 
    c.cluster_id,
    c.cluster_name,
    c.owned_by,
    ROUND(AVG(nt.cpu_user_percent + nt.cpu_system_percent), 1) AS avg_cpu_pct,
    ROUND(AVG(nt.mem_used_percent), 1) AS avg_mem_pct,
    SUM(TIMESTAMPDIFF(HOUR, nt.start_time, nt.end_time)) AS total_hours,
    ROUND(u.total_cost, 2) AS total_cost
FROM ${catalog}.${gold_schema}.fact_node_timeline nt
LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c 
    ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
LEFT JOIN (
    SELECT cluster_id, SUM(list_cost) AS total_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY cluster_id
) u ON c.cluster_id = u.cluster_id
WHERE nt.start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY c.cluster_id, c.cluster_name, c.owned_by, u.total_cost
HAVING AVG(nt.cpu_user_percent + nt.cpu_system_percent) < 30
ORDER BY total_cost DESC
LIMIT 20
```

---

## 🔒 Security Agent: Security & Audit Dashboard

### Purpose
Monitor data access patterns and security compliance.

### Agent Domain: 🔒 Security

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_table_lineage`
- `${catalog}.${gold_schema}.dim_workspace`

### Widget Queries

#### User Activity Summary (Table)
```sql
SELECT 
    created_by AS user,
    COUNT(*) AS total_events,
    SUM(CASE WHEN source_table_full_name IS NOT NULL THEN 1 ELSE 0 END) AS read_ops,
    SUM(CASE WHEN target_table_full_name IS NOT NULL THEN 1 ELSE 0 END) AS write_ops,
    COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name)) AS tables_accessed,
    MAX(event_time) AS last_activity
FROM ${catalog}.${gold_schema}.fact_table_lineage
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY created_by
ORDER BY total_events DESC
LIMIT 25
```

#### Most Accessed Tables (Bar Chart)
```sql
SELECT 
    COALESCE(source_table_full_name, target_table_full_name) AS table_name,
    COUNT(*) AS access_count,
    COUNT(DISTINCT created_by) AS unique_users
FROM ${catalog}.${gold_schema}.fact_table_lineage
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY 1
ORDER BY access_count DESC
LIMIT 15
```

#### Sensitive Table Access (Table)
```sql
SELECT * FROM TABLE(
    ${catalog}.${gold_schema}.get_sensitive_table_access(
        DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
        DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
        '%PII%'
    )
)
```

---

## ✅ Quality Agent: Table Health Advisor Dashboard

### Purpose
Monitor Delta table health, optimization status, and storage patterns.

### Agent Domain: ✅ Quality

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_data_quality_monitoring_table_results`
- Information schema views (system.storage.table_files)

**Inspired by:** [GitHub - Table Health Advisor](https://github.com/CodyAustinDavis/dbsql_sme/tree/main/Observability%20Dashboards%20and%20DBA%20Resources/Observability%20Lakeview%20Dashboard%20Templates/Table%20Health%20Advisor)

### Widget Queries

#### Table Size and File Distribution (Table)
```sql
SELECT
    table_catalog,
    table_schema,
    table_name,
    ROUND(SUM(size_in_bytes) / (1024*1024*1024), 2) AS size_gb,
    COUNT(*) AS num_files,
    ROUND(AVG(size_in_bytes) / (1024*1024), 2) AS avg_file_size_mb,
    MIN(modification_time) AS oldest_file,
    MAX(modification_time) AS newest_file
FROM system.storage.table_files
GROUP BY table_catalog, table_schema, table_name
ORDER BY size_gb DESC
LIMIT 50
```

#### Tables Needing Optimization (Table)
```sql
WITH table_stats AS (
    SELECT
        table_catalog,
        table_schema,
        table_name,
        SUM(size_in_bytes) AS total_bytes,
        COUNT(*) AS num_files,
        AVG(size_in_bytes) AS avg_file_size
    FROM system.storage.table_files
    GROUP BY ALL
)
SELECT
    table_catalog,
    table_schema,
    table_name,
    ROUND(total_bytes / (1024*1024*1024), 2) AS size_gb,
    num_files,
    ROUND(avg_file_size / (1024*1024), 2) AS avg_file_mb,
    CASE
        WHEN num_files > 1000 AND avg_file_size < 32*1024*1024 THEN 'NEEDS_COMPACTION'
        WHEN num_files > 100 AND avg_file_size < 16*1024*1024 THEN 'CONSIDER_COMPACTION'
        ELSE 'OK'
    END AS optimization_status
FROM table_stats
WHERE num_files > 50
ORDER BY num_files DESC
LIMIT 50
```

#### Recent Table Operations (Table)
```sql
SELECT
    table_catalog,
    table_schema,
    table_name,
    operation,
    operation_parameters,
    timestamp,
    operation_metrics
FROM system.information_schema.table_history
WHERE timestamp >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY timestamp DESC
LIMIT 100
```

---

## Deployment Configuration

```yaml
resources:
  jobs:
    dashboard_setup_job:
      name: "[${bundle.target}] Health Monitor - Dashboard Setup"
      
      tasks:
        - task_key: deploy_executive_dashboard
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/dashboards/executive_overview.sql
        
        - task_key: deploy_cost_dashboard
          depends_on: [deploy_executive_dashboard]
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/dashboards/cost_management.sql
        
        - task_key: deploy_reliability_dashboard
          depends_on: [deploy_cost_dashboard]
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/dashboards/job_reliability.sql
```

---

## ⚡ Performance Agent: DBR Migration & Compute Modernization Dashboard (NEW)

### Purpose
Track Databricks Runtime version adoption and identify workloads on legacy runtimes.

### Agent Domain: ⚡ Performance

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_job_run_timeline`
- `${catalog}.${gold_schema}.fact_usage`
- `${catalog}.${gold_schema}.dim_cluster`
- `${catalog}.${gold_schema}.dim_job`

### Inspired by: DBR Upgrade Managed Migration Dashboard

### Widget Queries

#### KPI: Jobs on Legacy DBR (<15)
```sql
-- Pattern from DBR_Upgrade_Managed_Migration_Complete dashboard
WITH latest_clusters AS (
    SELECT workspace_id, cluster_id, MAX_BY(dbr_version, change_time) AS dbr_version
    FROM system.compute.clusters
    WHERE delete_time IS NULL
    GROUP BY workspace_id, cluster_id
),
job_runs AS (
    SELECT DISTINCT jtr.job_id
    FROM system.lakeflow.job_task_run_timeline jtr
    CROSS JOIN LATERAL explode(jtr.compute_ids) AS t(cluster_id)
    INNER JOIN latest_clusters lc ON jtr.workspace_id = lc.workspace_id AND t.cluster_id = lc.cluster_id
    WHERE DATE(jtr.period_start_time) >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND CAST(regexp_extract(COALESCE(lc.dbr_version, '0'), '^(\\d+)', 1) AS INT) < 15
)
SELECT COUNT(DISTINCT job_id) AS legacy_job_count FROM job_runs
```

#### DBR Version Distribution (Pie Chart)
```sql
-- Pattern from DBR_Upgrade_Managed_Migration_Complete dashboard: DBR distribution
WITH latest_clusters AS (
    SELECT workspace_id, cluster_id,
           MAX_BY(dbr_version, change_time) AS dbr_version_raw,
           REGEXP_EXTRACT(LOWER(MAX_BY(dbr_version, change_time)), '(\\d+\\.\\d+)') AS dbr_core
    FROM system.compute.clusters
    WHERE delete_time IS NULL
    GROUP BY workspace_id, cluster_id
),
job_runs AS (
    SELECT lc.dbr_core
    FROM system.lakeflow.job_task_run_timeline jtr
    CROSS JOIN LATERAL EXPLODE(jtr.compute_ids) AS t(cluster_id)
    INNER JOIN latest_clusters lc ON jtr.workspace_id = lc.workspace_id AND t.cluster_id = lc.cluster_id
    WHERE DATE(jtr.period_start_time) >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND lc.dbr_core IS NOT NULL
)
SELECT 
    dbr_core AS dbr_version,
    COUNT(*) AS job_runs,
    CASE 
        WHEN CAST(SPLIT(dbr_core, '\\.')[0] AS INT) >= 15 THEN 'Current'
        WHEN CAST(SPLIT(dbr_core, '\\.')[0] AS INT) >= 13 THEN 'LTS'
        ELSE 'Legacy'
    END AS version_status
FROM job_runs
GROUP BY dbr_core
ORDER BY dbr_core DESC
```

#### Jobs on Legacy Runtime (Table)
```sql
-- Pattern from DBR_Upgrade_Managed_Migration_Complete dashboard: kpi_legacy_jobs
WITH latest_jobs AS (
    SELECT workspace_id, job_id, name,
           ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
    FROM system.lakeflow.jobs
    WHERE delete_time IS NULL
    QUALIFY rn = 1
),
latest_clusters AS (
    SELECT workspace_id, cluster_id, MAX_BY(dbr_version, change_time) AS dbr_version
    FROM system.compute.clusters
    WHERE delete_time IS NULL
    GROUP BY workspace_id, cluster_id
),
legacy_jobs AS (
    SELECT DISTINCT 
        jtr.workspace_id,
        jtr.job_id,
        lc.dbr_version,
        CAST(regexp_extract(COALESCE(lc.dbr_version, '0'), '^(\\d+)', 1) AS INT) AS dbr_major
    FROM system.lakeflow.job_task_run_timeline jtr
    CROSS JOIN LATERAL explode(jtr.compute_ids) AS t(cluster_id)
    INNER JOIN latest_clusters lc ON jtr.workspace_id = lc.workspace_id AND t.cluster_id = lc.cluster_id
    LEFT JOIN latest_jobs lj ON jtr.workspace_id = lj.workspace_id AND jtr.job_id = lj.job_id
    WHERE DATE(jtr.period_start_time) >= CURRENT_DATE() - INTERVAL 30 DAYS
        AND CAST(regexp_extract(COALESCE(lc.dbr_version, '0'), '^(\\d+)', 1) AS INT) < 15
)
SELECT 
    lj.workspace_id,
    mrj.name AS job_name,
    lj.job_id,
    lj.dbr_version,
    lj.dbr_major
FROM legacy_jobs lj
LEFT JOIN latest_jobs mrj ON lj.workspace_id = mrj.workspace_id AND lj.job_id = mrj.job_id
ORDER BY dbr_major ASC, job_name
LIMIT 50
```

#### Serverless Adoption Progress (Counter)
```sql
-- Track serverless adoption for cost optimization
WITH job_compute AS (
    SELECT
        workspace_id,
        job_id,
        CASE 
            WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
            ELSE 'Classic'
        END AS compute_type,
        SUM(list_costs.pricing.default) AS list_cost
    FROM system.billing.usage t1
    INNER JOIN system.billing.list_prices list_prices 
        ON t1.cloud = list_prices.cloud 
        AND t1.sku_name = list_prices.sku_name
    WHERE t1.sku_name LIKE '%JOBS%'
        AND t1.usage_metadata.job_id IS NOT NULL
        AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAY
    GROUP BY ALL
)
SELECT 
    compute_type,
    COUNT(DISTINCT job_id) AS job_count,
    ROUND(SUM(list_cost), 2) AS total_cost,
    ROUND(COUNT(DISTINCT job_id) * 100.0 / SUM(COUNT(DISTINCT job_id)) OVER (), 1) AS pct_of_jobs
FROM job_compute
GROUP BY compute_type
ORDER BY job_count DESC
```

---

## 🔒 Governance Agent: Data Governance Hub Dashboard (NEW)

### Purpose
Comprehensive data governance dashboard tracking asset usage, tag coverage, lineage, and documentation completeness. Inspired by [SYSTEM GENERATED] GOVERNANCE HUB SYSTEM DASHBOARD 1.0.5.

### Agent Domain: 🔒 Security/Governance

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_table_lineage`
- `${catalog}.${gold_schema}.fact_column_lineage`
- `${catalog}.information_schema.tables`
- `${catalog}.information_schema.columns`

### Key Visualizations

| Visualization | Type | Description |
|---------------|------|-------------|
| **Entity Counts** | KPI Cards | Catalogs, Schemas, Tables, Columns |
| **Active/Inactive Tables** | Donut | Tables with activity vs idle (30 days) |
| **Read/Write Activity Trend** | Line | Table access patterns over time |
| **Top Users by Table Access** | Bar | Users with most table interactions |
| **Tag Coverage Matrix** | Heatmap | Tag compliance by schema/catalog |
| **Tables Without Comments** | Table | Data quality gap identification |
| **Lineage Depth** | Tree/Table | Multi-level lineage tracking |
| **Popular Columns** | Table | Most frequently accessed columns |
| **Inactive Tables** | Table | Tables not accessed in 30+ days |

### Widget Queries

#### Active vs Inactive Tables (Donut)
```sql
-- Pattern from Governance Hub: Active/inactive tables
WITH table_activity AS (
    SELECT DISTINCT
        COALESCE(source_table_full_name, target_table_full_name) AS table_full_name
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
all_tables AS (
    SELECT CONCAT(table_catalog, '.', table_schema, '.', table_name) AS table_full_name
    FROM ${catalog}.information_schema.tables
    WHERE table_type = 'MANAGED'
)
SELECT
    CASE WHEN ta.table_full_name IS NOT NULL THEN 'Active' ELSE 'Inactive' END AS status,
    COUNT(*) AS table_count
FROM all_tables at
LEFT JOIN table_activity ta ON at.table_full_name = ta.table_full_name
GROUP BY 1
```

#### Top Queried Tables Without Comments
```sql
-- Pattern from Governance Hub: Top queried tables without comments
WITH table_usage AS (
    SELECT
        COALESCE(source_table_full_name, target_table_full_name) AS table_full_name,
        COUNT(*) AS access_count
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY 1
),
table_comments AS (
    SELECT
        CONCAT(table_catalog, '.', table_schema, '.', table_name) AS table_full_name,
        COALESCE(comment, '') AS table_comment
    FROM ${catalog}.information_schema.tables
)
SELECT
    tu.table_full_name,
    tu.access_count,
    tc.table_comment
FROM table_usage tu
LEFT JOIN table_comments tc ON tu.table_full_name = tc.table_full_name
WHERE tc.table_comment = '' OR tc.table_comment IS NULL
ORDER BY tu.access_count DESC
LIMIT 25
```

#### Popular Columns by Access
```sql
-- Pattern from Governance Hub: Popular columns
SELECT
    source_table_full_name AS table_name,
    source_column_name AS column_name,
    COUNT(*) AS access_count,
    COUNT(DISTINCT created_by) AS unique_users
FROM ${catalog}.${gold_schema}.fact_column_lineage
WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND source_column_name IS NOT NULL
GROUP BY source_table_full_name, source_column_name
ORDER BY access_count DESC
LIMIT 50
```

#### Tag Coverage by Schema
```sql
-- Pattern from Governance Hub: Tag/untagged tables
WITH table_tags AS (
    SELECT
        table_catalog,
        table_schema,
        table_name,
        CASE WHEN t.tags IS NOT NULL AND cardinality(t.tags) > 0 THEN 1 ELSE 0 END AS is_tagged
    FROM ${catalog}.information_schema.tables t
    WHERE table_type = 'MANAGED'
)
SELECT
    table_schema,
    COUNT(*) AS total_tables,
    SUM(is_tagged) AS tagged_tables,
    ROUND(SUM(is_tagged) * 100.0 / NULLIF(COUNT(*), 0), 1) AS tag_coverage_pct
FROM table_tags
GROUP BY table_schema
ORDER BY tag_coverage_pct ASC
```

---

## 🔄 Reliability Agent: DLT Pipeline Monitoring Dashboard (NEW)

### Purpose
Monitor Delta Live Tables pipelines for reliability, freshness, and cost. Inspired by LakeFlow System Tables Dashboard v0.1.

### Agent Domain: 🔄 Reliability

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_pipeline_event`
- `${catalog}.${gold_schema}.dim_pipeline`
- `${catalog}.${gold_schema}.fact_usage`

### Key Visualizations

| Visualization | Type | Description |
|---------------|------|-------------|
| **Pipeline Status Summary** | KPI Cards | Active, Failed, Idle pipelines |
| **Pipeline Execution Timeline** | Gantt | Pipeline runs over time |
| **Cost by Pipeline** | Bar | DLT cost attribution |
| **Update Frequency** | Table | Pipeline update cadence analysis |
| **Failed Updates** | Table | Recent pipeline failures with errors |
| **Pipeline Data Freshness** | Table | Time since last successful update |

### Widget Queries

#### Pipeline Execution Summary
```sql
-- Pattern from LakeFlow Dashboard: Pipeline execution overview
SELECT
    p.pipeline_name,
    COUNT(*) AS total_updates,
    SUM(CASE WHEN pe.state = 'COMPLETED' THEN 1 ELSE 0 END) AS successful_updates,
    SUM(CASE WHEN pe.state = 'FAILED' THEN 1 ELSE 0 END) AS failed_updates,
    ROUND(SUM(CASE WHEN pe.state = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate,
    MAX(pe.event_time) AS last_update
FROM ${catalog}.${gold_schema}.fact_pipeline_event pe
LEFT JOIN ${catalog}.${gold_schema}.dim_pipeline p
    ON pe.pipeline_id = p.pipeline_id AND p.is_current = TRUE
WHERE pe.event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY p.pipeline_name
ORDER BY failed_updates DESC
```

#### Pipeline Cost Attribution
```sql
-- Pattern from LakeFlow Dashboard: Cost per pipeline
SELECT
    p.pipeline_name,
    SUM(u.list_cost) AS total_cost,
    SUM(u.usage_quantity) AS total_dbu,
    COUNT(DISTINCT DATE(u.usage_date)) AS active_days
FROM ${catalog}.${gold_schema}.fact_usage u
LEFT JOIN ${catalog}.${gold_schema}.dim_pipeline p
    ON u.usage_metadata_dlt_pipeline_id = p.pipeline_id AND p.is_current = TRUE
WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND u.usage_metadata_dlt_pipeline_id IS NOT NULL
GROUP BY p.pipeline_name
ORDER BY total_cost DESC
LIMIT 20
```

---

## 💰 Cost Agent: Period Comparison Dashboard (NEW)

### Purpose
Compare spending across periods (30 vs 60 days, WoW, MoM) for trend analysis and budget tracking. Inspired by azure-serverless-jobs-and-notebooks-cost-observability dashboard.

### Agent Domain: 💰 Cost

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_usage`
- `${catalog}.${gold_schema}.dim_workspace`

### Key Visualizations

| Visualization | Type | Description |
|---------------|------|-------------|
| **30 vs 60 Day Spend** | Bar Comparison | Period-over-period cost comparison |
| **WoW Growth by Entity** | Table | Week-over-week cost growth by job/user |
| **Cost Velocity** | Line | Daily run rate vs target |
| **Outlier Runs** | Table | Job runs exceeding P90 cost |
| **Highest Growth Entities** | Table | 7 vs 14 day cost growth analysis |

### Widget Queries

#### 30 vs 60 Day Spend Comparison
```sql
-- Pattern from Azure Serverless Cost Dashboard: 30_60_day_spend
SELECT
    'Last 30 Days' AS period,
    SUM(list_cost) AS total_cost,
    COUNT(DISTINCT workspace_id) AS workspaces,
    COUNT(DISTINCT usage_metadata_job_id) AS jobs
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN CURRENT_DATE() - INTERVAL 30 DAYS AND CURRENT_DATE()

UNION ALL

SELECT
    'Prior 30 Days' AS period,
    SUM(list_cost) AS total_cost,
    COUNT(DISTINCT workspace_id) AS workspaces,
    COUNT(DISTINCT usage_metadata_job_id) AS jobs
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS AND CURRENT_DATE() - INTERVAL 30 DAYS
```

#### Highest Growth Users (7 vs 14 Day)
```sql
-- Pattern from Azure Serverless Cost Dashboard: highest_change_users_7_14_days
SELECT
    identity_metadata_run_as AS user,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS last_7_days,
    SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS prior_7_days,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) -
    SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS growth_amount,
    ROUND(
        (SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) -
         SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END)) * 100.0 /
        NULLIF(SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END), 0), 1
    ) AS growth_pct
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
GROUP BY identity_metadata_run_as
HAVING prior_7_days > 0
ORDER BY growth_amount DESC
LIMIT 20
```

#### Highest Growth Notebooks (7 vs 14 Day)
```sql
-- Pattern from Azure Serverless Cost Dashboard: highest_change_notebooks_7_14_days
SELECT
    usage_metadata_notebook_id AS notebook_id,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS last_7_days,
    SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS prior_7_days,
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) -
    SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS growth_amount
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
    AND usage_metadata_notebook_id IS NOT NULL
GROUP BY usage_metadata_notebook_id
HAVING prior_7_days > 10  -- Filter out low-cost notebooks
ORDER BY growth_amount DESC
LIMIT 20
```

---

## ⚡ Performance Agent: Warehouse Scaling & Idle Analysis Dashboard (NEW)

### Purpose
Analyze SQL Warehouse scaling efficiency, idle time, and cost optimization opportunities. Inspired by DBSQL Warehouse Advisor v5 scaling patterns.

### Agent Domain: ⚡ Performance

**Gold Tables Used:**
- `${catalog}.${gold_schema}.fact_query_history`
- `${catalog}.${gold_schema}.fact_warehouse_events`
- `${catalog}.${gold_schema}.dim_warehouse`

### Key Visualizations

| Visualization | Type | Description |
|---------------|------|-------------|
| **Warehouse Idle Time** | Bar | Idle percentage by warehouse |
| **Cluster Scaling Events** | Timeline | Scale up/down events over time |
| **Queries Per Cluster** | Line | Query distribution across clusters |
| **Idle Cost Analysis** | Table | Cost of idle warehouse time |
| **Scaling Efficiency** | Gauge | Actual vs optimal cluster count |

### Widget Queries

#### Warehouse Idle Percentage
```sql
-- Pattern from DBSQL Warehouse Advisor: Warehouse idle percent
WITH warehouse_time AS (
    SELECT
        warehouse_id,
        SUM(TIMESTAMPDIFF(SECOND, start_time, end_time)) AS total_runtime_sec,
        SUM(CASE WHEN query_count = 0 THEN TIMESTAMPDIFF(SECOND, start_time, end_time) ELSE 0 END) AS idle_time_sec
    FROM ${catalog}.${gold_schema}.fact_warehouse_events
    WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY warehouse_id
)
SELECT
    dw.warehouse_name,
    wt.total_runtime_sec / 3600 AS total_hours,
    wt.idle_time_sec / 3600 AS idle_hours,
    ROUND(wt.idle_time_sec * 100.0 / NULLIF(wt.total_runtime_sec, 0), 1) AS idle_pct
FROM warehouse_time wt
LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse dw
    ON wt.warehouse_id = dw.warehouse_id AND dw.is_current = TRUE
ORDER BY idle_pct DESC
```

#### Cluster Scaling Over Time
```sql
-- Pattern from DBSQL Warehouse Advisor: Cluster Scaling
SELECT
    DATE_TRUNC('hour', event_time) AS hour,
    dw.warehouse_name,
    MAX(cluster_count) AS max_clusters,
    MIN(cluster_count) AS min_clusters,
    AVG(cluster_count) AS avg_clusters
FROM ${catalog}.${gold_schema}.fact_warehouse_events we
LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse dw
    ON we.warehouse_id = dw.warehouse_id AND dw.is_current = TRUE
WHERE we.event_time >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY DATE_TRUNC('hour', event_time), dw.warehouse_name
ORDER BY hour, warehouse_name
```

---

## Dashboard Summary

| Dashboard | Purpose | Key Widgets | Refresh |
|-----------|---------|-------------|---------|
| Executive Overview | Leadership view | 3 KPIs, cost trend, summary table | Daily |
| Cost Management | FinOps analysis | Top contributors, SKU breakdown, WoW, tag costs, growth analysis | Daily |
| Commit Tracking | Budget monitoring | Commit vs actual, ML forecast, variance alerts | Daily |
| Tag-Based Attribution | Chargeback | Cost by tag, tag coverage, untagged resources | Daily |
| Job Reliability | DevOps monitoring | Success rate, failures, duration, retries, failure costs | Hourly |
| **Job Optimization** | Cost savings | Stale datasets, autoscaling, AP clusters, outliers | Daily |
| Query Performance | DBA optimization | Slow queries, queue time, efficiency flags, cost allocation | Hourly |
| Cluster Utilization | Right-sizing | CPU/Mem util, network metrics, underutilized | Daily |
| Security & Audit | Compliance | User activity, table access, audit | Daily |
| Table Health Advisor | Storage optimization | Table sizes, file distribution, optimization needs | Daily |
| **DBR Migration** | Modernization | Legacy DBR jobs, version distribution, serverless adoption | Weekly |
| **Data Governance Hub (NEW)** | Governance | Asset usage, tag coverage, lineage, documentation | Daily |
| **DLT Pipeline Monitoring (NEW)** | Pipeline health | Pipeline status, failures, cost, freshness | Hourly |
| **Period Comparison (NEW)** | Trend analysis | 30/60 day compare, WoW growth, outliers | Daily |
| **Warehouse Scaling (NEW)** | Performance | Idle time, scaling events, cluster efficiency | Hourly |

---

## Success Criteria

| Criteria | Target |
|----------|--------|
| Dashboards Created | 9 dashboards |
| Widget Count | 65+ total widgets |
| TVF Usage | 80% of parameterized queries use TVFs |
| Metric View Usage | All KPIs reference metric views |
| Load Time | < 5 seconds per dashboard |
| Query Patterns | 30+ unique SQL patterns from system tables |
| Optimization Insights | 5+ cost-saving analysis widgets |

---

## Cross-Reference: Dashboards ↔ TVFs & Metric Views

This section maps each dashboard to the TVFs and Metric Views that should power its widgets.

### TVF Coverage by Dashboard

| Dashboard | Supporting TVFs (51 Total) |
|-----------|----------------------------|
| **Executive Overview** | `get_cost_mtd_summary`, `get_job_success_rate`, `get_cost_trend_by_sku` |
| **Cost Management** | `get_top_cost_contributors`, `get_cost_trend_by_sku`, `get_cost_by_owner`, `get_cost_week_over_week`, `get_cost_growth_analysis`, `get_most_expensive_jobs` |
| **Commit Tracking** | `get_commit_vs_actual`, `get_cost_forecast_summary`, `get_cost_mtd_summary` |
| **Tag-Based Attribution** | `get_cost_by_tag`, `get_untagged_resources`, `get_tag_coverage`, `get_spend_by_custom_tags` |
| **Job Reliability** | `get_failed_jobs`, `get_job_success_rate`, `get_job_duration_percentiles`, `get_job_failure_trends`, `get_job_sla_compliance`, `get_job_retry_analysis`, `get_job_failure_costs` |
| **Job Optimization** | `get_job_repair_costs`, `get_job_spend_trend_analysis`, `get_jobs_without_autoscaling`, `get_job_run_duration_analysis` |
| **Query Performance** | `get_slow_queries`, `get_warehouse_utilization`, `get_query_efficiency`, `get_high_spill_queries`, `get_query_volume_trends`, `get_query_latency_percentiles`, `get_failed_queries` |
| **Cluster Utilization** | `get_cluster_utilization`, `get_cluster_resource_metrics`, `get_underutilized_clusters` |
| **Security & Audit** | `get_user_activity_summary`, `get_sensitive_table_access`, `get_failed_actions`, `get_permission_changes`, `get_off_hours_activity`, `get_security_events_timeline`, `get_ip_address_analysis`, `get_table_access_audit` |
| **Table Health Advisor** | `get_table_freshness`, `get_data_quality_summary`, `get_tables_failing_quality` |
| **DBR Migration** | `get_jobs_on_legacy_dbr`, `get_jobs_without_autoscaling` |
| **Data Governance Hub (NEW)** | `get_table_access_audit`, `get_tag_coverage`, `get_data_freshness_by_domain` |
| **DLT Pipeline Monitoring (NEW)** | `get_job_success_rate`, `get_job_failure_trends`, `get_data_freshness_by_domain` |
| **Period Comparison (NEW)** | `get_cost_week_over_week`, `get_cost_growth_analysis`, `get_job_spend_trend_analysis` |
| **Warehouse Scaling (NEW)** | `get_warehouse_utilization`, `get_query_volume_trends`, `get_cluster_utilization` |

### Metric View Coverage by Dashboard

| Dashboard | Primary Metric View | Alternative Views |
|-----------|---------------------|-------------------|
| **Executive Overview** | `cost_analytics` | `job_performance`, `query_performance` |
| **Cost Management** | `cost_analytics` | `commit_tracking` |
| **Commit Tracking** | `commit_tracking` | `cost_analytics` |
| **Tag-Based Attribution** | `cost_analytics` | - |
| **Job Reliability** | `job_performance` | - |
| **Job Optimization** | `job_performance` | `cost_analytics` |
| **Query Performance** | `query_performance` | - |
| **Cluster Utilization** | `cluster_utilization` | - |
| **Security & Audit** | `security_events` | - |
| **Table Health Advisor** | `data_quality` | - |
| **DBR Migration** | `job_performance` | `cluster_utilization` |
| **Data Governance Hub (NEW)** | `data_quality` | `security_events` |
| **DLT Pipeline Monitoring (NEW)** | `job_performance` | `data_quality` |
| **Period Comparison (NEW)** | `cost_analytics` | `job_performance` |
| **Warehouse Scaling (NEW)** | `query_performance` | `cluster_utilization` |

### ML-Enhanced Dashboard Opportunities

The `ml_intelligence` metric view can enhance these dashboards with predictive insights:

| Dashboard | ML Enhancement Opportunity |
|-----------|---------------------------|
| **Cost Management** | Cost anomaly alerts from `ml_intelligence.anomaly_count` |
| **Commit Tracking** | ML forecast confidence from `budget_forecast_predictions` |
| **Job Reliability** | Failure predictions from `job_failure_predictions` |
| **Query Performance** | Query regression alerts from `query_regression_predictions` |
| **Security & Audit** | Threat detection from `threat_detection_predictions` |

### TVF Inventory Summary

| Domain | TVF Count | Key Functions |
|--------|-----------|---------------|
| **Cost** | 13 | `get_top_cost_contributors`, `get_commit_vs_actual`, `get_cost_anomalies` |
| **Reliability** | 12 | `get_failed_jobs`, `get_job_success_rate`, `get_job_repair_costs` |
| **Performance** | 8 | `get_slow_queries`, `get_warehouse_utilization`, `get_query_efficiency` |
| **Security** | 8 | `get_user_activity_summary`, `get_permission_changes`, `get_off_hours_activity` |
| **Compute** | 5 | `get_cluster_utilization`, `get_underutilized_clusters`, `get_jobs_on_legacy_dbr` |
| **Quality** | 5 | `get_table_freshness`, `get_data_quality_summary`, `get_tables_failing_quality` |
| **Total** | **51** | |

### Metric View Inventory Summary

| Metric View | Source Table | Key Measures |
|-------------|--------------|--------------|
| `cost_analytics` | `fact_usage` | `total_cost`, `total_dbu`, `cost_per_dbu`, `unique_users` |
| `commit_tracking` | `fact_usage` + `commit_configurations` | `ytd_spend`, `run_rate`, `commit_variance` |
| `job_performance` | `fact_job_run_timeline` | `success_rate`, `avg_duration`, `failure_count` |
| `query_performance` | `fact_query_history` | `p95_latency`, `avg_rows_returned`, `spill_rate` |
| `cluster_utilization` | `fact_node_timeline` | `avg_cpu_utilization`, `avg_memory_utilization` |
| `security_events` | `fact_audit_logs` | `event_count`, `unique_users`, `failed_action_rate` |
| `data_quality` | `information_schema.tables` | `total_tables`, `freshness_rate`, `stale_tables` |
| `ml_intelligence` | `cost_anomaly_predictions` | `anomaly_count`, `anomaly_rate`, `anomaly_cost` |
| **Total** | **8 views** | |

---

## References

### Official Databricks Documentation
- [Databricks Lakeview Dashboards](https://docs.databricks.com/visualizations/lakeview)
- [Dashboard JSON Reference](https://docs.databricks.com/api/workspace/lakeview)
- [AI/BI Dashboard Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/resources)

### Microsoft Learn System Tables Documentation
- [Jobs Cost Observability](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost)
- [Job Run Timeline Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs)
- [Compute Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute)
- [Audit Logs Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)

### Inspiration Repositories
- [DBSQL Warehouse Advisor](https://github.com/CodyAustinDavis/dbsql_sme/tree/main/Observability%20Dashboards%20and%20DBA%20Resources/Observability%20Lakeview%20Dashboard%20Templates/DBSQL%20Warehouse%20Advisor%20With%20Data%20Model)
- [Table Health Advisor](https://github.com/CodyAustinDavis/dbsql_sme/tree/main/Observability%20Dashboards%20and%20DBA%20Resources/Observability%20Lakeview%20Dashboard%20Templates/Table%20Health%20Advisor)
- [Workflow Advisor](https://github.com/yati1002/Workflowadvisor)
- [System Tables Audit Logs](https://github.com/andyweaves/system-tables-audit-logs)

