"""
LangGraph Orchestrator Graph
============================

TRAINING MATERIAL: LangGraph State Machine Pattern
---------------------------------------------------

This module defines the HEART of the multi-agent system: the orchestrator
graph that controls how queries flow through different processing stages.

WHAT IS LANGGRAPH:
------------------
LangGraph is a library for building stateful, multi-actor applications
with LLMs. It extends LangChain with:
- State machines (graph-based control flow)
- Cycles (loops and retries)
- Persistence (checkpointing)
- Human-in-the-loop patterns

WHY LANGGRAPH (not just LangChain):
-----------------------------------
LangChain chains are LINEAR (A → B → C).
LangGraph graphs can have BRANCHES, CYCLES, and CONDITIONS.

Our orchestrator needs:
- Conditional routing (different domains based on intent)
- Parallel execution (query multiple domains)
- State persistence (conversation memory)
- Complex control flow (classify → route → query → synthesize)

GRAPH ARCHITECTURE:
-------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR GRAPH                                    │
│                                                                         │
│  START                                                                  │
│    ↓                                                                    │
│  [load_context]  ← Load user preferences from long-term memory         │
│    ↓                                                                    │
│  [classify_intent]  ← Determine which domain(s) to query               │
│    ↓                                                                    │
│  ┌─────── CONDITIONAL ROUTING ───────┐                                 │
│  ↓              ↓                    ↓                                  │
│  [cost]     [security]    ...   [parallel_agents]                      │
│  ↓              ↓                    ↓                                  │
│  └──────────────┴────────────────────┘                                 │
│                  ↓                                                      │
│  [synthesize]  ← Combine domain responses into coherent answer         │
│    ↓                                                                    │
│  [save_context]  ← Save query patterns to long-term memory             │
│    ↓                                                                    │
│  END                                                                    │
└─────────────────────────────────────────────────────────────────────────┘

KEY CONCEPTS:
1. NODES: Functions that transform state (load_context, classify, etc.)
2. EDGES: Connections between nodes (can be conditional)
3. STATE: Shared data that flows through the graph (AgentState)
4. ENTRY/EXIT: Where execution starts (set_entry_point) and ends (END)

STATE MANAGEMENT:
-----------------
AgentState is a TypedDict that flows through all nodes.
Each node:
- Receives full state
- Returns partial state update
- LangGraph merges updates automatically

This is different from LangChain chains where each step
only sees its immediate input.

CHECKPOINTING:
--------------
When compiled with a checkpointer, LangGraph saves state
after each node. This enables:
- Resume from last checkpoint (conversation continuity)
- Time-travel debugging
- State inspection

Defines the state machine for multi-agent orchestration.
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization for LangGraph
#
# KEY IMPORTS:
# - StateGraph: The main class for building graphs
# - END: Special constant indicating execution termination
# - HumanMessage/AIMessage: LangChain message types

from typing import Dict, Literal
import mlflow

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from .state import AgentState
from .intent_classifier import IntentClassifier
from .synthesizer import ResponseSynthesizer
from ..memory import get_checkpoint_saver, get_long_term_memory
from ..workers import get_worker_agent


# =============================================================================
# COMPONENT INITIALIZATION
# =============================================================================
# TRAINING MATERIAL: Module-Level Singletons
#
# WHY MODULE-LEVEL:
# These components are stateless and expensive to create.
# Creating once at module load time avoids:
# - Repeated initialization overhead
# - Memory waste from multiple instances
#
# ALTERNATIVE: Dependency injection
# Could pass these as parameters, but adds complexity
# for components that don't change at runtime.

intent_classifier = IntentClassifier()
synthesizer = ResponseSynthesizer()
long_term_memory = get_long_term_memory()


# =============================================================================
# NODE FUNCTIONS
# =============================================================================
# TRAINING MATERIAL: LangGraph Node Pattern
#
# WHAT ARE NODES:
# Nodes are functions that:
# 1. Receive the full AgentState as input
# 2. Perform some transformation or side effect
# 3. Return a PARTIAL state update (dict with keys to update)
#
# LangGraph automatically MERGES the returned dict into the state.
# This is different from LangChain where you return the full output.
#
# NODE FUNCTION SIGNATURE:
# def node_name(state: AgentState) -> Dict:
#     # Process state
#     return {"key_to_update": new_value}
#
# TRACING:
# @mlflow.trace decorator adds observability.
# span_type categorizes the operation (MEMORY, CLASSIFIER, AGENT, LLM)

@mlflow.trace(name="load_context", span_type="MEMORY")
def load_context(state: AgentState) -> Dict:
    """
    Load memory context for the user.
    
    TRAINING MATERIAL: Memory Node Pattern
    ======================================
    
    PURPOSE:
    Personalize the agent response by retrieving:
    - User preferences (cost thresholds, workspaces)
    - User role (manager, analyst, engineer)
    - Recent query patterns (for context)
    
    EXECUTION ORDER:
    This is the FIRST node in the graph.
    Runs before any domain processing.
    
    STATE INPUT:
    - state["user_id"]: Who is asking
    
    STATE OUTPUT:
    - {"memory_context": {...}}: User preferences and context
    
    GRACEFUL DEGRADATION:
    If memory retrieval fails (tables don't exist, service down):
    - Log error metric (for alerting)
    - Return empty context (agent still works)
    - NEVER raise exception (would crash entire request)
    
    SEMANTIC SEARCH:
    long_term_memory.search_memories() uses VECTOR SEARCH
    to find relevant memories, not exact key lookup.
    Query "user preferences workspace threshold" finds memories
    about preferences, workspaces, OR thresholds.

    Retrieves long-term memory (preferences, insights) to personalize
    the response.
    """
    user_id = state["user_id"]

    # Initialize with empty defaults (graceful degradation)
    memory_context = {
        "preferences": {},  # Cost threshold, preferred workspace, etc.
        "role": None,       # Manager, analyst, engineer
        "recent_queries": [],  # For personalization
    }

    try:
        # SEMANTIC SEARCH: Find relevant memories
        # Uses vector embeddings, not exact key match
        prefs = long_term_memory.search_memories(
            user_id=user_id,
            query="user preferences workspace threshold",
            limit=3,  # Top 3 most relevant
        )

        # Merge found memories into context
        for mem in prefs:
            if "preference" in mem.key.lower():
                memory_context["preferences"].update(mem.value)
            if "role" in mem.key.lower():
                memory_context["role"] = mem.value.get("role")

    except Exception as e:
        # GRACEFUL DEGRADATION: Memory unavailable - proceed without context
        # Log metric for monitoring/alerting
        mlflow.log_metric("memory_load_error", 1)
        # Don't raise - agent can still function without memory

    # Return PARTIAL state update (only memory_context)
    return {"memory_context": memory_context}


@mlflow.trace(name="classify_intent_node", span_type="CLASSIFIER")
def classify_intent(state: AgentState) -> Dict:
    """
    Classify the user's intent.

    Determines which domain(s) should handle the query.
    """
    query = state["query"]
    intent = intent_classifier.classify(query)

    # Add user message to conversation
    messages = [HumanMessage(content=query)]

    return {
        "intent": intent,
        "messages": messages,
    }


def route_to_agents(state: AgentState) -> Literal[
    "cost_agent", "security_agent", "performance_agent",
    "reliability_agent", "quality_agent", "parallel_agents"
]:
    """
    Route to appropriate agent(s) based on intent.

    For single-domain queries, routes to that domain.
    For multi-domain queries, routes to parallel execution.
    """
    intent = state.get("intent", {})
    domains = intent.get("domains", ["COST"])

    if len(domains) == 1:
        domain = domains[0].lower()
        return f"{domain}_agent"

    return "parallel_agents"


@mlflow.trace(name="query_worker", span_type="AGENT")
def create_worker_node(domain: str):
    """
    Factory function to create worker agent nodes.

    Args:
        domain: Domain name (cost, security, etc.)

    Returns:
        Node function for the domain worker.
    """
    def worker_node(state: AgentState) -> Dict:
        """Query the domain worker agent."""
        query = state["query"]
        memory_context = state.get("memory_context", {})

        # Get the worker agent for this domain
        worker = get_worker_agent(domain)

        if worker is None:
            return {
                "agent_responses": {
                    domain: {
                        "response": f"Worker agent for {domain} not available",
                        "sources": [],
                        "confidence": 0.0,
                        "error": "Worker not configured",
                    }
                }
            }

        # Build context for the worker
        context = {
            "preferences": memory_context.get("preferences", {}),
            "user_role": memory_context.get("role"),
        }

        # Query the worker (which queries Genie)
        response = worker.query(query, context)

        # Merge into agent_responses
        current_responses = state.get("agent_responses", {})
        current_responses[domain] = response

        return {"agent_responses": current_responses}

    return worker_node


@mlflow.trace(name="parallel_workers", span_type="AGENT")
def parallel_agents(state: AgentState) -> Dict:
    """
    Execute multiple domain workers in parallel.

    Used for multi-domain queries.
    """
    intent = state.get("intent", {})
    domains = intent.get("domains", [])
    query = state["query"]
    memory_context = state.get("memory_context", {})

    agent_responses = {}

    # Execute workers (could be parallelized with asyncio)
    for domain in domains:
        domain_lower = domain.lower()
        worker = get_worker_agent(domain_lower)

        if worker:
            context = {
                "preferences": memory_context.get("preferences", {}),
                "user_role": memory_context.get("role"),
            }
            response = worker.query(query, context)
            agent_responses[domain_lower] = response
        else:
            agent_responses[domain_lower] = {
                "response": f"Worker for {domain} not available",
                "sources": [],
                "confidence": 0.0,
                "error": "Worker not configured",
            }

    return {"agent_responses": agent_responses}


@mlflow.trace(name="synthesize_response_node", span_type="LLM")
def synthesize_response(state: AgentState) -> Dict:
    """
    Synthesize final response from domain responses.
    """
    query = state["query"]
    agent_responses = state.get("agent_responses", {})
    memory_context = state.get("memory_context", {})

    # Synthesize
    response = synthesizer.synthesize(
        query=query,
        agent_responses=agent_responses,
        user_context=memory_context,
    )

    # Extract sources and calculate confidence
    sources = synthesizer.extract_sources(agent_responses)
    confidence = synthesizer.calculate_confidence(agent_responses)

    # Add assistant message
    messages = [AIMessage(content=response)]

    return {
        "synthesized_response": response,
        "sources": sources,
        "confidence": confidence,
        "messages": messages,
    }


@mlflow.trace(name="save_context", span_type="MEMORY")
def save_context(state: AgentState) -> Dict:
    """
    Save conversation to memory.

    Updates long-term memory with query patterns and insights.
    """
    user_id = state["user_id"]
    query = state["query"]
    intent = state.get("intent", {})

    try:
        # Track query pattern for personalization
        domains = intent.get("domains", [])
        domain_str = ",".join(domains)

        long_term_memory.save_memory(
            user_id=user_id,
            memory_key=f"recent_query_{hash(query) % 10000}",
            memory_data={
                "query": query[:200],  # Truncate long queries
                "domains": domains,
            }
        )
    except Exception:
        # Non-critical - proceed anyway
        pass

    return {}


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================
# TRAINING MATERIAL: Building a LangGraph State Machine
#
# The create_orchestrator_graph() function is the FACTORY that builds
# the execution graph. This is called once, then the graph is reused.

def create_orchestrator_graph() -> StateGraph:
    """
    Create the LangGraph orchestrator workflow.
    
    TRAINING MATERIAL: LangGraph Construction Pattern
    ==================================================
    
    This function demonstrates how to build a production LangGraph:
    
    CONSTRUCTION STEPS:
    1. Create StateGraph with state type
    2. Add nodes (processing functions)
    3. Set entry point
    4. Add edges (fixed transitions)
    5. Add conditional edges (routing logic)
    6. Return uncompiled graph (caller compiles with checkpointer)
    
    GRAPH STRUCTURE VISUALIZATION:
    
                         START
                           │
                           ▼
                    ┌─────────────┐
                    │load_context │  ← Memory retrieval
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │classify_    │  ← Intent classification
                    │intent       │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌──────────┐
         │  cost  │  │security│  │ parallel │
         │ agent  │  │ agent  │  │  agents  │
         └───┬────┘  └───┬────┘  └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │synthesize   │  ← Combine responses
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │save_context │  ← Memory update
                    └──────┬──────┘
                           │
                           ▼
                          END
    
    CONDITIONAL EDGES EXPLAINED:
    ----------------------------
    add_conditional_edges takes:
    - source_node: Where the condition is evaluated
    - path_function: Function that returns the next node name
    - path_map: Dict mapping return values to node names
    
    Example:
    workflow.add_conditional_edges(
        "classify_intent",    # After this node...
        route_to_agents,      # Call this function...
        {"cost_agent": "cost_agent", ...}  # Map return to node
    )
    
    If route_to_agents returns "cost_agent", go to cost_agent node.
    
    WHY RETURN UNCOMPILED:
    ----------------------
    The caller may want to compile with different checkpointers:
    
    # With persistence:
    with get_checkpoint_saver() as checkpointer:
        graph = create_orchestrator_graph().compile(checkpointer=checkpointer)
    
    # Without persistence (stateless):
    graph = create_orchestrator_graph().compile()
    
    BEST PRACTICES:
    ---------------
    1. Node names should be descriptive (not "node1", "node2")
    2. Use factory functions for parameterized nodes (create_worker_node)
    3. All paths should eventually reach END
    4. Handle errors in nodes, not graph construction
    5. Keep graph structure simple; complexity goes in nodes

    The workflow:
    1. Loads user context from memory
    2. Classifies intent to determine domains
    3. Routes to appropriate worker(s)
    4. Synthesizes final response
    5. Saves context to memory

    Returns:
        StateGraph ready for compilation (not compiled).
    """
    # ==========================================================================
    # STEP 1: Create StateGraph with state type
    # ==========================================================================
    # AgentState defines what data flows through the graph
    workflow = StateGraph(AgentState)

    # ==========================================================================
    # STEP 2: Add nodes (processing functions)
    # ==========================================================================
    # Each node is a function: (state: AgentState) -> Dict
    
    # Memory operations
    workflow.add_node("load_context", load_context)
    
    # Intent classification
    workflow.add_node("classify_intent", classify_intent)
    
    # Domain workers (created by factory function)
    workflow.add_node("cost_agent", create_worker_node("cost"))
    workflow.add_node("security_agent", create_worker_node("security"))
    workflow.add_node("performance_agent", create_worker_node("performance"))
    workflow.add_node("reliability_agent", create_worker_node("reliability"))
    workflow.add_node("quality_agent", create_worker_node("quality"))
    
    # Parallel execution for multi-domain queries
    workflow.add_node("parallel_agents", parallel_agents)
    
    # Response synthesis
    workflow.add_node("synthesize", synthesize_response)
    
    # Memory persistence
    workflow.add_node("save_context", save_context)

    # ==========================================================================
    # STEP 3: Define edges (control flow)
    # ==========================================================================
    
    # Entry point: Where execution starts
    workflow.set_entry_point("load_context")
    
    # Fixed edge: load_context → classify_intent
    workflow.add_edge("load_context", "classify_intent")

    # Conditional routing based on intent
    # route_to_agents returns the next node name based on classified domains
    workflow.add_conditional_edges(
        "classify_intent",  # Source node
        route_to_agents,    # Routing function
        {
            # Map return values to node names
            "cost_agent": "cost_agent",
            "security_agent": "security_agent",
            "performance_agent": "performance_agent",
            "reliability_agent": "reliability_agent",
            "quality_agent": "quality_agent",
            "parallel_agents": "parallel_agents",
        }
    )

    # All domain paths converge at synthesize
    # This is the "fan-in" after the "fan-out" from classify_intent
    workflow.add_edge("cost_agent", "synthesize")
    workflow.add_edge("security_agent", "synthesize")
    workflow.add_edge("performance_agent", "synthesize")
    workflow.add_edge("reliability_agent", "synthesize")
    workflow.add_edge("quality_agent", "synthesize")
    workflow.add_edge("parallel_agents", "synthesize")

    # Final steps
    workflow.add_edge("synthesize", "save_context")
    workflow.add_edge("save_context", END)  # END is a special LangGraph constant

    # Return UNCOMPILED graph (caller adds checkpointer)
    return workflow
