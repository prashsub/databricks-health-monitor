# Gold Layer Development Standards

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | DA-01 through DA-08 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Data Engineering Team |
| **Status** | Approved |

---

## Executive Summary

The Gold layer contains business-ready, dimensional data models optimized for analytics and consumption. This document defines the mandatory patterns for Gold layer development including YAML-driven table creation, MERGE deduplication, constraint management, and LLM-friendly documentation.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| DA-01 | Gold tables must define PK/FK constraints | 🔴 Critical |
| DA-02 | Schema must be extracted from YAML (never generated) | 🔴 Critical |
| DA-05 | Surrogate keys generated via MD5 hash | 🟡 Required |
| DA-06 | Always deduplicate before MERGE | 🔴 Critical |
| DA-07 | SCD Type 2 for historical dimensions | 🟡 Required |
| DA-08 | LLM-friendly dual-purpose documentation | 🟡 Required |

---

## Rule DA-02: YAML-Driven Schema Management

### The Principle: Extract, Don't Generate

**ALWAYS extract table/column names from YAML source files. NEVER generate them from memory.**

**Why This Matters:**
- Generation leads to hallucinations (inventing non-existent columns)
- Typos cause runtime failures
- Schema mismatches between layers
- Broken references to tables, columns, functions

### Source of Truth Hierarchy

| Priority | Source | Location | Use For |
|----------|--------|----------|---------|
| 1 | Gold YAML | `gold_layer_design/yaml/{domain}/` | Table names, columns, types, constraints |
| 2 | Silver Schema | `DESCRIBE TABLE` or `df.columns` | Available source columns |
| 3 | System Tables | `system.information_schema.columns` | Verification |

### Standard YAML Schema Structure

```yaml
# gold_layer_design/yaml/billing/fact_usage.yaml
table_name: fact_usage
comment: "Fact table for daily usage metrics..."

primary_key:
  columns: ['usage_id']
  
foreign_keys:
  - columns: ['workspace_id']
    references: 'catalog.gold.dim_workspace'
    ref_columns: ['workspace_id']
  - columns: ['sku_id']
    references: 'catalog.gold.dim_sku'
    ref_columns: ['sku_id']

columns:
  - name: usage_id
    type: STRING
    nullable: false
    description: "Unique identifier for usage record. MD5 hash of workspace_id + date + sku."
  
  - name: workspace_id
    type: STRING
    nullable: false
    description: "Foreign key to dim_workspace."
  
  - name: usage_date
    type: DATE
    nullable: false
    description: "Date of usage. Grain is one row per workspace-date-sku."
  
  - name: dbus_consumed
    type: DECIMAL(18,6)
    nullable: true
    description: "Total DBUs consumed for the day."
```

### Extraction Code Patterns

#### Pattern 1: Extract Gold Table Schema

```python
import yaml
from pathlib import Path
from typing import Dict, List

def get_gold_schema(domain: str, table_name: str) -> Dict:
    """
    Extract Gold table schema from YAML (single source of truth).
    
    ALWAYS use this instead of hardcoding column lists.
    """
    yaml_file = Path(f"gold_layer_design/yaml/{domain}/{table_name}.yaml")
    
    if not yaml_file.exists():
        raise FileNotFoundError(
            f"Gold YAML not found: {yaml_file}\n"
            f"Cannot proceed without schema definition."
        )
    
    with open(yaml_file) as f:
        schema = yaml.safe_load(f)
    
    return schema

# ✅ CORRECT: Extract actual Gold schema
gold_schema = get_gold_schema("billing", "fact_usage")
gold_columns = [col['name'] for col in gold_schema['columns']]
print(f"Gold table expects {len(gold_columns)} columns: {gold_columns}")

# ❌ WRONG: Hardcode column list
gold_columns = ["usage_date", "workspace_id", "dbus"] # Might be wrong!
```

#### Pattern 2: Build DDL from YAML

```python
def build_create_table_ddl(config: Dict, catalog: str, schema: str) -> str:
    """
    Build CREATE TABLE DDL from YAML configuration.
    
    This ensures DDL always matches the single source of truth.
    """
    table_name = config['table_name']
    columns = config['columns']
    
    # Build column definitions
    column_defs = []
    for col in columns:
        nullable = "" if col.get('nullable', True) else "NOT NULL"
        desc = col.get('description', '').replace("'", "''")
        comment = f"COMMENT '{desc}'" if desc else ""
        column_defs.append(f"    {col['name']} {col['type']} {nullable} {comment}")
    
    columns_sql = ",\n".join(column_defs)
    
    ddl = f"""
CREATE OR REPLACE TABLE {catalog}.{schema}.{table_name} (
{columns_sql}
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'layer' = 'gold'
)
COMMENT '{config.get('comment', '')}'
    """
    
    return ddl

# Usage
config = get_gold_schema("billing", "fact_usage")
ddl = build_create_table_ddl(config, "my_catalog", "gold")
spark.sql(ddl)
```

#### Pattern 3: Validate Merge Readiness

```python
def validate_merge_readiness(
    spark,
    catalog: str,
    silver_schema: str,
    silver_table: str,
    domain: str,
    gold_table: str,
    manual_mappings: Dict[str, str] = None
) -> bool:
    """
    Validate that merge can proceed without column errors.
    
    ALWAYS run this before writing merge code.
    """
    manual_mappings = manual_mappings or {}
    
    # Extract actual schemas
    silver_df = spark.table(f"{catalog}.{silver_schema}.{silver_table}")
    silver_columns = set(silver_df.columns)
    
    gold_config = get_gold_schema(domain, gold_table)
    gold_columns = {col['name'] for col in gold_config['columns']}
    
    # Build complete mapping
    direct_matches = silver_columns & gold_columns
    all_mappings = {col: col for col in direct_matches}
    all_mappings.update(manual_mappings)
    
    # Derived columns (calculated in code, not from Silver)
    derived = {'record_created_timestamp', 'record_updated_timestamp', 
               'effective_from', 'effective_to', 'is_current'}
    
    # Check coverage
    unmapped = gold_columns - set(all_mappings.values()) - derived
    
    if unmapped:
        print(f"❌ VALIDATION FAILED")
        print(f"Unmapped Gold columns: {unmapped}")
        return False
    
    print(f"✅ VALIDATION PASSED")
    return True
```

---

## Rule DA-06: Delta MERGE Deduplication

### The Principle: Always Deduplicate Before MERGE

**Why This Matters:**

Delta Lake throws `[DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE]` when multiple source rows match a single target row. This happens when Silver data has duplicates.

### The Pattern

```python
def merge_with_deduplication(
    spark,
    silver_table: str,
    gold_table: str,
    business_key: str,
    timestamp_column: str = "processed_timestamp"
):
    """
    CRITICAL: Always deduplicate Silver source before MERGE.
    
    This pattern keeps the LATEST record per business key.
    """
    from pyspark.sql.functions import col
    from delta.tables import DeltaTable
    
    # Step 1: Read Silver data
    silver_raw = spark.table(silver_table)
    
    # Step 2: DEDUPLICATE - Keep latest record per business key
    silver_df = (
        silver_raw
        .orderBy(col(timestamp_column).desc())  # Latest first
        .dropDuplicates([business_key])  # Keep only first (latest)
    )
    
    # Step 3: Get Gold table
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    # Step 4: MERGE
    delta_gold.alias("target").merge(
        silver_df.alias("source"),
        f"target.{business_key} = source.{business_key}"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = silver_df.count()
    print(f"✓ Merged {record_count} deduplicated records")
```

### Critical Rule: Deduplication Key = MERGE Key

The deduplication key MUST match the MERGE condition key:

```python
# ✅ CORRECT: Same key for dedup and merge
silver_df = silver_raw.orderBy(col("processed_timestamp").desc()).dropDuplicates(["store_number"])
delta_gold.merge(silver_df, "target.store_number = source.store_number")

# ❌ WRONG: Different keys causes unexpected behavior
silver_df = silver_raw.dropDuplicates(["store_id"])  # Dedup by store_id
delta_gold.merge(silver_df, "target.store_number = source.store_number")  # Merge by store_number
```

### Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| `DELTA_MULTIPLE_SOURCE_ROW_MATCHING` | Missing deduplication | Add `orderBy().dropDuplicates()` |
| Duplicate records in Gold | Dedup key ≠ merge key | Align keys |
| Wrong records selected | Ordering incorrect | Use `desc()` to keep latest |
| More rows in Gold than expected | Dedup on wrong columns | Verify business key definition |

---

## Rule DA-01: PK/FK Constraints

### The Principle: Define Relational Integrity

Gold tables MUST declare PRIMARY KEY and FOREIGN KEY constraints for:
- Documentation of data model
- Query optimization hints
- Lineage tracking

### Implementation Pattern

**CRITICAL: Never define FK constraints inline in CREATE TABLE.** FKs reference other tables' PKs, which may not exist yet.

```python
def apply_constraints(spark, catalog: str, schema: str):
    """
    Apply constraints AFTER all tables are created.
    
    Order: 1) Create all tables, 2) Apply all constraints
    """
    # Step 1: Apply Primary Keys first
    spark.sql(f"""
        ALTER TABLE {catalog}.{schema}.dim_workspace
        ADD CONSTRAINT pk_dim_workspace 
        PRIMARY KEY (workspace_id) NOT ENFORCED
    """)
    
    spark.sql(f"""
        ALTER TABLE {catalog}.{schema}.fact_usage
        ADD CONSTRAINT pk_fact_usage 
        PRIMARY KEY (usage_id) NOT ENFORCED
    """)
    
    # Step 2: Apply Foreign Keys (PKs now exist)
    spark.sql(f"""
        ALTER TABLE {catalog}.{schema}.fact_usage
        ADD CONSTRAINT fk_usage_workspace 
        FOREIGN KEY (workspace_id) 
        REFERENCES {catalog}.{schema}.dim_workspace(workspace_id) 
        NOT ENFORCED
    """)

# Call after all tables created
create_all_gold_tables(spark, catalog, schema)
apply_constraints(spark, catalog, schema)  # Separate step!
```

### Constraint Automation from YAML

```python
def apply_fk_constraints_from_yaml(spark, catalog: str, schema: str, domain: str):
    """
    Extract FK definitions from YAML and apply them.
    """
    yaml_dir = Path(f"gold_layer_design/yaml/{domain}")
    
    for yaml_file in yaml_dir.glob("*.yaml"):
        config = yaml.safe_load(open(yaml_file))
        table_name = config['table_name']
        
        for fk in config.get('foreign_keys', []):
            fk_name = f"fk_{table_name}_{fk['columns'][0]}"
            
            spark.sql(f"""
                ALTER TABLE {catalog}.{schema}.{table_name}
                ADD CONSTRAINT {fk_name}
                FOREIGN KEY ({', '.join(fk['columns'])})
                REFERENCES {fk['references']}({', '.join(fk['ref_columns'])})
                NOT ENFORCED
            """)
```

---

## Rule DA-05: Surrogate Key Generation

### Pattern: MD5 Hash for Surrogate Keys

```python
from pyspark.sql.functions import md5, concat_ws, col

def generate_surrogate_key(df, key_columns: list, key_name: str = "surrogate_key"):
    """
    Generate deterministic surrogate key from business columns.
    
    Uses MD5 hash for consistency and reproducibility.
    """
    return df.withColumn(
        key_name,
        md5(concat_ws("||", *[col(c) for c in key_columns]))
    )

# Dimension tables: business key + effective timestamp (SCD2)
dim_df = generate_surrogate_key(
    dim_df, 
    ["store_number", "effective_from"],
    "store_key"
)

# Fact tables: all grain columns
fact_df = generate_surrogate_key(
    fact_df,
    ["workspace_id", "usage_date", "sku_id"],
    "usage_id"
)
```

---

## Rule DA-07: SCD Type 2 Patterns

### Dimension Table Pattern

```python
def merge_scd2_dimension(
    spark,
    silver_table: str,
    gold_table: str,
    business_key: str
):
    """
    SCD Type 2 MERGE pattern for tracking historical changes.
    """
    from pyspark.sql.functions import current_timestamp, lit
    
    silver_df = spark.table(silver_table)
    
    updates_df = (
        silver_df
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates([business_key])
        # Generate surrogate key
        .withColumn("surrogate_key", 
                   md5(concat_ws("||", col(business_key), col("processed_timestamp"))))
        # SCD2 columns
        .withColumn("effective_from", col("processed_timestamp"))
        .withColumn("effective_to", lit(None).cast("timestamp"))
        .withColumn("is_current", lit(True))
        # Audit columns
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
    )
    
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    # SCD2: Only update timestamp for current records
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        f"target.{business_key} = source.{business_key} AND target.is_current = true"
    ).whenMatchedUpdate(set={
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
```

---

## Rule DA-08: LLM-Friendly Documentation

### Dual-Purpose Comment Pattern

Every Gold table and column MUST have comprehensive documentation that serves both:
1. **Business users** - Understanding what the data means
2. **LLMs/Genie** - Automated query generation

### Table Comment Pattern

```
[Natural description]. Business: [context and use cases]. Technical: [implementation details].
```

**Example:**
```sql
COMMENT 'Gold layer daily usage fact table with consumption metrics at workspace-SKU-day grain. Business: Primary source for billing analytics, cost optimization, and usage trending. Used by finance dashboards and cost allocation reports. Technical: Grain is one row per workspace-SKU-date combination. Pre-aggregated from Silver transactions. Surrogate key is MD5 hash of grain columns.'
```

### Column Comment Pattern

```
[Definition]. Business: [purpose and business rules]. Technical: [data type, format, calculation, constraints].
```

**Example:**
```sql
workspace_id STRING NOT NULL COMMENT 'Foreign key to dim_workspace identifying the Databricks workspace. Business: Primary dimension for cost allocation and access control grouping. Technical: Matches workspace_id in dim_workspace. Immutable after creation.'

total_dbus DECIMAL(18,6) COMMENT 'Total DBUs consumed for the day. Business: Primary consumption metric for billing and capacity planning. Technical: Sum of all DBU usage from transactions. May include both committed and on-demand consumption.'
```

### Automated Documentation from YAML

```python
def generate_table_comment(config: Dict) -> str:
    """Generate LLM-friendly table comment from YAML config."""
    name = config['table_name']
    desc = config.get('description', config.get('comment', ''))
    
    # Extract grain from primary key
    pk_cols = config.get('primary_key', {}).get('columns', [])
    grain = ', '.join(pk_cols) if pk_cols else 'undefined'
    
    return f"{desc} Technical: Grain is ({grain}). Managed via YAML-driven setup."
```

---

## Validation Checklist

### Pre-Development
- [ ] Gold YAML exists for the table
- [ ] All columns defined with types and descriptions
- [ ] Primary key specified
- [ ] Foreign keys reference existing tables
- [ ] Silver source table verified

### Pre-Merge
- [ ] Schema validation script passed
- [ ] Deduplication key matches MERGE key
- [ ] All Gold columns mapped (direct, manual, or derived)
- [ ] SCD2 columns included if dimension

### Post-Deployment
- [ ] Table has COMMENT
- [ ] All columns have COMMENT
- [ ] PK constraint applied
- [ ] FK constraints applied (after PKs exist)
- [ ] Layer tag set to 'gold'

---

## Common Errors and Solutions

| Error | Root Cause | Solution |
|-------|------------|----------|
| `Column 'X' does not exist` | Generated column name | Extract from YAML |
| `DELTA_MULTIPLE_SOURCE_ROW_MATCHING` | Missing deduplication | Add `orderBy().dropDuplicates()` |
| `Table does not have a primary key` | FK before PK | Apply PKs first |
| `Cannot resolve column` | Silver/Gold mismatch | Run validation script |

---

## Related Documents

- [Medallion Architecture](../part1-platform-foundations/03-medallion-architecture.md)
- [Silver Layer Standards](11-silver-layer-standards.md)
- [YAML-Driven Setup](../../.cursor/rules/gold/25-yaml-driven-gold-setup.mdc) (detailed patterns)
- [Delta MERGE Deduplication](../../.cursor/rules/gold/11-gold-delta-merge-deduplication.mdc) (detailed patterns)

---

## References

- [Delta Lake MERGE](https://docs.delta.io/latest/delta-update.html)
- [SCD Type 2 Patterns](https://www.databricks.com/blog/dimensional-modeling-delta-lake)
- [Unity Catalog Constraints](https://docs.databricks.com/tables/constraints)
