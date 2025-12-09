-- =============================================================================
-- Databricks Health Monitor - FinOps Table-Valued Functions for Genie
-- 
-- This file contains parameterized functions optimized for Genie Spaces.
-- Each function includes LLM-friendly metadata for natural language understanding.
--
-- Key Patterns:
-- 1. STRING for date parameters (Genie doesn't support DATE type)
-- 2. Required parameters first, optional (DEFAULT) parameters last
-- 3. ROW_NUMBER + WHERE for Top N (not LIMIT with parameter)
-- 4. NULLIF for all divisions (null safety)
-- 5. is_current = true for SCD2 dimension joins
-- 6. Join to dim_sku for unit_price (cost calculation)
--
-- Usage: Deploy via gold_setup_job or setup_orchestrator_job
-- =============================================================================

-- Set context (parameterized via Asset Bundle)
USE CATALOG ${catalog};
USE SCHEMA ${gold_schema};

-- =============================================================================
-- TVF 1: Get Top Workspaces by Cost
-- =============================================================================
CREATE OR REPLACE FUNCTION get_top_workspaces_by_cost(
  start_date STRING COMMENT 'Start date for analysis (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date for analysis (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top workspaces to return (default: 10)'
)
RETURNS TABLE(
  rank INT COMMENT 'Workspace rank by total cost',
  workspace_id STRING COMMENT 'Workspace identifier',
  workspace_name STRING COMMENT 'Workspace display name',
  cloud_provider STRING COMMENT 'Cloud provider (AWS, Azure, GCP)',
  region STRING COMMENT 'Cloud region',
  pricing_tier STRING COMMENT 'Pricing tier (Premium, Enterprise)',
  total_cost DECIMAL(18,2) COMMENT 'Total cost in USD for the period',
  total_dbus DECIMAL(20,2) COMMENT 'Total DBUs consumed',
  total_usage_hours DECIMAL(18,2) COMMENT 'Total compute hours',
  unique_users BIGINT COMMENT 'Number of distinct users',
  unique_jobs BIGINT COMMENT 'Number of distinct jobs',
  serverless_cost_pct DECIMAL(5,2) COMMENT 'Percentage of cost from serverless compute',
  top_sku STRING COMMENT 'Most expensive SKU for this workspace',
  top_product STRING COMMENT 'Most expensive product (Jobs, SQL, DLT, etc.)'
)
COMMENT 'LLM: Returns the top N workspaces ranked by total cost for a date range. 
Use this for workspace-level cost analysis, chargeback reporting, and identifying 
high-spend workspaces. Parameters: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), 
optional top_n (default 10). 
Example: "What are the top 10 workspaces by cost this month?" or 
"Show me the most expensive workspaces last quarter"'
RETURN
  WITH workspace_metrics AS (
    SELECT 
      fbu.workspace_id,
      dw.workspace_name,
      dw.cloud_provider,
      dw.region,
      dw.pricing_tier,
      -- Cost calculation (join to dim_sku for unit_price)
      SUM(fbu.usage_quantity * ds.unit_price) as total_cost,
      -- DBU consumption
      SUM(CASE WHEN fbu.usage_unit = 'DBU' THEN fbu.usage_quantity ELSE 0 END) as total_dbus,
      -- Usage hours
      SUM((UNIX_TIMESTAMP(fbu.usage_end_time) - UNIX_TIMESTAMP(fbu.usage_start_time)) / 3600) as total_usage_hours,
      -- Unique users and jobs
      COUNT(DISTINCT fbu.user_email) as unique_users,
      COUNT(DISTINCT fbu.job_id) as unique_jobs,
      -- Serverless adoption
      SUM(CASE WHEN fbu.is_serverless = true THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) / 
        NULLIF(SUM(fbu.usage_quantity * ds.unit_price), 0) * 100 as serverless_cost_pct,
      -- Top SKU and product
      FIRST_VALUE(fbu.sku_name) OVER (
        PARTITION BY fbu.workspace_id 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_sku,
      FIRST_VALUE(fbu.billing_origin_product) OVER (
        PARTITION BY fbu.workspace_id 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_product
    FROM fact_billing_usage fbu
    -- Join to dim_workspace (SCD2 - use is_current)
    LEFT JOIN dim_workspace dw 
      ON fbu.workspace_key = dw.workspace_key 
      AND dw.is_current = true
    -- Join to dim_sku for unit_price
    LEFT JOIN dim_sku ds 
      ON fbu.sku_key = ds.sku_key
    -- Cast STRING dates to DATE for filtering
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fbu.workspace_id, dw.workspace_name, dw.cloud_provider, dw.region, dw.pricing_tier
  ),
  ranked_workspaces AS (
    SELECT 
      -- Rank using ROW_NUMBER (for parameterized top N)
      ROW_NUMBER() OVER (ORDER BY total_cost DESC) as rank,
      workspace_id,
      workspace_name,
      cloud_provider,
      region,
      pricing_tier,
      total_cost,
      total_dbus,
      total_usage_hours,
      unique_users,
      unique_jobs,
      serverless_cost_pct,
      top_sku,
      top_product
    FROM workspace_metrics
  )
  -- Filter by rank (not LIMIT) to support parameterized top N
  SELECT * FROM ranked_workspaces
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 2: Get Workspace Cost Breakdown
-- =============================================================================
CREATE OR REPLACE FUNCTION get_workspace_cost_breakdown(
  p_workspace_id STRING COMMENT 'Workspace ID to analyze',
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
  usage_date DATE COMMENT 'Usage date',
  sku_name STRING COMMENT 'SKU name',
  sku_category STRING COMMENT 'SKU category (Compute, Storage, etc.)',
  billing_origin_product STRING COMMENT 'Product (JOBS, SQL, DLT, MODEL_SERVING, etc.)',
  usage_quantity DECIMAL(20,6) COMMENT 'Usage quantity',
  usage_unit STRING COMMENT 'Unit of measure (DBU, GB, requests)',
  unit_price DECIMAL(18,6) COMMENT 'Price per unit in USD',
  total_cost DECIMAL(18,2) COMMENT 'Total cost for this SKU-product-date',
  is_serverless BOOLEAN COMMENT 'Serverless compute indicator',
  is_photon BOOLEAN COMMENT 'Photon engine indicator',
  custom_tags MAP<STRING, STRING> COMMENT 'User-defined custom tags'
)
COMMENT 'LLM: Returns detailed daily cost breakdown for a specific workspace. 
Use this for workspace-level deep dives, cost allocation, and chargeback analysis. 
Shows costs by SKU, product, and date with all relevant tags. 
Parameters: workspace_id, start_date, end_date. 
Example: "Show me all costs for workspace 12345 last month" or 
"Break down costs for workspace X this quarter"'
RETURN
  SELECT 
    fbu.usage_date,
    fbu.sku_name,
    ds.sku_category,
    fbu.billing_origin_product,
    fbu.usage_quantity,
    fbu.usage_unit,
    ds.unit_price,
    fbu.usage_quantity * ds.unit_price as total_cost,
    fbu.is_serverless,
    fbu.is_photon,
    fbu.custom_tags
  FROM fact_billing_usage fbu
  LEFT JOIN dim_sku ds 
    ON fbu.sku_key = ds.sku_key
  WHERE fbu.workspace_id = p_workspace_id
    AND fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
  ORDER BY fbu.usage_date, total_cost DESC;

-- =============================================================================
-- TVF 3: Get Top Jobs by DBU Consumption
-- =============================================================================
CREATE OR REPLACE FUNCTION get_top_jobs_by_dbu_consumption(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top jobs to return (default: 10)'
)
RETURNS TABLE(
  rank INT COMMENT 'Job rank by DBU consumption',
  job_id STRING COMMENT 'Job identifier',
  job_name STRING COMMENT 'Job display name',
  workspace_id STRING COMMENT 'Workspace ID',
  workspace_name STRING COMMENT 'Workspace name',
  total_dbus DECIMAL(20,2) COMMENT 'Total DBUs consumed',
  total_cost DECIMAL(18,2) COMMENT 'Total cost in USD',
  total_runs BIGINT COMMENT 'Number of job runs',
  avg_dbus_per_run DECIMAL(18,2) COMMENT 'Average DBUs per run',
  avg_runtime_seconds BIGINT COMMENT 'Average runtime in seconds',
  success_rate_pct DECIMAL(5,2) COMMENT 'Percentage of successful runs',
  avg_deviation_pct DECIMAL(10,2) COMMENT 'Average runtime deviation from baseline',
  is_serverless BOOLEAN COMMENT 'Serverless job indicator',
  jobs_tier STRING COMMENT 'Jobs tier (light, classic, NULL)'
)
COMMENT 'LLM: Returns the top N jobs ranked by total DBU consumption for a date range. 
Use this for job-level cost optimization, identifying expensive jobs, and right-sizing analysis. 
Includes performance metrics and efficiency indicators. 
Parameters: start_date, end_date, optional top_n (default 10). 
Example: "Which jobs are consuming the most DBUs?" or 
"Show me the most expensive jobs this month"'
RETURN
  WITH job_cost_metrics AS (
    SELECT 
      fbu.job_id,
      fbu.job_name,
      fbu.workspace_id,
      dw.workspace_name,
      -- DBU consumption
      SUM(CASE WHEN fbu.usage_unit = 'DBU' THEN fbu.usage_quantity ELSE 0 END) as total_dbus,
      -- Cost calculation
      SUM(fbu.usage_quantity * ds.unit_price) as total_cost,
      -- Run count
      COUNT(DISTINCT fbu.job_run_id) as total_runs,
      -- Serverless and tier info
      MAX(fbu.is_serverless) as is_serverless,
      MAX(fbu.jobs_tier) as jobs_tier
    FROM fact_billing_usage fbu
    LEFT JOIN dim_workspace dw 
      ON fbu.workspace_key = dw.workspace_key 
      AND dw.is_current = true
    LEFT JOIN dim_sku ds 
      ON fbu.sku_key = ds.sku_key
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND fbu.job_id IS NOT NULL
    GROUP BY fbu.job_id, fbu.job_name, fbu.workspace_id, dw.workspace_name
  ),
  job_performance_metrics AS (
    SELECT 
      fjr.job_id,
      AVG(fjr.run_duration_seconds) as avg_runtime_seconds,
      SUM(CASE WHEN fjr.run_status = 'SUCCESS' THEN 1 ELSE 0 END) / 
        NULLIF(COUNT(*), 0) * 100 as success_rate_pct,
      AVG(fjr.runtime_deviation_pct) as avg_deviation_pct
    FROM fact_job_run fjr
    JOIN dim_date dd ON fjr.date_key = dd.date_key
    WHERE dd.date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fjr.job_id
  ),
  ranked_jobs AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY jcm.total_dbus DESC) as rank,
      jcm.job_id,
      jcm.job_name,
      jcm.workspace_id,
      jcm.workspace_name,
      jcm.total_dbus,
      jcm.total_cost,
      jcm.total_runs,
      jcm.total_dbus / NULLIF(jcm.total_runs, 0) as avg_dbus_per_run,
      jpm.avg_runtime_seconds,
      jpm.success_rate_pct,
      jpm.avg_deviation_pct,
      jcm.is_serverless,
      jcm.jobs_tier
    FROM job_cost_metrics jcm
    LEFT JOIN job_performance_metrics jpm 
      ON jcm.job_id = jpm.job_id
  )
  SELECT * FROM ranked_jobs
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 4: Get Daily Cost Trend
-- =============================================================================
CREATE OR REPLACE FUNCTION get_daily_cost_trend(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
  usage_date DATE COMMENT 'Usage date',
  day_of_week_name STRING COMMENT 'Day name (Monday, etc.)',
  is_weekend BOOLEAN COMMENT 'Weekend indicator',
  total_cost DECIMAL(18,2) COMMENT 'Total cost in USD',
  total_dbus DECIMAL(20,2) COMMENT 'Total DBUs consumed',
  total_usage_hours DECIMAL(18,2) COMMENT 'Total compute hours',
  unique_workspaces BIGINT COMMENT 'Number of active workspaces',
  unique_users BIGINT COMMENT 'Number of active users',
  serverless_cost DECIMAL(18,2) COMMENT 'Serverless cost',
  classic_cost DECIMAL(18,2) COMMENT 'Classic compute cost',
  serverless_pct DECIMAL(5,2) COMMENT 'Serverless percentage of total',
  jobs_cost DECIMAL(18,2) COMMENT 'Jobs product cost',
  sql_cost DECIMAL(18,2) COMMENT 'SQL product cost',
  dlt_cost DECIMAL(18,2) COMMENT 'DLT product cost',
  ml_cost DECIMAL(18,2) COMMENT 'ML product cost (Model Serving + Training)'
)
COMMENT 'LLM: Returns daily cost trend with day-of-week context and product breakdown. 
Use this for trend analysis, budget tracking, and identifying cost patterns. 
Shows serverless adoption and product-level costs. 
Parameters: start_date, end_date. 
Example: "Show me daily cost trend for last month" or 
"What is the cost by day for Q4?"'
RETURN
  SELECT 
    fbu.usage_date,
    dd.day_of_week_name,
    dd.is_weekend,
    -- Total cost
    SUM(fbu.usage_quantity * ds.unit_price) as total_cost,
    -- DBU consumption
    SUM(CASE WHEN fbu.usage_unit = 'DBU' THEN fbu.usage_quantity ELSE 0 END) as total_dbus,
    -- Usage hours
    SUM((UNIX_TIMESTAMP(fbu.usage_end_time) - UNIX_TIMESTAMP(fbu.usage_start_time)) / 3600) as total_usage_hours,
    -- Unique counts
    COUNT(DISTINCT fbu.workspace_id) as unique_workspaces,
    COUNT(DISTINCT fbu.user_email) as unique_users,
    -- Serverless vs Classic
    SUM(CASE WHEN fbu.is_serverless = true THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as serverless_cost,
    SUM(CASE WHEN fbu.is_serverless = false THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as classic_cost,
    SUM(CASE WHEN fbu.is_serverless = true THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) / 
      NULLIF(SUM(fbu.usage_quantity * ds.unit_price), 0) * 100 as serverless_pct,
    -- Product breakdown
    SUM(CASE WHEN fbu.billing_origin_product = 'JOBS' THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as jobs_cost,
    SUM(CASE WHEN fbu.billing_origin_product = 'SQL' THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as sql_cost,
    SUM(CASE WHEN fbu.billing_origin_product = 'DLT' THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as dlt_cost,
    SUM(CASE WHEN fbu.billing_origin_product IN ('MODEL_SERVING', 'ML_TRAINING') 
        THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as ml_cost
  FROM fact_billing_usage fbu
  LEFT JOIN dim_sku ds 
    ON fbu.sku_key = ds.sku_key
  LEFT JOIN dim_date dd 
    ON fbu.date_key = dd.date_key
  WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
  GROUP BY fbu.usage_date, dd.day_of_week_name, dd.is_weekend
  ORDER BY fbu.usage_date;

-- =============================================================================
-- TVF 5: Get Cost by Product
-- =============================================================================
CREATE OR REPLACE FUNCTION get_cost_by_product(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
  billing_origin_product STRING COMMENT 'Product name (JOBS, SQL, DLT, etc.)',
  total_cost DECIMAL(18,2) COMMENT 'Total cost for product',
  total_dbus DECIMAL(20,2) COMMENT 'Total DBUs consumed',
  cost_pct DECIMAL(5,2) COMMENT 'Percentage of total cost',
  unique_workspaces BIGINT COMMENT 'Number of workspaces using this product',
  unique_users BIGINT COMMENT 'Number of users using this product',
  serverless_cost DECIMAL(18,2) COMMENT 'Serverless cost for this product',
  serverless_pct DECIMAL(5,2) COMMENT 'Serverless percentage for this product',
  top_sku STRING COMMENT 'Most expensive SKU for this product',
  top_workspace STRING COMMENT 'Workspace with highest spend on this product'
)
COMMENT 'LLM: Returns cost breakdown by Databricks product (Jobs, SQL, DLT, ML, etc.). 
Use this for product-level analysis, budget allocation, and understanding workload mix. 
Shows serverless adoption per product and identifies top consumers. 
Parameters: start_date, end_date. 
Example: "What is our cost by product?" or 
"Show me spending on Jobs vs SQL vs DLT"'
RETURN
  WITH product_metrics AS (
    SELECT 
      fbu.billing_origin_product,
      SUM(fbu.usage_quantity * ds.unit_price) as total_cost,
      SUM(CASE WHEN fbu.usage_unit = 'DBU' THEN fbu.usage_quantity ELSE 0 END) as total_dbus,
      COUNT(DISTINCT fbu.workspace_id) as unique_workspaces,
      COUNT(DISTINCT fbu.user_email) as unique_users,
      SUM(CASE WHEN fbu.is_serverless = true THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) as serverless_cost
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds 
      ON fbu.sku_key = ds.sku_key
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fbu.billing_origin_product
  ),
  total_cost_all AS (
    SELECT SUM(total_cost) as grand_total FROM product_metrics
  ),
  top_sku_per_product AS (
    SELECT 
      fbu.billing_origin_product,
      FIRST_VALUE(fbu.sku_name) OVER (
        PARTITION BY fbu.billing_origin_product 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_sku
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds ON fbu.sku_key = ds.sku_key
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fbu.billing_origin_product, fbu.sku_name
  ),
  top_workspace_per_product AS (
    SELECT 
      fbu.billing_origin_product,
      FIRST_VALUE(dw.workspace_name) OVER (
        PARTITION BY fbu.billing_origin_product 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_workspace
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds ON fbu.sku_key = ds.sku_key
    LEFT JOIN dim_workspace dw ON fbu.workspace_key = dw.workspace_key AND dw.is_current = true
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fbu.billing_origin_product, dw.workspace_name
  )
  SELECT 
    pm.billing_origin_product,
    pm.total_cost,
    pm.total_dbus,
    pm.total_cost / NULLIF(tc.grand_total, 0) * 100 as cost_pct,
    pm.unique_workspaces,
    pm.unique_users,
    pm.serverless_cost,
    pm.serverless_cost / NULLIF(pm.total_cost, 0) * 100 as serverless_pct,
    ts.top_sku,
    tw.top_workspace
  FROM product_metrics pm
  CROSS JOIN total_cost_all tc
  LEFT JOIN top_sku_per_product ts 
    ON pm.billing_origin_product = ts.billing_origin_product
  LEFT JOIN top_workspace_per_product tw 
    ON pm.billing_origin_product = tw.billing_origin_product
  ORDER BY pm.total_cost DESC;

-- =============================================================================
-- TVF 6: Get Top Users by Cost
-- =============================================================================
CREATE OR REPLACE FUNCTION get_top_users_by_cost(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top users to return (default: 10)'
)
RETURNS TABLE(
  rank INT COMMENT 'User rank by cost',
  user_email STRING COMMENT 'User email address',
  user_name STRING COMMENT 'User display name',
  total_cost DECIMAL(18,2) COMMENT 'Total cost attributed to user',
  total_dbus DECIMAL(20,2) COMMENT 'Total DBUs consumed',
  unique_workspaces BIGINT COMMENT 'Number of workspaces accessed',
  unique_jobs BIGINT COMMENT 'Number of distinct jobs run',
  serverless_cost_pct DECIMAL(5,2) COMMENT 'Serverless percentage',
  top_product STRING COMMENT 'Most expensive product for this user',
  top_workspace STRING COMMENT 'Workspace with highest spend for this user'
)
COMMENT 'LLM: Returns the top N users ranked by total cost for a date range. 
Use this for user-level chargeback, identifying high-spend users, and cost allocation. 
Includes usage patterns and resource distribution. 
Parameters: start_date, end_date, optional top_n (default 10). 
Example: "Which users are driving the highest costs?" or 
"Show me the top 20 users by spend this quarter"'
RETURN
  WITH user_metrics AS (
    SELECT 
      fbu.user_email,
      du.user_name,
      SUM(fbu.usage_quantity * ds.unit_price) as total_cost,
      SUM(CASE WHEN fbu.usage_unit = 'DBU' THEN fbu.usage_quantity ELSE 0 END) as total_dbus,
      COUNT(DISTINCT fbu.workspace_id) as unique_workspaces,
      COUNT(DISTINCT fbu.job_id) as unique_jobs,
      SUM(CASE WHEN fbu.is_serverless = true THEN fbu.usage_quantity * ds.unit_price ELSE 0 END) / 
        NULLIF(SUM(fbu.usage_quantity * ds.unit_price), 0) * 100 as serverless_cost_pct,
      FIRST_VALUE(fbu.billing_origin_product) OVER (
        PARTITION BY fbu.user_email 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_product,
      FIRST_VALUE(dw.workspace_name) OVER (
        PARTITION BY fbu.user_email 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_workspace
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds 
      ON fbu.sku_key = ds.sku_key
    LEFT JOIN dim_user du 
      ON fbu.user_key = du.user_key 
      AND du.is_current = true
    LEFT JOIN dim_workspace dw 
      ON fbu.workspace_key = dw.workspace_key 
      AND dw.is_current = true
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND fbu.user_email IS NOT NULL
    GROUP BY fbu.user_email, du.user_name, fbu.billing_origin_product, dw.workspace_name
  ),
  ranked_users AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY total_cost DESC) as rank,
      user_email,
      user_name,
      total_cost,
      total_dbus,
      unique_workspaces,
      unique_jobs,
      serverless_cost_pct,
      top_product,
      top_workspace
    FROM user_metrics
  )
  SELECT * FROM ranked_users
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 7: Get Inefficient Job Runs
-- =============================================================================
CREATE OR REPLACE FUNCTION get_inefficient_job_runs(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  deviation_threshold INT DEFAULT 50 COMMENT 'Minimum deviation percentage to flag (default: 50%)'
)
RETURNS TABLE(
  run_id BIGINT COMMENT 'Job run ID',
  job_id STRING COMMENT 'Job ID',
  job_name STRING COMMENT 'Job name',
  workspace_name STRING COMMENT 'Workspace name',
  start_time TIMESTAMP COMMENT 'Run start time',
  run_duration_seconds BIGINT COMMENT 'Actual runtime in seconds',
  baseline_p50_seconds BIGINT COMMENT 'Historical median runtime',
  runtime_deviation_pct DECIMAL(10,2) COMMENT 'Deviation from baseline (%)',
  run_status STRING COMMENT 'Run status (SUCCESS, FAILED, etc.)',
  cluster_type STRING COMMENT 'Cluster type (Interactive, Job, Serverless)',
  is_serverless BOOLEAN COMMENT 'Serverless indicator'
)
COMMENT 'LLM: Returns job runs that are running significantly slower than their historical baseline. 
Use this for performance optimization, identifying slow jobs, and right-sizing analysis. 
Helps detect performance regressions and inefficient resource usage. 
Parameters: start_date, end_date, optional deviation_threshold (default 50%). 
Example: "Show me jobs running slower than baseline" or 
"Which jobs have the worst performance this week?"'
RETURN
  SELECT 
    fjr.run_id,
    fjr.job_id,
    dj.job_name,
    dw.workspace_name,
    fjr.start_time,
    fjr.run_duration_seconds,
    fjr.baseline_p50_seconds,
    fjr.runtime_deviation_pct,
    fjr.run_status,
    dc.cluster_type,
    CASE WHEN dc.cluster_type = 'Serverless' THEN true ELSE false END as is_serverless
  FROM fact_job_run fjr
  JOIN dim_date dd 
    ON fjr.date_key = dd.date_key
  LEFT JOIN dim_job dj 
    ON fjr.job_key = dj.job_key 
    AND dj.is_current = true
  LEFT JOIN dim_workspace dw 
    ON fjr.workspace_key = dw.workspace_key 
    AND dw.is_current = true
  LEFT JOIN dim_cluster dc 
    ON fjr.cluster_key = dc.cluster_key 
    AND dc.is_current = true
  WHERE dd.date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    AND fjr.runtime_deviation_pct >= deviation_threshold
    AND fjr.run_status = 'SUCCESS'
  ORDER BY fjr.runtime_deviation_pct DESC;

-- =============================================================================
-- TVF 8: Get Cost by Custom Tags
-- =============================================================================
CREATE OR REPLACE FUNCTION get_cost_by_custom_tags(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  tag_key STRING COMMENT 'Custom tag key to analyze (e.g., "project", "environment")'
)
RETURNS TABLE(
  tag_value STRING COMMENT 'Custom tag value',
  total_cost DECIMAL(18,2) COMMENT 'Total cost for this tag value',
  total_dbus DECIMAL(20,2) COMMENT 'Total DBUs consumed',
  cost_pct DECIMAL(5,2) COMMENT 'Percentage of total cost',
  unique_workspaces BIGINT COMMENT 'Number of workspaces with this tag',
  unique_users BIGINT COMMENT 'Number of users with this tag',
  top_sku STRING COMMENT 'Most expensive SKU',
  top_product STRING COMMENT 'Most expensive product'
)
COMMENT 'LLM: Returns cost breakdown by custom tag values for chargeback and cost allocation. 
Use this for project-level tracking, environment-based analysis (prod vs dev), and custom reporting. 
Analyzes user-defined tags applied to compute resources and jobs. 
Parameters: start_date, end_date, tag_key (e.g., "project", "environment", "team"). 
Example: "Show me costs by project tag" or 
"What are costs by environment (production vs dev)?"'
RETURN
  WITH tag_metrics AS (
    SELECT 
      element_at(fbu.custom_tags, tag_key) as tag_value,
      SUM(fbu.usage_quantity * ds.unit_price) as total_cost,
      SUM(CASE WHEN fbu.usage_unit = 'DBU' THEN fbu.usage_quantity ELSE 0 END) as total_dbus,
      COUNT(DISTINCT fbu.workspace_id) as unique_workspaces,
      COUNT(DISTINCT fbu.user_email) as unique_users
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds 
      ON fbu.sku_key = ds.sku_key
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND map_contains_key(fbu.custom_tags, tag_key)
    GROUP BY element_at(fbu.custom_tags, tag_key)
  ),
  total_cost_all AS (
    SELECT SUM(total_cost) as grand_total FROM tag_metrics
  ),
  top_sku_per_tag AS (
    SELECT 
      element_at(fbu.custom_tags, tag_key) as tag_value,
      FIRST_VALUE(fbu.sku_name) OVER (
        PARTITION BY element_at(fbu.custom_tags, tag_key) 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_sku
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds ON fbu.sku_key = ds.sku_key
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND map_contains_key(fbu.custom_tags, tag_key)
    GROUP BY element_at(fbu.custom_tags, tag_key), fbu.sku_name
  ),
  top_product_per_tag AS (
    SELECT 
      element_at(fbu.custom_tags, tag_key) as tag_value,
      FIRST_VALUE(fbu.billing_origin_product) OVER (
        PARTITION BY element_at(fbu.custom_tags, tag_key) 
        ORDER BY SUM(fbu.usage_quantity * ds.unit_price) DESC
      ) as top_product
    FROM fact_billing_usage fbu
    LEFT JOIN dim_sku ds ON fbu.sku_key = ds.sku_key
    WHERE fbu.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND map_contains_key(fbu.custom_tags, tag_key)
    GROUP BY element_at(fbu.custom_tags, tag_key), fbu.billing_origin_product
  )
  SELECT 
    tm.tag_value,
    tm.total_cost,
    tm.total_dbus,
    tm.total_cost / NULLIF(tc.grand_total, 0) * 100 as cost_pct,
    tm.unique_workspaces,
    tm.unique_users,
    ts.top_sku,
    tp.top_product
  FROM tag_metrics tm
  CROSS JOIN total_cost_all tc
  LEFT JOIN top_sku_per_tag ts 
    ON tm.tag_value = ts.tag_value
  LEFT JOIN top_product_per_tag tp 
    ON tm.tag_value = tp.tag_value
  ORDER BY tm.total_cost DESC;

-- =============================================================================
-- End of FinOps Table-Valued Functions
-- =============================================================================



