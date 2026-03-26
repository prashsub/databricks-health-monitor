# Genie Bulk TVF Name Fix Progress

**Started:** January 7, 2026  
**Total Fixes:** 15 TVF name corrections  
**Files to Update:** 6 Genie JSON export files

---

## 📋 Fix List

| # | Old Name | New Name | Status |
|---|----------|----------|--------|
| 1 | `get_user_activity` | `get_user_activity_summary` | 🔄 In Progress |
| 2 | `get_pii_access_events` | `get_sensitive_table_access` | ⏳ Pending |
| 3 | `get_failed_authentication_events` | `get_failed_actions` | ⏳ Pending |
| 4 | `get_permission_change_events` | `get_permission_changes` | ⏳ Pending |
| 5 | `get_service_account_activity` | `get_service_account_audit` | ⏳ Pending |
| 6 | `get_query_spill_analysis` | `get_high_spill_queries` | ⏳ Pending |
| 7 | `get_idle_clusters` | `get_underutilized_clusters` | ⏳ Pending |
| 8 | `get_query_duration_percentiles` | `get_query_latency_percentiles` | ⏳ Pending |
| 9 | `get_failed_jobs_summary` | `get_failed_jobs` | ⏳ Pending |
| 10 | `get_job_success_rates` | `get_job_success_rate` | ⏳ Pending |
| 11 | `get_job_failure_patterns` | `get_job_failure_trends` | ⏳ Pending |
| 12 | `get_repair_cost_analysis` | `get_job_repair_costs` | ⏳ Pending |
| 13 | `get_stale_tables` | `get_table_freshness` | ⏳ Pending |
| 14 | `get_quality_check_failures` | `get_tables_failing_quality` | ⏳ Pending |
| 15 | `get_table_activity_summary` | `get_table_activity_status` | ⏳ Pending |

---

## 🎯 Files Being Updated

- [ ] security_auditor_genie_export.json (Fixes 1-5)
- [ ] performance_genie_export.json (Fixes 6-8)
- [ ] job_health_monitor_genie_export.json (Fixes 9-12)
- [ ] data_quality_monitor_genie_export.json (Fixes 13-15)
- [ ] unified_health_monitor_genie_export.json (Multiple fixes)
- [ ] cost_intelligence_genie_export.json (None expected)

---

## 📊 Progress
**Completed:** 0/15  
**In Progress:** 1/15  
**Pending:** 14/15


