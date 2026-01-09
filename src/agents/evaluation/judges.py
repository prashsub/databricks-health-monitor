"""
LLM Judges for Agent Evaluation
===============================

Custom scorers for evaluating agent response quality.
Includes both generic judges and domain-specific judges per the MLflow GenAI patterns.

Reference:
    28-mlflow-genai-patterns.mdc cursor rule
    docs/agent-framework-design/09-evaluation-and-judges.md

Usage:
    from agents.evaluation import (
        domain_accuracy_judge,
        cost_accuracy_judge,
        security_compliance_judge,
    )

    results = mlflow.genai.evaluate(
        model=agent,
        data=eval_data,
        scorers=[domain_accuracy_judge, cost_accuracy_judge]
    )
"""

import json
import re
from typing import Dict, Optional

from mlflow.genai import scorer, Score

from ..config import settings


# =============================================================================
# LLM Helper Function (using Databricks SDK)
# =============================================================================


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
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {"score": 0.5, "rationale": content[:200]}
            
    except Exception as e:
        return {"score": 0.5, "rationale": f"LLM call failed: {str(e)}"}


# =============================================================================
# Generic Judges
# =============================================================================


@scorer
def domain_accuracy_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge whether the response accurately addresses the domain query.

    Evaluates:
    - Correct domain identification
    - Relevant data points cited
    - Accurate interpretation of metrics

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")
    expected_domains = expectations.get("domains", []) if expectations else []

    prompt = f"""Evaluate the domain accuracy of this response.

QUERY: {query}
EXPECTED DOMAINS: {expected_domains or "Not specified"}
RESPONSE: {response}

Rate the response on domain accuracy (0.0-1.0):
- 1.0: Perfectly addresses the relevant domain(s)
- 0.7-0.9: Addresses correct domain with minor gaps
- 0.4-0.6: Partially correct domain focus
- 0.1-0.3: Wrong domain focus
- 0.0: Completely irrelevant

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def response_relevance_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge whether the response directly answers the query.

    Evaluates:
    - Direct answer provided
    - Relevant to the question asked
    - Not off-topic or generic

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate how directly this response answers the question.

QUERY: {query}
RESPONSE: {response}

Rate the relevance (0.0-1.0):
- 1.0: Directly answers the question with specific data
- 0.7-0.9: Answers the question but with some tangents
- 0.4-0.6: Partially relevant, missing key aspects
- 0.1-0.3: Mostly irrelevant to the question
- 0.0: Does not address the question at all

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def actionability_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge whether the response provides actionable recommendations.

    Evaluates:
    - Clear next steps provided
    - Specific recommendations
    - Practical implementation guidance

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate the actionability of this response.

QUERY: {query}
RESPONSE: {response}

Rate the actionability (0.0-1.0):
- 1.0: Clear, specific actions with implementation steps
- 0.7-0.9: Good recommendations but could be more specific
- 0.4-0.6: Generic recommendations without specifics
- 0.1-0.3: Vague or impractical suggestions
- 0.0: No actionable guidance provided

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def source_citation_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge whether the response properly cites data sources.

    Evaluates:
    - Sources mentioned
    - Traceability of claims
    - Proper attribution

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    response = outputs.get("response", "")
    sources = outputs.get("sources", [])

    # Check for source indicators
    has_brackets = "[" in response and "]" in response
    has_sources_section = "source" in response.lower()
    source_count = len(sources) if sources else 0

    score = 0.0
    rationale_parts = []

    if source_count > 0:
        score += 0.4
        rationale_parts.append(f"Listed {source_count} sources")

    if has_brackets:
        score += 0.3
        rationale_parts.append("Uses inline citations")

    if has_sources_section:
        score += 0.3
        rationale_parts.append("Has sources section")

    return Score(
        value=min(score, 1.0),
        rationale=". ".join(rationale_parts) if rationale_parts else "No sources cited",
    )


# =============================================================================
# Domain-Specific Judges
# =============================================================================

@scorer
def cost_accuracy_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge cost-related response accuracy.

    Evaluates:
    - Correct cost metrics (DBUs, dollars, percentages)
    - Accurate time period references
    - Valid workspace/SKU mentions
    - Appropriate cost thresholds and trends

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate the COST ACCURACY of this Databricks platform response.

QUERY: {query}
RESPONSE: {response}

Evaluate these cost-specific criteria:
1. Are DBU numbers plausible (not obviously wrong orders of magnitude)?
2. Are dollar amounts formatted correctly and reasonable?
3. Are time periods clearly specified?
4. Are workspace/SKU references accurate to Databricks terminology?
5. Are cost trends/changes described correctly (increase/decrease)?

Rate the cost accuracy (0.0-1.0):
- 1.0: All cost metrics are accurate and well-explained
- 0.7-0.9: Minor issues with specificity or formatting
- 0.4-0.6: Some cost data seems incorrect or unclear
- 0.1-0.3: Significant cost inaccuracies
- 0.0: Cost information is completely wrong or misleading

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def security_compliance_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge security-related response compliance.

    Evaluates:
    - Correct security terminology
    - Appropriate handling of sensitive information
    - Accurate audit log interpretation
    - Proper permission/access descriptions
    - Compliance framework awareness

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate the SECURITY COMPLIANCE of this Databricks platform response.

QUERY: {query}
RESPONSE: {response}

Evaluate these security-specific criteria:
1. Does it use correct security terminology (permissions, grants, audit events)?
2. Does it avoid exposing sensitive information (credentials, tokens, PII)?
3. Are audit log interpretations accurate?
4. Are permission descriptions correct (CAN_VIEW, CAN_MANAGE, etc.)?
5. Does it recommend appropriate security best practices?

Rate the security compliance (0.0-1.0):
- 1.0: Excellent security awareness and accurate information
- 0.7-0.9: Good security handling with minor gaps
- 0.4-0.6: Some security concerns or inaccuracies
- 0.1-0.3: Significant security issues in response
- 0.0: Response could enable security vulnerabilities

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def performance_accuracy_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge performance-related response accuracy.

    Evaluates:
    - Correct performance metrics (latency, throughput, utilization)
    - Accurate query analysis
    - Valid cluster/warehouse metrics
    - Appropriate optimization recommendations

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate the PERFORMANCE ACCURACY of this Databricks platform response.

QUERY: {query}
RESPONSE: {response}

Evaluate these performance-specific criteria:
1. Are latency/duration metrics in reasonable units and ranges?
2. Are utilization percentages valid (0-100%)?
3. Are cluster/warehouse metrics correctly identified?
4. Are performance bottlenecks accurately diagnosed?
5. Are optimization suggestions technically sound?

Rate the performance accuracy (0.0-1.0):
- 1.0: Excellent performance analysis with accurate metrics
- 0.7-0.9: Good analysis with minor metric issues
- 0.4-0.6: Some performance data seems incorrect
- 0.1-0.3: Significant performance analysis errors
- 0.0: Performance information is misleading

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def reliability_accuracy_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge reliability-related response accuracy.

    Evaluates:
    - Correct job/task status terminology
    - Accurate success/failure rate calculations
    - Valid SLA compliance metrics
    - Appropriate failure pattern identification
    - Correct incident/alert interpretation

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate the RELIABILITY ACCURACY of this Databricks platform response.

QUERY: {query}
RESPONSE: {response}

Evaluate these reliability-specific criteria:
1. Are job statuses correctly described (SUCCEEDED, FAILED, RUNNING, etc.)?
2. Are success/failure rates calculated correctly (percentages make sense)?
3. Are SLA metrics interpreted accurately?
4. Are failure patterns correctly identified?
5. Are root cause suggestions reasonable?

Rate the reliability accuracy (0.0-1.0):
- 1.0: Excellent reliability analysis with accurate metrics
- 0.7-0.9: Good analysis with minor issues
- 0.4-0.6: Some reliability data seems incorrect
- 0.1-0.3: Significant reliability analysis errors
- 0.0: Reliability information is misleading

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )


@scorer
def quality_accuracy_judge(
    inputs: Dict,
    outputs: Dict,
    expectations: Optional[Dict] = None,
) -> Score:
    """
    Judge data quality-related response accuracy.

    Evaluates:
    - Correct data quality metrics (freshness, completeness, validity)
    - Accurate lineage descriptions
    - Valid schema change identification
    - Appropriate data governance recommendations

    Args:
        inputs: Query inputs
        outputs: Agent outputs
        expectations: Optional expected outputs

    Returns:
        Score with value (0-1) and rationale.
    """
    query = inputs.get("query", "")
    response = outputs.get("response", "")

    prompt = f"""Evaluate the DATA QUALITY ACCURACY of this Databricks platform response.

QUERY: {query}
RESPONSE: {response}

Evaluate these data quality-specific criteria:
1. Are freshness metrics correctly described (last updated times)?
2. Are completeness metrics accurate (null rates, missing data)?
3. Are schema changes correctly identified?
4. Is data lineage accurately described?
5. Are data governance recommendations appropriate?

Rate the data quality accuracy (0.0-1.0):
- 1.0: Excellent data quality analysis with accurate metrics
- 0.7-0.9: Good analysis with minor issues
- 0.4-0.6: Some quality data seems incorrect
- 0.1-0.3: Significant data quality analysis errors
- 0.0: Data quality information is misleading

Return JSON: {{"score": <float>, "rationale": "<1-2 sentence explanation>"}}"""

    result = _call_llm(prompt)
    return Score(
        value=float(result.get("score", 0.5)),
        rationale=result.get("rationale", ""),
    )
