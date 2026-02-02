"""
TRAINING MATERIAL: Agent Evaluation Module Architecture
========================================================

This module provides a comprehensive evaluation framework for agent quality
assessment using the LLM-as-Judge pattern from MLflow GenAI.

EVALUATION ARCHITECTURE:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    EVALUATION FRAMEWORK COMPONENTS                       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  JUDGES (judges.py)                                              │   │
│  │  ─────────────────────────────────────────────────────────────   │   │
│  │  Generic:                                                        │   │
│  │  • domain_accuracy_judge    - Correct domain identification      │   │
│  │  • response_relevance_judge - Answers the question asked         │   │
│  │  • actionability_judge      - Includes recommendations           │   │
│  │  • source_citation_judge    - References data sources            │   │
│  │                                                                  │   │
│  │  Domain-Specific:                                                │   │
│  │  • cost_accuracy_judge      - Cost calculations correct          │   │
│  │  • security_compliance_judge- Security advice appropriate        │   │
│  │  • performance_accuracy_judge- Performance advice valid          │   │
│  │  • reliability_accuracy_judge- SLA analysis accurate             │   │
│  │  • quality_accuracy_judge   - Data quality assessment correct    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  EVALUATOR (evaluator.py)                                        │   │
│  │  ─────────────────────────────────────────────────────────────   │   │
│  │  • run_full_evaluation()  - Run all scorers on eval data         │   │
│  │  • evaluate_domain()      - Run domain-specific evaluation       │   │
│  │  • quick_evaluate()       - Fast smoke test                      │   │
│  │  • create_evaluation_dataset() - Build eval data from questions  │   │
│  │  • get_standard_eval_set()- Pre-defined test questions           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PRODUCTION MONITOR (production_monitor.py)                      │   │
│  │  ─────────────────────────────────────────────────────────────   │   │
│  │  • ProductionMonitor      - Real-time quality monitoring         │   │
│  │  • monitor_response_quality() - Check single response            │   │
│  │  • assess_and_alert()     - Check and trigger alerts             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

EVALUATION WORKFLOW:
--------------------

1. DEVELOPMENT (Before Deployment):
   eval_results = run_full_evaluation(agent, test_data)
   → Run comprehensive evaluation on standard test set
   → Check all judges pass threshold (e.g., 0.8)
   → Fix issues before deployment

2. PRE-DEPLOYMENT (Gate):
   quick_results = quick_evaluate(agent, smoke_test_data)
   → Fast sanity check
   → Block deployment if quality drops

3. PRODUCTION (Runtime):
   ProductionMonitor.assess_and_alert(response)
   → Sample production responses
   → Alert if quality degrades
   → Log metrics to MLflow

SCORING THRESHOLDS:
-------------------
Typical thresholds for production-ready agents:
- domain_accuracy:  >= 0.85
- relevance:        >= 0.80
- actionability:    >= 0.75
- source_citation:  >= 0.70

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
