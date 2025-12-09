# FinOps Business Questions for Databricks Health Monitor

**Project:** Databricks Health Monitor Using System Tables  
**Business Domain:** FinOps (Financial Operations) - Cost Optimization & Chargeback  
**Source System:** Databricks System Tables  
**Source Databricks Catalog:** `system`  
**Target Schema:** `prashanth_subrahmanyam_catalog.db_health_monitor`

---

## 📋 Common Business Questions (15 questions)

### Cost Attribution & Chargeback

| # | Question | TVF Name | Parameters |
|---|----------|----------|------------|
| 1 | "What are the top 10 workspaces by cost this month?" | `get_top_workspaces_by_cost` | start_date, end_date, top_n |
| 2 | "Show me all costs for workspace X last quarter" | `get_workspace_cost_breakdown` | workspace_id, start_date, end_date |
| 3 | "Which users are driving the highest costs?" | `get_top_users_by_cost` | start_date, end_date, top_n |
| 4 | "Which service principals have the highest spend?" | `get_top_service_principals_by_cost` | start_date, end_date, top_n |
| 5 | "Show me costs with custom tags for chargeback" | `get_cost_by_custom_tags` | start_date, end_date, tag_key |

### Resource Cost Analysis

| # | Question | TVF Name | Parameters |
|---|----------|----------|------------|
| 6 | "What are the most expensive SKUs we're using?" | `get_top_skus_by_spend` | start_date, end_date, top_n |
| 7 | "Which jobs are consuming the most DBUs?" | `get_top_jobs_by_dbu_consumption` | start_date, end_date, top_n |
| 8 | "What are our most expensive DLT pipelines?" | `get_top_pipelines_by_cost` | start_date, end_date, top_n |
| 9 | "Show me warehouse costs by size tier" | `get_warehouse_cost_by_tier` | start_date, end_date |
| 10 | "What's our cost by product (Jobs, SQL, DLT, ML)?" | `get_cost_by_product` | start_date, end_date |

### Optimization & Waste

| # | Question | TVF Name | Parameters |
|---|----------|----------|------------|
| 11 | "What are idle clusters costing us?" | `get_idle_cluster_waste` | start_date, end_date, min_idle_hours |
| 12 | "Show me jobs running slower than baseline" | `get_inefficient_job_runs` | start_date, end_date, deviation_threshold |
| 13 | "Show me all serverless vs classic compute costs" | `get_cost_by_compute_type` | start_date, end_date |

### Trend Analysis

| # | Question | TVF Name | Parameters |
|---|----------|----------|------------|
| 14 | "What's our daily cost trend over the last 30 days?" | `get_daily_cost_trend` | start_date, end_date |
| 15 | "Compare costs by cloud region" | `get_cost_by_region` | start_date, end_date |

---

## 📊 Gold Layer Tables Available

### Facts (Cost & Performance)

| Table | Grain | Key Measures |
|-------|-------|--------------|
| **fact_billing_usage** | One row per usage record | usage_quantity, sku_name, billing_origin_product, custom_tags |
| **fact_job_run** | One row per job run | run_duration_seconds, baseline_p50_seconds, runtime_deviation_pct |
| **fact_warehouse_utilization** | One row per warehouse-hour | total_queries_executed, total_execution_time_ms, avg_query_time_ms |
| **fact_cluster_utilization** | One row per cluster-hour | (node timeline metrics) |

### Dimensions (Attribution)

| Dimension | Type | Key Attributes |
|-----------|------|----------------|
| **dim_workspace** | SCD Type 2 | workspace_id, workspace_name, cloud_provider, region, pricing_tier |
| **dim_sku** | SCD Type 1 | sku_name, sku_category, unit_of_measure, unit_price, currency |
| **dim_user** | SCD Type 2 | user_id, user_name, user_email, group_ids |
| **dim_service_principal** | SCD Type 2 | sp_id, sp_name, application_id |
| **dim_job** | SCD Type 2 | job_id, job_name, job_type, task_keys |
| **dim_cluster** | SCD Type 2 | cluster_id, cluster_name, cluster_type, autoscale_min/max_workers |
| **dim_warehouse** | SCD Type 2 | warehouse_id, warehouse_name, warehouse_type, cluster_size |
| **dim_pipeline** | SCD Type 2 | pipeline_id, pipeline_name |
| **dim_endpoint** | SCD Type 2 | endpoint_id, endpoint_name (Model Serving / Vector Search) |
| **dim_date** | SCD Type 0 | date, year, quarter, month, day_of_week, is_weekend |

---

## 📐 Key Measures to Include

### Cost Measures

| Measure Name | Aggregation | Description |
|-------------|-------------|-------------|
| `total_cost` | `SUM(usage_quantity * unit_price)` | Total spend in USD (join to dim_sku for unit_price) |
| `total_dbus` | `SUM(CASE WHEN usage_unit = 'DBU' THEN usage_quantity ELSE 0 END)` | Total DBU consumption |
| `total_usage_hours` | `SUM(UNIX_TIMESTAMP(usage_end_time) - UNIX_TIMESTAMP(usage_start_time)) / 3600` | Total compute hours |
| `avg_cost_per_day` | `SUM(cost) / COUNT(DISTINCT usage_date)` | Average daily spend |
| `cost_per_dbu` | `SUM(cost) / NULLIF(SUM(dbus), 0)` | Average cost per DBU |

### Usage Measures

| Measure Name | Aggregation | Description |
|-------------|-------------|-------------|
| `unique_workspaces` | `COUNT(DISTINCT workspace_id)` | Number of active workspaces |
| `unique_users` | `COUNT(DISTINCT user_email)` | Number of users generating costs |
| `unique_jobs` | `COUNT(DISTINCT job_id)` | Number of distinct jobs run |
| `record_count` | `COUNT(*)` | Number of usage records |

### Efficiency Measures

| Measure Name | Aggregation | Description |
|-------------|-------------|-------------|
| `serverless_cost_pct` | `SUM(CASE WHEN is_serverless THEN cost END) / NULLIF(SUM(cost), 0) * 100` | Serverless adoption percentage |
| `jobs_tier_light_pct` | `SUM(CASE WHEN jobs_tier = 'light' THEN cost END) / NULLIF(SUM(cost), 0) * 100` | Light jobs tier percentage |
| `photon_adoption_pct` | `SUM(CASE WHEN is_photon THEN cost END) / NULLIF(SUM(cost), 0) * 100` | Photon usage percentage |

### Waste Measures

| Measure Name | Aggregation | Description |
|-------------|-------------|-------------|
| `idle_cost` | `SUM(CASE WHEN utilization_pct < 10 THEN cost END)` | Wasted spend on idle resources |
| `avg_runtime_deviation_pct` | `AVG(runtime_deviation_pct)` | Average job performance deviation from baseline |

---

## 🎯 Business Use Cases

### 1. Executive Dashboard
**Questions:** Total spend, daily trend, top workspaces, serverless adoption  
**TVFs:** `get_daily_cost_trend`, `get_top_workspaces_by_cost`, `get_cost_by_compute_type`

### 2. Chargeback Report
**Questions:** Cost by workspace, cost by user, cost by custom tags  
**TVFs:** `get_workspace_cost_breakdown`, `get_top_users_by_cost`, `get_cost_by_custom_tags`

### 3. Cost Optimization
**Questions:** Idle cluster waste, inefficient jobs, SKU optimization  
**TVFs:** `get_idle_cluster_waste`, `get_inefficient_job_runs`, `get_top_skus_by_spend`

### 4. Product Analysis
**Questions:** Cost by product (Jobs, SQL, DLT, ML), cost by feature tier  
**TVFs:** `get_cost_by_product`, `get_warehouse_cost_by_tier`

### 5. Regional Analysis
**Questions:** Cost by cloud region, cross-region data transfer costs  
**TVFs:** `get_cost_by_region`

---

## 💡 Implementation Notes

### Critical fact_billing_usage Fields

```sql
-- Core cost fields
usage_quantity DECIMAL(20,6)          -- Number of DBUs/GB/requests
usage_unit STRING                      -- 'DBU', 'GB', 'requests', etc.
sku_name STRING                        -- 'STANDARD_ALL_PURPOSE_COMPUTE', 'SERVERLESS_SQL', etc.
usage_date DATE                        -- Simplified date for fast aggregations
billing_origin_product STRING          -- 'JOBS', 'DLT', 'SQL', 'MODEL_SERVING', etc.

-- Attribution fields (conditional - nullable FKs)
workspace_id STRING
user_email STRING                      -- NULL for SP workloads
service_principal_application_id       -- NULL for user workloads
cluster_id STRING                      -- NULL for serverless
warehouse_id STRING                    -- NULL for non-SQL workloads
job_id STRING                          -- NULL for interactive workloads
dlt_pipeline_id STRING                 -- NULL for non-DLT workloads
endpoint_id STRING                     -- NULL for non-serving workloads

-- Product features (for optimization analysis)
is_serverless BOOLEAN
is_photon BOOLEAN
jobs_tier STRING                       -- 'light', 'classic', NULL
sql_tier STRING                        -- 'CLASSIC', 'PRO', NULL
dlt_tier STRING                        -- 'CORE', 'PRO', 'ADVANCED', NULL
performance_target STRING              -- 'PERFORMANCE_OPTIMIZED', 'STANDARD', NULL

-- Custom tags (for chargeback)
custom_tags MAP<STRING, STRING>        -- User-defined tags (e.g., {"env": "prod", "project": "ml"})

-- Correction handling
record_type STRING                     -- 'ORIGINAL', 'RETRACTION', 'RESTATEMENT'
```

### TVF Patterns

**Cost Calculation:**
```sql
-- Must join to dim_sku for unit_price (not in fact_billing_usage)
SUM(f.usage_quantity * s.unit_price) as total_cost
FROM fact_billing_usage f
LEFT JOIN dim_sku s ON f.sku_key = s.sku_key
```

**Custom Tags Filtering:**
```sql
-- Extract tag value from MAP column
WHERE custom_tags['project'] = 'ml_pipeline'
OR element_at(custom_tags, 'environment') = 'production'
```

**Correction Handling:**
```sql
-- SUM handles RETRACTION records (negative usage_quantity) automatically
SUM(usage_quantity) as total_usage  -- Correct: includes corrections
```

**Nullable FK Pattern:**
```sql
-- Cost can be from cluster OR warehouse OR pipeline (conditional attribution)
LEFT JOIN dim_cluster c ON f.cluster_key = c.cluster_key
LEFT JOIN dim_warehouse w ON f.warehouse_key = w.warehouse_key
LEFT JOIN dim_pipeline p ON f.pipeline_key = p.pipeline_key
```

---

## 📚 References

- [Databricks System Tables - Billing](https://docs.databricks.com/admin/system-tables/billing)
- [Databricks Pricing](https://www.databricks.com/product/pricing)
- [Cost Management Best Practices](https://docs.databricks.com/admin/cost-management.html)
- [Gold Layer Design README](../gold_layer_design/README.md)
- [Table-Valued Functions Guide](./gold-layer-dimensional-model-design.md)



