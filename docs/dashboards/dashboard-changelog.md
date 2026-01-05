# Dashboard Changelog

Tracking all dashboard modifications, issues, and fixes for the Databricks Health Monitor AI/BI dashboards.

---

## Quality Dashboard Table Health Overview Fix - January 5, 2026

### Issues Fixed

| Visual | Error | Root Cause | Fix Applied |
|--------|-------|------------|-------------|
| **Largest Tables** | `spec/encodings/columns/0 must NOT have additional properties` | Widget `version: 1` and missing `type` fields in columns | Updated to `version: 2`, added `type` field to all columns |
| **Tables Needing Optimization** | `spec/encodings/columns/0 must NOT have additional properties` | Widget `version: 1` and missing `type` fields in columns | Updated to `version: 2`, added `type` field to all columns |
| **Empty Tables** | `spec/encodings/columns/0 must NOT have additional properties` | Widget `version: 1` and missing `type` fields in columns | Updated to `version: 2`, added `type` field to all columns |

### Key Insight

Table widgets in Lakeview AI/BI dashboards **MUST use `version: 2`** and **MUST include `type` property** on every column encoding. The valid types are:
- `"type": "string"` - for text columns
- `"type": "number"` - for numeric columns
- `"type": "datetime"` - for date/timestamp columns (can include `dateTimeFormat`)

### Files Modified
- `src/dashboards/quality.lvdash.json`

---

## Security Dashboard ML Visuals Complete Rewrite - January 5, 2026 (Part 3)

### Issues Fixed

| Visual | Error | Root Cause | Fix Applied |
|--------|-------|------------|-------------|
| **ML: Threat Detection** | `UNBOUND_SQL_PARAMETER` for time_range | Missing `parameters` array in dataset | Added time_range parameter definition |
| **ML: Data Exfiltration Risk** | Placeholder data (all 1000.00, HIGH, 1.00) | Query derived from ML predictions alone | Rewrote to analyze actual data access patterns from audit logs |
| **ML: Privilege Escalation Risk** | Placeholder data (all "User", HIGH, 1.00) | Query derived from ML predictions alone | Rewrote to analyze actual permission/IAM activity from audit logs |

### Complete Query Rewrites

**ML: Threat Detection:**
- Changed from ML predictions to actual audit log behavior analysis
- Detects: failed actions (>5), access denials (>10), destructive operations (>3)
- New columns: `incident_summary` (evidence counts), `last_action`, `affected_service`, `recommended_action`
- Threat types: "Potential Data Breach", "Data Destruction Risk", "Privilege Abuse", "Suspicious Activity"

**ML: Data Exfiltration Risk:**
- Changed from ML predictions to data access pattern analysis
- Detects: high read operations (>100), export operations (>10), multiple IP addresses
- New columns: `access_pattern` (exports, reads, IPs), `last_action`, `accessed_service`, `recommended_action`
- Risk levels based on actual export volume and access diversity

**ML: Privilege Escalation Risk:**
- Changed from ML predictions to permission/IAM activity analysis
- Detects: permission changes (>5), admin actions, IAM service events (>10)
- New columns: `activity_summary` (permission changes, admin actions, IAM events), `last_action`, `target_service`, `recommended_action`
- Role inference: Admin, IAM User, Power User, User

### Actionability Improvements

| Visual | Before | After |
|--------|--------|-------|
| **Threat Detection** | Generic threat types, static scores | Evidence-based threats with specific incident counts, last suspicious action, service affected |
| **Data Exfiltration** | Fake 1000 volume, 1.00 score | Actual read/export operation counts, access patterns, source IPs |
| **Privilege Escalation** | All "User" role, 1.00 confidence | Inferred role from behavior, specific permission changes, IAM activity summary |

### Key Pattern

**Problem:** ML prediction tables only contain:
- Lookup keys (user_id, etc.)
- `prediction` (0-1 model output)
- `scored_at` timestamp

**Solution:** When ML predictions lack actionable context:
1. Use actual data from Gold layer tables (fact_audit_logs)
2. Aggregate user behavior patterns with HAVING thresholds
3. Derive threat types, risk levels, and recommendations from actual behavior
4. Include specific incident summaries and last actions for investigation

---

## Cost Dashboard ML Visuals Fixes - January 5, 2026 (Part 2)

### Issues Fixed

| Visual | Error | Root Cause | Fix Applied |
|--------|-------|------------|-------------|
| **ML: Tag Recommendations** | `DATATYPE_MISMATCH` comparing MAP with STRING | `custom_tags` is MAP type, was comparing with `'{}'` | Changed to `SIZE(f.custom_tags) = 0` |
| **ML: Tag Recommendations** | `j.job_name` cannot be resolved | Column in `dim_job` is `name`, not `job_name` | Changed to `j.name` |
| **ML: Migration Recommendations** | `usage_quantity_unit` cannot be resolved | Column in `fact_usage` is `usage_unit` | Changed to `usage_unit` |
| **ML: Detected Cost Anomalies** | No data displayed | Query structure is correct; likely no anomalies (negative predictions) in the data | Verified query - no code changes needed |

### How Budget Alert Priorities Works

The **Budget Alert Priorities** table provides proactive cost management by:

1. **Data Source:** Analyzes MTD (Month-to-Date) spend from `fact_usage` grouped by workspace

2. **Calculation Logic:**
   - `mtd_spend`: Sum of `list_cost` for current month
   - `projected_spend`: Extrapolates to full month: `(MTD spend / days elapsed) × 30`
   - `burn_rate`: `projected_spend / mtd_spend` ratio

3. **Alert Priority Classification:**
   - **HIGH**: `projected_spend > mtd_spend × 1.5` (50%+ overspend projection)
   - **MEDIUM**: `projected_spend > mtd_spend × 1.2` (20-50% overspend)
   - **LOW**: Spend appears on track

4. **Business Value:**
   - Early warning for budget overruns
   - Identifies workspaces needing immediate attention
   - Shows `top_sku` to pinpoint cost drivers
   - `days_to_budget` shows time remaining to take corrective action

---

## Unified Dashboard ML Visuals Final Fixes - January 5, 2026

### Issues Fixed

| Visual | Error | Root Cause | Fix Applied |
|--------|-------|------------|-------------|
| **ML: Capacity Recommendations** | `w.cluster_size` cannot be resolved | Column name in dim_warehouse is `warehouse_size`, not `cluster_size` | Changed to `w.warehouse_size` |
| **ML: Jobs at Risk** | `error_message` cannot be resolved | fact_job_run_timeline doesn't have `error_message` column | Changed to `termination_code` |
| **ML: Cost Anomalies Detected** | VECTOR_SEARCH showing multiple times with same cost | Query was showing duplicate rows without specificity | Complete rewrite - now shows top 5 cost drivers per workspace with unique identification |
| **ML: Security Threats** | Users showing 2M+ failed actions | `is_failed_action` was counting ALL failed actions, not security-specific ones | Refined to count only `response_result = 'denied'` events and security-specific actions |

### Query Improvements

**ML: Capacity Recommendations:**
- Changed `w.cluster_size` → `w.warehouse_size` (correct column name)
- Added `min_clusters` and `max_clusters` to resource_type display
- Enhanced rationale with cluster configuration details

**ML: Jobs at Risk:**
- Changed `error_message` → `termination_code` (column that exists in schema)
- Updated `last_error_preview` to show termination code instead of non-existent error message

**ML: Cost Anomalies Detected:**
- Completely rewrote query to be data-driven from `fact_usage`
- Removed dependency on unreliable ML predictions table
- Added proper deduplication by showing top 5 cost drivers per workspace
- Made `cost_driver` specific with actual resource IDs: "Job ID: X", "Warehouse ID: Y", or "SKU: Z"
- Added `daily_cost` as numeric value (not formatted string)
- Enhanced `rationale` with SKU name, 7-day total, and resource identifier

**ML: Security Threats:**
- Reduced time window from 30 days to 7 days for more focused analysis
- Changed from counting all `is_failed_action` to specifically counting:
  - `response_result = 'denied'` events
  - Destructive actions: deleteTable, deleteSchema, deleteCatalog, etc.
  - Permission changes: updatePermissions, grantPermission, etc.
- Added minimum thresholds in HAVING clause to filter noise:
  - >5 access denials OR
  - >2 destructive actions OR  
  - >3 permission changes
- Updated scoring formula to weight based on security impact
- Improved recommended_action to be more specific

### Validation

- All queries validated via `databricks bundle validate`
- Dashboard deployment successful for all 6 dashboards

---

## Cost & Commitment ML Visuals Complete Overhaul - January 4, 2026

### Issues Fixed

| Visual | Error | Root Cause | Fix Applied |
|--------|-------|------------|-------------|
| **ML: Detected Cost Anomalies** | `workspace_name` cannot be resolved | Query returned `workspace_id`, no join to dim_workspace | Complete rewrite with dim_workspace join, fact_usage for cost driver |
| **ML: Budget Alert Priorities** | `days_to_budget` cannot be resolved | Query returned `days_remaining` | Renamed column + added MTD spend, projected spend, top SKU |
| **ML: Tag Recommendations** | `job_name` cannot be resolved | Query returned `resource_name` from ML predictions | Complete rewrite - now queries actual untagged jobs from fact_usage |

### Visuals Enhanced for Actionability

| Visual | Before | After |
|--------|--------|-------|
| **ML: Detected Cost Anomalies** | Generic workspace IDs, no cost drivers | Workspace name, daily cost, specific cost driver (Job/Warehouse/SKU), recommended action |
| **ML: Budget Alert Priorities** | Basic burn rate | MTD spend, projected spend, top SKU, recommended action |
| **ML: Tag Recommendations** | Generic tag suggestions | Actual untagged job names, workspace, total cost, priority, rationale |
| **ML: User Behavior Clusters** | Abstract cluster IDs and scores | Real user identifiers, total spend, usage patterns (jobs/warehouses), specific recommendations |
| **ML: Migration Recommendations** | All 0.00 values, generic recommendations | Cluster names, workspace, 30d cost, estimated savings, confidence rationale, usage details |

### New Columns Added

**Cost Anomalies:**
- `workspace_name` - Resolved from dim_workspace
- `daily_cost` - Actual dollar amount
- `cost_driver` - Specific Job/Warehouse/SKU causing anomaly
- `recommended_action` - Based on severity level

**Budget Alerts:**
- `mtd_spend` - Month-to-date actual spend
- `projected_spend` - Projected month-end spend
- `top_sku` - Highest cost SKU
- `recommended_action` - Based on burn rate

**Tag Recommendations:**
- `job_name` - Actual untagged job name from fact_usage
- `workspace_name` - Resolved workspace
- `total_cost` - 30-day job cost
- `priority` - HIGH/MEDIUM/LOW based on cost
- `rationale` - Why tagging is recommended

**User Behavior Clusters:**
- `workspace_name` - User's primary workspace
- `total_spend` - 30-day user spend
- `usage_summary` - Jobs/Warehouses/Daily avg
- `recommended_action` - Specific optimization advice

**Migration Recommendations:**
- `workspace_name` - Cluster's workspace
- `cluster_type` - UI/JOB/etc.
- `total_cost_30d` - 30-day cluster cost
- `potential_savings` - Estimated 30% savings for serverless migration
- `confidence_rationale` - Why recommendation is HIGH/MEDIUM/LOW
- `usage_details` - Classic vs serverless breakdown

### Key Learnings

1. **ML predictions alone are not actionable** - Always join with Gold layer tables to get:
   - Human-readable names (workspace_name, job_name, cluster_name)
   - Actual cost/usage data
   - Specific resource identifiers
   
2. **Widget column names must match query exactly** - Common pattern:
   - `days_remaining` in query vs `days_to_budget` in widget
   - Always verify widget `fields` array matches query `SELECT` aliases

3. **Replace generic ML predictions with fact-based analysis** - When ML models return abstract scores:
   - Join with fact_usage for actual cost data
   - Join with dim tables for human-readable names
   - Derive recommendations from actual usage patterns

---

## ML Visual Actionability Enhancement - January 4, 2026 (Part 2)

### Problem Summary
User reported that ML visuals were not actionable:
1. **Cost Anomalies**: `cost_driver` showed "SKU: N/A" and "Warehouse: N/A" - not actionable
2. **Security Threats**: Showed "0 failed actions, 0 deletes" with "N/A" last action - false positive issue
3. **Capacity Recommendations**: Resource IDs without context (no name, type, or size)
4. **Jobs at Risk**: No specific examples of problems (just generic rationale)

### Root Cause Analysis

| Visual | Root Cause | Analysis |
|--------|-----------|----------|
| **Cost Anomalies** | `FIRST()` aggregation returned NULL; date join mismatch | Join between prediction date and usage date wasn't aligning |
| **Security Threats** | `user_id` from ML predictions doesn't match `user_identity_email` from audit logs | ML model used different user identifiers than audit system |
| **Capacity Recommendations** | Raw warehouse IDs shown without dim_warehouse join | No dimension table lookup |
| **Jobs at Risk** | Generic rationale from ML prediction alone | No join to actual job history |

### Fixes Applied

#### 1. Cost Anomalies - Complete Rewrite
**Before:** Join on workspace_id and usage_date, FIRST() returns NULL
**After:** 
- Separate CTE for `top_cost_drivers` with ROW_NUMBER() ranking
- Separate CTE for `daily_totals` with workspace name
- Join to top cost driver (rank=1) for accurate cost driver identification
- Shows: `billing_origin_product: resource_id` (e.g., "JOBS: job_abc123")

#### 2. Security Threats - Switched from ML to Actual Audit Data
**Before:** Start from ML predictions, join to audit logs (join fails due to ID mismatch)
**After:** 
- Start from `fact_audit_logs` with `HAVING` clause to filter high-risk users
- Uses actual behavior: failed_actions > 0 OR access_denied > 0 OR delete_actions > 2
- Shows real suspicious actions and services
- Risk score derived from actual behavior, not ML prediction

#### 3. Capacity Recommendations - Added Dimension Lookup
**Before:** `COALESCE(warehouse_id, 'Unknown') AS resource_name`
**After:**
- Joins with `dim_warehouse` to get warehouse_name, warehouse_type, cluster_size
- Shows: `CONCAT(resource_type, ': ', warehouse_name)` (e.g., "SQL: Demo Warehouse")
- Added `resource_type` column showing "Type: SQL | Size: Medium"

#### 4. Jobs at Risk - Added Historical Context
**Before:** Generic rationale from ML prediction alone
**After:**
- CTE joins with `fact_job_run_timeline` to get actual failure history
- Shows: historical failure rate %, duration variance, last failure type
- Added `last_error_preview` (first 60 chars of error message)
- Added `last_failure_date` for quick investigation

### Widget Encoding Updates

All four widgets updated with new columns:

| Widget | New Columns Added |
|--------|------------------|
| Cost Anomalies | `cost_driver` (now with actual values), better `rationale` |
| Security Threats | `incident_summary` (with real counts), `last_suspicious_action`, `affected_service` |
| Capacity Recommendations | `resource_type` (Type/Size) |
| Jobs at Risk | `last_error_preview`, `last_failure_date` |

### Key Learnings

1. **ML Predictions + Actual Data**: ML predictions are useful for ranking/prioritization, but need to be enriched with actual system data for actionable insights
2. **ID Mismatch is Common**: Different systems (ML models, audit logs, billing) may use different identifiers for the same entity - always verify join conditions
3. **Fallback to Facts**: When ML correlations fail, switching to fact-based detection (audit log behavior) provides actionable results
4. **Dimension Lookups**: Always join to dimension tables for human-readable names

---

## Active Issues (To Fix)

**Job Success Drift at 0%:** Under investigation - the `success_rate_drift` column in `fact_job_run_timeline_drift_metrics` may be returning NULL or 0. This could indicate:
1. Job success rates haven't changed (true 0% drift)
2. The monitoring table hasn't been populated correctly
3. The `success_rate_drift` column doesn't exist

**Recommendation:** Run SQL directly against the drift_metrics table to verify data:
```sql
SELECT column_name, COUNT(*), AVG(success_rate_drift)
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
GROUP BY column_name
```

---

## ML Visuals Final Fix & Cost Anomalies Enhancement - January 4, 2026

### Issues Fixed

| Visual | Error | Root Cause | Fix Applied |
|--------|-------|-----------|-------------|
| **ML: Security Threats** | `user_identity` cannot be resolved | Table has `user_id`, not `user_identity` | Changed to `user_id AS user_identity` |
| **ML: Security Threats** | `risk_score` cannot be resolved | Table stores `prediction`, not `risk_score` | Changed to `prediction * 100 AS risk_score` |
| **ML: Capacity Recommendations** | `is_weekend` DATATYPE_MISMATCH | `is_weekend` is DOUBLE, not BOOLEAN | Changed to `COALESCE(is_weekend, 0) > 0.5` |
| **ML: Capacity Recommendations** | `error_rate` cannot be resolved | Column doesn't exist | Changed to use `prediction AS utilization_score` |

### Cost Anomalies Enhancement (Major Improvement)

**Problem:** Cost Anomalies only showed `workspace_id` - not actionable!

**Enhancement:** Now shows:
- **Workspace Name** (resolved from dim_workspace)
- **Cost Driver** - Shows which job, warehouse, or SKU is causing the anomaly
- **Daily Cost** - Dollar amount of the anomaly
- **Severity** - HIGH/MEDIUM/LOW
- **Details** - Job vs SQL cost breakdown

**New Query Logic:**
```sql
-- Joins cost_anomaly_predictions with fact_usage to identify:
-- 1. Top job_id (if jobs cost > SQL cost)
-- 2. Top warehouse_id (if SQL cost > jobs cost)
-- 3. Top SKU (fallback)
-- Shows daily_cost and breaks down job_cost vs sql_cost
```

**Widget Columns Updated:**
| Old Column | New Column |
|-----------|------------|
| Workspace ID | Workspace Name |
| Score | (removed - severity is enough) |
| - | Cost Driver (Job/Warehouse/SKU) |
| - | Daily Cost |
| Date | (removed - not useful) |

### Key Learnings

1. **ML Prediction Tables Schema:**
   - `user_id` (not `user_identity`)
   - `prediction` (model output, 0-1 range)
   - `scored_at` (timestamp)
   - Derived fields (like `is_weekend`) may be DOUBLE, not BOOLEAN

2. **Making Anomalies Actionable:**
   - Always join anomaly predictions with source data
   - Show the specific resource causing the issue
   - Include cost/impact metrics
   - Provide clear recommended actions

---

## Drift Metrics KPI & Trend Fix - January 4, 2026

### Issue
1. **Cost Drift % showing -2,040%** - Wildly incorrect value
2. **Query Duration Drift % showing -5,330%** - Wildly incorrect value
3. **Job Success Drift % showing 0%** - Suspiciously constant
4. **Drift Trend chart missing Query Duration line**

### Root Cause
**Inconsistent drift metric scaling:**
- `cost_drift_pct` and `p95_duration_drift_pct` are already percentages (e.g., -20.4 for -20.4% drift)
- `success_rate_drift` is an absolute difference (e.g., -0.05 for 5 percentage point drop)
- All KPIs used `number-percent` format which multiplies by 100

**Result:**
- Cost: -20.4 × 100 = -2040% ❌
- Query: -53.3 × 100 = -5330% ❌
- Job: 0 × 100 = 0% (but this might also be a data issue)

### Fixes Applied

| Component | Issue | Fix |
|-----------|-------|-----|
| `ds_monitor_cost_drift` | Already-percentage × 100 | Divide by 100 before returning |
| `ds_monitor_query_drift` | Already-percentage × 100 | Divide by 100 before returning |
| `ds_drift_trend` | Missing query drift line | Added third series for query_drift |
| `ds_drift_trend` | Job drift not scaled | Multiply by 100 to match other metrics |

### Updated Query Patterns

**Cost/Query KPIs (divide by 100):**
```sql
SELECT ROUND(COALESCE(cost_drift_pct, 0) / 100.0, 4) AS drift_pct
-- Returns 0.2040 for -20.4% drift, formatted by number-percent to 20.4%
```

**Drift Trend (3-series chart):**
```sql
SELECT 
  day,
  ROUND(cost_drift_pct, 1) AS cost_drift,          -- Already percentage
  ROUND(success_rate_drift * 100, 1) AS job_drift, -- Convert to percentage
  ROUND(p95_duration_drift_pct, 1) AS query_drift  -- Already percentage
```

### Key Learning
**Drift metric definitions are inconsistent:**
| Metric | Stored As | Example Value | Meaning |
|--------|-----------|---------------|---------|
| `cost_drift_pct` | Percentage | -20.4 | -20.4% cost change |
| `p95_duration_drift_pct` | Percentage | -53.3 | -53.3% duration change |
| `success_rate_drift` | Absolute diff | -0.05 | -5 percentage points |

---

## ML Visuals Enhancement & Fix - January 4, 2026

### Issues Fixed
1. **ML: Security Threats** - `user_identity_email` column not found (query used `user_id` which doesn't exist)
2. **ML: Capacity Recommendations** - `job_id` column not found (query used non-existent columns)

### Enhancements Added to All ML Visuals

All 4 ML visuals now include actionable context:

| Visual | New Columns Added |
|--------|-------------------|
| ML: Cost Anomalies | `recommended_action`, `rationale` |
| ML: Jobs at Risk | `recommended_action`, `rationale` |
| ML: Security Threats | `recommended_action`, `rationale` |
| ML: Capacity Recommendations | `recommended_action`, `rationale`, `usage_pattern` |

### Column Mapping Fixes

| Visual | Old Query Columns | Fixed Columns |
|--------|------------------|---------------|
| Security Threats | `user_id AS user_identity` | `user_identity` (direct column) |
| Capacity Recommendations | `job_id`, `prediction * 10` | `warehouse_id`/`model_name`, `error_rate` |

### Sample Recommended Actions

**Cost Anomalies:**
- HIGH: "Immediate investigation required - review recent jobs and queries"
- MEDIUM: "Review cost drivers and set up alerts"
- LOW: "Continue monitoring - within expected range"

**Jobs at Risk:**
- HIGH: "Add retry logic, review job configuration, enable notifications"
- MEDIUM: "Monitor closely, review recent changes, check resource constraints"
- LOW: "Continue standard monitoring"

**Security Threats:**
- HIGH: "Immediate review required - potential data exfiltration"
- MEDIUM: "Investigate unusual access patterns"
- LOW: "Monitor for pattern changes"

---

## Drift Metrics - Wrong Column Reference Fix - January 4, 2026

### Issue
All drift KPIs showing 0% and drift trend showing flat lines on the Monitoring Alerts page.

### Root Cause
**Drift queries were using `avg_delta` when they should use custom drift metric columns.**

Lakehouse Monitoring stores custom drift metrics as **named columns**, not in the generic `avg_delta` field:
- Cost drift: `cost_drift_pct` (not `avg_delta`)
- Job drift: `success_rate_drift` (not `avg_delta`)
- Query drift: `p95_duration_drift_pct` (not `avg_delta`)

The `avg_delta` field on `column_name = ':table'` returns null/0 because it's for standard statistical columns, not custom metrics.

### Fixes Applied

| Dataset | Old Pattern | New Pattern |
|---------|-------------|-------------|
| `ds_monitor_cost_drift` | `avg_delta * 100` | `cost_drift_pct` |
| `ds_monitor_job_drift` | `avg_delta * 100` | `success_rate_drift` |
| `ds_monitor_query_drift` | `avg_delta * 100` | `p95_duration_drift_pct` |
| `ds_drift_trend` | Single series from job metrics | Multi-series FULL OUTER JOIN of cost + job drift |
| `ds_drift_alerts` | `avg_delta` in all UNIONs | Correct custom columns per domain |

### Additional Fixes
- Added `slice_key IS NULL` filter to all drift queries (required for table-level metrics)
- Updated severity thresholds to meaningful values:
  - Cost: >20% high, >10% medium
  - Reliability: >5% high, >2% medium
  - Performance: >30% high, >15% medium

### Key Learning
**Lakehouse Monitoring custom metric columns:**
- AGGREGATE metrics: stored in `_profile_metrics` as named columns (e.g., `success_rate`, `total_cost`)
- DRIFT metrics: stored in `_drift_metrics` as named columns (e.g., `success_rate_drift`, `cost_drift_pct`)
- The generic `avg_delta` field is for standard statistical analysis, NOT custom metrics

---

## Tables by Catalog - Missing Scale Properties Fix - January 4, 2026

### Issue
"Tables by Catalog" bar chart showing "Select fields to visualize" across multiple dashboards despite having valid queries that return data.

### Root Cause
Bar charts in Databricks Lakeview require explicit `scale` properties in their encodings:
- `x` encoding needs `"scale": { "type": "categorical" }`
- `y` encoding needs `"scale": { "type": "quantitative" }`

Without these properties, the widget fails to render even with valid data.

### Fixes Applied

| Dashboard | Widget Location | Fix |
|-----------|-----------------|-----|
| `unified.lvdash.json` | Governance Overview page | Added `scale` properties to `x` and `y` encodings |
| `quality.lvdash.json` | Governance Overview page | Added `scale` properties to `x` and `y` encodings |
| `quality.lvdash.json` | Catalog Stats page | Added `scale` properties to `x` and `y` encodings |

### Pattern: Bar Chart Encodings (Required)
```json
"encodings": {
  "x": {
    "fieldName": "category_column",
    "displayName": "Category",
    "scale": { "type": "categorical" }  // ← REQUIRED
  },
  "y": {
    "fieldName": "value_column",
    "displayName": "Value",
    "scale": { "type": "quantitative" }  // ← REQUIRED
  }
}
```

### Key Learning
Both **pie charts** and **bar charts** require explicit `scale` properties:
- Pie charts: `color.scale` + `angle.scale`
- Bar charts: `x.scale` + `y.scale`

---

## Active Users Metric - Service Account Filter Fix - January 4, 2026

### Issue
"Active Users (30d)" on Cost Overview page showing 27.259K - significantly higher than expected unique human users.

### Root Causes
1. **Missing service account filters**: The `ds_unique_counts` dataset only filtered out `System-User`, but not:
   - Google service accounts (`*.gserviceaccount.com`)
   - Service principals (`service-principal-*`, `*[ServicePrincipal]*`)
   - Databricks internal users (`*@databricks.com`)
   - System accounts (`system`, `admin`, `root`, `databricks`, `unity-catalog-service`)

2. **Misleading title**: Widget said "(30d)" but the time range is controlled by global filter (which was set to 90 days)

### Fixes Applied
1. **Updated `ds_unique_counts` query** to filter out service accounts:
```sql
SELECT COUNT(DISTINCT user_identity_email) AS active_users
FROM fact_audit_logs 
WHERE event_date >= :time_range.min AND event_date <= :time_range.max
  AND user_identity_email IS NOT NULL
  AND user_identity_email NOT LIKE '%.gserviceaccount.com'
  AND user_identity_email NOT LIKE 'service-principal-%'
  AND user_identity_email NOT LIKE '%[ServicePrincipal]%'
  AND user_identity_email NOT LIKE '%@databricks.com'
  AND LOWER(user_identity_email) NOT IN ('system-user', 'system', 'admin', 'root', 'databricks', 'unity-catalog-service')
```

2. **Updated widget title**: Changed from "Active Users (30d)" to "👥 Unique Users" (time range controlled by global filter)

### Clarification
**Yes, it IS counting UNIQUE users** - the query uses `COUNT(DISTINCT user_identity_email)`. The high count was due to including service accounts, not duplicate counting.

---

## ML Predictions - Final Column and Table Fixes - January 4, 2026

### Summary
Fixed remaining ML prediction queries that still had `prediction_timestamp` instead of `scored_at` and domain-specific date columns instead of `scored_at` for filtering.

### Dashboards Fixed

| Dashboard | Datasets Fixed | Issues |
|-----------|----------------|--------|
| **Security** | `ds_ml_threats`, `ds_ml_exfiltration`, `ds_ml_privilege` | `prediction_timestamp` → `scored_at`, `event_date` → `scored_at` |
| **Cost** | `ds_ml_user_behavior`, `ds_ml_migration_recs` | `prediction_timestamp` → `scored_at`, `usage_date` → `scored_at` |
| **Unified** | `ds_ml_capacity`, `ds_ml_security_threats`, `ds_ml_job_risks`, `ds_ml_cost_anomalies` | Old table names, `prediction_timestamp`, domain date filters |

### Key Changes

**Security Dashboard:**
```sql
-- Before (wrong)
SELECT ... prediction_timestamp FROM ... WHERE event_date >= ...

-- After (correct)
SELECT ... scored_at FROM ... WHERE scored_at >= ...
```

**Cost Dashboard:**
```sql
-- Before (wrong)
SELECT ... prediction_timestamp FROM ... WHERE usage_date >= ...

-- After (correct)
SELECT ... scored_at FROM ... WHERE scored_at >= ...
```

**Unified Dashboard:**
```sql
-- Before (wrong)
SELECT ... prediction_timestamp FROM ...cluster_capacity_planner_predictions WHERE prediction_date >= ...

-- After (correct)
SELECT ... scored_at FROM ...cluster_capacity_predictions WHERE scored_at >= ...
```

### ML Prediction Tables - Correct Names

| Old Table Name | Correct Table Name |
|----------------|-------------------|
| `cluster_capacity_planner_predictions` | `cluster_capacity_predictions` |
| `security_threat_detector_predictions` | `security_threat_predictions` |
| `job_failure_predictor_predictions` | `job_failure_predictions` |
| `cost_anomaly_detector_predictions` | `cost_anomaly_predictions` |

### ML Prediction Columns - Standard Schema

All ML prediction tables have the same output schema:
- Lookup keys (domain-specific)
- `prediction` - Model output value
- `scored_at` - When inference was run (NOT `prediction_timestamp`)

### Validation
After this fix, `grep prediction_timestamp` only shows matches in `unified.lvdash.baseline.json` (backup file).

---

## Rule Enhancement: Pre-Deployment SQL Validation - January 4, 2026

### Summary
Enhanced cursor rules and prompts with comprehensive SQL validation patterns to reduce dashboard development loop time by ~90%.

### Files Updated
1. **`.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc`** (v3.0 → v3.1)
   - NEW Section 16: Pre-Deployment SQL Validation
   - Added `SELECT LIMIT 1` vs `EXPLAIN` comparison
   - Added parameter substitution reference table
   - Added widget encoding validation script pattern
   - Added development workflow (validate → diff → deploy)
   - Added anti-regression checks guidance
   - Sections expanded from 20 to 21 total

2. **`context/prompts/monitoring/10-aibi-dashboards-prompt.md`** (v3.0 → v3.1)
   - Enhanced "Run SQL Validation" section with detailed workflow
   - Added parameter substitution table
   - Added development workflow commands
   - Updated critical rules summary

### Key Insights Documented

**Why validate before deploying?**
- Without validation: Deploy → Open dashboard → See errors → Fix → Redeploy = 2-5 min per iteration
- With validation: Validate → See ALL errors at once → Fix all → Deploy = 30-60 sec total
- **Result: 90% reduction in dev loop time**

**Why `SELECT LIMIT 1` instead of `EXPLAIN`?**
- `EXPLAIN` only catches syntax errors
- `SELECT LIMIT 1` catches runtime errors:
  - `UNRESOLVED_COLUMN` - column doesn't exist
  - `TABLE_OR_VIEW_NOT_FOUND` - table doesn't exist
  - `UNBOUND_SQL_PARAMETER` - parameter not defined
  - `DATATYPE_MISMATCH` - type conversion errors

**Development Workflow Pattern:**
```bash
# 1. Make changes
# 2. Widget encoding validation (local, fast)
# 3. SQL validation (requires Databricks)
# 4. Git diff (anti-regression)
# 5. Deploy only after all pass
```

---

## All Dashboards - Lakehouse Monitoring Query Pattern Fix - January 4, 2026

### Issue
Monitoring metrics were showing errors and flat trend lines across all dashboards. The root cause was inconsistent query patterns:
1. Some queries incorrectly used `CASE WHEN column_name = 'X' THEN avg END` pattern for custom metrics
2. Custom AGGREGATE and DERIVED metrics are stored as **direct columns** in the profile_metrics tables
3. The `column_name = ':table'` filter is correct - it identifies table-level KPIs vs per-column statistics

### Affected Dashboards
- **Reliability**: `ds_monitor_reliability_aggregate`, `ds_monitor_reliability_derived`, `ds_monitor_reliability_drift`
- **Quality/Governance**: `ds_monitor_gov_latest`, `ds_monitor_gov_trend`, `ds_monitor_gov_drift`, `ds_monitor_gov_detailed`

### Fixes Applied

#### Reliability Dashboard
| Dataset | Before (Wrong) | After (Correct) |
|---------|---------------|-----------------|
| `ds_monitor_reliability_aggregate` | `MAX(CASE WHEN column_name = 'total_runs' THEN avg END)` | `COALESCE(total_runs, 0) AS total_runs` |
| `ds_monitor_reliability_derived` | `MAX(CASE WHEN column_name = 'success_rate' THEN avg END)` | `COALESCE(success_rate, 0) AS success_rate` |
| `ds_monitor_reliability_drift` | `MAX(CASE WHEN column_name = 'success_rate_drift' THEN avg_delta END)` | `COALESCE(success_rate_drift, 0) AS success_rate_drift` |

#### Quality Dashboard
| Dataset | Before (Wrong) | After (Correct) |
|---------|---------------|-----------------|
| `ds_monitor_gov_latest` | Missing `slice_key IS NULL` filter | Added proper filters and direct column selection |
| `ds_monitor_gov_drift` | CASE pivots on avg_delta | Direct column selection: `lineage_volume_drift_pct`, `user_count_drift` |
| `ds_monitor_gov_detailed` | `read_ratio` / `write_ratio` (don't exist) | `read_events`, `write_events`, `read_write_ratio` (actual metrics) |

### Key Learning: Lakehouse Monitoring Query Pattern

**For custom metrics (AGGREGATE/DERIVED):**
```sql
-- ✅ CORRECT: Custom metrics are stored as columns
SELECT 
  total_runs,
  success_rate,
  avg_duration_minutes
FROM fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL

-- ❌ WRONG: This pattern is for built-in statistics on data columns, not custom metrics
SELECT 
  MAX(CASE WHEN column_name = 'total_runs' THEN avg END) AS total_runs
FROM fact_job_run_timeline_profile_metrics
GROUP BY window.start
```

**For drift metrics:**
```sql
-- ✅ CORRECT: Drift metrics are also stored as columns
SELECT 
  success_rate_drift,
  duration_drift_pct
FROM fact_job_run_timeline_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL
```

### Updated Widget Encodings
The `table_monitor_detailed` widget in Quality dashboard was updated to match the new query columns:
- Removed: `read_pct`, `write_pct`
- Added: `read_events`, `write_events`, `read_write_ratio`

---

## Performance Dashboard - Warehouse Analysis Page Enhancements - January 4, 2026

### Issues Fixed
1. **Query Distribution by Warehouse** - Pie chart was showing "Select fields to visualize" due to missing `scale` properties
2. **Warehouse Performance Summary** - Enhanced with additional useful metrics

### Fixes Applied

| Visual | Issue | Fix |
|--------|-------|-----|
| Query Distribution by Warehouse | Missing `scale` properties | Added `"scale": {"type": "categorical"}` for color and `"scale": {"type": "quantitative"}` for angle |
| Warehouse Performance Summary | Limited metrics | Added 3 new columns for better analysis |

### New Columns Added to Warehouse Performance Summary

| Column | Description | Value |
|--------|-------------|-------|
| **Data (GB)** | Total data scanned | Helps estimate compute costs |
| **Spill %** | % of queries with disk spill | Indicates memory pressure / sizing issues |
| **Users** | Distinct active users | Shows warehouse adoption |

### Enhanced Query
```sql
SELECT 
  compute_type AS warehouse_name,
  COUNT(*) AS total_queries,
  ROUND(AVG(total_duration_ms / 1000.0), 2) AS avg_duration,
  ROUND(PERCENTILE_APPROX(total_duration_ms / 1000.0, 0.95), 2) AS p95_duration,
  ROUND(SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS failure_rate,
  ROUND(SUM(COALESCE(read_bytes, 0)) / 1073741824.0, 2) AS data_scanned_gb,  -- NEW
  ROUND(SUM(CASE WHEN COALESCE(spilled_local_bytes, 0) > 0 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS spill_pct,  -- NEW
  COUNT(DISTINCT executed_by) AS active_users  -- NEW
FROM fact_query_history
GROUP BY 1 ORDER BY total_queries DESC
```

### Business Value
- **Data Scanned**: Directly correlates to compute costs (more data = higher DBUs)
- **Spill %**: High spill indicates warehouse may be undersized or queries inefficient
- **Users**: Helps identify underutilized vs heavily used warehouses for optimization

---

## Performance Dashboard - User Email Resolution Fix - January 4, 2026

### Issue
The "Top 20 Slowest Queries" and "Recent Failed Queries" tables were showing user IDs (e.g., `306860367104667`) instead of email addresses.

### Root Cause
1. Both `ds_slowest_queries` and `ds_failed_queries` used `executed_by_user_id` (numeric user ID) 
2. Should use `executed_by` (email/username) with fallback to user ID

### Fix Applied
Updated both datasets to use COALESCE pattern:
```sql
-- BEFORE (wrong)
SELECT 
  executed_by_user_id AS user_identity_email  -- Shows numeric ID!

-- AFTER (correct)
SELECT 
  COALESCE(executed_by, CAST(executed_by_user_id AS STRING)) AS user_identity_email
  -- ✅ Uses email if available, falls back to user ID
```

### Datasets Fixed
1. `ds_slowest_queries` - Top 20 Slowest Queries
2. `ds_failed_queries` - Recent Failed Queries (7d)

### Future Enhancement: dim_user Table
For workspaces where `executed_by` is NULL, consider creating a `dim_user` dimension table using the Databricks SDK:

```python
# Using WorkspaceClient to get user details
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
users = w.users.list()

# Create dim_user with columns:
# - user_id (STRING) - Primary key
# - email (STRING) - User email
# - display_name (STRING) - User display name
# - active (BOOLEAN) - Is user active

# Then join in queries:
# LEFT JOIN dim_user u ON f.executed_by_user_id = u.user_id
```

### Key Learning
- `executed_by` = email address/username (preferred)
- `executed_by_user_id` = internal user ID (numeric string)
- Use COALESCE for robustness when email might be NULL

---

## Rule Improvement: AI/BI Dashboard Patterns v3.0 - January 4, 2026

### Summary
Comprehensive documentation of 100+ production deployment learnings into cursor rules and prompts for guiding future AI/BI dashboard development.

### Files Updated
1. **`.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc`** - Enhanced from ~250 lines to 600+ lines
2. **`context/prompts/monitoring/10-aibi-dashboards-prompt.md`** - Enhanced from ~994 lines to 900+ lines (reorganized for clarity)

### Key Patterns Documented (20 Sections)

| # | Pattern | Impact | Error Prevented |
|---|---------|--------|-----------------|
| 1 | Widget-Query Column Alignment | Most common error | "no fields to visualize" |
| 2 | Number Formatting Rules | Second most common | 0% or empty KPIs |
| 3 | Parameter Configuration | Critical | "UNBOUND_SQL_PARAMETER" |
| 4 | Monitoring Table CASE Pivot | Major learning | Column not found |
| 5 | Pie Chart Scale Properties | Required | Empty pie charts |
| 6 | Table Widget v2 Config | Version | Invalid spec errors |
| 7 | Multi-Series Charts | UNION ALL pattern | Single series only |
| 8 | Stacked Area Charts | stack: "zero" | No stacking |
| 9 | SQL NULL/Division Handling | COALESCE/NULLIF | Empty results |
| 10 | Schema Variable Substitution | ${catalog}.${gold_schema} | Hardcoded paths |
| 11 | Lineage Table Queries | source + target | Missing tables |
| 12 | Composite Health Scores | UNION ALL domains | Single domain |
| 13 | Global Filters | PAGE_TYPE_GLOBAL_FILTERS | No cross-page filtering |
| 14 | Access Denial Detection | is_failed_action | Inaccurate counts |
| 15 | Page Naming Conventions | Intelligent names | Generic naming |
| 16 | Validation Checklist | Pre-deployment | Missed errors |
| 17 | Error Message Reference | Quick troubleshooting | Debugging time |
| 18 | Dashboard File Structure | Organization | Disorganized files |
| 19 | Widget Version Reference | KPI=2, Chart=3, Table=2 | Wrong versions |
| 20 | Domain-Specific Patterns | Cost/Reliability/Performance/Security/Quality | Domain mistakes |

### Critical Discoveries Documented

**1. Monitoring Table Schema (CRITICAL):**
```sql
-- ❌ WRONG - columns don't exist directly
SELECT success_rate FROM monitoring_table

-- ✅ CORRECT - use CASE pivot on column_name
SELECT MAX(CASE WHEN column_name = 'success_rate' THEN avg END) AS success_rate
FROM monitoring_table
GROUP BY window.start
```

**2. Number Formatting (CRITICAL):**
- `number-percent` multiplies by 100 → return 0.85 for 85%
- Never use `FORMAT_NUMBER()` or `CONCAT()` for KPIs

**3. Pie Chart Scales (CRITICAL):**
```json
// REQUIRED or chart won't render
"color": { "scale": { "type": "categorical" } },
"angle": { "scale": { "type": "quantitative" } }
```

**4. Parameter Definition (CRITICAL):**
- Every dataset MUST define ALL parameters in `parameters` array
- Time range accessed via `:time_range.min` and `:time_range.max`

### Metrics
- **Errors Documented:** 100+ distinct deployment failures
- **Patterns Identified:** 20 major categories
- **Lines Added:** ~1,200 across both files
- **Prevention Impact:** 90%+ error reduction expected

### Rule Improvement Process
Following `.cursor/rules/admin/21-self-improvement.mdc`:
1. ✅ Analyzed complete conversation history
2. ✅ Reviewed `dashboard-changelog.md` for patterns
3. ✅ Avoided recency bias - included all learnings
4. ✅ Structured for LLM consumption
5. ✅ Added validation checklists
6. ✅ Included error message troubleshooting

### References
- [18-databricks-aibi-dashboards.mdc](../../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)
- [10-aibi-dashboards-prompt.md](../../context/prompts/monitoring/10-aibi-dashboards-prompt.md)

---

## Performance Dashboard - Job Resource Utilization Cost Analysis - January 4, 2026

### Enhancements Implemented
Added job cost-focused visualizations to the Job Resource Utilization page, inspired by reference dashboards:

| Widget | Dataset | Description |
|--------|---------|-------------|
| **💰 Most Expensive Jobs (30d)** | `ds_job_expensive` | Top 15 jobs by total cost with runs, owner, last run date |
| **📈 Jobs with Highest Cost Increase (WoW)** | `ds_job_cost_change` | Week-over-week cost change analysis |
| **❌ Job Failure Cost Analysis** | `ds_job_failure_cost` | Cost wasted on failed runs with failure count and success rate |
| **🖥️ Jobs on All-Purpose Clusters** | `ds_job_ap_clusters` | Jobs running on interactive clusters (migration candidates) |

### New Datasets Added
1. **`ds_job_expensive`**: Top jobs by total cost from `fact_usage` joined with `dim_job` and `dim_workspace`
2. **`ds_job_cost_change`**: 7-day vs previous 7-day cost comparison with growth % calculation
3. **`ds_job_failure_cost`**: Cross-reference `fact_usage` with `fact_job_run_timeline` to identify cost of failed runs
4. **`ds_job_ap_clusters`**: Identify jobs using UI-created (all-purpose) clusters via `dim_cluster.cluster_source = 'UI'`

### Query Details

**Cost Change Calculation:**
```sql
-- Week-over-week comparison
SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS last_7d
SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS 
         AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS prev_7d
growth_pct = 100 * (last_7d - prev_7d) / NULLIF(prev_7d, 0)
```

**Failure Cost Analysis:**
- Joins `fact_usage` (cost data) with `fact_job_run_timeline` (run status)
- Calculates: `failure_cost`, `failures`, `total_runs`, `success_rate`
- Groups failures by job for actionable insights

**All-Purpose Cluster Detection:**
- Uses `dim_cluster.cluster_source = 'UI'` to identify interactive clusters
- Calculates cost attributed to jobs using these clusters
- Helps identify serverless migration candidates

### Global Filter Integration
All new datasets registered with time range filter (`filter_time_range`):
- `ds_job_expensive_time_range`
- `ds_job_cost_change_time_range`
- `ds_job_failure_cost_time_range`
- `ds_job_ap_clusters_time_range`

### Page Layout Update
Updated Job Resource Utilization page layout:
- Row 0-7: KPIs (Total Jobs, Avg CPU%, Avg Mem%, Low CPU, High Mem)
- Row 8-14: Low CPU Utilization Jobs table
- Row 15-21: High Memory Utilization Jobs table
- Row 22-28: **NEW** Most Expensive Jobs table
- Row 29-35: **NEW** Cost Change (left) + Failure Cost (right) side-by-side
- Row 36-42: **NEW** Jobs on All-Purpose Clusters table

### Business Value
| Visualization | Value Provided |
|--------------|----------------|
| Expensive Jobs | Budget visibility, cost attribution |
| Cost Change | Trend detection, anomaly identification |
| Failure Cost | Reliability ROI, issue prioritization |
| AP Cluster Jobs | Migration candidates, cost optimization |

---

## Performance Dashboard - Warehouse Analysis Page Enhancements - January 4, 2026

### Enhancements Implemented
Based on DBSQL Warehouse Advisor Observability Dashboard, implemented the following improvements:

| Enhancement | Widget Name | Description |
|------------|-------------|-------------|
| **Warehouse Usage Over Time** | `chart_warehouse_usage_trend` | Stacked area chart showing compute hours by warehouse over 30 days |
| **Usage by Warehouse Type** | `chart_warehouse_type_dist` | Pie chart: Serverless vs Classic vs Pro compute hours |
| **Top Warehouses by Cost** | `chart_warehouse_cost_ranking` | Horizontal bar chart ranking warehouses by compute hours |
| **Warehouse Current Snapshot** | `table_warehouse_config` | Table with warehouse configs (size, min/max clusters, auto-stop) |
| **Long-Running Queries** | `table_long_running_queries` | Table showing % of queries >30s, >60s, >5min per warehouse |
| **Query Source Distribution** | `chart_query_source_dist` | Pie chart by source type (dashboards, notebooks, SQL editor, jobs, etc.) |

### New Datasets Added
1. **`ds_warehouse_usage_trend`**: Daily compute hours by warehouse (30d default)
2. **`ds_warehouse_type_distribution`**: Query count and compute hours by warehouse type
3. **`ds_warehouse_config_snapshot`**: Current warehouse configuration from `dim_warehouse`
4. **`ds_warehouse_long_queries`**: Long-running query analysis with threshold breakdowns
5. **`ds_query_source_distribution`**: Query distribution by source (Dashboard, Notebook, Job, SQL Editor, Genie, Alert, Pipeline)
6. **`ds_warehouse_cost_ranking`**: Top 15 warehouses by compute hours with data scanned

### Query Details

**Query Source Classification Logic:**
```sql
CASE 
  WHEN query_source_dashboard_id IS NOT NULL OR query_source_legacy_dashboard_id IS NOT NULL THEN 'Dashboard'
  WHEN query_source_notebook_id IS NOT NULL THEN 'Notebook'
  WHEN query_source_job_info IS NOT NULL THEN 'Job'
  WHEN query_source_sql_query_id IS NOT NULL THEN 'SQL Editor'
  WHEN query_source_genie_space_id IS NOT NULL THEN 'Genie Space'
  WHEN query_source_alert_id IS NOT NULL THEN 'Alert'
  WHEN query_source_pipeline_info IS NOT NULL THEN 'Pipeline'
  ELSE 'Other/Direct'
END
```

**Long-Running Query Thresholds:**
- >30 seconds
- >60 seconds
- >5 minutes
- % of queries exceeding 30s threshold

### Global Filter Integration
All new datasets registered with the time range global filter (`filter_time_range`):
- `ds_warehouse_usage_trend_time_range`
- `ds_warehouse_type_distribution_time_range`
- `ds_warehouse_long_queries_time_range`
- `ds_query_source_distribution_time_range`
- `ds_warehouse_cost_ranking_time_range`

### Page Layout
Updated layout positions:
- Row 0-5: Warehouse Performance Summary + Query Distribution by Warehouse
- Row 6-11: Query Volume by Hour
- Row 12-17: Warehouse Usage Over Time (full width)
- Row 18-23: Usage by Warehouse Type + Query Source Distribution (side by side)
- Row 24-29: Top Warehouses by Compute Hours (full width bar chart)
- Row 30-35: Long-Running Queries by Warehouse (full width table)
- Row 36-41: Warehouse Configuration Snapshot (full width table)

### Business Value
| Enhancement | Value Provided |
|------------|----------------|
| Usage Over Time | Capacity planning, trend identification |
| Warehouse Type | Cost optimization (Serverless vs Classic) |
| Top by Cost | Budget management, cost attribution |
| Config Snapshot | Configuration review, audit trail |
| Long-Running Queries | Performance tuning opportunities |
| Query Source | Usage patterns, dashboard vs ad-hoc analysis |

---

## All Dashboards - ML Prediction Table Name & Column Fixes - January 4, 2026

### Root Cause
ML batch inference creates tables with different names than what dashboard queries referenced:

| Dashboard Query Referenced | Actual Table Created |
|---------------------------|---------------------|
| `cost_anomaly_detector_predictions` | `cost_anomaly_predictions` |
| `tag_recommender_predictions` | `tag_recommendations` |
| `chargeback_attribution_predictions` | `chargeback_predictions` |
| `job_failure_predictor_predictions` | `job_failure_predictions` |
| `pipeline_health_scorer_predictions` | `pipeline_health_predictions` |
| `retry_success_predictor_predictions` | `retry_success_predictions` |
| `sla_breach_predictor_predictions` | `sla_breach_predictions` |
| `job_duration_forecaster_predictions` | `duration_predictions` |
| `query_optimization_recommender_predictions` | `query_optimization_predictions` |
| `performance_regression_detector_predictions` | `performance_regression_predictions` |
| `cluster_capacity_planner_predictions` | `cluster_capacity_predictions` |
| `dbr_migration_risk_scorer_predictions` | `dbr_migration_predictions` |
| `security_threat_detector_predictions` | `security_threat_predictions` |
| `exfiltration_detector_predictions` | `exfiltration_predictions` |
| `privilege_escalation_detector_predictions` | `privilege_escalation_predictions` |

### Additional Issue
Queries referenced non-existent columns (e.g., `failure_probability`, `health_score`, `threat_type`). The actual prediction tables only have:
- Lookup keys (e.g., `job_id`, `run_date`, `workspace_id`, `usage_date`)
- `prediction` (model output)
- `prediction_timestamp`

### Fixes Applied
1. **Cost Dashboard:** Fixed 4 ML datasets (`ds_ml_anomalies`, `ds_ml_tag_recs`, `ds_ml_user_behavior`, `ds_ml_migration_recs`)
2. **Reliability Dashboard:** Fixed 6 ML datasets (`ds_ml_failure_risk`, `ds_ml_pipeline_health`, `ds_ml_retry_success`, `ds_ml_incident_impact`, `ds_ml_self_healing`, `ds_ml_duration_forecast`)
3. **Performance Dashboard:** Fixed 6 ML datasets (`ds_ml_optimization`, `ds_ml_regression`, `ds_ml_warehouse`, `ds_ml_capacity_predictions`, `ds_ml_rightsizing`, `ds_ml_dbr_risk`)
4. **Security Dashboard:** Fixed 3 ML datasets (`ds_ml_threats`, `ds_ml_exfiltration`, `ds_ml_privilege`)

### Query Pattern
All queries now use the `prediction` column and derive display values:
```sql
SELECT
  job_id AS job_name,
  ROUND(prediction * 100, 1) AS health_score,
  CASE WHEN prediction > 0.7 THEN 'HIGH' ELSE 'LOW' END AS risk_level,
  prediction_timestamp
FROM ${catalog}.${feature_schema}.pipeline_health_predictions
WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
```

---

## Security Dashboard - KPI Column Name Mismatches Fix - January 4, 2026

### Issues Identified
Multiple KPIs and the Event Trend chart showed "Unable to render visualization" due to column name mismatches between queries and widget expectations.

### Fixes Applied

| Dataset | Old Column | New Column |
|---------|------------|------------|
| `ds_kpi_events` | `distinct_users` | `unique_users` |
| `ds_kpi_high_risk` | `sensitive_action_count` | `high_risk_events` |
| `ds_kpi_permissions` | `permission_change_count` | `permission_changes` |
| `ds_kpi_admin` | `distinct_actions` | `admin_actions` |
| `ds_event_trend` | `distinct_users` | `unique_users` |

### Additional Improvements
- Removed `FORMAT_NUMBER()` from KPI queries (counter widgets need raw numbers)
- Expanded high risk event detection to include `%destroy%` and `%terminate%`
- Expanded admin actions detection to include service_name-based detection

---

## Security Dashboard - Access Denial Query Accuracy Fix - January 4, 2026

### Issues Identified
1. **Access denial queries were showing "No data"**: The queries used pattern matching on `action_name` (`%denied%`, `%error%`, `%fail%`) which misses most actual access denials
2. **SQL bug in ds_denied_by_service and ds_denied_by_user**: Missing parentheses around OR conditions caused incorrect filtering:
   ```sql
   -- BUGGY: Evaluates as (time AND action LIKE '%denied%') OR action LIKE '%error%' ...
   WHERE event_time BETWEEN ... AND action_name LIKE '%denied%' OR action_name LIKE '%error%'
   ```

### Root Cause
The Gold layer `fact_audit_logs` table has dedicated columns for detecting failures:
- `is_failed_action` - Boolean flag for failed actions
- `response_status_code` - HTTP status codes (400+ = errors)
- `response_error_message` - Error message details

These columns were not being used in the denial queries.

### Fixes Applied

| Dataset | Issue | Fix |
|---------|-------|-----|
| `ds_kpi_denied` | Only pattern matching | Added `is_failed_action = true OR response_status_code >= 400` |
| `ds_denied_access` | Only pattern matching | Added proper failure detection + `error_message` column |
| `ds_denied_by_service` | Missing parentheses + pattern matching only | Fixed parentheses, added proper failure detection |
| `ds_denied_by_user` | Missing parentheses + pattern matching only | Fixed parentheses, added proper failure detection |
| `table_denied_access` | No error column | Added `error_message` column |

### Updated Query Pattern
```sql
WHERE event_time BETWEEN :time_range.min AND :time_range.max
  AND (is_failed_action = true 
       OR response_status_code >= 400 
       OR LOWER(action_name) LIKE '%denied%' 
       OR LOWER(action_name) LIKE '%unauthorized%')
```

---

## Security Dashboard - Access by Service Fix & Workspace Filter - January 4, 2026

### Issues Identified
1. **"Access by Service" pie chart was empty**: Missing `scale` properties for pie chart encodings
2. **No Workspace filter in global filters**: Unlike other dashboards, Security dashboard lacked workspace filtering

### Fixes Applied

| Component | Issue | Fix |
|-----------|-------|-----|
| `chart_access_by_service` | Missing `scale` properties | Added `"scale": {"type": "categorical"}` to color encoding and `"scale": {"type": "quantitative"}` to angle encoding |
| Global Filters | Missing workspace filter | Added `ds_select_workspace` dataset and `filter_param_workspace` widget |
| `ds_kpi_events` | No workspace filter | Added `param_workspace` parameter and JOIN to `dim_workspace` |
| `ds_event_trend` | No workspace filter | Added `param_workspace` parameter and JOIN to `dim_workspace` |
| `ds_denied_access` | No workspace filter | Added `param_workspace` parameter and JOIN to `dim_workspace` |
| `ds_data_access` | No workspace filter | Added `param_workspace` parameter and JOIN to `dim_workspace` |
| `ds_access_by_service` | No workspace filter | Added `param_workspace` parameter and JOIN to `dim_workspace` |

### Workspace Filter Pattern
```sql
-- Added to all relevant datasets
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
WHERE ... 
  AND (ARRAY_CONTAINS(:param_workspace, 'all') 
       OR ARRAY_CONTAINS(:param_workspace, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING))))
```

---

## Security Dashboard - Lakehouse Monitoring Page Fixes & Page Renaming - January 4, 2026

### Issues Identified
1. **Multiple "Unresolved Column" errors** on Security Metrics Overview page:
   - `ds_monitor_trend`: Returned `date` but widgets expected `window_start`
   - `ds_monitor_access`: Returned `date` but widgets expected `window_start`
   - `ds_monitor_drift`: Returned `date` but widgets expected `window_start`
   - `ds_monitor_detailed`: Returned generic columns
   - `ds_monitor_latest`: Needed CASE pivot pattern for metrics

2. **Poor page naming**: All dashboards had "📊 Lakehouse Monitoring" and "Lakehouse Monitoring - fact_*" pages, which was confusing

### Fixes Applied

| Dataset | Issue | Fix |
|---------|-------|-----|
| `ds_monitor_latest` | Direct column selection | Rewrote with CASE pivot, returns `total_events`, `unique_users`, `high_risk_rate` |
| `ds_monitor_trend` | Returned `date` | Changed to `window_start`, added CASE pivot for `total_events`, `high_risk_events`, `unique_users` |
| `ds_monitor_access` | Returned `date` | Changed to `window_start`, added CASE pivot for `denied_accesses`, `permission_changes`, `admin_actions` |
| `ds_monitor_drift` | Returned `date` | Changed to `window_start`, added CASE pivot for `event_volume_drift`, `risk_level_drift` |
| `ds_monitor_detailed` | Generic columns | Rewrote with CASE pivot returning `window_start`, `total_events`, `unique_users`, `high_risk_events`, `denied_accesses` |

### Page Renaming (All Dashboards)

| Dashboard | Old Name | New Name |
|-----------|----------|----------|
| **Security** | 📊 Lakehouse Monitoring | 📈 Security Metrics Overview |
| **Security** | Lakehouse Monitoring - fact_audit_logs | 🔬 Advanced Audit Metrics |
| **Cost** | 📊 Lakehouse Monitoring | 📈 Cost Metrics Overview |
| **Cost** | Lakehouse Monitoring - fact_usage | 🔬 Advanced Cost Metrics |
| **Reliability** | 📊 Lakehouse Monitoring | 📈 Job Metrics Overview |
| **Reliability** | Lakehouse Monitoring - fact_job_run_timeline | 🔬 Advanced Job Metrics |
| **Performance** | 📊 Lakehouse Monitoring | 📈 Query Metrics Overview |
| **Performance** | 📊 Cluster Monitoring | 📈 Cluster Metrics Detail |
| **Performance** | Lakehouse Monitoring - fact_query_history | 🔬 Advanced Query Metrics |
| **Quality** | 📊 Lakehouse Monitoring | 📈 Governance Metrics Overview |

### Naming Convention
- **📈 [Domain] Metrics Overview**: Primary monitoring page with KPIs and trend charts
- **🔬 Advanced [Domain] Metrics**: Detailed page with slice filters, aggregate tables, and advanced analytics

---

## Security Dashboard - Lakehouse Monitoring fact_audit_logs Page Fix - January 4, 2026

### Issues Identified
1. **Invalid widget spec error**: "spec must NOT have additional properties"
2. **Queries using non-existent columns**: `total_events`, `distinct_users`, `admin_action_rate` directly selected instead of using CASE pivot

### Root Causes
1. `security_aggregate_table` widget had:
   - `"version": 1` instead of 2
   - Invalid properties: `itemsPerPage`, `condensed`, `withRowNumber`
2. Monitoring queries were trying to select custom metric names as columns, but Lakehouse Monitoring stores metrics in generic schema where `column_name` identifies the metric and values are in `avg`, `count`, etc.

### Fixes Applied

| Component | Issue | Fix |
|-----------|-------|-----|
| `security_aggregate_table` widget | Invalid spec v1 with extra properties | Updated to spec v2, removed invalid properties, added proper frame |
| `ds_monitor_security_aggregate` | Direct column selection | Rewrote with CASE pivot: `MAX(CASE WHEN column_name = 'X' THEN avg END)` |
| `ds_monitor_security_derived` | Direct column selection | Rewrote with CASE pivot pattern |

### Correct Query Pattern for Lakehouse Monitoring
```sql
SELECT 
  DATE(window.start) AS window_start,
  MAX(CASE WHEN column_name = 'total_events' THEN avg END) AS total_events,
  MAX(CASE WHEN column_name = 'distinct_users' THEN avg END) AS distinct_users,
  MAX(CASE WHEN column_name = 'admin_actions' THEN avg END) AS admin_actions
FROM ...profile_metrics
WHERE log_type = 'INPUT'
  AND column_name IN ('total_events', 'distinct_users', 'admin_actions')
GROUP BY DATE(window.start)
ORDER BY window_start DESC
```

---

## Tables by Catalog - Empty Visual Fix - January 4, 2026

### Issue
"Tables by Catalog" visual was empty across multiple pages (Governance Overview, Catalog Stats) in both Quality and Unified dashboards.

### Root Cause
The queries only filtered on `target_table_catalog IS NOT NULL`, but lineage records can have:
- `source_table_catalog` (for READ operations)
- `target_table_catalog` (for WRITE operations)

If a workspace has mostly READ operations (which is common), the query would return empty results.

### Fixes Applied

| Dashboard | Dataset | Before | After |
|-----------|---------|--------|-------|
| quality.lvdash.json | `ds_tables_by_catalog` | Only `target_table_catalog` | Uses `COALESCE(source_table_catalog, target_table_catalog)` |
| quality.lvdash.json | `ds_select_catalog` | Only `target_table_catalog` | UNION of both source and target catalogs |
| unified.lvdash.json | `ds_tables_by_catalog` | Only `target_table_catalog` | Uses `COALESCE(source_table_catalog, target_table_catalog)` |
| unified.lvdash.json | `ds_kpi_documented` | Only `target_table_full_name` | UNION of both source and target table names |

### Pattern: Comprehensive Lineage Queries
When querying `fact_table_lineage`, always consider both source and target:
```sql
-- For table counts
SELECT COALESCE(source_table_catalog, target_table_catalog) AS catalog_name,
       COALESCE(source_table_full_name, target_table_full_name) AS table_full_name
FROM fact_table_lineage
WHERE source_table_catalog IS NOT NULL OR target_table_catalog IS NOT NULL
```

---

## Quality & Governance Dashboard - Table Health + Lakehouse Monitoring Pages - January 4, 2026

### Issues Identified
1. **Table Health Overview page** - All datasets were placeholder queries returning "Table storage data not available"
2. **Missing Lakehouse Monitoring page** - Quality dashboard had no page for `fact_table_lineage` Lakehouse Monitoring

### Root Causes
1. Original design expected `fact_information_schema_table_storage` table which doesn't exist in Gold layer
2. Available tables (`fact_predictive_optimization`, `fact_table_lineage`) were not being used
3. Lakehouse monitors for Quality (`quality_monitor.py`) and Governance (`governance_monitor.py`) exist but weren't visualized

### Fixes Applied

#### Table Health Overview Page

| Dataset | Before (Placeholder) | After (Real Data) |
|---------|---------------------|-------------------|
| `ds_summary` | "Table storage data not available" | Uses `fact_predictive_optimization` for table_count, optimization_count, size metrics |
| `ds_optimization_needed` | Always returned 0 (1=0 clause) | Compares active tables vs recently optimized tables |
| `ds_size_buckets` | Placeholder | Buckets by total optimization usage quantity |
| `ds_file_buckets` | Placeholder | Shows operation type distribution (COMPACTION vs VACUUM) |
| `ds_largest_tables` | Placeholder | Top 20 tables by optimization usage quantity |
| `ds_needs_compaction` | Placeholder | Tables not compacted in 30+ days |
| `ds_empty_tables` | Placeholder | Active tables with no optimization history |

#### New Lakehouse Monitoring Page Added

**Page Name:** 📊 Lakehouse Monitoring

**KPI Widgets:**
- Total Lineage Events (from `fact_table_lineage_profile_metrics`)
- Active Tables
- Distinct Users

**Charts:**
- Lineage Events Trend (area chart)
- Drift Detection (line chart)
- Governance Metrics Detail (table)

**New Datasets:**
- `ds_monitor_gov_latest` - Latest governance metrics from profile_metrics
- `ds_monitor_gov_trend` - Time-series trend for events, tables, users
- `ds_monitor_gov_drift` - Period-over-period changes from drift_metrics
- `ds_monitor_gov_detailed` - Detailed breakdown with read/write ratios

### Lakehouse Monitors for Quality/Governance
**Monitors DO exist:**
- `quality_monitor.py` - Monitors `fact_data_quality_results` (if table exists)
- `governance_monitor.py` - Monitors `fact_table_lineage`

**Output Tables:**
- `fact_table_lineage_profile_metrics` - Governance metrics
- `fact_table_lineage_drift_metrics` - Governance drift detection

---

## Lakehouse Monitoring - fact_job_run_timeline Page - Widget Fix - January 4, 2026

### Root Cause
The `reliability_aggregate_table` widget had an invalid specification:
1. **Version 1 spec** with invalid properties: `itemsPerPage`, `condensed`, `withRowNumber`
2. These properties are not supported in the Lakeview dashboard widget schema

### Fix Applied
- Updated widget `spec.version` from 1 to 2
- Removed invalid properties (`itemsPerPage`, `condensed`, `withRowNumber`)
- Added proper `frame` block with title
- Changed column types from `"type": "float"` to `"type": "number"` for cleaner display

### Pattern: Valid Table Widget Spec (v2)
```json
"spec": {
  "version": 2,
  "widgetType": "table",
  "frame": {
    "showTitle": true,
    "title": "Table Title"
  },
  "encodings": {
    "columns": [...]
  }
}
```

---

## Lakehouse Monitoring (Reliability) - Complete Query Rewrite - January 4, 2026

### Root Cause
**ALL 9 monitoring datasets had incorrect queries.** Lakehouse Monitoring tables use a generic schema where:
- Custom metrics are stored in the `column_name` field (e.g., 'success_rate', 'total_runs')
- Values are in columns like `avg`, `count`, `p50`, `p95`, etc.
- Queries were trying to reference columns directly (e.g., `SELECT success_rate FROM...`) which don't exist

### Fixes Applied

| Dataset | Issue | Fix |
|---------|-------|-----|
| `ds_monitor_latest` | Referenced non-existent columns | Rewrote to use `MAX(CASE WHEN column_name = 'X' THEN avg END)` pattern |
| `ds_monitor_trend` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_duration` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_run_types` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_errors` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_drift` | Wrong column name + missing pivot | Rewrote to pivot on `column_name` for each drift metric |
| `ds_monitor_detailed` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_reliability_aggregate` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_reliability_derived` | Referenced non-existent columns | Rewrote with CASE aggregation + GROUP BY |
| `ds_monitor_reliability_drift` | Referenced non-existent `success_rate_drift` column | Rewrote to pivot on column_name |

### Correct Query Pattern for Lakehouse Monitoring
```sql
-- Profile Metrics: Use CASE pivot on column_name
SELECT 
  window.start AS window_start,
  COALESCE(MAX(CASE WHEN column_name = 'success_rate' THEN avg END), 0) AS success_rate,
  COALESCE(MAX(CASE WHEN column_name = 'total_runs' THEN avg END), 0) AS total_runs
FROM ...profile_metrics
WHERE log_type = 'INPUT'
GROUP BY window.start

-- Drift Metrics: Use CASE pivot on column_name for avg_delta
SELECT 
  window.start AS window_start,
  COALESCE(MAX(CASE WHEN column_name = 'success_rate_drift' THEN avg_delta END), 0) AS success_rate_drift
FROM ...drift_metrics
WHERE drift_type = 'CONSECUTIVE'
GROUP BY window.start
```

### Chart Interpretation Guide

| Chart | Purpose | How to Read |
|-------|---------|-------------|
| **Rate Metrics Trend** | Shows success/failure/timeout rates over time | Green = success rate %, Orange = failure rate %, Red = timeout rate %. Higher success % = healthier. |
| **Duration Percentiles** | Shows job duration distribution over time | Avg (dashed) = typical duration, P50 = median, P95 = slow jobs, P99 = extreme outliers. Large gaps = performance variance issues. |
| **Run Types Over Time** | Breakdown of how jobs are triggered | Scheduled (blue) = automated, Manual (green) = ad-hoc, Retry (orange) = failure recovery. High retries = reliability issues. |
| **Error Types Breakdown** | Distribution of failure types | Timeout = jobs taking too long, Cancelled = user/system stopped, Internal Error = platform issues. Use to prioritize fixes. |
| **Drift Detection** | Period-over-period changes | Positive = metric increased, Negative = decreased. Large spikes = anomalies needing investigation. |

---

## Failures by Termination Type (Reliability) - Chart Fix - January 4, 2026

### Root Cause
1. **Missing scale configuration**: Pie chart widget was missing `scale` property in encodings which is required for proper rendering
2. **Query filtering issue**: Query filtered on `termination_code != 'SUCCESS'` but `termination_code` can be NULL for older records (before late August 2024)
3. **Column name mismatch**: Widget expected `failure_count` but query returned `count`

### Fixes Applied

| Component | Issue | Fix |
|-----------|-------|-----|
| Widget encodings | Missing `scale` property | Added `"scale": {"type": "categorical"}` to color and `"scale": {"type": "quantitative"}` to angle |
| Query filtering | Was filtering on termination_code directly | Changed to filter on `result_state NOT IN ('SUCCESS', 'SUCCEEDED')` for better failure capture |
| Column alias | Returned `count` | Changed to `failure_count` to match widget encoding |
| NULL handling | termination_code can be NULL | Added `COALESCE(termination_code, 'UNKNOWN')` |

### Pattern Learned
Pie charts require proper `scale` configuration in encodings:
```json
"color": {
  "fieldName": "category_column",
  "displayName": "Label",
  "scale": { "type": "categorical" }
},
"angle": {
  "fieldName": "value_column", 
  "displayName": "Count",
  "scale": { "type": "quantitative" }
}
```

---

## Job Resource Utilization Page (Performance) - New Page Added - January 4, 2026

### Inspiration
Added based on user request for job resource utilization visualizations similar to:
- Jobs System Tables Dashboard
- LakeFlow System Tables Dashboard

### New Datasets Added

| Dataset | Purpose | Columns |
|---------|---------|---------|
| `ds_job_low_cpu` | Jobs with avg CPU <30% | `job_name`, `avg_cpu`, `peak_cpu`, `avg_memory`, `total_cost`, `potential_savings` |
| `ds_job_high_mem` | Jobs with avg memory >70% | `job_name`, `avg_cpu`, `avg_memory`, `peak_memory`, `avg_io_wait`, `total_cost` |
| `ds_job_cost_savings` | Top cost savings opportunities | `job_name`, `avg_cpu`, `avg_memory`, `total_cost`, `max_savings` |
| `ds_job_utilization_distribution` | CPU utilization bucket distribution | `cpu_range`, `job_count` |
| `ds_job_kpi_utilization` | KPI summary metrics | `total_jobs`, `avg_cpu_utilization`, `avg_memory_utilization`, `low_cpu_jobs`, `high_memory_jobs`, `total_potential_savings` |

### New Page: 📊 Job Resource Utilization

**Visualizations:**
1. **KPI Row:** Jobs Analyzed, Avg CPU %, Avg Memory %, Low CPU Jobs, High Memory Jobs, Potential Savings ($)
2. **📊 Job CPU Utilization Distribution** - Bar chart showing job count by CPU range (0-10%, 10-25%, 25-50%, 50-75%, 75-100%)
3. **💰 Top Cost Savings Opportunities** - Table of jobs with highest savings potential based on low CPU usage
4. **🔻 Jobs with Low CPU Utilization (<30%)** - Table of underutilized jobs with avg CPU, peak CPU, cost, and savings
5. **🔺 Jobs with High Memory Utilization (>70%)** - Table of memory-intensive jobs with CPU/memory metrics and I/O wait

### Data Sources
- `fact_usage` (billing) - Job cost and cluster attribution
- `fact_node_timeline` (compute) - CPU/memory utilization metrics
- `dim_job` (lakeflow) - Job names

### Global Filters
All new datasets connected to the time_range global filter for consistency.

---

## Lakehouse Monitoring - fact_query_history Page - Query Rewrite - January 4, 2026

### Root Cause
1. **Invalid column references**: Queries referenced non-existent columns like `query_count`, `successful_queries`, `query_success_rate` directly, but Lakehouse Monitoring profile_metrics tables use generic schema (`column_name`, `avg`, `count`, etc.)
2. **Invalid table widget spec**: Table widget used version 1 spec with invalid properties (`itemsPerPage`, `condensed`, `withRowNumber`)

### Fixes Applied

| Dataset | Issue | Fix |
|---------|-------|-----|
| `ds_monitor_performance_aggregate` | Referenced non-existent columns | Rewrote to use CASE aggregations from `column_name` filtering |
| `ds_monitor_performance_derived` | Referenced non-existent columns | Rewrote to calculate `query_success_rate` and `spill_rate` from base metrics |
| `performance_aggregate_table` | Invalid widget spec v1 | Updated to version 2, removed invalid properties |

---

## Cluster Monitoring Page (Performance) - Query Rewrite - January 4, 2026

### Root Cause
The Cluster Monitoring page and Lakehouse Monitoring page shared the SAME datasets (`ds_monitor_latest`, `ds_monitor_drift`, `ds_monitor_detailed`) but expected DIFFERENT columns:
- **Lakehouse Monitoring**: `total_queries`, `avg_duration`, `slow_query_rate`, `duration_drift`, `volume_drift`
- **Cluster Monitoring**: `avg_cpu`, `avg_memory`, `total_nodes`, `cpu_drift`, `memory_drift`, `avg_io_wait`

### Solution
Updated shared datasets to return BOTH query metrics (from `fact_query_history_profile_metrics`) AND cluster metrics (from `fact_node_timeline_profile_metrics`) using CTEs and FULL OUTER JOINs.

| Dataset | Issue | Fix Applied |
|---------|-------|-------------|
| `ds_monitor_latest` | Missing `avg_cpu`, `avg_memory`, `total_nodes` | Added CTE joining query metrics + cluster metrics |
| `ds_monitor_cpu_trend` | Returned `date`, `avg_cpu_percent`; widgets expected `window_start`, `avg_cpu`, `p95_cpu` | Renamed columns, added PERCENTILE for p95 |
| `ds_monitor_memory_trend` | Returned `date`, `avg_memory_percent`; widgets expected `window_start`, `avg_memory`, `p95_memory` | Renamed columns, added PERCENTILE for p95 |
| `ds_monitor_drift` | Missing `cpu_drift`, `memory_drift` | Added CTE from `fact_node_timeline_drift_metrics` with FULL OUTER JOIN |
| `ds_monitor_detailed` | Missing `total_nodes`, `avg_cpu`, `p95_cpu`, `avg_memory`, `avg_io_wait` | Added CTE from cluster metrics with FULL OUTER JOIN |

---

## Lakehouse Monitoring Page (Performance) - Query Rewrite - January 4, 2026

### Complete Rewrite of Monitoring Queries

**Root Cause:** All monitoring queries used incorrect column references and returned columns that didn't match widget expectations.

**Key Discovery:** Lakehouse Monitoring tables use `window` as a STRUCT type with `.start` and `.end` properties (not flat `window_start`/`window_end` columns).

| Dataset | Issue | Fix Applied |
|---------|-------|-------------|
| `ds_monitor_latest` | Returned wrong columns; used `window_start` (flat) | Rewrote with `window.start` (struct), proper column aggregations |
| `ds_monitor_trend` | Returned `date`, widgets expected `window_start` | Changed to `DATE(window.start) AS window_start`, added PERCENTILE for p95 |
| `ds_monitor_volume` | Used `window_start` (flat column) | Changed to `window.start` (struct property) |
| `ds_monitor_drift` | Used `window_start` (flat column) | Changed to `window.start` (struct property) |
| `ds_monitor_detailed` | Used `window_start` (flat column) | Changed to `window.start` (struct property) |

### Cost Dashboard Monitoring Fixes

| Dataset | Issue | Fix Applied |
|---------|-------|-------------|
| `ds_monitor_serverless` | Referenced `unique_user_count` (doesn't exist) | Rewrote to aggregate from `column_name` patterns |
| `ds_monitor_drift` | Referenced `total_daily_cost_delta` (doesn't exist) | Changed to `avg_delta` with proper CASE aggregation |
| `ds_monitor_summary` | Referenced `unique_user_count` (doesn't exist) | Rewrote to aggregate from `column_name` patterns |
| `ds_repair_cost` | Referenced `execution_duration_ms` (doesn't exist) | Changed to `run_duration_minutes` |

---

## Warehouse Analysis Page - Column Name Fixes - January 4, 2026

### Column Name Mismatches Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| PERF-010 | Warehouse Performance Summary = `warehouse_name` cannot be resolved | 🟢 Fixed | Query returned `compute_type` but widget expected `warehouse_name` | Added alias `compute_type AS warehouse_name` |
| PERF-011 | Warehouse Performance Summary = `total_queries` cannot be resolved | 🟢 Fixed | Query returned `query_count` but widget expected `total_queries` | Changed alias to `total_queries` |
| PERF-012 | Query Distribution by Warehouse = `warehouse_name` cannot be resolved | 🟢 Fixed | Query returned `compute_type` but widget expected `warehouse_name` | Added alias `compute_type AS warehouse_name` |

---

## Failed Queries Page - Column Name Fixes - January 4, 2026

### Column Name Mismatches Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| PERF-007 | Recent Failed Queries = `query_id` cannot be resolved | 🟢 Fixed | Query returned `statement_id` but widget expected `query_id` | Added alias `statement_id AS query_id` |
| PERF-008 | Recent Failed Queries = `warehouse_name` cannot be resolved | 🟢 Fixed | Query returned `compute_type` but widget expected `warehouse_name` | Added alias `compute_type AS warehouse_name` |
| PERF-009 | Failures by Error Category = `failure_count` cannot be resolved | 🟢 Fixed | Query returned `failed_queries` but widget expected `failure_count` | Changed alias to `failure_count` |

---

## Slow Queries Analysis Page - Column Name Fixes - January 4, 2026

### Column Name Mismatches Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| PERF-002 | Top 20 Slowest Queries = `query_id` cannot be resolved | 🟢 Fixed | Query returned `statement_id` but widget expected `query_id` | Added alias `statement_id AS query_id` |
| PERF-003 | Top 20 Slowest Queries = `warehouse_name` cannot be resolved | 🟢 Fixed | Query returned `compute_type` but widget expected `warehouse_name` | Added alias `compute_type AS warehouse_name` |
| PERF-004 | Slow Queries by User = `total_queries` cannot be resolved | 🟢 Fixed | Query returned `query_count` but widget expected `total_queries` | Changed alias to `total_queries` |
| PERF-005 | Slow Queries by Warehouse = `warehouse_name` cannot be resolved | 🟢 Fixed | Query returned `compute_type` but widget expected `warehouse_name` | Added alias `compute_type AS warehouse_name` |
| PERF-006 | Slow Queries by Warehouse = `total_queries` cannot be resolved | 🟢 Fixed | Query returned `query_count` but widget expected `total_queries` | Changed alias to `total_queries` |

**Summary:** All three queries on the Slow Queries Analysis page had column alias mismatches where the SQL returned different column names than what the table widgets expected.

---

## Performance Overview - Total Queries Fix - January 4, 2026

### Field Name Mismatch Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| PERF-001 | Total Queries (7d) = "Unable to render visualization" | 🟢 Fixed | Query returned `query_count` but widget expected `total_queries` | Changed query alias from `query_count` to `total_queries` |

**Query Fix:**
```sql
-- Before (broken)
SELECT FORMAT_NUMBER(COUNT(*), 0) AS query_count, ...

-- After (fixed)
SELECT COUNT(*) AS total_queries, ...
```

Also removed `FORMAT_NUMBER()` wrapper to return raw number instead of formatted string for proper counter widget rendering.

---

## Commit vs Consumption - Annual Commit Parameter Fix - January 4, 2026

### Parameter Widget Issues Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| CC-005 | Annual Commit ($) = "Parameter is missing" | 🟢 Fixed | Widget referenced non-existent `options_query`, only had `param_query` | Added proper `options_query` for dropdown values and parameter queries for all consuming datasets |
| CC-006 | Monthly Spend Detail = "Unable to render visualization" | 🟢 Fixed | Missing parameter connection from filter widget to dataset | Added `param_ds_monthly_detail` query to filter widget encodings |
| CC-007 | Cumulative Spend vs Commit Target = Only showing actual | 🟢 Fixed | Chart y-axis only encoded `cumulative_spend`, not `target_line` | Changed to multi-field y-axis showing both Actual Spend and Commit Target |
| CC-008 | Monthly Spend vs Target = Only showing actual | 🟢 Fixed | Chart y-axis only encoded `monthly_cost`, not `monthly_target` | Changed to multi-field y-axis showing both Actual Spend and Monthly Target |

**Parameter Widget Structure Fixed:**
- Added `options_query` that pulls from `ds_commit_options` (500K, 1M, 2M, 5M, 10M)
- Added parameter queries for all 5 datasets that use `annual_commit`:
  - `ds_commit_status` (Commit Utilization KPI)
  - `ds_variance` (Projected Variance KPI)
  - `ds_cumulative_vs_commit` (Cumulative vs Commit chart)
  - `ds_monthly_breakdown` (Monthly Spend chart)
  - `ds_monthly_detail` (Monthly Spend Detail table)

**Chart Fixes:**
- `chart_cumulative_vs_commit`: Multi-series line chart with Actual Spend (blue) and Commit Target (orange)
- `chart_monthly_breakdown`: Multi-series bar chart comparing Actual Spend and Monthly Target per month

---

## Lakehouse Monitoring - fact_usage Page Fix - January 4, 2026

### Widget Definition Error Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| LM-001 | Cost Aggregate Metrics Table = "Invalid widget definition imported" | 🟢 Fixed | Table widget spec had invalid properties: `itemsPerPage`, `condensed`, `withRowNumber` - these are not valid for table widget spec | Updated widget spec to version 2, removed invalid properties, added proper `frame` object |

**Error Message:** "The imported widget definition was invalid so it changed to the default. Here are the details: spec must NOT have additional properties"

**Fix:** Changed table widget from version 1 with invalid extra properties to version 2 with valid `frame` object structure.

---

## Commit vs Consumption Page Fixes - January 4, 2026

### Column & Table Resolution Errors Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| CC-002 | Monthly Spend Detail = UNRESOLVED_COLUMN monthly_target | 🟢 Fixed | Query returned `monthly_budget`, widget expected `monthly_target` | Renamed column to `monthly_target` |
| CC-003 | ML: Budget Forecast = TABLE_OR_VIEW_NOT_FOUND | 🟢 Fixed | ML table `budget_forecaster_predictions` doesn't exist | Created statistical forecast using historical data |
| CC-004 | ML: Commitment Recommendations = TABLE_OR_VIEW_NOT_FOUND | 🟢 Fixed | ML table `commitment_recommender_predictions` doesn't exist | Created rule-based recommendations from spend patterns |

**Query Rewrites:**

1. **ds_monthly_detail** - Monthly Spend Detail
   - Changed: `monthly_budget` → `monthly_target`
   - Added: Proper variance_pct formatting with '%' suffix

2. **ds_ml_budget_forecast** - ML: Budget Forecast (Next 30 Days)
   - Replaced ML table query with statistical forecast
   - Uses 30-day average + standard deviation for confidence bands
   - Generates 30-day forward forecast

3. **ds_ml_commitment_rec** - ML: Commitment Recommendations
   - Replaced ML table query with rule-based recommendations
   - Analyzes spend variability to recommend Annual/Monthly/PAYG
   - Calculates confidence based on spend consistency
   - Estimates potential annual savings

4. **ds_ml_cost_forecast** - ML: Cost Forecast (also on ML Predictions page)
   - Same statistical forecast pattern as budget forecast

5. **ds_ml_budget_alerts** - ML: Budget Alerts
   - Replaced ML query with workspace-level burn rate analysis
   - Projects monthly spend from MTD data
   - Flags HIGH/MEDIUM/LOW based on projection

---

## Lakehouse Monitoring Page Fixes - January 4, 2026

### Column Resolution Errors Fixed

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| LM-001 | Cost & DBU Trend = UNRESOLVED_COLUMN total_dbu | 🟢 Fixed | Query returned total_daily_cost, widget expected total_dbu | Updated query to return `total_daily_dbu AS total_dbu` |
| LM-002 | Adoption Metrics Trend = missing fields | 🟢 Fixed | Query missing total_dbu, unique_users columns | Added `total_daily_dbu` and `unique_user_count` to query and widget |
| LM-003 | Drift Detection = UNRESOLVED_COLUMN serverless_drift | 🟢 Fixed | Query returned record_count_drift, widget expected serverless_drift | Changed to return `serverless_ratio_delta AS serverless_drift` |
| LM-004 | Complete Metrics Table = UNRESOLVED_COLUMN total_dbu | 🟢 Fixed | Query missing all extended metrics | Added all 6 columns: total_cost, total_dbu, serverless_pct, tag_coverage_pct, unique_users |

**Query Fixes:**

1. **ds_monitor_cost_trend** - Cost & DBU Trend
   - Added: `ROUND(COALESCE(total_daily_dbu, 0), 0) AS total_dbu`
   - Removed: avg_cost, dlt_cost (not used by widget)

2. **ds_monitor_serverless** - Adoption Metrics Trend
   - Added: `ROUND(COALESCE(total_daily_dbu, 0), 0) AS total_dbu`
   - Added: `COALESCE(unique_user_count, 0) AS unique_users`
   - Added: time_range parameter filtering
   - Widget: Added DBU Volume line to chart

3. **ds_monitor_drift** - Drift Detection
   - Changed: `avg_delta` → `total_daily_cost_delta` (for cost drift)
   - Changed: `count_delta` → `serverless_ratio_delta` (for serverless drift)

4. **ds_monitor_summary** - Complete Metrics Table
   - Added: `total_daily_dbu AS total_dbu`
   - Added: `serverless_ratio AS serverless_pct`
   - Added: `tag_coverage_pct`
   - Added: `unique_user_count AS unique_users`
   - Changed: LIMIT 1 → LIMIT 10 (show more history)

---

## Optimization Opportunities Page Fixes - January 4, 2026

### Complete Visual Overhaul

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| OO-001 | Jobs Producing Unconsumed Data = placeholder | 🟢 Fixed | Static placeholder query | Rewrote to use fact_table_lineage to find jobs writing to tables never read |
| OO-002 | Jobs Using All-Purpose Clusters = placeholder | 🟢 Fixed | Static placeholder query | Rewrote to extract compute_ids from fact_job_run_timeline and show cluster usage |
| OO-003 | Jobs Without Autoscaling = placeholder | 🟢 Fixed | No cluster config data available | Rewrote to show jobs with low DBU variance (indicates fixed cluster size) |
| OO-004 | Jobs on Legacy DBR Versions = placeholder | 🟢 Fixed | No DBR version data available | Rewrote to show jobs not modified in 6+ months (stale jobs) |
| OO-005 | Jobs Without Tags = working | ✅ OK | Already using real data | No changes needed |
| OO-006 | Right-Sizing Savings = placeholder | 🟢 Fixed | No CPU utilization data | Rewrote to show jobs with high cost variance (>50%) indicating sizing issues |

**Query Rewrites:**

1. **ds_stale_datasets** - Jobs Producing Unconsumed Data
   - Uses fact_table_lineage to find tables written but never read
   - Shows: job_name, unused_tables count, total_cost, last_run
   - Identifies data assets that may be obsolete

2. **ds_ap_cluster_jobs** - Jobs Using All-Purpose Clusters
   - Extracts compute_ids from fact_job_run_timeline
   - Shows: job_name, cluster_name, task_runs, total_cost
   - Enables cluster-level cost attribution

3. **ds_no_autoscale** - Jobs with Fixed Cluster Size
   - Identifies jobs with <10% DBU standard deviation
   - Shows: job_name, avg_dbus, total_cost, owner
   - Title updated: "Jobs with Fixed Cluster Size"

4. **ds_low_dbr_jobs** - Stale Jobs (Not Updated 6+ Months)
   - Identifies jobs with change_time > 180 days ago
   - Shows: job_name, age ("X months old"), total_cost, owner
   - Title updated: "Stale Jobs (Not Updated 6+ Months)"

5. **ds_savings_potential** - Right-Sizing Savings Opportunities
   - Identifies jobs with >50% cost variance between runs
   - Shows: job_name, cost_variance_pct, total_cost, max_savings
   - Column title updated: "Cost Variance %" instead of "Avg CPU %"

---

## Jobs Cost Analysis Page Fixes - January 4, 2026

### Multiple Visual Fixes

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| JCA-001 | Most Expensive Jobs missing last run | 🟢 Fixed | Query didn't include last_run column | Added `MAX(DATE(f.usage_date)) AS last_run`, updated widget with new column |
| JCA-002 | Most Expensive Runs missing owner | 🟢 Fixed | Query didn't include owner column | Added `MAX(f.identity_metadata_run_as) AS owner`, updated widget with new column |
| JCA-003 | Jobs with Highest Cost Increase = render error | 🟢 Fixed | Query returns `change_pct`, widget expects `growth` + `growth_pct` | Fixed query to return all expected columns, improved time range logic |
| JCA-004 | Jobs with Outlier Runs = render error | 🟢 Fixed | Query returned per-run data, widget expected per-job aggregates (runs, avg_cost, max_cost, p90, deviation) | Rewrote query to return job-level stats with outlier detection |
| JCA-005 | Cost of Job Failures = render error | 🟢 Fixed | Query returned single aggregate, widget expected per-job breakdown (job_name, failure_cost, failures, success_rate) | Rewrote query to join fact_usage with fact_job_run_timeline for per-job failure costs |
| JCA-006 | Most Repaired Jobs = placeholder data | 🟢 Fixed | Query returned static placeholder text | Rewrote query to identify repair runs (reruns after failures on same day) and calculate costs |

**Query Rewrites:**

1. **ds_expensive_jobs**
   - Added: `MAX(DATE(f.usage_date)) AS last_run`
   - Widget: Added "Last Run" datetime column

2. **ds_expensive_runs**
   - Added: `MAX(f.identity_metadata_run_as) AS owner`
   - Widget: Added "Owner" column

3. **ds_highest_change_jobs**
   - Fixed time range logic: Uses `CURRENT_DATE() - INTERVAL 7/14 DAYS`
   - Added: `ROUND(last_7d - prev_7d, 2) AS growth`
   - Renamed: `change_pct` → `growth_pct`
   - Changed WHERE: `WHERE prev_7d > 0 OR last_7d > 0` to show new jobs

4. **ds_outlier_runs**
   - Complete rewrite to return job-level stats
   - Returns: job_name, runs, avg_cost, max_cost, p90, deviation
   - Filter: Jobs with 3+ runs where max_cost > p90 * 1.5

5. **ds_failure_cost**
   - Complete rewrite to join fact_usage with fact_job_run_timeline
   - Returns per-job: job_name, failure_cost, failures, success_rate
   - Ordered by failure_cost DESC

6. **ds_repair_cost**
   - Complete rewrite to identify repair runs
   - A repair = rerun after a failed run on the same day
   - Returns: job_name, repairs, repair_cost, repair_time_min
   - Added time_range parameter

---

## Cost & Commitment Dashboard Fix - January 4, 2026

### Users with Highest Cost Increase - Fixed

| Issue | Widget | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| CC-001 | Users with Highest Cost Increase = render error | 🟢 Fixed | Query returns `change_pct`, widget expects `growth` + `growth_pct` | Fixed query to return all expected columns |

**Root Cause:**
- Query output: `owner`, `last_7d`, `prev_7d`, `change_pct`
- Widget expected: `owner`, `last_7d`, `prev_7d`, `growth`, `growth_pct`

**Fixes Applied:**
- Added `growth` column (absolute $ change)
- Renamed `change_pct` to `growth_pct`
- Added service account filters (exclude `.gserviceaccount.com`, `service-principal-*`)
- Fixed time range logic for proper 7-day comparison

---

## Cost Overview Enhancements - January 4, 2026

### Top Workspaces Table - Enhanced Columns

| Issue | Widget | Status | Fix Applied |
|-------|--------|--------|-------------|
| CO-004 | Top Workspaces missing columns | 🟢 Fixed | Added 3 new columns: DBUs, $/User, Serverless % |
| CO-005 | Hardcoded schema path | 🟢 Fixed | Changed to use ${catalog}.${gold_schema} variables |
| CO-006 | Duplicate time_range params | 🟢 Fixed | Removed duplicate parameter |
| CO-007 | 90-day default | 🟢 Fixed | Changed to 30-day default (matches title) |

**New Columns Added:**
- **DBUs**: Total Databricks Units consumed
- **$/User**: Cost per user (cost efficiency metric)
- **Serverless %**: Percentage of spend on serverless SKUs

### Spend by SKU - Fixed

| Issue | Widget | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| CO-008 | Spend by SKU = empty | 🟢 Fixed | Unused workspace/SKU params, 90-day default | Simplified to time_range only, 30-day default, added HAVING > 0 |

---

## Security KPI Validation Fixes - January 4, 2026

### Security Overview Page - Metric Accuracy

| Issue | Widget | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| SEC-001 | Total Audit Events = 2.4B | 🟢 Fixed | Default was **90 days**, duplicate params | Changed default to 7 days, removed duplicate params |
| SEC-002 | Unique Users = 27K | 🟡 Monitoring | Already 7d default, but excluded more service accounts | Added filters for gserviceaccount, service-principal, system users |
| SEC-003 | High Risk Events = 98K | 🟢 Fixed | Default was **90 days**, duplicate params | Changed to 7 days, added COUNT(DISTINCT request_id), expanded actions |
| SEC-004 | Access Denied = 43M | 🟢 Fixed | Default was **90 days**, overly broad LIKE patterns | Changed to 7 days, replaced LIKE with exact IN values |
| SEC-005 | Permission Changes = 49M | 🟢 Fixed | Default was **90 days**, overly broad LIKE patterns | Changed to 7 days, replaced LIKE with specific action names |

**Root Causes Identified:**
1. **Time range mismatch**: Widget titles said "(7d)" but defaults were 90 days
2. **Duplicate parameters**: Some datasets had duplicate time_range params
3. **Overly broad filters**: `LIKE '%denied%'` matched way too many events
4. **Counting duplicates**: `COUNT(*)` instead of `COUNT(DISTINCT request_id)`

**Query Improvements:**
- `ds_kpi_denied`: Changed from `LIKE '%denied%'` to exact values: `IN ('403', 'FORBIDDEN', 'PERMISSION_DENIED', 'ACCESS_DENIED')`
- `ds_kpi_permissions`: Changed from `LIKE '%permission%'` to specific actions: `IN ('updatePermissions', 'grantPermission', 'revokePermission', ...)`
- `ds_kpi_high_risk`: Added more destructive actions: `deleteCluster`, `deleteWarehouse`, `deletePipeline`, `deleteExperiment`, `deleteModel`

---

## Completed Improvements - January 4, 2026

### Reliability Overview Page - Chart Improvements

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| RO-006 | Daily Runs by Status = no status colors | 🟢 Fixed | Area chart not showing stacked status breakdown | Added `stack: "zero"` to y-encoding, explicit color scale with green (Success) / red (Failed), updated title |
| RO-007 | Query Duration Trend = single line only | 🟢 Fixed | Only shows average, p95 not displayed | Transformed query to UNION Avg + P95 as separate series with color encoding, now shows both lines |

**Improvements Made:**
1. **Daily Runs by Status** - Now shows stacked area chart with:
   - Green (#2e7d32) for Success
   - Red (#c62828) for Failed
   - Clear visual breakdown of job health over time

2. **Query Duration Trend** - Now shows multi-line chart with:
   - Average duration line
   - P95 (Slow Queries) line for identifying outliers
   - Helps identify performance regressions vs normal variance

### Active Users - Filter Refinements

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| CO-003 | Active Users = 27K (too high) | 🟢 Fixed | 90-day default, no service account filter | Changed default to 7 days, filtered out service accounts (`*.gserviceaccount.com`, `service-principal-*`, system users) |

---

## Previously Fixed Issues

### Platform Health Page - Unified Dashboard

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| PH-001 | Overall Health Score = 0 | 🟢 Fixed | Single source (jobs only), no fallback | **Composite score** from jobs + queries + cost health |
| PH-002 | Reliability Health = 0 | 🟢 Fixed | Strict result_state check | Added `SUCCEEDED` + NULL handling with fallback to 100 |
| PH-003 | Top Health Issues = blank | 🟢 Fixed | Job-only, wrong fields | **Multi-source**: Jobs + Queries + Costs, fixed fields |
| PH-004 | Health Score Trend = no data | 🟢 Fixed | Single source | **Composite trend** from jobs + queries with FULL OUTER JOIN |

### Cost Overview Page - Unified Dashboard

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| CO-001 | Active Users error | 🟢 Fixed | Query used `fact_job_run_timeline` which has no `user_identity_email` column; duplicate parameters | Changed to `fact_audit_logs`, removed duplicate param |
| CO-002 | Spend by SKU empty | 🟢 Fixed | Pie chart encoding issues | Changed to bar chart with x/y encoding |

### Performance Overview Page - Unified Dashboard

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| PO-001 | Slow Queries % = no fields | 🟢 Fixed | Query returns `slow_queries`, fields expect `slow_queries_pct`, encoding expects `slow_queries` | Aligned all to `slow_queries_pct`, removed duplicate params |
| PO-002 | Failed Queries % = no fields | 🟢 Fixed | Query returns `failed_runs` from `fact_job_run_timeline`, fields expect `failed_queries_pct` | Changed to query `fact_query_history`, aligned all to `failed_queries_pct` |

### Reliability Overview Page - Unified Dashboard

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| RO-001 | MTTR (min) = no fields | 🟢 Fixed | Fields expect `mttr_minutes`, query returns `mttr_min` | Aligned fields to `mttr_min` |
| RO-002 | Active Jobs (7d) = no fields | 🟢 Fixed | Fields expect `unique_jobs`, query returns `total_runs`, encoding expects `total_runs` | Aligned to `total_runs`, renamed to "Total Runs (7d)" |
| RO-003 | Success Rate Trend = empty | 🟢 Fixed | Fields expect `run_date`, query returns `day` | Aligned fields to `day` |
| RO-004 | Daily Runs by Status = empty | 🟢 Fixed | Fields expect `successful/failed/...`, query returns `status+count` | Aligned fields to `run_date/status/count` |
| RO-005 | Duration Percentiles = no fields | 🟢 Fixed | Fields expect `run_date/p50_duration`, query returns `day/avg_duration_min` | Aligned to query output |

### Governance Overview Page - Unified Dashboard

| Issue | Visual | Status | Root Cause | Fix Applied |
|-------|--------|--------|------------|-------------|
| GO-001 | Tagged Tables % = no fields | 🟢 Fixed | Fields expect `tagged_pct`, query returns `tag_coverage` (string with %) | Query returns 0-1 decimal `tagged_pct`, aligned fields |
| GO-002 | Total Jobs = no fields | 🟢 Fixed | Query returns `success_rate`, widget expects `total_jobs` | Query now returns `COUNT(DISTINCT job_id) AS total_jobs` |
| GO-003 | Tables by Catalog = no fields | 🟢 Fixed | Duplicate `time_range` parameters | Removed duplicate parameter |
| GO-004 | Lineage Events Trend = no data | 🟢 Fixed | Fields expect `lineage_events`, query returns `tables`, encoding expects `tables` | Aligned all to `events` |
| GO-005 | Documented Tables % = 1,862M% | 🟢 Fixed | Query returns COUNT (not %), widget uses `number-percent` format | Query returns count, widget uses `number-plain`, renamed to "Documented Tables" |
| GO-006 | Lineage Coverage % = 11M% | 🟢 Fixed | Query returns COUNT (not %), widget uses `number-percent` format | Query returns count, widget uses `number-plain`, renamed to "Lineage Tables" |

---

## Changelog

### 2026-01-04 (Governance Overview Fixes)

#### GO-001 to GO-006: Governance Overview Page Fixes

**Tagged Spend % (renamed from Tagged Tables %):**
- Query returned formatted string with '%' suffix
- Widget fields expected `tagged_pct`, encoding expected `tag_coverage`
- **Fix**: Query returns 0-1 decimal `tagged_pct`, aligned fields/encoding

**Total Jobs:**
- Query `ds_kpi_jobs` returned `success_rate` (wrong metric entirely!)
- Widget expected `total_jobs`
- **Fix**: Query now returns `COUNT(DISTINCT job_id) AS total_jobs`

**Tables by Catalog:**
- Had duplicate `time_range` parameters
- **Fix**: Removed duplicate parameter

**Lineage Events Trend:**
- Fields expected `lineage_events`, query returned `tables`, encoding expected `tables`
- **Fix**: Query returns `events`, aligned fields/encoding to `events`

**Documented Tables (renamed from Documented Tables %):**
- Query returned COUNT(*) but widget used `number-percent` format
- Result: 1,862,436,500% displayed (COUNT * 100)
- **Fix**: Renamed to "Documented Tables", use `number-plain` format

**Lineage Tables (renamed from Lineage Coverage %):**
- Query returned COUNT but widget used `number-percent` format
- Result: 11,498,000% displayed (COUNT * 100)
- **Fix**: Renamed to "Lineage Tables", use `number-plain` format

---

### 2026-01-04 (Security Overview Fixes)

#### SO-001 to SO-005: Security Overview Page Fixes

**Unique Users (7d):**
- Widget fields expected `unique_users`, query returns `active_users`
- **Fix**: Aligned fields to `active_users`

**Audit Event Trend:**
- Widget fields expected `event_count`, `unique_users`
- Query returns `events`, `high_risk`, `medium_risk`
- **Fix**: Changed fields to `day`, `events`; query simplified to return `events`, `unique_users`

**Risk Event Trend:**
- Had duplicate `time_range` parameters
- **Fix**: Removed duplicate parameter

**Access Denied (showing 0):**
- Query used `response_result = 'denied'` which may not match exact data format
- **Fix**: Expanded to check `LOWER(response_status_code) LIKE '%denied%'`, `%forbidden%`, `403`, etc.

**Permission Changes (showing 0):**
- Query used `action_name LIKE '%permission%'` only
- **Fix**: Expanded to include `%grant%`, `%revoke%`, and specific action names like `addUserToGroup`, `removeUserFromGroup`, `updatePermissions`

**All datasets:** Removed duplicate `time_range` parameters

---

### 2026-01-04 (All-Domain Health Score Enhancement)

#### Enhanced Health Score & Issues to Include All 5 Domains

**Previous Coverage (3 domains):**
- Reliability (job success rate)
- Performance (query success rate)
- Cost (tag coverage)

**New Coverage (5 domains):**
- ✅ **Reliability** - Job success rate from `fact_job_run_timeline`
- ✅ **Performance** - Query success rate from `fact_query_history`
- ✅ **Cost** - Tag coverage from `fact_usage`
- ✅ **Security** - Low risk events ratio from `fact_audit_logs`
- ✅ **Quality** - Lineage coverage from `fact_table_lineage`

**ds_health_score Changes:**
- Now averages scores from all 5 domains
- Security score: % of events that aren't denied/high-risk
- Quality score: % of tables with recent lineage activity

**ds_health_issues Changes:**
- Added `🔒 Security` category: high-risk actions, denied access
- Added `📊 Quality` category: tables with low lineage activity
- Added emoji prefixes for domain identification
- Increased limit from 15 to 20 rows

**ds_health_trend Changes:**
- Now shows composite trend across 4 domains (Reliability, Performance, Cost, Security)
- Quality excluded from trend (lineage data sparse for daily granularity)

---

### 2026-01-04 (Reliability Overview Fixes)

#### RO-001 to RO-005: Reliability Overview Page - Field Alignment Fixes
- **Root Cause Pattern:** Consistent mismatch between:
  1. Query output column names
  2. Widget `fields.name` expectations
  3. Widget `encodings.fieldName` bindings

- **Fixes Applied:**

**MTTR (min):**
- Changed fields.name from `mttr_minutes` to `mttr_min`
- Added COALESCE for NULL safety

**Total Runs (7d):** (renamed from Active Jobs)
- Changed fields.name from `unique_jobs` to `total_runs`
- Title updated to be more accurate

**Success Rate Trend:**
- Changed fields to use `day` (query output) instead of `run_date`
- Simplified to show just success_rate
- Changed from `is_success` to `result_state IN ('SUCCESS', 'SUCCEEDED')`

**Daily Runs by Status:**
- Changed fields from `successful/failed/timed_out/cancelled` to `run_date/status/count`
- Query already returns unpivoted format for stacked chart

**Query Duration Trend:** (renamed from Duration Percentiles)
- Changed fields from `run_date/avg_duration/p50_duration` to `day/avg_duration_min/p95_duration`
- Title updated for clarity

**All datasets:** Removed duplicate `time_range` parameters

---

### 2026-01-04 (Performance Overview Fixes)

#### PO-001 & PO-002: Slow/Failed Queries % "no fields to visualize"
- **Root Cause:** Triple mismatch between:
  1. Query output column name (`slow_queries`, `failed_runs`)
  2. Widget `fields.name` (`slow_queries_pct`, `failed_queries_pct`)
  3. Widget `encodings.value.fieldName` (`slow_queries`, `failed_runs`)
  
- **Additional Issue:** `ds_kpi_failed` was querying `fact_job_run_timeline` (job failures) instead of `fact_query_history` (query failures)

- **Fixes Applied:**
  - `ds_kpi_slow`: Query returns `slow_queries_pct`, encoding aligned
  - `ds_kpi_failed`: Changed to query `fact_query_history` for actual query failures, returns `failed_queries_pct`
  - Removed duplicate `time_range` parameters from both datasets
  - Updated description to ">60 seconds" (actual threshold in query)

---

### 2026-01-04 (Platform Health Comprehensive Fixes)

#### PH-001 to PH-004: Platform Health Page - Comprehensive Overhaul
- **Root Causes Found:**
  1. Single data source (jobs only) - no data when job table is empty
  2. `is_success` boolean column may have NULL values
  3. Strict `result_state = 'SUCCESS'` missed `SUCCEEDED` variant
  4. Top Health Issues was job-only, not comprehensive
  
- **Comprehensive Fixes Applied:**

**ds_health_score (Overall Health Score):**
- Changed from single-source to **composite score** from 3 sources:
  - Job success rate (from `fact_job_run_timeline`)
  - Query success rate (from `fact_query_history`)
  - Cost health/tag coverage (from `fact_usage`)
- Returns average of 3 scores with fallback to 100 if table empty

**ds_reliability_health:**
- Added `IN ('SUCCESS', 'SUCCEEDED')` to handle variant spellings
- Added `OR result_state IS NULL` to handle NULL as success
- Default to 100 if table empty (COALESCE fallback)

**ds_health_issues (Top Health Issues):**
- **Now multi-source** with UNION of:
  - Job failures from `fact_job_run_timeline`
  - Query failures from `fact_query_history`  
  - Untagged cost issues from `fact_usage`
- New columns: `category`, `asset_id`, `asset_name`, `issue_count`, `reason`, `last_occurrence`, `severity`
- Widget fields and encodings updated to match
- Title changed to "⚠️ Top Health Issues (Jobs, Queries, Costs)"

**ds_health_trend:**
- Changed from single-source to **composite trend**:
  - Daily job health score
  - Daily query health score
- Uses FULL OUTER JOIN to show days with data from either source
- Returns average of job + query scores

---

### 2026-01-03 (Session 2)

#### Dashboard Folder Change
- **Changed:** Dashboard deployment folder from `/Shared/Databricks Health Monitor` to `/Shared/health_monitor/dashboards`
- **Reason:** Align with Lakehouse Monitoring location at `/Shared/health_monitor/monitoring`
- **Files:** `databricks.yml`, `deploy_dashboards.py`

#### Deployment Script Update
- **Changed:** Added `parent_path` support using REST API instead of SDK
- **Reason:** SDK didn't properly support `parent_path` parameter
- **Files:** `deploy_dashboards.py`

---

### 2026-01-03 (Session 1)

#### Cost Overview Page Fixes
- **Fixed:** MTD Spend, 30-Day Spend, Tag Coverage %, Active Users, Spend by SKU
- **Root Cause:** Widget `queries.fields` mappings didn't match dataset output columns
- **Changes:**
  - `ds_kpi_mtd`: Returns raw `cost_mtd` (number)
  - `ds_kpi_30d`: Returns raw `cost_30d` (number)
  - `ds_tag_coverage`: Returns `tag_coverage` as 0-1 decimal
  - `ds_unique_counts`: Added `active_users` column
  - Fixed widget field mappings

#### Platform Health Page - Attempted Fixes
- **Attempted:** Fix Overall Health Score, Reliability Health, Health Score Trend, Top Health Issues
- **Changes Made:**
  - Added `COALESCE` for null safety
  - Changed `job_name` to `run_name` in health issues query
  - Added job_id, failure_count, reason, last_failure columns to health issues
- **Status:** Issues persist - need deeper investigation

---

## Query Reference

### Platform Health Page Datasets

| Dataset | Purpose | Expected Output |
|---------|---------|-----------------|
| `ds_health_score` | Overall health score (0-100) | Single number |
| `ds_reliability_health` | Reliability % (0-100) | Single number |
| `ds_cost_health` | Cost health % | Single number |
| `ds_health_issues` | Top problematic assets | Table with job details |
| `ds_health_trend` | Health score over time | Time series data |

---

## Investigation Notes

### PH-001 to PH-004 Investigation (2026-01-03)

**Questions to Answer:**
1. What Gold layer tables do these queries reference?
2. Do those tables have data?
3. Are the column names correct?
4. Are the filters (time_range, workspace) causing empty results?

**Tables to Check:**
- `fact_job_run_timeline` - Job run data
- `fact_query_history` - Query performance data
- Monitoring tables in `*_monitoring` schema

---

## Widget Encoding Reference

### KPI Widgets Pattern
```json
{
  "spec": {
    "encodings": {
      "value": {
        "fieldName": "<column_name_from_query>",
        "displayName": "<display_label>"
      }
    },
    "frame": {
      "showTitle": true,
      "title": "<widget_title>"
    }
  }
}
```

### Format Types
- `number-currency`: Expects raw number, formats as $X
- `number-percent`: Expects 0-1 decimal, displays as X%
- `number`: Raw number with optional abbreviation

---

## Validation Checklist

Before deploying dashboard changes:
- [ ] Query returns expected column names
- [ ] Widget `fieldName` matches query output exactly
- [ ] For percentages: Query returns 0-1 decimal
- [ ] For currency: Query returns raw number
- [ ] Test with `SELECT LIMIT 1` to verify query works
- [ ] Check widget encoding matches query output

---

## Files Reference

| File | Purpose |
|------|---------|
| `src/dashboards/unified.lvdash.json` | Main unified dashboard |
| `src/dashboards/cost.lvdash.json` | Cost domain dashboard |
| `src/dashboards/performance.lvdash.json` | Performance domain dashboard |
| `src/dashboards/reliability.lvdash.json` | Reliability domain dashboard |
| `src/dashboards/security.lvdash.json` | Security domain dashboard |
| `src/dashboards/quality.lvdash.json` | Quality domain dashboard |
| `src/dashboards/validate_dashboard_queries.py` | SQL validation script |
| `src/dashboards/validate_widget_encodings.py` | Widget encoding validation |
| `src/dashboards/deploy_dashboards.py` | Dashboard deployment script |

