#!/usr/bin/env python3
"""
Complete the remaining Genie Space JSON exports by copying patterns from successful ones.

This script creates proper JSON exports for performance, security_auditor, and 
unified_health_monitor by using the cost_intelligence and job_health_monitor 
JSONs as templates and populating them with data from the markdown files.
"""

import json
import re
import uuid
from pathlib import Path
from typing import List, Dict

def generate_id():
    """Generate a Genie Space compatible ID (32 hex chars without dashes)."""
    return uuid.uuid4().hex

def main():
    project_root = Path(__file__).parent.parent
    genie_dir = project_root / "src" / "genie"
    
    # Load the template (cost_intelligence is comprehensive)
    template_file = genie_dir / "cost_intelligence_genie_export.json"
    with open(template_file) as f:
        template = json.load(f)
    
    # Spaces to complete
    spaces_to_complete = {
        "performance_genie_export.json": {
            "title": "Health Monitor Performance Space",
            "description": "Natural language interface for Databricks query and cluster performance analytics. Enables DBAs, platform engineers, and FinOps to query execution metrics, warehouse utilization, cluster efficiency, and right-sizing opportunities without SQL.",
            "metric_views": [
                "${catalog}.${gold_schema}.query_performance",
                "${catalog}.${gold_schema}.cluster_utilization",
                "${catalog}.${gold_schema}.cluster_efficiency"
            ],
            "fact_tables": [
                "${catalog}.${gold_schema}.fact_query_history",
                "${catalog}.${gold_schema}.fact_warehouse_events",
                "${catalog}.${gold_schema}.fact_node_timeline"
            ],
            "dim_tables": [
                "${catalog}.${gold_schema}.dim_warehouse",
                "${catalog}.${gold_schema}.dim_cluster",
                "${catalog}.${gold_schema}.dim_node_type",
                "${catalog}.${gold_schema}.dim_workspace"
            ],
            "ml_tables": [
                "${catalog}.${feature_schema}.query_optimization_classifications",
                "${catalog}.${feature_schema}.query_optimization_recommendations",
                "${catalog}.${feature_schema}.cache_hit_predictions",
                "${catalog}.${feature_schema}.job_duration_predictions",
                "${catalog}.${feature_schema}.cluster_capacity_recommendations",
                "${catalog}.${feature_schema}.cluster_rightsizing_recommendations",
                "${catalog}.${feature_schema}.dbr_migration_risk_scores"
            ],
            "monitoring_tables": [
                "${catalog}.${gold_schema}.fact_query_history_profile_metrics",
                "${catalog}.${gold_schema}.fact_query_history_drift_metrics",
                "${catalog}.${gold_schema}.fact_node_timeline_profile_metrics",
                "${catalog}.${gold_schema}.fact_node_timeline_drift_metrics"
            ],
            "sample_questions": [
                "What is our average query duration?",
                "Show me slow queries from today",
                "What is the P95 query duration?",
                "Which warehouse has the highest queue time?",
                "What is our average CPU utilization?",
                "Which clusters are underutilized?",
                "Show me right-sizing recommendations",
                "What's the potential savings from downsizing?",
                "Which queries should I optimize?"
            ]
        },
        "security_auditor_genie_export.json": {
            "title": "Health Monitor Security Auditor Space",
            "description": "Natural language interface for Databricks security audit and compliance analytics. Enables security teams, compliance officers, and platform admins to query access patterns, suspicious activities, and policy violations without SQL.",
            "metric_views": [
                "${catalog}.${gold_schema}.security_analytics"
            ],
            "fact_tables": [
                "${catalog}.${gold_schema}.fact_audit_logs"
            ],
            "dim_tables": [
                "${catalog}.${gold_schema}.dim_workspace"
            ],
            "ml_tables": [
                "${catalog}.${feature_schema}.anomalous_access_predictions",
                "${catalog}.${feature_schema}.privilege_escalation_predictions",
                "${catalog}.${feature_schema}.data_exfiltration_predictions",
                "${catalog}.${feature_schema}.compliance_risk_predictions",
                "${catalog}.${feature_schema}.access_pattern_predictions"
            ],
            "monitoring_tables": [
                "${catalog}.${gold_schema}.fact_audit_logs_profile_metrics",
                "${catalog}.${gold_schema}.fact_audit_logs_drift_metrics"
            ],
            "sample_questions": [
                "Show me failed login attempts",
                "What are recent security events?",
                "Which users have high risk scores?",
                "Show me admin actions today",
                "What tables were accessed by external users?",
                "Show me suspicious activities",
                "What are compliance violations?",
                "Who accessed sensitive data?"
            ]
        },
        "unified_health_monitor_genie_export.json": {
            "title": "Health Monitor Unified Space",
            "description": "Comprehensive Databricks platform health monitoring across cost, reliability, security, performance, and quality. Unified natural language interface for enterprise-wide observability.",
            "metric_views": [
                "${catalog}.${gold_schema}.cost_analytics",
                "${catalog}.${gold_schema}.job_performance",
                "${catalog}.${gold_schema}.query_performance"
            ],
            "fact_tables": [
                "${catalog}.${gold_schema}.fact_usage",
                "${catalog}.${gold_schema}.fact_job_run_timeline",
                "${catalog}.${gold_schema}.fact_query_history"
            ],
            "dim_tables": [
                "${catalog}.${gold_schema}.dim_workspace",
                "${catalog}.${gold_schema}.dim_sku",
                "${catalog}.${gold_schema}.dim_job",
                "${catalog}.${gold_schema}.dim_warehouse"
            ],
            "ml_tables": [
                "${catalog}.${feature_schema}.cost_anomaly_predictions",
                "${catalog}.${feature_schema}.job_failure_predictions",
                "${catalog}.${feature_schema}.query_optimization_recommendations"
            ],
            "monitoring_tables": [
                "${catalog}.${gold_schema}.fact_usage_profile_metrics",
                "${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics",
                "${catalog}.${gold_schema}.fact_query_history_profile_metrics"
            ],
            "sample_questions": [
                "What is our total spend this month?",
                "Which jobs failed today?",
                "Show me slow queries",
                "What is the job success rate?",
                "Which resources are underutilized?",
                "Show me cost anomalies",
                "What is our SLA breach rate?",
                "Which workspaces have the highest cost?"
            ]
        }
    }
    
    # Create each JSON
    for json_name, config in spaces_to_complete.items():
        print(f"Creating {json_name}...")
        
        # Start with template structure
        new_json = {
            "version": 1,
            "config": {
                "title": config["title"],
                "description": config["description"],
                "warehouse_id": "${warehouse_id}",
                "sample_questions": [
                    {"id": generate_id(), "question": [q]}
                    for q in config["sample_questions"]
                ]
            },
            "data_sources": {
                "tables": [],
                "metric_views": []
            },
            "instructions": {
                "sql_functions": [],  # Will need to be populated from markdown
                "text_instructions": [],
                "example_question_sqls": [],
                "join_specs": []
            },
            "benchmarks": {
                "questions": []  # Will need to be populated from markdown
            }
        }
        
        # Add tables
        for table in sorted(set(
            config.get("metric_views", []) +
            config.get("fact_tables", []) +
            config.get("dim_tables", []) +
            config.get("ml_tables", []) +
            config.get("monitoring_tables", [])
        )):
            new_json["data_sources"]["tables"].append({
                "identifier": table,
                "column_configs": []  # Minimal for now
            })
        
        # Write JSON
        output_file = genie_dir / json_name
        with open(output_file, 'w') as f:
            json.dump(new_json, f, indent=2)
        
        print(f"✅ Created {json_name} ({len(new_json['data_sources']['tables'])} tables)")
    
    print("\n✅ Completed all Genie Space JSON exports!")
    print("\n📋 Next steps:")
    print("1. Review the generated JSON files")
    print("2. Add TVF references to instructions.sql_functions from markdown")
    print("3. Add benchmark questions to benchmarks.questions from markdown")
    print("4. Deploy with: DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev genie_spaces_deployment_job")

if __name__ == "__main__":
    main()

