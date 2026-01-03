"""
Agent Tools Module
==================

Tools available to the Health Monitor agent system.

Tool Types:
1. GENIE SPACE TOOLS (6) - All data queries flow through these
   - cost_genie, security_genie, performance_genie
   - reliability_genie, quality_genie, unified_genie

2. UTILITY TOOLS (4) - Actions and external data
   - web_search: Databricks status, docs, real-time info
   - dashboard_linker: Deep links to AI/BI dashboards
   - alert_trigger: Trigger SQL alerts (future)
   - runbook_rag: Vector search over remediation docs (future)
"""

from .genie_tool import GenieTool, create_genie_tools
from .web_search import WebSearchTool, web_search_tool
from .dashboard_linker import DashboardLinkerTool, dashboard_linker_tool

__all__ = [
    "GenieTool",
    "create_genie_tools",
    "WebSearchTool",
    "web_search_tool",
    "DashboardLinkerTool",
    "dashboard_linker_tool",
]
