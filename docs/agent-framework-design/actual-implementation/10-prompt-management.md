# 10. Prompt Management

## Overview

This document covers the **MLflow Prompt Registry** integration for managing, versioning, and deploying prompts in the Health Monitor Agent. Proper prompt registration is essential for:

- **Version Control**: Track prompt changes over time
- **A/B Testing**: Compare prompt variants
- **Audit Trail**: Know which prompt version was used for each inference
- **Production Safety**: Promote prompts through staging to production
- **Trace Linking**: Automatically link prompts to MLflow traces

---

## 📍 File Locations

| File | Purpose |
|------|---------|
| `src/agents/setup/register_prompts.py` | Registers all prompts to MLflow Registry |
| `src/agents/prompts/orchestrator.py` | Orchestrator prompt templates |
| `src/agents/prompts/workers.py` | Domain worker prompt templates |
| `src/agents/setup/log_agent_model.py` | Loads prompts in traced functions |
| `resources/agents/agent_setup_job.yml` | Job that runs prompt registration |

---

## 🔑 Key Pattern: MLflow Prompt Registry

### The Problem with Traditional Approaches

❌ **Old Pattern (Delta Table Storage)**:
```python
# Stored prompts in Delta table - NOT visible in MLflow UI
prompts_data = [{"name": "orchestrator", "template": "..."}]
df = spark.createDataFrame(prompts_data)
df.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.agent_prompts")

# Also logged as artifacts - still NOT in Prompt Registry
mlflow.log_text(template, f"prompts/{name}.txt")
```

**Problems:**
- Prompts don't appear in MLflow Prompt Registry UI
- No version tracking through MLflow
- No alias support (staging/production)
- No automatic trace linking

---

### ✅ Correct Pattern: `mlflow.genai.register_prompt()`

**Reference:** [MLflow Prompt Registry Documentation](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/)

```python
import mlflow.genai

# Register prompt to MLflow Prompt Registry
prompt_info = mlflow.genai.register_prompt(
    name=f"{catalog}.{schema}.prompt_{prompt_name}",  # Unity Catalog path
    template=template_string,                          # The prompt template
)

# Set aliases for deployment stages
mlflow.genai.set_prompt_alias(
    name=f"{catalog}.{schema}.prompt_{prompt_name}",
    alias="production",
    version=prompt_info.version
)

mlflow.genai.set_prompt_alias(
    name=f"{catalog}.{schema}.prompt_{prompt_name}",
    alias="staging",
    version=prompt_info.version
)
```

**Benefits:**
- ✅ Prompts appear in MLflow Prompt Registry UI
- ✅ Full version history
- ✅ Alias support (production, staging, latest)
- ✅ Automatic trace linking when loaded in traced functions

---

## 📝 Complete Prompt Registration Script

**File:** `src/agents/setup/register_prompts.py`

```python
# Databricks notebook source
"""
Register Prompts to MLflow Prompt Registry

This script registers all agent prompts to the MLflow Prompt Registry,
making them visible in the MLflow UI and enabling:
- Version tracking
- Alias management (production, staging)
- Trace linking when loaded in predict()

Reference: https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/
"""

# COMMAND ----------

import mlflow
import mlflow.genai
from mlflow import MlflowClient

# COMMAND ----------

# Get parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"Registering prompts to: {catalog}.{agent_schema}")

# COMMAND ----------

# Define all prompts
PROMPTS = {
    "orchestrator": """You are the Databricks Health Monitor orchestrator.

Your role is to analyze user queries about their Databricks platform and coordinate
domain-specific workers to provide comprehensive insights.

## Capabilities
- Route queries to specialized domain agents (cost, security, performance, reliability, quality)
- Synthesize responses from multiple domains
- Provide actionable recommendations

## Response Guidelines
1. Always include time context (e.g., "today", "this week", "last 30 days")
2. Format monetary values as USD with appropriate precision
3. Cite specific data sources when available
4. Provide clear next steps or recommendations

User Query: {query}
Context: {context}""",

    "intent_classifier": """Classify the user's intent into one or more domains.

Domains:
- cost: DBU usage, billing, budgets, spend optimization
- security: Access control, audit logs, permissions, compliance
- performance: Query performance, cluster utilization, cache hits
- reliability: Job failures, SLA compliance, pipeline health
- quality: Data freshness, schema changes, data quality rules

User Query: {query}

Respond with a JSON object:
{{"domains": ["domain1", "domain2"], "confidence": 0.95, "reasoning": "..."}}""",

    "synthesizer": """Synthesize the following domain responses into a coherent answer.

User Query: {query}
Domain Responses:
{domain_responses}

Guidelines:
1. Combine insights from all domains coherently
2. Highlight the most important findings first
3. Note any conflicts between domain responses
4. Provide unified recommendations
5. Keep the response concise but comprehensive""",

    "cost_worker": """You are a cost analysis specialist for Databricks.

Analyze DBU consumption, billing trends, and cost optimization opportunities.

Key metrics to consider:
- DBU usage by workspace, cluster, job
- Cost trends over time (daily, weekly, monthly)
- Budget vs actual spend
- Serverless vs classic compute costs
- Tag coverage for cost attribution

Query: {query}
Data: {data}""",

    "security_worker": """You are a security and compliance specialist for Databricks.

Analyze audit logs, access patterns, and security events.

Key areas:
- Failed login attempts
- Permission changes
- Sensitive data access
- Security policy violations
- User activity patterns

Query: {query}
Data: {data}""",

    "performance_worker": """You are a performance optimization specialist for Databricks.

Analyze query performance, cluster utilization, and optimization opportunities.

Key metrics:
- Query execution times (p50, p95, p99)
- Cluster utilization rates
- Cache hit ratios
- Photon usage
- Auto-scaling efficiency

Query: {query}
Data: {data}""",

    "reliability_worker": """You are a reliability and operations specialist for Databricks.

Analyze job health, pipeline reliability, and SLA compliance.

Key metrics:
- Job success/failure rates
- Pipeline execution times
- SLA compliance percentages
- Error patterns and trends
- Recovery time statistics

Query: {query}
Data: {data}""",

    "quality_worker": """You are a data quality specialist for Databricks.

Analyze data freshness, schema health, and quality metrics.

Key areas:
- Data freshness by table/schema
- Schema changes and drift
- Null rates and anomalies
- Data quality rule violations
- Lineage health

Query: {query}
Data: {data}""",
}

# COMMAND ----------

def register_all_prompts(catalog: str, schema: str) -> dict:
    """
    Register all prompts to MLflow Prompt Registry.
    
    Returns:
        Dict mapping prompt names to their registered versions
    """
    registered = {}
    client = MlflowClient()
    
    for prompt_name, template in PROMPTS.items():
        try:
            # Full prompt name in Unity Catalog format
            full_name = f"{catalog}.{schema}.prompt_{prompt_name}"
            
            print(f"\n{'='*60}")
            print(f"Registering: {prompt_name}")
            print(f"  Full name: {full_name}")
            
            # Register to MLflow Prompt Registry
            # This is the KEY API that makes prompts visible in the UI
            prompt_info = mlflow.genai.register_prompt(
                name=full_name,
                template=template,
            )
            
            version = prompt_info.version
            print(f"  ✓ Registered as version {version}")
            
            # Set production alias
            try:
                mlflow.genai.set_prompt_alias(
                    name=full_name,
                    alias="production",
                    version=version
                )
                print(f"  ✓ Set 'production' alias → v{version}")
            except Exception as alias_err:
                print(f"  ⚠ Could not set production alias: {alias_err}")
            
            # Set staging alias
            try:
                mlflow.genai.set_prompt_alias(
                    name=full_name,
                    alias="staging",
                    version=version
                )
                print(f"  ✓ Set 'staging' alias → v{version}")
            except Exception as alias_err:
                print(f"  ⚠ Could not set staging alias: {alias_err}")
            
            registered[prompt_name] = {
                "full_name": full_name,
                "version": version,
                "aliases": ["production", "staging"]
            }
            
        except Exception as e:
            print(f"  ✗ Error registering {prompt_name}: {e}")
            registered[prompt_name] = {"error": str(e)}
    
    return registered

# COMMAND ----------

# Main execution
results = register_all_prompts(catalog, agent_schema)

# Summary
print("\n" + "="*70)
print("PROMPT REGISTRATION SUMMARY")
print("="*70)

success_count = sum(1 for r in results.values() if "version" in r)
error_count = sum(1 for r in results.values() if "error" in r)

print(f"\n✓ Successfully registered: {success_count}")
print(f"✗ Errors: {error_count}")

print("\nRegistered prompts:")
for name, info in results.items():
    if "version" in info:
        print(f"  • {name}: v{info['version']} (aliases: {info['aliases']})")
    else:
        print(f"  • {name}: ERROR - {info.get('error', 'Unknown')}")

print("\n" + "="*70)
print("View prompts at: MLflow UI → Prompt Registry")
print("="*70)

dbutils.notebook.exit("SUCCESS")
```

---

## 🔗 Loading Prompts in Traced Functions

### Why Load Inside Traced Functions?

When you load a prompt using `mlflow.genai.load_prompt()` **inside** a traced function, MLflow automatically:
1. Records which prompt version was used
2. Links the prompt to the trace in the UI
3. Enables prompt → trace navigation

### Implementation Pattern

**File:** `src/agents/setup/log_agent_model.py` (inside `predict` method)

```python
def predict(self, context, model_input):
    """ChatAgent predict method with prompt-trace linking."""
    
    # Get catalog/schema from environment (set by serving endpoint)
    _catalog = os.environ.get("AGENT_CATALOG", "prashanth_subrahmanyam_catalog")
    _schema = os.environ.get("AGENT_SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
    
    with mlflow.start_span(name="agent_predict", span_type="AGENT") as span:
        # ═══════════════════════════════════════════════════════════════
        # CRITICAL: Load prompts INSIDE the traced function
        # This creates the prompt-trace link in MLflow UI
        # ═══════════════════════════════════════════════════════════════
        prompts = {}
        prompt_names = ["orchestrator", "intent_classifier", "synthesizer",
                        "cost_worker", "security_worker", "performance_worker",
                        "reliability_worker", "quality_worker"]
        
        for prompt_name in prompt_names:
            try:
                # Load from MLflow Prompt Registry using @production alias
                prompt_uri = f"prompts:/{_catalog}.{_schema}.prompt_{prompt_name}@production"
                loaded_prompt = mlflow.genai.load_prompt(prompt_uri)
                prompts[prompt_name] = loaded_prompt.template
            except Exception as e:
                # Fallback to default if registry fails
                prompts[prompt_name] = f"Default prompt for {prompt_name}"
                print(f"⚠ Could not load prompt {prompt_name}: {e}")
        
        # Tag trace with prompt info
        mlflow.update_current_trace(tags={
            "prompts_loaded": ",".join(prompt_names),
            "prompt_catalog": _catalog,
            "prompt_schema": _schema,
        })
        
        # ... rest of predict logic using prompts["orchestrator"], etc.
```

### Prompt URI Formats

| Format | Description | Example |
|--------|-------------|---------|
| `prompts:/{name}@latest` | Latest version | `prompts:/catalog.schema.prompt_orchestrator@latest` |
| `prompts:/{name}@production` | Production alias | `prompts:/catalog.schema.prompt_orchestrator@production` |
| `prompts:/{name}@staging` | Staging alias | `prompts:/catalog.schema.prompt_orchestrator@staging` |
| `prompts:/{name}/{version}` | Specific version | `prompts:/catalog.schema.prompt_orchestrator/3` |

---

## 🏷️ Prompt Aliasing Strategy

### Recommended Workflow

```
Developer creates new prompt
         │
         ▼
    Register (creates new version)
         │
         ▼
    Set @staging alias
         │
         ▼
    Test in staging environment
         │
         ▼
    Promote @staging → @production
         │
         ▼
    Production uses @production alias
```

### Alias Management Code

```python
from mlflow import MlflowClient

client = MlflowClient()
prompt_name = f"{catalog}.{schema}.prompt_orchestrator"

# Get all versions
versions = client.search_model_versions(f"name='{prompt_name}'")
for v in versions:
    print(f"Version {v.version}: aliases={v.aliases}")

# Promote staging to production
# 1. Get current staging version
staging_info = mlflow.genai.load_prompt(f"prompts:/{prompt_name}@staging")
staging_version = staging_info.version

# 2. Update production alias
mlflow.genai.set_prompt_alias(
    name=prompt_name,
    alias="production",
    version=staging_version
)

print(f"Promoted v{staging_version} to production")
```

---

## 📊 Viewing Prompts in MLflow UI

### Navigation Path

1. Open Databricks workspace
2. Go to **Machine Learning** → **MLflow**
3. Click on **Prompt Registry** tab (or **Models** → filter by prompts)
4. Find prompts under your catalog/schema

### What You'll See

| Column | Description |
|--------|-------------|
| **Name** | `catalog.schema.prompt_name` |
| **Latest Version** | Current highest version number |
| **Aliases** | `production`, `staging`, etc. |
| **Created** | Timestamp of registration |

### Version Details

Click on a prompt to see:
- Full template text
- Variables (e.g., `{query}`, `{context}`)
- Version history
- Linked traces (if loaded in traced functions)

---

## ⚠️ Common Mistakes

### ❌ Mistake 1: Storing in Delta Table Instead of Registry

```python
# WRONG: Prompts won't appear in MLflow UI
df = spark.createDataFrame([{"name": "orchestrator", "template": "..."}])
df.write.saveAsTable(f"{catalog}.{schema}.agent_prompts")
```

**Fix:** Use `mlflow.genai.register_prompt()`

### ❌ Mistake 2: Loading Prompts Outside Traced Function

```python
# WRONG: No trace linking
prompt = mlflow.genai.load_prompt("prompts:/...@production")  # Outside trace

@mlflow.trace
def my_function():
    # prompt already loaded, no link created
    use_prompt(prompt)
```

**Fix:** Load inside the traced function

```python
@mlflow.trace
def my_function():
    # CORRECT: Load inside traced function
    prompt = mlflow.genai.load_prompt("prompts:/...@production")
    use_prompt(prompt)
```

### ❌ Mistake 3: Hardcoding Prompt Versions

```python
# WRONG: Hardcoded version
prompt = mlflow.genai.load_prompt("prompts:/catalog.schema.prompt_orchestrator/3")
```

**Fix:** Use aliases for flexibility

```python
# CORRECT: Use alias
prompt = mlflow.genai.load_prompt("prompts:/catalog.schema.prompt_orchestrator@production")
```

---

## ✅ Validation Checklist

### Prompt Registration
- [ ] All prompts registered using `mlflow.genai.register_prompt()`
- [ ] Prompts use Unity Catalog path format: `{catalog}.{schema}.prompt_{name}`
- [ ] `production` alias set for each prompt
- [ ] `staging` alias set for each prompt
- [ ] Prompts visible in MLflow Prompt Registry UI

### Prompt Loading
- [ ] Prompts loaded using `mlflow.genai.load_prompt()` inside traced functions
- [ ] Using `@production` alias in production code
- [ ] Fallback handling if prompt load fails
- [ ] Trace tags include prompt metadata

### Deployment
- [ ] `register_prompts` task in setup job
- [ ] Prompts registered before model logging
- [ ] Environment variables set for catalog/schema in serving endpoint

---

## 🔗 References

- [MLflow Prompt Registry](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/)
- [Register Prompts](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/register/)
- [Load Prompts](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/load/)
- [Prompt Aliases](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/alias/)

---

**Previous:** [09-deployment-pipeline.md](./09-deployment-pipeline.md)  
**Index:** [00-index.md](./00-index.md)


