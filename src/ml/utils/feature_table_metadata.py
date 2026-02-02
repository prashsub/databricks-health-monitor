"""
TRAINING MATERIAL: Feature Table Metadata for Genie/LLM Integration
====================================================================

This module provides centralized metadata definitions for ML feature tables,
enabling natural language queries via Genie Spaces and AI/BI dashboards.

WHY FEATURE TABLE METADATA:
---------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  WITHOUT METADATA                      │  WITH METADATA                  │
├────────────────────────────────────────┼─────────────────────────────────┤
│  User: "What affects cost predictions?"│  User: "What affects cost?"      │
│  Genie: ❌ "I see columns like         │  Genie: ✅ "Cost predictions     │
│         daily_dbu, serverless_cost..." │         are affected by:         │
│                                        │         - daily_dbu (DBU usage)  │
│                                        │         - serverless_cost        │
│                                        │         - jobs_on_all_purpose"   │
└────────────────────────────────────────┴─────────────────────────────────┘

FEATURE TABLE DESIGN PRINCIPLES:
--------------------------------

1. PRIMARY KEYS FOR FEATURE STORE
   - Every feature table needs explicit primary keys
   - Unity Catalog Feature Engineering requires them
   - Example: (workspace_id, usage_date) for cost_features

2. CONSISTENT DATA TYPES FOR ML
   - All numeric columns must be DOUBLE (not INT/BIGINT)
   - sklearn/xgboost require consistent float types
   - Prevents "float32/float64 mismatch" errors

3. NO NULL VALUES IN FEATURES
   - ML models can't handle NaN/NULL
   - Use COALESCE(col, 0) or fillna() during creation
   - Feature table creation handles this automatically

4. COMPREHENSIVE COLUMN METADATA
   Each column has:
   - business_description: What it means to analysts
   - technical_description: How it's calculated
   - data_type: Expected type (always DOUBLE for numerics)
   - unit: USD, DBU, seconds, count, etc.
   - valid_range: Expected value range

METADATA STRUCTURE:
-------------------

    FEATURE_TABLE_METADATA = {
        "cost_features": {
            "table_comment": "Purpose, domain, PKs, source, refresh...",
            "columns": {
                "daily_cost": {
                    "business_description": "Total cost in USD...",
                    "technical_description": "SUM(list_cost) from...",
                    "data_type": "DOUBLE",
                    "unit": "USD",
                    "valid_range": ">= 0"
                },
                ...
            }
        }
    }

Design Principles:
- Each column has: business_description, technical_description, data_type, unit, valid_range
- Table comments include: purpose, domain, primary_keys, source_tables, refresh_frequency
- All descriptions are Genie/LLM optimized for natural language queries
"""

from typing import Dict, Any, List

# ==============================================================================
# FEATURE TABLE METADATA REGISTRY
# ==============================================================================

FEATURE_TABLE_METADATA: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # COST FEATURES
    # =========================================================================
    "cost_features": {
        "table_comment": """Aggregated cost and usage features for ML models in the Cost domain.
Contains daily workspace-level metrics for DBU consumption, cost analysis, and optimization opportunities.
Used by: cost_anomaly_detector, budget_forecaster, job_cost_optimizer, chargeback_attribution, commitment_recommender.
Primary Keys: workspace_id, usage_date | Source: fact_usage | Domain: Cost | Refresh: Daily""",
        "columns": {
            # Primary Keys
            "workspace_id": {
                "business_description": "Unique identifier for the Databricks workspace. Use to join with dim_workspace for workspace name and region.",
                "technical_description": "String identifier from system.billing.usage. Primary key component.",
                "data_type": "STRING",
                "unit": "N/A",
                "valid_range": "Non-null workspace identifier"
            },
            "usage_date": {
                "business_description": "Date of the cost and usage observation. Use for time-series analysis and trend detection.",
                "technical_description": "Date derived from usage_date in fact_usage. Primary key component for daily granularity.",
                "data_type": "DATE",
                "unit": "Calendar date",
                "valid_range": "Past dates up to yesterday"
            },
            # Core Cost Metrics
            "daily_dbu": {
                "business_description": "Total Databricks Units (DBU) consumed by the workspace on this date. Core metric for capacity planning and cost allocation.",
                "technical_description": "SUM(usage_quantity) from fact_usage grouped by workspace and date. Cast to DOUBLE for ML compatibility.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0"
            },
            "daily_cost": {
                "business_description": "Total cost in USD for the workspace on this date. Primary target for budget forecasting models.",
                "technical_description": "SUM(list_cost) from fact_usage. Uses list price before discounts.",
                "data_type": "DOUBLE",
                "unit": "USD",
                "valid_range": ">= 0"
            },
            "jobs_on_all_purpose_cost": {
                "business_description": "Cost of running jobs on ALL_PURPOSE clusters instead of dedicated job clusters. High values indicate optimization opportunities.",
                "technical_description": "Cost filtered by sku_name='JOBS_COMPUTE' on ALL_PURPOSE clusters. Per Workflow Advisor Blog, this represents 40% potential savings.",
                "data_type": "DOUBLE",
                "unit": "USD",
                "valid_range": ">= 0"
            },
            "jobs_on_all_purpose_count": {
                "business_description": "Number of jobs running on ALL_PURPOSE clusters. Count of optimization candidates.",
                "technical_description": "COUNT of usage records with sku_name='JOBS_COMPUTE' on ALL_PURPOSE clusters.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0, Integer values"
            },
            "serverless_cost": {
                "business_description": "Total cost of serverless compute (SQL warehouses, notebooks). Indicates serverless adoption level.",
                "technical_description": "Cost filtered by sku_name containing 'SERVERLESS'.",
                "data_type": "DOUBLE",
                "unit": "USD",
                "valid_range": ">= 0"
            },
            "dlt_cost": {
                "business_description": "Cost of Delta Live Tables pipelines. Indicates DLT adoption and batch processing spend.",
                "technical_description": "Cost filtered by sku_name containing 'DLT' or 'DELTA_LIVE_TABLES'.",
                "data_type": "DOUBLE",
                "unit": "USD",
                "valid_range": ">= 0"
            },
            "model_serving_cost": {
                "business_description": "Cost of Model Serving endpoints. Indicates ML deployment activity.",
                "technical_description": "Cost filtered by sku_name containing 'MODEL_SERVING' or 'INFERENCE'.",
                "data_type": "DOUBLE",
                "unit": "USD",
                "valid_range": ">= 0"
            },
            # Rolling Window Features
            "avg_dbu_7d": {
                "business_description": "7-day rolling average of daily DBU consumption. Smoothed trend for short-term forecasting.",
                "technical_description": "AVG(daily_dbu) over sliding window of -6 to 0 days, partitioned by workspace_id.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0"
            },
            "std_dbu_7d": {
                "business_description": "7-day rolling standard deviation of DBU. High values indicate usage volatility.",
                "technical_description": "STDDEV(daily_dbu) over sliding window of -6 to 0 days.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0"
            },
            "avg_dbu_30d": {
                "business_description": "30-day rolling average of daily DBU consumption. Baseline for medium-term trends.",
                "technical_description": "AVG(daily_dbu) over sliding window of -29 to 0 days.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0"
            },
            "std_dbu_30d": {
                "business_description": "30-day rolling standard deviation of DBU. Used for anomaly detection thresholds.",
                "technical_description": "STDDEV(daily_dbu) over sliding window of -29 to 0 days.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0"
            },
            # Anomaly Detection Features
            "z_score_7d": {
                "business_description": "Z-score of daily DBU vs 7-day average. Values > 2 or < -2 indicate anomalies.",
                "technical_description": "(daily_dbu - avg_dbu_7d) / std_dbu_7d. NaN when std=0.",
                "data_type": "DOUBLE",
                "unit": "Standard deviations",
                "valid_range": "Typically -4 to +4"
            },
            "z_score_30d": {
                "business_description": "Z-score of daily DBU vs 30-day average. More stable baseline for anomaly detection.",
                "technical_description": "(daily_dbu - avg_dbu_30d) / std_dbu_30d. NaN when std=0.",
                "data_type": "DOUBLE",
                "unit": "Standard deviations",
                "valid_range": "Typically -4 to +4"
            },
            # Temporal Features
            "day_of_week": {
                "business_description": "Day of the week (1=Sunday, 7=Saturday). Use for weekly seasonality patterns.",
                "technical_description": "DAYOFWEEK(usage_date). Integer 1-7.",
                "data_type": "DOUBLE",
                "unit": "Day number",
                "valid_range": "1-7"
            },
            "is_weekend": {
                "business_description": "Boolean indicating weekend (Saturday/Sunday). Weekend usage patterns differ significantly.",
                "technical_description": "1 if day_of_week IN (1, 7), else 0.",
                "data_type": "DOUBLE",
                "unit": "Boolean (0/1)",
                "valid_range": "0 or 1"
            },
            "day_of_month": {
                "business_description": "Day of the month (1-31). Use for monthly seasonality and month-end spikes.",
                "technical_description": "DAYOFMONTH(usage_date).",
                "data_type": "DOUBLE",
                "unit": "Day number",
                "valid_range": "1-31"
            },
            "is_month_end": {
                "business_description": "Boolean indicating last 3 days of month. Month-end often has increased batch processing.",
                "technical_description": "1 if day_of_month >= 28, else 0.",
                "data_type": "DOUBLE",
                "unit": "Boolean (0/1)",
                "valid_range": "0 or 1"
            },
            "dow_sin": {
                "business_description": "Sine encoding of day of week. Enables cyclical pattern learning in ML models.",
                "technical_description": "SIN(2 * PI * day_of_week / 7). Continuous encoding for neural networks.",
                "data_type": "DOUBLE",
                "unit": "Sine value",
                "valid_range": "-1 to 1"
            },
            "dow_cos": {
                "business_description": "Cosine encoding of day of week. Paired with dow_sin for complete cyclical representation.",
                "technical_description": "COS(2 * PI * day_of_week / 7). Continuous encoding for neural networks.",
                "data_type": "DOUBLE",
                "unit": "Cosine value",
                "valid_range": "-1 to 1"
            },
            # Lag Features
            "daily_dbu_lag1": {
                "business_description": "DBU consumption from previous day. Use for day-over-day comparisons.",
                "technical_description": "LAG(daily_dbu, 1) over window partitioned by workspace_id ordered by usage_date.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0, NULL for first day"
            },
            "daily_dbu_lag7": {
                "business_description": "DBU consumption from same day last week. Use for week-over-week comparisons.",
                "technical_description": "LAG(daily_dbu, 7) over window partitioned by workspace_id ordered by usage_date.",
                "data_type": "DOUBLE",
                "unit": "DBU",
                "valid_range": ">= 0, NULL for first 7 days"
            },
            # Change Detection Features
            "dbu_change_pct_1d": {
                "business_description": "Percent change in DBU from previous day. Large changes may indicate anomalies.",
                "technical_description": "(daily_dbu - daily_dbu_lag1) / daily_dbu_lag1 * 100. NULL when lag is 0.",
                "data_type": "DOUBLE",
                "unit": "Percentage",
                "valid_range": "-100% to unbounded positive"
            },
            "dbu_change_pct_7d": {
                "business_description": "Percent change in DBU from same day last week. Week-over-week growth indicator.",
                "technical_description": "(daily_dbu - daily_dbu_lag7) / daily_dbu_lag7 * 100. NULL when lag is 0.",
                "data_type": "DOUBLE",
                "unit": "Percentage",
                "valid_range": "-100% to unbounded positive"
            },
            # Optimization Metrics
            "potential_job_cluster_savings": {
                "business_description": "Estimated USD savings from migrating ALL_PURPOSE jobs to job clusters. Per Workflow Advisor: 40% savings typical.",
                "technical_description": "jobs_on_all_purpose_cost * 0.4. Conservative estimate of savings.",
                "data_type": "DOUBLE",
                "unit": "USD",
                "valid_range": ">= 0"
            },
            "all_purpose_inefficiency_ratio": {
                "business_description": "Ratio of jobs-on-ALL_PURPOSE cost to total cost. High ratio = optimization opportunity.",
                "technical_description": "jobs_on_all_purpose_cost / daily_cost. NULL when daily_cost = 0.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            "serverless_adoption_ratio": {
                "business_description": "Ratio of serverless cost to total cost. Higher = more serverless adoption.",
                "technical_description": "serverless_cost / daily_cost. NULL when daily_cost = 0.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            }
        }
    },

    # =========================================================================
    # SECURITY FEATURES
    # =========================================================================
    "security_features": {
        "table_comment": """Aggregated security and audit features for ML models in the Security domain.
Contains daily user-level metrics for activity patterns, authentication events, and threat indicators.
Used by: security_threat_detector, exfiltration_detector, privilege_escalation_detector, user_behavior_baseline.
Primary Keys: user_id, event_date | Source: fact_audit_logs | Domain: Security | Refresh: Daily""",
        "columns": {
            # Primary Keys
            "user_id": {
                "business_description": "Unique identifier for the user. Use to join with dim_user for user details and type.",
                "technical_description": "User email or service principal ID from audit logs. Primary key component.",
                "data_type": "STRING",
                "unit": "N/A",
                "valid_range": "Non-null user identifier"
            },
            "event_date": {
                "business_description": "Date of the security activity observation. Use for temporal analysis of user behavior.",
                "technical_description": "Date derived from event_time in fact_audit_logs. Primary key component.",
                "data_type": "DATE",
                "unit": "Calendar date",
                "valid_range": "Past dates up to yesterday"
            },
            # Activity Volume Metrics
            "event_count": {
                "business_description": "Total number of audit events for this user on this date. Baseline for activity level.",
                "technical_description": "COUNT(*) from fact_audit_logs grouped by user and date.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 1"
            },
            "distinct_action_types": {
                "business_description": "Number of different action types performed. High diversity may indicate exploration or compromise.",
                "technical_description": "COUNT(DISTINCT action_name) from fact_audit_logs.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 1"
            },
            "distinct_workspaces": {
                "business_description": "Number of different workspaces accessed. Multi-workspace access requires monitoring.",
                "technical_description": "COUNT(DISTINCT workspace_id) from fact_audit_logs.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 1"
            },
            # Authentication Events
            "failed_auth_count": {
                "business_description": "Number of failed authentication attempts. Spike may indicate brute-force attack.",
                "technical_description": "COUNT where action_name contains 'login' AND response_status_code != 200.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "successful_auth_count": {
                "business_description": "Number of successful authentications. Unusual patterns may indicate credential sharing.",
                "technical_description": "COUNT where action_name contains 'login' AND response_status_code = 200.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "auth_failure_rate": {
                "business_description": "Rate of authentication failures. High rate (> 0.3) warrants investigation.",
                "technical_description": "failed_auth_count / (failed_auth_count + successful_auth_count). NULL if no auth events.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Privilege Events
            "permission_changes": {
                "business_description": "Number of permission modification events. High count may indicate privilege escalation.",
                "technical_description": "COUNT where action_name contains 'permission', 'grant', 'revoke', or 'acl'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "admin_actions": {
                "business_description": "Number of administrative actions performed. Admin activity by non-admins is suspicious.",
                "technical_description": "COUNT where action_name contains 'admin', 'create', 'delete', or 'update' on system objects.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Data Access Events
            "data_exports": {
                "business_description": "Number of data export events. High volume may indicate data exfiltration.",
                "technical_description": "COUNT where action_name contains 'export', 'download', or 'dbfs/get'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "secrets_accessed": {
                "business_description": "Number of secret access events. Unusual secret access patterns need investigation.",
                "technical_description": "COUNT where action_name contains 'secrets' or 'getSecret'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Temporal Features
            "off_hours_events": {
                "business_description": "Events outside business hours (6 PM - 6 AM). After-hours activity may be suspicious.",
                "technical_description": "COUNT where HOUR(event_time) < 6 OR HOUR(event_time) >= 18.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "weekend_events": {
                "business_description": "Events on weekends. Weekend activity by business users may need review.",
                "technical_description": "COUNT where DAYOFWEEK(event_date) IN (1, 7).",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Rolling Averages
            "avg_events_7d": {
                "business_description": "7-day rolling average of event count. Baseline for detecting activity anomalies.",
                "technical_description": "AVG(event_count) over sliding window of -6 to 0 days.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "event_z_score_7d": {
                "business_description": "Z-score of event count vs 7-day average. Values > 2 may indicate unusual activity.",
                "technical_description": "(event_count - avg_events_7d) / stddev_events_7d.",
                "data_type": "DOUBLE",
                "unit": "Standard deviations",
                "valid_range": "Typically -4 to +4"
            }
        }
    },

    # =========================================================================
    # PERFORMANCE FEATURES
    # =========================================================================
    "performance_features": {
        "table_comment": """Aggregated query and warehouse performance features for ML models in the Performance domain.
Contains daily warehouse-level metrics for query latency, resource utilization, and optimization opportunities.
Used by: query_performance_forecaster, warehouse_optimizer, cluster_capacity_planner, performance_regression_detector, cache_hit_predictor, query_optimization_recommender.
Primary Keys: warehouse_id, query_date | Source: fact_query_history | Domain: Performance | Refresh: Daily""",
        "columns": {
            # Primary Keys
            "warehouse_id": {
                "business_description": "Unique identifier for the SQL Warehouse. Use to join with dim_warehouse for warehouse configuration.",
                "technical_description": "Warehouse ID from system.compute.warehouse_events. Primary key component.",
                "data_type": "STRING",
                "unit": "N/A",
                "valid_range": "Non-null warehouse identifier"
            },
            "query_date": {
                "business_description": "Date of the query performance observation. Use for daily trends and seasonality analysis.",
                "technical_description": "Date derived from start_time in fact_query_history. Primary key component.",
                "data_type": "DATE",
                "unit": "Calendar date",
                "valid_range": "Past dates up to yesterday"
            },
            # Query Volume Metrics
            "query_count": {
                "business_description": "Total number of queries executed on this warehouse this date. Workload volume indicator.",
                "technical_description": "COUNT(*) from fact_query_history grouped by warehouse and date.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "distinct_users": {
                "business_description": "Number of unique users who ran queries. User distribution affects caching efficiency.",
                "technical_description": "COUNT(DISTINCT user_id) from fact_query_history.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Latency Metrics
            "avg_duration_ms": {
                "business_description": "Average query execution time in milliseconds. Primary SLA metric for performance monitoring.",
                "technical_description": "AVG(execution_time_ms) from fact_query_history.",
                "data_type": "DOUBLE",
                "unit": "Milliseconds",
                "valid_range": ">= 0"
            },
            "p50_duration_ms": {
                "business_description": "Median (50th percentile) query duration. More robust than average for typical user experience.",
                "technical_description": "PERCENTILE_APPROX(execution_time_ms, 0.5).",
                "data_type": "DOUBLE",
                "unit": "Milliseconds",
                "valid_range": ">= 0"
            },
            "p95_duration_ms": {
                "business_description": "95th percentile query duration. Identifies slow query tail that impacts user experience.",
                "technical_description": "PERCENTILE_APPROX(execution_time_ms, 0.95).",
                "data_type": "DOUBLE",
                "unit": "Milliseconds",
                "valid_range": ">= 0"
            },
            "p99_duration_ms": {
                "business_description": "99th percentile query duration. Extreme tail latency for SLA monitoring.",
                "technical_description": "PERCENTILE_APPROX(execution_time_ms, 0.99).",
                "data_type": "DOUBLE",
                "unit": "Milliseconds",
                "valid_range": ">= 0"
            },
            # Queue Metrics
            "avg_queue_time_ms": {
                "business_description": "Average time queries spent waiting in queue. High queue time indicates capacity issues.",
                "technical_description": "AVG(queue_time_ms) from fact_query_history.",
                "data_type": "DOUBLE",
                "unit": "Milliseconds",
                "valid_range": ">= 0"
            },
            "max_queue_time_ms": {
                "business_description": "Maximum queue time observed. Worst-case user wait time.",
                "technical_description": "MAX(queue_time_ms) from fact_query_history.",
                "data_type": "DOUBLE",
                "unit": "Milliseconds",
                "valid_range": ">= 0"
            },
            # Cache Efficiency
            "cache_hit_count": {
                "business_description": "Number of queries served from cache. High count indicates good cache utilization.",
                "technical_description": "COUNT where from_results_cache = true.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "cache_hit_rate": {
                "business_description": "Percentage of queries served from cache. Target > 30% for frequently run queries.",
                "technical_description": "cache_hit_count / query_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Resource Utilization
            "total_bytes_scanned": {
                "business_description": "Total bytes scanned by all queries. High values indicate large table scans.",
                "technical_description": "SUM(bytes_scanned) from fact_query_history.",
                "data_type": "DOUBLE",
                "unit": "Bytes",
                "valid_range": ">= 0"
            },
            "avg_bytes_per_query": {
                "business_description": "Average bytes scanned per query. Use for query complexity analysis.",
                "technical_description": "total_bytes_scanned / query_count.",
                "data_type": "DOUBLE",
                "unit": "Bytes",
                "valid_range": ">= 0"
            },
            "spill_to_disk_bytes": {
                "business_description": "Total bytes spilled to disk due to memory pressure. High spill indicates memory constraints.",
                "technical_description": "SUM(spill_to_disk_bytes) from fact_query_history.",
                "data_type": "DOUBLE",
                "unit": "Bytes",
                "valid_range": ">= 0"
            },
            "spill_rate": {
                "business_description": "Ratio of queries with disk spill. High rate (> 0.1) indicates sizing issues.",
                "technical_description": "COUNT(queries with spill) / query_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Error Metrics
            "failed_queries": {
                "business_description": "Number of queries that failed. Track for reliability monitoring.",
                "technical_description": "COUNT where status = 'FAILED'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "error_rate": {
                "business_description": "Rate of query failures. Target < 0.01 (1%) for healthy warehouse.",
                "technical_description": "failed_queries / query_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Temporal Features
            "peak_hour_queries": {
                "business_description": "Queries during peak hours (9 AM - 5 PM). Indicates business hours workload.",
                "technical_description": "COUNT where HOUR(start_time) BETWEEN 9 AND 17.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "peak_hour_ratio": {
                "business_description": "Ratio of peak hour to total queries. High ratio = business-hours focused workload.",
                "technical_description": "peak_hour_queries / query_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            }
        }
    },

    # =========================================================================
    # RELIABILITY FEATURES
    # =========================================================================
    "reliability_features": {
        "table_comment": """Aggregated job reliability and SLA features for ML models in the Reliability domain.
Contains daily job-level metrics for execution success, duration patterns, and failure prediction.
Used by: job_failure_predictor, job_duration_forecaster, sla_breach_predictor, retry_success_predictor, pipeline_health_scorer, dbr_migration_risk_scorer.
Primary Keys: job_id, run_date | Source: fact_job_runs | Domain: Reliability | Refresh: Daily""",
        "columns": {
            # Primary Keys
            "job_id": {
                "business_description": "Unique identifier for the Databricks job. Use to join with dim_job for job configuration.",
                "technical_description": "Job ID from system.lakeflow.jobs. Primary key component.",
                "data_type": "STRING",
                "unit": "N/A",
                "valid_range": "Non-null job identifier"
            },
            "run_date": {
                "business_description": "Date of the job run observation. Use for daily reliability trends.",
                "technical_description": "Date derived from start_time in fact_job_runs. Primary key component.",
                "data_type": "DATE",
                "unit": "Calendar date",
                "valid_range": "Past dates up to yesterday"
            },
            # Run Volume Metrics
            "run_count": {
                "business_description": "Total number of runs for this job on this date. Frequency indicator.",
                "technical_description": "COUNT(*) from fact_job_runs grouped by job and date.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 1"
            },
            "successful_runs": {
                "business_description": "Number of runs that completed successfully. Use for success rate calculation.",
                "technical_description": "COUNT where result_state = 'SUCCESS'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "failed_runs": {
                "business_description": "Number of runs that failed. Track for reliability monitoring.",
                "technical_description": "COUNT where result_state in ('FAILED', 'TIMEDOUT', 'CANCELLED').",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Success/Failure Rates
            "success_rate": {
                "business_description": "Rate of successful runs. Target > 0.95 for critical jobs.",
                "technical_description": "successful_runs / run_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            "failure_rate": {
                "business_description": "Rate of failed runs. > 0.2 indicates job needs investigation. Target for ML prediction.",
                "technical_description": "failed_runs / run_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Duration Metrics
            "avg_duration_seconds": {
                "business_description": "Average job run duration in seconds. Baseline for duration forecasting.",
                "technical_description": "AVG(duration_ms) / 1000 from fact_job_runs.",
                "data_type": "DOUBLE",
                "unit": "Seconds",
                "valid_range": ">= 0"
            },
            "min_duration_seconds": {
                "business_description": "Minimum run duration observed. Best-case execution time.",
                "technical_description": "MIN(duration_ms) / 1000 from fact_job_runs.",
                "data_type": "DOUBLE",
                "unit": "Seconds",
                "valid_range": ">= 0"
            },
            "max_duration_seconds": {
                "business_description": "Maximum run duration observed. Worst-case for SLA planning.",
                "technical_description": "MAX(duration_ms) / 1000 from fact_job_runs.",
                "data_type": "DOUBLE",
                "unit": "Seconds",
                "valid_range": ">= 0"
            },
            "duration_std_seconds": {
                "business_description": "Standard deviation of run duration. High variance indicates unpredictable performance.",
                "technical_description": "STDDEV(duration_ms) / 1000 from fact_job_runs.",
                "data_type": "DOUBLE",
                "unit": "Seconds",
                "valid_range": ">= 0"
            },
            # Retry Metrics
            "retry_count": {
                "business_description": "Number of automatic retries triggered. High retry count indicates flaky job.",
                "technical_description": "SUM(attempt_number - 1) where attempt_number > 1.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "retry_success_rate": {
                "business_description": "Rate of retries that succeeded. Use for intelligent retry policy decisions.",
                "technical_description": "successful retries / total retries.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # SLA Metrics
            "sla_breach_count": {
                "business_description": "Number of runs that exceeded SLA threshold. Use for SLA monitoring.",
                "technical_description": "COUNT where duration_ms > sla_threshold_ms.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "sla_breach_rate": {
                "business_description": "Rate of SLA breaches. > 0.1 indicates SLA needs review. Target for ML prediction.",
                "technical_description": "sla_breach_count / run_count.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Rolling Features
            "avg_failures_7d": {
                "business_description": "7-day rolling average of daily failures. Trend indicator for reliability.",
                "technical_description": "AVG(failed_runs) over sliding window of -6 to 0 days.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "failure_trend": {
                "business_description": "Trend direction of failures: 1=increasing, 0=stable, -1=decreasing.",
                "technical_description": "SIGN(failed_runs - avg_failures_7d).",
                "data_type": "DOUBLE",
                "unit": "Indicator (-1, 0, 1)",
                "valid_range": "-1, 0, or 1"
            }
        }
    },

    # =========================================================================
    # QUALITY FEATURES
    # =========================================================================
    "quality_features": {
        "table_comment": """Aggregated data quality and catalog metadata features for ML models in the Quality domain.
Contains daily catalog-level metrics for schema health, data freshness, and drift indicators.
Used by: data_drift_detector, data_freshness_predictor.
Primary Keys: catalog_name, snapshot_date | Source: system.information_schema | Domain: Quality | Refresh: Daily""",
        "columns": {
            # Primary Keys
            "catalog_name": {
                "business_description": "Unity Catalog name being monitored. Use to filter quality metrics by catalog.",
                "technical_description": "Catalog name from system.information_schema.columns. Primary key component.",
                "data_type": "STRING",
                "unit": "N/A",
                "valid_range": "Non-null catalog name"
            },
            "snapshot_date": {
                "business_description": "Date of the quality metrics snapshot. Use for tracking quality trends over time.",
                "technical_description": "Date when quality features were computed. Primary key component.",
                "data_type": "DATE",
                "unit": "Calendar date",
                "valid_range": "Past dates up to yesterday"
            },
            # Volume Metrics
            "total_tables": {
                "business_description": "Total number of tables in the catalog. Growth indicator for catalog management.",
                "technical_description": "COUNT(DISTINCT table_name) from information_schema.columns.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "total_columns": {
                "business_description": "Total number of columns across all tables. Schema complexity indicator.",
                "technical_description": "COUNT(*) from information_schema.columns.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "total_schemas": {
                "business_description": "Number of schemas in the catalog. Organizational complexity indicator.",
                "technical_description": "COUNT(DISTINCT table_schema) from information_schema.columns.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Documentation Quality
            "documented_columns": {
                "business_description": "Number of columns with comments/descriptions. Documentation coverage indicator.",
                "technical_description": "COUNT where comment IS NOT NULL AND comment != ''.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "documentation_coverage": {
                "business_description": "Percentage of columns with documentation. Target > 80% for governed catalogs.",
                "technical_description": "documented_columns / total_columns.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Data Type Distribution
            "string_columns": {
                "business_description": "Number of STRING type columns. High count may indicate need for type optimization.",
                "technical_description": "COUNT where data_type = 'STRING'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "numeric_columns": {
                "business_description": "Number of numeric type columns (INT, LONG, DOUBLE, DECIMAL).",
                "technical_description": "COUNT where data_type in numeric types.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "timestamp_columns": {
                "business_description": "Number of timestamp/date columns. Indicates temporal data presence.",
                "technical_description": "COUNT where data_type in ('TIMESTAMP', 'DATE').",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            # Nullable Analysis
            "nullable_columns": {
                "business_description": "Number of columns that allow NULL values. Data quality indicator.",
                "technical_description": "COUNT where is_nullable = 'YES'.",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": ">= 0"
            },
            "nullable_ratio": {
                "business_description": "Ratio of nullable to total columns. High ratio may indicate loose schema.",
                "technical_description": "nullable_columns / total_columns.",
                "data_type": "DOUBLE",
                "unit": "Ratio (0-1)",
                "valid_range": "0 to 1"
            },
            # Rolling Features
            "tables_added_7d": {
                "business_description": "Tables added in last 7 days. Growth rate indicator.",
                "technical_description": "total_tables - LAG(total_tables, 7).",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": "Can be negative (tables dropped)"
            },
            "columns_added_7d": {
                "business_description": "Columns added in last 7 days. Schema evolution indicator.",
                "technical_description": "total_columns - LAG(total_columns, 7).",
                "data_type": "DOUBLE",
                "unit": "Count",
                "valid_range": "Can be negative (columns dropped)"
            }
        }
    }
}


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def apply_feature_table_metadata(spark, full_table_name: str) -> bool:
    """
    Apply comprehensive table and column metadata to a feature table.
    
    Args:
        spark: SparkSession
        full_table_name: Fully qualified table name (catalog.schema.table)
        
    Returns:
        True if metadata was applied successfully, False otherwise
    """
    table_name = full_table_name.split('.')[-1]
    
    if table_name not in FEATURE_TABLE_METADATA:
        print(f"    ⚠ No metadata defined for {table_name}")
        return False
    
    metadata = FEATURE_TABLE_METADATA[table_name]
    
    try:
        # Apply table comment
        table_comment = metadata.get("table_comment", "").replace("'", "''")
        spark.sql(f"COMMENT ON TABLE {full_table_name} IS '{table_comment}'")
        print(f"    📝 Table comment added")
        
        # Apply column comments with full business + technical descriptions
        columns = metadata.get("columns", {})
        columns_updated = 0
        
        # Get actual columns from table
        table_columns = [f.name for f in spark.table(full_table_name).schema.fields]
        
        for col_name, col_meta in columns.items():
            if col_name in table_columns:
                # Combine business and technical descriptions
                if isinstance(col_meta, dict):
                    business_desc = col_meta.get("business_description", "")
                    tech_desc = col_meta.get("technical_description", "")
                    unit = col_meta.get("unit", "")
                    valid_range = col_meta.get("valid_range", "")
                    
                    # Format: Business description. Technical: ... | Unit: ... | Range: ...
                    full_comment = business_desc
                    if tech_desc:
                        full_comment += f" Technical: {tech_desc}"
                    if unit and unit != "N/A":
                        full_comment += f" | Unit: {unit}"
                    if valid_range:
                        full_comment += f" | Range: {valid_range}"
                else:
                    full_comment = col_meta
                
                # Truncate if too long and escape quotes
                full_comment = full_comment[:1000].replace("'", "''")
                spark.sql(f"ALTER TABLE {full_table_name} ALTER COLUMN `{col_name}` COMMENT '{full_comment}'")
                columns_updated += 1
        
        print(f"    📝 {columns_updated}/{len(columns)} column comments added")
        return True
        
    except Exception as e:
        print(f"    ⚠ Metadata error: {str(e)[:100]}")
        return False


def get_feature_table_metadata(table_name: str) -> Dict[str, Any]:
    """Get metadata for a specific feature table."""
    return FEATURE_TABLE_METADATA.get(table_name, {})


def get_all_feature_tables() -> List[str]:
    """Get list of all feature table names with metadata defined."""
    return list(FEATURE_TABLE_METADATA.keys())


def get_column_descriptions(table_name: str) -> Dict[str, str]:
    """Get simplified column descriptions (business only) for a feature table."""
    metadata = FEATURE_TABLE_METADATA.get(table_name, {})
    columns = metadata.get("columns", {})
    
    result = {}
    for col_name, col_meta in columns.items():
        if isinstance(col_meta, dict):
            result[col_name] = col_meta.get("business_description", "")
        else:
            result[col_name] = col_meta
    
    return result
