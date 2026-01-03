"""
LLM Judges for Agent Evaluation
===============================

Custom scorers for evaluating agent response quality.

Usage:
    from agents.evaluation import domain_accuracy_judge

    results = mlflow.genai.evaluate(
        model=agent,
        data=eval_data,
        scorers=[domain_accuracy_judge]
    )
"""

import json
from typing import Dict, Optional

from mlflow.genai import scorer, Score
from langchain_databricks import ChatDatabricks

from ..config import settings


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

    llm = ChatDatabricks(
        endpoint=settings.llm_endpoint,
        temperature=0,
    )

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

    try:
        result = llm.invoke(prompt)
        parsed = json.loads(result.content)
        return Score(
            value=float(parsed["score"]),
            rationale=parsed.get("rationale", ""),
        )
    except Exception as e:
        return Score(value=0.5, rationale=f"Evaluation error: {str(e)}")


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

    llm = ChatDatabricks(
        endpoint=settings.llm_endpoint,
        temperature=0,
    )

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

    try:
        result = llm.invoke(prompt)
        parsed = json.loads(result.content)
        return Score(
            value=float(parsed["score"]),
            rationale=parsed.get("rationale", ""),
        )
    except Exception as e:
        return Score(value=0.5, rationale=f"Evaluation error: {str(e)}")


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

    llm = ChatDatabricks(
        endpoint=settings.llm_endpoint,
        temperature=0,
    )

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

    try:
        result = llm.invoke(prompt)
        parsed = json.loads(result.content)
        return Score(
            value=float(parsed["score"]),
            rationale=parsed.get("rationale", ""),
        )
    except Exception as e:
        return Score(value=0.5, rationale=f"Evaluation error: {str(e)}")


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
