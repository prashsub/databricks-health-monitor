-- =============================================================================
-- COST AGENT TVFs
-- =============================================================================
-- Table-Valued Functions for cost analysis, chargeback, and tag-based attribution
--
-- All TVFs query Gold layer tables (fact_usage, dim_workspace, dim_sku)
-- Parameters use STRING type for dates (Genie compatibility)
-- =============================================================================

-- Variables are substituted at deployment time
-- ${catalog} = Unity Catalog name
-- ${gold_schema} = Gold schema name (e.g., system_gold)

-- -----------------------------------------------------------------------------
-- TVF 1: get_top_cost_contributors
-- Returns top N cost contributors by workspace and SKU
-- -----------------------------------------------------------------------------
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
COMMENT '
- PURPOSE: Identify top cost contributors by workspace and SKU for FinOps analysis
- BEST FOR: "What are the top cost drivers?" "Which workspace spent the most?" "Show biggest cost contributors"
- NOT FOR: Daily trend analysis (use get_cost_trend_by_sku instead)
- RETURNS: Ranked list with workspace, SKU, DBU usage, cost, and percentage of total
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), top_n (default 10)
- SYNTAX: SELECT * FROM TABLE(get_top_cost_contributors("2024-01-01", "2024-12-31", 10))
'
RETURN
    WITH cost_summary AS (
        SELECT
            f.workspace_id,
            w.workspace_name,
            f.sku_name,
            SUM(f.usage_quantity) AS total_dbu,
            SUM(f.list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage f
        LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w
            ON f.workspace_id = w.workspace_id
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


-- -----------------------------------------------------------------------------
-- TVF 2: get_cost_trend_by_sku
-- Returns daily cost trends by SKU
-- -----------------------------------------------------------------------------
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
COMMENT '
- PURPOSE: Track daily cost trends by SKU for budget monitoring and spike detection
- BEST FOR: "Show daily cost trend" "What is our spending pattern?" "Cost trend for Jobs Compute"
- NOT FOR: Top contributors ranking (use get_top_cost_contributors instead)
- RETURNS: Daily breakdown with DBU, cost, cumulative cost, and day-over-day percentage change
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), sku_filter (default ALL)
- SYNTAX: SELECT * FROM TABLE(get_cost_trend_by_sku("2024-01-01", "2024-12-31", "JOBS_COMPUTE"))
'
RETURN
    WITH daily_costs AS (
        SELECT
            usage_date,
            sku_name,
            SUM(usage_quantity) AS daily_dbu,
            SUM(list_cost) AS daily_cost
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


-- -----------------------------------------------------------------------------
-- TVF 3: get_cost_by_owner
-- Returns cost breakdown by resource owner
-- -----------------------------------------------------------------------------
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
    interactive_cost DOUBLE COMMENT 'Cost from interactive clusters',
    run_count INT COMMENT 'Number of job runs'
)
COMMENT '
- PURPOSE: Chargeback analysis by resource owner for accountability and cost allocation
- BEST FOR: "Who spent the most?" "Show cost by owner" "Which users have highest spend?"
- NOT FOR: Tag-based chargeback (use get_cost_by_tag instead)
- RETURNS: Ranked owners with total cost, job cost, interactive cost, and run count
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), top_n (default 20)
- SYNTAX: SELECT * FROM TABLE(get_cost_by_owner("2024-01-01", "2024-12-31", 20))
'
RETURN
    WITH owner_costs AS (
        SELECT
            COALESCE(identity_metadata_run_as, identity_metadata_owned_by, 'UNKNOWN') AS owner,
            CASE
                WHEN COALESCE(identity_metadata_run_as, identity_metadata_owned_by) LIKE '%@%' THEN 'USER'
                ELSE 'SERVICE_PRINCIPAL'
            END AS owner_type,
            SUM(list_cost) AS total_cost,
            SUM(CASE WHEN usage_metadata_job_id IS NOT NULL THEN list_cost ELSE 0 END) AS job_cost,
            SUM(CASE WHEN usage_metadata_cluster_id IS NOT NULL AND usage_metadata_job_id IS NULL THEN list_cost ELSE 0 END) AS interactive_cost,
            COUNT(DISTINCT usage_metadata_job_run_id) AS run_count
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY 1, 2
    ),
    ranked AS (
        SELECT *,
            ROW_NUMBER() OVER (ORDER BY total_cost DESC) AS rank
        FROM owner_costs
    )
    SELECT rank, owner, owner_type, total_cost, job_cost, interactive_cost, run_count
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 4: get_cost_by_tag
-- Returns cost grouped by custom tags (team, project, cost_center)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_by_tag(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    tag_key STRING DEFAULT 'team' COMMENT 'Tag key to group by (team, project, cost_center, env)'
)
RETURNS TABLE(
    tag_value STRING COMMENT 'Value of the tag',
    total_cost DOUBLE COMMENT 'Total cost for this tag value',
    total_dbu DOUBLE COMMENT 'Total DBUs for this tag value',
    resource_count INT COMMENT 'Number of resources with this tag',
    pct_of_total DOUBLE COMMENT 'Percentage of total cost'
)
COMMENT '
- PURPOSE: Tag-based cost allocation for chargeback and governance
- BEST FOR: "Show cost by team tag" "Cost breakdown by project" "Which cost centers spend most?"
- NOT FOR: Owner-based chargeback (use get_cost_by_owner instead)
- RETURNS: Tag values with cost, DBU, resource count, and percentage of total
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), tag_key (default "team")
- SYNTAX: SELECT * FROM TABLE(get_cost_by_tag("2024-01-01", "2024-12-31", "project"))
'
RETURN
    WITH tag_costs AS (
        SELECT
            COALESCE(custom_tags[tag_key], 'UNTAGGED') AS tag_value,
            SUM(list_cost) AS total_cost,
            SUM(usage_quantity) AS total_dbu,
            COUNT(DISTINCT COALESCE(usage_metadata_job_id, usage_metadata_cluster_id, usage_metadata_warehouse_id)) AS resource_count
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY 1
    ),
    with_totals AS (
        SELECT *,
            (total_cost / NULLIF(SUM(total_cost) OVER (), 0)) * 100 AS pct_of_total
        FROM tag_costs
    )
    SELECT tag_value, total_cost, total_dbu, resource_count, pct_of_total
    FROM with_totals
    ORDER BY total_cost DESC;


-- -----------------------------------------------------------------------------
-- TVF 5: get_untagged_resources
-- Returns resources without required tags
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_untagged_resources(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    resource_type STRING DEFAULT 'ALL' COMMENT 'Resource type: JOB, CLUSTER, WAREHOUSE, or ALL'
)
RETURNS TABLE(
    resource_type STRING COMMENT 'Type of resource (JOB, CLUSTER, WAREHOUSE)',
    resource_id STRING COMMENT 'Resource identifier',
    resource_name STRING COMMENT 'Resource name if available',
    owner STRING COMMENT 'Resource owner',
    total_cost DOUBLE COMMENT 'Total cost of untagged resource',
    last_used DATE COMMENT 'Last usage date'
)
COMMENT '
- PURPOSE: Tag governance enforcement by identifying resources missing required tags
- BEST FOR: "Show untagged jobs" "Which resources are missing tags?" "Tag compliance report"
- NOT FOR: Cost analysis of tagged resources (use get_cost_by_tag instead)
- RETURNS: Untagged resources with type, ID, name, owner, cost, and last used date
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), resource_type (JOB/CLUSTER/WAREHOUSE/ALL)
- SYNTAX: SELECT * FROM TABLE(get_untagged_resources("2024-01-01", "2024-12-31", "JOB"))
'
RETURN
    WITH untagged AS (
        SELECT
            CASE
                WHEN usage_metadata_job_id IS NOT NULL THEN 'JOB'
                WHEN usage_metadata_warehouse_id IS NOT NULL THEN 'WAREHOUSE'
                WHEN usage_metadata_cluster_id IS NOT NULL THEN 'CLUSTER'
                ELSE 'OTHER'
            END AS resource_type,
            COALESCE(usage_metadata_job_id, usage_metadata_warehouse_id, usage_metadata_cluster_id) AS resource_id,
            COALESCE(f.identity_metadata_run_as, f.identity_metadata_owned_by) AS owner,
            SUM(list_cost) AS total_cost,
            MAX(usage_date) AS last_used
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND is_tagged = FALSE
        GROUP BY 1, 2, 3
    )
    SELECT
        u.resource_type,
        u.resource_id,
        COALESCE(j.name, w.warehouse_name, c.cluster_name, 'Unknown') AS resource_name,
        u.owner,
        u.total_cost,
        u.last_used
    FROM untagged u
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j
        ON u.resource_type = 'JOB' AND u.resource_id = j.job_id AND j.delete_time IS NULL
    LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w
        ON u.resource_type = 'WAREHOUSE' AND u.resource_id = w.warehouse_id AND w.delete_time IS NULL
    LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c
        ON u.resource_type = 'CLUSTER' AND u.resource_id = c.cluster_id AND c.delete_time IS NULL
    WHERE resource_type = 'ALL' OR u.resource_type = resource_type
    ORDER BY u.total_cost DESC;


-- -----------------------------------------------------------------------------
-- TVF 6: get_tag_coverage
-- Returns tag coverage metrics
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_tag_coverage(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
    metric STRING COMMENT 'Coverage metric name',
    value DOUBLE COMMENT 'Metric value',
    description STRING COMMENT 'Metric description'
)
COMMENT '
- PURPOSE: Tag coverage metrics for governance reporting and compliance tracking
- BEST FOR: "What is our tag coverage?" "How much cost is untagged?" "Tag compliance summary"
- NOT FOR: Identifying specific untagged resources (use get_untagged_resources instead)
- RETURNS: Coverage metrics for records, cost, and resources with descriptions
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
- SYNTAX: SELECT * FROM TABLE(get_tag_coverage("2024-01-01", "2024-12-31"))
'
RETURN
    WITH summary AS (
        SELECT
            COUNT(*) AS total_records,
            SUM(CASE WHEN is_tagged THEN 1 ELSE 0 END) AS tagged_records,
            SUM(list_cost) AS total_cost,
            SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) AS tagged_cost,
            COUNT(DISTINCT CASE WHEN is_tagged THEN COALESCE(usage_metadata_job_id, usage_metadata_cluster_id) END) AS tagged_resources,
            COUNT(DISTINCT COALESCE(usage_metadata_job_id, usage_metadata_cluster_id)) AS total_resources
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    )
    SELECT 'record_coverage_pct' AS metric,
           (tagged_records * 100.0 / NULLIF(total_records, 0)) AS value,
           'Percentage of usage records with tags' AS description
    FROM summary
    UNION ALL
    SELECT 'cost_coverage_pct',
           (tagged_cost * 100.0 / NULLIF(total_cost, 0)),
           'Percentage of cost covered by tags'
    FROM summary
    UNION ALL
    SELECT 'resource_coverage_pct',
           (tagged_resources * 100.0 / NULLIF(total_resources, 0)),
           'Percentage of resources with tags'
    FROM summary
    UNION ALL
    SELECT 'untagged_cost_usd',
           (total_cost - tagged_cost),
           'Total cost not attributed to any tag'
    FROM summary;


-- -----------------------------------------------------------------------------
-- TVF 7: get_cost_week_over_week
-- Returns week-over-week cost growth
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_week_over_week(
    weeks_back INT DEFAULT 12 COMMENT 'Number of weeks to analyze'
)
RETURNS TABLE(
    week_start DATE COMMENT 'Start date of the week',
    weekly_cost DOUBLE COMMENT 'Total cost for the week',
    weekly_dbu DOUBLE COMMENT 'Total DBUs for the week',
    prior_week_cost DOUBLE COMMENT 'Prior week cost',
    wow_growth_pct DOUBLE COMMENT 'Week-over-week growth percentage',
    four_week_avg DOUBLE COMMENT '4-week moving average cost'
)
COMMENT '
- PURPOSE: Week-over-week cost trend analysis for growth tracking and seasonality detection
- BEST FOR: "Show weekly cost growth" "How did costs change WoW?" "Cost growth trend"
- NOT FOR: Daily granularity (use get_cost_trend_by_sku instead)
- RETURNS: Weekly breakdown with cost, DBU, prior week comparison, growth %, and 4-week average
- PARAMS: weeks_back (default 12)
- SYNTAX: SELECT * FROM TABLE(get_cost_week_over_week(12))
'
RETURN
    WITH weekly_costs AS (
        SELECT
            DATE_TRUNC('WEEK', usage_date) AS week_start,
            SUM(list_cost) AS weekly_cost,
            SUM(usage_quantity) AS weekly_dbu
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL weeks_back WEEK
        GROUP BY 1
    ),
    with_growth AS (
        SELECT *,
            LAG(weekly_cost) OVER (ORDER BY week_start) AS prior_week_cost,
            ((weekly_cost - LAG(weekly_cost) OVER (ORDER BY week_start)) /
                NULLIF(LAG(weekly_cost) OVER (ORDER BY week_start), 0)) * 100 AS wow_growth_pct,
            AVG(weekly_cost) OVER (ORDER BY week_start ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS four_week_avg
        FROM weekly_costs
    )
    SELECT week_start, weekly_cost, weekly_dbu, prior_week_cost, wow_growth_pct, four_week_avg
    FROM with_growth
    ORDER BY week_start;


-- -----------------------------------------------------------------------------
-- TVF 8: get_cost_anomalies
-- Returns detected cost anomalies
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_anomalies(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    z_score_threshold DOUBLE DEFAULT 2.0 COMMENT 'Z-score threshold for anomaly detection'
)
RETURNS TABLE(
    anomaly_date DATE COMMENT 'Date of anomaly',
    workspace_id STRING COMMENT 'Workspace ID',
    daily_cost DOUBLE COMMENT 'Actual daily cost',
    avg_cost_7d DOUBLE COMMENT '7-day average cost',
    std_cost_7d DOUBLE COMMENT '7-day standard deviation',
    z_score DOUBLE COMMENT 'Z-score (deviation from mean)',
    anomaly_type STRING COMMENT 'SPIKE or DIP'
)
COMMENT '
- PURPOSE: Statistical anomaly detection for cost spikes and unusual spending patterns
- BEST FOR: "Show cost anomalies" "Were there cost spikes?" "Unusual spending days"
- NOT FOR: Expected cost trends (use get_cost_trend_by_sku instead)
- RETURNS: Anomaly dates with actual cost, 7-day average, standard deviation, z-score, and type
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), z_score_threshold (default 2.0)
- SYNTAX: SELECT * FROM TABLE(get_cost_anomalies("2024-01-01", "2024-12-31", 2.0))
- NOTE: Z-score > 2 indicates values outside ~95% of normal distribution
'
RETURN
    WITH daily_costs AS (
        SELECT
            usage_date,
            workspace_id,
            SUM(list_cost) AS daily_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) - INTERVAL 14 DAY AND CAST(end_date AS DATE)
        GROUP BY usage_date, workspace_id
    ),
    with_stats AS (
        SELECT *,
            AVG(daily_cost) OVER (
                PARTITION BY workspace_id
                ORDER BY usage_date
                ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS avg_cost_7d,
            STDDEV(daily_cost) OVER (
                PARTITION BY workspace_id
                ORDER BY usage_date
                ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS std_cost_7d
        FROM daily_costs
    ),
    with_zscore AS (
        SELECT *,
            (daily_cost - avg_cost_7d) / NULLIF(std_cost_7d, 0) AS z_score
        FROM with_stats
        WHERE avg_cost_7d IS NOT NULL
    )
    SELECT
        usage_date AS anomaly_date,
        workspace_id,
        daily_cost,
        avg_cost_7d,
        std_cost_7d,
        z_score,
        CASE WHEN z_score > 0 THEN 'SPIKE' ELSE 'DIP' END AS anomaly_type
    FROM with_zscore
    WHERE ABS(z_score) >= z_score_threshold
        AND usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    ORDER BY ABS(z_score) DESC;


-- -----------------------------------------------------------------------------
-- TVF 9: get_cost_forecast_summary
-- Returns cost forecast summary (requires ML inference table)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_forecast_summary(
    forecast_months INT DEFAULT 3 COMMENT 'Number of months to forecast'
)
RETURNS TABLE(
    forecast_month DATE COMMENT 'Month being forecasted',
    predicted_cost_p50 DOUBLE COMMENT 'Median predicted cost',
    predicted_cost_p10 DOUBLE COMMENT 'Optimistic (10th percentile) cost',
    predicted_cost_p90 DOUBLE COMMENT 'Conservative (90th percentile) cost',
    mtd_actual DOUBLE COMMENT 'Month-to-date actual if available',
    variance_vs_actual DOUBLE COMMENT 'Variance from actual (if available)'
)
COMMENT '
- PURPOSE: Cost forecasting for budget planning and commit tracking
- BEST FOR: "What is our cost forecast?" "How much will we spend next month?" "Budget projection"
- NOT FOR: Historical cost analysis (use get_cost_trend_by_sku instead)
- RETURNS: Monthly forecast with P10/P50/P90 predictions and variance from actual
- PARAMS: forecast_months (default 3)
- SYNTAX: SELECT * FROM TABLE(get_cost_forecast_summary(3))
- NOTE: Uses historical average until ML inference table is deployed
'
RETURN
    -- Note: This TVF requires the ML inference table to be populated
    -- Placeholder implementation - will be enhanced when ML pipeline is deployed
    WITH monthly_history AS (
        SELECT
            DATE_TRUNC('MONTH', usage_date) AS month_start,
            SUM(list_cost) AS monthly_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL 12 MONTH
        GROUP BY 1
    ),
    recent_trend AS (
        SELECT
            AVG(monthly_cost) AS avg_monthly_cost,
            STDDEV(monthly_cost) AS std_monthly_cost
        FROM monthly_history
    )
    SELECT
        ADD_MONTHS(DATE_TRUNC('MONTH', CURRENT_DATE()), n) AS forecast_month,
        r.avg_monthly_cost AS predicted_cost_p50,
        r.avg_monthly_cost - r.std_monthly_cost AS predicted_cost_p10,
        r.avg_monthly_cost + r.std_monthly_cost AS predicted_cost_p90,
        NULL AS mtd_actual,
        NULL AS variance_vs_actual
    FROM recent_trend r
    CROSS JOIN (SELECT explode(sequence(1, forecast_months)) AS n);


-- -----------------------------------------------------------------------------
-- TVF 10: get_cost_mtd_summary
-- Returns month-to-date cost summary
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_mtd_summary()
RETURNS TABLE(
    metric STRING COMMENT 'Cost metric name',
    current_mtd DOUBLE COMMENT 'Current month-to-date value',
    prior_mtd DOUBLE COMMENT 'Same period last month',
    mom_change_pct DOUBLE COMMENT 'Month-over-month change %',
    projected_month_end DOUBLE COMMENT 'Projected end-of-month'
)
COMMENT '
- PURPOSE: Month-to-date cost tracking with month-over-month comparison
- BEST FOR: "What is our MTD cost?" "How do we compare to last month?" "Monthly progress"
- NOT FOR: Full month historical analysis (use get_cost_trend_by_sku instead)
- RETURNS: Current MTD, prior MTD, MoM change %, and projected month-end
- PARAMS: None
- SYNTAX: SELECT * FROM TABLE(get_cost_mtd_summary())
'
RETURN
    WITH current_month AS (
        SELECT
            SUM(list_cost) AS mtd_cost,
            SUM(usage_quantity) AS mtd_dbu,
            COUNT(DISTINCT usage_date) AS days_elapsed,
            DAY(LAST_DAY(CURRENT_DATE())) AS days_in_month
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
            AND usage_date <= CURRENT_DATE()
    ),
    prior_month AS (
        SELECT
            SUM(list_cost) AS prior_mtd_cost,
            SUM(usage_quantity) AS prior_mtd_dbu
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= ADD_MONTHS(DATE_TRUNC('MONTH', CURRENT_DATE()), -1)
            AND usage_date <= ADD_MONTHS(CURRENT_DATE(), -1)
    )
    SELECT 'Total Cost (USD)' AS metric,
           c.mtd_cost AS current_mtd,
           p.prior_mtd_cost AS prior_mtd,
           ((c.mtd_cost - p.prior_mtd_cost) / NULLIF(p.prior_mtd_cost, 0)) * 100 AS mom_change_pct,
           (c.mtd_cost / NULLIF(c.days_elapsed, 0)) * c.days_in_month AS projected_month_end
    FROM current_month c, prior_month p
    UNION ALL
    SELECT 'Total DBU',
           c.mtd_dbu,
           p.prior_mtd_dbu,
           ((c.mtd_dbu - p.prior_mtd_dbu) / NULLIF(p.prior_mtd_dbu, 0)) * 100,
           (c.mtd_dbu / NULLIF(c.days_elapsed, 0)) * c.days_in_month
    FROM current_month c, prior_month p;


-- -----------------------------------------------------------------------------
-- TVF 11: get_commit_vs_actual
-- Compares actual spend vs required run rate for commit tracking
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_commit_vs_actual(
    commit_year INT COMMENT 'Year of the commit to analyze (e.g., 2025)',
    annual_commit_amount DOUBLE COMMENT 'Annual commit amount in USD',
    as_of_date STRING DEFAULT NULL COMMENT 'Optional: Analysis as-of date (YYYY-MM-DD). Defaults to current date.'
)
RETURNS TABLE(
    month_num INT COMMENT 'Month number (1-12)',
    month_name STRING COMMENT 'Month name',
    monthly_spend DOUBLE COMMENT 'Actual monthly spend in USD',
    ytd_spend DOUBLE COMMENT 'Year-to-date cumulative spend',
    monthly_target DOUBLE COMMENT 'Required monthly spend to meet commit',
    ytd_target DOUBLE COMMENT 'Year-to-date target',
    required_run_rate DOUBLE COMMENT 'Required monthly rate from this point',
    actual_run_rate DOUBLE COMMENT 'Actual average monthly spend so far',
    projected_annual DOUBLE COMMENT 'Projected annual spend',
    variance_amount DOUBLE COMMENT 'Variance from commit (positive = overshoot)',
    variance_pct DOUBLE COMMENT 'Variance as percentage',
    commit_status STRING COMMENT 'ON_TRACK, UNDERSHOOT_RISK, or OVERSHOOT_RISK'
)
COMMENT '
- PURPOSE: Commit tracking to compare actual spend vs required run rate for annual commit
- BEST FOR: "Are we on track for commit?" "What is our required run rate?" "Commit variance"
- NOT FOR: Historical cost analysis (use get_cost_trend_by_sku instead)
- RETURNS: Monthly breakdown with actual, target, run rates, projections, and status
- PARAMS: commit_year (e.g., 2025), annual_commit_amount (USD), as_of_date (optional)
- SYNTAX: SELECT * FROM TABLE(get_commit_vs_actual(2025, 1000000, "2025-06-30"))
- NOTE: Status values: ON_TRACK, UNDERSHOOT_RISK, OVERSHOOT_RISK
'
RETURN
    WITH monthly_spend AS (
        SELECT
            MONTH(usage_date) AS month_num,
            DATE_FORMAT(usage_date, 'MMMM') AS month_name,
            SUM(list_cost) AS monthly_spend
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE YEAR(usage_date) = commit_year
            AND usage_date <= COALESCE(CAST(as_of_date AS DATE), CURRENT_DATE())
        GROUP BY MONTH(usage_date), DATE_FORMAT(usage_date, 'MMMM')
    ),
    cumulative AS (
        SELECT
            ms.month_num,
            ms.month_name,
            ms.monthly_spend,
            SUM(ms.monthly_spend) OVER (ORDER BY ms.month_num) AS ytd_spend,
            annual_commit_amount / 12 AS monthly_target,
            (annual_commit_amount / 12) * ms.month_num AS ytd_target,
            (annual_commit_amount - SUM(ms.monthly_spend) OVER (ORDER BY ms.month_num)) /
                NULLIF(12 - ms.month_num, 0) AS required_run_rate,
            SUM(ms.monthly_spend) OVER (ORDER BY ms.month_num) / ms.month_num AS actual_run_rate
        FROM monthly_spend ms
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
            WHEN actual_run_rate * 12 < annual_commit_amount * 0.9 THEN 'UNDERSHOOT_RISK'
            WHEN actual_run_rate * 12 > annual_commit_amount * 1.1 THEN 'OVERSHOOT_RISK'
            ELSE 'ON_TRACK'
        END AS commit_status
    FROM cumulative
    ORDER BY month_num;


-- -----------------------------------------------------------------------------
-- TVF 12: get_spend_by_custom_tags
-- Returns spend breakdown by any custom tag key
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_spend_by_custom_tags(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    tag_keys STRING DEFAULT 'team,project,cost_center' COMMENT 'Comma-separated tag keys to analyze'
)
RETURNS TABLE(
    tag_key STRING COMMENT 'Tag key being analyzed',
    tag_value STRING COMMENT 'Tag value (or UNTAGGED)',
    total_dbu DOUBLE COMMENT 'Total DBUs consumed',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    pct_of_total DOUBLE COMMENT 'Percentage of total cost',
    workspace_count INT COMMENT 'Number of workspaces',
    job_count INT COMMENT 'Number of jobs'
)
COMMENT '
- PURPOSE: Multi-tag cost analysis for flexible chargeback and attribution reporting
- BEST FOR: "Show cost by team and project tags" "What tags are driving cost?" "Tag breakdown"
- NOT FOR: Single tag analysis (use get_cost_by_tag instead)
- RETURNS: Tag key/value combinations with DBU, cost, percentage, and resource counts
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), tag_keys (comma-separated)
- SYNTAX: SELECT * FROM TABLE(get_spend_by_custom_tags("2024-01-01", "2024-12-31", "team,project,env"))
'
RETURN
    WITH tag_list AS (
        SELECT explode(split(tag_keys, ',')) AS tag_key
    ),
    cost_by_tag AS (
        SELECT
            t.tag_key,
            COALESCE(f.custom_tags[t.tag_key], 'UNTAGGED') AS tag_value,
            SUM(f.usage_quantity) AS total_dbu,
            SUM(f.list_cost) AS total_cost,
            COUNT(DISTINCT f.workspace_id) AS workspace_count,
            COUNT(DISTINCT f.usage_metadata_job_id) AS job_count
        FROM ${catalog}.${gold_schema}.fact_usage f
        CROSS JOIN tag_list t
        WHERE f.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY t.tag_key, COALESCE(f.custom_tags[t.tag_key], 'UNTAGGED')
    ),
    with_pct AS (
        SELECT *,
            (total_cost / NULLIF(SUM(total_cost) OVER (PARTITION BY tag_key), 0)) * 100 AS pct_of_total
        FROM cost_by_tag
    )
    SELECT tag_key, tag_value,
           ROUND(total_dbu, 2) AS total_dbu,
           ROUND(total_cost, 2) AS total_cost,
           ROUND(pct_of_total, 2) AS pct_of_total,
           workspace_count, job_count
    FROM with_pct
    ORDER BY tag_key, total_cost DESC;


-- -----------------------------------------------------------------------------
-- TVF 13: get_cost_growth_analysis
-- Identifies entities with highest cost growth week-over-week
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_growth_analysis(
    days_back INT DEFAULT 14 COMMENT 'Number of days to analyze (for week-over-week)',
    entity_type STRING DEFAULT 'WORKSPACE' COMMENT 'Entity type: WORKSPACE, JOB, or SKU',
    top_n INT DEFAULT 20 COMMENT 'Number of entities to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Growth rank (1 = highest growth)',
    entity_id STRING COMMENT 'Entity identifier',
    entity_name STRING COMMENT 'Entity name',
    last_7_day_spend DOUBLE COMMENT 'Spend in last 7 days',
    prior_7_day_spend DOUBLE COMMENT 'Spend in prior 7 days',
    growth_amount DOUBLE COMMENT 'Absolute growth in spend',
    growth_pct DOUBLE COMMENT 'Percentage growth'
)
COMMENT '
- PURPOSE: Identify entities with highest week-over-week cost growth for anomaly detection
- BEST FOR: "Which workspaces have highest cost growth?" "Show spending trends" "Cost increase analysis"
- NOT FOR: Comparing custom periods (use get_cost_growth_by_period instead)
- RETURNS: Entities ranked by growth with last 7d vs prior 7d spend and percentage change
- PARAMS: days_back (default 14), entity_type (WORKSPACE/JOB/SKU), top_n (default 20)
- SYNTAX: SELECT * FROM TABLE(get_cost_growth_analysis(14, "JOB", 10))
'
RETURN
    WITH aggregated AS (
        SELECT
            CASE entity_type
                WHEN 'WORKSPACE' THEN workspace_id
                WHEN 'JOB' THEN usage_metadata_job_id
                WHEN 'SKU' THEN sku_name
            END AS entity_id,
            SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 7 DAY AND CURRENT_DATE() - INTERVAL 1 DAY
                     THEN list_cost ELSE 0 END) AS last_7_day_spend,
            SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAY AND CURRENT_DATE() - INTERVAL 8 DAY
                     THEN list_cost ELSE 0 END) AS prior_7_day_spend
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY 1
    ),
    with_growth AS (
        SELECT
            a.entity_id,
            COALESCE(w.workspace_name, j.name, a.entity_id) AS entity_name,
            a.last_7_day_spend,
            a.prior_7_day_spend,
            a.last_7_day_spend - a.prior_7_day_spend AS growth_amount,
            (a.last_7_day_spend - a.prior_7_day_spend) / NULLIF(a.prior_7_day_spend, 0) * 100 AS growth_pct
        FROM aggregated a
        LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w
            ON entity_type = 'WORKSPACE' AND a.entity_id = w.workspace_id
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON entity_type = 'JOB' AND a.entity_id = j.job_id AND j.delete_time IS NULL
        WHERE a.entity_id IS NOT NULL
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY growth_amount DESC) AS rank
        FROM with_growth
    )
    SELECT CAST(rank AS INT) AS rank, entity_id, entity_name,
           ROUND(last_7_day_spend, 2) AS last_7_day_spend,
           ROUND(prior_7_day_spend, 2) AS prior_7_day_spend,
           ROUND(growth_amount, 2) AS growth_amount,
           ROUND(growth_pct, 2) AS growth_pct
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;


-- =============================================================================
-- DASHBOARD PATTERN TVFs (Added from Phase 3 Plan Enhancements)
-- =============================================================================
-- Source: phase3-addendum-3.2-tvfs.md - Dashboard Pattern Analysis

-- -----------------------------------------------------------------------------
-- TVF 14: get_cost_growth_by_period
-- Period-over-period comparison (7 vs 14 day pattern)
-- Source: Dashboard Pattern Analysis
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cost_growth_by_period(
    entity_type STRING DEFAULT 'WORKSPACE' COMMENT 'Entity type: WORKSPACE, JOB, or SKU',
    recent_days INT DEFAULT 7 COMMENT 'Number of days for recent period',
    comparison_days INT DEFAULT 7 COMMENT 'Number of days for comparison period',
    top_n INT DEFAULT 20 COMMENT 'Number of top entities to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Growth rank (1 = highest growth)',
    entity_id STRING COMMENT 'Entity identifier',
    entity_name STRING COMMENT 'Entity name',
    recent_period_spend DOUBLE COMMENT 'Spend in recent period',
    prior_period_spend DOUBLE COMMENT 'Spend in prior period',
    absolute_change DOUBLE COMMENT 'Absolute change in spend',
    pct_change DOUBLE COMMENT 'Percentage change',
    change_category STRING COMMENT 'SPIKE/GROWTH/STABLE/DECLINE/DROP'
)
COMMENT '
- PURPOSE: Flexible period-over-period cost comparison with customizable windows
- BEST FOR: "Compare last 7 days vs prior 7 days" "Which workspaces grew most?" "Cost change analysis"
- NOT FOR: Fixed week-over-week analysis (use get_cost_growth_analysis instead)
- RETURNS: Entities ranked by change with both periods, absolute change, %, and category
- PARAMS: entity_type (WORKSPACE/JOB/SKU), recent_days (default 7), comparison_days (default 7), top_n (default 20)
- SYNTAX: SELECT * FROM TABLE(get_cost_growth_by_period("JOB", 14, 14, 10))
- NOTE: Categories: SPIKE (>50%), GROWTH (>10%), STABLE (-10% to 10%), DECLINE (<-10%), DROP (<-50%)
'
RETURN
    WITH period_costs AS (
        SELECT
            CASE entity_type
                WHEN 'WORKSPACE' THEN workspace_id
                WHEN 'JOB' THEN usage_metadata_job_id
                WHEN 'SKU' THEN sku_name
            END AS entity_id,
            -- Recent period (e.g., last 7 days)
            SUM(CASE
                WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -(recent_days)) AND DATE_ADD(CURRENT_DATE(), -1)
                THEN list_cost ELSE 0
            END) AS recent_period_spend,
            -- Prior period (e.g., 7 days before recent)
            SUM(CASE
                WHEN usage_date BETWEEN DATE_ADD(CURRENT_DATE(), -(recent_days + comparison_days)) AND DATE_ADD(CURRENT_DATE(), -(recent_days + 1))
                THEN list_cost ELSE 0
            END) AS prior_period_spend
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -(recent_days + comparison_days + 1))
        GROUP BY 1
        HAVING entity_id IS NOT NULL
    ),
    with_change AS (
        SELECT
            p.entity_id,
            COALESCE(w.workspace_name, j.name, p.entity_id) AS entity_name,
            p.recent_period_spend,
            p.prior_period_spend,
            p.recent_period_spend - p.prior_period_spend AS absolute_change,
            (p.recent_period_spend - p.prior_period_spend) / NULLIF(p.prior_period_spend, 0) * 100 AS pct_change
        FROM period_costs p
        LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w
            ON entity_type = 'WORKSPACE' AND p.entity_id = w.workspace_id
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON entity_type = 'JOB' AND p.entity_id = j.job_id AND j.delete_time IS NULL
    ),
    categorized AS (
        SELECT *,
            CASE
                WHEN pct_change > 50 THEN 'SPIKE'
                WHEN pct_change > 10 THEN 'GROWTH'
                WHEN pct_change BETWEEN -10 AND 10 THEN 'STABLE'
                WHEN pct_change > -50 THEN 'DECLINE'
                ELSE 'DROP'
            END AS change_category,
            ROW_NUMBER() OVER (ORDER BY absolute_change DESC) AS rank
        FROM with_change
    )
    SELECT
        CAST(rank AS INT) AS rank,
        entity_id,
        entity_name,
        ROUND(recent_period_spend, 2) AS recent_period_spend,
        ROUND(prior_period_spend, 2) AS prior_period_spend,
        ROUND(absolute_change, 2) AS absolute_change,
        ROUND(pct_change, 2) AS pct_change,
        change_category
    FROM categorized
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 15: get_all_purpose_cluster_cost
-- Identifies All-Purpose cluster costs (less efficient than Job clusters)
-- Source: Workflow Advisor Blog
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_all_purpose_cluster_cost(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 20 COMMENT 'Number of top clusters to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Cost rank',
    cluster_id STRING COMMENT 'Cluster ID',
    cluster_name STRING COMMENT 'Cluster name',
    owned_by STRING COMMENT 'Cluster owner',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    total_hours DOUBLE COMMENT 'Total runtime hours',
    cost_per_hour DOUBLE COMMENT 'Cost per hour',
    recommendation STRING COMMENT 'Migration recommendation'
)
COMMENT '
- PURPOSE: Identify All-Purpose cluster costs for migration to more efficient Job clusters
- BEST FOR: "Show all-purpose cluster costs" "Which interactive clusters cost most?" "All-purpose migration"
- NOT FOR: Job cluster analysis (use get_cluster_utilization instead)
- RETURNS: All-Purpose clusters ranked by cost with runtime hours and migration recommendations
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), top_n (default 20)
- SYNTAX: SELECT * FROM TABLE(get_all_purpose_cluster_cost("2024-01-01", "2024-12-31", 10))
- NOTE: All-Purpose clusters are less cost-efficient than Job clusters for scheduled workloads
'
RETURN
    WITH all_purpose_usage AS (
        SELECT
            usage_metadata_cluster_id AS cluster_id,
            SUM(list_cost) AS total_cost,
            SUM(usage_quantity) AS total_dbu
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND (sku_name LIKE '%ALL_PURPOSE%' OR sku_name LIKE '%INTERACTIVE%')
            AND usage_metadata_cluster_id IS NOT NULL
        GROUP BY usage_metadata_cluster_id
    ),
    cluster_hours AS (
        SELECT
            cluster_id,
            SUM(TIMESTAMPDIFF(MINUTE, start_time, end_time)) / 60.0 AS total_hours
        FROM ${catalog}.${gold_schema}.fact_node_timeline
        WHERE CAST(start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY cluster_id
    ),
    enriched AS (
        SELECT
            u.cluster_id,
            c.cluster_name,
            c.owned_by,
            u.total_cost,
            COALESCE(h.total_hours, 0) AS total_hours,
            u.total_cost / NULLIF(h.total_hours, 0) AS cost_per_hour,
            ROW_NUMBER() OVER (ORDER BY u.total_cost DESC) AS rank
        FROM all_purpose_usage u
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c
            ON u.cluster_id = c.cluster_id AND c.delete_time IS NULL
        LEFT JOIN cluster_hours h ON u.cluster_id = h.cluster_id
    )
    SELECT
        CAST(rank AS INT) AS rank,
        cluster_id,
        cluster_name,
        owned_by,
        ROUND(total_cost, 2) AS total_cost,
        ROUND(total_hours, 2) AS total_hours,
        ROUND(cost_per_hour, 2) AS cost_per_hour,
        CASE
            WHEN cost_per_hour > 50 THEN 'HIGH COST: Migrate to Job clusters or serverless'
            WHEN cost_per_hour > 20 THEN 'Consider migrating scheduled workloads to Job clusters'
            WHEN total_hours > 200 THEN 'High usage: Evaluate for serverless migration'
            ELSE 'Review for optimization opportunities'
        END AS recommendation
    FROM enriched
    WHERE rank <= top_n
    ORDER BY rank;
