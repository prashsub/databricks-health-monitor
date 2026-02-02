"""
TRAINING MATERIAL: Intent Classification for Multi-Agent Routing
================================================================

This module classifies user queries into domain categories for routing to
the appropriate worker agents. It's the first step in the orchestration
pipeline that determines which agents will handle a query.

WHY INTENT CLASSIFICATION:
--------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  THE PROBLEM: Multiple Domain Experts                                    │
│                                                                         │
│  User asks: "Why did costs spike yesterday?"                            │
│                                                                         │
│  WITHOUT Classification:                                                │
│  → Ask ALL 5 domain agents (wasteful, slow, irrelevant answers)         │
│                                                                         │
│  WITH Classification:                                                   │
│  → Classify as COST → Route to Cost Agent ONLY                          │
│  → Faster response, relevant data, focused answer                       │
│                                                                         │
│  User asks: "Which expensive jobs are also failing?"                    │
│  → Classify as [COST, RELIABILITY] → Route to BOTH agents               │
│  → Cross-domain query handled correctly                                 │
└─────────────────────────────────────────────────────────────────────────┘

CLASSIFICATION FLOW:
--------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  INPUT: "Which expensive jobs are also failing?"                         │
│                                                                         │
│       ↓ LLM analyzes query                                              │
│                                                                         │
│  LLM REASONING:                                                         │
│  - "expensive" → Cost domain (billing, spend)                           │
│  - "jobs" → Could be Cost (job costs) or Reliability (job health)       │
│  - "failing" → Reliability domain (job failures)                        │
│  - Combination → Multi-domain query                                     │
│                                                                         │
│       ↓ Output structured JSON                                          │
│                                                                         │
│  OUTPUT: {"domains": ["COST", "RELIABILITY"], "confidence": 0.88}       │
└─────────────────────────────────────────────────────────────────────────┘

PROMPT ENGINEERING:
-------------------

The classification prompt includes:
1. DOMAIN DEFINITIONS - Clear descriptions of each domain's scope
2. CLASSIFICATION RULES - Multi-domain support, ordering, confidence
3. FEW-SHOT EXAMPLES - Sample queries with expected output

Key prompt techniques:
- Low temperature (0.1) for consistency
- JSON output format for reliable parsing
- Domain descriptions prevent confusion

CONFIDENCE SCORES:
------------------
- 0.9+ : High confidence, clear single-domain query
- 0.8-0.9: Good confidence, may involve secondary domain
- 0.7-0.8: Moderate confidence, ambiguous query
- <0.7: Low confidence, might need clarification

Classifies user queries into domain categories for routing.
"""

from typing import Dict, List
import json
import mlflow

from ..config import settings


INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for Databricks platform monitoring.

Analyze the user query and classify it into ONE OR MORE relevant domains.

AVAILABLE DOMAINS:
- COST: Billing, spending, DBU usage, budgets, chargeback, pricing, cost allocation
- SECURITY: Access control, audit logs, permissions, threats, compliance, authentication
- PERFORMANCE: Query speed, cluster utilization, latency, warehouse performance, optimization
- RELIABILITY: Job failures, SLAs, incidents, pipeline health, job runs, task success
- QUALITY: Data quality, lineage, freshness, governance, schema changes, data validation

CLASSIFICATION RULES:
1. Select ALL relevant domains (can be multiple)
2. Order domains by relevance (most relevant first)
3. Provide confidence score (0.0-1.0)
4. If query spans multiple domains, include all applicable ones

EXAMPLES:
Query: "Why did costs spike yesterday?"
Output: {{"domains": ["COST"], "confidence": 0.95}}

Query: "Which expensive jobs are also failing frequently?"
Output: {{"domains": ["COST", "RELIABILITY"], "confidence": 0.88}}

Query: "Who accessed sensitive data and what did it cost?"
Output: {{"domains": ["SECURITY", "COST"], "confidence": 0.85}}

Query: "Are slow queries causing job failures?"
Output: {{"domains": ["PERFORMANCE", "RELIABILITY"], "confidence": 0.82}}

RESPOND WITH ONLY A JSON OBJECT:
{{"domains": ["DOMAIN1", ...], "confidence": <float>}}"""


class IntentClassifier:
    """
    Classifies user queries into domain categories.

    Uses an LLM to analyze the query and determine which domain
    worker agents should handle it.

    Attributes:
        llm_endpoint: Databricks model serving endpoint name
        temperature: LLM temperature (lower = more deterministic)
    """

    def __init__(self, llm_endpoint: str = None, temperature: float = 0.1):
        """
        Initialize the intent classifier.

        Args:
            llm_endpoint: Databricks model serving endpoint
            temperature: LLM temperature (lower = more deterministic)
        """
        self.llm_endpoint = llm_endpoint or settings.llm_endpoint
        self.temperature = temperature

    def _call_llm(self, query: str) -> str:
        """Call Databricks Foundation Model using Databricks SDK."""
        try:
            from databricks.sdk import WorkspaceClient
            from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
            
            w = WorkspaceClient()
            response = w.serving_endpoints.query(
                name=self.llm_endpoint,
                messages=[
                    ChatMessage(role=ChatMessageRole.SYSTEM, content=INTENT_CLASSIFIER_PROMPT),
                    ChatMessage(role=ChatMessageRole.USER, content=query)
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"domains": ["COST"], "confidence": 0.5, "error": str(e)})

    @mlflow.trace(name="classify_intent", span_type="CLASSIFIER")
    def classify(self, query: str) -> Dict:
        """
        Classify a user query.

        Args:
            query: User query string

        Returns:
            Classification result with domains and confidence.

        Example:
            >>> classifier = IntentClassifier()
            >>> result = classifier.classify("Why did costs spike?")
            >>> print(result)
            {"domains": ["COST"], "confidence": 0.95}
        """
        with mlflow.start_span(name="llm_classify") as span:
            span.set_inputs({"query": query})

            content = self._call_llm(query)

            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(content[start:end])
                else:
                    # Default to unified handling
                    result = {"domains": ["COST"], "confidence": 0.5}

            # Normalize domain names to uppercase
            result["domains"] = [d.upper() for d in result.get("domains", [])]

            span.set_outputs(result)
            return result

    def get_primary_domain(self, classification: Dict) -> str:
        """
        Get the primary (most relevant) domain from classification.

        Args:
            classification: Classification result

        Returns:
            Primary domain string.
        """
        domains = classification.get("domains", [])
        return domains[0] if domains else "COST"

    def is_multi_domain(self, classification: Dict) -> bool:
        """
        Check if classification spans multiple domains.

        Args:
            classification: Classification result

        Returns:
            True if query requires multiple domains.
        """
        return len(classification.get("domains", [])) > 1

    def get_domains(self, classification: Dict) -> List[str]:
        """
        Get all domains from classification.

        Args:
            classification: Classification result

        Returns:
            List of domain strings.
        """
        return classification.get("domains", ["COST"])
