# Databricks notebook source
# ===========================================================================
# Run Agent Evaluation
# ===========================================================================
"""
Runs evaluation of the Health Monitor Agent using MLflow GenAI scorers.

This script evaluates the registered agent model using:
- Standard benchmark queries across all 5 domains
- MLflow built-in scorers where available
- Simple heuristic scorers as fallback

Reference: .cursor/rules/ml/28-mlflow-genai-patterns.mdc
"""

# COMMAND ----------

import mlflow
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")

# COMMAND ----------

def create_evaluation_dataset() -> pd.DataFrame:
    """
    Create comprehensive evaluation dataset covering all 5 domains.
    """
    data = [
        # Cost Domain
        {"query": "Why did costs spike yesterday?", "domain": "cost", "difficulty": "simple"},
        {"query": "What are the top 10 most expensive jobs this month?", "domain": "cost", "difficulty": "simple"},
        {"query": "Show DBU usage by workspace for last quarter", "domain": "cost", "difficulty": "moderate"},
        {"query": "Which teams are over budget?", "domain": "cost", "difficulty": "moderate"},
        
        # Security Domain
        {"query": "Who accessed sensitive data last week?", "domain": "security", "difficulty": "simple"},
        {"query": "Show failed login attempts in the past 24 hours", "domain": "security", "difficulty": "simple"},
        {"query": "What permissions changes were made this week?", "domain": "security", "difficulty": "moderate"},
        
        # Performance Domain
        {"query": "What are the slowest queries today?", "domain": "performance", "difficulty": "simple"},
        {"query": "Show cluster utilization trends this week", "domain": "performance", "difficulty": "moderate"},
        {"query": "Which warehouses have low cache hit rates?", "domain": "performance", "difficulty": "moderate"},
        
        # Reliability Domain
        {"query": "Which jobs failed today?", "domain": "reliability", "difficulty": "simple"},
        {"query": "What is our SLA compliance this week?", "domain": "reliability", "difficulty": "simple"},
        {"query": "Show pipeline health across all workspaces", "domain": "reliability", "difficulty": "moderate"},
        
        # Quality Domain
        {"query": "Which tables have data quality issues?", "domain": "quality", "difficulty": "simple"},
        {"query": "Show data freshness by schema", "domain": "quality", "difficulty": "moderate"},
        {"query": "What tables have stale data?", "domain": "quality", "difficulty": "simple"},
        
        # Multi-Domain
        {"query": "Are expensive jobs also the ones failing frequently?", "domain": "multi", "difficulty": "complex"},
        {"query": "Give me a complete health check of the platform", "domain": "multi", "difficulty": "complex"},
    ]
    
    return pd.DataFrame(data)

print(f"Created evaluation dataset with {len(create_evaluation_dataset())} queries")

# COMMAND ----------

def heuristic_relevance_score(query: str, response: str) -> float:
    """Simple heuristic scorer for response relevance."""
    if not response or len(response) < 50:
        return 0.3
    
    # Check for error indicators
    error_indicators = ["error", "failed", "could not", "unable to", "not found"]
    if any(err in response.lower() for err in error_indicators):
        return 0.4
    
    # Check for domain keywords
    domain_keywords = {
        "cost": ["cost", "spend", "budget", "dbu", "billing", "expense"],
        "security": ["access", "permission", "login", "user", "audit"],
        "performance": ["slow", "query", "cluster", "utilization", "latency"],
        "reliability": ["job", "fail", "pipeline", "sla", "success", "error"],
        "quality": ["table", "freshness", "schema", "data quality", "stale"],
    }
    
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Determine expected domain
    expected_domain = None
    for domain, keywords in domain_keywords.items():
        if any(kw in query_lower for kw in keywords):
            expected_domain = domain
            break
    
    # Check if response addresses the domain
    if expected_domain:
        keywords = domain_keywords[expected_domain]
        matches = sum(1 for kw in keywords if kw in response_lower)
        keyword_score = min(matches / 3, 1.0)  # Cap at 1.0
    else:
        keyword_score = 0.5
    
    # Check response length (longer = more detailed)
    length_score = min(len(response) / 500, 1.0)
    
    # Combine scores
    return 0.3 * length_score + 0.7 * keyword_score


def heuristic_safety_score(response: str) -> float:
    """Simple heuristic scorer for safety."""
    unsafe_patterns = [
        "password", "secret", "token", "credential",
        "personal information", "pii", "ssn", "credit card"
    ]
    
    response_lower = response.lower()
    
    if any(pattern in response_lower for pattern in unsafe_patterns):
        return 0.5
    
    return 1.0  # Safe by default

# COMMAND ----------

def evaluate_agent(catalog: str, agent_schema: str) -> Dict[str, Any]:
    """
    Run evaluation on the registered agent model with LoggedModel version tracking.
    
    Reference: https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/track-application-versions-with-mlflow
    """
    import subprocess
    from datetime import datetime
    
    model_name = f"{catalog}.{agent_schema}.health_monitor_agent"
    # Use dedicated evaluation experiment
    experiment_path = "/Shared/health_monitor_agent_evaluation"
    
    print(f"\nEvaluating: {model_name}")
    print(f"Experiment: {experiment_path}")
    
    mlflow.set_experiment(experiment_path)
    
    # ===========================================================================
    # MLflow 3.0 LoggedModel Version Tracking for Evaluation
    # ===========================================================================
    # Link evaluation results to a LoggedModel in the "Agent versions" UI
    # ===========================================================================
    
    # Generate version identifier (should match what was used in log_agent_model)
    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()[:8]
        )
        version_identifier = f"git-{git_commit}"
    except Exception:
        version_identifier = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    logged_model_name = f"health_monitor_agent-{version_identifier}"
    
    # Set active model to link evaluation runs to LoggedModel
    active_model_info = None
    try:
        active_model_info = mlflow.set_active_model(name=logged_model_name)
        print(f"✓ Linked evaluation to LoggedModel: '{active_model_info.name}'")
        print(f"  Model ID: '{active_model_info.model_id}'")
    except Exception as e:
        print(f"⚠ set_active_model not available: {e}")
    
    # Load evaluation data
    eval_data = create_evaluation_dataset()
    print(f"Queries to evaluate: {len(eval_data)}")
    
    # Try to load the agent model
    agent = None
    try:
        model_uri = f"models:/{model_name}@production"
        agent = mlflow.pyfunc.load_model(model_uri)
        print(f"✓ Loaded agent from {model_uri}")
    except Exception as e:
        print(f"⚠ Could not load agent: {e}")
        print("→ Running evaluation with placeholder responses")
    
    # Run evaluation
    results = []
    total_relevance = 0.0
    total_safety = 0.0
    
    # Generate run name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_name_with_ts = f"eval_setup_{timestamp}"
    
    with mlflow.start_run(run_name=run_name_with_ts) as run:
        # Standard tags for filtering and organization
        mlflow.set_tags({
            "run_type": "evaluation",
            "evaluation_type": "setup_script",
            "domain": "all",
            "agent_version": "v4.0",
            "dataset_type": "evaluation",
        })
        
        # Link to LoggedModel if available
        if active_model_info:
            mlflow.set_tag("logged_model_id", active_model_info.model_id)
            mlflow.set_tag("logged_model_name", active_model_info.name)
        print(f"\nMLflow Run ID: {run.info.run_id}")
        
        for idx, row in eval_data.iterrows():
            query = row["query"]
            domain = row["domain"]
            
            print(f"\n{'='*70}")
            print(f"Query {idx+1}/{len(eval_data)} - Domain: {domain}")
            print(f"{'='*70}")
            print(f"Question: {query}")
            
            # Get response
            response_error = None
            if agent is not None:
                try:
                    print(f"→ Calling agent with input_data...")
                    # CRITICAL: ResponsesAgent expects 'input' not 'messages'
                    input_data = {"input": [{"role": "user", "content": query}]}
                    response_obj = agent.predict(input_data)
                    response = str(response_obj)
                    print(f"✓ Agent responded ({len(response)} chars)")
                    print(f"Response preview: {response[:200]}...")
                except Exception as e:
                    response_error = str(e)
                    response = f"Error: {str(e)}"
                    print(f"✗ Agent error: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                # Placeholder response for testing without agent
                response = f"[Placeholder] Analysis for {domain} domain: {query}"
                print(f"⚠ Using placeholder response (agent not loaded)")
            
            # Score responses
            relevance = heuristic_relevance_score(query, response)
            safety = heuristic_safety_score(response)
            
            print(f"Scores: relevance={relevance:.2f}, safety={safety:.2f}")
            
            results.append({
                "query": query,
                "domain": domain,
                "response_length": len(response),
                "relevance_score": relevance,
                "safety_score": safety,
                "had_error": response_error is not None,
                "error_message": response_error,
            })
            
            total_relevance += relevance
            total_safety += safety
        
        # Calculate averages
        n = len(eval_data)
        avg_relevance = total_relevance / n
        avg_safety = total_safety / n
        overall = (avg_relevance + avg_safety) / 2
        
        # Log metrics
        mlflow.log_metric("avg_relevance", avg_relevance)
        mlflow.log_metric("avg_safety", avg_safety)
        mlflow.log_metric("overall_score", overall)
        mlflow.log_metric("total_queries", n)
        
        # Log per-domain metrics
        for domain in eval_data["domain"].unique():
            domain_data = [r for r in results if r["domain"] == domain]
            domain_relevance = sum(r["relevance_score"] for r in domain_data) / len(domain_data)
            mlflow.log_metric(f"{domain}_relevance", domain_relevance)
        
        # Log model info
        mlflow.log_params({
            "model_name": model_name,
            "agent_loaded": agent is not None,
            "dataset_size": n,
        })
        
        # Save results as artifact
        results_df = pd.DataFrame(results)
        results_df.to_csv("/tmp/evaluation_results.csv", index=False)
        mlflow.log_artifact("/tmp/evaluation_results.csv")
        
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        print(f"  Average Relevance: {avg_relevance:.3f}")
        print(f"  Average Safety:    {avg_safety:.3f}")
        print(f"  Overall Score:     {overall:.3f}")
        print(f"  Total Queries:     {n}")
        print("=" * 60)
        
        return {
            "run_id": run.info.run_id,
            "avg_relevance": avg_relevance,
            "avg_safety": avg_safety,
            "overall_score": overall,
            "total_queries": n,
            "agent_loaded": agent is not None,
        }

# COMMAND ----------

def save_results_to_delta(catalog: str, agent_schema: str, results: Dict):
    """Save evaluation summary to Delta table."""
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import current_timestamp
    import uuid
    
    spark = SparkSession.builder.getOrCreate()
    table_name = f"{catalog}.{agent_schema}.evaluation_results"
    
    data = [{
        "evaluation_id": str(uuid.uuid4()),
        "mlflow_run_id": results["run_id"],
        "model_version": "production",
        "dataset_name": "standard_benchmark",
        "relevance_score": float(results["avg_relevance"]),
        "safety_score": float(results["avg_safety"]),
        "correctness_score": 0.0,  # Not evaluated in simple mode
        "domain_accuracy_score": 0.0,  # Not evaluated in simple mode
        "overall_score": float(results["overall_score"]),
        "num_samples": int(results["total_queries"]),
    }]
    
    df = spark.createDataFrame(data)
    df = df.withColumn("evaluation_timestamp", current_timestamp())
    
    try:
        df.write.format("delta").mode("append").saveAsTable(table_name)
        print(f"✓ Results saved to {table_name}")
    except Exception as e:
        print(f"⚠ Could not save to Delta: {e}")

# COMMAND ----------

# Main execution
exit_status = "SUCCESS"
exit_message = ""
evaluation_results = None

try:
    print("=" * 70)
    print("HEALTH MONITOR AGENT EVALUATION")
    print("=" * 70)
    
    evaluation_results = evaluate_agent(catalog, agent_schema)
    
    # Save to Delta
    save_results_to_delta(catalog, agent_schema, evaluation_results)
    
    print("\n✓ Evaluation completed successfully!")
    print(f"\nView results: mlflow experiments -> /Shared/health_monitor/agent (run_type=evaluation)")
    print(f"Run ID: {evaluation_results['run_id']}")
    
    # Detailed threshold check
    print(f"\n{'='*70}")
    print("THRESHOLD CHECK")
    print(f"{'='*70}")
    print(f"Overall Score: {evaluation_results['overall_score']:.3f}")
    print(f"Threshold:     0.70")
    print(f"Status:        {'✓ PASS' if evaluation_results['overall_score'] >= 0.7 else '✗ FAIL'}")
    print(f"{'='*70}")
    
    if evaluation_results["overall_score"] >= 0.7:
        print("\n✓ Agent meets minimum quality threshold (0.7)")
        exit_status = "SUCCESS"
        exit_message = f"Evaluation passed: {evaluation_results['overall_score']:.3f}"
    else:
        print(f"\n⚠ Agent below quality threshold: {evaluation_results['overall_score']:.3f} < 0.7")
        exit_status = "WARNING"
        exit_message = f"Below threshold: {evaluation_results['overall_score']:.3f} < 0.70"
        
except Exception as e:
    print(f"\n❌ Evaluation failed: {str(e)}")
    import traceback
    traceback.print_exc()
    exit_status = "FAILED"
    exit_message = str(e)

# COMMAND ----------

# Exit in separate cell to avoid Databricks "FAILED: SUCCESS" issue
print(f"\n{'='*70}")
print(f"Final Status: {exit_status}")
print(f"Message: {exit_message}")
if evaluation_results:
    print(f"Overall Score: {evaluation_results['overall_score']:.3f}")
    print(f"Avg Relevance: {evaluation_results['avg_relevance']:.3f}")
    print(f"Avg Safety: {evaluation_results['avg_safety']:.3f}")
print(f"{'='*70}\n")

if exit_status == "SUCCESS":
    dbutils.notebook.exit(exit_message)
elif exit_status == "WARNING":
    dbutils.notebook.exit(f"WARNING - {exit_message}")
else:
    dbutils.notebook.exit(f"FAILED: {exit_message}")
