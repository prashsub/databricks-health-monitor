# Appendix C - Metric Views Troubleshooting

## Common Errors and Solutions

### Error: UNRESOLVED_COLUMN

**Symptom**:
```
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter 
with name `source`.`prediction_id` cannot be resolved.
```

**Cause**: The column doesn't exist in the source table.

**Solution**:
1. Verify column exists in source table:
   ```sql
   DESCRIBE TABLE {catalog}.{schema}.{source_table};
   ```
2. Check for typos in column name
3. Use correct column name or `COUNT(*)` instead of `COUNT(column)`

**Example Fix**:
```yaml
# WRONG: Column doesn't exist
- name: total_predictions
  expr: COUNT(source.prediction_id)  # ❌

# CORRECT: Use COUNT(*)
- name: total_predictions
  expr: COUNT(*)  # ✅
```

---

### Error: Unrecognized field "name"

**Symptom**:
```
[METRIC_VIEW_INVALID_VIEW_DEFINITION] Unrecognized field "name"
```

**Cause**: v1.1 specification doesn't support `name:` field in YAML root.

**Solution**: Remove the `name:` field. The view name comes from the CREATE VIEW statement.

**Example Fix**:
```yaml
# WRONG
version: "1.1"
name: my_metric_view  # ❌ Not supported!
source: ...

# CORRECT
version: "1.1"
# No name field - name comes from CREATE VIEW statement
source: ...
```

---

### Error: DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE

**Symptom**:
```
[DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE] Cannot resolve "CASE WHEN is_anomaly THEN 1 ELSE 0 END" 
due to data type mismatch: The first parameter requires the "BOOLEAN" type, 
however "is_anomaly" has the type "BIGINT".
```

**Cause**: Using a BIGINT column in a boolean context.

**Solution**: Use explicit comparison with `= 1`.

**Example Fix**:
```yaml
# WRONG: Boolean context for BIGINT
- name: anomaly_count
  expr: SUM(CASE WHEN source.is_anomaly THEN 1 ELSE 0 END)  # ❌

# CORRECT: Explicit comparison
- name: anomaly_count
  expr: SUM(CASE WHEN source.is_anomaly = 1 THEN 1 ELSE 0 END)  # ✅
```

---

### Error: Missing required creator property 'source'

**Symptom**:
```
Missing required creator property 'source' (index 2)
```

**Cause**: Wrong field name in joins. Using `table:` instead of `source:`.

**Solution**: Use `source:` field in joins.

**Example Fix**:
```yaml
# WRONG
joins:
  - name: dim_workspace
    table: catalog.schema.dim_workspace  # ❌
    'on': ...

# CORRECT
joins:
  - name: dim_workspace
    source: catalog.schema.dim_workspace  # ✅
    'on': ...
```

---

### Error: Source table does not exist

**Symptom**:
```
[TABLE_OR_VIEW_NOT_FOUND] The table or view `catalog`.`schema`.`source_table` cannot be found.
```

**Cause**: The source table hasn't been created or the name is wrong.

**Solution**:
1. Verify table exists:
   ```sql
   SHOW TABLES IN {catalog}.{schema} LIKE '{table_name}';
   ```
2. Check table name for typos
3. Run prerequisite pipeline (Gold layer or ML inference)

---

### Error: Permission denied

**Symptom**:
```
[PERMISSION_DENIED] User does not have SELECT permission on table
```

**Cause**: Missing SELECT permission on source table or dimension tables.

**Solution**:
```sql
-- Grant SELECT on source tables
GRANT SELECT ON {catalog}.{schema}.{table} TO `user@domain.com`;

-- Or grant on entire schema
GRANT SELECT ON SCHEMA {catalog}.{schema} TO `user@domain.com`;
```

---

### Error: Invalid ON clause

**Symptom**:
```
[PARSE_SYNTAX_ERROR] Syntax error at or near 'on'
```

**Cause**: The `on` field must be quoted in YAML because it's a reserved word.

**Solution**: Always quote `'on'`:

```yaml
# WRONG
joins:
  - name: dim_workspace
    source: catalog.schema.dim_workspace
    on: source.workspace_id = dim_workspace.workspace_id  # ❌

# CORRECT
joins:
  - name: dim_workspace
    source: catalog.schema.dim_workspace
    'on': source.workspace_id = dim_workspace.workspace_id  # ✅
```

---

### Error: Job shows SUCCESS but view not created

**Symptom**: Deployment job exits successfully but metric view doesn't exist.

**Cause**: Old code swallowed errors for "optional" views.

**Solution**: Check the updated deployment script enforces strict failure:
- All views are required
- Any failure raises `RuntimeError`
- Job fails if any view fails

**Verification**:
```sql
-- Check if view exists
SHOW VIEWS IN {catalog}.{schema} LIKE 'mv_{view_name}';

-- Verify it's a METRIC_VIEW type
DESCRIBE EXTENDED {catalog}.{schema}.mv_{view_name};
```

---

### Error: View created as regular VIEW, not METRIC_VIEW

**Symptom**: View exists but `DESCRIBE EXTENDED` shows `Type: VIEW` instead of `Type: METRIC_VIEW`.

**Cause**: Using wrong CREATE VIEW syntax.

**Solution**: Ensure using `WITH METRICS LANGUAGE YAML` syntax:

```sql
-- WRONG: Creates regular view
CREATE VIEW catalog.schema.mv_test AS SELECT 1;

-- CORRECT: Creates metric view
CREATE VIEW catalog.schema.mv_test
WITH METRICS
LANGUAGE YAML
AS $$
version: "1.1"
source: catalog.schema.table
dimensions:
  - name: col1
    expr: source.col1
$$;
```

---

## Debugging Workflow

### Step 1: Verify Source Table Schema

```sql
-- Check source table exists and has expected columns
DESCRIBE TABLE {catalog}.{schema}.{source_table};

-- List all columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_catalog = '{catalog}'
  AND table_schema = '{schema}'
  AND table_name = '{source_table}';
```

### Step 2: Validate YAML Syntax

```python
# Quick Python validation
import yaml

with open('metric_view.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
# Check required fields
assert 'version' in config
assert 'source' in config
assert 'dimensions' in config
print("YAML syntax valid!")
```

### Step 3: Test Column References

```sql
-- Test dimension expressions
SELECT 
    {dimension_expr} as test_dim
FROM {source_table}
LIMIT 5;

-- Test measure expressions
SELECT 
    {measure_expr} as test_measure
FROM {source_table};
```

### Step 4: Test Join Conditions

```sql
-- Verify join produces results
SELECT COUNT(*)
FROM {source_table} s
LEFT JOIN {dim_table} d
    ON s.{fk} = d.{pk} AND d.is_current = true;
```

### Step 5: Check Deployment Logs

```bash
# View job run output in Databricks UI
# Or use CLI
databricks runs get-output --run-id {run_id}
```

---

## Validation Checklist

Before deploying a metric view:

- [ ] Source table exists and is accessible
- [ ] All dimension columns exist in source/joined tables
- [ ] All measure columns exist and are numeric
- [ ] Join conditions reference correct columns
- [ ] `'on'` is quoted in YAML
- [ ] No `name:` field in YAML root
- [ ] BIGINT flags use `= 1` comparison
- [ ] All divisions use `NULLIF(denominator, 0)`
- [ ] Comment includes PURPOSE, BEST FOR, NOT FOR sections

---

## Quick Fixes Reference

| Error Pattern | Quick Fix |
|---------------|-----------|
| `UNRESOLVED_COLUMN` | Verify column name in source table |
| `Unrecognized field "name"` | Remove `name:` from YAML |
| `DATATYPE_MISMATCH` | Use `= 1` for BIGINT flags |
| `Missing required creator property` | Use `source:` not `table:` in joins |
| `TABLE_OR_VIEW_NOT_FOUND` | Run prerequisite pipeline |
| `Syntax error at 'on'` | Quote `'on'` in YAML |
| View created as regular VIEW | Use `WITH METRICS LANGUAGE YAML` |

---

## Related Documentation

- [22-Architecture](../22-metric-views-architecture.md) - Column reference rules
- [23-Deployment](../23-metric-views-deployment.md) - Error handling details
- [mv-B-yaml-patterns](mv-B-yaml-patterns.md) - Correct YAML patterns

