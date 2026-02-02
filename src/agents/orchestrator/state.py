"""
TRAINING MATERIAL: LangGraph State Management Pattern
======================================================

This module defines the state schema for the LangGraph orchestrator. State is
the core data structure that flows through the graph, being transformed by
each node.

WHY STATE-BASED ARCHITECTURE:
-----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  STATELESS FUNCTIONS                  │  STATEFUL GRAPH (LangGraph)      │
├───────────────────────────────────────┼──────────────────────────────────┤
│  classify(query) → intent             │  State flows through nodes        │
│  respond(query, intent) → response    │  Each node reads/writes state     │
│  → Need to pass all context manually  │  → Context automatically available│
│  → Hard to add new steps              │  → Easy to insert new nodes       │
│  → Difficult to debug mid-flow        │  → State is inspectable           │
└───────────────────────────────────────┴──────────────────────────────────┘

STATE FLOW THROUGH THE GRAPH:
-----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  INITIAL STATE                                                           │
│  ──────────────                                                          │
│  query: "Why did costs spike?"                                          │
│  user_id: "user@company.com"                                            │
│  intent: {}        ← Empty, will be filled                               │
│  agent_responses: {}                                                    │
│                                                                         │
│       ↓ classify_intent node                                            │
│                                                                         │
│  AFTER CLASSIFICATION                                                    │
│  ────────────────────                                                    │
│  intent: {"domains": ["COST"], "confidence": 0.95}  ← Now filled!       │
│                                                                         │
│       ↓ route_to_workers node                                           │
│                                                                         │
│  AFTER WORKERS                                                           │
│  ─────────────                                                           │
│  agent_responses: {                                                     │
│    "cost": {"response": "...", "sources": [...], "confidence": 0.9}     │
│  }                                                                      │
│                                                                         │
│       ↓ synthesize node                                                 │
│                                                                         │
│  FINAL STATE                                                             │
│  ───────────                                                             │
│  synthesized_response: "Your costs spiked because..."                   │
│  sources: ["Cost Intelligence", "fact_usage"]                           │
│  confidence: 0.92                                                       │
└─────────────────────────────────────────────────────────────────────────┘

KEY DESIGN DECISIONS:
---------------------

1. TypedDict (Not Pydantic)
   - LangGraph works best with TypedDict
   - Easier serialization/checkpointing
   - Compatible with reducer functions

2. Annotated with add_messages
   - messages: Annotated[List[BaseMessage], add_messages]
   - The add_messages reducer automatically merges message lists
   - Prevents accidental message overwriting

3. Optional vs Required Fields
   - Input fields (query, user_id): Required
   - Output fields (synthesized_response): Start empty
   - Error field: Optional for graceful error handling

4. Separate agent_responses and utility_results
   - agent_responses: Domain worker outputs
   - utility_results: Web search, dashboard links
   - Why: Different merge strategies needed

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
