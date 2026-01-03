"""
LangGraph Orchestrator Graph
============================

Defines the state machine for multi-agent orchestration.
"""

from typing import Dict, Literal
import mlflow

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from .state import AgentState
from .intent_classifier import IntentClassifier
from .synthesizer import ResponseSynthesizer
from ..memory import get_checkpoint_saver, get_long_term_memory
from ..workers import get_worker_agent


# Initialize components
intent_classifier = IntentClassifier()
synthesizer = ResponseSynthesizer()
long_term_memory = get_long_term_memory()


# =============================================================================
# Node Functions
# =============================================================================

@mlflow.trace(name="load_context", span_type="MEMORY")
def load_context(state: AgentState) -> Dict:
    """
    Load memory context for the user.

    Retrieves long-term memory (preferences, insights) to personalize
    the response.
    """
    user_id = state["user_id"]

    memory_context = {
        "preferences": {},
        "role": None,
        "recent_queries": [],
    }

    try:
        # Search for user preferences
        prefs = long_term_memory.search_memories(
            user_id=user_id,
            query="user preferences workspace threshold",
            limit=3,
        )

        for mem in prefs:
            if "preference" in mem.key.lower():
                memory_context["preferences"].update(mem.value)
            if "role" in mem.key.lower():
                memory_context["role"] = mem.value.get("role")

    except Exception as e:
        # Memory unavailable - proceed without context
        mlflow.log_metric("memory_load_error", 1)

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
# Graph Construction
# =============================================================================

def create_orchestrator_graph() -> StateGraph:
    """
    Create the LangGraph orchestrator workflow.

    The workflow:
    1. Loads user context from memory
    2. Classifies intent to determine domains
    3. Routes to appropriate worker(s)
    4. Synthesizes final response
    5. Saves context to memory

    Returns:
        Compiled StateGraph ready for execution.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("load_context", load_context)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("cost_agent", create_worker_node("cost"))
    workflow.add_node("security_agent", create_worker_node("security"))
    workflow.add_node("performance_agent", create_worker_node("performance"))
    workflow.add_node("reliability_agent", create_worker_node("reliability"))
    workflow.add_node("quality_agent", create_worker_node("quality"))
    workflow.add_node("parallel_agents", parallel_agents)
    workflow.add_node("synthesize", synthesize_response)
    workflow.add_node("save_context", save_context)

    # Define edges
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "classify_intent")

    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "classify_intent",
        route_to_agents,
        {
            "cost_agent": "cost_agent",
            "security_agent": "security_agent",
            "performance_agent": "performance_agent",
            "reliability_agent": "reliability_agent",
            "quality_agent": "quality_agent",
            "parallel_agents": "parallel_agents",
        }
    )

    # All paths lead to synthesize
    workflow.add_edge("cost_agent", "synthesize")
    workflow.add_edge("security_agent", "synthesize")
    workflow.add_edge("performance_agent", "synthesize")
    workflow.add_edge("reliability_agent", "synthesize")
    workflow.add_edge("quality_agent", "synthesize")
    workflow.add_edge("parallel_agents", "synthesize")

    # Final steps
    workflow.add_edge("synthesize", "save_context")
    workflow.add_edge("save_context", END)

    return workflow
