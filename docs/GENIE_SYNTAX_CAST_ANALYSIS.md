# SYNTAX_ERROR and CAST_INVALID_INPUT Analysis
## Date: Jan 9, 2026

## 📊 Error Summary

| Error Type | Count | Pattern |
|---|---|---|
| **SYNTAX_ERROR** | 5 | Malformed SQL (missing parens, wrong casting) |
| **CAST_INVALID_INPUT** | 9 | Type mismatches (UUID→INT, STRING→DATE, STRING→DOUBLE) |
| **Total** | 14 | |

---

## 🔴 SYNTAX_ERROR Analysis (5 errors)

### Pattern 1: Malformed Date Casting in TVF Calls

**Errors:**
- `performance Q8`: Syntax error near '::' in `get_high_spill_queries`
- `security_auditor Q5`: Syntax error near 'AS' in `get_user_activity_summary`
- `security_auditor Q6`: Syntax error near 'AS' in `get_sensitive_table_access`

**Root Cause**: Incorrect parameter formatting, likely:
```sql
-- ❌ WRONG
CAST(CURRENT_DATE(), CURRENT_DATE()::STRING,
  10
) - INTERVAL 7 DAYS AS STRING)

-- ✅ CORRECT
CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
CAST(CURRENT_DATE() AS STRING),
10
```

**Common Pattern**: Parentheses mismatch, CAST positioned incorrectly

---

### Pattern 2: Complex CTE Syntax

**Errors:**
- `cost_intelligence Q23`: Syntax error at position 544
- `unified_health_monitor Q20`: Missing ')' near 'OUTER' at position 2384

**Root Cause**: Likely unclosed CTEs or JOIN clauses

---

## 🔴 CAST_INVALID_INPUT Analysis (9 errors)

### Pattern 1: UUID String → Numeric Type

**Errors:**
- `cost_intelligence Q19`: UUID → INT
- `performance Q7`: UUID → DOUBLE

**Example Error:**
```
The value '01f0ec1f-9c1f-1f18-858a-40a7fec0501d' of the type "STRING" 
cannot be cast to "INT" because it is malformed
```

**Root Cause**: Trying to cast `warehouse_id` (UUID string) to numeric type

**Fix**: Remove the CAST, keep as STRING, or fix column reference

---

### Pattern 2: Date String → Numeric Type

**Errors:**
- `performance Q10`: '2026-01-09' → DOUBLE
- `performance Q12`: '2025-12-26' → INT

**Example Error:**
```
The value '2026-01-09' of the type "STRING" 
cannot be cast to "DOUBLE" because it is malformed
```

**Root Cause**: Incorrect data type expectation, should stay as DATE/STRING

**Fix**: Use DATE functions properly, not numeric casting

---

### Pattern 3: Numeric String → DATE

**Errors:**
- `security_auditor Q8`: '7' → DATE
- `unified_health_monitor Q12`: '7' → DATE
- `job_health_monitor Q4`: '1' → DATE
- `job_health_monitor Q7`: '30' → DATE
- `job_health_monitor Q12`: '30' → DATE

**Example Error:**
```
The value '7' of the type "STRING" 
cannot be cast to "DATE" because it is malformed
```

**Root Cause**: Passing day count (e.g., `7`) where DATE is expected

**Likely Pattern:**
```sql
-- ❌ WRONG
WHERE DATE(7) ...

-- ✅ CORRECT
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
```

---

## 🎯 Fix Strategy

### Phase 1: SYNTAX_ERROR Fixes (Manual)

**Requires manual SQL review for each query:**

1. **cost_intelligence Q23** - Review CTE structure at position 544
2. **performance Q8** - Fix date casting in `get_high_spill_queries` call
3. **security_auditor Q5** - Fix CAST/AS positioning in TVF call
4. **security_auditor Q6** - Fix CAST/AS positioning in TVF call
5. **unified_health_monitor Q20** - Review CTE/JOIN structure at position 2384

**Approach**: Read each SQL query, identify syntax issue, apply targeted fix

---

### Phase 2: CAST_INVALID_INPUT Fixes (Pattern-based)

#### Fix Pattern A: UUID → Numeric (2 errors)
**Solution**: Remove CAST or fix column reference

#### Fix Pattern B: Date String → Numeric (2 errors)
**Solution**: Use DATE type correctly, remove numeric casting

#### Fix Pattern C: Numeric → DATE (5 errors)
**Solution**: Replace `DATE(7)` with proper interval arithmetic:
```sql
CURRENT_DATE() - INTERVAL 7 DAYS
```

---

## 📝 Investigation Plan

### Step 1: Examine Actual SQL Queries
- Read the 14 problematic queries from JSON files
- Document exact SQL for each error
- Identify specific line numbers and patterns

### Step 2: Consult Ground Truth
- Check TVF signatures in `tvfs.md` for correct parameter types
- Verify date handling patterns
- Confirm UUID column handling

### Step 3: Create Fix Script
- Systematic replacements for Pattern C (numeric → DATE)
- Manual fixes for SYNTAX_ERROR
- UUID casting fixes

### Step 4: Validate Fixes
- Run offline SQL syntax validation
- Deploy and re-run validation job
- Verify error count reduction

---

## 🔧 Expected Fixes

| Error Type | Auto-Fixable | Manual Review |
|---|---|---|
| SYNTAX_ERROR (5) | 0-2 | 3-5 |
| CAST UUID→Numeric (2) | 2 | 0 |
| CAST Date→Numeric (2) | 2 | 0 |
| CAST Numeric→DATE (5) | 5 | 0 |
| **Total** | **9-11 (64-79%)** | **3-5 (21-36%)** |

---

## Next Steps

1. ✅ Read all 14 SQL queries to understand exact patterns
2. ✅ Create targeted fix script
3. ✅ Apply fixes
4. ✅ Deploy bundle
5. ✅ Re-run validation
6. ✅ Verify error reduction

**Expected outcome**: Reduce 14 errors to 2-5 errors (71-86% success rate)

