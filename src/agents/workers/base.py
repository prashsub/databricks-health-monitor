"""
Base Worker Agent
=================

Abstract base class for domain worker agents.
All workers query Genie Spaces as their sole data interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import time
import mlflow

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import (
    GenieAPI,
    GenieStartConversationMessageRequest,
    GenieMessage,
)

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
    Worker agent that queries a Genie Space.

    This is the standard implementation for domain workers.
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
        self._client: Optional[WorkspaceClient] = None
        self._genie: Optional[GenieAPI] = None

    @property
    def client(self) -> WorkspaceClient:
        """Lazily create WorkspaceClient."""
        if self._client is None:
            self._client = WorkspaceClient()
        return self._client

    @property
    def genie(self) -> GenieAPI:
        """Lazily create GenieAPI."""
        if self._genie is None:
            self._genie = self.client.genie
        return self._genie

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

    @mlflow.trace(name="genie_query", span_type="TOOL")
    def query(self, question: str, context: Dict = None) -> Dict:
        """
        Query the Genie Space.

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

            # Enhance the query
            enhanced_query = self.enhance_query(question, context)

            try:
                # Start conversation with Genie
                response = self.genie.start_conversation(
                    space_id=genie_space_id,
                    content=enhanced_query,
                )

                # Wait for response completion
                result = self._wait_for_completion(
                    space_id=genie_space_id,
                    conversation_id=response.conversation_id,
                    message_id=response.message_id,
                )

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

    def _wait_for_completion(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str,
        timeout_seconds: int = None,
    ) -> Dict:
        """
        Wait for Genie response to complete.

        Args:
            space_id: Genie Space ID
            conversation_id: Conversation ID
            message_id: Message ID
            timeout_seconds: Max wait time

        Returns:
            Response dict.
        """
        timeout = timeout_seconds or settings.genie_timeout_seconds
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                return {
                    "response": f"Genie query timed out after {timeout}s",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": self.domain,
                    "error": "TIMEOUT",
                }

            try:
                # Get message status
                message = self.genie.get_message(
                    space_id=space_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                )

                # Check completion status
                if message.status == "COMPLETED":
                    return self._parse_genie_response(message)

                if message.status in ("FAILED", "CANCELLED"):
                    return {
                        "response": f"Genie query {message.status.lower()}",
                        "sources": [],
                        "confidence": 0.0,
                        "domain": self.domain,
                        "error": message.status,
                    }

                # Still processing - wait and retry
                time.sleep(1)

            except Exception as e:
                return {
                    "response": f"Error checking Genie status: {str(e)}",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": self.domain,
                    "error": str(e),
                }

    def _parse_genie_response(self, message: GenieMessage) -> Dict:
        """
        Parse Genie response into standard format.

        Args:
            message: Genie message object

        Returns:
            Parsed response dict.
        """
        # Extract content from Genie response
        content = ""
        sources = []

        if message.attachments:
            for attachment in message.attachments:
                if hasattr(attachment, "text") and attachment.text:
                    if hasattr(attachment.text, "content"):
                        content += attachment.text.content + "\n"

        # Extract query info as sources
        if message.query_result:
            sources.append(f"SQL Query: {message.query_result.statement_id}")

        return {
            "response": content.strip() or "No response from Genie",
            "sources": sources or [f"{self.domain.title()} Genie Space"],
            "confidence": 0.9 if content else 0.5,
            "domain": self.domain,
        }

    def follow_up(
        self,
        conversation_id: str,
        question: str,
        context: Dict = None,
    ) -> Dict:
        """
        Send a follow-up question in an existing conversation.

        Args:
            conversation_id: Existing conversation ID
            question: Follow-up question
            context: Optional user context

        Returns:
            Response dict.
        """
        genie_space_id = self.get_genie_space_id()

        if not genie_space_id:
            return {
                "response": f"Genie Space for {self.domain} is not configured.",
                "sources": [],
                "confidence": 0.0,
                "domain": self.domain,
                "error": "GENIE_SPACE_NOT_CONFIGURED",
            }

        try:
            response = self.genie.create_message(
                space_id=genie_space_id,
                conversation_id=conversation_id,
                content=question,
            )

            return self._wait_for_completion(
                space_id=genie_space_id,
                conversation_id=conversation_id,
                message_id=response.message_id,
            )

        except Exception as e:
            return {
                "response": f"Error in follow-up: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "domain": self.domain,
                "error": str(e),
            }
