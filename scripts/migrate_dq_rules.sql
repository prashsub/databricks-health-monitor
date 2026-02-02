-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Migrate DQ Rules: Critical → Warning
-- MAGIC 
-- MAGIC This notebook updates existing Bronze layer DQ rules to use "warning" severity
-- MAGIC instead of "critical" for rules where NULL values are legitimate in system tables.
-- MAGIC 
-- MAGIC **Problem:** 
-- MAGIC - `column_lineage`: 309M records dropped
-- MAGIC - `clusters`: 155 records dropped
-- MAGIC 
-- MAGIC **Solution:** Change to warning severity to log issues without dropping records.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Set Parameters

-- COMMAND ----------

-- Update these values for your environment
CREATE WIDGET TEXT catalog DEFAULT "prashanth_subrahmanyam_catalog";
CREATE WIDGET TEXT schema DEFAULT "dev_prashanth_subrahmanyam_system_bronze";

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Show Current State (Before Migration)

-- COMMAND ----------

SELECT 
    table_name,
    rule_name,
    severity,
    enabled,
    description
FROM ${catalog}.${schema}.dq_rules
WHERE table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses', 'usage')
  AND severity = 'critical'
ORDER BY table_name, rule_name;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Migrate column_lineage Rules

-- COMMAND ----------

UPDATE ${catalog}.${schema}.dq_rules
SET 
    severity = 'warning',
    description = CASE 
        WHEN rule_name = 'valid_source_column' 
        THEN 'Source column name should be present (NULL legitimate for CREATE operations)'
        WHEN rule_name = 'valid_target_column'
        THEN 'Target column name should be present (NULL legitimate for DROP operations)'
        ELSE description
    END,
    updated_by = 'migration_script',
    updated_at = current_timestamp()
WHERE table_name = 'column_lineage'
  AND rule_name IN ('valid_source_column', 'valid_target_column')
  AND severity = 'critical';

SELECT 'column_lineage rules updated: ' || CAST(ROW_COUNT() AS STRING) as result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Migrate clusters Rules

-- COMMAND ----------

UPDATE ${catalog}.${schema}.dq_rules
SET 
    severity = 'warning',
    description = CASE 
        WHEN rule_name = 'valid_cluster_id' 
        THEN 'Cluster ID should be present for resource tracking'
        WHEN rule_name = 'valid_cluster_name'
        THEN 'Cluster name should be present for identification'
        WHEN rule_name = 'valid_state'
        THEN 'Cluster state should be present for tracking'
        ELSE description
    END,
    updated_by = 'migration_script',
    updated_at = current_timestamp()
WHERE table_name = 'clusters'
  AND rule_name IN ('valid_cluster_id', 'valid_cluster_name', 'valid_state')
  AND severity = 'critical';

SELECT 'clusters rules updated: ' || CAST(ROW_COUNT() AS STRING) as result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Migrate table_lineage Rules

-- COMMAND ----------

UPDATE ${catalog}.${schema}.dq_rules
SET 
    severity = 'warning',
    description = CASE 
        WHEN rule_name = 'valid_source_table' 
        THEN 'Source table name should be present for lineage tracking'
        WHEN rule_name = 'valid_target_table'
        THEN 'Target table name should be present for lineage tracking'
        ELSE description
    END,
    updated_by = 'migration_script',
    updated_at = current_timestamp()
WHERE table_name = 'table_lineage'
  AND rule_name IN ('valid_source_table', 'valid_target_table')
  AND severity = 'critical';

SELECT 'table_lineage rules updated: ' || CAST(ROW_COUNT() AS STRING) as result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Migrate warehouses Rules

-- COMMAND ----------

UPDATE ${catalog}.${schema}.dq_rules
SET 
    severity = 'warning',
    description = CASE 
        WHEN rule_name = 'valid_warehouse_id' 
        THEN 'Warehouse ID should be present for resource tracking'
        WHEN rule_name = 'valid_warehouse_name'
        THEN 'Warehouse name should be present for identification'
        WHEN rule_name = 'valid_state'
        THEN 'Warehouse state should be present for tracking'
        ELSE description
    END,
    updated_by = 'migration_script',
    updated_at = current_timestamp()
WHERE table_name = 'warehouses'
  AND rule_name IN ('valid_warehouse_id', 'valid_warehouse_name', 'valid_state')
  AND severity = 'critical';

SELECT 'warehouses rules updated: ' || CAST(ROW_COUNT() AS STRING) as result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Migrate usage Rules

-- COMMAND ----------

UPDATE ${catalog}.${schema}.dq_rules
SET 
    severity = 'warning',
    description = CASE 
        WHEN rule_name = 'valid_usage_date' 
        THEN 'Usage date should be present (NULL legitimate for account-level aggregations)'
        WHEN rule_name = 'valid_workspace_id'
        THEN 'Workspace ID should be present (NULL legitimate for account-level usage)'
        ELSE description
    END,
    updated_by = 'migration_script',
    updated_at = current_timestamp()
WHERE table_name = 'usage'
  AND rule_name IN ('valid_usage_date', 'valid_workspace_id')
  AND severity = 'critical';

SELECT 'usage rules updated: ' || CAST(ROW_COUNT() AS STRING) as result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Show Updated State (After Migration)

-- COMMAND ----------

SELECT 
    table_name,
    rule_name,
    severity,
    enabled,
    description
FROM ${catalog}.${schema}.dq_rules
WHERE table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses', 'usage')
ORDER BY table_name, severity DESC, rule_name;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Summary Statistics

-- COMMAND ----------

SELECT 
    table_name,
    severity,
    COUNT(*) as rule_count,
    SUM(CASE WHEN enabled THEN 1 ELSE 0 END) as enabled_count
FROM ${catalog}.${schema}.dq_rules
WHERE table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses', 'usage')
GROUP BY table_name, severity
ORDER BY table_name, severity;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ✅ Migration Complete!
-- MAGIC 
-- MAGIC **Next Steps:**
-- MAGIC 1. Re-run your Bronze streaming pipelines to pick up the new rules
-- MAGIC 2. Verify that record drop counts go to 0 (or near 0)
-- MAGIC 3. Check DLT expectations metrics in the pipeline UI
-- MAGIC 
-- MAGIC **Note:** The pipelines dynamically load rules at runtime via `dq_rules_loader.py`
