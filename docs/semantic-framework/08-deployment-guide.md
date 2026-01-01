# 08 - Deployment Guide

## Overview

This guide covers deploying the 60 TVFs to Unity Catalog using Databricks Asset Bundles. The deployment is automated through a job that processes SQL files and creates functions in the specified catalog and schema.

## Prerequisites

### 1. Databricks CLI Configuration

```bash
# Verify CLI version (requires 0.200+)
databricks --version

# Configure authentication profile
databricks auth login --host https://<workspace>.cloud.databricks.com --profile DEFAULT

# Verify authentication
databricks auth profiles
```

### 2. Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| USE CATALOG | Target catalog | Access to catalog |
| USE SCHEMA | Target schema | Access to schema |
| CREATE FUNCTION | Target schema | Create TVFs |
| SELECT | Gold layer tables | TVFs query these tables |

### 3. Gold Layer Tables

TVFs depend on these Gold layer tables being populated:
- `fact_usage`
- `fact_job_run_timeline`
- `fact_query_history`
- `fact_audit_logs`
- `fact_node_timeline`
- `fact_table_lineage`
- `dim_workspace`
- `dim_job`
- `dim_warehouse`
- `dim_cluster`
- `dim_sku`

## Deployment Process

### Step 1: Validate Bundle Configuration

```bash
# Navigate to project root
cd /path/to/DatabricksHealthMonitor

# Validate bundle configuration
databricks bundle validate -t dev
```

Expected output:
```
✓ Bundle successfully validated
```

### Step 2: Deploy Bundle

```bash
# Deploy all resources including TVF job
databricks bundle deploy -t dev
```

Expected output:
```
Deploying resources...
✓ Updating deployment state...
✓ Deploying resources...
Deployment complete!
```

### Step 3: Run TVF Deployment Job

```bash
# Execute the TVF deployment job
databricks bundle run -t dev tvf_deployment_job
```

### Step 4: Monitor Deployment

The job outputs detailed progress including:
- Files processed
- TVFs created per file
- Errors encountered
- Final verification count

**Expected Final Output**:
```
================================================================================
📊 DEPLOYMENT SUMMARY
================================================================================

📁 Results by File:
File                           Success     Failed      Total         Status
────────────────────────────────────────────────────────────────────────────
cost_tvfs.sql                       15          0         15           ✓ OK
reliability_tvfs.sql                12          0         12           ✓ OK
performance_tvfs.sql                10          0         10           ✓ OK
compute_tvfs.sql                     6          0          6           ✓ OK
security_tvfs.sql                   10          0         10           ✓ OK
quality_tvfs.sql                     7          0          7           ✓ OK
────────────────────────────────────────────────────────────────────────────
TOTAL                               60          0         60
================================================================================

✅ SUCCESSFULLY DEPLOYED TVFs:

💰 COST AGENT (15 TVFs):
   • get_top_cost_contributors
   • get_cost_trend_by_sku
   • get_cost_by_owner
   ... (12 more)

🔄 RELIABILITY AGENT (12 TVFs):
   • get_failed_jobs_summary
   • get_job_success_rates
   ... (10 more)

⚡ PERFORMANCE AGENT (16 TVFs):
   • get_slow_queries
   • get_query_latency_percentiles
   ... (14 more)

🔒 SECURITY AGENT (10 TVFs):
   • get_user_activity_summary
   ... (9 more)

📋 QUALITY AGENT (7 TVFs):
   • get_table_freshness
   ... (6 more)

================================================================================
✅ Verified 60 TVFs in Unity Catalog
================================================================================

Notebook exited: SUCCESS: All 60 TVFs deployed successfully!

📊 Summary by Agent Domain:
   🔄 RELIABILITY AGENT: 12 TVFs
   ✅ QUALITY AGENT: 7 TVFs
   ⚡ PERFORMANCE AGENT (Compute): 6 TVFs
   ⚡ PERFORMANCE AGENT (Queries): 10 TVFs
   💰 COST AGENT: 15 TVFs
   🔒 SECURITY AGENT: 10 TVFs

🎯 Target: <catalog>.<schema>
📁 Total Files: 6
✅ Total TVFs: 60
```

## Verification

### Verify TVFs in Unity Catalog

```sql
-- List all deployed TVFs
SELECT 
    function_name,
    function_type,
    data_type,
    created
FROM system.information_schema.routines
WHERE routine_catalog = '<catalog>'
  AND routine_schema = '<schema>'
  AND routine_type = 'FUNCTION'
ORDER BY function_name;
```

### Test a Sample TVF

```sql
-- Test cost TVF
SELECT * FROM TABLE(<catalog>.<schema>.get_top_cost_contributors(
    '2024-12-01', '2024-12-31', 5
));

-- Test reliability TVF  
SELECT * FROM TABLE(<catalog>.<schema>.get_failed_jobs_summary(7, 1));

-- Test performance TVF
SELECT * FROM TABLE(<catalog>.<schema>.get_slow_queries(7, 30));
```

## Troubleshooting

### Error: Authentication Failed

```bash
Error: Invalid access token
```

**Solution**:
```bash
# Re-authenticate
databricks auth login --host https://<workspace>.cloud.databricks.com --profile DEFAULT
```

### Error: Schema Does Not Exist

```
[SCHEMA_NOT_FOUND] Schema '<schema>' not found
```

**Solution**: Ensure Gold layer setup job has run first to create schemas.

### Error: Table Does Not Exist

```
[TABLE_NOT_FOUND] Table '<catalog>.<schema>.fact_usage' not found
```

**Solution**: Run the Gold layer merge job to populate tables before deploying TVFs.

### Error: Permission Denied

```
[ACCESS_DENIED] User does not have permission CREATE FUNCTION
```

**Solution**: Request CREATE FUNCTION permission on the target schema.

### Error: Parameter with DEFAULT

```
[PARSE_SYNTAX_ERROR] parameter with DEFAULT must not be followed by parameter without DEFAULT
```

**Solution**: Ensure required parameters (without DEFAULT) come before optional parameters (with DEFAULT) in TVF definition.

### Error: LIMIT with Parameter

```
[INVALID_LIMIT_LIKE_EXPRESSION] limit expression must evaluate to a constant value
```

**Solution**: Use `ROW_NUMBER() ... WHERE rank <= param` instead of `LIMIT param`.

## Redeployment

### Redeploy All TVFs

```bash
# TVFs use CREATE OR REPLACE, so redeployment is safe
databricks bundle deploy -t dev
databricks bundle run -t dev tvf_deployment_job
```

### Deploy to Production

```bash
# Deploy to prod target
databricks bundle deploy -t prod

# Run deployment job
databricks bundle run -t prod tvf_deployment_job
```

## Job Configuration

### Asset Bundle Job Definition

```yaml
# resources/semantic/tvf_deployment_job.yml
resources:
  jobs:
    tvf_deployment_job:
      name: "[${bundle.target}] Health Monitor - TVF Deployment"
      description: "Deploys all Table-Valued Functions to Unity Catalog"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
      
      tasks:
        - task_key: deploy_all_tvfs
          environment_key: default
          notebook_task:
            notebook_path: ../../src/semantic/tvfs/deploy_tvfs.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
      
      tags:
        layer: semantic
        job_type: deployment
```

### SQL File Organization

```
src/semantic/tvfs/
├── deploy_tvfs.py       # Deployment orchestrator
├── cost_tvfs.sql        # 15 cost TVFs
├── reliability_tvfs.sql # 12 reliability TVFs
├── performance_tvfs.sql # 10 query performance TVFs
├── compute_tvfs.sql     # 6 compute optimization TVFs
├── security_tvfs.sql    # 10 security TVFs
└── quality_tvfs.sql     # 7 data quality TVFs
```

## Next Steps

- **[09-Usage Examples](09-usage-examples.md)**: Test with example queries
- **[Appendices/A-Quick Reference](appendices/A-quick-reference.md)**: Complete TVF reference

