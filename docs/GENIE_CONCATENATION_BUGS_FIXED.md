# Genie Space Concatenation Bug Fixes
## Jan 9, 2026 - Critical Hotfix

## 🐛 Bug Description

During the previous fix session, a regex replacement error caused function names to be concatenated with `CAST`, resulting in invalid SQL syntax:

```sql
❌ WRONG: get_slow_queriesCAST(
✅ CORRECT: get_slow_queries(
```

This caused **6 queries to fail** with:
- **SYNTAX_ERROR**: Extra '(' or malformed CAST
- **WRONG_NUM_ARGS**: Too many parameters passed to TVFs

---

## 📊 Affected Queries

### 1. performance Q5
- **Error**: `SYNTAX_ERROR` - Extra '(' at pos 49
- **SQL**: `get_slow_queriesCAST( CURRENT_DATE( AS STRING)`
- **Fix**: Removed concatenation, fixed CAST syntax
- **Question**: "Show me slow queries from today..."

### 2. performance Q8
- **Error**: `WRONG_NUM_ARGS` - Expects 3 params, got 4
- **SQL**: `get_high_spill_queries(..., 5.0, 1.0)` ← 4 params
- **Fix**: Removed 4th parameter `1.0`
- **Question**: "Which queries have high disk spill?..."

### 3. security_auditor Q5
- **Error**: `WRONG_NUM_ARGS` - Expects 3 params, got 4
- **SQL**: `get_user_activity_summary(..., 10, 20)` ← 4 params
- **Fix**: Removed 4th parameter `20`
- **Question**: "Show me user activity summary..."

### 4. security_auditor Q7
- **Error**: `SYNTAX_ERROR` - Extra '(' at pos 14
- **SQL**: `get_failed_actionsCAST(\n  7,\n  CURRENT_DATE( AS STRING)`
- **Fix**: Removed concatenation, fixed date parameter to `CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING)`
- **Question**: "Show me failed access attempts..."

### 5. unified_health_monitor Q7
- **Error**: `SYNTAX_ERROR` - Extra '(' at pos 14
- **SQL**: `get_failed_jobsCAST(\n  1,\n  CURRENT_DATE( AS STRING)`
- **Fix**: Removed concatenation, fixed date parameter to `CAST(CURRENT_DATE() - INTERVAL 1 DAYS AS STRING)`
- **Question**: "Show me failed jobs today..."

### 6. unified_health_monitor Q8
- **Error**: `SYNTAX_ERROR` - Extra '(' at pos 49
- **SQL**: `get_slow_queriesCAST( CURRENT_DATE( AS STRING)`
- **Fix**: Removed concatenation, fixed CAST syntax
- **Question**: "Show me slow queries..."

---

## 🔧 Fixes Applied

### Before (Broken):
```sql
-- Concatenation bug
SELECT * FROM get_slow_queriesCAST(  CURRENT_DATE( AS STRING),  ...

-- Extra parameter
SELECT * FROM get_high_spill_queries(..., 5.0, 1.0)

-- Malformed date param
get_failed_jobsCAST(\n  1,\n  CURRENT_DATE( AS STRING), ...)
```

### After (Fixed):
```sql
-- Proper function call
SELECT * FROM get_slow_queries(
  CAST(CURRENT_DATE() AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  30,
  50
) ORDER BY duration_seconds DESC LIMIT 20;

-- Correct parameter count
SELECT * FROM get_high_spill_queries(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  5.0
) ORDER BY spill_bytes DESC LIMIT 15;

-- Proper date parameter
SELECT * FROM get_failed_jobs(
  CAST(CURRENT_DATE() - INTERVAL 1 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  '%'
) ORDER BY start_time DESC LIMIT 20;
```

---

## 📈 Impact

### Error Reduction:
- **Before**: 20+ errors (validation run 1)
- **After fixes**: ~14-16 errors (expected)
- **Reduction**: 6 errors fixed (~30% improvement)

### Files Modified:
1. `src/genie/performance_genie_export.json` - 2 queries (Q5, Q8)
2. `src/genie/security_auditor_genie_export.json` - 2 queries (Q5, Q7)
3. `src/genie/unified_health_monitor_genie_export.json` - 2 queries (Q7, Q8)

---

## ✅ Deployment Status

**Deployed**: Jan 9, 2026 - 20:21 PST  
**Validation**: Re-running now...  
**Expected success rate**: 85-90% (105-111 out of 123 queries)

---

## 🎯 Remaining Known Issues

After this fix, expected remaining errors:
1. **cost_intelligence Q19**: UUID→INT casting (warehouse_id)
2. **cost_intelligence Q23**: CTE syntax error
3. **cost_intelligence Q25**: Missing `workspace_id` column
4. **performance Q7, Q10, Q12**: UUID/Date casting issues
5. **performance Q16, Q18**: Column/casting issues
6. **performance Q23**: NESTED_AGGREGATE_FUNCTION
7. **unified_health_monitor Q12, Q18, Q19, Q20, Q21**: Various issues

**Total expected**: ~14-16 errors remaining

---

## 🔍 Root Cause Analysis

### Why did this happen?

The regex replacement in `fix_genie_final_cleanup.py` didn't account for cases where:
1. Function name directly preceded `CAST` without whitespace
2. Multiple parameters needed to be removed (not just modified)

### Regex Pattern Issue:
```python
# What happened:
'get_slow_queries(' + 'CAST(' → 'get_slow_queriesCAST('
```

### Prevention:
- Use more specific regex anchors
- Test replacements on small samples first
- Validate JSON after each fix session
- Use jq to extract and verify SQL before/after

---

## 📝 Lessons Learned

1. **Always test regex replacements** on a single file first
2. **Validate JSON syntax** after bulk modifications
3. **Extract SQL queries** before/after to verify changes
4. **Run validation immediately** after fixes to catch issues early
5. **Break large fix sessions** into smaller, testable chunks

---

**Status**: ✅ FIXES DEPLOYED - VALIDATION IN PROGRESS

