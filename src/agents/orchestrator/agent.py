"""
Health Monitor Agent
====================

Main agent class implementing the ChatAgent interface for model serving.

Based on MLflow GenAI patterns and Databricks agent best practices.
"""

from typing import List, Optional, Dict, Any
import uuid
import mlflow

from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import (
    ChatAgentMessage,
    ChatAgentResponse,
    ChatContext,
)
from databricks.sdk import WorkspaceClient
from databricks_langchain import DatabricksServingEndpoint, DatabricksLakebase

from .graph import create_orchestrator_graph
from .state import create_initial_state
from ..memory import get_checkpoint_saver, ShortTermMemory
from ..config import settings


class HealthMonitorAgent(ChatAgent):
    """
    Databricks Health Monitor Multi-Agent System.

    Implements the MLflow ChatAgent interface for deployment
    to Databricks Model Serving.

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
    """

    def __init__(self):
        """Initialize the Health Monitor Agent."""
        self.workspace_client = WorkspaceClient()
        self._graph = None
        self._checkpointer = None

    @property
    def graph(self):
        """Lazily create the orchestrator graph."""
        if self._graph is None:
            workflow = create_orchestrator_graph()
            # Compile with checkpointer for state persistence
            with get_checkpoint_saver() as checkpointer:
                self._graph = workflow.compile(checkpointer=checkpointer)
        return self._graph

    def _resolve_thread_id(
        self,
        custom_inputs: Optional[Dict] = None,
        context: Optional[ChatContext] = None,
    ) -> str:
        """
        Resolve thread ID for conversation continuity.

        Priority:
            1. custom_inputs["thread_id"]
            2. context.conversation_id
            3. New UUID

        Args:
            custom_inputs: Custom inputs from request
            context: ChatContext from request

        Returns:
            Thread ID string.
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

        Args:
            custom_inputs: Custom inputs from request
            context: ChatContext from request

        Returns:
            User ID string.
        """
        if custom_inputs and custom_inputs.get("user_id"):
            return custom_inputs["user_id"]
        if context and context.user_id:
            return context.user_id
        return "unknown_user"

    @mlflow.trace(name="agent_predict", span_type="AGENT")
    def predict(
        self,
        messages: List[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> ChatAgentResponse:
        """
        Process a user query and return a response.

        This is the main entry point called by Model Serving.

        Args:
            messages: List of conversation messages
            context: Optional chat context with user/conversation info
            custom_inputs: Optional custom inputs (thread_id, etc.)

        Returns:
            ChatAgentResponse with assistant message and metadata.
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
            "query_length": str(len(user_message)),
        })

        # Create initial state
        initial_state = create_initial_state(
            query=user_message,
            user_id=user_id,
            session_id=thread_id,
        )

        # Execute graph with checkpoint config
        checkpoint_config = ShortTermMemory.get_checkpoint_config(thread_id)

        try:
            # Run the orchestrator graph
            with get_checkpoint_saver() as checkpointer:
                graph = create_orchestrator_graph().compile(
                    checkpointer=checkpointer
                )
                final_state = graph.invoke(initial_state, checkpoint_config)

            # Extract response
            response_content = final_state.get(
                "synthesized_response",
                "I was unable to process your request."
            )
            sources = final_state.get("sources", [])
            confidence = final_state.get("confidence", 0.0)

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

    def predict_stream(
        self,
        messages: List[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream responses for real-time interaction.

        Yields response chunks as they become available.
        """
        # For now, use non-streaming and yield complete response
        # TODO: Implement true streaming with LangGraph
        response = self.predict(messages, context, custom_inputs)
        yield response


def get_mlflow_resources() -> List:
    """
    Get MLflow resource dependencies for model logging.

    These resources enable automatic authentication passthrough
    when the agent is deployed to Model Serving.

    Returns:
        List of Databricks resource dependencies.
    """
    return [
        DatabricksServingEndpoint(settings.llm_endpoint),
        DatabricksLakebase(database_instance_name=settings.lakebase_instance_name),
    ]


def log_agent_to_mlflow(
    agent: HealthMonitorAgent,
    registered_model_name: str = None,
    version: str = "1.0.0",
) -> str:
    """
    Log the agent to MLflow Model Registry.

    Args:
        agent: HealthMonitorAgent instance
        registered_model_name: Name for Unity Catalog model
        version: Version string

    Returns:
        Model URI string.

    Example:
        agent = HealthMonitorAgent()
        model_uri = log_agent_to_mlflow(
            agent,
            registered_model_name="health_monitor.agents.orchestrator"
        )
    """
    model_name = registered_model_name or (
        f"{settings.catalog}.{settings.schema}.health_monitor_agent"
    )

    # Set model for logging (per MLflow GenAI patterns)
    mlflow.models.set_model(agent)

    # Create input example
    input_example = {
        "messages": [
            {"role": "user", "content": "Why did costs spike yesterday?"}
        ],
        "custom_inputs": {"user_id": "example@company.com"},
    }

    with mlflow.start_run(run_name=f"health_monitor_agent_{version}"):
        mlflow.log_params({
            "agent_type": "multi_agent_orchestrator",
            "version": version,
            "llm_endpoint": settings.llm_endpoint,
            "lakebase_instance": settings.lakebase_instance_name,
        })

        logged_model = mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=agent,
            input_example=input_example,
            resources=get_mlflow_resources(),
            registered_model_name=model_name,
            pip_requirements=[
                "mlflow>=3.0.0",
                "langchain>=0.3.0",
                "langgraph>=0.2.0",
                "langchain-databricks>=0.1.0",
                "databricks-sdk>=0.30.0",
                "databricks-langchain>=0.1.0",
            ],
        )

        return logged_model.model_uri


# Create singleton instance for convenience
AGENT = HealthMonitorAgent()
