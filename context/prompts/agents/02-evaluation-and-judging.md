# Agent Evaluation & LLM Judging Implementation Prompt

## Purpose
Guide for implementing comprehensive agent evaluation using MLflow 3.0+ with LLM-as-judge pattern and custom domain-specific scorers.

## Core Principles

### 1. Evaluation as Gatekeeper
Evaluation is NOT just metrics - it's the **deployment approval mechanism**.

```python
# Pattern: Evaluation → Threshold Check → Deploy/Block
passed, metrics = run_evaluation(agent_uri)

if passed:
    deploy_to_production(agent_uri)
else:
    print("❌ Deployment blocked - thresholds not met")
    print(f"Failed metrics: {get_failed_metrics(metrics, thresholds)}")
```

### 2. Guidelines: 4-6 Essential Sections (Not 8+)

**Production Learning:** 8 comprehensive guidelines → 0.20 score (too strict)  
**Solution:** 4 focused guidelines → 0.5+ score (achievable, meaningful)

```python
# ❌ WRONG: Too comprehensive
guidelines = [
    "200-word section on response structure",
    "180-word section on data accuracy",
    "150-word section on no fabrication",
    "160-word section on actionability",
    "200-word section on domain expertise",
    "150-word section on cross-domain insights",
    "120-word section on professional tone",
    "170-word section on completeness"
]
# Result: guidelines/mean = 0.20

# ✅ CORRECT: Focused essentials
guidelines = [
    """Data Accuracy and Specificity:
    - MUST include specific numbers (costs in $, DBUs, percentages)
    - MUST include time context (when data is from)
    - MUST include trend direction (↑/↓)
    - MUST cite sources explicitly""",
    
    """No Data Fabrication (CRITICAL):
    - MUST NEVER fabricate numbers
    - If tool errors, MUST state explicitly
    - MUST NEVER hallucinate data""",
    
    """Actionability and Recommendations:
    - MUST provide specific, actionable next steps
    - MUST include concrete implementation details
    - MUST prioritize by urgency""",
    
    """Professional Enterprise Tone:
    - MUST maintain professional tone
    - MUST use proper markdown formatting
    - MUST be clear and concise"""
]
# Result: guidelines/mean = 0.5+
```

### 3. Custom Judges with Foundation Models

**Use foundation model endpoints (NOT pay-per-token) for cost efficiency.**

```python
from mlflow.metrics import make_genai_metric_from_prompt

@mlflow.trace(name="cost_accuracy_judge", span_type="JUDGE")
@scorer
def cost_accuracy_judge(trace, parameters=None):
    """Domain-specific judge for cost accuracy."""
    
    # Extract input/output from trace
    query = trace.data.request.get("messages", [{}])[-1].get("content", "")
    response = trace.data.response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Define evaluation prompt
    judge_prompt = """Evaluate cost accuracy (1-5):

1. **Specific Numbers**: Uses actual $ or DBU values
2. **Proper Units**: Costs in $ or DBUs, not percentages
3. **Time Context**: Specifies time period
4. **Source Citation**: References [Cost Genie]
5. **Trend Direction**: Shows increase/decrease

Query: {query}
Response: {response}

Output JSON: {{"score": <1-5>, "justification": "<reason>"}}"""
    
    # Use foundation model endpoint
    cost_metric = make_genai_metric_from_prompt(
        name="cost_accuracy",
        definition=judge_prompt,
        grading_prompt=judge_prompt,
        model="endpoints:/databricks-claude-sonnet-4-5",  # ✅ Foundation model
        parameters={"temperature": 0.0, "max_tokens": 500},
        aggregations=["mean", "p90"],
        greater_is_better=True
    )
    
    # Execute judge
    result = cost_metric.eval_fn(
        inputs={"query": query},
        outputs={"response": response},
        metrics={}
    )
    
    # Return standardized format
    return {
        "score": result.score / 5.0,  # Normalize to 0-1
        "justification": result.justification,
        "metadata": {
            "raw_score": result.score,
            "model": "databricks-claude-sonnet-4-5"
        }
    }
```

### 4. Consistent Run Naming for Programmatic Access

```python
# ✅ CORRECT: Predictable pattern
run_name = f"eval_pre_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Query latest evaluation
runs = mlflow.search_runs(
    filter_string="tags.mlflow.runName LIKE 'eval_pre_deploy_%'",
    order_by=["start_time DESC"],
    max_results=1
)
```

## Complete Evaluation Implementation

```python
# File: src/agents/setup/deployment_job.py

import mlflow
import pandas as pd
from datetime import datetime
from mlflow.metrics.genai import relevance, safety, Guidelines

# ===========================================================================
# EVALUATION CONFIGURATION
# ===========================================================================

EVAL_EXPERIMENT = "/Shared/my_agent_evaluation"
EVAL_DATASET_PATH = "datasets/evaluation_dataset.json"

# ===========================================================================
# CUSTOM JUDGES
# ===========================================================================

@mlflow.trace(name="domain_accuracy_judge", span_type="JUDGE")
@scorer
def domain_accuracy_judge(trace, parameters=None):
    """Judge for domain-specific accuracy."""
    # Implementation here
    pass

# ... more custom judges ...

# ===========================================================================
# THRESHOLD CONFIGURATION
# ===========================================================================

DEPLOYMENT_THRESHOLDS = {
    # Built-in judges
    "relevance/mean": 0.4,        # Lowered threshold
    "safety/mean": 0.7,           # Critical threshold
    "guidelines/mean": 0.5,       # Achievable with 4 sections
    
    # Custom domain judges
    "cost_accuracy/mean": 0.6,
    "security_compliance/mean": 0.6,
    "performance_accuracy/mean": 0.6,
    "reliability_accuracy/mean": 0.5,
    "quality_accuracy/mean": 0.6,
    
    # Response quality
    "response_length/mean": 0.1,  # Not too short
    "no_errors/mean": 0.3,        # Minimal errors
}

# ===========================================================================
# MAIN EVALUATION FUNCTION
# ===========================================================================

def run_agent_evaluation(model_uri: str) -> tuple[bool, dict]:
    """
    Run comprehensive agent evaluation.
    
    Returns:
        (passed: bool, metrics: dict)
    """
    print("\n" + "=" * 80)
    print("AGENT EVALUATION - LLM Judges")
    print("=" * 80)
    
    # Set evaluation experiment
    mlflow.set_experiment(EVAL_EXPERIMENT)
    
    # Load evaluation dataset
    eval_df = pd.read_json(EVAL_DATASET_PATH)
    print(f"✓ Loaded {len(eval_df)} evaluation queries")
    
    # ========== DEFINE EVALUATORS ==========
    
    # Built-in judges
    evaluators = [
        ("relevance", relevance, 1.0),
        ("safety", safety, 1.0),
        ("guidelines", Guidelines(guidelines=[
            """Data Accuracy: MUST include specific numbers with time context""",
            """No Fabrication: MUST NEVER guess at numbers""",
            """Actionability: MUST provide specific next steps""",
            """Professional Tone: MUST use proper formatting"""
        ]), 1.0),
    ]
    
    # Custom domain judges
    evaluators.extend([
        ("cost_accuracy", cost_accuracy_judge, 1.0),
        ("security_compliance", security_compliance_judge, 1.0),
        ("performance_accuracy", performance_accuracy_judge, 1.0),
        ("reliability_accuracy", reliability_accuracy_judge, 1.0),
        ("quality_accuracy", quality_accuracy_judge, 1.0),
    ])
    
    print(f"✓ Registered {len(evaluators)} evaluators")
    
    # ========== RUN EVALUATION ==========
    
    run_name = f"eval_pre_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        # Log parameters
        mlflow.log_params({
            "model_uri": model_uri,
            "eval_dataset": EVAL_DATASET_PATH,
            "num_queries": len(eval_df),
        })
        
        # Run evaluation
        results = mlflow.genai.evaluate(
            model=model_uri,
            data=eval_df,
            model_type="databricks-agent",
            evaluators=evaluators,
            evaluator_config={
                "col_mapping": {
                    "inputs": "request",
                    "output": "response"
                }
            }
        )
        
        print(f"✓ Evaluation complete: {run.info.run_id}")
        
        # ========== CHECK THRESHOLDS ==========
        
        metrics = results.metrics
        print("\n📊 Evaluation Metrics:")
        print("-" * 80)
        
        for metric_name, threshold in DEPLOYMENT_THRESHOLDS.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                passed = value >= threshold
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {metric_name:<30} {value:.3f}  (>= {threshold})  {status}")
        
        # Check all thresholds
        all_passed = all(
            metrics.get(metric_name, 0) >= threshold
            for metric_name, threshold in DEPLOYMENT_THRESHOLDS.items()
        )
        
        if all_passed:
            print("\n✅ All thresholds passed - APPROVED for deployment")
        else:
            failed_metrics = [
                metric for metric, threshold in DEPLOYMENT_THRESHOLDS.items()
                if metrics.get(metric, 0) < threshold
            ]
            print(f"\n❌ Failed thresholds: {', '.join(failed_metrics)}")
            print("NOT approved for deployment")
        
        return all_passed, metrics


# ===========================================================================
# DEPLOYMENT ORCHESTRATION
# ===========================================================================

def main():
    """Evaluate and deploy agent."""
    # Get model URI
    model_uri = f"models:/my_agent/{version}"
    
    # Run evaluation
    passed, metrics = run_agent_evaluation(model_uri)
    
    if passed:
        # Promote to production
        client = mlflow.MlflowClient()
        client.set_registered_model_alias(
            name="my_agent",
            alias="champion",
            version=str(version)
        )
        print(f"\n✅ Promoted version {version} to 'champion'")
    else:
        print(f"\n❌ Version {version} did NOT pass evaluation")
        print("Review metrics and improve agent before redeploying")
    
    return passed


if __name__ == "__main__":
    main()
```

## Evaluation Dataset Format

```json
[
    {
        "request": {
            "input": [{"role": "user", "content": "Why did costs spike yesterday?"}],
            "custom_inputs": {"user_id": "test_user"}
        },
        "expected_output": {
            "contains_cost_value": true,
            "contains_time_context": true,
            "cites_source": true,
            "no_fabrication": true
        }
    },
    {
        "request": {
            "input": [{"role": "user", "content": "Which jobs failed today?"}]
        },
        "expected_output": {
            "contains_job_names": true,
            "contains_failure_reasons": true,
            "no_fabrication": true
        }
    }
]
```

## Viewing Judge Criteria and Results

### Option 1: MLflow Experiment UI

1. Navigate to experiment: `/Shared/my_agent_evaluation`
2. Click on evaluation run (look for `eval_pre_deploy_*`)
3. **Evaluation** tab shows aggregate metrics per judge
4. **Traces** tab shows individual query executions with judge reasoning

### Option 2: Download Scored Outputs CSV

```python
from mlflow import MlflowClient

client = MlflowClient()

# Get latest evaluation run
runs = mlflow.search_runs(
    experiment_ids=[experiment_id],
    filter_string="tags.mlflow.runName LIKE 'eval_pre_deploy_%'",
    order_by=["start_time DESC"],
    max_results=1
)

run_id = runs.iloc[0]['run_id']

# Download scored outputs
for artifact in client.list_artifacts(run_id):
    if "scored_outputs" in artifact.path:
        local_path = client.download_artifacts(run_id, artifact.path)
        
        import pandas as pd
        df = pd.read_csv(local_path)
        
        # Columns include:
        # - request: Original query
        # - response: Agent output
        # - relevance: Score
        # - relevance/justification: Reasoning
        # - guidelines: Score
        # - cost_accuracy: Score
        # ... etc ...
```

## Custom Judge Template

```python
@mlflow.trace(name="{domain}_judge", span_type="JUDGE")
@scorer
def domain_judge(trace, parameters=None):
    """
    Custom judge for {domain} evaluation.
    
    Evaluates:
    1. Criterion 1
    2. Criterion 2
    3. Criterion 3
    """
    # Extract from trace
    query = trace.data.request.get("messages", [{}])[-1].get("content", "")
    response = trace.data.response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Define judge prompt
    judge_prompt = """Evaluate response quality (1-5):

**Evaluation Criteria:**
1. [Criterion 1]: [Description]
2. [Criterion 2]: [Description]
3. [Criterion 3]: [Description]

**Query:** {query}

**Response:** {response}

**Output JSON:**
{{
  "score": <1-5>,
  "justification": "<Specific examples from response>"
}}
"""
    
    # Create GenAI metric
    metric = make_genai_metric_from_prompt(
        name="{domain}_accuracy",
        definition=judge_prompt,
        grading_prompt=judge_prompt,
        model="endpoints:/databricks-claude-sonnet-4-5",
        parameters={"temperature": 0.0, "max_tokens": 500},
        aggregations=["mean", "p90"],
        greater_is_better=True
    )
    
    # Execute
    result = metric.eval_fn(
        inputs={"query": query},
        outputs={"response": response},
        metrics={}
    )
    
    # Return standardized
    return {
        "score": result.score / 5.0,
        "justification": result.justification,
        "metadata": {
            "raw_score": result.score,
            "model": "databricks-claude-sonnet-4-5"
        }
    }
```

## Common Mistakes to Avoid

### ❌ NEVER: Too Many Guidelines

```python
# BAD: 8 sections → 0.20 score
guidelines = [
    "200 words on structure",
    "180 words on accuracy",
    "150 words on fabrication",
    "160 words on actionability",
    "200 words on expertise",
    "150 words on cross-domain",
    "120 words on tone",
    "170 words on completeness"
]
```

### ❌ NEVER: Pay-Per-Token Endpoints

```python
# BAD: Expensive for evaluation
model="pay-per-token-endpoint"
```

### ❌ NEVER: Missing Run Name Pattern

```python
# BAD: Can't query programmatically
mlflow.genai.evaluate(...)  # No run_name!
```

### ❌ NEVER: No Threshold Checks

```python
# BAD: Evaluate but don't block deployment
run_evaluation(model)
deploy(model)  # Always deploys!
```

## Success Criteria

Your evaluation system is complete when:
- ✅ 4-6 focused guidelines (not 8+)
- ✅ Custom judges use foundation model endpoints
- ✅ Thresholds defined for all judges
- ✅ Consistent run naming enables programmatic queries
- ✅ Deployment blocked if thresholds not met
- ✅ Scored outputs CSV contains per-query results
- ✅ Traces show judge reasoning in MLflow UI
- ✅ Evaluation runs automatically before deployment

## Checklist for Each Judge

- [ ] Uses `@mlflow.trace(span_type="JUDGE")` decorator
- [ ] Uses `@scorer` decorator
- [ ] Returns `{"score": float, "justification": str, "metadata": dict}`
- [ ] Score normalized to 0-1 range
- [ ] Uses foundation model endpoint (not pay-per-token)
- [ ] Temperature = 0.0 for consistency
- [ ] 3-5 clear, objective evaluation criteria
- [ ] Examples of good/bad responses in prompt

## References

- [MLflow GenAI Evaluate](https://mlflow.org/docs/latest/llms/llm-evaluate/)
- [Custom LLM Metrics](https://mlflow.org/docs/latest/llms/llm-evaluate/index.html#creating-custom-llm-evaluation-metrics)
- [LLM-as-Judge Pattern](https://mlflow.org/docs/latest/llms/llm-evaluate/index.html#llm-as-judge-metrics)
- [Databricks Agent Evaluation](https://docs.databricks.com/en/generative-ai/agent-evaluation/)

---

**Use this prompt to implement comprehensive agent evaluation with LLM judges following production best practices.**
