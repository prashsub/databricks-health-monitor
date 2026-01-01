# 07 - Query Validation

## Overview

Query validation is a **critical pre-deployment step** that catches SQL errors before alerts are deployed to Databricks. This prevents deployment failures and ensures all alerts are functional.

## Why Pre-Deployment Validation?

| Without Validation | With Validation |
|--------------------|-----------------|
| Deploy alert → Fails at runtime | Validate → Fix → Deploy → Works |
| Silent failures (alert never fires) | Explicit errors before deployment |
| Debug in production | Debug in development |
| Wasted deployment iterations | Single successful deployment |

## Validation Approach

### EXPLAIN-Based Validation

The framework uses `EXPLAIN` to validate queries without executing them:

```python
def validate_query(spark: SparkSession, query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SQL query using EXPLAIN.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        spark.sql(f"EXPLAIN {query}")
        return (True, None)
    except Exception as e:
        return (False, str(e))
```

**Why EXPLAIN?**
- ✅ Validates syntax without execution
- ✅ Checks column references
- ✅ Verifies table existence
- ✅ Catches permission issues
- ✅ Fast (no data processing)

## Validation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     QUERY VALIDATION FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────┐
  │ alert_configurations │
  │ (is_enabled = TRUE)  │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ FOR EACH alert:                                                   │
  │                                                                   │
  │  1. Render Template                                               │
  │     ┌────────────────────────────────────────────────────────┐    │
  │     │ ${catalog} → actual_catalog                             │    │
  │     │ ${gold_schema} → actual_schema                          │    │
  │     └────────────────────────────────────────────────────────┘    │
  │                              │                                    │
  │                              ▼                                    │
  │  2. Execute EXPLAIN                                               │
  │     ┌────────────────────────────────────────────────────────┐    │
  │     │ spark.sql(f"EXPLAIN {rendered_query}")                  │    │
  │     └────────────────────────────────────────────────────────┘    │
  │                              │                                    │
  │           ┌──────────────────┴──────────────────┐                 │
  │           │                                     │                 │
  │           ▼                                     ▼                 │
  │  ┌────────────────┐                  ┌────────────────────┐      │
  │  │ SUCCESS        │                  │ FAILURE            │      │
  │  │ is_valid=TRUE  │                  │ is_valid=FALSE     │      │
  │  │ error=NULL     │                  │ error=<message>    │      │
  │  └────────────────┘                  └────────────────────┘      │
  │                                                                   │
  └───────────────────────────────────────────────────────────────────┘
             │
             ▼
  ┌──────────────────────┐
  │ alert_validation_    │
  │ results              │
  │ (overwrite mode)     │
  └──────────────────────┘
             │
             ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │ SUMMARY:                                                          │
  │ • Total: 29 alerts                                                │
  │ • Valid: 29 ✓                                                     │
  │ • Invalid: 0                                                      │
  │                                                                   │
  │ If invalid > 0: Exit with list of failed alert_ids               │
  └──────────────────────────────────────────────────────────────────┘
```

## Error Classification

The validator classifies errors for better debugging:

### UNRESOLVED_COLUMN

**Pattern:** `A column, variable, or function parameter with name X cannot be resolved`

```python
if "UNRESOLVED_COLUMN" in error_msg:
    # Extract column name from error
    match = re.search(r"with name `([^`]+)`", error_msg)
    col_name = match.group(1) if match else "unknown"
    return (alert_id, False, f"Column not found: `{col_name}`")
```

**Common Causes:**
- Typo in column name
- Column renamed in source table
- Wrong table being queried

### TABLE_OR_VIEW_NOT_FOUND

**Pattern:** `Table or view not found: X`

```python
if "TABLE_OR_VIEW_NOT_FOUND" in error_msg:
    match = re.search(r"Table or view not found: `?([^`\s]+)`?", error_msg)
    table_name = match.group(1) if match else "unknown"
    return (alert_id, False, f"Table not found: `{table_name}`")
```

**Common Causes:**
- Wrong catalog or schema
- Table not yet created
- Permission denied (appears as not found)

### PARSE_SYNTAX_ERROR

**Pattern:** `Syntax error at or near X`

```python
if "PARSE_SYNTAX_ERROR" in error_msg:
    return (alert_id, False, f"Syntax error: {error_msg[:200]}")
```

**Common Causes:**
- Missing quotes in SQL
- Unescaped special characters
- Invalid SQL syntax

## Implementation

### validate_alert_queries.py

```python
# Databricks notebook source
from datetime import datetime
from typing import List, Optional, Tuple
import re

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType


def render_query_template(
    template: str, 
    catalog: str, 
    gold_schema: str
) -> str:
    """Render query template with actual values."""
    return template.replace(
        "${catalog}", catalog
    ).replace(
        "${gold_schema}", gold_schema
    )


def validate_single_query(
    spark: SparkSession, 
    alert_id: str, 
    query: str
) -> Tuple[str, bool, Optional[str]]:
    """
    Validate a single SQL query using EXPLAIN.
    
    Returns:
        (alert_id, is_valid, error_message)
    """
    try:
        spark.sql(f"EXPLAIN {query}")
        return (alert_id, True, None)
    
    except Exception as e:
        error_msg = str(e)
        
        # Classify error
        if "UNRESOLVED_COLUMN" in error_msg:
            match = re.search(r"with name `([^`]+)`", error_msg)
            col_name = match.group(1) if match else "unknown"
            return (alert_id, False, f"Column not found: `{col_name}` - {error_msg[:200]}")
        
        elif "TABLE_OR_VIEW_NOT_FOUND" in error_msg:
            match = re.search(r"Table or view not found: `?([^`\s]+)`?", error_msg)
            table_name = match.group(1) if match else "unknown"
            return (alert_id, False, f"Table not found: `{table_name}`")
        
        elif "PARSE_SYNTAX_ERROR" in error_msg:
            return (alert_id, False, f"Syntax error: {error_msg[:200]}")
        
        else:
            return (alert_id, False, f"Error: {error_msg[:300]}")


def validate_all_alerts(
    spark: SparkSession,
    catalog: str,
    gold_schema: str
) -> List[Tuple[str, bool, Optional[str]]]:
    """
    Validate all enabled alert queries.
    
    Returns:
        List of (alert_id, is_valid, error_message) tuples
    """
    # Load enabled alerts
    df = spark.sql(f"""
        SELECT alert_id, alert_query_template
        FROM {catalog}.{gold_schema}.alert_configurations
        WHERE is_enabled = TRUE
    """)
    
    results = []
    
    for row in df.collect():
        # Render template
        rendered_query = render_query_template(
            row.alert_query_template,
            catalog,
            gold_schema
        )
        
        # Validate
        result = validate_single_query(spark, row.alert_id, rendered_query)
        results.append(result)
        
        # Print status
        if result[1]:
            print(f"✓ {result[0]}: Valid")
        else:
            print(f"✗ {result[0]}: {result[2]}")
    
    return results


def save_validation_results(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    results: List[Tuple[str, bool, Optional[str]]]
) -> None:
    """Save validation results to Delta table."""
    
    table_name = f"{catalog}.{gold_schema}.alert_validation_results"
    
    schema = StructType([
        StructField("alert_id", StringType(), False),
        StructField("is_valid", BooleanType(), False),
        StructField("error_message", StringType(), True),
        StructField("validation_timestamp", TimestampType(), False),
    ])
    
    data = [
        (alert_id, is_valid, error_msg, datetime.now())
        for alert_id, is_valid, error_msg in results
    ]
    
    df = spark.createDataFrame(data, schema)
    df.write.mode("overwrite").option("mergeSchema", "true").saveAsTable(table_name)
    
    print(f"\n✓ Validation results saved to {table_name}")


def main():
    """Main validation entry point."""
    spark = SparkSession.builder.getOrCreate()
    
    # Get parameters
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Validating alerts in {catalog}.{gold_schema}")
    print("=" * 60)
    
    # Run validation
    results = validate_all_alerts(spark, catalog, gold_schema)
    
    # Save results
    save_validation_results(spark, catalog, gold_schema, results)
    
    # Summary
    valid_count = sum(1 for _, is_valid, _ in results if is_valid)
    invalid_count = len(results) - valid_count
    
    print("\n" + "=" * 60)
    print(f"VALIDATION SUMMARY")
    print(f"  Total alerts:  {len(results)}")
    print(f"  Valid:         {valid_count} ✓")
    print(f"  Invalid:       {invalid_count} {'❌' if invalid_count > 0 else ''}")
    print("=" * 60)
    
    # Exit with status
    if invalid_count > 0:
        failed_ids = [aid for aid, is_valid, _ in results if not is_valid]
        dbutils.notebook.exit(f"FAILED: {invalid_count} invalid queries: {', '.join(failed_ids)}")
    else:
        dbutils.notebook.exit("SUCCESS: All queries valid")


if __name__ == "__main__":
    main()
```

## alert_validation_results Table

### Schema

```sql
CREATE TABLE ${catalog}.${gold_schema}.alert_validation_results (
    alert_id STRING NOT NULL,
    is_valid BOOLEAN NOT NULL,
    error_message STRING,
    validation_timestamp TIMESTAMP NOT NULL
)
USING DELTA;
```

### Query Validation Status

```sql
-- All invalid alerts
SELECT alert_id, error_message, validation_timestamp
FROM alert_validation_results
WHERE is_valid = FALSE
ORDER BY validation_timestamp DESC;

-- Validation coverage
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) as valid,
    SUM(CASE WHEN NOT is_valid THEN 1 ELSE 0 END) as invalid,
    ROUND(SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as valid_pct
FROM alert_validation_results;
```

## Integration with Job Pipeline

Validation runs **before** deployment in the job pipeline:

```
alerting_layer_setup_job (Composite)
├── setup_alerting_tables
├── seed_all_alerts
├── validate_alert_queries  ◄── Validation step
│   │
│   └── If invalid > 0: Job fails here (prevents bad deployment)
│
├── sync_notification_destinations
└── deploy_sql_alerts  ◄── Only runs if validation passes
```

## Common Validation Failures

### Issue 1: SQL Escaping in LIKE Patterns

**Problem:** Queries with `LIKE '%pattern%'` fail after insertion via SQL INSERT.

```sql
-- Original query
WHERE sku_name LIKE '%ALL_PURPOSE%'

-- After SQL INSERT (quotes stripped!)
WHERE sku_name LIKE %ALL_PURPOSE%  -- Invalid!
```

**Solution:** Use DataFrame insertion:

```python
# ✅ Use DataFrame with explicit schema
df = spark.createDataFrame([{
    "alert_query_template": "SELECT * FROM t WHERE col LIKE '%pattern%'"
}], schema=ALERT_CONFIG_SCHEMA)
df.write.mode("append").saveAsTable("alert_configurations")
```

### Issue 2: Column Renamed in Source

**Problem:** Source table column was renamed but alert not updated.

```sql
-- Old column name
SELECT event_time FROM fact_audit_logs
-- Error: UNRESOLVED_COLUMN: event_time

-- New column name
SELECT event_date FROM fact_audit_logs
-- ✓ Valid
```

**Solution:** Update alert query template to use new column name.

### Issue 3: Wrong Schema Reference

**Problem:** Query references wrong schema.

```sql
-- Hardcoded schema (wrong)
SELECT * FROM gold.fact_usage

-- Using placeholder (correct)
SELECT * FROM ${catalog}.${gold_schema}.fact_usage
```

## Validation Checklist

Before deployment, verify:

- [ ] All queries use `${catalog}` and `${gold_schema}` placeholders
- [ ] Column names match actual table schema
- [ ] Table names are correct
- [ ] SQL syntax is valid
- [ ] LIKE patterns use DataFrame insertion (not SQL INSERT)
- [ ] Division by zero is handled with NULLIF

## Troubleshooting

### Debug Invalid Query

```python
# Manually test a query
query = """
    SELECT SUM(list_cost) as daily_cost
    FROM my_catalog.gold.fact_usage
    WHERE usage_date = CURRENT_DATE() - 1
"""

try:
    spark.sql(f"EXPLAIN {query}")
    print("Query is valid!")
except Exception as e:
    print(f"Error: {e}")
```

### Re-validate After Fix

```bash
# Run validation job
databricks bundle run -t dev alert_query_validation_job
```

## Next Steps

- **[08-Hierarchical Job Architecture](08-hierarchical-job-architecture.md)**: Job structure
- **[09-Partial Success Patterns](09-partial-success-patterns.md)**: Error handling
- **[11-Implementation Guide](11-implementation-guide.md)**: Step-by-step setup


