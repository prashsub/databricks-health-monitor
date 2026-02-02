"""
Long-Term Memory with Lakebase DatabricksStore
=============================================

TRAINING MATERIAL: Long-Term Memory Pattern for AI Agents
----------------------------------------------------------

This module implements user-based persistent memory using vector embeddings.
Long-term memory enables the agent to remember user preferences and insights
across multiple conversations and sessions.

LONG-TERM MEMORY ARCHITECTURE:
------------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    LONG-TERM MEMORY FLOW                                 │
│                                                                         │
│  SAVE MEMORY (User sets preference)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. User: "I prefer to see costs for prod workspace only"        │   │
│  │  2. Agent extracts preference                                    │   │
│  │  3. save_memory(user_id, "preferred_workspace", {"value":"prod"})│   │
│  │  4. DatabricksStore → Embeds text → Stores in vector index       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  SEARCH MEMORY (Next session, different conversation)                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. User: "Show me the costs"                                    │   │
│  │  2. Agent: search_memories(user_id, "workspace preferences")     │   │
│  │  3. DatabricksStore → Semantic search → Returns relevant memories│   │
│  │  4. Agent: "Based on your preference, showing prod workspace..." │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

WHY VECTOR SEARCH FOR MEMORIES:
-------------------------------
Memories are stored with embeddings, enabling SEMANTIC search:

Traditional: Search by exact key
  "preferred_workspace" → {"value": "prod"}

Semantic: Search by meaning
  "What workspace does the user like?" → Finds "preferred_workspace"!
  "user's favorite environment" → Also finds "preferred_workspace"!

This is powerful because:
- Users don't remember exact keys
- Related memories are found together
- Context-aware retrieval

NAMESPACE ISOLATION:
--------------------
Each user has their own namespace, preventing memory leakage:

user1@company.com → namespace: ("user_memories", "user1-at-company-com")
user2@company.com → namespace: ("user_memories", "user2-at-company-com")

Search in user1's namespace ONLY returns user1's memories.

MEMORY TYPES TO STORE:
----------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  MEMORY TYPE        │  KEY PATTERN           │  EXAMPLE                 │
├─────────────────────┼────────────────────────┼──────────────────────────┤
│  Preferences        │  pref_<topic>          │  pref_workspace: "prod"  │
│  Thresholds         │  threshold_<metric>    │  threshold_cost: 10000   │
│  Insights           │  insight_<date>        │  insight_2025-01: "..."  │
│  Relationships      │  team_<name>           │  team_finance: [users]   │
│  Context            │  context_<topic>       │  context_project: "X"    │
└─────────────────────┴────────────────────────┴──────────────────────────┘

LANGCHAIN TOOL INTEGRATION:
---------------------------
Memory operations are exposed as LangChain tools, allowing the agent
to autonomously decide when to save or retrieve memories:

- get_user_memory: Semantic search for relevant memories
- save_user_memory: Store new preference/insight
- delete_user_memory: Remove a memory (user request)

Key Features:
    - Semantic search over stored memories
    - User namespace isolation
    - Vector embeddings for similarity retrieval
    - Structured memory storage (preferences, insights)

Reference:
    https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html

Usage:
    from agents.memory import get_memory_store

    store = get_memory_store()

    # Save user preference
    store.save_memory(
        user_id="user@example.com",
        memory_key="preferred_workspace",
        memory_data={"workspace": "prod", "reason": "Most used"}
    )

    # Retrieve relevant memories
    memories = store.search_memories(
        user_id="user@example.com",
        query="What workspace does the user prefer?"
    )
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization for Memory Module
#
# typing: For type hints
# dataclasses: For MemoryItem dataclass
# json: For serializing memory data
# mlflow: For tracing memory operations

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
import mlflow

# DATABRICKS-SPECIFIC IMPORTS:
# DatabricksStore: Vector store for long-term memory
from databricks_langchain import DatabricksStore

# LANGCHAIN IMPORTS:
# tool: Decorator to create LangChain tools from functions
# RunnableConfig: Config object passed to tools (contains user_id)
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from ..config import settings


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MemoryItem:
    """Represents a stored memory item."""

    key: str
    value: Dict[str, Any]
    score: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "score": self.score,
        }


class LongTermMemory:
    """
    Long-term memory manager using Lakebase DatabricksStore.

    This class provides:
    - Vector-based semantic search over user memories
    - Namespace isolation per user
    - CRUD operations for memory items
    - MLflow tracing for all operations

    Attributes:
        instance_name: Lakebase instance name
        embedding_endpoint: Databricks embedding model endpoint
        embedding_dims: Embedding vector dimensions
        _store: Underlying DatabricksStore instance
    """

    def __init__(
        self,
        instance_name: Optional[str] = None,
        embedding_endpoint: Optional[str] = None,
        embedding_dims: Optional[int] = None,
    ):
        """
        Initialize long-term memory.

        Args:
            instance_name: Lakebase instance name
            embedding_endpoint: Databricks embedding model endpoint
            embedding_dims: Embedding vector dimensions
        """
        self.instance_name = instance_name or settings.lakebase_instance_name
        self.embedding_endpoint = embedding_endpoint or settings.embedding_endpoint
        self.embedding_dims = embedding_dims or settings.embedding_dims
        self._store: Optional[DatabricksStore] = None

    def _get_store(self) -> DatabricksStore:
        """Get or create the DatabricksStore instance."""
        if self._store is None:
            self._store = DatabricksStore(
                instance_name=self.instance_name,
                embedding_endpoint=self.embedding_endpoint,
                embedding_dims=self.embedding_dims,
            )
        return self._store

    def setup(self) -> None:
        """
        Initialize Lakebase memory store.

        Creates necessary tables and indexes for vector storage.
        Should be called once during initial setup.
        """
        with mlflow.start_span(name="setup_memory_store", span_type="MEMORY") as span:
            span.set_inputs({
                "instance_name": self.instance_name,
                "embedding_endpoint": self.embedding_endpoint,
            })

            store = self._get_store()
            store.setup()

            span.set_outputs({"status": "success"})

    @staticmethod
    def _get_namespace(user_id: str) -> tuple:
        """
        Get namespace tuple for user memory isolation.

        Args:
            user_id: User identifier (e.g., email)

        Returns:
            Namespace tuple for DatabricksStore operations.
        """
        # Sanitize user_id for namespace (replace dots and special chars)
        sanitized = user_id.replace(".", "-").replace("@", "-at-")
        return ("user_memories", sanitized)

    @mlflow.trace(name="save_memory", span_type="MEMORY")
    def save_memory(
        self,
        user_id: str,
        memory_key: str,
        memory_data: Dict[str, Any],
    ) -> str:
        """
        Save a memory item for a user.

        Args:
            user_id: User identifier
            memory_key: Unique key for this memory
            memory_data: Memory data as a dictionary

        Returns:
            Success message string.
        """
        with mlflow.start_span(name="store_put") as span:
            span.set_inputs({
                "user_id": user_id,
                "memory_key": memory_key,
                "data_keys": list(memory_data.keys()),
            })

            namespace = self._get_namespace(user_id)
            store = self._get_store()
            store.put(namespace, memory_key, memory_data)

            span.set_outputs({"status": "success"})

        return f"Successfully saved memory with key '{memory_key}'"

    @mlflow.trace(name="search_memories", span_type="RETRIEVER")
    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> List[MemoryItem]:
        """
        Search user's memories using semantic similarity.

        Args:
            user_id: User identifier
            query: Natural language search query
            limit: Maximum number of results

        Returns:
            List of relevant MemoryItem objects.
        """
        with mlflow.start_span(name="store_search") as span:
            span.set_inputs({
                "user_id": user_id,
                "query": query,
                "limit": limit,
            })

            namespace = self._get_namespace(user_id)
            store = self._get_store()

            results = store.search(namespace, query=query, limit=limit)

            memories = [
                MemoryItem(
                    key=item.key,
                    value=item.value,
                    score=getattr(item, "score", None),
                )
                for item in results
            ]

            span.set_outputs({
                "result_count": len(memories),
                "keys": [m.key for m in memories],
            })

            return memories

    @mlflow.trace(name="get_memory", span_type="MEMORY")
    def get_memory(
        self,
        user_id: str,
        memory_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by key.

        Args:
            user_id: User identifier
            memory_key: Memory key to retrieve

        Returns:
            Memory data dict or None if not found.
        """
        namespace = self._get_namespace(user_id)
        store = self._get_store()

        try:
            item = store.get(namespace, memory_key)
            return item.value if item else None
        except Exception:
            return None

    @mlflow.trace(name="delete_memory", span_type="MEMORY")
    def delete_memory(
        self,
        user_id: str,
        memory_key: str,
    ) -> str:
        """
        Delete a specific memory.

        Args:
            user_id: User identifier
            memory_key: Memory key to delete

        Returns:
            Success message string.
        """
        namespace = self._get_namespace(user_id)
        store = self._get_store()
        store.delete(namespace, memory_key)

        return f"Successfully deleted memory with key '{memory_key}'"

    @mlflow.trace(name="list_memories", span_type="MEMORY")
    def list_memories(
        self,
        user_id: str,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """
        List all memory keys for a user.

        Args:
            user_id: User identifier
            prefix: Optional key prefix filter

        Returns:
            List of memory keys.
        """
        namespace = self._get_namespace(user_id)
        store = self._get_store()

        # Search with empty query returns all items
        results = store.search(namespace, query="", limit=100)

        keys = [item.key for item in results]
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]

        return keys


# ============================================================================
# LangChain Tools for Agent Integration
# ============================================================================

def create_memory_tools(memory: LongTermMemory) -> list:
    """
    Create LangChain tools for memory operations.

    These tools can be added to an agent's tool list to enable
    autonomous memory management.

    Args:
        memory: LongTermMemory instance

    Returns:
        List of LangChain tools for memory operations.
    """

    @tool
    def get_user_memory(query: str, config: RunnableConfig) -> str:
        """
        Search user's long-term memory using semantic similarity.

        Use this tool to recall user preferences, past insights,
        or any previously stored information relevant to the query.

        Args:
            query: Natural language description of what to find
            config: LangChain config (contains user_id)

        Returns:
            Formatted string of relevant memories.
        """
        user_id = config.get("configurable", {}).get("user_id", "unknown")

        results = memory.search_memories(user_id, query, limit=5)

        if not results:
            return "No memories found for this user."

        memory_items = [
            f"- [{item.key}]: {json.dumps(item.value)}"
            for item in results
        ]
        return "\n".join(memory_items)

    @tool
    def save_user_memory(
        memory_key: str,
        memory_data_json: str,
        config: RunnableConfig,
    ) -> str:
        """
        Save structured information to user's long-term memory.

        Use this tool to persist user preferences, important insights,
        or any information that should be remembered across conversations.

        Args:
            memory_key: Unique identifier for this memory (e.g., "preferred_workspace")
            memory_data_json: JSON string containing the memory data
            config: LangChain config (contains user_id)

        Returns:
            Success or error message.
        """
        user_id = config.get("configurable", {}).get("user_id", "unknown")

        try:
            memory_data = json.loads(memory_data_json)
            if not isinstance(memory_data, dict):
                return "Error: Memory data must be a JSON object (dictionary)"

            return memory.save_memory(user_id, memory_key, memory_data)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON - {str(e)}"

    @tool
    def delete_user_memory(memory_key: str, config: RunnableConfig) -> str:
        """
        Delete a specific memory from user's long-term storage.

        Use this tool when the user explicitly requests to forget
        or remove stored information.

        Args:
            memory_key: Key of the memory to delete
            config: LangChain config (contains user_id)

        Returns:
            Success message.
        """
        user_id = config.get("configurable", {}).get("user_id", "unknown")
        return memory.delete_memory(user_id, memory_key)

    return [get_user_memory, save_user_memory, delete_user_memory]


# Module-level convenience function
def get_memory_store(
    instance_name: Optional[str] = None,
) -> LongTermMemory:
    """
    Get a LongTermMemory instance.

    Args:
        instance_name: Optional Lakebase instance name override.

    Returns:
        LongTermMemory instance.

    Example:
        from agents.memory import get_memory_store

        store = get_memory_store()

        # Save a preference
        store.save_memory(
            user_id="user@example.com",
            memory_key="cost_threshold",
            memory_data={"threshold_usd": 10000, "alert": True}
        )

        # Search memories
        memories = store.search_memories(
            user_id="user@example.com",
            query="cost alerts and thresholds"
        )
    """
    return LongTermMemory(instance_name=instance_name)


# Singleton instance
_long_term_memory: Optional[LongTermMemory] = None


def get_long_term_memory() -> LongTermMemory:
    """Get the singleton LongTermMemory instance."""
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory()
    return _long_term_memory
