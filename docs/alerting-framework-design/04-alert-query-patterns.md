# 04 - Alert Query Patterns

## Overview

Alert queries are SQL statements that determine when an alert should trigger. This document covers best practices for writing effective, maintainable, and performant alert queries.

## Query Template Syntax

### Placeholder System

Alert queries support placeholders that are replaced at runtime:

| Placeholder | Replaced With | Example |
|-------------|---------------|---------|
| `${catalog}` | Target catalog name | `my_catalog` |
| `${gold_schema}` | Target schema name | `gold` |

### Example Template

```sql
SELECT 
    SUM(list_cost) as daily_cost,
    'Daily cost $' || ROUND(SUM(list_cost), 2) || ' exceeds threshold' as alert_message
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date = CURRENT_DATE() - 1
HAVING SUM(list_cost) > 5000
```

**After Rendering:**

```sql
SELECT 
    SUM(list_cost) as daily_cost,
    'Daily cost $' || ROUND(SUM(list_cost), 2) || ' exceeds threshold' as alert_message
FROM my_catalog.gold.fact_usage
WHERE usage_date = CURRENT_DATE() - 1
HAVING SUM(list_cost) > 5000
```

## Query Requirements

### Required Elements

| Element | Purpose | Example |
|---------|---------|---------|
| **threshold_column** | Column to evaluate against threshold | `daily_cost`, `failure_rate` |
| **Filtering logic** | HAVING clause to limit results | `HAVING SUM(cost) > 5000` |

### Recommended Elements

| Element | Purpose | Example |
|---------|---------|---------|
| **alert_message** | Human-readable notification content | `'Cost exceeded: $' \|\| ROUND(cost, 2)` |
| **context columns** | Additional info for debugging | `workspace_name`, `job_name` |

## Query Patterns by Type

### Pattern 1: Simple Threshold

**Use Case**: Alert when a metric exceeds a fixed value.

```sql
SELECT 
    SUM(list_cost) as daily_cost,
    'Daily cost $' || ROUND(SUM(list_cost), 2) || ' exceeds $5000 threshold' as alert_message
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date = CURRENT_DATE() - 1
HAVING SUM(list_cost) > 5000
```

**Key Points:**
- `daily_cost` is the threshold_column
- HAVING filters to only return rows when condition is met
- No rows returned = no alert triggered (if `empty_result_state = OK`)

### Pattern 2: Percentage-Based

**Use Case**: Alert when a rate exceeds a percentage threshold.

```sql
SELECT 
    ROUND(
        SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ) as failure_rate,
    'Job failure rate ' || 
        ROUND(
            SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
            NULLIF(COUNT(*), 0), 
            1
        ) || '% exceeds 10% threshold' as alert_message
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
HAVING SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / 
       NULLIF(COUNT(*), 0) > 10
```

**Key Points:**
- Use `NULLIF(denominator, 0)` to prevent division by zero
- Calculate percentage inline in HAVING
- Round for readability

### Pattern 3: Week-over-Week Comparison

**Use Case**: Alert when metric changes significantly from previous period.

```sql
WITH current_week AS (
    SELECT SUM(list_cost) as weekly_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_TRUNC('week', CURRENT_DATE())
),
previous_week AS (
    SELECT SUM(list_cost) as weekly_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= DATE_TRUNC('week', CURRENT_DATE() - INTERVAL 7 DAYS)
      AND usage_date < DATE_TRUNC('week', CURRENT_DATE())
)
SELECT 
    ROUND((c.weekly_cost - p.weekly_cost) / NULLIF(p.weekly_cost, 0) * 100, 1) as pct_change,
    'Weekly cost increased by ' || 
        ROUND((c.weekly_cost - p.weekly_cost) / NULLIF(p.weekly_cost, 0) * 100, 1) || 
        '% (Current: $' || ROUND(c.weekly_cost, 0) || 
        ', Previous: $' || ROUND(p.weekly_cost, 0) || ')' as alert_message
FROM current_week c, previous_week p
WHERE c.weekly_cost > p.weekly_cost * 1.25  -- >25% increase
```

**Key Points:**
- CTEs for readability
- Compare to previous period
- Include both values in message

### Pattern 4: Count-Based

**Use Case**: Alert when event count exceeds threshold.

```sql
SELECT 
    COUNT(*) as failed_jobs,
    'CRITICAL: ' || COUNT(*) || ' jobs failed in last 24 hours' as alert_message
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL 24 HOURS
  AND result_state = 'FAILED'
HAVING COUNT(*) > 0
```

**Key Points:**
- Simple COUNT with HAVING
- Filter to specific conditions in WHERE
- HAVING > 0 ensures alert only on failures

### Pattern 5: Top-N with Details

**Use Case**: Alert with breakdown of worst offenders.

```sql
WITH expensive_jobs AS (
    SELECT 
        job_name,
        SUM(total_cost) as job_cost,
        ROW_NUMBER() OVER (ORDER BY SUM(total_cost) DESC) as rn
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline
    WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY job_name
)
SELECT 
    SUM(job_cost) as total_cost,
    'Top 3 expensive jobs: ' || 
        CONCAT_WS(', ', COLLECT_LIST(job_name || ': $' || ROUND(job_cost, 0))) as alert_message
FROM expensive_jobs
WHERE rn <= 3
HAVING SUM(job_cost) > 10000
```

**Key Points:**
- Use window functions for ranking
- Aggregate details into message
- COLLECT_LIST for combining rows

### Pattern 6: Data Freshness

**Use Case**: Alert when data is stale.

```sql
SELECT 
    TIMESTAMPDIFF(HOUR, MAX(processed_at), CURRENT_TIMESTAMP()) as hours_since_update,
    'Data in fact_usage is ' || 
        TIMESTAMPDIFF(HOUR, MAX(processed_at), CURRENT_TIMESTAMP()) || 
        ' hours old (threshold: 24 hours)' as alert_message
FROM ${catalog}.${gold_schema}.fact_usage
HAVING TIMESTAMPDIFF(HOUR, MAX(processed_at), CURRENT_TIMESTAMP()) > 24
```

**Key Points:**
- Use TIMESTAMPDIFF for age calculation
- Check against max timestamp
- Clear threshold in message

### Pattern 7: Info/Summary (Always Triggers)

**Use Case**: Regular summary alerts (daily/weekly reports).

```sql
SELECT 
    SUM(booking_count) as total_bookings,
    SUM(total_booking_value) as total_revenue,
    1 as always_trigger,  -- Forces trigger for INFO alerts
    'Daily Summary: ' || SUM(booking_count) || ' bookings, $' || 
        ROUND(SUM(total_booking_value), 2) || ' revenue' as alert_message
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date = CURRENT_DATE() - 1
```

**Key Points:**
- Use `1 as always_trigger` with threshold > 0 to always fire
- No HAVING clause (always returns a row)
- Set `threshold_column = 'always_trigger'` and `threshold_value_double = 0`

### Pattern 8: Coverage/Percentage Below

**Use Case**: Alert when coverage drops below threshold.

```sql
WITH tag_analysis AS (
    SELECT
        CASE
            WHEN is_tagged = TRUE THEN 'TAGGED'
            ELSE 'UNTAGGED'
        END AS tag_status,
        SUM(list_cost) AS cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    GROUP BY is_tagged
)
SELECT
    ROUND(
        SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / 
        NULLIF(SUM(cost), 0) * 100, 
        1
    ) AS tag_coverage_pct,
    'Tag coverage ' || 
        ROUND(
            SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / 
            NULLIF(SUM(cost), 0) * 100, 
            1
        ) || '% is below 80% threshold' AS alert_message
FROM tag_analysis
HAVING SUM(CASE WHEN tag_status = 'TAGGED' THEN cost ELSE 0 END) / 
       NULLIF(SUM(cost), 0) * 100 < 80
```

**Key Points:**
- Use `<` operator for "below threshold" alerts
- NULLIF to handle division by zero
- Clear message about what's expected

## Common Mistakes

### ❌ Missing HAVING Clause

```sql
-- BAD: Always returns a row (always alerts)
SELECT SUM(cost) as daily_cost
FROM fact_usage
WHERE usage_date = CURRENT_DATE()
```

```sql
-- GOOD: Only returns when threshold exceeded
SELECT SUM(cost) as daily_cost
FROM fact_usage
WHERE usage_date = CURRENT_DATE()
HAVING SUM(cost) > 5000
```

### ❌ Division by Zero

```sql
-- BAD: Will error if denominator is 0
SELECT failed_count / total_count * 100 as failure_rate
```

```sql
-- GOOD: Safe division
SELECT failed_count / NULLIF(total_count, 0) * 100 as failure_rate
```

### ❌ Missing Threshold Column

```sql
-- BAD: Uses wrong column name
SELECT SUM(cost) as total_cost  -- But threshold_column = 'daily_cost'
```

```sql
-- GOOD: Column name matches configuration
SELECT SUM(cost) as daily_cost  -- threshold_column = 'daily_cost'
```

### ❌ Hardcoded Table Names

```sql
-- BAD: Won't work in different environments
SELECT * FROM production.gold.fact_usage
```

```sql
-- GOOD: Uses placeholders
SELECT * FROM ${catalog}.${gold_schema}.fact_usage
```

### ❌ SQL Escaping Issues (LIKE Patterns)

```sql
-- BAD: When using SQL INSERT, quotes are stripped
... WHERE sku_name LIKE '%ALL_PURPOSE%'
-- Becomes: WHERE sku_name LIKE %ALL_PURPOSE%  (invalid!)
```

```python
# GOOD: Use DataFrame insertion (see Pattern in 11-implementation-guide)
df = spark.createDataFrame([{
    "alert_query_template": "SELECT * FROM t WHERE col LIKE '%pattern%'"
}], schema=ALERT_CONFIG_SCHEMA)
df.write.mode("append").saveAsTable("alert_configurations")
```

## Query Performance Best Practices

### 1. Use Appropriate Time Filters

```sql
-- GOOD: Specific time range
WHERE usage_date = CURRENT_DATE() - 1

-- AVOID: Unbounded scans
WHERE usage_date < CURRENT_DATE()  -- Scans entire history
```

### 2. Leverage Partitioning

```sql
-- GOOD: Filter on partition column first
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND workspace_name = 'production'

-- LESS EFFICIENT: Non-partition column first
WHERE workspace_name = 'production'
  AND usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
```

### 3. Limit Result Size

```sql
-- GOOD: HAVING ensures small result set
SELECT SUM(cost) as daily_cost
FROM fact_usage
HAVING SUM(cost) > threshold

-- AVOID: Large result sets
SELECT * FROM fact_usage  -- Returns millions of rows
```

### 4. Use Aggregations Efficiently

```sql
-- GOOD: Aggregate in a single pass
SELECT 
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
    COUNT(*) as total
FROM jobs

-- LESS EFFICIENT: Multiple subqueries
SELECT 
    (SELECT COUNT(*) FROM jobs WHERE status = 'FAILED') as failed,
    (SELECT COUNT(*) FROM jobs) as total
```

## Query Validation

### Pre-Deployment Validation

All queries are validated using EXPLAIN before deployment:

```python
def validate_query(spark, query):
    try:
        spark.sql(f"EXPLAIN {query}")
        return (True, None)
    except Exception as e:
        return (False, str(e))
```

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `UNRESOLVED_COLUMN` | Column doesn't exist | Check column name in table schema |
| `TABLE_OR_VIEW_NOT_FOUND` | Table doesn't exist | Verify table name and schema |
| `PARSE_SYNTAX_ERROR` | SQL syntax error | Test query in SQL editor first |

## Testing Queries

### Before Adding to Configuration

1. **Test in SQL Editor**: Run query directly with actual values
2. **Verify Threshold Column**: Ensure column name matches configuration
3. **Check Return Format**: Confirm threshold_column is returned
4. **Test Edge Cases**: What happens when no data matches?

### Test Script

```sql
-- Replace placeholders manually for testing
WITH test_query AS (
    SELECT 
        SUM(list_cost) as daily_cost,
        'Test message' as alert_message
    FROM my_catalog.gold.fact_usage
    WHERE usage_date = CURRENT_DATE() - 1
    HAVING SUM(list_cost) > 5000
)
SELECT 
    daily_cost,
    alert_message,
    CASE WHEN daily_cost > 5000 THEN 'WOULD_TRIGGER' ELSE 'OK' END as status
FROM test_query;
```

## Next Steps

- **[05-Databricks SDK Integration](05-databricks-sdk-integration.md)**: How queries become alerts
- **[07-Query Validation](07-query-validation.md)**: Automated validation process
- **[10-Alert Templates](10-alert-templates.md)**: Pre-built query templates


