# 03 - Orchestrator Agent

## Overview

The Orchestrator Agent is the supervisor of the multi-agent system. It receives user queries, classifies intent, routes to appropriate worker agents, and synthesizes responses. Implemented using LangGraph for state machine orchestration.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Intent Classification** | Determine which domain(s) a query relates to |
| **Agent Routing** | Route queries to 1 or more worker agents |
| **Context Management** | Load/save conversation history from Lakebase |
| **Response Synthesis** | Combine multi-agent responses into coherent answer |
| **Utility Tool Invocation** | Call web search, dashboard linker, alerts, RAG |
| **Error Handling** | Graceful degradation when components fail |

## LangGraph State Machine

### State Definition

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """State that flows through the orchestrator graph."""
    
    # Input
    query: str
    user_id: str
    conversation_id: Optional[str]
    
    # Conversation history (from Lakebase)
    messages: Annotated[list, add_messages]
    
    # Intent classification results
    intent: dict  # {domains: List[str], confidence: float}
    
    # Worker agent responses
    agent_responses: dict  # {domain: response_dict}
    
    # Utility tool results
    utility_results: dict  # {tool_name: result}
    
    # Final output
    synthesized_response: str
    sources: List[str]
    confidence: float
    
    # Metadata
    trace_id: str
    timestamp: str
```

### Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import mlflow

def create_orchestrator_graph():
    """Create the orchestrator state machine."""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("load_context", load_context)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("route_to_agents", route_to_agents)
    workflow.add_node("cost_agent", query_cost_agent)
    workflow.add_node("security_agent", query_security_agent)
    workflow.add_node("performance_agent", query_performance_agent)
    workflow.add_node("reliability_agent", query_reliability_agent)
    workflow.add_node("quality_agent", query_quality_agent)
    workflow.add_node("collect_responses", collect_responses)
    workflow.add_node("check_utility_needs", check_utility_needs)
    workflow.add_node("invoke_utilities", invoke_utilities)
    workflow.add_node("synthesize", synthesize_response)
    workflow.add_node("save_context", save_context)
    
    # Define edges
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "classify_intent")
    workflow.add_edge("classify_intent", "route_to_agents")
    
    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "route_to_agents",
        determine_agents_to_invoke,
        {
            "cost_only": "cost_agent",
            "security_only": "security_agent",
            "performance_only": "performance_agent",
            "reliability_only": "reliability_agent",
            "quality_only": "quality_agent",
            "multi_agent": "cost_agent",  # Start parallel execution
        }
    )
    
    # All agents lead to collect_responses
    for agent in ["cost_agent", "security_agent", "performance_agent", 
                  "reliability_agent", "quality_agent"]:
        workflow.add_edge(agent, "collect_responses")
    
    workflow.add_edge("collect_responses", "check_utility_needs")
    
    # Conditional utility invocation
    workflow.add_conditional_edges(
        "check_utility_needs",
        needs_utility_tools,
        {
            "yes": "invoke_utilities",
            "no": "synthesize"
        }
    )
    
    workflow.add_edge("invoke_utilities", "synthesize")
    workflow.add_edge("synthesize", "save_context")
    workflow.add_edge("save_context", END)
    
    # Compile with checkpointing
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
```

## Intent Classification

### System Prompt

```python
INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for Databricks platform monitoring.

Analyze the user query and classify it into ONE OR MORE of these domains:

DOMAINS:
- COST: Billing, spending, DBU usage, budgets, chargeback, pricing, waste
- SECURITY: Access control, audit logs, threats, compliance, user activity, permissions
- PERFORMANCE: Query speed, cluster utilization, latency, optimization, slow queries
- RELIABILITY: Job failures, SLAs, incidents, success rates, pipelines, errors
- QUALITY: Data quality, lineage, freshness, governance, classification, anomalies

RULES:
1. A query can belong to multiple domains (e.g., "Are expensive jobs failing?" → COST + RELIABILITY)
2. If unsure, include all potentially relevant domains
3. Return confidence score (0.0-1.0) based on clarity of intent

EXAMPLES:
- "Why did costs spike?" → {domains: ["COST"], confidence: 0.95}
- "Who accessed sensitive data?" → {domains: ["SECURITY"], confidence: 0.92}
- "Which jobs are slow?" → {domains: ["PERFORMANCE", "RELIABILITY"], confidence: 0.85}
- "Give me a health overview" → {domains: ["COST", "SECURITY", "PERFORMANCE", "RELIABILITY", "QUALITY"], confidence: 0.70}

Return JSON only: {"domains": ["DOMAIN1", "DOMAIN2"], "confidence": 0.XX}"""
```

### Implementation

```python
from langchain_databricks import ChatDatabricks
from langchain.prompts import ChatPromptTemplate
import json

def classify_intent(state: AgentState) -> AgentState:
    """Classify the user query into domains."""
    
    with mlflow.start_span(name="intent_classification", span_type="CLASSIFIER") as span:
        llm = ChatDatabricks(
            endpoint="databricks-dbrx-instruct",
            temperature=0.1  # Low temperature for consistent classification
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_CLASSIFIER_PROMPT),
            ("human", "{query}")
        ])
        
        chain = prompt | llm
        
        response = chain.invoke({"query": state["query"]})
        intent = json.loads(response.content)
        
        # Log to trace
        span.set_attributes({
            "query": state["query"],
            "domains": intent["domains"],
            "confidence": intent["confidence"]
        })
        
        return {**state, "intent": intent}
```

## Agent Routing

### Routing Logic

```python
def determine_agents_to_invoke(state: AgentState) -> str:
    """Determine which agents to invoke based on intent."""
    
    domains = [d.lower() for d in state["intent"]["domains"]]
    
    if len(domains) == 1:
        return f"{domains[0]}_only"
    else:
        return "multi_agent"

def route_to_agents(state: AgentState) -> AgentState:
    """Prepare state for agent invocation."""
    
    domains = [d.lower() for d in state["intent"]["domains"]]
    
    # Initialize agent_responses dict
    state["agent_responses"] = {domain: None for domain in domains}
    
    return state
```

### Parallel Agent Execution

For multi-domain queries, agents execute in parallel:

```python
import asyncio
from typing import Dict

async def invoke_agents_parallel(state: AgentState, agents: Dict[str, callable]) -> AgentState:
    """Invoke multiple agents in parallel."""
    
    domains = [d.lower() for d in state["intent"]["domains"]]
    
    with mlflow.start_span(name="parallel_agent_execution") as span:
        tasks = []
        for domain in domains:
            if domain in agents:
                task = asyncio.create_task(
                    agents[domain].query_async(state["query"], state.get("messages", []))
                )
                tasks.append((domain, task))
        
        # Wait for all agents
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        
        # Collect responses
        for (domain, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                state["agent_responses"][domain] = {
                    "error": str(result),
                    "response": f"Error querying {domain} data"
                }
            else:
                state["agent_responses"][domain] = result
        
        span.set_attributes({
            "domains_queried": domains,
            "successful": sum(1 for r in results if not isinstance(r, Exception)),
            "failed": sum(1 for r in results if isinstance(r, Exception))
        })
    
    return state
```

## Response Synthesis

### System Prompt

```python
SYNTHESIS_PROMPT = """You are a response synthesizer for Databricks platform monitoring.

You have received responses from multiple domain experts. Your job is to:
1. Combine insights into a coherent, unified answer
2. Highlight correlations between domains (e.g., cost spikes related to job failures)
3. Provide actionable recommendations
4. Cite sources for each insight

DOMAIN RESPONSES:
{agent_responses}

USER QUESTION:
{query}

UTILITY DATA (if available):
{utility_results}

FORMAT YOUR RESPONSE:
1. Start with a direct answer to the user's question
2. Provide supporting details from each relevant domain
3. Note any cross-domain correlations
4. End with 1-3 actionable recommendations
5. Include sources in [brackets]

Be concise but comprehensive. Use bullet points for clarity."""
```

### Implementation

```python
def synthesize_response(state: AgentState) -> AgentState:
    """Synthesize responses from all agents into final answer."""
    
    with mlflow.start_span(name="response_synthesis", span_type="LLM") as span:
        llm = ChatDatabricks(
            endpoint="databricks-dbrx-instruct",
            temperature=0.3  # Slightly higher for natural language
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYNTHESIS_PROMPT),
            ("human", "Synthesize the responses above into a unified answer.")
        ])
        
        chain = prompt | llm
        
        # Format agent responses for prompt
        formatted_responses = "\n\n".join([
            f"### {domain.upper()} AGENT:\n{resp.get('response', 'No data')}"
            for domain, resp in state["agent_responses"].items()
            if resp is not None
        ])
        
        # Format utility results
        utility_str = "\n".join([
            f"- {tool}: {result}"
            for tool, result in state.get("utility_results", {}).items()
        ]) or "None"
        
        response = chain.invoke({
            "agent_responses": formatted_responses,
            "query": state["query"],
            "utility_results": utility_str
        })
        
        # Collect all sources
        sources = []
        for domain, resp in state["agent_responses"].items():
            if resp and "sources" in resp:
                sources.extend(resp["sources"])
        
        # Calculate confidence (average of agent confidences)
        confidences = [
            resp.get("confidence", 0.5)
            for resp in state["agent_responses"].values()
            if resp is not None
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        span.set_attributes({
            "response_length": len(response.content),
            "source_count": len(sources),
            "confidence": avg_confidence
        })
        
        return {
            **state,
            "synthesized_response": response.content,
            "sources": sources,
            "confidence": avg_confidence
        }
```

## Utility Tool Invocation

### Check if Utilities Needed

```python
def check_utility_needs(state: AgentState) -> AgentState:
    """Determine if utility tools should be invoked."""
    
    query_lower = state["query"].lower()
    
    needs = {
        "web_search": any(kw in query_lower for kw in [
            "outage", "status", "news", "latest", "update", "documentation"
        ]),
        "dashboard_linker": any(kw in query_lower for kw in [
            "show me", "dashboard", "visualize", "chart", "graph"
        ]),
        "alert_trigger": any(kw in query_lower for kw in [
            "alert", "notify", "trigger", "incident"
        ]),
        "runbook_rag": any(kw in query_lower for kw in [
            "how to fix", "remediate", "resolve", "troubleshoot"
        ])
    }
    
    state["utility_needs"] = needs
    return state

def needs_utility_tools(state: AgentState) -> str:
    """Routing function for utility tools."""
    needs = state.get("utility_needs", {})
    return "yes" if any(needs.values()) else "no"
```

### Invoke Utilities

```python
async def invoke_utilities(state: AgentState) -> AgentState:
    """Invoke required utility tools."""
    
    needs = state.get("utility_needs", {})
    results = {}
    
    with mlflow.start_span(name="utility_invocation") as span:
        if needs.get("web_search"):
            results["web_search"] = await web_search_tool.search(state["query"])
        
        if needs.get("dashboard_linker"):
            results["dashboard_linker"] = dashboard_linker.get_relevant_dashboard(
                state["intent"]["domains"]
            )
        
        if needs.get("alert_trigger"):
            results["alert_trigger"] = alert_trigger.prepare_alert(
                state["query"],
                state["agent_responses"]
            )
        
        if needs.get("runbook_rag"):
            results["runbook_rag"] = await runbook_rag.search(
                state["query"],
                state["agent_responses"]
            )
        
        span.set_attributes({
            "tools_invoked": list(results.keys()),
            "results_count": len(results)
        })
    
    return {**state, "utility_results": results}
```

## Memory Management

### Load Context

```python
from databricks.agents.memory import LakebaseMemory

def load_context(state: AgentState) -> AgentState:
    """Load conversation history and user preferences from Lakebase."""
    
    with mlflow.start_span(name="load_context") as span:
        # Short-term memory (conversation)
        short_term = LakebaseMemory(
            table_name="health_monitor.memory.short_term",
            ttl_hours=24
        )
        
        # Long-term memory (preferences)
        long_term = LakebaseMemory(
            table_name="health_monitor.memory.long_term",
            ttl_days=365
        )
        
        # Load conversation history
        conversation_id = state.get("conversation_id")
        if conversation_id:
            history = short_term.retrieve(
                session_id=conversation_id,
                max_messages=10
            )
            state["messages"] = history
        
        # Load user preferences
        user_prefs = long_term.retrieve(user_id=state["user_id"])
        if user_prefs:
            state["user_preferences"] = user_prefs
        
        span.set_attributes({
            "conversation_id": conversation_id,
            "message_count": len(state.get("messages", [])),
            "has_preferences": user_prefs is not None
        })
    
    return state
```

### Save Context

```python
def save_context(state: AgentState) -> AgentState:
    """Save conversation turn to Lakebase."""
    
    with mlflow.start_span(name="save_context") as span:
        short_term = LakebaseMemory(
            table_name="health_monitor.memory.short_term",
            ttl_hours=24
        )
        
        # Save current turn
        short_term.save(
            session_id=state.get("conversation_id", "default"),
            user_id=state["user_id"],
            messages=[
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": state["synthesized_response"]}
            ]
        )
        
        span.set_attributes({
            "saved_messages": 2,
            "conversation_id": state.get("conversation_id")
        })
    
    return state
```

## Complete Orchestrator Class

```python
from mlflow.pyfunc import ChatAgent
import mlflow

class HealthMonitorOrchestrator(ChatAgent):
    """Main orchestrator agent for the Health Monitor system."""
    
    def __init__(self):
        self.graph = create_orchestrator_graph()
        self.worker_agents = {
            "cost": CostWorkerAgent(),
            "security": SecurityWorkerAgent(),
            "performance": PerformanceWorkerAgent(),
            "reliability": ReliabilityWorkerAgent(),
            "quality": QualityWorkerAgent()
        }
    
    @mlflow.trace(name="orchestrator_invoke", span_type="AGENT")
    def predict(
        self,
        context,
        messages: list,
        params: dict = None
    ) -> dict:
        """
        Process a user query through the orchestrator.
        
        Args:
            context: MLflow context
            messages: Chat history with latest user message
            params: Optional parameters (user_id, conversation_id)
        
        Returns:
            {
                "content": str,  # The synthesized response
                "sources": List[str],  # Data sources used
                "confidence": float  # Response confidence
            }
        """
        # Extract latest query
        query = messages[-1]["content"]
        user_id = params.get("user_id", "anonymous")
        conversation_id = params.get("conversation_id")
        
        # Initialize state
        initial_state = {
            "query": query,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": messages[:-1],  # Previous messages
            "trace_id": mlflow.get_current_active_span().span_id
        }
        
        # Run the graph
        config = {"configurable": {"thread_id": conversation_id or "default"}}
        final_state = self.graph.invoke(initial_state, config)
        
        # Tag the trace
        mlflow.update_current_trace(tags={
            "user_id": user_id,
            "domains": ",".join(final_state["intent"]["domains"]),
            "confidence": str(final_state["confidence"])
        })
        
        return {
            "content": final_state["synthesized_response"],
            "sources": final_state["sources"],
            "confidence": final_state["confidence"]
        }

# Register for MLflow logging
mlflow.models.set_model(HealthMonitorOrchestrator())
```

## Configuration

### Environment Variables

```python
# Required environment variables
ORCHESTRATOR_CONFIG = {
    "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST"),
    "DATABRICKS_TOKEN": os.environ.get("DATABRICKS_TOKEN"),
    
    # LLM endpoints
    "CLASSIFIER_ENDPOINT": "databricks-dbrx-instruct",
    "SYNTHESIS_ENDPOINT": "databricks-dbrx-instruct",
    
    # Memory tables
    "SHORT_TERM_MEMORY_TABLE": "health_monitor.memory.short_term",
    "LONG_TERM_MEMORY_TABLE": "health_monitor.memory.long_term",
    
    # Timeouts
    "AGENT_TIMEOUT_SECONDS": 30,
    "GENIE_TIMEOUT_SECONDS": 45,
    
    # Retry config
    "MAX_RETRIES": 3,
    "RETRY_DELAY_SECONDS": 1
}
```

## Testing the Orchestrator

```python
# Test script
def test_orchestrator():
    orchestrator = HealthMonitorOrchestrator()
    
    test_cases = [
        {
            "messages": [{"role": "user", "content": "Why did costs spike last Tuesday?"}],
            "expected_domains": ["cost"]
        },
        {
            "messages": [{"role": "user", "content": "Are expensive jobs also failing?"}],
            "expected_domains": ["cost", "reliability"]
        },
        {
            "messages": [{"role": "user", "content": "Give me a platform health overview"}],
            "expected_domains": ["cost", "security", "performance", "reliability", "quality"]
        }
    ]
    
    for test in test_cases:
        result = orchestrator.predict(
            context=None,
            messages=test["messages"],
            params={"user_id": "test_user"}
        )
        
        print(f"Query: {test['messages'][-1]['content']}")
        print(f"Response: {result['content'][:200]}...")
        print(f"Confidence: {result['confidence']}")
        print(f"Sources: {result['sources']}")
        print("-" * 80)

if __name__ == "__main__":
    test_orchestrator()
```

## Next Steps

- **[04-Worker Agents](04-worker-agents.md)**: Detailed worker agent implementation
- **[05-Genie Integration](05-genie-integration.md)**: Genie API patterns
- **[08-MLflow Tracing](08-mlflow-tracing.md)**: Complete tracing setup

