"""
TRAINING MATERIAL: Table-Valued Functions for Genie Spaces
==========================================================

This module contains parameterized SQL functions that provide
pre-defined query patterns for Genie natural language access.

TVF vs METRIC VIEW COMPARISON:
------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  METRIC VIEW                      │  TVF (Table-Valued Function)        │
├───────────────────────────────────┼─────────────────────────────────────┤
│  Aggregation patterns             │  Parameterized queries              │
│  GROUP BY dimensions              │  Custom filtering logic             │
│  SUM/AVG/COUNT measures           │  Complex multi-table joins          │
│  "Total cost by workspace"        │  "Top N expensive jobs"             │
│  No parameters                    │  Input parameters (dates, limits)   │
└───────────────────────────────────┴─────────────────────────────────────┘

USE METRIC VIEW WHEN:
- Simple aggregations (SUM, COUNT, AVG)
- User wants to slice/dice by dimensions
- Standard BI dashboard patterns

USE TVF WHEN:
- Need parameters (date range, limit, threshold)
- Complex logic (ranking, filtering, conditional)
- Pre-defined "canned" reports

TVF EXAMPLE:
------------

    CREATE FUNCTION get_expensive_jobs(
        lookback_days INT DEFAULT 30,
        min_cost DOUBLE DEFAULT 100.0,
        top_n INT DEFAULT 10
    )
    RETURNS TABLE (
        job_name STRING,
        total_cost DOUBLE,
        run_count INT,
        avg_duration_minutes DOUBLE
    )
    RETURN
        SELECT job_name, SUM(cost) as total_cost, COUNT(*) as run_count, ...
        FROM gold.fact_job_run_timeline
        WHERE run_date >= current_date() - INTERVAL lookback_days DAY
          AND cost >= min_cost
        GROUP BY job_name
        ORDER BY total_cost DESC
        LIMIT top_n;

GENIE SPACE INTEGRATION:
------------------------

Genie can call TVFs when user asks:
- "Show me the 5 most expensive jobs this week"
- "What jobs failed yesterday?"
- "Which warehouses have worst cache hit rate?"

TVFs query the Gold layer tables (not system tables directly).
"""
