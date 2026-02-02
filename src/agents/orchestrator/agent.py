"""
Health Monitor Agent
====================

TRAINING MATERIAL: Multi-Agent Orchestration with MLflow ChatAgent
-------------------------------------------------------------------

This module implements the main agent class for the Databricks Health Monitor.
It serves as a comprehensive example of building production-grade AI agents
using MLflow's ChatAgent interface for deployment to Databricks Model Serving.

ARCHITECTURE OVERVIEW:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HealthMonitorAgent                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  predict() / predict_stream()                                        │   │
│  │    ↓                                                                 │   │
│  │  Intent Classification → Route to Domain Workers → Synthesize       │   │
│  │    ↓                         ↓                        ↓              │   │
│  │  LangGraph             Genie Spaces            LLM Response         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  State Management: Lakebase Checkpointer (short-term memory)               │
│  Tracing: MLflow GenAI Tracing (observability)                             │
│  Resources: Genie Spaces, SQL Warehouses, LLM Endpoints                    │
└─────────────────────────────────────────────────────────────────────────────┘

KEY CONCEPTS DEMONSTRATED:
1. MLflow ChatAgent Interface - Required for Databricks AI Playground compatibility
2. LangGraph Orchestration - Multi-agent workflow management
3. Lakebase Memory - Conversation state persistence across sessions
4. MLflow Tracing - Production observability with span types
5. Resource Declaration - Automatic authentication passthrough
6. Streaming Responses - Real-time feedback to users

WHY CHATAGENT (vs ResponsesAgent):
- ChatAgent is the established interface for Databricks Model Serving
- Provides automatic signature inference for AI Playground compatibility
- ResponsesAgent is newer (MLflow 3.1+) but ChatAgent is more battle-tested
- Both support streaming; ChatAgent has more deployment examples

BEST PRACTICES FOLLOWED:
- Lazy initialization of expensive resources (graph, checkpointer)
- Graceful fallback for optional dependencies (DatabricksLakebase)
- Comprehensive error handling with meaningful error messages
- MLflow tracing decorators for observability
- Type hints for maintainability
- Docstrings for self-documentation

ALTERNATIVES CONSIDERED:
- Direct LLM calls (rejected: no data grounding, hallucination risk)
- Single-agent architecture (rejected: doesn't scale to 5 domains)
- Custom REST API (rejected: loses Databricks platform integration)
- LangChain Agents (rejected: LangGraph provides better control)

Based on MLflow GenAI patterns and Databricks agent best practices.
Reference: https://docs.databricks.com/aws/en/generative-ai/agent-framework/
"""

# =============================================================================
# IMPORTS SECTION
# =============================================================================
# BEST PRACTICE: Group imports by category (standard library, third-party, local)
# This makes dependencies clear and helps with debugging import issues.

from typing import List, Optional, Dict, Any
import uuid
import mlflow

# MLflow ChatAgent Interface
# --------------------------
# WHY ChatAgent: This is the standard interface for Databricks Model Serving.
# The ChatAgent class provides:
# - predict() for synchronous requests
# - predict_stream() for streaming responses (user feedback during processing)
# - Automatic model signature inference (required for AI Playground)
#
# ALTERNATIVE: mlflow.pyfunc.PythonModel (lower-level, manual signature needed)
from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import (
    ChatAgentMessage,      # Standard message format (role, content)
    ChatAgentResponse,     # Response wrapper with metadata
    ChatContext,           # Request context (user_id, conversation_id)
)

# Databricks SDK
# --------------
# WHY WorkspaceClient: Provides authenticated access to Databricks APIs.
# Used for: Genie Spaces, SQL Warehouses, Model Serving endpoints.
# ALTERNATIVE: REST API calls (more verbose, same functionality)
from databricks.sdk import WorkspaceClient

# =============================================================================
# CONDITIONAL IMPORTS: MLflow Resources
# =============================================================================
# PATTERN: Graceful degradation for optional features
# 
# WHY THIS PATTERN:
# - MLflow versions may not have all resource types
# - DatabricksLakebase is newer (MLflow 3.3+)
# - Code should work on older MLflow versions without crashing
#
# WHAT THESE RESOURCES DO:
# - Enable "Automatic Authentication Passthrough" in Model Serving
# - Databricks creates service principals with access to declared resources
# - No manual credential management needed
#
# Reference: https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication

try:
    from mlflow.models.resources import (
        DatabricksServingEndpoint,  # LLM endpoints for inference
        DatabricksGenieSpace,       # Genie Spaces for data queries (MLflow 2.17.1+)
        DatabricksSQLWarehouse,     # SQL Warehouses for direct queries (MLflow 2.16.1+)
    )
    # DatabricksLakebase may not be available in all MLflow versions
    # WHAT IS LAKEBASE: Managed memory storage for agent conversations
    # Provides: Short-term (checkpointing) and long-term (knowledge) memory
    try:
        from mlflow.models.resources import DatabricksLakebase
        _HAS_LAKEBASE_RESOURCE = True
    except ImportError:
        DatabricksLakebase = None
        _HAS_LAKEBASE_RESOURCE = False
except ImportError:
    # Fallback for older MLflow versions without these resources
    # IMPACT: Authentication passthrough won't work, but basic agent still runs
    DatabricksServingEndpoint = None
    DatabricksGenieSpace = None
    DatabricksSQLWarehouse = None
    DatabricksLakebase = None
    _HAS_LAKEBASE_RESOURCE = False

# =============================================================================
# LOCAL IMPORTS
# =============================================================================
# PATTERN: Relative imports for local modules
# WHY: Makes the package self-contained and refactoring-friendly

from .graph import create_orchestrator_graph  # LangGraph workflow definition
from .state import create_initial_state       # State initialization helper
from ..memory import get_checkpoint_saver, ShortTermMemory  # Memory management
from ..config import settings                 # Centralized configuration


# =============================================================================
# MAIN AGENT CLASS
# =============================================================================
# TRAINING MATERIAL: This class demonstrates production agent implementation
# patterns that are essential for Databricks Model Serving deployment.

class HealthMonitorAgent(ChatAgent):
    """
    Databricks Health Monitor Multi-Agent System.
    
    TRAINING MATERIAL: Understanding the ChatAgent Interface
    =========================================================
    
    This class demonstrates how to build a production-grade AI agent
    that can be deployed to Databricks Model Serving and used in:
    - AI Playground (interactive testing)
    - Agent Evaluation (quality assessment)
    - Production APIs (real user traffic)
    
    INHERITANCE HIERARCHY:
    ----------------------
    mlflow.pyfunc.PythonModel          (base class - any ML model)
        ↓
    mlflow.pyfunc.ChatAgent            (chat-specific interface)
        ↓
    HealthMonitorAgent                 (our implementation)
    
    WHY INHERIT FROM ChatAgent:
    ---------------------------
    1. Automatic signature inference for AI Playground compatibility
    2. Standardized input/output format (messages, context)
    3. Built-in streaming support via predict_stream()
    4. Databricks platform integration (tracing, serving)
    
    DESIGN PATTERN: Lazy Initialization
    ------------------------------------
    Expensive resources (graph, checkpointer) are created on first use,
    not during __init__. This allows:
    - Fast agent instantiation (important for cold starts)
    - Graceful handling of configuration errors
    - Testing without full resource setup
    
    MEMORY ARCHITECTURE:
    --------------------
    ┌─────────────────────────────────────────────────────────────┐
    │                    Memory Layers                             │
    ├─────────────────────────────────────────────────────────────┤
    │  SHORT-TERM (Lakebase CheckpointSaver)                      │
    │  - Conversation history within a session                    │
    │  - LangGraph state checkpoints                              │
    │  - Keyed by thread_id (conversation identifier)             │
    ├─────────────────────────────────────────────────────────────┤
    │  LONG-TERM (Lakebase DatabricksStore)                       │
    │  - User preferences across sessions                         │
    │  - Historical patterns and insights                         │
    │  - Keyed by user_id (persistent identifier)                 │
    └─────────────────────────────────────────────────────────────┘
    
    MULTI-AGENT WORKFLOW:
    ---------------------
    1. User query arrives at predict()
    2. Orchestrator classifies intent → determines relevant domains
    3. Domain workers execute in parallel (cost, security, etc.)
    4. Each worker queries its Genie Space for real data
    5. Synthesizer combines results into coherent response
    6. Response returned with metadata (sources, confidence)

    Features:
        - Multi-agent orchestration via LangGraph
        - Short-term memory via Lakebase CheckpointSaver
        - Long-term memory via Lakebase DatabricksStore
        - MLflow tracing for all operations
        - Genie Spaces as data interface

    Usage:
        agent = HealthMonitorAgent()
        response = agent.predict(
            messages=[ChatAgentMessage(role="user", content="Why did costs spike?")],
            context=ChatContext(conversation_id="conv_123")
        )
    
    TESTING LOCALLY:
    ----------------
    # In a Databricks notebook:
    agent = HealthMonitorAgent()
    
    # Simulate a user query
    from mlflow.types.agent import ChatAgentMessage
    messages = [ChatAgentMessage(role="user", content="Why did costs spike?")]
    
    # Get response
    response = agent.predict(messages=messages)
    print(response.messages[-1].content)
    
    DEPLOYMENT:
    -----------
    See log_agent_to_mlflow() function below for deployment patterns.
    """

    def __init__(self):
        """
        Initialize the Health Monitor Agent.
        
        TRAINING MATERIAL: Agent Initialization Best Practices
        ========================================================
        
        WHAT HAPPENS HERE:
        1. Create WorkspaceClient for Databricks API access
        2. Initialize graph and checkpointer as None (lazy loading)
        
        WHAT DOES NOT HAPPEN HERE (and why):
        - LangGraph compilation: Too expensive for cold starts
        - Lakebase connection: May not be needed for all requests
        - Genie Space initialization: Loaded per-request by workers
        
        LAZY LOADING PATTERN:
        ---------------------
        Instead of:
            self._graph = create_and_compile_graph()  # 2-3 seconds
        
        We do:
            self._graph = None
            # Later, on first use:
            if self._graph is None:
                self._graph = create_and_compile_graph()
        
        BENEFITS:
        - Fast __init__ (< 100ms)
        - Errors surface during actual use, not import time
        - Testing can mock individual components
        
        WORKSPACE CLIENT:
        -----------------
        WHY CREATED IN __init__: Lightweight, needed by most operations
        AUTHENTICATION: Automatic in Databricks (managed identity)
        OUTSIDE DATABRICKS: Requires DATABRICKS_HOST + DATABRICKS_TOKEN
        """
        self.workspace_client = WorkspaceClient()
        self._graph = None          # LangGraph workflow (lazy)
        self._checkpointer = None   # Lakebase checkpointer (lazy)

    @property
    def graph(self):
        """
        Lazily create the orchestrator graph.
        
        TRAINING MATERIAL: Python @property for Lazy Initialization
        =============================================================
        
        WHAT IS @property:
        A decorator that makes a method behave like an attribute.
        Calling `agent.graph` invokes this method automatically.
        
        WHY USE @property HERE:
        1. Encapsulation: Hide the creation logic from callers
        2. Lazy loading: Only create when first accessed
        3. Caching: Create once, reuse on subsequent calls
        
        LANGGRAPH COMPILATION:
        ----------------------
        create_orchestrator_graph() returns an uncompiled StateGraph.
        compile() transforms it into an executable CompiledGraph.
        
        The compilation process:
        1. Validates all nodes and edges
        2. Creates execution schedule
        3. Attaches checkpointer for state persistence
        
        WITH CHECKPOINTER:
        ------------------
        The checkpointer enables "memory" across graph invocations:
        - Each invoke() call saves state to Lakebase
        - Next invoke() with same thread_id retrieves state
        - Enables multi-turn conversations
        
        WITHOUT CHECKPOINTER:
        ---------------------
        - Each invoke() starts fresh
        - No conversation history
        - Suitable for stateless queries only
        
        PRODUCTION CONSIDERATION:
        -------------------------
        In Model Serving, each replica maintains its own graph instance.
        The graph is stateless; all state lives in the checkpointer (Lakebase).
        This enables horizontal scaling without state synchronization.
        """
        if self._graph is None:
            workflow = create_orchestrator_graph()
            # Compile with checkpointer for state persistence
            # WHY CONTEXT MANAGER: Ensures clean connection handling
            with get_checkpoint_saver() as checkpointer:
                self._graph = workflow.compile(checkpointer=checkpointer)
        return self._graph

    # =========================================================================
    # HELPER METHODS: Identity Resolution
    # =========================================================================
    # TRAINING MATERIAL: These methods demonstrate how to extract user identity
    # from multiple potential sources in a consistent, priority-based manner.

    def _resolve_thread_id(
        self,
        custom_inputs: Optional[Dict] = None,
        context: Optional[ChatContext] = None,
    ) -> str:
        """
        Resolve thread ID for conversation continuity.
        
        TRAINING MATERIAL: Thread ID and Conversation Management
        =========================================================
        
        WHAT IS A THREAD ID:
        A unique identifier that groups messages in a conversation.
        All messages with the same thread_id share state/memory.
        
        WHY MULTIPLE SOURCES:
        Different clients provide identity differently:
        - AI Playground: Uses context.conversation_id
        - Custom apps: May use custom_inputs["thread_id"]
        - API calls: May not provide either (new conversation)
        
        PRIORITY ORDER (highest to lowest):
        1. custom_inputs["thread_id"] - Explicit override
        2. context.conversation_id   - Standard ChatAgent field
        3. New UUID                  - Fresh conversation
        
        WHY THIS ORDER:
        - Explicit > Implicit > Default
        - Allows testing with specific thread IDs
        - Maintains backward compatibility
        
        MEMORY IMPLICATIONS:
        --------------------
        thread_id is the PRIMARY KEY for:
        - Lakebase checkpointer (LangGraph state)
        - Conversation history retrieval
        - Multi-turn context
        
        Same thread_id = Continued conversation
        New thread_id  = Fresh start
        
        PRODUCTION CONSIDERATION:
        -------------------------
        Thread IDs should be:
        - Unique across users (avoid collision)
        - Stable within a session (don't change mid-conversation)
        - Opaque (don't embed sensitive information)

        Args:
            custom_inputs: Custom inputs from request (optional dict)
            context: ChatContext from request (optional)

        Returns:
            Thread ID string (existing or newly generated UUID).
        """
        return ShortTermMemory.resolve_thread_id(
            custom_inputs=custom_inputs,
            conversation_id=context.conversation_id if context else None,
        )

    def _resolve_user_id(
        self,
        custom_inputs: Optional[Dict] = None,
        context: Optional[ChatContext] = None,
    ) -> str:
        """
        Resolve user ID for memory and permissions.
        
        TRAINING MATERIAL: User Identity in AI Agents
        ==============================================
        
        WHAT IS USER ID:
        A persistent identifier for the human user.
        Unlike thread_id (per-conversation), user_id persists across sessions.
        
        USES OF USER ID:
        1. Long-term memory retrieval (preferences, history)
        2. Audit logging (who asked what)
        3. Permission checks (what data can they see)
        4. Personalization (response formatting)
        
        WHY "unknown_user" DEFAULT:
        ---------------------------
        - Allows agent to function without authentication
        - Enables testing without identity setup
        - Production should ALWAYS provide real user IDs
        
        SECURITY CONSIDERATION:
        -----------------------
        In Model Serving with OBO (On-Behalf-Of) authentication,
        the user_id may come from the authentication context,
        not from the request payload.
        
        NEVER TRUST client-provided user_id for permissions!
        Use server-side authentication for access control.
        
        ALTERNATIVE CONSIDERED:
        -----------------------
        Raising an exception for missing user_id was considered,
        but rejected because:
        - Breaks AI Playground testing
        - Reduces developer experience
        - Security checks should happen at data layer, not agent layer

        Args:
            custom_inputs: Custom inputs from request
            context: ChatContext from request

        Returns:
            User ID string ("unknown_user" if not provided).
        """
        if custom_inputs and custom_inputs.get("user_id"):
            return custom_inputs["user_id"]
        if context and context.user_id:
            return context.user_id
        return "unknown_user"

    # =========================================================================
    # MAIN PREDICTION METHOD
    # =========================================================================
    # TRAINING MATERIAL: This is the core method called by Databricks Model
    # Serving when a user sends a message to the agent.

    @mlflow.trace(name="agent_predict", span_type="AGENT")
    def predict(
        self,
        messages: List[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> ChatAgentResponse:
        """
        Process a user query and return a response.
        
        TRAINING MATERIAL: The predict() Method - Heart of ChatAgent
        ==============================================================
        
        This is the MAIN ENTRY POINT for all agent interactions.
        Every user message flows through this method.
        
        CALL CHAIN:
        -----------
        User Request (HTTP POST /serving-endpoints/.../invocations)
            ↓
        Databricks Model Serving
            ↓
        mlflow.pyfunc.load_model().predict()
            ↓
        THIS METHOD (HealthMonitorAgent.predict)
            ↓
        LangGraph orchestrator
            ↓
        Domain workers → Genie Spaces → Data
            ↓
        Response back to user
        
        @mlflow.trace DECORATOR:
        -------------------------
        - name="agent_predict": Appears in MLflow Tracing UI
        - span_type="AGENT": Categorizes this as an agent-level operation
        
        SPAN TYPES EXPLAINED:
        - AGENT: Top-level agent operations
        - TOOL: External service calls (Genie, APIs)
        - LLM: Language model invocations
        - RETRIEVER: Memory/document retrieval
        - CLASSIFIER: Classification operations
        
        WHY TRACING MATTERS:
        --------------------
        1. Debugging: See exactly what happened for each request
        2. Performance: Identify slow components
        3. Cost: Track LLM token usage
        4. Quality: Monitor response quality over time
        
        INPUT FORMAT:
        -------------
        messages: List of ChatAgentMessage
            [
                ChatAgentMessage(role="user", content="Why did costs spike?"),
                ChatAgentMessage(role="assistant", content="Previous response..."),
                ChatAgentMessage(role="user", content="Tell me more about SKU X"),
            ]
        
        The last message is the current user query.
        Previous messages are conversation history (for context).
        
        OUTPUT FORMAT:
        --------------
        ChatAgentResponse with:
        - messages: List with single assistant response
        - custom_outputs: Metadata (thread_id, sources, confidence)
        
        ERROR HANDLING STRATEGY:
        ------------------------
        - Catch all exceptions to prevent 500 errors
        - Return user-friendly error message
        - Log error metric for monitoring
        - Include error details in custom_outputs for debugging

        Args:
            messages: List of conversation messages (history + current query)
            context: Optional chat context with user/conversation info
            custom_inputs: Optional custom inputs (thread_id, user preferences, etc.)

        Returns:
            ChatAgentResponse with assistant message and metadata.
        
        EXAMPLE USAGE:
        --------------
        # In AI Playground or notebook:
        response = agent.predict(
            messages=[ChatAgentMessage(role="user", content="Show top 5 expensive jobs")],
            context=ChatContext(conversation_id="test-123"),
            custom_inputs={"user_id": "analyst@company.com"}
        )
        
        # Response structure:
        # response.messages[-1].content  → "Based on the data, the top 5..."
        # response.custom_outputs["sources"]  → ["Cost Genie"]
        # response.custom_outputs["confidence"]  → 0.95
        """
        # =====================================================================
        # STEP 1: Extract the user's query from messages
        # =====================================================================
        # WHY [-1]: The last message is always the current user input
        # WHY .content: ChatAgentMessage has role and content attributes
        # WHY empty string default: Defensive programming for malformed requests
        user_message = messages[-1].content if messages else ""

        # =====================================================================
        # STEP 2: Resolve identity information
        # =====================================================================
        # These IDs are crucial for:
        # - thread_id: Conversation state retrieval
        # - user_id: Long-term memory, audit logging, personalization
        thread_id = self._resolve_thread_id(custom_inputs, context)
        user_id = self._resolve_user_id(custom_inputs, context)

        # =====================================================================
        # STEP 3: Update trace with request metadata
        # =====================================================================
        # WHY update_current_trace: Adds searchable tags to the trace
        # This enables filtering in MLflow UI: "Show all traces for user X"
        # 
        # TAGS vs ATTRIBUTES:
        # - Tags: String key-value pairs, searchable in UI
        # - Attributes: Rich metadata, shown in trace details
        mlflow.update_current_trace(tags={
            "user_id": user_id,
            "thread_id": thread_id,
            "query_length": str(len(user_message)),
        })

        # =====================================================================
        # STEP 4: Create initial state for LangGraph
        # =====================================================================
        # The state object flows through all nodes in the graph.
        # Each node reads from and writes to this shared state.
        # 
        # LANGGRAPH STATE PATTERN:
        # - State is a TypedDict with defined fields
        # - Nodes return partial state updates
        # - LangGraph merges updates automatically
        initial_state = create_initial_state(
            query=user_message,
            user_id=user_id,
            session_id=thread_id,
        )

        # =====================================================================
        # STEP 5: Prepare checkpoint configuration
        # =====================================================================
        # The checkpoint config tells LangGraph:
        # - Where to store/retrieve state (thread_id)
        # - What namespace to use
        # 
        # WHY CHECKPOINTING:
        # - Enables conversation continuity across requests
        # - Survives Model Serving replica restarts
        # - Required for multi-turn conversations
        checkpoint_config = ShortTermMemory.get_checkpoint_config(thread_id)

        try:
            # =================================================================
            # STEP 6: Execute the LangGraph orchestrator
            # =================================================================
            # WHY CONTEXT MANAGER: Ensures Lakebase connection cleanup
            # 
            # GRAPH EXECUTION FLOW:
            # 1. Start at entry node (orchestrator)
            # 2. Classify intent → determine domains
            # 3. Route to domain workers (parallel execution)
            # 4. Each worker queries Genie Space
            # 5. Synthesizer combines results
            # 6. Return final state
            with get_checkpoint_saver() as checkpointer:
                graph = create_orchestrator_graph().compile(
                    checkpointer=checkpointer
                )
                final_state = graph.invoke(initial_state, checkpoint_config)

            # =================================================================
            # STEP 7: Extract response from final state
            # =================================================================
            # WHY .get() WITH DEFAULT: Defensive programming
            # If synthesizer fails, we still return something useful
            response_content = final_state.get(
                "synthesized_response",
                "I was unable to process your request."
            )
            sources = final_state.get("sources", [])
            confidence = final_state.get("confidence", 0.0)

            # =================================================================
            # STEP 8: Build and return response
            # =================================================================
            # ChatAgentResponse structure:
            # - messages: Always a list (even for single response)
            # - custom_outputs: Arbitrary metadata (returned to client)
            # 
            # WHY INCLUDE CUSTOM_OUTPUTS:
            # - thread_id: Client can use for subsequent requests
            # - sources: Transparency about where data came from
            # - confidence: Signal response quality
            # - domains: Which specialist agents contributed
            return ChatAgentResponse(
                messages=[
                    ChatAgentMessage(
                        role="assistant",
                        content=response_content,
                    )
                ],
                custom_outputs={
                    "thread_id": thread_id,
                    "sources": sources,
                    "confidence": confidence,
                    "domains": final_state.get("intent", {}).get("domains", []),
                },
            )

        except Exception as e:
            # =================================================================
            # ERROR HANDLING: Graceful degradation
            # =================================================================
            # WHY CATCH ALL EXCEPTIONS:
            # - Prevents 500 errors reaching users
            # - Maintains conversation context (thread_id returned)
            # - Enables debugging via error in custom_outputs
            # 
            # WHY LOG METRIC:
            # - Enables alerting on error rate
            # - Tracks agent reliability over time
            # 
            # ALTERNATIVE CONSIDERED:
            # Re-raising with wrapped exception was considered, but rejected
            # because it would cause HTTP 500 errors and poor UX.
            mlflow.log_metric("agent_error", 1)
            return ChatAgentResponse(
                messages=[
                    ChatAgentMessage(
                        role="assistant",
                        content=f"I encountered an error: {str(e)}. Please try again.",
                    )
                ],
                custom_outputs={
                    "thread_id": thread_id,
                    "error": str(e),
                },
            )

    # =========================================================================
    # STREAMING PREDICTION METHOD
    # =========================================================================
    # TRAINING MATERIAL: Streaming is essential for production agents.
    # It provides real-time feedback during long-running operations.

    @mlflow.trace(name="agent_predict_stream", span_type="AGENT")
    def predict_stream(
        self,
        messages: List[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream responses for real-time interaction.
        
        TRAINING MATERIAL: Why Streaming Matters for AI Agents
        ========================================================
        
        PROBLEM WITHOUT STREAMING:
        User sends query → waits 10-30 seconds → gets response
        This feels slow and provides no feedback.
        
        WITH STREAMING:
        User sends query → sees "Analyzing..." → sees "Querying cost data..."
        → sees "Found 5 anomalies..." → sees final response
        This feels responsive and builds trust.
        
        STREAMING ARCHITECTURE:
        -----------------------
        
        ┌─────────────────────────────────────────────────────────────┐
        │                    predict_stream()                          │
        │                                                              │
        │   yield("🔍 Analyzing...")     ←──────────────────────┐     │
        │          ↓                                            │     │
        │   graph.stream() ─────→ event ─────→ if domain found ─┘     │
        │          ↓                  │                               │
        │          ↓                  └────→ if worker done ──────┐   │
        │          ↓                                              │   │
        │   yield("📊 Querying...")    ←──────────────────────────┘   │
        │          ↓                                                  │
        │   yield(final_response)                                     │
        └─────────────────────────────────────────────────────────────┘
        
        PYTHON GENERATORS:
        ------------------
        This method uses `yield` instead of `return`.
        This makes it a GENERATOR FUNCTION that produces values lazily.
        
        Benefits of generators:
        - Memory efficient (one chunk at a time)
        - Real-time output (no buffering)
        - Can be iterated only once
        
        HOW MODEL SERVING HANDLES STREAMING:
        ------------------------------------
        1. HTTP response uses chunked transfer encoding
        2. Each yield becomes a Server-Sent Event (SSE)
        3. Client (AI Playground, app) processes events as they arrive
        
        LANGGRAPH STREAMING:
        --------------------
        graph.stream() yields events as nodes complete:
        - {"intent": {...}}       → Intent classification done
        - {"agent_responses": {}} → Workers starting to return
        - {"synthesized_response": "..."} → Final response ready
        
        PROGRESSIVE DISCLOSURE PATTERN:
        -------------------------------
        1. "Analyzing..." - User knows we received their query
        2. "Identified domains: cost, reliability" - Shows understanding
        3. "Querying data sources..." - Shows action being taken
        4. Final response - Delivers value
        
        This pattern reduces perceived latency significantly.

        Yields ChatAgentResponse chunks as they become available,
        providing progressive feedback during long-running operations.

        The streaming flow:
        1. Yield "thinking" status while processing
        2. Yield intermediate results from worker agents
        3. Yield final synthesized response

        Args:
            messages: List of conversation messages
            context: Optional chat context with user/conversation info
            custom_inputs: Optional custom inputs (thread_id, etc.)

        Yields:
            ChatAgentResponse objects with progressive content.

        Example:
            # In a Databricks notebook:
            for chunk in agent.predict_stream(messages):
                print(chunk.messages[-1].content)
                print(f"Status: {chunk.custom_outputs.get('status')}")
            
            # Output:
            # 🔍 Analyzing your query...
            # Status: thinking
            # 📊 Identified domains: cost, reliability. Querying data sources...
            # Status: processing
            # ✅ Received 2 domain response(s). Synthesizing answer...
            # Status: synthesizing
            # Based on the analysis, here's what I found...
            # Status: complete
        """
        # Extract the latest user message
        user_message = messages[-1].content if messages else ""

        # Resolve IDs
        thread_id = self._resolve_thread_id(custom_inputs, context)
        user_id = self._resolve_user_id(custom_inputs, context)

        # Update trace with metadata
        mlflow.update_current_trace(tags={
            "user_id": user_id,
            "thread_id": thread_id,
            "streaming": "true",
        })

        # Yield initial thinking status
        yield ChatAgentResponse(
            messages=[
                ChatAgentMessage(
                    role="assistant",
                    content="🔍 Analyzing your query...",
                )
            ],
            custom_outputs={
                "thread_id": thread_id,
                "status": "thinking",
                "stage": "intent_classification",
            },
        )

        # Create initial state
        initial_state = create_initial_state(
            query=user_message,
            user_id=user_id,
            session_id=thread_id,
        )

        # Execute graph with streaming
        checkpoint_config = ShortTermMemory.get_checkpoint_config(thread_id)

        try:
            with get_checkpoint_saver() as checkpointer:
                graph = create_orchestrator_graph().compile(
                    checkpointer=checkpointer
                )

                # Stream graph execution
                domains_identified = False
                worker_responses_started = False

                for event in graph.stream(initial_state, checkpoint_config):
                    # Check if intent classification is complete
                    if "intent" in event and not domains_identified:
                        intent = event.get("intent", {})
                        domains = intent.get("domains", [])
                        confidence = intent.get("confidence", 0.0)

                        if domains:
                            domains_identified = True
                            domain_str = ", ".join(domains)

                            yield ChatAgentResponse(
                                messages=[
                                    ChatAgentMessage(
                                        role="assistant",
                                        content=f"📊 Identified domains: {domain_str}. Querying data sources...",
                                    )
                                ],
                                custom_outputs={
                                    "thread_id": thread_id,
                                    "status": "processing",
                                    "stage": "domain_routing",
                                    "domains": domains,
                                    "confidence": confidence,
                                },
                            )

                    # Check for worker agent responses
                    if "agent_responses" in event and not worker_responses_started:
                        responses = event.get("agent_responses", {})
                        if responses:
                            worker_responses_started = True
                            num_responses = len(responses)

                            yield ChatAgentResponse(
                                messages=[
                                    ChatAgentMessage(
                                        role="assistant",
                                        content=f"✅ Received {num_responses} domain response(s). Synthesizing answer...",
                                    )
                                ],
                                custom_outputs={
                                    "thread_id": thread_id,
                                    "status": "synthesizing",
                                    "stage": "response_synthesis",
                                    "domains_queried": list(responses.keys()),
                                },
                            )

                    # Check for final synthesized response
                    if "synthesized_response" in event:
                        response_content = event.get("synthesized_response", "")
                        if response_content:
                            # Get final state data
                            sources = event.get("sources", [])
                            confidence = event.get("confidence", 0.0)
                            final_intent = event.get("intent", {})

                            yield ChatAgentResponse(
                                messages=[
                                    ChatAgentMessage(
                                        role="assistant",
                                        content=response_content,
                                    )
                                ],
                                custom_outputs={
                                    "thread_id": thread_id,
                                    "status": "complete",
                                    "stage": "final",
                                    "sources": sources,
                                    "confidence": confidence,
                                    "domains": final_intent.get("domains", []),
                                },
                            )
                            return

                # If we didn't get a synthesized response from streaming,
                # fall back to final state
                final_state = graph.invoke(initial_state, checkpoint_config)

                response_content = final_state.get(
                    "synthesized_response",
                    "I was unable to process your request."
                )
                sources = final_state.get("sources", [])
                confidence = final_state.get("confidence", 0.0)

                yield ChatAgentResponse(
                    messages=[
                        ChatAgentMessage(
                            role="assistant",
                            content=response_content,
                        )
                    ],
                    custom_outputs={
                        "thread_id": thread_id,
                        "status": "complete",
                        "stage": "final",
                        "sources": sources,
                        "confidence": confidence,
                        "domains": final_state.get("intent", {}).get("domains", []),
                    },
                )

        except Exception as e:
            mlflow.log_metric("agent_stream_error", 1)
            yield ChatAgentResponse(
                messages=[
                    ChatAgentMessage(
                        role="assistant",
                        content=f"❌ I encountered an error: {str(e)}. Please try again.",
                    )
                ],
                custom_outputs={
                    "thread_id": thread_id,
                    "status": "error",
                    "error": str(e),
                },
            )


# =============================================================================
# MLFLOW RESOURCE DECLARATION
# =============================================================================
# TRAINING MATERIAL: This function demonstrates a critical pattern for
# production agent deployment - declaring resource dependencies.

def get_mlflow_resources() -> List:
    """
    Get MLflow resource dependencies for model logging.
    
    TRAINING MATERIAL: Automatic Authentication Passthrough
    =========================================================
    
    THE PROBLEM:
    ------------
    Your agent needs to access:
    - Genie Spaces (for data queries)
    - LLM endpoints (for inference)
    - SQL Warehouses (for direct queries)
    - Lakebase (for memory)
    
    Without proper authentication, these calls fail with permission errors.
    
    THE SOLUTION: Resource Declaration
    -----------------------------------
    By declaring resources in mlflow.pyfunc.log_model(), Databricks
    automatically creates a SERVICE PRINCIPAL with access to those resources.
    
    When the agent runs in Model Serving:
    1. Databricks sees the declared resources
    2. Creates short-lived credentials for the service principal
    3. Injects credentials into the runtime environment
    4. Your code "just works" without manual credential handling
    
    HOW IT WORKS:
    -------------
    
    ┌───────────────────────────────────────────────────────────────────┐
    │                     Model Serving Runtime                         │
    │                                                                   │
    │   mlflow.pyfunc.log_model(                                       │
    │       resources=[                                                 │
    │           DatabricksGenieSpace(genie_space_id="...")  ←──────┐   │
    │           DatabricksSQLWarehouse(warehouse_id="...")  ←──────┤   │
    │       ]                                                      │   │
    │   )                                                          │   │
    │                                                              │   │
    │   Agent Code                                                 │   │
    │   ├── GenieAgent(space_id="...")  ─────→ Uses injected creds ┤   │
    │   └── WorkspaceClient()          ─────→ Uses injected creds ─┘   │
    └───────────────────────────────────────────────────────────────────┘
    
    TWO AUTHENTICATION CONTEXTS:
    ----------------------------
    1. SystemAuthPolicy (resources) - For evaluation, notebooks, jobs
       - Creates service principal with access to declared resources
       - Used when OBO is not available
    
    2. UserAuthPolicy (api_scopes) - For Model Serving with OBO
       - Uses end-user credentials passed through
       - Respects user's actual permissions
    
    CRITICAL LESSON LEARNED (Jan 27, 2026):
    ----------------------------------------
    Resource declaration is MANDATORY for evaluation to work!
    Without DatabricksGenieSpace in resources, agent evaluation fails with:
    "You need 'Can View' permission to perform this action"
    
    WHY CONDITIONAL CHECKS:
    -----------------------
    MLflow versions vary:
    - DatabricksGenieSpace: Requires MLflow 2.17.1+
    - DatabricksSQLWarehouse: Requires MLflow 2.16.1+
    - DatabricksLakebase: Requires MLflow 3.3.2+
    
    Conditional checks prevent import errors on older versions.

    Reference:
        https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#automatic-authentication-passthrough

    Resources declared:
        - DatabricksServingEndpoint: LLM endpoint for inference
        - DatabricksLakebase: Memory storage (short-term & long-term)
        - DatabricksGenieSpace: All 6 domain Genie Spaces
        - DatabricksSQLWarehouse: For any direct SQL operations

    Returns:
        List of Databricks resource dependencies.
    
    EXAMPLE USAGE:
    --------------
    resources = get_mlflow_resources()
    
    mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=agent,
        resources=resources,  # ← This enables auth passthrough
        ...
    )
    """
    resources = []
    
    # =========================================================================
    # RESOURCE 1: LLM Endpoint
    # =========================================================================
    # WHY: Agent needs to call LLM for:
    # - Intent classification
    # - Response synthesis
    # - Any LLM-based reasoning
    if DatabricksServingEndpoint is not None:
        resources.append(DatabricksServingEndpoint(endpoint_name=settings.llm_endpoint))
    
    # =========================================================================
    # RESOURCE 2: Lakebase (Memory Storage)
    # =========================================================================
    # WHY: Agent uses Lakebase for:
    # - Short-term memory (conversation state via checkpointer)
    # - Long-term memory (user preferences, historical patterns)
    # NOTE: May not be available in all MLflow versions (3.3.2+)
    if _HAS_LAKEBASE_RESOURCE and DatabricksLakebase is not None:
        resources.append(DatabricksLakebase(database_instance_name=settings.lakebase_instance_name))
    
    # =========================================================================
    # RESOURCE 3: SQL Warehouse
    # =========================================================================
    # WHY: Genie Spaces execute queries on SQL Warehouses
    # CRITICAL: Without this, Genie queries fail even with Genie Space declared
    if DatabricksSQLWarehouse is not None:
        resources.append(DatabricksSQLWarehouse(warehouse_id=settings.warehouse_id))
    
    # =========================================================================
    # RESOURCE 4: All Genie Spaces
    # =========================================================================
    # WHY: Each domain worker queries its dedicated Genie Space
    # CRITICAL: Must declare ALL Genie Spaces the agent might use
    # 
    # COMMON MISTAKE: Declaring only some Genie Spaces
    # RESULT: "Permission denied" errors for undeclared spaces
    if DatabricksGenieSpace is not None:
        genie_space_configs = [
            ("cost", settings.cost_genie_space_id),
            ("security", settings.security_genie_space_id),
            ("performance", settings.performance_genie_space_id),
            ("reliability", settings.reliability_genie_space_id),
            ("quality", settings.quality_genie_space_id),
            ("unified", settings.unified_genie_space_id),
        ]
        
        for domain, space_id in genie_space_configs:
            if space_id:  # Only add if configured (some may be None in dev)
                resources.append(
                    DatabricksGenieSpace(genie_space_id=space_id)
                )
    
    return resources


# =============================================================================
# MODEL LOGGING FUNCTION
# =============================================================================
# TRAINING MATERIAL: This function demonstrates the complete process of
# registering an agent with MLflow Model Registry for deployment.

def log_agent_to_mlflow(
    agent: HealthMonitorAgent,
    registered_model_name: str = None,
    version: str = "1.0.0",
) -> str:
    """
    Log the agent to MLflow Model Registry.
    
    TRAINING MATERIAL: Agent Registration for Deployment
    =====================================================
    
    This function packages the agent and registers it with Unity Catalog
    Model Registry, making it deployable to Databricks Model Serving.
    
    DEPLOYMENT WORKFLOW:
    --------------------
    
    1. Development:
       log_agent_to_mlflow(agent)
       ↓
    2. Model Registry:
       catalog.schema.health_monitor_agent (version 1, 2, 3...)
       ↓
    3. Set Alias:
       mlflow.set_alias("production", version=3)
       ↓
    4. Model Serving:
       Deploys @production alias automatically
    
    WHAT GETS PACKAGED:
    -------------------
    ┌─────────────────────────────────────────────────────────────┐
    │                    Model Artifact                           │
    ├─────────────────────────────────────────────────────────────┤
    │  python_model/    → Serialized agent class (pickle)         │
    │  requirements/    → pip_requirements list                   │
    │  MLmodel          → Model metadata (signature, flavors)     │
    │  input_example/   → Sample input for testing                │
    │  resources/       → Declared Databricks resources           │
    └─────────────────────────────────────────────────────────────┘
    
    CRITICAL: mlflow.models.set_model()
    ------------------------------------
    This call is REQUIRED before log_model() for ChatAgent/ResponsesAgent.
    It tells MLflow which model instance to serialize.
    Without it: MLflow doesn't know what to log.
    
    INPUT EXAMPLE FORMAT:
    ---------------------
    Must match the ChatAgent interface:
    - "messages": List of role/content dicts
    - "custom_inputs": Optional metadata dict
    
    This example is used for:
    - Signature inference (input/output types)
    - Testing in AI Playground
    - Documentation
    
    EXPERIMENT PATH:
    ----------------
    WHY /Shared/: This path always exists, no parent folder issues.
    WHY NOT /Users/: Requires parent folders to exist, fails silently.
    
    TAGS AND PARAMS:
    ----------------
    Tags enable filtering in MLflow UI:
    - "agent_version": Find all runs for a specific version
    - "domain": Filter by agent domain
    - "run_type": Distinguish training vs logging vs evaluation
    
    Params are logged for reproducibility:
    - "llm_endpoint": Which LLM was used
    - "lakebase_instance": Which memory backend
    
    pip_requirements:
    -----------------
    These packages are installed when the model is loaded:
    - mlflow>=3.0.0: Core MLflow functionality
    - langchain: LLM abstraction layer
    - langgraph: Multi-agent workflow orchestration
    - databricks-sdk: Workspace API access
    - databricks-agents: GenieAgent and other agent tools
    
    VERSION PINNING:
    ----------------
    Consider pinning exact versions in production:
    "mlflow==3.7.0" instead of "mlflow>=3.0.0"
    This prevents version mismatch warnings during inference.

    Args:
        agent: HealthMonitorAgent instance to log
        registered_model_name: Name for Unity Catalog model (3-level: catalog.schema.model)
        version: Version string for tracking (semantic versioning recommended)

    Returns:
        Model URI string (e.g., "models:/catalog.schema.model/1")

    Example:
        # Log agent during development
        agent = HealthMonitorAgent()
        model_uri = log_agent_to_mlflow(
            agent,
            registered_model_name="health_monitor.agents.orchestrator"
        )
        print(f"Logged model: {model_uri}")
        
        # Later, set production alias
        from mlflow import MlflowClient
        client = MlflowClient()
        client.set_registered_model_alias(
            name="health_monitor.agents.orchestrator",
            alias="production",
            version="1"
        )
    """
    # =========================================================================
    # STEP 1: Determine model name
    # =========================================================================
    # 3-level naming (catalog.schema.model) is REQUIRED for Unity Catalog
    model_name = registered_model_name or (
        f"{settings.catalog}.{settings.agent_schema}.health_monitor_agent"
    )

    # =========================================================================
    # STEP 2: Set model for logging
    # =========================================================================
    # CRITICAL: This tells MLflow which object to serialize
    # Without this, log_model() doesn't know what to package
    mlflow.models.set_model(agent)

    # =========================================================================
    # STEP 3: Create input example
    # =========================================================================
    # This example is used for:
    # - Automatic signature inference
    # - Testing the model after loading
    # - Documentation in MLflow UI
    input_example = {
        "messages": [
            {"role": "user", "content": "Why did costs spike yesterday?"}
        ],
        "custom_inputs": {"user_id": "example@company.com"},
    }

    # =========================================================================
    # STEP 4: Set experiment
    # =========================================================================
    # WHY /Shared/: Always exists, no parent folder creation needed
    # ALTERNATIVE: /Users/{user}/... (requires folder to exist first)
    mlflow.set_experiment("/Shared/health_monitor_agent_development")
    
    # =========================================================================
    # STEP 5: Create MLflow run for logging
    # =========================================================================
    # Run name includes timestamp for easy identification
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = f"dev_model_registration_{timestamp}"
    
    with mlflow.start_run(run_name=run_name):
        # =====================================================================
        # STEP 5a: Set tags for filtering
        # =====================================================================
        # Tags are searchable in MLflow UI
        # Use consistent tags across all agent runs
        mlflow.set_tags({
            "run_type": "model_logging",    # Distinguish from training/eval runs
            "domain": "all",                # Multi-domain agent
            "agent_version": f"v{version}", # Track agent versions
            "dataset_type": "none",         # No training data for logging
            "evaluation_type": "none",      # No evaluation for logging
        })
        
        # =====================================================================
        # STEP 5b: Log parameters for reproducibility
        # =====================================================================
        # Params capture the agent's configuration
        mlflow.log_params({
            "agent_type": "multi_agent_orchestrator",
            "version": version,
            "llm_endpoint": settings.llm_endpoint,
            "lakebase_instance": settings.lakebase_instance_name,
        })

        # =====================================================================
        # STEP 5c: Log the model
        # =====================================================================
        # This is the main action - packages and registers the agent
        logged_model = mlflow.pyfunc.log_model(
            artifact_path="agent",          # Path within the artifact store
            python_model=agent,             # The agent instance to serialize
            input_example=input_example,    # For signature inference
            resources=get_mlflow_resources(),  # Auth passthrough resources
            registered_model_name=model_name,  # Unity Catalog registration
            pip_requirements=[
                # Core MLflow - must match training version
                "mlflow>=3.0.0",
                # LangChain ecosystem for agent orchestration
                "langchain>=0.3.0",
                "langchain-core>=0.3.0",
                "langgraph>=0.2.0",
                # Databricks SDK for API access
                "databricks-sdk>=0.30.0",
                # Agent framework with GenieAgent support
                "databricks-agents>=0.16.0",
            ],
        )

        return logged_model.model_uri


# =============================================================================
# MODULE-LEVEL SINGLETON
# =============================================================================
# TRAINING MATERIAL: Singleton Pattern for Agent Instances
#
# WHY A SINGLETON:
# - Convenient for interactive use (just import AGENT)
# - Lazy initialization (created on first import)
# - Consistent instance across module
#
# WHEN TO USE:
# - Quick testing in notebooks
# - Simple scripts
# - Development workflows
#
# WHEN NOT TO USE:
# - Production Model Serving (creates fresh instance)
# - Testing (may want isolated instances)
# - Parallel processing (shared state issues)
#
# ALTERNATIVE: Factory function
# def create_agent() -> HealthMonitorAgent:
#     return HealthMonitorAgent()
#
# Usage: agent = create_agent()  # Fresh instance each time

# Create singleton instance for convenience
AGENT = HealthMonitorAgent()
