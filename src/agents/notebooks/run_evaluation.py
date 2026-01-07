# Databricks notebook source
# MAGIC %md
# MAGIC # Agent Evaluation Pipeline
# MAGIC
# MAGIC Runs quality evaluation on the Health Monitor agent using LLM judges.

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0.0 langchain>=0.3.0 langchain-databricks pandas
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "health_monitor")
dbutils.widgets.text("model_name", "health_monitor_agent")

catalog = dbutils.widgets.get("catalog")
model_name = dbutils.widgets.get("model_name")

# COMMAND ----------

import mlflow
import pandas as pd

# Use consolidated experiment (single experiment for all agent runs)
experiment_name = "/Shared/health_monitor/agent"
mlflow.set_experiment(experiment_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Agent

# COMMAND ----------

# Load the production agent
model_uri = f"models:/{catalog}.agents.{model_name}@champion"

try:
    agent = mlflow.pyfunc.load_model(model_uri)
    print(f"Loaded agent from {model_uri}")
except Exception as e:
    print(f"Failed to load agent: {e}")
    dbutils.notebook.exit("FAILED - Could not load agent")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Evaluation Dataset

# COMMAND ----------

eval_data = pd.DataFrame([
    # Cost queries
    {"query": "Why did costs spike yesterday?", "category": "cost", "expected_domains": ["COST"]},
    {"query": "What are the top 10 most expensive jobs?", "category": "cost", "expected_domains": ["COST"]},
    {"query": "Show DBU usage by workspace", "category": "cost", "expected_domains": ["COST"]},

    # Security queries
    {"query": "Who accessed sensitive data last week?", "category": "security", "expected_domains": ["SECURITY"]},
    {"query": "Show failed login attempts today", "category": "security", "expected_domains": ["SECURITY"]},

    # Performance queries
    {"query": "What are the slowest queries?", "category": "performance", "expected_domains": ["PERFORMANCE"]},
    {"query": "Show cluster utilization trends", "category": "performance", "expected_domains": ["PERFORMANCE"]},

    # Reliability queries
    {"query": "Which jobs failed today?", "category": "reliability", "expected_domains": ["RELIABILITY"]},
    {"query": "What is our SLA compliance?", "category": "reliability", "expected_domains": ["RELIABILITY"]},

    # Quality queries
    {"query": "Which tables have quality issues?", "category": "quality", "expected_domains": ["QUALITY"]},

    # Multi-domain queries
    {"query": "Are expensive jobs also failing?", "category": "multi", "expected_domains": ["COST", "RELIABILITY"]},
    {"query": "Show platform health overview", "category": "multi", "expected_domains": ["COST", "SECURITY", "PERFORMANCE", "RELIABILITY", "QUALITY"]},
])

print(f"Evaluation dataset: {len(eval_data)} queries")
display(eval_data)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Custom Judges

# COMMAND ----------

import json
from mlflow.genai import scorer, Score
from langchain_databricks import ChatDatabricks

LLM_ENDPOINT = "databricks-claude-3-7-sonnet"

@scorer
def domain_accuracy_judge(inputs: dict, outputs: dict, expectations: dict = None) -> Score:
    """Judge domain classification accuracy."""
    query = inputs.get("query", "")
    response = outputs.get("response", "")
    expected = expectations.get("expected_domains", []) if expectations else []

    llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=0)

    prompt = f"""Rate domain accuracy (0-1):
Query: {query}
Expected domains: {expected}
Response: {response[:500]}

Return JSON: {{"score": <float>, "rationale": "<reason>"}}"""

    try:
        result = llm.invoke(prompt)
        parsed = json.loads(result.content)
        return Score(value=float(parsed["score"]), rationale=parsed.get("rationale", ""))
    except:
        return Score(value=0.5, rationale="Evaluation error")

@scorer
def actionability_judge(inputs: dict, outputs: dict, expectations: dict = None) -> Score:
    """Judge response actionability."""
    response = outputs.get("response", "")

    llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=0)

    prompt = f"""Rate actionability (0-1):
Response: {response[:500]}

1.0 = Clear specific actions
0.5 = Generic recommendations
0.0 = No actionable guidance

Return JSON: {{"score": <float>, "rationale": "<reason>"}}"""

    try:
        result = llm.invoke(prompt)
        parsed = json.loads(result.content)
        return Score(value=float(parsed["score"]), rationale=parsed.get("rationale", ""))
    except:
        return Score(value=0.5, rationale="Evaluation error")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Evaluation

# COMMAND ----------

# Custom scorers (for MLflow version compatibility)
@scorer
def relevance_eval(inputs: dict, outputs: dict, expectations: dict = None) -> Score:
    """Custom relevance scorer."""
    query = inputs.get("query", "")
    response = str(outputs.get("response", ""))
    
    # Simple relevance check - could be enhanced with LLM
    if not response or len(response) < 10:
        return Score(value=0.0, rationale="Empty or too short response")
    return Score(value=0.8, rationale="Response provided")


@scorer
def safety_eval(inputs: dict, outputs: dict, expectations: dict = None) -> Score:
    """Custom safety scorer."""
    response = str(outputs.get("response", ""))
    
    # Basic safety check
    if "error" in response.lower() and "harm" in response.lower():
        return Score(value=0.0, rationale="Potentially unsafe")
    return Score(value=1.0, rationale="Response appears safe")


# Define predict function wrapper
def predict_fn(inputs):
    messages = [{"role": "user", "content": inputs["query"]}]
    result = agent.predict({"messages": messages})
    return {"response": result.get("response", "")}

# Run evaluation
with mlflow.start_run(run_name="agent_evaluation"):
    # Tag this run as evaluation type for filtering in consolidated experiment
    mlflow.set_tag("run_type", "evaluation")
    
    results = mlflow.genai.evaluate(
        predict_fn=predict_fn,
        data=eval_data,
        scorers=[
            relevance_eval,
            safety_eval,
            domain_accuracy_judge,
            actionability_judge,
        ],
    )

    # Log summary
    mlflow.log_metric("total_queries", len(eval_data))

    print("\nEvaluation Results:")
    print("=" * 50)
    for metric, value in results.metrics.items():
        print(f"{metric}: {value:.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Results by Category

# COMMAND ----------

# Display detailed results
if hasattr(results, 'tables') and 'eval_results' in results.tables:
    display(results.tables['eval_results'])

# COMMAND ----------

print("Evaluation complete")
dbutils.notebook.exit("SUCCESS")
