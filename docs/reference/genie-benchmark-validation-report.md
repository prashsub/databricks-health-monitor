# Genie Space Benchmark SQL Validation Report

> **Generated:** 2026-01-07  
> **Validated Against:** `docs/actual_assets.md`  
> **Status:** 🔴 **Multiple Critical Discrepancies Found**

---

## Executive Summary

| Genie Space | TVF Issues | ML Table Issues | Metric View Issues | Monitoring Table Issues |
|-------------|-----------|-----------------|-------------------|------------------------|
| Cost Intelligence | 🔴 9 missing TVFs | ✅ All correct | ✅ All correct | ✅ All correct |
| Data Quality Monitor | 🔴 5 missing/wrong TVFs | 🔴 2 wrong names | ✅ All correct | 🔴 3 missing tables |
| Job Health Monitor | 🔴 9 missing/wrong TVFs | ✅ All correct | ✅ All correct | ✅ All correct |
| Performance | 🔴 15 missing/wrong TVFs | 🔴 5 wrong names | ✅ All correct | ✅ All correct |
| Security Auditor | 🔴 6 missing/wrong TVFs | 🔴 4 wrong names | ✅ All correct | ✅ All correct |
| Unified Health Monitor | 🔴 Inherits all issues | 🔴 Inherits all issues | ✅ All correct | ✅ All correct |

**Total Issues:** 44+ asset reference mismatches requiring correction

---

## 1. Cost Intelligence Genie (`cost_intelligence_genie.md`)

### ✅ Correct Assets

| Asset Type | Referenced | Actual | Status |
|------------|-----------|--------|--------|
| **Metric Views** | | | |
| `mv_cost_analytics` | ✅ | `mv_cost_analytics` | ✅ Match |
| `mv_commit_tracking` | ✅ | `mv_commit_tracking` | ✅ Match |
| **ML Tables** | | | |
| `cost_anomaly_predictions` | ✅ | `cost_anomaly_predictions` | ✅ Match |
| `budget_forecast_predictions` | ✅ | `budget_forecast_predictions` | ✅ Match |
| `job_cost_optimizer_predictions` | ✅ | `job_cost_optimizer_predictions` | ✅ Match |
| `chargeback_predictions` | ✅ | `chargeback_predictions` | ✅ Match |
| `commitment_recommendations` | ✅ | `commitment_recommendations` | ✅ Match |
| `tag_recommendations` | ✅ | `tag_recommendations` | ✅ Match |
| **Monitoring Tables** | | | |
| `fact_usage_profile_metrics` | ✅ | `fact_usage_profile_metrics` | ✅ Match |
| `fact_usage_drift_metrics` | ✅ | `fact_usage_drift_metrics` | ✅ Match |

### 🔴 TVF Discrepancies (9 Issues)

| Referenced TVF | Actual TVF | Issue | Affected Questions |
|---------------|------------|-------|-------------------|
| `get_daily_cost_summary` | **NOT DEPLOYED** | Missing | Q11 |
| `get_workspace_cost_comparison` | **NOT DEPLOYED** | Missing | Q6 (TVF section) |
| `get_serverless_vs_classic_cost` | **NOT DEPLOYED** | Missing | Q10 |
| `get_job_cost_breakdown` | `get_most_expensive_jobs` | Wrong name | Q15 |
| `get_warehouse_cost_analysis` | **NOT DEPLOYED** | Missing | Q19 |
| `get_cost_forecast` | `get_cost_forecast_summary` | Wrong name | Q12, Deep Q25 |
| `get_cost_by_cluster_type` | `get_all_purpose_cluster_cost` | Wrong name | Q17 |
| `get_storage_cost_analysis` | **NOT DEPLOYED** | Missing | TVF section |
| `get_cost_efficiency_metrics` | **NOT DEPLOYED** | Missing | TVF section |

### 🔴 Benchmark SQL Corrections Needed

**Q11 - get_daily_cost_summary:**
```sql
-- ❌ Current (references non-existent TVF):
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_daily_cost_summary(...))

-- ✅ Fix: Use metric view instead:
SELECT 
  usage_date,
  MEASURE(total_cost) as daily_cost,
  LAG(MEASURE(total_cost)) OVER (ORDER BY usage_date) as prev_day_cost
FROM ${catalog}.${gold_schema}.mv_cost_analytics
WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
GROUP BY usage_date
ORDER BY usage_date DESC;
```

**Q15 - get_job_cost_breakdown:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_cost_breakdown(...))

-- ✅ Fix: Use actual TVF name:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_most_expensive_jobs(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  20
));
```

---

## 2. Data Quality Monitor Genie (`data_quality_monitor_genie.md`)

### ✅ Correct Assets

| Asset Type | Referenced | Actual | Status |
|------------|-----------|--------|--------|
| **Metric Views** | | | |
| `mv_data_quality` | ✅ | `mv_data_quality` | ✅ Match |
| `mv_ml_intelligence` | ✅ | `mv_ml_intelligence` | ✅ Match |

### 🔴 TVF Discrepancies (5 Issues)

| Referenced TVF | Actual TVF | Issue | Affected Questions |
|---------------|------------|-------|-------------------|
| `get_stale_tables(days_back, staleness_threshold_days)` | `get_table_freshness(freshness_threshold_hours)` | Wrong name & signature | Q2, Q10, Deep Q21-24 |
| `get_table_lineage(catalog, schema)` | `get_pipeline_data_lineage(days_back, entity_filter)` | Wrong name & signature | Q10 |
| `get_table_activity_summary(days_back)` | `get_table_activity_status(days_back, inactive_threshold_days)` | Wrong name & signature | Q4, Q5, Q6, Q8, Q11, Deep Q21-24 |
| `get_data_lineage_summary(catalog, schema)` | **NOT DEPLOYED** | Missing | Q10, Deep Q23 |
| `get_pipeline_lineage_impact(catalog)` | **NOT DEPLOYED** | Missing | TVF section |

### 🔴 ML Table Discrepancies (2 Issues)

| Referenced Table | Actual Table | Issue |
|-----------------|--------------|-------|
| `quality_anomaly_predictions` | `data_drift_predictions` | Wrong name |
| `freshness_alert_predictions` | `freshness_predictions` | Wrong name |

### 🔴 Lakehouse Monitoring Table Discrepancies (3 Issues)

| Referenced Table | Actual Table | Issue |
|-----------------|--------------|-------|
| `fact_table_quality_profile_metrics` | **NOT DEPLOYED** | Missing (only `fact_table_lineage_profile_metrics` exists) |
| `fact_governance_metrics_profile_metrics` | **NOT DEPLOYED** | Missing |
| `fact_table_quality_drift_metrics` | **NOT DEPLOYED** | Missing |

### 🔴 Benchmark SQL Corrections Needed

**Q2 - get_stale_tables:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_stale_tables(7, 24))

-- ✅ Fix: Use actual TVF:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_table_freshness(24))
WHERE hours_since_update > 24
ORDER BY hours_since_update DESC
LIMIT 20;
```

**Q14 - quality_anomaly_predictions:**
```sql
-- ❌ Current:
SELECT ... FROM ${catalog}.${feature_schema}.quality_anomaly_predictions

-- ✅ Fix: Use actual table name:
SELECT 
  table_name,
  prediction as drift_score,
  evaluation_date
FROM ${catalog}.${feature_schema}.data_drift_predictions
WHERE prediction > 0.5
ORDER BY prediction DESC
LIMIT 20;
```

**Q16 - freshness_alert_predictions:**
```sql
-- ❌ Current:
SELECT ... FROM ${catalog}.${feature_schema}.freshness_alert_predictions

-- ✅ Fix: Use actual table name:
SELECT 
  table_name,
  prediction as staleness_probability,
  evaluation_date
FROM ${catalog}.${feature_schema}.freshness_predictions
WHERE prediction > 0.7
ORDER BY prediction DESC
LIMIT 20;
```

---

## 3. Job Health Monitor Genie (`job_health_monitor_genie.md`)

### ✅ Correct Assets

| Asset Type | Referenced | Actual | Status |
|------------|-----------|--------|--------|
| **Metric Views** | | | |
| `mv_job_performance` | ✅ | `mv_job_performance` | ✅ Match |
| **ML Tables** | | | |
| `job_failure_predictions` | ✅ | `job_failure_predictions` | ✅ Match |
| `duration_predictions` | ✅ | `duration_predictions` | ✅ Match |
| `sla_breach_predictions` | ✅ | `sla_breach_predictions` | ✅ Match |
| `retry_success_predictions` | ✅ | `retry_success_predictions` | ✅ Match |
| `pipeline_health_predictions` | ✅ | `pipeline_health_predictions` | ✅ Match |
| **Monitoring Tables** | | | |
| `fact_job_run_timeline_profile_metrics` | ✅ | ✅ Match |
| `fact_job_run_timeline_drift_metrics` | ✅ | ✅ Match |

### 🔴 TVF Discrepancies (9 Issues)

| Referenced TVF | Actual TVF | Issue | Affected Questions |
|---------------|------------|-------|-------------------|
| `get_failed_jobs_summary(days_back, min_failures)` | `get_failed_jobs(start_date, end_date, workspace_filter)` | Wrong name & signature | Q4, Q7 |
| `get_job_success_rates(start_date, end_date, min_runs)` | `get_job_success_rate(start_date, end_date, min_runs)` | Wrong name (plural vs singular) | Q7 |
| `get_job_duration_trends(start_date, end_date)` | **NOT DEPLOYED** | Missing | TVF section |
| `get_job_failure_patterns(days_back)` | **NOT DEPLOYED** | Missing | Q8 |
| `get_long_running_jobs(days_back, threshold)` | **NOT DEPLOYED** | Missing | Q9 |
| `get_pipeline_health(days_back)` | **NOT DEPLOYED** | Missing | Q14, TVF section |
| `get_job_schedule_drift(days_back)` | **NOT DEPLOYED** | Missing | TVF section |
| `get_repair_cost_analysis(start_date, end_date)` | `get_job_repair_costs(start_date, end_date, top_n)` | Wrong name | Q12 |
| `get_job_failure_cost(start_date, end_date)` | `get_job_failure_costs(start_date, end_date, top_n)` | Wrong name (plural) | TVF section |

### 🔴 Benchmark SQL Corrections Needed

**Q4 - get_failed_jobs_summary:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(1, 1))

-- ✅ Fix: Use actual TVF with correct signature:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs(
  (CURRENT_DATE() - INTERVAL 1 DAY)::STRING,
  CURRENT_DATE()::STRING,
  NULL  -- workspace_filter
))
ORDER BY failure_count DESC
LIMIT 20;
```

**Q7 - get_job_success_rates:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rates(...))

-- ✅ Fix: Correct function name (singular):
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rate(
  (CURRENT_DATE() - INTERVAL 30 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  5
))
ORDER BY success_rate ASC
LIMIT 10;
```

---

## 4. Performance Genie (`performance_genie.md`)

### ✅ Correct Assets

| Asset Type | Referenced | Actual | Status |
|------------|-----------|--------|--------|
| **Metric Views** | | | |
| `mv_query_performance` | ✅ | `mv_query_performance` | ✅ Match |
| `mv_cluster_utilization` | ✅ | `mv_cluster_utilization` | ✅ Match |
| `mv_cluster_efficiency` | ✅ | `mv_cluster_efficiency` | ✅ Match |
| **ML Tables** | | | |
| `cache_hit_predictions` | ✅ | `cache_hit_predictions` | ✅ Match |

### 🔴 TVF Discrepancies (15 Issues)

| Referenced TVF | Actual TVF | Issue |
|---------------|------------|-------|
| `get_slowest_queries(days_back, threshold)` | `get_slow_queries(start_date, end_date, duration_threshold_seconds, top_n)` | Wrong name & signature |
| `get_warehouse_performance(start_date, end_date)` | `get_warehouse_utilization(start_date, end_date)` | Wrong name |
| `get_top_users_by_query_count(...)` | `get_user_query_summary(start_date, end_date, top_n)` | Wrong name |
| `get_query_efficiency_by_user(...)` | **NOT DEPLOYED** | Missing |
| `get_query_queue_analysis(...)` | **NOT DEPLOYED** | Missing |
| `get_failed_queries_summary(days_back)` | `get_failed_queries(start_date, end_date, top_n)` | Wrong name & signature |
| `get_cache_hit_analysis(days_back)` | **NOT DEPLOYED** | Missing |
| `get_spill_analysis(days_back)` | `get_high_spill_queries(start_date, end_date, min_spill_gb)` | Wrong name & signature |
| `get_cluster_rightsizing_recommendations(days_back)` | `get_cluster_right_sizing_recommendations(days_back, min_observation_hours)` | Wrong name (hyphen vs no hyphen) |
| `get_autoscaling_disabled_jobs(days_back)` | `get_jobs_without_autoscaling(days_back)` | Wrong name |
| `get_legacy_dbr_jobs(days_back)` | `get_jobs_on_legacy_dbr(days_back)` | Wrong name |
| `get_cluster_cost_by_type(...)` | `get_all_purpose_cluster_cost(start_date, end_date, top_n)` | Wrong name |
| `get_cluster_uptime_analysis(...)` | **NOT DEPLOYED** | Missing |
| `get_cluster_scaling_events(...)` | **NOT DEPLOYED** | Missing |
| `get_cluster_efficiency_metrics(...)` | **NOT DEPLOYED** | Missing |
| `get_node_utilization_by_cluster(...)` | **NOT DEPLOYED** | Missing |

### 🔴 ML Table Discrepancies (5 Issues)

| Referenced Table | Actual Table | Issue |
|-----------------|--------------|-------|
| `query_optimization_classifications` | `query_optimization_predictions` | Wrong name |
| `query_optimization_recommendations` | **NOT DEPLOYED** | Missing |
| `job_duration_predictions` | `duration_predictions` | Wrong name |
| `cluster_capacity_recommendations` | `cluster_capacity_predictions` | Wrong name |
| `cluster_rightsizing_recommendations` | **NOT DEPLOYED** | Missing |
| `dbr_migration_risk_scores` | `dbr_migration_predictions` | Wrong name |

### 🔴 Benchmark SQL Corrections Needed

**Q5 - get_slowest_queries:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_slowest_queries(1, 30))

-- ✅ Fix: Use actual TVF with correct signature:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_slow_queries(
  (CURRENT_DATE() - INTERVAL 1 DAY)::STRING,
  CURRENT_DATE()::STRING,
  30,  -- duration_threshold_seconds
  20   -- top_n
))
ORDER BY duration_seconds DESC;
```

**Q7 - get_warehouse_performance:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_warehouse_performance(...))

-- ✅ Fix: Use actual TVF name:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_warehouse_utilization(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING
))
ORDER BY query_count DESC
LIMIT 10;
```

**Q16 - get_cluster_rightsizing_recommendations:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cluster_rightsizing_recommendations(30))

-- ✅ Fix: Use actual TVF name (with hyphen):
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_cluster_right_sizing_recommendations(
  30,  -- days_back
  10   -- min_observation_hours
))
ORDER BY potential_savings DESC
LIMIT 15;
```

**Q17 - query_optimization_classifications:**
```sql
-- ❌ Current:
SELECT ... FROM ${catalog}.${feature_schema}.query_optimization_classifications

-- ✅ Fix: Use actual table name:
SELECT
  query_hash,
  prediction as optimization_score
FROM ${catalog}.${feature_schema}.query_optimization_predictions
WHERE prediction > 0.7
ORDER BY prediction DESC
LIMIT 20;
```

---

## 5. Security Auditor Genie (`security_auditor_genie.md`)

### ✅ Correct Assets

| Asset Type | Referenced | Actual | Status |
|------------|-----------|--------|--------|
| **Metric Views** | | | |
| `mv_security_events` | ✅ | `mv_security_events` | ✅ Match |
| `mv_governance_analytics` | ✅ | `mv_governance_analytics` | ✅ Match |
| **Monitoring Tables** | | | |
| `fact_audit_logs_profile_metrics` | ✅ | ✅ Match |
| `fact_audit_logs_drift_metrics` | ✅ | ✅ Match |

### 🔴 TVF Discrepancies (6 Issues)

| Referenced TVF | Actual TVF | Issue | Affected Questions |
|---------------|------------|-------|-------------------|
| `get_service_account_activity(days_back)` | `get_service_account_audit(days_back)` | Wrong name | Q16 |
| `get_failed_access_attempts(days_back)` | `get_failed_actions(start_date, end_date, user_filter)` | Wrong name & signature | Q7 |
| `get_sensitive_data_access(start_date, end_date)` | `get_sensitive_table_access(start_date, end_date, table_pattern)` | Wrong name & signature | Q6, Deep Q22, Q24, Q25 |
| `get_unusual_access_patterns(days_back)` | **NOT DEPLOYED** | Missing | Q9, Deep Q21 |
| `get_data_export_events(days_back)` | **NOT DEPLOYED** | Missing | Q13 |
| `get_user_risk_scores(days_back)` (TVF) | **NOT DEPLOYED** (this is an ML table only) | Missing | TVF section |

### 🔴 ML Table Discrepancies (4 Issues)

| Referenced Table | Actual Table | Issue |
|-----------------|--------------|-------|
| `access_anomaly_predictions` | `security_threat_predictions` | Wrong name |
| `user_risk_scores` | `user_behavior_predictions` | Wrong name |
| `access_classifications` | **NOT DEPLOYED** | Missing |
| `off_hours_baseline_predictions` | **NOT DEPLOYED** | Missing |

### 🔴 Benchmark SQL Corrections Needed

**Q7 - get_failed_access_attempts:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_access_attempts(7))

-- ✅ Fix: Use actual TVF with correct signature:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_actions(
  (CURRENT_DATE() - INTERVAL 7 DAYS)::STRING,
  CURRENT_DATE()::STRING,
  NULL  -- user_filter
))
ORDER BY failed_count DESC
LIMIT 20;
```

**Q16 - get_service_account_activity:**
```sql
-- ❌ Current:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_service_account_activity(30))

-- ✅ Fix: Use actual TVF name:
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_service_account_audit(30))
ORDER BY event_count DESC
LIMIT 20;
```

**Q17 - access_anomaly_predictions:**
```sql
-- ❌ Current:
SELECT ... FROM ${catalog}.${feature_schema}.access_anomaly_predictions

-- ✅ Fix: Use actual table name:
SELECT
  user_identity,
  prediction as threat_score,
  event_date
FROM ${catalog}.${feature_schema}.security_threat_predictions
WHERE prediction < -0.5
ORDER BY prediction ASC
LIMIT 20;
```

**Q18 - user_risk_scores:**
```sql
-- ❌ Current:
SELECT ... FROM ${catalog}.${feature_schema}.user_risk_scores

-- ✅ Fix: Use actual table name:
SELECT
  user_identity,
  prediction as risk_level,
  evaluation_date
FROM ${catalog}.${feature_schema}.user_behavior_predictions
WHERE prediction >= 4
ORDER BY prediction DESC
LIMIT 20;
```

---

## 6. Unified Health Monitor Genie (`unified_health_monitor_genie.md`)

This space inherits issues from all other spaces. Key issues:

### 🔴 Critical Issues
- References all the incorrect TVF names from domain-specific spaces
- References incorrect ML table names
- Many benchmark queries will fail

### Specific Issues Requiring Fixes
- Q7: Uses `get_failed_jobs_summary` → should use `get_failed_jobs`
- Q8: Uses `get_slowest_queries` → should use `get_slow_queries`
- Q10: Uses `get_stale_tables` → should use `get_table_freshness`
- Q13: Uses `get_warehouse_performance` → should use `get_warehouse_utilization`
- Q14: Uses `get_pipeline_health` → **NOT DEPLOYED**
- Q15: Uses `get_underutilized_clusters` → signature needs verification
- Q17: Uses `get_stale_tables` → should use `get_table_freshness`
- Q20: Uses `get_cluster_rightsizing_recommendations` → should use `get_cluster_right_sizing_recommendations`
- Deep Q22: Uses multiple non-existent TVFs
- Deep Q23: Uses `get_sensitive_data_access`, `get_off_hours_access` → wrong names

---

## Summary: Required Corrections

### TVFs to Rename (Pattern Fixes)

| Pattern | Fix |
|---------|-----|
| `get_*_summary` | Check if actual name is different |
| `get_slowest_queries` | → `get_slow_queries` |
| `get_warehouse_performance` | → `get_warehouse_utilization` |
| `get_*_rightsizing_*` | → `get_*_right_sizing_*` (with hyphen) |
| `get_failed_jobs_summary` | → `get_failed_jobs` |
| `get_job_success_rates` | → `get_job_success_rate` (singular) |
| `get_stale_tables` | → `get_table_freshness` |
| `get_service_account_activity` | → `get_service_account_audit` |

### ML Tables to Rename

| Referenced | Actual |
|-----------|--------|
| `quality_anomaly_predictions` | `data_drift_predictions` |
| `freshness_alert_predictions` | `freshness_predictions` |
| `access_anomaly_predictions` | `security_threat_predictions` |
| `user_risk_scores` | `user_behavior_predictions` |
| `query_optimization_classifications` | `query_optimization_predictions` |
| `job_duration_predictions` | `duration_predictions` |
| `cluster_capacity_recommendations` | `cluster_capacity_predictions` |
| `dbr_migration_risk_scores` | `dbr_migration_predictions` |

### TVFs That Don't Exist (Need Alternative Queries)

These TVFs are referenced but NOT deployed - benchmark queries must be rewritten using metric views or fact tables:

1. `get_daily_cost_summary` - Use `mv_cost_analytics` GROUP BY date
2. `get_workspace_cost_comparison` - Use `mv_cost_analytics` GROUP BY workspace
3. `get_serverless_vs_classic_cost` - Use `mv_cost_analytics` with is_serverless filter
4. `get_job_duration_trends` - Use `mv_job_performance` GROUP BY date
5. `get_job_failure_patterns` - Use `mv_job_performance` GROUP BY termination_code
6. `get_long_running_jobs` - Use `mv_job_performance` with duration filter
7. `get_pipeline_health` - Use `pipeline_health_predictions` ML table
8. `get_job_schedule_drift` - Not available
9. `get_query_efficiency_by_user` - Use `mv_query_performance` GROUP BY user
10. `get_query_queue_analysis` - Use `mv_query_performance` with queue metrics
11. `get_cache_hit_analysis` - Use `mv_query_performance` cache_hit_rate
12. `get_cluster_uptime_analysis` - Use `mv_cluster_utilization`
13. `get_cluster_scaling_events` - Not available
14. `get_cluster_efficiency_metrics` - Use `mv_cluster_efficiency`
15. `get_node_utilization_by_cluster` - Use `mv_cluster_utilization` GROUP BY cluster
16. `get_data_lineage_summary` - Use `mv_governance_analytics`
17. `get_pipeline_lineage_impact` - Not available
18. `get_unusual_access_patterns` - Use `security_threat_predictions` ML table
19. `get_data_export_events` - Not available

### Lakehouse Monitoring Tables That Don't Exist

| Referenced | Status | Alternative |
|-----------|--------|-------------|
| `fact_table_quality_profile_metrics` | NOT DEPLOYED | Use `fact_table_lineage_profile_metrics` |
| `fact_governance_metrics_profile_metrics` | NOT DEPLOYED | Use `mv_governance_analytics` |
| `fact_table_quality_drift_metrics` | NOT DEPLOYED | Not available |

---

## Recommended Action Plan

### Priority 1: Critical Fixes (Blocking)
1. **Rename TVF references** in all Genie spaces to match actual deployed names
2. **Rename ML table references** to match actual deployed names
3. **Update signatures** for TVFs with different parameter lists

### Priority 2: Rewrite Missing TVF Queries
1. Replace missing TVF calls with equivalent metric view queries
2. Document which benchmark questions need alternative approaches
3. Update benchmark expected results

### Priority 3: Align Documentation
1. Update `docs/actual_assets.md` if new assets are deployed
2. Or deploy missing TVFs to match Genie space requirements
3. Ensure TVF and ML table inventories match actual deployments

---

## References

- **Actual Assets Inventory:** `docs/actual_assets.md`
- **Cost Genie:** `src/genie/cost_intelligence_genie.md`
- **Data Quality Genie:** `src/genie/data_quality_monitor_genie.md`
- **Job Health Genie:** `src/genie/job_health_monitor_genie.md`
- **Performance Genie:** `src/genie/performance_genie.md`
- **Security Genie:** `src/genie/security_auditor_genie.md`
- **Unified Genie:** `src/genie/unified_health_monitor_genie.md`


