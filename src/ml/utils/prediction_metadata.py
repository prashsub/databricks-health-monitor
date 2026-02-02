"""
TRAINING MATERIAL: ML Prediction Metadata Pattern for Genie/LLM Integration
============================================================================

This module provides centralized metadata definitions for all ML prediction/inference
tables. The metadata is applied to tables after creation to enable natural language
queries via Genie Spaces and AI/BI dashboards.

WHY PREDICTION METADATA MATTERS:
--------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  WITHOUT METADATA                      │  WITH METADATA                  │
├────────────────────────────────────────┼─────────────────────────────────┤
│  User: "Show me security threats"      │  User: "Show me security threats│
│  Genie: ❌ "I don't know what          │  Genie: ✅ "Here are users with │
│         prediction=-1 means"           │         threat predictions..."  │
│                                        │                                 │
│  prediction column has no context      │  prediction column has:         │
│                                        │  - Business description         │
│                                        │  - Interpretation guide         │
│                                        │  - Valid values                 │
│                                        │  - Join table references        │
└────────────────────────────────────────┴─────────────────────────────────┘

METADATA STRUCTURE:
-------------------

Each prediction table has:
1. table_comment: Comprehensive description including:
   - What the model predicts
   - Interpretation guide
   - Business use cases
   - Recommended actions
   - Model type, domain, source, refresh frequency

2. columns: Dictionary of column metadata including:
   - business_description: What the column represents
   - interpretation: How to use/interpret values
   - data_type: Expected type
   - valid_values: Possible values
   - join_table: Related dimension for joins

PREDICTION INTERPRETATION PATTERNS:
-----------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  ANOMALY DETECTION (Isolation Forest):                                   │
│  prediction = -1 → ANOMALY (unusual, investigate)                       │
│  prediction =  1 → NORMAL (expected behavior)                           │
│                                                                         │
│  BINARY CLASSIFICATION (XGBoost/RF):                                    │
│  prediction = 0 → NEGATIVE class (e.g., no risk)                        │
│  prediction = 1 → POSITIVE class (e.g., high risk)                      │
│                                                                         │
│  REGRESSION (Gradient Boosting):                                        │
│  prediction = continuous value (e.g., cost in USD, duration in seconds) │
│                                                                         │
│  SCORING (0-1 scale):                                                   │
│  prediction > 0.7 → HIGH (immediate attention)                          │
│  prediction 0.4-0.7 → MEDIUM (schedule review)                          │
│  prediction < 0.4 → LOW (acceptable)                                    │
└─────────────────────────────────────────────────────────────────────────┘

USAGE PATTERN:
--------------

    from ml.utils.prediction_metadata import (
        apply_table_metadata,
        get_prediction_interpretation
    )
    
    # After batch inference creates tables
    apply_table_metadata(spark, "catalog.schema.cost_anomaly_predictions")
    
    # Get interpretation for UI display
    interp = get_prediction_interpretation("cost_anomaly_predictions")
    # Returns: "-1 = ANOMALY: Cost significantly deviates..."

Design Principles:
- Each table has: purpose, domain, model, source_features, refresh_frequency, usage_guidance
- Each column has: business_description, interpretation_guide, data_type, valid_values
- All descriptions are Genie/LLM optimized for natural language queries
- Prediction interpretation guidance included for actionability
"""

from typing import Dict, Any, List

# ==============================================================================
# PREDICTION TABLE METADATA REGISTRY
# ==============================================================================

PREDICTION_TABLE_METADATA: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # COST DOMAIN PREDICTIONS
    # =========================================================================
    "cost_anomaly_predictions": {
        "table_comment": """ML predictions from cost_anomaly_detector identifying unusual cost patterns.
Uses Isolation Forest anomaly detection on cost_features to detect spending anomalies.
Interpretation: -1 = anomaly (unusual cost), 1 = normal (expected cost pattern).
Business Use: Proactive cost monitoring, alerting on unexpected spend, budget variance analysis.
Action: Investigate records with prediction=-1 for root cause. Join with fact_usage for cost breakdown.
Model: Isolation Forest | Domain: Cost | Source: cost_features | Refresh: Daily batch inference""",
        "columns": {
            "workspace_id": {
                "business_description": "Workspace where cost anomaly was detected. Join with dim_workspace for workspace name and owner.",
                "interpretation": "Filter by workspace_id to focus on specific teams or environments.",
                "data_type": "STRING",
                "join_table": "dim_workspace"
            },
            "usage_date": {
                "business_description": "Date of the cost observation that was evaluated for anomalies.",
                "interpretation": "Use for time-series visualization of anomaly frequency. Cluster anomalies may indicate systemic issues.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Anomaly detection result indicating if the cost pattern is unusual.",
                "interpretation": "-1 = ANOMALY: Cost significantly deviates from historical pattern. Investigate immediately. 1 = NORMAL: Cost within expected range based on historical behavior.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (anomaly) or 1 (normal)"
            },
            "model_name": {
                "business_description": "Name of the ML model that generated this prediction for lineage tracking.",
                "interpretation": "Always 'cost_anomaly_detector'. Use for filtering if multiple models exist.",
                "data_type": "STRING",
                "valid_values": "cost_anomaly_detector"
            },
            "scored_at": {
                "business_description": "Timestamp when batch inference was executed. Use for data freshness verification.",
                "interpretation": "If scored_at is old, predictions may not reflect recent cost changes.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp (within 24 hours for daily refresh)"
            }
        }
    },
    
    "budget_forecast_predictions": {
        "table_comment": """ML predictions from budget_forecaster providing cost forecasts for planning.
Uses Gradient Boosting Regression on cost_features to predict expected daily costs.
Interpretation: Prediction value is forecasted cost in USD for the workspace-date combination.
Business Use: Budget planning, capacity planning, cost trend analysis, variance detection.
Action: Compare prediction vs actual cost in fact_usage. Large variances warrant investigation.
Model: GradientBoostingRegressor | Domain: Cost | Source: cost_features | Refresh: Daily batch inference""",
        "columns": {
            "workspace_id": {
                "business_description": "Workspace for which cost is being forecasted. Join with dim_workspace for context.",
                "interpretation": "Aggregate by workspace_id for departmental budget planning.",
                "data_type": "STRING",
                "join_table": "dim_workspace"
            },
            "usage_date": {
                "business_description": "Date for which the cost forecast applies.",
                "interpretation": "Compare with actual costs on this date for forecast accuracy assessment.",
                "data_type": "DATE",
                "valid_values": "Past dates (historical forecasts)"
            },
            "prediction": {
                "business_description": "Forecasted cost in USD based on historical patterns and temporal features.",
                "interpretation": "Use as expected budget baseline. Variance = (actual - prediction) / prediction. Variance > 20% warrants investigation.",
                "data_type": "DOUBLE",
                "valid_values": ">= 0 (USD amount)"
            },
            "model_name": {
                "business_description": "Name of the ML model for lineage and governance tracking.",
                "interpretation": "Always 'budget_forecaster'. Track model version for reproducibility.",
                "data_type": "STRING",
                "valid_values": "budget_forecaster"
            },
            "scored_at": {
                "business_description": "Timestamp of prediction generation. Indicates forecast freshness.",
                "interpretation": "Recent scored_at means forecast incorporates latest patterns.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "job_cost_optimizer_predictions": {
        "table_comment": """ML predictions from job_cost_optimizer identifying cost optimization opportunities.
Uses Gradient Boosting to score workspaces by optimization potential based on cost patterns.
Interpretation: Higher prediction score indicates greater savings potential from optimization.
Business Use: Prioritize cost optimization efforts, identify inefficient usage patterns.
Action: Focus on workspaces with high scores. Review ALL_PURPOSE cluster usage and serverless migration opportunities.
Model: GradientBoostingRegressor | Domain: Cost | Source: cost_features | Refresh: Daily batch inference""",
        "columns": {
            "workspace_id": {
                "business_description": "Workspace with identified optimization potential. Join with dim_workspace for owner contact.",
                "interpretation": "Prioritize high-score workspaces for FinOps review meetings.",
                "data_type": "STRING",
                "join_table": "dim_workspace"
            },
            "usage_date": {
                "business_description": "Date of cost data used for optimization scoring.",
                "interpretation": "Recent dates provide more actionable recommendations.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Optimization potential score. Higher = more savings opportunity available.",
                "interpretation": "Score 0.7+ = High priority: immediate review needed. Score 0.4-0.7 = Medium: schedule review. Score < 0.4 = Low: already optimized.",
                "data_type": "DOUBLE",
                "valid_values": "0 to 1 (continuous score)"
            },
            "model_name": {
                "business_description": "ML model name for prediction lineage.",
                "interpretation": "Always 'job_cost_optimizer'.",
                "data_type": "STRING",
                "valid_values": "job_cost_optimizer"
            },
            "scored_at": {
                "business_description": "Prediction timestamp for freshness verification.",
                "interpretation": "Use most recent predictions for optimization planning.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "chargeback_predictions": {
        "table_comment": """ML predictions from chargeback_attribution for cost allocation purposes.
Uses Gradient Boosting to predict attributed cost amounts for chargeback/showback reporting.
Interpretation: Prediction is the attributed cost amount in USD for billing purposes.
Business Use: Cost allocation, departmental billing, showback reporting, FinOps governance.
Action: Use predictions for internal billing. Reconcile with actual costs monthly.
Model: GradientBoostingRegressor | Domain: Cost | Source: cost_features | Refresh: Daily batch inference""",
        "columns": {
            "workspace_id": {
                "business_description": "Workspace for cost attribution. Map to cost center via dim_workspace.",
                "interpretation": "Group by workspace_id for departmental cost reports.",
                "data_type": "STRING",
                "join_table": "dim_workspace"
            },
            "usage_date": {
                "business_description": "Date for which cost is being attributed.",
                "interpretation": "Aggregate by month for billing cycles.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Attributed cost amount in USD for chargeback calculation.",
                "interpretation": "Use directly in billing reports. SUM by workspace for monthly chargeback totals.",
                "data_type": "DOUBLE",
                "valid_values": ">= 0 (USD amount)"
            },
            "model_name": {
                "business_description": "ML model for audit trail and governance.",
                "interpretation": "Always 'chargeback_attribution'.",
                "data_type": "STRING",
                "valid_values": "chargeback_attribution"
            },
            "scored_at": {
                "business_description": "Prediction generation timestamp.",
                "interpretation": "Verify predictions are current before billing.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "commitment_recommendations": {
        "table_comment": """ML predictions from commitment_recommender for capacity commitment decisions.
Uses XGBoost Classification to recommend serverless adoption based on usage patterns.
Interpretation: 1 = high serverless adoption recommended, 0 = maintain current compute strategy.
Business Use: Capacity planning, serverless migration decisions, commitment purchasing.
Action: Workspaces with prediction=1 are good serverless migration candidates. Review usage patterns.
Model: XGBClassifier | Domain: Cost | Source: cost_features | Refresh: Daily batch inference""",
        "columns": {
            "workspace_id": {
                "business_description": "Workspace for commitment recommendation. Join with dim_workspace for current configuration.",
                "interpretation": "Filter prediction=1 workspaces for serverless migration planning.",
                "data_type": "STRING",
                "join_table": "dim_workspace"
            },
            "usage_date": {
                "business_description": "Date of usage pattern used for recommendation.",
                "interpretation": "More recent dates provide more relevant recommendations.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Binary recommendation for serverless adoption.",
                "interpretation": "1 = RECOMMEND SERVERLESS: Usage pattern suits serverless. Consider migration. 0 = KEEP CURRENT: Current compute strategy is appropriate.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 or 1"
            },
            "model_name": {
                "business_description": "ML model for governance tracking.",
                "interpretation": "Always 'commitment_recommender'.",
                "data_type": "STRING",
                "valid_values": "commitment_recommender"
            },
            "scored_at": {
                "business_description": "Prediction timestamp.",
                "interpretation": "Use recent predictions for capacity planning decisions.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "tag_recommendations": {
        "table_comment": """ML predictions from tag_recommender for untagged job classification.
Uses Random Forest with TF-IDF text features to recommend tags based on job names and cost patterns.
Interpretation: predicted_tag is the recommended tag value with associated confidence score.
Business Use: Improve cost attribution coverage, governance compliance, automated tagging.
Action: Review high-confidence recommendations (>0.7) for automated tagging. Manual review for lower confidence.
Model: RandomForestClassifier (TF-IDF) | Domain: Cost | Source: cost_features + job_names | Refresh: Daily custom inference""",
        "columns": {
            "job_id": {
                "business_description": "Unique identifier of the untagged job receiving a recommendation.",
                "interpretation": "Use to apply recommended tag via Jobs API or manual update.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "job_name": {
                "business_description": "Name of the job used for TF-IDF text feature extraction.",
                "interpretation": "Job naming patterns drive recommendations. Consistent naming improves accuracy.",
                "data_type": "STRING",
                "valid_values": "Non-null job name"
            },
            "workspace_id": {
                "business_description": "Workspace where the job is defined.",
                "interpretation": "Use for workspace-level tag standardization efforts.",
                "data_type": "STRING",
                "join_table": "dim_workspace"
            },
            "usage_date": {
                "business_description": "Reference date for cost features used in prediction.",
                "interpretation": "Recent dates ensure recommendation uses current cost patterns.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "predicted_tag": {
                "business_description": "Recommended tag value (team name, project, cost center, etc.).",
                "interpretation": "Apply this tag to the job for cost attribution. Verify matches organizational taxonomy.",
                "data_type": "STRING",
                "valid_values": "Tag from training vocabulary"
            },
            "confidence_score": {
                "business_description": "Model confidence in the recommendation (0-1).",
                "interpretation": ">0.8 = High confidence, safe for auto-tagging. 0.5-0.8 = Medium, manual review recommended. <0.5 = Low, likely needs human decision.",
                "data_type": "DOUBLE",
                "valid_values": "0 to 1"
            },
            "total_cost_30d": {
                "business_description": "Total cost for this job over 30 days. Use for prioritization.",
                "interpretation": "Prioritize high-cost jobs for tagging. Higher cost = higher governance impact.",
                "data_type": "DOUBLE",
                "valid_values": ">= 0 (USD amount)"
            },
            "model_name": {
                "business_description": "ML model for lineage tracking.",
                "interpretation": "Always 'tag_recommender'.",
                "data_type": "STRING",
                "valid_values": "tag_recommender"
            },
            "model_version": {
                "business_description": "Model version used for this prediction.",
                "interpretation": "Track for reproducibility and debugging.",
                "data_type": "INTEGER",
                "valid_values": "Positive integer"
            },
            "scored_at": {
                "business_description": "Timestamp of prediction generation.",
                "interpretation": "Use recent predictions for tagging campaigns.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            },
            "scored_date": {
                "business_description": "Date partition for efficient querying.",
                "interpretation": "Filter by scored_date for recent recommendations only.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            }
        }
    },

    # =========================================================================
    # SECURITY DOMAIN PREDICTIONS
    # =========================================================================
    "security_threat_predictions": {
        "table_comment": """ML predictions from security_threat_detector identifying potential security threats.
Uses Isolation Forest anomaly detection on security_features to detect suspicious activity patterns.
Interpretation: -1 = potential threat (unusual activity), 1 = normal (expected behavior).
Business Use: Security monitoring, incident response prioritization, threat detection alerting.
Action: Investigate users with prediction=-1 immediately. Review audit logs for threat indicators.
Model: Isolation Forest | Domain: Security | Source: security_features | Refresh: Daily batch inference""",
        "columns": {
            "user_id": {
                "business_description": "User identifier flagged for potential security threat.",
                "interpretation": "Immediately investigate users with -1 predictions. Join with dim_user for user context.",
                "data_type": "STRING",
                "join_table": "dim_user"
            },
            "event_date": {
                "business_description": "Date of the security activity being analyzed.",
                "interpretation": "Multiple consecutive -1 days indicates persistent threat.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Security threat indicator based on activity pattern analysis.",
                "interpretation": "-1 = THREAT DETECTED: Unusual activity pattern. Escalate to security team. 1 = NORMAL: Activity within expected baseline.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (threat) or 1 (normal)"
            },
            "model_name": {
                "business_description": "ML model for security audit trail.",
                "interpretation": "Always 'security_threat_detector'.",
                "data_type": "STRING",
                "valid_values": "security_threat_detector"
            },
            "scored_at": {
                "business_description": "Prediction timestamp for incident timeline.",
                "interpretation": "Recent scored_at means detection is current. Old predictions may be stale.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "exfiltration_predictions": {
        "table_comment": """ML predictions from exfiltration_detector identifying potential data exfiltration.
Uses Isolation Forest to detect unusual data export and download patterns.
Interpretation: -1 = potential exfiltration risk, 1 = normal data access behavior.
Business Use: Data loss prevention, insider threat detection, compliance monitoring.
Action: Investigate -1 predictions for data export spikes. Review dbfs/get and download actions.
Model: Isolation Forest | Domain: Security | Source: security_features | Refresh: Daily batch inference""",
        "columns": {
            "user_id": {
                "business_description": "User flagged for potential data exfiltration activity.",
                "interpretation": "HIGH PRIORITY: Users with -1 may be exfiltrating data. Review immediately.",
                "data_type": "STRING",
                "join_table": "dim_user"
            },
            "event_date": {
                "business_description": "Date of potential exfiltration activity.",
                "interpretation": "Compare against data export volume in audit logs.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Exfiltration risk indicator.",
                "interpretation": "-1 = EXFILTRATION RISK: Unusual data export pattern. Block access and investigate. 1 = NORMAL: Data access within typical patterns.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (risk) or 1 (normal)"
            },
            "model_name": {
                "business_description": "Model name for security governance.",
                "interpretation": "Always 'exfiltration_detector'.",
                "data_type": "STRING",
                "valid_values": "exfiltration_detector"
            },
            "scored_at": {
                "business_description": "Detection timestamp.",
                "interpretation": "Timely detection is critical for DLP.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "privilege_escalation_predictions": {
        "table_comment": """ML predictions from privilege_escalation_detector identifying abnormal privilege usage.
Uses Isolation Forest to detect unusual permission changes and admin activity.
Interpretation: -1 = potential privilege escalation, 1 = normal privilege usage.
Business Use: Access control monitoring, insider threat detection, compliance auditing.
Action: Review -1 predictions for unauthorized admin actions or permission grants.
Model: Isolation Forest | Domain: Security | Source: security_features | Refresh: Daily batch inference""",
        "columns": {
            "user_id": {
                "business_description": "User with abnormal privilege activity detected.",
                "interpretation": "Check if user should have admin capabilities. Review permission_changes in audit logs.",
                "data_type": "STRING",
                "join_table": "dim_user"
            },
            "event_date": {
                "business_description": "Date of privilege activity being analyzed.",
                "interpretation": "Correlate with organizational changes (new hires, role changes).",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Privilege escalation risk indicator.",
                "interpretation": "-1 = ESCALATION DETECTED: Abnormal admin/permission activity. Verify authorization. 1 = NORMAL: Privilege usage within expected patterns.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (escalation) or 1 (normal)"
            },
            "model_name": {
                "business_description": "Model for compliance audit trail.",
                "interpretation": "Always 'privilege_escalation_detector'.",
                "data_type": "STRING",
                "valid_values": "privilege_escalation_detector"
            },
            "scored_at": {
                "business_description": "Detection timestamp.",
                "interpretation": "Recent detection enables timely response.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "user_behavior_predictions": {
        "table_comment": """ML predictions from user_behavior_baseline detecting deviations from normal behavior.
Uses Isolation Forest to establish and monitor user activity baselines.
Interpretation: -1 = behavior anomaly (deviation from baseline), 1 = normal baseline activity.
Business Use: User behavior analytics, insider threat detection, compromised account detection.
Action: Investigate -1 predictions for account compromise or policy violations.
Model: Isolation Forest | Domain: Security | Source: security_features | Refresh: Daily batch inference""",
        "columns": {
            "user_id": {
                "business_description": "User with behavior deviation from established baseline.",
                "interpretation": "May indicate compromised account or policy violation. Verify user identity.",
                "data_type": "STRING",
                "join_table": "dim_user"
            },
            "event_date": {
                "business_description": "Date of the behavior observation.",
                "interpretation": "Compare against user's historical activity pattern.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Behavior deviation indicator.",
                "interpretation": "-1 = BEHAVIOR ANOMALY: Activity differs significantly from baseline. Investigate. 1 = NORMAL: Activity consistent with established behavior patterns.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (anomaly) or 1 (normal)"
            },
            "model_name": {
                "business_description": "Model for UBA tracking.",
                "interpretation": "Always 'user_behavior_baseline'.",
                "data_type": "STRING",
                "valid_values": "user_behavior_baseline"
            },
            "scored_at": {
                "business_description": "Baseline comparison timestamp.",
                "interpretation": "Regular updates ensure baseline stays current.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },

    # =========================================================================
    # PERFORMANCE DOMAIN PREDICTIONS
    # =========================================================================
    "query_performance_predictions": {
        "table_comment": """ML predictions from query_performance_forecaster for query latency planning.
Uses Gradient Boosting Regression to forecast expected query execution times.
Interpretation: Prediction is forecasted query duration in seconds for the warehouse-date.
Business Use: SLA planning, capacity management, performance monitoring.
Action: Compare predicted vs actual latency. Large variances indicate performance issues.
Model: GradientBoostingRegressor | Domain: Performance | Source: performance_features | Refresh: Daily batch inference""",
        "columns": {
            "warehouse_id": {
                "business_description": "SQL Warehouse for performance forecast.",
                "interpretation": "Use for per-warehouse SLA tracking and capacity planning.",
                "data_type": "STRING",
                "join_table": "dim_warehouse"
            },
            "query_date": {
                "business_description": "Date for which query performance is forecasted.",
                "interpretation": "Compare forecast to actual p50/p95 latency for accuracy.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Forecasted average query execution time in seconds.",
                "interpretation": "Use as SLA baseline. Actual > prediction * 1.5 indicates degradation.",
                "data_type": "DOUBLE",
                "valid_values": ">= 0 (seconds)"
            },
            "model_name": {
                "business_description": "Model for performance lineage.",
                "interpretation": "Always 'query_performance_forecaster'.",
                "data_type": "STRING",
                "valid_values": "query_performance_forecaster"
            },
            "scored_at": {
                "business_description": "Forecast generation timestamp.",
                "interpretation": "Recent forecasts use latest patterns.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "warehouse_optimizer_predictions": {
        "table_comment": """ML predictions from warehouse_optimizer recommending sizing adjustments.
Uses Gradient Boosting to score warehouses by optimization need.
Interpretation: Higher score indicates more optimization opportunity (sizing, auto-scaling).
Business Use: Right-sizing warehouses, improving cost efficiency, reducing over-provisioning.
Action: Review high-score warehouses for sizing adjustments or auto-scaling policy changes.
Model: GradientBoostingRegressor | Domain: Performance | Source: performance_features | Refresh: Daily batch inference""",
        "columns": {
            "warehouse_id": {
                "business_description": "SQL Warehouse identified for optimization review.",
                "interpretation": "Join with dim_warehouse for current size and configuration.",
                "data_type": "STRING",
                "join_table": "dim_warehouse"
            },
            "query_date": {
                "business_description": "Date of performance data used for analysis.",
                "interpretation": "Use recent dates for current optimization recommendations.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Optimization opportunity score.",
                "interpretation": "Score > 0.7: Immediate sizing review needed. Score 0.4-0.7: Schedule optimization review. Score < 0.4: Well-optimized.",
                "data_type": "DOUBLE",
                "valid_values": "0 to 1 (continuous)"
            },
            "model_name": {
                "business_description": "Model for optimization tracking.",
                "interpretation": "Always 'warehouse_optimizer'.",
                "data_type": "STRING",
                "valid_values": "warehouse_optimizer"
            },
            "scored_at": {
                "business_description": "Scoring timestamp.",
                "interpretation": "Use recent scores for optimization planning.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "cluster_capacity_predictions": {
        "table_comment": """ML predictions from cluster_capacity_planner for capacity forecasting.
Uses Gradient Boosting to predict capacity requirements based on workload patterns.
Interpretation: Prediction is forecasted capacity need (cluster count or DBU).
Business Use: Capacity planning, auto-scaling policy optimization, cost management.
Action: Use predictions for pre-provisioning and auto-scaling threshold configuration.
Model: GradientBoostingRegressor | Domain: Performance | Source: performance_features | Refresh: Daily batch inference""",
        "columns": {
            "warehouse_id": {
                "business_description": "Warehouse for capacity planning.",
                "interpretation": "Use for per-warehouse capacity allocation decisions.",
                "data_type": "STRING",
                "join_table": "dim_warehouse"
            },
            "query_date": {
                "business_description": "Date for capacity forecast.",
                "interpretation": "Compare with actual utilization for forecast accuracy.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Forecasted capacity requirement.",
                "interpretation": "Use for auto-scaling max cluster settings. Over-provisioning wastes cost.",
                "data_type": "DOUBLE",
                "valid_values": ">= 0 (cluster count or DBU)"
            },
            "model_name": {
                "business_description": "Model for capacity lineage.",
                "interpretation": "Always 'cluster_capacity_planner'.",
                "data_type": "STRING",
                "valid_values": "cluster_capacity_planner"
            },
            "scored_at": {
                "business_description": "Forecast timestamp.",
                "interpretation": "Recent forecasts reflect current workload patterns.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "performance_regression_predictions": {
        "table_comment": """ML predictions from performance_regression_detector identifying degradation.
Uses Isolation Forest to detect performance regression patterns.
Interpretation: -1 = regression detected (performance degraded), 1 = normal performance.
Business Use: Performance monitoring, SLA alerting, regression detection.
Action: Investigate -1 predictions for root cause. Check recent code changes or data growth.
Model: Isolation Forest | Domain: Performance | Source: performance_features | Refresh: Daily batch inference""",
        "columns": {
            "warehouse_id": {
                "business_description": "Warehouse with detected performance regression.",
                "interpretation": "Prioritize -1 warehouses for performance investigation.",
                "data_type": "STRING",
                "join_table": "dim_warehouse"
            },
            "query_date": {
                "business_description": "Date of performance regression detection.",
                "interpretation": "Correlate with code deployments or data volume changes.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Performance regression indicator.",
                "interpretation": "-1 = REGRESSION: Performance significantly degraded from baseline. Investigate immediately. 1 = NORMAL: Performance within expected range.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (regression) or 1 (normal)"
            },
            "model_name": {
                "business_description": "Model for performance lineage.",
                "interpretation": "Always 'performance_regression_detector'.",
                "data_type": "STRING",
                "valid_values": "performance_regression_detector"
            },
            "scored_at": {
                "business_description": "Detection timestamp.",
                "interpretation": "Recent detection enables timely remediation.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "dbr_migration_predictions": {
        "table_comment": """ML predictions from dbr_migration_risk_scorer for runtime upgrade planning.
Uses Random Forest to assess migration risk based on job characteristics and history.
Interpretation: 1 = high migration risk, 0 = low risk (safe to migrate).
Business Use: DBR upgrade planning, risk assessment, migration prioritization.
Action: Test high-risk jobs (prediction=1) thoroughly before DBR upgrade. Low-risk can proceed.
Model: RandomForestClassifier | Domain: Performance | Source: reliability_features | Refresh: Daily batch inference""",
        "columns": {
            "job_id": {
                "business_description": "Job assessed for DBR migration risk.",
                "interpretation": "prediction=1 jobs need extended testing before DBR upgrade.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "run_date": {
                "business_description": "Date of job data used for risk assessment.",
                "interpretation": "Recent dates provide more relevant risk assessment.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "DBR migration risk assessment.",
                "interpretation": "1 = HIGH RISK: Job has characteristics that correlate with migration failures. Test thoroughly. 0 = LOW RISK: Job likely compatible with new DBR version.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 (low risk) or 1 (high risk)"
            },
            "model_name": {
                "business_description": "Model for migration planning.",
                "interpretation": "Always 'dbr_migration_risk_scorer'.",
                "data_type": "STRING",
                "valid_values": "dbr_migration_risk_scorer"
            },
            "scored_at": {
                "business_description": "Assessment timestamp.",
                "interpretation": "Use recent assessments for upgrade planning.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "cache_hit_predictions": {
        "table_comment": """ML predictions from cache_hit_predictor for query caching optimization.
Uses XGBoost Classification to predict cache hit likelihood.
Interpretation: 1 = high cache hit likelihood, 0 = low (cache miss expected).
Business Use: Cache optimization, query planning, cost reduction.
Action: Queries with low cache hit prediction may benefit from query restructuring.
Model: XGBClassifier | Domain: Performance | Source: performance_features | Refresh: Daily batch inference""",
        "columns": {
            "warehouse_id": {
                "business_description": "Warehouse for cache analysis.",
                "interpretation": "Track cache hit rates by warehouse for optimization.",
                "data_type": "STRING",
                "join_table": "dim_warehouse"
            },
            "query_date": {
                "business_description": "Date of cache prediction.",
                "interpretation": "Aggregate by date for cache efficiency trends.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Cache hit likelihood prediction.",
                "interpretation": "1 = CACHE HIT LIKELY: Query pattern suits caching. Expect fast response. 0 = CACHE MISS LIKELY: Query will scan data. May be slow.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 (miss) or 1 (hit)"
            },
            "model_name": {
                "business_description": "Model for cache optimization.",
                "interpretation": "Always 'cache_hit_predictor'.",
                "data_type": "STRING",
                "valid_values": "cache_hit_predictor"
            },
            "scored_at": {
                "business_description": "Prediction timestamp.",
                "interpretation": "Use for cache policy tuning.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "query_optimization_predictions": {
        "table_comment": """ML predictions from query_optimization_recommender for tuning prioritization.
Uses XGBoost Classification to identify queries needing optimization.
Interpretation: 1 = needs optimization, 0 = performing adequately.
Business Use: Query tuning prioritization, performance improvement, SLA management.
Action: Focus optimization efforts on prediction=1 queries. Review execution plans.
Model: XGBClassifier | Domain: Performance | Source: performance_features | Refresh: Daily batch inference""",
        "columns": {
            "warehouse_id": {
                "business_description": "Warehouse with queries needing optimization.",
                "interpretation": "Aggregate prediction=1 count by warehouse for optimization resource allocation.",
                "data_type": "STRING",
                "join_table": "dim_warehouse"
            },
            "query_date": {
                "business_description": "Date of optimization analysis.",
                "interpretation": "Focus on recent dates for current workload optimization.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Query optimization recommendation.",
                "interpretation": "1 = NEEDS OPTIMIZATION: Query has optimization opportunities. Review execution plan. 0 = ADEQUATE: Query performing within acceptable range.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 (adequate) or 1 (needs optimization)"
            },
            "model_name": {
                "business_description": "Model for optimization tracking.",
                "interpretation": "Always 'query_optimization_recommender'.",
                "data_type": "STRING",
                "valid_values": "query_optimization_recommender"
            },
            "scored_at": {
                "business_description": "Recommendation timestamp.",
                "interpretation": "Use recent recommendations for optimization planning.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },

    # =========================================================================
    # RELIABILITY DOMAIN PREDICTIONS
    # =========================================================================
    "job_failure_predictions": {
        "table_comment": """ML predictions from job_failure_predictor for proactive failure prevention.
Uses XGBoost Classification to predict job failure likelihood based on historical patterns.
Interpretation: 1 = high failure likelihood, 0 = likely to succeed.
Business Use: Proactive monitoring, SRE alerting, failure prevention, incident management.
Action: Monitor prediction=1 jobs closely. Preemptively scale resources or fix known issues.
Model: XGBClassifier | Domain: Reliability | Source: reliability_features | Refresh: Daily batch inference""",
        "columns": {
            "job_id": {
                "business_description": "Job at risk of failure based on historical patterns.",
                "interpretation": "prediction=1 jobs need proactive attention. Review recent failures.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "run_date": {
                "business_description": "Date for which failure is being predicted.",
                "interpretation": "Daily predictions enable proactive intervention.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Failure likelihood prediction.",
                "interpretation": "1 = HIGH FAILURE RISK: Job likely to fail based on patterns. Take preventive action. 0 = LIKELY SUCCESS: Job expected to complete successfully.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 (success) or 1 (failure risk)"
            },
            "model_name": {
                "business_description": "Model for SRE monitoring.",
                "interpretation": "Always 'job_failure_predictor'.",
                "data_type": "STRING",
                "valid_values": "job_failure_predictor"
            },
            "scored_at": {
                "business_description": "Prediction timestamp.",
                "interpretation": "Recent predictions enable timely intervention.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "duration_predictions": {
        "table_comment": """ML predictions from job_duration_forecaster for SLA planning.
Uses Gradient Boosting Regression to forecast expected job run duration.
Interpretation: Prediction is forecasted duration in seconds.
Business Use: SLA planning, scheduling optimization, capacity management.
Action: Use for job scheduling and SLA alerting thresholds.
Model: GradientBoostingRegressor | Domain: Reliability | Source: reliability_features | Refresh: Daily batch inference""",
        "columns": {
            "job_id": {
                "business_description": "Job for duration forecasting.",
                "interpretation": "Use for per-job SLA tracking and alerting.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "run_date": {
                "business_description": "Date for which duration is forecasted.",
                "interpretation": "Compare forecast to actual for accuracy tracking.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Forecasted job duration in seconds.",
                "interpretation": "Use as SLA baseline. Actual > prediction * 1.5 indicates issue.",
                "data_type": "DOUBLE",
                "valid_values": ">= 0 (seconds)"
            },
            "model_name": {
                "business_description": "Model for SLA lineage.",
                "interpretation": "Always 'job_duration_forecaster'.",
                "data_type": "STRING",
                "valid_values": "job_duration_forecaster"
            },
            "scored_at": {
                "business_description": "Forecast timestamp.",
                "interpretation": "Recent forecasts use latest job patterns.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "sla_breach_predictions": {
        "table_comment": """ML predictions from sla_breach_predictor for SLA monitoring.
Uses XGBoost Classification to predict SLA breach likelihood.
Interpretation: 1 = high SLA breach risk, 0 = likely to meet SLA.
Business Use: SLA monitoring, proactive intervention, customer communication.
Action: Escalate prediction=1 jobs. Consider rescheduling or resource scaling.
Model: XGBClassifier | Domain: Reliability | Source: reliability_features | Refresh: Daily batch inference""",
        "columns": {
            "job_id": {
                "business_description": "Job at risk of SLA breach.",
                "interpretation": "prediction=1 jobs need immediate attention for SLA compliance.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "run_date": {
                "business_description": "Date for SLA risk prediction.",
                "interpretation": "Use for daily SLA risk dashboard.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "SLA breach risk prediction.",
                "interpretation": "1 = SLA AT RISK: Job likely to miss SLA target. Intervene now. 0 = SLA SAFE: Job expected to meet SLA.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 (safe) or 1 (at risk)"
            },
            "model_name": {
                "business_description": "Model for SLA governance.",
                "interpretation": "Always 'sla_breach_predictor'.",
                "data_type": "STRING",
                "valid_values": "sla_breach_predictor"
            },
            "scored_at": {
                "business_description": "Prediction timestamp.",
                "interpretation": "Timely predictions enable SLA compliance.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "retry_success_predictions": {
        "table_comment": """ML predictions from retry_success_predictor for intelligent retry policies.
Uses XGBoost Classification to predict retry success likelihood.
Interpretation: 1 = retry likely to succeed, 0 = retry unlikely to help.
Business Use: Intelligent retry policies, resource optimization, failure handling.
Action: Configure retries for prediction=1 jobs. Skip retries for prediction=0 (fix root cause instead).
Model: XGBClassifier | Domain: Reliability | Source: reliability_features | Refresh: Daily batch inference""",
        "columns": {
            "job_id": {
                "business_description": "Job for retry success analysis.",
                "interpretation": "Use to configure per-job retry policies.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "run_date": {
                "business_description": "Date of retry analysis.",
                "interpretation": "Recent patterns indicate current retry success likelihood.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Retry success likelihood prediction.",
                "interpretation": "1 = RETRY LIKELY TO HELP: Transient failure, retry recommended. 0 = RETRY UNLIKELY: Persistent issue, fix root cause instead of retrying.",
                "data_type": "DOUBLE (INTEGER 0 or 1)",
                "valid_values": "0 (don't retry) or 1 (retry)"
            },
            "model_name": {
                "business_description": "Model for retry policy.",
                "interpretation": "Always 'retry_success_predictor'.",
                "data_type": "STRING",
                "valid_values": "retry_success_predictor"
            },
            "scored_at": {
                "business_description": "Analysis timestamp.",
                "interpretation": "Use recent predictions for retry configuration.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "pipeline_health_predictions": {
        "table_comment": """ML predictions from pipeline_health_scorer for overall pipeline monitoring.
Uses Gradient Boosting Regression to score pipeline health holistically.
Interpretation: Score 0-1 where higher = healthier pipeline.
Business Use: Pipeline monitoring, maintenance prioritization, health dashboards.
Action: Focus maintenance on low-score pipelines. Use for health dashboards.
Model: GradientBoostingRegressor | Domain: Reliability | Source: reliability_features | Refresh: Daily batch inference""",
        "columns": {
            "job_id": {
                "business_description": "Pipeline/job for health scoring.",
                "interpretation": "Use for pipeline health ranking and prioritization.",
                "data_type": "STRING",
                "join_table": "dim_job"
            },
            "run_date": {
                "business_description": "Date of health assessment.",
                "interpretation": "Track health trends over time.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Pipeline health score.",
                "interpretation": "Score > 0.8: Healthy. Score 0.5-0.8: Needs attention. Score < 0.5: Critical, immediate intervention needed.",
                "data_type": "DOUBLE",
                "valid_values": "0 to 1 (continuous)"
            },
            "model_name": {
                "business_description": "Model for health monitoring.",
                "interpretation": "Always 'pipeline_health_scorer'.",
                "data_type": "STRING",
                "valid_values": "pipeline_health_scorer"
            },
            "scored_at": {
                "business_description": "Scoring timestamp.",
                "interpretation": "Use recent scores for health dashboards.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },

    # =========================================================================
    # QUALITY DOMAIN PREDICTIONS
    # =========================================================================
    "data_drift_predictions": {
        "table_comment": """ML predictions from data_drift_detector identifying data distribution changes.
Uses Isolation Forest anomaly detection on catalog metadata features.
Interpretation: -1 = drift detected (distribution changed), 1 = stable distribution.
Business Use: Data quality monitoring, model retraining triggers, data governance.
Action: Investigate -1 predictions. May indicate upstream data issues or need model retraining.
Model: Isolation Forest | Domain: Quality | Source: quality_features | Refresh: Daily batch inference""",
        "columns": {
            "catalog_name": {
                "business_description": "Unity Catalog where data drift was detected.",
                "interpretation": "Catalog-level drift may affect multiple downstream models.",
                "data_type": "STRING",
                "valid_values": "Unity Catalog name"
            },
            "snapshot_date": {
                "business_description": "Date of drift detection analysis.",
                "interpretation": "Track drift over time. Persistent drift indicates systemic issue.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Data drift indicator.",
                "interpretation": "-1 = DRIFT DETECTED: Data distribution has changed significantly. Review upstream pipelines. 1 = STABLE: Data distribution within historical norms.",
                "data_type": "DOUBLE (INTEGER -1 or 1)",
                "valid_values": "-1 (drift) or 1 (stable)"
            },
            "model_name": {
                "business_description": "Model for data quality governance.",
                "interpretation": "Always 'data_drift_detector'.",
                "data_type": "STRING",
                "valid_values": "data_drift_detector"
            },
            "scored_at": {
                "business_description": "Detection timestamp.",
                "interpretation": "Recent detection enables timely data quality response.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    },
    
    "freshness_predictions": {
        "table_comment": """ML predictions from data_freshness_predictor for data timeliness monitoring.
Uses Gradient Boosting Regression to predict/assess data freshness.
Interpretation: Higher score = fresher data. Low score indicates stale data.
Business Use: Data freshness monitoring, SLA compliance, pipeline health.
Action: Low freshness scores indicate delayed pipelines. Investigate ETL jobs.
Model: GradientBoostingRegressor | Domain: Quality | Source: quality_features | Refresh: Daily batch inference""",
        "columns": {
            "catalog_name": {
                "business_description": "Unity Catalog being monitored for freshness.",
                "interpretation": "Track freshness by catalog for data governance.",
                "data_type": "STRING",
                "valid_values": "Unity Catalog name"
            },
            "snapshot_date": {
                "business_description": "Date of freshness assessment.",
                "interpretation": "Daily freshness tracking for SLA monitoring.",
                "data_type": "DATE",
                "valid_values": "Past dates"
            },
            "prediction": {
                "business_description": "Data freshness score or predicted staleness.",
                "interpretation": "Higher score = fresher data. Score < 0.5 indicates stale data requiring investigation.",
                "data_type": "DOUBLE",
                "valid_values": "0 to 1 (continuous, higher = fresher)"
            },
            "model_name": {
                "business_description": "Model for freshness monitoring.",
                "interpretation": "Always 'data_freshness_predictor'.",
                "data_type": "STRING",
                "valid_values": "data_freshness_predictor"
            },
            "scored_at": {
                "business_description": "Assessment timestamp.",
                "interpretation": "Use recent assessments for SLA reporting.",
                "data_type": "TIMESTAMP",
                "valid_values": "Recent timestamp"
            }
        }
    }
}


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def apply_table_metadata(spark, full_table_name: str) -> bool:
    """
    Apply comprehensive table and column metadata to a prediction table.
    
    Args:
        spark: SparkSession
        full_table_name: Fully qualified table name (catalog.schema.table)
        
    Returns:
        True if metadata was applied successfully, False otherwise
    """
    table_name = full_table_name.split('.')[-1]
    
    if table_name not in PREDICTION_TABLE_METADATA:
        print(f"    ⚠ No metadata defined for {table_name}")
        return False
    
    metadata = PREDICTION_TABLE_METADATA[table_name]
    
    try:
        # Apply table comment
        table_comment = metadata.get("table_comment", "").replace("'", "''")
        spark.sql(f"COMMENT ON TABLE {full_table_name} IS '{table_comment}'")
        print(f"    📝 Table comment added")
        
        # Apply column comments with full business + interpretation
        columns = metadata.get("columns", {})
        columns_updated = 0
        
        # Get actual columns from table
        table_columns = [f.name for f in spark.table(full_table_name).schema.fields]
        
        for col_name, col_meta in columns.items():
            if col_name in table_columns:
                # Combine descriptions for comprehensive column comment
                if isinstance(col_meta, dict):
                    business_desc = col_meta.get("business_description", "")
                    interpretation = col_meta.get("interpretation", "")
                    data_type = col_meta.get("data_type", "")
                    valid_values = col_meta.get("valid_values", "")
                    join_table = col_meta.get("join_table", "")
                    
                    # Format: Business description. Interpretation: ... | Type: ... | Values: ... | Join: ...
                    full_comment = business_desc
                    if interpretation:
                        full_comment += f" Interpretation: {interpretation}"
                    if data_type:
                        full_comment += f" | Type: {data_type}"
                    if valid_values:
                        full_comment += f" | Values: {valid_values}"
                    if join_table:
                        full_comment += f" | Join: {join_table}"
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


def get_table_metadata(table_name: str) -> Dict[str, Any]:
    """Get metadata for a specific prediction table."""
    return PREDICTION_TABLE_METADATA.get(table_name, {})


def get_all_prediction_tables() -> List[str]:
    """Get list of all prediction table names with metadata defined."""
    return list(PREDICTION_TABLE_METADATA.keys())


def get_column_descriptions(table_name: str, include_interpretation: bool = True) -> Dict[str, str]:
    """
    Get simplified column descriptions for a prediction table.
    
    Args:
        table_name: Name of the prediction table
        include_interpretation: If True, includes interpretation guidance
        
    Returns:
        Dictionary of column name to description
    """
    metadata = PREDICTION_TABLE_METADATA.get(table_name, {})
    columns = metadata.get("columns", {})
    
    result = {}
    for col_name, col_meta in columns.items():
        if isinstance(col_meta, dict):
            desc = col_meta.get("business_description", "")
            if include_interpretation and col_meta.get("interpretation"):
                desc += f" {col_meta.get('interpretation')}"
            result[col_name] = desc
        else:
            result[col_name] = col_meta
    
    return result


def get_prediction_interpretation(table_name: str) -> str:
    """
    Get the interpretation guidance for a prediction table's prediction column.
    
    Args:
        table_name: Name of the prediction table
        
    Returns:
        Interpretation string for the prediction column
    """
    metadata = PREDICTION_TABLE_METADATA.get(table_name, {})
    columns = metadata.get("columns", {})
    
    prediction_col = columns.get("prediction", {})
    if isinstance(prediction_col, dict):
        return prediction_col.get("interpretation", "")
    return ""
