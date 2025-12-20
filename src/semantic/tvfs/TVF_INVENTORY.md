# TVF Inventory by Agent Domain

## Overview

Total TVFs: **60 functions** organized across **5 Agent Domains** (exceeds 50+ target ✅)

| Agent Domain | File | TVF Count | Primary Use Cases |
|--------------|------|-----------|-------------------|
| 💰 **Cost** | `cost_tvfs.sql` | **15** | FinOps, chargeback, tag governance, commit tracking |
| 🔄 **Reliability** | `reliability_tvfs.sql` | **12** | Job failures, SLA compliance, retry patterns, costs |
| ⚡ **Performance** | `performance_tvfs.sql` + `compute_tvfs.sql` | **16** | Query analysis, warehouse sizing, cluster optimization |
| 🔒 **Security** | `security_tvfs.sql` | **10** | Audit trails, access patterns, compliance |
| ✅ **Quality** | `quality_tvfs.sql` | **7** | Data freshness, lineage, governance |

---

## 💰 Cost Agent TVFs (15)

| # | TVF Name | Purpose |
|---|----------|---------|
| 1 | `get_top_cost_contributors` | Identify top cost contributors by workspace and SKU |
| 2 | `get_cost_trend_by_sku` | Track daily cost trends by SKU for budget monitoring |
| 3 | `get_cost_by_owner` | Chargeback analysis by resource owner |
| 4 | `get_cost_by_tag` | Tag-based cost allocation for chargeback |
| 5 | `get_untagged_resources` | Tag governance enforcement - find untagged resources |
| 6 | `get_tag_coverage` | Tag coverage metrics for compliance tracking |
| 7 | `get_cost_week_over_week` | Week-over-week cost trend analysis |
| 8 | `get_cost_anomalies` | Statistical anomaly detection for cost spikes |
| 9 | `get_cost_forecast_summary` | Cost forecasting for budget planning |
| 10 | `get_cost_mtd_summary` | Month-to-date cost tracking |
| 11 | `get_commit_vs_actual` | Commit tracking vs actual spend |
| 12 | `get_spend_by_custom_tags` | Multi-tag cost analysis |
| 13 | `get_cost_growth_analysis` | Identify entities with highest cost growth |
| 14 | `get_cost_growth_by_period` | Flexible period-over-period comparison |
| 15 | `get_all_purpose_cluster_cost` | Identify All-Purpose cluster costs for migration |

---

## 🔄 Reliability Agent TVFs (12)

| # | TVF Name | Purpose |
|---|----------|---------|
| 1 | `get_failed_jobs` | Failed job run analysis for root cause investigation |
| 2 | `get_job_success_rate` | Job success rate analysis for SLA compliance |
| 3 | `get_job_duration_percentiles` | Job duration percentiles for SLA planning |
| 4 | `get_job_failure_trends` | Daily failure trend tracking |
| 5 | `get_job_sla_compliance` | SLA compliance tracking by job |
| 6 | `get_job_run_details` | Detailed run history for specific jobs |
| 7 | `get_most_expensive_jobs` | Identify most expensive jobs by compute cost |
| 8 | `get_job_retry_analysis` | Identify flaky jobs requiring retries |
| 9 | `get_job_repair_costs` | Jobs with highest repair (retry) costs |
| 10 | `get_job_spend_trend_analysis` | Jobs with highest cost growth |
| 11 | `get_job_failure_costs` | Jobs with high failure counts and costs |
| 12 | `get_job_run_duration_analysis` | Job duration statistics with percentiles |

---

## ⚡ Performance Agent TVFs (16)

### Query Performance (10)

| # | TVF Name | Purpose |
|---|----------|---------|
| 1 | `get_slow_queries` | Identify slowest queries exceeding threshold |
| 2 | `get_warehouse_utilization` | SQL Warehouse utilization metrics |
| 3 | `get_query_efficiency` | Query efficiency analysis with optimization flags |
| 4 | `get_high_spill_queries` | Queries with disk spills (memory pressure) |
| 5 | `get_query_volume_trends` | Query volume trend analysis |
| 6 | `get_user_query_summary` | User-level query usage summary |
| 7 | `get_query_latency_percentiles` | Query latency percentiles by warehouse |
| 8 | `get_failed_queries` | Failed queries with error details |
| 9 | `get_query_efficiency_analysis` | Warehouse query efficiency for scaling decisions |
| 10 | `get_job_outlier_runs` | Job runs deviating from P90 baseline |

### Compute/Cluster (6)

| # | TVF Name | Purpose |
|---|----------|---------|
| 1 | `get_cluster_utilization` | Cluster utilization metrics for optimization |
| 2 | `get_cluster_resource_metrics` | Detailed cluster resource metrics |
| 3 | `get_underutilized_clusters` | Underutilized clusters with savings potential |
| 4 | `get_jobs_without_autoscaling` | Jobs that could benefit from autoscaling |
| 5 | `get_jobs_on_legacy_dbr` | Jobs running on legacy DBR versions |
| 6 | `get_cluster_right_sizing_recommendations` | Comprehensive cluster right-sizing analysis |

---

## 🔒 Security Agent TVFs (10)

| # | TVF Name | Purpose |
|---|----------|---------|
| 1 | `get_user_activity_summary` | User activity with risk scoring |
| 2 | `get_sensitive_table_access` | Table access pattern analysis for PII monitoring |
| 3 | `get_failed_actions` | Failed action investigation |
| 4 | `get_permission_changes` | Permission change audit trail |
| 5 | `get_off_hours_activity` | Off-hours activity detection |
| 6 | `get_security_events_timeline` | Chronological security event timeline |
| 7 | `get_ip_address_analysis` | IP address analysis for shared account detection |
| 8 | `get_table_access_audit` | Table access audit trail for compliance |
| 9 | `get_user_activity_patterns` | Temporal activity patterns with anomaly detection |
| 10 | `get_service_account_audit` | Service account audit for automated activity |

---

## ✅ Quality Agent TVFs (7)

| # | TVF Name | Purpose |
|---|----------|---------|
| 1 | `get_table_freshness` | Table freshness monitoring for SLA compliance |
| 2 | `get_job_data_quality_status` | Data quality status from job execution patterns |
| 3 | `get_data_freshness_by_domain` | Domain-level data freshness summary |
| 4 | `get_data_quality_summary` | Overall data quality summary across dimensions |
| 5 | `get_tables_failing_quality` | Tables failing quality checks |
| 6 | `get_table_activity_status` | Table activity analysis to identify orphaned tables |
| 7 | `get_pipeline_data_lineage` | Pipeline data lineage with dependencies |

---

## Comment Format Standard

All TVFs use the standardized bullet-point comment format for Genie compatibility:

```sql
COMMENT '
- PURPOSE: Primary function purpose
- BEST FOR: "Natural language question 1" "Question 2" "Question 3"
- NOT FOR: Alternative TVFs to use instead
- RETURNS: What the function returns
- PARAMS: param1 (type), param2 (default value)
- SYNTAX: SELECT * FROM TABLE(function_name("param1", "param2"))
- NOTE: Additional notes (optional)
'
```

---

## Deployment

Deploy all TVFs using the deployment script:

```bash
databricks bundle run -t dev deploy_tvfs_job
```

Or execute directly:

```python
# Run deploy_tvfs.py notebook with parameters:
# - catalog: target_catalog
# - gold_schema: target_gold_schema
```

---

## Verification

After deployment, verify TVFs:

```sql
-- Count deployed TVFs
SELECT COUNT(*) AS tvf_count
FROM {catalog}.information_schema.routines
WHERE routine_schema = '{gold_schema}'
  AND routine_type = 'FUNCTION';

-- List all TVFs
SELECT routine_name, created, last_altered
FROM {catalog}.information_schema.routines
WHERE routine_schema = '{gold_schema}'
  AND routine_type = 'FUNCTION'
ORDER BY routine_name;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12 | Initial 60 TVFs organized by 5 Agent Domains |

