# Appendix C - References

## Official Databricks Documentation

### Table-Valued Functions (TVFs)

- [SQL Language Manual - TVF](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-tvf)
- [User-Defined Functions](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-udf-scalar)
- [Function Parameters](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-function)

### Genie Spaces

- [Genie Overview](https://docs.databricks.com/aws/en/genie/index.html)
- [Trusted Assets for Genie](https://docs.databricks.com/aws/en/genie/trusted-assets)
- [Tips for Writing Functions](https://docs.databricks.com/aws/en/genie/trusted-assets#tips-for-writing-functions)
- [Genie Best Practices](https://docs.databricks.com/aws/en/genie/best-practices)

### Unity Catalog

- [Unity Catalog Overview](https://docs.databricks.com/aws/en/unity-catalog/)
- [Functions in Unity Catalog](https://docs.databricks.com/aws/en/unity-catalog/functions)
- [Privileges](https://docs.databricks.com/aws/en/unity-catalog/manage-privileges/)

### Delta Lake

- [Delta Lake Overview](https://docs.databricks.com/aws/en/delta/index.html)
- [Table Properties](https://docs.databricks.com/aws/en/delta/table-properties.html)
- [Liquid Clustering](https://docs.databricks.com/aws/en/delta/clustering)

### SQL Reference

- [SQL Reference](https://docs.databricks.com/aws/en/sql/language-manual/index.html)
- [Built-in Functions](https://docs.databricks.com/aws/en/sql/language-manual/functions/index.html)
- [Window Functions](https://docs.databricks.com/aws/en/sql/language-manual/functions/window-functions)
- [Aggregate Functions](https://docs.databricks.com/aws/en/sql/language-manual/functions/aggregate-functions)

### Asset Bundles

- [Databricks Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Bundle Resources](https://docs.databricks.com/aws/en/dev-tools/bundles/resources)
- [Jobs Configuration](https://docs.databricks.com/aws/en/dev-tools/bundles/resources#jobs)

---

## Project Documentation

### Architecture

- [Agent Framework Design](../../agent-framework-design/00-index.md)
- [Gold Layer Design](../../../gold_layer_design/README.md)
- [Genie Spaces Plan](../../../plans/phase3-addendum-3.6-genie-spaces.md)

### Implementation Plans

- [Phase 3.2 TVF Plan](../../../plans/phase3-addendum-3.2-tvfs.md)
- [Phase 3 Overview](../../../plans/phase3-use-cases.md)
- [Phase 4 Agent Framework](../../../plans/phase4-agent-framework.md)

### Cursor Rules

- [Databricks Asset Bundles Rule](../../../.cursor/rules/common/02-databricks-asset-bundles.mdc)
- [Table Properties Rule](../../../.cursor/rules/common/04-databricks-table-properties.mdc)
- [TVF Patterns Rule](../../../.cursor/rules/common/databricks-table-valued-functions.mdc)

---

## SQL Function Reference

### Date/Time Functions

| Function | Description | Example |
|----------|-------------|---------|
| `CAST(x AS DATE)` | Convert string to date | `CAST('2024-12-31' AS DATE)` |
| `CURRENT_DATE()` | Current date | `WHERE date >= CURRENT_DATE()` |
| `DATE_ADD(date, n)` | Add days to date | `DATE_ADD(CURRENT_DATE(), -30)` |
| `TIMESTAMPADD(unit, n, ts)` | Add time units | `TIMESTAMPADD(HOUR, -24, CURRENT_TIMESTAMP())` |
| `DATE_TRUNC(unit, date)` | Truncate to unit | `DATE_TRUNC('month', date)` |

### Aggregate Functions

| Function | Description | Example |
|----------|-------------|---------|
| `SUM(x)` | Sum values | `SUM(cost)` |
| `COUNT(*)` | Count rows | `COUNT(*)` |
| `COUNT(DISTINCT x)` | Count unique | `COUNT(DISTINCT user_id)` |
| `AVG(x)` | Average | `AVG(duration)` |
| `MAX(x)` / `MIN(x)` | Maximum/minimum | `MAX(timestamp)` |
| `ANY_VALUE(x)` | Any value from group | `ANY_VALUE(name)` |
| `PERCENTILE_APPROX(x, p)` | Approximate percentile | `PERCENTILE_APPROX(duration, 0.95)` |

### Window Functions

| Function | Description | Example |
|----------|-------------|---------|
| `ROW_NUMBER()` | Sequential row number | `ROW_NUMBER() OVER (ORDER BY cost DESC)` |
| `RANK()` | Rank with gaps | `RANK() OVER (ORDER BY score DESC)` |
| `LAG(x, n)` | Previous row value | `LAG(cost, 1) OVER (ORDER BY date)` |
| `LEAD(x, n)` | Next row value | `LEAD(cost, 1) OVER (ORDER BY date)` |
| `SUM() OVER` | Running sum | `SUM(cost) OVER (ORDER BY date)` |

### String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `CONCAT(a, b)` | Concatenate | `CONCAT(first_name, ' ', last_name)` |
| `SUBSTRING(s, start, len)` | Extract substring | `SUBSTRING(query_text, 1, 200)` |
| `LOWER(s)` / `UPPER(s)` | Case conversion | `LOWER(email)` |
| `COALESCE(a, b, ...)` | First non-null | `COALESCE(name, 'Unknown')` |
| `NULLIF(a, b)` | Return NULL if equal | `total / NULLIF(count, 0)` |

### Array Functions

| Function | Description | Example |
|----------|-------------|---------|
| `EXPLODE(arr)` | Unpack array | `EXPLODE(compute_ids)` |
| `SIZE(arr)` | Array length | `SIZE(compute_ids) > 0` |
| `ARRAY_CONTAINS(arr, x)` | Check membership | `ARRAY_CONTAINS(tags, 'prod')` |

---

## Related Resources

### Databricks Labs

- [DQX Data Quality](https://databrickslabs.github.io/dqx/)
- [UCX Migration](https://databrickslabs.github.io/ucx/)

### Community

- [Databricks Community](https://community.databricks.com/)
- [Stack Overflow - Databricks](https://stackoverflow.com/questions/tagged/databricks)

### GitHub Examples

- [Bundle Examples](https://github.com/databricks/bundle-examples)
- [Databricks SDK Python](https://github.com/databricks/databricks-sdk-py)

