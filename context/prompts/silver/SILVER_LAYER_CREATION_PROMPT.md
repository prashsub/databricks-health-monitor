# Silver Layer Creation Prompt

## Quick Reference

**Use this prompt when creating a new Silver layer DLT pipeline in any Databricks project.**

---

## Core Philosophy: Clone + Quality

**⚠️ CRITICAL PRINCIPLE:**

The Silver layer should **essentially clone the source Bronze schema** with minimal transformations:

- ✅ **Same column names** as Bronze (no complex renaming)
- ✅ **Same data types** (minimal type conversions)
- ✅ **Same grain** (no aggregation, that's for Gold)
- ✅ **Add data quality rules** (the main value-add)
- ✅ **Add derived flags** (business indicators like `is_return`, `is_out_of_stock`)
- ✅ **Add business keys** (SHA256 hashes for tracking)
- ✅ **Add timestamps** (`processed_timestamp`)

**What NOT to do in Silver:**
- ❌ Major schema restructuring
- ❌ Aggregations (save for Gold)
- ❌ Complex business logic (simple flags only)
- ❌ Joining across tables (dimension lookups in Gold)

**Why This Matters:**
- Silver is the **validated copy** of source data
- Gold layer handles complex transformations
- Keeps Silver focused on data quality
- Makes troubleshooting easier (column names match source)

---

## Overview

Create a production-grade Databricks Delta Live Tables (DLT) Silver layer with:
- Centralized data quality rules
- Quarantine patterns for invalid records
- Comprehensive monitoring views
- Streaming ingestion from Bronze
- Schema cloning from source

---

## File Structure to Create

```
src/{project}_silver/
├── data_quality_rules.py          # Pure Python (NO notebook header) - centralized DQ rules
├── silver_dimensions.py           # DLT notebook - dimension tables (stores, products, etc.)
├── silver_transactions.py         # DLT notebook - transactional fact table with quarantine
├── silver_inventory.py            # DLT notebook - inventory fact tables (if applicable)
└── data_quality_monitoring.py     # DLT notebook - DQ monitoring views
```

---

## Step 1: Centralized Data Quality Rules

### File: `data_quality_rules.py`

**⚠️ CRITICAL: This MUST be a pure Python file (NOT a Databricks notebook)**

- NO `# Databricks notebook source` header at the top
- Must be importable using standard Python imports
- Contains ALL data quality rules for ALL Silver tables

**Required Functions:**

```python
def get_all_rules():
    """
    Returns all data quality rules with table name, rule name, constraint, and severity.
    
    Returns:
        list: List of dictionaries with keys: table, name, constraint, severity
    """
    return [
        {
            "table": "silver_transactions",
            "name": "valid_transaction_id",
            "constraint": "transaction_id IS NOT NULL AND LENGTH(transaction_id) > 0",
            "severity": "critical"
        },
        {
            "table": "silver_transactions",
            "name": "reasonable_quantity",
            "constraint": "quantity_sold BETWEEN -20 AND 50",
            "severity": "warning"
        },
        # ... more rules
    ]

def get_critical_rules_for_table(table_name):
    """Get critical DQ rules for @dlt.expect_all_or_drop() decorator."""
    all_rules = get_all_rules()
    critical_rules = [r for r in all_rules if r["table"] == table_name and r["severity"] == "critical"]
    return {rule["name"]: rule["constraint"] for rule in critical_rules}

def get_warning_rules_for_table(table_name):
    """Get warning DQ rules for @dlt.expect_all() decorator."""
    all_rules = get_all_rules()
    warning_rules = [r for r in all_rules if r["table"] == table_name and r["severity"] == "warning"]
    return {rule["name"]: rule["constraint"] for rule in warning_rules}

def get_quarantine_condition(table_name):
    """Get SQL condition for quarantine table (inverse of critical rules)."""
    critical_rules = get_critical_rules_for_table(table_name)
    if not critical_rules:
        return "FALSE"
    quarantine_conditions = [f"NOT ({constraint})" for constraint in critical_rules.values()]
    return " OR ".join(quarantine_conditions)
```

**Severity Definitions:**

| Severity | Behavior | Use For | Decorator |
|---|---|---|---|
| `critical` | Record DROPPED/QUARANTINED<br>(pipeline continues) | Primary keys, required dates, referential integrity | `@dlt.expect_all_or_drop()` |
| `warning` | Logged but record passes | Business logic, reasonableness checks, format preferences | `@dlt.expect_all()` |

**Example Rules by Severity:**

```python
# CRITICAL: Must pass or record is quarantined
{
    "table": "silver_transactions",
    "name": "valid_transaction_id",
    "constraint": "transaction_id IS NOT NULL AND LENGTH(transaction_id) > 0",
    "severity": "critical"
},
{
    "table": "silver_transactions",
    "name": "valid_store_number",
    "constraint": "store_number IS NOT NULL",  # FK to dim_store
    "severity": "critical"
},
{
    "table": "silver_transactions",
    "name": "valid_transaction_date",
    "constraint": "transaction_date IS NOT NULL AND transaction_date >= '2020-01-01'",
    "severity": "critical"
},
{
    "table": "silver_transactions",
    "name": "non_zero_quantity",
    "constraint": "quantity_sold != 0",
    "severity": "critical"
},

# WARNING: Logged but record passes through
{
    "table": "silver_transactions",
    "name": "reasonable_quantity",
    "constraint": "quantity_sold BETWEEN -20 AND 50",
    "severity": "warning"
},
{
    "table": "silver_transactions",
    "name": "reasonable_price",
    "constraint": "final_sales_price BETWEEN 0.01 AND 500.00",
    "severity": "warning"
},
{
    "table": "silver_transactions",
    "name": "recent_transaction",
    "constraint": "transaction_date >= CURRENT_DATE() - INTERVAL 365 DAYS",
    "severity": "warning"
}
```

---

## Step 2: DLT Table Helper Function

**Every DLT notebook MUST include this helper at the top:**

```python
def get_bronze_table(table_name):
    """
    Helper function to get fully qualified Bronze table name from DLT configuration.
    
    Supports DLT Direct Publishing Mode - uses catalog/schema from pipeline config.
    
    Args:
        table_name: Name of the Bronze table (e.g., "bronze_transactions")
    
    Returns:
        Fully qualified table name: "{catalog}.{schema}.{table_name}"
    """
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    return f"{catalog}.{bronze_schema}.{table_name}"
```

**Why This Helper?**
- DLT Direct Publishing Mode requires fully qualified table names
- No more `LIVE.` prefix (deprecated pattern)
- Configuration comes from DLT pipeline YAML
- Single source of truth for table references

**Usage:**
```python
dlt.read_stream(get_bronze_table("bronze_transactions"))
# Expands to: catalog.bronze_schema.bronze_transactions
```

---

## Step 3: Standard Silver Table Pattern

### Template for ALL Silver Tables

**Key Principle: Clone Bronze schema + Add DQ rules + Add derived fields**

```python
# Databricks notebook source

"""
{Project} Silver Layer - {Entity Type} Tables with DLT

Delta Live Tables pipeline for Silver {entity_type} tables with:
- Centralized data quality expectations (from data_quality_rules)
- Automatic liquid clustering (cluster_by_auto=True)
- Advanced Delta Lake features (row tracking, deletion vectors)
- Schema cloning from Bronze with minimal transformation
"""

import dlt
from pyspark.sql.functions import col, current_timestamp, sha2, concat_ws, coalesce, when

# Import centralized DQ rules (pure Python module, not notebook)
from data_quality_rules import (
    get_critical_rules_for_table,
    get_warning_rules_for_table
)

# Get configuration from DLT pipeline
def get_bronze_table(table_name):
    """Helper function to get fully qualified Bronze table name from DLT configuration."""
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    return f"{catalog}.{bronze_schema}.{table_name}"


# ============================================================================
# SILVER {ENTITY} TABLE
# ============================================================================

@dlt.table(
    name="silver_{entity}",
    comment="""LLM: Silver layer {entity_description} with comprehensive data quality rules, 
    streaming ingestion, and business rule validation""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "application": "{project_name}",
        "project": "{project_demo}",
        "layer": "silver",
        "source_table": "bronze_{entity}",
        "domain": "{domain}",  # retail, sales, inventory, product, logistics
        "entity_type": "{type}",  # dimension, fact
        "contains_pii": "{true|false}",
        "data_classification": "{confidential|internal}",
        "consumer": "{team}",
        "developer": "edp",
        "support": "edp",
        "business_owner": "{Business Team}",
        "technical_owner": "Data Engineering",
        "business_owner_email": "{email}@company.com",
        "technical_owner_email": "data-engineering@company.com"
    },
    cluster_by_auto=True  # ⚠️ ALWAYS AUTO, never specify columns manually
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_{entity}"))
@dlt.expect_all(get_warning_rules_for_table("silver_{entity}"))
def silver_{entity}():
    """
    Silver {entity} with data quality rules and streaming ingestion.
    
    Schema Strategy: Clone Bronze schema with minimal transformation
    - ✅ Same column names as Bronze
    - ✅ Same data types
    - ✅ Add derived flags (is_*, has_*)
    - ✅ Add business keys (SHA256 hashes)
    - ✅ Add processed_timestamp
    
    Data Quality Rules (centralized in data_quality_rules.py):
    
    CRITICAL (Record DROPPED/QUARANTINED, pipeline continues):
    - {List critical rules - primary keys, required dates, FKs}
    
    WARNING (Logged but record passes through):
    - {List warning rules - business logic, reasonableness}
    
    Pipeline behavior:
    - ✅ Pipeline NEVER FAILS on data quality issues
    - ✅ Records violating CRITICAL rules are QUARANTINED
    - ✅ Records violating WARNING rules pass through (logged)
    """
    return (
        dlt.read_stream(get_bronze_table("bronze_{entity}"))
        
        # ========================================
        # MINIMAL TRANSFORMATIONS (Clone Bronze schema)
        # ========================================
        
        # Add business key (SHA256 hash of natural key)
        .withColumn("{entity}_business_key",
                   sha2(concat_ws("||", col("natural_key1"), col("natural_key2")), 256))
        
        # Add derived boolean flags (simple business indicators)
        .withColumn("is_{flag_name}", 
                   when(col("field") > threshold, True).otherwise(False))
        
        # Add processed timestamp
        .withColumn("processed_timestamp", current_timestamp())
        
        # ========================================
        # AVOID IN SILVER (Save for Gold):
        # - Aggregations
        # - Complex calculations
        # - Joining across tables
        # - Major schema restructuring
        # ========================================
    )
```

### Dimension Table Example

```python
@dlt.table(
    name="silver_store_dim",
    comment="LLM: Silver layer store dimension with validated location data and deduplication",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "bronze_store_dim",
        "domain": "retail",
        "entity_type": "dimension",
        "contains_pii": "true",
        "data_classification": "confidential"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_store_dim"))
@dlt.expect_all(get_warning_rules_for_table("silver_store_dim"))
def silver_store_dim():
    """
    Silver store dimension - clones Bronze schema with validation.
    
    Transformations:
    - ✅ Standardize state code (UPPER, TRIM)
    - ✅ Add business key hash
    - ✅ Add processed timestamp
    - ❌ NO aggregation
    - ❌ NO complex calculations
    """
    return (
        dlt.read_stream(get_bronze_table("bronze_store_dim"))
        .withColumn("state", upper(trim(col("state"))))  # Minimal standardization
        .withColumn("store_business_key", 
                   sha2(concat_ws("||", col("store_number"), col("store_name")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )
```

### Fact Table Example

```python
@dlt.table(
    name="silver_transactions",
    comment="""LLM: Silver layer streaming fact table for transactions with comprehensive 
    data quality rules and quarantine pattern""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "bronze_transactions",
        "domain": "sales",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_transactions"))
@dlt.expect_all(get_warning_rules_for_table("silver_transactions"))
def silver_transactions():
    """
    Silver transactions - clones Bronze with simple derived fields.
    
    Transformations:
    - ✅ Calculate total_discount (sum of discount fields)
    - ✅ Add is_return flag (quantity < 0)
    - ✅ Add business key hash
    - ❌ NO daily aggregation (that's Gold)
    - ❌ NO dimension lookups (that's Gold)
    """
    return (
        dlt.read_stream(get_bronze_table("bronze_transactions"))
        
        # Simple derived fields (single-record calculations only)
        .withColumn("total_discount_amount",
                   coalesce(col("multi_unit_discount"), lit(0)) +
                   coalesce(col("coupon_discount"), lit(0)) +
                   coalesce(col("loyalty_discount"), lit(0)))
        
        # Simple boolean flags
        .withColumn("is_return", when(col("quantity_sold") < 0, True).otherwise(False))
        .withColumn("is_loyalty_transaction", 
                   when(col("loyalty_id").isNotNull(), True).otherwise(False))
        
        # Standard audit fields
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("transaction_business_key",
                   sha2(concat_ws("||", col("transaction_id")), 256))
    )
```

---

## Step 4: Quarantine Table Pattern

**For CRITICAL fact tables, add quarantine to capture invalid records:**

```python
@dlt.table(
    name="silver_{entity}_quarantine",
    comment="""LLM: Quarantine table for {entity} that failed CRITICAL data quality checks. 
    Records here require manual review and remediation before promotion to Silver.""",
    table_properties={
        "quality": "quarantine",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "bronze_{entity}",
        "domain": "{domain}",
        "entity_type": "quarantine",
        "contains_pii": "{inherit_from_main}",
        "data_classification": "{inherit_from_main}"
    },
    cluster_by_auto=True
)
def silver_{entity}_quarantine():
    """
    Quarantine table for records that fail CRITICAL validations.
    
    Uses centralized DQ rules from data_quality_rules.py to automatically
    capture records that fail ANY critical rule.
    
    Pipeline behavior:
    - ✅ Pipeline continues (no failure)
    - ✅ Invalid records captured here
    - ✅ Valid records flow to silver_{entity}
    - ✅ WARNING violations not captured (logged only)
    """
    return (
        dlt.read_stream(get_bronze_table("bronze_{entity}"))
        # Use centralized quarantine condition (inverse of critical rules)
        .filter(get_quarantine_condition("silver_{entity}"))
        .withColumn("quarantine_reason",
            when(col("primary_key").isNull(), "CRITICAL: Missing primary key")
            .when(col("required_date").isNull(), "CRITICAL: Missing required date")
            .when(col("foreign_key").isNull(), "CRITICAL: Missing foreign key")
            .otherwise("CRITICAL: Multiple validation failures"))
        .withColumn("quarantine_timestamp", current_timestamp())
    )
```

**When to Use Quarantine:**
- ✅ High-volume transactional tables (transactions, events)
- ✅ Tables with complex validation rules
- ✅ Tables where you need to track failure patterns
- ❌ Dimension tables (simpler validation, lower volume)
- ❌ Lookup/reference tables

---

## Step 5: Data Quality Monitoring Views

### File: `data_quality_monitoring.py`

Create DLT views to monitor data quality metrics in real-time:

```python
# Databricks notebook source

"""
{Project} Silver Layer - Data Quality Monitoring Views

Delta Live Tables views for monitoring data quality metrics, expectation failures,
and overall pipeline health across the Silver layer.
"""

import dlt
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, min as spark_min, 
    max as spark_max, current_timestamp, lit, when
)

# ============================================================================
# DATA QUALITY METRICS - PER TABLE
# ============================================================================

@dlt.table(
    name="dq_{entity}_metrics",
    comment="""LLM: Real-time data quality metrics for {entity} showing record counts, 
    validation pass rates, quarantine rates, and business rule compliance""",
    table_properties={
        "quality": "monitoring",
        "layer": "silver",
        "pipelines.autoOptimize.managed": "true"
    }
)
def dq_{entity}_metrics():
    """
    Comprehensive data quality metrics for {entity}.
    
    Metrics:
    - Total records processed
    - Records in Silver vs Quarantine
    - Pass/fail rates
    - Business rule violations
    """
    silver = dlt.read("silver_{entity}")
    quarantine = dlt.read("silver_{entity}_quarantine")
    
    # Calculate metrics
    silver_metrics = silver.agg(
        count("*").alias("silver_record_count"),
        # Add entity-specific metrics here
    )
    
    quarantine_metrics = quarantine.agg(
        count("*").alias("quarantine_record_count")
    )
    
    # Combine and calculate rates
    return (
        silver_metrics
        .crossJoin(quarantine_metrics)
        .withColumn("total_records", 
                   col("silver_record_count") + col("quarantine_record_count"))
        .withColumn("silver_pass_rate",
                   (col("silver_record_count") / col("total_records")) * 100)
        .withColumn("quarantine_rate",
                   (col("quarantine_record_count") / col("total_records")) * 100)
        .withColumn("metric_timestamp", current_timestamp())
    )

# ============================================================================
# REFERENTIAL INTEGRITY CHECKS
# ============================================================================

@dlt.table(
    name="dq_referential_integrity",
    comment="""LLM: Referential integrity validation between fact and dimension tables. 
    Identifies orphaned records and missing references.""",
    table_properties={
        "quality": "monitoring",
        "layer": "silver"
    }
)
def dq_referential_integrity():
    """
    Check referential integrity between Silver fact and dimension tables.
    
    Validates:
    - Facts reference valid dimensions
    - No orphaned records
    """
    facts = dlt.read("silver_facts")
    dimensions = dlt.read("silver_dimensions")
    
    # Check for orphaned records
    orphans = (
        facts
        .join(dimensions.select("key"), ["key"], "left_anti")
        .agg(
            lit("facts_to_dimensions").alias("check_name"),
            count("*").alias("orphaned_records")
        )
        .withColumn("status",
                   when(col("orphaned_records") == 0, "PASS")
                   .when(col("orphaned_records") < 10, "WARNING")
                   .otherwise("FAIL"))
        .withColumn("check_timestamp", current_timestamp())
    )
    
    return orphans
```

---

## Step 6: DLT Pipeline Configuration

### File: `resources/silver_dlt_pipeline.yml`

```yaml
resources:
  pipelines:
    silver_dlt_pipeline:
      name: "[${bundle.target}] Silver Layer Pipeline"
      
      # Pipeline root folder (Lakeflow Pipelines Editor best practice)
      # All pipeline assets must be within this root folder
      root_path: ../src/{project}_silver
      
      # DLT Direct Publishing Mode (Modern Pattern)
      # ✅ Use 'schema' field (not 'target' - deprecated)
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      
      # DLT Libraries (Python notebooks or SQL files)
      libraries:
        - notebook:
            path: ../src/{project}_silver/silver_dimensions.py
        - notebook:
            path: ../src/{project}_silver/silver_transactions.py
        - notebook:
            path: ../src/{project}_silver/silver_inventory.py
        - notebook:
            path: ../src/{project}_silver/data_quality_monitoring.py
      
      # Pipeline Configuration (passed to notebooks)
      # Use fully qualified table names in notebooks: {catalog}.{schema}.{table}
      configuration:
        catalog: ${var.catalog}
        bronze_schema: ${var.bronze_schema}
        silver_schema: ${var.silver_schema}
        pipelines.enableTrackHistory: "true"
      
      # Serverless Compute
      serverless: true
      
      # Photon Engine
      photon: true
      
      # Channel (CURRENT = latest features)
      channel: CURRENT
      
      # Continuous vs Triggered
      continuous: false
      
      # Development Mode (faster iteration, auto-recovery)
      development: true
      
      # Edition (ADVANCED for expectations, SCD, etc.)
      edition: ADVANCED
      
      # Notifications
      notifications:
        - alerts:
            - on-update-failure
            - on-update-fatal-failure
            - on-flow-failure
          email_recipients:
            - data-engineering@company.com
      
      # Tags
      tags:
        environment: ${bundle.target}
        project: {project_name}
        layer: silver
        pipeline_type: medallion
        compute_type: serverless
```

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Create `src/{project}_silver/` directory
- [ ] Create `data_quality_rules.py` as **pure Python file** (NO notebook header)
- [ ] Define severity levels: `critical` (drop/quarantine) vs `warning` (log)
- [ ] Add helper functions: `get_critical_rules_for_table()`, `get_warning_rules_for_table()`, `get_quarantine_condition()`

### Phase 2: Data Quality Rules
- [ ] Map Bronze tables to Silver tables (1:1 initially)
- [ ] For each table, define critical rules:
  - [ ] Primary key validation (NOT NULL, LENGTH > 0)
  - [ ] Required date fields (NOT NULL, >= minimum date)
  - [ ] Foreign key fields (NOT NULL for FK columns)
  - [ ] Non-zero checks for quantities/amounts
- [ ] For each table, define warning rules:
  - [ ] Reasonableness checks (quantity ranges, price ranges)
  - [ ] Format checks (UPC length, state code format)
  - [ ] Recency checks (date within last N days)

### Phase 3: DLT Notebooks
- [ ] Create dimension notebooks (e.g., `silver_dimensions.py`)
  - [ ] Add `get_bronze_table()` helper function
  - [ ] Import DQ rules: `from data_quality_rules import ...`
  - [ ] Create table with `@dlt.table()` decorator
  - [ ] Apply critical rules: `@dlt.expect_all_or_drop(get_critical_rules_for_table(...))`
  - [ ] Apply warning rules: `@dlt.expect_all(get_warning_rules_for_table(...))`
  - [ ] Clone Bronze schema with minimal transformations
  - [ ] Add business key, processed_timestamp
  - [ ] Use `cluster_by_auto=True`
  
- [ ] Create fact notebooks (e.g., `silver_transactions.py`)
  - [ ] Same steps as dimensions
  - [ ] Add derived boolean flags (is_return, is_loyalty, etc.)
  - [ ] Create quarantine table using `get_quarantine_condition()`
  - [ ] Add quarantine_reason, quarantine_timestamp

### Phase 4: Monitoring
- [ ] Create `data_quality_monitoring.py`
- [ ] Add DQ metrics view per table
- [ ] Add referential integrity checks
- [ ] Add data freshness monitoring

### Phase 5: Pipeline Configuration
- [ ] Create `resources/silver_dlt_pipeline.yml`
- [ ] Set `root_path` to `../src/{project}_silver`
- [ ] Use `catalog` + `schema` fields (Direct Publishing Mode)
- [ ] Add all notebook libraries
- [ ] Pass configuration: catalog, bronze_schema, silver_schema
- [ ] Set `serverless: true`, `edition: ADVANCED`
- [ ] Configure notifications

### Phase 6: Testing
- [ ] Validate `data_quality_rules.py` has no notebook header
- [ ] Test import: `from data_quality_rules import get_all_rules`
- [ ] Deploy DLT pipeline: `databricks bundle deploy -t dev`
- [ ] Trigger pipeline: `databricks pipelines start-update --pipeline-name "[dev] Silver Layer Pipeline"`
- [ ] Verify Silver tables created
- [ ] Check quarantine table has failed records
- [ ] Review DQ metrics views

---

## Key Principles

### 1. Schema Cloning (Silver = Bronze + DQ)
- ✅ Keep same column names as Bronze
- ✅ Keep same data types
- ✅ Add data quality rules (main value-add)
- ✅ Add simple derived flags
- ❌ No complex transformations (save for Gold)
- ❌ No aggregations (save for Gold)
- ❌ No joins (save for Gold)

### 2. Pipeline Never Fails
- ✅ Critical rules drop/quarantine records, pipeline continues
- ✅ Warning rules log violations, records pass through
- ✅ No `@dlt.expect_or_fail()` - use `@dlt.expect_all_or_drop()` instead

### 3. Centralized Rules
- ✅ Single source of truth: `data_quality_rules.py`
- ✅ Zero duplication across notebooks
- ✅ Easy to audit and update

### 4. Pure Python for Shared Code
- ✅ Rules file must be importable (NO notebook header)
- ✅ Use standard Python imports
- ✅ Works with DLT ADVANCED edition

### 5. Auto Clustering
- ✅ Always `cluster_by_auto=True`
- ❌ Never specify columns manually
- ✅ Delta automatically optimizes

### 6. Governance First
- ✅ Complete table properties on every table
- ✅ Include: layer, domain, entity_type, contains_pii, data_classification
- ✅ Business owner + Technical owner

### 7. Business Keys
- ✅ Generate SHA256 hashes for tracking
- ✅ Use `sha2(concat_ws("||", col("key1"), col("key2")), 256)`
- ✅ Named: `{entity}_business_key`

### 8. Direct Publishing Mode
- ✅ Use fully qualified table names
- ✅ Helper: `get_bronze_table(table_name)`
- ✅ Configure: `catalog` + `schema` in YAML
- ❌ No `LIVE.` prefix (deprecated)

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Notebook Header in Rules File
```python
# data_quality_rules.py
# Databricks notebook source  # ❌ Makes it a notebook, breaks imports!

def get_all_rules():
    return [...]
```
**Fix:** Remove `# Databricks notebook source` line

### ❌ Mistake 2: Complex Transformations in Silver
```python
# ❌ WRONG: Aggregation belongs in Gold
def silver_sales_daily():
    return (
        dlt.read_stream(get_bronze_table("bronze_transactions"))
        .groupBy("store_number", "transaction_date")  # ❌ Aggregation!
        .agg(sum("revenue").alias("daily_revenue"))
    )
```
**Fix:** Keep Silver at transaction grain, aggregate in Gold

### ❌ Mistake 3: Manual Clustering Columns
```python
# ❌ WRONG: Manual clustering
@dlt.table(
    cluster_by=["store_number", "transaction_date"]  # ❌ Don't specify!
)
```
**Fix:** Always use `cluster_by_auto=True`

### ❌ Mistake 4: Using expect_or_fail
```python
# ❌ WRONG: Pipeline fails on bad data
@dlt.expect_or_fail("valid_id", "id IS NOT NULL")
```
**Fix:** Use `@dlt.expect_all_or_drop()` for critical rules

### ❌ Mistake 5: Not Using Centralized Rules
```python
# ❌ WRONG: Hardcoded rules in notebook
@dlt.expect_or_drop("valid_id", "id IS NOT NULL")
@dlt.expect_or_drop("valid_date", "date IS NOT NULL")
```
**Fix:** Import from `data_quality_rules.py`

---

## References

### Official Databricks Documentation
- [DLT Expectations](https://docs.databricks.com/aws/en/dlt/expectations)
- [DLT Expectation Patterns](https://docs.databricks.com/aws/en/dlt/expectation-patterns)
- [Share Code Between Notebooks](https://docs.databricks.com/aws/en/notebooks/share-code)
- [Automatic Clustering](https://docs.databricks.com/aws/en/delta/clustering#enable-or-disable-automatic-liquid-clustering)

### Project Documentation
- [DQ Critical vs Warning Implementation](./DQ_CRITICAL_WARNING_IMPLEMENTATION.md)
- [DQ Monitoring Views Guide](./DQ_MONITORING_VIEWS_GUIDE.md)
- [Silver Layer README](./SILVER_LAYER_README.md)

---

## Summary: What to Create

1. **`data_quality_rules.py`** (pure Python) - Centralized DQ rules
2. **`silver_dimensions.py`** (DLT notebook) - Dimension tables
3. **`silver_transactions.py`** (DLT notebook) - Fact tables with quarantine
4. **`silver_inventory.py`** (DLT notebook, optional) - Additional fact tables
5. **`data_quality_monitoring.py`** (DLT notebook) - Monitoring views
6. **`resources/silver_dlt_pipeline.yml`** - Pipeline configuration

**Core Philosophy:** Silver = Bronze schema clone + Data quality validation

**Time Estimate:** 2-4 hours for initial setup, 1 hour per additional table

