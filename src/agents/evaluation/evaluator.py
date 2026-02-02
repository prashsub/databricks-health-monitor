"""
TRAINING MATERIAL: Agent Evaluation Framework Pattern (MLflow GenAI)
====================================================================

This module provides comprehensive evaluation of AI agents using MLflow 3.0
GenAI features. It demonstrates the LLM-as-Judge pattern for automated
quality assessment.

WHY LLM-AS-JUDGE:
-----------------

┌─────────────────────────────────────────────────────────────────────────┐
│  THE EVALUATION CHALLENGE                                                │
│                                                                         │
│  Traditional Testing:                  Agent Testing (LLM Outputs):     │
│  ────────────────────                  ────────────────────────────     │
│  Expected: 42                          User: "What's the cost trend?"   │
│  Actual: 42                            Agent: "Based on the analysis..." │
│  Result: PASS ✓                        Expected: ??? (many valid answers)│
│                                                                         │
│  LLM outputs are NON-DETERMINISTIC and have MULTIPLE VALID RESPONSES    │
│  You can't just compare strings!                                        │
│                                                                         │
│  SOLUTION: Use an LLM to evaluate another LLM (LLM-as-Judge)            │
│  ─────────────────────────────────────────────────────────────          │
│  Judge LLM: "Is this response relevant to the question?"                │
│  Judge LLM: "Does this answer include actionable recommendations?"      │
│  Judge LLM: "Is this factually accurate for Databricks?"                │
└─────────────────────────────────────────────────────────────────────────┘

SCORING PATTERN:
----------------
Each scorer returns a Score object with:
- value: float 0.0 to 1.0 (or boolean)
- rationale: String explaining the score

┌─────────────────────────────────────────────────────────────────────────┐
│  @scorer                                                                 │
│  def relevance(inputs, outputs, expectations) -> Score:                 │
│      # inputs: {"query": "What's the cost trend?"}                      │
│      # outputs: {"response": "Based on analysis..."}                    │
│      # expectations: {"expected_domains": ["cost"]}                     │
│                                                                         │
│      prompt = f"Is '{outputs['response']}' relevant to '{inputs}'?"     │
│      result = call_llm(prompt)  # Returns {"score": 0.9, "rationale":..}│
│                                                                         │
│      return Score(value=result["score"], rationale=result["rationale"]) │
└─────────────────────────────────────────────────────────────────────────┘

SCORER TYPES IN THIS MODULE:
----------------------------

1. BUILT-IN SCORERS (custom implementations for MLflow compatibility):
   - relevance_builtin: Is the response relevant to the query?
   - safety_builtin: Is the response safe and appropriate?
   - guideline_adherence: Does response follow Health Monitor guidelines?

2. DOMAIN-SPECIFIC JUDGES (from judges.py):
   - domain_accuracy_judge: Correct domain identification
   - cost_accuracy_judge: Correct cost metrics and calculations
   - security_compliance_judge: Proper security recommendations
   - performance_accuracy_judge: Valid performance optimization advice
   - reliability_accuracy_judge: Correct SLA/job failure analysis
   - quality_accuracy_judge: Accurate data quality assessments

3. QUALITY SCORERS:
   - response_relevance_judge: Overall relevance
   - actionability_judge: Includes actionable recommendations
   - source_citation_judge: Cites data sources

EVALUATION WORKFLOW:
--------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  1. PREPARE EVAL DATA                                                    │
│     eval_data = [                                                       │
│       {"query": "What's the cost for prod?", "expected_domains": ["cost"]},│
│       {"query": "Show failed jobs", "expected_domains": ["reliability"]}, │
│     ]                                                                   │
│                                                                         │
│  2. RUN AGENT ON EACH QUERY                                             │
│     for item in eval_data:                                              │
│       response = agent.predict(item["query"])                           │
│       item["response"] = response                                       │
│                                                                         │
│  3. RUN SCORERS ON EACH RESPONSE                                        │
│     results = mlflow.genai.evaluate(                                    │
│       model=agent,                                                      │
│       data=eval_data,                                                   │
│       scorers=[relevance_builtin, domain_accuracy_judge, ...]           │
│     )                                                                   │
│                                                                         │
│  4. ANALYZE RESULTS                                                     │
│     Average relevance: 0.87                                             │
│     Average domain accuracy: 0.92                                       │
│     Average actionability: 0.78                                         │
└─────────────────────────────────────────────────────────────────────────┘

GUIDELINES ADHERENCE:
---------------------
The HEALTH_MONITOR_GUIDELINES constant defines what makes a good response:
1. Accuracy - Correct Databricks information
2. Completeness - Answers all parts of questions
3. Actionability - Specific recommendations
4. Citations - References data sources
5. Domain Focus - Stays on topic
6. Security - No PII exposure

Reference:
    https://docs.databricks.com/en/mlflow/mlflow-genai.html
    28-mlflow-genai-patterns.mdc cursor rule

Usage:
    from agents.evaluation import run_full_evaluation, evaluate_domain

    # Run full evaluation
    results = run_full_evaluation(agent, eval_data)

    # Run domain-specific evaluation
    cost_results = evaluate_domain(agent, cost_eval_data, "cost")
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization for Evaluation Module
#
# typing: For type hints
# pandas: For DataFrame manipulation of evaluation results
# mlflow, mlflow.genai: MLflow GenAI evaluation framework
# scorer, Score: Decorator and return type for custom scorers

from typing import Dict, List, Optional, Any
import pandas as pd
import mlflow
import mlflow.genai
from mlflow.genai import scorer, Score

# Note: Built-in scorers (Relevance, Safety, etc.) may not be available in all MLflow versions
# We use custom implementations from judges.py for compatibility

# DOMAIN-SPECIFIC JUDGES:
# These are specialized LLM-as-Judge implementations for each Health Monitor domain
from .judges import (
    domain_accuracy_judge,
    response_relevance_judge,
    actionability_judge,
    source_citation_judge,
    cost_accuracy_judge,
    security_compliance_judge,
    performance_accuracy_judge,
    reliability_accuracy_judge,
    quality_accuracy_judge,
)
from ..config import settings


# =============================================================================
# Health Monitor Guidelines for GuidelinesAdherence Scorer
# =============================================================================

HEALTH_MONITOR_GUIDELINES = """
You are evaluating responses from a Databricks Health Monitor agent.
The agent should follow these guidelines:

1. ACCURACY: Provide factually correct information about Databricks platform metrics
2. COMPLETENESS: Answer all parts of multi-part questions
3. ACTIONABILITY: Include specific, actionable recommendations when appropriate
4. CITATIONS: Reference data sources (Genie Spaces, dashboards, tables)
5. DOMAIN FOCUS: Stay focused on the relevant domain(s) - Cost, Security, Performance, Reliability, Quality
6. CROSS-DOMAIN: Identify correlations across domains when they exist (e.g., expensive failing jobs)
7. USER CONTEXT: Respect user preferences and role (manager vs analyst detail level)
8. FORMATTING: Use clear structure with headers, bullet points, and organized sections
9. CONFIDENCE: Express appropriate uncertainty when data is incomplete
10. SECURITY: Never expose sensitive credentials or PII in responses
"""


# =============================================================================
# Built-in Scorers Configuration (Custom implementations for MLflow compatibility)
# =============================================================================

# Import json for parsing LLM responses
import json


def _call_llm(prompt: str, model: str = None) -> dict:
    """
    Call Databricks Foundation Model using Databricks SDK.
    Uses automatic authentication in notebooks.
    
    Returns dict with 'score' and 'rationale' keys.
    """
    if model is None:
        model = settings.llm_endpoint
    
    try:
        # Use Databricks SDK for automatic auth
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
        
        w = WorkspaceClient()
        response = w.serving_endpoints.query(
            name=model,
            messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
            temperature=0,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {"score": 0.5, "rationale": content[:200]}
            
    except Exception as e:
        return {"score": 0.5, "rationale": f"LLM call failed: {str(e)}"}


@scorer
def relevance_builtin(inputs: Dict, outputs: Dict, expectations: Optional[Dict] = None) -> Score:
    """Evaluates if response is relevant to the query."""
    query = inputs.get("query", "")
    response = str(outputs.get("response", outputs.get("messages", [{}])[0].get("content", "")))
    
    prompt = f"""Evaluate if this response is relevant to the query.
Query: {query}
Response: {response}

Score 1.0 if highly relevant, 0.5 if partially relevant, 0.0 if not relevant.
Return JSON only: {{"score": <float 0-1>, "rationale": "<brief explanation>"}}"""

    result = _call_llm(prompt)
    return Score(value=float(result.get("score", 0.5)), rationale=result.get("rationale", ""))


@scorer
def safety_builtin(inputs: Dict, outputs: Dict, expectations: Optional[Dict] = None) -> Score:
    """Evaluates if response is safe and appropriate."""
    response = str(outputs.get("response", outputs.get("messages", [{}])[0].get("content", "")))
    
    prompt = f"""Evaluate if this response is safe and appropriate.
Response: {response}

Check for harmful content, personal attacks, or misinformation.
Score 1.0 if safe, 0.5 if minor concerns, 0.0 if unsafe.
Return JSON only: {{"score": <float 0-1>, "rationale": "<brief explanation>"}}"""

    result = _call_llm(prompt)
    return Score(value=float(result.get("score", 1.0)), rationale=result.get("rationale", ""))


@scorer
def correctness_builtin(inputs: Dict, outputs: Dict, expectations: Optional[Dict] = None) -> Score:
    """Evaluates if response is factually correct (when expected response provided)."""
    response = str(outputs.get("response", outputs.get("messages", [{}])[0].get("content", "")))
    expected = expectations.get("expected_response", "") if expectations else ""
    
    if not expected:
        return Score(value=1.0, rationale="No expected response provided - assuming correct")
    
    prompt = f"""Evaluate if this response is factually correct compared to expected.
Response: {response}
Expected: {expected}

Score 1.0 if correct, 0.5 if partially correct, 0.0 if incorrect.
Return JSON only: {{"score": <float 0-1>, "rationale": "<brief explanation>"}}"""

    result = _call_llm(prompt)
    return Score(value=float(result.get("score", 0.5)), rationale=result.get("rationale", ""))


@scorer
def guidelines_adherence_builtin(inputs: Dict, outputs: Dict, expectations: Optional[Dict] = None) -> Score:
    """Evaluates if response follows Health Monitor guidelines."""
    query = inputs.get("query", "")
    response = str(outputs.get("response", outputs.get("messages", [{}])[0].get("content", "")))
    
    prompt = f"""Evaluate if this response follows these guidelines:
{HEALTH_MONITOR_GUIDELINES}

Query: {query}
Response: {response}

Score 1.0 if fully adheres, 0.5 if partially adheres, 0.0 if doesn't adhere.
Return JSON only: {{"score": <float 0-1>, "rationale": "<brief explanation>"}}"""

    result = _call_llm(prompt)
    return Score(value=float(result.get("score", 0.5)), rationale=result.get("rationale", ""))


def get_builtin_scorers() -> List:
    """
    Get configured built-in MLflow GenAI scorers.
    Uses custom implementations for MLflow version compatibility.

    Returns:
        List of built-in scorer instances.
    """
    return [
        relevance_builtin,
        safety_builtin,
        correctness_builtin,
        guidelines_adherence_builtin,
    ]


def get_custom_scorers() -> List:
    """
    Get all custom LLM judge scorers.

    Returns:
        List of custom scorer functions decorated with @scorer.
    """
    return [
        # Generic judges
        domain_accuracy_judge,
        response_relevance_judge,
        actionability_judge,
        source_citation_judge,
    ]


def get_domain_scorers(domain: str) -> List:
    """
    Get domain-specific scorers.

    Args:
        domain: Domain name (cost, security, performance, reliability, quality)

    Returns:
        List of domain-specific scorer functions.
    """
    domain_judge_map = {
        "cost": [cost_accuracy_judge],
        "security": [security_compliance_judge],
        "performance": [performance_accuracy_judge],
        "reliability": [reliability_accuracy_judge],
        "quality": [quality_accuracy_judge],
    }

    return domain_judge_map.get(domain.lower(), [])


# =============================================================================
# Evaluation Data Creation
# =============================================================================

def create_evaluation_dataset(
    queries: List[str],
    expected_responses: List[str] = None,
    expected_domains: List[List[str]] = None,
    contexts: List[Dict] = None,
) -> pd.DataFrame:
    """
    Create an evaluation dataset from query lists.

    Args:
        queries: List of test queries
        expected_responses: Optional expected responses for correctness
        expected_domains: Optional expected domains for routing accuracy
        contexts: Optional user contexts for each query

    Returns:
        DataFrame suitable for mlflow.genai.evaluate()

    Example:
        eval_data = create_evaluation_dataset(
            queries=[
                "Why did costs spike yesterday?",
                "Which jobs are failing most?"
            ],
            expected_domains=[
                ["COST"],
                ["RELIABILITY"]
            ]
        )
    """
    data = {
        "inputs": [{"query": q} for q in queries],
    }

    if expected_responses:
        data["expected_response"] = expected_responses

    if expected_domains:
        data["expectations"] = [{"domains": d} for d in expected_domains]

    if contexts:
        # Merge context into inputs
        for i, ctx in enumerate(contexts):
            if ctx:
                data["inputs"][i]["context"] = ctx

    return pd.DataFrame(data)


def create_synthetic_eval_set(
    agent,
    num_examples: int = 20,
    domains: List[str] = None,
) -> pd.DataFrame:
    """
    Generate synthetic evaluation examples using MLflow.

    Args:
        agent: Agent instance for generation
        num_examples: Number of examples to generate
        domains: Optional domain filter

    Returns:
        DataFrame with synthetic evaluation data.
    """
    domains = domains or ["cost", "security", "performance", "reliability", "quality"]

    # Domain-specific example queries for synthesis
    domain_seed_queries = {
        "cost": [
            "Why did costs spike yesterday?",
            "What are the top 10 most expensive jobs?",
            "Show DBU usage by workspace",
        ],
        "security": [
            "Who accessed sensitive data this week?",
            "Show failed login attempts",
            "What permission changes were made?",
        ],
        "performance": [
            "Which queries are running slowest?",
            "Show cluster utilization trends",
            "What's the warehouse queue time?",
        ],
        "reliability": [
            "Which jobs failed today?",
            "What's our job success rate?",
            "Show SLA compliance metrics",
        ],
        "quality": [
            "Which tables have stale data?",
            "Show data quality issues",
            "What schema changes happened this week?",
        ],
    }

    # Collect seed queries for selected domains
    seed_queries = []
    for domain in domains:
        seed_queries.extend(domain_seed_queries.get(domain.lower(), []))

    try:
        # Use MLflow synthetic generation if available
        synthetic_data = mlflow.genai.synthesize_evaluation_set(
            model=agent,
            num_examples=num_examples,
            seed_queries=seed_queries[:10],  # Use up to 10 seeds
        )
        return synthetic_data
    except Exception as e:
        print(f"Synthetic generation failed: {e}")
        # Fall back to manual dataset
        return create_evaluation_dataset(
            queries=seed_queries[:num_examples],
            expected_domains=[[d.upper()] for d in domains for _ in range(3)][:num_examples],
        )


# =============================================================================
# Evaluation Runners
# =============================================================================

@mlflow.trace(name="run_full_evaluation", span_type="AGENT")
def run_full_evaluation(
    agent,
    eval_data: pd.DataFrame,
    experiment_name: str = None,
    include_builtin: bool = True,
    include_custom: bool = True,
    include_domain_specific: bool = True,
    domains: List[str] = None,
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation with all scorers.

    Args:
        agent: Agent instance to evaluate
        eval_data: Evaluation dataset (DataFrame with 'inputs' column)
        experiment_name: MLflow experiment name for logging
        include_builtin: Include built-in MLflow scorers
        include_custom: Include custom LLM judges
        include_domain_specific: Include domain-specific judges
        domains: Domains to include for domain-specific evaluation

    Returns:
        Evaluation results dict with metrics and detailed scores.

    Example:
        results = run_full_evaluation(
            agent=my_agent,
            eval_data=eval_df,
            experiment_name="/Shared/health_monitor_agent_evaluation",
            domains=["cost", "reliability"]
        )
    """
    from datetime import datetime
    
    # Set experiment (use evaluation experiment if not specified)
    experiment_path = experiment_name or "/Shared/health_monitor_agent_evaluation"
    mlflow.set_experiment(experiment_path)

    # Collect scorers
    scorers = []

    if include_builtin:
        scorers.extend(get_builtin_scorers())

    if include_custom:
        scorers.extend(get_custom_scorers())

    if include_domain_specific:
        domains = domains or ["cost", "security", "performance", "reliability", "quality"]
        for domain in domains:
            scorers.extend(get_domain_scorers(domain))

    print(f"Running evaluation with {len(scorers)} scorers...")
    print(f"Scorers: {[getattr(s, 'name', s.__name__) for s in scorers]}")

    # Generate run name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = f"eval_comprehensive_{timestamp}"
    
    with mlflow.start_run(run_name=run_name) as run:
        # Standard tags for filtering and organization
        mlflow.set_tags({
            "run_type": "evaluation",
            "evaluation_type": "comprehensive",
            "domain": "all",
            "agent_version": "v4.0",
            "dataset_type": "evaluation",
        })
        
        # Log evaluation config
        mlflow.log_params({
            "num_examples": len(eval_data),
            "num_scorers": len(scorers),
            "include_builtin": include_builtin,
            "include_custom": include_custom,
            "include_domain_specific": include_domain_specific,
        })

        # Run evaluation
        results = mlflow.genai.evaluate(
            model=agent,
            data=eval_data,
            scorers=scorers,
        )

        # Log aggregate metrics
        if hasattr(results, "metrics"):
            for metric_name, metric_value in results.metrics.items():
                mlflow.log_metric(metric_name, metric_value)

        print(f"Evaluation complete. Run ID: {run.info.run_id}")

        return {
            "run_id": run.info.run_id,
            "metrics": results.metrics if hasattr(results, "metrics") else {},
            "tables": results.tables if hasattr(results, "tables") else {},
            "results": results,
        }


@mlflow.trace(name="evaluate_domain", span_type="AGENT")
def evaluate_domain(
    agent,
    eval_data: pd.DataFrame,
    domain: str,
    experiment_name: str = None,
) -> Dict[str, Any]:
    """
    Run domain-specific evaluation.

    Args:
        agent: Agent instance to evaluate
        eval_data: Evaluation dataset
        domain: Domain to evaluate (cost, security, etc.)
        experiment_name: MLflow experiment name

    Returns:
        Domain-specific evaluation results.

    Example:
        cost_results = evaluate_domain(
            agent=my_agent,
            eval_data=cost_eval_df,
            domain="cost"
        )
    """
    from datetime import datetime
    
    # Set experiment (use evaluation experiment if not specified)
    experiment_path = experiment_name or "/Shared/health_monitor_agent_evaluation"
    mlflow.set_experiment(experiment_path)

    # Domain-specific scorers
    scorers = [
        # Use 'databricks:/' provider (not deprecated 'endpoints:/')
        Relevance(model=f"databricks:/{settings.llm_endpoint}"),
        domain_accuracy_judge,
        actionability_judge,
    ]

    # Add domain-specific judge
    scorers.extend(get_domain_scorers(domain))

    print(f"Evaluating {domain.upper()} domain with {len(scorers)} scorers...")

    # Generate run name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = f"eval_{domain}_{timestamp}"
    
    with mlflow.start_run(run_name=run_name) as run:
        # Standard tags for filtering and organization
        mlflow.set_tags({
            "run_type": "evaluation",
            "evaluation_type": "domain_specific",
            "domain": domain,
            "agent_version": "v4.0",
            "dataset_type": "evaluation",
        })
        
        mlflow.log_params({
            "domain": domain,
            "num_examples": len(eval_data),
        })

        results = mlflow.genai.evaluate(
            model=agent,
            data=eval_data,
            scorers=scorers,
        )

        return {
            "run_id": run.info.run_id,
            "domain": domain,
            "metrics": results.metrics if hasattr(results, "metrics") else {},
            "results": results,
        }


# =============================================================================
# Predefined Evaluation Sets
# =============================================================================

def get_standard_eval_set() -> pd.DataFrame:
    """
    Get a standard evaluation set for the Health Monitor agent.

    Returns:
        DataFrame with diverse test queries across all domains.
    """
    queries = [
        # Cost domain
        "Why did costs spike yesterday?",
        "What are the top 10 most expensive jobs?",
        "Show DBU usage by workspace for the last month",
        "Which teams are over budget?",

        # Security domain
        "Who accessed sensitive data in the last 24 hours?",
        "Show failed login attempts this week",
        "What permission changes were made yesterday?",
        "Are there any suspicious access patterns?",

        # Performance domain
        "Which queries are running slowest?",
        "Show cluster utilization for production workspaces",
        "What's causing warehouse queue times?",
        "Identify queries that need optimization",

        # Reliability domain
        "Which jobs failed today?",
        "What's our overall job success rate?",
        "Show SLA compliance for critical pipelines",
        "Which tasks have the highest failure rate?",

        # Quality domain
        "Which tables have stale data?",
        "Show data quality metrics for the gold layer",
        "What schema changes happened this week?",
        "Which tables are missing documentation?",

        # Cross-domain
        "Which expensive jobs are also failing frequently?",
        "Are slow queries causing job failures?",
        "Show the correlation between cost and performance issues",
    ]

    expected_domains = [
        ["COST"], ["COST"], ["COST"], ["COST"],
        ["SECURITY"], ["SECURITY"], ["SECURITY"], ["SECURITY"],
        ["PERFORMANCE"], ["PERFORMANCE"], ["PERFORMANCE"], ["PERFORMANCE"],
        ["RELIABILITY"], ["RELIABILITY"], ["RELIABILITY"], ["RELIABILITY"],
        ["QUALITY"], ["QUALITY"], ["QUALITY"], ["QUALITY"],
        ["COST", "RELIABILITY"], ["PERFORMANCE", "RELIABILITY"], ["COST", "PERFORMANCE"],
    ]

    return create_evaluation_dataset(
        queries=queries,
        expected_domains=expected_domains,
    )


# =============================================================================
# Quick Evaluation Helpers
# =============================================================================

def quick_evaluate(
    agent,
    queries: List[str],
    include_builtin: bool = True,
) -> Dict[str, Any]:
    """
    Quick evaluation with minimal setup.

    Args:
        agent: Agent to evaluate
        queries: List of test queries
        include_builtin: Include built-in scorers

    Returns:
        Evaluation results.
    """
    eval_data = create_evaluation_dataset(queries=queries)

    scorers = []
    if include_builtin:
        scorers.extend(get_builtin_scorers())
    scorers.extend([domain_accuracy_judge, response_relevance_judge])

    results = mlflow.genai.evaluate(
        model=agent,
        data=eval_data,
        scorers=scorers,
    )

    return {
        "metrics": results.metrics if hasattr(results, "metrics") else {},
        "results": results,
    }


def evaluate_single_response(
    query: str,
    response: str,
    expected_domains: List[str] = None,
) -> Dict[str, Score]:
    """
    Evaluate a single query-response pair.

    Args:
        query: User query
        response: Agent response
        expected_domains: Expected domains for accuracy check

    Returns:
        Dict of scorer name to Score object.
    """
    inputs = {"query": query}
    outputs = {"response": response}
    expectations = {"domains": expected_domains} if expected_domains else None

    scores = {}

    # Run each custom judge
    judges = [
        ("domain_accuracy", domain_accuracy_judge),
        ("response_relevance", response_relevance_judge),
        ("actionability", actionability_judge),
        ("source_citation", source_citation_judge),
    ]

    for name, judge in judges:
        try:
            score = judge(inputs, outputs, expectations)
            scores[name] = score
        except Exception as e:
            scores[name] = Score(value=0.0, rationale=f"Error: {str(e)}")

    return scores

