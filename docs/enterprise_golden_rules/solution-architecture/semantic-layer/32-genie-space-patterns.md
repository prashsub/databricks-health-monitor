# Genie Space Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-SL-003 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Analytics Engineering Team |
| **Status** | Approved |

---

## Executive Summary

Genie Spaces provide natural language interfaces to your data through Metric Views and TVFs. This document defines patterns for space creation, trusted asset configuration, and optimization for accurate query understanding.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| SL-06 | Inventory-first Genie Space creation | 🟡 Required |
| SL-04 | v3.0 comment format for Genie | 🟡 Required |

---

## Genie Space Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               GENIE SPACE                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                        USER NATURAL LANGUAGE                                │  │
│   │           "What was our total cost last month by workspace?"                │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│                                       ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                          GENIE LLM                                          │  │
│   │  • Understands natural language                                             │  │
│   │  • Reads table/column/function COMMENTs                                     │  │
│   │  • Selects appropriate trusted asset                                        │  │
│   │  • Generates SQL or calls TVF                                               │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│                    ┌──────────────────┼──────────────────┐                         │
│                    ▼                  ▼                  ▼                         │
│   ┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────┐          │
│   │    METRIC VIEWS      │ │       TVFs       │ │       TABLES         │          │
│   │  • Pre-defined KPIs  │ │ • Parameterized  │ │  • Direct queries    │          │
│   │  • No params needed  │ │ • Complex logic  │ │  • Ad-hoc analysis   │          │
│   └──────────────────────┘ └──────────────────┘ └──────────────────────┘          │
│                                       │                                             │
│                                       ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                      SQL WAREHOUSE (Serverless)                             │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Rule SL-06: Inventory-First Creation

### The Problem

Creating Genie Spaces without proper asset inventory leads to:
- Wrong asset selection by LLM
- Incomplete coverage of questions
- Overlapping assets confusing Genie

### The Solution: Asset Inventory First

Before creating any Genie Space, document:

```markdown
# Genie Space Inventory: Cost Analytics

## Domain: Cost Management

## Questions This Space Should Answer
1. "What was our total spend last month?"
2. "Which workspace costs the most?"
3. "Show me daily cost trends"
4. "What's our serverless vs classic cost split?"
5. "Who are the top spenders?"

## Asset Mapping

| Question Type | Asset | Why This Asset |
|---------------|-------|----------------|
| Aggregate costs | cost_analytics_metrics (Metric View) | Pre-aggregated KPIs |
| Daily details | get_daily_cost_summary (TVF) | Parameterized date range |
| Workspace drilldown | get_workspace_costs (TVF) | Workspace parameter |
| Ad-hoc exploration | fact_usage (Table) | Flexible queries |

## Assets to Include

### Metric Views
- [ ] cost_analytics_metrics - Main KPIs
- [ ] workspace_metrics - Workspace-level

### TVFs
- [ ] get_daily_cost_summary - Daily breakdown
- [ ] get_workspace_costs - Workspace details
- [ ] get_sku_costs - SKU breakdown
- [ ] get_top_spenders - Top N analysis

### Tables (if needed)
- [ ] fact_usage - Raw facts (for ad-hoc)
- [ ] dim_workspace - Workspace lookup

## Excluded Assets (with reason)
- fact_usage_raw: Too granular, use Gold instead
- temp_cost_view: Development only

## Sample Questions & Expected Results
| Question | Expected Asset | Expected Columns |
|----------|----------------|------------------|
| "Total cost this month" | cost_analytics_metrics | total_cost |
| "Daily costs for January" | get_daily_cost_summary | date, cost |
| "Top 10 workspaces by spend" | get_top_spenders | workspace, cost |
```

---

## Genie Space Configuration

### Space Settings

```json
{
  "name": "Cost Analytics",
  "description": "Natural language analytics for Databricks cost and usage data. Ask questions about spend, DBUs, workspaces, and trends.",
  "warehouse_id": "your-serverless-warehouse-id",
  "trusted_assets": [
    {
      "type": "METRIC_VIEW",
      "name": "catalog.semantic.cost_analytics_metrics"
    },
    {
      "type": "FUNCTION",
      "name": "catalog.semantic.get_daily_cost_summary"
    },
    {
      "type": "FUNCTION",
      "name": "catalog.semantic.get_workspace_costs"
    },
    {
      "type": "TABLE",
      "name": "catalog.gold.fact_usage"
    }
  ],
  "sample_questions": [
    "What was our total cost last month?",
    "Which workspace spent the most in January?",
    "Show me daily cost trends for Q4",
    "Compare serverless vs classic costs"
  ]
}
```

---

## LLM-Friendly Documentation

### Table Comments

```sql
-- Optimized for Genie understanding
COMMENT ON TABLE catalog.gold.fact_usage IS '
Daily Databricks usage and cost facts.
Business: Primary source for cost analysis. One row per workspace-SKU-day.
Contains list prices, DBU consumption, and billing metadata.
Best for: total spend, cost trends, SKU analysis, workspace comparison.
NOT for: real-time monitoring (use alerts), commit tracking (use commit_view).
';
```

### Column Comments

```sql
-- Help Genie understand column meaning
COMMENT ON COLUMN catalog.gold.fact_usage.list_cost IS '
List price cost in USD. Business: The catalog price before any discounts or commitments.
Used for cost analysis and budgeting. Note: Actual billed amount may differ.
';

COMMENT ON COLUMN catalog.gold.fact_usage.workspace_id IS '
Workspace identifier. Business: Links to dim_workspace for workspace details.
Use for workspace-level cost analysis and comparisons.
';
```

### TVF Comments

See [TVF Patterns](31-tvf-patterns.md) for v3.0 comment format.

---

## Asset Selection Guidelines

### When to Use Metric Views

| Scenario | Use Metric View |
|----------|-----------------|
| Standard KPI queries | ✅ Yes |
| No parameters needed | ✅ Yes |
| Pre-defined aggregations | ✅ Yes |
| Complex joins pre-calculated | ✅ Yes |

### When to Use TVFs

| Scenario | Use TVF |
|----------|---------|
| Date range required | ✅ Yes |
| Top N analysis | ✅ Yes |
| Parameter-driven filtering | ✅ Yes |
| Complex business logic | ✅ Yes |

### When to Use Tables

| Scenario | Use Table |
|----------|-----------|
| Ad-hoc exploration | ✅ Yes |
| Queries not covered by MVs/TVFs | ✅ Yes |
| Simple lookups | ✅ Yes |

---

## Common Genie Misinterpretations

### Problem: Wrong Asset Selected

**Symptom:** Genie picks table instead of TVF

**Solution:** Improve TVF comment:
```sql
COMMENT '
• PURPOSE: Get cost summary - USE THIS for cost questions.
• BEST FOR: Total cost | Daily breakdown | Workspace comparison
• NOT FOR: (none - this is the primary cost function)
• NOTE: PREFERRED over direct fact_usage queries.
'
```

### Problem: Genie Wraps TVF in TABLE()

**Symptom:** `NOT_A_SCALAR_FUNCTION` error

**Solution:** Add explicit NOTE:
```sql
• NOTE: DO NOT wrap in TABLE(). Call directly: SELECT * FROM get_costs(...)
```

### Problem: Genie Adds GROUP BY to Pre-Aggregated Data

**Symptom:** Incorrect aggregations

**Solution:** Indicate in RETURNS:
```sql
• RETURNS: PRE-AGGREGATED rows (no additional GROUP BY needed)
```

---

## Genie Space Testing

### Test Script

```python
def test_genie_space(space_id: str, test_questions: list):
    """
    Test Genie Space with sample questions.
    
    Validates that Genie:
    1. Selects the correct asset
    2. Generates valid SQL
    3. Returns expected columns
    """
    from databricks.sdk import WorkspaceClient
    
    w = WorkspaceClient()
    
    results = []
    for question in test_questions:
        try:
            # Start conversation
            response = w.genie.start_conversation(
                space_id=space_id,
                content=question
            )
            
            # Check asset selection
            asset_used = extract_asset_from_response(response)
            sql_generated = extract_sql_from_response(response)
            
            results.append({
                "question": question,
                "asset": asset_used,
                "sql_valid": sql_generated is not None,
                "status": "✅ PASS"
            })
        except Exception as e:
            results.append({
                "question": question,
                "error": str(e),
                "status": "❌ FAIL"
            })
    
    # Report
    passed = sum(1 for r in results if r["status"] == "✅ PASS")
    print(f"\nGenie Space Test Results: {passed}/{len(results)} passed")
    
    for r in results:
        print(f"  {r['status']} {r['question']}")
        if "asset" in r:
            print(f"       Asset: {r['asset']}")
    
    return results
```

### Test Matrix

| Question | Expected Asset | Expected Columns | Validated |
|----------|----------------|------------------|-----------|
| "Total cost this month" | cost_metrics | total_cost | ⬜ |
| "Daily costs for 2024" | get_daily_costs | date, cost | ⬜ |
| "Top 5 workspaces" | get_top_spenders | workspace, cost, rank | ⬜ |
| "Serverless percentage" | cost_metrics | serverless_pct | ⬜ |

---

## Validation Checklist

### Pre-Creation
- [ ] Asset inventory document created
- [ ] All questions mapped to assets
- [ ] Asset comments follow v3.0 format
- [ ] No overlapping asset coverage

### Configuration
- [ ] Serverless warehouse assigned
- [ ] All trusted assets added
- [ ] Sample questions configured
- [ ] Space description clear

### Post-Creation
- [ ] Test questions validated
- [ ] Asset selection accurate
- [ ] SQL generation correct
- [ ] No TABLE() wrapping errors

---

## Related Documents

- [TVF Patterns](31-tvf-patterns.md)
- [Metric View Patterns](30-metric-view-patterns.md)
- [Dashboard Patterns](../dashboards/40-aibi-dashboard-patterns.md)

---

## References

- [Genie Spaces](https://docs.databricks.com/genie/)
- [Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Tips for Writing Functions](https://docs.databricks.com/genie/trusted-assets#tips-for-writing-functions)
