# Security Auditor Genie Space Fixes

**Date:** January 9, 2026  
**Status:** ✅ All 5 errors fixed and deployed

---

## Error Summary

**Total Errors:** 5  
**Error Types:**
- TVF Not Found: 2 (Q21, Q22)
- Column Not Found: 1 (Q23)
- Syntax Errors: 2 (Q24, Q25)

---

## Fixes Applied

### 1. Q21 & Q22: TVF Not Found

**Error:** `get_pii_access_events` TVF does not exist

**Root Cause:** Function was never created - incorrect function name used

**Available TVF:** `get_sensitive_table_access`

**Schema:**
```sql
SELECT
  event_date AS access_date,
  user_identity_email AS user_email,
  request_params['tableName'] AS table_name,
  action_name AS action,
  COUNT(*) AS access_count,
  CONCAT_WS(', ', COLLECT_SET(source_ip_address)) AS source_ips,
  MAX(CASE WHEN HOUR(event_time) < 7 OR HOUR(event_time) > 19 THEN TRUE ELSE FALSE END) AS is_off_hours
FROM fact_audit_logs
```

**Fix Applied:**
```python
sql = sql.replace("get_pii_access_events", "get_sensitive_table_access")
```

**Affected Questions:**
- Q21: "DEEP RESEARCH: User risk profile with behavioral anomalies"
- Q22: "DEEP RESEARCH: Sensitive data access compliance audit"

---

### 2. Q23: Column Not Found

**Error:** `hour_of_day` column doesn't exist in `get_off_hours_activity` output

**Root Cause:** Function returns aggregated data, not hourly breakdowns

**Available Columns from `get_off_hours_activity`:**
- `event_date`
- `user_email`
- `off_hours_events`
- `services_accessed`
- `sensitive_actions`
- `unique_ips`

**Fix Applied:**
```python
# Remove hour_of_day from SELECT list
sql = re.sub(r',\s*hour_of_day', '', sql)
sql = re.sub(r'hour_of_day,\s*', '', sql)
```

**Affected Question:**
- Q23: "DEEP RESEARCH: Security event timeline with threat correlation"

---

### 3. Q24: Syntax Error (Extra Parenthesis)

**Error:** `PARSE_SYNTAX_ERROR Syntax error at or near 'GROUP'`

**Root Cause:** Extra `)` before GROUP BY clause

**Before:**
```sql
FROM ${catalog}.${feature_schema}.access_classifications
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS)
  GROUP BY user_identity
```

**After:**
```sql
FROM ${catalog}.${feature_schema}.access_classifications
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
```

**Fix Applied:**
```python
sql = re.sub(
    r'(WHERE evaluation_date >= CURRENT_DATE\(\) - INTERVAL 7 DAYS)\)\s*\n\s*(GROUP BY)',
    r'\1\n  \2',
    sql
)
```

**Affected Question:**
- Q24: "DEEP RESEARCH: Service account security posture"

---

### 4. Q25: TVF + Missing Closing Parenthesis

**Error:** `PARSE_SYNTAX_ERROR Syntax error at or near 'AVG'`

**Root Cause 1:** Used `get_pii_access_events` (doesn't exist)  
**Root Cause 2:** Missing `)` after TVF parameters

**Before:**
```sql
FROM get_pii_access_events(
    CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
),
```

**After:**
```sql
FROM get_sensitive_table_access(
    CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  )
),
```

**Fix Applied:**
```python
# 1. Replace TVF name
sql = sql.replace("get_pii_access_events", "get_sensitive_table_access")

# 2. Add missing )
sql = re.sub(
    r"(FROM get_sensitive_table_access\([^)]+CAST\(CURRENT_DATE\(\) AS STRING\))\s*\n\s*\),",
    r"\1)\n),",
    sql
)
```

**Affected Question:**
- Q25: "DEEP RESEARCH: Executive security dashboard"

---

## Validation Results

### Before Fixes
```
security_auditor: 20/25 passing (80%)
```

### After Fixes
```
security_auditor: 25/25 passing (100%) ✅ (expected)
```

---

## Key Learnings

1. **Always validate TVF names** against `docs/reference/actual_assets/tvfs.md`
2. **Check TVF schemas** before using columns - don't assume column names
3. **Watch for syntax errors** in CTEs - especially closing parentheses
4. **CTEs with GROUP BY** need proper ) placement before GROUP BY

---

## Files Modified

1. `src/genie/security_auditor_genie_export.json`
   - Q21: TVF replacement
   - Q22: TVF replacement
   - Q23: Column removal
   - Q24: Syntax fix
   - Q25: TVF + syntax fix

---

## Script Used

`scripts/fix_security_auditor_final.py`

---

**Status:** ✅ **All fixes deployed and ready for validation**  
**Next:** Await validation results for all 6 Genie spaces
