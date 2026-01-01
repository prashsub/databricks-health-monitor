# Appendix B - Metric View YAML Patterns

## Standard YAML Template

```yaml
version: "1.1"

comment: >
  PURPOSE: One-line description of what this view provides.
  
  BEST FOR: Question 1 | Question 2 | Question 3 | Question 4
  
  NOT FOR: What this view shouldn't be used for (use alternative instead)
  
  DIMENSIONS: dim1, dim2, dim3, dim4, dim5
  
  MEASURES: measure1, measure2, measure3, measure4, measure5
  
  SOURCE: source_table (domain)
  
  JOINS: dim_table1 (description), dim_table2 (description)
  
  NOTE: Critical caveats or limitations

source: ${catalog}.${gold_schema}.fact_table

joins:
  - name: dim_table
    source: ${catalog}.${gold_schema}.dim_table
    'on': source.fk_column = dim_table.pk_column AND dim_table.is_current = true

dimensions:
  - name: dimension_name
    expr: source.column_name
    comment: Business description for LLM understanding
    display_name: User-Friendly Name
    synonyms:
      - alternative name 1
      - alternative name 2
      - alternative name 3

measures:
  - name: measure_name
    expr: SUM(source.numeric_column)
    comment: Business description and calculation logic
    display_name: User-Friendly Name
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
      - total
```

## Dimension Patterns

### Simple Source Column

```yaml
dimensions:
  - name: usage_date
    expr: source.usage_date
    comment: Date of usage record for time-based analysis
    display_name: Usage Date
    synonyms:
      - date
      - billing date
      - transaction date
```

### Joined Dimension Column

```yaml
dimensions:
  - name: workspace_name
    expr: dim_workspace.workspace_name
    comment: Human-readable workspace name for organizational analysis
    display_name: Workspace Name
    synonyms:
      - workspace
      - environment
```

### Calculated Dimension

```yaml
dimensions:
  - name: entity_type
    expr: >
      CONCAT_WS(' ',
        CASE WHEN source.is_serverless THEN 'SERVERLESS' ELSE 'CLASSIC' END,
        CASE
          WHEN source.billing_origin_product = 'JOBS' THEN 'JOB'
          WHEN source.billing_origin_product = 'SQL' THEN 'WAREHOUSE'
          ELSE source.billing_origin_product
        END)
    comment: Combined serverless/classic indicator with product type
    display_name: Entity Type
    synonyms:
      - compute type
      - resource type
```

### Categorical Dimension with CASE

```yaml
dimensions:
  - name: freshness_status
    expr: >
      CASE 
        WHEN TIMESTAMPDIFF(HOUR, source.last_altered, CURRENT_TIMESTAMP()) <= 24 THEN 'FRESH'
        WHEN TIMESTAMPDIFF(HOUR, source.last_altered, CURRENT_TIMESTAMP()) <= 48 THEN 'WARNING'
        ELSE 'STALE'
      END
    comment: Table freshness classification based on update recency
    display_name: Freshness Status
    synonyms:
      - status
      - data freshness
```

### Tag Extraction from MAP

```yaml
dimensions:
  - name: team_tag
    expr: COALESCE(source.custom_tags['team'], 'Unassigned')
    comment: Team tag value for cost attribution and chargeback
    display_name: Team Tag
    synonyms:
      - team
      - department
```

### Boolean Dimension

```yaml
dimensions:
  - name: is_serverless
    expr: source.is_serverless
    comment: Flag indicating serverless vs classic compute
    display_name: Is Serverless
    synonyms:
      - serverless
      - serverless flag
```

## Measure Patterns

### Simple SUM

```yaml
measures:
  - name: total_cost
    expr: SUM(source.list_cost)
    comment: Total USD cost across all usage records
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
      - total spend
```

### COUNT

```yaml
measures:
  - name: total_queries
    expr: COUNT(*)
    comment: Total number of queries executed
    display_name: Total Queries
    format:
      type: number
      abbreviation: compact
    synonyms:
      - queries
      - query count
```

### AVG with NULLIF Safety

```yaml
measures:
  - name: avg_duration_seconds
    expr: AVG(source.duration_ms) / 1000.0
    comment: Average query duration in seconds
    display_name: Avg Duration (seconds)
    format:
      type: number
      decimal_places:
        type: exact
        places: 2
    synonyms:
      - average duration
      - avg runtime
```

### Percentage with NULLIF

```yaml
measures:
  - name: success_rate
    expr: (SUM(CASE WHEN source.result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0) / NULLIF(COUNT(*), 0)
    comment: Percentage of successful job runs
    display_name: Success Rate
    format:
      type: percentage
      decimal_places:
        type: exact
        places: 1
    synonyms:
      - success percentage
      - success pct
```

### Conditional SUM (BIGINT flag)

```yaml
measures:
  - name: anomaly_count
    expr: SUM(CASE WHEN source.is_anomaly = 1 THEN 1 ELSE 0 END)
    comment: Count of records flagged as anomalies
    display_name: Anomaly Count
    format:
      type: number
    synonyms:
      - anomalies
      - flagged records
```

### Week-over-Week Growth

```yaml
measures:
  - name: week_over_week_growth_pct
    expr: >
      (SUM(CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -7) THEN source.list_cost ELSE 0 END) -
       SUM(CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -14) 
           AND source.usage_date < DATE_ADD(CURRENT_DATE(), -7) THEN source.list_cost ELSE 0 END)) * 100.0 /
      NULLIF(SUM(CASE WHEN source.usage_date >= DATE_ADD(CURRENT_DATE(), -14) 
          AND source.usage_date < DATE_ADD(CURRENT_DATE(), -7) THEN source.list_cost ELSE 0 END), 0)
    comment: Week-over-week cost growth percentage
    display_name: WoW Growth %
    format:
      type: percentage
      decimal_places:
        type: exact
        places: 1
    synonyms:
      - wow growth
      - weekly growth
```

### Month-to-Date

```yaml
measures:
  - name: mtd_cost
    expr: SUM(CASE WHEN source.usage_date >= DATE_TRUNC('month', CURRENT_DATE()) THEN source.list_cost ELSE 0 END)
    comment: Month-to-date cost accumulation
    display_name: MTD Cost
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
    synonyms:
      - month to date
      - mtd spend
```

### Projected Monthly Cost

```yaml
measures:
  - name: projected_monthly_cost
    expr: >
      (SUM(CASE WHEN source.usage_date >= DATE_TRUNC('month', CURRENT_DATE()) THEN source.list_cost ELSE 0 END) 
       / NULLIF(DATEDIFF(CURRENT_DATE(), DATE_TRUNC('month', CURRENT_DATE())) + 1, 0))
      * DAY(LAST_DAY(CURRENT_DATE()))
    comment: Projected month-end cost based on current MTD burn rate
    display_name: Projected Monthly Cost
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
    synonyms:
      - projected cost
      - forecast
```

## Join Patterns

### SCD2 Current Record Join

```yaml
joins:
  - name: dim_workspace
    source: ${catalog}.${gold_schema}.dim_workspace
    'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
```

### SCD2 with delete_time Pattern

```yaml
joins:
  - name: dim_job
    source: ${catalog}.${gold_schema}.dim_job
    'on': source.job_id = dim_job.job_id AND dim_job.delete_time IS NULL
```

### Multiple Joins

```yaml
joins:
  - name: dim_workspace
    source: ${catalog}.${gold_schema}.dim_workspace
    'on': source.workspace_id = dim_workspace.workspace_id AND dim_workspace.is_current = true
  
  - name: dim_warehouse
    source: ${catalog}.${gold_schema}.dim_warehouse
    'on': source.warehouse_id = dim_warehouse.warehouse_id AND dim_warehouse.delete_time IS NULL
```

## Format Patterns

### Currency

```yaml
format:
  type: currency
  currency_code: USD
  decimal_places:
    type: exact
    places: 2
  hide_group_separator: false
  abbreviation: compact
```

### Percentage

```yaml
format:
  type: percentage
  decimal_places:
    type: exact
    places: 1
```

### Number with Compact Display

```yaml
format:
  type: number
  decimal_places:
    type: all
  hide_group_separator: false
  abbreviation: compact
```

### Number with Fixed Decimals

```yaml
format:
  type: number
  decimal_places:
    type: exact
    places: 2
```

## Common Mistakes to Avoid

### ❌ Including `name` field (v1.1 doesn't support)

```yaml
# WRONG
version: "1.1"
name: my_metric_view  # ❌ Will cause "Unrecognized field" error

# CORRECT
version: "1.1"
# Name comes from CREATE VIEW statement, not YAML
```

### ❌ Using table name instead of `source.`

```yaml
# WRONG
expr: fact_usage.list_cost  # ❌

# CORRECT
expr: source.list_cost  # ✅
```

### ❌ Boolean expression on BIGINT column

```yaml
# WRONG - is_anomaly is BIGINT
expr: SUM(CASE WHEN source.is_anomaly THEN 1 ELSE 0 END)  # ❌

# CORRECT
expr: SUM(CASE WHEN source.is_anomaly = 1 THEN 1 ELSE 0 END)  # ✅
```

### ❌ Transitive joins

```yaml
# WRONG - Cannot join dim1 to dim2
joins:
  - name: dim_property
    source: catalog.schema.dim_property
    'on': source.property_id = dim_property.property_id
  - name: dim_destination
    source: catalog.schema.dim_destination
    'on': dim_property.destination_id = dim_destination.destination_id  # ❌

# Solution: Use FK directly or denormalize fact table
```

### ❌ Division without NULLIF

```yaml
# WRONG - May cause division by zero
expr: SUM(success) / COUNT(*)  # ❌

# CORRECT
expr: SUM(success) / NULLIF(COUNT(*), 0)  # ✅
```

