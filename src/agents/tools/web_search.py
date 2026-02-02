"""
TRAINING MATERIAL: External Information Tool Pattern
=====================================================

This module implements a web search tool that allows the agent to access
external information beyond what's in the Genie Spaces (structured data).

WHY EXTERNAL SEARCH:
--------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  GENIE SPACES (Structured Data)      │  WEB SEARCH (External Info)      │
├──────────────────────────────────────┼──────────────────────────────────┤
│  ✅ Cost data, job metrics, audit    │  ✅ Databricks documentation     │
│  ✅ Real-time platform telemetry     │  ✅ Platform status/incidents    │
│  ✅ Historical trends, anomalies     │  ✅ Best practices, tutorials    │
│  ❌ "How to configure Photon?"       │  ✅ Community Q&A, solutions     │
│  ❌ "Is Databricks down right now?"  │  ✅ Feature announcements        │
└──────────────────────────────────────┴──────────────────────────────────┘

Web search complements Genie data for questions like:
- "Why is Photon not being used for my queries?"
- "Is there a known issue with Delta Lake today?"
- "What's the best practice for cluster autoscaling?"

TRUSTED DOMAINS:
----------------
Search is restricted to trusted sources only:
- docs.databricks.com - Official documentation
- status.databricks.com - Platform status/incidents
- community.databricks.com - Community discussions
- learn.microsoft.com - Azure Databricks docs

This prevents the agent from citing unreliable sources.

TAVILY INTEGRATION:
-------------------
We use Tavily API for web search because:
- Designed for AI/LLM applications
- Returns structured results (not HTML)
- Supports domain filtering
- Provides AI-generated summaries

API Pattern:
┌─────────────────────────────────────────────────────────────────────────┐
│  response = tavily_client.search(                                        │
│      query="Databricks Photon configuration",                           │
│      max_results=5,                                                     │
│      include_domains=["docs.databricks.com", ...]                       │
│  )                                                                      │
│  # Returns: {"answer": "...", "results": [{"title", "url", "content"}]} │
└─────────────────────────────────────────────────────────────────────────┘

GRACEFUL DEGRADATION:
---------------------
The tool handles missing configuration gracefully:
- No API key → Returns "Web search not configured"
- Search disabled → Returns "Web search is disabled"
- API error → Returns error message, doesn't crash

This ensures the agent can still function without web search.

Tool for searching Databricks documentation and status pages.
Uses Tavily for web search with domain restrictions.
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization
#
# typing: For type hints
# mlflow: For tracing tool invocations
# tool: LangChain decorator for creating tools

from typing import List, Optional
import mlflow

from langchain_core.tools import tool

from ..config import settings


# =============================================================================
# WEB SEARCH TOOL CLASS
# =============================================================================

class WebSearchTool:
    """
    Web search tool for external information.

    Searches trusted domains for:
    - Databricks documentation
    - Platform status updates
    - Best practices and guides

    Attributes:
        api_key: Tavily API key
        trusted_domains: List of allowed search domains
    """

    # Trusted domains for search results
    TRUSTED_DOMAINS = [
        "docs.databricks.com",
        "status.databricks.com",
        "community.databricks.com",
        "www.databricks.com",
        "learn.microsoft.com/azure/databricks",
    ]

    def __init__(self, api_key: str = None):
        """
        Initialize web search tool.

        Args:
            api_key: Tavily API key (or from settings)
        """
        self.api_key = api_key or settings.tavily_api_key
        self._client = None

    @property
    def client(self):
        """Lazily create Tavily client."""
        if self._client is None:
            if not self.api_key:
                return None
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                return None
        return self._client

    @mlflow.trace(name="web_search", span_type="TOOL")
    def search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: List[str] = None,
    ) -> dict:
        """
        Search for information on trusted domains.

        Args:
            query: Search query
            max_results: Maximum results to return
            include_domains: Optional domain filter

        Returns:
            Search results dict with 'results' and 'answer' keys.
        """
        with mlflow.start_span(name="tavily_search") as span:
            span.set_inputs({
                "query": query,
                "max_results": max_results,
            })

            # Check if search is enabled
            if not settings.enable_web_search:
                result = {
                    "results": [],
                    "answer": "Web search is disabled.",
                    "error": "DISABLED",
                }
                span.set_outputs(result)
                return result

            # Check if client is available
            if self.client is None:
                result = {
                    "results": [],
                    "answer": "Web search not configured (missing Tavily API key).",
                    "error": "NOT_CONFIGURED",
                }
                span.set_outputs(result)
                return result

            domains = include_domains or self.TRUSTED_DOMAINS

            try:
                response = self.client.search(
                    query=query,
                    max_results=max_results,
                    include_domains=domains,
                )

                result = {
                    "results": response.get("results", []),
                    "answer": response.get("answer", ""),
                }
                span.set_outputs({
                    "result_count": len(result["results"]),
                    "has_answer": bool(result["answer"]),
                })
                return result

            except Exception as e:
                result = {
                    "results": [],
                    "answer": f"Search error: {str(e)}",
                    "error": str(e),
                }
                span.set_outputs(result)
                return result


# Create singleton instance
_web_search: Optional[WebSearchTool] = None


def get_web_search_tool() -> WebSearchTool:
    """Get the singleton WebSearchTool instance."""
    global _web_search
    if _web_search is None:
        _web_search = WebSearchTool()
    return _web_search


# LangChain tool wrapper
@tool
def web_search_tool(query: str) -> str:
    """
    Search Databricks documentation and status pages.

    Use this tool to find:
    - Official documentation on Databricks features
    - Platform status and incident updates
    - Best practices and troubleshooting guides
    - Community answers and solutions

    Args:
        query: The search query

    Returns:
        Search results formatted as text.
    """
    searcher = get_web_search_tool()
    results = searcher.search(query)

    if results.get("error"):
        return results.get("answer", "Search failed")

    # Format results
    output = []

    if results.get("answer"):
        output.append(f"Summary: {results['answer']}\n")

    if results.get("results"):
        output.append("Sources:")
        for i, result in enumerate(results["results"][:5], 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            snippet = result.get("content", "")[:200]
            output.append(f"\n{i}. {title}")
            output.append(f"   URL: {url}")
            output.append(f"   {snippet}...")

    return "\n".join(output) if output else "No results found"
