"""
Memory Management Module
========================

TRAINING MATERIAL: Stateful Agent Memory Architecture
-----------------------------------------------------

This module provides the memory infrastructure for building stateful AI agents.
Understanding these patterns is essential for building production-grade
conversational AI on Databricks.

CORE CONCEPT: Two-Layer Memory Architecture
============================================

Agents need two distinct types of memory:

┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SHORT-TERM MEMORY (CheckpointSaver)                                │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  WHAT: LangGraph state (conversation history, intermediate results) │   │
│  │  SCOPE: Single conversation thread (thread_id)                      │   │
│  │  LIFETIME: Hours to days (TTL configurable)                         │   │
│  │  USE CASE: "What did I ask 5 minutes ago?"                         │   │
│  │                                                                     │   │
│  │  User: "Why did costs spike?"                                       │   │
│  │  Agent: "Costs spiked due to SKU X..."                             │   │
│  │  User: "Tell me more about that SKU"  ← Requires memory!           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LONG-TERM MEMORY (DatabricksStore)                                 │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  WHAT: User preferences, insights, patterns                         │   │
│  │  SCOPE: Entire user history (user_id)                              │   │
│  │  LIFETIME: Months to years (TTL configurable)                       │   │
│  │  USE CASE: "Remember my preferred cost threshold"                   │   │
│  │                                                                     │   │
│  │  User (Day 1): "Alert me when costs exceed $1000"                  │   │
│  │  Agent: [Stores preference]                                         │   │
│  │  User (Day 30): "Check my alerts"                                   │   │
│  │  Agent: "Based on your $1000 threshold..." ← Requires memory!      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

WHY DATABRICKS LAKEBASE:
------------------------
1. Unity Catalog-backed: Governed, auditable, enterprise-grade
2. Managed service: No infrastructure to maintain
3. Vector search: Semantic retrieval for long-term memory
4. Delta Lake: ACID transactions, time travel
5. Integrated: Works with LangGraph and MLflow

KEY IDENTIFIERS:
----------------
- thread_id: Identifies a conversation (short-term memory key)
- user_id: Identifies a human user (long-term memory key)

IMPORTANT: These are different!
- Same user can have multiple threads (different conversations)
- Same thread should not span multiple users (conversation isolation)

GRACEFUL DEGRADATION:
---------------------
Memory is an OPTIONAL enhancement, not a requirement.
If Lakebase tables don't exist:
- Agent should still function (stateless mode)
- No errors thrown (silent fallback)
- User experience slightly degraded (no context retention)

This pattern ensures:
- Agent works during initial setup (before tables created)
- Agent works if Lakebase service unavailable
- Testing possible without full infrastructure

SETUP REQUIREMENTS:
-------------------
1. Create Lakebase instance (via workspace admin)
2. Run setup script to create tables:
   - Short-term: ShortTermMemory().setup()
   - Long-term: LongTermMemory().setup()
3. Configure embedding endpoint (for long-term semantic search)

Provides short-term and long-term memory using Databricks Lakebase.

Short-Term Memory (CheckpointSaver):
    - Persists LangGraph state across conversation turns
    - Uses thread_id for session continuity
    - TTL: 24 hours (configurable)

Long-Term Memory (DatabricksStore):
    - Stores user preferences, insights, and patterns
    - Vector embeddings for semantic retrieval
    - TTL: 365 days (configurable)

USAGE EXAMPLES:
---------------

# Short-term memory with LangGraph
from agents.memory import get_checkpoint_saver, ShortTermMemory

with get_checkpoint_saver() as checkpointer:
    graph = workflow.compile(checkpointer=checkpointer)
    
    # Execute with thread_id for continuity
    thread_id = ShortTermMemory.resolve_thread_id(custom_inputs, conversation_id)
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(state, config)

# Long-term memory for user preferences
from agents.memory import get_memory_store

with get_memory_store() as store:
    # Save a preference
    store.save_memory(
        user_id="analyst@company.com",
        memory_key="preferred_cost_threshold",
        memory_data={"threshold": 1000, "currency": "USD"}
    )
    
    # Search memories semantically
    results = store.search_memories(
        user_id="analyst@company.com",
        query="cost alerting preferences"
    )

Reference:
    - https://docs.databricks.com/aws/en/notebooks/source/generative-ai/short-term-memory-agent-lakebase.html
    - https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html
"""

# =============================================================================
# EXPORTS
# =============================================================================
# TRAINING MATERIAL: Python Package Organization
#
# This __init__.py file makes these classes importable as:
#   from agents.memory import ShortTermMemory
# Instead of:
#   from agents.memory.short_term import ShortTermMemory
#
# WHY __all__: Explicit list of public API (what gets imported with *)
# BEST PRACTICE: Keep __all__ synchronized with actual exports

from .short_term import ShortTermMemory, get_checkpoint_saver
from .long_term import LongTermMemory, get_memory_store

__all__ = [
    # Short-term (conversation continuity)
    "ShortTermMemory",       # Class for advanced usage
    "get_checkpoint_saver",  # Context manager for simple usage
    
    # Long-term (user preferences)
    "LongTermMemory",        # Class for advanced usage
    "get_memory_store",      # Context manager for simple usage
]
