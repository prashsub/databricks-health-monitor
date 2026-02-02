# Bronze Layer Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-DP-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Data Engineering Team |
| **Status** | Approved |

---

## Executive Summary

The Bronze layer is the raw data landing zone in our Medallion Architecture. This document defines patterns for Bronze table creation, synthetic data generation for development, and proper configuration for downstream streaming.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| DP-01 | Medallion Architecture required | 🔴 Critical |
| DP-02 | CDF enabled on Bronze tables | 🟡 Required |
| PA-02 | All tables use Delta Lake | 🔴 Critical |
| PA-08 | LLM-friendly table COMMENTs | 🟡 Required |

---

## Bronze Layer Purpose

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               BRONZE LAYER                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                        DATA SOURCES                                         │  │
│   │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               │  │
│   │  │  APIs  │  │  Files │  │  DBs   │  │ Streams│  │ Events │               │  │
│   │  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘               │  │
│   └──────┼───────────┼───────────┼───────────┼───────────┼──────────────────────┘  │
│          │           │           │           │           │                          │
│          └───────────┴───────────┴───────────┴───────────┘                          │
│                                  │                                                  │
│                                  ▼                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                     BRONZE TABLES (Raw Landing)                             │  │
│   │                                                                             │  │
│   │  • Append-only ingestion (no updates)                                       │  │
│   │  • Preserve source schema                                                   │  │
│   │  • Add processing metadata (timestamp, source)                              │  │
│   │  • Enable CDF for incremental Silver                                        │  │
│   │  • Minimal transformation                                                   │  │
│   │                                                                             │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                  │                                                  │
│                                  │ CDF (Change Data Feed)                          │
│                                  ▼                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                        SILVER LAYER (DLT Streaming)                         │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Rule DP-02: CDF Enabled on Bronze

### Why CDF?

Change Data Feed enables Silver layer to stream changes incrementally instead of full table scans.

```sql
-- ✅ CORRECT: CDF enabled
CREATE TABLE catalog.bronze.orders (
    ...
)
USING DELTA
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true'  -- Required for Silver streaming
);

-- In Silver DLT pipeline:
dlt.read_stream("bronze_orders")  -- Reads only new changes via CDF
```

---

## Bronze Table Template

```sql
-- ============================================================================
-- Bronze Table: {table_name}
-- Source: {source_system}
-- Description: {brief description}
-- ============================================================================

CREATE OR REPLACE TABLE ${catalog}.${bronze_schema}.bronze_{table_name} (
    -- Business columns (preserve source schema)
    {column_name} {data_type} COMMENT '{description}',
    ...
    
    -- Processing metadata (always include)
    processed_timestamp TIMESTAMP NOT NULL 
        COMMENT 'When this record was ingested into Bronze layer',
    source_file STRING 
        COMMENT 'Source file or API endpoint that provided this record',
    batch_id STRING 
        COMMENT 'Batch identifier for this ingestion run'
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
    -- Required for Silver streaming
    'delta.enableChangeDataFeed' = 'true',
    
    -- Optimization
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    
    -- Governance tags
    'layer' = 'bronze',
    'source_system' = '{source_name}',
    'domain' = '{domain}',
    'contains_pii' = '{true|false}',
    'data_classification' = '{confidential|internal}'
)
COMMENT 'Bronze layer table for {entity}. Raw data from {source}. CDF enabled for Silver streaming.';
```

---

## Standard Bronze Tables

### Dimension Source Tables

```python
def create_bronze_dimension(
    spark,
    catalog: str,
    schema: str,
    table_name: str,
    columns: list,
    source_system: str,
    domain: str
):
    """Create Bronze dimension table following standards."""
    
    # Build column definitions
    col_defs = []
    for col in columns:
        col_defs.append(f"{col['name']} {col['type']} COMMENT '{col['description']}'")
    
    # Add standard metadata columns
    col_defs.extend([
        "processed_timestamp TIMESTAMP NOT NULL COMMENT 'Ingestion timestamp'",
        "source_file STRING COMMENT 'Source file path'",
        "batch_id STRING COMMENT 'Batch identifier'"
    ])
    
    columns_sql = ",\n    ".join(col_defs)
    
    ddl = f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.bronze_{table_name} (
            {columns_sql}
        )
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = '{source_system}',
            'domain' = '{domain}'
        )
        COMMENT 'Bronze dimension table for {table_name} from {source_system}.'
    """
    
    spark.sql(ddl)
    print(f"✓ Created {catalog}.{schema}.bronze_{table_name}")
```

### Fact Source Tables

```python
def create_bronze_fact(
    spark,
    catalog: str,
    schema: str,
    table_name: str,
    columns: list,
    source_system: str,
    domain: str
):
    """Create Bronze fact table following standards."""
    
    col_defs = []
    for col in columns:
        col_defs.append(f"{col['name']} {col['type']} COMMENT '{col['description']}'")
    
    col_defs.extend([
        "processed_timestamp TIMESTAMP NOT NULL COMMENT 'Ingestion timestamp'",
        "source_file STRING COMMENT 'Source file path'",
        "batch_id STRING COMMENT 'Batch identifier'"
    ])
    
    columns_sql = ",\n    ".join(col_defs)
    
    ddl = f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.bronze_{table_name} (
            {columns_sql}
        )
        USING DELTA
        CLUSTER BY AUTO
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'bronze',
            'source_system' = '{source_system}',
            'domain' = '{domain}',
            'entity_type' = 'fact'
        )
        COMMENT 'Bronze fact table for {table_name} from {source_system}. High volume transactional data.'
    """
    
    spark.sql(ddl)
    print(f"✓ Created {catalog}.{schema}.bronze_{table_name}")
```

---

## Synthetic Data Generation (Faker)

### Why Faker?

For development and testing, we use Faker to generate realistic synthetic data that exercises all code paths including edge cases.

### Installation

```yaml
# In Asset Bundle YAML
environments:
  - environment_key: default
    spec:
      environment_version: "4"
      dependencies:
        - "Faker==22.0.0"
```

### Standard Data Generator

```python
from faker import Faker
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random


def generate_bronze_customers(spark, num_records: int):
    """
    Generate synthetic customer data for Bronze layer.
    
    Includes:
    - Valid records (majority)
    - Edge cases (nulls, empty strings)
    - Invalid data (~5% for testing DLT expectations)
    """
    fake = Faker()
    Faker.seed(42)  # Reproducible data
    
    customers = []
    for i in range(num_records):
        # Determine record quality
        is_invalid = random.random() < 0.05  # 5% invalid
        is_edge_case = random.random() < 0.10  # 10% edge cases
        
        customer = {
            "customer_id": f"CUST-{i:08d}",
            "email": None if is_invalid else fake.email(),
            "first_name": "" if is_edge_case else fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.phone_number() if not is_edge_case else None,
            "address": fake.address().replace('\n', ', '),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode(),
            "country": "US",
            "created_date": fake.date_between(start_date="-3y", end_date="today"),
            "is_active": True if not is_invalid else None,
            "segment": random.choice(["premium", "standard", "basic"]),
            "processed_timestamp": datetime.now(),
            "source_file": f"s3://landing/customers/batch_{datetime.now():%Y%m%d}.parquet",
            "batch_id": f"batch_{datetime.now():%Y%m%d%H%M%S}"
        }
        customers.append(customer)
    
    schema = StructType([
        StructField("customer_id", StringType(), False),
        StructField("email", StringType(), True),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("address", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zip_code", StringType(), True),
        StructField("country", StringType(), True),
        StructField("created_date", DateType(), True),
        StructField("is_active", BooleanType(), True),
        StructField("segment", StringType(), True),
        StructField("processed_timestamp", TimestampType(), False),
        StructField("source_file", StringType(), True),
        StructField("batch_id", StringType(), True),
    ])
    
    return spark.createDataFrame(customers, schema)


def generate_bronze_orders(spark, num_records: int, customer_ids: list):
    """
    Generate synthetic order data for Bronze layer.
    
    Includes referential integrity to customers.
    """
    fake = Faker()
    Faker.seed(42)
    
    orders = []
    for i in range(num_records):
        is_invalid = random.random() < 0.05
        
        order = {
            "order_id": f"ORD-{i:010d}",
            "customer_id": random.choice(customer_ids),
            "order_date": fake.date_between(start_date="-90d", end_date="today"),
            "product_id": f"PROD-{random.randint(1, 500):05d}",
            "quantity": 0 if is_invalid else random.randint(1, 10),
            "unit_price": -10.0 if is_invalid else round(random.uniform(10, 500), 2),
            "discount_pct": round(random.uniform(0, 0.3), 2),
            "channel": random.choice(["web", "mobile", "store", "phone"]),
            "status": random.choice(["completed", "pending", "cancelled", "returned"]),
            "processed_timestamp": datetime.now(),
            "source_file": f"s3://landing/orders/batch_{datetime.now():%Y%m%d}.parquet",
            "batch_id": f"batch_{datetime.now():%Y%m%d%H%M%S}"
        }
        orders.append(order)
    
    schema = StructType([
        StructField("order_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("order_date", DateType(), False),
        StructField("product_id", StringType(), False),
        StructField("quantity", IntegerType(), True),
        StructField("unit_price", DoubleType(), True),
        StructField("discount_pct", DoubleType(), True),
        StructField("channel", StringType(), True),
        StructField("status", StringType(), True),
        StructField("processed_timestamp", TimestampType(), False),
        StructField("source_file", StringType(), True),
        StructField("batch_id", StringType(), True),
    ])
    
    return spark.createDataFrame(orders, schema)
```

### Data Quality Test Patterns

```python
def add_test_scenarios(df, column_name: str, test_pct: float = 0.05):
    """
    Add specific test scenarios to generated data.
    
    Test scenarios:
    - NULL values
    - Empty strings
    - Boundary values
    - Invalid formats
    """
    from pyspark.sql.functions import when, rand, lit
    
    return (
        df
        .withColumn(
            column_name,
            when(rand() < test_pct, lit(None))  # NULL
            .when(rand() < test_pct * 2, lit(""))  # Empty
            .otherwise(col(column_name))
        )
    )
```

---

## Ingestion Patterns

### Batch Ingestion

```python
def ingest_batch(
    spark,
    source_path: str,
    target_table: str,
    batch_id: str
):
    """
    Batch ingestion pattern for Bronze layer.
    
    Always append (never overwrite) to preserve history.
    """
    from pyspark.sql.functions import current_timestamp, lit
    
    # Read source data
    df = spark.read.parquet(source_path)
    
    # Add metadata
    df = (
        df
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("source_file", lit(source_path))
        .withColumn("batch_id", lit(batch_id))
    )
    
    # Append to Bronze (never overwrite!)
    df.write.mode("append").saveAsTable(target_table)
    
    count = df.count()
    print(f"✓ Ingested {count} records to {target_table}")
    
    return count
```

### Auto Loader (Streaming Files)

```python
def setup_autoloader(
    spark,
    source_path: str,
    target_table: str,
    checkpoint_path: str,
    file_format: str = "parquet"
):
    """
    Auto Loader for continuous file ingestion.
    """
    from pyspark.sql.functions import current_timestamp, input_file_name
    
    stream = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", file_format)
        .option("cloudFiles.schemaLocation", f"{checkpoint_path}/schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .load(source_path)
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("source_file", input_file_name())
    )
    
    query = (
        stream.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{checkpoint_path}/checkpoint")
        .trigger(availableNow=True)  # Process all available, then stop
        .toTable(target_table)
    )
    
    return query
```

---

## Validation Checklist

### Table Creation
- [ ] Table uses Delta Lake format
- [ ] CDF enabled (`delta.enableChangeDataFeed = true`)
- [ ] CLUSTER BY AUTO applied
- [ ] All required TBLPROPERTIES set
- [ ] Table has COMMENT with business context
- [ ] All columns have COMMENT

### Metadata Columns
- [ ] `processed_timestamp` column exists
- [ ] `source_file` column exists
- [ ] `batch_id` column exists

### Synthetic Data
- [ ] ~5% invalid data for testing
- [ ] ~10% edge cases (nulls, empty)
- [ ] Referential integrity maintained
- [ ] Faker seed set for reproducibility

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Silver DLT fails to read | CDF not enabled | Enable CDF on Bronze table |
| Data loss | Using overwrite mode | Always use append mode |
| Schema evolution errors | Auto Loader schema drift | Configure schema hints |
| Slow ingestion | No optimization | Enable auto-optimize properties |

---

## Related Documents

- [Silver Layer Patterns](11-silver-layer-patterns.md)
- [Gold Layer Patterns](12-gold-layer-patterns.md)
- [Asset Bundle Standards](../../platform-architecture/20-cicd-asset-bundles.md)

---

## References

- [Delta Lake](https://docs.delta.io/)
- [Change Data Feed](https://docs.databricks.com/delta/delta-change-data-feed.html)
- [Auto Loader](https://docs.databricks.com/ingestion/auto-loader/)
- [Faker Library](https://faker.readthedocs.io/)
