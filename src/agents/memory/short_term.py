"""
Short-Term Memory with Lakebase CheckpointSaver
==============================================

Implements conversation-level state persistence using Databricks Lakebase.
Based on the official Databricks short-term memory agent pattern.

Key Features:
    - Thread-based conversation continuity
    - Automatic state persistence across turns
    - LangGraph checkpoint integration
    - Efficient retrieval by thread_id

Reference:
    https://docs.databricks.com/aws/en/notebooks/source/generative-ai/short-term-memory-agent-lakebase.html

Usage:
    from agents.memory import get_checkpoint_saver

    # Get checkpoint saver for LangGraph
    with get_checkpoint_saver() as checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)

        # Execute with thread_id for state persistence
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(inputs, config)
"""

from typing import Optional, Generator
from contextlib import contextmanager
import uuid
import mlflow

from databricks_langchain import CheckpointSaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from ..config import settings


class ShortTermMemory:
    """
    Short-term memory manager using Lakebase CheckpointSaver.

    This class wraps the Databricks CheckpointSaver to provide:
    - Thread ID management for conversation continuity
    - Automatic checkpoint table setup
    - MLflow tracing for memory operations

    Attributes:
        instance_name: Lakebase instance name
        _checkpointer: Underlying CheckpointSaver instance
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

        This creates the necessary tables for storing LangGraph checkpoints.
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
        Get a checkpoint saver context for LangGraph compilation.

        Yields:
            CheckpointSaver instance for use with LangGraph.

        Example:
            with memory.get_checkpointer() as checkpointer:
                graph = workflow.compile(checkpointer=checkpointer)
        """
        with CheckpointSaver(instance_name=self.instance_name) as checkpointer:
            yield checkpointer

    @staticmethod
    def generate_thread_id() -> str:
        """Generate a new unique thread ID for a conversation."""
        return str(uuid.uuid4())

    @staticmethod
    @mlflow.trace(name="resolve_thread_id", span_type="MEMORY")
    def resolve_thread_id(
        custom_inputs: Optional[dict] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Resolve thread ID from various sources.

        Priority:
            1. custom_inputs["thread_id"] - Explicit thread ID
            2. conversation_id - From ChatContext
            3. New UUID - Fresh conversation

        Args:
            custom_inputs: Custom inputs dict from request
            conversation_id: Conversation ID from ChatContext

        Returns:
            Thread ID string for checkpoint configuration.
        """
        # Check custom_inputs first
        if custom_inputs and custom_inputs.get("thread_id"):
            return custom_inputs["thread_id"]

        # Fall back to conversation_id
        if conversation_id:
            return conversation_id

        # Generate new thread ID
        return ShortTermMemory.generate_thread_id()

    @staticmethod
    def get_checkpoint_config(thread_id: str) -> dict:
        """
        Build LangGraph checkpoint configuration.

        Args:
            thread_id: Thread ID for the conversation

        Returns:
            Configuration dict for LangGraph invocation.
        """
        return {"configurable": {"thread_id": thread_id}}


# Module-level convenience function
@contextmanager
def get_checkpoint_saver(
    instance_name: Optional[str] = None
) -> Generator[BaseCheckpointSaver, None, None]:
    """
    Get a CheckpointSaver for LangGraph state persistence.

    This is the recommended way to use short-term memory with LangGraph.

    Args:
        instance_name: Optional Lakebase instance name override.

    Yields:
        CheckpointSaver for use with LangGraph.compile()

    Example:
        from agents.memory import get_checkpoint_saver

        with get_checkpoint_saver() as checkpointer:
            graph = workflow.compile(checkpointer=checkpointer)

            thread_id = request.custom_inputs.get("thread_id") or str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}

            result = graph.invoke({"messages": messages}, config)
    """
    memory = ShortTermMemory(instance_name)
    with memory.get_checkpointer() as checkpointer:
        yield checkpointer


# Singleton instance for common use
_short_term_memory: Optional[ShortTermMemory] = None


def get_short_term_memory() -> ShortTermMemory:
    """Get the singleton ShortTermMemory instance."""
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory
