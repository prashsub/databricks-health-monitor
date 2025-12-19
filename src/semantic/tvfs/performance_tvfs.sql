-- =============================================================================
-- PERFORMANCE AGENT TVFs
-- =============================================================================
-- Table-Valued Functions for query performance and warehouse optimization
--
-- All TVFs query Gold layer tables (fact_query_history, fact_warehouse_events)
-- Parameters use STRING type for dates (Genie compatibility)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TVF 1: get_slow_queries
-- Returns queries exceeding duration threshold
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_slow_queries(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    duration_threshold_seconds INT DEFAULT 300 COMMENT 'Minimum duration in seconds',
    top_n INT DEFAULT 50 COMMENT 'Number of queries to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Slowness rank',
    statement_id STRING COMMENT 'Query statement ID',
    warehouse_id STRING COMMENT 'Warehouse ID',
    warehouse_name STRING COMMENT 'Warehouse name',
    executed_by STRING COMMENT 'User who ran the query',
    statement_type STRING COMMENT 'Query type (SELECT, INSERT, etc.)',
    duration_seconds DOUBLE COMMENT 'Query duration in seconds',
    read_gb DOUBLE COMMENT 'Data read in GB',
    rows_produced BIGINT COMMENT 'Result rows',
    start_time TIMESTAMP COMMENT 'Query start time'
)
COMMENT 'LLM: Returns the slowest queries exceeding a duration threshold.
Use for identifying performance bottlenecks and optimization targets.
Example: "Show me slow queries" or "Which queries took longer than 5 minutes?"'
RETURN
    WITH slow AS (
        SELECT
            q.statement_id,
            q.compute_warehouse_id AS warehouse_id,
            w.warehouse_name,
            q.executed_by,
            q.statement_type,
            q.total_duration_ms / 1000.0 AS duration_seconds,
            q.read_bytes / 1073741824.0 AS read_gb,
            q.produced_rows AS rows_produced,
            q.start_time,
            ROW_NUMBER() OVER (ORDER BY q.total_duration_ms DESC) AS rank
        FROM ${catalog}.${gold_schema}.fact_query_history q
        LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w
            ON q.compute_warehouse_id = w.warehouse_id AND w.is_current = TRUE
        WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND q.total_duration_ms >= duration_threshold_seconds * 1000
            AND q.execution_status = 'FINISHED'
    )
    SELECT rank, statement_id, warehouse_id, warehouse_name, executed_by,
           statement_type, duration_seconds, read_gb, rows_produced, start_time
    FROM slow
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 2: get_warehouse_utilization
-- Returns warehouse utilization metrics
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_warehouse_utilization(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
    warehouse_id STRING COMMENT 'Warehouse ID',
    warehouse_name STRING COMMENT 'Warehouse name',
    warehouse_size STRING COMMENT 'Warehouse size (T-shirt size)',
    total_queries INT COMMENT 'Total queries executed',
    total_duration_hours DOUBLE COMMENT 'Total query duration in hours',
    avg_duration_seconds DOUBLE COMMENT 'Average query duration',
    p95_duration_seconds DOUBLE COMMENT '95th percentile duration',
    avg_queue_time_seconds DOUBLE COMMENT 'Average queue time',
    peak_concurrency INT COMMENT 'Peak concurrent queries',
    error_rate_pct DOUBLE COMMENT 'Query error rate'
)
COMMENT 'LLM: Returns warehouse utilization and performance metrics.
Use for right-sizing, capacity planning, and optimization.
Example: "Show me warehouse utilization" or "How are our warehouses performing?"'
RETURN
    SELECT
        q.compute_warehouse_id AS warehouse_id,
        w.warehouse_name,
        w.cluster_size AS warehouse_size,
        COUNT(*) AS total_queries,
        SUM(q.total_duration_ms) / 3600000.0 AS total_duration_hours,
        AVG(q.total_duration_ms) / 1000.0 AS avg_duration_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.95) AS p95_duration_seconds,
        AVG(COALESCE(q.waiting_in_queue_ms, 0)) / 1000.0 AS avg_queue_time_seconds,
        MAX(q.statement_id) AS peak_concurrency,  -- Placeholder: need proper concurrency calc
        (SUM(CASE WHEN q.execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) AS error_rate_pct
    FROM ${catalog}.${gold_schema}.fact_query_history q
    LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w
        ON q.compute_warehouse_id = w.warehouse_id AND w.is_current = TRUE
    WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND q.compute_warehouse_id IS NOT NULL
    GROUP BY q.compute_warehouse_id, w.warehouse_name, w.cluster_size
    ORDER BY total_queries DESC;


-- -----------------------------------------------------------------------------
-- TVF 3: get_query_efficiency
-- Returns query efficiency metrics and flags
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_query_efficiency(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    min_duration_seconds INT DEFAULT 60 COMMENT 'Minimum duration to analyze',
    top_n INT DEFAULT 100 COMMENT 'Number of queries to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Efficiency rank (1 = least efficient)',
    statement_id STRING COMMENT 'Query statement ID',
    warehouse_id STRING COMMENT 'Warehouse ID',
    executed_by STRING COMMENT 'User',
    duration_seconds DOUBLE COMMENT 'Duration in seconds',
    read_gb DOUBLE COMMENT 'Data read in GB',
    rows_produced BIGINT COMMENT 'Result rows',
    bytes_per_row DOUBLE COMMENT 'Bytes read per row produced',
    has_spill BOOLEAN COMMENT 'True if query spilled to disk',
    spill_gb DOUBLE COMMENT 'Data spilled in GB',
    efficiency_score INT COMMENT 'Efficiency score (0-100)',
    optimization_flags ARRAY<STRING> COMMENT 'Suggested optimizations'
)
COMMENT 'LLM: Returns query efficiency analysis with optimization suggestions.
Use for identifying inefficient queries and optimization opportunities.
Example: "Which queries are inefficient?" or "Show me queries that need optimization"'
RETURN
    WITH efficiency_analysis AS (
        SELECT
            statement_id,
            compute_warehouse_id AS warehouse_id,
            executed_by,
            total_duration_ms / 1000.0 AS duration_seconds,
            read_bytes / 1073741824.0 AS read_gb,
            produced_rows AS rows_produced,
            read_bytes / NULLIF(produced_rows, 0) AS bytes_per_row,
            spilled_local_bytes > 0 OR spilled_remote_bytes > 0 AS has_spill,
            (COALESCE(spilled_local_bytes, 0) + COALESCE(spilled_remote_bytes, 0)) / 1073741824.0 AS spill_gb,
            CASE
                WHEN spilled_local_bytes > 0 THEN 40
                WHEN read_bytes / NULLIF(produced_rows, 0) > 10000000 THEN 50
                WHEN total_duration_ms > 600000 THEN 60
                ELSE 80
            END AS efficiency_score,
            ARRAY_COMPACT(ARRAY(
                CASE WHEN spilled_local_bytes > 0 THEN 'REDUCE_DATA_SHUFFLE' END,
                CASE WHEN read_bytes / NULLIF(produced_rows, 0) > 10000000 THEN 'ADD_PARTITION_FILTER' END,
                CASE WHEN total_duration_ms > 600000 AND produced_rows < 1000 THEN 'OPTIMIZE_QUERY_PLAN' END,
                CASE WHEN read_bytes > 10737418240 THEN 'CONSIDER_CACHING' END
            )) AS optimization_flags
        FROM ${catalog}.${gold_schema}.fact_query_history
        WHERE DATE(start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND total_duration_ms >= min_duration_seconds * 1000
            AND execution_status = 'FINISHED'
    ),
    ranked AS (
        SELECT *,
            ROW_NUMBER() OVER (ORDER BY efficiency_score ASC, duration_seconds DESC) AS rank
        FROM efficiency_analysis
    )
    SELECT rank, statement_id, warehouse_id, executed_by, duration_seconds, read_gb,
           rows_produced, bytes_per_row, has_spill, spill_gb, efficiency_score, optimization_flags
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 4: get_high_spill_queries
-- Returns queries with significant disk spills
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_high_spill_queries(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    min_spill_gb DOUBLE DEFAULT 1.0 COMMENT 'Minimum spill in GB'
)
RETURNS TABLE(
    statement_id STRING COMMENT 'Query statement ID',
    warehouse_id STRING COMMENT 'Warehouse ID',
    executed_by STRING COMMENT 'User',
    statement_type STRING COMMENT 'Query type',
    duration_seconds DOUBLE COMMENT 'Duration in seconds',
    local_spill_gb DOUBLE COMMENT 'Local disk spill in GB',
    remote_spill_gb DOUBLE COMMENT 'Remote disk spill in GB',
    total_spill_gb DOUBLE COMMENT 'Total spill in GB',
    read_gb DOUBLE COMMENT 'Data read in GB',
    spill_ratio DOUBLE COMMENT 'Spill to read ratio'
)
COMMENT 'LLM: Returns queries with significant disk spills indicating memory pressure.
Use for identifying queries that need memory optimization or cluster resizing.
Example: "Show me queries with high spill" or "Which queries are spilling to disk?"'
RETURN
    SELECT
        statement_id,
        compute_warehouse_id AS warehouse_id,
        executed_by,
        statement_type,
        total_duration_ms / 1000.0 AS duration_seconds,
        COALESCE(spilled_local_bytes, 0) / 1073741824.0 AS local_spill_gb,
        COALESCE(spilled_remote_bytes, 0) / 1073741824.0 AS remote_spill_gb,
        (COALESCE(spilled_local_bytes, 0) + COALESCE(spilled_remote_bytes, 0)) / 1073741824.0 AS total_spill_gb,
        read_bytes / 1073741824.0 AS read_gb,
        (COALESCE(spilled_local_bytes, 0) + COALESCE(spilled_remote_bytes, 0)) / NULLIF(read_bytes, 0) AS spill_ratio
    FROM ${catalog}.${gold_schema}.fact_query_history
    WHERE DATE(start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (COALESCE(spilled_local_bytes, 0) + COALESCE(spilled_remote_bytes, 0)) >= min_spill_gb * 1073741824
    ORDER BY total_spill_gb DESC;


-- -----------------------------------------------------------------------------
-- TVF 5: get_query_volume_trends
-- Returns query volume trends over time
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_query_volume_trends(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze',
    granularity STRING DEFAULT 'DAY' COMMENT 'Granularity: HOUR, DAY, WEEK'
)
RETURNS TABLE(
    period_start TIMESTAMP COMMENT 'Start of period',
    query_count INT COMMENT 'Number of queries',
    unique_users INT COMMENT 'Unique users',
    avg_duration_seconds DOUBLE COMMENT 'Average duration',
    total_read_tb DOUBLE COMMENT 'Total data read in TB',
    error_count INT COMMENT 'Number of errors',
    prior_period_count INT COMMENT 'Prior period query count',
    change_pct DOUBLE COMMENT 'Change vs prior period'
)
COMMENT 'LLM: Returns query volume trends over time for capacity planning.
Use for identifying usage patterns and growth trends.
Example: "Show me query volume trends" or "How is query usage changing?"'
RETURN
    WITH periods AS (
        SELECT
            CASE
                WHEN granularity = 'HOUR' THEN DATE_TRUNC('HOUR', start_time)
                WHEN granularity = 'WEEK' THEN DATE_TRUNC('WEEK', start_time)
                ELSE DATE_TRUNC('DAY', start_time)
            END AS period_start,
            COUNT(*) AS query_count,
            COUNT(DISTINCT executed_by) AS unique_users,
            AVG(total_duration_ms) / 1000.0 AS avg_duration_seconds,
            SUM(read_bytes) / 1099511627776.0 AS total_read_tb,
            SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) AS error_count
        FROM ${catalog}.${gold_schema}.fact_query_history
        WHERE DATE(start_time) >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY 1
    )
    SELECT
        period_start,
        query_count,
        unique_users,
        avg_duration_seconds,
        total_read_tb,
        error_count,
        LAG(query_count) OVER (ORDER BY period_start) AS prior_period_count,
        ((query_count - LAG(query_count) OVER (ORDER BY period_start)) * 100.0 /
            NULLIF(LAG(query_count) OVER (ORDER BY period_start), 0)) AS change_pct
    FROM periods
    ORDER BY period_start;


-- -----------------------------------------------------------------------------
-- TVF 6: get_user_query_summary
-- Returns query usage summary by user
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_user_query_summary(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 50 COMMENT 'Number of top users to return'
)
RETURNS TABLE(
    rank INT COMMENT 'Usage rank',
    user_email STRING COMMENT 'User email',
    query_count INT COMMENT 'Total queries',
    total_duration_hours DOUBLE COMMENT 'Total query time in hours',
    avg_duration_seconds DOUBLE COMMENT 'Average query duration',
    total_read_gb DOUBLE COMMENT 'Total data read in GB',
    error_rate_pct DOUBLE COMMENT 'Query error rate',
    most_used_warehouse STRING COMMENT 'Most frequently used warehouse'
)
COMMENT 'LLM: Returns query usage summary by user for chargeback and analysis.
Use for identifying heavy users and query patterns.
Example: "Who runs the most queries?" or "Show me user query usage"'
RETURN
    WITH user_stats AS (
        SELECT
            executed_by AS user_email,
            COUNT(*) AS query_count,
            SUM(total_duration_ms) / 3600000.0 AS total_duration_hours,
            AVG(total_duration_ms) / 1000.0 AS avg_duration_seconds,
            SUM(read_bytes) / 1073741824.0 AS total_read_gb,
            (SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) AS error_rate_pct,
            FIRST(compute_warehouse_id, TRUE) AS most_used_warehouse
        FROM ${catalog}.${gold_schema}.fact_query_history
        WHERE DATE(start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY executed_by
    ),
    ranked AS (
        SELECT *,
            ROW_NUMBER() OVER (ORDER BY query_count DESC) AS rank
        FROM user_stats
    )
    SELECT rank, user_email, query_count, total_duration_hours, avg_duration_seconds,
           total_read_gb, error_rate_pct, most_used_warehouse
    FROM ranked
    WHERE rank <= top_n
    ORDER BY rank;


-- -----------------------------------------------------------------------------
-- TVF 7: get_query_latency_percentiles
-- Returns query latency percentiles by warehouse
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_query_latency_percentiles(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE(
    warehouse_id STRING COMMENT 'Warehouse ID',
    warehouse_name STRING COMMENT 'Warehouse name',
    query_count INT COMMENT 'Number of queries',
    p50_seconds DOUBLE COMMENT 'Median latency',
    p75_seconds DOUBLE COMMENT '75th percentile latency',
    p90_seconds DOUBLE COMMENT '90th percentile latency',
    p95_seconds DOUBLE COMMENT '95th percentile latency',
    p99_seconds DOUBLE COMMENT '99th percentile latency',
    max_seconds DOUBLE COMMENT 'Maximum latency'
)
COMMENT 'LLM: Returns query latency percentiles by warehouse for SLA tracking.
Use for setting latency targets and monitoring performance.
Example: "What are our query latency percentiles?" or "Show me P99 latency by warehouse"'
RETURN
    SELECT
        q.compute_warehouse_id AS warehouse_id,
        w.warehouse_name,
        COUNT(*) AS query_count,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.5) AS p50_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.75) AS p75_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.90) AS p90_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.95) AS p95_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.99) AS p99_seconds,
        MAX(q.total_duration_ms / 1000.0) AS max_seconds
    FROM ${catalog}.${gold_schema}.fact_query_history q
    LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w
        ON q.compute_warehouse_id = w.warehouse_id AND w.is_current = TRUE
    WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND q.execution_status = 'FINISHED'
        AND q.compute_warehouse_id IS NOT NULL
    GROUP BY q.compute_warehouse_id, w.warehouse_name
    ORDER BY query_count DESC;


-- -----------------------------------------------------------------------------
-- TVF 8: get_failed_queries
-- Returns failed queries with error details
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_failed_queries(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
    top_n INT DEFAULT 100 COMMENT 'Number of queries to return'
)
RETURNS TABLE(
    statement_id STRING COMMENT 'Query statement ID',
    warehouse_id STRING COMMENT 'Warehouse ID',
    executed_by STRING COMMENT 'User',
    statement_type STRING COMMENT 'Query type',
    error_message STRING COMMENT 'Error message',
    start_time TIMESTAMP COMMENT 'Query start time',
    duration_before_failure_seconds DOUBLE COMMENT 'Time until failure'
)
COMMENT 'LLM: Returns failed queries with error details for troubleshooting.
Use for identifying common failure patterns and error root causes.
Example: "Show me failed queries" or "Why are queries failing?"'
RETURN
    WITH ranked_failures AS (
        SELECT
            statement_id,
            compute_warehouse_id AS warehouse_id,
            executed_by,
            statement_type,
            error_message,
            start_time,
            total_duration_ms / 1000.0 AS duration_before_failure_seconds,
            ROW_NUMBER() OVER (ORDER BY start_time DESC) AS rank
        FROM ${catalog}.${gold_schema}.fact_query_history
        WHERE DATE(start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND execution_status IN ('FAILED', 'CANCELED')
    )
    SELECT statement_id, warehouse_id, executed_by, statement_type,
           error_message, start_time, duration_before_failure_seconds
    FROM ranked_failures
    WHERE rank <= top_n
    ORDER BY start_time DESC;


-- =============================================================================
-- GITHUB REPOSITORY PATTERN TVFs (Added from Phase 3 Plan Enhancements)
-- =============================================================================
-- Source: phase3-addendum-3.2-tvfs.md - GitHub Repository Analysis

-- -----------------------------------------------------------------------------
-- TVF 9: get_query_efficiency_analysis
-- Analyzes query efficiency patterns by warehouse
-- Source: DBSQL Warehouse Advisor Repository
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_query_efficiency_analysis(
    hours_back INT DEFAULT 24 COMMENT 'Hours of history to analyze',
    warehouse_filter STRING DEFAULT 'ALL' COMMENT 'Warehouse ID or ALL'
)
RETURNS TABLE(
    warehouse_id STRING COMMENT 'SQL Warehouse ID',
    warehouse_name STRING COMMENT 'Warehouse name',
    total_queries BIGINT COMMENT 'Total queries executed',
    efficient_queries BIGINT COMMENT 'Queries without issues',
    high_spill_queries BIGINT COMMENT 'Queries with disk spill',
    high_queue_queries BIGINT COMMENT 'Queries with >10% queue time',
    slow_queries BIGINT COMMENT 'Queries > 5 minutes',
    efficiency_rate DOUBLE COMMENT 'Percent of efficient queries',
    avg_queue_ratio DOUBLE COMMENT 'Average queue/execution ratio',
    spill_rate DOUBLE COMMENT 'Percent of queries with spill',
    p95_duration_sec DOUBLE COMMENT 'P95 query duration in seconds',
    p99_duration_sec DOUBLE COMMENT 'P99 query duration in seconds',
    sizing_indicator STRING COMMENT 'SCALE_UP_NEEDED, OPTIMAL, or SCALE_DOWN_POSSIBLE'
)
COMMENT 'LLM: Analyzes query efficiency patterns by warehouse for optimization.
- PURPOSE: Warehouse optimization and scaling decisions
- BEST FOR: "Which warehouses need to scale up?" "Show me query efficiency by warehouse"
- PARAMS: hours_back (default 24), warehouse_filter (warehouse ID or ALL)
- RETURNS: Warehouse query metrics with scaling recommendations
Pattern source: DBSQL Warehouse Advisor Repository
Example: SELECT * FROM TABLE(get_query_efficiency_analysis(24, "ALL"))'
RETURN
    WITH query_metrics AS (
        SELECT
            qh.compute_warehouse_id AS warehouse_id,
            dw.warehouse_name,
            COUNT(*) AS total_queries,
            SUM(CASE
                WHEN (COALESCE(qh.spilled_local_bytes, 0) + COALESCE(qh.spilled_remote_bytes, 0)) = 0
                 AND qh.waiting_at_capacity_duration_ms <= qh.total_duration_ms * 0.1
                 AND qh.total_duration_ms <= 300000
                THEN 1 ELSE 0
            END) AS efficient_queries,
            SUM(CASE WHEN (COALESCE(qh.spilled_local_bytes, 0) + COALESCE(qh.spilled_remote_bytes, 0)) > 0 THEN 1 ELSE 0 END) AS high_spill_queries,
            SUM(CASE WHEN qh.waiting_at_capacity_duration_ms > qh.total_duration_ms * 0.1 THEN 1 ELSE 0 END) AS high_queue_queries,
            SUM(CASE WHEN qh.total_duration_ms > 300000 THEN 1 ELSE 0 END) AS slow_queries,
            AVG(qh.waiting_at_capacity_duration_ms * 100.0 / NULLIF(qh.total_duration_ms, 0)) AS avg_queue_ratio,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY qh.total_duration_ms) / 1000.0 AS p95_duration_sec,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY qh.total_duration_ms) / 1000.0 AS p99_duration_sec
        FROM ${catalog}.${gold_schema}.fact_query_history qh
        LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse dw
            ON qh.compute_warehouse_id = dw.warehouse_id AND dw.is_current = TRUE
        WHERE qh.start_time >= CURRENT_TIMESTAMP() - INTERVAL hours_back HOUR
            AND qh.total_duration_ms > 1000  -- Exclude trivial queries
            AND (warehouse_filter = 'ALL' OR qh.compute_warehouse_id = warehouse_filter)
            AND qh.compute_warehouse_id IS NOT NULL
        GROUP BY qh.compute_warehouse_id, dw.warehouse_name
    )
    SELECT
        warehouse_id,
        warehouse_name,
        total_queries,
        efficient_queries,
        high_spill_queries,
        high_queue_queries,
        slow_queries,
        ROUND(efficient_queries * 100.0 / NULLIF(total_queries, 0), 1) AS efficiency_rate,
        ROUND(avg_queue_ratio, 1) AS avg_queue_ratio,
        ROUND(high_spill_queries * 100.0 / NULLIF(total_queries, 0), 1) AS spill_rate,
        ROUND(p95_duration_sec, 2) AS p95_duration_sec,
        ROUND(p99_duration_sec, 2) AS p99_duration_sec,
        CASE
            WHEN high_queue_queries * 100.0 / NULLIF(total_queries, 0) > 20 THEN 'SCALE_UP_NEEDED'
            WHEN total_queries < 50 AND efficient_queries * 100.0 / NULLIF(total_queries, 0) > 95 THEN 'SCALE_DOWN_POSSIBLE'
            ELSE 'OPTIMAL'
        END AS sizing_indicator
    FROM query_metrics
    ORDER BY efficiency_rate ASC;


-- -----------------------------------------------------------------------------
-- TVF 10: get_job_outlier_runs
-- Identifies job runs that deviate significantly from P90 baseline
-- Source: Dashboard Pattern Analysis
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_job_outlier_runs(
    days_back INT DEFAULT 7 COMMENT 'Days of history to analyze',
    deviation_threshold DOUBLE DEFAULT 1.5 COMMENT 'Multiplier vs P90 to flag as outlier',
    min_baseline_runs INT DEFAULT 5 COMMENT 'Minimum runs to establish baseline'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_id STRING COMMENT 'Run ID',
    run_date DATE COMMENT 'Date of outlier run',
    duration_seconds DOUBLE COMMENT 'Actual duration in seconds',
    p90_duration_seconds DOUBLE COMMENT 'P90 baseline duration',
    deviation_ratio DOUBLE COMMENT 'Ratio vs P90 (>1 = slower)',
    outlier_type STRING COMMENT 'SLOW_OUTLIER or FAST_OUTLIER',
    run_cost DOUBLE COMMENT 'Estimated run cost'
)
COMMENT 'LLM: Identifies job runs that deviate significantly from normal patterns.
- PURPOSE: Detect anomalous job runs for investigation
- BEST FOR: "Which job runs were outliers?" "Show me slow job runs"
- PARAMS: days_back, deviation_threshold (default 1.5x P90), min_baseline_runs
- RETURNS: Job runs flagged as outliers with deviation metrics
Pattern source: Dashboard P90 outlier detection pattern
Example: SELECT * FROM TABLE(get_job_outlier_runs(7, 1.5, 5))'
RETURN
    WITH job_baselines AS (
        SELECT
            job_id,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY run_duration_seconds) AS p90_duration,
            COUNT(*) AS run_count
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline
        WHERE run_date >= CURRENT_DATE() - INTERVAL (days_back + 30) DAY  -- Extended window for baseline
            AND run_duration_seconds IS NOT NULL
            AND result_state = 'SUCCESS'
        GROUP BY job_id
        HAVING run_count >= min_baseline_runs
    ),
    recent_runs AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            jrt.run_id,
            jrt.run_date,
            jrt.run_duration_seconds,
            jrt.result_state
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        WHERE jrt.run_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND jrt.run_duration_seconds IS NOT NULL
    ),
    run_costs AS (
        SELECT
            usage_metadata_job_run_id AS run_id,
            SUM(list_cost) AS run_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND usage_metadata_job_run_id IS NOT NULL
        GROUP BY usage_metadata_job_run_id
    ),
    with_deviation AS (
        SELECT
            rr.job_id,
            rr.job_name,
            rr.run_id,
            rr.run_date,
            rr.run_duration_seconds AS duration_seconds,
            jb.p90_duration AS p90_duration_seconds,
            rr.run_duration_seconds / NULLIF(jb.p90_duration, 0) AS deviation_ratio,
            COALESCE(rc.run_cost, 0) AS run_cost
        FROM recent_runs rr
        JOIN job_baselines jb ON rr.job_id = jb.job_id
        LEFT JOIN run_costs rc ON rr.run_id = rc.run_id
    )
    SELECT
        job_id,
        job_name,
        run_id,
        run_date,
        ROUND(duration_seconds, 2) AS duration_seconds,
        ROUND(p90_duration_seconds, 2) AS p90_duration_seconds,
        ROUND(deviation_ratio, 2) AS deviation_ratio,
        CASE
            WHEN deviation_ratio > deviation_threshold THEN 'SLOW_OUTLIER'
            WHEN deviation_ratio < 1.0 / deviation_threshold THEN 'FAST_OUTLIER'
        END AS outlier_type,
        ROUND(run_cost, 2) AS run_cost
    FROM with_deviation
    WHERE deviation_ratio > deviation_threshold OR deviation_ratio < 1.0 / deviation_threshold
    ORDER BY deviation_ratio DESC;
