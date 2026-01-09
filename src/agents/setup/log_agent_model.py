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

class HealthMonitorAgent(mlflow.pyfunc.ResponsesAgent):
    """
    Health Monitor Agent implementing MLflow 3.0 ResponsesAgent pattern.
    
    ResponsesAgent is the recommended interface for Databricks AI Playground
    compatibility. It provides:
    - Automatic signature inference (no manual schema needed)
    - AI Playground compatibility
    - Streaming support
    - Multi-agent and tool-calling support
    - MLflow tracing integration
    
    Reference: https://mlflow.org/docs/latest/genai/serving/responses-agent
    Reference: https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/author-agent
    
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
        # GENIE CONVERSATION TRACKING FOR FOLLOW-UP QUESTIONS
        # Per Databricks Genie API best practices:
        # - Start a new conversation for each SESSION
        # - Use create_message() for follow-ups within same session
        # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
        # ================================================================
        # Dict: {session_id: {domain: conversation_id}}
        self._genie_conversations = {}
        
        print(f"Agent initialized. LLM: {self.llm_endpoint}")
    
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
        # Genie conversation tracking for follow-ups
        self._genie_conversations = {}
        print(f"Agent loaded. LLM: {self.llm_endpoint}")
    
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
    
    def _query_genie(self, domain: str, query: str, session_id: str = None) -> str:
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
        
        Args:
            domain: Domain to query (cost, security, etc.)
            query: User's question
            session_id: Optional session ID for conversation continuity
        """
        import time
        
        space_id = self._get_genie_space_id(domain)
        if not space_id:
            raise ValueError(f"No Genie Space ID configured for domain: {domain}")
        
        client = self._get_genie_client(domain)
        
        # ================================================================
        # GENIE CONVERSATION CONTINUITY
        # Per Databricks docs: "Start a new conversation for each session"
        # Within a session, reuse conversation_id for follow-up context
        # Reference: https://learn.microsoft.com/en-us/azure/databricks/genie/conversation-api
        # ================================================================
        existing_conversation_id = None
        if session_id:
            if session_id not in self._genie_conversations:
                self._genie_conversations[session_id] = {}
            existing_conversation_id = self._genie_conversations[session_id].get(domain)
        
        # Use existing conversation for follow-ups within same session
        if existing_conversation_id:
            print(f"→ Follow-up Genie query for {domain} (conversation: {existing_conversation_id[:8]}...)")
            return self._follow_up_genie_internal(
                client, space_id, existing_conversation_id, query, domain
            )
        
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
            conversation_id = getattr(response, 'conversation_id', None)
            message_id = getattr(response, 'id', None) or getattr(response, 'message_id', None)
            
            # Store conversation_id for follow-ups within this session
            if session_id and conversation_id:
                self._genie_conversations[session_id][domain] = conversation_id
                print(f"  → Stored conversation_id for session {session_id[:8]}...")
            
            # Debug: Print response structure
            print(f"  → Conversation: {conversation_id[:8] if conversation_id else 'N/A'}...")
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
                return f"Genie returned no results for: {query}"
            
            for attachment in response.attachments:
                # Try multiple attribute names for attachment ID
                # SDK may use 'attachment_id' or 'id' depending on version
                attachment_id = (
                    getattr(attachment, 'attachment_id', None) or 
                    getattr(attachment, 'id', None)
                )
                
                # Debug: Print available attributes to diagnose
                if not attachment_id:
                    attachment_attrs = [a for a in dir(attachment) if not a.startswith('_')]
                    print(f"  → Attachment attributes: {attachment_attrs[:10]}...")
                
                print(f"  → Processing attachment: {attachment_id[:8] if attachment_id else 'unknown'}...")
                
                # Extract text response (natural language explanation)
                if hasattr(attachment, 'text') and attachment.text:
                    text_content = ""
                    if hasattr(attachment.text, 'content'):
                        text_content = attachment.text.content
                    else:
                        text_content = str(attachment.text)
                    if text_content:
                        result_text += text_content + "\n"
                        print(f"    → Text: {len(text_content)} chars")
                
                # Extract generated SQL and get query RESULTS
                if hasattr(attachment, 'query') and attachment.query:
                    if hasattr(attachment.query, 'query'):
                        generated_sql = attachment.query.query
                        print(f"    → SQL: {len(generated_sql)} chars")
                        
                        # ================================================================
                        # STEP 3: Get EXECUTED query results (the actual DATA!)
                        # Reference: GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}
                        # SDK method: get_message_attachment_query_result()
                        # 
                        # This is the CRITICAL step that returns actual data rows!
                        # Without this, you only get the SQL text.
                        # ================================================================
                        if conversation_id and message_id and attachment_id:
                            try:
                                print(f"    → Fetching query results...")
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
            # STEP 4: Format final response with results, SQL, and explanation
            # Priority: Data > Explanation > SQL (so users see results first)
            # ================================================================
            final_response = ""
            
            # Include query results FIRST (the actual DATA - most important!)
            if query_results_text and not query_results_text.startswith("("):
                final_response += "**Query Results:**\n" + query_results_text + "\n\n"
            elif query_results_text.startswith("("):
                # Error message - still include it
                final_response += f"**Note:** {query_results_text}\n\n"
            
            # Include natural language explanation
            if result_text.strip():
                final_response += "**Analysis:**\n" + result_text.strip() + "\n\n"
            
            # Include the generated SQL for transparency
            if generated_sql:
                final_response += f"**Generated SQL:**\n```sql\n{generated_sql}\n```\n"
            
            if not final_response:
                # Fallback: try to extract any content
                if hasattr(response, 'content'):
                    final_response = str(response.content)
                else:
                    final_response = f"Genie processed your query but returned no structured response."
            
            print(f"✓ Genie response for {domain} ({len(final_response)} chars)")
            return final_response.strip()
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Genie query failed for {domain}: {error_msg}")
            
            # Provide helpful error messages with actual error details
            if "PERMISSION" in error_msg.upper() or "authorized" in error_msg.lower():
                return f"**Permission Error**\n\nUnable to access the Genie Space for {domain}. Please ensure you have CAN USE permissions on the SQL warehouse and the Genie Space.\n\n**Debug Info:** {error_msg[:200]}"
            elif "RATE_LIMIT" in error_msg.upper() or "429" in error_msg:
                return f"**Rate Limit**\n\nGenie API rate limit reached (5 queries/minute). Please wait and try again."
            elif "NOT_FOUND" in error_msg.upper() or "404" in error_msg:
                return f"**Not Found**\n\nGenie Space for {domain} not found. Please check the configuration."
            else:
                return f"**Error**\n\nFailed to query Genie for {domain}: {error_msg}"
    
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
            
            # Format final response
            final_response = ""
            if query_results_text and not query_results_text.startswith("("):
                final_response += "**Query Results:**\n" + query_results_text + "\n\n"
            if result_text.strip():
                final_response += "**Analysis:**\n" + result_text.strip() + "\n\n"
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
            
            # Update trace with context
            try:
                mlflow.update_current_trace(
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
            except Exception as trace_err:
                print(f"Trace context update failed (non-fatal): {trace_err}")
                
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
            
            # Update trace tag with actual domain (tags are mutable)
            try:
                mlflow.update_current_trace(tags={
                    "query_category": domain,
                    "domain": domain,
                })
            except Exception:
                pass
            
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
                    # Pass session_id for conversation continuity (follow-ups within same session)
                    response = self._query_genie(domain, query, session_id=session_id)
                    
                    tool_span.set_outputs({"response": response[:200] + "..." if len(response) > 200 else response, "source": "genie"})
                    
                    return ResponsesAgentResponse(
                        id=f"resp_{uuid.uuid4().hex[:12]}",  # Required for AI Playground
                        output=[self.create_text_output_item(
                            text=response,
                            id=str(uuid.uuid4())
                        )],
                        custom_outputs={"domain": domain, "source": "genie"}
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
                        custom_outputs={"domain": domain, "source": "error", "error": str(e)}
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
                    custom_outputs={"domain": domain, "source": "error", "error": "genie_not_available"}
                )

# COMMAND ----------

def get_mlflow_resources() -> List:
    """
    Get resources for SYSTEM authentication (LLM endpoint only).
    
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
                "databricks-langchain",  # Contains GenieAgent
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
