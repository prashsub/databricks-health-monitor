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
dbutils.widgets.text("feature_schema", "features", "Feature Schema (for ML predictions)")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
feature_schema = dbutils.widgets.get("feature_schema")

print(f"Deploying Metric Views to: {catalog}.{gold_schema}")
print(f"Feature Schema: {catalog}.{feature_schema}")

# COMMAND ----------

# Schema for metric views (separate from data tables)
METRIC_VIEW_SCHEMA = "metric_views"

# Create metric view schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{METRIC_VIEW_SCHEMA}")
print(f"✓ Schema {catalog}.{METRIC_VIEW_SCHEMA} ready")

# COMMAND ----------

def substitute_variables(yaml_content: str, catalog: str, gold_schema: str, feature_schema: str = None) -> str:
    """Replace ${catalog}, ${gold_schema}, and ${feature_schema} placeholders in YAML content."""
    result = yaml_content.replace('${catalog}', catalog).replace('${gold_schema}', gold_schema)
    if feature_schema:
        result = result.replace('${feature_schema}', feature_schema)
    return result


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


def load_metric_view_yaml(file_path: str, catalog: str, gold_schema: str, feature_schema: str = None) -> dict:
    """Load and parse a metric view YAML file with variable substitution."""
    content = read_workspace_file(file_path)

    # Substitute variables
    content = substitute_variables(content, catalog, gold_schema, feature_schema)

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


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the catalog."""
    try:
        spark.sql(f"DESCRIBE TABLE {table_name}")
        return True
    except Exception:
        return False


# Mapping of tables to prerequisite jobs (in order of execution)
TABLE_PREREQUISITES = {
    # ML inference output tables require the full ML pipeline chain
    "cost_anomaly_predictions": [
        "ml_feature_pipeline",      # Creates feature tables
        "ml_training_pipeline",     # Trains and registers models
        "ml_inference_pipeline"     # Creates prediction tables
    ],
    "security_threat_predictions": [
        "ml_feature_pipeline",
        "ml_training_pipeline", 
        "ml_inference_pipeline"
    ],
    # Add more mappings as needed
}


def get_prerequisite_instructions(table_name: str) -> str:
    """Get instructions for running prerequisite jobs."""
    simple_name = table_name.split('.')[-1]
    
    if simple_name in TABLE_PREREQUISITES:
        jobs = TABLE_PREREQUISITES[simple_name]
        instructions = f"""
    ┌─────────────────────────────────────────────────────────────────────┐
    │  PREREQUISITE JOBS REQUIRED                                          │
    │  Table: {simple_name}                                                │
    │                                                                       │
    │  Run these jobs in order:                                             │
"""
        for i, job in enumerate(jobs, 1):
            instructions += f"    │    {i}. databricks bundle run -t dev {job:<40} │\n"
        
        instructions += """    │                                                                       │
    │  Or run the master orchestrator that includes ML setup:              │
    │    databricks bundle run -t dev master_setup_orchestrator            │
    └─────────────────────────────────────────────────────────────────────┘
"""
        return instructions
    else:
        return f"""
    ⚠ Table {simple_name} does not exist.
    
    Please ensure the appropriate data pipeline has been run to create this table.
"""


def deploy_metric_view(view_name: str, yaml_file: str, catalog: str, gold_schema: str,
                       feature_schema: str = None, domain: str = "General") -> Tuple[bool, str]:
    """Deploy a single metric view from YAML file.
    
    Returns:
        Tuple[bool, str]: (success, error_reason) where error_reason is empty string if success
    """
    try:
        print(f"\n[{domain}] Deploying metric view: {view_name}")

        # Load YAML with variable substitution
        config = load_metric_view_yaml(yaml_file, catalog, gold_schema, feature_schema)
        
        # Check if source table exists
        source_table = config.get('source', '')
        if source_table and not check_table_exists(source_table):
            error_reason = f"Source table does not exist: {source_table}"
            print(f"  ✗ {error_reason}")
            print(get_prerequisite_instructions(source_table))
            return (False, error_reason)

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
        return (True, "")

    except Exception as e:
        import traceback
        error_reason = str(e)
        print(f"  ✗ Failed to deploy {view_name}: {error_reason}")
        print(f"  Full traceback:\n{traceback.format_exc()}")
        return (False, error_reason)

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
# All metric views are REQUIRED - job fails if any view fails to deploy
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
    ("ml_intelligence", "ml_intelligence.yaml", "Quality"),  # Requires ML inference pipeline to have run
]

# COMMAND ----------

# Deploy all metric views
print("=" * 60)
print("Starting Metric View Deployment")
print("=" * 60)
print(f"Total metric views to deploy: {len(METRIC_VIEWS)}")

# Results: (view_name, domain, success, error_reason)
results: List[Tuple[str, str, bool, str]] = []

for view_name, yaml_file, domain in METRIC_VIEWS:
    # Build full path (works for both workspace and local)
    if isinstance(metric_views_dir, str) and metric_views_dir.startswith("/Workspace"):
        yaml_path = f"{metric_views_dir}/{yaml_file}"
    else:
        yaml_path = str(Path(metric_views_dir) / yaml_file)
    
    # Try to deploy - the read_workspace_file function handles file not found
    success, error_reason = deploy_metric_view(view_name, yaml_path, catalog, gold_schema, feature_schema, domain)
    results.append((view_name, domain, success, error_reason))

# COMMAND ----------

# Summary by Agent Domain
print("\n" + "=" * 60)
print("Metric View Deployment Summary")
print("=" * 60)

# Group by domain
domain_results: Dict[str, List[Tuple[str, bool, str]]] = {}
for view_name, domain, success, error_reason in results:
    if domain not in domain_results:
        domain_results[domain] = []
    domain_results[domain].append((view_name, success, error_reason))

# Print by domain
for domain in ["Cost", "Performance", "Reliability", "Security", "Quality"]:
    if domain in domain_results:
        views = domain_results[domain]
        success_count = sum(1 for _, s, _ in views if s)
        total_count = len(views)
        status = "✓" if success_count == total_count else "✗"
        print(f"\n{status} {domain}: {success_count}/{total_count}")
        for view_name, success, error_reason in views:
            status_icon = "✓" if success else "✗"
            if success:
                print(f"    {status_icon} {view_name}")
            else:
                print(f"    {status_icon} {view_name}: {error_reason}")

# Overall summary
print("\n" + "-" * 60)
successful = sum(1 for _, _, success, _ in results if success)
failed = sum(1 for _, _, success, _ in results if not success)
print(f"Total: {len(results)} | Successful: {successful} | Failed: {failed}")

# COMMAND ----------

# List failed views if any
if failed > 0:
    print("\n" + "=" * 60)
    print("❌ Failed Metric Views")
    print("=" * 60)
    for view_name, domain, success, error_reason in results:
        if not success:
            print(f"  [{domain}] {view_name}: {error_reason}")

# COMMAND ----------

# Verify deployed views
print("\n" + "=" * 60)
print("Deployed Metric Views in Catalog")
print("=" * 60)

try:
    # Set catalog context first to avoid schema resolution errors
    spark.sql(f"USE CATALOG {catalog}")
    views_df = spark.sql(f"SHOW VIEWS IN {METRIC_VIEW_SCHEMA}")
    display(views_df)
except Exception as e:
    # Fallback: Query information_schema for views
    print(f"Note: SHOW VIEWS failed ({str(e)[:50]}...), querying information_schema instead:")
    try:
        views_df = spark.sql(f"""
            SELECT table_name as view_name, table_type 
            FROM {catalog}.information_schema.tables 
            WHERE table_schema = '{METRIC_VIEW_SCHEMA}' 
            AND table_type = 'VIEW'
            ORDER BY table_name
        """)
        display(views_df)
    except Exception as e2:
        print(f"Could not list views: {e2}")

# COMMAND ----------

# Query to verify metric view functionality
print("\n" + "=" * 60)
print("Metric View Verification Queries")
print("=" * 60)

# Ensure catalog context is set
try:
    spark.sql(f"USE CATALOG {catalog}")
except Exception:
    pass

# Verify a sample of deployed views
verification_queries = [
    ("cost_analytics", f"SELECT COUNT(*) as total FROM {catalog}.{METRIC_VIEW_SCHEMA}.cost_analytics LIMIT 1"),
    ("job_performance", f"SELECT COUNT(*) as total FROM {catalog}.{METRIC_VIEW_SCHEMA}.job_performance LIMIT 1"),
]

for view_name, query in verification_queries:
    try:
        result = spark.sql(query).first()
        count = result[0] if result else 0
        print(f"  ✓ {view_name}: Query successful (records: {count})")
    except Exception as e:
        print(f"  ✗ {view_name}: {str(e)[:80]}...")

# COMMAND ----------

# Exit with appropriate status
# FAIL if ANY metric view fails to deploy - no optional views
if failed > 0:
    failed_details = [(view_name, error_reason) for view_name, _, success, error_reason in results if not success]
    failed_names = [name for name, _ in failed_details]
    error_lines = [f"\n  - {name}: {reason}" for name, reason in failed_details]
    error_msg = f"FAILED: {failed} metric views failed to deploy: {', '.join(failed_names)}{''.join(error_lines)}"
    print(f"\n❌ {error_msg}")
    raise RuntimeError(error_msg)
else:
    success_msg = f"SUCCESS: All {successful} metric views deployed to {catalog}.{METRIC_VIEW_SCHEMA}"
    print(f"\n✅ {success_msg}")
    dbutils.notebook.exit(success_msg)
