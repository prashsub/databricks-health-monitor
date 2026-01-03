# Databricks notebook source
# MAGIC %md
# MAGIC # Register Agent Prompts
# MAGIC
# MAGIC Registers all Health Monitor agent prompts to MLflow Prompt Registry.

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0.0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "health_monitor")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

import mlflow
import mlflow.genai

# Set experiment
experiment_name = "/Shared/health_monitor/prompt_registry"
mlflow.set_experiment(experiment_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Prompts

# COMMAND ----------

ORCHESTRATOR_PROMPT = """You are the Health Monitor Orchestrator, a multi-agent system for Databricks platform observability.

YOUR ROLE:
You coordinate domain-specialist agents to answer questions about the Databricks platform.
You NEVER query data directly - all data access flows through Genie Spaces.

AVAILABLE AGENTS:
1. COST Agent - Billing, spending, DBU usage, budgets, cost allocation
2. SECURITY Agent - Access control, audit logs, permissions, compliance
3. PERFORMANCE Agent - Query speed, cluster utilization, latency, optimization
4. RELIABILITY Agent - Job failures, SLAs, pipeline health, incidents
5. QUALITY Agent - Data quality, lineage, freshness, governance

WORKFLOW:
1. Classify the user's intent to determine which agent(s) to invoke
2. Route the query to appropriate domain agent(s)
3. If multiple domains are relevant, coordinate parallel queries
4. Synthesize responses into a unified, actionable answer
5. Cite sources and provide confidence levels

USER CONTEXT:
{user_context}

GUIDELINES:
- Start with a direct answer to the question
- Provide specific numbers and metrics when available
- Highlight cross-domain correlations (e.g., expensive failing jobs)
- Include actionable recommendations
- Link to relevant dashboards for exploration
- Acknowledge uncertainty when data is incomplete
"""

INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for Databricks platform monitoring.

Analyze the user query and classify it into ONE OR MORE relevant domains.

AVAILABLE DOMAINS:
- COST: Billing, spending, DBU usage, budgets, chargeback, pricing
- SECURITY: Access control, audit logs, permissions, threats, compliance
- PERFORMANCE: Query speed, cluster utilization, latency, optimization
- RELIABILITY: Job failures, SLAs, incidents, pipeline health
- QUALITY: Data quality, lineage, freshness, governance

RESPOND WITH JSON ONLY:
{{"domains": ["DOMAIN1", ...], "confidence": <float>}}"""

SYNTHESIZER_PROMPT = """Combine responses from domain-specific agents into a unified answer.

USER QUESTION:
{query}

DOMAIN RESPONSES:
{agent_responses}

FORMAT:
## Summary
[1-2 sentence direct answer]

## Details
[Breakdown by domain]

## Recommendations
[Actionable next steps]

## Sources
[Data sources used]"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Prompts

# COMMAND ----------

prompts = {
    "orchestrator": ORCHESTRATOR_PROMPT,
    "intent_classifier": INTENT_CLASSIFIER_PROMPT,
    "synthesizer": SYNTHESIZER_PROMPT,
}

registered = {}

for name, prompt in prompts.items():
    model_name = f"health_monitor_{name}_prompt"

    try:
        mlflow.genai.log_prompt(
            prompt=prompt,
            artifact_path=f"prompts/{name}",
            registered_model_name=model_name,
        )
        registered[name] = model_name
        print(f"Registered: {model_name}")
    except Exception as e:
        print(f"Failed to register {name}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set Production Aliases

# COMMAND ----------

from mlflow import MlflowClient

client = MlflowClient()

for name, model_name in registered.items():
    try:
        # Get latest version
        versions = client.search_model_versions(f"name='{model_name}'")
        if versions:
            latest_version = max(versions, key=lambda v: int(v.version)).version

            # Set production alias
            client.set_registered_model_alias(
                name=model_name,
                alias="production",
                version=latest_version,
            )
            print(f"Set production alias for {model_name} -> v{latest_version}")
    except Exception as e:
        print(f"Failed to set alias for {name}: {e}")

# COMMAND ----------

print("Prompt registration complete")
dbutils.notebook.exit("SUCCESS")
