# Performance Intelligence Genie Space - Repeatability Report

**Test Date:** 2026-01-30  
**Genie Space:** Performance Intelligence (`01f0f1a3c3e31a8e8e6dee3eddf5d61f`)  
**Questions Tested:** 25  
**Iterations per Question:** 3  
**Total API Calls:** 75  
**Test Duration:** ~36 minutes  

---

## Executive Summary

| Metric | Value | Target | Status |
|---|---|---|---|
| **Overall Repeatability** | 42.7% | 90%+ | 🚨 **CRITICAL** |
| **Perfectly Repeatable** | 2/25 (8%) | 80%+ | 🚨 **CRITICAL** |
| **Variable Questions** | 23/25 (92%) | <20% | 🚨 **CRITICAL** |

---

## Optimization Attempts & Results

### Control Levers Applied

| Lever | Action | Result |
|-------|--------|--------|
| **1. UC Tables Metadata** | Updated `fact_query_history`, `dim_warehouse`, `dim_cluster` comments with routing guidance | ⚠️ Minimal impact |
| **2. UC Metric Views** | Already well-documented with PURPOSE/BEST FOR/NOT FOR | N/A - Already done |
| **3. UC Functions (TVFs)** | Already well-documented with routing guidance | N/A - Already done |
| **4. Lakehouse Monitoring** | Not applicable | - |
| **5. ML Model Tables** | Not applicable | - |
| **6. Genie Space Instructions** | Could not update via API (401 auth issue) | ❌ Failed |

### Post-Optimization Test (Focused on 5 worst questions)

#### Round 1: Table Metadata Only (Lever 1)

| Question | Before | After | Change |
|----------|--------|-------|--------|
| perf_001: P95 query duration | 33.3% | 33.3% | No change |
| perf_002: Slow queries last hour | 33.3% | 33.3% | No change |
| perf_003: Warehouse utilization | 33.3% | 33.3% | No change |
| perf_004: Inefficient queries | 33.3% | **66.7%** | +33.4% ✅ |
| perf_008: Failed queries | 33.3% | 33.3% | No change |

**Round 1 Result: 33.3% → 40.0% (+6.7%)**

#### Round 2: Genie Space Instructions (Lever 6)

Successfully updated Genie Space via API with explicit routing rules:
- Asset selection rules (metric view vs TVF vs table)
- Time filter patterns (exact SQL for "last hour", "today", etc.)
- Standard column sets
- Terminology disambiguation

| Question | Before | After | Change | Asset Used |
|----------|--------|-------|--------|------------|
| perf_001: P95 query duration | 33.3% | **66.7%** | +33.4% ↑ | MV ✅ |
| perf_002: Slow queries last hour | 33.3% | 33.3% | No change | TVF ✅ |
| perf_003: Warehouse utilization | 33.3% | **66.7%** | +33.4% ↑ | MV ✅ |
| perf_004: Inefficient queries | 66.7% | 33.3% | -33.4% ↓ | FACT ❌ |
| perf_008: Failed queries | 33.3% | 33.3% | No change | MV ✅ |

**Round 2 Result: 40.0% → 46.7% (+6.7%)**

**Total Improvement: 33.3% → 46.7% (+13.4%)**

### Key Finding: Instructions Improve Asset Routing, Not Full Repeatability

**Both Lever 1 (Table Metadata) and Lever 6 (Instructions) together achieved +13.4% improvement**, but still fall short of the 90% target.

**What Worked:**
- **Asset routing improved** - 4/5 questions now use the correct asset type (MV or TVF)
- **perf_001 and perf_003** improved from 33% to 67% (metric view routing)
- Instructions helped Genie choose the right table/view for aggregations

**What Didn't Work:**
- **SQL variance within the same asset** - Even when using the right metric view, Genie generates different SQL each time
- **perf_004 regressed** - Instructions may have confused the routing for "inefficient queries"
- **LLM non-determinism** remains the fundamental limitation

### Root Cause Analysis

| Issue | Impact | Can Instructions Fix? |
|-------|--------|----------------------|
| **Multiple valid assets** | Genie chooses randomly | ✅ Partially (4/5 now use correct asset) |
| **Column selection variance** | Different columns each time | ❌ No - LLM non-determinism |
| **Time filter interpretation** | Different SQL patterns | ❌ No - Even with exact patterns specified |
| **Aggregation function choice** | SUM vs COUNT vs MEASURE | ❌ No - LLM decides at runtime |

### 🚨 Critical Finding: Severe Repeatability Issues

The Performance domain has **significantly worse repeatability than Cost domain** (42.7% vs 80%). This indicates:

1. **Ambiguous metadata** - Questions have multiple valid interpretations
2. **Competing assets** - Multiple tables/views could answer the same question (MV, TVF, fact table)
3. **LLM non-determinism** - Genie's LLM chooses randomly between valid approaches

---

## Actions Completed

### ✅ Lever 1: Table Metadata (Applied)

Updated table comments via SQL:
- `fact_query_history` - Added routing guidance to use metric views for aggregations
- `dim_warehouse` - Added join guidance
- `dim_cluster` - Added metric view reference

### ✅ Lever 6: Genie Space Instructions (Applied via API)

Successfully updated Performance Genie Space (`01f0f1a3c3e31a8e8e6dee3eddf5d61f`) with:

```
=== CRITICAL ASSET ROUTING (ALWAYS FOLLOW) ===

1. Query Aggregations (P95, P99, avg, counts) → USE: mv_query_performance metric view
2. Slow Query Lists → USE: get_slow_queries TVF
3. Warehouse Utilization → USE: get_warehouse_utilization TVF
4. Query Efficiency → USE: mv_query_performance with query_efficiency_status
5. Cluster CPU/Memory → USE: mv_cluster_utilization metric view
6. Failed Queries → USE: get_failed_queries TVF

=== TIME FILTER PATTERNS ===

• "last hour" → query_date = CURRENT_DATE() AND hour_of_day = HOUR(CURRENT_TIMESTAMP())
• "today" → query_date = CURRENT_DATE()
• "this week" → query_date >= DATE_ADD(CURRENT_DATE(), -7)
```

---

## Conclusion: Levers Have Limited Impact on Repeatability

### What We Learned

| Control Lever | Impact on Repeatability | Best Use Case |
|---------------|------------------------|---------------|
| **Lever 1: Table Metadata** | +6.7% | Clarify which tables to use |
| **Lever 6: Instructions** | +6.7% | Improve asset routing (MV vs TVF) |
| **Combined** | **+13.4%** | Better routing, not full repeatability |

### The Fundamental Limitation

**Genie's LLM non-determinism cannot be fully controlled by instructions.** Even with explicit routing rules:
- The LLM still generates **different SQL syntax** for the same logical query
- Column selection, aggregation functions, and formatting vary between runs
- This is inherent to LLM-based SQL generation

### Recommendations for Production

1. **Accept ~50% repeatability** for ad-hoc analytical queries
2. **For critical dashboards**, use **saved queries** or **materialized views** instead of Genie
3. **Focus accuracy optimization** on ensuring Genie gives *correct* answers, even if SQL varies
4. **Monitor semantic equivalence** - different SQL that returns same results is acceptable

---

## Comparison with Cost Domain

| Metric | Cost Domain | Performance Domain | Gap |
|---|---|---|---|
| Overall Repeatability | 80.0% | 42.7% | -37.3% |
| Repeatable Questions | 3/5 (60%) | 2/25 (8%) | -52% |
| 100% Repeatability | 3/5 | 2/25 | Significant |

---

## Detailed Results

### ✅ Repeatable Questions (100%)

Only **2 questions** achieved perfect repeatability:

#### perf_007: Show me query latency percentiles by warehouse

```sql
SELECT `warehouse_id`,
       MEASURE(`p50_duration_seconds`) AS `p50_duration_seconds`,
       MEASURE(`p95_duration_seconds`) AS `p95_duration_seconds`,
       MEASURE(`p99_duration_seconds`) AS `p99_duration_seconds`
FROM `prashanth_subrahmanyam_catalog`.`dev_prashanth_subrahmanyam_system_gold`.`mv_query_performance`
WHERE `warehouse_id` IS NOT NULL
GROUP BY ALL
ORDER BY `p95_duration_seconds` DESC
```

**Why repeatable:** Very specific request (latency percentiles + by warehouse) with clear column names.

---

#### perf_023: How has warehouse utilization changed this week?

**Why repeatable:** Clear time constraint ("this week") and specific request ("utilization changed").

---

### ⚠️ Partially Repeatable Questions (67%)

**4 questions** achieved 67% repeatability (2/3 same SQL):

| ID | Question | Repeatability |
|---|---|---|
| perf_012 | What is our average memory utilization? | 66.7% |
| perf_015 | Who are the heaviest query users? | 66.7% |
| perf_017 | How many queries did each warehouse run today? | 66.7% |

---

### ❌ Low Repeatability Questions (33%)

**19 questions** had only 33% repeatability (3 different SQLs in 3 runs):

| ID | Question | Variants | Root Cause |
|---|---|---|---|
| perf_001 | What is our P95 query duration? | 3 | Different HAVING clauses |
| perf_002 | Show me slow queries in the last hour | 3 | Different tables (metric view vs fact table) |
| perf_003 | What's the warehouse utilization? | 3 | Different columns selected |
| perf_004 | Which queries are inefficient? | 3 | Different filter conditions |
| perf_005 | Show me queries with high disk spill | 3 | Different column sets |
| perf_006 | What are the query volume trends? | 3 | Different date ranges |
| perf_008 | What are the failed queries? | 3 | Different column sets |
| perf_009 | Show me underutilized clusters | 3 | Different metrics selected |
| perf_010 | What are the cluster right-sizing recommendations? | 3 | Different column orders |
| perf_011 | What is our average CPU utilization? | 3 | Different metrics included |
| perf_013 | Show warehouse efficiency analysis | 3 | Different efficiency metrics |
| perf_014 | Which warehouses need to scale up? | 3 | Different criteria |
| perf_016 | Show me user query summary | 3 | Different aggregations |
| perf_018 | What is the query error rate? | 3 | Different calculations |
| perf_019 | What queries should we optimize? | 3 | Different optimization criteria |
| perf_020 | Which warehouses are predicted to have capacity issues? | 3 | Different prediction tables |
| perf_021 | Show predicted slow queries | 3 | Different prediction sources |
| perf_022 | Show query performance trends over time | 3 | Different time windows |
| perf_024 | Show me job outlier runs by performance | 3 | Different outlier definitions |
| perf_025 | What is our P99 query latency by warehouse? | 3 | Different column sets |

---

## Variance Analysis

### Example: perf_002 "Show me slow queries in the last hour"

**Variant 1:** Uses CTE with MAX(hour_of_day)
```sql
WITH latest_hour AS (SELECT MAX(`hour_of_day`) AS max_hour FROM mv_query_performance...)
SELECT ... WHERE `hour_of_day` = (SELECT max_hour FROM latest_hour)
```

**Variant 2:** Uses current hour directly
```sql
SELECT ... WHERE `hour_of_day` = hour(current_timestamp())
```

**Variant 3:** Uses fact table with timestamp filter
```sql
SELECT ... FROM fact_query_history WHERE `start_time` >= dateadd(HOUR, -1, CURRENT_TIMESTAMP)
```

**Analysis:** Three completely different approaches to "last hour" - LLM is choosing randomly.

---

### Example: perf_001 "What is our P95 query duration?"

**Variant 1:**
```sql
SELECT MEASURE(`p95_duration_seconds`) AS p95_query_duration ... HAVING p95_query_duration IS NOT NULL
```

**Variant 2:**
```sql
SELECT MEASURE(`p95_duration_seconds`) AS `p95_query_duration_seconds` ... HAVING p95_query_duration_seconds IS NOT NULL
```

**Variant 3:**
```sql
SELECT MEASURE(`p95_duration_seconds`) AS `p95_query_duration_seconds` ... GROUP BY ALL
```

**Analysis:** Minor differences - alias naming and optional HAVING clause. Semantically equivalent but not identical.

---

## Root Causes

### 1. Competing Assets (Primary Issue)

The Performance domain has multiple views that could answer similar questions:
- `mv_query_performance` - Query metrics
- `mv_cluster_utilization` - Cluster metrics
- `fact_query_history` - Raw query history
- ML prediction tables

**Example:** "Show slow queries" could use:
- `mv_query_performance` WHERE p95_duration_seconds > threshold
- `fact_query_history` WHERE duration_seconds > threshold
- ML predictions for slow queries

### 2. Ambiguous Time Filters

"Last hour", "today", "this week" have multiple valid SQL interpretations:
- `WHERE hour_of_day = hour(current_timestamp())`
- `WHERE start_time >= dateadd(HOUR, -1, CURRENT_TIMESTAMP)`
- `WHERE query_date = current_date() AND hour_of_day >= ...`

### 3. Column Selection Variance

For questions like "What's the warehouse utilization?", Genie varies between:
- Just CPU + memory
- CPU + memory + efficiency score
- CPU + memory + wasted capacity %

---

## Recommendations

### High Priority: Add Sample Queries

Add sample queries for all 23 variable questions to lock in the expected pattern:

```python
# Example for perf_001
client.add_sample_query(
    question="What is our P95 query duration?",
    sql="""SELECT MEASURE(`p95_duration_seconds`) AS `p95_duration_seconds`
FROM `catalog`.`schema`.`mv_query_performance`
GROUP BY ALL
HAVING p95_duration_seconds IS NOT NULL"""
)

# Example for perf_002
client.add_sample_query(
    question="Show me slow queries in the last hour",
    sql="""SELECT `statement_id`, `warehouse_name`, 
       MEASURE(`avg_duration_seconds`) AS `avg_duration_seconds`
FROM `catalog`.`schema`.`mv_query_performance`
WHERE `query_date` = current_date() 
  AND `hour_of_day` = hour(current_timestamp())
  AND `query_efficiency_status` = 'SLOW'
GROUP BY ALL
ORDER BY `avg_duration_seconds` DESC
LIMIT 20"""
)
```

### Medium Priority: Add Instructions

Add explicit instructions for common patterns:

```python
client.add_instruction(
    "For 'slow queries' always use mv_query_performance with query_efficiency_status = 'SLOW'. "
    "Do not use fact_query_history for this type of query."
)

client.add_instruction(
    "For 'last hour' queries, use: query_date = current_date() AND hour_of_day = hour(current_timestamp())"
)
```

### Low Priority: Update Table Metadata

Update table comments to clarify primary use cases:

```sql
ALTER TABLE mv_query_performance SET TBLPROPERTIES (
    'comment' = 'PRIMARY source for query performance analysis. Use this for slow queries, 
    efficiency analysis, latency percentiles, and query volume metrics. Prefer over fact_query_history.'
)
```

---

## Prioritized Fix List

| Priority | Question ID | Fix Type | Estimated Impact |
|---|---|---|---|
| 1 | perf_001 | Sample Query | High - Common question |
| 2 | perf_002 | Sample Query + Instruction | High - Time ambiguity |
| 3 | perf_003 | Sample Query | High - Utilization questions |
| 4 | perf_004 | Sample Query | High - Inefficient query patterns |
| 5 | perf_008 | Sample Query | High - Failed query tracking |
| 6 | All time-based | Instruction | Medium - Standardize time filters |
| 7 | perf_009-010 | Sample Query | Medium - Cluster recommendations |
| 8 | perf_020-021 | Sample Query | Medium - ML prediction queries |

---

## Summary

| Metric | Before Fix | Target After Fix |
|---|---|---|
| Overall Repeatability | 42.7% | 90%+ |
| Repeatable Questions | 2/25 | 22/25+ |
| Variable Questions | 23/25 | 3/25 or fewer |

**Estimated Effort:** 2-3 hours to add sample queries for all 23 variable questions.

**Expected Outcome:** Repeatability should improve to 85-95% after adding sample queries.

---

*Generated by Databricks Health Monitor Genie Space Optimizer*
