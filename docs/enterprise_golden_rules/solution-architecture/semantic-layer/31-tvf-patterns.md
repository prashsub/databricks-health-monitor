# Table-Valued Function (TVF) Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-SL-002 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Analytics Engineering Team |
| **Status** | Approved |

---

## Executive Summary

Table-Valued Functions (TVFs) provide parameterized, reusable SQL queries optimized for Genie Spaces and programmatic access. This document defines the mandatory patterns for TVF development including parameter handling, comment format, and common pitfalls.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| SL-02 | TVFs must use STRING for date parameters | 🔴 Critical |
| SL-03 | Schema validation required before writing SQL | 🔴 Critical |
| SL-04 | v3.0 comment format for Genie optimization | 🟡 Required |
| SL-07 | Required parameters before optional | 🔴 Critical |
| SL-08 | No LIMIT with parameters (use ROW_NUMBER) | 🔴 Critical |
| SL-09 | Single aggregation pass (no Cartesian products) | 🔴 Critical |

---

## Rule SL-03: Schema Validation Before SQL

### The Principle

**ALWAYS consult Gold layer YAML schemas before writing ANY TVF SQL.**

### The Problem

```sql
-- Assumed column exists
SELECT workspace_owner FROM dim_workspace;
-- Error: UNRESOLVED_COLUMN - 'workspace_owner' does not exist
-- Actual column name: workspace_admin
```

### The Solution: Create SCHEMA_MAPPING.md

Before writing ANY TVF, create a schema mapping:

```markdown
# TVF Schema Mapping: get_workspace_costs

## Source Tables

### fact_usage (gold_layer_design/yaml/billing/fact_usage.yaml)
| Column | Type | In TVF |
|--------|------|--------|
| workspace_id | STRING | ✅ Join key |
| usage_date | DATE | ✅ Filter |
| list_cost | DECIMAL(18,6) | ✅ Aggregate |
| sku_id | STRING | ❌ Not needed |

### dim_workspace (gold_layer_design/yaml/workspace/dim_workspace.yaml)
| Column | Type | In TVF |
|--------|------|--------|
| workspace_id | STRING | ✅ Join key |
| workspace_name | STRING | ✅ Output |
| is_current | BOOLEAN | ✅ SCD2 filter |
| workspace_admin | STRING | ⚠️ Note: NOT 'workspace_owner' |
```

### Validation Script

```python
def validate_tvf_schema(tvf_sql: str, gold_yaml_dir: str) -> list:
    """Validate all column references in TVF SQL against Gold YAML."""
    import re
    import yaml
    from pathlib import Path
    
    errors = []
    
    # Load Gold schemas
    schemas = {}
    for yaml_file in Path(gold_yaml_dir).rglob("*.yaml"):
        config = yaml.safe_load(open(yaml_file))
        table = config['table_name']
        schemas[table] = {col['name'] for col in config['columns']}
    
    # Parse SQL for table.column references
    references = re.findall(r'(\w+)\.(\w+)', tvf_sql)
    
    for table, column in references:
        if table in schemas and column not in schemas[table]:
            errors.append(f"❌ Column '{column}' not in {table}")
    
    return errors
```

---

## Rule SL-02: STRING for Date Parameters

### The Problem

Genie Spaces cannot pass DATE type parameters. Using DATE causes runtime errors.

### The Pattern

```sql
-- ✅ CORRECT: STRING parameter with CAST
CREATE OR REPLACE FUNCTION catalog.schema.get_daily_costs(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
    workspace_name STRING,
    usage_date DATE,
    total_cost DECIMAL(18,2)
)
RETURN
SELECT 
    w.workspace_name,
    f.usage_date,
    SUM(f.list_cost) as total_cost
FROM catalog.schema.fact_usage f
JOIN catalog.schema.dim_workspace w 
    ON f.workspace_id = w.workspace_id AND w.is_current = true
WHERE f.usage_date >= CAST(start_date AS DATE)
  AND f.usage_date <= CAST(end_date AS DATE)
GROUP BY w.workspace_name, f.usage_date;

-- ❌ WRONG: DATE parameter type
CREATE OR REPLACE FUNCTION get_daily_costs(
    start_date DATE,  -- Genie cannot pass DATE values!
    end_date DATE
)
```

---

## Rule SL-07: Required Parameters Before Optional

### The Problem

Parameters with DEFAULT after parameters without DEFAULT cause compilation errors.

### The Pattern

```sql
-- ✅ CORRECT: Required first, optional last
CREATE OR REPLACE FUNCTION get_workspace_costs(
    workspace_name STRING,                          -- Required (no DEFAULT)
    start_date STRING DEFAULT '2024-01-01',        -- Optional
    end_date STRING DEFAULT '2024-12-31',          -- Optional
    limit_rows STRING DEFAULT '100'                 -- Optional
)

-- ❌ WRONG: Optional before required
CREATE OR REPLACE FUNCTION get_workspace_costs(
    start_date STRING DEFAULT '2024-01-01',        -- Optional first!
    workspace_name STRING                           -- Required after!
)
-- Error: Required parameter after optional parameter
```

---

## Rule SL-08: No LIMIT with Parameters

### The Problem

Using a parameter in LIMIT clause causes compilation errors.

```sql
-- ❌ WRONG
SELECT * FROM results LIMIT limit_rows;
-- Error: [INVALID_LIMIT_LIKE_EXPRESSION.IS_UNFOLDABLE]
```

### The Solution: ROW_NUMBER with WHERE

```sql
-- ✅ CORRECT
WITH ranked AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY total_cost DESC) AS rn
    FROM cost_summary
)
SELECT 
    workspace_name,
    total_cost,
    total_dbus
FROM ranked 
WHERE rn <= CAST(limit_rows AS INT);
```

---

## Rule SL-04: v3.0 Comment Format

### The Standard

All TVFs MUST use this bullet-point comment format:

```sql
CREATE OR REPLACE FUNCTION catalog.schema.get_cost_summary(
    start_date STRING DEFAULT '2024-01-01',
    end_date STRING DEFAULT '2024-12-31',
    limit_rows STRING DEFAULT '100'
)
RETURNS TABLE (
    workspace_name STRING,
    total_cost DECIMAL(18,2),
    total_dbus DECIMAL(18,6),
    cost_rank INT
)
COMMENT '
• PURPOSE: Get summarized cost metrics by workspace for a date range.

• BEST FOR: Total spend by workspace | Cost summary | Workspace comparison | Top spenders

• NOT FOR: Daily cost details (use get_daily_cost_details) | Real-time cost monitoring

• RETURNS: PRE-AGGREGATED rows (workspace_name, total_cost, total_dbus, cost_rank)

• PARAMS: start_date (YYYY-MM-DD, default: 2024-01-01), end_date (YYYY-MM-DD, default: 2024-12-31), limit_rows (default: 100)

• SYNTAX: SELECT * FROM get_cost_summary(''2024-01-01'', ''2024-12-31'', ''50'')

• NOTE: DO NOT wrap in TABLE(). DO NOT add GROUP BY - data is already aggregated. Results ordered by total_cost DESC.
'
RETURN
...
```

### Comment Section Reference

| Section | Purpose | Required |
|---------|---------|----------|
| **PURPOSE** | One-line description | ✅ Yes |
| **BEST FOR** | Example questions (pipe-separated) | ✅ Yes |
| **NOT FOR** | Redirect to correct asset | ✅ Yes |
| **RETURNS** | PRE-AGGREGATED or Individual + column list | ✅ Yes |
| **PARAMS** | All parameters with formats and defaults | ✅ Yes |
| **SYNTAX** | Exact call example with escaped quotes | ✅ Yes |
| **NOTE** | Critical caveats | ✅ Yes |

### Genie Misuse Prevention (NOTE Section)

| Misuse | Prevention Text |
|--------|-----------------|
| Wrapping in TABLE() | "DO NOT wrap in TABLE() - causes NOT_A_SCALAR_FUNCTION error" |
| Adding GROUP BY | "DO NOT add GROUP BY - data is already aggregated" |
| Missing parameters | "REQUIRED: workspace_name must be provided" |
| Wrong date format | "Date format must be YYYY-MM-DD" |

---

## Rule SL-09: Single Aggregation Pass

### The Problem: Cartesian Product Bug

When the same table is read multiple times in different CTEs and then joined, it creates inflated results.

```sql
-- ❌ WRONG: Cartesian product bug (results inflated 254x!)
WITH 
workspace_costs AS (
    SELECT workspace_id, SUM(cost) as total_cost
    FROM fact_usage  -- First read
    GROUP BY workspace_id
),
workspace_dbus AS (
    SELECT workspace_id, SUM(dbus) as total_dbus
    FROM fact_usage  -- Second read (same table!)
    GROUP BY workspace_id
)
SELECT 
    w.workspace_name,
    c.total_cost,
    d.total_dbus
FROM dim_workspace w
JOIN workspace_costs c ON w.workspace_id = c.workspace_id
JOIN workspace_dbus d ON w.workspace_id = d.workspace_id;
-- Bug: Each workspace_id in workspace_costs joins to EVERY matching row in workspace_dbus
```

### Detection Signs

- Results dramatically higher than expected (100x, 254x, etc.)
- "SUM of a SUM" pattern in output
- Same source table in multiple aggregation CTEs

### The Solution: Single Read

```sql
-- ✅ CORRECT: Single read of fact table
WITH workspace_metrics AS (
    SELECT 
        workspace_id,
        SUM(cost) as total_cost,
        SUM(dbus) as total_dbus
    FROM fact_usage
    GROUP BY workspace_id
)
SELECT 
    w.workspace_name,
    m.total_cost,
    m.total_dbus
FROM dim_workspace w
JOIN workspace_metrics m ON w.workspace_id = m.workspace_id;
```

### Prevention Rule

**Each source table should be read ONCE for aggregation.**

If you need different aggregations:
1. ✅ Combine into single CTE with multiple columns
2. ✅ Use CASE WHEN for conditional aggregations
3. ❌ Never create multiple CTEs from the same table for separate aggregations

---

## Complete TVF Template

```sql
-- ============================================================================
-- TVF: get_workspace_cost_summary
-- Description: Summarized cost metrics by workspace
-- Author: [Name]
-- Created: [Date]
-- ============================================================================

CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_workspace_cost_summary(
    -- Required parameters (no DEFAULT) first
    -- Optional parameters (with DEFAULT) last
    start_date STRING DEFAULT '2024-01-01',
    end_date STRING DEFAULT '2024-12-31',
    limit_rows STRING DEFAULT '100'
)
RETURNS TABLE (
    workspace_name STRING,
    total_cost DECIMAL(18,2),
    total_dbus DECIMAL(18,6),
    avg_daily_cost DECIMAL(18,2),
    cost_rank INT
)
COMMENT '
• PURPOSE: Get summarized cost metrics by workspace for a date range.

• BEST FOR: Total spend by workspace | Cost comparison | Top spenders | Budget analysis

• NOT FOR: Daily cost breakdown (use get_daily_costs) | SKU-level details (use get_sku_costs)

• RETURNS: PRE-AGGREGATED rows (workspace_name, total_cost, total_dbus, avg_daily_cost, cost_rank)

• PARAMS: start_date (YYYY-MM-DD, default: 2024-01-01), end_date (YYYY-MM-DD, default: 2024-12-31), limit_rows (default: 100)

• SYNTAX: SELECT * FROM get_workspace_cost_summary(''2024-01-01'', ''2024-12-31'', ''50'')

• NOTE: DO NOT wrap in TABLE(). DO NOT add GROUP BY - data is already aggregated. Ordered by total_cost DESC.
'
RETURN
WITH workspace_metrics AS (
    -- Single aggregation pass (Rule SL-09)
    SELECT 
        f.workspace_id,
        SUM(f.list_cost) as total_cost,
        SUM(f.dbus_consumed) as total_dbus,
        AVG(f.list_cost) as avg_daily_cost,
        COUNT(DISTINCT f.usage_date) as days_active
    FROM ${catalog}.${gold_schema}.fact_usage f
    WHERE f.usage_date >= CAST(start_date AS DATE)
      AND f.usage_date <= CAST(end_date AS DATE)
    GROUP BY f.workspace_id
),
ranked AS (
    SELECT 
        w.workspace_name,
        m.total_cost,
        m.total_dbus,
        m.avg_daily_cost,
        ROW_NUMBER() OVER (ORDER BY m.total_cost DESC) as cost_rank
    FROM workspace_metrics m
    JOIN ${catalog}.${gold_schema}.dim_workspace w 
        ON m.workspace_id = w.workspace_id 
        AND w.is_current = true  -- SCD2 filter!
)
SELECT 
    workspace_name,
    total_cost,
    total_dbus,
    avg_daily_cost,
    cost_rank
FROM ranked
WHERE cost_rank <= CAST(limit_rows AS INT);  -- Use WHERE, not LIMIT
```

---

## Validation Checklist

### Pre-Development
- [ ] Schema mapping document created
- [ ] All column references verified against Gold YAML
- [ ] SCD2 dimensions have `is_current = true` filter planned
- [ ] Join paths documented

### Code Review
- [ ] Date parameters use STRING type
- [ ] Required parameters before optional
- [ ] No `LIMIT parameter` (uses ROW_NUMBER + WHERE)
- [ ] Single aggregation pass per source table
- [ ] v3.0 comment format complete
- [ ] NOTE includes "DO NOT wrap in TABLE()"

### Pre-Deployment
- [ ] Schema validation script passes
- [ ] TVF executes successfully
- [ ] Results match expected values
- [ ] Genie Space can discover the TVF

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `UNRESOLVED_COLUMN` | Column doesn't exist | Check Gold YAML |
| `NOT_A_SCALAR_FUNCTION` | TVF wrapped in TABLE() | Add NOTE to comment |
| `INVALID_LIMIT_LIKE_EXPRESSION` | Parameter in LIMIT | Use ROW_NUMBER + WHERE |
| Results inflated 100x+ | Cartesian product | Single aggregation pass |
| Required parameter after optional | Wrong param order | Reorder parameters |
| `Parameter type DATE not supported` | DATE param in Genie | Use STRING + CAST |

---

## Related Documents

- [Metric View Patterns](30-metric-view-patterns.md)
- [Genie Space Patterns](32-genie-space-patterns.md)
- [Gold Layer Patterns](../data-pipelines/12-gold-layer-patterns.md)

---

## References

- [TVF SQL Reference](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-qry-select-tvf)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
