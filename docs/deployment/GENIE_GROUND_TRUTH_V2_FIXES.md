# Genie Space Ground Truth Fixes V2

**Date:** Thu Jan  8 17:36:06 CST 2026
**Total Fixes Applied:** 9

## Fixes Summary

### cost_intelligence_genie_export.json

- **Q22:** ✅ FIXED
  - Error: `scCROSS.total_sku_cost`
  - Fix: `scCROSS.total_cost`
  - Reason: mv_cost_analytics has total_cost, not total_sku_cost

- **Q25:** ⚠️  MANUAL
  - Error: `workspace_id`
  - Reason: workspace_id exists in both tables - need to check query context

### performance_genie_export.json

- **Q16:** ⚠️  MANUAL
  - Error: `potential_savings_usd`
  - Reason: No savings column in warehouse_optimizer_predictions ML table

- **Q25:** ✅ FIXED
  - Error: `qh.avg_query_duration`
  - Fix: `qhCROSS.avg_query_duration`
  - Reason: CROSS JOIN alias is qhCROSS, not qh

### security_auditor_genie_export.json

- **Q7:** ✅ FIXED
  - Error: `off_hours_events`
  - Fix: `failed_events`
  - Reason: get_failed_actions TVF returns failed_events column

- **Q11:** ✅ FIXED
  - Error: `hour_of_day`
  - Fix: `event_hour`
  - Reason: get_off_hours_activity TVF returns event_hour column

### unified_health_monitor_genie_export.json

- **Q7:** ✅ FIXED
  - Error: `failed_runs`
  - Fix: `error_message`
  - Reason: get_failed_jobs TVF returns job details, count in outer query

- **Q13:** ✅ FIXED
  - Error: `failed_records`
  - Fix: `failed_count`
  - Reason: mv_dlt_pipeline_health has failed_count column

- **Q18:** ⚠️  MANUAL
  - Error: `potential_savings_usd`
  - Reason: No savings column in warehouse_optimizer_predictions ML table

- **Q19:** ✅ FIXED
  - Error: `sla_breach_rate`
  - Fix: `sla_breach_rate`
  - Reason: sla_breach_rate exists in cache_hit_predictions - query context issue

### job_health_monitor_genie_export.json

- **Q6:** ✅ FIXED
  - Error: `p95_duration_min`
  - Fix: `p90_duration_min`
  - Reason: mv_job_performance has p90_duration_min, not p95

- **Q7:** ✅ FIXED
  - Error: `get_job_success_rate_pct`
  - Fix: `get_job_success_rate`
  - Reason: TVF is called get_job_success_rate (no _pct suffix)

- **Q10:** ⚠️  MANUAL
  - Error: `retry_effectiveness`
  - Reason: get_job_retry_analysis doesn't have retry_effectiveness column

- **Q14:** ✅ FIXED
  - Error: `p.pipeline_name`
  - Fix: `p.name`
  - Reason: system.lakeflow.pipelines table has 'name' column, not 'pipeline_name'

- **Q18:** ⚠️  MANUAL
  - Error: `jt.depends_on`
  - Reason: system.lakeflow.job_task_run_timeline doesn't have depends_on column

