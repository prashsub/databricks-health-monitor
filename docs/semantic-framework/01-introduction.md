# 01 - Introduction

## Purpose

The Semantic Framework provides a library of **60 Table-Valued Functions (TVFs)** that serve as the query interface for Databricks Genie Spaces. These TVFs encapsulate complex analytical queries with LLM-friendly metadata, enabling users to ask business questions in natural language and receive accurate, consistent answers.

## Scope

### In Scope

- **Cost Analysis TVFs**: Cost attribution, chargeback, tag-based allocation, trend analysis
- **Reliability TVFs**: Job success rates, failure analysis, SLA compliance, repair costs
- **Performance TVFs**: Query latency, warehouse utilization, cluster optimization
- **Security TVFs**: Audit analysis, access patterns, risk scoring, activity monitoring
- **Quality TVFs**: Data freshness, lineage tracking, governance compliance

### Out of Scope

- Direct Gold layer table access (use TVFs instead)
- Real-time streaming queries (batch analysis only)
- Cross-workspace queries (single catalog focus)
- Custom visualization (dashboards handle presentation)

## Prerequisites

### Required Components

| Component | Count | Status | Documentation |
|-----------|-------|--------|---------------|
| Gold Layer Fact Tables | 14 | Required | [Gold Layer Design](../../gold_layer_design/) |
| Gold Layer Dimension Tables | 8 | Required | [Gold Layer Design](../../gold_layer_design/) |
| Unity Catalog | 1 | Required | Databricks workspace |
| SQL Warehouse | 1 | Required | Serverless recommended |

### Gold Layer Tables Used

**Fact Tables**:
- `fact_usage` - Billing and cost data
- `fact_job_run_timeline` - Job execution history
- `fact_query_history` - SQL query metrics
- `fact_audit_logs` - Security audit events
- `fact_node_timeline` - Cluster node metrics
- `fact_table_lineage` - Data lineage events

**Dimension Tables**:
- `dim_workspace` - Workspace metadata
- `dim_job` - Job definitions
- `dim_warehouse` - SQL Warehouse metadata
- `dim_cluster` - Cluster configurations
- `dim_sku` - SKU pricing information

### Infrastructure Requirements

| Requirement | Specification |
|-------------|---------------|
| Databricks Runtime | SQL Warehouse (any version) |
| Unity Catalog | Enabled with SELECT permissions |
| Authentication | Named profile configured |
| Asset Bundles | Databricks CLI 0.200+ |

## Design Principles

### 1. Genie-Compatible Parameters

**Problem**: Genie Spaces don't support DATE type parameters.

**Solution**: Use STRING for all date parameters with explicit format hints.

```sql
-- ❌ WRONG: DATE parameter
CREATE FUNCTION get_data(start_date DATE)

-- ✅ CORRECT: STRING parameter with format comment
CREATE FUNCTION get_data(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)'
)
...
WHERE usage_date >= CAST(start_date AS DATE)
```

### 2. Parameter Ordering

**Problem**: SQL requires parameters with DEFAULT values to come after required parameters.

**Solution**: Always put required parameters first.

```sql
-- ❌ WRONG: Optional before required
CREATE FUNCTION get_data(
    top_n INT DEFAULT 10,    -- Optional with DEFAULT
    start_date STRING        -- Required without DEFAULT
)

-- ✅ CORRECT: Required before optional
CREATE FUNCTION get_data(
    start_date STRING,       -- Required (no DEFAULT)
    end_date STRING,         -- Required (no DEFAULT)
    top_n INT DEFAULT 10     -- Optional (has DEFAULT)
)
```

### 3. Top N Pattern

**Problem**: `LIMIT` clause requires compile-time constants, not parameters.

**Solution**: Use `ROW_NUMBER()` with `WHERE` instead of `LIMIT`.

```sql
-- ❌ WRONG: Parameter in LIMIT
SELECT * FROM data ORDER BY revenue DESC LIMIT top_n

-- ✅ CORRECT: ROW_NUMBER with WHERE
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rank
    FROM data
)
SELECT * FROM ranked WHERE rank <= top_n ORDER BY rank
```

### 4. Null-Safe Division

**Problem**: Division by zero causes query failures.

**Solution**: Always use `NULLIF` for denominators.

```sql
-- ❌ WRONG: Division may fail
SELECT total / count AS average FROM data

-- ✅ CORRECT: Null-safe division
SELECT total / NULLIF(count, 0) AS average FROM data
```

### 5. SCD2 Dimension Handling

**Problem**: Dimension tables have historical versions; need current record only.

**Solution**: Filter with `delete_time IS NULL` pattern.

```sql
-- ✅ CORRECT: Filter for current dimension records
SELECT f.*, d.entity_name
FROM fact_table f
LEFT JOIN dim_entity d
    ON f.entity_id = d.entity_id
    AND d.delete_time IS NULL  -- Current record only
```

### 6. LLM-Friendly Documentation

Every TVF includes a structured comment block to help Genie understand when to use it:

```sql
COMMENT '
- PURPOSE: What this function does and why
- BEST FOR: Natural language questions it handles well
- NOT FOR: Questions to redirect to other TVFs
- RETURNS: What columns and data types are returned
- PARAMS: Parameter descriptions with formats
- SYNTAX: Example SQL invocation
- NOTE: Important caveats or limitations
'
```

## TVF Inventory Summary

| Domain | TVF Count | Primary Tables |
|--------|-----------|----------------|
| Cost | 15 | fact_usage, dim_workspace, dim_sku |
| Reliability | 12 | fact_job_run_timeline, dim_job, fact_usage |
| Performance (Query) | 10 | fact_query_history, dim_warehouse |
| Performance (Compute) | 6 | fact_node_timeline, dim_cluster, fact_usage |
| Security | 10 | fact_audit_logs, fact_table_lineage |
| Quality | 7 | information_schema, fact_table_lineage, dim_job |
| **Total** | **60** | |

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| TVF deployment success | 100% | All 60 TVFs deploy without errors |
| Documentation coverage | 100% | Every TVF has complete comment block |
| Genie compatibility | 100% | All TVFs work with Genie natural language |
| Parameter validation | 100% | No runtime errors from valid inputs |
| Query performance | <10s P95 | Monitor query latency |

## Next Steps

1. **Read [02-Architecture Overview](02-architecture-overview.md)** to understand the data flow
2. **Review domain-specific docs (03-07)** for TVF details
3. **Follow [08-Deployment Guide](08-deployment-guide.md)** to deploy TVFs
4. **Try examples from [09-Usage Examples](09-usage-examples.md)** to test

