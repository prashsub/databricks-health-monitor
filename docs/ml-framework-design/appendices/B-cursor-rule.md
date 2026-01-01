# Appendix B - MLflow Cursor Rule

This appendix contains the key patterns from the ML cursor rule that should be followed for all ML development.

## Non-Negotiable Rules

1. **ALWAYS cast label columns** to DOUBLE (regression) or INT (classification) in `base_df` before `fe.create_training_set()`

2. **ALWAYS use `fe.log_model()`** with `training_set` parameter to embed feature lookup metadata

3. **ALWAYS provide `signature` and `input_example`** to `fe.log_model()` - Unity Catalog requires both

4. **ALWAYS use float64** for `input_example`: `X_train.head(5).astype('float64')`

5. **NEVER use DECIMAL types** in training data - cast to DOUBLE before creating signature

6. **ALWAYS use `X_train` consistently** - don't mix `X` and `X_train` variable names

7. **ALWAYS return `X_train`** from prepare functions for signature creation

8. **ALWAYS verify feature names** match actual feature table columns before training

## Label Type Reference

| Model Type | Label Cast | Example |
|---|---|---|
| Regression | `cast("double")` | `F.col("daily_cost").cast("double")` |
| Binary Classification | `cast("int")` | `F.col("is_anomaly").cast("int")` |
| Multi-class Classification | `cast("int")` | `F.col("category_id").cast("int")` |
| Anomaly Detection | N/A | No label needed |

## Feature Engineering Validation Checklist

### Before Training
- [ ] Feature table exists
- [ ] Feature table has PRIMARY KEY constraint
- [ ] Feature names in script match actual columns
- [ ] Primary key columns are NOT NULL

### During create_training_set
- [ ] base_df has ONLY: primary keys + label (if supervised)
- [ ] Label column cast to correct type in base_df
- [ ] feature_lookups use correct lookup_key
- [ ] exclude_columns includes primary keys

### During Model Logging
- [ ] X_train is returned from prepare function
- [ ] input_example uses X_train.head(5).astype('float64')
- [ ] signature is inferred with infer_signature()
- [ ] fe.log_model includes training_set parameter
- [ ] registered_model_name format: catalog.schema.model_name

## Common Errors Quick Reference

| Error | Solution |
|---|---|
| "signature contains only inputs" | Cast label to DOUBLE/INT in base_df |
| "DECIMAL type not supported" | Use .astype('float64') for input_example |
| "name 'X_train' is not defined" | Return X_train from prepare function |
| "UNRESOLVED_COLUMN" | Verify column names match feature table |
| "Table does not have primary key" | Add PRIMARY KEY constraint to feature table |

## Full Cursor Rule Reference

See `.cursor/rules/ml/27-mlflow-mlmodels-patterns.mdc` for the complete rule with all patterns and examples.

