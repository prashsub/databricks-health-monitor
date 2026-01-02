# Semantic Layer Rationalization Analysis

## Executive Summary

This document analyzes **all 383+ measurements** across the three semantic layer components to ensure they align, serve distinct purposes, and prevent Genie confusion.

### Component Overview

| Component | Count | Purpose | Invocation | Time Capability |
|-----------|-------|---------|------------|-----------------|
| **TVFs** | 60 | Parameterized drill-down queries | `SELECT * FROM TABLE(tvf_name(...))` | Point-in-time filters |
| **Metric Views** | 10 (150+ dims/measures) | Pre-aggregated dashboards | `SELECT MEASURE(...) FROM mv_*` | Aggregate over periods |
| **Custom Metrics** | 213+ | Time series analysis & drift | Auto-computed in `_profile_metrics` | Period comparison |

---

## Key Design Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SEMANTIC LAYER HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    CUSTOM METRICS (Lakehouse Monitoring)            │    │
│  │         Purpose: TIME SERIES ANALYSIS & DRIFT DETECTION              │    │
│  │                                                                      │    │
│  │   ✅ Automated computation every refresh                            │    │
│  │   ✅ Period-over-period drift (baseline vs current)                 │    │
│  │   ✅ Statistical profiling (distribution, nulls, cardinality)       │    │
│  │   ✅ Anomaly detection via drift thresholds                         │    │
│  │   ❌ NOT for user-parameterized queries                             │    │
│  │   ❌ NOT for ad-hoc drill-down                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                         │
│                                    │ Alerts trigger when drift exceeds       │
│                                    │ thresholds, then user drills down       │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    METRIC VIEWS (10 Views)                          │    │
│  │         Purpose: AGGREGATE ANALYTICS FOR DASHBOARDS                  │    │
│  │                                                                      │    │
│  │   ✅ Pre-configured dimensions and measures                         │    │
│  │   ✅ Natural language: "Show me total cost by workspace"            │    │
│  │   ✅ Dashboard KPIs with formatting                                 │    │
│  │   ❌ NOT for specific date range queries                            │    │
│  │   ❌ NOT for entity-specific lookups                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                         │
│                                    │ Dashboard shows high-level trend,       │
│                                    │ user wants to drill into specifics      │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    TVFs (60 Functions)                              │    │
│  │         Purpose: PARAMETERIZED DRILL-DOWN QUERIES                    │    │
│  │                                                                      │    │
│  │   ✅ User-specified date ranges, top_n, thresholds                  │    │
│  │   ✅ "Show me the top 10 cost drivers this week"                    │    │
│  │   ✅ Entity-specific lookups (job, user, table)                     │    │
│  │   ✅ Actionable lists (what failed, what's slow)                    │    │
│  │   ❌ NOT for trend analysis over time                               │    │
│  │   ❌ NOT for automated monitoring                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Domain-by-Domain Analysis

### 💰 COST Domain

| Layer | Asset | Measurements | Purpose |
|-------|-------|--------------|---------|
| **Custom Metrics** | Cost Monitor | 35 metrics | Automated time series tracking of daily cost, tag coverage drift, SKU distribution changes |
| **Metric Views** | `mv_cost_analytics` | 26 dims, 30 measures | Dashboard aggregates: total_cost, mtd_cost, ytd_cost, serverless_ratio |
| **Metric Views** | `mv_commit_tracking` | 10 dims, 12 measures | Budget projection: projected_monthly_cost, daily_burn_rate |
| **TVFs** | 15 functions | Parameterized | Drill-down: get_top_cost_contributors, get_cost_anomalies, get_untagged_resources |

#### Overlap Analysis

| Measurement Concept | Custom Metric | Metric View | TVF | **Verdict** |
|---------------------|---------------|-------------|-----|-------------|
| Total daily cost | `total_daily_cost` | `total_cost` | `get_daily_cost_summary` | ✅ **No overlap** - Different purposes |
| Tag coverage % | `tag_coverage_pct` | `tag_coverage_pct` | `get_untagged_resources` | ✅ **Complementary** - CM tracks drift, MV shows current, TVF lists untagged |
| Cost by SKU | `jobs_compute_cost`, `sql_compute_cost` | By dimension | `get_cost_trend_by_sku` | ✅ **Complementary** - CM totals, TVF daily trends |
| Cost anomalies | `cost_drift_pct` (DRIFT) | - | `get_cost_anomalies` | ⚠️ **Potential overlap** - Both detect anomalies |

#### Recommendations - Cost Domain

1. **Clarify anomaly detection roles:**
   - Custom Metrics: Automated drift alerts (threshold-based, period comparison)
   - TVF: User-initiated investigation with custom thresholds
   - **Action:** Add comment to TVF: "Use after Lakehouse Monitoring alerts trigger"

2. **Avoid duplication in Metric View:**
   - `mv_cost_analytics.total_cost` and `mv_commit_tracking.mtd_cost` overlap
   - **Action:** Document that `mv_commit_tracking` is for FinOps budget tracking, `mv_cost_analytics` for operational analysis

---

### 🔄 RELIABILITY Domain

| Layer | Asset | Measurements | Purpose |
|-------|-------|--------------|---------|
| **Custom Metrics** | Job Monitor | 50 metrics | Time series: success_rate drift, duration trends, failure patterns |
| **Metric Views** | `mv_job_performance` | 14 dims, 16 measures | Dashboard: success_rate, failure_rate, p95_duration |
| **TVFs** | 12 functions | Parameterized | Drill-down: get_failed_jobs_summary, get_job_sla_compliance, get_repair_cost_analysis |

#### Overlap Analysis

| Measurement Concept | Custom Metric | Metric View | TVF | **Verdict** |
|---------------------|---------------|-------------|-----|-------------|
| Success rate | `success_rate` (DERIVED) | `success_rate` | `get_job_success_rates` | ⚠️ **Same calculation, different context** |
| Failure count | `failure_count` (AGGREGATE) | `total_failures` | `get_failed_jobs_summary` | ✅ **Complementary** - CM tracks trend, TVF shows current failures |
| Duration P95 | `p95_duration_minutes` | `p95_duration_minutes` | `get_job_duration_percentiles` | ⚠️ **Same metric, different granularity** |

#### Key Distinction

```
WHEN TO USE WHAT:

"What's the current job success rate?"
  → Metric View: SELECT MEASURE(success_rate) FROM mv_job_performance

"Is job success rate degrading over time?"  
  → Custom Metrics: Check success_rate_drift in _drift_metrics

"Which specific jobs failed yesterday?"
  → TVF: SELECT * FROM TABLE(get_failed_jobs_summary(1, 1))
```

#### Recommendations - Reliability Domain

1. **Add drift context to Metric View comments:**
   ```yaml
   success_rate:
     comment: >
       Current success rate. For trend analysis and drift detection,
       query Lakehouse Monitoring: fact_job_run_timeline_drift_metrics
   ```

2. **Ensure TVFs reference monitoring alerts:**
   - TVF comments should say: "Typically used after Lakehouse Monitoring triggers high failure_count_drift"

---

### ⚡ PERFORMANCE Domain

| Layer | Asset | Measurements | Purpose |
|-------|-------|--------------|---------|
| **Custom Metrics** | Query Monitor | 40 metrics | Time series: query latency trends, cache efficiency drift |
| **Custom Metrics** | Cluster Monitor | 40 metrics | Time series: CPU/memory utilization, idle time trends |
| **Metric Views** | `mv_query_performance` | 15 dims, 18 measures | Dashboard: avg_duration, p95_duration, cache_hit_rate |
| **Metric Views** | `mv_cluster_utilization` | 12 dims, 14 measures | Dashboard: avg_cpu, avg_memory, wasted_hours |
| **Metric Views** | `mv_cluster_efficiency` | 8 dims, 10 measures | Dashboard: efficiency_score, idle_percentage |
| **TVFs** | 16 functions | Parameterized | Drill-down: get_slow_queries, get_underutilized_clusters |

#### Overlap Analysis

| Measurement Concept | Custom Metric | Metric View | TVF | **Verdict** |
|---------------------|---------------|-------------|-----|-------------|
| Query P95 latency | `p95_duration_seconds` | `p95_duration_seconds` | `get_query_latency_percentiles` | ✅ **Different purposes** |
| Slow queries | `long_running_count` | - | `get_slow_queries` | ✅ **Complementary** - CM counts, TVF lists |
| Cluster CPU | `avg_cpu_pct` | `avg_cpu_utilization` | `get_cluster_utilization` | ⚠️ **Same metric** |

#### Recommendations - Performance Domain

1. **Separate concerns for cluster metrics:**
   - `mv_cluster_utilization`: Current state aggregates
   - `mv_cluster_efficiency`: Derived scores (efficiency_score)
   - Custom Metrics: Trend over time
   - **Action:** Already well-separated ✅

2. **TVF should include threshold guidance:**
   ```sql
   -- get_slow_queries: Use after mv_query_performance shows high p95_duration
   -- Default threshold: 30 seconds (configurable)
   ```

---

### 🔒 SECURITY Domain

| Layer | Asset | Measurements | Purpose |
|-------|-------|--------------|---------|
| **Custom Metrics** | Security Monitor | 13 metrics | Time series: failed_auth_count drift, admin_action trends |
| **Metric Views** | `mv_security_events` | 16 dims, 12 measures | Dashboard: total_events, failed_events, sensitive_events_24h |
| **Metric Views** | `mv_governance_analytics` | 10 dims, 8 measures | Dashboard: read/write events, activity by entity |
| **TVFs** | 10 functions | Parameterized | Drill-down: get_user_risk_scores, get_unusual_access_patterns |

#### Overlap Analysis

| Measurement Concept | Custom Metric | Metric View | TVF | **Verdict** |
|---------------------|---------------|-------------|-----|-------------|
| Failed auth count | `failed_auth_count` | `failed_events` | `get_failed_access_attempts` | ✅ **Complementary** |
| Admin actions | `admin_actions` | By dimension | `get_permission_changes` | ✅ **Complementary** |
| Risk scoring | - | - | `get_user_risk_scores` | ✅ **TVF-only** (complex calculation) |

#### Recommendations - Security Domain

1. **Risk scoring is TVF-only (correct):**
   - Complex multi-factor calculation best suited for TVF
   - No Custom Metric equivalent needed
   - ✅ Already correct

2. **Clarify audit log access patterns:**
   - `mv_security_events`: High-level counts and trends
   - `mv_governance_analytics`: Data lineage focus
   - TVFs: User-specific investigations
   - ✅ Already well-separated

---

### 📋 QUALITY Domain

| Layer | Asset | Measurements | Purpose |
|-------|-------|--------------|---------|
| **Custom Metrics** | Quality Monitor | 10 metrics | Time series: freshness trends, null violation drift |
| **Custom Metrics** | Governance Monitor | 11 metrics | Time series: documentation rate trends |
| **Metric Views** | `mv_data_quality` | 8 dims, 10 measures | Dashboard: freshness_rate, stale_tables count |
| **Metric Views** | `mv_ml_intelligence` | 10 dims, 14 measures | Dashboard: anomaly_count, anomaly_rate (requires ML) |
| **TVFs** | 7 functions | Parameterized | Drill-down: get_stale_tables, get_governance_compliance |

#### Overlap Analysis

| Measurement Concept | Custom Metric | Metric View | TVF | **Verdict** |
|---------------------|---------------|-------------|-----|-------------|
| Stale table count | `tables_with_issues` | `stale_tables` | `get_stale_tables` | ✅ **Complementary** - CM trends, MV counts, TVF lists |
| Freshness % | - | `freshness_rate` | `get_data_freshness_by_domain` | ✅ **Complementary** |

#### Recommendations - Quality Domain

1. **ML Intelligence has correct separation:**
   - Requires ML pipeline to populate
   - TVFs don't duplicate ML predictions
   - ✅ Already correct

---

## Genie Confusion Prevention Strategy

### Problem Statement

When a user asks "What's the current success rate?", Genie could:
1. Query `mv_job_performance` for current aggregate
2. Query Custom Metric `success_rate` in `_profile_metrics`
3. Call TVF `get_job_success_rates`

### Solution: Structured Comments

Each asset type should have comments that clearly indicate:
1. **BEST FOR**: When to use this asset
2. **NOT FOR**: When to use something else
3. **SEE ALSO**: Related assets

#### Metric View Comment Template

```yaml
comment: >
  PURPOSE: Current-state aggregate metrics for job performance.
  
  BEST FOR: Dashboard KPIs | Current success rate | Period aggregates
  
  NOT FOR: 
  - Trend over time → Query Lakehouse Monitoring _profile_metrics tables
  - Specific job failures → Use get_failed_jobs_summary TVF
  - Drift detection → Query _drift_metrics tables
  
  DIMENSIONS: job_name, workspace_name, trigger_type, outcome_category
  MEASURES: success_rate, failure_rate, avg_duration_minutes, p95_duration
```

#### TVF Comment Template

```sql
/*
  PURPOSE: Parameterized query to list jobs with failures.
  
  BEST FOR: Which jobs failed? | Failure investigation | Specific date range analysis
  
  NOT FOR:
  - High-level dashboard → Use mv_job_performance Metric View
  - Is failure rate increasing? → Check Lakehouse Monitoring drift metrics
  
  PARAMS: days_back (required), min_failures (default 1)
  
  EXAMPLE: "Show me jobs that failed 3+ times this week"
  → SELECT * FROM TABLE(get_failed_jobs_summary(7, 3))
*/
```

#### Custom Metric Documentation (in monitor_utils.py)

```python
METRIC_DESCRIPTIONS = {
    "success_rate": """
        Current period job success rate (successes / total * 100).
        
        Business: Primary reliability KPI for job execution.
        Technical: Computed from success_count / total_runs * 100.
        
        BEST FOR: Time series analysis | Trend detection | Alerting thresholds
        
        NOT FOR:
        - Which specific jobs failed? → Use get_failed_jobs_summary TVF
        - Current aggregate for dashboard → Use mv_job_performance
    """,
}
```

---

## Complete Measurement Matrix

### Cost Domain (50 total)

| Measurement | Custom Metric | Metric View | TVF | Primary Owner |
|-------------|:-------------:|:-----------:|:---:|---------------|
| Total daily cost | ✅ | ✅ | ✅ | **Metric View** (dashboard) |
| Cost by SKU | ✅ | By dimension | ✅ | **TVF** (drill-down) |
| Tag coverage % | ✅ | ✅ | - | **Custom Metric** (drift tracking) |
| Untagged resources list | - | - | ✅ | **TVF** (action list) |
| Cost forecast | - | ✅ projected | ✅ | **TVF** (parameterized) |
| Cost anomalies | ✅ drift | - | ✅ | **Custom Metric** (automated) + **TVF** (investigation) |
| WoW growth | ✅ drift | ✅ | - | **Metric View** (dashboard KPI) |

### Reliability Domain (78 total)

| Measurement | Custom Metric | Metric View | TVF | Primary Owner |
|-------------|:-------------:|:-----------:|:---:|---------------|
| Success rate | ✅ | ✅ | ✅ | **Metric View** (current) + **CM** (trend) |
| Failure count | ✅ | ✅ | ✅ | **TVF** (action list) |
| Duration percentiles | ✅ P50-P99 | ✅ P95 | ✅ all | **Custom Metric** (trend) |
| SLA compliance | - | - | ✅ | **TVF** (parameterized) |
| Failed job list | - | - | ✅ | **TVF** (action list) |
| Repair cost | - | - | ✅ | **TVF** (analysis) |
| Success rate drift | ✅ drift | - | - | **Custom Metric** (alerting) |

### Performance Domain (108 total)

| Measurement | Custom Metric | Metric View | TVF | Primary Owner |
|-------------|:-------------:|:-----------:|:---:|---------------|
| Query latency P95 | ✅ | ✅ | ✅ | **Metric View** (dashboard) |
| Cache hit rate | ✅ | ✅ | - | **Metric View** (dashboard) |
| Slow query list | - | - | ✅ | **TVF** (action list) |
| Spill analysis | - | - | ✅ | **TVF** (optimization) |
| CPU utilization | ✅ | ✅ | ✅ | **Custom Metric** (trend) |
| Underutilized clusters | - | ✅ count | ✅ list | **TVF** (action list) |
| Right-sizing recs | - | - | ✅ | **TVF** (recommendations) |

### Security Domain (35 total)

| Measurement | Custom Metric | Metric View | TVF | Primary Owner |
|-------------|:-------------:|:-----------:|:---:|---------------|
| Total audit events | ✅ | ✅ | ✅ | **Metric View** (dashboard) |
| Failed auth count | ✅ | ✅ | ✅ | **Custom Metric** (alerting) |
| User risk scores | - | - | ✅ | **TVF** (complex calculation) |
| Permission changes | - | - | ✅ | **TVF** (audit trail) |
| Sensitive data access | - | - | ✅ | **TVF** (compliance) |

### Quality Domain (47 total)

| Measurement | Custom Metric | Metric View | TVF | Primary Owner |
|-------------|:-------------:|:-----------:|:---:|---------------|
| Freshness rate | ✅ | ✅ | ✅ | **Metric View** (dashboard) |
| Stale table count | ✅ | ✅ | - | **Custom Metric** (alerting) |
| Stale table list | - | - | ✅ | **TVF** (action list) |
| Lineage summary | - | ✅ | ✅ | **TVF** (parameterized) |
| Governance compliance | ✅ | - | ✅ | **TVF** (detailed report) |
| ML anomaly detection | - | ✅ | - | **Metric View** (ML-powered) |

---

## Action Items

### High Priority (Prevent Genie Confusion)

- [ ] **Update all Metric View comments** with BEST FOR / NOT FOR / SEE ALSO format
- [ ] **Update all TVF comments** with purpose clarification and related assets
- [ ] **Add "Primary Owner" guidance** to Genie Space agent instructions
- [ ] **Create Genie instruction template** that explains when to use each asset type

### Medium Priority (Documentation Alignment)

- [ ] **Consolidate this document** into Genie Space agent instructions
- [ ] **Update 03-custom-metrics.md** with "NOT FOR" guidance
- [ ] **Update 24-metric-views-reference.md** with cross-references

### Low Priority (Future Enhancement)

- [ ] Consider removing duplicate calculations where Primary Owner is clear
- [ ] Add automated tests to detect measurement duplication

---

## Conclusion

The semantic layer is **well-designed with appropriate separation of concerns**:

1. **Custom Metrics**: Automated time series analysis and drift detection (alerting)
2. **Metric Views**: Pre-aggregated dashboards (visualization)
3. **TVFs**: Parameterized drill-down queries (investigation)

The main improvement opportunity is **documentation clarity** - adding structured comments that guide Genie to the right asset for each query type.

### Key Principle

```
Alert → Dashboard → Drill-Down

1. Custom Metrics detect drift, trigger SQL Alerts
2. User checks Metric View dashboard for context
3. User calls TVF for specific investigation
```

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Author:** Data Engineering Team

