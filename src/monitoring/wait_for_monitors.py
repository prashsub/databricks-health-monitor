# Databricks notebook source
"""
TRAINING MATERIAL: Async Monitor Table Creation Pattern
=======================================================

This utility demonstrates handling Lakehouse Monitor's asynchronous
table creation in Databricks workflows.

THE ASYNC PROBLEM:
------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW TASK SEQUENCE                                                  │
│                                                                         │
│  [Create Monitors] ─────► [Document Monitors] ─────► [Validate]         │
│        │                        │                                       │
│        ▼                        ▼                                       │
│  API returns immediately   Tries to ALTER TABLE                         │
│  Tables created async       ❌ TABLE NOT FOUND!                         │
│  (10-15 min later)                                                      │
│                                                                         │
│  SOLUTION: Wait task between create and document                        │
│                                                                         │
│  [Create Monitors] → [WAIT 20min] → [Document Monitors] → [Validate]   │
│                           │                                             │
│                           ▼                                             │
│                   Tables now exist                                      │
│                   ✅ ALTER TABLE works                                  │
└─────────────────────────────────────────────────────────────────────────┘

WHY 20 MINUTES:
---------------

- Monitor metrics computation: 5-10 minutes
- Table materialization: 2-5 minutes
- Safety buffer: 5 minutes
- Total conservative estimate: 20 minutes

In production, consider polling for table existence instead of fixed wait.

ALTERNATIVE: Polling Pattern
----------------------------

    while not table_exists(output_table):
        time.sleep(60)
        if elapsed > max_wait:
            raise TimeoutError("Monitor tables not created")

The polling approach is more efficient but requires more complex code.
For simplicity, this implementation uses a fixed wait.

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

