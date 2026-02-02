# Silver Layer Development Standards

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | DA-03 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Data Engineering Team |
| **Status** | Approved |

---

## Executive Summary

The Silver layer transforms raw Bronze data into validated, cleaned, and deduplicated datasets using Delta Live Tables (DLT) with data quality expectations. This document defines standards for DLT patterns, expectations, and the DQX framework.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| DA-03 | Silver layer must be streaming with DLT expectations | 🔴 Critical |
| DA-04 | DLT expectations must quarantine bad records | 🟡 Required |
| DA-05 | DQX for advanced validation with detailed diagnostics | 🟡 Required |
| DA-06 | Pure Python files for shared modules (not notebooks) | 🔴 Critical |

---

## Rule DA-03: DLT Streaming Pattern

### Standard DLT Table Definition

```python
import dlt
from pyspark.sql.functions import col, current_timestamp


@dlt.table(
    name="silver_customers",
    comment="""
    Silver layer customer dimension with data quality validation.
    Business: Validated customer records from Bronze layer.
    Technical: Streaming incremental from Bronze with deduplication.
    """,
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "layer": "silver",
        "source_table": "bronze_customers",
        "domain": "customer"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop({
    "valid_customer_id": "customer_id IS NOT NULL",
    "valid_email": "email IS NOT NULL AND email LIKE '%@%'",
    "valid_status": "status IN ('active', 'inactive', 'pending')"
})
def silver_customers():
    """Transform Bronze customers to Silver with validation."""
    return (
        dlt.read_stream("bronze_customers")
        .select(
            col("customer_id"),
            col("email"),
            col("first_name"),
            col("last_name"),
            col("status"),
            col("created_date"),
            current_timestamp().alias("processed_timestamp")
        )
    )
```

### DLT Direct Publishing Mode

**Modern pattern - use `catalog:` and `schema:` fields:**

```yaml
# In resources/silver_dlt_pipeline.yml
resources:
  pipelines:
    silver_pipeline:
      name: "[${bundle.target}] Silver DLT Pipeline"
      
      # ✅ CORRECT: Direct Publishing Mode
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      
      # ❌ DEPRECATED: target field
      # target: ${var.catalog}.${var.silver_schema}
```

---

## Rule DA-04: DLT Expectations Patterns

### Expectation Types

| Type | Behavior | Use When |
|------|----------|----------|
| `@dlt.expect` | Log violation, keep record | Warning only |
| `@dlt.expect_or_drop` | Drop violating records | Data quality critical |
| `@dlt.expect_or_fail` | Fail pipeline | Hard constraint |
| `@dlt.expect_all_or_drop` | Multiple rules, drop on any failure | Multiple quality rules |

### Dynamic Expectations from Config

```python
def get_quality_rules(table_name: str) -> dict:
    """
    Load quality rules from dq_rules table.
    
    This enables rule changes without code deployment.
    """
    try:
        # Read from config table
        rules_df = spark.table(f"{catalog}.{schema}.dq_rules")
        rules = rules_df.filter(col("table_name") == table_name).collect()
        
        return {row.rule_name: row.rule_expression for row in rules}
    except Exception as e:
        print(f"⚠ Could not load rules: {e}")
        return {}


@dlt.table(name="silver_orders")
@dlt.expect_all_or_drop(get_quality_rules("silver_orders"))
def silver_orders():
    return dlt.read_stream("bronze_orders")
```

### Quarantine Pattern

```python
# Main validated table
@dlt.table(name="silver_orders")
@dlt.expect_all_or_drop({
    "valid_order_id": "order_id IS NOT NULL",
    "valid_amount": "amount > 0"
})
def silver_orders():
    return dlt.read_stream("bronze_orders")


# Quarantine table for failed records
@dlt.table(
    name="silver_orders_quarantine",
    comment="Failed validation records for investigation"
)
def silver_orders_quarantine():
    return (
        dlt.read_stream("bronze_orders")
        .filter(
            (col("order_id").isNull()) | 
            (col("amount") <= 0)
        )
        .withColumn("quarantine_reason", 
            when(col("order_id").isNull(), "null_order_id")
            .when(col("amount") <= 0, "invalid_amount")
            .otherwise("unknown")
        )
        .withColumn("quarantine_timestamp", current_timestamp())
    )
```

---

## Rule DA-05: DQX Framework

### When to Use DQX vs DLT Expectations

| Feature | DLT Expectations | DQX |
|---------|------------------|-----|
| Simple null/range checks | ✅ Preferred | Works |
| Detailed failure diagnostics | ❌ Limited | ✅ Detailed |
| Auto-profiling | ❌ No | ✅ Yes |
| Custom error messages | ❌ No | ✅ Yes |
| Quarantine with metadata | Manual | ✅ Built-in |

### DQX Installation

**CRITICAL: Environment-level dependencies for serverless:**

```yaml
# In databricks.yml
environments:
  - environment_key: "default"
    spec:
      environment_version: "4"
      dependencies:
        - "dqx"  # ✅ Environment level
```

### DQX Check Definition (YAML)

```yaml
# checks/silver_orders_checks.yaml
checks:
  - name: order_id_not_null
    criticality: error
    check:
      function: is_not_null
      arguments:
        column: order_id

  - name: amount_positive
    criticality: error
    check:
      function: is_not_less_than
      arguments:
        column: amount
        limit: 0  # ✅ Integer, not float
        # ❌ value: 0.0  # Wrong parameter name

  - name: status_valid
    criticality: warning
    check:
      function: is_in_list
      arguments:
        column: status
        allowed: ['pending', 'completed', 'cancelled']
        # ❌ values: [...]  # Wrong parameter name
```

### DQX API Reference

**CRITICAL: Use exact function and parameter names:**

| Function | Parameters | Example |
|----------|------------|---------|
| `is_not_null` | `column` | `is_not_null(column="id")` |
| `is_not_less_than` | `column`, `limit` | `is_not_less_than(column="amount", limit=0)` |
| `is_not_greater_than` | `column`, `limit` | `is_not_greater_than(column="age", limit=150)` |
| `is_in_list` | `column`, `allowed` | `is_in_list(column="status", allowed=["a","b"])` |
| `is_in_range` | `column`, `min_limit`, `max_limit` | `is_in_range(column="pct", min_limit=0, max_limit=100)` |
| `matches_regex` | `column`, `regex` | `matches_regex(column="email", regex=".*@.*")` |

### DQX Application Pattern

```python
from dqx import DQEngine


def apply_dqx_checks(df, checks_yaml_path: str, entity_name: str):
    """
    Apply DQX checks and split valid/invalid records.
    
    Uses metadata-based API for YAML checks.
    """
    import yaml
    
    # Load checks from YAML
    with open(checks_yaml_path) as f:
        checks = yaml.safe_load(f)['checks']
    
    # Initialize DQX engine
    engine = DQEngine(spark)
    
    # Apply checks and split
    # ✅ CORRECT: apply_checks_by_metadata_and_split for dict/YAML
    valid_df, invalid_df = engine.apply_checks_by_metadata_and_split(
        df, checks
    )
    
    # ❌ WRONG: apply_checks_and_split is for code-based checks
    # valid_df, invalid_df = engine.apply_checks_and_split(df, checks)
    
    return valid_df, invalid_df
```

### DQX Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Function 'has_min' not defined` | Wrong function name | Use `is_not_less_than` |
| `Unexpected argument 'value'` | Wrong parameter name | Use `limit` |
| `TypeError: expected int, got float` | Float in limit | Use integer: `0` not `0.0` |
| `sparkContext not supported` | Spark Connect incompatible | Use `spark.sql()` instead |

---

## Rule DA-06: Pure Python Modules

### The Problem

Notebooks with `# Databricks notebook source` header cannot be imported in serverless compute.

### The Solution

```python
# ❌ WRONG: Notebook header prevents import
# File: utils.py
# Databricks notebook source  # ❌ This line breaks imports!

def helper():
    pass


# ✅ CORRECT: Pure Python file (no header)
# File: utils.py
"""Utility functions for Silver layer."""

def helper():
    """Helper function."""
    pass
```

### Import Pattern for Asset Bundles

```python
# At top of notebook that needs to import modules
import sys
from pathlib import Path

# Add src to path for Asset Bundle imports
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
workspace_path = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, workspace_path)

# Now imports work
from utils import helper  # ✅ Works if utils.py is pure Python
```

---

## Table Properties Standard

```python
table_properties={
    # Quality marker
    "quality": "silver",
    
    # Delta features
    "delta.enableChangeDataFeed": "true",
    "delta.enableRowTracking": "true",
    "delta.enableDeletionVectors": "true",
    "delta.autoOptimize.optimizeWrite": "true",
    "delta.autoOptimize.autoCompact": "true",
    "delta.tuneFileSizesForRewrites": "true",
    
    # Governance
    "layer": "silver",
    "source_table": "<bronze_table_name>",
    "domain": "<domain>",
    "entity_type": "dimension|fact",
    "contains_pii": "true|false",
    "data_classification": "confidential|internal"
}
```

---

## Validation Checklist

### DLT Configuration
- [ ] Pipeline uses Direct Publishing Mode (`catalog:` + `schema:`)
- [ ] All tables use `@dlt.table` decorator
- [ ] All tables have `cluster_by_auto=True`
- [ ] All tables have comprehensive `table_properties`
- [ ] All tables have LLM-friendly comments

### Data Quality
- [ ] All tables have DLT expectations
- [ ] Critical rules use `expect_or_drop` or `expect_all_or_drop`
- [ ] Quarantine tables exist for failed records
- [ ] DQX used for advanced validation (if needed)

### Code Quality
- [ ] Shared modules are pure Python (no notebook header)
- [ ] sys.path setup for Asset Bundle imports
- [ ] Rules externalized to config table (optional)

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Table not found: dq_rules` | DLT ran before setup | Run setup job first |
| `ModuleNotFoundError` | Notebook header in .py file | Remove `# Databricks notebook source` |
| `DataFrame.collect not supported` | Spark Connect limitation | Use `toPandas()` |
| DLT expectation not firing | Stream vs batch mismatch | Use `read_stream` |

---

## Related Documents

- [Bronze Layer Standards](10-bronze-layer-standards.md)
- [Gold Layer Standards](12-gold-layer-standards.md)
- [Python Development Standards](../part3-infrastructure/21-python-development-standards.md)

---

## References

- [DLT Expectations](https://docs.databricks.com/dlt/expectations)
- [DLT Expectation Patterns](https://docs.databricks.com/dlt/expectation-patterns)
- [DQX Documentation](https://databrickslabs.github.io/dqx/)
