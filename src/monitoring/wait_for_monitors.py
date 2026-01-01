# Databricks notebook source
"""
Wait for Lakehouse Monitor Tables

This utility notebook waits for Lakehouse Monitor output tables to be created.
Monitors create their output tables asynchronously, so we need to wait before
adding documentation/descriptions to them.

Conservative delay: 20 minutes (monitors typically ready in 10-15 min)
"""

import time

# COMMAND ----------

# Get parameters
wait_minutes = int(dbutils.widgets.get("wait_minutes") if dbutils.widgets.get("wait_minutes") else "20")

print(f"=" * 60)
print(f"⏳ Waiting {wait_minutes} minutes for Lakehouse Monitor tables to initialize...")
print(f"=" * 60)
print(f"")
print(f"Why we wait:")
print(f"  - Lakehouse Monitors create output tables asynchronously")
print(f"  - _profile_metrics and _drift_metrics tables need time to be created")
print(f"  - Documentation job needs these tables to exist before adding descriptions")
print(f"")

# COMMAND ----------

# Wait with progress updates
total_seconds = wait_minutes * 60
update_interval = 60  # Update every minute

for elapsed in range(0, total_seconds, update_interval):
    remaining = (total_seconds - elapsed) // 60
    print(f"⏳ {remaining} minutes remaining...")
    time.sleep(min(update_interval, total_seconds - elapsed))

print(f"")
print(f"✓ Wait complete! Monitor tables should now be ready.")
print(f"=" * 60)

# COMMAND ----------

# Signal success
dbutils.notebook.exit("SUCCESS")

