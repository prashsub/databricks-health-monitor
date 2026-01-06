# Semantic Layer Rules for Claude Code

This file combines all semantic layer cursor rules for use by Claude Code.

---

## Table of Contents
1. [Table-Valued Functions (TVFs)](#table-valued-functions-tvfs)
2. [Genie Space Patterns](#genie-space-patterns)
3. [Metric Views](#metric-views)

---

## Table-Valued Functions (TVFs)

### Schema-First Approach

**RULE #0: Always consult YAML schema definitions before writing any TVF SQL**

```bash
# Check Gold layer YAML definition
grep "^- name:" gold_layer_design/yaml/{domain}/{table}.yaml
```

### Critical SQL Requirements

#### 1. STRING for Date Parameters

```sql
-- ✅ CORRECT: STRING parameters
CREATE OR REPLACE FUNCTION get_sales_by_date_range(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
...
WHERE transaction_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)

-- ❌ WRONG: DATE type parameters
CREATE FUNCTION get_sales(start_date DATE)  -- Will fail!
```

#### 2. Parameters with DEFAULT Must Come Last

```sql
-- ✅ CORRECT: Required first, optional last
CREATE FUNCTION get_top_stores(
  start_date STRING,              -- Required
  end_date STRING,                -- Required
  top_n INT DEFAULT 10            -- Optional (with DEFAULT)
)

-- ❌ WRONG: DEFAULT in the middle
CREATE FUNCTION get_top_stores(
  top_n INT DEFAULT 10,           -- Wrong position!
  start_date STRING,
  end_date STRING
)
```

#### 3. LIMIT Cannot Use Parameters

```sql
-- ✅ CORRECT: Use WHERE with ROW_NUMBER
RETURN
  WITH store_metrics AS (
    SELECT ... FROM ...
  ),
  ranked_stores AS (
    SELECT ...,
      ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank
    FROM store_metrics
  )
  SELECT * FROM ranked_stores
  WHERE rank <= top_n  -- ✅ Parameter in WHERE
  ORDER BY rank;

-- ❌ WRONG: Parameter in LIMIT
SELECT * FROM ranked_stores
LIMIT top_n;  -- Will fail!
```

### Standardized TVF Comment Format

```sql
COMMENT '
• PURPOSE: [One-line description of what the TVF does]
• BEST FOR: [Example questions separated by |]
• NOT FOR: [What to avoid - redirect to correct TVF] (optional)
• RETURNS: [PRE-AGGREGATED rows or Individual rows] (exact column list)
• PARAMS: [Parameter names with defaults]
• SYNTAX: SELECT * FROM tvf_name(''param1'', ''param2'')
• NOTE: [Important caveats - DO NOT wrap in TABLE(), etc.] (optional)
'
```

**Example:**

```sql
CREATE OR REPLACE FUNCTION get_top_performing_stores(
  start_date STRING COMMENT 'Start date (YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of stores to return'
)
RETURNS TABLE (
  store_number STRING,
  store_name STRING,
  total_revenue DECIMAL(18,2),
  transaction_count BIGINT,
  avg_transaction_value DECIMAL(18,2),
  rank BIGINT
)
COMMENT '
• PURPOSE: Returns top-performing stores by revenue within a date range
• BEST FOR: "Top 10 stores this month" | "Best performing locations in Q4" | "Store revenue rankings"
• RETURNS: PRE-AGGREGATED rows (store_number, store_name, total_revenue, transaction_count, avg_transaction_value, rank)
• PARAMS: start_date (required), end_date (required), top_n (default: 10)
• SYNTAX: SELECT * FROM get_top_performing_stores(''2024-01-01'', ''2024-12-31'', 20)
• NOTE: DO NOT wrap in TABLE(). Results already aggregated at store level.
'
RETURN
  WITH store_metrics AS (
    SELECT 
      f.store_number,
      d.store_name,
      SUM(f.net_revenue) as total_revenue,
      SUM(f.transaction_count) as transaction_count,
      SUM(f.net_revenue) / NULLIF(SUM(f.transaction_count), 0) as avg_transaction_value
    FROM catalog.schema.fact_sales_daily f
    JOIN catalog.schema.dim_store d ON f.store_number = d.store_number AND d.is_current = true
    WHERE f.transaction_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY f.store_number, d.store_name
  ),
  ranked_stores AS (
    SELECT *,
      ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank
    FROM store_metrics
  )
  SELECT * FROM ranked_stores
  WHERE rank <= top_n
  ORDER BY rank;
```

### SCD Type 2 Dimension Handling

```sql
-- Always filter for current version
JOIN catalog.schema.dim_store d 
  ON f.store_number = d.store_number 
  AND d.is_current = true  -- ✅ Current version only
```

### Null Safety

```sql
-- Always use COALESCE for potentially null values
SUM(COALESCE(f.net_revenue, 0)) as total_revenue

-- Use NULLIF to prevent division by zero
SUM(f.net_revenue) / NULLIF(SUM(f.transaction_count), 0) as avg_transaction_value
```

### Preventing Cartesian Product Bugs

```sql
-- ✅ CORRECT: Single aggregation pass
SELECT
  DATE_TRUNC(time_grain, f.date) AS period_start,
  SUM(f.revenue) as total_revenue,
  COUNT(*) as transaction_count
FROM fact_table f
WHERE f.date BETWEEN start_date AND end_date
GROUP BY DATE_TRUNC(time_grain, f.date)

-- ❌ WRONG: Self-join causing cartesian product
WITH totals AS (SELECT SUM(revenue) as total FROM fact_table),
     counts AS (SELECT COUNT(*) as cnt FROM fact_table)
SELECT t.total, c.cnt FROM totals t, counts c  -- Cartesian!
```

### Validation Checklist

- [ ] YAML schema validated for all referenced columns
- [ ] Date parameters are STRING type
- [ ] Parameters with DEFAULT come last
- [ ] No parameters in LIMIT clause (use WHERE with rank)
- [ ] SCD2 dimensions filtered with `is_current = true`
- [ ] COALESCE used for null-safe aggregations
- [ ] NULLIF used for division operations
- [ ] TVF comment follows standardized format
- [ ] No cartesian products in CTEs

---

## Genie Space Patterns

### Required 7-Section Document

**Every Genie Space setup MUST produce ALL 7 sections:**

| Section | What to Provide |
|---------|-----------------|
| A. Space Name | `{Project} {Domain} Analytics Space` |
| B. Space Description | 2-3 sentence purpose |
| C. Sample Questions | 10-15 user-facing questions |
| D. Data Assets | ALL tables & metric views |
| E. General Instructions | **≤20 LINES** |
| F. TVFs | ALL functions with signatures |
| G. Benchmark Questions | 10-15 with **EXACT SQL** |

### A. Space Name

```
{Project Name} {Domain} Analytics Space

Example: Databricks Health Monitor Cost Analytics Space
```

### B. Space Description

```
Natural language analytics interface for {domain} analysis. 
Query {data assets} using conversational questions. 
Supports time-based filtering, dimensional analysis, and KPI calculations.
```

### C. Sample Questions (Grouped by Domain)

```markdown
### Cost Analysis
- "What is our total spend this month?"
- "Show cost breakdown by workspace"
- "Which SKUs are most expensive?"

### Performance
- "What's our job success rate?"
- "Show slowest running jobs"
- "Failed jobs in the last 24 hours"
```

### D. Data Assets Table

```markdown
| Asset Type | Name | Purpose |
|------------|------|---------|
| Metric View | cost_analytics | Cost aggregations and trends |
| Metric View | job_performance | Job success/failure metrics |
| TVF | get_cost_summary | Parameterized cost drill-down |
| TVF | get_failed_jobs | Recent failed jobs listing |
| Table | dim_workspace | Workspace attributes |
```

### E. General Instructions (≤20 LINES)

**⚠️ CONSTRAINT: EXACTLY 20 LINES OR LESS**

```markdown
1. Use MEASURE() for metric view aggregations: `SELECT MEASURE(total_cost) FROM cost_analytics`
2. Always use full 3-part names: `${catalog}.${schema}.object_name`
3. For rankings/top-N: use TVFs like `get_top_workspaces('2024-01-01', '2024-12-31', 10)`
4. Date parameters are strings: 'YYYY-MM-DD' format
5. For cost questions → cost_analytics metric view or get_cost_summary TVF
6. For job questions → job_performance metric view or get_failed_jobs TVF
7. SCD2 dimensions: always filter `is_current = true`
8. Null handling: use COALESCE for sums, NULLIF for division
9. TVFs return pre-aggregated data - don't re-aggregate
10. Time filters: use BETWEEN with CAST for date comparisons
```

### F. TVFs with Signatures

```markdown
### get_cost_summary(start_date, end_date, group_by)
**Purpose:** Flexible cost aggregation by dimension
**Parameters:**
- start_date STRING (required): Start date 'YYYY-MM-DD'
- end_date STRING (required): End date 'YYYY-MM-DD'  
- group_by STRING DEFAULT 'workspace': Grouping dimension

**Returns:** group_value, total_cost, dbu_count, cost_per_dbu

**Example:** `SELECT * FROM get_cost_summary('2024-01-01', '2024-03-31', 'sku')`
```

### G. Benchmark Questions with SQL

```markdown
### Question: "What is total cost by workspace this month?"

**SQL:**
```sql
SELECT 
  workspace_name,
  MEASURE(total_cost) as total_cost,
  MEASURE(total_dbus) as total_dbus
FROM ${catalog}.${gold_schema}.cost_analytics
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
GROUP BY workspace_name
ORDER BY total_cost DESC
```

**Expected Result:** Table with workspace_name, total_cost, total_dbus columns
```

### Critical Rules

#### MEASURE() Uses Column Names

```sql
-- ✅ CORRECT: Use actual column names
SELECT 
  MEASURE(total_revenue) as revenue,
  MEASURE(booking_count) as bookings
FROM ${catalog}.${gold_schema}.revenue_analytics_metrics;

-- ❌ WRONG: Using display names
SELECT MEASURE(`Total Revenue`)  -- Wrong!
```

#### Full UC 3-Part Namespace

```sql
-- Always use: ${catalog}.${gold_schema}.object_name
SELECT * FROM ${catalog}.${gold_schema}.fact_booking_daily;
SELECT * FROM ${catalog}.${gold_schema}.get_revenue_by_period('2024-01-01', '2024-12-31', 'week');
```

#### Routing Logic

```markdown
| Question Type | Route To |
|--------------|----------|
| Aggregations, trends | Metric Views |
| Rankings, top-N | TVFs |
| Specific entity lookup | Tables + TVFs |
| Time-series analysis | Metric Views |
```

---

## Metric Views

### v1.1 Unsupported Fields

**These will cause errors:**
- `name` - Name is in CREATE VIEW statement
- `time_dimension` - Use regular dimension
- `window_measures` - Pre-calculate in Gold layer

### Correct SQL Syntax

```sql
CREATE OR REPLACE VIEW ${catalog}.${schema}.my_metrics
WITH METRICS
LANGUAGE YAML
COMMENT 'Description...'
AS $$
version: '1.1'
comment: 'Detailed description'
source: ${catalog}.${schema}.fact_table

dimensions:
  - name: store_number
    expr: source.store_number
    comment: Store identifier
    display_name: Store Number
    synonyms:
      - store id
      - location

measures:
  - name: total_revenue
    expr: SUM(source.net_revenue)
    comment: Total net revenue
    display_name: Total Revenue
    format:
      type: currency
      currency_code: USD
    synonyms:
      - revenue
      - sales
$$
```

### Mandatory Schema Validation

**Before writing ANY metric view YAML:**

1. Verify source table columns exist
2. Verify all joined table columns exist
3. Validate join keys match
4. Check SCD2 tables have `is_current`

### Joins Pattern

```yaml
joins:
  - name: dim_store
    source: ${catalog}.${schema}.dim_store
    'on': source.store_number = dim_store.store_number AND dim_store.is_current = true
```

**Rules:**
- Each join must be direct: `source.fk = dim.pk`
- NOT transitive: `dim1.fk = dim2.pk` ❌
- Include SCD2 filter: `is_current = true`

### Source Table Selection

| Metric Type | Source Table |
|-------------|--------------|
| Revenue, Bookings | FACT table |
| Property counts | DIMENSION table |
| Host attributes | DIMENSION table |

### Standardized Comment Format

```yaml
comment: >
  PURPOSE: Comprehensive cost analytics for billing analysis.
  
  BEST FOR: Total spend by workspace | Cost trend over time | SKU breakdown
  
  NOT FOR: Commit tracking (use commit_tracking) | Real-time alerts (use TVF)
  
  DIMENSIONS: usage_date, workspace_name, sku_name, owner, is_serverless
  
  MEASURES: total_cost, total_dbus, cost_7d, serverless_percentage
  
  SOURCE: fact_usage (billing domain)
  
  JOINS: dim_workspace (workspace details), dim_sku (SKU details)
  
  NOTE: Cost values are list prices. Actual billed amounts may differ.
```

### Validation Checklist

- [ ] v1.1 version specified
- [ ] NO `name` field in YAML
- [ ] NO `time_dimension` or `window_measures`
- [ ] All dimension/measure columns verified against schema
- [ ] Joins are direct (not transitive)
- [ ] SCD2 dimensions include `is_current = true`
- [ ] Comment follows structured format
- [ ] `source.` prefix used for main table columns




