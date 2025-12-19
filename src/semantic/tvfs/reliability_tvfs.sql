-- =============================================================================
-- RELIABILITY AGENT TVFs
-- =============================================================================
-- Table-Valued Functions for job reliability, failure analysis, and SLA tracking
--
-- All TVFs query Gold layer tables (fact_job_run_timeline, dim_job)
-- Parameters use STRING type for dates (Genie compatibility)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TVF 1: get_failed_jobs
-- Returns all failed job runs with details
-- -----------------------------------------------------------------------------
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
    result_state STRING COMMENT 'Result state (FAILED, ERROR, TIMED_OUT)',
    termination_code STRING COMMENT 'Termination code',
    run_as STRING COMMENT 'User who ran the job',
    start_time TIMESTAMP COMMENT 'Run start time',
    end_time TIMESTAMP COMMENT 'Run end time',
    duration_minutes DOUBLE COMMENT 'Run duration in minutes'
)
COMMENT 'LLM: Returns all failed job runs with details for root cause analysis.
Use for failure investigation, reliability tracking, and alerting.
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
        jrt.run_duration_minutes AS duration_minutes
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j
        ON jrt.job_id = j.job_id AND j.is_current = TRUE
    WHERE jrt.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT', 'CANCELED')
        AND jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (workspace_filter = 'ALL' OR jrt.workspace_id = workspace_filter)
    ORDER BY jrt.period_start_time DESC;


-- -----------------------------------------------------------------------------
-- TVF 2: get_job_success_rate
-- Returns job success rates and reliability metrics
-- -----------------------------------------------------------------------------
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
    success_rate_pct DOUBLE COMMENT 'Success rate percentage',
    avg_duration_min DOUBLE COMMENT 'Average run duration in minutes',
    p95_duration_min DOUBLE COMMENT '95th percentile duration'
)
COMMENT 'LLM: Returns job success rates and reliability metrics.
Use for identifying unreliable jobs and SLA compliance tracking.
Example: "What is our job success rate?" or "Which jobs have the lowest success rate?"'
RETURN
    WITH job_stats AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            FIRST(jrt.run_as, TRUE) AS run_as,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN jrt.is_success THEN 1 ELSE 0 END) AS successful_runs,
            SUM(CASE WHEN jrt.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END) AS failed_runs,
            AVG(jrt.run_duration_minutes) AS avg_duration_min,
            PERCENTILE_APPROX(jrt.run_duration_minutes, 0.95) AS p95_duration_min
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.result_state IS NOT NULL
            AND jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY jrt.job_id, j.name
    )
    SELECT
        job_id,
        job_name,
        run_as,
        total_runs,
        successful_runs,
        failed_runs,
        (successful_runs * 100.0 / NULLIF(total_runs, 0)) AS success_rate_pct,
        avg_duration_min,
        p95_duration_min
    FROM job_stats
    WHERE total_runs >= min_runs
    ORDER BY success_rate_pct ASC, total_runs DESC;


-- -----------------------------------------------------------------------------
-- TVF 3: get_job_duration_percentiles
-- Returns job duration percentiles for SLA planning
-- -----------------------------------------------------------------------------
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
    max_duration_min DOUBLE COMMENT 'Maximum duration',
    duration_cv DOUBLE COMMENT 'Coefficient of variation (stability measure)'
)
COMMENT 'LLM: Returns job duration percentiles for SLA planning and capacity.
Use for identifying outliers, setting SLA targets, and performance tracking.
Example: "What are the P99 job durations?" or "Show me job duration percentiles"'
RETURN
    SELECT
        jrt.job_id,
        j.name AS job_name,
        COUNT(*) AS run_count,
        AVG(jrt.run_duration_minutes) AS avg_duration_min,
        PERCENTILE_APPROX(jrt.run_duration_minutes, 0.5) AS p50_duration_min,
        PERCENTILE_APPROX(jrt.run_duration_minutes, 0.75) AS p75_duration_min,
        PERCENTILE_APPROX(jrt.run_duration_minutes, 0.90) AS p90_duration_min,
        PERCENTILE_APPROX(jrt.run_duration_minutes, 0.99) AS p99_duration_min,
        MAX(jrt.run_duration_minutes) AS max_duration_min,
        STDDEV(jrt.run_duration_minutes) / NULLIF(AVG(jrt.run_duration_minutes), 0) AS duration_cv
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j
        ON jrt.job_id = j.job_id AND j.is_current = TRUE
    WHERE jrt.is_success = TRUE
        AND jrt.run_date >= CURRENT_DATE() - INTERVAL days_back DAY
        AND (job_name_filter = 'ALL' OR j.name LIKE CONCAT('%', job_name_filter, '%'))
    GROUP BY jrt.job_id, j.name
    HAVING COUNT(*) >= 5
    ORDER BY avg_duration_min DESC;


-- -----------------------------------------------------------------------------
-- TVF 4: get_job_failure_trends
-- Returns daily failure trends for monitoring
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_failure_trends(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze'
)
RETURNS TABLE(
    run_date DATE COMMENT 'Date',
    total_runs INT COMMENT 'Total job runs',
    failed_runs INT COMMENT 'Failed runs',
    failure_rate_pct DOUBLE COMMENT 'Failure rate percentage',
    failure_rate_7d_avg DOUBLE COMMENT '7-day moving average failure rate',
    unique_failing_jobs INT COMMENT 'Number of unique failing jobs'
)
COMMENT 'LLM: Returns daily job failure trends for reliability monitoring.
Use for tracking reliability over time and identifying degradation.
Example: "What is the failure trend?" or "Is reliability improving?"'
RETURN
    WITH daily_stats AS (
        SELECT
            run_date,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END) AS failed_runs,
            COUNT(DISTINCT CASE WHEN result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN job_id END) AS unique_failing_jobs
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE run_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND result_state IS NOT NULL
        GROUP BY run_date
    )
    SELECT
        run_date,
        total_runs,
        failed_runs,
        (failed_runs * 100.0 / NULLIF(total_runs, 0)) AS failure_rate_pct,
        AVG(failed_runs * 100.0 / NULLIF(total_runs, 0)) OVER (
            ORDER BY run_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS failure_rate_7d_avg,
        unique_failing_jobs
    FROM daily_stats
    ORDER BY run_date;


-- -----------------------------------------------------------------------------
-- TVF 5: get_job_sla_compliance
-- Returns SLA compliance metrics by job
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_sla_compliance(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    sla_duration_minutes INT DEFAULT 60 COMMENT 'SLA duration threshold in minutes'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    total_runs INT COMMENT 'Total runs',
    runs_within_sla INT COMMENT 'Runs completing within SLA',
    runs_breaching_sla INT COMMENT 'Runs exceeding SLA',
    sla_compliance_pct DOUBLE COMMENT 'SLA compliance percentage',
    avg_breach_minutes DOUBLE COMMENT 'Average minutes over SLA when breached'
)
COMMENT 'LLM: Returns SLA compliance metrics for each job.
Use for SLA tracking, identifying problematic jobs, and capacity planning.
Example: "Which jobs are breaching SLA?" or "What is our SLA compliance?"'
RETURN
    WITH sla_stats AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN jrt.run_duration_minutes <= sla_duration_minutes THEN 1 ELSE 0 END) AS runs_within_sla,
            SUM(CASE WHEN jrt.run_duration_minutes > sla_duration_minutes THEN 1 ELSE 0 END) AS runs_breaching_sla,
            AVG(CASE WHEN jrt.run_duration_minutes > sla_duration_minutes
                     THEN jrt.run_duration_minutes - sla_duration_minutes
                     ELSE NULL END) AS avg_breach_minutes
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.is_success = TRUE
            AND jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY jrt.job_id, j.name
    )
    SELECT
        job_id,
        job_name,
        total_runs,
        runs_within_sla,
        runs_breaching_sla,
        (runs_within_sla * 100.0 / NULLIF(total_runs, 0)) AS sla_compliance_pct,
        avg_breach_minutes
    FROM sla_stats
    WHERE total_runs >= 3
    ORDER BY sla_compliance_pct ASC;


-- -----------------------------------------------------------------------------
-- TVF 6: get_job_run_details
-- Returns detailed information for a specific job
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_run_details(
    job_id_filter STRING COMMENT 'Job ID to get details for',
    days_back INT DEFAULT 7 COMMENT 'Number of days to look back'
)
RETURNS TABLE(
    run_id STRING COMMENT 'Run ID',
    run_date DATE COMMENT 'Run date',
    start_time TIMESTAMP COMMENT 'Start time',
    end_time TIMESTAMP COMMENT 'End time',
    duration_minutes DOUBLE COMMENT 'Duration in minutes',
    result_state STRING COMMENT 'Result state',
    termination_code STRING COMMENT 'Termination code',
    run_as STRING COMMENT 'User who ran the job',
    trigger_type STRING COMMENT 'How the job was triggered',
    run_page_url STRING COMMENT 'URL to job run page'
)
COMMENT 'LLM: Returns detailed run history for a specific job.
Use for investigating job behavior and troubleshooting.
Example: "Show me runs for job X" or "What happened with job Y?"'
RETURN
    SELECT
        run_id,
        run_date,
        period_start_time AS start_time,
        period_end_time AS end_time,
        run_duration_minutes AS duration_minutes,
        result_state,
        termination_code,
        run_as,
        trigger_type,
        run_page_url
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline
    WHERE job_id = job_id_filter
        AND run_date >= CURRENT_DATE() - INTERVAL days_back DAY
    ORDER BY period_start_time DESC;


-- -----------------------------------------------------------------------------
-- TVF 7: get_most_expensive_jobs
-- Returns jobs with highest cost (requires fact_usage join)
-- -----------------------------------------------------------------------------
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
    success_rate_pct DOUBLE COMMENT 'Success rate'
)
COMMENT 'LLM: Returns the most expensive jobs by total compute cost.
Use for cost optimization and identifying expensive workloads.
Example: "What are our most expensive jobs?" or "Which jobs cost the most?"'
RETURN
    WITH job_costs AS (
        SELECT
            u.usage_metadata_job_id AS job_id,
            j.name AS job_name,
            FIRST(u.identity_metadata_run_as, TRUE) AS run_as,
            COUNT(DISTINCT u.usage_metadata_job_run_id) AS run_count,
            SUM(u.list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage u
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON u.usage_metadata_job_id = j.job_id AND j.is_current = TRUE
        WHERE u.usage_metadata_job_id IS NOT NULL
            AND u.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY u.usage_metadata_job_id, j.name
    ),
    job_reliability AS (
        SELECT
            job_id,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN is_success THEN 1 ELSE 0 END) AS successful_runs
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY job_id
    ),
    combined AS (
        SELECT
            c.job_id,
            c.job_name,
            c.run_as,
            c.run_count,
            c.total_cost,
            c.total_cost / NULLIF(c.run_count, 0) AS avg_cost_per_run,
            (r.successful_runs * 100.0 / NULLIF(r.total_runs, 0)) AS success_rate_pct,
            ROW_NUMBER() OVER (ORDER BY c.total_cost DESC) AS rank
        FROM job_costs c
        LEFT JOIN job_reliability r ON c.job_id = r.job_id
    )
    SELECT rank, job_id, job_name, run_as, run_count, total_cost, avg_cost_per_run, success_rate_pct
    FROM combined
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 8: get_job_retry_analysis
-- Returns job retry patterns and costs
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_retry_analysis(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    total_attempts INT COMMENT 'Total run attempts',
    initial_failures INT COMMENT 'Initial attempt failures',
    retry_count INT COMMENT 'Number of retries',
    final_success_count INT COMMENT 'Eventually successful',
    retry_rate_pct DOUBLE COMMENT 'Percentage requiring retry',
    eventual_success_pct DOUBLE COMMENT 'Percentage eventually succeeding'
)
COMMENT 'LLM: Analyzes job retry patterns to identify flaky jobs.
Use for identifying jobs that frequently need retries.
Example: "Which jobs are flaky?" or "Show me retry patterns"'
RETURN
    WITH run_attempts AS (
        SELECT
            job_id,
            run_date,
            COUNT(*) AS attempts_per_day,
            SUM(CASE WHEN is_success THEN 1 ELSE 0 END) AS successes_per_day,
            MIN(period_start_time) AS first_attempt_time
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY job_id, run_date
    ),
    job_retry_stats AS (
        SELECT
            r.job_id,
            j.name AS job_name,
            SUM(r.attempts_per_day) AS total_attempts,
            COUNT(CASE WHEN r.attempts_per_day > 1 AND r.successes_per_day < r.attempts_per_day THEN 1 END) AS days_with_retries,
            SUM(CASE WHEN r.attempts_per_day > 1 THEN r.attempts_per_day - 1 ELSE 0 END) AS retry_count,
            SUM(CASE WHEN r.successes_per_day > 0 THEN 1 ELSE 0 END) AS days_eventually_successful,
            COUNT(DISTINCT r.run_date) AS total_days
        FROM run_attempts r
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON r.job_id = j.job_id AND j.is_current = TRUE
        GROUP BY r.job_id, j.name
    )
    SELECT
        job_id,
        job_name,
        total_attempts,
        total_days AS initial_failures,
        retry_count,
        days_eventually_successful AS final_success_count,
        (days_with_retries * 100.0 / NULLIF(total_days, 0)) AS retry_rate_pct,
        (days_eventually_successful * 100.0 / NULLIF(total_days, 0)) AS eventual_success_pct
    FROM job_retry_stats
    WHERE retry_count > 0
    ORDER BY retry_count DESC;


-- -----------------------------------------------------------------------------
-- TVF: get_job_repair_costs
-- Returns jobs with highest repair (retry) costs
-- Reference: Microsoft Learn - Jobs Cost Operational Health
-- -----------------------------------------------------------------------------
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
    total_runs INT COMMENT 'Total number of runs',
    repair_count INT COMMENT 'Number of repairs (retries)',
    repair_cost DOUBLE COMMENT 'Total cost of repair runs in USD',
    repair_pct DOUBLE COMMENT 'Percentage of runs that were repairs'
)
COMMENT 'LLM: Returns jobs with highest repair (retry) costs.
- PURPOSE: Identify jobs with reliability issues causing wasted spend
- BEST FOR: "Which jobs have highest repair costs?" "Show job retry costs"
- PARAMS: start_date, end_date, top_n
- RETURNS: Jobs ranked by repair cost
Example: SELECT * FROM TABLE(get_job_repair_costs("2024-01-01", "2024-12-31", 20))'
RETURN
    WITH job_runs AS (
        SELECT
            jrt.job_id,
            jrt.run_id,
            jrt.result_state,
            jrt.is_success,
            j.name AS job_name,
            j.run_as
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND jrt.result_state IS NOT NULL
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            usage_metadata_job_run_id AS run_id,
            SUM(list_cost) AS run_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id, usage_metadata_job_run_id
    ),
    run_summary AS (
        SELECT
            jr.job_id,
            FIRST(jr.job_name) AS job_name,
            FIRST(jr.run_as) AS run_as,
            COUNT(DISTINCT jr.run_id) AS total_runs,
            SUM(CASE WHEN jr.is_success = FALSE THEN 1 ELSE 0 END) AS repair_count,
            SUM(CASE WHEN jr.is_success = FALSE THEN COALESCE(jc.run_cost, 0) ELSE 0 END) AS repair_cost
        FROM job_runs jr
        LEFT JOIN job_costs jc ON jr.job_id = jc.job_id AND jr.run_id = jc.run_id
        GROUP BY jr.job_id
    ),
    ranked AS (
        SELECT *,
            ROW_NUMBER() OVER (ORDER BY repair_cost DESC) AS rank
        FROM run_summary
        WHERE repair_count > 0
    )
    SELECT CAST(rank AS INT) AS rank, job_id, job_name, run_as, total_runs, repair_count,
           ROUND(repair_cost, 2) AS repair_cost,
           ROUND(repair_count * 100.0 / NULLIF(total_runs, 0), 2) AS repair_pct
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF: get_job_spend_trend_analysis
-- Identifies jobs with highest increase in cost week-over-week
-- Reference: Microsoft Learn - Cost Observability Queries
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_spend_trend_analysis(
    days_back INT DEFAULT 14 COMMENT 'Number of days to analyze',
    top_n INT DEFAULT 50 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    job_name STRING COMMENT 'Job name',
    workspace_id STRING COMMENT 'Workspace ID',
    job_id STRING COMMENT 'Job ID',
    run_as STRING COMMENT 'Job owner',
    last_7_day_spend DOUBLE COMMENT 'Spend in last 7 days',
    prior_7_day_spend DOUBLE COMMENT 'Spend in prior 7 days',
    spend_growth DOUBLE COMMENT 'Absolute growth in spend',
    spend_growth_pct DOUBLE COMMENT 'Percentage growth in spend'
)
COMMENT 'LLM: Identifies jobs with highest increase in cost spend week-over-week.
- PURPOSE: Cost anomaly detection and spend trend analysis for jobs
- BEST FOR: "Which jobs have highest cost growth?" "Show job spending trends"
- PARAMS: days_back (default 14), top_n
- RETURNS: Jobs ranked by cost growth
Example: SELECT * FROM TABLE(get_job_spend_trend_analysis(14, 25))'
RETURN
    WITH job_costs AS (
        SELECT
            workspace_id,
            usage_metadata_job_id AS job_id,
            COALESCE(identity_metadata_run_as, owned_by) AS run_as,
            SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 7 DAY AND CURRENT_DATE() - INTERVAL 1 DAY
                     THEN list_cost ELSE 0 END) AS last_7_day_spend,
            SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAY AND CURRENT_DATE() - INTERVAL 8 DAY
                     THEN list_cost ELSE 0 END) AS prior_7_day_spend
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY workspace_id, usage_metadata_job_id, COALESCE(identity_metadata_run_as, owned_by)
    ),
    with_growth AS (
        SELECT
            j.name AS job_name,
            jc.workspace_id,
            jc.job_id,
            jc.run_as,
            jc.last_7_day_spend,
            jc.prior_7_day_spend,
            jc.last_7_day_spend - jc.prior_7_day_spend AS spend_growth,
            (jc.last_7_day_spend - jc.prior_7_day_spend) / NULLIF(jc.prior_7_day_spend, 0) * 100 AS spend_growth_pct
        FROM job_costs jc
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jc.job_id = j.job_id AND j.is_current = TRUE
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY spend_growth DESC) AS rank
        FROM with_growth
    )
    SELECT job_name, workspace_id, job_id, run_as,
           ROUND(last_7_day_spend, 2) AS last_7_day_spend,
           ROUND(prior_7_day_spend, 2) AS prior_7_day_spend,
           ROUND(spend_growth, 2) AS spend_growth,
           ROUND(spend_growth_pct, 2) AS spend_growth_pct
    FROM ranked
    WHERE rank <= top_n
    ORDER BY spend_growth DESC;


-- -----------------------------------------------------------------------------
-- TVF: get_job_failure_costs
-- Returns jobs with high failure counts and associated costs
-- Reference: Microsoft Learn - Operational Health Queries
-- -----------------------------------------------------------------------------
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
    success_rate DOUBLE COMMENT 'Success rate percentage',
    failure_cost DOUBLE COMMENT 'Cost of failed runs in USD',
    last_failure_date DATE COMMENT 'Date of last failure'
)
COMMENT 'LLM: Returns jobs with high failure counts and their associated costs.
- PURPOSE: Identify unreliable jobs that waste spend
- BEST FOR: "Which failing jobs cost the most?" "Show job failure costs"
- PARAMS: start_date, end_date, top_n
- RETURNS: Jobs ranked by failure count
Example: SELECT * FROM TABLE(get_job_failure_costs("2024-01-01", "2024-12-31", 30))'
RETURN
    WITH job_runs AS (
        SELECT
            jrt.workspace_id,
            jrt.job_id,
            jrt.run_id,
            jrt.is_success,
            jrt.result_state,
            jrt.run_date
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        WHERE jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND jrt.result_state IS NOT NULL
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            usage_metadata_job_run_id AS run_id,
            SUM(list_cost) AS run_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id, usage_metadata_job_run_id
    ),
    aggregated AS (
        SELECT
            jr.workspace_id,
            jr.job_id,
            j.name AS job_name,
            j.run_as,
            COUNT(DISTINCT jr.run_id) AS total_runs,
            SUM(CASE WHEN jr.is_success = FALSE THEN 1 ELSE 0 END) AS failures,
            SUM(CASE WHEN jr.is_success = FALSE THEN COALESCE(jc.run_cost, 0) ELSE 0 END) AS failure_cost,
            MAX(CASE WHEN jr.is_success = FALSE THEN jr.run_date END) AS last_failure_date
        FROM job_runs jr
        LEFT JOIN job_costs jc ON jr.job_id = jc.job_id AND jr.run_id = jc.run_id
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON jr.job_id = j.job_id AND j.is_current = TRUE
        GROUP BY jr.workspace_id, jr.job_id, j.name, j.run_as
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY failures DESC) AS rank
        FROM aggregated
        WHERE failures > 0
    )
    SELECT job_name, workspace_id, job_id, run_as, total_runs, failures,
           ROUND((total_runs - failures) * 100.0 / NULLIF(total_runs, 0), 2) AS success_rate,
           ROUND(failure_cost, 2) AS failure_cost,
           last_failure_date
    FROM ranked
    WHERE rank <= top_n
    ORDER BY failures DESC;


-- -----------------------------------------------------------------------------
-- TVF: get_job_run_duration_analysis
-- Returns job run duration statistics with percentiles
-- Reference: Microsoft Learn - Job Run Timeline Queries
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_run_duration_analysis(
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze',
    min_runs INT DEFAULT 5 COMMENT 'Minimum number of runs to include job',
    top_n INT DEFAULT 100 COMMENT 'Number of jobs to return'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    total_runs INT COMMENT 'Total number of runs',
    avg_duration_min DOUBLE COMMENT 'Average duration in minutes',
    median_duration_min DOUBLE COMMENT 'Median (P50) duration in minutes',
    p90_duration_min DOUBLE COMMENT 'P90 duration in minutes',
    p95_duration_min DOUBLE COMMENT 'P95 duration in minutes',
    max_duration_min DOUBLE COMMENT 'Maximum duration in minutes'
)
COMMENT 'LLM: Returns job run duration statistics with percentiles.
- PURPOSE: SLA analysis and identifying slow jobs
- BEST FOR: "What are the P95 job durations?" "Which jobs take the longest?"
- PARAMS: days_back, min_runs, top_n
- RETURNS: Jobs with duration statistics
Example: SELECT * FROM TABLE(get_job_run_duration_analysis(7, 5, 50))'
RETURN
    WITH job_durations AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            jrt.run_duration_minutes
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.run_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND jrt.result_state IS NOT NULL
            AND jrt.run_duration_minutes IS NOT NULL
    ),
    duration_stats AS (
        SELECT
            job_id,
            FIRST(job_name) AS job_name,
            COUNT(*) AS total_runs,
            AVG(run_duration_minutes) AS avg_duration_min,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY run_duration_minutes) AS median_duration_min,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY run_duration_minutes) AS p90_duration_min,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY run_duration_minutes) AS p95_duration_min,
            MAX(run_duration_minutes) AS max_duration_min
        FROM job_durations
        GROUP BY job_id
        HAVING COUNT(*) >= min_runs
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY p95_duration_min DESC) AS rank
        FROM duration_stats
    )
    SELECT job_id, job_name, total_runs,
           ROUND(avg_duration_min, 2) AS avg_duration_min,
           ROUND(median_duration_min, 2) AS median_duration_min,
           ROUND(p90_duration_min, 2) AS p90_duration_min,
           ROUND(p95_duration_min, 2) AS p95_duration_min,
           ROUND(max_duration_min, 2) AS max_duration_min
    FROM ranked
    WHERE rank <= top_n
    ORDER BY p95_duration_min DESC;
