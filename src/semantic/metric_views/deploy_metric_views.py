# Databricks notebook source
"""
Metric Views Deployment Script
==============================

Deploys all Metric View YAMLs as SQL views with METRICS LANGUAGE extension.
Metric Views enable Genie natural language queries against Gold layer tables.

Usage:
    Run as a notebook or job task after Gold layer setup.

Reference:
    https://docs.databricks.com/sql/language-manual/sql-ref-syntax-ddl-create-metric-view.html
"""

# COMMAND ----------

import yaml
import os
from pathlib import Path
from string import Template

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

print(f"Deploying Metric Views to: {catalog}.{gold_schema}")

# COMMAND ----------

# Schema for metric views (separate from data tables)
METRIC_VIEW_SCHEMA = "metric_views"

# Create metric view schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{METRIC_VIEW_SCHEMA}")

# COMMAND ----------

def substitute_variables(yaml_content: str, catalog: str, gold_schema: str) -> str:
    """Replace ${catalog} and ${gold_schema} placeholders in YAML content."""
    template = Template(yaml_content.replace('${', '$').replace('}', ''))
    # Need to handle the variable syntax properly
    return yaml_content.replace('${catalog}', catalog).replace('${gold_schema}', gold_schema)


def load_metric_view_yaml(file_path: str, catalog: str, gold_schema: str) -> dict:
    """Load and parse a metric view YAML file with variable substitution."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Substitute variables
    content = substitute_variables(content, catalog, gold_schema)

    return yaml.safe_load(content)


def generate_metric_view_sql(view_name: str, config: dict) -> str:
    """Generate CREATE VIEW ... WITH METRICS LANGUAGE YAML statement."""

    # The YAML content for the metric view (without the catalog/schema variables)
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)

    # Escape single quotes in YAML for SQL
    yaml_escaped = yaml_content.replace("'", "''")

    sql = f"""
CREATE OR REPLACE VIEW {view_name}
WITH METRICS LANGUAGE YAML
AS '''
{yaml_escaped}
'''
"""
    return sql


def deploy_metric_view(view_name: str, yaml_file: str, catalog: str, gold_schema: str) -> bool:
    """Deploy a single metric view from YAML file."""
    try:
        print(f"Deploying metric view: {view_name}")

        # Load YAML with variable substitution
        config = load_metric_view_yaml(yaml_file, catalog, gold_schema)

        # Full view name with catalog and schema
        full_view_name = f"{catalog}.{METRIC_VIEW_SCHEMA}.{view_name}"

        # Generate SQL
        sql = generate_metric_view_sql(full_view_name, config)

        # Execute
        spark.sql(sql)

        print(f"  ✓ Successfully deployed: {full_view_name}")
        return True

    except Exception as e:
        print(f"  ✗ Failed to deploy {view_name}: {str(e)}")
        return False

# COMMAND ----------

# Find all metric view YAML files
metric_views_dir = Path(__file__).parent if '__file__' in dir() else Path(".")

# List of metric views to deploy
METRIC_VIEWS = [
    ("cost_analytics", "cost_analytics.yaml"),
    ("job_performance", "job_performance.yaml"),
    ("query_performance", "query_performance.yaml"),
    ("cluster_utilization", "cluster_utilization.yaml"),
    ("security_events", "security_events.yaml"),
    ("commit_tracking", "commit_tracking.yaml"),
]

# COMMAND ----------

# Deploy all metric views
results = []
for view_name, yaml_file in METRIC_VIEWS:
    yaml_path = metric_views_dir / yaml_file
    if yaml_path.exists():
        success = deploy_metric_view(view_name, str(yaml_path), catalog, gold_schema)
        results.append((view_name, success))
    else:
        print(f"  ⚠ YAML file not found: {yaml_file}")
        results.append((view_name, False))

# COMMAND ----------

# Summary
print("\n" + "=" * 50)
print("Metric View Deployment Summary")
print("=" * 50)

successful = sum(1 for _, success in results if success)
failed = sum(1 for _, success in results if not success)

print(f"\nTotal: {len(results)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

if failed > 0:
    print("\nFailed views:")
    for view_name, success in results:
        if not success:
            print(f"  - {view_name}")

# COMMAND ----------

# Verify deployed views
print("\n" + "=" * 50)
print("Deployed Metric Views")
print("=" * 50)

views_df = spark.sql(f"SHOW VIEWS IN {catalog}.{METRIC_VIEW_SCHEMA}")
display(views_df)

# COMMAND ----------

# Exit with error if any deployments failed
if failed > 0:
    dbutils.notebook.exit(f"FAILED: {failed} metric views failed to deploy")
else:
    dbutils.notebook.exit(f"SUCCESS: {successful} metric views deployed")
