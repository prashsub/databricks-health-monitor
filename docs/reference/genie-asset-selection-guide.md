# Genie Asset Selection Guide

## Quick Decision Tree

```
USER QUERY                                          → USE THIS
─────────────────────────────────────────────────────────────────
"What's the current X?"                             → Metric View
"Show me total X by Y"                              → Metric View
"Dashboard of X"                                    → Metric View
─────────────────────────────────────────────────────────────────
"Is X increasing/decreasing over time?"             → Custom Metrics (_drift_metrics)
"How has X changed since last week?"                → Custom Metrics (_drift_metrics)
"Alert me when X exceeds threshold"                 → Custom Metrics (for alerting)
─────────────────────────────────────────────────────────────────
"Which specific items have X?"                      → TVF
"List the top N items with X"                       → TVF
"Show me items from DATE to DATE with X"            → TVF
"What failed/what's slow/what's stale?"             → TVF
─────────────────────────────────────────────────────────────────
```

---

## Asset Selection by Query Type

### Current State Queries → **Metric Views**

| Example Query | Metric View | Measure |
|---------------|-------------|---------|
| "What's the current job success rate?" | `mv_job_performance` | `success_rate` |
| "Total cost this month" | `mv_cost_analytics` | `mtd_cost` |
| "Query latency P95" | `mv_query_performance` | `p95_duration_seconds` |
| "How much cost is untagged?" | `mv_cost_analytics` | `tag_coverage_pct` |

### Trend/Drift Queries → **Custom Metrics (Lakehouse Monitoring)**

| Example Query | Table | Metric |
|---------------|-------|--------|
| "Is success rate degrading?" | `fact_job_run_timeline_drift_metrics` | `success_rate_drift` |
| "Is cost increasing vs last period?" | `fact_usage_drift_metrics` | `cost_drift_pct` |
| "Query latency trend" | `fact_query_history_profile_metrics` | `p95_duration_seconds` over time |
| "Tag coverage trend" | `fact_usage_profile_metrics` | `tag_coverage_pct` over time |

### Investigation Queries → **TVFs**

| Example Query | TVF | Key Parameters |
|---------------|-----|----------------|
| "Which jobs failed this week?" | `get_failed_jobs_summary` | `days_back=7` |
| "Top 10 cost drivers" | `get_top_cost_contributors` | `top_n=10` |
| "Queries over 30 seconds" | `get_slow_queries` | `duration_threshold_sec=30` |
| "Stale tables" | `get_stale_tables` | `staleness_threshold_days=7` |
| "User risk scores" | `get_user_risk_scores` | `days_back=30` |

---

## Domain-Specific Guidance

### 💰 Cost Queries

| Query Intent | Asset | Notes |
|--------------|-------|-------|
| Current total cost | `mv_cost_analytics` | Use `total_cost`, `mtd_cost`, `ytd_cost` |
| Cost trend/drift | `_drift_metrics` | Check `cost_drift_pct` |
| Top cost drivers | `get_top_cost_contributors` | Parameterized by date range |
| Untagged resources | `get_untagged_resources` | Returns actionable list |
| Budget projection | `mv_commit_tracking` | Use `projected_monthly_cost` |

### 🔄 Reliability Queries

| Query Intent | Asset | Notes |
|--------------|-------|-------|
| Current success rate | `mv_job_performance` | Use `success_rate` measure |
| Success rate degrading? | `_drift_metrics` | Check `success_rate_drift` |
| Which jobs failed? | `get_failed_jobs_summary` | Returns job list with errors |
| SLA compliance | `get_job_sla_compliance` | Parameterized analysis |
| Duration trends | `_profile_metrics` | Check `p95_duration_minutes` over time |

### ⚡ Performance Queries

| Query Intent | Asset | Notes |
|--------------|-------|-------|
| Query latency P95 | `mv_query_performance` | Dashboard aggregate |
| Latency trend | `_profile_metrics` | Time series analysis |
| Slow query list | `get_slow_queries` | Parameterized threshold |
| Underutilized clusters | `get_underutilized_clusters` | Returns savings opportunities |
| Right-sizing recs | `get_cluster_rightsizing` | Detailed recommendations |

### 🔒 Security Queries

| Query Intent | Asset | Notes |
|--------------|-------|-------|
| Total audit events | `mv_security_events` | Dashboard aggregate |
| Failed auth trend | `_drift_metrics` | Alerting on auth_failure_drift |
| User risk scores | `get_user_risk_scores` | Complex multi-factor calculation |
| Permission changes | `get_permission_changes` | Audit trail |
| Unusual activity | `get_unusual_access_patterns` | Anomaly detection |

### 📋 Quality Queries

| Query Intent | Asset | Notes |
|--------------|-------|-------|
| Freshness rate | `mv_data_quality` | Current percentage |
| Stale table list | `get_stale_tables` | Actionable list |
| Governance compliance | `get_governance_compliance` | Detailed report |
| Freshness by domain | `get_data_freshness_by_domain` | Portfolio view |
| ML anomaly insights | `mv_ml_intelligence` | Requires ML pipeline |

---

## For Genie Space Agent Instructions

Include this in your Genie Space agent instructions:

```markdown
## Asset Selection Rules

When answering user queries, select the appropriate asset type:

### Use Metric Views (mv_*) when:
- User wants current state aggregates
- Query is for dashboard-style KPIs
- No specific date range or entity filter needed
- Examples: "total cost", "success rate", "query latency"

### Use Custom Metrics (*_profile_metrics, *_drift_metrics) when:
- User asks about trends over time
- User asks if something is increasing/decreasing
- Query involves period comparison (vs baseline)
- Examples: "is X degrading?", "X trend", "X over time"

### Use TVFs (get_*) when:
- User wants a specific list of items
- Query includes "top N", "which", "list"
- User specifies date range or threshold
- User needs actionable investigation results
- Examples: "which jobs failed?", "top 10 cost drivers", "slow queries"

### Priority Order:
1. If user asks for a LIST → TVF
2. If user asks about TREND → Custom Metrics
3. If user asks for CURRENT VALUE → Metric View
```

---

## Common Confusion Scenarios

### Scenario 1: "What's the success rate?"

**Wrong:** Query TVF `get_job_success_rates`  
**Right:** Query Metric View `mv_job_performance` → `MEASURE(success_rate)`

**Why:** User wants current aggregate, not a parameterized list.

### Scenario 2: "Is cost going up?"

**Wrong:** Query Metric View `mv_cost_analytics`  
**Right:** Query `fact_usage_drift_metrics` → `cost_drift_pct`

**Why:** User wants trend comparison, not current value.

### Scenario 3: "Which jobs failed yesterday?"

**Wrong:** Query Custom Metrics  
**Right:** Call TVF `get_failed_jobs_summary(1, 1)`

**Why:** User wants specific list, not aggregate.

### Scenario 4: "Show me cost by workspace"

**Right:** Query Metric View `mv_cost_analytics` grouped by `workspace_name`

**Why:** Dashboard-style aggregate with dimension.

---

**Version:** 1.0  
**Last Updated:** January 2026

