# Appendix B - SQL Patterns

## Overview

This appendix documents the SQL patterns used throughout the TVF implementations. These patterns address Genie compatibility, performance, and correctness.

---

## Pattern 1: STRING Date Parameters

**Problem**: Genie Spaces don't support DATE type parameters.

**Solution**: Use STRING with CAST in WHERE clauses.

```sql
-- ❌ WRONG: DATE parameter
CREATE FUNCTION get_data(start_date DATE)

-- ✅ CORRECT: STRING parameter
CREATE FUNCTION get_data(
    start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)'
)
RETURNS TABLE(...)
RETURN
    SELECT * FROM fact_table
    WHERE usage_date >= CAST(start_date AS DATE);
```

---

## Pattern 2: Required Before Optional Parameters

**Problem**: SQL requires non-DEFAULT parameters before DEFAULT parameters.

**Solution**: Order parameters with required first.

```sql
-- ❌ WRONG: Default before required
CREATE FUNCTION get_data(
    top_n INT DEFAULT 10,    -- Has default
    start_date STRING        -- No default
)

-- ✅ CORRECT: Required first
CREATE FUNCTION get_data(
    start_date STRING,       -- Required (no default)
    end_date STRING,         -- Required (no default)
    top_n INT DEFAULT 10     -- Optional (has default)
)
```

---

## Pattern 3: ROW_NUMBER for Top N

**Problem**: LIMIT requires compile-time constants, not parameters.

**Solution**: Use ROW_NUMBER() with WHERE filter.

```sql
-- ❌ WRONG: Parameter in LIMIT
SELECT * FROM data
ORDER BY revenue DESC
LIMIT top_n;

-- ✅ CORRECT: ROW_NUMBER with WHERE
WITH ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rank
    FROM data
)
SELECT * FROM ranked
WHERE rank <= top_n
ORDER BY rank;
```

---

## Pattern 4: NULLIF for Safe Division

**Problem**: Division by zero causes query failures.

**Solution**: Always use NULLIF on denominators.

```sql
-- ❌ WRONG: May fail
SELECT total / count AS average

-- ✅ CORRECT: Returns NULL if count is 0
SELECT total / NULLIF(count, 0) AS average
```

---

## Pattern 5: SCD Type 2 Dimension Joins

**Problem**: Dimension tables have historical records; need current only.

**Solution**: Filter with `delete_time IS NULL`.

```sql
-- ✅ CORRECT: Current record only
LEFT JOIN dim_job j
    ON f.job_id = j.job_id
    AND j.delete_time IS NULL

-- For composite keys
LEFT JOIN dim_job j
    ON f.workspace_id = j.workspace_id
    AND f.job_id = j.job_id
    AND j.delete_time IS NULL
```

---

## Pattern 6: Date Arithmetic with Parameters

**Problem**: `INTERVAL param DAY` syntax doesn't work in TVFs.

**Solution**: Use `DATE_ADD()` or `TIMESTAMPADD()`.

```sql
-- ❌ WRONG: INTERVAL syntax
WHERE date >= CURRENT_DATE() - INTERVAL days_back DAY

-- ✅ CORRECT: DATE_ADD
WHERE date >= DATE_ADD(CURRENT_DATE(), -days_back)

-- ✅ CORRECT: TIMESTAMPADD for timestamps
WHERE ts >= TIMESTAMPADD(HOUR, -hours_back, CURRENT_TIMESTAMP())
```

---

## Pattern 7: PERCENTILE_APPROX

**Problem**: `PERCENTILE_CONT` has limited support in some contexts.

**Solution**: Use `PERCENTILE_APPROX` for percentile calculations.

```sql
-- ❌ May have issues
PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration)

-- ✅ CORRECT: Use PERCENTILE_APPROX
PERCENTILE_APPROX(duration, 0.95) AS p95_duration
```

---

## Pattern 8: ANY_VALUE for Non-Aggregated Columns

**Problem**: `FIRST()` function has inconsistent support.

**Solution**: Use `ANY_VALUE()` for non-aggregated columns in GROUP BY.

```sql
-- ❌ May have issues
SELECT job_id, FIRST(job_name) AS job_name, SUM(cost)

-- ✅ CORRECT: ANY_VALUE
SELECT job_id, ANY_VALUE(job_name) AS job_name, SUM(cost)
GROUP BY job_id
```

---

## Pattern 9: Array Handling with EXPLODE

**Problem**: Joining on array columns requires unpacking.

**Solution**: Use EXPLODE in a CTE.

```sql
-- Unpack array for joining
WITH exploded_clusters AS (
    SELECT
        job_id,
        run_id,
        EXPLODE(compute_ids) AS cluster_id
    FROM fact_job_run_timeline
    WHERE compute_ids IS NOT NULL
        AND SIZE(compute_ids) > 0
)
SELECT e.job_id, c.cluster_name
FROM exploded_clusters e
JOIN dim_cluster c ON e.cluster_id = c.cluster_id;
```

---

## Pattern 10: Parameter in Aggregate Context

**Problem**: Parameters can't be used inside aggregates in certain subquery patterns.

**Solution**: Move parameter comparison outside aggregate or use fixed values.

```sql
-- ❌ WRONG: Parameter in aggregate subquery
SELECT
    SUM(CASE WHEN duration <= threshold THEN 1 ELSE 0 END)
FROM data

-- ✅ CORRECT: Pre-calculate or restructure
WITH classified AS (
    SELECT *, 
        CASE WHEN duration <= 60 THEN 'within_sla' ELSE 'breach' END AS status
    FROM data
)
SELECT 
    SUM(CASE WHEN status = 'within_sla' THEN 1 ELSE 0 END)
FROM classified;
```

---

## Pattern 11: LLM-Friendly Comments

**Structure**: Include PURPOSE, BEST FOR, NOT FOR, PARAMS, SYNTAX.

```sql
COMMENT '
- PURPOSE: Calculate top N cost contributors by workspace and SKU
- BEST FOR: "What are the biggest cost drivers?" "Top spending workspaces"
- NOT FOR: Detailed daily trends (use get_cost_trend_by_sku instead)
- RETURNS: Ranked list with workspace, SKU, costs, percentages
- PARAMS: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), top_n (default 10)
- SYNTAX: SELECT * FROM TABLE(get_top_cost_contributors(''2024-12-01'', ''2024-12-31'', 10))
- NOTE: Returns combined DBU and cloud costs
'
```

---

## Pattern 12: Conditional Aggregation

**Use Case**: Count different categories in one pass.

```sql
SELECT
    job_id,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN NOT is_success THEN 1 ELSE 0 END) AS failure_count,
    COUNT(*) AS total_count,
    SUM(CASE WHEN is_success THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(*), 0) AS success_rate
FROM job_runs
GROUP BY job_id;
```

---

## Pattern 13: CTE Pipeline Structure

**Use Case**: Break complex queries into readable steps.

```sql
WITH 
-- Step 1: Get base data
base_data AS (
    SELECT * FROM fact_table
    WHERE date >= CAST(start_date AS DATE)
),

-- Step 2: Add dimension attributes
with_dimensions AS (
    SELECT b.*, d.name
    FROM base_data b
    LEFT JOIN dim_table d ON b.key = d.key
        AND d.delete_time IS NULL
),

-- Step 3: Aggregate
aggregated AS (
    SELECT 
        name,
        SUM(amount) AS total,
        COUNT(*) AS count
    FROM with_dimensions
    GROUP BY name
),

-- Step 4: Rank for Top N
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (ORDER BY total DESC) AS rank
    FROM aggregated
)

-- Final output
SELECT * FROM ranked
WHERE rank <= top_n
ORDER BY rank;
```

---

## Common Gotchas

| Issue | Symptom | Solution |
|-------|---------|----------|
| DATE parameter | "Unsupported type: date" | Use STRING with CAST |
| Parameter order | "DEFAULT must not be followed by..." | Required params first |
| LIMIT with param | "Must evaluate to constant" | Use ROW_NUMBER/WHERE |
| Division by zero | Query fails | Use NULLIF |
| Wrong dimension version | Historical data joined | Use delete_time IS NULL |
| INTERVAL syntax | "Syntax error at 'days_back'" | Use DATE_ADD |
| PERCENTILE_CONT | Various errors | Use PERCENTILE_APPROX |
| FIRST() function | Unsupported | Use ANY_VALUE |
| Array columns | Can't join directly | Use EXPLODE |
| Parameter in aggregate | "Correlated subquery" error | Restructure query |

