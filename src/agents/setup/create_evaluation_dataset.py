# Databricks notebook source
# ===========================================================================
# Create Manual Evaluation Dataset for Health Monitor Agent
# ===========================================================================
"""
TRAINING MATERIAL: Manual vs Synthetic Evaluation Datasets
==========================================================

This script demonstrates creating hand-crafted evaluation datasets
for agents that don't fit the standard RAG pattern.

WHY MANUAL EVALUATION:
----------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  APPROACH              │  BEST FOR                │  OUR AGENT          │
├────────────────────────┼──────────────────────────┼─────────────────────┤
│  Synthetic (LLM-gen)   │  Document RAG, Q&A       │  ❌ Not applicable   │
│  Manual (Hand-crafted) │  Tool-using, Multi-step  │  ✅ Recommended      │
│  Production Logs       │  Existing deployments    │  ✅ Supplement       │
└────────────────────────┴──────────────────────────┴─────────────────────┘

Our agent queries Genie Spaces (not documents), so synthetic generation
(which assumes document retrieval) produces irrelevant questions.

EVALUATION DATASET STRUCTURE:
-----------------------------

    {
        "request": "What's our daily DBU spend?",  # User question
        "expected_response": "...",                # Ground truth (optional)
        "expected_facts": ["DBU", "cost"],         # Required concepts
        "domain": "cost",                          # For domain-specific analysis
    }

DATASET REGISTRATION:
---------------------

Datasets are registered to MLflow for:
- Version tracking
- UI visibility (Experiment → Datasets tab)
- Reproducible evaluation runs

    mlflow.genai.datasets.create_eval_dataset(
        uc_table_name=f"{catalog}.{schema}.eval_questions",
        experiment_id=experiment.experiment_id,
        name="manual_evaluation_v1"
    )

This makes evaluation datasets visible in the MLflow UI under:
  Experiment → Datasets tab

Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/build-eval-dataset
"""

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0.0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
from mlflow import MlflowClient
import mlflow.genai.datasets as mlflow_datasets
import pandas as pd
from datetime import datetime

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")

# COMMAND ----------

# ===========================================================================
# MLFLOW EXPERIMENT SETUP
# ===========================================================================
# Datasets are attached to experiments - using the same experiment as evaluation

experiment_path = "/Shared/health_monitor_agent_evaluation"
mlflow.set_experiment(experiment_path)
print(f"MLflow Experiment: {experiment_path}")

# COMMAND ----------

# ===========================================================================
# MANUAL EVALUATION DATASET
# ===========================================================================
# Hand-crafted evaluation questions with expected responses
# These provide high-quality ground truth for evaluation
# REQUIREMENT: At least 5 questions per domain for comprehensive coverage

print("\n" + "=" * 60)
print("CREATING MANUAL EVALUATION DATASET")
print("=" * 60)

MANUAL_EVALS = [
    # ===========================================================================
    # COST DOMAIN (6 questions)
    # ===========================================================================
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
    {
        "inputs": {"messages": [{"role": "user", "content": "What is our serverless vs classic compute cost ratio?"}]},
        "expectations": {
            "expected_domains": ["cost"],
            "expected_facts": [
                "Should break down serverless costs",
                "Should break down classic compute costs",
                "Should show ratio or percentage comparison"
            ]
        },
        "category": "cost",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Show DBU consumption trends over the last 7 days"}]},
        "expectations": {
            "expected_domains": ["cost"],
            "expected_facts": [
                "Should show daily DBU consumption",
                "Should identify trends (increasing/decreasing)",
                "Should cover 7-day timeframe"
            ]
        },
        "category": "cost",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which workspaces have the highest untagged spend?"}]},
        "expectations": {
            "expected_domains": ["cost"],
            "expected_facts": [
                "Should identify workspaces",
                "Should show untagged cost amounts",
                "Should rank by highest untagged spend"
            ]
        },
        "category": "cost",
        "difficulty": "moderate"
    },
    
    # ===========================================================================
    # SECURITY DOMAIN (6 questions)
    # ===========================================================================
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
    {
        "inputs": {"messages": [{"role": "user", "content": "What permissions were changed yesterday?"}]},
        "expectations": {
            "expected_domains": ["security"],
            "expected_facts": [
                "Should list permission changes",
                "Should identify who made changes",
                "Should show what was changed"
            ]
        },
        "category": "security",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Are there any unusual access patterns today?"}]},
        "expectations": {
            "expected_domains": ["security"],
            "expected_facts": [
                "Should identify anomalous activity",
                "Should describe what makes it unusual",
                "Should mention users or resources involved"
            ]
        },
        "category": "security",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which service principals are most active?"}]},
        "expectations": {
            "expected_domains": ["security"],
            "expected_facts": [
                "Should list service principal names",
                "Should show activity counts",
                "Should rank by activity level"
            ]
        },
        "category": "security",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Show audit events for data deletions this week"}]},
        "expectations": {
            "expected_domains": ["security"],
            "expected_facts": [
                "Should filter for delete operations",
                "Should list affected resources",
                "Should identify who performed deletions"
            ]
        },
        "category": "security",
        "difficulty": "moderate"
    },
    
    # ===========================================================================
    # PERFORMANCE DOMAIN (6 questions)
    # ===========================================================================
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
    {
        "inputs": {"messages": [{"role": "user", "content": "Are there any performance regressions this week?"}]},
        "expectations": {
            "expected_domains": ["performance"],
            "expected_facts": [
                "Should compare current vs historical performance",
                "Should identify degraded queries or jobs",
                "Should quantify the regression"
            ]
        },
        "category": "performance",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What is the average query latency by warehouse?"}]},
        "expectations": {
            "expected_domains": ["performance"],
            "expected_facts": [
                "Should group by warehouse",
                "Should show average latency metrics",
                "Should enable comparison across warehouses"
            ]
        },
        "category": "performance",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which jobs are running longer than usual?"}]},
        "expectations": {
            "expected_domains": ["performance"],
            "expected_facts": [
                "Should identify outlier job durations",
                "Should compare to historical baseline",
                "Should list affected jobs"
            ]
        },
        "category": "performance",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Show cluster utilization metrics for the past week"}]},
        "expectations": {
            "expected_domains": ["performance"],
            "expected_facts": [
                "Should show CPU/memory utilization",
                "Should identify over/under-utilized clusters",
                "Should cover 7-day timeframe"
            ]
        },
        "category": "performance",
        "difficulty": "moderate"
    },
    
    # ===========================================================================
    # RELIABILITY DOMAIN (6 questions)
    # ===========================================================================
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
    {
        "inputs": {"messages": [{"role": "user", "content": "What is the job success rate by workspace?"}]},
        "expectations": {
            "expected_domains": ["reliability"],
            "expected_facts": [
                "Should calculate success rates",
                "Should group by workspace",
                "Should enable comparison"
            ]
        },
        "category": "reliability",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Show recurring job failures this week"}]},
        "expectations": {
            "expected_domains": ["reliability"],
            "expected_facts": [
                "Should identify repeatedly failing jobs",
                "Should show failure frequency",
                "Should help prioritize fixes"
            ]
        },
        "category": "reliability",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which jobs have the most retries?"}]},
        "expectations": {
            "expected_domains": ["reliability"],
            "expected_facts": [
                "Should list job names",
                "Should count retries",
                "Should rank by retry count"
            ]
        },
        "category": "reliability",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Are there any jobs with degraded reliability?"}]},
        "expectations": {
            "expected_domains": ["reliability"],
            "expected_facts": [
                "Should compare current vs historical reliability",
                "Should identify degraded jobs",
                "Should quantify the degradation"
            ]
        },
        "category": "reliability",
        "difficulty": "complex"
    },
    
    # ===========================================================================
    # QUALITY DOMAIN (6 questions)
    # ===========================================================================
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
    {
        "inputs": {"messages": [{"role": "user", "content": "Are there any null rate anomalies?"}]},
        "expectations": {
            "expected_domains": ["quality"],
            "expected_facts": [
                "Should identify columns with unexpected nulls",
                "Should compare to baseline null rates",
                "Should flag anomalies"
            ]
        },
        "category": "quality",
        "difficulty": "moderate"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Show data freshness for all monitored tables"}]},
        "expectations": {
            "expected_domains": ["quality"],
            "expected_facts": [
                "Should list all monitored tables",
                "Should show last update times",
                "Should indicate freshness status"
            ]
        },
        "category": "quality",
        "difficulty": "simple"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which columns have schema drift?"}]},
        "expectations": {
            "expected_domains": ["quality"],
            "expected_facts": [
                "Should identify columns with type changes",
                "Should show old vs new schema",
                "Should list affected tables"
            ]
        },
        "category": "quality",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What is our data quality score across domains?"}]},
        "expectations": {
            "expected_domains": ["quality"],
            "expected_facts": [
                "Should provide aggregate quality metrics",
                "Should break down by data domain",
                "Should enable comparison"
            ]
        },
        "category": "quality",
        "difficulty": "moderate"
    },
    
    # ===========================================================================
    # CROSS-DOMAIN (Complex multi-domain questions)
    # ===========================================================================
    # These test the agent's ability to query multiple Genie Spaces in parallel
    # and synthesize results into coherent, actionable insights.
    # ===========================================================================
    
    # COST + RELIABILITY
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
        "inputs": {"messages": [{"role": "user", "content": "How much money are we wasting on failed jobs?"}]},
        "expectations": {
            "expected_domains": ["cost", "reliability"],
            "expected_facts": [
                "Should calculate cost of failed job runs",
                "Should identify highest-waste jobs",
                "Should suggest cost recovery opportunities"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # COST + PERFORMANCE
    {
        "inputs": {"messages": [{"role": "user", "content": "Are slow queries costing us more money?"}]},
        "expectations": {
            "expected_domains": ["cost", "performance"],
            "expected_facts": [
                "Should correlate query duration with cost",
                "Should identify expensive slow queries",
                "Should provide optimization recommendations"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Compare cost efficiency across different warehouse sizes"}]},
        "expectations": {
            "expected_domains": ["cost", "performance"],
            "expected_facts": [
                "Should analyze cost per query by warehouse size",
                "Should compare performance metrics",
                "Should recommend optimal warehouse configuration"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # COST + SECURITY
    {
        "inputs": {"messages": [{"role": "user", "content": "Which service principals are generating the most cost?"}]},
        "expectations": {
            "expected_domains": ["cost", "security"],
            "expected_facts": [
                "Should identify service principals by activity",
                "Should correlate with cost data",
                "Should flag any unauthorized high-cost activity"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # COST + QUALITY
    {
        "inputs": {"messages": [{"role": "user", "content": "Are we spending money processing low-quality data?"}]},
        "expectations": {
            "expected_domains": ["cost", "quality"],
            "expected_facts": [
                "Should identify jobs processing tables with quality issues",
                "Should calculate cost impact of quality problems",
                "Should recommend data quality investments"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # SECURITY + PERFORMANCE
    {
        "inputs": {"messages": [{"role": "user", "content": "Are there any security events correlated with performance degradation?"}]},
        "expectations": {
            "expected_domains": ["security", "performance"],
            "expected_facts": [
                "Should analyze timing of security events",
                "Should correlate with performance metrics",
                "Should identify potential attack patterns"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # SECURITY + RELIABILITY  
    {
        "inputs": {"messages": [{"role": "user", "content": "Are failed jobs related to permission issues?"}]},
        "expectations": {
            "expected_domains": ["security", "reliability"],
            "expected_facts": [
                "Should analyze job failure reasons",
                "Should identify permission-related failures",
                "Should correlate with access control changes"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # PERFORMANCE + RELIABILITY
    {
        "inputs": {"messages": [{"role": "user", "content": "Are timeouts causing job failures?"}]},
        "expectations": {
            "expected_domains": ["performance", "reliability"],
            "expected_facts": [
                "Should identify timeout-related failures",
                "Should analyze job duration patterns",
                "Should recommend timeout adjustments"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What's the relationship between cluster utilization and job success rate?"}]},
        "expectations": {
            "expected_domains": ["performance", "reliability"],
            "expected_facts": [
                "Should correlate utilization with success metrics",
                "Should identify resource contention issues",
                "Should provide capacity recommendations"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # PERFORMANCE + QUALITY
    {
        "inputs": {"messages": [{"role": "user", "content": "What's the relationship between query performance and data quality?"}]},
        "expectations": {
            "expected_domains": ["performance", "quality"],
            "expected_facts": [
                "Should analyze performance on low-quality tables",
                "Should identify quality issues affecting performance",
                "Should provide insights on correlation"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Are queries slower on tables with schema drift?"}]},
        "expectations": {
            "expected_domains": ["performance", "quality"],
            "expected_facts": [
                "Should identify tables with schema changes",
                "Should analyze query performance impact",
                "Should recommend schema management practices"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # RELIABILITY + QUALITY
    {
        "inputs": {"messages": [{"role": "user", "content": "Are pipelines failing due to data quality issues?"}]},
        "expectations": {
            "expected_domains": ["reliability", "quality"],
            "expected_facts": [
                "Should identify quality-related failures",
                "Should correlate with data validation rules",
                "Should recommend data quality improvements"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Which data quality monitors are associated with job failures?"}]},
        "expectations": {
            "expected_domains": ["reliability", "quality"],
            "expected_facts": [
                "Should link monitor alerts to job failures",
                "Should identify critical quality thresholds",
                "Should suggest monitoring improvements"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # ALL DOMAINS - Comprehensive
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
    {
        "inputs": {"messages": [{"role": "user", "content": "Show me a summary of issues requiring immediate attention"}]},
        "expectations": {
            "expected_domains": ["cost", "security", "performance", "reliability", "quality"],
            "expected_facts": [
                "Should prioritize by severity",
                "Should list actionable issues",
                "Should cover multiple domains"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What's the overall health of our Databricks workspace?"}]},
        "expectations": {
            "expected_domains": ["cost", "security", "performance", "reliability", "quality"],
            "expected_facts": [
                "Should provide holistic assessment",
                "Should highlight cross-domain concerns",
                "Should recommend priority actions"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "Compare this week's metrics across all domains vs last week"}]},
        "expectations": {
            "expected_domains": ["cost", "security", "performance", "reliability", "quality"],
            "expected_facts": [
                "Should show week-over-week trends",
                "Should cover all domains",
                "Should identify significant changes"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    
    # CAUSAL/INVESTIGATIVE Cross-Domain
    {
        "inputs": {"messages": [{"role": "user", "content": "Why did costs spike when jobs started failing more?"}]},
        "expectations": {
            "expected_domains": ["cost", "reliability"],
            "expected_facts": [
                "Should establish timeline correlation",
                "Should identify root cause",
                "Should quantify impact"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
    {
        "inputs": {"messages": [{"role": "user", "content": "What's causing our overall platform degradation?"}]},
        "expectations": {
            "expected_domains": ["cost", "performance", "reliability"],
            "expected_facts": [
                "Should analyze multiple signals",
                "Should identify common root causes",
                "Should provide remediation plan"
            ]
        },
        "category": "cross_domain",
        "difficulty": "complex"
    },
]

# Convert to DataFrame
manual_evals_df = pd.DataFrame(MANUAL_EVALS)
print(f"Created {len(manual_evals_df)} manual evaluations")
print(f"  Categories: {list(manual_evals_df['category'].unique())}")
print(f"  Difficulties: {list(manual_evals_df['difficulty'].unique())}")

# COMMAND ----------

# ===========================================================================
# CONVERT TO MLFLOW EVALUATION RECORDS FORMAT
# ===========================================================================

def convert_to_eval_records(df):
    """Convert DataFrame to MLflow GenAI evaluation records format.
    
    Uses "query" as the input key to match:
    - Built-in MLflow scorers (RelevanceToQuery expects inputs.query)
    - Custom scorers in deployment_job.py
    """
    records = []
    columns = df.columns.tolist()
    
    for _, row in df.iterrows():
        # Extract query from nested message format
        query = ""
        inputs_val = row["inputs"] if "inputs" in columns else None
        if isinstance(inputs_val, dict):
            messages = inputs_val.get("messages", [])
            if messages and isinstance(messages[0], dict):
                query = messages[0].get("content", "")
        elif inputs_val:
            query = str(inputs_val)
        
        expectations_val = row["expectations"] if "expectations" in columns else {}
        category_val = row["category"] if "category" in columns else "unknown"
        difficulty_val = row["difficulty"] if "difficulty" in columns else "moderate"
        
        record = {
            "inputs": {
                "query": query,  # CRITICAL: Use "query" not "question"
                "category": category_val,
                "difficulty": difficulty_val,
            },
            "expectations": expectations_val
        }
        records.append(record)
    
    return records

# COMMAND ----------

# ===========================================================================
# CREATE MLFLOW GENAI EVALUATION DATASET
# ===========================================================================

dataset_name = f"{catalog}.{agent_schema}.eval_dataset_manual"

print(f"\n📊 Creating evaluation dataset: {dataset_name}")

# Delete existing dataset to ensure clean state
try:
    mlflow_datasets.delete_dataset(name=dataset_name)
    print(f"  ✓ Deleted existing dataset")
except Exception as e:
    print(f"  No existing dataset found: {str(e)[:100]}")

# Create fresh dataset
print(f"  Creating new dataset...")
dataset = mlflow_datasets.create_dataset(name=dataset_name)
print(f"  ✓ Created dataset: {dataset_name}")

# Convert and add records
records = convert_to_eval_records(manual_evals_df)
print(f"\n  Adding {len(records)} records...")

# Validate records before adding
valid_records = []
for i, r in enumerate(records):
    query = r.get("inputs", {}).get("query", "")
    if query and query.strip():
        valid_records.append(r)
    else:
        print(f"  ⚠ Skipping record {i} with empty query")

if valid_records:
    dataset.merge_records(valid_records)
    print(f"  ✓ Added {len(valid_records)} records")
else:
    print(f"  ⚠ WARNING: No valid records!")

# COMMAND ----------

# ===========================================================================
# SUMMARY
# ===========================================================================

print("\n" + "=" * 70)
print("EVALUATION DATASET CREATION COMPLETE")
print("=" * 70)

print(f"\n📊 Dataset: {dataset_name}")
print(f"   Records: {len(valid_records)}")
print(f"   Categories: {list(manual_evals_df['category'].unique())}")
print(f"   Questions per domain:")
for cat in manual_evals_df['category'].unique():
    count = len(manual_evals_df[manual_evals_df['category'] == cat])
    print(f"     • {cat}: {count}")

print(f"\n✨ Dataset visible in MLflow UI:")
print(f"   Experiment: {experiment_path}")
print(f"   → Navigate to Experiment → Datasets tab")

print("\n" + "=" * 70)

# Return success
dbutils.notebook.exit("SUCCESS")
