"""
Agent State Definition
======================

Defines the state schema for the LangGraph orchestrator.
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State schema for the Health Monitor orchestrator.

    This state is passed through all nodes in the LangGraph workflow.

    Attributes:
        query: Original user query
        user_id: User identifier for memory and permissions
        session_id: Session ID for short-term memory (thread_id)
        messages: Conversation messages (uses add_messages reducer)
        intent: Classified intent with domains and confidence
        agent_responses: Responses from domain worker agents
        utility_results: Results from utility tools
        synthesized_response: Final synthesized response
        sources: Data sources cited in response
        confidence: Overall response confidence score
        memory_context: Retrieved memory context
        error: Any error message
    """

    # Input
    query: str
    user_id: str
    session_id: Optional[str]

    # Messages with LangGraph reducer for automatic merging
    messages: Annotated[List[BaseMessage], add_messages]

    # Intent classification
    intent: Dict[str, any]  # {"domains": [...], "confidence": float}

    # Worker agent responses
    agent_responses: Dict[str, Dict]  # {"cost": {...}, "security": {...}, ...}

    # Utility tool results
    utility_results: Dict[str, any]

    # Output
    synthesized_response: str
    sources: List[str]
    confidence: float

    # Context
    memory_context: Dict[str, any]

    # Error handling
    error: Optional[str]


def create_initial_state(
    query: str,
    user_id: str,
    session_id: Optional[str] = None,
    messages: Optional[List[BaseMessage]] = None,
) -> AgentState:
    """
    Create initial state for a new query.

    Args:
        query: User query string
        user_id: User identifier
        session_id: Optional session ID for memory
        messages: Optional existing messages

    Returns:
        Initialized AgentState.
    """
    return AgentState(
        query=query,
        user_id=user_id,
        session_id=session_id,
        messages=messages or [],
        intent={},
        agent_responses={},
        utility_results={},
        synthesized_response="",
        sources=[],
        confidence=0.0,
        memory_context={},
        error=None,
    )
