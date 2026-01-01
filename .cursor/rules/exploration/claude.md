# Exploration Rules for Claude Code

This file combines all exploration-related cursor rules for use by Claude Code.

---

## Ad-Hoc Exploration Notebooks

### Core Principle: Dual-Format Development

Ad-hoc exploration notebooks must work in **two environments**:
1. **Databricks Workspace** (`.py` format with magic commands)
2. **Local Development via Databricks Connect** (`.ipynb` format)

**Key Insight:** Magic commands (`%pip`, `%sql`, `dbutils.library.restartPython()`) only work in Databricks workspace, NOT in Databricks Connect.

### Databricks Workspace Format (.py)

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Ad-Hoc Data Exploration Notebook
# MAGIC 
# MAGIC Interactive exploration of the data lake with pre-built helper functions.

# COMMAND ----------

from databricks.connect import DatabricksSession
from pyspark.sql.functions import *
from databricks.sdk.runtime import dbutils
import json

# Initialize Spark session for Databricks Connect
# ✅ CRITICAL: Specify serverless or cluster_id for Databricks Connect
spark = DatabricksSession.builder.serverless().profile("your_profile").getOrCreate()

# Configuration - Update these values for your environment
catalog = "your_catalog"
bronze_schema = "your_bronze_schema"
silver_schema = "your_silver_schema"
gold_schema = "your_gold_schema"

# Try to use widgets if available (Databricks workspace)
try:
    dbutils.widgets.text("catalog", catalog, "Catalog")
    dbutils.widgets.text("bronze_schema", bronze_schema, "Bronze Schema")
    dbutils.widgets.text("silver_schema", silver_schema, "Silver Schema")
    dbutils.widgets.text("gold_schema", gold_schema, "Gold Schema")
    
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    silver_schema = dbutils.widgets.get("silver_schema")
    gold_schema = dbutils.widgets.get("gold_schema")
except Exception:
    # Widgets not available (Databricks Connect), use direct assignment
    pass

print(f"Catalog: {catalog}")
print(f"Bronze Schema: {bronze_schema}")
print(f"Silver Schema: {silver_schema}")
print(f"Gold Schema: {gold_schema}")
```

### Local Jupyter Format (.ipynb)

```python
# Cell 1: Setup
from databricks.connect import DatabricksSession
from pyspark.sql.functions import *
import json

# Initialize Spark session - MUST specify serverless or cluster
spark = DatabricksSession.builder.serverless().profile("your_profile").getOrCreate()

# Direct assignment (no widgets in Databricks Connect)
catalog = "your_catalog"
bronze_schema = "your_bronze_schema"
silver_schema = "your_silver_schema"
gold_schema = "your_gold_schema"
```

### Standard Helper Functions

#### 1. List Tables in Schema

```python
def list_tables(schema_name: str) -> None:
    """List all tables in a schema with row counts."""
    tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema_name}").collect()
    
    print(f"\n{'='*60}")
    print(f"Tables in {catalog}.{schema_name}")
    print(f"{'='*60}")
    
    for table in tables:
        table_name = table.tableName
        try:
            count = spark.table(f"{catalog}.{schema_name}.{table_name}").count()
            print(f"  {table_name}: {count:,} rows")
        except Exception as e:
            print(f"  {table_name}: Error - {str(e)[:50]}")
```

#### 2. Explore Table

```python
def explore_table(table_name: str, sample_size: int = 5) -> None:
    """Show schema and sample data for a table."""
    print(f"\n{'='*60}")
    print(f"Exploring: {table_name}")
    print(f"{'='*60}")
    
    df = spark.table(table_name)
    
    # Schema
    print("\nSchema:")
    df.printSchema()
    
    # Row count
    count = df.count()
    print(f"\nTotal Rows: {count:,}")
    
    # Sample data
    print(f"\nSample ({sample_size} rows):")
    df.show(sample_size, truncate=False)
    
    # Statistics for numeric columns
    print("\nNumeric Column Statistics:")
    df.describe().show()
```

#### 3. Check Data Quality

```python
def check_data_quality(table_name: str) -> dict:
    """Run basic data quality checks on a table."""
    df = spark.table(table_name)
    
    results = {
        "table": table_name,
        "total_rows": df.count(),
        "columns": [],
        "issues": []
    }
    
    for column in df.columns:
        col_info = {
            "name": column,
            "null_count": df.filter(col(column).isNull()).count(),
            "distinct_count": df.select(column).distinct().count()
        }
        
        col_info["null_percentage"] = (col_info["null_count"] / results["total_rows"] * 100) if results["total_rows"] > 0 else 0
        
        if col_info["null_percentage"] > 10:
            results["issues"].append(f"High null rate in {column}: {col_info['null_percentage']:.1f}%")
        
        if col_info["distinct_count"] == 1:
            results["issues"].append(f"Single value in {column}")
            
        results["columns"].append(col_info)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Data Quality Report: {table_name}")
    print(f"{'='*60}")
    print(f"Total Rows: {results['total_rows']:,}")
    print(f"\nColumn Analysis:")
    for col_info in results["columns"]:
        print(f"  {col_info['name']}: {col_info['null_count']:,} nulls ({col_info['null_percentage']:.1f}%), {col_info['distinct_count']:,} distinct")
    
    if results["issues"]:
        print(f"\n⚠️ Issues Found:")
        for issue in results["issues"]:
            print(f"  - {issue}")
    else:
        print(f"\n✅ No issues found")
    
    return results
```

#### 4. Compare Tables

```python
def compare_tables(table1: str, table2: str, key_columns: list) -> None:
    """Compare two tables by key columns."""
    df1 = spark.table(table1)
    df2 = spark.table(table2)
    
    print(f"\n{'='*60}")
    print(f"Comparing Tables")
    print(f"{'='*60}")
    print(f"Table 1: {table1} ({df1.count():,} rows)")
    print(f"Table 2: {table2} ({df2.count():,} rows)")
    
    # Keys in table1 not in table2
    keys1 = df1.select(key_columns).distinct()
    keys2 = df2.select(key_columns).distinct()
    
    only_in_1 = keys1.subtract(keys2).count()
    only_in_2 = keys2.subtract(keys1).count()
    in_both = keys1.intersect(keys2).count()
    
    print(f"\nKey Analysis (on {key_columns}):")
    print(f"  Only in {table1}: {only_in_1:,}")
    print(f"  Only in {table2}: {only_in_2:,}")
    print(f"  In both: {in_both:,}")
```

#### 5. Show Table Properties

```python
def show_table_properties(table_name: str) -> None:
    """Show table properties and metadata."""
    print(f"\n{'='*60}")
    print(f"Table Properties: {table_name}")
    print(f"{'='*60}")
    
    # Extended description
    spark.sql(f"DESCRIBE EXTENDED {table_name}").show(100, truncate=False)
    
    # Table properties
    print("\nTable Properties:")
    spark.sql(f"SHOW TBLPROPERTIES {table_name}").show(100, truncate=False)
```

### Critical Patterns

#### Widget Fallback Pattern

```python
# Try to use widgets if available (Databricks workspace)
try:
    dbutils.widgets.text("param_name", default_value, "Label")
    param_value = dbutils.widgets.get("param_name")
except Exception:
    # Widgets not available (Databricks Connect), use direct assignment
    param_value = default_value
```

#### Spark Session Initialization

```python
# ✅ CORRECT: Always specify serverless or cluster_id
spark = DatabricksSession.builder.serverless().profile("your_profile").getOrCreate()

# OR with specific cluster
spark = DatabricksSession.builder.clusterId("your-cluster-id").profile("your_profile").getOrCreate()

# ❌ WRONG: Missing compute specification
spark = DatabricksSession.builder.getOrCreate()  # Will fail!
```

### Documentation Requirements

Each exploration notebook should include:

1. **README.md** - Overview and setup instructions
2. **QUICKSTART.md** - Quick commands to get started

#### README.md Template

```markdown
# Ad-Hoc Exploration Notebook

## Overview
Interactive data exploration notebook for [project name].

## Setup

### Databricks Workspace
1. Import the `.py` file to your workspace
2. Attach to a cluster or use serverless
3. Run cells interactively

### Local Development (Databricks Connect)
1. Install requirements: `pip install -r requirements.txt`
2. Configure Databricks profile: `databricks configure --profile your_profile`
3. Open `.ipynb` in Jupyter

## Available Functions
- `list_tables(schema)` - List all tables with row counts
- `explore_table(table_name)` - Show schema and sample data
- `check_data_quality(table_name)` - Run DQ checks
- `compare_tables(t1, t2, keys)` - Compare two tables
- `show_table_properties(table_name)` - Show metadata

## Configuration
Update these variables at the top of the notebook:
- `catalog` - Unity Catalog name
- `bronze_schema` - Bronze layer schema
- `silver_schema` - Silver layer schema  
- `gold_schema` - Gold layer schema
```

### Common Mistakes to Avoid

❌ **Magic commands in Databricks Connect:**
```python
%pip install package  # Won't work in Databricks Connect
%sql SELECT * FROM table  # Won't work in Databricks Connect
```

✅ **Use Python equivalents:**
```python
# For SQL
spark.sql("SELECT * FROM table").show()

# For pip (do before starting notebook)
# pip install package
```

❌ **Missing Spark session configuration:**
```python
spark = DatabricksSession.builder.getOrCreate()  # Missing compute!
```

✅ **Always specify compute:**
```python
spark = DatabricksSession.builder.serverless().profile("profile").getOrCreate()
```

### Validation Checklist

- [ ] Both `.py` and `.ipynb` versions exist
- [ ] Widget fallback pattern implemented
- [ ] Spark session specifies serverless or cluster_id
- [ ] All 5 standard helper functions included
- [ ] README.md and QUICKSTART.md provided
- [ ] No magic commands in `.ipynb` version
- [ ] Tested in both Databricks workspace and locally

