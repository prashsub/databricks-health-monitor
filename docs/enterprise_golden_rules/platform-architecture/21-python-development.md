# Python Development Standards

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | PA-DEV-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Platform Engineering Team |
| **Status** | Approved |

---

## Executive Summary

This document defines Python development standards for Databricks, including parameter handling, module imports, and the critical distinction between pure Python files and notebooks. These patterns prevent common deployment failures in Asset Bundle jobs.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| PA-07 | Use `dbutils.widgets.get()` for parameters | 🔴 Critical |
| PA-08 | Pure Python files for imports | 🔴 Critical |
| PA-11 | sys.path setup for Asset Bundle imports | 🔴 Critical |
| PA-12 | No notebook header in importable modules | 🔴 Critical |

---

## Rule PA-07: Parameter Handling

### The Problem

When notebooks run via `notebook_task` in Asset Bundles, parameters are passed through widgets, NOT command-line arguments. Using `argparse` causes immediate failure.

```python
# Error when using argparse in notebook_task:
# usage: db_ipykernel_launcher.py [-h] --catalog CATALOG
# error: the following arguments are required: --catalog
```

### The Pattern

```python
# ✅ CORRECT: dbutils.widgets.get()
def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
    
    print(f"Parameters received:")
    print(f"  catalog: {catalog}")
    print(f"  schema: {schema}")
    
    return catalog, schema


def main():
    catalog, schema = get_parameters()
    
    spark = SparkSession.builder.appName("My Job").getOrCreate()
    
    # Your logic here
    ...


if __name__ == "__main__":
    main()
```

### ❌ WRONG: argparse

```python
# ❌ This FAILS in notebook_task!
import argparse

def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args()  # ERROR!
    return args.catalog, args.schema
```

### YAML Configuration

```yaml
tasks:
  - task_key: my_task
    notebook_task:
      notebook_path: ../src/my_script.py
      base_parameters:  # These become widgets
        catalog: ${var.catalog}
        schema: ${var.gold_schema}
```

### Parameter Method Decision Table

| Context | YAML Config | Python Method |
|---------|-------------|---------------|
| `notebook_task` in DABs | `base_parameters: {}` | `dbutils.widgets.get()` |
| Interactive notebook | Widgets panel | `dbutils.widgets.get()` |
| DLT pipeline | `configuration: {}` | `spark.conf.get()` |
| Local Python script | Command line | `argparse` |

---

## Rule PA-08 & PA-12: Pure Python Files vs Notebooks

### The Problem

Files with the `# Databricks notebook source` header cannot be imported in serverless compute. This header is automatically added when you create a notebook in the Databricks UI.

```python
# ❌ utils.py with notebook header - CANNOT be imported!
# Databricks notebook source  ← This line breaks imports!

def helper():
    pass

# When you try to import:
# from utils import helper
# Error: ModuleNotFoundError
```

### The Solution

**Remove the notebook header from any file you want to import:**

```python
# ✅ utils.py - Pure Python file (NO header)
"""Utility functions for data processing."""

def helper():
    """Helper function that can be imported."""
    pass

def another_helper():
    """Another importable function."""
    pass
```

### How to Convert Notebook to Pure Python

1. Open the file in an editor (VS Code, etc.)
2. Remove the first line if it contains `# Databricks notebook source`
3. Remove any magic commands (`%pip`, `%run`, etc.)
4. Ensure all imports are standard Python imports

### File Type Reference

| File Type | Header | Can Import | Use For |
|-----------|--------|------------|---------|
| **Pure Python (.py)** | None | ✅ Yes | Shared modules, utilities |
| **Databricks Notebook** | `# Databricks notebook source` | ❌ No | Entry points, interactive work |

### Organization Pattern

```
src/
├── my_project/
│   ├── __init__.py           # Package init
│   ├── utils.py              # Pure Python - shared utilities
│   ├── transformations.py    # Pure Python - reusable transforms
│   └── constants.py          # Pure Python - config constants
│
├── jobs/
│   ├── bronze_setup.py       # Notebook - entry point
│   ├── gold_merge.py         # Notebook - entry point
│   └── silver_pipeline.py    # Notebook - DLT pipeline
```

---

## Rule PA-11: sys.path Setup for Asset Bundles

### The Problem

When Asset Bundles deploy notebooks, the module search path doesn't include your `src/` folder. Standard imports fail.

```python
# In deployed notebook
from my_project.utils import helper
# Error: ModuleNotFoundError: No module named 'my_project'
```

### The Solution: sys.path Setup Block

Add this block at the top of notebooks that need to import modules:

```python
# Databricks notebook source

# ============================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ============================================
import sys
from pathlib import Path

def setup_path():
    """Set up sys.path for Asset Bundle module imports."""
    try:
        # Get notebook location in workspace
        notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        
        # Calculate workspace path (adjust depth based on your structure)
        # If notebook is at /Workspace/.../src/jobs/my_job.py
        # We need /Workspace/.../src
        workspace_base = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
        
        if workspace_base not in sys.path:
            sys.path.insert(0, workspace_base)
            print(f"Added to sys.path: {workspace_base}")
        
        return workspace_base
    except Exception as e:
        print(f"⚠ Could not set up path: {e}")
        return None

# Run setup
workspace_path = setup_path()

# ============================================
# NOW IMPORTS WORK
# ============================================
from my_project.utils import helper
from my_project.transformations import transform_data
```

### Alternative: Inline Functions

For simpler cases, inline the functions directly:

```python
# Instead of importing from utils.py, define inline
def get_gold_schema(domain: str, table_name: str) -> dict:
    """Inline function when imports are problematic."""
    import yaml
    from pathlib import Path
    
    yaml_file = Path(f"gold_layer_design/yaml/{domain}/{table_name}.yaml")
    with open(yaml_file) as f:
        return yaml.safe_load(f)
```

---

## DLT Pipeline Parameter Pattern

### The Pattern

DLT pipelines use `spark.conf.get()` instead of `dbutils.widgets.get()`:

```python
# DLT Pipeline
import dlt
from pyspark.sql import functions as F

# Get configuration from pipeline settings
catalog = spark.conf.get("catalog")
bronze_schema = spark.conf.get("bronze_schema")
silver_schema = spark.conf.get("silver_schema")

@dlt.table(name="silver_customers")
def silver_customers():
    return (
        dlt.read_stream(f"{catalog}.{bronze_schema}.bronze_customers")
        .select(...)
    )
```

### YAML Configuration

```yaml
resources:
  pipelines:
    silver_pipeline:
      configuration:
        catalog: ${var.catalog}
        bronze_schema: ${var.bronze_schema}
        silver_schema: ${var.silver_schema}
```

---

## Spark Session Handling

### The Pattern

```python
def get_spark_session():
    """Get or create Spark session with proper configuration."""
    from pyspark.sql import SparkSession
    
    spark = (
        SparkSession.builder
        .appName("My Application")
        .getOrCreate()
    )
    
    return spark


def main():
    spark = get_spark_session()
    
    try:
        # Your logic here
        process_data(spark)
        
        print("✅ Job completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
        
    finally:
        # Note: Don't call spark.stop() in Databricks jobs
        # The session is managed by the cluster
        pass


if __name__ == "__main__":
    main()
```

---

## Error Handling Pattern

```python
def robust_job():
    """Job with comprehensive error handling."""
    catalog, schema = get_parameters()
    spark = get_spark_session()
    
    # Track progress
    tables_processed = 0
    errors = []
    
    try:
        # Process tables
        tables = ["dim_customer", "dim_product", "fact_orders"]
        
        for table in tables:
            try:
                process_table(spark, catalog, schema, table)
                tables_processed += 1
                print(f"✓ Processed {table}")
            except Exception as e:
                error_msg = f"Failed to process {table}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Processed: {tables_processed}/{len(tables)} tables")
        
        if errors:
            print(f"Errors ({len(errors)}):")
            for err in errors:
                print(f"  - {err}")
            raise RuntimeError(f"Job completed with {len(errors)} errors")
        
        print("✅ Job completed successfully!")
        
        # Signal success for notebook workflows
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Job failed: {str(e)}")
        dbutils.notebook.exit(f"FAILED: {str(e)}")
        raise
```

---

## Logging Pattern

```python
import logging

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up logging for a job."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    
    return logger


# Usage
logger = setup_logging("gold_merge_job")

logger.info("Starting Gold merge job")
logger.warning("Table has NULL values in key column")
logger.error(f"Failed to process: {error}")
```

---

## Standard Function Signatures

### Job Entry Point

```python
def main():
    """Main entry point for the job."""
    # 1. Get parameters
    catalog, schema = get_parameters()
    
    # 2. Get Spark session
    spark = get_spark_session()
    
    # 3. Execute logic
    try:
        result = process(spark, catalog, schema)
        print(f"✅ Completed: {result}")
        dbutils.notebook.exit("SUCCESS")
    except Exception as e:
        print(f"❌ Failed: {e}")
        dbutils.notebook.exit(f"FAILED: {e}")
        raise
```

### Data Processing Function

```python
def process_table(
    spark: SparkSession,
    catalog: str,
    schema: str,
    table_name: str,
    **kwargs
) -> int:
    """
    Process a single table.
    
    Args:
        spark: Active Spark session
        catalog: Unity Catalog name
        schema: Schema name
        table_name: Table to process
        **kwargs: Additional options
    
    Returns:
        Number of records processed
    
    Raises:
        ValueError: If table doesn't exist
        RuntimeError: If processing fails
    """
    fqn = f"{catalog}.{schema}.{table_name}"
    
    df = spark.table(fqn)
    count = df.count()
    
    # Processing logic...
    
    return count
```

---

## Validation Checklist

### Parameter Handling
- [ ] Uses `dbutils.widgets.get()` (not argparse)
- [ ] Parameters logged for debugging
- [ ] YAML uses `base_parameters` dictionary

### Module Organization
- [ ] Shared code in pure Python files (no notebook header)
- [ ] Entry points are notebooks
- [ ] sys.path setup at top of notebooks needing imports

### Error Handling
- [ ] try/except around main logic
- [ ] Errors logged with context
- [ ] `dbutils.notebook.exit()` for workflow signaling

### Code Quality
- [ ] Functions have docstrings
- [ ] Type hints on function signatures
- [ ] Constants at top of file
- [ ] No hardcoded values

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `arguments are required` | argparse in notebook_task | Use dbutils.widgets.get() |
| `ModuleNotFoundError` | Notebook header in .py file | Remove `# Databricks notebook source` |
| `ModuleNotFoundError` | Missing sys.path | Add sys.path setup block |
| `AttributeError: dbutils` | Running locally | Use try/except with fallback |
| `SparkSession not available` | Outside Spark context | Use get_spark_session() |

---

## Related Documents

- [CI/CD Asset Bundles](20-cicd-asset-bundles.md)
- [Schema Management](22-schema-management.md)
- [Deployment Checklist](../templates/deployment-checklist.md)

---

## References

- [Databricks Notebooks](https://docs.databricks.com/notebooks/)
- [Databricks Widgets](https://docs.databricks.com/notebooks/widgets.html)
- [Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
