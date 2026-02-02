# Metric View Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-SL-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Analytics Engineering Team |
| **Status** | Approved |

---

## Executive Summary

Metric Views provide a semantic layer for natural language queries via Genie and AI/BI dashboards. This document defines the mandatory YAML structure for v1.1, critical limitations, and patterns for successful deployment.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| SL-01 | Metric Views use v1.1 YAML (no name field) | 🔴 Critical |
| SL-05 | No transitive joins in Metric Views | 🔴 Critical |
| SL-03 | Schema validation before writing YAML | 🔴 Critical |

---

## Critical v1.1 Limitations

### Fields NOT Supported in v1.1

| Field | Error | Status |
|-------|-------|--------|
| **`name`** | `Unrecognized field "name"` | ❌ NEVER include |
| `time_dimension` | `Unrecognized field` | ❌ Use regular dimension |
| `window_measures` | `Unrecognized field` | ❌ Pre-calculate in Gold |
| `join_type` | Not supported | ❌ Defaults to LEFT OUTER |

### Correct SQL Syntax

```sql
-- ✅ CORRECT: WITH METRICS LANGUAGE YAML
CREATE OR REPLACE VIEW catalog.schema.my_metric_view
WITH METRICS
LANGUAGE YAML
COMMENT 'Description...'
AS $$
version: '1.1'
source: catalog.schema.fact_table
dimensions:
  - name: dimension1
    expr: source.column1
$$;

-- ❌ WRONG: Regular view with TBLPROPERTIES
CREATE OR REPLACE VIEW catalog.schema.my_metric_view
TBLPROPERTIES ('metric_view_spec' = '...')
AS SELECT 1 as placeholder;  -- Creates VIEW not METRIC_VIEW!
```

---

## Rule SL-01: v1.1 YAML Structure

### Complete Template

```yaml
version: "1.1"  # Required, quoted string

# View-level comment (structured for Genie)
comment: >
  PURPOSE: [One-line description].
  
  BEST FOR: [Question 1] | [Question 2] | [Question 3]
  
  NOT FOR: [Redirect to correct asset]
  
  DIMENSIONS: [dim1], [dim2], [dim3]
  
  MEASURES: [measure1], [measure2], [measure3]
  
  SOURCE: [fact_table] ([domain])
  
  NOTE: [Critical caveats]

# Source table (fully qualified)
source: ${catalog}.${gold_schema}.fact_table_name

# Joins to dimension tables (optional)
joins:
  - name: dim_alias  # Alias for referencing in expressions
    source: ${catalog}.${gold_schema}.dim_table
    'on': source.fk_column = dim_alias.pk_column AND dim_alias.is_current = true

dimensions:
  # Source table columns use 'source.' prefix
  - name: transaction_date
    expr: source.transaction_date
    comment: Date of transaction
    display_name: Transaction Date
    synonyms:
      - date
      - order date
  
  # Joined table columns use join alias prefix
  - name: customer_name
    expr: dim_customer.customer_name
    comment: Customer full name
    display_name: Customer Name
    synonyms:
      - name
      - customer

measures:
  - name: total_revenue
    expr: SUM(source.revenue)
    comment: Total revenue in USD
    display_name: Total Revenue
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
      abbreviation: compact
    synonyms:
      - revenue
      - sales
```

---

## Rule SL-05: No Transitive Joins

### The Problem

Metric Views v1.1 only support direct joins from source to dimension. Chained joins fail.

```yaml
# ❌ WRONG: Transitive join (not supported)
joins:
  - name: dim_property
    source: catalog.schema.dim_property
    'on': source.property_id = dim_property.property_id
  
  - name: dim_destination
    source: catalog.schema.dim_destination
    # ERROR: Cannot reference dim_property!
    'on': dim_property.destination_id = dim_destination.destination_id
```

### Solutions

**Option 1: Use FK Directly**
```yaml
dimensions:
  - name: destination_id
    expr: dim_property.destination_id  # Use FK instead of joined name
```

**Option 2: Denormalize in Gold**
```python
# Add destination_id directly to fact table
fact_df = fact_df.join(dim_property, "property_id").select(
    fact_df["*"],
    dim_property["destination_id"]
)
```

**Option 3: Create Enriched View**
```sql
CREATE VIEW fact_enriched AS
SELECT f.*, d.destination_name
FROM fact_table f
JOIN dim_property p ON f.property_id = p.property_id
JOIN dim_destination d ON p.destination_id = d.destination_id;
```

---

## Rule SL-03: Schema Validation Before YAML

### Validation Checklist

Before writing ANY metric view YAML:

```markdown
## Schema Mapping: cost_analytics_metrics

### Source: fact_usage
Columns (from gold_layer_design/yaml/billing/fact_usage.yaml):
- workspace_id ✅ (join key)
- usage_date ✅ (dimension)
- list_cost ✅ (measure)
- dbus_consumed ✅ (measure)

### Joined: dim_workspace
Columns (from gold_layer_design/yaml/workspace/dim_workspace.yaml):
- workspace_id ✅ (join key)
- workspace_name ✅ (dimension)
- is_current ✅ (SCD2 filter)
- workspace_admin ⚠️ (NOT workspace_owner!)

### Join Validation:
- source.workspace_id = dim_workspace.workspace_id ✅
- dim_workspace.is_current = true ✅ (SCD2)
```

### Common Column Name Errors

| Assumed | Actual | Table |
|---------|--------|-------|
| `is_active` | `is_current` | SCD2 dimensions |
| `created_at` | `joined_at` | dim_host |
| `booking_count` | `COUNT(booking_id)` | Must aggregate |
| `workspace_owner` | `workspace_admin` | dim_workspace |

---

## Structured Comment Format (v3.0)

```yaml
comment: >
  PURPOSE: Comprehensive cost analytics for Databricks billing.
  
  BEST FOR: Total spend by workspace | Cost trend | SKU breakdown | Tag coverage
  
  NOT FOR: Real-time monitoring (use alerts) | Commit tracking (use commit_view)
  
  DIMENSIONS: usage_date, workspace_name, sku_name, owner, tag_team
  
  MEASURES: total_cost, total_dbus, cost_7d, cost_30d, tag_coverage_pct
  
  SOURCE: fact_usage (billing domain)
  
  JOINS: dim_workspace (workspace details), dim_sku (SKU details)
  
  NOTE: Costs are list prices. Actual billed amounts may differ.
```

---

## Format Options Reference

### Currency
```yaml
format:
  type: currency
  currency_code: USD
  decimal_places:
    type: exact
    places: 2
  abbreviation: compact  # 1.5M instead of 1,500,000
```

### Number
```yaml
format:
  type: number
  decimal_places:
    type: all  # or exact with places
  abbreviation: compact
```

### Percentage
```yaml
format:
  type: percentage
  decimal_places:
    type: exact
    places: 1  # Shows 45.3%
```

---

## Complete Example

```yaml
version: "1.1"

comment: >
  PURPOSE: Cost analytics for Databricks workspace billing analysis.
  
  BEST FOR: Total spend by workspace | Daily cost trends | SKU cost breakdown
  
  NOT FOR: Real-time alerts (use SQL alerts) | Commit tracking
  
  DIMENSIONS: usage_date, workspace_name, sku_name, is_serverless
  
  MEASURES: total_cost, total_dbus, avg_daily_cost, workspace_count
  
  SOURCE: fact_usage (billing domain)
  
  JOINS: dim_workspace, dim_sku
  
  NOTE: List prices shown. Actual costs may differ with commitments.

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
    comment: Databricks workspace name
    display_name: Workspace
    synonyms:
      - workspace
      - ws
  
  - name: sku_name
    expr: dim_sku.sku_name
    comment: SKU name for the billing item
    display_name: SKU
    synonyms:
      - sku
      - product
  
  - name: is_serverless
    expr: dim_sku.is_serverless
    comment: Whether this is serverless compute
    display_name: Is Serverless
    synonyms:
      - serverless

measures:
  - name: total_cost
    expr: SUM(source.list_cost)
    comment: Total list cost in USD
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
      - revenue
  
  - name: total_dbus
    expr: SUM(source.dbus_consumed)
    comment: Total DBUs consumed
    display_name: Total DBUs
    format:
      type: number
      abbreviation: compact
    synonyms:
      - dbus
      - compute
  
  - name: workspace_count
    expr: COUNT(DISTINCT source.workspace_id)
    comment: Number of unique workspaces
    display_name: Workspace Count
    format:
      type: number
    synonyms:
      - workspaces
      - ws count
```

---

## Python Deployment Script

```python
import yaml
from pathlib import Path


def deploy_metric_view(
    spark,
    catalog: str,
    schema: str,
    yaml_path: str
):
    """
    Deploy metric view from YAML file.
    
    Note: View name comes from filename, NOT from YAML content.
    """
    # Extract view name from filename (Rule SL-01)
    view_name = Path(yaml_path).stem
    fqn = f"{catalog}.{schema}.{view_name}"
    
    # Load YAML
    with open(yaml_path) as f:
        content = f.read()
    
    # Substitute variables
    content = content.replace("${catalog}", catalog)
    content = content.replace("${gold_schema}", schema)
    
    # Escape for SQL
    yaml_str = content.replace("'", "''")
    
    # Parse for comment extraction
    metric_view = yaml.safe_load(content)
    comment = metric_view.get('comment', '').replace("'", "''")
    
    # Drop existing (clean state)
    try:
        spark.sql(f"DROP VIEW IF EXISTS {fqn}")
        spark.sql(f"DROP TABLE IF EXISTS {fqn}")
    except:
        pass
    
    # Create metric view
    create_sql = f"""
    CREATE VIEW {fqn}
    WITH METRICS
    LANGUAGE YAML
    COMMENT '{comment}'
    AS $$
{content}
    $$
    """
    
    spark.sql(create_sql)
    print(f"✅ Created metric view: {fqn}")


def deploy_all_metric_views(spark, catalog: str, schema: str, yaml_dir: str):
    """Deploy all metric views from directory."""
    yaml_files = list(Path(yaml_dir).glob("*.yaml"))
    
    success = 0
    failed = []
    
    for yaml_file in yaml_files:
        try:
            deploy_metric_view(spark, catalog, schema, str(yaml_file))
            success += 1
        except Exception as e:
            failed.append((yaml_file.name, str(e)))
            print(f"❌ Failed: {yaml_file.name}: {e}")
    
    print(f"\nDeployed {success}/{len(yaml_files)} metric views")
    
    if failed:
        raise RuntimeError(f"Failed: {[f[0] for f in failed]}")
```

---

## Validation Checklist

### Pre-Development
- [ ] Schema mapping document created
- [ ] All source table columns verified
- [ ] All joined table columns verified
- [ ] No transitive joins planned
- [ ] SCD2 dimensions have is_current filter

### YAML Structure
- [ ] version: "1.1" (quoted string)
- [ ] NO `name` field (extracted from filename)
- [ ] NO `time_dimension` field
- [ ] NO `window_measures` field
- [ ] Structured comment format (v3.0)
- [ ] All dimensions have synonyms (3+)
- [ ] All measures have format specified

### Deployment
- [ ] Variable substitution working
- [ ] CREATE VIEW WITH METRICS syntax
- [ ] LANGUAGE YAML specified
- [ ] Verification query succeeds

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Unrecognized field "name"` | name field in YAML | Remove name, use filename |
| `UNRESOLVED_COLUMN` | Column doesn't exist | Check Gold YAML |
| `Missing required property 'source'` | Wrong join syntax | Use `source:` not `table:` |
| Transitive join error | Chained joins | Denormalize or use FK |
| Not a METRIC_VIEW | Wrong CREATE syntax | Use WITH METRICS LANGUAGE YAML |

---

## Related Documents

- [TVF Patterns](31-tvf-patterns.md)
- [Genie Space Patterns](32-genie-space-patterns.md)
- [Gold Layer Patterns](../data-pipelines/12-gold-layer-patterns.md)

---

## References

- [Metric Views SQL](https://docs.databricks.com/metric-views/create/sql)
- [Metric Views YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [Metric Views Joins](https://docs.databricks.com/metric-views/joins)
