# Genie Space Remaining Fixes - Detailed Instructions

**Date:** 2026-01-07
**Status:** Partially Complete - Manual fixes needed for Performance, Security, and Unified

---

## ✅ COMPLETED (3/6 Genie Spaces)

1. **Cost Intelligence Genie** - All TVF names, signatures, and benchmark SQLs fixed
2. **Data Quality Monitor Genie** - All TVF names, ML tables, and benchmark SQLs fixed
3. **Job Health Monitor Genie** - All TVF names and signatures fixed

---

## ⚠️ PERFORMANCE GENIE - Remaining Fixes

### File: `src/genie/performance_genie.md`

### TVF Name Changes (Partially Complete)

**Query TVFs (10) - ✅ DONE:**
- ✅ `get_slowest_queries` → `get_slow_queries`
- ✅ `get_query_latency_percentiles` → `get_query_duration_percentiles`
- ✅ `get_warehouse_performance` → `get_warehouse_utilization`
- ✅ `get_query_volume_trends` → `get_query_volume_by_hour`
- ✅ `get_top_users_by_query_count` → `get_top_query_users`
- ✅ `get_query_efficiency_by_user` → `get_user_query_efficiency`
- ✅ `get_query_queue_analysis` → `get_warehouse_queue_analysis`
- ✅ `get_failed_queries_summary` → `get_failed_queries`
- ✅ `get_cache_hit_analysis` → `get_query_cache_analysis`
- ✅ `get_spill_analysis` → `get_query_spill_analysis`

**Cluster TVFs (11) - ⚠️ NEEDS COMPLETION:**

Find and replace these in the TVF signature section (around line 315-325):

```markdown
# OLD → NEW
get_cluster_utilization → get_cluster_resource_utilization
get_cluster_resource_metrics → get_cluster_efficiency_score  
get_underutilized_clusters → get_idle_clusters
get_cluster_rightsizing_recommendations → (Use ML table: cluster_rightsizing_recommendations)
get_autoscaling_disabled_jobs → get_jobs_without_autoscaling
get_legacy_dbr_jobs → get_jobs_on_old_dbr
get_cluster_cost_by_type → get_cluster_cost_analysis
get_cluster_uptime_analysis → get_cluster_uptime
get_cluster_scaling_events → get_autoscaling_events
get_cluster_efficiency_metrics → (Removed - use get_cluster_efficiency_score)
get_node_utilization_by_cluster → get_cluster_node_efficiency
```

**New TVFs Added:**
- `get_cluster_memory_pressure`
- `get_cluster_cpu_saturation`

### Benchmark SQL Fixes Needed

Search for these TVF calls in benchmark questions and update:

1. **Question 2:** `get_slowest_queries` → `get_slow_queries`
2. **Question 3:** `get_query_latency_percentiles` → `get_query_duration_percentiles`
3. **Question 4:** `get_warehouse_performance` → `get_warehouse_utilization`
4. **Question 5:** `get_query_volume_trends` → `get_query_volume_by_hour`
5. **Question 6:** `get_top_users_by_query_count` → `get_top_query_users`
6. **Question 7:** `get_query_efficiency_by_user` → `get_user_query_efficiency`
7. **Question 8:** `get_query_queue_analysis` → `get_warehouse_queue_analysis`
8. **Question 9:** `get_failed_queries_summary` → `get_failed_queries`
9. **Question 10:** `get_cache_hit_analysis` → `get_query_cache_analysis`
10. **Question 11:** `get_spill_analysis` → `get_query_spill_analysis`
11. **Question 12:** `get_cluster_utilization` → `get_cluster_resource_utilization`
12. **Question 13:** `get_underutilized_clusters` → `get_idle_clusters`
13. **Question 14:** `get_cluster_rightsizing_recommendations` → Use ML table
14. **Question 15:** `get_autoscaling_disabled_jobs` → `get_jobs_without_autoscaling`
15. **Question 16:** `get_legacy_dbr_jobs` → `get_jobs_on_old_dbr`

---

## ⚠️ SECURITY AUDITOR GENIE - All Fixes Needed

### File: `src/genie/security_auditor_genie.md`

### TVF Name Changes (10 fixes)

Find and replace in TVF list section:

```markdown
# OLD → NEW
get_user_activity_summary → get_user_activity
get_table_access_audit → get_table_access_events
get_permission_changes → get_permission_change_events
get_service_account_activity → get_service_principal_activity
get_failed_access_attempts → get_failed_authentication_events
get_sensitive_data_access → get_pii_access_events
get_unusual_access_patterns → get_anomalous_access_events
get_user_activity_patterns → get_off_hours_activity
get_data_export_events → get_data_exfiltration_events
get_user_risk_scores → (Use ML table: user_risk_scores)
```

### TVF Signature Updates

Update signatures (around line 150-200):

```markdown
get_user_activity(start_date STRING, end_date STRING, top_n INT DEFAULT 50)
get_table_access_events(start_date STRING, end_date STRING, table_filter STRING DEFAULT '%')
get_permission_change_events(start_date STRING, end_date STRING, entity_type STRING DEFAULT '%')
get_service_principal_activity(start_date STRING, end_date STRING)
get_failed_authentication_events(start_date STRING, end_date STRING, min_failures INT DEFAULT 3)
get_pii_access_events(start_date STRING, end_date STRING, sensitivity_level STRING DEFAULT 'HIGH')
get_anomalous_access_events(start_date STRING, end_date STRING, anomaly_threshold DOUBLE DEFAULT 2.0)
get_off_hours_activity(start_date STRING, end_date STRING, business_hours_start INT DEFAULT 8, business_hours_end INT DEFAULT 18)
get_data_exfiltration_events(start_date STRING, end_date STRING, volume_threshold_gb DOUBLE DEFAULT 10.0)
```

### ML Table Name Change

```markdown
# OLD → NEW
access_anomaly_predictions → security_anomaly_predictions
```

### Benchmark SQL Fixes (10+ queries)

Update all benchmark questions that reference the old TVF names.

---

## ⚠️ UNIFIED HEALTH MONITOR GENIE - Cascading Fixes

### File: `src/genie/unified_health_monitor_genie.md`

This Genie inherits ALL fixes from the other 5 domains. Apply cascading updates:

### Cost Domain References
- Apply all 9 TVF name changes from Cost Intelligence Genie
- Update all cost-related benchmark queries

### Reliability Domain References
- Apply all 9 TVF name changes from Job Health Monitor Genie
- Update all job/pipeline-related queries

### Performance Domain References
- Apply all 20 TVF name changes from Performance Genie
- Update all query/cluster-related queries

### Security Domain References
- Apply all 10 TVF name changes from Security Auditor Genie
- Update all security-related queries

### Quality Domain References
- Apply all 5 TVF name changes from Data Quality Monitor Genie
- Apply 2 ML table name changes
- Update all quality-related queries

### Cross-Domain Queries
- Update Deep Research queries that combine multiple domains
- Fix any queries that join across domains

---

## 🔧 MANUAL FIX PROCESS

### Step 1: Performance Genie
```bash
# Open file
code src/genie/performance_genie.md

# Find and replace (use editor's find/replace):
1. Search for "get_cluster_utilization" → Replace with "get_cluster_resource_utilization"
2. Search for "get_underutilized_clusters" → Replace with "get_idle_clusters"
3. Search for "get_legacy_dbr_jobs" → Replace with "get_jobs_on_old_dbr"
4. Search for "get_cluster_cost_by_type" → Replace with "get_cluster_cost_analysis"
5. Search for "get_cluster_uptime_analysis" → Replace with "get_cluster_uptime"
6. Search for "get_cluster_scaling_events" → Replace with "get_autoscaling_events"
7. Search for "get_autoscaling_disabled_jobs" → Replace with "get_jobs_without_autoscaling"

# Update signatures section manually
# Update all benchmark SQL queries
```

### Step 2: Security Auditor Genie
```bash
# Open file
code src/genie/security_auditor_genie.md

# Find and replace all 10 TVF names
# Update all signatures
# Update ML table name: access_anomaly_predictions → security_anomaly_predictions
# Update all benchmark queries
```

### Step 3: Unified Health Monitor Genie
```bash
# Open file
code src/genie/unified_health_monitor_genie.md

# Apply ALL fixes from other 5 Genies
# This is the most complex - requires careful review
# Update all cross-domain queries
```

---

## ✅ VALIDATION CHECKLIST

After completing manual fixes:

### Performance Genie
- [ ] All 20 TVF names updated in asset list
- [ ] All 20 TVF signatures updated
- [ ] All 20+ benchmark SQL queries updated
- [ ] ML table names verified (cache_hit_predictions, duration_predictions)
- [ ] No references to removed TVFs (get_cluster_rightsizing_recommendations, get_cluster_efficiency_metrics)

### Security Auditor Genie
- [ ] All 10 TVF names updated in asset list
- [ ] All 10 TVF signatures updated
- [ ] All 10+ benchmark SQL queries updated
- [ ] ML table name updated (access_anomaly_predictions → security_anomaly_predictions)
- [ ] No references to removed TVF (get_user_risk_scores - use ML table)

### Unified Health Monitor Genie
- [ ] All Cost Intelligence fixes applied (9 TVFs)
- [ ] All Job Health Monitor fixes applied (9 TVFs)
- [ ] All Performance fixes applied (20 TVFs)
- [ ] All Security fixes applied (10 TVFs)
- [ ] All Data Quality fixes applied (5 TVFs + 2 ML tables)
- [ ] All cross-domain queries updated
- [ ] All Deep Research queries updated
- [ ] No orphaned references to old asset names

---

## 📊 FINAL SUMMARY

| Genie Space | Status | TVF Fixes | ML Fixes | SQL Fixes |
|-------------|--------|-----------|----------|-----------|
| Cost Intelligence | ✅ Complete | 9/9 | 0/0 | 7/7 |
| Data Quality Monitor | ✅ Complete | 5/5 | 2/2 | 13/13 |
| Job Health Monitor | ✅ Complete | 9/9 | 0/0 | 12/12 |
| Performance | ⚠️ Partial | 14/20 | 2/2 | 0/20+ |
| Security Auditor | ❌ Pending | 0/10 | 0/1 | 0/10+ |
| Unified Health Monitor | ❌ Pending | 0/50+ | 0/3 | 0/20+ |
| **TOTAL** | **50%** | **37/103** | **4/6** | **32/82+** |

---

## 🎯 ESTIMATED TIME

- **Performance Genie:** 30 minutes (6 TVF names + 20 SQL queries)
- **Security Auditor Genie:** 20 minutes (10 TVF names + 10 SQL queries)
- **Unified Health Monitor Genie:** 60 minutes (cascading fixes + cross-domain queries)

**Total Remaining:** ~2 hours of manual editing

---

**Last Updated:** 2026-01-07
**Next Action:** Manual find/replace in remaining 3 Genie files


