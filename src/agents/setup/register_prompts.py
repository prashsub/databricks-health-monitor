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

Respond with JSON format:
- "domains": array of domain names like ["COST", "SECURITY"]
- "confidence": number between 0 and 1
- "reasoning": brief explanation string""",

    "synthesizer": """Synthesize responses from multiple domain specialists into a coherent answer.

User Query: {query}

Domain Responses:
{domain_responses}

Guidelines:
1. Combine insights from all domains
2. Highlight key findings and recommendations
3. Note any conflicting information
4. Provide actionable next steps

Synthesized Response:""",

    # ==========================================================================
    # Domain Analyst Prompts
    # ==========================================================================
    
    "cost_analyst": """You are a Databricks Cost Analyst specializing in cloud spending optimization.

Query: {query}

Your expertise includes:
- DBU (Databricks Unit) usage analysis and forecasting
- Cost allocation across workspaces, teams, and projects
- Budget monitoring and alerting
- Identifying cost optimization opportunities
- Analyzing spend trends (day-over-day, week-over-week)
- SKU-level cost breakdown (Jobs, SQL, All-Purpose clusters)
- Serverless vs. classic compute cost comparison
- Tag-based cost attribution

Analyze the Genie Space data and provide:
1. Relevant cost metrics and trends
2. Comparison to budgets or expectations
3. Specific, actionable recommendations
4. Supporting data and calculations

Be precise with numbers and include time context.""",

    "security_analyst": """You are a Databricks Security Analyst specializing in platform security and compliance.

Query: {query}

Your expertise includes:
- Access control and permissions analysis
- Audit log review and anomaly detection
- Compliance monitoring (SOC2, HIPAA, GDPR)
- Secret and credential management
- Identity and authentication patterns
- Data access governance
- Security incident investigation
- Permission change tracking

Analyze the Genie Space data and provide:
1. Security findings and risk assessment
2. Compliance status if relevant
3. Specific security recommendations
4. Evidence from audit logs or access patterns

Prioritize findings by risk level.""",

    "performance_analyst": """You are a Databricks Performance Analyst specializing in query and cluster optimization.

Query: {query}

Your expertise includes:
- Query performance analysis and optimization
- Cluster utilization and sizing recommendations
- Cache hit rates and optimization
- Spark job performance tuning
- SQL warehouse performance metrics
- Photon acceleration analysis
- I/O and shuffle optimization
- Auto-scaling effectiveness

Analyze the Genie Space data and provide:
1. Performance metrics and bottlenecks
2. Comparison to baselines or SLAs
3. Specific optimization recommendations
4. Expected improvement estimates

Include quantitative metrics where possible.""",

    "reliability_analyst": """You are a Databricks Reliability Analyst specializing in job health and SLA management.

Query: {query}

Your expertise includes:
- Job failure analysis and root cause identification
- SLA monitoring and compliance tracking
- Pipeline health assessment
- Retry patterns and error categorization
- Job duration trends and anomalies
- Dependency chain analysis
- Incident correlation
- Mean time to recovery (MTTR) analysis

Analyze the Genie Space data and provide:
1. Reliability metrics and failure patterns
2. Root cause analysis for failures
3. SLA compliance status
4. Recommendations for improving reliability

Prioritize by business impact.""",

    "quality_analyst": """You are a Databricks Data Quality Analyst specializing in data governance and quality monitoring.

Query: {query}

Your expertise includes:
- Data freshness and staleness detection
- Schema drift monitoring
- Null rate and completeness analysis
- Data profiling and anomaly detection
- Lakehouse monitoring metrics
- Table health and maintenance
- Data lineage tracking
- Quality rule violations

Analyze the Genie Space data and provide:
1. Data quality metrics and issues
2. Freshness and completeness assessment
3. Schema or quality drift findings
4. Recommendations for data quality improvement

Include specific tables and metrics affected."""
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


def register_prompts_to_uc_registry(catalog: str, schema: str, prompts: dict):
    """
    Register prompts to MLflow Prompt Registry in Unity Catalog.
    
    This is the NEW MLflow 3.0 pattern that makes prompts appear in the 
    MLflow UI "Prompts" tab.
    
    REQUIRES: MLflow 3.0+ with mlflow.genai module. Job will FAIL if not available.
    
    Reference: https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/
    """
    # Check if mlflow.genai is available (requires MLflow 3.0+)
    try:
        import mlflow.genai
    except ImportError as e:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "❌ CRITICAL ERROR: MLflow 3.0+ Required\n"
            "=" * 70 + "\n"
            f"The mlflow.genai module is not available.\n\n"
            f"Import Error: {e}\n\n"
            "This agent requires MLflow 3.0+ for:\n"
            "  - MLflow Prompt Registry\n"
            "  - MLflow GenAI Scorers\n"
            "  - Production Monitoring\n\n"
            "Solutions:\n"
            "  1. Upgrade MLflow: pip install 'mlflow>=3.0.0'\n"
            "  2. Use a Databricks Runtime with MLflow 3.0+ pre-installed\n"
            "  3. Add mlflow>=3.0.0 to job environment dependencies\n"
            "=" * 70
        )
        print(error_msg)
        raise ImportError(error_msg) from e
    
    print(f"\nRegistering prompts to MLflow Prompt Registry (Unity Catalog)...")
    print(f"Target: {catalog}.{schema}.<prompt_name>")
    
    for name, template in prompts.items():
        prompt_name = f"{catalog}.{schema}.prompt_{name}"
        
        # Convert single-brace {var} to double-brace {{var}} for MLflow template format
        # BUT preserve existing double-braces (used in JSON examples)
        # Strategy: First protect existing {{...}}, then convert single braces, then restore
        import re
        
        # Step 1: Find and protect existing double-brace patterns like {{...}}
        # These are literal braces in Python that should remain as single braces in MLflow
        protected = template
        
        # Step 2: Only convert single braces that look like variable placeholders {word}
        # Pattern: single { followed by word characters, then single }
        # Don't match {{ or }}
        def convert_placeholder(match):
            return "{{" + match.group(1) + "}}"
        
        # Match {word} but not {{word}} - only convert single-brace placeholders
        converted_template = re.sub(r'(?<!\{)\{(\w+)\}(?!\})', convert_placeholder, protected)
        
        try:
            # Register the prompt - this creates the entry in Prompts UI
            prompt = mlflow.genai.register_prompt(
                name=prompt_name,
                template=converted_template,
                commit_message=f"Initial version of {name} prompt"
            )
            print(f"  ✓ Registered: {prompt_name} (version {prompt.version})")
            
            # Set production alias
            try:
                mlflow.genai.set_prompt_alias(
                    name=prompt_name,
                    alias="production",
                    version=prompt.version
                )
                print(f"    → Set alias 'production' -> version {prompt.version}")
            except Exception as alias_err:
                print(f"    ⚠ Alias error: {alias_err}")
                
        except Exception as e:
            # Check if it's a "prompt already exists" error
            if "already exists" in str(e).lower():
                print(f"  ↳ Prompt exists, creating new version: {prompt_name}")
                try:
                    prompt = mlflow.genai.register_prompt(
                        name=prompt_name,
                        template=converted_template,
                        commit_message=f"Updated {name} prompt"
                    )
                    print(f"  ✓ Updated: {prompt_name} (version {prompt.version})")
                    
                    mlflow.genai.set_prompt_alias(
                        name=prompt_name,
                        alias="production",
                        version=prompt.version
                    )
                    print(f"    → Updated alias 'production' -> version {prompt.version}")
                except Exception as update_err:
                    print(f"  ✗ Update failed: {update_err}")
            else:
                print(f"  ✗ Registration failed for {name}: {e}")


def log_prompts_to_mlflow(prompts: dict):
    """
    Print prompt summary (NO MLFLOW RUN).
    
    Prompt registration is configuration management, not experimentation.
    Prompts are registered to MLflow Prompt Registry directly.
    This function provides a summary without creating experiment runs.
    """
    print("\n" + "=" * 60)
    print("PROMPT REGISTRATION SUMMARY (No MLflow Run)")
    print("=" * 60)
    print("\nNote: Prompt registration is config management, not experimentation")
    print("Prompts are registered to MLflow Prompt Registry, not as experiment runs")
    
    # Print summary of registered prompts
    prompt_summary = {name: {"length": len(template), "variables": _extract_variables(template)} 
                     for name, template in prompts.items()}
    
    print(f"\n📝 Prompts Registered: {len(prompts)}")
    for name, info in prompt_summary.items():
        print(f"  • {name}: {info['length']} chars, variables: {info['variables']}")
    
    print(f"\n✨ No MLflow run created (config management, not experimentation)")
    print("   Prompts are in MLflow Prompt Registry: Models > Prompt Engineering")
    print("=" * 60)


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
        
        # 1. Register prompts to MLflow Prompt Registry (Unity Catalog)
        # This makes prompts appear in the MLflow UI "Prompts" tab
        register_prompts_to_uc_registry(catalog, agent_schema, PROMPTS)
        
        # 2. Store prompts in the config table (runtime retrieval)
        register_prompts_to_table(spark, catalog, agent_schema, PROMPTS)
        
        # 3. Log prompts to MLflow experiment as artifacts (backup)
        log_prompts_to_mlflow(PROMPTS)
        
        print("\n" + "=" * 60)
        print("✓ All prompts registered successfully!")
        print("=" * 60)
        print(f"\nPrompts registered to:")
        print(f"  1. MLflow Prompt Registry: {catalog}.{agent_schema}.prompt_*")
        print(f"  2. Config table: {catalog}.{agent_schema}.agent_config")
        print(f"  3. MLflow experiment: /Shared/health_monitor/agent (run_type=prompt_registry)")
        print(f"\nPrompts:")
        for name in PROMPTS:
            print(f"  - {catalog}.{agent_schema}.prompt_{name}")
        print(f"\nView prompts in MLflow UI: Experiment -> Prompts tab")
        
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error registering prompts: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


# COMMAND ----------

if __name__ == "__main__":
    main()
