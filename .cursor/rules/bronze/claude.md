# Bronze Layer Rules for Claude Code

This file combines all Bronze layer cursor rules for use by Claude Code.

---

## Faker Data Generation Patterns

### Core Principles

1. **Realistic Data**: Generate realistic-looking data that represents business scenarios
2. **Referential Integrity**: Maintain proper relationships between dimension and fact tables
3. **Configurable Corruption**: Support configurable data corruption rates for testing DQ rules
4. **DQ Mapping**: Document which DQ expectations each corruption type tests
5. **Consistency**: Use consistent patterns across all generators

### Standard Function Signatures

```python
def generate_dimension_data(
    spark: SparkSession,
    catalog: str,
    schema: str,
    num_records: int,
    corruption_rate: float = 0.05  # 5% default corruption
) -> DataFrame:
    """
    Generate dimension data with optional corruption for DQ testing.
    
    Args:
        spark: SparkSession instance
        catalog: Unity Catalog name
        schema: Schema name
        num_records: Number of records to generate
        corruption_rate: Percentage of records to corrupt (0.0 to 1.0)
    
    Returns:
        DataFrame with generated records
    """
```

### Corruption Patterns

**ALWAYS include comment explaining which DQ expectation the corruption tests:**

```python
if should_corrupt:
    corruption_type = random.choice([
        'zero_quantity',
        'negative_price',
        'excessive_price',
        'loyalty_without_id',
        'multi_unit_without_quantity'
    ])
    
    if corruption_type == 'zero_quantity':
        # Will fail: non_zero_quantity expectation
        quantity_sold = 0
    elif corruption_type == 'negative_price':
        # Will fail: valid_final_price expectation
        final_sales_price = -random.uniform(1.0, 50.0)
    elif corruption_type == 'excessive_price':
        # Will fail: reasonable_price_range expectation
        final_sales_price = random.uniform(50000.0, 100000.0)
    elif corruption_type == 'loyalty_without_id':
        # Will fail: loyalty_consistency expectation
        loyalty_discount = random.uniform(1.0, 10.0)
        loyalty_card_id = None
    elif corruption_type == 'multi_unit_without_quantity':
        # Will fail: multi_unit_consistency expectation
        multi_unit_discount = random.uniform(1.0, 5.0)
        quantity_sold = 1
```

### Parameter Handling for Notebooks

```python
# Databricks notebook source
def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    schema = dbutils.widgets.get("schema")
    num_records = int(dbutils.widgets.get("num_records"))
    corruption_rate = float(dbutils.widgets.get("corruption_rate"))
    
    print(f"Catalog: {catalog}")
    print(f"Schema: {schema}")
    print(f"Num Records: {num_records}")
    print(f"Corruption Rate: {corruption_rate}")
    
    return catalog, schema, num_records, corruption_rate
```

### Corruption Type Categories

#### Price/Value Corruptions
- `negative_price` - Tests: `valid_final_price`, `positive_amount`
- `excessive_price` - Tests: `reasonable_price_range`
- `zero_amount` - Tests: `non_zero_transaction`

#### Quantity Corruptions
- `zero_quantity` - Tests: `non_zero_quantity`
- `negative_quantity` - Tests: `valid_quantity`
- `excessive_quantity` - Tests: `reasonable_quantity_range`

#### Referential Corruptions
- `invalid_store` - Tests: `valid_store_reference`
- `invalid_product` - Tests: `valid_product_reference`
- `future_date` - Tests: `valid_date_range`

#### Business Logic Corruptions
- `loyalty_without_id` - Tests: `loyalty_consistency`
- `multi_unit_without_quantity` - Tests: `multi_unit_consistency`
- `discount_exceeds_price` - Tests: `valid_discount_amount`

### Dimension vs Fact Generation

**Dimensions:**
- Generate a fixed number of records
- Must complete BEFORE fact generation
- Should be idempotent (same seed = same data)

**Facts:**
- Reference existing dimension keys
- Support configurable volume
- Include corruption for DQ testing

### Example: Complete Dimension Generator

```python
def generate_store_dimension(
    spark: SparkSession,
    catalog: str,
    schema: str,
    num_stores: int,
    corruption_rate: float = 0.05
) -> int:
    """
    Generate store dimension data.
    
    Corruption types:
    - missing_state: Tests valid_state_code expectation
    - invalid_zip: Tests valid_zip_format expectation
    - future_open_date: Tests valid_open_date expectation
    """
    fake = Faker()
    Faker.seed(42)  # Reproducible data
    random.seed(42)
    
    stores = []
    for i in range(num_stores):
        should_corrupt = random.random() < corruption_rate
        
        # Normal values
        state = fake.state_abbr()
        zip_code = fake.zipcode()
        open_date = fake.date_between(start_date='-10y', end_date='today')
        
        if should_corrupt:
            corruption = random.choice(['missing_state', 'invalid_zip', 'future_open_date'])
            if corruption == 'missing_state':
                state = None  # Will fail: valid_state_code
            elif corruption == 'invalid_zip':
                zip_code = "INVALID"  # Will fail: valid_zip_format
            elif corruption == 'future_open_date':
                open_date = fake.date_between(start_date='+1y', end_date='+5y')  # Will fail: valid_open_date
        
        stores.append({
            'store_number': f"STR{i+1:05d}",
            'store_name': fake.company(),
            'address': fake.street_address(),
            'city': fake.city(),
            'state': state,
            'zip_code': zip_code,
            'open_date': open_date,
            'processed_timestamp': datetime.now()
        })
    
    df = spark.createDataFrame(stores)
    df.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.stores")
    
    return num_stores
```

### Documentation Requirements

Every generator must document:

1. **Purpose**: What data it generates
2. **Corruption Types**: List of corruption patterns with mapped DQ expectations
3. **Dependencies**: What dimensions must exist first
4. **Volume Guidance**: Recommended record counts for testing
5. **Seed Behavior**: Whether data is reproducible

### Validation Checklist

- [ ] Function signature matches standard pattern
- [ ] All corruption types have DQ expectation comments
- [ ] Uses `dbutils.widgets.get()` for parameters (NOT `argparse`)
- [ ] Includes corruption_rate parameter with default
- [ ] Documents all corruption types in docstring
- [ ] Seeds random generators for reproducibility
- [ ] Handles both normal and corrupted record generation
- [ ] Returns meaningful statistics (record counts, corruption counts)




