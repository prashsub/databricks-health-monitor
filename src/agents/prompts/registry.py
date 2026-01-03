"""
Prompt Registry
===============

Centralized prompt management with MLflow versioning.

Usage:
    from agents.prompts import register_all_prompts, load_prompt

    # Register prompts (run once during setup)
    register_all_prompts()

    # Load prompt by alias
    prompt = load_prompt("orchestrator", alias="production")
"""

from typing import Optional
import mlflow
import mlflow.genai

from ..config import settings


# =============================================================================
# System Prompts
# =============================================================================

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
- COST: Billing, spending, DBU usage, budgets, chargeback, pricing, cost allocation
- SECURITY: Access control, audit logs, permissions, threats, compliance, authentication
- PERFORMANCE: Query speed, cluster utilization, latency, warehouse performance, optimization
- RELIABILITY: Job failures, SLAs, incidents, pipeline health, job runs, task success
- QUALITY: Data quality, lineage, freshness, governance, schema changes, data validation

CLASSIFICATION RULES:
1. Select ALL relevant domains (can be multiple)
2. Order domains by relevance (most relevant first)
3. Provide confidence score (0.0-1.0)
4. If query spans multiple domains, include all applicable ones

RESPOND WITH JSON ONLY:
{{"domains": ["DOMAIN1", ...], "confidence": <float>}}"""

SYNTHESIZER_PROMPT = """You are a response synthesizer for a Databricks platform monitoring system.

Combine responses from domain-specific agents into a unified, coherent answer.

USER QUESTION:
{query}

DOMAIN AGENT RESPONSES:
{agent_responses}

USER CONTEXT:
{user_context}

GUIDELINES:
1. Start with a direct answer to the user's question
2. Integrate insights from all relevant domain responses
3. Highlight cross-domain correlations when found
4. Provide actionable recommendations based on the data
5. Use clear formatting with headers and bullet points
6. Cite data sources in [brackets]
7. If any domain returned an error, note it gracefully
8. Keep the response concise but comprehensive

FORMAT:
## Summary
[1-2 sentence direct answer]

## Details
[Detailed breakdown by domain]

## Recommendations
[Actionable next steps]

## Sources
[List of data sources used]"""

WORKER_AGENT_PROMPT = """You are a {domain} specialist agent for Databricks platform monitoring.

YOUR DOMAIN: {domain_description}

CAPABILITIES:
You have access to a Genie Space that can answer natural language questions about:
{capabilities}

GUIDELINES:
1. Understand the user's question in the context of {domain}
2. Query the Genie Space with a clear, specific question
3. Interpret the results and provide actionable insights
4. If the question is outside your domain, say so clearly
5. Always cite the data source

Return your response in this format:
- Answer: [Direct answer to the question]
- Key Metrics: [Relevant numbers and trends]
- Insight: [What this means for the user]
- Recommendation: [What action to take]
"""


# =============================================================================
# Registry Functions
# =============================================================================

def register_prompt(
    name: str,
    prompt: str,
    description: str = None,
) -> str:
    """
    Register a prompt to MLflow.

    Args:
        name: Prompt name (e.g., "orchestrator")
        prompt: Prompt template string
        description: Optional description

    Returns:
        Registered model name.
    """
    model_name = f"health_monitor_{name}_prompt"

    try:
        mlflow.genai.log_prompt(
            prompt=prompt,
            artifact_path=f"prompts/{name}",
            registered_model_name=model_name,
        )
        print(f"Registered prompt: {model_name}")
        return model_name
    except Exception as e:
        print(f"Failed to register prompt {name}: {e}")
        return None


def register_all_prompts() -> dict:
    """
    Register all prompts to MLflow.

    Returns:
        Dict of prompt names to registered model names.
    """
    prompts = {
        "orchestrator": {
            "prompt": ORCHESTRATOR_PROMPT,
            "description": "Main orchestrator system prompt",
        },
        "intent_classifier": {
            "prompt": INTENT_CLASSIFIER_PROMPT,
            "description": "Intent classification prompt",
        },
        "synthesizer": {
            "prompt": SYNTHESIZER_PROMPT,
            "description": "Response synthesis prompt",
        },
    }

    # Add domain-specific prompts
    for domain in ["cost", "security", "performance", "reliability", "quality"]:
        prompts[f"worker_{domain}"] = {
            "prompt": WORKER_AGENT_PROMPT.format(
                domain=domain.upper(),
                domain_description=get_domain_description(domain),
                capabilities=get_domain_capabilities(domain),
            ),
            "description": f"{domain.title()} worker agent prompt",
        }

    results = {}
    for name, config in prompts.items():
        model_name = register_prompt(
            name=name,
            prompt=config["prompt"],
            description=config.get("description"),
        )
        results[name] = model_name

    return results


def load_prompt(
    name: str,
    alias: str = "production",
    version: int = None,
) -> str:
    """
    Load a prompt from MLflow registry.

    Args:
        name: Prompt name (e.g., "orchestrator")
        alias: Model alias (e.g., "production")
        version: Specific version number (overrides alias)

    Returns:
        Prompt template string.
    """
    model_name = f"health_monitor_{name}_prompt"

    try:
        if version:
            uri = f"prompts:/{model_name}/{version}"
        else:
            uri = f"prompts:/{model_name}/{alias}"

        prompt = mlflow.genai.load_prompt(uri)
        return prompt
    except Exception as e:
        # Fall back to hardcoded prompts
        fallbacks = {
            "orchestrator": ORCHESTRATOR_PROMPT,
            "intent_classifier": INTENT_CLASSIFIER_PROMPT,
            "synthesizer": SYNTHESIZER_PROMPT,
        }
        return fallbacks.get(name, "")


def set_prompt_alias(
    name: str,
    alias: str,
    version: int,
) -> None:
    """
    Set an alias for a prompt version.

    Args:
        name: Prompt name
        alias: Alias to set (e.g., "production", "staging")
        version: Version number to alias
    """
    from mlflow import MlflowClient

    client = MlflowClient()
    model_name = f"health_monitor_{name}_prompt"

    client.set_registered_model_alias(
        name=model_name,
        alias=alias,
        version=str(version),
    )
    print(f"Set alias '{alias}' for {model_name} version {version}")


# =============================================================================
# Helper Functions
# =============================================================================

def get_domain_description(domain: str) -> str:
    """Get description for a domain."""
    descriptions = {
        "cost": "Billing, spending analysis, and cost optimization",
        "security": "Access control, audit logs, and compliance monitoring",
        "performance": "Query performance, cluster utilization, and optimization",
        "reliability": "Job health, SLA compliance, and incident tracking",
        "quality": "Data quality, lineage, and governance",
    }
    return descriptions.get(domain, domain)


def get_domain_capabilities(domain: str) -> str:
    """Get capabilities list for a domain."""
    capabilities = {
        "cost": """
- DBU usage by workspace, user, SKU
- Spending trends and anomalies
- Budget tracking and forecasts
- Cost allocation and chargeback
- Top expensive jobs and queries""",
        "security": """
- User access patterns and anomalies
- Audit log analysis
- Permission changes and grants
- Failed authentication attempts
- Sensitive data access tracking""",
        "performance": """
- Slow query identification
- Cluster CPU/memory utilization
- Warehouse efficiency metrics
- Query cache hit rates
- Resource sizing recommendations""",
        "reliability": """
- Job success/failure rates
- SLA compliance tracking
- Pipeline health monitoring
- Task execution analysis
- Failure pattern detection""",
        "quality": """
- Data freshness monitoring
- Schema change detection
- Data lineage tracking
- Null/invalid value rates
- Table optimization status""",
    }
    return capabilities.get(domain, "")
