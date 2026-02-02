# GenAI Agent Development Standards

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | ML-05 through ML-08 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | ML Engineering Team |
| **Status** | Approved |

---

## Executive Summary

This document defines standards for building production GenAI agents on Databricks, including agent implementation patterns, memory management with Lakebase, prompt versioning, evaluation frameworks, and authentication patterns for Model Serving.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| ML-05 | Agent must inherit from `ResponsesAgent` | 🔴 Critical |
| ML-06 | OBO authentication requires context detection | 🔴 Critical |
| ML-07 | Genie Space resources must be declared | 🔴 Critical |
| ML-08 | Evaluation thresholds required before production | 🟡 Required |
| ML-09 | Dual-layer memory (short-term + long-term) | 🟡 Required |
| ML-10 | Prompts in Unity Catalog with MLflow versioning | 🟡 Required |

---

## Rule ML-05: ResponsesAgent Pattern

### Why ResponsesAgent?

Agents MUST inherit from `mlflow.pyfunc.ResponsesAgent` for:
- AI Playground compatibility
- Proper request/response handling
- MLflow tracing integration
- Model Serving deployment

### Standard Agent Implementation

```python
from typing import Any, Generator, Optional
import mlflow
from mlflow.pyfunc import ResponsesAgent
from databricks.sdk import WorkspaceClient


class DataPlatformAgent(ResponsesAgent["DataPlatformAgent"]):
    """
    Production agent following ResponsesAgent pattern.
    
    CRITICAL: Do NOT add signature parameter to mlflow.pyfunc.log_model()
    """
    
    def __init__(self):
        """Initialize agent with tools and LLM."""
        self.w = WorkspaceClient()
        self._setup_tools()
        self._setup_memory()
    
    def _setup_tools(self):
        """Initialize Genie and other tools."""
        from databricks_langchain import ChatDatabricks
        from langchain_community.tools.databricks import GenieAgent
        
        self.llm = ChatDatabricks(
            endpoint="databricks-meta-llama-3-1-70b-instruct",
            temperature=0.1
        )
        
        # Genie tool for each domain
        self.genie_tools = {}
        for domain, space_id in GENIE_SPACES.items():
            self.genie_tools[domain] = GenieAgent(
                genie_space_id=space_id,
                genie_agent_name=f"{domain}_analytics"
            )
    
    def _setup_memory(self):
        """Initialize Lakebase memory."""
        try:
            from databricks_langchain import DatabricksStore, CheckpointSaver
            
            self.short_term = CheckpointSaver.from_credentials(
                catalog=CATALOG, schema=SCHEMA, table_name="checkpoints"
            )
            self.long_term = DatabricksStore.from_credentials(
                catalog=CATALOG, schema=SCHEMA, table_name="preferences"
            )
        except Exception as e:
            print(f"⚠ Memory unavailable: {e}")
            self.short_term = None
            self.long_term = None
    
    @mlflow.trace(span_type="AGENT")
    def predict(
        self,
        context,
        model_input: dict[str, Any],
        params: Optional[dict[str, Any]] = None
    ) -> dict:
        """
        Main prediction method called by Model Serving.
        
        CRITICAL: Return format must include 'content' key.
        """
        messages = model_input.get("messages", [])
        custom_inputs = model_input.get("custom_inputs", {})
        
        user_id = custom_inputs.get("user_id", "anonymous")
        thread_id = custom_inputs.get("thread_id", str(uuid.uuid4()))
        
        # Process with memory context
        response = self._process_with_memory(messages, user_id, thread_id)
        
        return {
            "content": response,
            "custom_outputs": {
                "thread_id": thread_id,  # Return for conversation continuity
                "user_id": user_id
            }
        }
    
    def predict_stream(
        self,
        context,
        model_input: dict[str, Any],
        params: Optional[dict[str, Any]] = None
    ) -> Generator[dict, None, None]:
        """Streaming prediction for real-time responses."""
        # Stream implementation
        pass
```

### Logging the Agent Model

```python
def log_agent_model(agent_class, resources, auth_policy):
    """
    Log agent model to MLflow.
    
    CRITICAL: Do NOT pass signature parameter.
    """
    with mlflow.start_run(run_name="agent_deployment"):
        mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=agent_class(),
            pip_requirements=[
                "mlflow>=2.17.1",
                "databricks-langchain>=0.1.0",
                "databricks-sdk>=0.30.0",
                "langgraph>=0.2.0"
            ],
            resources=resources,        # ✅ Required for auth
            auth_policy=auth_policy,    # ✅ Required for auth
            # signature=...             # ❌ DO NOT include
        )
```

---

## Rule ML-06: OBO Authentication Context Detection

### The Problem

On-Behalf-Of (OBO) authentication using `ModelServingUserCredentials` ONLY works in Model Serving. Using it in evaluation or notebooks causes permission errors.

### Context Detection Pattern

```python
import os
from databricks.sdk import WorkspaceClient


def is_model_serving_context() -> bool:
    """
    Detect if running in Model Serving environment.
    
    CRITICAL: OBO only works in Model Serving.
    """
    indicators = [
        "IS_IN_DB_MODEL_SERVING_ENV",
        "DATABRICKS_SERVING_ENDPOINT",
        "MLFLOW_DEPLOYMENT_FLAVOR_NAME"
    ]
    return any(os.environ.get(var) for var in indicators)


def get_workspace_client() -> WorkspaceClient:
    """
    Get WorkspaceClient with context-appropriate authentication.
    """
    if is_model_serving_context():
        # OBO: Use end-user credentials in production
        from databricks.sdk.credentials import ModelServingUserCredentials
        return WorkspaceClient(credentials_strategy=ModelServingUserCredentials())
    else:
        # Default: Use service principal/PAT in dev/eval
        return WorkspaceClient()


# Usage in agent
class DataPlatformAgent(ResponsesAgent):
    def __init__(self):
        self.w = get_workspace_client()  # ✅ Context-aware auth
```

### Authentication Behavior Table

| Context | Auth Method | Credentials |
|---------|-------------|-------------|
| Model Serving | OBO (ModelServingUserCredentials) | End-user token |
| Notebooks | Default (WorkspaceClient) | PAT or service principal |
| Evaluation Jobs | Default (WorkspaceClient) | Job service principal |

---

## Rule ML-07: Genie Space Resource Declaration

### The Problem

Agent evaluation fails with permission errors even when OBO context detection is correct. Why? The service principal created by Databricks for evaluation needs explicit resource access.

### Two Authentication Mechanisms

1. **OBO (UserAuthPolicy)** - Uses end-user credentials in Model Serving
2. **Automatic Passthrough (SystemAuthPolicy)** - Creates service principal with access to declared resources

**BOTH must be configured:**

```python
from mlflow.models.resources import (
    DatabricksGenieSpace,
    DatabricksSQLWarehouse,
    DatabricksUCFunction
)
from mlflow.models.auth_policy import (
    AuthPolicy,
    SystemAuthPolicy,
    UserAuthPolicy
)


# Genie Space IDs by domain
GENIE_SPACES = {
    "cost": "01xxxxxx-xxxx-xxxx",
    "security": "01xxxxxx-xxxx-xxxx",
    "performance": "01xxxxxx-xxxx-xxxx",
    "reliability": "01xxxxxx-xxxx-xxxx",
    "quality": "01xxxxxx-xxxx-xxxx"
}

WAREHOUSE_ID = "xxxxxxxxxxxx"


def get_mlflow_resources():
    """
    Declare ALL resources the agent needs access to.
    
    CRITICAL: Missing resources cause permission errors in evaluation.
    """
    resources = []
    
    # Genie Spaces
    for domain, space_id in GENIE_SPACES.items():
        resources.append(DatabricksGenieSpace(genie_space_id=space_id))
    
    # SQL Warehouse for Genie queries
    resources.append(DatabricksSQLWarehouse(warehouse_id=WAREHOUSE_ID))
    
    # Unity Catalog functions (if used)
    # resources.append(DatabricksUCFunction(function_name="catalog.schema.my_func"))
    
    return resources


def get_auth_policy():
    """
    Configure auth policy for both OBO and automatic passthrough.
    """
    resources = get_mlflow_resources()
    
    # System auth: Service principal gets access to these resources
    system_policy = SystemAuthPolicy(resources=resources)
    
    # User auth: OBO scopes for Model Serving
    user_policy = UserAuthPolicy(
        api_scopes=[
            "genie-space-execute",
            "serving-endpoint-query"
        ]
    )
    
    return AuthPolicy(
        system_auth_policy=system_policy,
        user_auth_policy=user_policy
    )


# Log model with full auth configuration
mlflow.pyfunc.log_model(
    artifact_path="agent",
    python_model=DataPlatformAgent(),
    resources=get_mlflow_resources(),   # ✅ Resource declaration
    auth_policy=get_auth_policy()       # ✅ Auth policy
)
```

### MLflow Version Requirements

| Resource Type | Minimum MLflow Version |
|---------------|------------------------|
| `DatabricksGenieSpace` | 2.17.1 |
| `DatabricksSQLWarehouse` | 2.16.1 |
| `DatabricksUCFunction` | 2.16.1 |

---

## Rule ML-08: Evaluation Framework

### Standard Evaluation Pattern

```python
import mlflow
from mlflow.genai.scorers import Guidelines, RelevanceToQuery


def evaluate_agent(model_uri: str, eval_dataset_name: str):
    """
    Evaluate agent with threshold-based gates.
    """
    # Load evaluation dataset from Unity Catalog
    eval_df = spark.table(f"{CATALOG}.{SCHEMA}.{eval_dataset_name}").toPandas()
    
    # Define scorers
    scorers = [
        RelevanceToQuery(),
        Guidelines(
            guidelines=[
                "Response must include specific metrics",
                "Response must cite data source",
                "Response must be factually accurate"
            ]
        )
    ]
    
    # Run evaluation
    results = mlflow.genai.evaluate(
        model=model_uri,
        data=eval_df,
        model_type="databricks-agent",
        scorers=scorers
    )
    
    # Check thresholds
    check_thresholds(results, {
        "relevance_to_query/mean": 0.8,
        "guidelines/mean": 0.7
    })
    
    return results


def check_thresholds(results, thresholds: dict):
    """
    Gate deployment based on evaluation thresholds.
    
    CRITICAL: Fail deployment if thresholds not met.
    """
    metrics = results.metrics
    
    failures = []
    for metric, threshold in thresholds.items():
        # Handle metric naming variations
        actual = find_metric(metrics, metric)
        if actual is not None and actual < threshold:
            failures.append(f"{metric}: {actual:.3f} < {threshold}")
    
    if failures:
        raise ValueError(f"Evaluation failed:\n" + "\n".join(failures))


def find_metric(metrics: dict, name: str) -> float:
    """Find metric handling naming variations."""
    aliases = {
        "relevance_to_query/mean": ["relevance/mean", "relevancy/mean"],
        "guidelines/mean": ["guideline_adherence/mean"]
    }
    
    if name in metrics:
        return metrics[name]
    
    for alias in aliases.get(name, []):
        if alias in metrics:
            return metrics[alias]
    
    return None
```

---

## Rule ML-09: Lakebase Memory Architecture

### Two-Layer Memory System

| Layer | Storage | Scope | Purpose |
|-------|---------|-------|---------|
| **Short-Term** | CheckpointSaver | Thread-based | Conversation continuity |
| **Long-Term** | DatabricksStore | User-based | Preferences, history |

### Implementation Pattern

```python
from databricks_langchain import CheckpointSaver, DatabricksStore


class AgentMemory:
    """Memory management for stateful agents."""
    
    def __init__(self, catalog: str, schema: str):
        self.catalog = catalog
        self.schema = schema
        self._init_short_term()
        self._init_long_term()
    
    def _init_short_term(self):
        """Short-term memory for conversation state."""
        try:
            self.checkpointer = CheckpointSaver.from_credentials(
                catalog=self.catalog,
                schema=self.schema,
                table_name="agent_checkpoints"
            )
        except Exception as e:
            print(f"⚠ Short-term memory unavailable: {e}")
            self.checkpointer = None
    
    def _init_long_term(self):
        """Long-term memory for user preferences."""
        try:
            self.store = DatabricksStore.from_credentials(
                catalog=self.catalog,
                schema=self.schema,
                table_name="agent_preferences"
            )
        except Exception as e:
            print(f"⚠ Long-term memory unavailable: {e}")
            self.store = None
    
    def get_conversation_state(self, thread_id: str) -> dict:
        """Retrieve conversation state for a thread."""
        if self.checkpointer is None:
            return {}
        
        with self.checkpointer.get_checkpointer() as cp:
            state = cp.get(thread_id)
            return state if state else {}
    
    def get_user_preferences(self, user_id: str) -> dict:
        """Retrieve user preferences."""
        if self.store is None:
            return {}
        
        items = self.store.search(("user", user_id))
        return {item.key: item.value for item in items}
    
    def save_user_preference(self, user_id: str, key: str, value: str):
        """Save a user preference."""
        if self.store is None:
            return
        
        self.store.put(
            namespace=("user", user_id),
            key=key,
            value=value
        )


# Integration with agent
class DataPlatformAgent(ResponsesAgent):
    def __init__(self):
        self.memory = AgentMemory(CATALOG, SCHEMA)
    
    def predict(self, context, model_input, params=None):
        custom_inputs = model_input.get("custom_inputs", {})
        user_id = custom_inputs.get("user_id", "anonymous")
        thread_id = custom_inputs.get("thread_id", str(uuid.uuid4()))
        
        # Load context from memory
        conversation_state = self.memory.get_conversation_state(thread_id)
        user_prefs = self.memory.get_user_preferences(user_id)
        
        # Process with memory context
        response = self._process(
            model_input["messages"],
            conversation_state,
            user_prefs
        )
        
        # Return thread_id for continuation
        return {
            "content": response,
            "custom_outputs": {"thread_id": thread_id}
        }
```

### Graceful Degradation

**CRITICAL: Agent MUST function without memory tables.**

```python
def _process_with_memory(self, messages, user_id, thread_id):
    """Process with graceful memory fallback."""
    try:
        # Try to use memory
        state = self.memory.get_conversation_state(thread_id)
        prefs = self.memory.get_user_preferences(user_id)
    except Exception as e:
        # Graceful fallback to stateless
        print(f"⚠ Memory unavailable, running stateless: {e}")
        state = {}
        prefs = {}
    
    return self._invoke_llm(messages, state, prefs)
```

---

## Rule ML-10: Prompt Registry

### Dual Storage Pattern

1. **Unity Catalog table** - Runtime access
2. **MLflow artifacts** - Versioning and lineage

```python
def register_prompt(
    spark,
    prompt_key: str,
    prompt_text: str,
    table_name: str
):
    """
    Register prompt to both UC and MLflow.
    
    CRITICAL: Escape single quotes to prevent SQL injection.
    """
    # Escape for SQL
    escaped_text = prompt_text.replace("'", "''")
    
    # Store in Unity Catalog
    spark.sql(f"""
        INSERT INTO {table_name}
        VALUES (
            '{prompt_key}',
            '{escaped_text}',
            'prompt',
            1,
            current_timestamp()
        )
    """)
    
    # Log to MLflow for versioning
    with mlflow.start_run(run_name=f"prompt_{prompt_key}"):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt_text)
            temp_path = f.name
        
        mlflow.log_artifact(temp_path, artifact_path=f"prompts/{prompt_key}")


def load_prompt(spark, prompt_key: str, table_name: str, alias: str = "champion") -> str:
    """Load prompt from Unity Catalog by alias."""
    df = spark.sql(f"""
        SELECT prompt_text
        FROM {table_name}
        WHERE prompt_key = '{prompt_key}'
        AND alias = '{alias}'
        ORDER BY version DESC
        LIMIT 1
    """)
    
    rows = df.collect()
    if not rows:
        raise ValueError(f"Prompt not found: {prompt_key}/{alias}")
    
    return rows[0].prompt_text
```

---

## Validation Checklist

### Agent Implementation
- [ ] Inherits from `ResponsesAgent`
- [ ] No `signature` parameter in `log_model()`
- [ ] Returns `content` key in response
- [ ] Returns `thread_id` in `custom_outputs`
- [ ] Graceful memory fallback implemented

### Authentication
- [ ] Context detection for OBO implemented
- [ ] All Genie Spaces in resources list
- [ ] SQL Warehouse in resources list
- [ ] SystemAuthPolicy includes all resources
- [ ] UserAuthPolicy has required scopes

### Evaluation
- [ ] Evaluation dataset in Unity Catalog
- [ ] Threshold checks implemented
- [ ] Metric naming variations handled
- [ ] Evaluation gates deployment

### Memory
- [ ] Short-term memory (CheckpointSaver) configured
- [ ] Long-term memory (DatabricksStore) configured
- [ ] Memory tables exist in Unity Catalog
- [ ] Stateless fallback works

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Agent not working in AI Playground" | Missing ResponsesAgent | Inherit from ResponsesAgent |
| "Permission denied" in evaluation | Missing resource declaration | Add resources to SystemAuthPolicy |
| "Permission denied" in Model Serving | OBO not configured | Add UserAuthPolicy with scopes |
| "Prompt not found" | Missing escape | Escape single quotes |
| "Memory table not found" | Tables not created | Implement graceful fallback |

---

## Related Documents

- [ML Model Standards](17-ml-model-standards.md)
- [Genie Space Standards](14-genie-space-standards.md)
- [Lakehouse Monitoring Standards](19-lakehouse-monitoring-standards.md)

---

## References

- [Databricks Agent Framework](https://docs.databricks.com/generative-ai/agent-framework/)
- [MLflow ResponsesAgent](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.ResponsesAgent)
- [Agent Authentication](https://docs.databricks.com/generative-ai/agent-framework/agent-authentication)
- [Lakebase Memory](https://docs.databricks.com/generative-ai/agent-framework/lakebase)
