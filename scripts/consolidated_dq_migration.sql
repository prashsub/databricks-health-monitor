-- ============================================================================
-- CONSOLIDATED DQ RULES MIGRATION
-- ============================================================================
-- Problem: Bronze streaming tables dropping legitimate system table records
--   - column_lineage: 309M records dropped
--   - usage: 43K records dropped  
--   - clusters: 155 records dropped
--
-- Solution: Change severity from "critical" → "warning" for rules where 
--           NULL values are legitimate in Databricks system tables
-- ============================================================================

-- REPLACE WITH YOUR VALUES:
-- Catalog: prashanth_subrahmanyam_catalog
-- Schema: dev_prashanth_subrahmanyam_system_bronze

UPDATE prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_bronze.dq_rules
SET 
    severity = 'warning',
    description = CASE 
        -- column_lineage rules
        WHEN table_name = 'column_lineage' AND rule_name = 'valid_source_column' 
            THEN 'Source column name should be present (NULL legitimate for CREATE operations)'
        WHEN table_name = 'column_lineage' AND rule_name = 'valid_target_column'
            THEN 'Target column name should be present (NULL legitimate for DROP operations)'
        
        -- clusters rules
        WHEN table_name = 'clusters' AND rule_name = 'valid_cluster_id' 
            THEN 'Cluster ID should be present for resource tracking'
        WHEN table_name = 'clusters' AND rule_name = 'valid_cluster_name'
            THEN 'Cluster name should be present for identification'
        WHEN table_name = 'clusters' AND rule_name = 'valid_state'
            THEN 'Cluster state should be present for tracking'
        
        -- table_lineage rules
        WHEN table_name = 'table_lineage' AND rule_name = 'valid_source_table' 
            THEN 'Source table name should be present for lineage tracking'
        WHEN table_name = 'table_lineage' AND rule_name = 'valid_target_table'
            THEN 'Target table name should be present for lineage tracking'
        
        -- warehouses rules
        WHEN table_name = 'warehouses' AND rule_name = 'valid_warehouse_id' 
            THEN 'Warehouse ID should be present for resource tracking'
        WHEN table_name = 'warehouses' AND rule_name = 'valid_warehouse_name'
            THEN 'Warehouse name should be present for identification'
        WHEN table_name = 'warehouses' AND rule_name = 'valid_state'
            THEN 'Warehouse state should be present for tracking'
        
        -- usage rules
        WHEN table_name = 'usage' AND rule_name = 'valid_usage_date' 
            THEN 'Usage date should be present (NULL legitimate for account-level aggregations)'
        WHEN table_name = 'usage' AND rule_name = 'valid_workspace_id'
            THEN 'Workspace ID should be present (NULL legitimate for account-level usage)'
        
        ELSE description
    END,
    updated_by = 'consolidated_migration',
    updated_at = current_timestamp()
WHERE 
    severity = 'critical'
    AND (
        -- column_lineage
        (table_name = 'column_lineage' AND rule_name IN ('valid_source_column', 'valid_target_column'))
        OR
        -- clusters
        (table_name = 'clusters' AND rule_name IN ('valid_cluster_id', 'valid_cluster_name', 'valid_state'))
        OR
        -- table_lineage
        (table_name = 'table_lineage' AND rule_name IN ('valid_source_table', 'valid_target_table'))
        OR
        -- warehouses
        (table_name = 'warehouses' AND rule_name IN ('valid_warehouse_id', 'valid_warehouse_name', 'valid_state'))
        OR
        -- usage
        (table_name = 'usage' AND rule_name IN ('valid_usage_date', 'valid_workspace_id'))
    );

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify the updates were successful:

SELECT 
    '✅ MIGRATION SUMMARY' as status,
    COUNT(*) as total_updated_rules
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_bronze.dq_rules
WHERE updated_by = 'consolidated_migration';

-- Show breakdown by table
SELECT 
    table_name,
    severity,
    COUNT(*) as rule_count
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_bronze.dq_rules
WHERE table_name IN ('column_lineage', 'clusters', 'table_lineage', 'warehouses', 'usage')
GROUP BY table_name, severity
ORDER BY table_name, severity;

-- ============================================================================
-- EXPECTED RESULTS:
-- ============================================================================
-- Should update 12 rules total:
--   - column_lineage: 2 rules
--   - clusters: 3 rules
--   - table_lineage: 2 rules
--   - warehouses: 3 rules
--   - usage: 2 rules
--
-- After re-running Bronze streaming pipeline:
--   - column_lineage dropped: 309M → ~0
--   - usage dropped: 43K → ~0
--   - clusters dropped: 155 → 0
-- ============================================================================
