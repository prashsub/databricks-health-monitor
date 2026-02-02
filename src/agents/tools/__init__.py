"""
TRAINING MATERIAL: Agent Tools Module Architecture
===================================================

Tools are the "hands" of an AI agent - they allow the agent to interact
with external systems, query data, and take actions. This module provides
all tools available to the Health Monitor agent system.

TOOL ARCHITECTURE:
------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    HEALTH MONITOR TOOL HIERARCHY                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  GENIE SPACE TOOLS (6) - Primary data access                    │   │
│  │  ─────────────────────────────────────────────────────────────  │   │
│  │  • cost_genie        - Billing, DBU usage, spend analysis       │   │
│  │  • security_genie    - Audit logs, access patterns, compliance  │   │
│  │  • performance_genie - Query latency, cluster utilization       │   │
│  │  • reliability_genie - Job failures, SLA compliance             │   │
│  │  • quality_genie     - Data freshness, schema drift             │   │
│  │  • unified_genie     - Cross-domain queries                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  UTILITY TOOLS - External data and actions                      │   │
│  │  ─────────────────────────────────────────────────────────────  │   │
│  │  • web_search        - Databricks docs, status, best practices  │   │
│  │  • dashboard_linker  - Deep links to AI/BI dashboards           │   │
│  │  • alert_trigger     - Trigger SQL alerts (future)              │   │
│  │  • runbook_rag       - Vector search over runbooks (future)     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

HOW TOOLS WORK WITH AGENTS:
---------------------------

1. Agent receives user query: "What's causing our high costs?"

2. LLM decides which tool(s) to use based on tool DESCRIPTIONS:
   - "Query cost and billing data..." → cost_genie selected!
   
3. Agent invokes tool with parameters:
   cost_genie.invoke({"query": "high cost analysis"})
   
4. Tool returns results to agent

5. Agent synthesizes response for user

TOOL DESCRIPTION MATTERS:
-------------------------
The tool DESCRIPTION is critical for agent routing:

GOOD: "Query cost and billing data. Use for questions about: 
       spending, DBU usage, budgets, cost allocation, pricing."
       
BAD:  "A tool for cost stuff."

More specific = better routing decisions by the LLM.

WHY MULTIPLE GENIE TOOLS:
-------------------------
Each domain has its own Genie Space with optimized:
- Table-Valued Functions (TVFs)
- Metric Views
- Sample questions
- Instructions

Separate tools allow precise routing:
- "Show failed jobs" → reliability_genie (not cost_genie!)
- "Security audit" → security_genie (not unified_genie!)

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

# =============================================================================
# EXPORTS
# =============================================================================
# TRAINING MATERIAL: Module Export Pattern
#
# This __init__.py file makes tools available via simple imports:
#   from agents.tools import create_genie_tools
#
# Rather than deep imports:
#   from agents.tools.genie_tool import create_genie_tools

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
