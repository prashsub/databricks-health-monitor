# 23 - Metric Views Deployment Guide

## Quick Start

### Deploy via Asset Bundle

```bash
# Validate configuration
databricks bundle validate -t dev

# Deploy resources
databricks bundle deploy -t dev

# Run metric view deployment job
databricks bundle run -t dev metric_view_deployment_job
```

## Architecture

```
YAML Files                    Deployment Script                Output
───────────                   ─────────────────                ──────
cost_analytics.yaml    →                                     mv_cost_analytics
commit_tracking.yaml   →                                     mv_commit_tracking
query_performance.yaml →      deploy_metric_views.py   →     mv_query_performance
cluster_utilization.yaml →           │                       mv_cluster_utilization
...                    →             │                       ...
                                     ▼
                              Gold Schema (mv_*)
```

## Configuration

### Widget Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `catalog` | `health_monitor` | Target Unity Catalog |
| `gold_schema` | `gold` | Schema for metric views |
| `feature_schema` | `features` | Schema for ML predictions |

### Naming Convention

All metric views use the `mv_` prefix:

```
{catalog}.{gold_schema}.mv_{view_name}

Example: health_monitor.gold.mv_cost_analytics
```

## Metric Views Registry

The deployment script maintains a registry of all metric views:

```python
METRIC_VIEWS = [
    # Cost Domain
    ("cost_analytics", "cost_analytics.yaml", "Cost"),
    ("commit_tracking", "commit_tracking.yaml", "Cost"),
    
    # Performance Domain
    ("query_performance", "query_performance.yaml", "Performance"),
    ("cluster_utilization", "cluster_utilization.yaml", "Performance"),
    ("cluster_efficiency", "cluster_efficiency.yaml", "Performance"),
    
    # Reliability Domain
    ("job_performance", "job_performance.yaml", "Reliability"),
    
    # Security Domain
    ("security_events", "security_events.yaml", "Security"),
    ("governance_analytics", "governance_analytics.yaml", "Security"),
    
    # Quality Domain
    ("data_quality", "data_quality.yaml", "Quality"),
    ("ml_intelligence", "ml_intelligence.yaml", "Quality"),
]
```

## Prerequisites

### Source Tables

Each metric view requires its source table to exist:

| Metric View | Source Table | Prerequisite Job |
|-------------|--------------|------------------|
| `mv_cost_analytics` | `fact_usage` | Gold pipeline |
| `mv_commit_tracking` | `fact_usage` | Gold pipeline |
| `mv_query_performance` | `fact_query_history` | Gold pipeline |
| `mv_cluster_utilization` | `fact_node_timeline` | Gold pipeline |
| `mv_cluster_efficiency` | `fact_node_timeline` | Gold pipeline |
| `mv_job_performance` | `fact_job_run_timeline` | Gold pipeline |
| `mv_security_events` | `fact_audit_logs` | Gold pipeline |
| `mv_governance_analytics` | `fact_table_lineage` | Gold pipeline |
| `mv_data_quality` | `information_schema.tables` | Built-in |
| `mv_ml_intelligence` | `cost_anomaly_predictions` | ML inference pipeline |

### ML Pipeline Dependencies

For `mv_ml_intelligence`, the ML pipeline must run first:

```bash
# Run ML pipeline chain
databricks bundle run -t dev ml_feature_pipeline
databricks bundle run -t dev ml_training_pipeline
databricks bundle run -t dev ml_inference_pipeline
```

**Alternative**: Run the master orchestrator which includes ML:

```bash
databricks bundle run -t dev master_setup_orchestrator
```

## Error Handling

### Strict Failure Policy

All metric views are **required**. The deployment job:

1. Attempts to deploy all views
2. Collects success/failure status for each
3. Logs detailed results
4. Fails the job if ANY view fails

### Error Reporting

On failure, the job provides:

```
============================================================
❌ METRIC VIEW DEPLOYMENT FAILED
============================================================
Total Views: 10 | Success: 9 | Failed: 1

✓ Cost Domain (2/2) [8.5s]
  ✓ cost_analytics (4.2s)
  ✓ commit_tracking (4.3s)
✓ Performance Domain (3/3) [12.1s]
...
✗ Quality Domain (1/2) [15.6s]
  ✓ data_quality (5.2s)
  ✗ ml_intelligence (10.4s)
    ERROR: Source table 'cost_anomaly_predictions' does not exist

FAILED VIEWS:
1. ml_intelligence (Quality): Source table does not exist
```

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Source table not found | Prerequisites not run | Run Gold pipeline first |
| `UNRESOLVED_COLUMN` | Column doesn't exist | Verify column in source table schema |
| `Unrecognized field "name"` | Invalid YAML | Remove `name:` field from YAML |
| `DATATYPE_MISMATCH` | Type mismatch in expression | Use `= 1` for BIGINT flags |
| Permission denied | Missing grants | Grant SELECT on source tables |

## Deployment Output

### Success Output

```
============================================================
METRIC VIEW DEPLOYMENT SUMMARY
============================================================
Timestamp: 2025-01-01T10:30:45Z
Target: health_monitor.gold (with mv_ prefix)
Total Views: 10 | Success: 10 | Failed: 0
Total Duration: 45.23s

✓ Cost Domain (2/2) [8.5s]
  ✓ mv_cost_analytics (4.2s)
  ✓ mv_commit_tracking (4.3s)
✓ Performance Domain (3/3) [12.1s]
  ✓ mv_query_performance (3.8s)
  ✓ mv_cluster_utilization (4.1s)
  ✓ mv_cluster_efficiency (4.2s)
✓ Reliability Domain (1/1) [3.8s]
  ✓ mv_job_performance (3.8s)
✓ Security Domain (2/2) [7.2s]
  ✓ mv_security_events (3.5s)
  ✓ mv_governance_analytics (3.7s)
✓ Quality Domain (2/2) [13.6s]
  ✓ mv_data_quality (5.2s)
  ✓ mv_ml_intelligence (8.4s)

✅ SUCCESS: All 10 metric views deployed to health_monitor.gold
============================================================
```

## Verification

### List All Metric Views

```sql
-- Show all metric views
SHOW VIEWS IN health_monitor.gold LIKE 'mv_*';
```

### Verify View Type

```sql
-- Confirm it's a METRIC_VIEW
DESCRIBE EXTENDED health_monitor.gold.mv_cost_analytics;

-- Should show: Type: METRIC_VIEW
```

### Test Query

```sql
-- Test with MEASURE function
SELECT 
    workspace_name,
    MEASURE(total_cost) as spend
FROM health_monitor.gold.mv_cost_analytics
GROUP BY workspace_name
LIMIT 5;
```

### Full Validation Script

```sql
-- Validate all metric views exist and are queryable
WITH views AS (
    SELECT 'mv_cost_analytics' as view_name UNION ALL
    SELECT 'mv_commit_tracking' UNION ALL
    SELECT 'mv_query_performance' UNION ALL
    SELECT 'mv_cluster_utilization' UNION ALL
    SELECT 'mv_cluster_efficiency' UNION ALL
    SELECT 'mv_job_performance' UNION ALL
    SELECT 'mv_security_events' UNION ALL
    SELECT 'mv_governance_analytics' UNION ALL
    SELECT 'mv_data_quality' UNION ALL
    SELECT 'mv_ml_intelligence'
),
existing AS (
    SELECT table_name as view_name
    FROM information_schema.views
    WHERE table_schema = 'gold'
      AND table_name LIKE 'mv_%'
)
SELECT 
    v.view_name,
    CASE WHEN e.view_name IS NOT NULL THEN '✓' ELSE '✗' END as status
FROM views v
LEFT JOIN existing e ON v.view_name = e.view_name;
```

## Adding New Metric Views

### 1. Create YAML Definition

```yaml
# src/semantic/metric_views/my_new_view.yaml
version: "1.1"
comment: >
  PURPOSE: Description of what this view provides.
  BEST FOR: Question 1 | Question 2 | Question 3
  NOT FOR: Redirections to other assets
  DIMENSIONS: dim1, dim2, dim3
  MEASURES: measure1, measure2, measure3
  SOURCE: source_table (domain)
  JOINS: dim_table (description)
  NOTE: Important caveats

source: ${catalog}.${gold_schema}.source_table

dimensions:
  - name: my_dimension
    expr: source.column
    comment: Description
    display_name: My Dimension
    synonyms: [alt1, alt2]

measures:
  - name: my_measure
    expr: SUM(source.value)
    comment: Description
    format:
      type: number
```

### 2. Register in Deployment Script

Edit `deploy_metric_views.py`:

```python
METRIC_VIEWS = [
    # ... existing views ...
    ("my_new_view", "my_new_view.yaml", "YourDomain"),
]
```

### 3. Deploy

```bash
databricks bundle deploy -t dev
databricks bundle run -t dev metric_view_deployment_job
```

## Redeployment

### Redeploy All Views

```bash
# Simply re-run the deployment job
databricks bundle run -t dev metric_view_deployment_job
```

The script uses `CREATE OR REPLACE VIEW`, so existing views are updated in place.

### Redeploy Single View

Currently, the script deploys all views. To redeploy a single view:

1. Run the full deployment job (fast, ~45s total)
2. Or manually execute the CREATE VIEW statement

### Clean Deployment

To completely remove and redeploy:

```sql
-- Drop all metric views
DROP VIEW IF EXISTS health_monitor.gold.mv_cost_analytics;
DROP VIEW IF EXISTS health_monitor.gold.mv_commit_tracking;
-- ... etc

-- Then redeploy
databricks bundle run -t dev metric_view_deployment_job
```

## CI/CD Integration

### Pre-Deployment Validation

```bash
# Validate YAML syntax
python -c "import yaml; [yaml.safe_load(open(f)) for f in glob.glob('src/semantic/metric_views/*.yaml')]"

# Validate bundle
databricks bundle validate -t dev
```

### Deployment Pipeline

```yaml
# .github/workflows/deploy.yml (example)
jobs:
  deploy-metric-views:
    steps:
      - name: Validate
        run: databricks bundle validate -t ${{ env.TARGET }}
      
      - name: Deploy
        run: databricks bundle deploy -t ${{ env.TARGET }}
      
      - name: Run Metric View Deployment
        run: databricks bundle run -t ${{ env.TARGET }} metric_view_deployment_job
```

## Related Documentation

- [20-Metric Views Index](20-metric-views-index.md)
- [22-Metric Views Architecture](22-metric-views-architecture.md)
- [24-Metric Views Reference](24-metric-views-reference.md)
- [Domain Documentation](by-domain/)

