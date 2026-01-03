"""
Genie Tool for LangGraph
========================

LangChain tool wrapper for Genie Space interactions.

Based on the official LangGraph multi-agent Genie pattern:
https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-multiagent-genie.html

The GenieTool allows agents to query structured data through
natural language, with Genie handling the SQL generation.
"""

from typing import Dict, List, Optional, Any
import time
import mlflow

from langchain_core.tools import tool, BaseTool
from pydantic import BaseModel, Field
from databricks.sdk import WorkspaceClient

from ..config import settings


class GenieQueryInput(BaseModel):
    """Input schema for Genie query tool."""

    query: str = Field(description="Natural language question to ask Genie")
    workspace_filter: Optional[str] = Field(
        default=None,
        description="Optional workspace to filter results"
    )


class GenieTool(BaseTool):
    """
    LangChain tool for querying Genie Spaces.

    This tool wraps a Genie Space and provides a clean interface
    for LangGraph agents to query structured data.

    Attributes:
        name: Tool name (e.g., "cost_genie")
        description: Tool description for agent routing
        genie_space_id: Genie Space identifier
        domain: Domain category (cost, security, etc.)
    """

    name: str
    description: str
    genie_space_id: str
    domain: str
    timeout_seconds: int = 45

    # Private attributes
    _client: Optional[WorkspaceClient] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def client(self) -> WorkspaceClient:
        """Lazily create WorkspaceClient."""
        if self._client is None:
            self._client = WorkspaceClient()
        return self._client

    def _run(self, query: str, workspace_filter: str = None) -> str:
        """
        Execute Genie query synchronously.

        Args:
            query: Natural language question
            workspace_filter: Optional workspace filter

        Returns:
            Genie response as string.
        """
        return self._query_genie(query, workspace_filter)

    async def _arun(self, query: str, workspace_filter: str = None) -> str:
        """
        Execute Genie query asynchronously.

        For now, delegates to sync implementation.
        TODO: Implement true async with aiohttp.
        """
        return self._run(query, workspace_filter)

    @mlflow.trace(name="genie_tool_query", span_type="TOOL")
    def _query_genie(self, query: str, workspace_filter: str = None) -> str:
        """
        Query the Genie Space.

        Args:
            query: Natural language question
            workspace_filter: Optional workspace filter

        Returns:
            Formatted response string.
        """
        with mlflow.start_span(name=f"genie_{self.domain}") as span:
            span.set_inputs({
                "query": query,
                "domain": self.domain,
                "genie_space_id": self.genie_space_id,
            })

            # Check if Genie Space is configured
            if not self.genie_space_id:
                result = f"Error: Genie Space for {self.domain} is not configured."
                span.set_outputs({"error": "NOT_CONFIGURED"})
                return result

            # Enhance query with workspace filter
            enhanced_query = query
            if workspace_filter:
                enhanced_query += f" Filter by workspace: {workspace_filter}"

            try:
                # Start Genie conversation
                response = self.client.genie.start_conversation(
                    space_id=self.genie_space_id,
                    content=enhanced_query,
                )

                # Wait for completion and parse response
                result = self._wait_and_parse(
                    conversation_id=response.conversation_id,
                    message_id=response.message_id,
                )

                span.set_outputs({
                    "response_length": len(result),
                    "conversation_id": response.conversation_id,
                })

                return result

            except Exception as e:
                error_msg = f"Error querying {self.domain} Genie: {str(e)}"
                span.set_outputs({"error": str(e)})
                return error_msg

    def _wait_and_parse(
        self,
        conversation_id: str,
        message_id: str,
    ) -> str:
        """
        Wait for Genie response and parse it.

        Args:
            conversation_id: Genie conversation ID
            message_id: Message ID to poll

        Returns:
            Parsed response string.
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                return f"Genie query timed out after {self.timeout_seconds}s"

            try:
                message = self.client.genie.get_message(
                    space_id=self.genie_space_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                )

                # Check status
                status = getattr(message, "status", None)

                if status == "COMPLETED":
                    return self._format_response(message)

                if status in ("FAILED", "CANCELLED", "ERROR"):
                    return f"Genie query {status.lower()}"

                # Still processing
                time.sleep(1)

            except Exception as e:
                return f"Error checking Genie status: {str(e)}"

    def _format_response(self, message: Any) -> str:
        """
        Format Genie response for return.

        Args:
            message: Genie message object

        Returns:
            Formatted response string.
        """
        content_parts = []

        # Extract text attachments
        if hasattr(message, "attachments") and message.attachments:
            for attachment in message.attachments:
                if hasattr(attachment, "text"):
                    text = attachment.text
                    if hasattr(text, "content"):
                        content_parts.append(text.content)

        # Extract query result info
        if hasattr(message, "query_result") and message.query_result:
            result = message.query_result
            if hasattr(result, "description"):
                content_parts.append(f"\nQuery: {result.description}")

        if content_parts:
            return "\n".join(content_parts)

        return "Genie returned no content"


def create_genie_tools() -> List[GenieTool]:
    """
    Create Genie tools for all domains.

    Returns:
        List of GenieTool instances for each domain.
    """
    tools = []

    # Domain configurations
    domains = {
        "cost": {
            "name": "cost_genie",
            "description": (
                "Query cost and billing data. Use for questions about: "
                "spending, DBU usage, budgets, cost allocation, pricing, "
                "chargeback, most expensive jobs, cost trends, SKU analysis."
            ),
            "genie_space_id": settings.cost_genie_space_id,
        },
        "security": {
            "name": "security_genie",
            "description": (
                "Query security and audit data. Use for questions about: "
                "access control, permissions, audit logs, who accessed what, "
                "failed logins, compliance, threats, sensitive data access."
            ),
            "genie_space_id": settings.security_genie_space_id,
        },
        "performance": {
            "name": "performance_genie",
            "description": (
                "Query performance data. Use for questions about: "
                "slow queries, cluster utilization, warehouse efficiency, "
                "latency, cache hit rates, query optimization, resource sizing."
            ),
            "genie_space_id": settings.performance_genie_space_id,
        },
        "reliability": {
            "name": "reliability_genie",
            "description": (
                "Query reliability data. Use for questions about: "
                "job failures, SLA compliance, pipeline health, task success, "
                "incidents, job duration, failing jobs, success rates."
            ),
            "genie_space_id": settings.reliability_genie_space_id,
        },
        "quality": {
            "name": "quality_genie",
            "description": (
                "Query data quality data. Use for questions about: "
                "data freshness, schema changes, data lineage, null rates, "
                "table health, governance, data classification."
            ),
            "genie_space_id": settings.quality_genie_space_id,
        },
        "unified": {
            "name": "unified_genie",
            "description": (
                "Query cross-domain data. Use for complex questions spanning "
                "multiple domains, correlation analysis, or when you need "
                "a holistic view of platform health."
            ),
            "genie_space_id": settings.unified_genie_space_id,
        },
    }

    for domain, config in domains.items():
        # Only create tool if Genie Space ID is configured
        if config["genie_space_id"]:
            tools.append(GenieTool(
                name=config["name"],
                description=config["description"],
                genie_space_id=config["genie_space_id"],
                domain=domain,
            ))

    return tools


# Create tools lazily
_genie_tools: Optional[List[GenieTool]] = None


def get_genie_tools() -> List[GenieTool]:
    """Get all configured Genie tools."""
    global _genie_tools
    if _genie_tools is None:
        _genie_tools = create_genie_tools()
    return _genie_tools
