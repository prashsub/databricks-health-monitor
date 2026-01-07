# 05 - Memory System

## Overview

This document details the dual-memory architecture: short-term memory for conversation continuity and long-term memory for user personalization. Both use Databricks Lakebase as the storage backend.

---

## 📍 File Locations

| File | Purpose |
|------|---------|
| `src/agents/memory/__init__.py` | Module exports and factories |
| `src/agents/memory/short_term.py` | CheckpointSaver for conversation state |
| `src/agents/memory/long_term.py` | DatabricksStore for user preferences |

---

## 🧠 Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Memory System                                 │
├───────────────────────────────┬─────────────────────────────────────┤
│       Short-Term Memory       │        Long-Term Memory             │
│       (Conversation)          │        (User Profile)               │
├───────────────────────────────┼─────────────────────────────────────┤
│ Storage: CheckpointSaver      │ Storage: DatabricksStore            │
│ Backend: Lakebase             │ Backend: Lakebase + Embeddings      │
│ Key: thread_id                │ Key: user_id + namespace            │
│ TTL: 24 hours                 │ TTL: 365 days                       │
│ Purpose: State persistence    │ Purpose: Personalization            │
│          across turns         │          via semantic search        │
├───────────────────────────────┼─────────────────────────────────────┤
│ Data:                         │ Data:                               │
│ - Conversation messages       │ - User preferences                  │
│ - Agent state (intent,        │ - Role information                  │
│   worker_results, etc.)       │ - Historical insights               │
│ - Intermediate results        │ - Saved queries                     │
└───────────────────────────────┴─────────────────────────────────────┘
```

---

## 💬 Short-Term Memory

### Purpose

Short-term memory maintains **conversation state** across multiple turns within a session. It enables:

1. **Conversation continuity** - "What was the cost?" → "Break it down by workspace"
2. **State persistence** - Resume interrupted conversations
3. **Checkpoint recovery** - Recover from failures mid-conversation

### Implementation

```python
# File: src/agents/memory/short_term.py
# Lines: 40-110

class ShortTermMemory:
    """
    Short-term memory manager using Lakebase CheckpointSaver.

    This class wraps the Databricks CheckpointSaver to provide:
    - Thread ID management for conversation continuity
    - Automatic checkpoint table setup
    - MLflow tracing for memory operations
    """

    def __init__(self, instance_name: Optional[str] = None):
        """
        Initialize short-term memory.

        Args:
            instance_name: Lakebase instance name. Defaults to settings value.
        """
        self.instance_name = instance_name or settings.lakebase_instance_name
        self._checkpointer: Optional[CheckpointSaver] = None

    def setup(self) -> None:
        """
        Initialize Lakebase checkpoint tables.

        Creates the necessary tables for storing LangGraph checkpoints.
        Should be called once during initial setup.
        """
        with mlflow.start_span(name="setup_checkpoint_tables", span_type="MEMORY") as span:
            span.set_inputs({"instance_name": self.instance_name})

            with CheckpointSaver(instance_name=self.instance_name) as saver:
                saver.setup()

            span.set_outputs({"status": "success"})

    @contextmanager
    def get_checkpointer(self) -> Generator[BaseCheckpointSaver, None, None]:
        """
        Get a CheckpointSaver context manager.

        Usage:
            with memory.get_checkpointer() as checkpointer:
                graph = workflow.compile(checkpointer=checkpointer)
        """
        with CheckpointSaver(instance_name=self.instance_name) as checkpointer:
            yield checkpointer

    def get_thread_history(self, thread_id: str) -> List[Dict]:
        """
        Retrieve conversation history for a thread.

        Args:
            thread_id: Conversation thread identifier

        Returns:
            List of checkpoint states for the thread.
        """
        with mlflow.start_span(name="get_thread_history", span_type="MEMORY") as span:
            span.set_inputs({"thread_id": thread_id})

            with self.get_checkpointer() as checkpointer:
                # Get all checkpoints for thread
                config = {"configurable": {"thread_id": thread_id}}
                history = list(checkpointer.list(config))

            span.set_outputs({"checkpoint_count": len(history)})
            return history

    def clear_thread(self, thread_id: str) -> None:
        """
        Clear conversation history for a thread.

        Args:
            thread_id: Conversation thread identifier
        """
        with mlflow.start_span(name="clear_thread", span_type="MEMORY") as span:
            span.set_inputs({"thread_id": thread_id})

            with self.get_checkpointer() as checkpointer:
                # Delete checkpoints for thread
                config = {"configurable": {"thread_id": thread_id}}
                checkpointer.delete(config)

            span.set_outputs({"status": "cleared"})
```

### Factory Function

```python
# File: src/agents/memory/__init__.py
# Lines: 20-45

# Global instance
_short_term_memory: Optional[ShortTermMemory] = None


def get_short_term_memory() -> ShortTermMemory:
    """
    Get the short-term memory singleton.
    
    Returns:
        ShortTermMemory instance.
    """
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory


@contextmanager
def get_checkpoint_saver():
    """
    Get a CheckpointSaver context manager.
    
    Convenience wrapper for LangGraph integration.
    
    Usage:
        with get_checkpoint_saver() as checkpointer:
            graph = workflow.compile(checkpointer=checkpointer)
    """
    memory = get_short_term_memory()
    with memory.get_checkpointer() as checkpointer:
        yield checkpointer
```

### Usage in Agent

```python
# File: src/agents/orchestrator/agent.py
# Lines: 78-86

@property
def graph(self):
    """Lazily create the orchestrator graph."""
    if self._graph is None:
        workflow = create_orchestrator_graph()
        # Compile with checkpointer for state persistence
        with get_checkpoint_saver() as checkpointer:
            self._graph = workflow.compile(checkpointer=checkpointer)
    return self._graph
```

```python
# Invoking with thread_id
config = {"configurable": {"thread_id": thread_id}}
result = self.graph.invoke(initial_state, config)
```

---

## 📚 Long-Term Memory

### Purpose

Long-term memory stores **user-specific information** that persists across sessions:

1. **User preferences** - Preferred workspaces, cost thresholds
2. **Role information** - Job title, team, access level
3. **Historical insights** - Previous queries and learnings
4. **Personalization data** - Language preferences, report formats

### Implementation

```python
# File: src/agents/memory/long_term.py
# Lines: 65-200

class LongTermMemory:
    """
    Long-term memory manager using Lakebase DatabricksStore.

    This class provides:
    - Vector-based semantic search over user memories
    - Namespace isolation per user
    - CRUD operations for memory items
    - MLflow tracing for all operations
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

    @property
    def store(self) -> DatabricksStore:
        """Lazily initialize DatabricksStore."""
        if self._store is None:
            self._store = DatabricksStore(
                instance_name=self.instance_name,
                embedding_endpoint=self.embedding_endpoint,
                embedding_dims=self.embedding_dims,
            )
        return self._store

    def setup(self) -> None:
        """
        Initialize Lakebase memory tables.
        
        Creates the vector store tables for memory storage.
        """
        with mlflow.start_span(name="setup_memory_store", span_type="MEMORY") as span:
            span.set_inputs({"instance_name": self.instance_name})
            self.store.setup()
            span.set_outputs({"status": "success"})

    @mlflow.trace(name="save_memory", span_type="MEMORY")
    def save_memory(
        self,
        user_id: str,
        memory_key: str,
        memory_data: Dict[str, Any],
        namespace: str = "default",
    ) -> None:
        """
        Save a memory item for a user.

        Args:
            user_id: User identifier
            memory_key: Unique key for this memory (e.g., "preferred_workspace")
            memory_data: Data to store (will be serialized to JSON)
            namespace: Memory namespace for organization
        """
        # Build full key with namespace
        full_key = f"{namespace}:{memory_key}"

        # Serialize data
        value = json.dumps(memory_data)

        # Store with user namespace
        self.store.put(
            namespace=(user_id,),
            key=full_key,
            value=value,
        )

    @mlflow.trace(name="search_memories", span_type="RETRIEVER")
    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        namespace: str = None,
    ) -> List[MemoryItem]:
        """
        Search user memories by semantic similarity.

        Args:
            user_id: User identifier
            query: Search query (semantic search)
            limit: Maximum results to return
            namespace: Optional namespace filter

        Returns:
            List of MemoryItem objects sorted by relevance.
        """
        # Search in user's namespace
        results = self.store.search(
            namespace=(user_id,),
            query=query,
            limit=limit,
        )

        # Parse results
        memories = []
        for item in results:
            try:
                value = json.loads(item.value)
            except json.JSONDecodeError:
                value = {"raw": item.value}

            memories.append(MemoryItem(
                key=item.key,
                value=value,
                score=item.score if hasattr(item, 'score') else None,
            ))

        return memories

    @mlflow.trace(name="get_memory", span_type="MEMORY")
    def get_memory(
        self,
        user_id: str,
        memory_key: str,
        namespace: str = "default",
    ) -> Optional[MemoryItem]:
        """
        Get a specific memory item.

        Args:
            user_id: User identifier
            memory_key: Memory key to retrieve
            namespace: Memory namespace

        Returns:
            MemoryItem or None if not found.
        """
        full_key = f"{namespace}:{memory_key}"

        result = self.store.get(
            namespace=(user_id,),
            key=full_key,
        )

        if result is None:
            return None

        try:
            value = json.loads(result.value)
        except json.JSONDecodeError:
            value = {"raw": result.value}

        return MemoryItem(key=memory_key, value=value)

    @mlflow.trace(name="delete_memory", span_type="MEMORY")
    def delete_memory(
        self,
        user_id: str,
        memory_key: str,
        namespace: str = "default",
    ) -> bool:
        """
        Delete a memory item.

        Args:
            user_id: User identifier
            memory_key: Memory key to delete
            namespace: Memory namespace

        Returns:
            True if deleted, False if not found.
        """
        full_key = f"{namespace}:{memory_key}"

        try:
            self.store.delete(
                namespace=(user_id,),
                key=full_key,
            )
            return True
        except Exception:
            return False
```

### Memory Item Data Class

```python
# File: src/agents/memory/long_term.py
# Lines: 48-62

@dataclass
class MemoryItem:
    """Represents a stored memory item."""

    key: str
    value: Dict[str, Any]
    score: Optional[float] = None  # Relevance score from search

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "score": self.score,
        }
```

### Usage in Graph

```python
# File: src/agents/orchestrator/graph.py
# Lines: 31-65

@mlflow.trace(name="load_context", span_type="MEMORY")
def load_context(state: AgentState) -> Dict:
    """
    Load memory context for the user.
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
        mlflow.log_metric("memory_load_error", 1)

    return {"memory_context": memory_context}
```

---

## 🔧 LangChain Memory Tools

### Save Memory Tool

```python
# File: src/agents/memory/long_term.py
# Lines: 280-330

@tool
def save_user_preference(
    preference_name: str,
    preference_value: str,
    config: RunnableConfig,
) -> str:
    """
    Save a user preference to long-term memory.

    Use this tool when the user expresses a preference that should be
    remembered for future interactions.

    Args:
        preference_name: Name of the preference (e.g., "favorite_workspace")
        preference_value: Value of the preference

    Examples:
        - User says "I mainly work with the production workspace"
          → save_user_preference("preferred_workspace", "production")
        - User says "Costs above $500 concern me"
          → save_user_preference("cost_threshold", "500")
    """
    # Extract user_id from config
    user_id = config.get("configurable", {}).get("user_id", "anonymous")

    memory = get_long_term_memory()
    memory.save_memory(
        user_id=user_id,
        memory_key=f"preference:{preference_name}",
        memory_data={
            "name": preference_name,
            "value": preference_value,
        },
        namespace="preferences",
    )

    return f"Saved preference: {preference_name} = {preference_value}"


@tool
def recall_user_context(
    query: str,
    config: RunnableConfig,
) -> str:
    """
    Search user's memory for relevant context.

    Use this tool to retrieve information about the user that might
    help personalize the response.

    Args:
        query: What to search for in user memory

    Returns:
        Relevant memories as a formatted string.
    """
    user_id = config.get("configurable", {}).get("user_id", "anonymous")

    memory = get_long_term_memory()
    results = memory.search_memories(
        user_id=user_id,
        query=query,
        limit=3,
    )

    if not results:
        return "No relevant memories found."

    formatted = []
    for mem in results:
        formatted.append(f"- {mem.key}: {mem.value}")

    return "User context:\n" + "\n".join(formatted)
```

---

## 📊 Memory Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Request                                 │
│                   thread_id: "conv_123"                             │
│                   user_id: "user@company.com"                       │
│                   query: "What's the cost trend?"                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    1. Load Long-Term Memory                          │
│                                                                      │
│   search_memories(user_id, "preferences workspace threshold")        │
│                                                                      │
│   Results:                                                           │
│   - preferences:workspace → {"workspace": "prod"}                    │
│   - preferences:cost_threshold → {"value": 1000}                     │
│   - role:job_title → {"role": "data_engineer"}                       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    2. Check Short-Term Memory                        │
│                                                                      │
│   CheckpointSaver.get(thread_id="conv_123")                          │
│                                                                      │
│   Previous State (if exists):                                        │
│   - messages: [HumanMessage("Show me costs"), AIMessage("Here...")]  │
│   - worker_results: {"cost": {...}}                                  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    3. Process Request                                │
│                                                                      │
│   memory_context = {                                                 │
│     "preferences": {"workspace": "prod", "cost_threshold": 1000},    │
│     "role": "data_engineer",                                         │
│   }                                                                  │
│                                                                      │
│   Enhanced query: "What's the cost trend?"                           │
│                   + "Context: Focus on prod workspace"               │
│                   + "Consider costs above $1000 significant"         │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    4. Save State Checkpoint                          │
│                                                                      │
│   CheckpointSaver.put(thread_id="conv_123", state={...})             │
│                                                                      │
│   State saved for conversation continuity                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Settings

```python
# File: src/agents/config/settings.py
# Lines: 96-108

# Lakebase Memory Configuration
lakebase_instance_name: str = field(
    default_factory=lambda: os.environ.get("LAKEBASE_INSTANCE_NAME", "health_monitor_memory")
)

# Short-term memory (conversation context)
short_term_memory_ttl_hours: int = field(
    default_factory=lambda: int(os.environ.get("SHORT_TERM_MEMORY_TTL_HOURS", "24"))
)

# Long-term memory (user preferences, insights)
long_term_memory_ttl_days: int = field(
    default_factory=lambda: int(os.environ.get("LONG_TERM_MEMORY_TTL_DAYS", "365"))
)

# Embedding model for long-term memory vector search
embedding_endpoint: str = field(
    default_factory=lambda: os.environ.get("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
)
embedding_dims: int = field(
    default_factory=lambda: int(os.environ.get("EMBEDDING_DIMS", "1024"))
)
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LAKEBASE_INSTANCE_NAME` | `health_monitor_memory` | Lakebase instance |
| `SHORT_TERM_MEMORY_TTL_HOURS` | `24` | Conversation expiry |
| `LONG_TERM_MEMORY_TTL_DAYS` | `365` | User data expiry |
| `EMBEDDING_ENDPOINT` | `databricks-gte-large-en` | Embedding model |
| `EMBEDDING_DIMS` | `1024` | Vector dimensions |

---

## 🧪 Testing Memory

### Unit Tests

```python
# Test short-term memory
def test_short_term_memory():
    memory = ShortTermMemory(instance_name="test_memory")
    
    # Setup tables
    memory.setup()
    
    # Get checkpointer
    with memory.get_checkpointer() as checkpointer:
        # Compile graph with checkpointer
        graph = workflow.compile(checkpointer=checkpointer)
        
        # Invoke with thread_id
        config = {"configurable": {"thread_id": "test-thread"}}
        result = graph.invoke(state, config)
        
        # Verify state persisted
        history = memory.get_thread_history("test-thread")
        assert len(history) > 0


# Test long-term memory
def test_long_term_memory():
    memory = LongTermMemory(instance_name="test_memory")
    
    # Setup tables
    memory.setup()
    
    # Save preference
    memory.save_memory(
        user_id="test_user",
        memory_key="workspace_preference",
        memory_data={"workspace": "production"},
    )
    
    # Search memories
    results = memory.search_memories(
        user_id="test_user",
        query="workspace preference",
    )
    
    assert len(results) > 0
    assert results[0].value.get("workspace") == "production"
```

---

**Next:** [06-tracing-and-observability.md](./06-tracing-and-observability.md)

