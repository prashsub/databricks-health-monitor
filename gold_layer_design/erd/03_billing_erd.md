# Billing Domain ERD

## Overview
Cost management, usage tracking, and pricing.

## Tables
- `dim_sku` - SKU/pricing definitions
- `fact_usage` - Billable usage records
- `fact_list_prices` - Published pricing
- `fact_account_prices` - Account-specific pricing

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_workspace ||--o{ fact_usage : "workspace_id"
    dim_sku ||--o{ fact_usage : "sku_name"
    dim_sku ||--o{ fact_list_prices : "sku_name"
    dim_sku ||--o{ fact_account_prices : "sku_name"

    dim_workspace {
        STRING workspace_id PK
        STRING workspace_name
    }

    dim_sku {
        STRING sku_name PK
        STRING billing_type
        STRING usage_unit
    }

    fact_usage {
        STRING workspace_id PK
        STRING sku_name FK
        DATE usage_date PK
        STRING usage_unit
        DOUBLE usage_quantity
        STRING billing_origin_product
        STRING usage_type
    }

    fact_list_prices {
        STRING sku_name FK
        STRING currency_code PK
        DATE price_start_time PK
        DATE price_end_time
        DOUBLE list_price
    }

    fact_account_prices {
        STRING account_id PK
        STRING sku_name FK
        STRING currency_code PK
        DATE price_start_time PK
        DOUBLE account_price
    }
```

## Key Relationships

| From | To | Cardinality | FK Columns |
|------|-----|-------------|------------|
| dim_sku | fact_usage | 1:N | sku_name |
| dim_sku | fact_list_prices | 1:N | sku_name |
| dim_sku | fact_account_prices | 1:N | sku_name |
| dim_workspace | fact_usage | 1:N | workspace_id |

