# Genie ML Table Name Validation Against Deployed Assets

**Date:** January 7, 2026  
**Source:** `docs/actual_assets.md` - Section 1: ML Prediction Tables  
**Total TABLE_NOT_FOUND Errors:** ~5

---

## ✅ ML Tables That EXIST (22 total)

From `docs/actual_assets.md`:

| Table Name | Status |
|------------|--------|
| `budget_forecast_predictions` | ✅ Exists |
| `cache_hit_predictions` | ✅ Exists |
| `chargeback_predictions` | ✅ Exists |
| `cluster_capacity_predictions` | ✅ Exists |
| `commitment_recommendations` | ✅ Exists |
| `cost_anomaly_predictions` | ✅ Exists |
| `data_drift_predictions` | ✅ Exists |
| `dbr_migration_predictions` | ✅ Exists |
| `duration_predictions` | ✅ Exists |
| `exfiltration_predictions` | ✅ Exists |
| `freshness_predictions` | ✅ Exists |
| `job_cost_optimizer_predictions` | ✅ Exists |
| `job_failure_predictions` | ✅ Exists |
| `performance_regression_predictions` | ✅ Exists |
| `pipeline_health_predictions` | ✅ Exists |
| `privilege_escalation_predictions` | ✅ Exists |
| `query_optimization_predictions` | ✅ Exists |
| `query_performance_predictions` | ✅ Exists |
| `retry_success_predictions` | ✅ Exists |
| `security_threat_predictions` | ✅ Exists |
| `sla_breach_predictions` | ✅ Exists |
| `tag_recommendations` | ✅ Exists |
| `user_behavior_predictions` | ✅ Exists |
| `warehouse_optimizer_predictions` | ✅ Exists |

---

## ❌ ML Table Name Issues in Genie Files

### 🔴 WRONG NAMES (need fixes) - 5 issues

#### 1. `security_anomaly_predictions` → `security_threat_predictions`

**Genie Spaces:** security_auditor, unified_health_monitor  
**Current (Wrong):** `security_anomaly_predictions`  
**Correct Name:** `security_threat_predictions`

**Fix:**
```json
"${catalog}.${feature_schema}.security_anomaly_predictions"
→
"${catalog}.${feature_schema}.security_threat_predictions"
```

---

#### 2. `query_optimization_classifications` → `query_optimization_predictions`

**Genie Space:** performance  
**Current (Wrong):** `query_optimization_classifications`  
**Correct Name:** `query_optimization_predictions`

**Fix:**
```json
"${catalog}.${feature_schema}.query_optimization_classifications"
→
"${catalog}.${feature_schema}.query_optimization_predictions"
```

---

#### 3. `cluster_rightsizing_recommendations` → `cluster_capacity_predictions`

**Genie Spaces:** performance, unified_health_monitor  
**Current (Wrong):** `cluster_rightsizing_recommendations`  
**Correct Name:** `cluster_capacity_predictions`

**Fix:**
```json
"${catalog}.${feature_schema}.cluster_rightsizing_recommendations"
→
"${catalog}.${feature_schema}.cluster_capacity_predictions"
```

---

#### 4. `query_optimization_recommendations` → `query_optimization_predictions`

**Genie Space:** performance  
**Current (Wrong):** `query_optimization_recommendations`  
**Correct Name:** `query_optimization_predictions` (same as #2)

**Fix:**
```json
"${catalog}.${feature_schema}.query_optimization_recommendations"
→
"${catalog}.${feature_schema}.query_optimization_predictions"
```

---

#### 5. `freshness_alert_predictions` → `freshness_predictions`

**Genie Space:** data_quality_monitor  
**Current (Wrong):** `freshness_alert_predictions`  
**Correct Name:** `freshness_predictions`

**Fix:**
```json
"${catalog}.${feature_schema}.freshness_alert_predictions"
→
"${catalog}.${feature_schema}.freshness_predictions"
```

---

### 🔴 NON-EXISTENT TABLES (need removal/rewrite) - 4 issues

These tables do NOT exist in the deployed ML schema and need to be removed from queries or replaced with valid tables:

#### 1. `access_anomaly_predictions` ❌

**Genie Space:** security_auditor, unified_health_monitor  
**Status:** DOES NOT EXIST  
**Possible Alternatives:**  
- `user_behavior_predictions` (general behavior anomalies)  
- `privilege_escalation_predictions` (security-specific)  
- `security_threat_predictions` (general security threats)

**Action:** Replace with `user_behavior_predictions` (most relevant)

---

#### 2. `user_risk_scores` ❌

**Genie Space:** security_auditor, unified_health_monitor  
**Status:** DOES NOT EXIST (not an ML prediction table)  
**Action:** Remove queries or replace with `user_behavior_predictions`

---

#### 3. `access_classifications` ❌

**Genie Space:** security_auditor  
**Status:** DOES NOT EXIST  
**Action:** Remove queries or replace with `user_behavior_predictions`

---

#### 4. `off_hours_baseline_predictions` ❌

**Genie Space:** security_auditor  
**Status:** DOES NOT EXIST  
**Action:** Remove queries or replace with `user_behavior_predictions`

---

## 📋 Fix Summary

| Issue Type | Count | Action |
|------------|-------|--------|
| **Wrong Names** | 5 | Rename via search_replace |
| **Non-Existent** | 4 | Remove or replace with valid tables |
| **Total Issues** | 9 | Systematic fixes |

---

## 🎯 Bulk Fix Plan

### Phase 1: Rename Existing Tables (5 fixes)

```bash
# 1. security_anomaly_predictions → security_threat_predictions
# 2. query_optimization_classifications → query_optimization_predictions
# 3. cluster_rightsizing_recommendations → cluster_capacity_predictions
# 4. query_optimization_recommendations → query_optimization_predictions
# 5. freshness_alert_predictions → freshness_predictions
```

### Phase 2: Handle Non-Existent Tables (4 fixes)

```bash
# 1. access_anomaly_predictions → user_behavior_predictions
# 2. user_risk_scores → Remove or replace with user_behavior_predictions
# 3. access_classifications → Remove or replace with user_behavior_predictions
# 4. off_hours_baseline_predictions → Remove or replace with user_behavior_predictions
```

---

## ✅ Next Steps

1. ✅ Apply Phase 1 renames (5 fixes)
2. ✅ Apply Phase 2 replacements (4 fixes)
3. ✅ Redeploy bundle
4. ✅ Run validation job
5. ✅ Verify TABLE_NOT_FOUND errors eliminated


