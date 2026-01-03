"""
Memory Management Module
========================

Provides short-term and long-term memory using Databricks Lakebase.

Short-Term Memory (CheckpointSaver):
    - Persists LangGraph state across conversation turns
    - Uses thread_id for session continuity
    - TTL: 24 hours (configurable)

Long-Term Memory (DatabricksStore):
    - Stores user preferences, insights, and patterns
    - Vector embeddings for semantic retrieval
    - TTL: 365 days (configurable)

Reference:
    - https://docs.databricks.com/aws/en/notebooks/source/generative-ai/short-term-memory-agent-lakebase.html
    - https://docs.databricks.com/aws/en/notebooks/source/generative-ai/long-term-memory-agent-lakebase.html
"""

from .short_term import ShortTermMemory, get_checkpoint_saver
from .long_term import LongTermMemory, get_memory_store

__all__ = [
    "ShortTermMemory",
    "LongTermMemory",
    "get_checkpoint_saver",
    "get_memory_store",
]
