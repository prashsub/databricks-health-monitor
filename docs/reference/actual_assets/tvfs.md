routine_catalog	routine_schema	routine_name	routine_type	return_type	routine_definition
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_all_purpose_cluster_cost	FUNCTION	TABLE_TYPE	"WITH all_purpose_usage AS (
        SELECT
            usage_metadata_cluster_id AS cluster_id,
            SUM(list_cost) AS total_cost,
            SUM(usage_quantity) AS total_dbu
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND (sku_name LIKE '%ALL_PURPOSE%' OR sku_name LIKE '%INTERACTIVE%')
            AND usage_metadata_cluster_id IS NOT NULL
        GROUP BY usage_metadata_cluster_id
    ),
    cluster_hours AS (
        SELECT
            cluster_id,
            SUM(TIMESTAMPDIFF(MINUTE, start_time, end_time)) / 60.0 AS total_hours
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_node_timeline
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
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cluster_resource_metrics	FUNCTION	TABLE_TYPE	"WITH ranked AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_node_timeline nt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.delete_time IS NULL
        WHERE nt.start_time >= DATE_ADD(CURRENT_DATE(), -days_back)
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
    ORDER BY avg_cpu_utilization DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cluster_right_sizing_recommendations	FUNCTION	TABLE_TYPE	"WITH cluster_metrics AS (
        SELECT
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            COUNT(*) / 60.0 AS observation_hours,
            AVG(nt.cpu_user_percent + nt.cpu_system_percent) AS avg_cpu_util,
            PERCENTILE_APPROX(nt.cpu_user_percent + nt.cpu_system_percent, 0.95) AS p95_cpu_util,
            AVG(nt.mem_used_percent) AS avg_memory_util,
            PERCENTILE_APPROX(nt.mem_used_percent, 0.95) AS p95_memory_util,
            SUM(CASE WHEN nt.cpu_user_percent + nt.cpu_system_percent > 90 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS cpu_saturation_pct,
            SUM(CASE WHEN nt.cpu_user_percent + nt.cpu_system_percent < 20 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS cpu_idle_pct
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_node_timeline nt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.delete_time IS NULL
        WHERE nt.start_time >= TIMESTAMPADD(DAY, -days_back, CURRENT_TIMESTAMP())
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
        HAVING observation_hours >= min_observation_hours
    ),
    cluster_costs AS (
        SELECT
            usage_metadata_cluster_id AS cluster_id,
            SUM(list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND usage_metadata_cluster_id IS NOT NULL
        GROUP BY usage_metadata_cluster_id
    ),
    with_sizing AS (
        SELECT
            cm.*,
            COALESCE(cc.total_cost, 0) AS total_cost,
            CASE
                WHEN cm.cpu_saturation_pct > 20 OR cm.p95_memory_util > 85 THEN 'UNDERPROVISIONED'
                WHEN cm.cpu_idle_pct > 70 AND cm.avg_memory_util < 30 THEN 'OVERPROVISIONED'
                WHEN cm.cpu_idle_pct > 50 AND cm.avg_memory_util < 50 THEN 'UNDERUTILIZED'
                ELSE 'OPTIMAL'
            END AS sizing_status,
            CASE
                WHEN cm.cpu_idle_pct > 70 THEN 'HIGH'
                WHEN cm.cpu_idle_pct > 50 THEN 'MEDIUM'
                WHEN cm.cpu_idle_pct > 30 THEN 'LOW'
                ELSE 'NONE'
            END AS savings_opportunity,
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
        potential_savings DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cluster_utilization	FUNCTION	TABLE_TYPE	"WITH cluster_metrics AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_node_timeline nt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.delete_time IS NULL
        WHERE CAST(nt.start_time AS DATE) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
    ),
    cluster_cost AS (
        SELECT usage_metadata_cluster_id AS cluster_id, SUM(list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    ORDER BY total_cost DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_commit_vs_actual	FUNCTION	TABLE_TYPE	"WITH monthly_spend AS (
        SELECT
            MONTH(usage_date) AS month_num,
            DATE_FORMAT(usage_date, 'MMMM') AS month_name,
            SUM(list_cost) AS monthly_spend
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    ORDER BY month_num"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_anomalies	FUNCTION	TABLE_TYPE	"WITH daily_costs AS (
        SELECT
            usage_date,
            workspace_id,
            SUM(list_cost) AS daily_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    ORDER BY ABS(z_score) DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_by_owner	FUNCTION	TABLE_TYPE	"WITH owner_costs AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_by_tag	FUNCTION	TABLE_TYPE	"WITH tag_costs AS (
        SELECT
            COALESCE(custom_tags[tag_key], 'UNTAGGED') AS tag_value,
            SUM(list_cost) AS total_cost,
            SUM(usage_quantity) AS total_dbu,
            COUNT(DISTINCT COALESCE(usage_metadata_job_id, usage_metadata_cluster_id, usage_metadata_warehouse_id)) AS resource_count
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    ORDER BY total_cost DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_forecast_summary	FUNCTION	TABLE_TYPE	"WITH monthly_history AS (
        SELECT
            DATE_TRUNC('MONTH', usage_date) AS month_start,
            SUM(list_cost) AS monthly_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    CROSS JOIN (SELECT explode(sequence(1, forecast_months)) AS n)"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_growth_analysis	FUNCTION	TABLE_TYPE	"WITH aggregated AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
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
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_workspace w
            ON entity_type = 'WORKSPACE' AND a.entity_id = w.workspace_id
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_growth_by_period	FUNCTION	TABLE_TYPE	"WITH base_data AS (
        SELECT
            CASE entity_type
                WHEN 'WORKSPACE' THEN fu.workspace_id
                WHEN 'JOB' THEN fu.usage_metadata_job_id
                WHEN 'SKU' THEN fu.sku_name
            END AS entity_id,
            COALESCE(w.workspace_name, j.name,
                CASE entity_type
                    WHEN 'WORKSPACE' THEN fu.workspace_id
                    WHEN 'JOB' THEN fu.usage_metadata_job_id
                    WHEN 'SKU' THEN fu.sku_name
                END) AS entity_name,
            SUM(CASE WHEN fu.usage_date >= CURRENT_DATE() - INTERVAL 7 DAY THEN fu.list_cost ELSE 0 END) AS recent_spend,
            SUM(CASE WHEN fu.usage_date >= CURRENT_DATE() - INTERVAL 14 DAY
                          AND fu.usage_date < CURRENT_DATE() - INTERVAL 7 DAY
                     THEN fu.list_cost ELSE 0 END) AS prior_spend
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage fu
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_workspace w ON fu.workspace_id = w.workspace_id
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j ON fu.usage_metadata_job_id = j.job_id AND j.delete_time IS NULL
        WHERE fu.usage_date >= CURRENT_DATE() - INTERVAL 14 DAY
        GROUP BY 1, 2
        HAVING entity_id IS NOT NULL
    ),
    ranked AS (
        SELECT
            CAST(ROW_NUMBER() OVER (ORDER BY (recent_spend - prior_spend) DESC) AS INT) AS rank,
            entity_id,
            entity_name,
            ROUND(recent_spend, 2) AS recent_7d_spend,
            ROUND(prior_spend, 2) AS prior_7d_spend,
            ROUND(recent_spend - prior_spend, 2) AS absolute_change,
            ROUND((recent_spend - prior_spend) / NULLIF(prior_spend, 0) * 100, 2) AS pct_change,
            CASE
                WHEN (recent_spend - prior_spend) / NULLIF(prior_spend, 0) * 100 > 50 THEN 'SPIKE'
                WHEN (recent_spend - prior_spend) / NULLIF(prior_spend, 0) * 100 > 10 THEN 'GROWTH'
                WHEN (recent_spend - prior_spend) / NULLIF(prior_spend, 0) * 100 BETWEEN -10 AND 10 THEN 'STABLE'
                WHEN (recent_spend - prior_spend) / NULLIF(prior_spend, 0) * 100 > -50 THEN 'DECLINE'
                ELSE 'DROP'
            END AS change_category
        FROM base_data
    )
    SELECT * FROM ranked
    WHERE rank <= top_n
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_mtd_summary	FUNCTION	TABLE_TYPE	"WITH current_month AS (
        SELECT
            SUM(list_cost) AS mtd_cost,
            SUM(usage_quantity) AS mtd_dbu,
            COUNT(DISTINCT usage_date) AS days_elapsed,
            DAY(LAST_DAY(CURRENT_DATE())) AS days_in_month
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
            AND usage_date <= CURRENT_DATE()
    ),
    prior_month AS (
        SELECT
            SUM(list_cost) AS prior_mtd_cost,
            SUM(usage_quantity) AS prior_mtd_dbu
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    FROM current_month c, prior_month p"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_trend_by_sku	FUNCTION	TABLE_TYPE	"WITH daily_costs AS (
        SELECT
            usage_date,
            sku_name,
            SUM(usage_quantity) AS daily_dbu,
            SUM(list_cost) AS daily_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    ORDER BY usage_date, sku_name"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_cost_week_over_week	FUNCTION	TABLE_TYPE	"WITH weekly_costs AS (
        SELECT
            DATE_TRUNC('WEEK', usage_date) AS week_start,
            SUM(list_cost) AS weekly_cost,
            SUM(usage_quantity) AS weekly_dbu
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -weeks_back * 7)
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
    ORDER BY week_start"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_data_freshness_by_domain	FUNCTION	TABLE_TYPE	"SELECT
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
    FROM prashanth_subrahmanyam_catalog.information_schema.tables
    WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
        AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
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
    ORDER BY max_hours_since_update DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_data_quality_summary	FUNCTION	TABLE_TYPE	"SELECT
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
    FROM prashanth_subrahmanyam_catalog.information_schema.tables
    WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
        AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
        AND table_type = 'MANAGED'

    UNION ALL
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
    FROM prashanth_subrahmanyam_catalog.information_schema.tables
    WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
        AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
        AND table_type = 'MANAGED'

    UNION ALL
    SELECT
        'CONSISTENCY' AS quality_dimension,
        'Schema Coverage' AS metric_name,
        CASE WHEN EXISTS (
            SELECT 1 FROM prashanth_subrahmanyam_catalog.information_schema.tables
            WHERE table_schema = 'dev_prashanth_subrahmanyam_system_gold' AND table_name LIKE 'fact_usage%'
        ) THEN 100.0 ELSE 0.0 END AS metric_value,
        100.0 AS target_value,
        CASE WHEN EXISTS (
            SELECT 1 FROM prashanth_subrahmanyam_catalog.information_schema.tables
            WHERE table_schema = 'dev_prashanth_subrahmanyam_system_gold' AND table_name LIKE 'fact_usage%'
        ) THEN 'PASS' ELSE 'FAIL' END AS status,
        'Core billing fact table exists' AS details

    UNION ALL

    SELECT
        'CONSISTENCY' AS quality_dimension,
        'Dimension Tables' AS metric_name,
        (SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.information_schema.tables
         WHERE table_schema = 'dev_prashanth_subrahmanyam_system_gold' AND table_name LIKE 'dim_%') * 10.0 AS metric_value,
        50.0 AS target_value,
        CASE WHEN (SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.information_schema.tables
                   WHERE table_schema = 'dev_prashanth_subrahmanyam_system_gold' AND table_name LIKE 'dim_%') >= 5 THEN 'PASS'
             ELSE 'WARNING' END AS status,
        CONCAT((SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.information_schema.tables
                WHERE table_schema = 'dev_prashanth_subrahmanyam_system_gold' AND table_name LIKE 'dim_%'), ' dimension tables') AS details

    ORDER BY quality_dimension, metric_name"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_failed_actions	FUNCTION	TABLE_TYPE	"SELECT
        event_time,
        user_identity_email AS user_email,
        service_name AS service,
        action_name AS action,
        response_status_code AS status_code,
        response_error_message AS error_message,
        source_ip_address AS source_ip
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND is_failed_action = TRUE
        AND (user_filter = 'ALL' OR user_identity_email = user_filter)
    ORDER BY event_time DESC
    LIMIT 500"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_failed_jobs	FUNCTION	TABLE_TYPE	"SELECT
        jrt.workspace_id,
        jrt.job_id,
        j.name AS job_name,
        jrt.run_id,
        jrt.result_state,
        jrt.termination_code,
        j.run_as,
        jrt.period_start_time AS start_time,
        jrt.period_end_time AS end_time,
        jrt.run_duration_minutes AS duration_minutes
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
        ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
    WHERE jrt.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT', 'CANCELED')
        AND jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (workspace_filter = 'ALL' OR jrt.workspace_id = workspace_filter)
    ORDER BY jrt.period_start_time DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_failed_queries	FUNCTION	TABLE_TYPE	"WITH ranked_failures AS (
        SELECT
            statement_id,
            compute_warehouse_id AS warehouse_id,
            executed_by,
            statement_type,
            error_message,
            start_time,
            total_duration_ms / 1000.0 AS duration_before_failure_seconds,
            ROW_NUMBER() OVER (ORDER BY start_time DESC) AS rank
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history
        WHERE DATE(start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND execution_status IN ('FAILED', 'CANCELED')
    )
    SELECT statement_id, warehouse_id, executed_by, statement_type,
           error_message, start_time, duration_before_failure_seconds
    FROM ranked_failures
    WHERE rank <= top_n
    ORDER BY start_time DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_high_spill_queries	FUNCTION	TABLE_TYPE	"SELECT
        statement_id,
        compute_warehouse_id AS warehouse_id,
        executed_by,
        statement_type,
        total_duration_ms / 1000.0 AS duration_seconds,
        COALESCE(spilled_local_bytes, 0) / 1073741824.0 AS local_spill_gb,
        0.0 AS remote_spill_gb,
        COALESCE(spilled_local_bytes, 0) / 1073741824.0 AS total_spill_gb,
        read_bytes / 1073741824.0 AS read_gb,
        COALESCE(spilled_local_bytes, 0) / NULLIF(read_bytes, 0) AS spill_ratio
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history
    WHERE DATE(start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND COALESCE(spilled_local_bytes, 0) >= min_spill_gb * 1073741824
    ORDER BY total_spill_gb DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_ip_address_analysis	FUNCTION	TABLE_TYPE	"SELECT
        source_ip_address AS source_ip,
        COUNT(DISTINCT user_identity_email) AS unique_users,
        CONCAT_WS(', ', COLLECT_SET(user_identity_email)) AS user_list,
        COUNT(*) AS event_count,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
        CONCAT_WS(', ', COLLECT_SET(service_name)) AS services_accessed,
        MIN(event_time) AS first_seen,
        MAX(event_time) AS last_seen,
        COUNT(DISTINCT user_identity_email) > 1 AS is_shared_ip
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND source_ip_address IS NOT NULL
    GROUP BY source_ip_address
    ORDER BY unique_users DESC, event_count DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_data_quality_status	FUNCTION	TABLE_TYPE	"WITH job_stats AS (
        SELECT
            j.name AS job_name,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN jrt.is_success THEN 1 ELSE 0 END) AS successful_runs,
            SUM(CASE WHEN NOT jrt.is_success THEN 1 ELSE 0 END) AS failed_runs,
            MAX(CASE WHEN jrt.is_success THEN jrt.period_end_time END) AS last_success
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
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
    ORDER BY success_rate_pct ASC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_duration_percentiles	FUNCTION	TABLE_TYPE	"SELECT
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
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
        ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
    WHERE jrt.is_success = TRUE
        AND jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
        AND (job_name_filter = 'ALL' OR j.name LIKE CONCAT('%', job_name_filter, '%'))
    GROUP BY jrt.job_id, j.name
    HAVING COUNT(*) >= 5
    ORDER BY avg_duration_min DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_failure_costs	FUNCTION	TABLE_TYPE	"WITH job_runs AS (
        SELECT
            jrt.workspace_id,
            jrt.job_id,
            jrt.run_id,
            jrt.is_success,
            jrt.result_state,
            jrt.run_date
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        WHERE jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND jrt.result_state IS NOT NULL
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            usage_metadata_job_run_id AS run_id,
            SUM(list_cost) AS run_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j ON jr.job_id = j.job_id AND j.delete_time IS NULL
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
    ORDER BY failures DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_failure_trends	FUNCTION	TABLE_TYPE	"WITH daily_stats AS (
        SELECT
            run_date,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END) AS failed_runs,
            COUNT(DISTINCT CASE WHEN result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN job_id END) AS unique_failing_jobs
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline
        WHERE run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
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
    ORDER BY run_date"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_outlier_runs	FUNCTION	TABLE_TYPE	"WITH job_baselines AS (
        SELECT
            job_id,
            PERCENTILE_APPROX(run_duration_seconds, 0.90) AS p90_duration,
            COUNT(*) AS run_count
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline
        WHERE run_date >= DATE_ADD(CURRENT_DATE(), -(days_back + 30))
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
        WHERE jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND jrt.run_duration_seconds IS NOT NULL
    ),
    run_costs AS (
        SELECT
            usage_metadata_job_run_id AS run_id,
            SUM(list_cost) AS run_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
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
    ORDER BY deviation_ratio DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_repair_costs	FUNCTION	TABLE_TYPE	"WITH job_runs AS (
        SELECT
            jrt.job_id,
            jrt.run_id,
            jrt.result_state,
            jrt.is_success,
            j.name AS job_name,
            j.run_as
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
        WHERE jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND jrt.result_state IS NOT NULL
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            usage_metadata_job_run_id AS run_id,
            SUM(list_cost) AS run_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id, usage_metadata_job_run_id
    ),
    run_summary AS (
        SELECT
            jr.job_id,
            ANY_VALUE(jr.job_name) AS job_name,
            ANY_VALUE(jr.run_as) AS run_as,
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_retry_analysis	FUNCTION	TABLE_TYPE	"WITH run_attempts AS (
        SELECT
            job_id,
            run_date,
            COUNT(*) AS attempts_per_day,
            SUM(CASE WHEN is_success THEN 1 ELSE 0 END) AS successes_per_day,
            MIN(period_start_time) AS first_attempt_time
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline
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
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON r.job_id = j.job_id AND j.delete_time IS NULL
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
    ORDER BY retry_count DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_run_details	FUNCTION	TABLE_TYPE	"SELECT
        jrt.run_id,
        jrt.run_date,
        jrt.period_start_time AS start_time,
        jrt.period_end_time AS end_time,
        jrt.run_duration_minutes AS duration_minutes,
        jrt.result_state,
        jrt.termination_code,
        j.run_as,
        jrt.trigger_type
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
        ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
    WHERE jrt.job_id = job_id_filter
        AND jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
    ORDER BY jrt.period_start_time DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_run_duration_analysis	FUNCTION	TABLE_TYPE	"WITH job_durations AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            jrt.run_duration_minutes
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
        WHERE jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND jrt.result_state IS NOT NULL
            AND jrt.run_duration_minutes IS NOT NULL
    ),
    duration_stats AS (
        SELECT
            job_id,
            FIRST(job_name) AS job_name,
            COUNT(*) AS total_runs,
            AVG(run_duration_minutes) AS avg_duration_min,
            PERCENTILE_APPROX(run_duration_minutes, 0.5) AS median_duration_min,
            PERCENTILE_APPROX(run_duration_minutes, 0.9) AS p90_duration_min,
            PERCENTILE_APPROX(run_duration_minutes, 0.95) AS p95_duration_min,
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
    ORDER BY p95_duration_min DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_sla_compliance	FUNCTION	TABLE_TYPE	"SELECT
        jrt.job_id,
        j.name AS job_name,
        CAST(COUNT(*) AS INT) AS total_runs,
        CAST(COUNT(CASE WHEN jrt.run_duration_minutes <= 60 THEN 1 END) AS INT) AS runs_within_60min,
        CAST(COUNT(CASE WHEN jrt.run_duration_minutes > 60 THEN 1 END) AS INT) AS runs_over_60min,
        ROUND(COUNT(CASE WHEN jrt.run_duration_minutes <= 60 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS sla_compliance_pct,
        ROUND(AVG(jrt.run_duration_minutes), 2) AS avg_duration_minutes,
        ROUND(MAX(jrt.run_duration_minutes), 2) AS max_duration_minutes
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
        ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
    WHERE jrt.is_success = TRUE
        AND jrt.run_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY jrt.job_id, j.name
    HAVING COUNT(*) >= 3
    ORDER BY sla_compliance_pct ASC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_spend_trend_analysis	FUNCTION	TABLE_TYPE	"WITH job_costs AS (
        SELECT
            workspace_id,
            usage_metadata_job_id AS job_id,
            COALESCE(identity_metadata_run_as, identity_metadata_owned_by) AS run_as,
            SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 7 DAY AND CURRENT_DATE() - INTERVAL 1 DAY
                     THEN list_cost ELSE 0 END) AS last_7_day_spend,
            SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAY AND CURRENT_DATE() - INTERVAL 8 DAY
                     THEN list_cost ELSE 0 END) AS prior_7_day_spend
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY workspace_id, usage_metadata_job_id, COALESCE(identity_metadata_run_as, identity_metadata_owned_by)
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
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jc.workspace_id = j.workspace_id AND jc.job_id = j.job_id AND j.delete_time IS NULL
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
    ORDER BY spend_growth DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_job_success_rate	FUNCTION	TABLE_TYPE	"WITH job_stats AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            ANY_VALUE(j.run_as) AS run_as,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN jrt.is_success THEN 1 ELSE 0 END) AS successful_runs,
            SUM(CASE WHEN jrt.result_state IN ('FAILED', 'ERROR', 'TIMED_OUT') THEN 1 ELSE 0 END) AS failed_runs,
            AVG(jrt.run_duration_minutes) AS avg_duration_min,
            PERCENTILE_APPROX(jrt.run_duration_minutes, 0.95) AS p95_duration_min
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jrt.workspace_id = j.workspace_id AND jrt.job_id = j.job_id AND j.delete_time IS NULL
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
    ORDER BY success_rate_pct ASC, total_runs DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_jobs_on_legacy_dbr	FUNCTION	TABLE_TYPE	"WITH job_runs_exploded AS (
        SELECT
            jrt.workspace_id,
            jrt.job_id,
            jrt.run_id,
            jrt.run_date,
            EXPLODE(jrt.compute_ids) AS cluster_id
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        WHERE jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND jrt.compute_ids IS NOT NULL
            AND SIZE(jrt.compute_ids) > 0
    ),
    job_dbr AS (
        SELECT
            jre.job_id,
            j.name AS job_name,
            j.run_as,
            c.dbr_version,
            COUNT(DISTINCT jre.run_id) AS total_runs
        FROM job_runs_exploded jre
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jre.workspace_id = j.workspace_id AND jre.job_id = j.job_id AND j.delete_time IS NULL
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
            ON jre.cluster_id = c.cluster_id AND c.delete_time IS NULL
        WHERE c.dbr_version IS NOT NULL
        GROUP BY jre.job_id, j.name, j.run_as, c.dbr_version
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            SUM(list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id
    )
    SELECT
        jd.job_id,
        jd.job_name,
        jd.run_as,
        jd.dbr_version,
        jd.total_runs,
        ROUND(COALESCE(jc.total_cost, 0), 2) AS total_cost,
        CASE
            WHEN jd.dbr_version LIKE '9.%' THEN 'URGENT: Upgrade to latest LTS immediately'
            WHEN jd.dbr_version LIKE '8.%' THEN 'URGENT: Upgrade to latest LTS immediately'
            WHEN jd.dbr_version LIKE '7.%' THEN 'URGENT: Upgrade to latest LTS immediately'
            WHEN jd.dbr_version LIKE '10.%' THEN 'Recommended: Upgrade to DBR 14 LTS'
            WHEN jd.dbr_version LIKE '11.%' THEN 'Recommended: Upgrade to DBR 14 LTS'
            WHEN jd.dbr_version LIKE '12.%' THEN 'Consider: Upgrade to latest LTS'
            WHEN jd.dbr_version LIKE '13.%' THEN 'Consider: Upgrade to latest LTS'
            ELSE 'On supported version'
        END AS recommendation
    FROM job_dbr jd
    LEFT JOIN job_costs jc ON jd.job_id = jc.job_id
    ORDER BY jd.dbr_version ASC, jc.total_cost DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_jobs_without_autoscaling	FUNCTION	TABLE_TYPE	"WITH job_metrics AS (
        SELECT
            jrt.job_id,
            j.name AS job_name,
            j.run_as,
            COUNT(*) AS total_runs,
            AVG(jrt.run_duration_minutes) AS avg_duration,
            MAX(jrt.run_duration_minutes) AS max_duration,
            STDDEV(jrt.run_duration_minutes) AS duration_std
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline jrt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON jrt.job_id = j.job_id AND j.delete_time IS NULL
        WHERE jrt.run_date >= DATE_ADD(CURRENT_DATE(), -days_back)
        GROUP BY jrt.job_id, j.name, j.run_as
        HAVING COUNT(*) >= 5
    ),
    job_costs AS (
        SELECT
            usage_metadata_job_id AS job_id,
            SUM(list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND usage_metadata_job_id IS NOT NULL
        GROUP BY usage_metadata_job_id
    )
    SELECT
        jm.job_id,
        jm.job_name,
        jm.run_as,
        jm.total_runs,
        ROUND(COALESCE(jc.total_cost, 0), 2) AS total_cost,
        ROUND(jm.avg_duration, 2) AS avg_duration_minutes,
        ROUND(jm.max_duration, 2) AS max_duration_minutes,
        ROUND(jm.duration_std, 2) AS duration_variance,
        CASE
            WHEN jm.duration_std > 30 AND jm.avg_duration > 10 THEN 'High duration variance - strong autoscaling candidate'
            WHEN jm.duration_std > 15 THEN 'Variable duration - autoscaling recommended'
            WHEN jm.max_duration > jm.avg_duration * 2 THEN 'Occasional long runs - consider autoscaling'
            ELSE 'Evaluate for autoscaling benefits'
        END AS recommendation
    FROM job_metrics jm
    LEFT JOIN job_costs jc ON jm.job_id = jc.job_id
    WHERE COALESCE(jc.total_cost, 0) >= 100
    ORDER BY jc.total_cost DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_most_expensive_jobs	FUNCTION	TABLE_TYPE	"WITH job_costs AS (
        SELECT
            u.usage_metadata_job_id AS job_id,
            j.name AS job_name,
            ANY_VALUE(u.identity_metadata_run_as) AS run_as,
            COUNT(DISTINCT u.usage_metadata_job_run_id) AS run_count,
            SUM(u.list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage u
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
            ON u.usage_metadata_job_id = j.job_id AND j.delete_time IS NULL
        WHERE u.usage_metadata_job_id IS NOT NULL
            AND u.usage_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        GROUP BY u.usage_metadata_job_id, j.name
    ),
    job_reliability AS (
        SELECT
            job_id,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN is_success THEN 1 ELSE 0 END) AS successful_runs
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_job_run_timeline
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_off_hours_activity	FUNCTION	TABLE_TYPE	"SELECT
        event_date,
        user_identity_email AS user_email,
        COUNT(*) AS off_hours_events,
        CONCAT_WS(', ', COLLECT_SET(service_name)) AS services_accessed,
        SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_actions,
        COUNT(DISTINCT source_ip_address) AS unique_ips
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (HOUR(event_time) < business_hours_start OR HOUR(event_time) >= business_hours_end)
        AND user_identity_email IS NOT NULL
    GROUP BY event_date, user_identity_email
    HAVING COUNT(*) >= 5
    ORDER BY off_hours_events DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_permission_changes	FUNCTION	TABLE_TYPE	"SELECT
        event_time,
        user_identity_email AS changed_by,
        service_name AS service,
        action_name AS action,
        COALESCE(
            request_params['tableName'],
            request_params['schemaName'],
            request_params['catalogName'],
            request_params['clusterName'],
            request_params['warehouseId']
        ) AS target_resource,
        COALESCE(
            request_params['permission'],
            request_params['privileges'],
            request_params['access_level']
        ) AS permission,
        source_ip_address AS source_ip,
        NOT is_failed_action AS success
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (
            action_name LIKE '%grant%' OR
            action_name LIKE '%revoke%' OR
            action_name LIKE '%permission%' OR
            action_name LIKE '%access%' OR
            action_name IN ('updatePermissions', 'changeOwner', 'setPermissions')
        )
    ORDER BY event_time DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_pipeline_data_lineage	FUNCTION	TABLE_TYPE	"WITH lineage_summary AS (
        SELECT
            entity_type,
            entity_id,
            COLLECT_SET(source_table_full_name) AS sources,
            COLLECT_SET(target_table_full_name) AS targets,
            COUNT(DISTINCT event_date) AS unique_days,
            COUNT(*) AS total_events,
            MAX(event_date) AS last_run_date
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_table_lineage
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
        SIZE(ls.sources) + SIZE(ls.targets) * 2 AS complexity_score
    FROM lineage_summary ls
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
        ON ls.entity_type = 'JOB' AND ls.entity_id = j.job_id AND j.delete_time IS NULL
    ORDER BY complexity_score DESC, total_events DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_query_efficiency	FUNCTION	TABLE_TYPE	"WITH efficiency_analysis AS (
        SELECT
            statement_id,
            compute_warehouse_id AS warehouse_id,
            executed_by,
            total_duration_ms / 1000.0 AS duration_seconds,
            read_bytes / 1073741824.0 AS read_gb,
            produced_rows AS rows_produced,
            read_bytes / NULLIF(produced_rows, 0) AS bytes_per_row,
            spilled_local_bytes > 0 AS has_spill,
            COALESCE(spilled_local_bytes, 0) / 1073741824.0 AS spill_gb,
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_query_efficiency_analysis	FUNCTION	TABLE_TYPE	"WITH query_metrics AS (
        SELECT
            qh.compute_warehouse_id AS warehouse_id,
            dw.warehouse_name,
            COUNT(*) AS total_queries,
            SUM(CASE
                WHEN COALESCE(qh.spilled_local_bytes, 0) = 0
                 AND qh.waiting_at_capacity_duration_ms <= qh.total_duration_ms * 0.1
                 AND qh.total_duration_ms <= 300000
                THEN 1 ELSE 0
            END) AS efficient_queries,
            SUM(CASE WHEN COALESCE(qh.spilled_local_bytes, 0) > 0 THEN 1 ELSE 0 END) AS high_spill_queries,
            SUM(CASE WHEN qh.waiting_at_capacity_duration_ms > qh.total_duration_ms * 0.1 THEN 1 ELSE 0 END) AS high_queue_queries,
            SUM(CASE WHEN qh.total_duration_ms > 300000 THEN 1 ELSE 0 END) AS slow_queries,
            AVG(qh.waiting_at_capacity_duration_ms * 100.0 / NULLIF(qh.total_duration_ms, 0)) AS avg_queue_ratio,
            PERCENTILE_APPROX(qh.total_duration_ms, 0.95) / 1000.0 AS p95_duration_sec,
            PERCENTILE_APPROX(qh.total_duration_ms, 0.99) / 1000.0 AS p99_duration_sec
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history qh
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_warehouse dw
            ON qh.compute_warehouse_id = dw.warehouse_id AND dw.delete_time IS NULL
        WHERE qh.start_time >= TIMESTAMPADD(HOUR, -hours_back, CURRENT_TIMESTAMP())
            AND qh.total_duration_ms > 1000
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
    ORDER BY efficiency_rate ASC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_query_latency_percentiles	FUNCTION	TABLE_TYPE	"SELECT
        q.compute_warehouse_id AS warehouse_id,
        w.warehouse_name,
        COUNT(*) AS query_count,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.5) AS p50_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.75) AS p75_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.90) AS p90_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.95) AS p95_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.99) AS p99_seconds,
        MAX(q.total_duration_ms / 1000.0) AS max_seconds
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history q
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_warehouse w
        ON q.compute_warehouse_id = w.warehouse_id AND w.delete_time IS NULL
    WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND q.execution_status = 'FINISHED'
        AND q.compute_warehouse_id IS NOT NULL
    GROUP BY q.compute_warehouse_id, w.warehouse_name
    ORDER BY query_count DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_query_volume_trends	FUNCTION	TABLE_TYPE	"WITH periods AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history
        WHERE DATE(start_time) >= DATE_ADD(CURRENT_DATE(), -days_back)
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
    ORDER BY period_start"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_security_events_timeline	FUNCTION	TABLE_TYPE	"SELECT
        event_time,
        user_identity_email AS user_email,
        CASE
            WHEN is_sensitive_action AND is_failed_action THEN 'FAILED_SENSITIVE'
            WHEN is_sensitive_action THEN 'SENSITIVE'
            WHEN is_failed_action THEN 'FAILED'
            ELSE 'NORMAL'
        END AS event_type,
        service_name AS service,
        action_name AS action,
        COALESCE(
            request_params['tableName'],
            request_params['schemaName'],
            request_params['clusterName'],
            request_params['warehouseId'],
            request_params['jobId']
        ) AS target_resource,
        NOT is_failed_action AS success,
        source_ip_address AS source_ip
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND (user_filter = 'ALL' OR user_identity_email = user_filter)
        AND (is_sensitive_action OR is_failed_action)
    ORDER BY event_time DESC
    LIMIT 1000"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_sensitive_table_access	FUNCTION	TABLE_TYPE	"SELECT
        event_date AS access_date,
        user_identity_email AS user_email,
        request_params['tableName'] AS table_name,
        action_name AS action,
        COUNT(*) AS access_count,
        CONCAT_WS(', ', COLLECT_SET(source_ip_address)) AS source_ips,
        MAX(CASE WHEN HOUR(event_time) < 7 OR HOUR(event_time) > 19 THEN TRUE ELSE FALSE END) AS is_off_hours
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
    WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND request_params['tableName'] IS NOT NULL
        AND request_params['tableName'] LIKE table_pattern
        AND action_name IN ('getTable', 'selectFromTable', 'readTable', 'queryTable')
    GROUP BY event_date, user_identity_email, request_params['tableName'], action_name
    ORDER BY access_date DESC, access_count DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_service_account_audit	FUNCTION	TABLE_TYPE	"WITH service_accounts AS (
        SELECT
            user_identity_email AS account_email,
            CASE
                WHEN user_identity_email LIKE '%@databricks.com'
                     AND user_identity_email LIKE 'System-%' THEN 'SYSTEM'
                WHEN user_identity_email LIKE 'system-%' THEN 'SYSTEM'
                WHEN user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema') THEN 'PLATFORM'
                WHEN user_identity_email LIKE 'DBX_%' THEN 'PLATFORM'
                WHEN user_identity_email LIKE '%@%.iam.gserviceaccount.com' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email LIKE '%spn@%' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email NOT LIKE '%@%' THEN 'SERVICE_PRINCIPAL'
                ELSE NULL
            END AS account_type,
            event_time,
            action_name,
            service_name,
            source_ip_address,
            is_failed_action,
            is_sensitive_action
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND user_identity_email IS NOT NULL
    )
    SELECT
        account_email,
        account_type,
        COUNT(*) AS total_events,
        COUNT(DISTINCT action_name) AS unique_actions,
        COUNT(DISTINCT service_name) AS unique_services,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
        SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) AS failure_rate,
        COUNT(DISTINCT source_ip_address) AS unique_ips,
        SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_events,
        MIN(event_time) AS first_activity,
        MAX(event_time) AS last_activity,
        CASE
            WHEN SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) > 20 THEN 'HIGH'
            WHEN SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) > 100 THEN 'HIGH'
            WHEN COUNT(DISTINCT source_ip_address) > 10 THEN 'MEDIUM'
            WHEN SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) > 10 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS risk_level
    FROM service_accounts
    WHERE account_type IS NOT NULL
    GROUP BY account_email, account_type
    ORDER BY
        CASE risk_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
        total_events DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_slow_queries	FUNCTION	TABLE_TYPE	"WITH slow AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history q
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_warehouse w
            ON q.compute_warehouse_id = w.warehouse_id AND w.delete_time IS NULL
        WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND q.total_duration_ms >= duration_threshold_seconds * 1000
            AND q.execution_status = 'FINISHED'
    )
    SELECT rank, statement_id, warehouse_id, warehouse_name, executed_by,
           statement_type, duration_seconds, read_gb, rows_produced, start_time
    FROM slow
    WHERE rank <= top_n
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_spend_by_custom_tags	FUNCTION	TABLE_TYPE	"WITH tag_list AS (
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
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage f
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
    ORDER BY tag_key, total_cost DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_table_access_audit	FUNCTION	TABLE_TYPE	"WITH table_access AS (
        SELECT
            event_date,
            COALESCE(source_table_full_name, target_table_full_name) AS table_full_name,
            CASE
                WHEN target_table_full_name IS NOT NULL THEN 'WRITE'
                ELSE 'READ'
            END AS access_type,
            created_by AS user_email,
            entity_type,
            entity_id,
            event_time
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_table_lineage
        WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND (source_table_full_name LIKE table_pattern OR target_table_full_name LIKE table_pattern)
    )
    SELECT
        event_date,
        table_full_name,
        access_type,
        user_email,
        entity_type,
        entity_id,
        COUNT(*) AS access_count,
        MIN(event_time) AS first_access,
        MAX(event_time) AS last_access
    FROM table_access
    WHERE table_full_name IS NOT NULL
    GROUP BY event_date, table_full_name, access_type, user_email, entity_type, entity_id
    ORDER BY event_date DESC, access_count DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_table_activity_status	FUNCTION	TABLE_TYPE	"WITH table_reads AS (
        SELECT
            source_table_full_name AS table_full_name,
            event_date,
            created_by
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_table_lineage
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND source_table_full_name IS NOT NULL
    ),
    table_writes AS (
        SELECT
            target_table_full_name AS table_full_name,
            event_date,
            created_by
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_table_lineage
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
        days_since_last_access DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_table_freshness	FUNCTION	TABLE_TYPE	"SELECT
        table_catalog,
        table_schema,
        table_name,
        last_altered AS last_modified,
        TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) AS hours_since_update,
        TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) > freshness_threshold_hours AS is_stale,
        NULL AS row_count
    FROM prashanth_subrahmanyam_catalog.information_schema.tables
    WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
        AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
        AND table_type = 'MANAGED'
    ORDER BY hours_since_update DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_tables_failing_quality	FUNCTION	TABLE_TYPE	"WITH table_info AS (
        SELECT
            table_name,
            TIMESTAMPDIFF(HOUR, last_altered, CURRENT_TIMESTAMP()) AS hours_since_update
        FROM prashanth_subrahmanyam_catalog.information_schema.tables
        WHERE table_catalog = 'prashanth_subrahmanyam_catalog'
            AND table_schema = 'dev_prashanth_subrahmanyam_system_gold'
            AND table_type = 'MANAGED'
    )
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

    ORDER BY severity DESC, hours_since_update DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_tag_coverage	FUNCTION	TABLE_TYPE	"WITH summary AS (
        SELECT
            COUNT(*) AS total_records,
            SUM(CASE WHEN is_tagged THEN 1 ELSE 0 END) AS tagged_records,
            SUM(list_cost) AS total_cost,
            SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) AS tagged_cost,
            COUNT(DISTINCT CASE WHEN is_tagged THEN COALESCE(usage_metadata_job_id, usage_metadata_cluster_id) END) AS tagged_resources,
            COUNT(DISTINCT COALESCE(usage_metadata_job_id, usage_metadata_cluster_id)) AS total_resources
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    FROM summary"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_top_cost_contributors	FUNCTION	TABLE_TYPE	"WITH cost_summary AS (
        SELECT
            f.workspace_id,
            w.workspace_name,
            f.sku_name,
            SUM(f.usage_quantity) AS total_dbu,
            SUM(f.list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage f
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_workspace w
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_underutilized_clusters	FUNCTION	TABLE_TYPE	"WITH cluster_metrics AS (
        SELECT
            nt.cluster_id,
            c.cluster_name,
            c.cluster_source AS cluster_type,
            c.owned_by,
            ROUND(AVG(nt.cpu_user_percent + nt.cpu_system_percent), 1) AS avg_cpu_pct,
            ROUND(AVG(nt.mem_used_percent), 1) AS avg_mem_pct,
            SUM(TIMESTAMPDIFF(MINUTE, nt.start_time, nt.end_time)) / 60.0 AS total_hours
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_node_timeline nt
        LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
            ON nt.cluster_id = c.cluster_id AND c.delete_time IS NULL
        WHERE nt.start_time >= DATE_ADD(CURRENT_DATE(), -days_back)
        GROUP BY nt.cluster_id, c.cluster_name, c.cluster_source, c.owned_by
        HAVING total_hours >= min_hours
    ),
    cluster_cost AS (
        SELECT usage_metadata_cluster_id AS cluster_id, SUM(list_cost) AS total_cost
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
        WHERE usage_date >= DATE_ADD(CURRENT_DATE(), -days_back)
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
    ORDER BY potential_savings DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_untagged_resources	FUNCTION	TABLE_TYPE	"WITH untagged AS (
        SELECT
            CASE
                WHEN usage_metadata_job_id IS NOT NULL THEN 'JOB'
                WHEN usage_metadata_warehouse_id IS NOT NULL THEN 'WAREHOUSE'
                WHEN usage_metadata_cluster_id IS NOT NULL THEN 'CLUSTER'
                ELSE 'OTHER'
            END AS resource_type,
            COALESCE(usage_metadata_job_id, usage_metadata_warehouse_id, usage_metadata_cluster_id) AS resource_id,
            COALESCE(identity_metadata_run_as, identity_metadata_owned_by) AS owner,
            SUM(list_cost) AS total_cost,
            MAX(usage_date) AS last_used
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage
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
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_job j
        ON u.resource_type = 'JOB' AND u.resource_id = j.job_id AND j.delete_time IS NULL
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_warehouse w
        ON u.resource_type = 'WAREHOUSE' AND u.resource_id = w.warehouse_id AND w.delete_time IS NULL
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_cluster c
        ON u.resource_type = 'CLUSTER' AND u.resource_id = c.cluster_id AND c.delete_time IS NULL
    WHERE resource_type = 'ALL' OR u.resource_type = resource_type
    ORDER BY u.total_cost DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_user_activity_patterns	FUNCTION	TABLE_TYPE	"WITH user_activity AS (
        SELECT
            user_identity_email AS user_email,
            CASE
                WHEN user_identity_email LIKE '%@databricks.com'
                     AND user_identity_email LIKE 'System-%' THEN 'SYSTEM'
                WHEN user_identity_email LIKE 'system-%' THEN 'SYSTEM'
                WHEN user_identity_email IN ('Unity Catalog', 'Delta Sharing', 'Catalog', 'Schema') THEN 'PLATFORM'
                WHEN user_identity_email LIKE 'DBX_%' THEN 'PLATFORM'
                WHEN user_identity_email LIKE '%@%.iam.gserviceaccount.com' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email LIKE '%spn@%' THEN 'SERVICE_PRINCIPAL'
                WHEN user_identity_email NOT LIKE '%@%' THEN 'SERVICE_PRINCIPAL'
                ELSE 'HUMAN_USER'
            END AS user_type,
            event_date,
            HOUR(event_time) AS event_hour,
            DAYOFWEEK(event_date) AS day_of_week,
            is_failed_action,
            service_name,
            source_ip_address
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
        WHERE event_date >= DATE_ADD(CURRENT_DATE(), -days_back)
            AND user_identity_email IS NOT NULL
    ),
    hourly_activity AS (
        SELECT
            user_email,
            user_type,
            event_date,
            event_hour,
            COUNT(*) AS hourly_events
        FROM user_activity
        GROUP BY user_email, user_type, event_date, event_hour
    ),
    hourly_counts AS (
        SELECT
            user_email,
            event_hour,
            COUNT(*) AS hour_events,
            ROW_NUMBER() OVER (PARTITION BY user_email ORDER BY COUNT(*) DESC) AS hour_rank
        FROM user_activity
        GROUP BY user_email, event_hour
    ),
    peak_hours AS (
        SELECT user_email, event_hour AS peak_hour, hour_events AS peak_hour_events_raw
        FROM hourly_counts
        WHERE hour_rank = 1
    ),
    user_metrics AS (
        SELECT
            ua.user_email,
            ua.user_type,
            COUNT(*) AS total_events,
            COUNT(DISTINCT ua.event_date) AS active_days,
            COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT ua.event_date), 0) AS avg_daily_events,
            SUM(CASE WHEN ua.event_hour < 7 OR ua.event_hour >= 19 THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS off_hours_pct,
            SUM(CASE WHEN ua.day_of_week IN (1, 7) THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS weekend_pct,
            COUNT(DISTINCT ua.service_name) AS unique_services,
            COUNT(DISTINCT ua.source_ip_address) AS unique_ips,
            SUM(CASE WHEN ua.is_failed_action THEN 1 ELSE 0 END) * 100.0 /
                NULLIF(COUNT(*), 0) AS failed_action_rate
        FROM user_activity ua
        GROUP BY ua.user_email, ua.user_type
    ),
    burst_counts AS (
        SELECT
            user_email,
            COUNT(*) AS burst_count,
            MAX(hourly_events) AS peak_hour_events
        FROM hourly_activity
        WHERE hourly_events >= burst_threshold
        GROUP BY user_email
    ),
    final_metrics AS (
        SELECT
            um.user_email,
            um.user_type,
            um.total_events,
            um.active_days,
            um.avg_daily_events,
            COALESCE(ph.peak_hour, 0) AS peak_hour,
            COALESCE(ph.peak_hour_events_raw, bc.peak_hour_events, 0) AS peak_hour_events,
            um.off_hours_pct,
            um.weekend_pct,
            COALESCE(bc.burst_count, 0) AS burst_count,
            um.unique_services,
            um.unique_ips,
            um.failed_action_rate,
            CASE
                WHEN bc.burst_count >= 3 AND um.off_hours_pct > 30 THEN 'ANOMALOUS'
                WHEN bc.burst_count >= 3 THEN 'BURSTY'
                WHEN um.off_hours_pct > 50 THEN 'AFTER_HOURS'
                ELSE 'NORMAL'
            END AS activity_pattern
        FROM user_metrics um
        LEFT JOIN peak_hours ph ON um.user_email = ph.user_email
        LEFT JOIN burst_counts bc ON um.user_email = bc.user_email
    )
    SELECT *
    FROM final_metrics
    WHERE (NOT exclude_system_accounts OR user_type NOT IN ('SYSTEM', 'PLATFORM'))
    ORDER BY
        CASE activity_pattern
            WHEN 'ANOMALOUS' THEN 1
            WHEN 'BURSTY' THEN 2
            WHEN 'AFTER_HOURS' THEN 3
            ELSE 4
        END,
        total_events DESC"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_user_activity_summary	FUNCTION	TABLE_TYPE	"WITH user_stats AS (
        SELECT
            user_identity_email AS user_email,
            COUNT(*) AS event_count,
            COUNT(DISTINCT action_name) AS unique_actions,
            COUNT(DISTINCT service_name) AS unique_services,
            SUM(CASE WHEN is_failed_action THEN 1 ELSE 0 END) AS failed_events,
            SUM(CASE WHEN is_sensitive_action THEN 1 ELSE 0 END) AS sensitive_events,
            COUNT(DISTINCT source_ip_address) AS unique_ips,
            SUM(CASE WHEN HOUR(event_time) < 7 OR HOUR(event_time) > 19 THEN 1 ELSE 0 END) AS off_hours_events
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_audit_logs
        WHERE event_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
            AND user_identity_email IS NOT NULL
        GROUP BY user_identity_email
    ),
    with_risk AS (
        SELECT *,
            LEAST(100,
                (failed_events * 10) +
                (CASE WHEN unique_ips > 5 THEN 20 ELSE 0 END) +
                (sensitive_events * 2) +
                (CASE WHEN off_hours_events > event_count * 0.3 THEN 30 ELSE 0 END)
            ) AS risk_score,
            ROW_NUMBER() OVER (ORDER BY event_count DESC) AS rank
        FROM user_stats
    )
    SELECT rank, user_email, event_count, unique_actions, unique_services,
           failed_events, sensitive_events, unique_ips, off_hours_events, risk_score
    FROM with_risk
    WHERE rank <= top_n
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_user_query_summary	FUNCTION	TABLE_TYPE	"WITH user_stats AS (
        SELECT
            executed_by AS user_email,
            COUNT(*) AS query_count,
            SUM(total_duration_ms) / 3600000.0 AS total_duration_hours,
            AVG(total_duration_ms) / 1000.0 AS avg_duration_seconds,
            SUM(read_bytes) / 1073741824.0 AS total_read_gb,
            (SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) AS error_rate_pct,
            FIRST(compute_warehouse_id, TRUE) AS most_used_warehouse
        FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history
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
    ORDER BY rank"
prashanth_subrahmanyam_catalog	dev_prashanth_subrahmanyam_system_gold	get_warehouse_utilization	FUNCTION	TABLE_TYPE	"SELECT
        q.compute_warehouse_id AS warehouse_id,
        w.warehouse_name,
        w.warehouse_size AS warehouse_size,
        COUNT(*) AS total_queries,
        SUM(q.total_duration_ms) / 3600000.0 AS total_duration_hours,
        AVG(q.total_duration_ms) / 1000.0 AS avg_duration_seconds,
        PERCENTILE_APPROX(q.total_duration_ms / 1000.0, 0.95) AS p95_duration_seconds,
        AVG(COALESCE(q.waiting_at_capacity_duration_ms, 0)) / 1000.0 AS avg_queue_time_seconds,
        MAX(q.statement_id) AS peak_concurrency,
        (SUM(CASE WHEN q.execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) AS error_rate_pct
    FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_query_history q
    LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_warehouse w
        ON q.compute_warehouse_id = w.warehouse_id AND w.delete_time IS NULL
    WHERE DATE(q.start_time) BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
        AND q.compute_warehouse_id IS NOT NULL
    GROUP BY q.compute_warehouse_id, w.warehouse_name, w.warehouse_size
    ORDER BY total_queries DESC"