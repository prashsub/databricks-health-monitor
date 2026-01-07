# Databricks notebook source
# ===========================================================================
# Log Agent Model to MLflow Registry (MLflow 3.0 Pattern)
# ===========================================================================
"""
Log Health Monitor Agent to Unity Catalog Model Registry using MLflow 3.0
LoggedModel pattern.

References:
- https://docs.databricks.com/aws/en/mlflow/logged-model
- https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent
- https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent#register-the-agent-to-unity-catalog
"""

# COMMAND ----------

import mlflow
import mlflow.pyfunc
from mlflow import MlflowClient
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec
from typing import List, Dict, Any
import os

# Enable MLflow 3 tracing (if available)
try:
    mlflow.langchain.autolog(
        log_models=False,  # We log manually
        log_input_examples=True,
        log_model_signatures=True,
    )
    print("MLflow LangChain autolog enabled")
except Exception as e:
    print(f"MLflow LangChain autolog not available: {e}")

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
# Configuration - DEFAULTS (actual values come from environment variables)
# ===========================================================================
# NOTE: The source of truth for Genie Space IDs is src/agents/config/genie_spaces.py
# These defaults are embedded here for Model Serving container isolation.
# The serving endpoint sets environment variables from the central registry.
# ===========================================================================
DEFAULT_GENIE_SPACES = {
    "cost": "01f0ea871ffe176fa6aee6f895f83d3b",
    "security": "01f0ea9367f214d6a4821605432234c4",
    "performance": "01f0ea93671e12d490224183f349dba0",
    "reliability": "01f0ea8724fd160e8e959b8a5af1a8c5",
    "quality": "01f0ea93616c1978a99a59d3f2e805bd",
    "unified": "01f0ea9368801e019e681aa3abaa0089",
}

LLM_ENDPOINT = "databricks-claude-3-7-sonnet"

# COMMAND ----------

class HealthMonitorAgent(mlflow.pyfunc.PythonModel):
    """
    Health Monitor Agent implementing MLflow 3.0 ChatAgent pattern.
    
    This agent routes queries to domain-specific Genie Spaces with
    proper MLflow tracing instrumentation.
    
    Domains:
    - Cost: DBU usage, billing, spend analysis
    - Security: Audit logs, access patterns, compliance
    - Performance: Query latency, cluster utilization
    - Reliability: Job failures, SLA compliance
    - Quality: Data freshness, schema drift
    """
    
    def load_context(self, context):
        """Initialize agent with lazy loading for serving efficiency."""
        self.llm_endpoint = os.environ.get("LLM_ENDPOINT", LLM_ENDPOINT)
        # Load Genie Space IDs from env vars with defaults from central config
        # Source of truth: src/agents/config/genie_spaces.py
        self.genie_spaces = {
            "cost": os.environ.get("COST_GENIE_SPACE_ID", DEFAULT_GENIE_SPACES["cost"]),
            "security": os.environ.get("SECURITY_GENIE_SPACE_ID", DEFAULT_GENIE_SPACES["security"]),
            "performance": os.environ.get("PERFORMANCE_GENIE_SPACE_ID", DEFAULT_GENIE_SPACES["performance"]),
            "reliability": os.environ.get("RELIABILITY_GENIE_SPACE_ID", DEFAULT_GENIE_SPACES["reliability"]),
            "quality": os.environ.get("QUALITY_GENIE_SPACE_ID", DEFAULT_GENIE_SPACES["quality"]),
            "unified": os.environ.get("UNIFIED_GENIE_SPACE_ID", DEFAULT_GENIE_SPACES["unified"]),
        }
        self._llm = None
        self._genie_agents = None
        print(f"Agent loaded. LLM: {self.llm_endpoint}")
    
    def _get_llm(self):
        """Lazy LLM initialization with tracing."""
        if self._llm is None:
            from langchain_databricks import ChatDatabricks
            self._llm = ChatDatabricks(
                endpoint=self.llm_endpoint,
                temperature=0.3,
            )
        return self._llm
    
    def _get_genie(self, domain: str):
        """Lazy Genie agent initialization."""
        if self._genie_agents is None:
            self._genie_agents = {}
        
        if domain not in self._genie_agents:
            space_id = self.genie_spaces.get(domain, "")
            if space_id:
                try:
                    from databricks_langchain.genie import GenieAgent
                    self._genie_agents[domain] = GenieAgent(
                        genie_space_id=space_id,
                        genie_agent_name=f"{domain}_genie",
                    )
                except Exception as e:
                    print(f"Genie init failed for {domain}: {e}")
                    self._genie_agents[domain] = None
            else:
                self._genie_agents[domain] = None
        
        return self._genie_agents.get(domain)
    
    def _classify_domain(self, query: str) -> str:
        """Classify query to appropriate domain."""
        q = query.lower()
        
        domain_keywords = {
            "cost": ["cost", "spend", "budget", "billing", "dbu", "expensive", "price"],
            "security": ["security", "access", "permission", "audit", "login", "user", "compliance"],
            "performance": ["slow", "performance", "latency", "cache", "optimize", "query time"],
            "reliability": ["fail", "job", "error", "sla", "pipeline", "success", "retry"],
            "quality": ["quality", "freshness", "stale", "schema", "null", "drift", "validation"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in q for kw in keywords):
                return domain
        
        return "unified"
    
    def predict(self, context, model_input):
        """
        Handle inference requests with MLflow tracing.
        
        Input format (ChatAgent compatible):
        {
            "messages": [{"role": "user", "content": "..."}]
        }
        
        Also handles DataFrame input from Model Serving:
        - DataFrame with "messages" column containing JSON string
        - DataFrame with individual message fields
        
        IMPORTANT: Prompts are loaded inside this traced function to link
        them to traces in MLflow UI. See:
        https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/
        """
        import mlflow
        import json
        import os
        
        # ==================================================================
        # LOAD PROMPTS FROM MLFLOW PROMPT REGISTRY (Links to Traces!)
        # ==================================================================
        # Loading prompts inside the traced function automatically links
        # the prompt version to this trace in the MLflow UI.
        # Reference: Link prompts to traces by loading registered prompts
        # inside the traced function using mlflow.genai.load_prompt()
        # ==================================================================
        def _load_prompt_safe(prompt_uri: str, default: str = "") -> str:
            """Safely load a prompt, returning default if not found."""
            try:
                return mlflow.genai.load_prompt(prompt_uri).template
            except Exception:
                return default
        
        # Get catalog/schema from environment or use defaults
        _catalog = os.environ.get("AGENT_CATALOG", "prashanth_subrahmanyam_catalog")
        _schema = os.environ.get("AGENT_SCHEMA", "dev_prashanth_subrahmanyam_system_gold_agent")
        
        # Load prompts - this links them to the current trace!
        prompts = {}
        prompt_names = ["orchestrator", "intent_classifier", "cost_analyst", 
                       "security_analyst", "performance_analyst", 
                       "reliability_analyst", "quality_analyst", "synthesizer"]
        
        for prompt_name in prompt_names:
            prompt_uri = f"prompts:/{_catalog}.{_schema}.prompt_{prompt_name}@production"
            prompts[prompt_name] = _load_prompt_safe(prompt_uri, f"Default {prompt_name} prompt")
        
        # Start trace span for this prediction
        with mlflow.start_span(name="agent_predict", span_type="AGENT") as span:
            # Parse input - handle various formats from Model Serving
            try:
                # ================================================================
                # ROBUST INPUT PARSING FOR MODEL SERVING
                # ================================================================
                # Model Serving can send input as:
                # 1. DataFrame (converted to dict of records)
                # 2. Dict with "messages" key
                # 3. Dict with "content" key directly
                # 4. Raw string
                # ================================================================
                
                query = ""
                messages = []
                
                # Step 1: Handle pandas DataFrame
                if hasattr(model_input, 'to_dict'):
                    try:
                        records = model_input.to_dict(orient='records')
                        model_input = records[0] if records else {}
                    except Exception:
                        # If DataFrame conversion fails, try values
                        try:
                            model_input = dict(model_input.iloc[0]) if len(model_input) > 0 else {}
                        except Exception:
                            model_input = {}
                
                # Step 2: Parse based on input type
                if isinstance(model_input, dict):
                    # Try to extract messages
                    messages = model_input.get("messages", [])
                    
                    # If messages is empty, try to get content directly
                    if not messages:
                        content = model_input.get("content", model_input.get("query", ""))
                        if content:
                            messages = [{"role": "user", "content": str(content)}]
                    
                    # If messages is a string (JSON), parse it
                    if isinstance(messages, str):
                        try:
                            messages = json.loads(messages)
                        except json.JSONDecodeError:
                            messages = [{"role": "user", "content": messages}]
                    
                    # Ensure messages is a list
                    if not isinstance(messages, list):
                        messages = [{"role": "user", "content": str(messages)}]
                        
                elif isinstance(model_input, str):
                    # Raw string input
                    messages = [{"role": "user", "content": model_input}]
                else:
                    # Unknown type - convert to string
                    messages = [{"role": "user", "content": str(model_input)}]
                
                # Step 3: Ensure we have at least one message
                if not messages:
                    return {"messages": [{"role": "assistant", "content": "No query provided."}]}
                
                # Step 4: Safely get query from last message
                try:
                    last_msg = messages[len(messages) - 1]  # Use len() instead of -1 index
                    if isinstance(last_msg, dict):
                        query = last_msg.get("content", "") or last_msg.get("text", "")
                    else:
                        query = str(last_msg)
                except (IndexError, KeyError, TypeError):
                    query = str(messages) if messages else ""
                
                span.set_inputs({"query": query, "messages": messages})
                
                # ==============================================================
                # USER & SESSION TRACKING (MLflow 3.0 Standard Metadata)
                # ==============================================================
                # Use standard metadata fields for user/session tracking.
                # This enables filtering and grouping in MLflow UI.
                # Reference: https://mlflow.org/docs/latest/genai/tracing/track-users-sessions/
                # ==============================================================
                
                # Extract user_id and session_id from input if provided
                user_id = "unknown"
                session_id = "unknown"
                
                if isinstance(model_input, dict):
                    # Check for user_id in various locations
                    user_id = model_input.get("user_id") or \
                             model_input.get("custom_inputs", {}).get("user_id") or \
                             os.environ.get("USER_ID", "unknown")
                    
                    # Check for session_id in various locations
                    session_id = model_input.get("session_id") or \
                                model_input.get("custom_inputs", {}).get("session_id") or \
                                model_input.get("thread_id") or \
                                os.environ.get("SESSION_ID", "unknown")
                
                # Update trace with standard MLflow metadata and custom tags
                try:
                    mlflow.update_current_trace(
                        # Standard MLflow metadata for user/session tracking
                        # These enable filtering and grouping in MLflow UI
                        metadata={
                            "mlflow.trace.user": user_id,      # Links trace to specific user
                            "mlflow.trace.session": session_id, # Groups traces in conversation
                        },
                        # Custom tags for additional context
                        tags={
                            "prompts_loaded": ",".join(prompt_names),
                            "prompt_catalog": _catalog,
                            "prompt_schema": _schema,
                            "user_id": user_id,       # Also in tags for legacy compatibility
                            "session_id": session_id, # Also in tags for legacy compatibility
                        }
                    )
                except Exception:
                    pass  # Non-critical - tracing is best effort
                
            except Exception as parse_error:
                error_msg = f"Error parsing input: {str(parse_error)}. Input type: {type(model_input)}"
                span.set_outputs({"error": error_msg})
                return {"messages": [{"role": "assistant", "content": error_msg}]}
            
            # Classify domain
            with mlflow.start_span(name="classify_domain", span_type="CLASSIFIER") as cls_span:
                domain = self._classify_domain(query)
                cls_span.set_outputs({"domain": domain})
            
            # Try Genie tool
            with mlflow.start_span(name=f"genie_{domain}", span_type="TOOL") as tool_span:
                genie = self._get_genie(domain)
                tool_span.set_inputs({"domain": domain, "query": query})
                
                if genie:
                    try:
                        result = genie.invoke({"input": query})
                        response = result.get("output", str(result))
                        tool_span.set_outputs({"response": response, "source": "genie"})
                        
                        output = {
                            "messages": [{"role": "assistant", "content": response}],
                            "metadata": {"domain": domain, "source": "genie"}
                        }
                        span.set_outputs(output)
                        return output
                    except Exception as e:
                        tool_span.set_attributes({"error": str(e)})
            
            # Fallback to LLM using loaded prompts
            with mlflow.start_span(name="llm_fallback", span_type="LLM") as llm_span:
                try:
                    llm = self._get_llm()
                    from langchain_core.messages import SystemMessage, HumanMessage
                    
                    # Get domain-specific prompt (loaded earlier, linked to trace!)
                    domain_prompt_key = f"{domain}_analyst" if domain != "unified" else "orchestrator"
                    domain_prompt = prompts.get(domain_prompt_key, f"You are a {domain} analyst.")
                    
                    llm_span.set_inputs({
                        "query": query, 
                        "domain": domain,
                        "prompt_used": domain_prompt_key
                    })
                    
                    # Use the loaded prompt as system message
                    system_content = domain_prompt if "{query}" not in domain_prompt else \
                        f"You are a Databricks Health Monitor {domain} analyst. {domain_prompt}"
                    
                    response = llm.invoke([
                        SystemMessage(content=system_content),
                        HumanMessage(content=query)
                    ])
                    
                    llm_span.set_outputs({
                        "response": response.content,
                        "prompt_key": domain_prompt_key
                    })
                    
                    output = {
                        "messages": [{"role": "assistant", "content": response.content}],
                        "metadata": {"domain": domain, "source": "llm"}
                    }
                    span.set_outputs(output)
                    return output
                    
                except Exception as e:
                    llm_span.set_attributes({"error": str(e)})
                    output = {
                        "messages": [{"role": "assistant", "content": f"Error: {str(e)}"}],
                        "metadata": {"domain": domain, "source": "error"}
                    }
                    span.set_outputs(output)
                    return output

# COMMAND ----------

def get_mlflow_resources() -> List:
    """
    Get resources for automatic authentication passthrough.
    
    Reference: https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication
    """
    resources = []
    
    try:
        from mlflow.models.resources import DatabricksServingEndpoint
        resources.append(DatabricksServingEndpoint(LLM_ENDPOINT))
    except ImportError:
        pass
    
    try:
        from mlflow.models.resources import DatabricksGenieSpace
        for space_id in DEFAULT_GENIE_SPACES.values():
            if space_id:
                resources.append(DatabricksGenieSpace(space_id))
    except ImportError:
        pass
    
    return resources

# COMMAND ----------

def log_agent():
    """
    Log agent using MLflow 3.0 LoggedModel pattern with version tracking.
    
    Key MLflow 3 features used:
    1. mlflow.set_active_model() - Creates LoggedModel in "Agent versions" UI
    2. mlflow.log_model_params() - Records version parameters
    3. mlflow.models.set_model() - Sets the model for logging
    4. Unity Catalog registration - Three-part naming
    5. Model signature - Defines input/output schema
    
    References:
    - https://docs.databricks.com/aws/en/mlflow/logged-model
    - https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/track-application-versions-with-mlflow
    """
    import subprocess
    from datetime import datetime
    
    model_name = f"{catalog}.{agent_schema}.health_monitor_agent"
    # Use consolidated experiment (single experiment for all agent runs)
    experiment_path = "/Shared/health_monitor/agent"
    
    print(f"Logging model to Unity Catalog: {model_name}")
    print(f"Experiment: {experiment_path}")
    
    mlflow.set_experiment(experiment_path)
    
    # ===========================================================================
    # MLflow 3.0 LoggedModel Version Tracking
    # ===========================================================================
    # This creates entries in the "Agent versions" tab in MLflow UI
    # Reference: https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/track-application-versions-with-mlflow
    # ===========================================================================
    
    # Generate version identifier from git commit or timestamp
    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()[:8]
        )
        version_identifier = f"git-{git_commit}"
    except Exception:
        # Fallback if not in git repo
        version_identifier = f"build-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    logged_model_name = f"health_monitor_agent-{version_identifier}"
    
    # CRITICAL: set_active_model creates the LoggedModel that appears in "Agent versions" UI
    active_model_info = None
    try:
        active_model_info = mlflow.set_active_model(name=logged_model_name)
        print(f"✓ Active LoggedModel: '{active_model_info.name}'")
        print(f"  Model ID: '{active_model_info.model_id}'")
    except Exception as e:
        print(f"⚠ set_active_model not available: {e}")
    
    # Log application parameters to the LoggedModel for version tracking
    if active_model_info:
        try:
            app_params = {
                "agent_version": "4.0.0",
                "llm_endpoint": LLM_ENDPOINT,
                "domains": "cost,security,performance,reliability,quality",
                "genie_spaces_count": str(len(DEFAULT_GENIE_SPACES)),
                "version_identifier": version_identifier,
            }
            mlflow.log_model_params(model_id=active_model_info.model_id, params=app_params)
            print(f"✓ Logged parameters to LoggedModel")
        except Exception as e:
            print(f"⚠ log_model_params error: {e}")
    
    # Create agent instance
    agent = HealthMonitorAgent()
    
    # Also set_model for backward compatibility with model logging
    try:
        mlflow.models.set_model(agent)
        print("✓ MLflow 3 set_model configured")
    except Exception as e:
        print(f"⚠ MLflow 3 set_model not available: {e}")
    
    # Define input/output signature for ChatAgent interface
    input_schema = Schema([
        ColSpec("string", "messages")  # JSON array of messages
    ])
    output_schema = Schema([
        ColSpec("string", "messages"),  # JSON array of response messages
        ColSpec("string", "metadata")   # JSON object with metadata
    ])
    signature = ModelSignature(inputs=input_schema, outputs=output_schema)
    
    # Input example matching ChatAgent interface
    input_example = {
        "messages": [{"role": "user", "content": "Why did costs spike yesterday?"}]
    }
    
    resources = get_mlflow_resources()
    
    with mlflow.start_run(run_name="health_monitor_agent_mlflow3") as run:
        # Tag this run as model_logging type for filtering in consolidated experiment
        mlflow.set_tag("run_type", "model_logging")
        
        # Log comprehensive parameters
        mlflow.log_params({
            "agent_type": "multi_domain_genie_orchestrator",
            "agent_version": "4.0.0",
            "llm_endpoint": LLM_ENDPOINT,
            "domains": "cost,security,performance,reliability,quality",
            "genie_spaces_configured": len([v for v in DEFAULT_GENIE_SPACES.values() if v]),
            "mlflow_version": "3.0",
            "tracing_enabled": True,
        })
        
        # Log model with MLflow 3 features
        logged_model = mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=agent,
            input_example=input_example,
            signature=signature,
            resources=resources if resources else None,
            registered_model_name=model_name,
            pip_requirements=[
                # Note: langchain-databricks is pre-installed on Databricks Model Serving
                # Don't specify version constraints to avoid installation conflicts
                "mlflow",
                "langchain",
                "langchain-core",
                "langchain-databricks",  # Required for ChatDatabricks
                "langgraph",
                "databricks-sdk",
                "databricks-agents",  # Required for GenieAgent
            ],
        )
        
        # Log the LoggedModel ID for tracking
        model_info = logged_model.model_info if hasattr(logged_model, 'model_info') else None
        if model_info:
            mlflow.log_params({
                "logged_model_id": getattr(model_info, 'model_id', 'unknown'),
                "model_uri": logged_model.model_uri,
            })
        
        print(f"✓ LoggedModel URI: {logged_model.model_uri}")
        print(f"✓ Run ID: {run.info.run_id}")
    
    # Set production and staging aliases
    client = MlflowClient()
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            
            client.set_registered_model_alias(model_name, "production", latest.version)
            client.set_registered_model_alias(model_name, "staging", latest.version)
            
            print(f"✓ Set aliases (production, staging) to version {latest.version}")
    except Exception as e:
        print(f"⚠ Alias error: {e}")
    
    return model_name

# COMMAND ----------

# Main execution
try:
    model = log_agent()
    
    print("\n" + "=" * 70)
    print("✓ Agent logged successfully with MLflow 3.0 LoggedModel pattern!")
    print("=" * 70)
    print(f"\nModel: {model}")
    print(f"Aliases: production, staging")
    print(f"\nMLflow 3 Features:")
    print("  - LoggedModel tracking enabled")
    print("  - Tracing instrumentation added")
    print("  - Unity Catalog registration complete")
    print("  - Authentication passthrough configured")
    
    dbutils.notebook.exit("SUCCESS")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    dbutils.notebook.exit(f"FAILED: {e}")
