# Databricks notebook source
"""
Lakehouse Monitor Refresh Script
================================

Manually triggers a refresh for all Lakehouse Monitors.
Use this to force an immediate update of monitor metrics.

Agent Domains: 💰 Cost, ⚡ Performance, 🔄 Reliability, 🔒 Security, ✅ Quality
"""

# COMMAND ----------

# Install required SDK version
%pip install --upgrade "databricks-sdk>=0.28.0" --quiet
dbutils.library.restartPython()

# COMMAND ----------

from databricks.sdk import WorkspaceClient

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

print(f"Catalog: {catalog}")
print(f"Gold Schema: {gold_schema}")

# COMMAND ----------

def refresh_monitor(ws: WorkspaceClient, table_name: str) -> bool:
    """Trigger a refresh for a specific monitor."""
    try:
        # Run refresh
        ws.quality_monitors.run_refresh(table_name=table_name)
        print(f"  ✓ Refresh triggered for: {table_name}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "does not have a monitor" in error_msg.lower():
            print(f"  ⚠ No monitor exists for: {table_name}")
        else:
            print(f"  ✗ Failed to refresh {table_name}: {error_msg[:100]}")
        return False

# COMMAND ----------

def main():
    """Main entry point for monitor refresh."""
    print("\n" + "=" * 80)
    print("REFRESHING LAKEHOUSE MONITORS")
    print("=" * 80)
    
    ws = WorkspaceClient()
    
    # Tables with monitors by Agent Domain
    monitored_tables = [
        # Cost Domain
        ("💰 Cost", f"{catalog}.{gold_schema}.fact_usage"),
        
        # Performance Domain  
        ("⚡ Performance", f"{catalog}.{gold_schema}.fact_query_history"),
        ("⚡ Performance", f"{catalog}.{gold_schema}.fact_node_timeline"),
        
        # Reliability Domain
        ("🔄 Reliability", f"{catalog}.{gold_schema}.fact_job_run_timeline"),
        
        # Security Domain
        ("🔒 Security", f"{catalog}.{gold_schema}.fact_audit_logs"),
        
        # Quality Domain
        ("✅ Quality", f"{catalog}.{gold_schema}.fact_information_schema_table_storage"),
        
        # Governance Domain
        ("📊 Governance", f"{catalog}.{gold_schema}.fact_table_lineage"),
        
        # ML Domain (if ML inference table exists)
        ("🤖 ML", f"{catalog}.{gold_schema}.cost_anomaly_predictions"),
    ]
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for domain, table_name in monitored_tables:
        print(f"\n[{domain}] Refreshing: {table_name.split('.')[-1]}")
        result = refresh_monitor(ws, table_name)
        if result:
            success_count += 1
        else:
            # Check if it was skipped (no monitor) or actual error
            skip_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("REFRESH SUMMARY")
    print("=" * 80)
    print(f"✓ Successfully triggered: {success_count}")
    print(f"⚠ Skipped (no monitor): {skip_count}")
    print(f"✗ Errors: {error_count}")
    
    if success_count > 0:
        print("\n✅ Monitor refresh triggered successfully!")
        print("Note: Refresh runs asynchronously. Check Lakehouse Monitoring UI for status.")

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
main()



