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

Stores all agent prompts in the agent_config table for versioning
and retrieval at runtime. Also logs to MLflow as artifacts for tracking.

Note: The MLflow Prompt Registry API (mlflow.genai.log_prompt) is not available
in current MLflow versions. We use a table-based approach instead.

Schema Naming Convention:
    Dev: prashanth_subrahmanyam_catalog.dev_<user>_system_gold_agent
    Prod: main.system_gold_agent
"""

# COMMAND ----------

import mlflow
import json
from datetime import datetime
from pyspark.sql import SparkSession


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

def register_prompts_to_table(spark: SparkSession, catalog: str, schema: str, prompts: dict):
    """
    Store prompts in the agent_config table for versioning and runtime retrieval.
    """
    table_name = f"{catalog}.{schema}.agent_config"
    current_time = datetime.now()
    
    print(f"Storing {len(prompts)} prompts in {table_name}...")
    
    for name, template in prompts.items():
        config_key = f"prompt_{name}"
        
        # Delete existing entry if exists
        spark.sql(f"""
            DELETE FROM {table_name}
            WHERE config_key = '{config_key}'
        """)
        
        # Insert new entry
        spark.sql(f"""
            INSERT INTO {table_name} (config_key, config_value, config_type, description, updated_at, updated_by)
            VALUES (
                '{config_key}',
                '{template.replace("'", "''")}',
                'string',
                'Agent prompt template: {name}',
                CURRENT_TIMESTAMP(),
                'setup_job'
            )
        """)
        print(f"  ✓ Stored prompt: {name}")


def log_prompts_to_mlflow(prompts: dict):
    """
    Log prompts as MLflow artifacts for tracking and versioning.
    """
    experiment_path = "/Shared/health_monitor/prompts"
    mlflow.set_experiment(experiment_path)
    
    print(f"\nLogging prompts to MLflow experiment: {experiment_path}")
    
    with mlflow.start_run(run_name="prompt_registration"):
        # Log each prompt as a text file artifact
        for name, template in prompts.items():
            # Write prompt to a temp file and log
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(template)
                temp_path = f.name
            
            mlflow.log_artifact(temp_path, artifact_path=f"prompts/{name}")
            os.remove(temp_path)
            print(f"  ✓ Logged artifact: prompts/{name}")
        
        # Log summary as JSON
        prompt_summary = {name: {"length": len(template), "variables": _extract_variables(template)} 
                        for name, template in prompts.items()}
        mlflow.log_dict(prompt_summary, "prompts/summary.json")
        
        # Log params
        mlflow.log_params({
            "prompt_count": len(prompts),
            "prompt_names": ",".join(prompts.keys()),
            "registration_timestamp": datetime.now().isoformat()
        })
        
        print(f"  ✓ Logged summary and parameters")


def _extract_variables(template: str) -> list:
    """Extract variable placeholders from a template string."""
    import re
    # Find all {variable} patterns
    variables = re.findall(r'\{(\w+)\}', template)
    return list(set(variables))


def main():
    """Main entry point."""
    catalog, agent_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Register Prompts").getOrCreate()
    
    try:
        print("\n" + "=" * 60)
        print("Registering Agent Prompts")
        print("=" * 60)
        
        # 1. Store prompts in the config table (primary storage)
        register_prompts_to_table(spark, catalog, agent_schema, PROMPTS)
        
        # 2. Log prompts to MLflow for tracking (secondary)
        log_prompts_to_mlflow(PROMPTS)
        
        print("\n" + "=" * 60)
        print("✓ All prompts registered successfully!")
        print("=" * 60)
        print(f"\nPrompts stored in: {catalog}.{agent_schema}.agent_config")
        print(f"MLflow artifacts at: /Shared/health_monitor/prompts")
        print(f"\nPrompts registered:")
        for name in PROMPTS:
            print(f"  - prompt_{name}")
        
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error registering prompts: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


# COMMAND ----------

if __name__ == "__main__":
    main()
