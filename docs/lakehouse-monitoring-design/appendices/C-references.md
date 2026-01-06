# Appendix C - References

## Official Databricks Documentation

### Lakehouse Monitoring

| Topic | URL |
|-------|-----|
| **Overview** | https://docs.databricks.com/lakehouse-monitoring |
| **Create Monitor** | https://docs.databricks.com/lakehouse-monitoring/create-monitor.html |
| **Custom Metrics** | https://docs.databricks.com/lakehouse-monitoring/custom-metrics.html |
| **Monitor Types** | https://docs.databricks.com/lakehouse-monitoring/monitor-types.html |
| **API Reference** | https://docs.databricks.com/api/workspace/qualitymonitors |

### Databricks SDK

| Topic | URL |
|-------|-----|
| **Python SDK** | https://docs.databricks.com/dev-tools/sdk-python.html |
| **SDK Reference** | https://databricks-sdk-py.readthedocs.io/ |
| **Quality Monitors** | https://databricks-sdk-py.readthedocs.io/en/latest/workspace/catalog/quality_monitors.html |

### Asset Bundles

| Topic | URL |
|-------|-----|
| **Overview** | https://docs.databricks.com/dev-tools/bundles/ |
| **Job Resources** | https://docs.databricks.com/dev-tools/bundles/resources.html#jobs |
| **Bundle YAML** | https://docs.databricks.com/dev-tools/bundles/settings.html |

### Unity Catalog

| Topic | URL |
|-------|-----|
| **Overview** | https://docs.databricks.com/data-governance/unity-catalog/ |
| **Schemas** | https://docs.databricks.com/data-governance/unity-catalog/create-schemas.html |
| **Permissions** | https://docs.databricks.com/data-governance/unity-catalog/manage-privileges.html |

## Project Documentation

### Cursor Rules

| Rule | Path | Description |
|------|------|-------------|
| **Lakehouse Monitoring** | `.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc` | Development patterns |
| **Asset Bundles** | `.cursor/rules/common/02-databricks-asset-bundles.mdc` | Bundle configuration |
| **Python Imports** | `.cursor/rules/common/09-databricks-python-imports.mdc` | Pure Python pattern |

### Project Plans

| Document | Path | Description |
|----------|------|-------------|
| **Phase 3 Addendum** | `plans/phase3-addendum-3.4-lakehouse-monitoring.md` | Original design plan |
| **Gold Layer Design** | `plans/phase2-gold-layer-design.md` | Source table design |

### Source Code

| Component | Path | Description |
|-----------|------|-------------|
| **Monitor Utils** | `src/monitoring/monitor_utils.py` | Shared utilities |
| **Cost Monitor** | `src/monitoring/cost_monitor.py` | Cost domain metrics |
| **Job Monitor** | `src/monitoring/job_monitor.py` | Reliability metrics |
| **Query Monitor** | `src/monitoring/query_monitor.py` | Performance metrics |
| **Cluster Monitor** | `src/monitoring/cluster_monitor.py` | Utilization metrics |
| **Security Monitor** | `src/monitoring/security_monitor.py` | Audit metrics |
| **Documentation** | `src/monitoring/document_monitors.py` | Genie documentation |
| **Job YAML** | `resources/monitoring/lakehouse_monitors_job.yml` | Asset Bundle |

## API Reference

### MonitorMetric Class

```python
from databricks.sdk.service.catalog import MonitorMetric, MonitorMetricType

MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,  # or DERIVED, DRIFT
    name="metric_name",
    input_columns=[":table"],  # or specific column names
    definition="SQL expression",
    output_data_type='{"type":"struct","fields":[{"name":"output","type":"double"}]}'
)
```

### MonitorTimeSeries Class

```python
from databricks.sdk.service.catalog import MonitorTimeSeries

MonitorTimeSeries(
    timestamp_col="timestamp_column",
    granularities=["1 day", "1 hour"]
)
```

### MonitorCronSchedule Class

```python
from databricks.sdk.service.catalog import MonitorCronSchedule

MonitorCronSchedule(
    quartz_cron_expression="0 0 6 * * ?",  # Daily at 6 AM
    timezone_id="UTC"
)
```

### WorkspaceClient Quality Monitors

```python
from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient()

# Create
monitor = workspace_client.quality_monitors.create(
    table_name="catalog.schema.table",
    time_series=MonitorTimeSeries(...),
    custom_metrics=[...],
    ...
)

# Get
monitor = workspace_client.quality_monitors.get(table_name="catalog.schema.table")

# Update
workspace_client.quality_monitors.update(
    table_name="catalog.schema.table",
    custom_metrics=[...]  # Must include all metrics!
)

# Delete
workspace_client.quality_monitors.delete(table_name="catalog.schema.table")

# Refresh
workspace_client.quality_monitors.run_refresh(table_name="catalog.schema.table")
```

## SQL Reference

### System Tables

```sql
-- List all monitors
SELECT * FROM system.information_schema.lakehouse_monitors
WHERE table_catalog = 'your_catalog';

-- Monitor metrics
SELECT * FROM system.information_schema.lakehouse_monitor_metrics
WHERE table_name = 'your_table';

-- Table metadata
SELECT * FROM system.information_schema.tables
WHERE table_schema = 'your_schema_monitoring';

-- Column metadata
SELECT * FROM system.information_schema.columns
WHERE table_schema = 'your_schema_monitoring'
  AND table_name = 'fact_usage_profile_metrics';
```

### ALTER Statements

```sql
-- Add table comment
ALTER TABLE catalog.schema.table 
SET TBLPROPERTIES ('comment' = 'Description');

-- Add column comment
ALTER TABLE catalog.schema.table 
ALTER COLUMN column_name COMMENT 'Description';

-- Create schema
CREATE SCHEMA IF NOT EXISTS catalog.schema_monitoring;
```

## External Resources

### Databricks Blogs

| Title | URL |
|-------|-----|
| **Introducing Lakehouse Monitoring** | https://www.databricks.com/blog/introducing-lakehouse-monitoring |
| **Custom Metrics Deep Dive** | https://www.databricks.com/blog/lakehouse-monitoring-custom-metrics |

### GitHub Examples

| Repository | URL |
|------------|-----|
| **Bundle Examples** | https://github.com/databricks/bundle-examples |
| **SDK Examples** | https://github.com/databricks/databricks-sdk-py |

## Version Information

| Component | Version | Notes |
|-----------|---------|-------|
| **Databricks Runtime** | 13.3+ | Required for Lakehouse Monitoring |
| **Databricks SDK** | ≥0.28.0 | Required for MonitorMetric types |
| **Unity Catalog** | v1 | Required |

---

**Version:** 1.0  
**Last Updated:** January 2026




