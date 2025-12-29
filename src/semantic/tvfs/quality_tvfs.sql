-- =============================================================================
-- DATA QUALITY AGENT TVFs
-- =============================================================================
-- Table-Valued Functions for data quality monitoring and governance
--
-- NOTE: These TVFs require data quality monitoring tables to be populated.
-- In a full implementation, these would query:
-- - fact_table_quality (from Lakehouse Monitor)
-- - fact_column_statistics
-- - fact_data_freshness
--
-- For MVP, these use proxy metrics from existing tables.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TVF 1: get_table_freshness
-- Returns freshness status of tables based on last update time
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_table_freshness(
    freshness_threshold_hours INT DEFAULT 24 COMMENT 'Maximum acceptable hours since last update'
)
RETURNS TABLE(
    table_catalog STRING COMMENT 'Catalog name',
    table_schema STRING COMMENT 'Schema name',
    table_name STRING COMMENT 'Table name',
    last_modified TIMESTAMP COMMENT 'Last modification time',
    hours_since_update DOUBLE COMMENT 'Hours since last update',
    is_stale BOOLEAN COMMENT 'True if exceeds threshold',
    row_count BIGINT COMMENT 'Approximate row count'
)
COMMENT '
- PURPOSE: Table freshness monitoring to identify stale data and SLA violations
- BEST FOR: "Which tables are stale?" "Show table freshness status" "Data freshness report"
- NOT FOR: Domain-level summary (use get_data_freshness_by_domain), quality scores (use get_job_data_quality_status)
- RETURNS: Tables with last modified time, hours since update, staleness flag, and row count
- PARAMS: freshness_threshold_hours (default 24)
- SYNTAX: SELECT * FROM TABLE(get_table_freshness(24))
'
RETURN
    SELECT
        table_catalog,
        table_schema,
        table_name,
        last_altered AS last_modified,
        TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) AS hours_since_update,
        TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) > freshness_threshold_hours AS is_stale,
        NULL AS row_count  -- Would need DESCRIBE DETAIL
    FROM ${catalog}.information_schema.tables
    WHERE table_catalog = '${catalog}'
        AND table_schema = '${gold_schema}'
        AND table_type = 'MANAGED'
    ORDER BY hours_since_update DESC;


-- -----------------------------------------------------------------------------
-- TVF 2: get_job_data_quality_status
-- Returns data quality status based on job success patterns
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_data_quality_status(
    days_back INT COMMENT 'Number of days to analyze (required)'
)
RETURNS TABLE(
    job_name STRING COMMENT 'Job name',
    total_runs INT COMMENT 'Total runs in period',
    successful_runs INT COMMENT 'Successful runs',
    failed_runs INT COMMENT 'Failed runs',
    success_rate_pct DOUBLE COMMENT 'Success rate percentage',
    data_quality_score INT COMMENT 'Quality score (0-100)',
    last_success TIMESTAMP COMMENT 'Last successful run',
    status STRING COMMENT 'HEALTHY, WARNING, or CRITICAL'
)
COMMENT '
- PURPOSE: Data quality status inference from job execution patterns for pipeline health
- BEST FOR: "What is the data quality status?" "Which pipelines are unhealthy?" "Job health scores"
- NOT FOR: Table freshness (use get_table_freshness), detailed failures (use get_failed_jobs)
- RETURNS: Jobs with success rate, quality score (0-100), last success, and health status
- PARAMS: days_back (default 7)
- SYNTAX: SELECT * FROM TABLE(get_job_data_quality_status(7))
- NOTE: Status levels: HEALTHY (>=95%), WARNING (>=80%), CRITICAL (<80%)
'
RETURN
    WITH job_stats AS (
        SELECT
            j.name AS job_name,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN jrt.is_success THEN 1 ELSE 0 END) AS successful_runs,
            SUM(CASE WHEN NOT jrt.is_success THEN 1 ELSE 0 END) AS failed_runs,
            MAX(CASE WHEN jrt.is_success THEN jrt.period_end_time END) AS last_success
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
        WHERE jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
        GROUP BY j.name
    )
    SELECT
        job_name,
        total_runs,
        successful_runs,
        failed_runs,
        (successful_runs * 100.0 / NULLIF(total_runs, 0)) AS success_rate_pct,
        CAST((successful_runs * 100.0 / NULLIF(total_runs, 0)) AS INT) AS data_quality_score,
        last_success,
        CASE
            WHEN successful_runs * 100.0 / NULLIF(total_runs, 0) >= 95 THEN 'HEALTHY'
            WHEN successful_runs * 100.0 / NULLIF(total_runs, 0) >= 80 THEN 'WARNING'
            ELSE 'CRITICAL'
        END AS status
    FROM job_stats
    WHERE total_runs >= 3
    ORDER BY success_rate_pct ASC;


-- -----------------------------------------------------------------------------
-- TVF 3: get_data_freshness_by_domain
-- Returns freshness summary by domain
-- NOTE: Simplified to avoid parameter in aggregate expressions (unsupported in SQL TVFs)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_data_freshness_by_domain(
    freshness_threshold_hours INT COMMENT 'Maximum acceptable hours since last update (required)'
)
RETURNS TABLE(
    domain STRING COMMENT 'Data domain (billing, compute, etc.)',
    table_count INT COMMENT 'Number of tables',
    avg_hours_since_update DOUBLE COMMENT 'Average hours since last update',
    max_hours_since_update DOUBLE COMMENT 'Maximum hours since last update (oldest table)',
    min_hours_since_update DOUBLE COMMENT 'Minimum hours since last update (freshest table)',
    freshness_threshold INT COMMENT 'The threshold used for freshness evaluation'
)
COMMENT '
- PURPOSE: Domain-level data freshness summary for governance reporting and SLA tracking
- BEST FOR: "How fresh is data by domain?" "Which domains have stale data?" "Domain freshness summary"
- NOT FOR: Individual table freshness (use get_table_freshness), quality scores (use get_data_quality_summary)
- RETURNS: Domains with table count, avg/max/min hours since update, and the threshold for reference
- PARAMS: freshness_threshold_hours (required) - for reference in output
- SYNTAX: SELECT * FROM TABLE(get_data_freshness_by_domain(24))
- NOTE: Compare max_hours_since_update to freshness_threshold to identify stale domains
'
RETURN
    SELECT
        CASE
            WHEN table_name LIKE '%usage%' OR table_name LIKE '%price%' THEN 'billing'
            WHEN table_name LIKE '%job%' OR table_name LIKE '%pipeline%' THEN 'lakeflow'
            WHEN table_name LIKE '%query%' OR table_name LIKE '%warehouse%' THEN 'query_performance'
            WHEN table_name LIKE '%cluster%' OR table_name LIKE '%node%' THEN 'compute'
            WHEN table_name LIKE '%audit%' OR table_name LIKE '%lineage%' THEN 'security'
            ELSE 'other'
        END AS domain,
        CAST(COUNT(*) AS INT) AS table_count,
        ROUND(AVG(TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP())), 2) AS avg_hours_since_update,
        ROUND(MAX(TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP())), 2) AS max_hours_since_update,
        ROUND(MIN(TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP())), 2) AS min_hours_since_update,
        freshness_threshold_hours AS freshness_threshold
    FROM ${catalog}.information_schema.tables
    WHERE table_catalog = '${catalog}'
        AND table_schema = '${gold_schema}'
        AND table_type = 'MANAGED'
    GROUP BY 
        CASE
            WHEN table_name LIKE '%usage%' OR table_name LIKE '%price%' THEN 'billing'
            WHEN table_name LIKE '%job%' OR table_name LIKE '%pipeline%' THEN 'lakeflow'
            WHEN table_name LIKE '%query%' OR table_name LIKE '%warehouse%' THEN 'query_performance'
            WHEN table_name LIKE '%cluster%' OR table_name LIKE '%node%' THEN 'compute'
            WHEN table_name LIKE '%audit%' OR table_name LIKE '%lineage%' THEN 'security'
            ELSE 'other'
        END
    ORDER BY max_hours_since_update DESC;


-- -----------------------------------------------------------------------------
-- TVF 4: get_data_quality_summary
-- Returns overall data quality summary across Gold tables
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_data_quality_summary()
RETURNS TABLE(
    quality_dimension STRING COMMENT 'Quality dimension (completeness, freshness, etc.)',
    metric_name STRING COMMENT 'Specific metric being measured',
    metric_value DOUBLE COMMENT 'Metric value (0-100 for percentages)',
    target_value DOUBLE COMMENT 'Target threshold',
    status STRING COMMENT 'PASS, WARNING, or FAIL',
    details STRING COMMENT 'Additional details'
)
COMMENT '
- PURPOSE: Overall data quality summary across all dimensions for executive dashboard
- BEST FOR: "What is our data quality score?" "Show quality summary" "Executive data quality"
- NOT FOR: Individual table issues (use get_tables_failing_quality), domain breakdown (use get_data_freshness_by_domain)
- RETURNS: Quality metrics by dimension (freshness, volume, consistency) with status and targets
- PARAMS: None
- SYNTAX: SELECT * FROM TABLE(get_data_quality_summary())
- NOTE: Status levels: PASS (meets target), WARNING (close to target), FAIL (below target)
'
RETURN
    -- Freshness metrics
    SELECT
        'FRESHNESS' AS quality_dimension,
        'Gold Tables Fresh (<24h)' AS metric_name,
        (SUM(CASE WHEN TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) <= 24 THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)) AS metric_value,
        90.0 AS target_value,
        CASE
            WHEN (SUM(CASE WHEN TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) <= 24 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0)) >= 90 THEN 'PASS'
            WHEN (SUM(CASE WHEN TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) <= 24 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0)) >= 75 THEN 'WARNING'
            ELSE 'FAIL'
        END AS status,
        CONCAT(
            SUM(CASE WHEN TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) <= 24 THEN 1 ELSE 0 END),
            ' of ', COUNT(*), ' tables fresh'
        ) AS details
    FROM ${catalog}.information_schema.tables
    WHERE table_catalog = '${catalog}'
        AND table_schema = '${gold_schema}'
        AND table_type = 'MANAGED'

    UNION ALL

    -- Record count check
    SELECT
        'VOLUME' AS quality_dimension,
        'Tables With Records' AS metric_name,
        (SUM(CASE WHEN table_name LIKE 'fact_%' OR table_name LIKE 'dim_%' THEN 1 ELSE 0 END) * 100.0 /
            NULLIF(COUNT(*), 0)) AS metric_value,
        100.0 AS target_value,
        CASE
            WHEN COUNT(*) > 10 THEN 'PASS'
            ELSE 'WARNING'
        END AS status,
        CONCAT(COUNT(*), ' total tables in Gold schema') AS details
    FROM ${catalog}.information_schema.tables
    WHERE table_catalog = '${catalog}'
        AND table_schema = '${gold_schema}'
        AND table_type = 'MANAGED'

    UNION ALL

    -- Schema consistency
    SELECT
        'CONSISTENCY' AS quality_dimension,
        'Schema Coverage' AS metric_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM ${catalog}.information_schema.tables
            WHERE table_schema = '${gold_schema}' AND table_name LIKE 'fact_usage%'
        ) THEN 100.0 ELSE 0.0 END AS metric_value,
        100.0 AS target_value,
        CASE WHEN EXISTS (
            SELECT 1 FROM ${catalog}.information_schema.tables
            WHERE table_schema = '${gold_schema}' AND table_name LIKE 'fact_usage%'
        ) THEN 'PASS' ELSE 'FAIL' END AS status,
        'Core billing fact table exists' AS details

    UNION ALL

    SELECT
        'CONSISTENCY' AS quality_dimension,
        'Dimension Tables' AS metric_name,
        (SELECT COUNT(*) FROM ${catalog}.information_schema.tables
         WHERE table_schema = '${gold_schema}' AND table_name LIKE 'dim_%') * 10.0 AS metric_value,
        50.0 AS target_value,
        CASE WHEN (SELECT COUNT(*) FROM ${catalog}.information_schema.tables
                   WHERE table_schema = '${gold_schema}' AND table_name LIKE 'dim_%') >= 5 THEN 'PASS'
             ELSE 'WARNING' END AS status,
        CONCAT((SELECT COUNT(*) FROM ${catalog}.information_schema.tables
                WHERE table_schema = '${gold_schema}' AND table_name LIKE 'dim_%'), ' dimension tables') AS details

    ORDER BY quality_dimension, metric_name;


-- -----------------------------------------------------------------------------
-- TVF 5: get_tables_failing_quality
-- Returns tables failing quality checks
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_tables_failing_quality(
    freshness_threshold_hours INT DEFAULT 24 COMMENT 'Hours threshold for freshness check'
)
RETURNS TABLE(
    table_name STRING COMMENT 'Table name',
    quality_issue STRING COMMENT 'Type of quality issue',
    current_value STRING COMMENT 'Current value',
    threshold STRING COMMENT 'Expected threshold',
    severity STRING COMMENT 'HIGH, MEDIUM, or LOW',
    recommendation STRING COMMENT 'Suggested action'
)
COMMENT '
- PURPOSE: Identify tables failing quality checks for targeted remediation
- BEST FOR: "Which tables have quality issues?" "Show failing tables" "Data quality alerts"
- NOT FOR: Overall summary (use get_data_quality_summary), domain breakdown (use get_data_freshness_by_domain)
- RETURNS: Failing tables with issue type, current value, threshold, severity, and recommendation
- PARAMS: freshness_threshold_hours (default 24)
- SYNTAX: SELECT * FROM TABLE(get_tables_failing_quality(24))
- NOTE: Severity levels: HIGH (3x threshold), MEDIUM (2x threshold), LOW (1x threshold)
'
RETURN
    WITH table_info AS (
        SELECT
            table_name,
            TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) AS hours_since_update
        FROM ${catalog}.information_schema.tables
        WHERE table_catalog = '${catalog}'
            AND table_schema = '${gold_schema}'
            AND table_type = 'MANAGED'
    )
    -- Stale tables
    SELECT
        table_name,
        'STALE_DATA' AS quality_issue,
        CONCAT(hours_since_update, ' hours') AS current_value,
        CONCAT(freshness_threshold_hours, ' hours') AS threshold,
        CASE
            WHEN hours_since_update > freshness_threshold_hours * 3 THEN 'HIGH'
            WHEN hours_since_update > freshness_threshold_hours * 2 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS severity,
        'Check pipeline execution and data source availability' AS recommendation
    FROM table_info
    WHERE hours_since_update > freshness_threshold_hours

    ORDER BY severity DESC, hours_since_update DESC;


-- -----------------------------------------------------------------------------
-- TVF 6: get_table_activity_status
-- Returns active/inactive table status based on lineage data
-- Source: Dashboard lineage pattern analysis
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_table_activity_status(
    days_back INT COMMENT 'Number of days to analyze (required)',
    inactive_threshold_days INT DEFAULT 14 COMMENT 'Days without activity to flag as inactive'
)
RETURNS TABLE(
    table_full_name STRING COMMENT 'Full table name (catalog.schema.table)',
    table_catalog STRING COMMENT 'Catalog name',
    table_schema STRING COMMENT 'Schema name',
    table_name STRING COMMENT 'Table name',
    read_count INT COMMENT 'Number of reads in period',
    write_count INT COMMENT 'Number of writes in period',
    total_access_count INT COMMENT 'Total accesses in period',
    unique_readers INT COMMENT 'Unique users who read the table',
    unique_writers INT COMMENT 'Unique users who wrote to the table',
    last_read_date DATE COMMENT 'Date of last read',
    last_write_date DATE COMMENT 'Date of last write',
    days_since_last_access INT COMMENT 'Days since last access',
    activity_status STRING COMMENT 'ACTIVE, INACTIVE, or ORPHANED',
    recommendation STRING COMMENT 'Suggested action'
)
COMMENT '
- PURPOSE: Table activity analysis from lineage to identify orphaned/inactive tables for cleanup
- BEST FOR: "Which tables are inactive?" "Show orphaned tables" "Unused table analysis"
- NOT FOR: Data lineage tracking (use get_pipeline_data_lineage), table freshness (use get_table_freshness)
- RETURNS: Tables with read/write counts, activity status, days since last access, and recommendation
- PARAMS: days_back (default 30), inactive_threshold_days (default 14)
- SYNTAX: SELECT * FROM TABLE(get_table_activity_status(30, 14))
- NOTE: Status levels: ACTIVE, INACTIVE, ORPHANED (no activity detected)
'
RETURN
    WITH table_reads AS (
        SELECT
            source_table_full_name AS table_full_name,
            event_date,
            created_by
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND source_table_full_name IS NOT NULL
    ),
    table_writes AS (
        SELECT
            target_table_full_name AS table_full_name,
            event_date,
            created_by
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND target_table_full_name IS NOT NULL
    ),
    table_activity AS (
        SELECT
            COALESCE(r.table_full_name, w.table_full_name) AS table_full_name,
            COUNT(DISTINCT r.event_date) AS read_count,
            COUNT(DISTINCT w.event_date) AS write_count,
            COUNT(DISTINCT r.event_date) + COUNT(DISTINCT w.event_date) AS total_access_count,
            COUNT(DISTINCT r.created_by) AS unique_readers,
            COUNT(DISTINCT w.created_by) AS unique_writers,
            MAX(r.event_date) AS last_read_date,
            MAX(w.event_date) AS last_write_date
        FROM table_reads r
        FULL OUTER JOIN table_writes w
            ON r.table_full_name = w.table_full_name
        GROUP BY COALESCE(r.table_full_name, w.table_full_name)
    )
    SELECT
        ta.table_full_name,
        SPLIT(ta.table_full_name, '\\.')[0] AS table_catalog,
        SPLIT(ta.table_full_name, '\\.')[1] AS table_schema,
        SPLIT(ta.table_full_name, '\\.')[2] AS table_name,
        ta.read_count,
        ta.write_count,
        ta.total_access_count,
        ta.unique_readers,
        ta.unique_writers,
        ta.last_read_date,
        ta.last_write_date,
        DATEDIFF(CURRENT_DATE(), COALESCE(
            GREATEST(ta.last_read_date, ta.last_write_date),
            ta.last_read_date,
            ta.last_write_date
        )) AS days_since_last_access,
        CASE
            WHEN DATEDIFF(CURRENT_DATE(), COALESCE(
                GREATEST(ta.last_read_date, ta.last_write_date),
                ta.last_read_date,
                ta.last_write_date
            )) <= inactive_threshold_days THEN 'ACTIVE'
            WHEN ta.read_count = 0 AND ta.write_count = 0 THEN 'ORPHANED'
            ELSE 'INACTIVE'
        END AS activity_status,
        CASE
            WHEN ta.read_count = 0 AND ta.write_count = 0 THEN 'No activity detected - consider archiving or deleting'
            WHEN DATEDIFF(CURRENT_DATE(), COALESCE(
                GREATEST(ta.last_read_date, ta.last_write_date),
                ta.last_read_date,
                ta.last_write_date
            )) > inactive_threshold_days * 2 THEN 'Consider archiving - no recent activity'
            WHEN ta.unique_readers = 0 THEN 'Table has writes but no reads - review pipeline'
            ELSE 'No action needed'
        END AS recommendation
    FROM table_activity ta
    ORDER BY
        CASE activity_status
            WHEN 'ORPHANED' THEN 1
            WHEN 'INACTIVE' THEN 2
            ELSE 3
        END,
        days_since_last_access DESC;


-- -----------------------------------------------------------------------------
-- TVF 7: get_pipeline_data_lineage
-- Returns data lineage for pipelines showing upstream/downstream dependencies
-- Source: Dashboard lineage tracking pattern
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_pipeline_data_lineage(
    days_back INT COMMENT 'Number of days to analyze (required)',
    entity_filter STRING DEFAULT 'ALL' COMMENT 'Entity type filter: JOB, NOTEBOOK, PIPELINE, or ALL'
)
RETURNS TABLE(
    entity_type STRING COMMENT 'Entity type (JOB, NOTEBOOK, PIPELINE)',
    entity_id STRING COMMENT 'Entity identifier',
    entity_name STRING COMMENT 'Entity name if available',
    source_tables STRING COMMENT 'Comma-separated list of source tables',
    target_tables STRING COMMENT 'Comma-separated list of target tables',
    source_count INT COMMENT 'Number of source tables',
    target_count INT COMMENT 'Number of target tables',
    unique_days INT COMMENT 'Days with lineage events',
    total_events INT COMMENT 'Total lineage events',
    last_run_date DATE COMMENT 'Date of last lineage event',
    complexity_score INT COMMENT 'Complexity score based on tables touched'
)
COMMENT '
- PURPOSE: Pipeline data lineage showing upstream/downstream table dependencies for impact analysis
- BEST FOR: "Show pipeline lineage" "What tables does this job read from?" "Data flow analysis"
- NOT FOR: Table activity status (use get_table_activity_status), table access audit (use get_table_access_audit)
- RETURNS: Entities with source tables, target tables, counts, and complexity score
- PARAMS: days_back (default 7), entity_filter (JOB/NOTEBOOK/PIPELINE/ALL)
- SYNTAX: SELECT * FROM TABLE(get_pipeline_data_lineage(7, "JOB"))
'
RETURN
    WITH lineage_summary AS (
        SELECT
            entity_type,
            entity_id,
            COLLECT_SET(source_table_full_name) AS sources,
            COLLECT_SET(target_table_full_name) AS targets,
            COUNT(DISTINCT event_date) AS unique_days,
            COUNT(*) AS total_events,
            MAX(event_date) AS last_run_date
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND (entity_filter = 'ALL' OR entity_type = entity_filter)
        GROUP BY entity_type, entity_id
    )
    SELECT
        ls.entity_type,
        ls.entity_id,
        COALESCE(j.name, ls.entity_id) AS entity_name,
        CONCAT_WS(', ', ls.sources) AS source_tables,
        CONCAT_WS(', ', ls.targets) AS target_tables,
        SIZE(ls.sources) AS source_count,
        SIZE(ls.targets) AS target_count,
        ls.unique_days,
        ls.total_events,
        ls.last_run_date,
        -- Complexity score: more tables = higher complexity
        SIZE(ls.sources) + SIZE(ls.targets) * 2 AS complexity_score
    FROM lineage_summary ls
    LEFT JOIN ${catalog}.${gold_schema}.dim_job j
        ON ls.entity_type = 'JOB' AND ls.entity_id = j.job_id AND j.delete_time IS NULL
    ORDER BY complexity_score DESC, total_events DESC;
