"""
Evaluation Runner
=================

Pipeline for running agent evaluations.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import mlflow
import mlflow.genai
from mlflow.genai.scorers import Relevance, Safety

from .judges import (
    domain_accuracy_judge,
    response_relevance_judge,
    actionability_judge,
    source_citation_judge,
)


def create_evaluation_dataset() -> pd.DataFrame:
    """
    Create synthetic evaluation dataset.

    Returns:
        DataFrame with test queries and expected outcomes.
    """
    data = [
        # Cost domain
        {
            "query": "Why did costs spike yesterday?",
            "category": "cost",
            "expected_domains": ["COST"],
            "difficulty": "simple",
        },
        {
            "query": "What are the top 10 most expensive jobs this month?",
            "category": "cost",
            "expected_domains": ["COST"],
            "difficulty": "simple",
        },
        {
            "query": "Show DBU usage by workspace for last quarter",
            "category": "cost",
            "expected_domains": ["COST"],
            "difficulty": "moderate",
        },
        # Security domain
        {
            "query": "Who accessed sensitive data last week?",
            "category": "security",
            "expected_domains": ["SECURITY"],
            "difficulty": "simple",
        },
        {
            "query": "Show failed login attempts in the past 24 hours",
            "category": "security",
            "expected_domains": ["SECURITY"],
            "difficulty": "simple",
        },
        # Performance domain
        {
            "query": "What are the slowest queries today?",
            "category": "performance",
            "expected_domains": ["PERFORMANCE"],
            "difficulty": "simple",
        },
        {
            "query": "Show cluster utilization trends this week",
            "category": "performance",
            "expected_domains": ["PERFORMANCE"],
            "difficulty": "moderate",
        },
        # Reliability domain
        {
            "query": "Which jobs failed today?",
            "category": "reliability",
            "expected_domains": ["RELIABILITY"],
            "difficulty": "simple",
        },
        {
            "query": "What is our SLA compliance this week?",
            "category": "reliability",
            "expected_domains": ["RELIABILITY"],
            "difficulty": "simple",
        },
        # Quality domain
        {
            "query": "Which tables have data quality issues?",
            "category": "quality",
            "expected_domains": ["QUALITY"],
            "difficulty": "simple",
        },
        {
            "query": "Show data freshness by schema",
            "category": "quality",
            "expected_domains": ["QUALITY"],
            "difficulty": "moderate",
        },
        # Multi-domain queries
        {
            "query": "Are expensive jobs also the ones failing frequently?",
            "category": "multi_domain",
            "expected_domains": ["COST", "RELIABILITY"],
            "difficulty": "complex",
        },
        {
            "query": "Who accessed sensitive data and what did it cost?",
            "category": "multi_domain",
            "expected_domains": ["SECURITY", "COST"],
            "difficulty": "complex",
        },
        {
            "query": "Are slow queries causing job failures?",
            "category": "multi_domain",
            "expected_domains": ["PERFORMANCE", "RELIABILITY"],
            "difficulty": "complex",
        },
        {
            "query": "Show me a complete health check of the platform",
            "category": "multi_domain",
            "expected_domains": ["COST", "SECURITY", "PERFORMANCE", "RELIABILITY", "QUALITY"],
            "difficulty": "complex",
        },
    ]

    return pd.DataFrame(data)


def run_evaluation(
    agent: Any,
    data: Optional[pd.DataFrame] = None,
    custom_scorers: Optional[List] = None,
    run_name: str = "agent_evaluation",
) -> Dict:
    """
    Run evaluation pipeline on the agent.

    Args:
        agent: Agent to evaluate
        data: Optional evaluation DataFrame
        custom_scorers: Optional additional scorers
        run_name: MLflow run name

    Returns:
        Evaluation results dict.
    """
    # Use default dataset if none provided
    if data is None:
        data = create_evaluation_dataset()

    # Default scorers
    scorers = [
        Relevance(),
        Safety(),
        domain_accuracy_judge,
        response_relevance_judge,
        actionability_judge,
        source_citation_judge,
    ]

    # Add custom scorers
    if custom_scorers:
        scorers.extend(custom_scorers)

    # Run evaluation
    with mlflow.start_run(run_name=run_name):
        results = mlflow.genai.evaluate(
            model=agent,
            data=data,
            scorers=scorers,
        )

        # Log summary metrics
        mlflow.log_metrics({
            "eval_queries": len(data),
            "avg_relevance": results.metrics.get("relevance/mean", 0),
            "avg_domain_accuracy": results.metrics.get("domain_accuracy_judge/mean", 0),
            "avg_actionability": results.metrics.get("actionability_judge/mean", 0),
        })

        return {
            "metrics": results.metrics,
            "artifacts_uri": results.artifacts_uri,
            "run_id": mlflow.active_run().info.run_id,
        }


def evaluate_by_category(
    agent: Any,
    data: Optional[pd.DataFrame] = None,
) -> Dict[str, Dict]:
    """
    Run evaluation grouped by query category.

    Args:
        agent: Agent to evaluate
        data: Optional evaluation DataFrame

    Returns:
        Results grouped by category.
    """
    if data is None:
        data = create_evaluation_dataset()

    results_by_category = {}

    for category in data["category"].unique():
        category_data = data[data["category"] == category]

        results = run_evaluation(
            agent=agent,
            data=category_data,
            run_name=f"eval_{category}",
        )

        results_by_category[category] = results

    return results_by_category
