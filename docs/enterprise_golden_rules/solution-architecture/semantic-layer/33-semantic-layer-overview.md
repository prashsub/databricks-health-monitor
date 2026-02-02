# Semantic Layer Development Standards

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SL-01 through SL-06 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Analytics Engineering Team |
| **Status** | Approved |

---

## Executive Summary

The Semantic Layer provides business-friendly interfaces to the Gold layer through Metric Views and Table-Valued Functions (TVFs). This layer is optimized for natural language queries via Genie Spaces and AI/BI dashboards.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| SL-01 | Metric Views must use v1.1 YAML (no `name` field) | 🔴 Critical |
| SL-02 | TVFs must use STRING for date parameters | 🔴 Critical |
| SL-03 | Schema validation required before writing SQL | 🔴 Critical |
| SL-04 | Standardized v3.0 comment format for Genie | 🟡 Required |
| SL-05 | No transitive joins in Metric Views | 🔴 Critical |
| SL-06 | Pre-deployment TVF validation required | 🟡 Required |

---

## Part 1: Metric Views

### Rule SL-01: Metric View YAML Structure (v1.1)

**CRITICAL: The Metric View name is in the CREATE VIEW statement, NOT in the YAML.**

```python
# ✅ CORRECT: Name from filename, not YAML
view_name = yaml_file.stem  # e.g., "cost_analytics_metrics" from filename
fqn = f"{catalog}.{schema}.{view_name}"

create_sql = f"""
CREATE VIEW {fqn}
WITH METRICS
LANGUAGE YAML
COMMENT '{comment}'
AS $$
{yaml_content}  -- NO 'name' field in YAML!
$$
"""

# ❌ WRONG: name field in YAML
# yaml:
#   name: cost_analytics_metrics  # ERROR: Unrecognized field "name"
```

### Unsupported Fields in v1.1

| Field | Error | Action |
|-------|-------|--------|
| `name` | `Unrecognized field "name"` | ❌ Never include |
| `time_dimension` | `Unrecognized field` | ❌ Remove |
| `window_measures` | `Unrecognized field` | ❌ Remove |
| `join_type` | Unsupported | ❌ Remove |

### Standard Metric View YAML Structure

```yaml
version: "1.1"
comment: >
  PURPOSE: Comprehensive cost analytics for Databricks billing.
  
  BEST FOR: Total spend by workspace | Cost trend over time | SKU breakdown
  
  NOT FOR: Commit tracking (use commit_tracking) | Real-time alerts (use TVF)
  
  DIMENSIONS: usage_date, workspace_name, sku_name, owner, tag_team
  
  MEASURES: total_cost, total_dbus, cost_7d, cost_30d, tag_coverage_pct
  
  SOURCE: fact_usage (billing domain)
  
  JOINS: dim_workspace (workspace details), dim_sku (SKU details)
  
  NOTE: Cost values are list prices. Actual billed may differ.

source: ${catalog}.${gold_schema}.fact_usage

joins:
  - name: dim_workspace
    source: ${catalog}.${gold_schema}.dim_workspace
    'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
  
  - name: dim_sku
    source: ${catalog}.${gold_schema}.dim_sku
    'on': source.sku_id = dim_sku.sku_id

dimensions:
  - name: usage_date
    expr: source.usage_date
    comment: Date of usage for time-based analysis
    display_name: Usage Date
    synonyms:
      - date
      - day

  - name: workspace_name
    expr: dim_workspace.workspace_name
    comment: Databricks workspace name for cost allocation
    display_name: Workspace
    synonyms:
      - workspace
      - environment

measures:
  - name: total_cost
    expr: SUM(source.list_cost)
    comment: Total cost at list price. Primary spend metric.
    display_name: Total Cost
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
      abbreviation: compact
    synonyms:
      - cost
      - spend
      - dollars
```

### Rule SL-05: No Transitive Joins

**Metric Views v1.1 DO NOT support chained joins.**

```yaml
# ❌ WRONG: Transitive join (dim_property → dim_destination)
joins:
  - name: dim_property
    source: catalog.schema.dim_property
    'on': source.property_id = dim_property.property_id
  
  - name: dim_destination
    source: catalog.schema.dim_destination
    'on': dim_property.destination_id = dim_destination.destination_id  # ❌ ERROR!
```

**Error:** `dim_property.destination_id cannot be resolved`

**Solutions:**

1. **Use FK directly:**
```yaml
dimensions:
  - name: destination_id
    expr: dim_property.destination_id  # ✅ Use FK, not joined name
```

2. **Denormalize fact table** (add `destination_id` to fact during Gold ETL)

3. **Create enriched view** (pre-join the data)

---

## Part 2: Table-Valued Functions (TVFs)

### Rule SL-02: STRING for Date Parameters

**Genie Spaces do not support DATE type parameters. Always use STRING and CAST.**

```sql
-- ✅ CORRECT: STRING parameter with CAST
CREATE OR REPLACE FUNCTION catalog.schema.get_daily_costs(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
    end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (...)
RETURN
SELECT ...
WHERE usage_date >= CAST(start_date AS DATE)
  AND usage_date <= CAST(end_date AS DATE);

-- ❌ WRONG: DATE parameter
CREATE OR REPLACE FUNCTION get_daily_costs(
    start_date DATE,  -- ❌ Genie cannot pass DATE values
    end_date DATE
)
```

### Rule: Required Parameters First

**All parameters with DEFAULT must come AFTER parameters without DEFAULT.**

```sql
-- ✅ CORRECT: Required first, optional last
CREATE OR REPLACE FUNCTION get_workspace_costs(
    workspace_name STRING,                          -- Required (no DEFAULT)
    start_date STRING DEFAULT '2024-01-01',        -- Optional (has DEFAULT)
    limit_rows STRING DEFAULT '100'                 -- Optional (has DEFAULT)
)

-- ❌ WRONG: Optional before required
CREATE OR REPLACE FUNCTION get_workspace_costs(
    start_date STRING DEFAULT '2024-01-01',        -- ❌ Optional first!
    workspace_name STRING                           -- ❌ Required after optional!
)
```

### Rule: Use WHERE Instead of LIMIT for Parameters

**`LIMIT parameter` causes compilation errors. Use `ROW_NUMBER()` with `WHERE`.**

```sql
-- ❌ WRONG: Parameter in LIMIT clause
SELECT * FROM results LIMIT limit_rows;
-- Error: [INVALID_LIMIT_LIKE_EXPRESSION.IS_UNFOLDABLE]

-- ✅ CORRECT: ROW_NUMBER with WHERE
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY cost DESC) AS rn
    FROM results
)
SELECT * FROM ranked WHERE rn <= CAST(limit_rows AS INT);
```

### Rule SL-04: Standardized TVF Comment Format (v3.0)

**All TVFs MUST use this bullet-point comment format for Genie optimization:**

```sql
CREATE OR REPLACE FUNCTION catalog.schema.get_cost_summary(
    start_date STRING DEFAULT '2024-01-01',
    end_date STRING DEFAULT '2024-12-31'
)
RETURNS TABLE (
    workspace_name STRING,
    total_cost DECIMAL(18,2),
    total_dbus DECIMAL(18,6)
)
COMMENT '
• PURPOSE: Get summarized cost metrics by workspace for a date range.

• BEST FOR: Total spend by workspace | Cost summary | Workspace comparison

• NOT FOR: Daily cost details (use get_daily_cost_details) | Real-time alerts

• RETURNS: PRE-AGGREGATED rows (workspace_name, total_cost, total_dbus)

• PARAMS: start_date (YYYY-MM-DD, default: 2024-01-01), end_date (YYYY-MM-DD, default: 2024-12-31)

• SYNTAX: SELECT * FROM get_cost_summary(''2024-01-01'', ''2024-12-31'')

• NOTE: DO NOT wrap in TABLE(). DO NOT add GROUP BY - data is already aggregated.
'
RETURN
...
```

### Critical Comment Sections

| Section | Purpose | Example |
|---------|---------|---------|
| **PURPOSE** | One-line description | "Get summarized cost metrics by workspace" |
| **BEST FOR** | Example questions (pipe-separated) | "Total spend \| Cost by SKU" |
| **NOT FOR** | Redirect to correct asset | "Real-time alerts (use alerting TVF)" |
| **RETURNS** | Pre-aggregated OR individual rows + columns | "PRE-AGGREGATED rows (col1, col2)" |
| **PARAMS** | Parameters with formats and defaults | "start_date (YYYY-MM-DD, default: 2024-01-01)" |
| **SYNTAX** | Exact call example | "SELECT * FROM func('val')" |
| **NOTE** | Critical caveats | "DO NOT wrap in TABLE()" |

### Common Genie Misuse Prevention

| Misuse Pattern | Prevention (in NOTE section) |
|----------------|------------------------------|
| Wrapping in `TABLE()` | "DO NOT wrap in TABLE() - causes NOT_A_SCALAR_FUNCTION error" |
| Adding GROUP BY to aggregates | "DO NOT add GROUP BY - data is already aggregated" |
| Missing required params | "REQUIRED: workspace_name must be provided" |

---

## Rule SL-03: Schema Validation Before SQL

**CRITICAL: Always verify columns exist in Gold YAML before writing TVF SQL.**

### The Problem

```sql
-- Assumed column exists
SELECT workspace_owner FROM dim_workspace;  -- ❌ Column doesn't exist!
-- Error: UNRESOLVED_COLUMN
```

### The Solution: Create SCHEMA_MAPPING.md

Before writing any TVF, create a schema mapping document:

```markdown
# TVF Schema Mapping: get_cost_summary

## Source Tables

### fact_usage (from gold_layer_design/yaml/billing/fact_usage.yaml)
| Column | Type | In TVF |
|--------|------|--------|
| workspace_id | STRING | ✅ Yes (join key) |
| usage_date | DATE | ✅ Yes (filter) |
| list_cost | DECIMAL | ✅ Yes (aggregate) |
| sku_id | STRING | ❌ Not needed |

### dim_workspace (from gold_layer_design/yaml/workspace/dim_workspace.yaml)
| Column | Type | In TVF |
|--------|------|--------|
| workspace_id | STRING | ✅ Yes (join key) |
| workspace_name | STRING | ✅ Yes (output) |
| is_current | BOOLEAN | ✅ Yes (SCD2 filter) |
| owner | STRING | ⚠️ Verify exists! |
```

### Schema Validation Script

```python
def validate_tvf_columns(sql_file: str, gold_yaml_dir: str) -> list:
    """
    Validate all column references in TVF SQL against Gold YAML schemas.
    
    Returns list of errors (empty if valid).
    """
    import re
    
    errors = []
    
    # Parse SQL for table.column references
    sql = Path(sql_file).read_text()
    references = re.findall(r'(\w+)\.(\w+)', sql)
    
    # Load Gold schemas
    schemas = {}
    for yaml_file in Path(gold_yaml_dir).rglob("*.yaml"):
        config = yaml.safe_load(open(yaml_file))
        table = config['table_name']
        schemas[table] = {col['name'] for col in config['columns']}
    
    # Validate each reference
    for table, column in references:
        if table in schemas:
            if column not in schemas[table]:
                errors.append(f"❌ Column '{column}' not found in {table}")
    
    return errors

# Run before deployment
errors = validate_tvf_columns("tvfs/get_cost_summary.sql", "gold_layer_design/yaml")
if errors:
    print("\n".join(errors))
    raise ValueError("Schema validation failed")
```

---

## Cartesian Product Prevention

### The Bug: Re-Joining Aggregated Tables

When a source table is read multiple times in different CTEs and then joined, it creates a Cartesian product.

```sql
-- ❌ WRONG: Cartesian product bug
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
JOIN workspace_dbus d ON w.workspace_id = d.workspace_id;  -- ❌ Cartesian!
-- Result: total_cost * total_dbus inflation (e.g., 254x actual value!)
```

### Detection Signs

- Results are dramatically higher than expected (100x, 254x)
- SUM of a SUM in the output (e.g., `SUM(c.total_cost)`)
- Same source table in multiple aggregation CTEs

### The Fix: Single Aggregation Pass

```sql
-- ✅ CORRECT: Single read of fact table
WITH workspace_metrics AS (
    SELECT 
        workspace_id,
        SUM(cost) as total_cost,      -- Aggregated once
        SUM(dbus) as total_dbus       -- Aggregated once
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

---

## Validation Checklist

### Pre-Development (TVFs)
- [ ] Created SCHEMA_MAPPING.md for the TVF
- [ ] Verified all columns exist in Gold YAML
- [ ] Verified SCD2 dimensions have `is_current` filter
- [ ] Identified join paths through dimensions

### Pre-Development (Metric Views)
- [ ] YAML has no `name` field
- [ ] YAML has no `time_dimension` or `window_measures`
- [ ] All joins are direct (source → dimension, not dimension → dimension)
- [ ] Comment uses v3.0 structured format

### Pre-Deployment
- [ ] Schema validation script passes
- [ ] Date parameters use STRING type
- [ ] Required parameters before optional
- [ ] No `LIMIT parameter` (use WHERE with ROW_NUMBER)
- [ ] Comment includes all sections (PURPOSE, BEST FOR, RETURNS, etc.)
- [ ] NOTE section includes "DO NOT wrap in TABLE()"

### Post-Deployment
- [ ] TVF callable via `SELECT * FROM function_name(...)`
- [ ] Metric View shows as `METRIC_VIEW` type (not `VIEW`)
- [ ] Genie Space can discover and use the asset

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Unrecognized field "name"` | `name` in YAML | Remove `name` field |
| `UNRESOLVED_COLUMN` | Column doesn't exist | Check Gold YAML |
| `NOT_A_SCALAR_FUNCTION` | TVF wrapped in TABLE() | Add NOTE: DO NOT wrap |
| `INVALID_LIMIT_LIKE_EXPRESSION` | Parameter in LIMIT | Use ROW_NUMBER + WHERE |
| Values inflated 100x+ | Cartesian product | Single aggregation pass |
| `Parameter type DATE not supported` | DATE param type | Use STRING + CAST |

---

## Related Documents

- [Gold Layer Standards](12-gold-layer-standards.md)
- [Genie Space Standards](14-genie-space-standards.md)
- [Dashboard Standards](15-dashboard-standards.md)

---

## References

- [Metric Views YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [TVF SQL Reference](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-qry-select-tvf)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
