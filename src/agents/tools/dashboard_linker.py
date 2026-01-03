"""
Dashboard Linker Tool
=====================

Tool for generating deep links to AI/BI dashboards.
"""

from typing import Dict, List, Optional
import mlflow

from langchain_core.tools import tool

from ..config import settings


class DashboardLinkerTool:
    """
    Dashboard linking tool for navigation.

    Generates deep links to relevant AI/BI dashboards
    based on query context and domain.

    Attributes:
        host: Databricks workspace host
        dashboards: Dashboard configuration registry
    """

    # Dashboard registry with IDs and metadata
    # TODO: Replace IDs with actual deployed dashboard IDs
    DASHBOARDS = {
        "cost": {
            "id": "COST_DASHBOARD_ID",  # Placeholder
            "name": "Cost Analysis Dashboard",
            "description": "DBU usage, spending trends, budget tracking",
            "tabs": ["Executive Overview", "Cost Management", "Commit Tracking"],
        },
        "security": {
            "id": "SECURITY_DASHBOARD_ID",  # Placeholder
            "name": "Security Audit Dashboard",
            "description": "User activity, access patterns, audit logs",
            "tabs": ["Security Audit", "Governance Hub"],
        },
        "performance": {
            "id": "PERFORMANCE_DASHBOARD_ID",  # Placeholder
            "name": "Performance Dashboard",
            "description": "Query latency, cluster utilization, optimization",
            "tabs": ["Query Performance", "Cluster Utilization"],
        },
        "reliability": {
            "id": "RELIABILITY_DASHBOARD_ID",  # Placeholder
            "name": "Job Reliability Dashboard",
            "description": "Job success rates, failures, SLA tracking",
            "tabs": ["Job Reliability", "Job Optimization"],
        },
        "quality": {
            "id": "QUALITY_DASHBOARD_ID",  # Placeholder
            "name": "Data Quality Dashboard",
            "description": "Data freshness, lineage, table health",
            "tabs": ["Table Health", "Governance Hub"],
        },
        "unified": {
            "id": "UNIFIED_DASHBOARD_ID",  # Placeholder
            "name": "Health Monitor Unified Dashboard",
            "description": "Platform-wide health overview across all domains",
            "tabs": [
                "Executive Overview", "Cost Management", "Commit Tracking",
                "Job Reliability", "Job Optimization", "Query Performance",
                "Cluster Utilization", "DBR Migration", "Security Audit",
                "Governance Hub", "Table Health",
            ],
        },
    }

    def __init__(self, host: str = None):
        """
        Initialize dashboard linker.

        Args:
            host: Databricks workspace host URL
        """
        self.host = (host or settings.databricks_host).rstrip("/")

    def get_dashboard_url(
        self,
        domain: str,
        tab: str = None,
        filters: Dict = None,
    ) -> str:
        """
        Generate dashboard URL for a domain.

        Args:
            domain: Domain name (cost, security, etc.)
            tab: Optional specific tab to open
            filters: Optional URL filters to apply

        Returns:
            Dashboard URL string.
        """
        domain_lower = domain.lower()
        dashboard = self.DASHBOARDS.get(domain_lower)

        if not dashboard:
            # Fall back to unified dashboard
            dashboard = self.DASHBOARDS["unified"]

        base_url = f"{self.host}/sql/dashboards/{dashboard['id']}"

        # Add tab parameter if specified
        if tab:
            base_url += f"?tab={tab.replace(' ', '+')}"

        # Add filters
        if filters:
            separator = "&" if "?" in base_url else "?"
            filter_params = "&".join([f"{k}={v}" for k, v in filters.items()])
            base_url += f"{separator}{filter_params}"

        return base_url

    @mlflow.trace(name="get_dashboard_link", span_type="TOOL")
    def get_dashboard_for_query(
        self,
        domains: List[str],
        query: str = None,
    ) -> Dict:
        """
        Get best dashboard for a query.

        Args:
            domains: List of relevant domains
            query: Optional query for context

        Returns:
            Dashboard info dict with name, url, and description.
        """
        with mlflow.start_span(name="resolve_dashboard") as span:
            span.set_inputs({
                "domains": domains,
                "query": query,
            })

            # Single domain - direct dashboard
            if len(domains) == 1:
                domain = domains[0].lower()
                if domain in self.DASHBOARDS:
                    dashboard = self.DASHBOARDS[domain]
                    result = {
                        "name": dashboard["name"],
                        "url": self.get_dashboard_url(domain),
                        "description": dashboard["description"],
                        "domain": domain,
                    }
                    span.set_outputs(result)
                    return result

            # Multi-domain - unified dashboard
            dashboard = self.DASHBOARDS["unified"]
            result = {
                "name": dashboard["name"],
                "url": self.get_dashboard_url("unified"),
                "description": dashboard["description"],
                "domain": "unified",
            }
            span.set_outputs(result)
            return result

    def list_dashboards(self) -> List[Dict]:
        """List all available dashboards."""
        return [
            {
                "domain": domain,
                "name": info["name"],
                "description": info["description"],
                "tabs": info["tabs"],
            }
            for domain, info in self.DASHBOARDS.items()
        ]


# Create singleton instance
_dashboard_linker: Optional[DashboardLinkerTool] = None


def get_dashboard_linker() -> DashboardLinkerTool:
    """Get the singleton DashboardLinkerTool instance."""
    global _dashboard_linker
    if _dashboard_linker is None:
        _dashboard_linker = DashboardLinkerTool()
    return _dashboard_linker


# LangChain tool wrapper
@tool
def dashboard_linker_tool(domains: str) -> str:
    """
    Get a link to the relevant AI/BI dashboard.

    Use this tool to provide users with direct links to
    dashboards for deeper exploration of their data.

    Args:
        domains: Comma-separated list of domains (e.g., "cost,reliability")

    Returns:
        Dashboard link with description.
    """
    linker = get_dashboard_linker()

    # Parse domains
    domain_list = [d.strip() for d in domains.split(",")]

    result = linker.get_dashboard_for_query(domain_list)

    return (
        f"**{result['name']}**\n"
        f"{result['description']}\n"
        f"[Open Dashboard]({result['url']})"
    )
