# Databricks notebook source
# ===========================================================================
# PATH SETUP FOR ASSET BUNDLE IMPORTS
# ===========================================================================
import sys
import os

try:
    _notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    _bundle_root = "/Workspace" + str(_notebook_path).rsplit('/src/', 1)[0]
    if _bundle_root not in sys.path:
        sys.path.insert(0, _bundle_root)
        print(f"✓ Added bundle root to sys.path: {_bundle_root}")
except Exception as e:
    print(f"⚠ Path setup skipped (local execution): {e}")
# ===========================================================================
"""
Register Prompts
================

Registers all agent prompts to MLflow Prompt Registry with versioning
and production aliases.

Schema Naming Convention:
    Dev: prashanth_subrahmanyam_catalog.dev_<user>_system_gold_agent
    Prod: main.system_gold_agent
"""

# COMMAND ----------

import mlflow
import mlflow.genai
from mlflow import MlflowClient


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    agent_schema = dbutils.widgets.get("agent_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Agent Schema: {agent_schema}")
    
    return catalog, agent_schema


# COMMAND ----------

# Prompt definitions
PROMPTS = {
    "orchestrator": """You are the Health Monitor Orchestrator Agent for Databricks platform monitoring.

Your role is to:
1. Understand the user's query about their Databricks environment
2. Route queries to the appropriate domain specialist (Cost, Security, Performance, Reliability, Quality)
3. Synthesize responses from multiple specialists when needed
4. Provide clear, actionable insights

User Context:
{user_context}

Conversation History:
{conversation_history}

Current Query:
{query}

Available Domains:
- COST: DBU usage, spending, budgets, cost optimization
- SECURITY: Access control, audit logs, permissions, compliance
- PERFORMANCE: Query speed, cluster utilization, optimization
- RELIABILITY: Job failures, SLAs, pipeline health
- QUALITY: Data quality, lineage, freshness

Respond with:
1. Which domain(s) to query
2. What specific questions to ask each domain
3. How to synthesize the responses""",

    "intent_classifier": """Classify the user's query into one or more Databricks monitoring domains.

Query: {query}

Domains:
- COST: Spending, DBU usage, budgets, cost allocation, billing
- SECURITY: Access control, audit, permissions, compliance, secrets
- PERFORMANCE: Speed, latency, optimization, cluster utilization
- RELIABILITY: Failures, SLAs, uptime, pipeline health
- QUALITY: Data quality, freshness, lineage, governance

Respond with JSON:
{{"domains": ["DOMAIN1", "DOMAIN2"], "confidence": 0.95, "reasoning": "..."}}""",

    "synthesizer": """Synthesize responses from multiple domain specialists into a coherent answer.

User Query: {query}

Domain Responses:
{domain_responses}

Guidelines:
1. Combine insights from all domains
2. Highlight key findings and recommendations
3. Note any conflicting information
4. Provide actionable next steps

Synthesized Response:"""
}


# COMMAND ----------

def register_prompt(catalog: str, schema: str, name: str, template: str):
    """Register a prompt to MLflow with versioning."""
    model_name = f"{catalog}.{schema}.prompt_{name}"
    
    print(f"Registering prompt: {name} -> {model_name}")
    
    try:
        with mlflow.start_run(run_name=f"prompt_{name}_registration"):
            # Log the prompt
            mlflow.genai.log_prompt(
                prompt=template,
                artifact_path=f"prompts/{name}",
                registered_model_name=model_name
            )
            
            # Get the latest version
            client = MlflowClient()
            latest_versions = client.get_latest_versions(model_name)
            
            if latest_versions:
                latest_version = latest_versions[0].version
                
                # Set production alias
                client.set_registered_model_alias(
                    name=model_name,
                    alias="production",
                    version=latest_version
                )
                print(f"  ✓ Registered {name} v{latest_version}, alias=production")
            
    except Exception as e:
        print(f"  ⚠ Error registering {name}: {e}")
        raise


def main():
    """Main entry point."""
    catalog, agent_schema = get_parameters()
    
    # Set experiment for prompt tracking
    experiment_path = f"/Shared/health_monitor/prompts"
    mlflow.set_experiment(experiment_path)
    print(f"Using MLflow experiment: {experiment_path}")
    
    try:
        for name, template in PROMPTS.items():
            register_prompt(catalog, agent_schema, name, template)
        
        print("\n" + "=" * 60)
        print("✓ All prompts registered successfully!")
        print("=" * 60)
        
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error registering prompts: {str(e)}")
        raise


# COMMAND ----------

if __name__ == "__main__":
    main()

