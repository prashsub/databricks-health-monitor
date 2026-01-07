# Databricks notebook source
# ===========================================================================
# Create Synthetic Evaluation Dataset for Health Monitor Agent
# ===========================================================================
"""
Creates a synthetic evaluation dataset using Databricks' official
generate_evals_df API from databricks-agents.

This makes evaluation datasets visible in the MLflow UI under:
  Experiment → Datasets tab

Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-evaluation/synthesize-evaluation-set
"""

# COMMAND ----------

# MAGIC %pip install databricks-agents mlflow>=3.0.0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
from mlflow import MlflowClient
from databricks.agents.evals import generate_evals_df, estimate_synthetic_num_evals
import pandas as pd
from datetime import datetime

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")
dbutils.widgets.text("num_evals", "50")  # Number of synthetic evaluations

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")
num_evals = int(dbutils.widgets.get("num_evals"))

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")
print(f"Target Evaluations: {num_evals}")

# COMMAND ----------

# Set experiment
experiment_path = "/Shared/health_monitor/agent"
mlflow.set_experiment(experiment_path)
print(f"Experiment: {experiment_path}")

# COMMAND ----------

# ===========================================================================
# DOMAIN DOCUMENTATION
# ===========================================================================
# These documents describe what the agent knows about each domain.
# generate_evals_df uses these to synthesize relevant questions.

DOMAIN_DOCUMENTS = pd.DataFrame([
    # ===========================================================================
    # COST DOMAIN
    # ===========================================================================
    {
        "content": """
        The Cost Intelligence domain provides comprehensive Databricks billing and usage analysis.
        
        Key capabilities:
        - Total DBU (Databricks Unit) consumption by workspace, cluster, job, and user
        - Cost breakdown by SKU type (Jobs Compute, SQL Warehouse, All-Purpose Compute)
        - Serverless vs classic compute cost comparison
        - Tag coverage analysis for cost allocation
        - Daily, weekly, and monthly cost trends
        - Budget tracking and overspend alerts
        - Cost attribution to teams via tags (tag_team, tag_project)
        
        Common questions users ask:
        - "Why did costs spike yesterday?"
        - "Which jobs are most expensive?"
        - "What is our serverless vs classic ratio?"
        - "Which teams are over budget?"
        - "Show DBU usage by workspace"
        
        Key metrics: total_cost, total_dbus, cost_7d, cost_30d, tag_coverage_percentage
        """,
        "doc_uri": "health_monitor://domains/cost"
    },
    {
        "content": """
        Cost anomaly detection and budget management for Databricks workloads.
        
        The agent can identify:
        - Sudden cost spikes (>20% day-over-day increase)
        - Unusual DBU consumption patterns
        - Inefficient cluster configurations
        - Underutilized resources
        - Cost optimization opportunities
        
        Budget features:
        - Compare actual spend vs allocated budget
        - Forecast monthly costs based on current trajectory
        - Alert when spend exceeds thresholds
        - Track committed vs on-demand usage
        
        Optimization recommendations:
        - Resize overprovisioned clusters
        - Enable autoscaling
        - Use spot instances for non-critical workloads
        - Consolidate underutilized warehouses
        """,
        "doc_uri": "health_monitor://domains/cost/optimization"
    },
    
    # ===========================================================================
    # SECURITY DOMAIN
    # ===========================================================================
    {
        "content": """
        The Security Auditor domain provides comprehensive security monitoring and compliance.
        
        Key capabilities:
        - Audit log analysis (who did what, when, where)
        - Failed login attempt tracking
        - Permission change monitoring
        - Sensitive data access patterns
        - Compliance reporting (SOC2, HIPAA, GDPR)
        - Service principal activity tracking
        
        Common questions users ask:
        - "Who accessed sensitive data last week?"
        - "Show failed login attempts today"
        - "What permissions were changed recently?"
        - "Which service principals are most active?"
        - "Are there any unusual access patterns?"
        
        Key metrics: total_events, failed_events, success_rate, unique_users, high_risk_events
        """,
        "doc_uri": "health_monitor://domains/security"
    },
    {
        "content": """
        Security risk detection and threat monitoring for Databricks workspaces.
        
        Risk indicators tracked:
        - Multiple failed authentication attempts
        - Access from unusual IP addresses or locations
        - After-hours data access
        - Bulk data downloads
        - Privilege escalation attempts
        - Dormant account reactivation
        
        Compliance features:
        - Track access to PII-tagged columns
        - Monitor data export activities
        - Audit secret and credential access
        - Report on data retention compliance
        """,
        "doc_uri": "health_monitor://domains/security/risk"
    },
    
    # ===========================================================================
    # PERFORMANCE DOMAIN
    # ===========================================================================
    {
        "content": """
        The Performance domain monitors query execution and compute efficiency.
        
        Key capabilities:
        - Query execution time analysis
        - Cluster utilization metrics
        - SQL warehouse performance
        - Spark job optimization
        - Cache hit rate tracking
        - Query queue analysis
        
        Common questions users ask:
        - "What are the slowest queries today?"
        - "Which warehouses have low cache hit rates?"
        - "Show cluster utilization this week"
        - "Are there any queries timing out?"
        - "Which jobs have performance regressions?"
        
        Key metrics: avg_duration_seconds, p95_duration_seconds, cache_hit_rate, queue_time
        """,
        "doc_uri": "health_monitor://domains/performance"
    },
    {
        "content": """
        Performance optimization and bottleneck detection.
        
        Optimization opportunities:
        - Queries without clustering keys
        - Missing Z-ORDER optimization
        - Inefficient join patterns
        - Full table scans on large tables
        - Suboptimal file sizes
        
        Cluster tuning:
        - Right-size worker nodes
        - Optimize Spark configurations
        - Enable Photon acceleration
        - Configure auto-termination
        """,
        "doc_uri": "health_monitor://domains/performance/optimization"
    },
    
    # ===========================================================================
    # RELIABILITY DOMAIN
    # ===========================================================================
    {
        "content": """
        The Reliability domain tracks job execution and pipeline health.
        
        Key capabilities:
        - Job success/failure rates
        - Pipeline run monitoring
        - SLA compliance tracking
        - Error categorization
        - Retry pattern analysis
        - Duration trend monitoring
        
        Common questions users ask:
        - "Which jobs failed today?"
        - "What is our SLA compliance this week?"
        - "Show pipeline health across workspaces"
        - "Which jobs have the highest failure rate?"
        - "Are there any recurring errors?"
        
        Key metrics: success_rate, failure_rate, total_runs, avg_duration, error_count
        """,
        "doc_uri": "health_monitor://domains/reliability"
    },
    {
        "content": """
        Job failure analysis and root cause detection.
        
        Error categories:
        - DRIVER_FAILED: Driver process crashed
        - CLUSTER_FAILED: Cluster startup issues
        - TIMEOUT: Job exceeded time limit
        - USER_CANCELLED: Manually stopped
        - DEPENDENCY_FAILED: Upstream failure
        - OUT_OF_MEMORY: Resource exhaustion
        
        Reliability improvements:
        - Configure job alerts
        - Set up retry policies
        - Implement circuit breakers
        - Add health checks
        """,
        "doc_uri": "health_monitor://domains/reliability/failures"
    },
    
    # ===========================================================================
    # DATA QUALITY DOMAIN
    # ===========================================================================
    {
        "content": """
        The Data Quality domain monitors data freshness, completeness, and accuracy.
        
        Key capabilities:
        - Data freshness monitoring (staleness detection)
        - Schema drift detection
        - Null rate tracking
        - Duplicate detection
        - Data volume monitoring
        - Expectation validation results
        
        Common questions users ask:
        - "Which tables have stale data?"
        - "What tables have data quality issues?"
        - "Show data freshness by schema"
        - "Are there any schema changes today?"
        - "Which pipelines have failing expectations?"
        
        Key metrics: freshness_hours, null_rate, duplicate_rate, row_count_change
        """,
        "doc_uri": "health_monitor://domains/quality"
    },
    {
        "content": """
        Data quality rules and validation framework.
        
        Quality checks:
        - NOT_NULL constraints
        - UNIQUE constraints
        - RANGE checks (min/max values)
        - PATTERN matching (regex)
        - REFERENTIAL integrity
        - CUSTOM expectations
        
        Monitoring features:
        - Track quality score over time
        - Alert on quality degradation
        - Quarantine bad records
        - Generate quality reports
        """,
        "doc_uri": "health_monitor://domains/quality/rules"
    },
    
    # ===========================================================================
    # UNIFIED/CROSS-DOMAIN
    # ===========================================================================
    {
        "content": """
        The Unified Health Monitor provides cross-domain analysis and insights.
        
        Key capabilities:
        - Correlate cost with performance issues
        - Link job failures to data quality problems
        - Identify expensive and unreliable jobs
        - Holistic platform health assessment
        - Executive summary dashboards
        
        Common questions users ask:
        - "Give me a complete health check"
        - "Are expensive jobs also failing frequently?"
        - "What's the overall platform status?"
        - "Summarize issues across all domains"
        - "What should I prioritize fixing?"
        
        The agent routes questions to the appropriate domain specialist
        and can synthesize insights across multiple domains.
        """,
        "doc_uri": "health_monitor://domains/unified"
    },
])

print(f"Created {len(DOMAIN_DOCUMENTS)} domain documents")
display(DOMAIN_DOCUMENTS)

# COMMAND ----------

# ===========================================================================
# AGENT DESCRIPTION
# ===========================================================================

AGENT_DESCRIPTION = """
The Databricks Health Monitor Agent is an AI assistant that helps users understand
and optimize their Databricks platform. It specializes in five domains:

1. COST: Billing analysis, DBU consumption, budget tracking, cost optimization
2. SECURITY: Audit logs, access patterns, compliance, threat detection
3. PERFORMANCE: Query optimization, cluster utilization, cache efficiency
4. RELIABILITY: Job monitoring, failure analysis, SLA compliance
5. DATA QUALITY: Freshness monitoring, schema drift, data validation

The agent uses Genie Spaces to query structured data in the Gold layer,
providing accurate, data-driven insights rather than generic advice.

Users are typically:
- Data Engineers monitoring pipeline health
- Platform Administrators managing costs and security
- Data Scientists optimizing query performance
- Engineering Managers tracking SLA compliance
"""

# ===========================================================================
# QUESTION GUIDELINES
# ===========================================================================

QUESTION_GUIDELINES = """
# User Personas
- Data Engineer: Focuses on pipeline reliability and data quality
- Platform Admin: Focuses on costs, security, and resource management
- Data Scientist: Focuses on query performance and optimization
- Engineering Manager: Focuses on SLAs and overall health

# Question Types by Domain

## Cost Domain
- "Why did costs spike yesterday?"
- "What are the top 10 most expensive jobs this month?"
- "Show DBU usage by workspace for last quarter"
- "Which teams are over budget?"
- "Compare serverless vs classic compute costs"

## Security Domain
- "Who accessed sensitive data last week?"
- "Show failed login attempts in the past 24 hours"
- "What permissions changes were made this week?"
- "Are there any unusual access patterns?"

## Performance Domain
- "What are the slowest queries today?"
- "Show cluster utilization trends this week"
- "Which warehouses have low cache hit rates?"
- "Are there any queries timing out?"

## Reliability Domain
- "Which jobs failed today?"
- "What is our SLA compliance this week?"
- "Show pipeline health across all workspaces"
- "Which jobs have the highest failure rate?"

## Quality Domain
- "Which tables have data quality issues?"
- "Show data freshness by schema"
- "What tables have stale data?"
- "Are there any schema changes today?"

## Cross-Domain
- "Are expensive jobs also the ones failing frequently?"
- "Give me a complete health check of the platform"
- "What should I prioritize fixing?"

# Additional Guidelines
- Questions should be natural and human-like
- Include both simple (single fact) and complex (analysis) questions
- Cover different time ranges (today, this week, last month)
- Include questions that require data from Genie Spaces
"""

# COMMAND ----------

# ===========================================================================
# GENERATE SYNTHETIC EVALUATION DATASET
# ===========================================================================

print("\n" + "=" * 60)
print("GENERATING SYNTHETIC EVALUATION DATASET")
print("=" * 60)

# Estimate how many evals we can generate given the documents
estimated_evals = estimate_synthetic_num_evals(
    DOMAIN_DOCUMENTS,
    eval_per_x_tokens=500  # Generate 1 eval per 500 tokens
)
print(f"Estimated possible evaluations: {estimated_evals}")
print(f"Requested evaluations: {num_evals}")

# Generate the synthetic dataset
print("\nGenerating synthetic evaluations...")
evals_df = generate_evals_df(
    docs=DOMAIN_DOCUMENTS,
    num_evals=min(num_evals, estimated_evals),
    agent_description=AGENT_DESCRIPTION,
    question_guidelines=QUESTION_GUIDELINES
)

print(f"\n✓ Generated {len(evals_df)} synthetic evaluations")
display(evals_df)

# COMMAND ----------

# ===========================================================================
# REGISTER DATASET TO MLFLOW
# ===========================================================================

print("\n" + "=" * 60)
print("REGISTERING DATASET TO MLFLOW")
print("=" * 60)

# Create MLflow dataset from the DataFrame
dataset_name = f"health_monitor_eval_synthetic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

with mlflow.start_run(run_name="create_evaluation_dataset"):
    mlflow.set_tag("run_type", "dataset_creation")
    
    # Log the dataset as an MLflow artifact
    # This makes it visible in the MLflow UI
    mlflow_dataset = mlflow.data.from_pandas(
        evals_df,
        source=f"synthetic_generation_{num_evals}_evals",
        name=dataset_name,
    )
    
    # Log the dataset to the run
    mlflow.log_input(mlflow_dataset, context="evaluation")
    
    # Also log parameters about the generation
    mlflow.log_params({
        "num_evals_requested": num_evals,
        "num_evals_generated": len(evals_df),
        "num_source_documents": len(DOMAIN_DOCUMENTS),
        "dataset_name": dataset_name,
    })
    
    print(f"✓ Registered dataset: {dataset_name}")

# COMMAND ----------

# ===========================================================================
# SAVE TO UNITY CATALOG TABLE
# ===========================================================================

print("\n" + "=" * 60)
print("SAVING TO UNITY CATALOG")
print("=" * 60)

# Convert to Spark DataFrame
spark_df = spark.createDataFrame(evals_df)

# Save to Unity Catalog
table_name = f"{catalog}.{agent_schema}.evaluation_dataset_synthetic"

# Create or replace the table
spark_df.write.mode("overwrite").saveAsTable(table_name)

print(f"✓ Saved to: {table_name}")
print(f"  Total rows: {spark_df.count()}")

# COMMAND ----------

# ===========================================================================
# ALSO CREATE MANUAL EVALUATION DATASET (Domain-Specific)
# ===========================================================================

print("\n" + "=" * 60)
print("CREATING MANUAL EVALUATION DATASET")
print("=" * 60)

# Hand-crafted evaluation questions with expected responses
# These provide high-quality ground truth for evaluation
MANUAL_EVALS = [
    # COST DOMAIN
    {
        "inputs": {"messages": [{"role": "user", "content": "Why did costs spike yesterday?"}]},
        "expectations": {
            "expected_domains": ["cost"],
            "expected_facts": [
                "Should analyze day-over-day cost change",
                "Should identify contributing workloads or clusters",
                "Should mention specific cost amounts or percentages"
            ]
        },
        "category": "cost",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What are the top 10 most expensive jobs this month?"}]},
        "expectations": {
            "expected_domains": ["cost"],
            "expected_facts": [
                "Should list job names",
                "Should include cost amounts",
                "Should be sorted by cost descending"
            ]
        },
        "category": "cost",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which teams are over budget?"}]},
        "expectations": {
            "expected_domains": ["cost"],
            "expected_facts": [
                "Should identify teams by tag",
                "Should compare actual vs budget",
                "Should show overspend amount"
            ]
        },
        "category": "cost",
        "difficulty": "moderate"
    },
    
    # SECURITY DOMAIN
    {
        "inputs": {"messages": [{"role": "user", "content": "Who accessed sensitive data last week?"}]},
        "expectations": {
            "expected_domains": ["security"],
            "expected_facts": [
                "Should list user identities",
                "Should mention data accessed",
                "Should include timestamps or date range"
            ]
        },
        "category": "security",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Show failed login attempts in the past 24 hours"}]},
        "expectations": {
            "expected_domains": ["security"],
            "expected_facts": [
                "Should count failed attempts",
                "Should identify users affected",
                "Should mention timeframe"
            ]
        },
        "category": "security",
        "difficulty": "simple"
    },
    
    # PERFORMANCE DOMAIN
    {
        "inputs": {"messages": [{"role": "user", "content": "What are the slowest queries today?"}]},
        "expectations": {
            "expected_domains": ["performance"],
            "expected_facts": [
                "Should list query identifiers",
                "Should include duration",
                "Should be sorted by duration descending"
            ]
        },
        "category": "performance",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which warehouses have low cache hit rates?"}]},
        "expectations": {
            "expected_domains": ["performance"],
            "expected_facts": [
                "Should list warehouse names",
                "Should include cache hit percentages",
                "Should identify underperformers"
            ]
        },
        "category": "performance",
        "difficulty": "moderate"
    },
    
    # RELIABILITY DOMAIN
    {
        "inputs": {"messages": [{"role": "user", "content": "Which jobs failed today?"}]},
        "expectations": {
            "expected_domains": ["reliability"],
            "expected_facts": [
                "Should list failed job names",
                "Should include failure reasons",
                "Should mention failure count"
            ]
        },
        "category": "reliability",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What is our SLA compliance this week?"}]},
        "expectations": {
            "expected_domains": ["reliability"],
            "expected_facts": [
                "Should mention compliance percentage",
                "Should compare to target SLA",
                "Should identify any breaches"
            ]
        },
        "category": "reliability",
        "difficulty": "moderate"
    },
    
    # QUALITY DOMAIN
    {
        "inputs": {"messages": [{"role": "user", "content": "Which tables have stale data?"}]},
        "expectations": {
            "expected_domains": ["quality"],
            "expected_facts": [
                "Should list table names",
                "Should include freshness duration",
                "Should identify staleness threshold breaches"
            ]
        },
        "category": "quality",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What tables have data quality issues?"}]},
        "expectations": {
            "expected_domains": ["quality"],
            "expected_facts": [
                "Should list affected tables",
                "Should describe quality issues",
                "Should include severity or impact"
            ]
        },
        "category": "quality",
        "difficulty": "moderate"
    },
    
    # CROSS-DOMAIN
    {
        "inputs": {"messages": [{"role": "user", "content": "Are expensive jobs also the ones failing frequently?"}]},
        "expectations": {
            "expected_domains": ["cost", "reliability"],
            "expected_facts": [
                "Should correlate cost and failure data",
                "Should identify jobs that are both expensive and unreliable",
                "Should provide actionable recommendations"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Give me a complete health check of the platform"}]},
        "expectations": {
            "expected_domains": ["cost", "security", "performance", "reliability", "quality"],
            "expected_facts": [
                "Should cover all five domains",
                "Should provide summary metrics for each",
                "Should highlight any issues",
                "Should prioritize concerns"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
]

# Convert to DataFrame
manual_evals_df = pd.DataFrame(MANUAL_EVALS)
print(f"Created {len(manual_evals_df)} manual evaluations")

# Register to MLflow
with mlflow.start_run(run_name="create_manual_evaluation_dataset"):
    mlflow.set_tag("run_type", "dataset_creation")
    
    mlflow_manual_dataset = mlflow.data.from_pandas(
        manual_evals_df,
        source="manual_curation",
        name="health_monitor_eval_manual",
    )
    
    mlflow.log_input(mlflow_manual_dataset, context="evaluation")
    
    mlflow.log_params({
        "num_evals": len(manual_evals_df),
        "categories": list(manual_evals_df["category"].unique()),
        "difficulties": list(manual_evals_df["difficulty"].unique()),
    })
    
    print(f"✓ Registered manual dataset")

# Save to Unity Catalog
manual_table_name = f"{catalog}.{agent_schema}.evaluation_dataset_manual"
spark.createDataFrame(manual_evals_df).write.mode("overwrite").saveAsTable(manual_table_name)
print(f"✓ Saved to: {manual_table_name}")

# COMMAND ----------

# ===========================================================================
# SUMMARY
# ===========================================================================

print("\n" + "=" * 70)
print("EVALUATION DATASET CREATION SUMMARY")
print("=" * 70)

print("\n📊 Datasets Created:")
print(f"  1. Synthetic Dataset: {len(evals_df)} evaluations")
print(f"     → Table: {table_name}")
print(f"  2. Manual Dataset: {len(manual_evals_df)} evaluations")
print(f"     → Table: {manual_table_name}")

print("\n📍 View in MLflow UI:")
print(f"  Experiment: {experiment_path}")
print(f"  Tab: Datasets")

print("\n🔧 Usage:")
print(f"  # Load synthetic dataset")
print(f"  evals = spark.table('{table_name}').toPandas()")
print(f"  mlflow.evaluate(model=agent, data=evals, model_type='databricks-agent')")

print("=" * 70)

dbutils.notebook.exit("SUCCESS")

