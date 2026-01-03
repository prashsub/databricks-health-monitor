"""
Evaluation Module
=================

Comprehensive evaluation framework for agent quality assessment.
Includes LLM judges, built-in scorers, evaluation runners, and production monitoring.

Reference:
    28-mlflow-genai-patterns.mdc cursor rule
    docs/agent-framework-design/09-evaluation-and-judges.md

Usage:
    # Custom LLM Judges
    from agents.evaluation import domain_accuracy_judge, cost_accuracy_judge

    # Built-in scorers and evaluation
    from agents.evaluation import (
        run_full_evaluation,
        evaluate_domain,
        get_builtin_scorers,
    )

    # Production monitoring
    from agents.evaluation import (
        ProductionMonitor,
        monitor_response_quality,
        assess_and_alert,
    )
"""

# Generic LLM Judges
from .judges import (
    domain_accuracy_judge,
    response_relevance_judge,
    actionability_judge,
    source_citation_judge,
)

# Domain-Specific LLM Judges
from .judges import (
    cost_accuracy_judge,
    security_compliance_judge,
    performance_accuracy_judge,
    reliability_accuracy_judge,
    quality_accuracy_judge,
)

# Evaluation Framework
from .evaluator import (
    run_full_evaluation,
    evaluate_domain,
    quick_evaluate,
    evaluate_single_response,
    get_builtin_scorers,
    get_custom_scorers,
    get_domain_scorers,
    create_evaluation_dataset,
    create_synthetic_eval_set,
    get_standard_eval_set,
    HEALTH_MONITOR_GUIDELINES,
)

# Production Monitoring
from .production_monitor import (
    ProductionMonitor,
    AssessmentResult,
    get_production_monitor,
    monitor_response_quality,
    assess_and_alert,
)

__all__ = [
    # Generic Judges
    "domain_accuracy_judge",
    "response_relevance_judge",
    "actionability_judge",
    "source_citation_judge",
    # Domain-Specific Judges
    "cost_accuracy_judge",
    "security_compliance_judge",
    "performance_accuracy_judge",
    "reliability_accuracy_judge",
    "quality_accuracy_judge",
    # Evaluation Framework
    "run_full_evaluation",
    "evaluate_domain",
    "quick_evaluate",
    "evaluate_single_response",
    "get_builtin_scorers",
    "get_custom_scorers",
    "get_domain_scorers",
    "create_evaluation_dataset",
    "create_synthetic_eval_set",
    "get_standard_eval_set",
    "HEALTH_MONITOR_GUIDELINES",
    # Production Monitoring
    "ProductionMonitor",
    "AssessmentResult",
    "get_production_monitor",
    "monitor_response_quality",
    "assess_and_alert",
]
