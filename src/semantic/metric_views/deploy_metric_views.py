# Databricks notebook source
"""
Metric Views Deployment Script
==============================

Deploys all Metric View YAMLs as SQL views with METRICS LANGUAGE extension.
Metric Views enable Genie natural language queries against Gold layer tables.

Agent Domain Organization:
- Cost: cost_analytics, commit_tracking
- Performance: query_performance, cluster_utilization, cluster_efficiency
- Reliability: job_performance
- Security: security_events, governance_analytics
- Quality: data_quality, ml_intelligence

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
from typing import Dict, List, Tuple

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
print(f"✓ Schema {catalog}.{METRIC_VIEW_SCHEMA} ready")

# COMMAND ----------

def substitute_variables(yaml_content: str, catalog: str, gold_schema: str) -> str:
    """Replace ${catalog} and ${gold_schema} placeholders in YAML content."""
    return yaml_content.replace('${catalog}', catalog).replace('${gold_schema}', gold_schema)


def read_workspace_file(file_path: str) -> str:
    """
    Read file from Databricks workspace or local filesystem.
    
    In serverless notebooks, /Workspace paths are accessible via standard file I/O.
    
    Args:
        file_path: Path to file (e.g., /Workspace/... or local path)
        
    Returns:
        File content as string
    """
    # Method 1: Direct file read (works for /Workspace paths in serverless)
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e1:
        print(f"  Direct file read failed for {file_path}: {e1}")
    
    # Method 2: Try Workspace API as fallback
    try:
        import base64
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        response = w.workspace.export(file_path, format="SOURCE")
        content = base64.b64decode(response.content).decode('utf-8')
        return content
    except Exception as e2:
        print(f"  Workspace API failed: {e2}")
    
    raise Exception(f"Cannot read file from any method: {file_path}")


def load_metric_view_yaml(file_path: str, catalog: str, gold_schema: str) -> dict:
    """Load and parse a metric view YAML file with variable substitution."""
    content = read_workspace_file(file_path)

    # Substitute variables
    content = substitute_variables(content, catalog, gold_schema)

    return yaml.safe_load(content)


def generate_metric_view_sql(view_name: str, config: dict) -> str:
    """
    Generate CREATE VIEW ... WITH METRICS LANGUAGE YAML statement.
    
    Per Metric Views v1.1 spec:
    - Name is in CREATE VIEW statement, NOT in YAML
    - Uses $$ delimiters for YAML content
    """
    # Remove 'name' field if present (v1.1 doesn't use it in YAML)
    if 'name' in config:
        del config['name']

    # The YAML content for the metric view
    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)

    # Extract comment for the view (if present in YAML)
    comment = config.get('comment', '').replace("'", "''").strip()
    if len(comment) > 200:
        comment = comment[:197] + "..."

    sql = f"""
CREATE OR REPLACE VIEW {view_name}
WITH METRICS
LANGUAGE YAML
COMMENT '{comment}'
AS $$
{yaml_content}
$$
"""
    return sql


def deploy_metric_view(view_name: str, yaml_file: str, catalog: str, gold_schema: str, 
                       domain: str = "General") -> bool:
    """Deploy a single metric view from YAML file."""
    try:
        print(f"\n[{domain}] Deploying metric view: {view_name}")

        # Load YAML with variable substitution
        config = load_metric_view_yaml(yaml_file, catalog, gold_schema)

        # Full view name with catalog and schema
        full_view_name = f"{catalog}.{METRIC_VIEW_SCHEMA}.{view_name}"

        # Drop existing view/table to avoid conflicts
        try:
            spark.sql(f"DROP VIEW IF EXISTS {full_view_name}")
            spark.sql(f"DROP TABLE IF EXISTS {full_view_name}")
        except Exception:
            pass

        # Generate and execute SQL
        sql = generate_metric_view_sql(full_view_name, config)
        spark.sql(sql)

        print(f"  ✓ Successfully deployed: {full_view_name}")
        return True

    except Exception as e:
        print(f"  ✗ Failed to deploy {view_name}: {str(e)}")
        return False

# COMMAND ----------

# Find metric views directory
# Get workspace path for Databricks notebook execution
try:
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    # Convert notebook path to workspace path
    workspace_root = "/Workspace" + "/".join(notebook_path.split("/")[:-1])
    metric_views_dir = workspace_root
    print(f"Using workspace path: {metric_views_dir}")
except Exception as e:
    # Fallback for local testing
    metric_views_dir = str(Path(__file__).parent) if '__file__' in dir() else "."
    print(f"Using local path: {metric_views_dir}")

# COMMAND ----------

# Metric Views organized by Agent Domain
# Each tuple: (view_name, yaml_file, agent_domain)
METRIC_VIEWS: List[Tuple[str, str, str]] = [
    # === Cost Domain ===
    ("cost_analytics", "cost_analytics.yaml", "Cost"),
    ("commit_tracking", "commit_tracking.yaml", "Cost"),
    
    # === Performance Domain ===
    ("query_performance", "query_performance.yaml", "Performance"),
    ("cluster_utilization", "cluster_utilization.yaml", "Performance"),
    ("cluster_efficiency", "cluster_efficiency.yaml", "Performance"),
    
    # === Reliability Domain ===
    ("job_performance", "job_performance.yaml", "Reliability"),
    
    # === Security Domain ===
    ("security_events", "security_events.yaml", "Security"),
    ("governance_analytics", "governance_analytics.yaml", "Security"),
    
    # === Quality Domain ===
    ("data_quality", "data_quality.yaml", "Quality"),
    ("ml_intelligence", "ml_intelligence.yaml", "Quality"),
]

# COMMAND ----------

# Deploy all metric views
print("=" * 60)
print("Starting Metric View Deployment")
print("=" * 60)
print(f"Total metric views to deploy: {len(METRIC_VIEWS)}")

results: List[Tuple[str, str, bool]] = []

for view_name, yaml_file, domain in METRIC_VIEWS:
    # Build full path (works for both workspace and local)
    if isinstance(metric_views_dir, str) and metric_views_dir.startswith("/Workspace"):
        yaml_path = f"{metric_views_dir}/{yaml_file}"
    else:
        yaml_path = str(Path(metric_views_dir) / yaml_file)
    
    # Try to deploy - the read_workspace_file function handles file not found
    success = deploy_metric_view(view_name, yaml_path, catalog, gold_schema, domain)
    results.append((view_name, domain, success))

# COMMAND ----------

# Summary by Agent Domain
print("\n" + "=" * 60)
print("Metric View Deployment Summary")
print("=" * 60)

# Group by domain
domain_results: Dict[str, List[Tuple[str, bool]]] = {}
for view_name, domain, success in results:
    if domain not in domain_results:
        domain_results[domain] = []
    domain_results[domain].append((view_name, success))

# Print by domain
for domain in ["Cost", "Performance", "Reliability", "Security", "Quality"]:
    if domain in domain_results:
        views = domain_results[domain]
        success_count = sum(1 for _, s in views if s)
        total_count = len(views)
        status = "✓" if success_count == total_count else "✗"
        print(f"\n{status} {domain}: {success_count}/{total_count}")
        for view_name, success in views:
            status_icon = "✓" if success else "✗"
            print(f"    {status_icon} {view_name}")

# Overall summary
print("\n" + "-" * 60)
successful = sum(1 for _, _, success in results if success)
failed = sum(1 for _, _, success in results if not success)
print(f"Total: {len(results)} | Successful: {successful} | Failed: {failed}")

# COMMAND ----------

# List failed views if any
if failed > 0:
    print("\n" + "=" * 60)
    print("⚠ Failed Metric Views")
    print("=" * 60)
    for view_name, domain, success in results:
        if not success:
            print(f"  [{domain}] {view_name}")

# COMMAND ----------

# Verify deployed views
print("\n" + "=" * 60)
print("Deployed Metric Views in Catalog")
print("=" * 60)

try:
    views_df = spark.sql(f"SHOW VIEWS IN {catalog}.{METRIC_VIEW_SCHEMA}")
    display(views_df)
except Exception as e:
    print(f"Could not list views: {e}")

# COMMAND ----------

# Query to verify metric view functionality
print("\n" + "=" * 60)
print("Metric View Verification Queries")
print("=" * 60)

verification_queries = [
    ("cost_analytics", "SELECT COUNT(*) as total FROM {schema}.cost_analytics LIMIT 1"),
    ("job_performance", "SELECT COUNT(*) as total FROM {schema}.job_performance LIMIT 1"),
]

for view_name, query in verification_queries:
    full_schema = f"{catalog}.{METRIC_VIEW_SCHEMA}"
    try:
        result = spark.sql(query.format(schema=full_schema)).first()
        print(f"  ✓ {view_name}: Query successful")
    except Exception as e:
        print(f"  ✗ {view_name}: {str(e)[:50]}...")

# COMMAND ----------

# Exit with appropriate status
if failed > 0:
    error_msg = f"FAILED: {failed} metric views failed to deploy"
    print(f"\n❌ {error_msg}")
    raise RuntimeError(error_msg)
else:
    success_msg = f"SUCCESS: {successful} metric views deployed to {catalog}.{METRIC_VIEW_SCHEMA}"
    print(f"\n✅ {success_msg}")
    dbutils.notebook.exit(success_msg)
