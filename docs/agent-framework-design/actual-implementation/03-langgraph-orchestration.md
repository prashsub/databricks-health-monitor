# 03 - LangGraph Orchestration

## Overview

This document details the LangGraph state machine that orchestrates the multi-agent workflow. The graph defines nodes (processing steps), edges (transitions), and conditional routing based on user intent.

---

## 📍 File Locations

| File | Purpose |
|------|---------|
| `src/agents/orchestrator/graph.py` | Graph definition and node functions |
| `src/agents/orchestrator/state.py` | AgentState TypedDict |
| `src/agents/orchestrator/intent_classifier.py` | Intent classification logic |
| `src/agents/orchestrator/synthesizer.py` | Response synthesis |

---

## 🗺️ Graph Structure

### Visual Representation

```
                                    START
                                      │
                                      ▼
                              ┌───────────────┐
                              │  load_context │
                              │   (MEMORY)    │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │classify_intent│
                              │  (CLASSIFIER) │
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │route_to_agents│
                              │  (CONDITIONAL)│
                              └───────┬───────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   cost_agent    │    │ security_agent  │    │ parallel_agents │
    │     (TOOL)      │    │     (TOOL)      │    │   (PARALLEL)    │
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                           ┌───────────────────┐
                           │synthesize_response│
                           │       (LLM)       │
                           └────────┬──────────┘
                                    │
                                    ▼
                                   END
```

---

## 🏗️ Graph Construction

### create_orchestrator_graph()

```python
# File: src/agents/orchestrator/graph.py
# Lines: 200-270

def create_orchestrator_graph() -> StateGraph:
    """
    Create the orchestrator state graph.
    
    Returns:
        StateGraph configured with all nodes and edges.
    """
    # Create graph with AgentState schema
    workflow = StateGraph(AgentState)
    
    # =====================
    # Add nodes
    # =====================
    workflow.add_node("load_context", load_context)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("cost_agent", cost_agent_node)
    workflow.add_node("security_agent", security_agent_node)
    workflow.add_node("performance_agent", performance_agent_node)
    workflow.add_node("reliability_agent", reliability_agent_node)
    workflow.add_node("quality_agent", quality_agent_node)
    workflow.add_node("parallel_agents", parallel_agents_node)
    workflow.add_node("synthesize_response", synthesize_response)
    
    # =====================
    # Add edges
    # =====================
    
    # Entry point
    workflow.set_entry_point("load_context")
    
    # Sequential flow
    workflow.add_edge("load_context", "classify_intent")
    
    # Conditional routing after classification
    workflow.add_conditional_edges(
        "classify_intent",
        route_to_agents,
        {
            "cost_agent": "cost_agent",
            "security_agent": "security_agent",
            "performance_agent": "performance_agent",
            "reliability_agent": "reliability_agent",
            "quality_agent": "quality_agent",
            "parallel_agents": "parallel_agents",
        }
    )
    
    # All worker agents lead to synthesis
    for agent_name in [
        "cost_agent", "security_agent", "performance_agent",
        "reliability_agent", "quality_agent", "parallel_agents"
    ]:
        workflow.add_edge(agent_name, "synthesize_response")
    
    # Terminal node
    workflow.add_edge("synthesize_response", END)
    
    return workflow
```

---

## 📦 Node Implementations

### 1. load_context Node

**Purpose:** Retrieve user preferences and history from long-term memory.

```python
# File: src/agents/orchestrator/graph.py
# Lines: 31-65

@mlflow.trace(name="load_context", span_type="MEMORY")
def load_context(state: AgentState) -> Dict:
    """
    Load memory context for the user.

    Retrieves long-term memory (preferences, insights) to personalize
    the response.
    """
    user_id = state["user_id"]

    memory_context = {
        "preferences": {},
        "role": None,
        "recent_queries": [],
    }

    try:
        # Search for user preferences
        prefs = long_term_memory.search_memories(
            user_id=user_id,
            query="user preferences workspace threshold",
            limit=3,
        )

        for mem in prefs:
            if "preference" in mem.key.lower():
                memory_context["preferences"].update(mem.value)
            if "role" in mem.key.lower():
                memory_context["role"] = mem.value.get("role")

    except Exception as e:
        # Memory unavailable - proceed without context
        mlflow.log_metric("memory_load_error", 1)

    return {"memory_context": memory_context}
```

**State Changes:**
- **Input:** `user_id`
- **Output:** `memory_context` (dict with preferences, role, recent_queries)

---

### 2. classify_intent Node

**Purpose:** Classify user query into one or more domains.

```python
# File: src/agents/orchestrator/graph.py
# Lines: 68-84

@mlflow.trace(name="classify_intent_node", span_type="CLASSIFIER")
def classify_intent(state: AgentState) -> Dict:
    """
    Classify the user's intent.

    Determines which domain(s) should handle the query.
    """
    query = state["query"]
    intent = intent_classifier.classify(query)

    # Add user message to conversation
    messages = [HumanMessage(content=query)]

    return {
        "intent": intent,
        "messages": messages,
    }
```

**State Changes:**
- **Input:** `query`
- **Output:** `intent` (dict with `domains` list and `confidence` score)

**Intent Classifier Details:**

```python
# File: src/agents/orchestrator/intent_classifier.py
# Lines: 52-110

class IntentClassifier:
    """
    Classifies user queries into domain categories.
    """

    def __init__(self, llm_endpoint: str = None, temperature: float = 0.1):
        self.llm = ChatDatabricks(
            endpoint=llm_endpoint or settings.llm_endpoint,
            temperature=temperature,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_CLASSIFIER_PROMPT),
            ("human", "{query}"),
        ])
        self.chain = self.prompt | self.llm

    @mlflow.trace(name="classify_intent", span_type="CLASSIFIER")
    def classify(self, query: str) -> Dict:
        """
        Classify a query into domain categories.
        
        Returns:
            {"domains": ["COST", ...], "confidence": 0.95}
        """
        try:
            response = self.chain.invoke({"query": query})
            result = json.loads(response.content)
            
            # Validate response structure
            if "domains" not in result:
                result = {"domains": ["COST"], "confidence": 0.5}
            
            return result
            
        except Exception as e:
            # Fallback to cost domain
            return {"domains": ["COST"], "confidence": 0.5}
```

---

### 3. route_to_agents (Conditional Edge)

**Purpose:** Route to appropriate worker agent(s) based on classification.

```python
# File: src/agents/orchestrator/graph.py
# Lines: 87-115

def route_to_agents(state: AgentState) -> Literal[
    "cost_agent", "security_agent", "performance_agent",
    "reliability_agent", "quality_agent", "parallel_agents"
]:
    """
    Route to appropriate agent(s) based on intent.

    For single-domain queries, routes to that domain.
    For multi-domain queries, routes to parallel execution.
    """
    intent = state.get("intent", {})
    domains = intent.get("domains", ["COST"])

    if len(domains) == 1:
        # Single domain - route directly
        domain = domains[0].lower()
        agent_map = {
            "cost": "cost_agent",
            "security": "security_agent",
            "performance": "performance_agent",
            "reliability": "reliability_agent",
            "quality": "quality_agent",
        }
        return agent_map.get(domain, "cost_agent")
    else:
        # Multiple domains - parallel execution
        return "parallel_agents"
```

**Routing Logic:**

| Query Type | Domains | Route To |
|------------|---------|----------|
| Single domain | `["COST"]` | `cost_agent` |
| Single domain | `["SECURITY"]` | `security_agent` |
| Multi-domain | `["COST", "RELIABILITY"]` | `parallel_agents` |

---

### 4. Worker Agent Nodes

**Purpose:** Query domain-specific Genie Spaces.

```python
# File: src/agents/orchestrator/graph.py
# Lines: 118-155

@mlflow.trace(name="cost_agent_node", span_type="TOOL")
def cost_agent_node(state: AgentState) -> Dict:
    """
    Execute cost domain worker.
    """
    query = state["query"]
    context = state.get("memory_context", {})
    
    worker = get_worker_agent("cost")
    result = worker.query(query, context)
    
    return {
        "worker_results": {
            "cost": result
        }
    }


@mlflow.trace(name="security_agent_node", span_type="TOOL")
def security_agent_node(state: AgentState) -> Dict:
    """
    Execute security domain worker.
    """
    query = state["query"]
    context = state.get("memory_context", {})
    
    worker = get_worker_agent("security")
    result = worker.query(query, context)
    
    return {
        "worker_results": {
            "security": result
        }
    }

# Similar pattern for performance, reliability, quality agents...
```

---

### 5. parallel_agents Node

**Purpose:** Execute multiple workers concurrently.

```python
# File: src/agents/orchestrator/graph.py
# Lines: 158-195

@mlflow.trace(name="parallel_agents_node", span_type="TOOL")
def parallel_agents_node(state: AgentState) -> Dict:
    """
    Execute multiple domain workers in parallel.
    
    Uses concurrent.futures for parallel execution.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    query = state["query"]
    context = state.get("memory_context", {})
    domains = state.get("intent", {}).get("domains", [])
    
    worker_results = {}
    
    def query_worker(domain: str) -> tuple:
        """Query a single worker and return (domain, result)."""
        worker = get_worker_agent(domain.lower())
        result = worker.query(query, context)
        return (domain.lower(), result)
    
    # Execute workers in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(query_worker, domain): domain 
            for domain in domains
        }
        
        for future in as_completed(futures, timeout=settings.agent_timeout_seconds):
            try:
                domain, result = future.result()
                worker_results[domain] = result
            except Exception as e:
                domain = futures[future]
                worker_results[domain.lower()] = {
                    "response": f"Error querying {domain}: {str(e)}",
                    "confidence": 0.0,
                    "sources": [],
                }
    
    return {"worker_results": worker_results}
```

---

### 6. synthesize_response Node

**Purpose:** Combine worker results into coherent response.

```python
# File: src/agents/orchestrator/graph.py
# Lines: 200-250

@mlflow.trace(name="synthesize_response", span_type="LLM")
def synthesize_response(state: AgentState) -> Dict:
    """
    Synthesize a coherent response from worker results.
    
    Uses an LLM to combine multiple domain responses into
    a single, well-formatted answer.
    """
    query = state["query"]
    worker_results = state.get("worker_results", {})
    memory_context = state.get("memory_context", {})
    
    # Use synthesizer to combine results
    response, confidence, sources = synthesizer.synthesize(
        query=query,
        worker_results=worker_results,
        user_context=memory_context,
    )
    
    # Add assistant message to conversation
    messages = state.get("messages", [])
    messages.append(AIMessage(content=response))
    
    return {
        "response": response,
        "confidence": confidence,
        "sources": sources,
        "messages": messages,
    }
```

**Synthesizer Implementation:**

```python
# File: src/agents/orchestrator/synthesizer.py
# Lines: 30-100

class ResponseSynthesizer:
    """
    Synthesizes coherent responses from multiple worker results.
    """
    
    def __init__(self, llm_endpoint: str = None):
        self.llm = ChatDatabricks(
            endpoint=llm_endpoint or settings.llm_endpoint,
            temperature=0.3,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYNTHESIS_PROMPT),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm
    
    @mlflow.trace(name="synthesize", span_type="LLM")
    def synthesize(
        self,
        query: str,
        worker_results: Dict[str, Dict],
        user_context: Dict = None,
    ) -> Tuple[str, float, List[str]]:
        """
        Synthesize a response from worker results.
        
        Returns:
            Tuple of (response_text, confidence, sources)
        """
        # Format worker results for LLM
        results_text = self._format_results(worker_results)
        
        # Build synthesis input
        synthesis_input = {
            "query": query,
            "results": results_text,
            "user_role": user_context.get("role", "user") if user_context else "user",
            "preferences": user_context.get("preferences", {}) if user_context else {},
        }
        
        # Generate synthesis
        response = self.chain.invoke({"input": json.dumps(synthesis_input)})
        
        # Calculate overall confidence
        confidences = [
            r.get("confidence", 0.5) 
            for r in worker_results.values()
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Collect all sources
        all_sources = []
        for r in worker_results.values():
            all_sources.extend(r.get("sources", []))
        
        return response.content, avg_confidence, list(set(all_sources))
```

---

## 🔄 State Transitions

### Complete State Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Initial State                                 │
├─────────────────────────────────────────────────────────────────────┤
│ {                                                                   │
│   "user_id": "user@company.com",                                    │
│   "thread_id": "conv_abc123",                                       │
│   "query": "Why did costs spike yesterday?",                        │
│   "intent": {},                                                     │
│   "memory_context": {},                                             │
│   "worker_results": {},                                             │
│   "messages": [],                                                   │
│   "response": "",                                                   │
│   "confidence": 0.0,                                                │
│   "sources": []                                                     │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      After load_context                             │
├─────────────────────────────────────────────────────────────────────┤
│ {                                                                   │
│   ...                                                               │
│   "memory_context": {                                               │
│     "preferences": {"cost_threshold": 1000, "workspace": "prod"},   │
│     "role": "data_engineer",                                        │
│     "recent_queries": ["What's our monthly budget?"]                │
│   },                                                                │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      After classify_intent                          │
├─────────────────────────────────────────────────────────────────────┤
│ {                                                                   │
│   ...                                                               │
│   "intent": {                                                       │
│     "domains": ["COST"],                                            │
│     "confidence": 0.95                                              │
│   },                                                                │
│   "messages": [HumanMessage(content="Why did costs spike...")]      │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      After cost_agent                               │
├─────────────────────────────────────────────────────────────────────┤
│ {                                                                   │
│   ...                                                               │
│   "worker_results": {                                               │
│     "cost": {                                                       │
│       "response": "Costs increased by 45% due to...",               │
│       "confidence": 0.9,                                            │
│       "sources": ["fact_usage", "dim_sku"],                         │
│       "domain": "cost"                                              │
│     }                                                               │
│   }                                                                 │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    After synthesize_response                        │
├─────────────────────────────────────────────────────────────────────┤
│ {                                                                   │
│   ...                                                               │
│   "response": "Yesterday's costs spiked by 45% primarily due to...",│
│   "confidence": 0.9,                                                │
│   "sources": ["fact_usage", "dim_sku"],                             │
│   "messages": [                                                     │
│     HumanMessage(content="Why did costs..."),                       │
│     AIMessage(content="Yesterday's costs spiked...")                │
│   ]                                                                 │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Graph Compilation

### With Checkpointer

```python
# File: src/agents/orchestrator/agent.py
# Lines: 78-86

@property
def graph(self):
    """Lazily create the orchestrator graph."""
    if self._graph is None:
        workflow = create_orchestrator_graph()
        # Compile with checkpointer for state persistence
        with get_checkpoint_saver() as checkpointer:
            self._graph = workflow.compile(checkpointer=checkpointer)
    return self._graph
```

**Checkpointer Benefits:**
- Automatic state persistence after each node
- Conversation continuity via `thread_id`
- State recovery on failures

### Invocation Configuration

```python
# Thread-based config for memory
config = {
    "configurable": {
        "thread_id": thread_id,  # Required for checkpointing
    }
}

# Invoke the graph
result = graph.invoke(initial_state, config)
```

---

## 📊 Tracing Hierarchy

```
health_monitor_predict (AGENT)
├── load_context (MEMORY)
│   └── search_memories (RETRIEVER)
│
├── classify_intent_node (CLASSIFIER)
│   └── classify_intent (CLASSIFIER)
│       └── llm_invoke (LLM)
│
├── cost_agent_node (TOOL)
│   └── genie_query (TOOL)
│       └── GenieAgent.invoke (LLM)
│
└── synthesize_response (LLM)
    └── synthesize (LLM)
        └── llm_invoke (LLM)
```

---

## 🛠️ Extending the Graph

### Adding a New Node

```python
# 1. Define the node function
@mlflow.trace(name="my_new_node", span_type="TOOL")
def my_new_node(state: AgentState) -> Dict:
    """Process state and return updates."""
    # Your logic here
    return {"new_field": value}

# 2. Add to graph construction
workflow.add_node("my_new_node", my_new_node)

# 3. Connect with edges
workflow.add_edge("some_node", "my_new_node")
workflow.add_edge("my_new_node", "next_node")
```

### Adding Conditional Routing

```python
# Define routing function
def my_routing_function(state: AgentState) -> Literal["path_a", "path_b"]:
    if state.get("some_condition"):
        return "path_a"
    return "path_b"

# Add conditional edges
workflow.add_conditional_edges(
    "source_node",
    my_routing_function,
    {
        "path_a": "node_a",
        "path_b": "node_b",
    }
)
```

---

**Next:** [04-worker-agents-and-genie.md](./04-worker-agents-and-genie.md)

