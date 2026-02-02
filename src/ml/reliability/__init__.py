"""
TRAINING MATERIAL: Reliability Domain ML Models Package
=======================================================

This package contains 5 ML models for the Reliability Agent domain,
focused on job execution, SLA compliance, and system health.

RELIABILITY DOMAIN MODEL INVENTORY:
-----------------------------------

┌────────────────────────────────────────────────────────────────────────────┐
│  MODEL                    │  TYPE          │  USE CASE                      │
├───────────────────────────┼────────────────┼────────────────────────────────┤
│  job_failure_predictor    │  Classification│  Pre-run failure probability   │
│  job_duration_forecaster  │  Regression    │  Expected runtime estimation   │
│  sla_breach_predictor     │  Classification│  SLA violation risk            │
│  retry_success_predictor  │  Classification│  Retry likely to succeed?      │
│  pipeline_health_scorer   │  Regression    │  Overall pipeline health score │
└───────────────────────────┴────────────────┴────────────────────────────────┘

USE CASE FLOW:
--------------

    Job Scheduled
         │
         ▼
    ┌─────────────────────────┐
    │ job_failure_predictor   │──▶ P(failure) > 0.7? → Pre-emptive alert
    └─────────────────────────┘
         │
         ▼
    ┌─────────────────────────┐
    │ job_duration_forecaster │──▶ Expected runtime for capacity planning
    └─────────────────────────┘
         │
         ▼
    ┌─────────────────────────┐
    │ sla_breach_predictor    │──▶ Will it miss SLA? → Prioritize resources
    └─────────────────────────┘
         │
         ▼ (if fails)
    ┌─────────────────────────┐
    │ retry_success_predictor │──▶ Retry? Or escalate immediately?
    └─────────────────────────┘

FEATURE TABLE: reliability_features
-----------------------------------

Primary Keys: workspace_id, job_id, run_date
Key Features:
- failure_rate: Historical failure rate
- avg_duration_seconds: Average runtime
- p95_duration_seconds: 95th percentile runtime
- retry_success_rate: Historical retry success
- sla_target_seconds: SLA threshold

ALGORITHM SELECTION:
--------------------

Classification (XGBoost) for:
- Binary outcomes: fail/succeed, breach/meet SLA
- High interpretability via feature importance
- Handles imbalanced classes (failures are rare)

Regression (Gradient Boosting) for:
- Continuous outcomes: duration, health score
- Non-linear relationships with runtime factors
- Confidence intervals for SLA planning

5 Models: Failure Predictor, Duration Forecaster, SLA Breach Predictor, Retry Success Predictor, Pipeline Health Scorer
"""






