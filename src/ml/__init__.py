# Databricks Health Monitor - ML Models Package
# ==============================================
# Implements 23 ML models for predictive analytics using MLflow 3.0 best practices
#
# Agent Domains:
#   - Cost Agent (5 models): Anomaly detection, forecasting, optimization
#   - Security Agent (4 models): Threat detection, exfiltration, privilege escalation
#   - Performance Agent (6 models): Query forecasting, warehouse optimization
#   - Reliability Agent (5 models): Failure prediction, SLA breach
#   - Quality Agent (3 models): Freshness prediction, schema drift
#
# MLflow 3.0 Features Used:
#   - LoggedModel with name parameter (not artifact_path)
#   - Unity Catalog Model Registry (databricks-uc)
#   - Feature Engineering in Unity Catalog
#   - Inference tables for model monitoring
#   - mlflow.models.evaluate for traditional ML
#   - Model signatures required for UC registration

__version__ = "1.0.0"

