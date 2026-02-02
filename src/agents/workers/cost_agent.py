"""
Cost Worker Agent
=================

TRAINING MATERIAL: Domain-Specific Worker Agent Pattern
---------------------------------------------------------

This module demonstrates how to create a specialized domain worker
in a multi-agent system. Each domain worker:
1. Inherits from a base worker class (GenieWorkerAgent)
2. Connects to a domain-specific Genie Space
3. Enhances queries with domain knowledge
4. Provides example queries for testing

ARCHITECTURE CONTEXT:
---------------------
This agent is ONE of 5 domain specialists in the Health Monitor:

┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                           │
│                            ↓                                     │
│         Intent Classification → Route to Workers                 │
│                            ↓                                     │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐           │
│  │  COST   │SECURITY │  PERF   │RELIAB.  │QUALITY  │           │
│  │ Worker  │ Worker  │ Worker  │ Worker  │ Worker  │           │
│  │  ↓      │  ↓      │  ↓      │  ↓      │  ↓      │           │
│  │ Cost    │Security │Perform. │Reliab.  │Quality  │           │
│  │ Genie   │ Genie   │ Genie   │ Genie   │ Genie   │           │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘           │
└─────────────────────────────────────────────────────────────────┘

WHY SEPARATE WORKERS:
---------------------
1. SEPARATION OF CONCERNS: Each worker handles one domain
2. PARALLEL EXECUTION: Workers can run simultaneously
3. SPECIALIZED KNOWLEDGE: Each worker knows its domain deeply
4. EASIER TESTING: Test each domain independently
5. MAINTAINABILITY: Changes in one domain don't affect others

GENIE SPACE INTEGRATION:
------------------------
Each worker queries a dedicated Genie Space containing:
- Domain-specific tables (e.g., fact_usage, dim_sku for cost)
- Table-Valued Functions (TVFs) optimized for common questions
- Metric Views for aggregated analytics
- Sample questions for LLM guidance

ALTERNATIVES CONSIDERED:
------------------------
1. Single agent with all domains (rejected: too complex, slow)
2. Direct SQL queries (rejected: loses Genie's NL understanding)
3. Per-query agent creation (rejected: too slow, no context)
4. Hardcoded responses (rejected: no real data, hallucination risk)

BEST PRACTICES DEMONSTRATED:
----------------------------
- Inheritance for code reuse (GenieWorkerAgent base class)
- Configuration from settings (not hardcoded)
- Query enhancement for personalization
- Example queries for testing and documentation
- Type hints for maintainability

Domain specialist for cost analysis, billing, and FinOps queries.
"""

# =============================================================================
# IMPORTS
# =============================================================================
# PATTERN: Minimal imports, relative imports for local modules

from typing import Dict

# Base class provides common Genie integration logic
# WHY INHERITANCE: All domain workers share the same Genie query pattern
from .base import GenieWorkerAgent

# Centralized configuration
# WHY: Avoid hardcoding Genie Space IDs, endpoints, etc.
from ..config import settings


# =============================================================================
# COST WORKER AGENT CLASS
# =============================================================================

class CostWorkerAgent(GenieWorkerAgent):
    """
    Cost domain worker agent.
    
    TRAINING MATERIAL: Implementing a Domain Worker
    ================================================
    
    This class demonstrates the pattern for creating domain-specific
    workers in a multi-agent system.
    
    INHERITANCE HIERARCHY:
    ----------------------
    GenieWorkerAgent (base class)
        ↓
    CostWorkerAgent (this class)
    
    WHAT THE BASE CLASS PROVIDES:
    -----------------------------
    - Genie Space connection management
    - Query execution with error handling
    - Response formatting
    - MLflow tracing integration
    
    WHAT THIS CLASS ADDS:
    ---------------------
    - Domain-specific configuration (Genie Space ID)
    - Query enhancement with cost-specific context
    - Example queries for this domain
    
    DOMAIN KNOWLEDGE:
    -----------------
    The Cost domain encompasses:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    Cost Domain                               │
    ├─────────────────────────────────────────────────────────────┤
    │  BILLING                                                     │
    │  ├── DBU consumption tracking                               │
    │  ├── SKU-level cost analysis                                │
    │  └── List price vs. committed pricing                       │
    │                                                              │
    │  BUDGET MANAGEMENT                                           │
    │  ├── Budget tracking and alerts                             │
    │  ├── Forecast vs. actual comparisons                        │
    │  └── Overspend detection                                    │
    │                                                              │
    │  ALLOCATION                                                  │
    │  ├── Chargeback by team/project                             │
    │  ├── Tag-based cost attribution                             │
    │  └── Untagged resource identification                       │
    │                                                              │
    │  OPTIMIZATION                                                │
    │  ├── Cost anomaly detection (ML)                            │
    │  ├── Commitment recommendations                             │
    │  └── Waste identification                                   │
    └─────────────────────────────────────────────────────────────┘
    
    GENIE SPACE ASSETS:
    -------------------
    The Cost Intelligence Genie Space includes:
    
    Gold Tables:
    - fact_usage: Detailed usage records
    - fact_list_prices: SKU pricing history
    - dim_sku: SKU dimension
    - dim_workspace: Workspace dimension
    
    Table-Valued Functions (TVFs):
    - get_cost_summary(start_date, end_date)
    - get_top_cost_drivers(n, period)
    - get_budget_status(budget_id)
    - get_untagged_costs(min_cost)
    - ... 15 total
    
    Metric Views:
    - cost_analytics: Aggregated cost KPIs
    - commit_tracking: Commitment utilization
    
    ML Models:
    - cost_anomaly_detector: Flags unusual spend
    - budget_forecaster: Predicts future costs

    Handles queries related to:
    - Billing and spending analysis
    - DBU usage and allocation
    - Budget tracking and forecasting
    - Cost anomaly detection
    - Chargeback and showback
    - SKU analysis

    Genie Space: Cost Intelligence
    TVFs: 15 cost-related functions
    Metric Views: cost_analytics, commit_tracking
    ML Models: Cost anomaly, forecast, budget alerts
    """

    # =========================================================================
    # CLASS ATTRIBUTES
    # =========================================================================
    # WHY CLASS ATTRIBUTE: Shared across all instances, easy to override in tests
    # TODO: This placeholder is for documentation; actual ID comes from settings
    GENIE_SPACE_ID_PLACEHOLDER = "COST_GENIE_SPACE_ID"

    def __init__(self, genie_space_id: str = None):
        """
        Initialize Cost Worker Agent.
        
        TRAINING MATERIAL: Worker Initialization Pattern
        ==================================================
        
        INITIALIZATION FLOW:
        1. Accept optional genie_space_id (for testing overrides)
        2. Fall back to settings.cost_genie_space_id (production)
        3. Call base class __init__ with domain and space_id
        
        WHY OPTIONAL PARAMETER:
        -----------------------
        - Testing: Can inject mock Genie Space ID
        - Local dev: Can use different spaces
        - Production: Uses settings (default)
        
        WHAT BASE CLASS DOES:
        ---------------------
        super().__init__ will:
        - Store domain name ("cost")
        - Store Genie Space ID
        - Initialize Genie client (lazy, on first query)
        - Set up tracing context
        
        Args:
            genie_space_id: Optional override for Genie Space ID.
                           If None, uses settings.cost_genie_space_id
        """
        super().__init__(
            domain="cost",
            genie_space_id=genie_space_id or settings.cost_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance query with cost-specific context.
        
        TRAINING MATERIAL: Query Enhancement Pattern
        ==============================================
        
        WHY ENHANCE QUERIES:
        --------------------
        Raw user queries may lack context that Genie needs:
        - User: "Why are costs high?"
        - Enhanced: "Why are costs high? Focus on workspace: prod-analytics.
                    Flag any costs exceeding $1000. Provide executive summary."
        
        The enhancement adds:
        1. User preferences (thresholds, workspaces)
        2. Role-based formatting (executive vs. analyst)
        3. Default filters (time ranges, cost floors)
        
        ENHANCEMENT SOURCES:
        --------------------
        
        ┌─────────────────────────────────────────────────────────────┐
        │                    Context Object                           │
        │                                                              │
        │  preferences:                                                │
        │  ├── cost_threshold: $1000 (flag expensive items)          │
        │  ├── preferred_workspace: "prod-analytics"                 │
        │  └── time_range: "last_7_days"                             │
        │                                                              │
        │  user_role: "manager" | "analyst" | "engineer"             │
        │  └── Affects response format and detail level              │
        └─────────────────────────────────────────────────────────────┘
        
        ENHANCEMENT RULES:
        ------------------
        1. Never modify the core intent of the query
        2. Add context that helps, not constrains
        3. Use natural language (Genie understands it)
        4. Be specific but not overly restrictive
        
        ROLE-BASED FORMATTING:
        ----------------------
        Manager: "Provide executive summary with key metrics"
          → High-level numbers, trends, recommendations
        
        Analyst: "Include detailed breakdowns and trends"
          → Granular data, drill-downs, statistical analysis
        
        Engineer: (default) Technical details, job names, configs
        
        ALTERNATIVE APPROACHES:
        -----------------------
        1. Prompt injection (rejected: harder to test, debug)
        2. Separate system prompt (rejected: Genie doesn't use system prompts)
        3. Post-processing (rejected: better to get right data first)
        
        Args:
            query: Original user query string
            context: Dict with preferences, user_role, etc.
            
        Returns:
            Enhanced query string with added context
        """
        enhanced = query
        prefs = context.get("preferences", {})

        # =====================================================================
        # Enhancement 1: Cost threshold for flagging expensive items
        # =====================================================================
        # WHY: Users often have implicit thresholds for "expensive"
        # Explicit threshold helps Genie focus on relevant data
        if prefs.get("cost_threshold"):
            threshold = prefs["cost_threshold"]
            enhanced += f" Flag any costs exceeding ${threshold}."

        # =====================================================================
        # Enhancement 2: Workspace filter for focused analysis
        # =====================================================================
        # WHY: Large enterprises have many workspaces
        # Users typically care about specific workspaces
        if prefs.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {prefs['preferred_workspace']}."

        # =====================================================================
        # Enhancement 3: Role-based response formatting
        # =====================================================================
        # WHY: Different roles need different levels of detail
        # Managers want summaries; analysts want details
        role = context.get("user_role")
        if role == "manager":
            enhanced += " Provide executive summary with key metrics."
        elif role == "analyst":
            enhanced += " Include detailed breakdowns and trends."
        # Engineers (default) get technical details without special formatting

        return enhanced

    def get_example_queries(self) -> list[str]:
        """
        Return example queries this agent handles.
        
        TRAINING MATERIAL: Example Queries Pattern
        ============================================
        
        PURPOSE OF EXAMPLE QUERIES:
        ---------------------------
        1. TESTING: Verify agent works with representative queries
        2. DOCUMENTATION: Show what this worker can do
        3. GENIE TRAINING: Can be added to Genie Space sample questions
        4. INTENT CLASSIFICATION: Help orchestrator route correctly
        
        QUERY DESIGN PRINCIPLES:
        ------------------------
        1. Cover all major use cases in the domain
        2. Vary complexity (simple to multi-part)
        3. Use natural language (how users actually ask)
        4. Include time references (yesterday, last month)
        5. Include entity references (jobs, teams, workspaces)
        
        MAPPING TO CAPABILITIES:
        ------------------------
        
        Query                              Capability
        ─────────────────────────────────  ─────────────────────────
        "Why did costs spike yesterday?"   → Anomaly detection
        "Top 10 most expensive jobs?"      → Cost ranking
        "DBU usage by workspace"           → Allocation analysis
        "Which teams are over budget?"     → Budget tracking
        "Forecast next month's spending"   → Forecasting (ML)
        "What SKUs are driving costs?"     → SKU analysis
        "Show untagged resource costs"     → Governance/tagging
        
        TESTING WITH EXAMPLES:
        ----------------------
        # In a notebook:
        agent = CostWorkerAgent()
        for query in agent.get_example_queries():
            print(f"Query: {query}")
            response = agent.process(query, {})
            print(f"Response: {response[:200]}...")
        
        Returns:
            List of example query strings for this domain.
        """
        return [
            # Anomaly detection query
            "Why did costs spike yesterday?",
            
            # Ranking/top-N query
            "What are the top 10 most expensive jobs?",
            
            # Aggregation with time filter
            "Show DBU usage by workspace for last month",
            
            # Budget tracking
            "Which teams are over budget?",
            
            # Forecasting (uses ML model)
            "Forecast next month's spending",
            
            # SKU analysis
            "What SKUs are driving cost increases?",
            
            # Governance/tagging analysis
            "Show untagged resource costs",
        ]
