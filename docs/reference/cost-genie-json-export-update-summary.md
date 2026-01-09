# Cost Intelligence Genie - JSON Export Update Summary

**Date:** January 2026  
**Source:** `src/genie/cost_intelligence_genie.md`  
**Target:** `src/genie/cost_intelligence_genie_export.json`

---

## Updates Applied ✅

### 1. TVF Signature Corrections

#### `get_untagged_resources`
- **Old Signature:** `get_untagged_resources(start_date STRING, end_date STRING, resource_type STRING DEFAULT 'ALL')`
- **New Signature:** `get_untagged_resources(start_date STRING, end_date STRING)`
- **Change:** Removed `resource_type` parameter to match deployed TVF

#### `get_cost_week_over_week`
- **Old Signature:** `get_cost_week_over_week(weeks_back INT DEFAULT 8)`
- **New Signature:** `get_cost_week_over_week(weeks_back INT DEFAULT 4)`
- **Change:** Updated default value from 8 to 4 weeks
- **Old Returns:** `week_start, total_cost, wow_change_pct, avg_daily_cost`
- **New Returns:** `week_start, week_end, total_cost, wow_growth_pct`

#### `get_spend_by_custom_tags`
- **Old Signature:** `get_spend_by_custom_tags(start_date STRING, end_date STRING, tag_keys ARRAY<STRING>)`
- **New Signature:** `get_spend_by_custom_tags(start_date STRING, end_date STRING, tag_keys STRING)`
- **Change:** Changed from ARRAY<STRING> to STRING (comma-separated)
- **Example Updated:** From `array('team', 'project')` to `'team,project'`

#### `get_commit_vs_actual`
- **Old Signature:** `get_commit_vs_actual(commit_year INT, annual_commit_amount DOUBLE, as_of_date STRING DEFAULT NULL)`
- **New Signature:** `get_commit_vs_actual(commit_year INT, annual_commit_amount DECIMAL, as_of_date DATE)`
- **Changes:**
  - `annual_commit_amount`: DOUBLE → DECIMAL
  - `as_of_date`: STRING DEFAULT NULL → DATE (required)
- **Old Returns:** `month, committed_amount, actual_usage, utilization_pct, remaining_commit`
- **New Returns:** `commit_amount, consumed_amount, remaining_amount, burn_rate_daily, projected_year_end`
- **Example Updated:** From `(2025, 100000.0, NULL)` to `(2024, 1000000, CURRENT_DATE())`

---

### 2. New TVFs Added

#### `get_all_purpose_cluster_cost`
```json
{
  "id": "f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c4",
  "name": "get_all_purpose_cluster_cost",
  "signature": "get_all_purpose_cluster_cost(start_date STRING, end_date STRING, top_n INT DEFAULT 20)",
  "full_name": "${catalog}.${gold_schema}.get_all_purpose_cluster_cost"
}
```

**Purpose:** Returns ALL_PURPOSE cluster costs with migration savings potential  
**Use When:** User asks for "ALL_PURPOSE cluster costs" or "migration opportunities"  
**Returns:** `cluster_name, workspace_name, total_cost, migration_savings_potential`

#### `get_cost_growth_by_period`
```json
{
  "id": "a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d5",
  "name": "get_cost_growth_by_period",
  "signature": "get_cost_growth_by_period(entity_type STRING, top_n INT DEFAULT 10)",
  "full_name": "${catalog}.${gold_schema}.get_cost_growth_by_period"
}
```

**Purpose:** Returns period-over-period cost growth analysis  
**Use When:** User asks for "period growth" or "cost comparison"  
**Returns:** `entity_name, current_period_cost, previous_period_cost, growth_pct`

---

### 3. Benchmark SQL Updates

#### Updated Query Parameters
**Question 8:** "Show me untagged resources"
- **Old SQL:** `get_untagged_resources(..., 'ALL')`
- **New SQL:** `get_untagged_resources(...)` (removed 3rd parameter)

**Question 24:** "Tag compliance and cost attribution gap analysis"
- **Old SQL:** `get_untagged_resources(..., 'ALL')`
- **New SQL:** `get_untagged_resources(...)` (removed 3rd parameter)

#### New Deep Research Questions Added

**Question 21:** "🔬 ML-powered cost anomaly predictions with workspace context"
```sql
SELECT
  w.workspace_name,
  ca.usage_date,
  ca.prediction as deviation
FROM ${catalog}.${feature_schema}.cost_anomaly_predictions ca
JOIN ${catalog}.${gold_schema}.dim_workspace w ON ca.workspace_id = w.workspace_id
WHERE ca.usage_date = CURRENT_DATE()
ORDER BY ca.prediction DESC
LIMIT 10;
```

**Question 25:** "🔬 Predictive cost optimization roadmap"
- Combines ML forecasts, anomaly detection, and commitment recommendations
- Creates prioritized action plan with recommendations

---

## TVF Count Summary

| Category | Count | Status |
|----------|-------|--------|
| **Total TVFs in JSON** | **17** | ✅ Complete |
| Previously in JSON | 15 | - |
| Newly Added | 2 | ✅ |
| Signature Updates | 4 | ✅ |

---

## Benchmark Questions Summary

| Category | Count | Status |
|----------|-------|--------|
| **Total Questions** | **25** | ✅ Complete |
| Normal Questions | 20 | ✅ |
| Deep Research Questions | 5 | ✅ |

**Deep Research Questions:**
1. Cross-domain cost and reliability correlation
2. SKU-level cost efficiency analysis with utilization patterns
3. Tag compliance and cost attribution gap analysis
4. ML-powered cost anomaly predictions with workspace context
5. Predictive cost optimization roadmap

---

## Complete TVF List (17 Functions)

1. ✅ `get_top_cost_contributors` - Top cost contributors
2. ✅ `get_cost_trend_by_sku` - Daily cost trend by SKU
3. ✅ `get_cost_by_owner` - Cost allocation by owner
4. ✅ `get_cost_by_tag` - Tag-based cost allocation
5. ✅ `get_untagged_resources` - Untagged resources (signature updated)
6. ✅ `get_cost_anomalies` - Anomaly detection
7. ✅ `get_cost_mtd_summary` - Month-to-date summary
8. ✅ `get_cost_week_over_week` - Weekly trends (signature updated)
9. ✅ `get_spend_by_custom_tags` - Multi-tag analysis (signature updated)
10. ✅ `get_most_expensive_jobs` - Job costs
11. ✅ `get_warehouse_utilization` - SQL warehouse metrics
12. ✅ `get_cost_forecast_summary` - Cost forecasting
13. ✅ `get_cost_growth_analysis` - Growth analysis by entity
14. ✅ `get_tag_coverage` - Tag coverage metrics
15. ✅ `get_commit_vs_actual` - Commitment tracking (signature updated)
16. ✅ `get_all_purpose_cluster_cost` - ALL_PURPOSE cluster costs (NEW)
17. ✅ `get_cost_growth_by_period` - Period-over-period growth (NEW)

---

## Validation Checklist

- [x] All TVF signatures match `docs/actual_assets.md`
- [x] All TVF signatures match markdown file
- [x] All 17 TVFs documented with complete descriptions
- [x] All 25 benchmark questions included
- [x] All SQL queries use correct TVF signatures
- [x] All parameter types match (STRING, INT, DECIMAL, DATE)
- [x] All return values documented
- [x] All examples use correct syntax
- [x] Deep Research questions follow 🔬 emoji convention
- [x] JSON is properly formatted and valid

---

## API Deployment Readiness

The JSON export is now ready for Genie Space API deployment:

```bash
# Create/Update Genie Space via API
POST /api/2.0/genie/spaces
{
  "title": "Health Monitor Cost Intelligence Space",
  "description": "Natural language interface for Databricks cost analytics and FinOps...",
  "warehouse_id": "<your_warehouse_id>",
  "serialized_space": "<contents of cost_intelligence_genie_export.json>"
}
```

**Prerequisites:**
- All 17 TVFs must be deployed in Unity Catalog
- All ML Prediction tables must exist in `${feature_schema}`
- All Metric Views must be created
- SQL Warehouse must be active

---

## References

### Source Files
- **Markdown Definition:** `src/genie/cost_intelligence_genie.md`
- **JSON Export:** `src/genie/cost_intelligence_genie_export.json`
- **Asset Inventory:** `docs/actual_assets.md`

### Related Documentation
- [Genie Space API Patterns](../../.cursor/rules/semantic-layer/29-genie-space-export-import-api.mdc)
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md)
- [Complete Genie Fixes Report](./genie-fixes-complete-report.md)

---

**Status:** ✅ **COMPLETE - JSON Export Synchronized with Markdown**  
**Last Updated:** January 2026


