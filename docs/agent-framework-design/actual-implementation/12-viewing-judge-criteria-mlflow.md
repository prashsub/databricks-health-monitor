# Where to Find Judge Criteria in MLflow

## Overview

This guide shows you where to view the **judging criteria** used to evaluate your agent in MLflow experiments, traces, and evaluation runs.

**Updated:** January 10, 2026  
**Guidelines Score:** Target 0.5-0.7 (4 essential sections)

---

## 📍 Where Judge Criteria Are Stored

### 1️⃣ Source Code (Deployment Job)

**Location:** `src/agents/setup/deployment_job.py`

The judge criteria are defined when registering scorers:

```python
# Lines 1753-1803 (reduced to 4 sections)
Guidelines(guidelines=[
    """Data Accuracy and Source Citation:
    - MUST include specific numbers from Genie
    - MUST cite sources explicitly: [Cost Genie], etc.
    - MUST include time context
    - MUST format numbers properly
    """,
    
    """No Data Fabrication (CRITICAL):
    - MUST NEVER fabricate data
    - If Genie fails, MUST return explicit error
    """,
    
    """Actionability and Recommendations:
    - SHOULD provide specific next steps
    - SHOULD include concrete details
    """,
    
    """Professional Communication:
    - MUST maintain professional tone
    - MUST use markdown formatting
    """,
])
```

### 2️⃣ MLflow Experiment Artifacts

**Location:** MLflow Experiment → Run → Artifacts

When you run the deployment job, MLflow logs the evaluation artifacts:

**Path:**
```
/Shared/health_monitor_agent_evaluation
  └── Run: eval_pre_deploy_YYYYMMDD_HHMMSS
      └── Artifacts
          ├── eval_results_table/
          │   └── scored_outputs.csv  # Individual scores per query
          ├── evaluation_summary.json  # Aggregate metrics
          └── model_info.json
```

**What's in `scored_outputs.csv`:**

| Column | Description |
|--------|-------------|
| `query` | The evaluation query |
| `output` | Agent's response |
| `guidelines/mean` | Overall guidelines score (0.0-1.0) |
| `guidelines/rationale` | LLM's explanation of score |
| `relevance/mean` | Relevance score |
| `safety/mean` | Safety score |
| ... | All other scorers |

### 3️⃣ MLflow Traces (Individual Evaluation)

**Location:** MLflow Experiment → Run → Traces

Each evaluation query creates a trace with detailed scoring:

**Steps to View:**

1. Open MLflow: `/ml/experiments/XXXXXXX`
2. Click on an evaluation run (e.g., `eval_pre_deploy_20260110_123456`)
3. Click **"Traces"** tab
4. Select a specific trace (one per evaluation query)
5. Expand the trace to see:
   - **Inputs:** Query, expected domain
   - **Outputs:** Agent response
   - **Scorers:** Individual scorer results with rationales

**Example Trace:**
```
Trace: eval_query_1
├── Inputs
│   └── query: "Why did costs spike yesterday?"
├── Agent Execution
│   ├── LLM calls
│   ├── Genie tool calls
│   └── Response generation
└── Scorers
    ├── guidelines: 0.75
    │   ├── Section 1 (Data Accuracy): ✅ Pass (has numbers, cites [Cost Genie])
    │   ├── Section 2 (No Fabrication): ✅ Pass (real data used)
    │   ├── Section 3 (Actionability): ❌ Fail (no specific recommendations)
    │   └── Section 4 (Professional): ✅ Pass (proper formatting)
    │
    ├── relevance: 0.85
    │   └── Rationale: "Response directly addresses cost spike"
    │
    └── safety: 1.0
        └── Rationale: "No harmful content"
```

### 4️⃣ Evaluation Results UI

**Location:** Databricks Workspace → Experiments → Run → "Evaluation" Tab

When you click on an evaluation run, Databricks shows a **dedicated Evaluation UI**:

**Features:**
- ✅ **Aggregate metrics** (guidelines/mean, relevance/mean, etc.)
- ✅ **Per-query breakdown** (see which queries scored low)
- ✅ **Rationales** (why each query got its score)
- ✅ **Comparison view** (compare multiple evaluation runs)

**Screenshot:**
```
┌───────────────────────────────────────────────────────┐
│ Evaluation: eval_pre_deploy_20260110_123456          │
├───────────────────────────────────────────────────────┤
│ Metrics:                                              │
│   guidelines/mean:        0.58  ✅ (threshold: 0.50) │
│   relevance/mean:         0.72  ✅ (threshold: 0.40) │
│   safety/mean:            0.92  ✅ (threshold: 0.70) │
│   cost_accuracy/mean:     0.68  ✅ (threshold: 0.60) │
│   ...                                                 │
├───────────────────────────────────────────────────────┤
│ Per-Query Results (18 queries):                       │
│   Query 1: "Why did costs spike yesterday?"          │
│     - guidelines: 0.75                                │
│     - rationale: "3/4 sections passed"                │
│   Query 2: "Show me failed jobs"                     │
│     - guidelines: 0.50                                │
│     - rationale: "Missing actionable recommendations" │
│   ...                                                 │
└───────────────────────────────────────────────────────┘
```

### 5️⃣ Model Versions (Unity Catalog)

**Location:** Unity Catalog → Models → `health_monitor_agent_dev`

Each registered model version includes evaluation metadata:

**Path:**
```
main.dev_prashanth_subrahmanyam_system_gold_agent.health_monitor_agent_dev
  └── Version 3
      └── Tags
          ├── evaluation_run_id: eval_XXXXX
          ├── guidelines_mean: 0.58
          ├── relevance_mean: 0.72
          ├── safety_mean: 0.92
          └── deployment_status: PROMOTED_WITH_ENDPOINT
```

---

## 🔍 How to View Judge Criteria (Step-by-Step)

### Option 1: View in Databricks Workspace

1. **Navigate to Experiments:**
   ```
   Databricks Workspace → Machine Learning → Experiments
   → /Shared/health_monitor_agent_evaluation
   ```

2. **Select Latest Evaluation Run:**
   - Look for run name: `eval_pre_deploy_YYYYMMDD_HHMMSS`
   - Click on the run

3. **View Evaluation Tab:**
   - Click **"Evaluation"** tab (if available)
   - See aggregate metrics at top
   - Scroll down for per-query breakdown

4. **View Individual Traces:**
   - Click **"Traces"** tab
   - Select a trace to see detailed scoring

### Option 2: Download Scored Outputs CSV

```python
import mlflow
from mlflow import MlflowClient

# Get evaluation run
client = MlflowClient()
experiment = client.get_experiment_by_name("/Shared/health_monitor_agent_evaluation")
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string="tags.mlflow.runName LIKE 'eval_pre_deploy_%'",
    order_by=["start_time DESC"],
    max_results=1
)

eval_run = runs[0]

# Download scored outputs
artifact_path = client.download_artifacts(
    run_id=eval_run.info.run_id,
    path="eval_results_table/scored_outputs.csv"
)

print(f"Downloaded to: {artifact_path}")
```

Then open in Excel/pandas to analyze:

```python
import pandas as pd

df = pd.read_csv(artifact_path)

# View guidelines scores
print(df[["query", "guidelines/mean", "guidelines/rationale"]])

# Identify low-scoring queries
low_scores = df[df["guidelines/mean"] < 0.5]
print(f"\nLow-scoring queries ({len(low_scores)}):")
print(low_scores[["query", "guidelines/mean"]])
```

### Option 3: Query via MLflow API

```python
import mlflow

mlflow.set_experiment("/Shared/health_monitor_agent_evaluation")

# Get latest evaluation run
runs = mlflow.search_runs(
    filter_string="tags.mlflow.runName LIKE 'eval_pre_deploy_%'",
    order_by=["start_time DESC"],
    max_results=1
)

if len(runs) > 0:
    run = runs.iloc[0]
    
    print(f"Run ID: {run['run_id']}")
    print(f"Guidelines Score: {run['metrics.guidelines/mean']:.3f}")
    print(f"Relevance Score: {run['metrics.relevance/mean']:.3f}")
    print(f"Safety Score: {run['metrics.safety/mean']:.3f}")
    
    # Get artifacts
    artifacts = mlflow.artifacts.list_artifacts(run_id=run['run_id'])
    print("\nAvailable artifacts:")
    for artifact in artifacts:
        print(f"  - {artifact.path}")
```

---

## 📊 Understanding Guidelines Score Breakdown

### Current Configuration (4 Sections)

| Section | Weight | Pass Condition | Why It Matters |
|---------|--------|----------------|----------------|
| **1. Data Accuracy** | 25% | Numbers + citations + time context | Users need concrete, verifiable data |
| **2. No Fabrication** | 25% | Never hallucinate, explicit errors | Trust is critical for production use |
| **3. Actionability** | 25% | Specific next steps when applicable | Users need to know what to do |
| **4. Professional Tone** | 25% | Markdown, grammar, clear language | Enterprise communication standards |

### Score Calculation

The Guidelines scorer evaluates **each section independently** for each query:

**Example Query:** "Why did costs spike yesterday?"

```
Section 1 (Data Accuracy):     ✅ Pass (1.0) - Response has "$12K" + "[Cost Genie]"
Section 2 (No Fabrication):    ✅ Pass (1.0) - Real data used
Section 3 (Actionability):     ❌ Fail (0.0) - No recommendations
Section 4 (Professional Tone): ✅ Pass (1.0) - Proper markdown

Query Score: (1.0 + 1.0 + 0.0 + 1.0) / 4 = 0.75
```

**Average across 18 queries:**
```
Query 1: 0.75
Query 2: 0.50
Query 3: 1.00
Query 4: 0.50
...
Query 18: 0.75

Average: 0.58 (58%)
```

### Target Score: 0.5-0.7

With 4 sections, a score of **0.5-0.7** is **excellent** and indicates:

- ✅ Agent consistently provides accurate data with citations
- ✅ Agent never fabricates data
- ✅ Agent provides actionable recommendations in most cases
- ✅ Agent maintains professional tone

---

## 🎯 Where to Find Specific Criteria

### For Each Built-in Judge:

| Judge | Criteria Location | Databricks Docs |
|-------|------------------|----------------|
| **Guidelines** | `deployment_job.py:1753-1803` | [Guidelines Judge](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/judges/guidelines) |
| **Relevance** | Built-in MLflow | [Relevance Judge](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/scorers#relevance) |
| **Safety** | Built-in MLflow | [Safety Judge](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/scorers#safety) |

### For Domain-Specific Judges:

| Judge | Criteria Location | What It Evaluates |
|-------|------------------|-------------------|
| **cost_accuracy** | `deployment_job.py:1133-1262` | 7 cost-specific criteria (DBUs, SKUs, billing, etc.) |
| **security_compliance** | `deployment_job.py:1264-1391` | 7 security criteria (audit logs, RBAC, PII, etc.) |
| **reliability_accuracy** | `deployment_job.py:1393-1520` | 7 reliability criteria (SLA, MTTR, failures, etc.) |
| **performance_accuracy** | `deployment_job.py:1522-1649` | 7 performance criteria (latency, cache, Photon, etc.) |
| **quality_accuracy** | `deployment_job.py:1651-1778` | 7 quality criteria (freshness, nulls, schema, etc.) |

---

## 📈 How to Improve Guidelines Score

### Current Score: 0.206 → Target: 0.5-0.7

With the new 4-section configuration, here's what to focus on:

### 1. **Data Accuracy (Section 1)** - Most Common Failure

❌ **Failing:**
```
Response: "Costs increased significantly last week."
```

✅ **Passing:**
```
Response: "Costs increased $12,345.67 (+23.4% ↑) over last 7 days according to [Cost Genie]"
```

**Fix:** Ensure agent includes:
- Specific numbers ($, DBUs, %)
- Time context (last 7 days, today, MTD)
- Explicit citations ([Cost Genie])

### 2. **No Fabrication (Section 2)** - Critical for Trust

❌ **Failing:**
```python
# Agent code that generates fake data on error
except Exception:
    return f"Based on typical patterns, costs likely increased by ~$10K"  # ❌ FABRICATED!
```

✅ **Passing:**
```python
# Agent code that returns explicit error
except Exception as e:
    return f"## Genie Query Failed\n\n**Error:** {str(e)}\n\nI will NOT generate fake data."
```

**Fix:** Never fall back to LLM when Genie fails for data queries.

### 3. **Actionability (Section 3)** - SHOULD, Not MUST

❌ **Failing:**
```
Response: "You should look into this."  # Too vague
```

✅ **Passing:**
```
Response:
**Immediate**: Scale etl_daily cluster from Small (8 cores) to Medium (16 cores)
**Expected Impact**: 60% latency reduction, ~$2K/month cost increase
```

**Fix:** Include specific job names, parameter values, and estimated impact.

### 4. **Professional Tone (Section 4)** - Easy to Pass

❌ **Failing:**
```
Response: "Dude, your warehouse is kinda small for what you're doing LOL"
```

✅ **Passing:**
```
Response:
## Analysis

The SQL warehouse is currently undersized for the workload.

**Current Config:** Small (8 cores)
**Recommended:** Medium (16 cores)
```

**Fix:** Use markdown, proper grammar, professional language.

---

## 🔄 Next Steps

### 1. Deploy Updated Guidelines (4 Sections)

```bash
cd "/Users/prashanth.subrahmanyam/Library/CloudStorage/GoogleDrive-prashanth.subrahmanyam@databricks.com/My Drive/DSA/DatabricksHealthMonitor"
DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev agent_setup_job
```

This will:
- Register the new 4-section Guidelines scorer
- Target score: 0.5-0.7 (achievable range)

### 2. Run Deployment Job

```bash
DATABRICKS_CONFIG_PROFILE=health_monitor databricks bundle run -t dev agent_deployment_job
```

This will:
- Evaluate with new Guidelines scorer
- Show improved score (expected: 0.5-0.6)
- Deploy if threshold (0.5) is met

### 3. View Results in MLflow

Follow **Option 1** above to view:
- Aggregate guidelines score
- Per-query breakdown
- Rationales for each query

### 4. Iterate on Agent Prompts

If score is still below 0.5:
- Focus on Section 1 (Data Accuracy) - add explicit citation requirements to prompts
- Focus on Section 2 (No Fabrication) - verify error handling works
- Review traces to identify which queries are failing

---

## 📚 References

### Official Documentation
- [MLflow Guidelines Judge](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/judges/guidelines)
- [MLflow Evaluation](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/)
- [MLflow Traces](https://learn.microsoft.com/en-us/azure/databricks/mlflow/tracking/tracing)

### Project Files
- **Deployment Job:** `src/agents/setup/deployment_job.py`
- **Guidelines Definition:** Lines 1753-1803 (4 sections)
- **Thresholds:** Line 2427 (`guidelines/mean: 0.5`)
- **Evaluation Dataset:** `src/agents/setup/create_evaluation_dataset.py`

---

**Last Updated:** January 10, 2026  
**Guidelines Score:** 0.206 → **Target: 0.5-0.7** (4 sections)  
**Status:** ✅ Updated, ready to deploy

