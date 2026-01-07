"""
Base Worker Agent
=================

Abstract base class for domain worker agents.
All workers query Genie Spaces as their sole data interface.

Aligned with official Databricks LangGraph Multi-Agent Genie pattern:
https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie
https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/multi-agent-genie
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import mlflow

from ..config import settings


class BaseWorkerAgent(ABC):
    """
    Abstract base class for domain worker agents.

    All worker agents must implement:
    - enhance_query(): Add domain-specific context to the query
    - get_genie_space_id(): Return the Genie Space ID for this domain
    """

    def __init__(self, domain: str):
        """
        Initialize the worker agent.

        Args:
            domain: Domain name (cost, security, etc.)
        """
        self.domain = domain

    @abstractmethod
    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance the query with domain-specific context.

        Args:
            query: Original user query
            context: User context (preferences, role, etc.)

        Returns:
            Enhanced query string.
        """
        pass

    @abstractmethod
    def get_genie_space_id(self) -> str:
        """
        Get the Genie Space ID for this domain.

        Returns:
            Genie Space ID string.
        """
        pass

    @abstractmethod
    def query(self, question: str, context: Dict = None) -> Dict:
        """
        Query the domain for information.

        Args:
            question: User question
            context: Optional user context

        Returns:
            Response dict with keys: response, sources, confidence, domain
        """
        pass


class GenieWorkerAgent(BaseWorkerAgent):
    """
    Worker agent that queries a Genie Space using GenieAgent.

    This implementation follows the official Databricks LangGraph Multi-Agent
    Genie pattern using `databricks_langchain.genie.GenieAgent`.

    Reference:
    - https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie
    - https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/multi-agent-genie

    Each domain has its own Genie Space configured with relevant
    TVFs, Metric Views, and instructions.
    """

    def __init__(self, domain: str, genie_space_id: str = None):
        """
        Initialize the Genie worker agent.

        Args:
            domain: Domain name (cost, security, etc.)
            genie_space_id: Genie Space ID (or None to use settings)
        """
        super().__init__(domain)
        self._genie_space_id = genie_space_id
        self._genie_agent: Optional[Any] = None

    @property
    def genie_agent(self):
        """
        Lazily create GenieAgent.
        
        Uses databricks_langchain.genie.GenieAgent which is the official
        LangGraph-compatible wrapper for Genie Spaces.
        """
        if self._genie_agent is None:
            space_id = self.get_genie_space_id()
            if space_id:
                try:
                    from databricks_langchain.genie import GenieAgent
                    self._genie_agent = GenieAgent(
                        genie_space_id=space_id,
                        genie_agent_name=f"{self.domain}_genie",
                    )
                except ImportError as e:
                    mlflow.log_metric("genie_agent_import_error", 1)
                    print(f"Warning: Could not import GenieAgent: {e}")
                except Exception as e:
                    mlflow.log_metric("genie_agent_init_error", 1)
                    print(f"Warning: Could not initialize GenieAgent for {self.domain}: {e}")
        return self._genie_agent

    def get_genie_space_id(self) -> str:
        """Get the Genie Space ID for this domain."""
        if self._genie_space_id:
            return self._genie_space_id
        return settings.get_genie_space_id(self.domain) or ""

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with domain context.

        Override in subclasses for domain-specific enhancements.
        """
        enhanced = query

        # Add workspace filter if specified
        if context.get("preferences", {}).get("preferred_workspace"):
            workspace = context["preferences"]["preferred_workspace"]
            enhanced += f" Focus on workspace: {workspace}"

        return enhanced

    @mlflow.trace(name="genie_worker_query", span_type="TOOL")
    def query(self, question: str, context: Dict = None) -> Dict:
        """
        Query the Genie Space using GenieAgent.

        This method follows the official LangGraph Multi-Agent Genie pattern:
        - Uses GenieAgent.invoke() for LangGraph compatibility
        - Proper MLflow tracing on all operations
        - Standardized response format

        Args:
            question: User question
            context: Optional user context

        Returns:
            Response dict with: response, sources, confidence, domain
        """
        context = context or {}
        genie_space_id = self.get_genie_space_id()

        with mlflow.start_span(name=f"{self.domain}_genie_query") as span:
            span.set_inputs({
                "domain": self.domain,
                "question": question,
                "genie_space_id": genie_space_id,
            })

            # Check if Genie Space is configured
            if not genie_space_id:
                result = {
                    "response": f"Genie Space for {self.domain} is not configured.",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": self.domain,
                    "error": "GENIE_SPACE_NOT_CONFIGURED",
                }
                span.set_outputs(result)
                return result

            # Enhance the query with domain context
            enhanced_query = self.enhance_query(question, context)

            # Check if GenieAgent is available
            genie = self.genie_agent
            if genie is None:
                result = {
                    "response": f"GenieAgent for {self.domain} is not available.",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": self.domain,
                    "error": "GENIE_AGENT_NOT_AVAILABLE",
                }
                span.set_outputs(result)
                return result

            try:
                # Use GenieAgent.invoke() - the official LangGraph pattern
                genie_result = genie.invoke({"input": enhanced_query})

                # Parse GenieAgent response
                result = self._parse_genie_agent_response(genie_result)
                span.set_outputs(result)
                return result

            except Exception as e:
                result = {
                    "response": f"Error querying {self.domain} Genie: {str(e)}",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": self.domain,
                    "error": str(e),
                }
                span.set_outputs(result)
                return result

    def _parse_genie_agent_response(self, genie_result: Any) -> Dict:
        """
        Parse GenieAgent response into standard format.

        GenieAgent.invoke() returns a dict with 'output' key containing
        the natural language response.

        Args:
            genie_result: Result from GenieAgent.invoke()

        Returns:
            Parsed response dict.
        """
        # Extract output from GenieAgent result
        if isinstance(genie_result, dict):
            content = genie_result.get("output", "")
            if not content:
                # Try other possible keys
                content = genie_result.get("response", "")
                if not content:
                    content = str(genie_result)
        else:
            content = str(genie_result)

        return {
            "response": content.strip() if content else "No response from Genie",
            "sources": [f"{self.domain.title()} Genie Space"],
            "confidence": 0.9 if content else 0.5,
            "domain": self.domain,
        }

    @mlflow.trace(name="genie_worker_follow_up", span_type="TOOL")
    def follow_up(
        self,
        conversation_id: str,
        question: str,
        context: Dict = None,
    ) -> Dict:
        """
        Send a follow-up question using GenieAgent.

        Note: GenieAgent handles conversation state internally,
        so conversation_id is used for tracking purposes.

        Args:
            conversation_id: Conversation identifier for tracking
            question: Follow-up question
            context: Optional user context

        Returns:
            Response dict.
        """
        # GenieAgent manages conversation state internally
        # Just invoke with the follow-up question
        return self.query(question, context)
