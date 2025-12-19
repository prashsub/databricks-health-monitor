-- =============================================================================
-- COMPUTE AGENT TVFs - PERFORMANCE DOMAIN
-- =============================================================================
-- Table-Valued Functions for cluster utilization and optimization
--
-- Domain: Performance / Compute
-- All TVFs query Gold layer tables (fact_node_timeline, dim_cluster, fact_usage)
-- Parameters use STRING type for dates (Genie compatibility)
-- Reference: Microsoft Learn - Compute Sample Queries
-- =============================================================================

-- Variables are substituted at deployment time
-- ${catalog} = Unity Catalog name
-- ${gold_schema} = Gold schema name (e.g., system_gold)

-- -----------------------------------------------------------------------------
-- TVF 1: get_cluster_utilization
-- Returns cluster utilization metrics for optimization
-- -----------------------------------------------------------------------------
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
- PURPOSE: Identify underutilized clusters and cost optimization
- BEST FOR: "Show cluster utilization" "Which clusters are underutilized?"
- PARAMS: start_date, end_date, min_hours
- RETURNS: Clusters with CPU/memory utilization and cost
Example: SELECT * FROM TABLE(get_cluster_utilization("2024-01-01", "2024-12-31", 5))'
RETURN
    WITH cluster_metrics AS (
        SELECT
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            SUM(TIMESTAMPDIFF(MINUTE, nt.start_time, nt.end_time)) / 60.0 AS total_hours,
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
        SELECT usage_metadata_cluster_id AS cluster_id, SUM(list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_metadata_cluster_id IS NOT NULL
            AND usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY usage_metadata_cluster_id
    )
    SELECT
        cm.cluster_id,
        cm.cluster_name,
        cm.cluster_type,
        cm.owned_by,
        ROUND(cm.total_hours, 2) AS total_hours,
        ROUND(cm.avg_cpu_utilization, 2) AS avg_cpu_utilization,
        ROUND(cm.avg_memory_utilization, 2) AS avg_memory_utilization,
        ROUND(cm.peak_cpu, 2) AS peak_cpu,
        ROUND(cm.peak_memory, 2) AS peak_memory,
        ROUND(COALESCE(cc.total_cost, 0), 2) AS total_cost
    FROM cluster_metrics cm
    LEFT JOIN cluster_cost cc ON cm.cluster_id = cc.cluster_id
    WHERE cm.total_hours >= min_hours
    ORDER BY total_cost DESC;


-- -----------------------------------------------------------------------------
-- TVF 2: get_cluster_resource_metrics
-- Returns detailed cluster resource utilization metrics
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cluster_resource_metrics(
    days_back INT DEFAULT 1 COMMENT 'Number of days to analyze',
    top_n INT DEFAULT 50 COMMENT 'Number of clusters to return'
)
RETURNS TABLE(
    cluster_id STRING COMMENT 'Cluster identifier',
    cluster_name STRING COMMENT 'Cluster name',
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
- PURPOSE: Right-sizing clusters, identifying bottlenecks, capacity planning
- BEST FOR: "Show cluster CPU and memory utilization" "Which clusters have high CPU wait?"
- PARAMS: days_back, top_n
- RETURNS: Detailed resource metrics per cluster/node
Example: SELECT * FROM TABLE(get_cluster_resource_metrics(7, 25))'
RETURN
    WITH ranked AS (
        SELECT
            nt.cluster_id,
            c.cluster_name,
            nt.driver AS is_driver,
            AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_utilization,
            MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS peak_cpu_utilization,
            AVG(nt.cpu_wait_percent) AS avg_cpu_wait,
            MAX(nt.cpu_wait_percent) AS max_cpu_wait,
            AVG(nt.mem_used_percent) AS avg_memory_utilization,
            MAX(nt.mem_used_percent) AS max_memory_utilization,
            AVG(nt.network_received_bytes) / (1024 * 1024) AS avg_network_mb_received,
            AVG(nt.network_sent_bytes) / (1024 * 1024) AS avg_network_mb_sent,
            ROW_NUMBER() OVER (ORDER BY AVG(nt.cpu_user_percent + nt.cpu_system_percent) DESC) AS rank
        FROM ${catalog}.${gold_schema}.fact_node_timeline nt
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
        WHERE nt.start_time >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY nt.cluster_id, c.cluster_name, nt.driver
    )
    SELECT cluster_id, cluster_name, is_driver,
           ROUND(avg_cpu_utilization, 2) AS avg_cpu_utilization,
           ROUND(peak_cpu_utilization, 2) AS peak_cpu_utilization,
           ROUND(avg_cpu_wait, 2) AS avg_cpu_wait,
           ROUND(max_cpu_wait, 2) AS max_cpu_wait,
           ROUND(avg_memory_utilization, 2) AS avg_memory_utilization,
           ROUND(max_memory_utilization, 2) AS max_memory_utilization,
           ROUND(avg_network_mb_received, 2) AS avg_network_mb_received,
           ROUND(avg_network_mb_sent, 2) AS avg_network_mb_sent
    FROM ranked
    WHERE rank <= top_n
    ORDER BY avg_cpu_utilization DESC;


-- -----------------------------------------------------------------------------
-- TVF 3: get_underutilized_clusters
-- Returns underutilized clusters with cost savings potential
-- -----------------------------------------------------------------------------
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
    potential_savings DOUBLE COMMENT 'Potential cost savings if right-sized',
    recommendation STRING COMMENT 'Right-sizing recommendation'
)
COMMENT 'LLM: Returns underutilized clusters with cost savings potential.
- PURPOSE: Cost optimization and right-sizing recommendations
- BEST FOR: "Which clusters are underutilized?" "Show potential cost savings"
- PARAMS: days_back, cpu_threshold (default 30%), min_hours
- RETURNS: Underutilized clusters with savings estimate
Example: SELECT * FROM TABLE(get_underutilized_clusters(7, 30, 10))'
RETURN
    WITH cluster_metrics AS (
        SELECT
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            ROUND(AVG(nt.cpu_user_percent + nt.cpu_system_percent), 1) AS avg_cpu_pct,
            ROUND(AVG(nt.mem_used_percent), 1) AS avg_mem_pct,
            SUM(TIMESTAMPDIFF(MINUTE, nt.start_time, nt.end_time)) / 60.0 AS total_hours
        FROM ${catalog}.${gold_schema}.fact_node_timeline nt
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
        WHERE nt.start_time >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
        HAVING total_hours >= min_hours
    ),
    cluster_cost AS (
        SELECT usage_metadata_cluster_id AS cluster_id, SUM(list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND usage_metadata_cluster_id IS NOT NULL
        GROUP BY usage_metadata_cluster_id
    )
    SELECT
        cm.cluster_id,
        cm.cluster_name,
        cm.cluster_type,
        cm.owned_by,
        cm.avg_cpu_pct,
        cm.avg_mem_pct,
        ROUND(cm.total_hours, 2) AS total_hours,
        ROUND(COALESCE(cc.total_cost, 0), 2) AS total_cost,
        ROUND(CASE
            WHEN cm.avg_cpu_pct < 15 THEN cc.total_cost * 0.6
            WHEN cm.avg_cpu_pct < 20 THEN cc.total_cost * 0.5
            WHEN cm.avg_cpu_pct < 30 THEN cc.total_cost * 0.3
            ELSE 0
        END, 2) AS potential_savings,
        CASE
            WHEN cm.avg_cpu_pct < 15 THEN 'Consider downsizing by 50%+ or using serverless'
            WHEN cm.avg_cpu_pct < 20 THEN 'Consider downsizing by 40% or enabling autoscaling'
            WHEN cm.avg_cpu_pct < 30 THEN 'Consider enabling autoscaling or slight downsize'
            ELSE 'Utilization acceptable'
        END AS recommendation
    FROM cluster_metrics cm
    LEFT JOIN cluster_cost cc ON cm.cluster_id = cc.cluster_id
    WHERE cm.avg_cpu_pct < cpu_threshold
    ORDER BY potential_savings DESC;


-- -----------------------------------------------------------------------------
-- TVF 4: get_jobs_without_autoscaling
-- Returns job clusters that could benefit from autoscaling
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_jobs_without_autoscaling(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze',
    min_runs INT DEFAULT 5 COMMENT 'Minimum runs to include job',
    min_cost DOUBLE DEFAULT 100 COMMENT 'Minimum cost to include job'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_as STRING COMMENT 'Job owner',
    total_runs INT COMMENT 'Total runs in period',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    avg_cpu_pct DOUBLE COMMENT 'Average CPU utilization',
    max_cpu_pct DOUBLE COMMENT 'Maximum CPU utilization',
    cpu_variance DOUBLE COMMENT 'CPU utilization variance (high = autoscaling candidate)',
    recommendation STRING COMMENT 'Autoscaling recommendation'
)
COMMENT 'LLM: Identifies job clusters that could benefit from autoscaling.
- PURPOSE: Cost optimization through autoscaling recommendations
- BEST FOR: "Which jobs should enable autoscaling?" "Show autoscaling opportunities"
- PARAMS: days_back, min_runs, min_cost
- RETURNS: Jobs with autoscaling recommendations
Example: SELECT * FROM TABLE(get_jobs_without_autoscaling(30, 5, 500))'
RETURN
    WITH job_cluster_metrics AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            j.run_as,
            COUNT(DISTINCT jrt.run_id) AS total_runs,
            AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_pct,
            MAX(nt.cpu_user_percent + nt.cpu_system_percent) AS max_cpu_pct,
            STDDEV(nt.cpu_user_percent + nt.cpu_system_percent) AS cpu_std
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        LEFT JOIN ${catalog}.${gold_schema}.fact_node_timeline nt
            ON jrt.cluster_id = nt.cluster_id
            AND nt.start_time BETWEEN jrt.period_start_time AND jrt.period_end_time
        WHERE jrt.run_date >= CURRENT_DATE() - INTERVAL days_back DAY
        GROUP BY jrt.job_id, j.name, j.run_as
        HAVING COUNT(DISTINCT jrt.run_id) >= min_runs
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            SUM(list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id
    )
    SELECT
        jcm.job_id,
        jcm.job_name,
        jcm.run_as,
        jcm.total_runs,
        ROUND(COALESCE(jc.total_cost, 0), 2) AS total_cost,
        ROUND(jcm.avg_cpu_pct, 2) AS avg_cpu_pct,
        ROUND(jcm.max_cpu_pct, 2) AS max_cpu_pct,
        ROUND(jcm.cpu_std, 2) AS cpu_variance,
        CASE
            WHEN jcm.cpu_std > 20 AND jcm.avg_cpu_pct < 50 THEN 'High variance, low avg - strong autoscaling candidate'
            WHEN jcm.avg_cpu_pct < 30 THEN 'Low utilization - consider smaller cluster or autoscaling'
            WHEN jcm.cpu_std > 15 THEN 'Variable workload - autoscaling recommended'
            ELSE 'Evaluate for autoscaling benefits'
        END AS recommendation
    FROM job_cluster_metrics jcm
    LEFT JOIN job_costs jc ON jcm.job_id = jc.job_id
    WHERE COALESCE(jc.total_cost, 0) >= min_cost
    ORDER BY jc.total_cost DESC;


-- -----------------------------------------------------------------------------
-- TVF 5: get_jobs_on_legacy_dbr
-- Returns jobs running on legacy Databricks Runtime versions
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_jobs_on_legacy_dbr(
    days_back INT DEFAULT 30 COMMENT 'Number of days to analyze',
    legacy_threshold INT DEFAULT 13 COMMENT 'DBR major version below which is considered legacy'
)
RETURNS TABLE(
    job_id STRING COMMENT 'Job ID',
    job_name STRING COMMENT 'Job name',
    run_as STRING COMMENT 'Job owner',
    dbr_version STRING COMMENT 'Databricks Runtime version',
    dbr_major INT COMMENT 'DBR major version number',
    total_runs INT COMMENT 'Total runs in period',
    total_cost DOUBLE COMMENT 'Total cost in USD',
    recommendation STRING COMMENT 'Upgrade recommendation'
)
COMMENT 'LLM: Returns jobs running on legacy Databricks Runtime versions.
- PURPOSE: Identify migration candidates for DBR upgrades
- BEST FOR: "Which jobs use old DBR?" "Show legacy runtime jobs"
- PARAMS: days_back, legacy_threshold (DBR major version)
- RETURNS: Jobs with legacy DBR and upgrade recommendations
Example: SELECT * FROM TABLE(get_jobs_on_legacy_dbr(30, 13))'
RETURN
    WITH job_dbr AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            j.run_as,
            c.dbr_version,
            CAST(SPLIT(c.dbr_version, '\\.')[0] AS INT) AS dbr_major,
            COUNT(DISTINCT jrt.run_id) AS total_runs
        FROM ${catalog}.${gold_schema}.fact_job_run_timeline jrt
        LEFT JOIN ${catalog}.${gold_schema}.dim_job j
            ON jrt.job_id = j.job_id AND j.is_current = TRUE
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c
            ON jrt.cluster_id = c.cluster_id AND c.is_current = TRUE
        WHERE jrt.run_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND c.dbr_version IS NOT NULL
        GROUP BY jrt.job_id, j.name, j.run_as, c.dbr_version
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            SUM(list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id
    )
    SELECT
        jd.job_id,
        jd.job_name,
        jd.run_as,
        jd.dbr_version,
        jd.dbr_major,
        jd.total_runs,
        ROUND(COALESCE(jc.total_cost, 0), 2) AS total_cost,
        CASE
            WHEN jd.dbr_major < 10 THEN 'URGENT: Upgrade to latest LTS immediately'
            WHEN jd.dbr_major < 12 THEN 'Recommended: Upgrade to DBR 14 LTS'
            WHEN jd.dbr_major < 14 THEN 'Consider: Upgrade to latest LTS for best performance'
            ELSE 'On supported version'
        END AS recommendation
    FROM job_dbr jd
    LEFT JOIN job_costs jc ON jd.job_id = jc.job_id
    WHERE jd.dbr_major < legacy_threshold
    ORDER BY jd.dbr_major ASC, jc.total_cost DESC;


-- =============================================================================
-- GITHUB REPOSITORY PATTERN TVFs (Added from Phase 3 Plan Enhancements)
-- =============================================================================
-- Source: phase3-addendum-3.2-tvfs.md - GitHub Repository Analysis

-- -----------------------------------------------------------------------------
-- TVF 6: get_cluster_right_sizing_recommendations
-- Comprehensive cluster sizing analysis with recommendations
-- Source: Workflow Advisor Repository
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_cluster_right_sizing_recommendations(
    days_back INT DEFAULT 7 COMMENT 'Days of history to analyze',
    min_observation_hours INT DEFAULT 10 COMMENT 'Minimum hours of data required'
)
RETURNS TABLE(
    cluster_id STRING COMMENT 'Cluster ID',
    cluster_name STRING COMMENT 'Cluster name',
    cluster_type STRING COMMENT 'Cluster type (JOB/ALL_PURPOSE)',
    owned_by STRING COMMENT 'Cluster owner',
    observation_hours DOUBLE COMMENT 'Hours of observation data',
    avg_cpu_util DOUBLE COMMENT 'Average CPU utilization percentage',
    p95_cpu_util DOUBLE COMMENT '95th percentile CPU utilization',
    avg_memory_util DOUBLE COMMENT 'Average memory utilization percentage',
    p95_memory_util DOUBLE COMMENT '95th percentile memory utilization',
    cpu_saturation_pct DOUBLE COMMENT 'Percent of time CPU > 90%',
    cpu_idle_pct DOUBLE COMMENT 'Percent of time CPU < 20%',
    total_cost DOUBLE COMMENT 'Total cost in period',
    sizing_status STRING COMMENT 'UNDERPROVISIONED, OVERPROVISIONED, UNDERUTILIZED, or OPTIMAL',
    savings_opportunity STRING COMMENT 'HIGH, MEDIUM, LOW, or NONE',
    potential_savings DOUBLE COMMENT 'Estimated potential savings in USD',
    recommendation STRING COMMENT 'Action recommendation'
)
COMMENT 'LLM: Analyzes cluster utilization to provide right-sizing recommendations.
- PURPOSE: Cost optimization through cluster right-sizing
- BEST FOR: "Which clusters are overprovisioned?" "Show me clusters with cost savings opportunities"
- PARAMS: days_back (default 7), min_observation_hours (default 10)
- RETURNS: Clusters with sizing status, savings opportunity, and specific recommendations
Pattern source: Workflow Advisor Repository
Example: SELECT * FROM TABLE(get_cluster_right_sizing_recommendations(7, 10))'
RETURN
    WITH cluster_metrics AS (
        SELECT
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            COUNT(*) / 60.0 AS observation_hours,
            AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_util,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY nt.cpu_user_percent + nt.cpu_system_percent) AS p95_cpu_util,
            AVG(nt.mem_used_percent) AS avg_memory_util,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY nt.mem_used_percent) AS p95_memory_util,
            SUM(CASE WHEN nt.cpu_user_percent + nt.cpu_system_percent > 90 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS cpu_saturation_pct,
            SUM(CASE WHEN nt.cpu_user_percent + nt.cpu_system_percent < 20 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS cpu_idle_pct
        FROM ${catalog}.${gold_schema}.fact_node_timeline nt
        LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.is_current = TRUE
        WHERE nt.start_time >= CURRENT_TIMESTAMP() - INTERVAL days_back DAY
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
        HAVING observation_hours >= min_observation_hours
    ),
    cluster_costs AS (
        SELECT
            usage_metadata_cluster_id AS cluster_id,
            SUM(list_cost) AS total_cost
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE() - INTERVAL days_back DAY
            AND usage_metadata_cluster_id IS NOT NULL
        GROUP BY usage_metadata_cluster_id
    ),
    with_sizing AS (
        SELECT
            cm.*,
            COALESCE(cc.total_cost, 0) AS total_cost,
            -- Sizing status
            CASE
                WHEN cm.cpu_saturation_pct > 20 OR cm.p95_memory_util > 85 THEN 'UNDERPROVISIONED'
                WHEN cm.cpu_idle_pct > 70 AND cm.avg_memory_util < 30 THEN 'OVERPROVISIONED'
                WHEN cm.cpu_idle_pct > 50 AND cm.avg_memory_util < 50 THEN 'UNDERUTILIZED'
                ELSE 'OPTIMAL'
            END AS sizing_status,
            -- Savings opportunity
            CASE
                WHEN cm.cpu_idle_pct > 70 THEN 'HIGH'
                WHEN cm.cpu_idle_pct > 50 THEN 'MEDIUM'
                WHEN cm.cpu_idle_pct > 30 THEN 'LOW'
                ELSE 'NONE'
            END AS savings_opportunity,
            -- Potential savings calculation
            CASE
                WHEN cm.cpu_idle_pct > 70 THEN COALESCE(cc.total_cost, 0) * 0.5
                WHEN cm.cpu_idle_pct > 50 THEN COALESCE(cc.total_cost, 0) * 0.3
                WHEN cm.cpu_idle_pct > 30 THEN COALESCE(cc.total_cost, 0) * 0.15
                ELSE 0
            END AS potential_savings
        FROM cluster_metrics cm
        LEFT JOIN cluster_costs cc ON cm.cluster_id = cc.cluster_id
    )
    SELECT
        cluster_id,
        cluster_name,
        cluster_type,
        owned_by,
        ROUND(observation_hours, 1) AS observation_hours,
        ROUND(avg_cpu_util, 1) AS avg_cpu_util,
        ROUND(p95_cpu_util, 1) AS p95_cpu_util,
        ROUND(avg_memory_util, 1) AS avg_memory_util,
        ROUND(p95_memory_util, 1) AS p95_memory_util,
        ROUND(cpu_saturation_pct, 1) AS cpu_saturation_pct,
        ROUND(cpu_idle_pct, 1) AS cpu_idle_pct,
        ROUND(total_cost, 2) AS total_cost,
        sizing_status,
        savings_opportunity,
        ROUND(potential_savings, 2) AS potential_savings,
        CASE sizing_status
            WHEN 'UNDERPROVISIONED' THEN 'Consider increasing cluster size or adding workers'
            WHEN 'OVERPROVISIONED' THEN 'Significant underutilization - consider downsizing by 50%'
            WHEN 'UNDERUTILIZED' THEN 'Moderate underutilization - review cluster sizing or enable autoscaling'
            ELSE 'Cluster is appropriately sized'
        END AS recommendation
    FROM with_sizing
    ORDER BY
        CASE sizing_status
            WHEN 'OVERPROVISIONED' THEN 1
            WHEN 'UNDERPROVISIONED' THEN 2
            WHEN 'UNDERUTILIZED' THEN 3
            ELSE 4
        END,
        potential_savings DESC;
