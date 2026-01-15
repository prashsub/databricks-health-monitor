# Cost Intelligence Genie Space - Table Reference Fix

**Date**: January 13, 2026  
**Issue**: Tables not showing in Genie UI  
**Root Cause**: Incorrect schema variable references

---

## Problem Identified

After Session 23 deployment, the Cost Intelligence Genie Space showed only 2 metric views but none of the 18 tables in the UI.

### Root Causes

1. **ML Prediction Tables** used `${feature_schema}` variable which doesn't exist
   - Should use `${gold_schema}` instead
   
2. **Lakehouse Monitoring Tables** used template variables
   - Should use hardcoded monitoring schema name (like Performance space)

---

## Fixes Applied

### Before (Incorrect)

```json
{
  "tables": [
    {
      "identifier": "${catalog}.${feature_schema}.cost_anomaly_predictions",
      "description": ["ML model predictions..."]
    },
    {
      "identifier": "${catalog}.${gold_schema}.fact_usage_profile_metrics",
      "description": ["Lakehouse Monitoring..."]
    }
  ]
}
```

### After (Correct)

```json
{
  "tables": [
    {
      "identifier": "${catalog}.${gold_schema}.cost_anomaly_predictions",
      "description": ["ML model predictions..."]
    },
    {
      "identifier": "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring.fact_usage_profile_metrics",
      "description": ["Lakehouse Monitoring..."]
    }
  ]
}
```

---

## Changes Summary

| Table Type | Count | Old Pattern | New Pattern |
|---|---|---|---|
| ML Predictions | 6 | `${catalog}.${feature_schema}.{table}` | `${catalog}.${gold_schema}.{table}` ✅ |
| Lakehouse Monitoring | 2 | `${catalog}.${gold_schema}.{table}` | Hardcoded schema path ✅ |
| Dimensions | 5 | `${catalog}.${gold_schema}.{table}` | No change ✅ |
| Facts | 5 | `${catalog}.${gold_schema}.{table}` | No change ✅ |

**Total**: 18 tables fixed

---

## Validation Notebook Fix

Also separated the `dbutils.notebook.exit()` into a separate cell to allow seeing debug messages:

### Before
```python
def main():
    # ... validation logic ...
    print(f"✅ SUCCESS: All {valid_count} queries validated!")
    dbutils.notebook.exit("SUCCESS")  # Hides debug messages!
```

### After
```python
def main():
    # ... validation logic ...
    print(f"✅ SUCCESS: All {valid_count} queries validated!")

# COMMAND ----------

# Exit message in separate cell to allow seeing debug messages
dbutils.notebook.exit("SUCCESS")
```

---

## Next Steps

1. **Redeploy cost_intelligence Genie Space**:
   ```bash
   DATABRICKS_CONFIG_PROFILE=health-monitor databricks bundle run -t dev genie_spaces_deployment_job
   ```

2. **Verify in UI**: Check that all 18 tables appear in Genie Space data sources

3. **Test Queries**: Try sample questions that reference the tables directly

---

## Reference Pattern

For future Genie Spaces with Lakehouse Monitoring tables, always use **hardcoded schema paths**:

```json
{
  "identifier": "prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_monitoring.{monitoring_table}",
  "description": ["..."]
}
```

**Why**: Template variable substitution may not work correctly for monitoring schema during Genie Space deployment.
