# Genie Space Column Error Fixes Report

**Date:** Thu Jan  8 15:10:44 CST 2026
**Total Fixes Applied:** 13
**Files Modified:** 5

## Fixes Applied:

- **d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a6:** `sc.total_sku_cost` → `total_cost`
- **4002051c4693c098dfb4fb218342f9a1:** `p99_duration` → `p99_duration_seconds`
- **def0123456789abcdef0123456789abc:** `failed_count` → `failed_events`
- **0123456789abcdef0123456789abcdef:** `risk_level` → `audit_level`
- **56789abcdef0123456789abcdef01234:** `unique_data_consumers` → `unique_actions`
- **6789abcdef0123456789abcdef012345:** `event_count` → `total_events`
- **f0e9a9f44dbdea8ed766d4c0b95f3363:** `success_rate` → `successful_events`
- **a38b9b6611cb8a91a1cdb69250c58aa2:** `risk_level` → `audit_level`
- **2f5e00f43b399b047a61bc3b17897379:** `cost_7d` → `last_7_day_cost`
- **3946480a0fa84c8688d18d931eb63a2b:** `failure_count` → `failed_runs`
- **b4edc0312c5e4aeba8d68235f45a86f7:** `failure_count` → `failed_runs`
- **c04f050ba8c54743bbc75a9c68ad1709:** `deviation_score` → `termination_code`
- **15e71a6f8bf14fceb6a2774bf574ad65:** `ft.run_date` → `run_date`

## Files Modified:

- `src/genie/cost_intelligence_genie_export.json`
- `src/genie/job_health_monitor_genie_export.json`
- `src/genie/performance_genie_export.json`
- `src/genie/security_auditor_genie_export.json`
- `src/genie/unified_health_monitor_genie_export.json`

## Next Steps:

1. Deploy bundle: `databricks bundle deploy -t dev`
2. Re-run validation: `databricks bundle run -t dev genie_benchmark_sql_validation_job`
3. Review remaining errors
