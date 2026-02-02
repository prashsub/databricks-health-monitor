"""
Base Worker Agent
=================

TRAINING MATERIAL: Abstract Base Classes and Domain Worker Pattern
-------------------------------------------------------------------

This module defines the foundation for all domain worker agents in
the multi-agent system. It demonstrates key software engineering
patterns for building extensible, maintainable agent architectures.

DESIGN PATTERN: Template Method Pattern
---------------------------------------
The base class defines the overall algorithm structure (query flow),
while subclasses provide domain-specific implementations.

┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKER AGENT HIERARCHY                                │
│                                                                         │
│                      BaseWorkerAgent (ABC)                              │
│                        │ Abstract base                                  │
│                        │ Defines interface                              │
│                        ↓                                                │
│                    GenieWorkerAgent                                     │
│                        │ Concrete base                                  │
│                        │ Genie integration                              │
│                        ↓                                                │
│    ┌─────────┬─────────┬─────────┬─────────┬─────────┐                │
│    │  Cost   │Security │  Perf   │Reliab.  │Quality  │                │
│    │ Worker  │ Worker  │ Worker  │ Worker  │ Worker  │                │
│    │ Domain  │ Domain  │ Domain  │ Domain  │ Domain  │                │
│    └─────────┴─────────┴─────────┴─────────┴─────────┘                │
└─────────────────────────────────────────────────────────────────────────┘

WHY THIS PATTERN:
1. INTERFACE GUARANTEE: All workers have same methods
2. CODE REUSE: Common logic in GenieWorkerAgent
3. DOMAIN SPECIFICITY: Each worker knows its domain
4. TESTABILITY: Can test base class and domains separately
5. EXTENSIBILITY: Add new domains by creating subclasses

GENIE SPACE INTEGRATION:
------------------------
All workers query Genie Spaces as their sole data interface.
This ensures:
- Data grounding (real data, not hallucinations)
- Consistent data governance
- Natural language understanding
- SQL query generation by Genie

ALTERNATIVES CONSIDERED:
------------------------
1. Direct SQL queries (rejected: loses NL understanding)
2. Single worker (rejected: doesn't scale to 5 domains)
3. LLM-only (rejected: no data grounding, hallucination risk)
4. REST API per domain (rejected: no unified NL interface)

Abstract base class for domain worker agents.
All workers query Genie Spaces as their sole data interface.

Aligned with official Databricks LangGraph Multi-Agent Genie pattern:
https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie
https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/multi-agent-genie
"""

# =============================================================================
# IMPORTS
# =============================================================================
# TRAINING MATERIAL: Import Organization
#
# PATTERN: Standard library → Third-party → Local
# WHY ABC: Python's Abstract Base Class for interface definition

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import mlflow

from ..config import settings


# =============================================================================
# ABSTRACT BASE CLASS
# =============================================================================

class BaseWorkerAgent(ABC):
    """
    Abstract base class for domain worker agents.
    
    TRAINING MATERIAL: Python Abstract Base Classes (ABC)
    =====================================================
    
    WHAT IS ABC:
    Python's ABC module provides a way to define interfaces.
    Classes inheriting from ABC with @abstractmethod decorators
    CANNOT be instantiated until all abstract methods are implemented.
    
    WHY USE ABC:
    1. ENFORCEMENT: Python will raise error if abstract methods not implemented
    2. DOCUMENTATION: Clearly defines the interface contract
    3. TYPE SAFETY: IDE can catch missing implementations
    4. DESIGN: Forces consistent API across all domain workers
    
    INTERFACE CONTRACT:
    -------------------
    All worker agents MUST implement:
    - enhance_query(): Add domain-specific context to the query
    - get_genie_space_id(): Return the Genie Space ID for this domain
    - query(): Execute the query and return results
    
    WHY THESE METHODS:
    - enhance_query(): Enables domain-specific personalization
    - get_genie_space_id(): Each domain has its own Genie Space
    - query(): Core functionality - ask domain for information
    
    ALTERNATIVE: Protocol (Python 3.8+)
    -----------------------------------
    Could use typing.Protocol for structural subtyping:
    
    class WorkerProtocol(Protocol):
        def query(self, question: str) -> Dict: ...
    
    ABC chosen because:
    - Explicit inheritance makes relationship clear
    - Can include common implementation in base class
    - Better IDE support for abstract method detection

    All worker agents must implement:
    - enhance_query(): Add domain-specific context to the query
    - get_genie_space_id(): Return the Genie Space ID for this domain
    """

    def __init__(self, domain: str):
        """
        Initialize the worker agent.
        
        TRAINING MATERIAL: Base Class Initialization
        =============================================
        
        PATTERN: Store domain identifier for later use.
        
        WHY DOMAIN AS STRING:
        - Simple, serializable identifier
        - Used for logging, tracing, error messages
        - Maps to configuration (Genie Space IDs)
        
        SUBCLASS PATTERN:
        Subclasses should call super().__init__(domain) first,
        then add domain-specific initialization.
        
        Example:
            class CostWorkerAgent(GenieWorkerAgent):
                def __init__(self):
                    super().__init__(domain="cost")
                    # Domain-specific setup here

        Args:
            domain: Domain name (cost, security, etc.)
        """
        self.domain = domain

    @abstractmethod
    def enhance_query(self, query: str, context: Dict) -> str:
        """
        Enhance the query with domain-specific context.
        
        TRAINING MATERIAL: Query Enhancement Pattern
        =============================================
        
        PURPOSE:
        Inject domain knowledge into the user's query to help
        Genie provide more relevant responses.
        
        ENHANCEMENT EXAMPLES:
        - Add workspace filter based on user preference
        - Add cost threshold for flagging expensive items
        - Add role-based formatting instructions
        
        Input:  "Why are costs high?"
        Output: "Why are costs high? Focus on workspace: prod-analytics.
                 Flag costs > $1000. Provide executive summary."
        
        WHY @abstractmethod:
        Each domain has different enhancement logic.
        Cost adds thresholds, Security adds severity context, etc.

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
        
        TRAINING MATERIAL: Genie Space Configuration
        =============================================
        
        Each domain has a dedicated Genie Space containing:
        - Domain-specific Gold tables
        - Optimized Table-Valued Functions (TVFs)
        - Metric Views for aggregations
        - Sample questions for guidance
        - Domain-specific instructions
        
        CONFIGURATION SOURCE:
        Typically from settings (not hardcoded):
        
        def get_genie_space_id(self) -> str:
            return settings.cost_genie_space_id
        
        WHY DEDICATED SPACES:
        - Focused context (no cross-domain confusion)
        - Optimized prompts for domain
        - Separate governance
        - Independent optimization

        Returns:
            Genie Space ID string.
        """
        pass

    @abstractmethod
    def query(self, question: str, context: Dict = None) -> Dict:
        """
        Query the domain for information.
        
        TRAINING MATERIAL: Query Response Format
        ========================================
        
        STANDARDIZED RESPONSE:
        All workers return the same structure:
        {
            "response": str,    # Natural language answer
            "sources": list,    # Data sources used
            "confidence": float, # 0.0-1.0 confidence score
            "domain": str,      # Domain identifier
            "error": str,       # Optional error info
        }
        
        WHY STANDARDIZED:
        - Synthesizer can process any domain response
        - Easy to aggregate multi-domain results
        - Consistent error handling
        - Comparable confidence scores
        
        ERROR HANDLING:
        Never raise exceptions - return error response instead.
        This ensures other domains can still respond.

        Args:
            question: User question
            context: Optional user context

        Returns:
            Response dict with keys: response, sources, confidence, domain
        """
        pass


# =============================================================================
# CONCRETE BASE CLASS: GenieWorkerAgent
# =============================================================================

class GenieWorkerAgent(BaseWorkerAgent):
    """
    Worker agent that queries a Genie Space using GenieAgent.
    
    TRAINING MATERIAL: Genie Integration Pattern
    =============================================
    
    This is the CONCRETE base class that all domain workers inherit from.
    It implements the Genie Space query logic that's common across all domains.
    
    INHERITANCE HIERARCHY:
    ----------------------
    BaseWorkerAgent (ABC)     → Defines interface
        ↓
    GenieWorkerAgent          → Implements Genie integration (THIS CLASS)
        ↓
    CostWorkerAgent, etc.     → Add domain-specific enhancements
    
    WHAT IS GenieAgent:
    -------------------
    `databricks_langchain.genie.GenieAgent` is the official LangGraph-compatible
    wrapper for Databricks Genie Spaces. It provides:
    - invoke() method for LangGraph integration
    - Automatic SQL generation from natural language
    - Query execution against configured tables
    - Response formatting
    
    GENIE SPACE ARCHITECTURE:
    -------------------------
    
    ┌─────────────────────────────────────────────────────────────────────┐
    │                      Genie Space (per domain)                        │
    │                                                                     │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  TRUSTED ASSETS                                              │   │
    │  │  ├── Gold Tables (fact_*, dim_*)                            │   │
    │  │  ├── Table-Valued Functions (TVFs)                          │   │
    │  │  ├── Metric Views (aggregated KPIs)                         │   │
    │  │  └── ML Prediction Tables                                   │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  CONFIGURATION                                               │   │
    │  │  ├── Sample Questions (few-shot examples)                   │   │
    │  │  ├── Instructions (domain-specific prompts)                 │   │
    │  │  └── Asset Descriptions (schema + metadata)                 │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    │  User Query → NL Understanding → SQL Generation → Execution → Response │
    └─────────────────────────────────────────────────────────────────────┘
    
    LAZY INITIALIZATION:
    --------------------
    GenieAgent is created on first use, not at __init__.
    This allows:
    - Fast agent startup
    - Testing without Genie connection
    - Graceful handling if Genie unavailable
    
    ERROR HANDLING PHILOSOPHY:
    --------------------------
    NEVER RAISE EXCEPTIONS FROM query().
    Instead, return error response dict.
    This ensures:
    - Other domains can still respond
    - Orchestrator doesn't crash
    - User gets partial results instead of nothing

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
        
        TRAINING MATERIAL: Dependency Injection Pattern
        ================================================
        
        genie_space_id is OPTIONAL because:
        1. Production: Uses settings (default)
        2. Testing: Can inject mock/test space ID
        3. Development: Can use different spaces
        
        LAZY INITIALIZATION:
        _genie_agent is None initially.
        Created on first access via @property.
        
        WHY LAZY:
        - GenieAgent creation involves network calls
        - May not be needed for all code paths
        - Allows testing without Genie connection

        Args:
            domain: Domain name (cost, security, etc.)
            genie_space_id: Genie Space ID (or None to use settings)
        """
        super().__init__(domain)
        self._genie_space_id = genie_space_id
        self._genie_agent: Optional[Any] = None  # Lazy initialized

    @property
    def genie_agent(self):
        """
        Lazily create GenieAgent.
        
        TRAINING MATERIAL: Python @property for Lazy Initialization
        ===========================================================
        
        PATTERN:
        @property decorator makes this method look like an attribute.
        `worker.genie_agent` calls this method automatically.
        
        LAZY LOADING LOGIC:
        1. Check if already created (_genie_agent is not None)
        2. If not, create and cache
        3. Return cached instance
        
        WHY @property:
        - Encapsulates creation logic
        - Feels like simple attribute access
        - Creation happens transparently
        
        ERROR HANDLING:
        - ImportError: databricks_langchain not installed
        - Exception: Genie Space doesn't exist, auth issues, etc.
        Both logged as metrics for monitoring.
        
        GRACEFUL DEGRADATION:
        If creation fails, returns None.
        query() method checks for None and returns error response.
        
        Uses databricks_langchain.genie.GenieAgent which is the official
        LangGraph-compatible wrapper for Genie Spaces.
        """
        if self._genie_agent is None:
            space_id = self.get_genie_space_id()
            if space_id:
                try:
                    # Dynamic import - only load when needed
                    from databricks_langchain.genie import GenieAgent
                    self._genie_agent = GenieAgent(
                        genie_space_id=space_id,
                        genie_agent_name=f"{self.domain}_genie",
                    )
                except ImportError as e:
                    # Package not installed
                    mlflow.log_metric("genie_agent_import_error", 1)
                    print(f"Warning: Could not import GenieAgent: {e}")
                except Exception as e:
                    # Other initialization errors
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
