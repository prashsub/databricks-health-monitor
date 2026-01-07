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

# Import MLflow resources with graceful fallback for older versions
try:
    from mlflow.models.resources import (
        DatabricksServingEndpoint,
        DatabricksGenieSpace,
        DatabricksSQLWarehouse,
    )
    # DatabricksLakebase may not be available in all MLflow versions
    try:
        from mlflow.models.resources import DatabricksLakebase
        _HAS_LAKEBASE_RESOURCE = True
    except ImportError:
        DatabricksLakebase = None
        _HAS_LAKEBASE_RESOURCE = False
except ImportError:
    # Fallback for older MLflow versions without these resources
    DatabricksServingEndpoint = None
    DatabricksGenieSpace = None
    DatabricksSQLWarehouse = None
    DatabricksLakebase = None
    _HAS_LAKEBASE_RESOURCE = False

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

    @mlflow.trace(name="agent_predict_stream", span_type="AGENT")
    def predict_stream(
        self,
        messages: List[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream responses for real-time interaction.

        Yields ChatAgentResponse chunks as they become available,
        providing progressive feedback during long-running operations.

        The streaming flow:
        1. Yield "thinking" status while processing
        2. Yield intermediate results from worker agents
        3. Yield final synthesized response

        Args:
            messages: List of conversation messages
            context: Optional chat context with user/conversation info
            custom_inputs: Optional custom inputs (thread_id, etc.)

        Yields:
            ChatAgentResponse objects with progressive content.

        Example:
            for chunk in agent.predict_stream(messages):
                print(chunk.messages[-1].content)
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
            "streaming": "true",
        })

        # Yield initial thinking status
        yield ChatAgentResponse(
            messages=[
                ChatAgentMessage(
                    role="assistant",
                    content="🔍 Analyzing your query...",
                )
            ],
            custom_outputs={
                "thread_id": thread_id,
                "status": "thinking",
                "stage": "intent_classification",
            },
        )

        # Create initial state
        initial_state = create_initial_state(
            query=user_message,
            user_id=user_id,
            session_id=thread_id,
        )

        # Execute graph with streaming
        checkpoint_config = ShortTermMemory.get_checkpoint_config(thread_id)

        try:
            with get_checkpoint_saver() as checkpointer:
                graph = create_orchestrator_graph().compile(
                    checkpointer=checkpointer
                )

                # Stream graph execution
                domains_identified = False
                worker_responses_started = False

                for event in graph.stream(initial_state, checkpoint_config):
                    # Check if intent classification is complete
                    if "intent" in event and not domains_identified:
                        intent = event.get("intent", {})
                        domains = intent.get("domains", [])
                        confidence = intent.get("confidence", 0.0)

                        if domains:
                            domains_identified = True
                            domain_str = ", ".join(domains)

                            yield ChatAgentResponse(
                                messages=[
                                    ChatAgentMessage(
                                        role="assistant",
                                        content=f"📊 Identified domains: {domain_str}. Querying data sources...",
                                    )
                                ],
                                custom_outputs={
                                    "thread_id": thread_id,
                                    "status": "processing",
                                    "stage": "domain_routing",
                                    "domains": domains,
                                    "confidence": confidence,
                                },
                            )

                    # Check for worker agent responses
                    if "agent_responses" in event and not worker_responses_started:
                        responses = event.get("agent_responses", {})
                        if responses:
                            worker_responses_started = True
                            num_responses = len(responses)

                            yield ChatAgentResponse(
                                messages=[
                                    ChatAgentMessage(
                                        role="assistant",
                                        content=f"✅ Received {num_responses} domain response(s). Synthesizing answer...",
                                    )
                                ],
                                custom_outputs={
                                    "thread_id": thread_id,
                                    "status": "synthesizing",
                                    "stage": "response_synthesis",
                                    "domains_queried": list(responses.keys()),
                                },
                            )

                    # Check for final synthesized response
                    if "synthesized_response" in event:
                        response_content = event.get("synthesized_response", "")
                        if response_content:
                            # Get final state data
                            sources = event.get("sources", [])
                            confidence = event.get("confidence", 0.0)
                            final_intent = event.get("intent", {})

                            yield ChatAgentResponse(
                                messages=[
                                    ChatAgentMessage(
                                        role="assistant",
                                        content=response_content,
                                    )
                                ],
                                custom_outputs={
                                    "thread_id": thread_id,
                                    "status": "complete",
                                    "stage": "final",
                                    "sources": sources,
                                    "confidence": confidence,
                                    "domains": final_intent.get("domains", []),
                                },
                            )
                            return

                # If we didn't get a synthesized response from streaming,
                # fall back to final state
                final_state = graph.invoke(initial_state, checkpoint_config)

                response_content = final_state.get(
                    "synthesized_response",
                    "I was unable to process your request."
                )
                sources = final_state.get("sources", [])
                confidence = final_state.get("confidence", 0.0)

                yield ChatAgentResponse(
                    messages=[
                        ChatAgentMessage(
                            role="assistant",
                            content=response_content,
                        )
                    ],
                    custom_outputs={
                        "thread_id": thread_id,
                        "status": "complete",
                        "stage": "final",
                        "sources": sources,
                        "confidence": confidence,
                        "domains": final_state.get("intent", {}).get("domains", []),
                    },
                )

        except Exception as e:
            mlflow.log_metric("agent_stream_error", 1)
            yield ChatAgentResponse(
                messages=[
                    ChatAgentMessage(
                        role="assistant",
                        content=f"❌ I encountered an error: {str(e)}. Please try again.",
                    )
                ],
                custom_outputs={
                    "thread_id": thread_id,
                    "status": "error",
                    "error": str(e),
                },
            )


def get_mlflow_resources() -> List:
    """
    Get MLflow resource dependencies for model logging.

    These resources enable **automatic authentication passthrough**
    when the agent is deployed to Model Serving. Databricks will
    automatically manage short-lived credentials for all declared resources.

    Reference:
        https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#automatic-authentication-passthrough

    Resources declared:
        - DatabricksServingEndpoint: LLM endpoint for inference
        - DatabricksLakebase: Memory storage (short-term & long-term)
        - DatabricksGenieSpace: All 6 domain Genie Spaces
        - DatabricksSQLWarehouse: For any direct SQL operations

    Returns:
        List of Databricks resource dependencies.
    """
    resources = []
    
    # LLM Endpoint for agent inference
    if DatabricksServingEndpoint is not None:
        resources.append(DatabricksServingEndpoint(endpoint_name=settings.llm_endpoint))
    
    # Lakebase for memory persistence (may not be available in all MLflow versions)
    if _HAS_LAKEBASE_RESOURCE and DatabricksLakebase is not None:
        resources.append(DatabricksLakebase(database_instance_name=settings.lakebase_instance_name))
    
    # SQL Warehouse for direct queries (if needed)
    if DatabricksSQLWarehouse is not None:
        resources.append(DatabricksSQLWarehouse(warehouse_id=settings.warehouse_id))
    
    # Add all configured Genie Spaces
    if DatabricksGenieSpace is not None:
        genie_space_configs = [
            ("cost", settings.cost_genie_space_id),
            ("security", settings.security_genie_space_id),
            ("performance", settings.performance_genie_space_id),
            ("reliability", settings.reliability_genie_space_id),
            ("quality", settings.quality_genie_space_id),
            ("unified", settings.unified_genie_space_id),
        ]
        
        for domain, space_id in genie_space_configs:
            if space_id:  # Only add if configured
                resources.append(
                    DatabricksGenieSpace(genie_space_id=space_id)
                )
    
    return resources


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
        f"{settings.catalog}.{settings.agent_schema}.health_monitor_agent"
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
                "langchain-core>=0.3.0",
                "langgraph>=0.2.0",
                "databricks-sdk>=0.30.0",
                "databricks-agents>=0.16.0",  # Agent framework with GenieAgent support
            ],
        )

        return logged_model.model_uri


# Create singleton instance for convenience
AGENT = HealthMonitorAgent()
