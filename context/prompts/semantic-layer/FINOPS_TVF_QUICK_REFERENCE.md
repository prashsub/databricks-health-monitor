# FinOps TVF Quick Reference Card

**Project:** Databricks Health Monitor  
**Use:** Copy-paste queries for common FinOps questions

---

## 🚀 Quick Start

```sql
-- Set your catalog/schema
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA db_health_monitor;
```

---

## 📊 Top 8 Questions & Queries

### 1. "What are the top 10 workspaces by cost this month?"

```sql
SELECT * FROM get_top_workspaces_by_cost(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  10
);
```

**Returns:** workspace_id, workspace_name, total_cost, total_dbus, serverless_cost_pct, top_sku, top_product

---

### 2. "Show me all costs for workspace X last quarter"

```sql
SELECT * FROM get_workspace_cost_breakdown(
  '12345',  -- Replace with your workspace_id
  DATE_SUB(CURRENT_DATE(), 90),
  CURRENT_DATE()
);
```

**Returns:** Daily breakdown by SKU, product, usage, cost, serverless indicator, custom tags

---

### 3. "Which jobs are consuming the most DBUs?"

```sql
SELECT * FROM get_top_jobs_by_dbu_consumption(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  10
);
```

**Returns:** job_id, job_name, total_dbus, total_cost, avg_runtime, success_rate, deviation_pct

---

### 4. "What's our daily cost trend over the last 30 days?"

```sql
SELECT * FROM get_daily_cost_trend(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE()
);
```

**Returns:** Daily costs with product breakdown (Jobs, SQL, DLT, ML), serverless %, day-of-week

---

### 5. "What's our cost by product (Jobs, SQL, DLT, ML)?"

```sql
SELECT * FROM get_cost_by_product(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE()
);
```

**Returns:** Cost by product, serverless adoption per product, top SKU, top workspace

---

### 6. "Which users are driving the highest costs?"

```sql
SELECT * FROM get_top_users_by_cost(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  20
);
```

**Returns:** user_email, user_name, total_cost, serverless_pct, top_product, top_workspace

---

### 7. "Show me jobs running slower than baseline"

```sql
SELECT * FROM get_inefficient_job_runs(
  DATE_SUB(CURRENT_DATE(), 7),
  CURRENT_DATE(),
  50  -- 50% deviation threshold
);
```

**Returns:** Jobs exceeding baseline runtime by 50%+, with actual vs baseline comparison

---

### 8. "Show me costs by project tag for chargeback"

```sql
SELECT * FROM get_cost_by_custom_tags(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  'project'  -- Or 'environment', 'team', etc.
);
```

**Returns:** Cost breakdown by tag value, cost %, top SKU, top product

---

## 📅 Common Date Ranges

```sql
-- Last 7 days
DATE_SUB(CURRENT_DATE(), 7), CURRENT_DATE()

-- Last 30 days (this month)
DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE()

-- Last 90 days (this quarter)
DATE_SUB(CURRENT_DATE(), 90), CURRENT_DATE()

-- Last 365 days (this year)
DATE_SUB(CURRENT_DATE(), 365), CURRENT_DATE()

-- Current month (MTD)
DATE_TRUNC('MONTH', CURRENT_DATE()), CURRENT_DATE()

-- Previous month
DATE_TRUNC('MONTH', ADD_MONTHS(CURRENT_DATE(), -1)), 
LAST_DAY(ADD_MONTHS(CURRENT_DATE(), -1))

-- Current quarter (QTD)
DATE_TRUNC('QUARTER', CURRENT_DATE()), CURRENT_DATE()

-- Specific date range
'2024-11-01', '2024-11-30'
```

---

## 🎯 Executive Dashboard Query

**One query for complete overview:**

```sql
-- Daily trend
SELECT 
  'Daily Trend' as metric_type,
  usage_date as date,
  total_cost,
  serverless_pct,
  jobs_cost,
  sql_cost,
  dlt_cost,
  ml_cost
FROM get_daily_cost_trend(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE()
)

UNION ALL

-- Top workspaces
SELECT 
  'Top Workspaces' as metric_type,
  workspace_name as date,  -- Reuse column for workspace name
  total_cost,
  serverless_cost_pct as serverless_pct,
  NULL as jobs_cost,
  NULL as sql_cost,
  NULL as dlt_cost,
  NULL as ml_cost
FROM get_top_workspaces_by_cost(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  5
)

ORDER BY metric_type, date;
```

---

## 🔍 Advanced Filtering

### Filter by Cloud Provider

```sql
SELECT * 
FROM get_top_workspaces_by_cost(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  20
)
WHERE cloud_provider = 'AWS';  -- or 'Azure', 'GCP'
```

### Filter by Region

```sql
SELECT * 
FROM get_top_workspaces_by_cost(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  20
)
WHERE region LIKE 'us-%';  -- US regions only
```

### Filter by Serverless Only

```sql
SELECT * 
FROM get_top_jobs_by_dbu_consumption(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  20
)
WHERE is_serverless = true;
```

### Combine Multiple TVFs

```sql
-- Jobs with high cost AND poor performance
SELECT 
  j.job_id,
  j.job_name,
  j.total_cost,
  i.runtime_deviation_pct,
  i.run_duration_seconds
FROM get_top_jobs_by_dbu_consumption(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  50
) j
JOIN get_inefficient_job_runs(
  DATE_SUB(CURRENT_DATE(), 30),
  CURRENT_DATE(),
  30
) i ON j.job_id = i.job_id
ORDER BY j.total_cost DESC;
```

---

## 📈 Aggregation Examples

### Weekly Aggregation

```sql
SELECT 
  DATE_TRUNC('WEEK', usage_date) as week_start,
  SUM(total_cost) as weekly_cost,
  AVG(serverless_pct) as avg_serverless_pct
FROM get_daily_cost_trend(
  DATE_SUB(CURRENT_DATE(), 90),
  CURRENT_DATE()
)
GROUP BY DATE_TRUNC('WEEK', usage_date)
ORDER BY week_start;
```

### Monthly Aggregation

```sql
SELECT 
  DATE_TRUNC('MONTH', usage_date) as month_start,
  SUM(total_cost) as monthly_cost,
  SUM(jobs_cost) as jobs_cost,
  SUM(sql_cost) as sql_cost,
  SUM(dlt_cost) as dlt_cost
FROM get_daily_cost_trend(
  DATE_SUB(CURRENT_DATE(), 365),
  CURRENT_DATE()
)
GROUP BY DATE_TRUNC('MONTH', usage_date)
ORDER BY month_start;
```

---

## 💡 Pro Tips

### 1. Use DATE_SUB for Relative Dates
```sql
-- ✅ Good: Relative to today
DATE_SUB(CURRENT_DATE(), 30)

-- ❌ Avoid: Hardcoded dates
'2024-11-01'
```

### 2. Always Specify top_n for Large Datasets
```sql
-- ✅ Good: Limit results
get_top_workspaces_by_cost('2024-01-01', '2024-12-31', 10)

-- ❌ Avoid: No limit (uses default 10)
get_top_workspaces_by_cost('2024-01-01', '2024-12-31')
```

### 3. Combine TVFs for Deep Analysis
```sql
-- Workspace breakdown + Daily trend
WITH workspace_costs AS (
  SELECT * FROM get_workspace_cost_breakdown(
    '12345',
    DATE_SUB(CURRENT_DATE(), 30),
    CURRENT_DATE()
  )
)
SELECT 
  DATE_TRUNC('WEEK', usage_date) as week,
  billing_origin_product,
  SUM(total_cost) as weekly_cost
FROM workspace_costs
GROUP BY DATE_TRUNC('WEEK', usage_date), billing_origin_product
ORDER BY week, weekly_cost DESC;
```

---

## 🔗 Related Documentation

- [Business Questions](./finops-tvf-business-questions.md) - Complete requirements
- [SQL Examples](./finops-tvf-sql-examples.sql) - Full TVF definitions
- [Implementation Summary](./FINOPS_TVF_IMPLEMENTATION_SUMMARY.md) - Deployment guide
- [Gold Layer Design](../gold_layer_design/README.md) - Table schemas

---

## ⚡ One-Liners for Common Questions

```sql
-- Total spend this month
SELECT SUM(total_cost) FROM get_daily_cost_trend(DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE());

-- Serverless adoption %
SELECT AVG(serverless_pct) FROM get_daily_cost_trend(DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE());

-- Most expensive workspace
SELECT workspace_name, total_cost FROM get_top_workspaces_by_cost(DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE(), 1);

-- Most expensive job
SELECT job_name, total_cost FROM get_top_jobs_by_dbu_consumption(DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE(), 1);

-- Most expensive user
SELECT user_email, total_cost FROM get_top_users_by_cost(DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE(), 1);

-- Cost by product
SELECT billing_origin_product, total_cost FROM get_cost_by_product(DATE_SUB(CURRENT_DATE(), 30), CURRENT_DATE());
```

---

**Bookmark this page for quick access to FinOps queries!**



