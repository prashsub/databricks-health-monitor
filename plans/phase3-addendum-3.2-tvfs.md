# Phase 3 Addendum 3.2: Table-Valued Functions (TVFs) for Databricks Health Monitor

## Overview

**Status:** 🔧 Enhanced  
**Dependencies:** Gold Layer (Phase 2)  
**Estimated Effort:** 2 weeks  
**Reference:** [Cursor Rule: Table-Valued Functions](../.cursor/rules/15-databricks-table-valued-functions.mdc)

---

## Purpose

Create parameterized SQL functions that:
- **Encapsulate complex business logic** for reusability
- **Enable Genie natural language queries** through LLM-friendly metadata
- **Standardize analytics patterns** across dashboards and reports
- **Provide self-service analytics** for non-technical users

---

## TVF Design Principles

### Genie Compatibility Rules

1. **Use STRING for date parameters** (not DATE type)
2. **Required parameters first**, optional parameters with DEFAULT last
3. **Use WHERE with ROW_NUMBER() instead of LIMIT parameter**
4. **LLM-friendly COMMENT** on function and all columns
5. **NULLIF guards** against division by zero

### ⚠️ Gold Layer Pattern (REQUIRED)

**All TVFs MUST query Gold layer tables, NOT system tables directly.**

```sql
-- ❌ DON'T: Query system tables
FROM system.billing.usage

-- ✅ DO: Query Gold layer
FROM ${catalog}.${gold_schema}.fact_usage
```

---

## TVF Catalog by Agent Domain

| Agent Domain | TVF Count | Key Functions |
|--------------|-----------|---------------|
| **💰 Cost** | 15 | get_top_cost_contributors, get_cost_growth_analysis, get_job_cost_savings, **get_commit_vs_actual**, **get_cost_by_tag**, **get_untagged_resources**, **get_tag_coverage** |
| **🔒 Security** | 4 | get_user_activity_summary, get_sensitive_table_access |
| **⚡ Performance** | 8 | get_slow_queries, get_warehouse_utilization, get_cluster_utilization |
| **🔄 Reliability** | 8 | get_failed_jobs, get_job_success_rate, get_job_repair_costs |
| **✅ Quality** | 3 | get_data_quality_summary, get_tables_failing_quality |

---

## 💰 Cost Agent TVFs (10 TVFs)

#### TVF 1.1: get_top_cost_contributors

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_top_cost_contributors(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 10 COMMENT 'Number of top contributors to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Cost rank (1 = highest)',
    workspace_id STRING COMMENT 'Databricks workspace ID',
    workspace_name STRING COMMENT 'Workspace display name',
    sku_name STRING COMMENT 'Databricks SKU (product category)',
    total_dbu DOUBLE COMMENT 'Total DBUs consumed',
    total_cost DOUBLE COMMENT 'Estimated cost in USD',
    pct_of_total DOUBLE COMMENT 'Percentage of total account cost'
)
COMMENT 'LLM: Returns the top N cost contributors by workspace and SKU for a date range.
Use this for cost optimization, chargeback analysis, and identifying spending hotspots.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default 10).
Example questions: "What are the top 10 cost drivers this month?" or 
"Which workspace spent the most last week?" or "Show me our biggest cost contributors"'
RETURN
    WITH cost_summary AS (
        SELECT 
            f.workspace_id,
            w.workspace_name,
            f.sku_name,
            SUM(f.usage_quantity) AS total_dbu,
            SUM(f.usage_quantity * COALESCE(f.list_price, 0)) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage f
        LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
            ON f.workspace_id = w.workspace_id AND w.is_current = TRUE
        WHERE f.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY f.workspace_id, w.workspace_name, f.sku_name
    ),
    with_totals AS (
        SELECT *,
            SUM(total_cost) OVER () AS grand_total,
            (total_cost / NULLIF(SUM(total_cost) OVER (), 0)) * 100 AS pct_of_total
        FROM cost_summary
    ),
    ranked AS (
        SELECT *,
            ROW_NUMBER() OVER (ORDER BY total_cost DESC) AS rank
        FROM with_totals
    )
    SELECT rank, workspace_id, workspace_name, sku_name, total_dbu, total_cost, pct_of_total
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;
```

#### TVF 1.2: get_cost_trend_by_sku

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_trend_by_sku(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    sku_filter STRING DEFAULT 'ALL' COMMENT 'SKU name filter, or ALL for all SKUs'
)
RETURNS TABLE(
    usage_date DATE COMMENT 'Date of usage',
    sku_name STRING COMMENT 'Databricks SKU name',
    daily_dbu DOUBLE COMMENT 'DBUs consumed that day',
    daily_cost DOUBLE COMMENT 'Cost in USD for that day',
    cumulative_cost DOUBLE COMMENT 'Running total cost',
    pct_change_vs_prior DOUBLE COMMENT 'Percentage change vs prior day'
)
COMMENT 'LLM: Returns daily cost trends broken down by SKU.
Use for tracking spending patterns, identifying cost spikes, and budget monitoring.
Parameters: start_date, end_date, optional sku_filter (e.g., "JOBS_COMPUTE" or "ALL").
Example: "Show me daily cost trend for Jobs Compute" or "What is our spending pattern this month?"'
RETURN
    WITH daily_costs AS (
        SELECT 
            usage_date,
            sku_name,
            SUM(usage_quantity) AS daily_dbu,
            SUM(usage_quantity * COALESCE(list_price, 0)) AS daily_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND (sku_filter = 'ALL' OR sku_name = sku_filter)
        GROUP BY usage_date, sku_name
    ),
    with_running AS (
        SELECT *,
            SUM(daily_cost) OVER (PARTITION BY sku_name ORDER BY usage_date) AS cumulative_cost,
            LAG(daily_cost) OVER (PARTITION BY sku_name ORDER BY usage_date) AS prior_day_cost
        FROM daily_costs
    )
    SELECT 
        usage_date,
        sku_name,
        daily_dbu,
        daily_cost,
        cumulative_cost,
        ((daily_cost - prior_day_cost) / NULLIF(prior_day_cost, 0)) * 100 AS pct_change_vs_prior
    FROM with_running
    ORDER BY usage_date, sku_name;
```

#### TVF 1.3: get_cost_by_owner

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_by_owner(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 20 COMMENT 'Number of top owners to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Cost rank by owner',
    owner STRING COMMENT 'Resource owner (user or service principal)',
    owner_type STRING COMMENT 'SERVICE_PRINCIPAL or USER',
    total_cost DOUBLE COMMENT 'Total cost attributed to owner',
    job_cost DOUBLE COMMENT 'Cost from jobs',
    cluster_cost DOUBLE COMMENT 'Cost from clusters',
    run_count INT COMMENT 'Number of job runs'
)
COMMENT 'LLM: Returns cost breakdown by resource owner (user or service principal).
Use for chargeback, accountability, and identifying high-spending users.
Example: "Who spent the most on Databricks last month?" or "Show me cost by owner"'
RETURN
    WITH owner_costs AS (
        SELECT 
            COALESCE(run_as, owned_by, 'UNKNOWN') AS owner,
            CASE 
                WHEN COALESCE(run_as, owned_by) LIKE '%@%' THEN 'USER'
                ELSE 'SERVICE_PRINCIPAL'
            END AS owner_type,
            SUM(usage_quantity * COALESCE(list_price, 0)) AS total_cost,
            SUM(CASE WHEN job_id IS NOT NULL THEN usage_quantity * COALESCE(list_price, 0) ELSE 0 END) AS job_cost,
            SUM(CASE WHEN cluster_id IS NOT NULL AND job_id IS NULL THEN usage_quantity * COALESCE(list_price, 0) ELSE 0 END) AS cluster_cost,
            COUNT(DISTINCT job_run_id) AS run_count
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY 1, 2
    ),
    ranked AS (
        SELECT *,
            ROW_NUMBER() OVER (ORDER BY total_cost DESC) AS rank
        FROM owner_costs
    )
    SELECT rank, owner, owner_type, total_cost, job_cost, cluster_cost, run_count
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;
```

#### TVF 1.4: get_cost_week_over_week

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_week_over_week(
    weeks_back INT DEFAULT 12 COMMENT 'Number of weeks to analyze'
)
RETURNS TABLE(
    week_start DATE COMMENT 'Start date of the week',
    weekly_cost DOUBLE COMMENT 'Total cost for the week',
    weekly_growth_pct DOUBLE COMMENT 'Percentage growth vs prior week',
    three_month_moving_avg DOUBLE COMMENT '12-week moving average growth'
)
COMMENT 'LLM: Returns week-over-week cost growth trends.
Use for identifying cost trends and seasonality patterns.
Example: "Show me weekly cost growth" or "How is our spending trending week over week?"'
RETURN
    WITH weekly_costs AS (
        SELECT 
            DATE_SUB(usage_date, DAYOFWEEK(usage_date)) AS week_start,
            SUM(usage_quantity * COALESCE(list_price, 0)) AS weekly_cost,
            COUNT(DISTINCT usage_date) AS days_in_week
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL weeks_back WEEK
        GROUP BY 1
        HAVING days_in_week = 7
    ),
    with_growth AS (
        SELECT *,
            LAG(weekly_cost) OVER (ORDER BY week_start) AS prior_week_cost,
            ((weekly_cost - LAG(weekly_cost) OVER (ORDER BY week_start)) / 
                NULLIF(LAG(weekly_cost) OVER (ORDER BY week_start), 0)) * 100 AS weekly_growth_pct
        FROM weekly_costs
    )
    SELECT 
        week_start,
        weekly_cost,
        weekly_growth_pct,
        AVG(weekly_growth_pct) OVER (ORDER BY week_start ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS three_month_moving_avg
    FROM with_growth
    ORDER BY week_start;
```

---

### Domain 2: Job Performance (8 TVFs)

#### TVF 2.1: get_failed_jobs

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_failed_jobs(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    workspace_filter STRING DEFAULT 'ALL' COMMENT 'Workspace ID filter, or ALL'
)
RETURNS TABLE(
    workspace_id STRING COMMENT 'Workspace ID',
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_id STRING COMMENT 'Run ID',
    result_state STRING COMMENT 'Result state (ERROR, FAILED, TIMED_OUT)',
    termination_code STRING COMMENT 'Termination code',
    run_as STRING COMMENT 'User who ran the job',
    start_time TIMESTAMP COMMENT 'Run start time',
    end_time TIMESTAMP COMMENT 'Run end time',
    duration_minutes DOUBLE COMMENT 'Run duration in minutes',
    failure_cost DOUBLE COMMENT 'Estimated cost of failed run'
)
COMMENT 'LLM: Returns all failed job runs with details.
Use for failure analysis, root cause investigation, and reliability tracking.
Example: "Show me failed jobs today" or "Which jobs failed this week?"'
RETURN
    SELECT 
        jrt.workspace_id,
        jrt.job_id,
        j.name AS job_name,
        jrt.run_id,
        jrt.result_state,
        jrt.termination_code,
        jrt.run_as,
        jrt.period_start_time AS start_time,
        jrt.period_end_time AS end_time,
        TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time) AS duration_minutes,
        COALESCE(u.failure_cost, 0) AS failure_cost
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
        ON jrt.job_id = j.job_id AND j.is_current = TRUE
    LEFT JOIN (
        SELECT job_id, run_id, SUM(usage_quantity * COALESCE(list_price, 0)) AS failure_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE job_id IS NOT NULL AND job_run_id IS NOT NULL
        GROUP BY job_id, run_id
    ) u ON jrt.job_id = u.job_id AND jrt.run_id = u.run_id
    WHERE jrt.result_state IN ('ERROR', 'FAILED', 'TIMED_OUT')
        AND CAST(jrt.period_start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (workspace_filter = 'ALL' OR jrt.workspace_id = workspace_filter)
    ORDER BY jrt.period_start_time DESC;
```

#### TVF 2.2: get_job_success_rate

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_success_rate(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    min_runs INT DEFAULT 5 COMMENT 'Minimum runs to include job'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_as STRING COMMENT 'Primary job owner',
    total_runs INT COMMENT 'Total number of runs',
    successful_runs INT COMMENT 'Number of successful runs',
    failed_runs INT COMMENT 'Number of failed runs',
    success_rate DOUBLE COMMENT 'Success rate percentage',
    avg_duration_minutes DOUBLE COMMENT 'Average run duration',
    total_cost DOUBLE COMMENT 'Total cost of all runs'
)
COMMENT 'LLM: Returns job success rates and reliability metrics.
Use for identifying unreliable jobs and reliability reporting.
Example: "What is our job success rate?" or "Which jobs have the lowest success rate?"'
RETURN
    WITH job_stats AS (
        SELECT 
            jrt.job_id,
            j.name AS job_name,
            FIRST(jrt.run_as, TRUE) AS run_as,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN jrt.result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful_runs,
            SUM(CASE WHEN jrt.result_state IN ('ERROR', 'FAILED', 'TIMED_OUT') THEN 1 ELSE 0 END) AS failed_runs,
            AVG(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time)) AS avg_duration_minutes
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.result_state IS NOT NULL
            AND CAST(jrt.period_start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY jrt.job_id, j.name
    ),
    with_cost AS (
        SELECT 
            js.*,
            (successful_runs / NULLIF(total_runs, 0)) * 100 AS success_rate,
            COALESCE(u.total_cost, 0) AS total_cost
        FROM job_stats js
        LEFT JOIN (
            SELECT job_id, SUM(usage_quantity * COALESCE(list_price, 0)) AS total_cost
            FROM ${catalog}.${gold_schema}.fact_usage
            WHERE job_id IS NOT NULL
            GROUP BY job_id
        ) u ON js.job_id = u.job_id
    )
    SELECT * FROM with_cost
    WHERE total_runs >= min_runs
    ORDER BY success_rate ASC, total_cost DESC;
```

#### TVF 2.3: get_most_expensive_jobs

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_most_expensive_jobs(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 25 COMMENT 'Number of top jobs to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Cost rank',
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_as STRING COMMENT 'Job owner',
    run_count INT COMMENT 'Number of runs',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    avg_cost_per_run DOUBLE COMMENT 'Average cost per run',
    last_run_date DATE COMMENT 'Date of last run'
)
COMMENT 'LLM: Returns the most expensive jobs by total cost.
Use for cost optimization and identifying expensive workloads.
Example: "What are our most expensive jobs?" or "Which jobs cost the most?"'
RETURN
    WITH job_costs AS (
        SELECT 
            u.job_id,
            j.name AS job_name,
            FIRST(u.run_as, TRUE) AS run_as,
            COUNT(DISTINCT u.job_run_id) AS run_count,
            SUM(u.usage_quantity * COALESCE(u.list_price, 0)) AS total_cost,
            MAX(u.usage_date) AS last_run_date
        FROM ${catalog}.${gold_schema}.fact_usage u
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
            ON u.job_id = j.job_id AND j.is_current = TRUE
        WHERE u.job_id IS NOT NULL
            AND u.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY u.job_id, j.name
    ),
    ranked AS (
        SELECT *,
            total_cost / NULLIF(run_count, 0) AS avg_cost_per_run,
            ROW_NUMBER() OVER (ORDER BY total_cost DESC) AS rank
        FROM job_costs
    )
    SELECT rank, job_id, job_name, run_as, run_count, total_cost, avg_cost_per_run, last_run_date
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;
```

#### TVF 2.4: get_job_duration_percentiles

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_duration_percentiles(
    job_name_filter STRING DEFAULT 'ALL' COMMENT 'Job name filter, or ALL',
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_count INT COMMENT 'Number of runs analyzed',
    avg_duration_min DOUBLE COMMENT 'Average duration in minutes',
    p50_duration_min DOUBLE COMMENT 'Median (50th percentile) duration',
    p75_duration_min DOUBLE COMMENT '75th percentile duration',
    p90_duration_min DOUBLE COMMENT '90th percentile duration',
    p99_duration_min DOUBLE COMMENT '99th percentile duration',
    max_duration_min DOUBLE COMMENT 'Maximum duration'
)
COMMENT 'LLM: Returns job duration percentiles for performance analysis.
Use for SLA planning, identifying outliers, and capacity planning.
Example: "What are the P99 job durations?" or "Show me job duration percentiles"'
RETURN
    SELECT 
        jrt.job_id,
        j.name AS job_name,
        COUNT(*) AS run_count,
        AVG(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time)) AS avg_duration_min,
        PERCENTILE(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time), 0.5) AS p50_duration_min,
        PERCENTILE(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time), 0.75) AS p75_duration_min,
        PERCENTILE(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time), 0.90) AS p90_duration_min,
        PERCENTILE(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time), 0.99) AS p99_duration_min,
        MAX(TIMESTAMPDIFF(MINUTE, jrt.period_start_time, jrt.period_end_time)) AS max_duration_min
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
        ON jrt.job_id = j.job_id AND j.is_current = TRUE
    WHERE jrt.result_state IS NOT NULL
        AND jrt.period_start_time >= CURRENT_DATE() - INTERVAL days_back DAY
        AND (job_name_filter = 'ALL' OR j.name = job_name_filter)
    GROUP BY jrt.job_id, j.name
    HAVING COUNT(*) >= 5
    ORDER BY p99_duration_min DESC;
```

#### TVF 2.5: get_job_repair_costs

**Reference:** [Microsoft Learn - Jobs Cost Operational Health](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost#operational-health-queries)

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_repair_costs(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 20 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Rank by repair cost',
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_as STRING COMMENT 'Job owner',
    repair_count INT COMMENT 'Number of repairs (retries)',
    repair_cost DOUBLE COMMENT 'Total cost of repair runs',
    repair_time_seconds BIGINT COMMENT 'Total time spent on repairs in seconds'
)
COMMENT 'LLM: Returns jobs with highest repair (retry) costs.
Use for identifying jobs with reliability issues causing wasted spend.
Example: "Which jobs have the highest repair costs?" or "Show me job retry costs"'
RETURN
    WITH job_run_timeline_with_cost AS (
        SELECT
            t1.*,
            t2.job_id,
            t2.run_id,
            t1.identity_metadata.run_as as run_as,
            t2.result_state,
            t1.usage_quantity * list_prices.pricing.default as list_cost
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
            AND t1.usage_start_time >= list_prices.price_start_time
            AND (t1.usage_end_time <= list_prices.price_end_time OR list_prices.price_end_time IS NULL)
        WHERE t1.billing_origin_product = 'JOBS'
            AND t1.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    ),
    repaired_runs AS (
        SELECT workspace_id, job_id, run_id, COUNT(*) AS cnt
        FROM system.lakeflow.job_run_timeline
        WHERE result_state IS NOT NULL
        GROUP BY ALL
        HAVING cnt > 1
    ),
    successful_repairs AS (
        SELECT t1.workspace_id, t1.job_id, t1.run_id, MAX(t1.period_end_time) AS period_end_time
        FROM system.lakeflow.job_run_timeline t1
        JOIN repaired_runs t2 USING (workspace_id, job_id, run_id)
        WHERE t1.result_state = 'SUCCEEDED'
        GROUP BY ALL
    ),
    cost_per_unsuccessful AS (
        SELECT workspace_id, job_id, run_id, 
               FIRST(run_as, TRUE) AS run_as,
               SUM(list_cost) AS repair_cost
        FROM job_run_timeline_with_cost
        WHERE result_state != 'SUCCEEDED'
        GROUP BY ALL
    ),
    most_recent_jobs AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
        FROM system.lakeflow.jobs QUALIFY rn = 1
    ),
    combined AS (
        SELECT 
            t3.name AS job_name,
            t1.job_id,
            FIRST(t4.run_as, TRUE) AS run_as,
            SUM(t1.cnt - 1) AS repair_count,
            SUM(t4.repair_cost) AS repair_cost,
            SUM(CAST(t2.period_end_time - MIN(t5.period_end_time) AS LONG)) AS repair_time_seconds
        FROM repaired_runs t1
        LEFT JOIN successful_repairs t2 USING (workspace_id, job_id, run_id)
        LEFT JOIN most_recent_jobs t3 USING (workspace_id, job_id)
        LEFT JOIN cost_per_unsuccessful t4 USING (workspace_id, job_id, run_id)
        LEFT JOIN system.lakeflow.job_run_timeline t5 USING (workspace_id, job_id, run_id)
        WHERE t5.result_state IS NOT NULL
        GROUP BY t3.name, t1.job_id
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY repair_cost DESC) AS rank
        FROM combined
    )
    SELECT rank, job_id, job_name, run_as, repair_count, repair_cost, repair_time_seconds
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;
```

#### TVF 2.6: get_job_spend_trend_analysis

**Reference:** [Microsoft Learn - Cost Observability Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost#cost-observability-queries)

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_spend_trend_analysis(
    days_back INT DEFAULT 14 COMMENT 'Number of days to analyze (for week-over-week comparison)',
    top_n INT DEFAULT 100 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    job_name STRING COMMENT 'Job name',
    workspace_id STRING COMMENT 'Workspace ID',
    job_id STRING COMMENT 'Job ID',
    sku_name STRING COMMENT 'SKU being used',
    run_as STRING COMMENT 'Job owner',
    last_7_day_spend DOUBLE COMMENT 'Spend in last 7 days',
    prior_7_day_spend DOUBLE COMMENT 'Spend in prior 7 days',
    last_7_day_growth DOUBLE COMMENT 'Absolute growth in spend',
    last_7_day_growth_pct DOUBLE COMMENT 'Percentage growth in spend'
)
COMMENT 'LLM: Identifies jobs with highest increase in cost spend week-over-week.
Use for cost anomaly detection and spend trend analysis.
Example: "Which jobs have the highest cost growth?" or "Show spending trends"'
RETURN
    WITH job_run_timeline_with_cost AS (
        SELECT
            t1.*,
            t1.usage_metadata.job_id AS job_id,
            t1.identity_metadata.run_as AS run_as,
            t1.usage_quantity * list_prices.pricing.default AS list_cost
        FROM system.billing.usage t1
        INNER JOIN system.billing.list_prices list_prices
            ON t1.cloud = list_prices.cloud
            AND t1.sku_name = list_prices.sku_name
            AND t1.usage_start_time >= list_prices.price_start_time
            AND (t1.usage_end_time <= list_prices.price_end_time OR list_prices.price_end_time IS NULL)
        WHERE t1.billing_origin_product = 'JOBS'
            AND t1.usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
    ),
    most_recent_jobs AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
        FROM system.lakeflow.jobs QUALIFY rn = 1
    ),
    aggregated AS (
        SELECT
            workspace_id,
            job_id,
            run_as,
            sku_name,
            SUM(list_cost) AS spend,
            SUM(CASE WHEN usage_end_time BETWEEN date_add(current_date(), -8) AND date_add(current_date(), -1) 
                     THEN list_cost ELSE 0 END) AS last_7_day_spend,
            SUM(CASE WHEN usage_end_time BETWEEN date_add(current_date(), -15) AND date_add(current_date(), -8) 
                     THEN list_cost ELSE 0 END) AS prior_7_day_spend
        FROM job_run_timeline_with_cost
        GROUP BY ALL
    ),
    with_growth AS (
        SELECT 
            t2.name AS job_name,
            t1.workspace_id,
            t1.job_id,
            t1.sku_name,
            t1.run_as,
            t1.last_7_day_spend,
            t1.prior_7_day_spend,
            t1.last_7_day_spend - t1.prior_7_day_spend AS last_7_day_growth,
            try_divide((t1.last_7_day_spend - t1.prior_7_day_spend), t1.prior_7_day_spend) * 100 AS last_7_day_growth_pct
        FROM aggregated t1
        LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY last_7_day_growth DESC) AS rank
        FROM with_growth
    )
    SELECT job_name, workspace_id, job_id, sku_name, run_as, 
           last_7_day_spend, prior_7_day_spend, last_7_day_growth, last_7_day_growth_pct
    FROM ranked
    WHERE rank <= top_n
    ORDER BY last_7_day_growth DESC;
```

#### TVF 2.7: get_job_failure_costs

**Reference:** [Microsoft Learn - Operational Health Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost#operational-health-queries)

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_failure_costs(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 50 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    job_name STRING COMMENT 'Job name',
    workspace_id STRING COMMENT 'Workspace ID',
    job_id STRING COMMENT 'Job ID',
    run_as STRING COMMENT 'Job owner',
    total_runs INT COMMENT 'Total number of runs',
    failures INT COMMENT 'Number of failed runs',
    success_ratio DOUBLE COMMENT 'Success rate percentage',
    failure_list_cost DOUBLE COMMENT 'Cost of failed runs',
    last_seen_date TIMESTAMP COMMENT 'Last run timestamp'
)
COMMENT 'LLM: Returns jobs with high failure counts and their associated costs.
Use for identifying unreliable jobs that waste spend.
Example: "Which failing jobs cost the most?" or "Show job failure costs"'
RETURN
    WITH job_run_timeline_with_cost AS (
        SELECT
            t1.*,
            t1.identity_metadata.run_as AS run_as,
            t2.job_id,
            t2.run_id,
            t2.result_state,
            t1.usage_quantity * list_prices.pricing.default AS list_cost
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
            AND t1.usage_start_time >= list_prices.price_start_time
            AND (t1.usage_end_time <= list_prices.price_end_time OR list_prices.price_end_time IS NULL)
        WHERE t1.billing_origin_product = 'JOBS'
            AND t1.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    ),
    cost_per_status_agg AS (
        SELECT workspace_id, job_id, FIRST(run_as, TRUE) AS run_as, SUM(list_cost) AS list_cost
        FROM job_run_timeline_with_cost
        WHERE result_state IN ('ERROR', 'FAILED', 'TIMED_OUT')
        GROUP BY ALL
    ),
    terminal_statuses AS (
        SELECT
            workspace_id, job_id,
            CASE WHEN result_state IN ('ERROR', 'FAILED', 'TIMED_OUT') THEN 1 ELSE 0 END AS is_failure,
            period_end_time AS last_seen_date
        FROM system.lakeflow.job_run_timeline
        WHERE result_state IS NOT NULL
            AND period_end_time BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    ),
    most_recent_jobs AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
        FROM system.lakeflow.jobs QUALIFY rn = 1
    ),
    aggregated AS (
        SELECT
            FIRST(t2.name) AS job_name,
            t1.workspace_id,
            t1.job_id,
            t3.run_as,
            COUNT(*) AS total_runs,
            SUM(is_failure) AS failures,
            (1 - COALESCE(try_divide(SUM(is_failure), COUNT(*)), 0)) * 100 AS success_ratio,
            FIRST(t3.list_cost) AS failure_list_cost,
            MAX(t1.last_seen_date) AS last_seen_date
        FROM terminal_statuses t1
        LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
        LEFT JOIN cost_per_status_agg t3 USING (workspace_id, job_id)
        GROUP BY ALL
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY failures DESC) AS rank
        FROM aggregated
    )
    SELECT job_name, workspace_id, job_id, run_as, total_runs, failures, 
           success_ratio, failure_list_cost, last_seen_date
    FROM ranked
    WHERE rank <= top_n
    ORDER BY failures DESC;
```

#### TVF 2.8: get_job_run_duration_analysis

**Reference:** [Microsoft Learn - Job Run Timeline Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs#detailed-schema-reference)

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_run_duration_analysis(
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze',
    min_runs INT DEFAULT 5 COMMENT 'Minimum number of runs to include job',
    top_n INT DEFAULT 100 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    workspace_id STRING COMMENT 'Workspace ID',
    job_id STRING COMMENT 'Job ID',
    total_runs INT COMMENT 'Total number of runs',
    mean_seconds DOUBLE COMMENT 'Mean run duration in seconds',
    avg_seconds DOUBLE COMMENT 'Average run duration in seconds',
    p90_seconds DOUBLE COMMENT '90th percentile duration',
    p95_seconds DOUBLE COMMENT '95th percentile duration'
)
COMMENT 'LLM: Returns job run duration statistics with percentiles.
Use for SLA analysis and identifying slow jobs.
Example: "What are the P95 job durations?" or "Which jobs take the longest?"'
RETURN
    WITH job_run_duration AS (
        SELECT
            workspace_id,
            job_id,
            run_id,
            CAST(SUM(period_end_time - period_start_time) AS LONG) AS duration
        FROM system.lakeflow.job_run_timeline
        WHERE period_start_time > CURRENT_TIMESTAMP() - INTERVAL days_back DAYS
        GROUP BY ALL
    ),
    aggregated AS (
        SELECT
            t1.workspace_id,
            t1.job_id,
            COUNT(DISTINCT t1.run_id) AS total_runs,
            MEAN(t1.duration) AS mean_seconds,
            AVG(t1.duration) AS avg_seconds,
            PERCENTILE(t1.duration, 0.9) AS p90_seconds,
            PERCENTILE(t1.duration, 0.95) AS p95_seconds
        FROM job_run_duration t1
        GROUP BY ALL
        HAVING COUNT(DISTINCT t1.run_id) >= min_runs
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY mean_seconds DESC) AS rank
        FROM aggregated
    )
    SELECT workspace_id, job_id, total_runs, mean_seconds, avg_seconds, p90_seconds, p95_seconds
    FROM ranked
    WHERE rank <= top_n
    ORDER BY mean_seconds DESC;
```

---

### Domain 3: Query Performance (6 TVFs)

#### TVF 3.1: get_slow_queries

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_slow_queries(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    min_duration_seconds INT DEFAULT 300 COMMENT 'Minimum duration threshold in seconds'
)
RETURNS TABLE(
    statement_id STRING COMMENT 'Query statement ID',
    warehouse_id STRING COMMENT 'SQL Warehouse ID',
    warehouse_name STRING COMMENT 'SQL Warehouse name',
    executed_by STRING COMMENT 'User who executed the query',
    statement_type STRING COMMENT 'Query type (SELECT, INSERT, etc.)',
    execution_status STRING COMMENT 'Execution status',
    duration_seconds DOUBLE COMMENT 'Query duration in seconds',
    read_bytes_gb DOUBLE COMMENT 'Data read in GB',
    spill_bytes_gb DOUBLE COMMENT 'Data spilled to disk in GB',
    start_time TIMESTAMP COMMENT 'Query start time',
    query_text STRING COMMENT 'First 500 chars of query'
)
COMMENT 'LLM: Returns queries exceeding duration threshold (slow queries).
Use for query optimization, identifying inefficient queries.
Example: "Show me slow queries today" or "Which queries took more than 5 minutes?"'
RETURN
    SELECT 
        qh.statement_id,
        qh.warehouse_id,
        w.warehouse_name,
        qh.executed_by,
        qh.statement_type,
        qh.execution_status,
        qh.total_duration_ms / 1000 AS duration_seconds,
        qh.read_bytes / (1024*1024*1024) AS read_bytes_gb,
        COALESCE(qh.spill_local_bytes + qh.spill_remote_bytes, 0) / (1024*1024*1024) AS spill_bytes_gb,
        qh.start_time,
        SUBSTRING(qh.statement_text, 1, 500) AS query_text
    FROM ${catalog}.${gold_schema}.fact_query_history qh
    LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w 
        ON qh.warehouse_id = w.warehouse_id AND w.is_current = TRUE
    WHERE CAST(qh.start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND qh.total_duration_ms / 1000 >= min_duration_seconds
    ORDER BY duration_seconds DESC;
```

#### TVF 3.2: get_warehouse_utilization

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_warehouse_utilization(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    warehouse_filter STRING DEFAULT 'ALL' COMMENT 'Warehouse ID filter, or ALL'
)
RETURNS TABLE(
    warehouse_id STRING COMMENT 'SQL Warehouse ID',
    warehouse_name STRING COMMENT 'SQL Warehouse name',
    warehouse_size STRING COMMENT 'Warehouse size (XS to 4XL)',
    total_queries INT COMMENT 'Total queries executed',
    total_dbu DOUBLE COMMENT 'Total DBUs consumed',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    avg_query_duration_sec DOUBLE COMMENT 'Average query duration',
    avg_queue_time_sec DOUBLE COMMENT 'Average queue wait time',
    queue_time_pct DOUBLE COMMENT 'Percentage of time spent queueing',
    peak_concurrent_queries INT COMMENT 'Maximum concurrent queries'
)
COMMENT 'LLM: Returns SQL warehouse utilization metrics.
Use for warehouse sizing, cost optimization, and capacity planning.
Example: "Show warehouse utilization" or "Which warehouse is most used?"'
RETURN
    WITH warehouse_usage AS (
        SELECT 
            qh.warehouse_id,
            w.warehouse_name,
            w.warehouse_size,
            COUNT(*) AS total_queries,
            AVG(qh.total_duration_ms / 1000) AS avg_query_duration_sec,
            AVG(qh.waiting_at_capacity_duration_ms / 1000) AS avg_queue_time_sec
        FROM ${catalog}.${gold_schema}.fact_query_history qh
        LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w 
            ON qh.warehouse_id = w.warehouse_id AND w.is_current = TRUE
        WHERE CAST(qh.start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND (warehouse_filter = 'ALL' OR qh.warehouse_id = warehouse_filter)
        GROUP BY qh.warehouse_id, w.warehouse_name, w.warehouse_size
    ),
    warehouse_cost AS (
        SELECT 
            warehouse_id,
            SUM(usage_quantity) AS total_dbu,
            SUM(usage_quantity * COALESCE(list_price, 0)) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE warehouse_id IS NOT NULL
            AND usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY warehouse_id
    )
    SELECT 
        wu.warehouse_id,
        wu.warehouse_name,
        wu.warehouse_size,
        wu.total_queries,
        COALESCE(wc.total_dbu, 0) AS total_dbu,
        COALESCE(wc.total_cost, 0) AS total_cost,
        wu.avg_query_duration_sec,
        wu.avg_queue_time_sec,
        (wu.avg_queue_time_sec / NULLIF(wu.avg_query_duration_sec + wu.avg_queue_time_sec, 0)) * 100 AS queue_time_pct,
        0 AS peak_concurrent_queries  -- Would need query-level data
    FROM warehouse_usage wu
    LEFT JOIN warehouse_cost wc ON wu.warehouse_id = wc.warehouse_id
    ORDER BY total_cost DESC;
```

---

### Domain 4: Security & Audit (7 TVFs)

#### TVF 4.0: get_table_access_audit

**Reference:** [Microsoft Learn - Audit Logs Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs#sample-queries)

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_table_access_audit(
    table_full_name STRING COMMENT 'Full table name (catalog.schema.table)',
    days_back INT DEFAULT 7 COMMENT 'Number of days to look back'
)
RETURNS TABLE(
    user_email STRING COMMENT 'User who accessed the table',
    table_name STRING COMMENT 'Table that was accessed',
    access_type STRING COMMENT 'Type of access (createTable, getTable, deleteTable)',
    access_time TIMESTAMP COMMENT 'Time of access'
)
COMMENT 'LLM: Returns users who accessed a specific table within a time range.
Use for security auditing, compliance reporting, and access reviews.
Example: "Who accessed this table last week?" or "Show table access audit"'
RETURN
    SELECT
        user_identity.email AS user_email,
        IFNULL(request_params.full_name_arg, request_params.name) AS table_name,
        action_name AS access_type,
        event_time AS access_time
    FROM system.access.audit
    WHERE (
        request_params.full_name_arg = table_full_name
        OR (
            request_params.name = SPLIT(table_full_name, '.')[2]
            AND request_params.schema_name = SPLIT(table_full_name, '.')[1]
        )
    )
    AND action_name IN ('createTable', 'getTable', 'deleteTable', 'commandSubmit')
    AND event_date > now() - INTERVAL days_back DAY
    ORDER BY event_date DESC;
```

#### TVF 4.1: get_user_activity_summary

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_user_activity_summary(
    user_email STRING COMMENT 'User email to analyze',
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze'
)
RETURNS TABLE(
    activity_date DATE COMMENT 'Date of activity',
    read_events INT COMMENT 'Number of table read events',
    write_events INT COMMENT 'Number of table write events',
    tables_accessed INT COMMENT 'Unique tables accessed',
    queries_executed INT COMMENT 'Number of queries run',
    compute_cost DOUBLE COMMENT 'Compute cost attributed to user'
)
COMMENT 'LLM: Returns activity summary for a specific user.
Use for user behavior analysis, audit reporting, and access reviews.
Example: "Show me activity for user@company.com" or "What did this user do last month?"'
RETURN
    SELECT 
        CAST(event_time AS DATE) AS activity_date,
        SUM(CASE WHEN source_table_full_name IS NOT NULL THEN 1 ELSE 0 END) AS read_events,
        SUM(CASE WHEN target_table_full_name IS NOT NULL THEN 1 ELSE 0 END) AS write_events,
        COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name)) AS tables_accessed,
        COUNT(DISTINCT statement_id) AS queries_executed,
        0.0 AS compute_cost  -- Would need to join with usage
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE created_by = user_email
        AND event_date >= CURRENT_DATE() - INTERVAL days_back DAY
    GROUP BY CAST(event_time AS DATE)
    ORDER BY activity_date DESC;
```

#### TVF 4.2: get_sensitive_table_access

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_sensitive_table_access(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    table_pattern STRING DEFAULT '%PII%' COMMENT 'Table name pattern to match'
)
RETURNS TABLE(
    accessed_by STRING COMMENT 'User who accessed the table',
    table_full_name STRING COMMENT 'Full table name accessed',
    access_type STRING COMMENT 'READ or WRITE',
    access_count INT COMMENT 'Number of times accessed',
    first_access TIMESTAMP COMMENT 'First access time',
    last_access TIMESTAMP COMMENT 'Last access time'
)
COMMENT 'LLM: Returns access events to sensitive tables matching a pattern.
Use for security auditing and compliance monitoring.
Example: "Who accessed PII tables this week?" or "Show sensitive table access"'
RETURN
    SELECT 
        created_by AS accessed_by,
        COALESCE(source_table_full_name, target_table_full_name) AS table_full_name,
        CASE 
            WHEN target_table_full_name IS NOT NULL THEN 'WRITE'
            ELSE 'READ'
        END AS access_type,
        COUNT(*) AS access_count,
        MIN(event_time) AS first_access,
        MAX(event_time) AS last_access
    FROM ${catalog}.${gold_schema}.fact_table_lineage
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (source_table_full_name LIKE table_pattern 
             OR target_table_full_name LIKE table_pattern)
    GROUP BY 1, 2, 3
    ORDER BY access_count DESC;
```

---

### Domain 5: Compute & Clusters (4 TVFs)

#### TVF 5.1: get_cluster_utilization

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cluster_utilization(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    min_hours INT DEFAULT 1 COMMENT 'Minimum hours of runtime to include'
)
RETURNS TABLE(
    cluster_id STRING COMMENT 'Cluster ID',
    cluster_name STRING COMMENT 'Cluster name',
    cluster_type STRING COMMENT 'Cluster type (JOB/ALL_PURPOSE)',
    owned_by STRING COMMENT 'Cluster owner',
    total_hours DOUBLE COMMENT 'Total runtime hours',
    avg_cpu_utilization DOUBLE COMMENT 'Average CPU utilization %',
    avg_memory_utilization DOUBLE COMMENT 'Average memory utilization %',
    peak_cpu DOUBLE COMMENT 'Peak CPU utilization %',
    peak_memory DOUBLE COMMENT 'Peak memory utilization %',
    total_cost DOUBLE COMMENT 'Total cost in USD'
)
COMMENT 'LLM: Returns cluster utilization metrics for optimization.
Use for identifying underutilized clusters and cost optimization.
Example: "Show cluster utilization" or "Which clusters are underutilized?"'
RETURN
    WITH cluster_metrics AS (
        SELECT 
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            SUM(TIMESTAMPDIFF(HOUR, nt.start_time, nt.end_time)) AS total_hours,
            AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_utilization,
            AVG(nt.mem_used_percent) AS avg_memory_utilization,
            MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS peak_cpu,
            MAX(nt.mem_used_percent) AS peak_memory
        FROM ${catalog}.${gold_schema}.fact_node_timeline nt
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c 
            ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
        WHERE CAST(nt.start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
    ),
    cluster_cost AS (
        SELECT cluster_id, SUM(usage_quantity * COALESCE(list_price, 0)) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE cluster_id IS NOT NULL
            AND usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY cluster_id
    )
    SELECT 
        cm.cluster_id,
        cm.cluster_name,
        cm.cluster_type,
        cm.owned_by,
        cm.total_hours,
        cm.avg_cpu_utilization,
        cm.avg_memory_utilization,
        cm.peak_cpu,
        cm.peak_memory,
        COALESCE(cc.total_cost, 0) AS total_cost
    FROM cluster_metrics cm
    LEFT JOIN cluster_cost cc ON cm.cluster_id = cc.cluster_id
    WHERE cm.total_hours >= min_hours
    ORDER BY total_cost DESC;
```

---

### Domain 6: Compute & Clusters (Additional TVFs)

#### TVF 6.1: get_cluster_resource_metrics

**Reference:** [Microsoft Learn - Compute Sample Queries](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute#sample-queries)

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cluster_resource_metrics(
    days_back INT DEFAULT 1 COMMENT 'Number of days to analyze',
    top_n INT DEFAULT 50 COMMENT 'Number of clusters to return'
)
RETURNS TABLE(
    cluster_id STRING COMMENT 'Cluster identifier',
    is_driver BOOLEAN COMMENT 'Whether this is the driver node',
    avg_cpu_utilization DOUBLE COMMENT 'Average CPU utilization %',
    peak_cpu_utilization DOUBLE COMMENT 'Peak CPU utilization %',
    avg_cpu_wait DOUBLE COMMENT 'Average CPU wait % (IO bound indicator)',
    max_cpu_wait DOUBLE COMMENT 'Maximum CPU wait %',
    avg_memory_utilization DOUBLE COMMENT 'Average memory utilization %',
    max_memory_utilization DOUBLE COMMENT 'Maximum memory utilization %',
    avg_network_mb_received DOUBLE COMMENT 'Avg network MB received per minute',
    avg_network_mb_sent DOUBLE COMMENT 'Avg network MB sent per minute'
)
COMMENT 'LLM: Returns detailed cluster resource utilization metrics.
Use for right-sizing clusters, identifying bottlenecks, and capacity planning.
Example: "Show cluster CPU and memory utilization" or "Which clusters have high CPU wait?"'
RETURN
    WITH ranked AS (
        SELECT
            DISTINCT cluster_id,
            driver AS is_driver,
            AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu_utilization,
            MAX(cpu_user_percent + cpu_system_percent) AS peak_cpu_utilization,
            AVG(cpu_wait_percent) AS avg_cpu_wait,
            MAX(cpu_wait_percent) AS max_cpu_wait,
            AVG(mem_used_percent) AS avg_memory_utilization,
            MAX(mem_used_percent) AS max_memory_utilization,
            AVG(network_received_bytes) / (1024 * 1024) AS avg_network_mb_received,
            AVG(network_sent_bytes) / (1024 * 1024) AS avg_network_mb_sent,
            ROW_NUMBER() OVER (ORDER BY AVG(cpu_user_percent + cpu_system_percent) DESC) AS rank
        FROM system.compute.node_timeline
        WHERE start_time >= date_add(now(), -days_back)
        GROUP BY cluster_id, driver
    )
    SELECT cluster_id, is_driver, avg_cpu_utilization, peak_cpu_utilization,
           avg_cpu_wait, max_cpu_wait, avg_memory_utilization, max_memory_utilization,
           avg_network_mb_received, avg_network_mb_sent
    FROM ranked
    WHERE rank <= top_n
    ORDER BY avg_cpu_utilization DESC;
```

#### TVF 6.2: get_underutilized_clusters

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_underutilized_clusters(
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze',
    cpu_threshold DOUBLE DEFAULT 30.0 COMMENT 'CPU utilization threshold (below = underutilized)',
    min_hours INT DEFAULT 10 COMMENT 'Minimum runtime hours to include'
)
RETURNS TABLE(
    cluster_id STRING COMMENT 'Cluster identifier',
    cluster_name STRING COMMENT 'Cluster name',
    cluster_type STRING COMMENT 'Cluster type (JOB/ALL_PURPOSE)',
    owned_by STRING COMMENT 'Cluster owner',
    avg_cpu_pct DOUBLE COMMENT 'Average CPU utilization %',
    avg_mem_pct DOUBLE COMMENT 'Average memory utilization %',
    total_hours DOUBLE COMMENT 'Total runtime hours',
    total_cost DOUBLE COMMENT 'Total estimated cost',
    potential_savings DOUBLE COMMENT 'Potential cost savings if right-sized'
)
COMMENT 'LLM: Returns underutilized clusters with cost savings potential.
Use for cost optimization and right-sizing recommendations.
Example: "Which clusters are underutilized?" or "Show potential cost savings"'
RETURN
    WITH cluster_metrics AS (
        SELECT 
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            ROUND(AVG(nt.cpu_user_percent + nt.cpu_system_percent), 1) AS avg_cpu_pct,
            ROUND(AVG(nt.mem_used_percent), 1) AS avg_mem_pct,
            SUM(TIMESTAMPDIFF(HOUR, nt.start_time, nt.end_time)) AS total_hours
        FROM system.compute.node_timeline nt
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c 
            ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
        WHERE nt.start_time >= CURRENT_DATE() - INTERVAL days_back DAYS
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
        HAVING total_hours >= min_hours
    ),
    cluster_cost AS (
        SELECT cluster_id, SUM(usage_quantity * COALESCE(list_price, 0)) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAYS
        GROUP BY cluster_id
    )
    SELECT 
        cm.cluster_id,
        cm.cluster_name,
        cm.cluster_type,
        cm.owned_by,
        cm.avg_cpu_pct,
        cm.avg_mem_pct,
        cm.total_hours,
        COALESCE(cc.total_cost, 0) AS total_cost,
        CASE 
            WHEN cm.avg_cpu_pct < 20 THEN cc.total_cost * 0.5
            WHEN cm.avg_cpu_pct < 30 THEN cc.total_cost * 0.3
            ELSE 0
        END AS potential_savings
    FROM cluster_metrics cm
    LEFT JOIN cluster_cost cc ON cm.cluster_id = cc.cluster_id
    WHERE cm.avg_cpu_pct < cpu_threshold
    ORDER BY potential_savings DESC;
```

---

---

### Domain 7: Job Optimization (Advanced TVFs)

**Source:** Jobs System Tables Dashboard, Serverless Cost Observability Dashboard

#### TVF 7.1: get_jobs_stale_datasets

**Insight:** Identifies jobs producing datasets that are never consumed - wasted compute.

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_jobs_stale_datasets(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze'
)
RETURNS TABLE(
    workspace_id STRING COMMENT 'Workspace ID',
    job_name STRING COMMENT 'Job name',
    job_id STRING COMMENT 'Job ID',
    run_as STRING COMMENT 'Job owner',
    not_used_datasets ARRAY<STRING> COMMENT 'Datasets produced but never consumed',
    used_datasets ARRAY<STRING> COMMENT 'Datasets that are consumed',
    last_seen_job_date DATE COMMENT 'Last job run date',
    runs INT COMMENT 'Number of runs',
    list_cost_30d DOUBLE COMMENT '30-day list cost'
)
COMMENT 'LLM: Finds jobs producing datasets that are never consumed.
Use for identifying wasted compute and data cleanup opportunities.
Example: "Which jobs produce unused data?" or "Show stale dataset producers"'
RETURN
    WITH producers AS (
        SELECT workspace_id, entity_id AS job_id, target_table_full_name, created_by
        FROM system.access.table_lineage
        WHERE entity_type = 'JOB' 
            AND target_table_full_name IS NOT NULL
            AND event_date > CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY ALL
    ),
    consumers AS (
        SELECT workspace_id, source_table_full_name
        FROM system.access.table_lineage
        WHERE source_table_full_name IS NOT NULL 
            AND event_date > CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY ALL
    ),
    jobs_with_datasets AS (
        SELECT workspace_id, entity_id AS job_id, collect_set(target_table_full_name) AS populated_sets
        FROM system.access.table_lineage
        WHERE entity_type = 'JOB' AND target_table_full_name IS NOT NULL
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
        SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
        FROM system.lakeflow.jobs QUALIFY rn = 1
    )
    SELECT 
        t1.workspace_id,
        t5.name AS job_name,
        t1.job_id,
        t4.run_as,
        collect_set(target_table_full_name) AS not_used_datasets,
        array_except(FIRST(t3.populated_sets), collect_set(target_table_full_name)) AS used_datasets,
        DATE(MAX(t2.period_end_time)) AS last_seen_job_date,
        COUNT(DISTINCT t2.run_id) AS runs,
        FIRST(t4.list_cost) AS list_cost_30d
    FROM jobs_without_consumption t1
    INNER JOIN jobs_with_datasets t3 USING (workspace_id, job_id)
    LEFT JOIN system.lakeflow.job_run_timeline t2 USING (workspace_id, job_id)
    LEFT JOIN (
        SELECT workspace_id, job_id, FIRST(run_as, TRUE) AS run_as, SUM(list_cost) AS list_cost
        FROM (
            SELECT t1.workspace_id, t1.usage_metadata.job_id AS job_id, 
                   t1.identity_metadata.run_as AS run_as,
                   t1.usage_quantity * list_prices.pricing.default AS list_cost
            FROM system.billing.usage t1
            INNER JOIN system.billing.list_prices list_prices 
                ON t1.cloud = list_prices.cloud 
                AND t1.sku_name = list_prices.sku_name
            WHERE t1.sku_name LIKE '%JOBS%' AND t1.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
        )
        GROUP BY workspace_id, job_id
    ) t4 USING (workspace_id, job_id)
    LEFT JOIN most_recent_jobs t5 USING (workspace_id, job_id)
    GROUP BY ALL
    HAVING runs > 0
    ORDER BY list_cost_30d DESC, runs DESC;
```

#### TVF 7.2: get_job_cost_savings_opportunities

**Insight:** Combines CPU utilization with cost to find right-sizing opportunities.

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_cost_savings_opportunities(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze',
    top_n INT DEFAULT 25 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    workspace_id STRING COMMENT 'Workspace ID',
    job_name STRING COMMENT 'Job name',
    avg_cpu_utilization DOUBLE COMMENT 'Average CPU utilization %',
    peak_cpu_utilization DOUBLE COMMENT 'Peak CPU utilization %',
    avg_memory_utilization DOUBLE COMMENT 'Average memory utilization %',
    peak_memory_utilization DOUBLE COMMENT 'Peak memory utilization %',
    job_cost_30d DOUBLE COMMENT '30-day job cost',
    max_potential_savings DOUBLE COMMENT 'Estimated maximum savings'
)
COMMENT 'LLM: Identifies jobs with low CPU utilization for right-sizing.
Use for cost optimization recommendations based on actual resource usage.
Example: "Which jobs have right-sizing opportunities?" or "Show potential savings"'
RETURN
    WITH list_cost_per_job_cluster AS (
        SELECT
            t1.workspace_id,
            t1.usage_metadata.job_id,
            t1.usage_metadata.cluster_id,
            SUM(t1.usage_quantity * list_prices.pricing.default) AS list_cost
        FROM system.billing.usage t1
        INNER JOIN system.billing.list_prices list_prices 
            ON t1.cloud = list_prices.cloud 
            AND t1.sku_name = list_prices.sku_name
        WHERE t1.sku_name LIKE '%JOBS%'
            AND t1.sku_name NOT ILIKE '%jobs_serverless%'
            AND t1.usage_metadata.job_id IS NOT NULL
            AND t1.usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY ALL
    ),
    most_recent_jobs AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
        FROM system.lakeflow.jobs QUALIFY rn = 1
    ),
    jobs_rolling AS (
        SELECT t2.name, t1.job_id, t1.workspace_id, t1.cluster_id, SUM(list_cost) AS list_cost
        FROM list_cost_per_job_cluster t1
        LEFT JOIN most_recent_jobs t2 USING (workspace_id, job_id)
        GROUP BY ALL
    ),
    jobs_with_util AS (
        SELECT 
            jr.workspace_id, 
            jr.name AS job_name,
            AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_utilization,
            MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS peak_cpu_utilization,
            AVG(nt.mem_used_percent) AS avg_memory_utilization,
            MAX(nt.mem_used_percent) AS peak_memory_utilization,
            SUM(jr.list_cost) AS job_cost_30d
        FROM system.compute.node_timeline nt
        JOIN jobs_rolling jr ON nt.cluster_id = jr.cluster_id
        WHERE nt.start_time >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY jr.workspace_id, jr.name
    )
    SELECT 
        workspace_id,
        job_name,
        ROUND(avg_cpu_utilization, 1) AS avg_cpu_utilization,
        ROUND(peak_cpu_utilization, 1) AS peak_cpu_utilization,
        ROUND(avg_memory_utilization, 1) AS avg_memory_utilization,
        ROUND(peak_memory_utilization, 1) AS peak_memory_utilization,
        ROUND(job_cost_30d, 2) AS job_cost_30d,
        ROUND((job_cost_30d * (1 - (avg_cpu_utilization / 100))) / 2.0, 2) AS max_potential_savings
    FROM jobs_with_util
    WHERE avg_cpu_utilization < 50  -- Low utilization threshold
    ORDER BY max_potential_savings DESC
    LIMIT top_n;
```

#### TVF 7.3: get_jobs_without_autoscaling

**Insight:** Jobs with static clusters that could benefit from autoscaling.

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_jobs_without_autoscaling(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze',
    min_workers INT DEFAULT 2 COMMENT 'Minimum worker count to consider'
)
RETURNS TABLE(
    workspace_id STRING COMMENT 'Workspace ID',
    job_name STRING COMMENT 'Job name',
    job_id STRING COMMENT 'Job ID',
    run_as STRING COMMENT 'Job owner',
    list_cost DOUBLE COMMENT '30-day list cost',
    worker_count INT COMMENT 'Static worker count',
    min_autoscale_workers INT COMMENT 'Min autoscale (NULL if not set)',
    max_autoscale_workers INT COMMENT 'Max autoscale (NULL if not set)'
)
COMMENT 'LLM: Finds jobs without autoscaling that could benefit from dynamic sizing.
Use for identifying optimization opportunities for static clusters.
Example: "Which jobs dont use autoscaling?" or "Show fixed-size cluster jobs"'
RETURN
    WITH clusters AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, cluster_id ORDER BY change_time DESC) AS rn
        FROM system.compute.clusters
        WHERE cluster_source = 'JOB'
        QUALIFY rn = 1
    ),
    job_runs AS (
        SELECT t2.name, t1.job_id, t1.workspace_id, t1.cluster_id, 
               t1.run_as, SUM(list_cost) AS list_cost
        FROM (
            SELECT t1.workspace_id, t1.usage_metadata.job_id, t1.usage_metadata.cluster_id,
                   FIRST(t1.identity_metadata.run_as, TRUE) AS run_as,
                   SUM(t1.usage_quantity * list_prices.pricing.default) AS list_cost
            FROM system.billing.usage t1
            INNER JOIN system.billing.list_prices list_prices ON t1.cloud = list_prices.cloud 
                AND t1.sku_name = list_prices.sku_name
            WHERE t1.sku_name LIKE '%JOBS%' 
                AND t1.sku_name NOT LIKE '%SERVERLESS'
                AND t1.usage_metadata.job_id IS NOT NULL
                AND t1.usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            GROUP BY ALL
        ) t1
        LEFT JOIN (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
            FROM system.lakeflow.jobs QUALIFY rn = 1
        ) t2 USING (workspace_id, job_id)
        GROUP BY ALL
    )
    SELECT 
        c.workspace_id,
        jr.name AS job_name,
        jr.job_id,
        jr.run_as,
        ROUND(jr.list_cost, 2) AS list_cost,
        c.worker_count,
        c.min_autoscale_workers,
        c.max_autoscale_workers
    FROM clusters c
    JOIN job_runs jr USING (workspace_id, cluster_id)
    WHERE (c.min_autoscale_workers IS NULL OR c.max_autoscale_workers IS NULL)
        AND c.worker_count >= min_workers
    ORDER BY list_cost DESC;
```

#### TVF 7.4: get_spend_by_custom_tags

**Insight:** Cost allocation using custom tags for chargeback.

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_spend_by_custom_tags(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze',
    top_n INT DEFAULT 20 COMMENT 'Number of tag combinations to return'
)
RETURNS TABLE(
    tag_key_value STRING COMMENT 'Tag key:value combination',
    list_cost DOUBLE COMMENT 'Total list cost for this tag'
)
COMMENT 'LLM: Shows job spend broken down by custom tags for chargeback.
Use for cost allocation by team, project, or environment.
Example: "Show spend by tags" or "Cost allocation by custom tags"'
RETURN
    WITH tag_raw AS (
        SELECT 
            explode(custom_tags) AS (tag_key, tag_value),
            (usage_quantity * list_prices.pricing.default) AS list_cost
        FROM system.billing.usage t1
        INNER JOIN system.billing.list_prices list_prices 
            ON t1.cloud = list_prices.cloud 
            AND t1.sku_name = list_prices.sku_name
        WHERE t1.sku_name LIKE '%JOBS%'
            AND t1.sku_name NOT ILIKE '%jobs_serverless%'
            AND t1.usage_metadata.job_id IS NOT NULL
            AND t1.usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
    ),
    tag_spend AS (
        SELECT CONCAT(tag_key, ': ', tag_value) AS tag_key_value, SUM(list_cost) AS list_cost
        FROM tag_raw
        GROUP BY ALL
    ),
    untagged AS (
        SELECT 'Untagged' AS tag_key_value, SUM(usage_quantity * list_prices.pricing.default) AS list_cost
        FROM system.billing.usage t1
        INNER JOIN system.billing.list_prices list_prices 
            ON t1.cloud = list_prices.cloud 
            AND t1.sku_name = list_prices.sku_name
        WHERE t1.sku_name LIKE '%JOBS%'
            AND t1.sku_name NOT ILIKE '%jobs_serverless%'
            AND t1.usage_metadata.job_id IS NOT NULL
            AND t1.usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND cardinality(custom_tags) = 0
    )
    SELECT tag_key_value, ROUND(list_cost, 2) AS list_cost
    FROM (SELECT * FROM tag_spend UNION ALL SELECT * FROM untagged)
    ORDER BY list_cost DESC
    LIMIT top_n;
```

---

### Domain 8: DBR Version & Migration (TVFs)

**Source:** DBR Upgrade Managed Migration Dashboard

#### TVF 8.1: get_jobs_on_legacy_dbr

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_jobs_on_legacy_dbr(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    dbr_threshold INT DEFAULT 15 COMMENT 'DBR major version threshold (jobs below this are legacy)'
)
RETURNS TABLE(
    workspace_id STRING COMMENT 'Workspace ID',
    job_name STRING COMMENT 'Job name',
    job_id STRING COMMENT 'Job ID',
    dbr_version STRING COMMENT 'Current DBR version',
    dbr_major INT COMMENT 'Major version number',
    is_legacy BOOLEAN COMMENT 'True if below threshold'
)
COMMENT 'LLM: Finds jobs running on legacy Databricks Runtime versions.
Use for DBR upgrade planning and migration tracking.
Example: "Which jobs use old DBR?" or "Show legacy runtime jobs"'
RETURN
    WITH latest_jobs AS (
        SELECT workspace_id, job_id, name,
               ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
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
    job_runs AS (
        SELECT DISTINCT 
            jtr.workspace_id,
            lj.name AS job_name,
            jtr.job_id,
            lc.dbr_version,
            CAST(regexp_extract(COALESCE(lc.dbr_version, '0'), '^(\\d+)', 1) AS INT) AS dbr_major
        FROM system.lakeflow.job_task_run_timeline jtr
        CROSS JOIN LATERAL explode(jtr.compute_ids) AS t(cluster_id)
        INNER JOIN latest_clusters lc 
            ON jtr.workspace_id = lc.workspace_id AND t.cluster_id = lc.cluster_id
        LEFT JOIN latest_jobs lj 
            ON jtr.workspace_id = lj.workspace_id AND jtr.job_id = lj.job_id
        WHERE DATE(jtr.period_start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    )
    SELECT 
        workspace_id,
        job_name,
        job_id,
        dbr_version,
        dbr_major,
        (dbr_major < dbr_threshold) AS is_legacy
    FROM job_runs
    WHERE dbr_major > 0
    ORDER BY dbr_major ASC, job_name;
```

---

## 💰 Cost Agent: Commit Tracking & Tag Analysis TVFs (NEW)

These TVFs support the two critical FinOps use cases:
1. **Commit Amount Tracking** - Compare actual spend vs required run rate to meet Databricks commit
2. **Tag-Based Cost Attribution** - Fine-grained cost analysis using custom tags from [system.billing.usage](https://docs.databricks.com/aws/en/admin/system-tables/billing)

---

#### TVF: get_commit_vs_actual

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_commit_vs_actual(
    commit_year INT COMMENT 'Year of the commit to analyze (e.g., 2025)',
    as_of_date STRING DEFAULT NULL COMMENT 'Optional: Analysis as-of date (format: YYYY-MM-DD). Defaults to current date.'
)
RETURNS TABLE(
    month_num INT COMMENT 'Month number (1-12)',
    month_name STRING COMMENT 'Month name (January, February, etc.)',
    monthly_spend DOUBLE COMMENT 'Actual monthly spend in USD',
    ytd_spend DOUBLE COMMENT 'Year-to-date cumulative spend in USD',
    monthly_target DOUBLE COMMENT 'Required monthly spend to meet commit (annual_commit/12)',
    ytd_target DOUBLE COMMENT 'Year-to-date target (monthly_target * month_num)',
    required_run_rate DOUBLE COMMENT 'Required monthly rate to meet commit from this point forward',
    actual_run_rate DOUBLE COMMENT 'Actual average monthly spend so far',
    projected_annual DOUBLE COMMENT 'Projected annual spend based on actual run rate',
    variance_amount DOUBLE COMMENT 'Projected variance from commit (positive = overshoot)',
    variance_pct DOUBLE COMMENT 'Variance as percentage of commit',
    commit_status STRING COMMENT 'Status: ON_TRACK, UNDERSHOOT_RISK, OVERSHOOT_RISK'
)
COMMENT 'LLM: Compares actual spend vs required run rate to meet annual Databricks commit amount.
Use this for FinOps planning, commit tracking, and forecasting under/overshoot.
Parameters: commit_year (e.g., 2025), optional as_of_date (defaults to today).
Example questions: "Are we on track to meet our 2025 commit?" or 
"What is our required run rate?" or "Will we overshoot our Databricks commitment?" or
"Show me our commit vs actual for this year"'
RETURN
    WITH commit_config AS (
        SELECT 
            annual_commit_amount,
            annual_commit_amount / 12 AS monthly_target,
            undershoot_alert_pct,
            overshoot_alert_pct
        FROM ${catalog}.${gold_schema}.commit_configurations
        WHERE commit_year = get_commit_vs_actual.commit_year
        LIMIT 1
    ),
    monthly_spend AS (
        SELECT 
            MONTH(usage_date) AS month_num,
            DATE_FORMAT(usage_date, 'MMMM') AS month_name,
            SUM(usage_quantity * list_price) AS monthly_spend
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE YEAR(usage_date) = get_commit_vs_actual.commit_year
            AND usage_date <= COALESCE(CAST(as_of_date AS DATE), CURRENT_DATE())
        GROUP BY MONTH(usage_date), DATE_FORMAT(usage_date, 'MMMM')
    ),
    cumulative AS (
        SELECT 
            ms.month_num,
            ms.month_name,
            ms.monthly_spend,
            SUM(ms.monthly_spend) OVER (ORDER BY ms.month_num) AS ytd_spend,
            cc.monthly_target,
            cc.monthly_target * ms.month_num AS ytd_target,
            cc.annual_commit_amount,
            -- Required run rate to meet commit from current point
            (cc.annual_commit_amount - SUM(ms.monthly_spend) OVER (ORDER BY ms.month_num)) / 
                NULLIF(12 - ms.month_num, 0) AS required_run_rate,
            -- Actual run rate
            SUM(ms.monthly_spend) OVER (ORDER BY ms.month_num) / ms.month_num AS actual_run_rate,
            cc.undershoot_alert_pct,
            cc.overshoot_alert_pct
        FROM monthly_spend ms
        CROSS JOIN commit_config cc
    )
    SELECT 
        month_num,
        month_name,
        ROUND(monthly_spend, 2) AS monthly_spend,
        ROUND(ytd_spend, 2) AS ytd_spend,
        ROUND(monthly_target, 2) AS monthly_target,
        ROUND(ytd_target, 2) AS ytd_target,
        ROUND(required_run_rate, 2) AS required_run_rate,
        ROUND(actual_run_rate, 2) AS actual_run_rate,
        ROUND(actual_run_rate * 12, 2) AS projected_annual,
        ROUND(actual_run_rate * 12 - annual_commit_amount, 2) AS variance_amount,
        ROUND((actual_run_rate * 12 - annual_commit_amount) / NULLIF(annual_commit_amount, 0) * 100, 2) AS variance_pct,
        CASE 
            WHEN actual_run_rate * 12 < annual_commit_amount * undershoot_alert_pct THEN 'UNDERSHOOT_RISK'
            WHEN actual_run_rate * 12 > annual_commit_amount * overshoot_alert_pct THEN 'OVERSHOOT_RISK'
            ELSE 'ON_TRACK'
        END AS commit_status
    FROM cumulative
    ORDER BY month_num;
```

---

#### TVF: get_commit_forecast

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_commit_forecast(
    commit_year INT COMMENT 'Year of the commit to forecast (e.g., 2025)'
)
RETURNS TABLE(
    forecast_month DATE COMMENT 'Month being forecasted',
    p10_forecast DOUBLE COMMENT 'Optimistic forecast (10th percentile)',
    p50_forecast DOUBLE COMMENT 'Expected forecast (median)',
    p90_forecast DOUBLE COMMENT 'Conservative forecast (90th percentile)',
    cumulative_p10 DOUBLE COMMENT 'Cumulative optimistic spend',
    cumulative_p50 DOUBLE COMMENT 'Cumulative expected spend',
    cumulative_p90 DOUBLE COMMENT 'Cumulative conservative spend',
    annual_commit DOUBLE COMMENT 'Annual commit amount',
    p50_vs_commit_pct DOUBLE COMMENT 'P50 projection vs commit percentage'
)
COMMENT 'LLM: Returns ML-based cost forecast with confidence intervals to predict commit overshoot/undershoot.
Use this for planning and proactive budget management.
Example questions: "Will we meet our commit?" or "What is our forecasted spend?" or 
"Show me the cost forecast for this year"'
RETURN
    SELECT 
        forecast_date AS forecast_month,
        ROUND(predicted_monthly_cost_p10, 2) AS p10_forecast,
        ROUND(predicted_monthly_cost, 2) AS p50_forecast,
        ROUND(predicted_monthly_cost_p90, 2) AS p90_forecast,
        ROUND(SUM(predicted_monthly_cost_p10) OVER (ORDER BY forecast_date), 2) AS cumulative_p10,
        ROUND(SUM(predicted_monthly_cost) OVER (ORDER BY forecast_date), 2) AS cumulative_p50,
        ROUND(SUM(predicted_monthly_cost_p90) OVER (ORDER BY forecast_date), 2) AS cumulative_p90,
        cc.annual_commit_amount AS annual_commit,
        ROUND(SUM(predicted_monthly_cost) OVER (ORDER BY forecast_date) / 
            NULLIF(cc.annual_commit_amount, 0) * 100, 2) AS p50_vs_commit_pct
    FROM ${catalog}.${gold_schema}.budget_forecast_predictions bfp
    CROSS JOIN ${catalog}.${gold_schema}.commit_configurations cc
    WHERE cc.commit_year = get_commit_forecast.commit_year
        AND YEAR(forecast_date) = get_commit_forecast.commit_year
    ORDER BY forecast_date;
```

---

#### TVF: get_cost_by_tag

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_by_tag(
    tag_key STRING COMMENT 'Tag key to analyze (e.g., team, project, cost_center, env)',
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 20 COMMENT 'Number of top tag values to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Cost rank by tag value',
    tag_value STRING COMMENT 'Tag value (or UNTAGGED if not set)',
    total_dbu DOUBLE COMMENT 'Total DBUs consumed',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    pct_of_total DOUBLE COMMENT 'Percentage of total cost',
    workspace_count INT COMMENT 'Number of workspaces with this tag',
    job_count INT COMMENT 'Number of jobs with this tag'
)
COMMENT 'LLM: Returns cost breakdown by a specific tag key for fine-grained chargeback and attribution.
Tags are defined in custom_tags column from billing data (https://docs.databricks.com/aws/en/admin/system-tables/billing).
Use this for team-level chargeback, project cost tracking, and cost allocation.
Parameters: tag_key (e.g., "team", "project", "cost_center"), start_date, end_date, top_n.
Example questions: "What is the cost by team?" or "Show me spend by project tag" or 
"Cost breakdown by cost_center" or "Which teams are spending the most?"'
RETURN
    WITH cost_by_tag AS (
        SELECT 
            COALESCE(custom_tags[tag_key], 'UNTAGGED') AS tag_value,
            SUM(usage_quantity) AS total_dbu,
            SUM(usage_quantity * list_price) AS total_cost,
            COUNT(DISTINCT workspace_id) AS workspace_count,
            COUNT(DISTINCT usage_metadata.job_id) AS job_count
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY COALESCE(custom_tags[tag_key], 'UNTAGGED')
    ),
    ranked AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (ORDER BY total_cost DESC) AS rank,
            SUM(total_cost) OVER () AS grand_total
        FROM cost_by_tag
    )
    SELECT 
        CAST(rank AS INT) AS rank,
        tag_value,
        ROUND(total_dbu, 2) AS total_dbu,
        ROUND(total_cost, 2) AS total_cost,
        ROUND(total_cost / NULLIF(grand_total, 0) * 100, 2) AS pct_of_total,
        CAST(workspace_count AS INT) AS workspace_count,
        CAST(job_count AS INT) AS job_count
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;
```

---

#### TVF: get_untagged_resources

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_untagged_resources(
    resource_type STRING DEFAULT 'ALL' COMMENT 'Resource type: JOB, CLUSTER, WAREHOUSE, or ALL',
    lookback_days INT DEFAULT 90 COMMENT 'Number of days to look back for activity',
    min_cost DOUBLE DEFAULT 0 COMMENT 'Minimum cost threshold to include'
)
RETURNS TABLE(
    resource_type STRING COMMENT 'Type of resource (JOB, CLUSTER, WAREHOUSE)',
    workspace_id STRING COMMENT 'Workspace ID',
    workspace_name STRING COMMENT 'Workspace name',
    resource_id STRING COMMENT 'Resource ID (job_id, cluster_id, or warehouse_id)',
    resource_name STRING COMMENT 'Resource name',
    owner STRING COMMENT 'Resource owner (run_as for jobs, creator for others)',
    total_cost DOUBLE COMMENT 'Total cost in last N days',
    last_used DATE COMMENT 'Last activity date'
)
COMMENT 'LLM: Returns resources (jobs, clusters, warehouses) that have no tags but have incurred cost.
Use this to identify resources needing tag assignment for proper cost attribution.
Based on query pattern from https://docs.databricks.com/aws/en/admin/system-tables/billing showing custom_tags usage.
Example questions: "Which jobs are not tagged?" or "Show me untagged resources" or 
"What resources need tags?" or "Find jobs without cost center tags"'
RETURN
    -- Untagged Jobs
    SELECT 
        'JOB' AS resource_type,
        j.workspace_id,
        w.workspace_name,
        j.job_id AS resource_id,
        j.name AS resource_name,
        j.run_as AS owner,
        ROUND(COALESCE(jc.total_cost, 0), 2) AS total_cost,
        jc.last_used
    FROM ${catalog}.${gold_schema}.dim_job j
    LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
        ON j.workspace_id = w.workspace_id AND w.is_current = TRUE
    LEFT JOIN (
        SELECT 
            usage_metadata.job_id AS job_id,
            SUM(usage_quantity * list_price) AS total_cost,
            MAX(usage_date) AS last_used
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL lookback_days DAYS
            AND usage_metadata.job_id IS NOT NULL
        GROUP BY usage_metadata.job_id
    ) jc ON j.job_id = jc.job_id
    WHERE j.is_current = TRUE
        AND (j.tags IS NULL OR cardinality(j.tags) = 0)
        AND COALESCE(jc.total_cost, 0) >= min_cost
        AND (resource_type = 'ALL' OR resource_type = 'JOB')

    UNION ALL

    -- Untagged Clusters
    SELECT 
        'CLUSTER' AS resource_type,
        c.workspace_id,
        w.workspace_name,
        c.cluster_id AS resource_id,
        c.cluster_name AS resource_name,
        c.creator_user_name AS owner,
        ROUND(COALESCE(cc.total_cost, 0), 2) AS total_cost,
        cc.last_used
    FROM ${catalog}.${gold_schema}.dim_cluster c
    LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
        ON c.workspace_id = w.workspace_id AND w.is_current = TRUE
    LEFT JOIN (
        SELECT 
            usage_metadata.cluster_id AS cluster_id,
            SUM(usage_quantity * list_price) AS total_cost,
            MAX(usage_date) AS last_used
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL lookback_days DAYS
            AND usage_metadata.cluster_id IS NOT NULL
        GROUP BY usage_metadata.cluster_id
    ) cc ON c.cluster_id = cc.cluster_id
    WHERE c.is_current = TRUE
        AND (c.custom_tags IS NULL OR cardinality(c.custom_tags) = 0)
        AND COALESCE(cc.total_cost, 0) >= min_cost
        AND (resource_type = 'ALL' OR resource_type = 'CLUSTER')

    ORDER BY total_cost DESC;
```

---

#### TVF: get_tag_coverage

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_tag_coverage(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    granularity STRING DEFAULT 'DAY' COMMENT 'Time granularity: DAY, WEEK, or MONTH'
)
RETURNS TABLE(
    period_start DATE COMMENT 'Start of the time period',
    tagged_cost DOUBLE COMMENT 'Cost from tagged resources',
    untagged_cost DOUBLE COMMENT 'Cost from untagged resources',
    total_cost DOUBLE COMMENT 'Total cost',
    tag_coverage_pct DOUBLE COMMENT 'Percentage of cost that is tagged',
    tagged_dbu DOUBLE COMMENT 'DBUs from tagged resources',
    untagged_dbu DOUBLE COMMENT 'DBUs from untagged resources'
)
COMMENT 'LLM: Returns tag coverage metrics over time to track improvement in tagging practices.
Use this to monitor tag adoption and identify periods with poor tagging.
Example questions: "What is our tag coverage?" or "Are we improving tagging over time?" or 
"How much cost is untagged?" or "Show tag coverage trend"'
RETURN
    WITH usage_tagged AS (
        SELECT 
            CASE 
                WHEN granularity = 'DAY' THEN usage_date
                WHEN granularity = 'WEEK' THEN DATE_TRUNC('week', usage_date)
                WHEN granularity = 'MONTH' THEN DATE_TRUNC('month', usage_date)
                ELSE usage_date
            END AS period_start,
            CASE 
                WHEN custom_tags IS NULL OR cardinality(custom_tags) = 0 THEN 'UNTAGGED'
                ELSE 'TAGGED'
            END AS tag_status,
            usage_quantity,
            usage_quantity * list_price AS cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    )
    SELECT 
        period_start,
        ROUND(SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END), 2) AS tagged_cost,
        ROUND(SUM(CASE WHEN tag_status = 'UNTAGGED' THEN cost ELSE 0 END), 2) AS untagged_cost,
        ROUND(SUM(cost), 2) AS total_cost,
        ROUND(SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / 
            NULLIF(SUM(cost), 0) * 100, 2) AS tag_coverage_pct,
        ROUND(SUM(CASE WHEN tag_status = 'TAGGED' THEN usage_quantity ELSE 0 END), 2) AS tagged_dbu,
        ROUND(SUM(CASE WHEN tag_status = 'UNTAGGED' THEN usage_quantity ELSE 0 END), 2) AS untagged_dbu
    FROM usage_tagged
    GROUP BY period_start
    ORDER BY period_start;
```

---

## TVF Inventory Summary

| Domain | TVF Count | Key Functions |
|--------|-----------|---------------|
| **Cost & Billing** | 4 | top_cost_contributors, cost_trend, cost_by_owner, week_over_week |
| **Commit Tracking** | 2 | get_commit_vs_actual, get_commit_forecast (NEW) |
| **Tag Analysis** | 3 | get_cost_by_tag, get_untagged_resources, get_tag_coverage (NEW) |
| **Job Performance** | 11 | failed_jobs, success_rate, expensive_jobs, duration_percentiles, repair_costs, spend_trend, failure_costs, duration_analysis |
| **Query Performance** | 6 | slow_queries, warehouse_utilization, query_efficiency |
| **Security & Audit** | 7 | table_access_audit, user_activity, sensitive_table_access |
| **Compute & Clusters** | 6 | cluster_utilization, cluster_resource_metrics, underutilized_clusters |
| **Job Optimization** | 4 | stale_datasets, cost_savings, autoscaling, spend_by_tags |
| **DBR Migration** | 1 | legacy_dbr_jobs |
| **Total** | **39+** | |

---

## Deployment Configuration

```yaml
# resources/gold/tvf_setup_job.yml
resources:
  jobs:
    tvf_setup_job:
      name: "[${bundle.target}] Health Monitor - TVF Setup"
      
      tasks:
        - task_key: create_cost_tvfs
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/tvfs/cost_tvfs.sql
        
        - task_key: create_job_tvfs
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/tvfs/job_tvfs.sql
        
        - task_key: create_query_tvfs
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/tvfs/query_tvfs.sql
        
        - task_key: create_security_tvfs
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/tvfs/security_tvfs.sql
        
        - task_key: create_compute_tvfs
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/gold/tvfs/compute_tvfs.sql
      
      tags:
        project: health_monitor
        layer: gold
        artifact_type: tvf
```

---

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| **TVF Count** | 31 functions | Count in information_schema |
| **Genie Compatibility** | 100% | All use STRING dates, proper COMMENTS |
| **Test Coverage** | 100% | Each TVF tested with sample queries |
| **Documentation** | Complete | LLM comments on every function |
| **Performance** | <5s response | P95 latency for typical parameters |

---

## References

- [Databricks Table-Valued Functions](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-qry-select-tvf)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Cursor Rule: TVF Patterns](../.cursor/rules/15-databricks-table-valued-functions.mdc)

