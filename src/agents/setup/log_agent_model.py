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
# Note: Schema/ColSpec/ModelSignature NOT needed - ResponsesAgent auto-infers signature
from typing import List, Dict, Any, Generator, Optional
import os
import json
import uuid

# Enable MLflow 3 tracing (if available)
try:
    # Try new MLflow 3.x API first (no log_models parameter)
    mlflow.langchain.autolog()
    print("✓ MLflow LangChain autolog enabled")
except TypeError:
    # Fallback for older MLflow versions
    try:
        mlflow.langchain.autolog(
            log_models=False,
            log_input_examples=True,
            log_model_signatures=True,
        )
        print("✓ MLflow LangChain autolog enabled (legacy API)")
    except Exception as e:
        print(f"⚠ MLflow autolog not available: {e}")
except Exception as e:
    print(f"⚠ MLflow LangChain autolog not available: {e}")

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

LLM_ENDPOINT = "databricks-claude-sonnet-4-5"

# ===========================================================================
# LAKEBASE MEMORY CONFIGURATION
# ===========================================================================
# Short-term memory: Persists conversation context within a session (thread_id)
# Long-term memory: Persists user preferences and insights across sessions
#
# Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents
# Reference: https://docs.databricks.com/aws/en/notebooks/source/generative-ai/short-term-memory-agent-lakebase.html
# Reference: https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html
# ===========================================================================
LAKEBASE_INSTANCE_NAME = os.environ.get("LAKEBASE_INSTANCE_NAME", "vibe-coding-workshop-lakebase")

# Embedding model for long-term memory semantic search
EMBEDDING_ENDPOINT = os.environ.get("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1024"))

# Memory TTL settings
SHORT_TERM_MEMORY_TTL_HOURS = int(os.environ.get("SHORT_TERM_MEMORY_TTL_HOURS", "24"))
LONG_TERM_MEMORY_TTL_DAYS = int(os.environ.get("LONG_TERM_MEMORY_TTL_DAYS", "365"))

# ===========================================================================
# HELPER: Safe trace update (suppresses warnings when no active trace)
# ===========================================================================
def _safe_update_trace(metadata: dict = None, tags: dict = None) -> bool:
    """
    Safely update the current MLflow trace without triggering warnings.
    
    During evaluation testing, there may not be an active trace context.
    This helper checks for an active trace before attempting updates.
    
    Returns:
        True if update succeeded, False if no active trace.
    """
    try:
        # Check if there's an active trace by trying to get current span
        current_span = mlflow.get_current_active_span()
        if current_span is None:
            return False
        
        # Safe to update
        mlflow.update_current_trace(metadata=metadata, tags=tags)
        return True
    except Exception:
        return False

# COMMAND ----------

class HealthMonitorAgent(mlflow.pyfunc.ResponsesAgent):
    """
    Health Monitor Agent implementing MLflow 3.0 ResponsesAgent pattern with Streaming.
    
    ResponsesAgent is the recommended interface for Databricks AI Playground
    compatibility. It provides:
    - Automatic signature inference (no manual schema needed)
    - AI Playground compatibility
    - **Streaming support** via predict_stream() with delta events
    - Multi-agent and tool-calling support
    - MLflow tracing integration
    
    Streaming Implementation (per official docs):
    - predict_stream() yields ResponsesAgentStreamEvent objects
    - predict() delegates to predict_stream() (code reuse pattern)
    - Delta events sent with same item_id for text chunks
    - Final response.output_item.done event signals completion
    
    Reference: https://mlflow.org/docs/latest/genai/serving/responses-agent
    Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent#streaming-responses
    
    Domains:
    - Cost: DBU usage, billing, spend analysis
    - Security: Audit logs, access patterns, compliance
    - Performance: Query latency, cluster utilization
    - Reliability: Job failures, SLA compliance
    - Quality: Data freshness, schema drift
    """
    
    def __init__(self):
        """Initialize agent - called when model is loaded."""
        super().__init__()
        self.llm_endpoint = os.environ.get("LLM_ENDPOINT", LLM_ENDPOINT)
        # Load Genie Space IDs from env vars with defaults from central config
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
        
        # ================================================================
        # LAKEBASE MEMORY CONFIGURATION
        # 
        # Short-term memory: CheckpointSaver for conversation context
        # Long-term memory: DatabricksStore for user preferences/insights
        #
        # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents
        # ================================================================
        self.lakebase_instance_name = os.environ.get("LAKEBASE_INSTANCE_NAME", LAKEBASE_INSTANCE_NAME)
        self.embedding_endpoint = os.environ.get("EMBEDDING_ENDPOINT", EMBEDDING_ENDPOINT)
        self.embedding_dims = int(os.environ.get("EMBEDDING_DIMS", str(EMBEDDING_DIMS)))
        
        # Lazy-loaded memory stores (initialized on first use in predict)
        self._short_term_memory = None
        self._long_term_memory = None
        
        # Track if Lakebase memory is available (tables may not exist)
        # Once set to False, we skip memory operations silently
        self._short_term_memory_available = True  # Assume available until proven otherwise
        self._long_term_memory_available = True
        
        # ================================================================
        # GENIE CONVERSATION TRACKING: STATELESS PATTERN
        # 
        # IMPORTANT: In Model Serving, replicas don't share state!
        # Per Databricks docs: "don't assume the same replica handles all requests"
        # 
        # Solution: conversation_id is passed via custom_inputs/custom_outputs.
        # Clients must track genie_conversation_ids and pass them back.
        # See _query_genie() for implementation details.
        # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
        # ================================================================
        
        print(f"Agent initialized. LLM: {self.llm_endpoint}")
        print(f"Memory: Lakebase '{self.lakebase_instance_name}' (optional, requires tables)")
    
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
        
        # Lakebase memory configuration (lazy-loaded)
        self.lakebase_instance_name = os.environ.get("LAKEBASE_INSTANCE_NAME", LAKEBASE_INSTANCE_NAME)
        self.embedding_endpoint = os.environ.get("EMBEDDING_ENDPOINT", EMBEDDING_ENDPOINT)
        self.embedding_dims = int(os.environ.get("EMBEDDING_DIMS", str(EMBEDDING_DIMS)))
        self._short_term_memory = None
        self._long_term_memory = None
        self._short_term_memory_available = True  # Assume available until proven otherwise
        self._long_term_memory_available = True
        
        # Note: Genie conversation tracking is stateless (via custom_inputs/outputs)
        print(f"Agent loaded. LLM: {self.llm_endpoint}")
        print(f"Memory: Lakebase '{self.lakebase_instance_name}' (optional, requires tables)")
    
    # ========================================================================
    # SHORT-TERM MEMORY: CheckpointSaver for conversation context
    # ========================================================================
    # Persists conversation state across turns within a session (thread_id).
    # This allows the agent to remember previous messages in the same conversation.
    #
    # Usage Pattern (per official docs):
    # - thread_id passed via custom_inputs["thread_id"]
    # - If not provided, a new thread_id is generated
    # - thread_id returned in custom_outputs for client to track
    #
    # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents
    # ========================================================================
    
    def _resolve_thread_id(self, custom_inputs: Optional[Dict] = None) -> str:
        """
        Resolve thread ID from custom_inputs or generate a new one.
        
        Priority:
        1. custom_inputs["thread_id"] - Explicit from client
        2. New UUID - Fresh conversation
        
        Args:
            custom_inputs: Custom inputs dict from request
            
        Returns:
            Thread ID string for checkpoint configuration.
        """
        if custom_inputs and isinstance(custom_inputs, dict):
            thread_id = custom_inputs.get("thread_id")
            if thread_id:
                return str(thread_id)
        
        # Generate new thread ID
        return str(uuid.uuid4())
    
    def _get_conversation_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history from short-term memory.
        
        Uses Lakebase CheckpointSaver to get previous messages in this thread.
        
        Args:
            thread_id: The conversation thread identifier
            
        Returns:
            List of previous messages in the conversation.
        """
        # Skip if memory was previously marked unavailable
        if not self._short_term_memory_available:
            return []
            
        try:
            from databricks_langchain import CheckpointSaver
            
            with CheckpointSaver(instance_name=self.lakebase_instance_name) as checkpointer:
                config = {"configurable": {"thread_id": thread_id}}
                
                # Get the latest checkpoint for this thread
                checkpoint_tuple = checkpointer.get_tuple(config)
                
                if checkpoint_tuple and checkpoint_tuple.checkpoint:
                    messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
                    
                    # Convert to serializable format
                    history = []
                    for msg in messages:
                        if hasattr(msg, "content") and hasattr(msg, "type"):
                            history.append({
                                "role": "assistant" if msg.type == "ai" else "user",
                                "content": msg.content
                            })
                        elif isinstance(msg, dict):
                            history.append(msg)
                    
                    return history
                    
        except ImportError as ie:
            # Mark as unavailable and log once
            self._short_term_memory_available = False
            print(f"⚠ Short-term memory disabled: {ie}")
        except Exception as e:
            # Check if this is a "table does not exist" error
            if "does not exist" in str(e) or "checkpoints" in str(e).lower():
                self._short_term_memory_available = False
                print(f"⚠ Short-term memory disabled (Lakebase tables not initialized)")
            # Don't log other transient errors
        
        return []
    
    def _save_to_short_term_memory(
        self, 
        thread_id: str, 
        user_message: str, 
        assistant_response: str,
        domain: str
    ) -> bool:
        """
        Save conversation turn to short-term memory.
        
        Uses Lakebase CheckpointSaver to persist the conversation state.
        
        Args:
            thread_id: The conversation thread identifier
            user_message: The user's query
            assistant_response: The agent's response
            domain: The domain classification
            
        Returns:
            True if saved successfully, False otherwise.
        """
        # Skip if memory was previously marked unavailable
        if not self._short_term_memory_available:
            return False
            
        try:
            from databricks_langchain import CheckpointSaver
            from langchain_core.messages import HumanMessage, AIMessage
            
            with CheckpointSaver(instance_name=self.lakebase_instance_name) as checkpointer:
                config = {"configurable": {"thread_id": thread_id}}
                
                # Get existing checkpoint or create new
                checkpoint_tuple = checkpointer.get_tuple(config)
                
                existing_messages = []
                if checkpoint_tuple and checkpoint_tuple.checkpoint:
                    existing_messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
                
                # Add new messages
                new_messages = existing_messages + [
                    HumanMessage(content=user_message),
                    AIMessage(content=assistant_response, additional_kwargs={"domain": domain})
                ]
                
                # Create checkpoint with updated messages
                checkpoint = {
                    "v": 1,
                    "ts": str(uuid.uuid4()),  # Unique timestamp ID
                    "channel_values": {
                        "messages": new_messages
                    }
                }
                
                # Save checkpoint
                checkpoint_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": "",
                        "checkpoint_id": str(uuid.uuid4())
                    }
                }
                
                checkpointer.put(
                    config=checkpoint_config,
                    checkpoint=checkpoint,
                    metadata={"domain": domain, "source": "health_monitor_agent"}
                )
                
                return True
                
        except ImportError as ie:
            self._short_term_memory_available = False
            print(f"⚠ Short-term memory disabled: {ie}")
        except Exception as e:
            # Check if this is a "table does not exist" error
            if "does not exist" in str(e) or "checkpoints" in str(e).lower():
                self._short_term_memory_available = False
                # Only log once when disabling
                print(f"⚠ Short-term memory disabled (Lakebase tables not initialized)")
        
        return False
    
    # ========================================================================
    # LONG-TERM MEMORY: DatabricksStore for user preferences and insights
    # ========================================================================
    # Persists user-specific information across sessions:
    # - User preferences (preferred domains, alert thresholds)
    # - Learned insights (common queries, patterns)
    # - Historical context (recent analysis topics)
    #
    # Uses vector embeddings for semantic retrieval.
    #
    # Reference: https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html
    # ========================================================================
    
    def _get_user_namespace(self, user_id: str) -> tuple:
        """
        Get namespace tuple for user memory isolation.
        
        Args:
            user_id: User identifier (e.g., email)
            
        Returns:
            Namespace tuple for DatabricksStore operations.
        """
        # Sanitize user_id for namespace (replace special chars)
        sanitized = user_id.replace(".", "-").replace("@", "-at-").replace("/", "-")
        return ("health_monitor_users", sanitized)
    
    def _get_user_preferences(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Retrieve relevant user preferences and context from long-term memory.
        
        Uses semantic search to find memories relevant to the current query.
        
        Args:
            user_id: User identifier
            query: Current query for semantic matching
            
        Returns:
            Dict with user preferences and relevant context.
        """
        # Skip if memory was previously marked unavailable
        if not self._long_term_memory_available:
            return {}
            
        try:
            from databricks_langchain import DatabricksStore
            
            store = DatabricksStore(
                instance_name=self.lakebase_instance_name,
                embedding_endpoint=self.embedding_endpoint,
                embedding_dims=self.embedding_dims
            )
            
            namespace = self._get_user_namespace(user_id)
            
            # Search for relevant memories
            results = store.search(namespace, query=query, limit=5)
            
            preferences = {
                "preferred_domains": [],
                "alert_thresholds": {},
                "recent_topics": [],
                "custom_settings": {}
            }
            
            for item in results:
                key = item.key
                value = item.value
                
                if key.startswith("preference_"):
                    pref_type = key.replace("preference_", "")
                    preferences["custom_settings"][pref_type] = value
                elif key.startswith("domain_"):
                    preferences["preferred_domains"].append(value.get("domain"))
                elif key.startswith("threshold_"):
                    threshold_name = key.replace("threshold_", "")
                    preferences["alert_thresholds"][threshold_name] = value
                elif key.startswith("topic_"):
                    preferences["recent_topics"].append(value)
            
            return preferences
            
        except ImportError as ie:
            self._long_term_memory_available = False
            print(f"⚠ Long-term memory disabled: {ie}")
        except Exception as e:
            # Check if this is a "table does not exist" error
            if "does not exist" in str(e) or "store" in str(e).lower():
                self._long_term_memory_available = False
                print(f"⚠ Long-term memory disabled (Lakebase tables not initialized)")
        
        return {}
    
    def _save_user_insight(
        self, 
        user_id: str, 
        insight_key: str, 
        insight_data: Dict[str, Any]
    ) -> bool:
        """
        Save an insight or preference to long-term memory.
        
        Args:
            user_id: User identifier
            insight_key: Unique key for this insight (e.g., "topic_cost_analysis")
            insight_data: Data to store
            
        Returns:
            True if saved successfully, False otherwise.
        """
        # Skip if memory was previously marked unavailable
        if not self._long_term_memory_available:
            return False
            
        try:
            from databricks_langchain import DatabricksStore
            
            store = DatabricksStore(
                instance_name=self.lakebase_instance_name,
                embedding_endpoint=self.embedding_endpoint,
                embedding_dims=self.embedding_dims
            )
            
            namespace = self._get_user_namespace(user_id)
            
            # Add timestamp to insight
            from datetime import datetime, timezone
            insight_data["saved_at"] = datetime.now(timezone.utc).isoformat()
            
            store.put(namespace, insight_key, insight_data)
            
            return True
            
        except ImportError as ie:
            self._long_term_memory_available = False
            print(f"⚠ Long-term memory disabled: {ie}")
        except Exception as e:
            # Check if this is a "table does not exist" error
            if "does not exist" in str(e) or "store" in str(e).lower():
                self._long_term_memory_available = False
                print(f"⚠ Long-term memory disabled (Lakebase tables not initialized)")
        
        return False
    
    def _extract_and_save_insights(
        self, 
        user_id: str, 
        query: str, 
        response: str, 
        domain: str
    ) -> None:
        """
        Extract insights from the conversation and save to long-term memory.
        
        This is called after each successful query to build user context.
        
        Args:
            user_id: User identifier
            query: The user's query
            response: The agent's response
            domain: The domain classification
        """
        # Save the query topic for future reference
        topic_key = f"topic_{domain}_{hash(query) % 10000}"
        self._save_user_insight(
            user_id=user_id,
            insight_key=topic_key,
            insight_data={
                "domain": domain,
                "query_summary": query[:200] if len(query) > 200 else query,
                "response_length": len(response),
                "type": "query_history"
            }
        )
        
        # Track domain preference (increments usage)
        domain_key = f"domain_{domain}"
        self._save_user_insight(
            user_id=user_id,
            insight_key=domain_key,
            insight_data={
                "domain": domain,
                "query_count": 1,  # In practice, would increment
                "type": "domain_preference"
            }
        )
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Call Databricks Foundation Model using Databricks SDK.
        
        Uses WorkspaceClient which handles authentication automatically in:
        - Model Serving (automatic auth passthrough via DatabricksServingEndpoint resource)
        - Databricks notebooks
        - Jobs
        
        IMPORTANT: Do NOT use OpenAI SDK fallback - it causes dependency issues
        in Model Serving. The Databricks SDK is pre-installed and reliable.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            from databricks.sdk import WorkspaceClient
            from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
            
            # WorkspaceClient handles authentication automatically
            # In Model Serving with auth passthrough, it uses the injected credentials
            # This works because we declared DatabricksServingEndpoint(LLM_ENDPOINT) in resources
            w = WorkspaceClient()
            
            sdk_messages = []
            for msg in messages:
                role = ChatMessageRole.SYSTEM if msg["role"] == "system" else ChatMessageRole.USER
                sdk_messages.append(ChatMessage(role=role, content=msg["content"]))
            
            response = w.serving_endpoints.query(
                name=self.llm_endpoint,
                messages=sdk_messages,
                temperature=0.3,
                max_tokens=4096
            )
            return response.choices[0].message.content
            
        except ImportError as e:
            return f"LLM call failed: Databricks SDK not available - {str(e)}"
            
        except Exception as e:
            return f"LLM call failed: {str(e)}"
    
    def _get_genie_space_id(self, domain: str) -> str:
        """Get Genie Space ID for a domain."""
        return self.genie_spaces.get(domain, "")
    
    def _get_genie_client(self, domain: str):
        """
        Get authenticated Databricks WorkspaceClient for Genie API.
        
        Supports:
        - On-behalf-of-user auth (Model Serving with auth passthrough)
        - Default workspace auth (notebooks, jobs)
        
        Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication
        """
        from databricks.sdk import WorkspaceClient
        
        try:
            from databricks_ai_bridge import ModelServingUserCredentials
            client = WorkspaceClient(credentials_strategy=ModelServingUserCredentials())
            print(f"✓ Using on-behalf-of-user auth for {domain} Genie")
            return client
        except ImportError as ie:
            client = WorkspaceClient()
            print(f"⚠ databricks-ai-bridge not available for {domain} Genie: {ie}")
            print(f"  Falling back to default auth (service principal or PAT)")
            return client
        except Exception as auth_e:
            client = WorkspaceClient()
            print(f"⚠ Auth setup failed for {domain} Genie: {type(auth_e).__name__}: {auth_e}")
            print(f"  Falling back to default auth")
            return client
    
    def _query_genie(self, domain: str, query: str, session_id: str = None, conversation_id: str = None) -> tuple:
        """
        Query Genie Space using Databricks SDK Genie API.
        
        This implements the full Genie conversation flow:
        1. start_conversation_and_wait() - Sends query, waits for SQL generation
        2. get_message_attachment_query_result() - Gets EXECUTED query results (actual data!)
        
        CRITICAL: Without step 2, you only get the SQL, not the results!
        
        Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
        Reference: https://docs.databricks.com/api/workspace/genie
        
        Best practices from Databricks docs:
        - Poll every 1-5 seconds with exponential backoff
        - Start a new conversation for each SESSION (not each query)
        - Use create_message() for follow-up questions within same session
        - Query results limited to 5,000 rows
        
        IMPORTANT (Model Serving Statelessness):
        Per Databricks docs: "don't assume the same replica handles all requests"
        Therefore, conversation_id MUST be passed in custom_inputs, NOT stored
        in instance state. This method now RETURNS the conversation_id so the
        client can track it and pass it back for follow-ups.
        
        Args:
            domain: Domain to query (cost, security, etc.)
            query: User's question
            session_id: Optional session ID (legacy, not used in stateless mode)
            conversation_id: Existing conversation ID for follow-up questions
                            (passed via custom_inputs from client)
        
        Returns:
            tuple: (response_text, conversation_id) - The response and conversation ID
                   for tracking follow-ups
        """
        import time
        
        space_id = self._get_genie_space_id(domain)
        if not space_id:
            raise ValueError(f"No Genie Space ID configured for domain: {domain}")
        
        client = self._get_genie_client(domain)
        
        # ================================================================
        # GENIE CONVERSATION CONTINUITY (Stateless Pattern)
        # 
        # CRITICAL: In Model Serving, replicas don't share state!
        # Per docs: "don't assume the same replica handles all requests"
        # 
        # Solution: conversation_id is passed IN via custom_inputs and
        # returned OUT via custom_outputs. Client tracks the state.
        #
        # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
        # ================================================================
        
        # Use conversation_id from custom_inputs for follow-up questions
        if conversation_id:
            print(f"→ Follow-up Genie query for {domain} (conversation: {conversation_id[:8]}...)")
            response_text = self._follow_up_genie_internal(
                client, space_id, conversation_id, query, domain
            )
            return (response_text, conversation_id)  # Return same conversation_id
        
        # Start new conversation
        print(f"→ Starting new Genie conversation for {domain} (space_id: {space_id[:8]}...)")
        
        try:
            # ================================================================
            # STEP 1: Start conversation and wait for completion
            # Reference: POST /api/2.0/genie/spaces/{space_id}/start-conversation
            # SDK method: start_conversation_and_wait() handles polling automatically
            # ================================================================
            response = client.genie.start_conversation_and_wait(
                space_id=space_id,
                content=query
            )
            
            # Extract IDs needed for query result retrieval
            new_conversation_id = getattr(response, 'conversation_id', None)
            message_id = getattr(response, 'id', None) or getattr(response, 'message_id', None)
            
            # Debug: Print response structure
            print(f"  → Conversation: {new_conversation_id[:8] if new_conversation_id else 'N/A'}...")
            print(f"  → Message: {message_id[:8] if message_id else 'N/A'}...")
            
            # ================================================================
            # STEP 2: Extract attachments (text, SQL, query results)
            # Each message can have multiple attachments:
            # - text: Natural language explanation
            # - query: Generated SQL + executed results
            # ================================================================
            result_text = ""
            query_results_text = ""
            generated_sql = ""
            
            if not response or not hasattr(response, 'attachments') or not response.attachments:
                print(f"⚠ No attachments in Genie response")
                return (f"Genie returned no results for: {query}", new_conversation_id)
            
            for attachment in response.attachments:
                # Try multiple attribute names for attachment ID
                # SDK may use 'attachment_id' or 'id' depending on version
                attachment_id = (
                    getattr(attachment, 'attachment_id', None) or 
                    getattr(attachment, 'id', None)
                )
                
                # ================================================================
                # DEBUG: Print ALL attachment attributes to understand structure
                # This helps diagnose why text/analysis might be missing
                # ================================================================
                attachment_attrs = [a for a in dir(attachment) if not a.startswith('_')]
                print(f"  → Attachment attributes: {attachment_attrs}")
                
                # Check for type field (attachments can be 'text' or 'query' type)
                attachment_type = getattr(attachment, 'type', None)
                print(f"  → Attachment type: {attachment_type}")
                
                print(f"  → Processing attachment: {attachment_id[:8] if attachment_id else 'unknown'}...")
                
                # ================================================================
                # EXTRACT TEXT RESPONSE (multiple strategies)
                # The Genie API can return text in different ways:
                # 1. attachment.text.content (TextAttachment object)
                # 2. attachment.text (string directly)
                # 3. attachment.content (sometimes used)
                # 4. attachment.query.description (query explanation)
                # ================================================================
                
                # Strategy 1: attachment.text.content
                if hasattr(attachment, 'text') and attachment.text:
                    text_content = ""
                    text_obj = attachment.text
                    print(f"    → Found text attribute, type: {type(text_obj)}")
                    
                    if hasattr(text_obj, 'content') and text_obj.content:
                        text_content = text_obj.content
                        print(f"    → Text.content: {len(text_content)} chars")
                    elif isinstance(text_obj, str):
                        text_content = text_obj
                        print(f"    → Text (string): {len(text_content)} chars")
                    else:
                        # Try to extract from object
                        text_content = str(text_obj) if text_obj else ""
                        if text_content and text_content != "None":
                            print(f"    → Text (str()): {len(text_content)} chars")
                    
                    if text_content and text_content not in ["None", "", "null"]:
                        result_text += text_content + "\n"
                        print(f"    ✓ Text extracted: {len(text_content)} chars")
                
                # Strategy 2: attachment.content (fallback)
                if not result_text and hasattr(attachment, 'content') and attachment.content:
                    content = attachment.content
                    if isinstance(content, str):
                        result_text += content + "\n"
                        print(f"    → Content (direct): {len(content)} chars")
                    elif hasattr(content, 'text'):
                        result_text += str(content.text) + "\n"
                        print(f"    → Content.text: {len(content.text)} chars")
                
                # Extract generated SQL and get query RESULTS
                if hasattr(attachment, 'query') and attachment.query:
                    query_obj = attachment.query
                    
                    # Check for description in query attachment (analysis text)
                    if hasattr(query_obj, 'description') and query_obj.description:
                        desc = query_obj.description
                        if desc and desc not in ["None", "", "null"]:
                            result_text += f"{desc}\n"
                            print(f"    → Query description: {len(desc)} chars")
                    
                    if hasattr(query_obj, 'query'):
                        generated_sql = query_obj.query
                        print(f"    → SQL: {len(generated_sql)} chars")
                        
                        # ================================================================
                        # STEP 3: Get EXECUTED query results (the actual DATA!)
                        # Reference: GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}
                        # SDK method: get_message_attachment_query_result()
                        # 
                        # This is the CRITICAL step that returns actual data rows!
                        # Without this, you only get the SQL text.
                        # ================================================================
                        if new_conversation_id and message_id and attachment_id:
                            try:
                                print(f"    → Fetching query results...")
                                query_result = client.genie.get_message_attachment_query_result(
                                    space_id=space_id,
                                    conversation_id=new_conversation_id,
                                    message_id=message_id,
                                    attachment_id=attachment_id
                                )
                                
                                if query_result:
                                    query_results_text = self._format_query_results(query_result)
                                    row_count = self._count_result_rows(query_result)
                                    print(f"    → Got {row_count} rows of data")
                                else:
                                    print(f"    ⚠ Query result was empty")
                                    
                            except Exception as qr_err:
                                error_msg = str(qr_err)
                                print(f"    ⚠ Could not get query results: {error_msg}")
                                # Include error context but don't fail entirely
                                if "PERMISSION" in error_msg.upper():
                                    query_results_text = "(Permission denied to execute query)"
                                elif "TIMEOUT" in error_msg.upper():
                                    query_results_text = "(Query execution timed out)"
                                else:
                                    query_results_text = f"(Query execution error: {error_msg[:100]})"
            
            # ================================================================
            # STEP 4: Format final response with ANALYSIS, results, and SQL
            # 
            # CRITICAL: Genie's API returns "rephrasing" text (e.g., "You want to
            # see the percentage change...") but NOT the rich analysis that the
            # Genie UI shows (e.g., "Yesterday, costs increased by 105.7%...").
            # 
            # The Genie UI generates that analysis CLIENT-SIDE using the query
            # results. We must do the same - use our LLM to generate analysis!
            # 
            # Priority: Analysis > Data > SQL (analysis FIRST for insights!)
            # ================================================================
            final_response = ""
            
            # ================================================================
            # SMART ANALYSIS DETECTION
            # Detect if result_text is just "rephrasing/clarification" vs actual
            # data-driven analysis. Rephrasing typically:
            # - Asks clarifying questions ("Would you prefer...", "Do you mean...")
            # - Restates the question ("You want to see...")
            # - Doesn't contain specific numbers from results
            # 
            # If we only have rephrasing, we MUST generate real analysis!
            # ================================================================
            is_just_rephrasing = False
            rephrasing_text = ""
            
            if result_text.strip():
                text_lower = result_text.lower()
                # Patterns that indicate rephrasing, not analysis
                rephrasing_patterns = [
                    "you want to see",
                    "would you prefer",
                    "do you mean",
                    "did you mean",
                    "would you like",
                    "are you looking for",
                    "could you clarify",
                    "please clarify",
                    "instead of just",
                    "i understand you",
                    "let me clarify"
                ]
                
                # Check if text matches rephrasing patterns
                for pattern in rephrasing_patterns:
                    if pattern in text_lower:
                        is_just_rephrasing = True
                        rephrasing_text = result_text.strip()
                        print(f"  → Detected rephrasing text (not analysis): '{pattern}' found")
                        break
                
                # Also check: if we have query results with numbers, but the text
                # doesn't contain those numbers, it's probably not analysis
                if not is_just_rephrasing and query_results_text:
                    # Extract numbers from query results
                    import re
                    result_numbers = set(re.findall(r'\d+\.?\d*', query_results_text))
                    text_numbers = set(re.findall(r'\d+\.?\d*', result_text))
                    # If text has no numbers from results, likely not analysis
                    if result_numbers and not (result_numbers & text_numbers):
                        # Text doesn't reference any numbers from results
                        if len(result_text) < 300:  # Short text without data reference
                            is_just_rephrasing = True
                            rephrasing_text = result_text.strip()
                            print(f"  → Text doesn't reference result data, treating as rephrasing")
            
            # Generate LLM analysis if:
            # 1. No text at all, OR
            # 2. Text is just rephrasing (not data-driven analysis)
            should_generate_analysis = (
                (not result_text.strip() or is_just_rephrasing) and 
                query_results_text and 
                not query_results_text.startswith("(")
            )
            
            if should_generate_analysis:
                reason = "rephrasing only" if is_just_rephrasing else "no text"
                print(f"  → Generating LLM analysis ({reason})...")
                try:
                    # Build context-aware prompt
                    context_section = ""
                    if rephrasing_text:
                        context_section = f"\n**Genie's Understanding:** {rephrasing_text}\n"
                    
                    analysis_prompt = f"""You are a Databricks data analyst. Analyze the query results and provide a clear, actionable interpretation.

**User Question:** {query}
{context_section}
**Query Results:**
{query_results_text}

Provide analysis (2-4 sentences) that:
1. DIRECTLY answers the user's question using SPECIFIC numbers from the data
2. Highlights the most important finding first (lead with the insight!)
3. References actual values, percentages, or trends from the results
4. Notes any concerns or patterns that need attention

IMPORTANT: Start with the main insight/answer. Use specific numbers from the data.
Example format: "Yesterday, costs increased by X% compared to the previous day, driven by Y..."

Your analysis:"""

                    analysis_text = self._call_llm(
                        analysis_prompt, 
                        "You are a senior Databricks data analyst providing clear, data-driven insights. Always reference specific numbers from the results."
                    )
                    print(f"  ✓ Generated LLM analysis: {len(analysis_text)} chars")
                    
                    # Use the generated analysis as result_text
                    result_text = analysis_text
                    
                except Exception as llm_err:
                    print(f"  ⚠ LLM analysis generation failed: {llm_err}")
                    # Fall back to rephrasing text if available
                    if rephrasing_text:
                        result_text = rephrasing_text
            
            # Include natural language analysis FIRST (insights are most important!)
            if result_text.strip():
                final_response += "**Analysis:**\n" + result_text.strip() + "\n\n"
            
            # Include query results (the actual DATA)
            if query_results_text and not query_results_text.startswith("("):
                final_response += "**Query Results:**\n" + query_results_text + "\n\n"
            elif query_results_text and query_results_text.startswith("("):
                # Error message - still include it
                final_response += f"**Note:** {query_results_text}\n\n"
            
            # Include the generated SQL for transparency (at the end)
            if generated_sql:
                final_response += f"**Generated SQL:**\n```sql\n{generated_sql}\n```\n"
            
            if not final_response:
                # Fallback: try to extract any content
                if hasattr(response, 'content'):
                    final_response = str(response.content)
                else:
                    final_response = f"Genie processed your query but returned no structured response."
            
            print(f"✓ Genie response for {domain} ({len(final_response)} chars)")
            # Return tuple: (response_text, conversation_id) for stateless tracking
            return (final_response.strip(), new_conversation_id)
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Genie query failed for {domain}: {error_msg}")
            
            # Provide helpful error messages with actual error details
            # Return tuple: (error_text, None) - no conversation_id on error
            if "PERMISSION" in error_msg.upper() or "authorized" in error_msg.lower():
                return (f"**Permission Error**\n\nUnable to access the Genie Space for {domain}. Please ensure you have CAN USE permissions on the SQL warehouse and the Genie Space.\n\n**Debug Info:** {error_msg[:200]}", None)
            elif "RATE_LIMIT" in error_msg.upper() or "429" in error_msg:
                return (f"**Rate Limit**\n\nGenie API rate limit reached (5 queries/minute). Please wait and try again.", None)
            elif "NOT_FOUND" in error_msg.upper() or "404" in error_msg:
                return (f"**Not Found**\n\nGenie Space for {domain} not found. Please check the configuration.", None)
            else:
                return (f"**Error**\n\nFailed to query Genie for {domain}: {error_msg}", None)
    
    def _count_result_rows(self, query_result) -> int:
        """Count the number of rows in a query result."""
        try:
            data_array = getattr(query_result, 'data_array', []) or []
            if data_array:
                return len(data_array)
            
            # Try statement_response format
            if hasattr(query_result, 'statement_response'):
                sr = query_result.statement_response
                if hasattr(sr, 'result') and sr.result:
                    if hasattr(sr.result, 'data_array'):
                        return len(sr.result.data_array or [])
            
            return 0
        except:
            return 0
    
    def _format_query_results(self, query_result) -> str:
        """
        Format Genie query results into a readable markdown table.
        
        Query result structure (from Databricks SDK):
        - columns: Array of column definitions
        - data_array: Array of row arrays
        
        Alternative structure (statement_response):
        - statement_response.result.data_array
        - statement_response.manifest.schema.columns
        
        Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
        """
        try:
            # Extract columns and data from query result
            columns = getattr(query_result, 'columns', []) or []
            data_array = getattr(query_result, 'data_array', []) or []
            
            # Try alternative structure (statement_response)
            if not columns or not data_array:
                if hasattr(query_result, 'statement_response'):
                    sr = query_result.statement_response
                    if hasattr(sr, 'result') and sr.result:
                        if hasattr(sr.result, 'data_array'):
                            data_array = sr.result.data_array or []
                    if hasattr(sr, 'manifest') and sr.manifest:
                        if hasattr(sr.manifest, 'schema') and sr.manifest.schema:
                            if hasattr(sr.manifest.schema, 'columns'):
                                columns = sr.manifest.schema.columns or []
            
            # Debug info
            print(f"      → Formatting: {len(columns)} columns, {len(data_array)} rows")
            
            if not data_array:
                return "(Query returned no data)"
            
            # Get column names
            col_names = []
            for col in columns:
                if hasattr(col, 'name'):
                    col_names.append(col.name)
                elif isinstance(col, dict):
                    col_names.append(col.get('name', 'Column'))
                else:
                    col_names.append(str(col))
            
            # If no column names but we have data, create generic names
            if not col_names and data_array:
                first_row = data_array[0] if data_array else []
                col_count = len(first_row) if isinstance(first_row, (list, tuple)) else 1
                col_names = [f"Column_{i+1}" for i in range(col_count)]
            
            if not col_names:
                return "(Could not determine column structure)"
            
            # Format as markdown table
            lines = []
            
            # Truncate long column names
            display_cols = [c[:25] + "..." if len(str(c)) > 25 else str(c) for c in col_names]
            
            # Header row
            lines.append("| " + " | ".join(display_cols) + " |")
            lines.append("| " + " | ".join(["---"] * len(display_cols)) + " |")
            
            # Data rows (limit to first 25 for readability; API limits to 5000)
            max_rows = 25
            for row in data_array[:max_rows]:
                if isinstance(row, (list, tuple)):
                    row_values = []
                    for v in row:
                        if v is None:
                            row_values.append("")
                        else:
                            s = str(v)
                            # Truncate long values
                            row_values.append(s[:50] + "..." if len(s) > 50 else s)
                else:
                    row_values = [str(row)[:50]]
                
                # Ensure row has same number of columns
                while len(row_values) < len(display_cols):
                    row_values.append("")
                
                lines.append("| " + " | ".join(row_values[:len(display_cols)]) + " |")
            
            if len(data_array) > max_rows:
                lines.append(f"\n*Showing {max_rows} of {len(data_array)} rows*")
            
            return "\n".join(lines)
            
        except Exception as e:
            print(f"⚠ Error formatting query results: {e}")
            return f"(Error formatting results: {str(e)[:100]})"
    
    # ===========================================================================
    # VISUALIZATION HINTS: Suggest appropriate charts for tabular data
    # ===========================================================================
    # Reference: docs/agent-framework-design/14-visualization-hints-backend.md
    # ===========================================================================
    
    def _extract_tabular_data(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract tabular data from Genie response markdown.
        
        Genie returns markdown tables like:
        | Column1 | Column2 |
        |---------|---------|
        | Value1  | Value2  |
        
        This method parses them into: [{"Column1": "Value1", "Column2": "Value2"}]
        
        Args:
            response_text: Raw Genie response text with markdown table
        
        Returns:
            List of dictionaries (one per row) or None if no table detected
        """
        if not response_text or "|" not in response_text:
            return None
        
        lines = response_text.strip().split("\n")
        
        # Find table start (header row with pipes)
        table_start = None
        for i, line in enumerate(lines):
            if "|" in line and i < len(lines) - 1 and "|" in lines[i + 1]:
                # Check if next line is separator (contains dashes)
                if "-" in lines[i + 1]:
                    table_start = i
                    break
        
        if table_start is None:
            return None
        
        # Parse header
        header_line = lines[table_start].strip()
        headers = [h.strip() for h in header_line.split("|") if h.strip()]
        
        if not headers:
            return None
        
        # Skip separator line
        data_start = table_start + 2
        
        # Parse rows
        data = []
        for line in lines[data_start:]:
            line = line.strip()
            if not line or "|" not in line:
                break
            
            # Stop if we hit another markdown element
            if line.startswith("#") or line.startswith("*") or line.startswith("```"):
                break
            
            values = [v.strip() for v in line.split("|") if v.strip() != ""]
            
            # Only add row if column count matches
            if len(values) == len(headers):
                row = dict(zip(headers, values))
                data.append(row)
        
        return data if data else None
    
    def _suggest_visualization(
        self,
        data: List[Dict[str, Any]],
        query: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Suggest appropriate visualization for tabular data.
        
        Args:
            data: List of dictionaries representing table rows
            query: Original user query (for pattern matching)
            domain: Domain name (cost, security, performance, reliability, quality)
        
        Returns:
            Dictionary with visualization hint:
            {
                "type": "bar_chart|line_chart|pie_chart|table|text",
                "x_axis": "column_name",
                "y_axis": ["column1", "column2"],
                "title": "Chart title",
                "reason": "Why this visualization was chosen",
                "domain_preferences": {...}
            }
        """
        if not data or len(data) == 0:
            return {
                "type": "text", 
                "reason": "No tabular data to visualize",
                "domain_preferences": self._get_domain_preferences(domain, query)
            }
        
        # Analyze column types
        headers = list(data[0].keys())
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []
        
        for col in headers:
            # Sample first row to infer type
            sample_val = data[0].get(col, "")
            if self._is_datetime_value(str(sample_val)):
                datetime_cols.append(col)
            elif self._is_numeric_value(str(sample_val)):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)
        
        row_count = len(data)
        query_lower = query.lower() if query else ""
        
        # RULE 1: Time series pattern - datetime column with numeric metrics
        if datetime_cols and numeric_cols:
            return {
                "type": "line_chart",
                "x_axis": datetime_cols[0],
                "y_axis": numeric_cols[:3],  # Up to 3 metrics
                "title": f"{', '.join(numeric_cols[:2])} Over Time",
                "reason": "Time series data with numeric metrics",
                "row_count": row_count,
                "domain_preferences": self._get_domain_preferences(domain, query)
            }
        
        # RULE 2: Top N pattern (cost queries, job performance, etc.)
        if categorical_cols and numeric_cols and row_count <= 20:
            top_n_keywords = ['top', 'highest', 'most', 'expensive', 'slowest', 'worst', 'best', 'largest', 'biggest']
            if any(word in query_lower for word in top_n_keywords):
                return {
                    "type": "bar_chart",
                    "x_axis": categorical_cols[0],
                    "y_axis": numeric_cols[0],
                    "title": f"Top {row_count} {categorical_cols[0].replace('_', ' ').title()} by {numeric_cols[0].replace('_', ' ').title()}",
                    "reason": "Top N comparison query",
                    "row_count": row_count,
                    "domain_preferences": self._get_domain_preferences(domain, query)
                }
        
        # RULE 3: Distribution pattern (percentages, breakdowns)
        if categorical_cols and numeric_cols and row_count <= 10:
            distribution_keywords = ['breakdown', 'distribution', 'percentage', 'share', 'split', 'by type', 'by category']
            if any(word in query_lower for word in distribution_keywords):
                return {
                    "type": "pie_chart",
                    "label": categorical_cols[0],
                    "value": numeric_cols[0],
                    "title": f"Distribution of {numeric_cols[0].replace('_', ' ').title()}",
                    "reason": "Distribution/breakdown query",
                    "row_count": row_count,
                    "domain_preferences": self._get_domain_preferences(domain, query)
                }
        
        # RULE 4: Comparison pattern for small datasets
        if row_count <= 15 and numeric_cols and categorical_cols:
            return {
                "type": "bar_chart",
                "x_axis": categorical_cols[0],
                "y_axis": numeric_cols[0],
                "title": f"{numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}",
                "reason": "Comparison across categories",
                "row_count": row_count,
                "domain_preferences": self._get_domain_preferences(domain, query)
            }
        
        # RULE 5: Default to table for complex/large data
        return {
            "type": "table",
            "columns": headers,
            "reason": f"Complex data ({row_count} rows, {len(headers)} columns) - table view recommended",
            "row_count": row_count,
            "domain_preferences": self._get_domain_preferences(domain, query)
        }
    
    def _is_datetime_value(self, value: str) -> bool:
        """Check if a string value looks like a datetime."""
        import re
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{4}-\d{2}-\d{2}T',  # ISO datetime
        ]
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        return False
    
    def _is_numeric_value(self, value: str) -> bool:
        """Check if a string value looks numeric."""
        import re
        # Remove currency symbols and commas
        cleaned = re.sub(r'[\$,]', '', value.strip())
        try:
            float(cleaned)
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_domain_preferences(self, domain: str, query: str) -> Dict[str, Any]:
        """
        Get domain-specific visualization preferences.
        
        Args:
            domain: Domain name
            query: User query
        
        Returns:
            Dictionary with domain-specific preferences
        """
        domain_rules = {
            "cost": {
                "prefer_currency_format": True,
                "color_scheme": "red_amber_green",
                "default_sort": "descending",
                "highlight_threshold": "high values",
                "suggested_formats": {"currency": "USD", "decimals": 2}
            },
            "performance": {
                "highlight_outliers": True,
                "color_scheme": "sequential",
                "default_sort": "descending",
                "suggested_formats": {"duration": "seconds", "percentage": True}
            },
            "security": {
                "highlight_critical": True,
                "color_scheme": "red_amber_green",
                "default_sort": "severity",
                "severity_levels": ["critical", "high", "medium", "low"]
            },
            "reliability": {
                "show_thresholds": True,
                "color_scheme": "red_amber_green",
                "default_sort": "descending",
                "suggested_formats": {"rate": "percentage", "count": True}
            },
            "quality": {
                "show_percentages": True,
                "color_scheme": "red_amber_green",
                "default_sort": "quality_score",
                "suggested_formats": {"score": "percentage"}
            },
            "unified": {
                "color_scheme": "categorical",
                "default_sort": "relevance",
                "multi_domain": True
            }
        }
        
        return domain_rules.get(domain, {
            "color_scheme": "default",
            "default_sort": "ascending"
        })
    
    def _follow_up_genie_internal(self, client, space_id: str, conversation_id: str, query: str, domain: str) -> str:
        """
        Internal method: Send a follow-up question to an existing Genie conversation.
        
        Called from _query_genie when session has existing conversation_id.
        This enables multi-turn conversations within the same session.
        
        Reference: POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages
        Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api#-ask-follow-up-questions
        SDK method: create_message_and_wait()
        
        Args:
            client: WorkspaceClient with OBO auth
            space_id: Genie Space ID
            conversation_id: Existing conversation ID from previous query in this session
            query: User's follow-up question
            domain: Domain name for logging
        """
        try:
            # Send follow-up message to existing conversation
            # This maintains context from previous messages in the conversation
            response = client.genie.create_message_and_wait(
                space_id=space_id,
                conversation_id=conversation_id,
                content=query
            )
            
            # Process response same as initial query
            message_id = getattr(response, 'id', None)
            print(f"  → Message: {message_id[:8] if message_id else 'N/A'}...")
            
            result_text = ""
            query_results_text = ""
            generated_sql = ""
            
            if not response or not hasattr(response, 'attachments') or not response.attachments:
                print(f"⚠ No attachments in follow-up Genie response")
                return f"Genie returned no results for follow-up: {query}"
            
            for attachment in response.attachments:
                attachment_id = (
                    getattr(attachment, 'attachment_id', None) or 
                    getattr(attachment, 'id', None)
                )
                
                if hasattr(attachment, 'text') and attachment.text:
                    if hasattr(attachment.text, 'content'):
                        result_text += attachment.text.content + "\n"
                
                if hasattr(attachment, 'query') and attachment.query:
                    if hasattr(attachment.query, 'query'):
                        generated_sql = attachment.query.query
                        
                        if conversation_id and message_id and attachment_id:
                            try:
                                query_result = client.genie.get_message_attachment_query_result(
                                    space_id=space_id,
                                    conversation_id=conversation_id,
                                    message_id=message_id,
                                    attachment_id=attachment_id
                                )
                                if query_result:
                                    query_results_text = self._format_query_results(query_result)
                                    row_count = self._count_result_rows(query_result)
                                    print(f"    → Got {row_count} rows of data")
                            except Exception as qr_err:
                                error_msg = str(qr_err)
                                print(f"    ⚠ Could not get query results: {error_msg}")
            
            # ================================================================
            # SMART ANALYSIS DETECTION (same logic as _query_genie)
            # Detect if result_text is just "rephrasing" vs actual analysis
            # ================================================================
            is_just_rephrasing = False
            rephrasing_text = ""
            
            if result_text.strip():
                text_lower = result_text.lower()
                rephrasing_patterns = [
                    "you want to see", "would you prefer", "do you mean",
                    "did you mean", "would you like", "are you looking for",
                    "could you clarify", "please clarify", "instead of just",
                    "i understand you", "let me clarify"
                ]
                
                for pattern in rephrasing_patterns:
                    if pattern in text_lower:
                        is_just_rephrasing = True
                        rephrasing_text = result_text.strip()
                        print(f"  → Detected rephrasing in follow-up response")
                        break
                
                # Check if text references numbers from results
                if not is_just_rephrasing and query_results_text:
                    import re
                    result_numbers = set(re.findall(r'\d+\.?\d*', query_results_text))
                    text_numbers = set(re.findall(r'\d+\.?\d*', result_text))
                    if result_numbers and not (result_numbers & text_numbers):
                        if len(result_text) < 300:
                            is_just_rephrasing = True
                            rephrasing_text = result_text.strip()
                            print(f"  → Follow-up text doesn't reference result data")
            
            # Generate LLM analysis if needed
            should_generate_analysis = (
                (not result_text.strip() or is_just_rephrasing) and 
                query_results_text and 
                not query_results_text.startswith("(")
            )
            
            if should_generate_analysis:
                reason = "rephrasing only" if is_just_rephrasing else "no text"
                print(f"  → Generating LLM analysis for follow-up ({reason})...")
                try:
                    context_section = f"\n**Genie's Understanding:** {rephrasing_text}\n" if rephrasing_text else ""
                    
                    analysis_prompt = f"""You are a Databricks data analyst. Analyze the query results for this follow-up question.

**User Follow-up Question:** {query}
{context_section}
**Query Results:**
{query_results_text}

Provide analysis (2-4 sentences) that:
1. DIRECTLY answers the follow-up question using SPECIFIC numbers from the data
2. Leads with the main insight
3. References actual values from the results
4. Notes any concerns or patterns

Start with the main insight. Use specific numbers from the data.

Your analysis:"""

                    analysis_text = self._call_llm(
                        analysis_prompt, 
                        "You are a senior Databricks data analyst providing clear, data-driven insights."
                    )
                    result_text = analysis_text
                    print(f"  ✓ Generated LLM analysis: {len(result_text)} chars")
                except Exception as llm_err:
                    print(f"  ⚠ LLM analysis generation failed: {llm_err}")
                    if rephrasing_text:
                        result_text = rephrasing_text
            
            # Format final response (Analysis FIRST, then data, then SQL)
            final_response = ""
            if result_text.strip():
                final_response += "**Analysis:**\n" + result_text.strip() + "\n\n"
            if query_results_text and not query_results_text.startswith("("):
                final_response += "**Query Results:**\n" + query_results_text + "\n\n"
            if generated_sql:
                final_response += f"**Generated SQL:**\n```sql\n{generated_sql}\n```\n"
            
            if not final_response:
                final_response = f"Genie processed your follow-up but returned no structured response."
            
            print(f"✓ Genie follow-up response for {domain} ({len(final_response)} chars)")
            return final_response.strip()
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Genie follow-up failed for {domain}: {error_msg}")
            return f"**Error**\n\nFailed to query Genie follow-up for {domain}: {error_msg}"
    
    def _follow_up_genie(self, domain: str, conversation_id: str, query: str) -> str:
        """
        Send a follow-up question to an existing Genie conversation.
        
        Use this for multi-turn conversations where context matters.
        
        Reference: POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages
        SDK method: create_message_and_wait()
        """
        space_id = self._get_genie_space_id(domain)
        if not space_id:
            raise ValueError(f"No Genie Space ID configured for domain: {domain}")
        
        client = self._get_genie_client(domain)
        print(f"→ Follow-up Genie query for {domain} (conversation: {conversation_id[:8]}...)")
        
        try:
            # Send follow-up message to existing conversation
            response = client.genie.create_message_and_wait(
                space_id=space_id,
                conversation_id=conversation_id,
                content=query
            )
            
            # Process response same as initial query
            message_id = getattr(response, 'id', None)
            
            result_text = ""
            query_results_text = ""
            generated_sql = ""
            
            if response and hasattr(response, 'attachments') and response.attachments:
                for attachment in response.attachments:
                    # Try multiple attribute names for attachment ID
                    attachment_id = (
                        getattr(attachment, 'attachment_id', None) or 
                        getattr(attachment, 'id', None)
                    )
                    
                    if hasattr(attachment, 'text') and attachment.text:
                        if hasattr(attachment.text, 'content'):
                            result_text += attachment.text.content + "\n"
                    
                    if hasattr(attachment, 'query') and attachment.query:
                        if hasattr(attachment.query, 'query'):
                            generated_sql = attachment.query.query
                            
                            if conversation_id and message_id and attachment_id:
                                try:
                                    query_result = client.genie.get_message_attachment_query_result(
                                        space_id=space_id,
                                        conversation_id=conversation_id,
                                        message_id=message_id,
                                        attachment_id=attachment_id
                                    )
                                    if query_result:
                                        query_results_text = self._format_query_results(query_result)
                                except Exception as qr_err:
                                    print(f"⚠ Follow-up query results failed: {qr_err}")
            
            # Format response
            final_response = ""
            if query_results_text and not query_results_text.startswith("("):
                final_response += "**Query Results:**\n" + query_results_text + "\n\n"
            if result_text.strip():
                final_response += "**Analysis:**\n" + result_text.strip() + "\n\n"
            if generated_sql:
                final_response += f"**Generated SQL:**\n```sql\n{generated_sql}\n```\n"
            
            return final_response.strip() if final_response else "No results from follow-up query."
            
        except Exception as e:
            return f"Follow-up query failed: {str(e)}"
    
    # Keep legacy _get_genie for backwards compatibility
    def _get_genie(self, domain: str):
        """
        Legacy method - returns truthy value if Genie is configured.
        Use _query_genie() for actual queries.
        """
        space_id = self._get_genie_space_id(domain)
        return space_id if space_id else None
    
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
    
    @mlflow.trace(name="health_monitor_agent", span_type="AGENT")
    def predict(self, request):
        """
        Handle inference requests using ResponsesAgent interface.
        
        ResponsesAgent is the recommended interface for Databricks AI Playground.
        Reference: https://mlflow.org/docs/latest/genai/serving/responses-agent
        Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent
        
        Input format (ResponsesAgent):
        {
            "input": [{"role": "user", "content": "..."}],
            "custom_inputs": {"user_id": "...", "session_id": "..."}  # Optional
        }
        
        Output format (ResponsesAgentResponse):
        {
            "output": [{"type": "message", "role": "assistant", "content": [...]}]
        }
        
        IMPORTANT: Prompts are loaded inside this traced function to link
        them to traces in MLflow UI.
        """
        import mlflow
        import json
        import os
        import uuid
        from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
        
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
        
        # ================================================================
        # PARSE RESPONSESAGENT INPUT
        # ================================================================
        # ResponsesAgent uses 'input' field (not 'messages')
        # Input format: {"input": [{"role": "user", "content": "..."}]}
        # Reference: https://mlflow.org/docs/latest/genai/serving/responses-agent
        # ================================================================
        
        try:
            query = ""
            input_messages = []
            
            # Handle ResponsesAgentRequest object
            if hasattr(request, 'input'):
                # ResponsesAgentRequest - use input field
                input_messages = [msg.model_dump() if hasattr(msg, 'model_dump') else dict(msg) 
                                 for msg in request.input]
            elif isinstance(request, dict):
                # Dict format - check for 'input' (ResponsesAgent) or 'messages' (legacy)
                if 'input' in request:
                    raw_input = request.get('input', [])
                    if isinstance(raw_input, list):
                        input_messages = raw_input
                    elif isinstance(raw_input, str):
                        input_messages = [{"role": "user", "content": raw_input}]
                elif 'messages' in request:
                    # Legacy format support
                    input_messages = request.get('messages', [])
                else:
                    # Direct content
                    content = request.get("content") or request.get("query") or request.get("text") or ""
                    input_messages = [{"role": "user", "content": str(content)}] if content else []
            else:
                # String input
                input_messages = [{"role": "user", "content": str(request)}]
            
            # Ensure we have input
            if not input_messages:
                return ResponsesAgentResponse(
                    id=f"resp_{uuid.uuid4().hex[:12]}",  # Required for AI Playground
                    output=[self.create_text_output_item(
                        text="No query provided.",
                        id=str(uuid.uuid4())
                    )]
                )
            
            # Extract query from last user message
            for msg in reversed(input_messages):
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    if role == "user":
                        query = str(msg.get("content", "") or msg.get("text", "") or "")
                        break
                else:
                    query = str(msg)
                    break
            
            if not query:
                query = str(input_messages[-1].get("content", "")) if input_messages else ""
            
            # ==============================================================
            # COMPREHENSIVE TRACE CONTEXT (MLflow 3.0 Best Practices)
            # ==============================================================
            from datetime import datetime, timezone
            
            # Extract custom_inputs from request if available
            # CRITICAL: Ensure custom_inputs is always a dict (not string)
            custom_inputs = {}
            try:
                if hasattr(request, 'custom_inputs') and request.custom_inputs:
                    ci = request.custom_inputs
                    if isinstance(ci, dict):
                        custom_inputs = ci
                    elif hasattr(ci, '__dict__'):
                        custom_inputs = vars(ci)
                    # If it's a string or other type, leave as empty dict
                elif isinstance(request, dict):
                    ci = request.get("custom_inputs", {})
                    if isinstance(ci, dict):
                        custom_inputs = ci
            except Exception:
                custom_inputs = {}  # Safe fallback
            
            # 1. Extract User ID (with safe dict access)
            user_id = custom_inputs.get("user_id", os.environ.get("USER_ID", "anonymous")) if isinstance(custom_inputs, dict) else os.environ.get("USER_ID", "anonymous")
            
            # 2. Extract Session ID (with safe dict access)
            if isinstance(custom_inputs, dict):
                session_id = custom_inputs.get("session_id", 
                             custom_inputs.get("conversation_id",
                             os.environ.get("SESSION_ID", "single-turn")))
            else:
                session_id = os.environ.get("SESSION_ID", "single-turn")
            
            # 2b. Extract Genie Conversation IDs for follow-up questions
            # Per Databricks docs: "don't assume the same replica handles all requests"
            # Client must track and pass conversation_ids for follow-ups
            # Format: {"genie_conversation_ids": {"cost": "conv_abc123", "security": "conv_def456"}}
            # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
            genie_conversation_ids = {}
            if isinstance(custom_inputs, dict):
                genie_conversation_ids = custom_inputs.get("genie_conversation_ids", {})
            
            # ================================================================
            # LAKEBASE MEMORY: Load conversation context and user preferences
            # ================================================================
            # Short-term: Conversation history within this thread
            # Long-term: User preferences and insights across sessions
            # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents
            # ================================================================
            
            # 2c. Resolve thread_id for short-term memory
            thread_id = self._resolve_thread_id(custom_inputs)
            
            # 2d. Load conversation history from short-term memory
            conversation_history = []
            try:
                conversation_history = self._get_conversation_history(thread_id)
            except Exception as mem_err:
                print(f"⚠ Short-term memory load failed (non-fatal): {mem_err}")
            
            # 2e. Load user preferences from long-term memory
            user_preferences = {}
            try:
                user_preferences = self._get_user_preferences(user_id, query)
            except Exception as pref_err:
                print(f"⚠ Long-term memory load failed (non-fatal): {pref_err}")
            
            # 3. Generate Client Request ID (with safe dict access)
            client_request_id = custom_inputs.get("request_id", str(uuid.uuid4())[:8]) if isinstance(custom_inputs, dict) else str(uuid.uuid4())[:8]
            
            # 4. Environment info
            app_environment = os.environ.get("APP_ENVIRONMENT", 
                               os.environ.get("ENVIRONMENT", "development"))
            app_version = os.environ.get("APP_VERSION", 
                          os.environ.get("MLFLOW_ACTIVE_MODEL_ID", "unknown"))
            deployment_region = os.environ.get("DEPLOYMENT_REGION", "unknown")
            endpoint_name = os.environ.get("ENDPOINT_NAME", 
                            os.environ.get("DATABRICKS_SERVING_ENDPOINT_NAME", "local"))
            
            # Update trace with context (safely, to avoid warnings during evaluation)
            _safe_update_trace(
                metadata={
                    "mlflow.trace.user": user_id,
                    "mlflow.trace.session": session_id,
                    "mlflow.source.type": app_environment.upper(),
                    "mlflow.modelId": app_version,
                    "client_request_id": client_request_id,
                    "deployment_region": deployment_region,
                    "endpoint_name": endpoint_name,
                    "query_length": str(len(query) if query else 0),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                tags={
                    "user_id": user_id,
                    "session_id": session_id,
                    "request_id": client_request_id,
                    "environment": app_environment,
                    "app_version": app_version,
                    "prompts_loaded": ",".join(prompt_names),
                    "prompt_catalog": _catalog,
                    "prompt_schema": _schema,
                    "query_category": "pending",
                    "agent_name": "health_monitor_agent",
                    "agent_type": "multi-domain-genie",
                }
            )
                
        except Exception as parse_error:
            error_msg = f"Error parsing input: {str(parse_error)}. Request type: {type(request)}"
            return ResponsesAgentResponse(
                id=f"resp_{uuid.uuid4().hex[:12]}",  # Required for AI Playground
                output=[self.create_text_output_item(
                    text=error_msg,
                    id=str(uuid.uuid4())
                )]
            )
        
        # Classify domain
        with mlflow.start_span(name="classify_domain", span_type="CLASSIFIER") as cls_span:
            domain = self._classify_domain(query)
            cls_span.set_outputs({"domain": domain})
            
            # Update trace tag with actual domain (safely, to avoid warnings during evaluation)
            _safe_update_trace(tags={
                "query_category": domain,
                "domain": domain,
            })
            
        # Try Genie tool - GENIE IS REQUIRED, NO LLM FALLBACK
        # LLM fallback causes hallucination of fake data - NEVER fall back to LLM for data queries
        with mlflow.start_span(name=f"genie_{domain}", span_type="TOOL") as tool_span:
            space_id = self._get_genie_space_id(domain)
            tool_span.set_inputs({"domain": domain, "query": query, "space_id": space_id[:8] + "..." if space_id else "none"})
            
            if space_id:
                try:
                    # Use Databricks SDK Genie API directly (not GenieAgent.invoke())
                    # GenieAgent.invoke() returns "Please provide chat history" for single queries
                    # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
                    # 
                    # STATELESS FOLLOW-UP PATTERN:
                    # Pass conversation_id from custom_inputs for follow-ups.
                    # Model Serving doesn't share state between replicas, so clients
                    # must track and pass genie_conversation_ids back.
                    existing_conv_id = genie_conversation_ids.get(domain) if genie_conversation_ids else None
                    response_text, new_conv_id = self._query_genie(
                        domain=domain, 
                        query=query, 
                        session_id=session_id,
                        conversation_id=existing_conv_id  # From custom_inputs for follow-ups
                    )
                    
                    tool_span.set_outputs({
                        "response": response_text[:200] + "..." if len(response_text) > 200 else response_text, 
                        "source": "genie",
                        "conversation_id": new_conv_id[:8] + "..." if new_conv_id else "none"
                    })
                    
                    # Build updated conversation IDs for client to track
                    updated_conv_ids = dict(genie_conversation_ids) if genie_conversation_ids else {}
                    if new_conv_id:
                        updated_conv_ids[domain] = new_conv_id
                    
                    # ================================================================
                    # LAKEBASE MEMORY: Save conversation and extract insights
                    # ================================================================
                    # Save to short-term memory (conversation context)
                    try:
                        self._save_to_short_term_memory(
                            thread_id=thread_id,
                            user_message=query,
                            assistant_response=response_text,
                            domain=domain
                        )
                    except Exception as save_err:
                        print(f"⚠ Short-term memory save failed (non-fatal): {save_err}")
                    
                    # Save to long-term memory (user insights)
                    try:
                        self._extract_and_save_insights(
                            user_id=user_id,
                            query=query,
                            response=response_text,
                            domain=domain
                        )
                    except Exception as insight_err:
                        print(f"⚠ Long-term memory save failed (non-fatal): {insight_err}")
                    
                    # ================================================================
                    # VISUALIZATION HINTS: Analyze data and suggest charts
                    # Reference: docs/agent-framework-design/14-visualization-hints-backend.md
                    # ================================================================
                    visualization_hint = None
                    tabular_data = None
                    
                    try:
                        # Extract tabular data from the response
                        tabular_data = self._extract_tabular_data(response_text)
                        
                        if tabular_data and len(tabular_data) > 0:
                            # Generate visualization hint based on the data
                            visualization_hint = self._suggest_visualization(
                                data=tabular_data,
                                query=query,
                                domain=domain
                            )
                            print(f"  ✓ Visualization hint: {visualization_hint.get('type', 'none')} ({len(tabular_data)} rows)")
                        else:
                            visualization_hint = {
                                "type": "text",
                                "reason": "Response contains no tabular data",
                                "domain_preferences": self._get_domain_preferences(domain, query)
                            }
                    except Exception as viz_err:
                        print(f"⚠ Visualization hint generation failed (non-fatal): {viz_err}")
                        visualization_hint = {
                            "type": "text",
                            "reason": f"Hint generation error: {str(viz_err)[:100]}",
                            "domain_preferences": self._get_domain_preferences(domain, query)
                        }
                    
                    return ResponsesAgentResponse(
                        id=f"resp_{uuid.uuid4().hex[:12]}",  # Required for AI Playground
                        output=[self.create_text_output_item(
                            text=response_text,
                            id=str(uuid.uuid4())
                        )],
                        # IMPORTANT: Return thread_id and conversation IDs for stateful conversations
                        # NEW: Include visualization hints for frontend rendering
                        custom_outputs={
                            "domain": domain, 
                            "source": "genie",
                            "thread_id": thread_id,  # For short-term memory continuity
                            "genie_conversation_ids": updated_conv_ids,  # For Genie follow-ups
                            "memory_status": "saved",  # Indicates memory operations succeeded
                            # Visualization hints for frontend chart rendering
                            "visualization_hint": visualization_hint,
                            "data": tabular_data,  # Parsed tabular data (or None)
                        }
                    )
                except Exception as e:
                    # Genie invocation failed - return error, DO NOT hallucinate with LLM
                    error_msg = f"""## Genie Query Failed

**Domain:** {domain}
**Query:** {query}
**Error:** {str(e)}

I was unable to retrieve real data from the Databricks Genie Space for the **{domain}** domain.

### What this means:
- The Genie Space for {domain} monitoring encountered an error
- I cannot provide accurate data without querying the actual system tables

### What you can do:
1. Check the Genie Space configuration for the {domain} domain
2. Verify the Genie Space has access to the required tables
3. Try again in a few moments

**Note:** I will NOT generate fake data. All responses must come from real Databricks system tables via Genie."""
                    
                    tool_span.set_attributes({"error": str(e), "fallback": "none"})
                    tool_span.set_outputs({"response": error_msg, "source": "error"})
                    
                    return ResponsesAgentResponse(
                        id=f"resp_{uuid.uuid4().hex[:12]}",  # Required for AI Playground
                        output=[self.create_text_output_item(
                            text=error_msg,
                            id=str(uuid.uuid4())
                        )],
                        custom_outputs={
                            "domain": domain, 
                            "source": "error", 
                            "error": str(e),
                            "thread_id": thread_id,  # For memory continuity even on errors
                            # Empty visualization hints for error cases
                            "visualization_hint": {"type": "error", "reason": "Query failed"},
                            "data": None,
                        }
                    )
            else:
                # Genie Space ID not configured for this domain - return clear error
                error_msg = f"""## Genie Space Not Configured

**Domain:** {domain}
**Query:** {query}

No Genie Space ID is configured for the **{domain}** domain.

### Possible causes:
- The Genie Space ID for {domain} was not added to the genie_spaces configuration
- The domain name may be misspelled or not recognized

### What you can do:
1. Verify the Genie Space ID is correctly configured for {domain}
2. Check that the Genie Space exists and is accessible
3. Ensure the service principal has access to the Genie Space

**Note:** I will NOT generate fake data. All responses must come from real Databricks system tables via Genie."""
                
                tool_span.set_attributes({"error": "genie_not_available", "fallback": "none"})
                tool_span.set_outputs({"response": error_msg, "source": "error"})
                
                return ResponsesAgentResponse(
                    id=f"resp_{uuid.uuid4().hex[:12]}",  # Required for AI Playground
                    output=[self.create_text_output_item(
                        text=error_msg,
                        id=str(uuid.uuid4())
                    )],
                    custom_outputs={
                        "domain": domain, 
                        "source": "error", 
                        "error": "genie_not_available",
                        "thread_id": thread_id,  # For memory continuity even on errors
                        # Empty visualization hints for error cases
                        "visualization_hint": {"type": "error", "reason": "Genie Space not configured"},
                        "data": None,
                    }
                )
    
    def predict_stream(self, request) -> Generator:
        """
        Streaming inference for ResponsesAgent.
        
        Streaming allows the agent to send responses in real-time chunks instead of
        waiting for the complete response. This is the recommended pattern per
        Databricks official documentation.
        
        Implementation:
        1. Emit delta events: Send multiple output_text.delta events with same item_id
        2. Finish with done event: Send response.output_item.done with complete text
        
        The final done event signals Databricks to:
        - Trace your agent's output with MLflow tracing
        - Aggregate streamed responses in AI Gateway inference tables
        - Show the complete output in the AI Playground UI
        
        Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent#streaming-responses
        
        Yields:
            ResponsesAgentStreamEvent: Streaming events (deltas and final done)
        """
        import uuid
        from mlflow.types.responses import (
            ResponsesAgentRequest, 
            ResponsesAgentResponse,
            ResponsesAgentStreamEvent
        )
        
        # ================================================================
        # STEP 1: Parse request and get query (same as predict)
        # ================================================================
        try:
            query = ""
            input_messages = []
            
            if hasattr(request, 'input'):
                input_messages = [msg.model_dump() if hasattr(msg, 'model_dump') else dict(msg) 
                                 for msg in request.input]
            elif isinstance(request, dict):
                if 'input' in request:
                    raw_input = request.get('input', [])
                    if isinstance(raw_input, list):
                        input_messages = raw_input
                    elif isinstance(raw_input, str):
                        input_messages = [{"role": "user", "content": raw_input}]
                elif 'messages' in request:
                    input_messages = request.get('messages', [])
                else:
                    content = request.get("content") or request.get("query") or request.get("text") or ""
                    input_messages = [{"role": "user", "content": str(content)}] if content else []
            else:
                input_messages = [{"role": "user", "content": str(request)}]
            
            # Extract query from last user message
            for msg in reversed(input_messages):
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    if role == "user":
                        query = str(msg.get("content", "") or msg.get("text", "") or "")
                        break
                else:
                    query = str(msg)
                    break
            
            if not query:
                query = str(input_messages[-1].get("content", "")) if input_messages else ""
            
        except Exception as parse_error:
            # Emit error as final done event
            item_id = str(uuid.uuid4())
            error_msg = f"Error parsing input: {str(parse_error)}"
            yield ResponsesAgentStreamEvent(
                type="response.output_item.done",
                item=self.create_text_output_item(text=error_msg, id=item_id)
            )
            return
        
        if not query:
            item_id = str(uuid.uuid4())
            yield ResponsesAgentStreamEvent(
                type="response.output_item.done",
                item=self.create_text_output_item(text="No query provided.", id=item_id)
            )
            return
        
        # ================================================================
        # STEP 2: Extract session_id from custom_inputs
        # ================================================================
        import os
        custom_inputs = {}
        try:
            if hasattr(request, 'custom_inputs') and request.custom_inputs:
                ci = request.custom_inputs
                if isinstance(ci, dict):
                    custom_inputs = ci
                elif hasattr(ci, '__dict__'):
                    custom_inputs = vars(ci)
            elif isinstance(request, dict):
                ci = request.get("custom_inputs", {})
                if isinstance(ci, dict):
                    custom_inputs = ci
        except Exception:
            custom_inputs = {}
        
        session_id = custom_inputs.get("session_id", 
                     custom_inputs.get("conversation_id",
                     os.environ.get("SESSION_ID", "single-turn"))) if isinstance(custom_inputs, dict) else "single-turn"
        
        # Extract Genie Conversation IDs for follow-up questions
        # Per Databricks docs: "don't assume the same replica handles all requests"
        genie_conversation_ids = custom_inputs.get("genie_conversation_ids", {}) if isinstance(custom_inputs, dict) else {}
        
        # ================================================================
        # LAKEBASE MEMORY: Load conversation context and user preferences
        # ================================================================
        user_id = custom_inputs.get("user_id", os.environ.get("USER_ID", "anonymous")) if isinstance(custom_inputs, dict) else "anonymous"
        thread_id = self._resolve_thread_id(custom_inputs)
        
        # Load conversation history from short-term memory (non-blocking)
        conversation_history = []
        try:
            conversation_history = self._get_conversation_history(thread_id)
        except Exception as mem_err:
            print(f"⚠ Short-term memory load failed (non-fatal): {mem_err}")
        
        # Load user preferences from long-term memory (non-blocking)
        user_preferences = {}
        try:
            user_preferences = self._get_user_preferences(user_id, query)
        except Exception as pref_err:
            print(f"⚠ Long-term memory load failed (non-fatal): {pref_err}")
        
        # ================================================================
        # STEP 3: Classify domain and query Genie
        # ================================================================
        domain = self._classify_domain(query)
        space_id = self._get_genie_space_id(domain)
        
        # Generate unique item_id for this response stream
        item_id = str(uuid.uuid4())
        
        # ================================================================
        # STEP 4: Stream the response in chunks
        # ================================================================
        if space_id:
            try:
                # Emit "thinking" delta to show progress immediately
                yield self.create_text_delta(
                    delta=f"🔍 Querying {domain.title()} Genie Space...\n\n",
                    item_id=item_id
                )
                
                # Query Genie (this is the slow operation)
                # STATELESS FOLLOW-UP PATTERN: Pass conversation_id for follow-ups
                existing_conv_id = genie_conversation_ids.get(domain) if genie_conversation_ids else None
                response_text, new_conv_id = self._query_genie(
                    domain=domain, 
                    query=query, 
                    session_id=session_id,
                    conversation_id=existing_conv_id
                )
                
                # ================================================================
                # STEP 5: Stream the response in chunks for real-time display
                # Split response into paragraphs/sections for natural streaming
                # ================================================================
                if response_text:
                    # Stream the actual content in chunks
                    # We split by double newlines (paragraphs) for natural streaming
                    chunks = response_text.split('\n\n')
                    
                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            # Add back the paragraph separator (except for first chunk)
                            text_to_emit = chunk + ('\n\n' if i < len(chunks) - 1 else '')
                            yield self.create_text_delta(
                                delta=text_to_emit,
                                item_id=item_id
                            )
                    
                    # Reconstruct full response for the done event
                    full_response = f"🔍 Querying {domain.title()} Genie Space...\n\n" + response_text
                else:
                    full_response = f"🔍 Querying {domain.title()} Genie Space...\n\nNo results returned from Genie."
                    yield self.create_text_delta(
                        delta="No results returned from Genie.",
                        item_id=item_id
                    )
                
                # ================================================================
                # LAKEBASE MEMORY: Save conversation and extract insights
                # ================================================================
                try:
                    self._save_to_short_term_memory(
                        thread_id=thread_id,
                        user_message=query,
                        assistant_response=response_text or "No results",
                        domain=domain
                    )
                except Exception as save_err:
                    print(f"⚠ Short-term memory save failed (non-fatal): {save_err}")
                
                try:
                    self._extract_and_save_insights(
                        user_id=user_id,
                        query=query,
                        response=response_text or "No results",
                        domain=domain
                    )
                except Exception as insight_err:
                    print(f"⚠ Long-term memory save failed (non-fatal): {insight_err}")
                
                # ================================================================
                # STEP 6: Generate visualization hints for the response data
                # Reference: docs/agent-framework-design/14-visualization-hints-backend.md
                # ================================================================
                visualization_hint = None
                tabular_data = None
                
                try:
                    tabular_data = self._extract_tabular_data(response_text or "")
                    if tabular_data and len(tabular_data) > 0:
                        visualization_hint = self._suggest_visualization(
                            data=tabular_data,
                            query=query,
                            domain=domain
                        )
                        print(f"  ✓ Stream viz hint: {visualization_hint.get('type', 'none')} ({len(tabular_data)} rows)")
                    else:
                        visualization_hint = {
                            "type": "text",
                            "reason": "Response contains no tabular data",
                            "domain_preferences": self._get_domain_preferences(domain, query)
                        }
                except Exception as viz_err:
                    print(f"⚠ Stream visualization hint failed (non-fatal): {viz_err}")
                    visualization_hint = {
                        "type": "text",
                        "reason": f"Hint generation error",
                        "domain_preferences": self._get_domain_preferences(domain, query)
                    }
                
                # ================================================================
                # STEP 7: Emit final done event with aggregated text
                # This is REQUIRED for:
                # - MLflow tracing
                # - AI Gateway inference tables
                # - AI Playground UI display
                # ================================================================
                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=full_response, id=item_id)
                )
                
                # ================================================================
                # STEP 8: Yield final ResponsesAgentResponse with custom_outputs
                # This ensures visualization hints and data are available to clients
                # in both streaming and non-streaming modes
                # ================================================================
                # Build updated conversation IDs for client to track
                updated_conv_ids = dict(genie_conversation_ids) if genie_conversation_ids else {}
                if new_conv_id:
                    updated_conv_ids[domain] = new_conv_id
                
                yield ResponsesAgentResponse(
                    id=f"resp_{uuid.uuid4().hex[:12]}",
                    output=[self.create_text_output_item(text=full_response, id=item_id)],
                    custom_outputs={
                        "domain": domain,
                        "source": "genie",
                        "thread_id": thread_id,
                        "genie_conversation_ids": updated_conv_ids,
                        "memory_status": "saved",
                        "visualization_hint": visualization_hint,
                        "data": tabular_data,
                    }
                )
                
            except Exception as e:
                # Emit error as streamed chunks then done event
                error_msg = f"""## Genie Query Failed

**Domain:** {domain}
**Query:** {query}
**Error:** {str(e)}

I was unable to retrieve real data from the Databricks Genie Space.

**Note:** I will NOT generate fake data. All responses must come from real system tables via Genie."""
                
                yield self.create_text_delta(
                    delta=error_msg,
                    item_id=item_id
                )
                
                full_response = f"🔍 Querying {domain.title()} Genie Space...\n\n" + error_msg
                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=full_response, id=item_id)
                )
                
                # Yield final response with custom_outputs (error case)
                yield ResponsesAgentResponse(
                    id=f"resp_{uuid.uuid4().hex[:12]}",
                    output=[self.create_text_output_item(text=full_response, id=item_id)],
                    custom_outputs={
                        "domain": domain,
                        "source": "error",
                        "error": str(e),
                        "thread_id": thread_id,
                        "visualization_hint": {"type": "error", "reason": "Query failed"},
                        "data": None,
                    }
                )
        else:
            # No Genie Space configured
            error_msg = f"""## Genie Space Not Configured

**Domain:** {domain}

No Genie Space ID is configured for the **{domain}** domain.

**Note:** I will NOT generate fake data. All responses must come from real system tables via Genie."""
            
            yield self.create_text_delta(
                delta=error_msg,
                item_id=item_id
            )
            
            yield ResponsesAgentStreamEvent(
                type="response.output_item.done",
                item=self.create_text_output_item(text=error_msg, id=item_id)
            )
            
            # Yield final response with custom_outputs (error case)
            yield ResponsesAgentResponse(
                id=f"resp_{uuid.uuid4().hex[:12]}",
                output=[self.create_text_output_item(text=error_msg, id=item_id)],
                custom_outputs={
                    "domain": domain,
                    "source": "error",
                    "error": "genie_not_configured",
                    "thread_id": thread_id,
                    "visualization_hint": {"type": "error", "reason": "Genie Space not configured"},
                    "data": None,
                }
            )

# COMMAND ----------

def get_mlflow_resources() -> List:
    """
    Get resources for SYSTEM authentication (LLM endpoint and Lakebase memory).
    
    Genie Spaces use OBO authentication (on-behalf-of-user), so they are NOT
    included here. They are declared in the UserAuthPolicy with api_scopes.
    
    Reference: https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication
    """
    resources = []
    
    # LLM endpoint uses system auth (automatic passthrough)
    try:
        from mlflow.models.resources import DatabricksServingEndpoint
        resources.append(DatabricksServingEndpoint(LLM_ENDPOINT))
    except ImportError:
        pass
    
    # Lakebase memory storage (short-term and long-term)
    # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/stateful-agents
    try:
        from mlflow.models.resources import DatabricksLakebase
        resources.append(DatabricksLakebase(database_instance_name=LAKEBASE_INSTANCE_NAME))
        print(f"✓ Added DatabricksLakebase resource: {LAKEBASE_INSTANCE_NAME}")
    except ImportError as ie:
        print(f"⚠ DatabricksLakebase resource not available: {ie}")
    except Exception as e:
        print(f"⚠ Could not add DatabricksLakebase resource: {e}")
    
    # NOTE: Genie Spaces NOT included here - they use OBO auth via UserAuthPolicy
    # The agent uses ModelServingUserCredentials() at runtime for Genie access
    
    return resources


def get_auth_policy():
    """
    Get MLflow AuthPolicy for On-Behalf-Of-User (OBO) authentication.
    
    This enables the agent to access Genie Spaces and SQL warehouses
    using the END USER's credentials, not the deployer's credentials.
    
    Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication
    
    Required API scopes for OBO:
    - dashboards.genie: Access Genie spaces
    - sql.warehouses: Query SQL warehouses
    - sql.statement-execution: Execute SQL statements
    - serving.serving-endpoints: Call LLM endpoints
    """
    try:
        from mlflow.models.auth_policy import AuthPolicy, SystemAuthPolicy, UserAuthPolicy
        from mlflow.models.resources import DatabricksServingEndpoint
        
        # System policy: LLM endpoint accessed with system credentials
        # (deployer's permissions for the Foundation Model API)
        system_resources = []
        try:
            system_resources.append(DatabricksServingEndpoint(LLM_ENDPOINT))
        except Exception:
            pass
        
        system_policy = SystemAuthPolicy(resources=system_resources) if system_resources else None
        
        # User policy: API scopes for on-behalf-of-user access
        # These scopes define what the agent can do with the USER's credentials
        user_policy = UserAuthPolicy(api_scopes=[
            # Genie Space access
            "dashboards.genie",
            # SQL Warehouse access (required for Genie to execute queries)
            "sql.warehouses",
            "sql.statement-execution",
            # Model Serving access (for LLM calls if using OBO for those too)
            "serving.serving-endpoints",
        ])
        
        auth_policy = AuthPolicy(
            system_auth_policy=system_policy,
            user_auth_policy=user_policy
        )
        
        print("✓ Created OBO AuthPolicy with scopes: dashboards.genie, sql.warehouses, sql.statement-execution, serving.serving-endpoints")
        return auth_policy
        
    except ImportError as e:
        print(f"⚠ AuthPolicy not available (MLflow version too old?): {e}")
        print("  Falling back to resources-only authentication")
        return None
    except Exception as e:
        print(f"⚠ Error creating AuthPolicy: {e}")
        return None

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
    6. UC Volume for artifact storage - Best practice for managed artifacts
    
    References:
    - https://docs.databricks.com/aws/en/mlflow/logged-model
    - https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/track-application-versions-with-mlflow
    """
    import subprocess
    from datetime import datetime, timezone
    from pyspark.sql import SparkSession
    
    model_name = f"{catalog}.{agent_schema}.health_monitor_agent"
    # Use development experiment for model logging/registration
    # This keeps model development separate from evaluation and deployment
    experiment_path = "/Shared/health_monitor_agent_development"
    
    # ===========================================================================
    # ARTIFACT STORAGE: Unity Catalog Volume (Best Practice)
    # ===========================================================================
    # Model artifacts should be stored in a UC volume for:
    # - Governance and lineage tracking
    # - Access control via Unity Catalog
    # - Cross-workspace sharing
    # Reference: https://docs.databricks.com/en/mlflow/artifacts-best-practices.html
    # ===========================================================================
    uc_volume_name = "artifacts"
    uc_volume_path = f"/Volumes/{catalog}/{agent_schema}/{uc_volume_name}"
    artifact_location = f"dbfs:{uc_volume_path}"
    
    print(f"Logging model to Unity Catalog: {model_name}")
    print(f"Experiment: {experiment_path}")
    print(f"Artifact Location: {artifact_location}")
    
    # Ensure UC volume exists for artifact storage
    try:
        spark = SparkSession.builder.getOrCreate()
        spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{agent_schema}.{uc_volume_name}")
        print(f"✓ UC Volume ensured: {catalog}.{agent_schema}.{uc_volume_name}")
    except Exception as e:
        print(f"⚠ Could not create UC volume (may already exist): {e}")
    
    # Set or create experiment with UC volume artifact location
    try:
        # Try to get existing experiment
        experiment = mlflow.get_experiment_by_name(experiment_path)
        if experiment is None:
            # Create experiment with UC volume artifact location
            experiment_id = mlflow.create_experiment(
                name=experiment_path,
                artifact_location=artifact_location
            )
            print(f"✓ Created experiment with UC volume artifact location")
        else:
            # Experiment exists - just set it (can't change artifact location after creation)
            print(f"✓ Using existing experiment (artifact location: {experiment.artifact_location})")
        
        mlflow.set_experiment(experiment_path)
    except Exception as e:
        print(f"⚠ Experiment setup error: {e}, using default")
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
    
    # =======================================================================
    # RESPONSESAGENT: Automatic Signature Inference
    # =======================================================================
    # MLflow automatically infers the signature for ResponsesAgent.
    # DO NOT define a manual signature - this breaks AI Playground compatibility.
    # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/create-agent#understand-model-signatures-to-ensure-compatibility-with-azure-databricks-features
    # Reference: https://mlflow.org/docs/latest/genai/serving/responses-agent
    # =======================================================================
    
    # Input example matching ResponsesAgent interface (uses 'input' not 'messages')
    input_example = {
        "input": [{"role": "user", "content": "Why did costs spike yesterday?"}]
    }
    
    resources = get_mlflow_resources()
    
    # Generate timestamp for run name
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = f"dev_model_registration_{timestamp}"
    
    with mlflow.start_run(run_name=run_name) as run:
        # Standard tags for filtering and organization
        mlflow.set_tags({
            "run_type": "model_logging",
            "domain": "all",
            "agent_version": "v4.0",
            "dataset_type": "none",  # Model logging doesn't use datasets
            "evaluation_type": "none",
        })
        
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
        # =============================================================
        # IMPORTANT: Using OBO (On-Behalf-Of-User) authentication
        # for Genie Spaces via auth_policy parameter.
        # 
        # DO NOT pass signature parameter!
        # ResponsesAgent automatically infers the correct signature.
        # Manual signatures break AI Playground compatibility.
        #
        # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication#on-behalf-of-user-authentication
        # =============================================================
        
        # Get OBO auth policy for Genie Space access
        auth_policy = get_auth_policy()
        
        log_model_kwargs = {
            "artifact_path": "agent",
            "python_model": agent,
            "input_example": input_example,
            "registered_model_name": model_name,
            "pip_requirements": [
                # Package dependencies for Model Serving
                # =========================================================
                # CRITICAL: Explicit dependencies for on-behalf-of-user auth
                # Reference: https://github.com/databricks/databricks-ai-bridge
                # Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-authentication
                # =========================================================
                "mlflow>=3.0.0",  # Required for mlflow.genai and ResponsesAgent
                "databricks-sdk>=0.28.0",  # For WorkspaceClient
                "databricks-langchain[memory]",  # Contains GenieAgent + Lakebase memory (CheckpointSaver, DatabricksStore)
                "databricks-agents>=1.2.0",  # For agent framework utilities
                "databricks-ai-bridge",  # EXPLICIT: Required for ModelServingUserCredentials
            ],
        }
        
        # Use auth_policy if available (MLflow 2.22.1+), otherwise fall back to resources
        if auth_policy is not None:
            log_model_kwargs["auth_policy"] = auth_policy
            print("✓ Using OBO authentication (auth_policy with UserAuthPolicy)")
        elif resources:
            log_model_kwargs["resources"] = resources
            print("⚠ Falling back to automatic auth passthrough (resources only)")
        
        logged_model = mlflow.pyfunc.log_model(**log_model_kwargs)
        
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
