# Genie Space Comprehensive Column Fixes

**Date:** Thu Jan  8 16:40:51 CST 2026
**Total Fixes:** 26
**Source:** Ground truth from docs/reference/actual_assets/

## Fixes Applied:

### cost_intelligence

- **Q22**: `total_cost` → `scCROSS.total_sku_cost`
  - Context: SKU CROSS JOIN context
  - Question ID: d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a6

- **Q25**: `workspace_name` → `workspace_id`
  - Context: cost_anomaly_predictions table
  - Question ID: a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d9

### job_health_monitor

- **Q4**: `failed_runs` → `job_name`
  - Context: get_failed_jobs TVF - use COUNT(*) for failures
  - Question ID: 3946480a0fa84c8688d18d931eb63a2b

- **Q6**: `p95_duration_minutes` → `p95_duration_min`
  - Context: mv_job_performance actual column
  - Question ID: c358015134824e219400a6b58020943f

- **Q7**: `success_rate` → `success_rate_pct`
  - Context: mv_job_performance actual column
  - Question ID: df52b062b3804ebba4cba65b10384f41

- **Q9**: `termination_code` → `deviation_ratio`
  - Context: get_job_sla_deviations TVF output
  - Question ID: c04f050ba8c54743bbc75a9c68ad1709

- **Q14**: `f.start_time` → `f.period_start_time`
  - Context: system.lakeflow.flow_events alias
  - Question ID: bb5f4ff19a4840e08311cde2b7aebc88

- **Q18**: `run_date` → `ft.run_id`
  - Context: mv_job_performance alias - use run_id instead
  - Question ID: 15e71a6f8bf14fceb6a2774bf574ad65

### performance

- **Q14**: `p99_duration_seconds` → `p99_seconds`
  - Context: mv_query_performance actual column name
  - Question ID: 4002051c4693c098dfb4fb218342f9a1

- **Q16**: `recommended_action` → `prediction`
  - Context: cluster_rightsizing_predictions table
  - Question ID: 550801d6c8a6f42a17c5969ccfd24fb8

- **Q25**: `qh.query_volume` → `qhCROSS.query_volume`
  - Context: Alias fix for CROSS JOIN
  - Question ID: c78abcd7201a0b0907cf3220b0f9c8c6

### security_auditor

- **Q7**: `failed_events` → `off_hours_events`
  - Context: TVF output column
  - Question ID: def0123456789abcdef0123456789abc

- **Q8**: `change_date` → `event_time`
  - Context: get_permission_changes TVF output
  - Question ID: ef0123456789abcdef0123456789abcd

- **Q9**: `event_count` → `off_hours_events`
  - Context: get_off_hours_activity TVF output
  - Question ID: f0123456789abcdef0123456789abcde

- **Q10**: `high_risk_events` → `failed_events`
  - Context: mv_security_events actual column
  - Question ID: 0123456789abcdef0123456789abcdef

- **Q11**: `user_identity` → `user_email`
  - Context: get_off_hours_activity TVF output
  - Question ID: 123456789abcdef0123456789abcdef0

- **Q15**: `unique_actions` → `unique_users`
  - Context: mv_security_events actual column
  - Question ID: 56789abcdef0123456789abcdef01234

- **Q17**: `event_volume_drift` → `event_volume_drift_pct`
  - Context: monitoring table column
  - Question ID: b16acdef0123456789abcdef01234516

### unified_health_monitor

- **Q7**: `failure_count` → `failed_runs`
  - Context: get_failed_jobs TVF output
  - Question ID: c7885e2ee783ad77b1482037e1480da8

- **Q11**: `utilization_rate` → `daily_avg_cost`
  - Context: mv_commit_tracking actual column
  - Question ID: 0010b2efae72f0f211bcdc144b2a05fe

- **Q12**: `query_count` → `total_queries`
  - Context: mv_query_performance actual column
  - Question ID: 9221de68365dcffa6ced08299727ed89

- **Q13**: `failed_events` → `failed_records`
  - Context: DLT monitoring table column
  - Question ID: ac3dd5574e65ed5539480999f83c0c61

- **Q15**: `high_risk_events` → `failed_events`
  - Context: mv_security_events actual column
  - Question ID: a38b9b6611cb8a91a1cdb69250c58aa2

- **Q16**: `days_since_last_access` → `hours_since_update`
  - Context: mv_data_quality actual column
  - Question ID: a8ec2cc04f4e4055b3c6942856468721

- **Q18**: `recommended_action` → `prediction`
  - Context: cluster_rightsizing_predictions table
  - Question ID: 20e9892d32598a3befe821d2033ee99f

- **Q19**: `cost_30d` → `last_30_day_cost`
  - Context: mv_cost_analytics actual column
  - Question ID: 2f5e00f43b399b047a61bc3b17897379


## Next Steps:

1. Deploy bundle: `databricks bundle deploy -t dev`
2. Re-run validation: `databricks bundle run -t dev genie_benchmark_sql_validation_job`
3. Expected: ~27 fixes applied, reducing errors from 40 to ~13
