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
COMMENT 'LLM: Returns freshness status of tables to identify stale data.
Use for data quality monitoring and SLA compliance.
Example: "Which tables are stale?" or "Show me table freshness status"'
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
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze'
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
COMMENT 'LLM: Returns data quality status inferred from job execution patterns.
Use for identifying data pipeline issues and quality degradation.
Example: "What is the data quality status?" or "Which pipelines are unhealthy?"'
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
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.run_date >= CURRENT_DATE() - INTERVAL days_back DAY
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
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_data_freshness_by_domain(
    freshness_threshold_hours INT DEFAULT 24 COMMENT 'Maximum acceptable hours since last update'
)
RETURNS TABLE(
    domain STRING COMMENT 'Data domain (billing, compute, etc.)',
    table_count INT COMMENT 'Number of tables',
    fresh_tables INT COMMENT 'Tables within freshness SLA',
    stale_tables INT COMMENT 'Tables exceeding freshness SLA',
    freshness_pct DOUBLE COMMENT 'Percentage of fresh tables',
    oldest_table_hours DOUBLE COMMENT 'Hours since oldest table update'
)
COMMENT 'LLM: Returns data freshness summary by domain for governance reporting.
Use for identifying which data domains have freshness issues.
Example: "How fresh is our data by domain?" or "Which domains have stale data?"'
RETURN
    WITH table_freshness AS (
        SELECT
            CASE
                WHEN table_name LIKE '%usage%' OR table_name LIKE '%price%' THEN 'billing'
                WHEN table_name LIKE '%job%' OR table_name LIKE '%pipeline%' THEN 'lakeflow'
                WHEN table_name LIKE '%query%' OR table_name LIKE '%warehouse%' THEN 'query_performance'
                WHEN table_name LIKE '%cluster%' OR table_name LIKE '%node%' THEN 'compute'
                WHEN table_name LIKE '%audit%' OR table_name LIKE '%lineage%' THEN 'security'
                ELSE 'other'
            END AS domain,
            table_name,
            TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) AS hours_since_update
        FROM ${catalog}.information_schema.tables
        WHERE table_catalog = '${catalog}'
            AND table_schema = '${gold_schema}'
            AND table_type = 'MANAGED'
    )
    SELECT
        domain,
        COUNT(*) AS table_count,
        SUM(CASE WHEN hours_since_update <= freshness_threshold_hours THEN 1 ELSE 0 END) AS fresh_tables,
        SUM(CASE WHEN hours_since_update > freshness_threshold_hours THEN 1 ELSE 0 END) AS stale_tables,
        (SUM(CASE WHEN hours_since_update <= freshness_threshold_hours THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) AS freshness_pct,
        MAX(hours_since_update) AS oldest_table_hours
    FROM table_freshness
    GROUP BY domain
    ORDER BY freshness_pct ASC;


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
COMMENT 'LLM: Returns overall data quality summary across Gold layer tables.
- PURPOSE: Executive quality dashboard, SLA monitoring
- BEST FOR: "What is our data quality score?" "Show quality summary"
- PARAMS: None
- RETURNS: Quality metrics across all dimensions
Example: SELECT * FROM TABLE(get_data_quality_summary())'
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
COMMENT 'LLM: Returns tables that are failing quality checks.
- PURPOSE: Identify data quality issues requiring attention
- BEST FOR: "Which tables have quality issues?" "Show failing tables"
- PARAMS: freshness_threshold_hours (default 24)
- RETURNS: Tables with quality issues and recommendations
Example: SELECT * FROM TABLE(get_tables_failing_quality(24))'
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
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze for activity',
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
COMMENT 'LLM: Returns table activity status based on lineage data to identify orphaned tables.
Use for data governance, cost optimization, and identifying unused tables for cleanup.
Example: "Which tables are inactive?" or "Show me orphaned tables"'
RETURN
    WITH table_reads AS (
        SELECT
            source_table_full_name AS table_full_name,
            event_date,
            created_by
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND source_table_full_name IS NOT NULL
    ),
    table_writes AS (
        SELECT
            target_table_full_name AS table_full_name,
            event_date,
            created_by
        FROM ${catalog}.${gold_schema}.fact_table_lineage
        WHERE event_date >= CURRENT_DATE() - INTERVAL days_back DAY
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
    days_back INT DEFAULT 7 COMMENT 'Number of days to analyze',
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
COMMENT 'LLM: Returns data lineage by pipeline/job showing upstream and downstream dependencies.
Use for impact analysis, data governance, and understanding data flow.
Example: "Show me pipeline lineage" or "What tables does this job read from?"'
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
        WHERE event_date >= CURRENT_DATE() - INTERVAL days_back DAY
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
        ON ls.entity_type = 'JOB' AND ls.entity_id = j.job_id AND j.is_current = TRUE
    ORDER BY complexity_score DESC, total_events DESC;
