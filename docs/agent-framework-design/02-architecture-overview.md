# 02 - Architecture Overview

> **✅ Implementation Status**: See `src/agents/orchestrator/graph.py` for the actual LangGraph implementation.
> Key differences from this design:
> - Memory uses Lakebase `CheckpointSaver` and `DatabricksStore` (not custom Delta tables)
> - Worker agents use `GenieWorkerAgent` base class with placeholder Genie Space IDs
> - Graph has simplified routing via `add_conditional_edges`

## System Architecture

The Databricks Health Monitor Agent System uses a **hierarchical multi-agent architecture** with a custom LangGraph orchestrator supervising domain-specific worker agents. All data access flows through Genie Spaces.

```mermaid
graph TB
    subgraph UserInterface [User Interface Layer]
        UI[Databricks Apps<br/>Streamlit Chat]
    end
    
    subgraph Serving [Model Serving Layer]
        MS[Model Serving Endpoint<br/>health_monitor_orchestrator]
    end
    
    subgraph Orchestrator [Orchestrator Layer]
        OA[Orchestrator Agent<br/>LangGraph Supervisor]
        IC[Intent Classifier]
        RS[Response Synthesizer]
    end
    
    subgraph Workers [Worker Agent Layer]
        CA[Cost Agent]
        SA[Security Agent]
        PA[Performance Agent]
        RA[Reliability Agent]
        QA[Quality Agent]
    end
    
    subgraph Genie [Genie Space Layer]
        CG[Cost Intelligence<br/>Genie Space]
        SG[Security Auditor<br/>Genie Space]
        PG[Performance<br/>Genie Space]
        RG[Job Health<br/>Genie Space]
        QG[Data Quality<br/>Genie Space]
        UG[Unified Health<br/>Genie Space]
    end
    
    subgraph DataAssets [Data Assets - Abstracted Behind Genie]
        TVF[60 TVFs]
        MV[10 Metric Views]
        ML[25 ML Models]
        LM[10 Lakehouse Monitors]
    end
    
    subgraph Utility [Utility Tools]
        WS[Web Search]
        DL[Dashboard Linker]
        AT[Alert Trigger]
        RR[Runbook RAG]
    end
    
    subgraph Memory [Memory Layer]
        STM[Short-Term Memory<br/>Lakebase 24h]
        LTM[Long-Term Memory<br/>Lakebase 1yr]
    end
    
    subgraph MLflow [MLflow Layer]
        TR[Tracing]
        PR[Prompt Registry]
        MR[Model Registry]
        EV[Evaluation]
    end
    
    UI --> MS
    MS --> OA
    OA --> IC
    OA --> RS
    IC --> CA & SA & PA & RA & QA
    CA --> CG
    SA --> SG
    PA --> PG
    RA --> RG
    QA --> QG
    OA --> UG
    CG & SG & PG & RG & QG & UG --> TVF & MV & ML & LM
    OA --> WS & DL & AT & RR
    OA --> STM & LTM
    OA --> TR & PR
    MS --> MR
    EV --> TR
```

## Data Flow

### Query Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Databricks App
    participant MS as Model Serving
    participant O as Orchestrator
    participant IC as Intent Classifier
    participant W as Worker Agent
    participant G as Genie Space
    participant D as Data Assets
    participant M as Memory
    participant T as MLflow Tracing
    
    U->>UI: "Why did costs spike last Tuesday?"
    UI->>MS: POST /invocations
    MS->>O: invoke(query, user_id)
    
    Note over O,T: Start MLflow Trace
    O->>T: mlflow.start_span("orchestrator")
    
    O->>M: Retrieve conversation history
    M-->>O: Previous 10 messages
    
    O->>IC: Classify intent
    IC-->>O: {domains: ["cost"], confidence: 0.95}
    
    O->>W: Route to Cost Agent
    W->>G: Natural language query
    
    Note over G,D: Genie internally routes
    G->>D: Execute TVF/Query Metric View
    D-->>G: Structured data
    G-->>W: Formatted response
    
    W-->>O: Domain response
    O->>O: Synthesize final response
    
    O->>M: Save conversation turn
    O->>T: End trace with tags
    
    O-->>MS: {response, sources, confidence}
    MS-->>UI: JSON response
    UI-->>U: Rendered answer with citations
```

### Multi-Domain Query Flow

For queries spanning multiple domains (e.g., "Are expensive jobs also the ones failing?"):

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant IC as Intent Classifier
    participant CA as Cost Agent
    participant RA as Reliability Agent
    participant CG as Cost Genie
    participant RG as Reliability Genie
    participant S as Synthesizer
    
    O->>IC: Classify intent
    IC-->>O: {domains: ["cost", "reliability"], confidence: 0.88}
    
    par Parallel Agent Execution
        O->>CA: Query cost data
        CA->>CG: "What are the most expensive jobs?"
        CG-->>CA: Top 10 expensive jobs
        CA-->>O: Cost response
    and
        O->>RA: Query reliability data
        RA->>RG: "What jobs are failing most?"
        RG-->>RA: Top 10 failing jobs
        RA-->>O: Reliability response
    end
    
    O->>S: Combine responses
    S->>S: Correlate expensive jobs with failures
    S-->>O: Synthesized insight
```

## Component Architecture

### Orchestrator Agent

The orchestrator is the brain of the system, implemented as a LangGraph state machine:

```mermaid
stateDiagram-v2
    [*] --> LoadContext: Start
    LoadContext --> ClassifyIntent: Load user preferences
    ClassifyIntent --> CostAgent: domain=cost
    ClassifyIntent --> SecurityAgent: domain=security
    ClassifyIntent --> PerformanceAgent: domain=performance
    ClassifyIntent --> ReliabilityAgent: domain=reliability
    ClassifyIntent --> QualityAgent: domain=quality
    ClassifyIntent --> ParallelAgents: multi-domain

    CostAgent --> Synthesize
    SecurityAgent --> Synthesize
    PerformanceAgent --> Synthesize
    ReliabilityAgent --> Synthesize
    QualityAgent --> Synthesize
    ParallelAgents --> Synthesize

    Synthesize --> SaveContext: Combine responses
    SaveContext --> [*]: Return
```

> **Implementation Note**: The actual implementation in `src/agents/orchestrator/graph.py` uses `add_conditional_edges` for routing and does not have separate `RouteToWorker` or `CollectResponses` nodes.

### Worker Agent Design

Each worker agent follows a consistent interface:

```mermaid
classDiagram
    class WorkerAgent {
        <<interface>>
        +domain: str
        +genie_space_id: str
        +query(question: str, context: dict) dict
        +format_response(genie_response: dict) str
    }
    
    class CostAgent {
        +domain = "cost"
        +genie_space_id = "cost_intelligence"
        +query(question, context)
        +format_response(response)
    }
    
    class SecurityAgent {
        +domain = "security"
        +genie_space_id = "security_auditor"
        +query(question, context)
        +format_response(response)
    }
    
    class PerformanceAgent {
        +domain = "performance"
        +genie_space_id = "performance_optimizer"
        +query(question, context)
        +format_response(response)
    }
    
    class ReliabilityAgent {
        +domain = "reliability"
        +genie_space_id = "job_health_monitor"
        +query(question, context)
        +format_response(response)
    }
    
    class QualityAgent {
        +domain = "quality"
        +genie_space_id = "data_quality_monitor"
        +query(question, context)
        +format_response(response)
    }
    
    WorkerAgent <|-- CostAgent
    WorkerAgent <|-- SecurityAgent
    WorkerAgent <|-- PerformanceAgent
    WorkerAgent <|-- ReliabilityAgent
    WorkerAgent <|-- QualityAgent
```

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Orchestration** | LangGraph | 0.2+ | State machine for multi-agent coordination |
| **LLM** | DBRX Instruct | Latest | Intent classification, synthesis |
| **LLM (Fallback)** | Llama 3.1 70B | Latest | Worker agent responses |
| **Framework** | LangChain | 0.3+ | Agent primitives, tool integration |
| **Data Access** | Genie API | Latest | Natural language data queries |
| **Memory** | Lakebase | Latest | Short-term and long-term storage |
| **Tracing** | MLflow 3.0 | 3.0+ | Observability and debugging |
| **Deployment** | Model Serving | Serverless | Production endpoint |
| **Frontend** | Databricks Apps | Latest | Chat interface |

### Python Dependencies

```python
# requirements.txt
mlflow>=3.0.0
langchain>=0.3.0
langgraph>=0.2.0
langchain-databricks>=0.1.0
databricks-sdk>=0.30.0
databricks-agents>=0.1.0
pydantic>=2.0.0
streamlit>=1.30.0
tavily-python>=0.3.0  # For web search
```

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant App as Databricks App
    participant MS as Model Serving
    participant Agent as Agent
    participant Genie as Genie Space
    participant UC as Unity Catalog
    
    U->>App: Login (SSO/OAuth)
    App->>App: Obtain user token
    App->>MS: Request with user token
    MS->>Agent: Pass user context
    Agent->>Genie: Query with on-behalf-of-user
    Genie->>UC: Check permissions
    UC-->>Genie: Allowed tables/columns
    Genie-->>Agent: Filtered response
    Agent-->>MS: Response
    MS-->>App: Response
    App-->>U: Display (respects permissions)
```

### Key Security Features

| Feature | Implementation |
|---------|----------------|
| **On-behalf-of-user Auth** | Genie queries execute with user's permissions |
| **Unity Catalog Governance** | Row/column-level security enforced |
| **Secrets Management** | API keys in Databricks Secrets |
| **Audit Logging** | All queries logged via MLflow traces |
| **Rate Limiting** | Model Serving endpoint limits |

## Scalability Considerations

### Horizontal Scaling

```mermaid
graph LR
    subgraph LoadBalancer [Load Balancer]
        LB[Model Serving]
    end
    
    subgraph Replicas [Agent Replicas]
        R1[Replica 1]
        R2[Replica 2]
        R3[Replica 3]
    end
    
    subgraph Shared [Shared State]
        M[Lakebase Memory]
        T[MLflow Tracking]
    end
    
    LB --> R1 & R2 & R3
    R1 & R2 & R3 --> M
    R1 & R2 & R3 --> T
```

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Latency (P50) | <5s | Single-domain queries |
| Latency (P95) | <10s | Multi-domain queries |
| Throughput | 100 req/min | Per endpoint |
| Concurrent Users | 50 | Via Model Serving |
| Memory per Request | <512MB | LangGraph state |

## Error Handling

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Genie timeout | 30s timeout | Retry with simpler query |
| LLM rate limit | 429 response | Exponential backoff |
| Memory unavailable | Connection error | Proceed without context |
| Worker agent error | Exception | Log and skip domain |
| Utility tool error | Exception | Return partial response |

### Graceful Degradation

```python
# Pseudo-code for error handling
def orchestrate(query: str, user_id: str) -> dict:
    try:
        # Normal flow
        intent = classify_intent(query)
        responses = await gather_worker_responses(intent.domains)
        return synthesize(responses)
    except GenieTimeoutError:
        # Fallback to unified Genie with simpler query
        return unified_genie.query(simplify(query))
    except MemoryUnavailableError:
        # Proceed without conversation history
        return orchestrate_stateless(query)
    except Exception as e:
        # Log error and return apologetic response
        mlflow.log_metric("error_count", 1)
        return {"response": "I encountered an issue. Please try again."}
```

## Next Steps

- **[03-Orchestrator Agent](03-orchestrator-agent.md)**: Detailed orchestrator implementation
- **[04-Worker Agents](04-worker-agents.md)**: Domain specialist agent details
- **[05-Genie Integration](05-genie-integration.md)**: Genie API patterns

