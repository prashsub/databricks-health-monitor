#!/usr/bin/env python3
"""
Delete Lakeview monitoring dashboards from Databricks workspace.

Usage:
    python scripts/delete_dashboards.py
    
Requires:
    - Databricks CLI authenticated (databricks auth login)
    - DATABRICKS_HOST environment variable or ~/.databrickscfg
"""

from databricks.sdk import WorkspaceClient

# Dashboard names to delete (all variations)
DASHBOARDS_TO_DELETE = [
    # Original versions
    "fact_table_lineage Monitoring",
    "fact_audit_logs Monitoring",
    "fact_node_timeline Monitoring",
    "fact_query_history Monitoring",
    "fact_job_run_timeline Monitoring",
    "fact_usage Monitoring",
    # Version (1)
    "fact_table_lineage Monitoring (1)",
    "fact_audit_logs Monitoring (1)",
    "fact_node_timeline Monitoring (1)",
    "fact_query_history Monitoring (1)",
    "fact_job_run_timeline Monitoring (1)",
    "fact_usage Monitoring (1)",
    # Version (2)
    "fact_table_lineage Monitoring (2)",
    "fact_audit_logs Monitoring (2)",
    "fact_node_timeline Monitoring (2)",
    "fact_query_history Monitoring (2)",
    "fact_job_run_timeline Monitoring (2)",
    "fact_usage Monitoring (2)",
    # Version (3)
    "fact_table_lineage Monitoring (3)",
    "fact_audit_logs Monitoring (3)",
    "fact_node_timeline Monitoring (3)",
    "fact_query_history Monitoring (3)",
    "fact_job_run_timeline Monitoring (3)",
    "fact_usage Monitoring (3)",
    # Version (4)
    "fact_table_lineage Monitoring (4)",
    "fact_audit_logs Monitoring (4)",
    "fact_node_timeline Monitoring (4)",
    "fact_query_history Monitoring (4)",
    "fact_job_run_timeline Monitoring (4)",
    "fact_usage Monitoring (4)",
    # Version (5)
    "fact_table_lineage Monitoring (5)",
    "fact_audit_logs Monitoring (5)",
    "fact_node_timeline Monitoring (5)",
    "fact_query_history Monitoring (5)",
    "fact_job_run_timeline Monitoring (5)",
    "fact_usage Monitoring (5)",
    # Version (6)
    "fact_table_lineage Monitoring (6)",
    "fact_audit_logs Monitoring (6)",
    "fact_node_timeline Monitoring (6)",
    "fact_query_history Monitoring (6)",
    "fact_job_run_timeline Monitoring (6)",
    "fact_usage Monitoring (6)",
    # Version (7)
    "fact_table_lineage Monitoring (7)",
    "fact_audit_logs Monitoring (7)",
    "fact_node_timeline Monitoring (7)",
    "fact_query_history Monitoring (7)",
    "fact_job_run_timeline Monitoring (7)",
    "fact_usage Monitoring (7)",
]


def main():
    """Main entry point."""
    print("=" * 70)
    print("Databricks Lakeview Dashboard Deletion Script")
    print("=" * 70)
    
    # Initialize client
    try:
        w = WorkspaceClient()
        print(f"✓ Connected to workspace: {w.config.host}")
    except Exception as e:
        print(f"❌ Failed to connect to workspace: {e}")
        print("\nMake sure you're authenticated:")
        print("  databricks auth login --host <workspace-url>")
        return 1
    
    # List all dashboards
    print("\n📋 Listing Lakeview dashboards...")
    try:
        dashboards = list(w.lakeview.list())
        print(f"   Found {len(dashboards)} total dashboards")
    except Exception as e:
        print(f"❌ Failed to list dashboards: {e}")
        return 1
    
    # Filter dashboards to delete
    dashboards_to_delete = []
    target_names_set = set(DASHBOARDS_TO_DELETE)
    
    for dashboard in dashboards:
        if dashboard.display_name in target_names_set:
            dashboards_to_delete.append(dashboard)
    
    print(f"   Found {len(dashboards_to_delete)} dashboards matching deletion criteria")
    
    if not dashboards_to_delete:
        print("\n✅ No matching dashboards found. Nothing to delete.")
        return 0
    
    # Display dashboards to be deleted
    print("\n📋 Dashboards to be deleted:")
    print("-" * 70)
    for d in dashboards_to_delete:
        print(f"   - {d.display_name} (ID: {d.dashboard_id})")
    print("-" * 70)
    
    # Confirm deletion
    print(f"\n⚠️  About to delete {len(dashboards_to_delete)} dashboards.")
    confirm = input("Type 'yes' to confirm deletion: ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Deletion cancelled.")
        return 0
    
    # Delete dashboards
    print("\n🗑️  Deleting dashboards...")
    deleted_count = 0
    failed_count = 0
    
    for dashboard in dashboards_to_delete:
        try:
            w.lakeview.trash(dashboard.dashboard_id)
            print(f"   ✓ Deleted: {dashboard.display_name}")
            deleted_count += 1
        except Exception as e:
            print(f"   ❌ Failed to delete {dashboard.display_name}: {e}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"   ✓ Deleted: {deleted_count}")
    print(f"   ❌ Failed: {failed_count}")
    print("=" * 70)
    
    if failed_count > 0:
        return 1
    
    print("\n✅ All dashboards deleted successfully!")
    return 0


if __name__ == "__main__":
    exit(main())

