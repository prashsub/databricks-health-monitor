# Silver Layer Rules for Claude Code

This file combines all Silver layer cursor rules for use by Claude Code.

---

## DQX (Data Quality Framework) Patterns

### When to Use DQX vs DLT Expectations

| Feature | DLT Expectations | DQX |
|---------|------------------|-----|
| Detailed failure diagnostics | ❌ | ✅ |
| Auto data profiling | ❌ | ✅ |
| Flexible quarantine strategies | ❌ | ✅ |
| Native DLT integration | ✅ | Hybrid |
| Performance overhead | Low | Medium |
| Setup complexity | Low | Medium |

**Use DQX when:**
- Need detailed failure diagnostics per record
- Want auto data profiling
- Need flexible quarantine strategies
- Implementing Gold layer pre-merge validation

### Serverless Library Configuration

```yaml
# resources/<layer>_job.yml
resources:
  jobs:
    silver_dq_job:
      name: "[${bundle.target}] Silver DQ with DQX"
      
      # ✅ Define dependencies at environment level (NOT task level)
      environments:
        - environment_key: default
          spec:
            dependencies:
              - "databricks-labs-dqx==0.8.0"
      
      tasks:
        - task_key: apply_dqx_checks
          environment_key: default
          notebook_task:
            notebook_path: ../src/<layer>/apply_dqx_checks.py
```

### DQX API Reference

#### Correct Function Names

| Use Case | ✅ Correct Function | ❌ WRONG |
|----------|---------------------|----------|
| Column >= value | `is_not_less_than` | `has_min` |
| Column <= value | `is_not_greater_than` | `has_max` |
| Column in list | `is_in_list` | `is_in` |
| Not null | `is_not_null` | `not_null` |
| Unique | `is_unique` | `unique` |
| Regex match | `matches_regex` | `regex_match` |

#### Parameter Names

```python
# ✅ CORRECT: Use 'limit' for comparison functions
{
    "function": "is_not_less_than",
    "arguments": {
        "column": "revenue",
        "limit": 0  # ✅ Correct parameter name
    }
}

# ❌ WRONG: 'value' not recognized
{
    "function": "is_not_less_than",
    "arguments": {
        "column": "revenue",
        "value": 0  # ❌ Will fail!
    }
}
```

#### Data Type Requirements

```python
# ✅ CORRECT: Integer values for limits
{
    "function": "is_not_greater_than",
    "arguments": {
        "column": "return_rate_pct",
        "limit": 50  # ✅ Integer
    }
}

# ❌ WRONG: Float values
{
    "function": "is_not_greater_than",
    "arguments": {
        "column": "return_rate_pct",
        "limit": 50.0  # ❌ Float may cause issues
    }
}
```

### Quality Check Definition

#### YAML Format

```yaml
# checks/silver_checks.yaml
checks:
  - function: is_not_null
    arguments:
      column: store_number
    criticality: error
    
  - function: is_not_less_than
    arguments:
      column: quantity_sold
      limit: 0
    criticality: warn
    
  - function: is_in_list
    arguments:
      column: status
      allowed: ["active", "inactive", "pending"]
    criticality: error
```

#### Python Programmatic

```python
from databricks.labs.dqx.col_functions import (
    is_not_null,
    is_not_less_than,
    is_in_list,
    matches_regex
)

checks = [
    is_not_null("store_number"),
    is_not_less_than("quantity_sold", 0),
    is_in_list("status", ["active", "inactive", "pending"]),
    matches_regex("email", r"^[\w\.-]+@[\w\.-]+\.\w+$")
]
```

### Applying Checks

#### Metadata-Based API (for YAML/Dict checks)

```python
from databricks.labs.dqx.engine import DQEngine

dq_engine = DQEngine(spark)

# Load checks from YAML
checks = dq_engine.load_checks_from_yaml("checks/silver_checks.yaml")

# Apply and split valid/invalid
valid_df, invalid_df = dq_engine.apply_checks_by_metadata_and_split(df, checks)

print(f"Valid records: {valid_df.count()}")
print(f"Invalid records: {invalid_df.count()}")
```

#### Code-Based API (for Python function checks)

```python
# Apply checks defined as Python functions
result_df = dq_engine.apply_checks(df, checks)

# Split results
valid_df = result_df.filter("_dq_status = 'valid'")
invalid_df = result_df.filter("_dq_status = 'invalid'")
```

### Gold Layer Pre-Merge Validation

```python
from databricks.labs.dqx.engine import DQEngine
from databricks.labs.dqx.col_functions import (
    is_not_null,
    is_not_less_than,
    is_not_greater_than
)

def apply_dqx_validation(
    spark,
    df,
    catalog,
    schema,
    entity,
    enable_quarantine=True
):
    """Apply DQX validation before Gold merge."""
    
    dq_engine = DQEngine(spark)
    
    # Define checks for Gold layer
    checks = [
        is_not_null("store_number"),
        is_not_null("transaction_date"),
        is_not_less_than("net_revenue", 0),
        is_not_greater_than("discount_pct", 100),
    ]
    
    # Apply checks
    result_df = dq_engine.apply_checks(df, checks)
    
    # Split valid/invalid
    valid_df = result_df.filter("_dq_status = 'valid'").drop("_dq_status", "_dq_issues")
    invalid_df = result_df.filter("_dq_status = 'invalid'")
    
    # Quarantine invalid records
    if enable_quarantine and invalid_df.count() > 0:
        invalid_df.write.mode("append").saveAsTable(
            f"{catalog}.{schema}.{entity}_quarantine"
        )
        print(f"⚠️ Quarantined {invalid_df.count()} invalid records")
    
    # Statistics
    stats = {
        "total": df.count(),
        "valid": valid_df.count(),
        "invalid": invalid_df.count(),
        "pass_rate": valid_df.count() / df.count() * 100
    }
    
    print(f"DQX Validation: {stats['pass_rate']:.1f}% pass rate")
    
    return valid_df, invalid_df, stats
```

### DLT + DQX Hybrid Pattern

```python
import dlt
from databricks.labs.dqx.engine import DQEngine

@dlt.table(
    name="silver_transactions",
    comment="Silver transactions with DLT + DQX quality",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_store", "store_number IS NOT NULL")
@dlt.expect_or_drop("positive_amount", "amount > 0")
def silver_transactions():
    # DLT handles basic expectations
    df = dlt.read_stream("bronze_transactions")
    
    # DQX adds detailed diagnostics for complex rules
    dq_engine = DQEngine(spark)
    checks = load_complex_checks()  # From YAML or code
    
    result_df = dq_engine.apply_checks(df, checks)
    valid_df = result_df.filter("_dq_status = 'valid'")
    
    return valid_df.drop("_dq_status", "_dq_issues")
```

### Spark Connect Compatibility

**Avoid `sparkContext` - use SQL queries instead:**

```python
# ❌ WRONG: sparkContext not available in Spark Connect
spark.sparkContext.setLogLevel("ERROR")

# ✅ CORRECT: Use SQL or DataFrame operations
# (DQX works with DataFrame API, which is Spark Connect compatible)
```

### Troubleshooting Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `AttributeError: 'has_min'` | Wrong function name | Use `is_not_less_than` |
| `TypeError: limit` | Wrong parameter name | Use `limit` not `value` |
| `ValidationError: float` | Float instead of int | Use integer for limits |
| `ModuleNotFoundError` | Wrong library install location | Install at environment level |

### Validation Checklist

- [ ] DQX installed at environment level (not task level)
- [ ] Correct function names used (`is_not_less_than`, etc.)
- [ ] Correct parameter names (`limit`, not `value`)
- [ ] Integer values for numeric limits
- [ ] `apply_checks_by_metadata_and_split` for YAML/dict checks
- [ ] `apply_checks` for Python function checks
- [ ] Quarantine table created for invalid records
- [ ] No `sparkContext` usage (Spark Connect compatible)
- [ ] Statistics logged for monitoring



