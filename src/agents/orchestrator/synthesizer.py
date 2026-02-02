"""
TRAINING MATERIAL: Multi-Agent Response Synthesis Pattern
==========================================================

This module combines responses from multiple domain agents into a unified,
coherent answer. It's the final step in the orchestration pipeline that
creates the user-facing response.

WHY SYNTHESIS IS NEEDED:
------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  THE PROBLEM: Multiple Agent Responses                                   │
│                                                                         │
│  User: "Which expensive jobs are also failing?"                         │
│                                                                         │
│  Cost Agent says:                                                       │
│  "Top 5 expensive jobs: ETL_Daily ($450/day), ML_Train ($320/day)..."   │
│                                                                         │
│  Reliability Agent says:                                                │
│  "Frequently failing jobs: ML_Train (15% failure), Data_Load (12%)..."  │
│                                                                         │
│  WITHOUT Synthesis:                                                     │
│  → Show both responses separately                                       │
│  → User has to mentally combine them                                    │
│  → No insight into the intersection                                     │
│                                                                         │
│  WITH Synthesis:                                                        │
│  "ML_Train is both expensive ($320/day) AND unreliable (15% failures).  │
│   This job costs ~$450/week in wasted compute. Consider optimizing..."  │
│  → Cross-domain insight, actionable recommendation                      │
└─────────────────────────────────────────────────────────────────────────┘

SYNTHESIS PROCESS:
------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  1. COLLECT AGENT RESPONSES                                              │
│     agent_responses = {                                                 │
│       "cost": {"response": "...", "sources": [...], "confidence": 0.9}, │
│       "reliability": {"response": "...", "sources": [...]}              │
│     }                                                                   │
│                                                                         │
│  2. FORMAT FOR LLM                                                       │
│     Structured prompt with all domain responses                         │
│                                                                         │
│  3. LLM SYNTHESIZES                                                      │
│     - Identifies cross-domain correlations                              │
│     - Generates unified narrative                                       │
│     - Adds actionable recommendations                                   │
│                                                                         │
│  4. STRUCTURE OUTPUT                                                     │
│     ## Summary                                                          │
│     ## Details (by domain)                                              │
│     ## Recommendations                                                  │
│     ## Sources                                                          │
└─────────────────────────────────────────────────────────────────────────┘

OUTPUT FORMAT:
--------------

The synthesizer produces structured responses:

## Summary
[1-2 sentence direct answer to the question]

## Details
[Domain-specific breakdown with data]

## Recommendations  
[Actionable next steps based on analysis]

## Sources
[Data sources cited, e.g., Cost Intelligence, Job Health Monitor]

CONFIDENCE AGGREGATION:
-----------------------

Overall confidence is calculated from agent confidences:
- Average of all non-error agent confidences
- Errors reduce overall confidence implicitly
- Used for response quality assessment

KEY DESIGN DECISIONS:
---------------------

1. Temperature 0.3 (vs 0.1 for classifier)
   - Synthesis benefits from some creativity
   - Too low = robotic responses
   - Too high = inconsistent formatting

2. User Context Integration
   - Role-based response tailoring
   - Workspace preferences
   - Cost thresholds for alerts

3. Source Citation
   - Every claim backed by source
   - Builds user trust
   - Enables verification

Combines responses from multiple domain agents into a unified answer.
"""

from typing import Dict, List
import mlflow
import os

from ..config import settings


SYNTHESIZER_PROMPT = """You are a response synthesizer for a Databricks platform monitoring system.

Your task is to combine responses from domain-specific agents into a unified, coherent answer.

USER QUESTION:
{query}

DOMAIN AGENT RESPONSES:
{agent_responses}

USER CONTEXT:
{user_context}

GUIDELINES:
1. Start with a direct answer to the user's question
2. Integrate insights from all relevant domain responses
3. Highlight cross-domain correlations when found (e.g., "expensive jobs that are also failing")
4. Provide actionable recommendations based on the data
5. Use clear formatting with headers and bullet points
6. Cite data sources in [brackets] (e.g., [Cost Intelligence], [Job Health Monitor])
7. If any domain returned an error, note it gracefully
8. Keep the response concise but comprehensive

FORMAT:
## Summary
[1-2 sentence direct answer]

## Details
[Detailed breakdown by domain]

## Recommendations
[Actionable next steps]

## Sources
[List of data sources used]"""


class ResponseSynthesizer:
    """
    Synthesizes responses from multiple domain agents.

    Combines individual domain responses into a unified,
    coherent answer that addresses the user's original query.
    """

    def __init__(self, llm_endpoint: str = None, temperature: float = 0.3):
        """
        Initialize the synthesizer.

        Args:
            llm_endpoint: Databricks model serving endpoint
            temperature: LLM temperature for response generation
        """
        self.llm_endpoint = llm_endpoint or settings.llm_endpoint
        self.temperature = temperature

    def _call_llm(self, prompt: str) -> str:
        """Call Databricks Foundation Model using Databricks SDK."""
        try:
            from databricks.sdk import WorkspaceClient
            from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
            
            w = WorkspaceClient()
            response = w.serving_endpoints.query(
                name=self.llm_endpoint,
                messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
                temperature=self.temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error synthesizing response: {str(e)}"

    @mlflow.trace(name="synthesize_response", span_type="LLM")
    def synthesize(
        self,
        query: str,
        agent_responses: Dict[str, Dict],
        user_context: Dict = None,
    ) -> str:
        """
        Synthesize domain responses into unified answer.

        Args:
            query: Original user query
            agent_responses: Dict of domain -> response dicts
            user_context: Optional user context (preferences, role)

        Returns:
            Synthesized response string.
        """
        with mlflow.start_span(name="format_and_synthesize") as span:
            span.set_inputs({
                "query": query,
                "domains": list(agent_responses.keys()),
            })

            # Format domain responses
            formatted_responses = self._format_agent_responses(agent_responses)

            # Format user context
            context_str = self._format_user_context(user_context or {})

            # Build the full prompt
            full_prompt = SYNTHESIZER_PROMPT.format(
                query=query,
                agent_responses=formatted_responses,
                user_context=context_str,
            )

            # Call LLM
            result = self._call_llm(full_prompt)

            span.set_outputs({
                "response_length": len(result),
            })

            return result

    def _format_agent_responses(self, responses: Dict[str, Dict]) -> str:
        """Format agent responses for the prompt."""
        sections = []

        for domain, response in responses.items():
            domain_upper = domain.upper()

            if response.get("error"):
                sections.append(
                    f"### {domain_upper} (Error)\n"
                    f"Unable to retrieve data: {response['error']}"
                )
            else:
                content = response.get("response", "No data available")
                sources = response.get("sources", [])
                confidence = response.get("confidence", 0.0)

                source_str = ", ".join(sources) if sources else "N/A"
                sections.append(
                    f"### {domain_upper}\n"
                    f"{content}\n"
                    f"_Sources: {source_str} | Confidence: {confidence:.0%}_"
                )

        return "\n\n".join(sections)

    def _format_user_context(self, context: Dict) -> str:
        """Format user context for the prompt."""
        if not context:
            return "No user context available."

        parts = []

        if context.get("role"):
            parts.append(f"- Role: {context['role']}")

        if context.get("preferences"):
            prefs = context["preferences"]
            if prefs.get("preferred_workspace"):
                parts.append(f"- Preferred Workspace: {prefs['preferred_workspace']}")
            if prefs.get("cost_threshold"):
                parts.append(f"- Cost Alert Threshold: ${prefs['cost_threshold']}")

        return "\n".join(parts) if parts else "No specific preferences."

    def extract_sources(self, agent_responses: Dict[str, Dict]) -> List[str]:
        """
        Extract all sources from agent responses.

        Args:
            agent_responses: Dict of domain -> response dicts

        Returns:
            Deduplicated list of source strings.
        """
        sources = set()
        for domain, response in agent_responses.items():
            domain_sources = response.get("sources", [])
            sources.update(domain_sources)
            # Also add domain as a source
            sources.add(f"{domain.title()} Intelligence")

        return sorted(list(sources))

    def calculate_confidence(self, agent_responses: Dict[str, Dict]) -> float:
        """
        Calculate overall confidence from agent responses.

        Args:
            agent_responses: Dict of domain -> response dicts

        Returns:
            Average confidence score.
        """
        confidences = [
            r.get("confidence", 0.0)
            for r in agent_responses.values()
            if not r.get("error")
        ]

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)
