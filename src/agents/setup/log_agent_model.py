# Databricks notebook source
# ===========================================================================
# Log Agent Model to MLflow Registry
# ===========================================================================
"""
Log Health Monitor Agent to MLflow Model Registry.

Uses a minimal, self-contained implementation optimized for Model Serving.
"""

# COMMAND ----------

import mlflow
import mlflow.pyfunc
from mlflow import MlflowClient
from typing import List, Dict, Any

# Parameters
dbutils.widgets.text("catalog", "prashanth_subrahmanyam_catalog")
dbutils.widgets.text("agent_schema", "dev_prashanth_subrahmanyam_system_gold_agent")

catalog = dbutils.widgets.get("catalog")
agent_schema = dbutils.widgets.get("agent_schema")

print(f"Catalog: {catalog}")
print(f"Agent Schema: {agent_schema}")

# COMMAND ----------

# Genie Space IDs (from Phase 3.6 deployment)
GENIE_SPACES = {
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
    Minimal Health Monitor Agent for Model Serving.
    
    All imports are deferred to predict() to avoid container build issues.
    """
    
    def load_context(self, context):
        """Minimal initialization - just store config."""
        import os
        
        # Store config from environment
        self.llm_endpoint = os.environ.get("LLM_ENDPOINT", "databricks-claude-3-7-sonnet")
        self.genie_spaces = {
            "cost": os.environ.get("COST_GENIE_SPACE_ID", ""),
            "security": os.environ.get("SECURITY_GENIE_SPACE_ID", ""),
            "performance": os.environ.get("PERFORMANCE_GENIE_SPACE_ID", ""),
            "reliability": os.environ.get("RELIABILITY_GENIE_SPACE_ID", ""),
            "quality": os.environ.get("QUALITY_GENIE_SPACE_ID", ""),
            "unified": os.environ.get("UNIFIED_GENIE_SPACE_ID", ""),
        }
        
        # Lazy initialization flags
        self._llm = None
        self._genie_agents = None
        
        print(f"Agent loaded. LLM: {self.llm_endpoint}")
    
    def _get_llm(self):
        """Lazy LLM initialization."""
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
                    print(f"Failed to init Genie for {domain}: {e}")
                    self._genie_agents[domain] = None
            else:
                self._genie_agents[domain] = None
        
        return self._genie_agents.get(domain)
    
    def _classify_domain(self, query: str) -> str:
        """Simple keyword-based domain classification."""
        q = query.lower()
        
        if any(w in q for w in ["cost", "spend", "budget", "billing", "dbu", "expensive"]):
            return "cost"
        if any(w in q for w in ["security", "access", "permission", "audit", "login", "user"]):
            return "security"
        if any(w in q for w in ["slow", "performance", "latency", "cache", "optimize"]):
            return "performance"
        if any(w in q for w in ["fail", "job", "error", "sla", "pipeline", "success"]):
            return "reliability"
        if any(w in q for w in ["quality", "freshness", "stale", "schema", "null"]):
            return "quality"
        
        return "unified"
    
    def predict(self, context, model_input):
        """Handle inference requests."""
        # Parse input
        if hasattr(model_input, 'to_dict'):
            model_input = model_input.to_dict(orient='records')
            if model_input:
                model_input = model_input[0]
        
        messages = model_input.get("messages", [])
        if not messages:
            return {"messages": [{"role": "assistant", "content": "No query provided."}]}
        
        # Get query
        last_msg = messages[-1]
        query = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
        
        # Classify domain
        domain = self._classify_domain(query)
        
        # Try Genie first
        genie = self._get_genie(domain)
        if genie:
            try:
                result = genie.invoke({"input": query})
                response = result.get("output", str(result))
                return {
                    "messages": [{"role": "assistant", "content": response}],
                    "metadata": {"domain": domain, "source": "genie"}
                }
            except Exception as e:
                print(f"Genie error: {e}")
        
        # Fallback to LLM
        try:
            llm = self._get_llm()
            from langchain_core.messages import SystemMessage, HumanMessage
            
            response = llm.invoke([
                SystemMessage(content=f"You are a Databricks Health Monitor assistant for {domain} queries. Be concise and actionable."),
                HumanMessage(content=query)
            ])
            
            return {
                "messages": [{"role": "assistant", "content": response.content}],
                "metadata": {"domain": domain, "source": "llm"}
            }
        except Exception as e:
            return {
                "messages": [{"role": "assistant", "content": f"Error: {str(e)}"}],
                "metadata": {"domain": domain, "source": "error"}
            }

# COMMAND ----------

def get_mlflow_resources() -> List:
    """Get resources for authentication passthrough."""
    resources = []
    
    try:
        from mlflow.models.resources import DatabricksServingEndpoint
        resources.append(DatabricksServingEndpoint(LLM_ENDPOINT))
    except:
        pass
    
    try:
        from mlflow.models.resources import DatabricksGenieSpace
        for space_id in GENIE_SPACES.values():
            if space_id:
                resources.append(DatabricksGenieSpace(space_id))
    except:
        pass
    
    return resources

# COMMAND ----------

def log_agent():
    """Log the agent model."""
    model_name = f"{catalog}.{agent_schema}.health_monitor_agent"
    
    print(f"Logging model: {model_name}")
    
    mlflow.set_experiment("/Shared/health_monitor/agent_models")
    
    agent = HealthMonitorAgent()
    
    input_example = {
        "messages": [{"role": "user", "content": "Why did costs spike?"}]
    }
    
    resources = get_mlflow_resources()
    
    with mlflow.start_run(run_name="health_monitor_agent_v3"):
        mlflow.log_params({
            "agent_version": "3.0.0",
            "llm_endpoint": LLM_ENDPOINT,
        })
        
        logged = mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=agent,
            input_example=input_example,
            resources=resources if resources else None,
            registered_model_name=model_name,
            pip_requirements=[
                "langchain>=0.3.0",
                "langchain-core>=0.3.0",
                "langchain-databricks>=0.1.0",
                "databricks-langchain>=0.1.0",
            ],
        )
        
        print(f"Logged: {logged.model_uri}")
    
    # Set aliases
    client = MlflowClient()
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            client.set_registered_model_alias(model_name, "production", latest.version)
            print(f"Set production alias to v{latest.version}")
    except Exception as e:
        print(f"Alias error: {e}")
    
    return model_name

# COMMAND ----------

try:
    model = log_agent()
    print(f"\n✓ Success: {model}")
    dbutils.notebook.exit("SUCCESS")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    dbutils.notebook.exit(f"FAILED: {e}")
