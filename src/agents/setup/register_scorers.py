# Databricks notebook source
# ===========================================================================
# Register Scorers for Production Monitoring
# ===========================================================================
"""
Register built-in and custom scorers to MLflow for production monitoring.

This makes scorers appear in the MLflow UI "Scorers" tab and enables
automatic quality assessment of production traces.

NOTE: Requires MLflow 3.0+ with mlflow.genai module. If not available,
this notebook will exit early (scorers require MLflow GenAI features).

Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/production-monitoring
"""

# COMMAND ----------

import mlflow

# Check if mlflow.genai is available (requires MLflow 3.0+)
# Job will FAIL if MLflow 3.0+ is not available - no graceful degradation
try:
    from mlflow.genai.scorers import scorer, ScorerSamplingConfig
    print("✓ mlflow.genai module available")
except ImportError as e:
    error_msg = (
        "\n" + "=" * 70 + "\n"
        "❌ CRITICAL ERROR: MLflow 3.0+ Required\n"
        "=" * 70 + "\n"
        f"The mlflow.genai module is not available.\n\n"
        f"Import Error: {e}\n\n"
        "This agent requires MLflow 3.0+ for:\n"
        "  - MLflow GenAI Scorers (Safety, Relevance, etc.)\n"
        "  - Production Monitoring\n"
        "  - Custom LLM Judges\n\n"
        "Solutions:\n"
        "  1. Upgrade MLflow: pip install 'mlflow>=3.0.0'\n"
        "  2. Use a Databricks Runtime with MLflow 3.0+ pre-installed\n"
        "  3. Add mlflow>=3.0.0 to job environment dependencies\n"
        "=" * 70
    )
    print(error_msg)
    raise ImportError(error_msg) from e

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")

# COMMAND ----------

# NOTE: Scorer registration is configuration, not experimentation
# Scorers are registered to MLflow and used by evaluation runs
# No MLflow run is created for scorer registration
print("✓ Scorers will be available for evaluation runs")
print("  Evaluation experiment: /Shared/health_monitor_agent_evaluation")

# COMMAND ----------

# ===========================================================================
# Built-in LLM Judges
# ===========================================================================

def register_builtin_scorers():
    """Register MLflow's built-in LLM judges for production monitoring."""
    
    print("\n" + "=" * 60)
    print("Registering Built-in Scorers")
    print("=" * 60)
    
    registered_scorers = []
    
    # Safety Judge - High priority, 100% coverage
    try:
        from mlflow.genai.scorers import Safety
        safety_judge = Safety()
        safety_judge = safety_judge.register(name="safety_judge")
        safety_judge = safety_judge.start(sampling_config=ScorerSamplingConfig(sample_rate=1.0))
        print(f"  ✓ Registered: safety_judge (sample_rate=1.0)")
        registered_scorers.append("safety_judge")
    except Exception as e:
        print(f"  ✗ Safety scorer error: {e}")
    
    # Relevance Judge - Medium priority
    try:
        from mlflow.genai.scorers import Relevance
        relevance_judge = Relevance()
        relevance_judge = relevance_judge.register(name="relevance_judge")
        relevance_judge = relevance_judge.start(sampling_config=ScorerSamplingConfig(sample_rate=0.5))
        print(f"  ✓ Registered: relevance_judge (sample_rate=0.5)")
        registered_scorers.append("relevance_judge")
    except Exception as e:
        print(f"  ✗ Relevance scorer error: {e}")
    
    # Correctness Judge - Medium priority
    try:
        from mlflow.genai.scorers import Correctness
        correctness_judge = Correctness()
        correctness_judge = correctness_judge.register(name="correctness_judge")
        correctness_judge = correctness_judge.start(sampling_config=ScorerSamplingConfig(sample_rate=0.3))
        print(f"  ✓ Registered: correctness_judge (sample_rate=0.3)")
        registered_scorers.append("correctness_judge")
    except Exception as e:
        print(f"  ✗ Correctness scorer error: {e}")
    
    return registered_scorers

# COMMAND ----------

# ===========================================================================
# Guidelines-based Scorers
# ===========================================================================

def register_guidelines_scorers():
    """Register Guidelines-based LLM judges."""
    
    print("\n" + "=" * 60)
    print("Registering Guidelines Scorers")
    print("=" * 60)
    
    registered_scorers = []
    
    try:
        from mlflow.genai.scorers import Guidelines
        
        # Health Monitor specific guidelines
        health_monitor_guidelines = Guidelines(
            name="health_monitor_guidelines",
            guidelines=[
                "Response should include relevant Databricks metrics or data",
                "Response should be actionable with clear recommendations",
                "Response should correctly identify the domain (cost, security, performance, reliability, quality)",
                "Response should not expose sensitive credentials or PII",
                "Response should cite specific tables, jobs, or resources when available"
            ]
        )
        health_monitor_guidelines = health_monitor_guidelines.register(name="health_monitor_guidelines")
        health_monitor_guidelines = health_monitor_guidelines.start(
            sampling_config=ScorerSamplingConfig(sample_rate=0.3)
        )
        print(f"  ✓ Registered: health_monitor_guidelines (sample_rate=0.3)")
        registered_scorers.append("health_monitor_guidelines")
        
    except Exception as e:
        print(f"  ✗ Guidelines scorer error: {e}")
    
    return registered_scorers

# COMMAND ----------

# ===========================================================================
# Custom Code-based Scorers
# ===========================================================================

def register_custom_scorers():
    """Register custom code-based scorers for domain-specific monitoring."""
    
    print("\n" + "=" * 60)
    print("Registering Custom Scorers")
    print("=" * 60)
    
    registered_scorers = []
    
    # Response length scorer
    @scorer(aggregations=["mean", "min", "max"])
    def response_length(outputs):
        """Measure response length in characters."""
        response = outputs.get("response", "") if isinstance(outputs, dict) else str(outputs)
        return len(str(response))
    
    try:
        response_length_scorer = response_length.register(name="response_length")
        response_length_scorer = response_length_scorer.start(
            sampling_config=ScorerSamplingConfig(sample_rate=1.0)
        )
        print(f"  ✓ Registered: response_length (sample_rate=1.0)")
        registered_scorers.append("response_length")
    except Exception as e:
        print(f"  ✗ Response length scorer error: {e}")
    
    # Domain detection scorer
    @scorer
    def domain_detected(inputs, outputs):
        """Check if a valid domain was detected in the response."""
        valid_domains = ["cost", "security", "performance", "reliability", "quality", "unified"]
        
        response = outputs.get("response", "") if isinstance(outputs, dict) else str(outputs)
        response_lower = response.lower()
        
        for domain in valid_domains:
            if domain in response_lower:
                return 1.0
        return 0.0
    
    try:
        domain_scorer = domain_detected.register(name="domain_detected")
        domain_scorer = domain_scorer.start(
            sampling_config=ScorerSamplingConfig(sample_rate=0.5)
        )
        print(f"  ✓ Registered: domain_detected (sample_rate=0.5)")
        registered_scorers.append("domain_detected")
    except Exception as e:
        print(f"  ✗ Domain detected scorer error: {e}")
    
    # Mentions Databricks scorer
    @scorer
    def mentions_databricks(outputs):
        """Check if response mentions Databricks-related concepts."""
        databricks_terms = [
            "databricks", "cluster", "warehouse", "job", "notebook", 
            "unity catalog", "delta", "spark", "dbu", "workspace"
        ]
        
        response = outputs.get("response", "") if isinstance(outputs, dict) else str(outputs)
        response_lower = response.lower()
        
        matches = sum(1 for term in databricks_terms if term in response_lower)
        return min(matches / 3, 1.0)  # Normalize to 0-1
    
    try:
        databricks_scorer = mentions_databricks.register(name="mentions_databricks")
        databricks_scorer = databricks_scorer.start(
            sampling_config=ScorerSamplingConfig(sample_rate=0.5)
        )
        print(f"  ✓ Registered: mentions_databricks (sample_rate=0.5)")
        registered_scorers.append("mentions_databricks")
    except Exception as e:
        print(f"  ✗ Mentions Databricks scorer error: {e}")
    
    # Actionable response scorer
    @scorer
    def actionable_response(outputs):
        """Check if response contains actionable recommendations."""
        action_keywords = [
            "recommend", "suggest", "should", "consider", "try",
            "action", "step", "optimize", "reduce", "increase",
            "check", "review", "investigate", "monitor"
        ]
        
        response = outputs.get("response", "") if isinstance(outputs, dict) else str(outputs)
        response_lower = response.lower()
        
        matches = sum(1 for kw in action_keywords if kw in response_lower)
        return min(matches / 3, 1.0)  # Normalize to 0-1
    
    try:
        actionable_scorer = actionable_response.register(name="actionable_response")
        actionable_scorer = actionable_scorer.start(
            sampling_config=ScorerSamplingConfig(sample_rate=0.3)
        )
        print(f"  ✓ Registered: actionable_response (sample_rate=0.3)")
        registered_scorers.append("actionable_response")
    except Exception as e:
        print(f"  ✗ Actionable response scorer error: {e}")
    
    return registered_scorers

# COMMAND ----------

# ===========================================================================
# Domain-Specific LLM Judges
# ===========================================================================

def register_domain_judges():
    """Register domain-specific LLM judges using custom prompts."""
    
    print("\n" + "=" * 60)
    print("Registering Domain-Specific LLM Judges")
    print("=" * 60)
    
    registered_scorers = []
    
    # Cost Domain Judge
    @scorer
    def cost_domain_accuracy(inputs, outputs, trace):
        """Evaluate accuracy of cost-related responses."""
        from mlflow.genai.judges import custom_prompt_judge
        from mlflow.entities.assessment import DEFAULT_FEEDBACK_NAME
        
        cost_prompt = """
        You are evaluating a response about Databricks cost analysis.
        
        <query>{{request}}</query>
        <response>{{response}}</response>
        
        Evaluate if the response accurately addresses cost-related queries.
        
        [[accurate]]: Response provides accurate cost insights with specific metrics.
        [[partially_accurate]]: Response addresses cost but lacks specifics.
        [[inaccurate]]: Response does not correctly address cost queries.
        """
        
        judge = custom_prompt_judge(
            name="cost_accuracy",
            prompt_template=cost_prompt,
            numeric_values={
                "accurate": 1.0,
                "partially_accurate": 0.5,
                "inaccurate": 0.0,
            },
        )
        
        query = inputs.get("query", "") if isinstance(inputs, dict) else str(inputs)
        response = outputs.get("response", "") if isinstance(outputs, dict) else str(outputs)
        
        result = judge(request=query, response=response)
        if hasattr(result, "name"):
            result.name = DEFAULT_FEEDBACK_NAME
        return result
    
    try:
        cost_judge = cost_domain_accuracy.register(name="cost_domain_accuracy")
        cost_judge = cost_judge.start(sampling_config=ScorerSamplingConfig(sample_rate=0.1))
        print(f"  ✓ Registered: cost_domain_accuracy (sample_rate=0.1)")
        registered_scorers.append("cost_domain_accuracy")
    except Exception as e:
        print(f"  ✗ Cost domain judge error: {e}")
    
    # Security Domain Judge
    @scorer
    def security_domain_accuracy(inputs, outputs, trace):
        """Evaluate accuracy of security-related responses."""
        from mlflow.genai.judges import custom_prompt_judge
        from mlflow.entities.assessment import DEFAULT_FEEDBACK_NAME
        
        security_prompt = """
        You are evaluating a response about Databricks security and compliance.
        
        <query>{{request}}</query>
        <response>{{response}}</response>
        
        Evaluate if the response accurately addresses security concerns.
        
        [[secure]]: Response provides accurate security insights without exposing sensitive info.
        [[partially_secure]]: Response addresses security but may be incomplete.
        [[insecure]]: Response may expose sensitive information or gives incorrect security advice.
        """
        
        judge = custom_prompt_judge(
            name="security_accuracy",
            prompt_template=security_prompt,
            numeric_values={
                "secure": 1.0,
                "partially_secure": 0.5,
                "insecure": 0.0,
            },
        )
        
        query = inputs.get("query", "") if isinstance(inputs, dict) else str(inputs)
        response = outputs.get("response", "") if isinstance(outputs, dict) else str(outputs)
        
        result = judge(request=query, response=response)
        if hasattr(result, "name"):
            result.name = DEFAULT_FEEDBACK_NAME
        return result
    
    try:
        security_judge = security_domain_accuracy.register(name="security_domain_accuracy")
        security_judge = security_judge.start(sampling_config=ScorerSamplingConfig(sample_rate=0.1))
        print(f"  ✓ Registered: security_domain_accuracy (sample_rate=0.1)")
        registered_scorers.append("security_domain_accuracy")
    except Exception as e:
        print(f"  ✗ Security domain judge error: {e}")
    
    return registered_scorers

# COMMAND ----------

def main():
    """Main entry point for scorer registration."""
    
    # Experiment path for evaluation runs (scorers will be used here)
    experiment_path = "/Shared/health_monitor_agent_evaluation"
    
    print("\n" + "=" * 70)
    print("PRODUCTION MONITORING SCORER REGISTRATION")
    print("=" * 70)
    print(f"\nExperiment: {experiment_path}")
    print(f"Schema: {catalog}.{agent_schema}")
    
    all_scorers = []
    
    # Register all scorer types
    all_scorers.extend(register_builtin_scorers())
    all_scorers.extend(register_guidelines_scorers())
    all_scorers.extend(register_custom_scorers())
    all_scorers.extend(register_domain_judges())
    
    print("\n" + "=" * 70)
    print("REGISTRATION SUMMARY")
    print("=" * 70)
    print(f"\nTotal scorers registered: {len(all_scorers)}")
    for scorer_name in all_scorers:
        print(f"  - {scorer_name}")
    
    print(f"\nView scorers in MLflow UI:")
    print(f"  Experiment → Scorers tab")
    print(f"\nScorers will automatically evaluate production traces!")
    
    dbutils.notebook.exit("SUCCESS")

# COMMAND ----------

if __name__ == "__main__":
    main()

