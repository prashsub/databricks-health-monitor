# Job Health Monitor Genie - JSON Export Update Summary

**Date:** January 2026  
**Source:** `src/genie/job_health_monitor_genie.md`  
**Target:** `src/genie/job_health_monitor_genie_export.json`

---

## Updates Applied ✅

### 1. TVF Name Corrections (5 updates)

All Table-Valued Function references updated to match deployed assets from `docs/actual_assets.md`:

| Old Name | New Name | Usage |
|----------|----------|-------|
| `get_failed_jobs` | `get_failed_jobs_summary` | Failed jobs list |
| `get_job_success_rate` | `get_job_success_rates` | Success rate calculation (plural) |
| `get_job_failure_trends` | `get_job_failure_patterns` | Failure pattern analysis |
| `get_job_failure_costs` | `get_job_failure_cost` | Failure cost impact (singular) |
| `get_job_repair_costs` | `get_repair_cost_analysis` | Repair cost analysis |

### 2. TVF Removals (2 non-existent functions)

Removed TVFs that don't exist in actual deployed assets:

- ❌ `get_most_expensive_jobs` (not in actual_assets.md)
- ❌ `get_job_spend_trend_analysis` (not in actual_assets.md)

### 3. SQL Functions Section Updated

**Before:**
```json
"sql_functions": [
  {
    "identifier": "${catalog}.${gold_schema}.get_failed_jobs"
  },
  {
    "identifier": "${catalog}.${gold_schema}.get_job_success_rate"
  },
  {
    "identifier": "${catalog}.${gold_schema}.get_job_failure_trends"
  }
]
```

**After:**
```json
"sql_functions": [
  {
    "identifier": "${catalog}.${gold_schema}.get_failed_jobs_summary"
  },
  {
    "identifier": "${catalog}.${gold_schema}.get_job_success_rates"
  },
  {
    "identifier": "${catalog}.${gold_schema}.get_job_failure_patterns"
  }
]
```

### 4. Benchmark SQL Query Updates (4 queries)

#### Query 1: "Show me failed jobs today"
**Before:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs(
  CAST(CURRENT_DATE() AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
))
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_failed_jobs_summary(
  1
))
```

**Signature Change:** `(start_date, end_date, workspace_filter)` → `(days_back INT)`

---

#### Query 2: "Which jobs have the lowest success rate?"
**Before:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rate(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5
))
ORDER BY ROUND(100.0 * (total_events - failed_events) / NULLIF(total_events, 0), 2) ASC
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_success_rates(
  30
))
ORDER BY success_rate ASC
```

**Signature Change:** `(start_date, end_date, min_runs)` → `(days_back INT)`

---

#### Query 3: "Show me job failure trends"
**Before:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_failure_trends(
  30
))
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_failure_patterns(
  30
))
```

**Function Rename:** `get_job_failure_trends` → `get_job_failure_patterns`

---

#### Query 4: "Show me job repair costs from retries"
**Before:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_job_repair_costs(
  CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  15
))
```

**After:**
```sql
SELECT * FROM TABLE(${catalog}.${gold_schema}.get_repair_cost_analysis(
  30
))
```

**Signature Change:** `(start_date, end_date, top_n)` → `(days_back INT)`

---

### 5. Instruction Text Updated

**Before:**
```
13. **Failed Jobs:** For "failed jobs today" → use get_failed_jobs(start_date, end_date, workspace_filter) with TABLE()
```

**After:**
```
13. **Failed Jobs:** For "failed jobs today" → use get_failed_jobs_summary(days_back) with TABLE()
```

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **TVF Name Corrections** | 5 |
| **TVFs Removed** | 2 |
| **SQL Query Updates** | 4 |
| **Instruction Updates** | 1 |

---

## Validation

✅ **JSON syntax validated** - File passes `python3 -m json.tool` validation

---

## Key Changes Rationale

### 1. Signature Standardization
- **Old Pattern:** Date string parameters `(start_date STRING, end_date STRING)`
- **New Pattern:** Simple `days_back INT` parameter
- **Benefit:** Simpler API, consistent with other TVFs

### 2. Singular vs Plural Naming
- `get_job_failure_cost` (singular) - Returns aggregated cost metric
- `get_job_success_rates` (plural) - Returns multiple success rate records

### 3. Function Name Clarity
- `get_job_failure_patterns` (not `trends`) - Better describes the analysis type (patterns by error category)
- `get_repair_cost_analysis` (not `get_job_repair_costs`) - More comprehensive analysis function name

---

## Affected Genie Space Sections

1. ✅ **sql_functions** - TVF identifiers updated
2. ✅ **text_instructions** - Failed jobs instruction updated
3. ✅ **benchmarks.questions** - 4 SQL queries updated

---

## Next Steps

1. Test updated Genie space with corrected TVF names
2. Verify all benchmark queries execute successfully
3. Update any documentation referencing old TVF names

---

## References

- [Job Health Monitor Genie Markdown](../../src/genie/job_health_monitor_genie.md)
- [Actual Assets Inventory](../actual_assets.md)
- [TVF Signatures](../../src/semantic/tvfs/TVF_INVENTORY.md)


