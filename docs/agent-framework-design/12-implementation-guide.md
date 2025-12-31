# 12 - Implementation Guide

## Overview

This document provides a step-by-step implementation guide for the Health Monitor Multi-Agent System. Follow these phases in order for a successful deployment.

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Environment Setup | 2 days | Dependencies, Genie access, Lakebase tables |
| 2. Orchestrator Agent | 1 week | LangGraph supervisor, intent classification |
| 3. Worker Agents | 1 week | 5 domain specialists + Genie integration |
| 4. Utility Tools | 3 days | Web search, dashboard linker, RAG, alerts |
| 5. Memory Integration | 3 days | Lakebase short/long-term memory |
| 6. MLflow Integration | 1 week | Tracing, logging, prompt registry |
| 7. Evaluation Pipeline | 3 days | LLM judges, evaluation sets |
| 8. Deployment | 2 days | Model Serving, Apps frontend |
| **Total** | **~5 weeks** | Production-ready agent system |

## Phase 1: Environment Setup (2 Days)

### Day 1: Dependencies and Configuration

#### Step 1.1: Create Project Structure

```bash
# Create directory structure
mkdir -p src/agents/{orchestrator,workers,tools,memory}
mkdir -p src/agents/config
mkdir -p src/agents/prompts
mkdir -p tests/agents
mkdir -p evaluation_sets
```

#### Step 1.2: Install Dependencies

```python
# requirements.txt for agent system
mlflow>=3.0.0
langchain>=0.3.0
langgraph>=0.2.0
langchain-databricks>=0.1.0
databricks-sdk>=0.30.0
databricks-agents>=0.1.0
pydantic>=2.0.0
tavily-python>=0.3.0
streamlit>=1.30.0
pytest>=8.0.0
```

#### Step 1.3: Configure Environment Variables

```python
# src/agents/config/settings.py
import os
from dataclasses import dataclass

@dataclass
class AgentSettings:
    # Databricks
    databricks_host: str = os.environ.get("DATABRICKS_HOST", "")
    
    # LLM
    llm_endpoint: str = os.environ.get("LLM_ENDPOINT", "databricks-dbrx-instruct")
    llm_temperature: float = float(os.environ.get("LLM_TEMPERATURE", "0.3"))
    
    # Genie Spaces (from Phase 3.6)
    cost_genie_space_id: str = os.environ.get("COST_GENIE_SPACE_ID", "")
    security_genie_space_id: str = os.environ.get("SECURITY_GENIE_SPACE_ID", "")
    performance_genie_space_id: str = os.environ.get("PERFORMANCE_GENIE_SPACE_ID", "")
    reliability_genie_space_id: str = os.environ.get("RELIABILITY_GENIE_SPACE_ID", "")
    quality_genie_space_id: str = os.environ.get("QUALITY_GENIE_SPACE_ID", "")
    unified_genie_space_id: str = os.environ.get("UNIFIED_GENIE_SPACE_ID", "")
    
    # Memory
    short_term_memory_table: str = os.environ.get(
        "SHORT_TERM_MEMORY_TABLE", "health_monitor.memory.short_term"
    )
    long_term_memory_table: str = os.environ.get(
        "LONG_TERM_MEMORY_TABLE", "health_monitor.memory.long_term"
    )
    memory_ttl_hours: int = int(os.environ.get("MEMORY_TTL_HOURS", "24"))
    
    # Timeouts
    genie_timeout_seconds: int = int(os.environ.get("GENIE_TIMEOUT_SECONDS", "45"))
    agent_timeout_seconds: int = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "30"))
    
    # Utility tools
    tavily_api_key: str = os.environ.get("TAVILY_API_KEY", "")
    vector_search_endpoint: str = os.environ.get("VECTOR_SEARCH_ENDPOINT", "")

settings = AgentSettings()
```

### Day 2: Infrastructure Setup

#### Step 1.4: Create Lakebase Memory Tables

```sql
-- Run in Databricks SQL
-- Short-term memory table
CREATE TABLE IF NOT EXISTS health_monitor.memory.short_term (
    session_id STRING NOT NULL,
    user_id STRING NOT NULL,
    message_id STRING NOT NULL,
    role STRING NOT NULL,
    content STRING NOT NULL,
    metadata MAP<STRING, STRING>,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_short_term PRIMARY KEY (session_id, message_id)
)
USING DELTA
CLUSTER BY (session_id, user_id)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Long-term memory table
CREATE TABLE IF NOT EXISTS health_monitor.memory.long_term (
    user_id STRING NOT NULL PRIMARY KEY,
    preferences MAP<STRING, STRING>,
    frequent_queries ARRAY<STRING>,
    insights ARRAY<STRUCT<timestamp: TIMESTAMP, domain: STRING, insight: STRING>>,
    role STRING,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP
)
USING DELTA
CLUSTER BY (user_id);
```

#### Step 1.5: Verify Genie Space Access

```python
# src/agents/tools/verify_genie.py
from databricks.sdk import WorkspaceClient
from config.settings import settings

def verify_genie_access():
    """Verify access to all Genie Spaces."""
    client = WorkspaceClient()
    
    spaces = {
        "cost": settings.cost_genie_space_id,
        "security": settings.security_genie_space_id,
        "performance": settings.performance_genie_space_id,
        "reliability": settings.reliability_genie_space_id,
        "quality": settings.quality_genie_space_id,
        "unified": settings.unified_genie_space_id
    }
    
    results = {}
    for domain, space_id in spaces.items():
        try:
            # Try to access the space
            space = client.genie.get_space(space_id)
            results[domain] = {"status": "OK", "name": space.name}
        except Exception as e:
            results[domain] = {"status": "ERROR", "error": str(e)}
    
    return results

if __name__ == "__main__":
    results = verify_genie_access()
    for domain, result in results.items():
        print(f"{domain}: {result['status']}")
```

## Phase 2: Orchestrator Agent (1 Week)

### Step 2.1: Create Intent Classifier

```python
# src/agents/orchestrator/intent_classifier.py
from langchain_databricks import ChatDatabricks
from langchain.prompts import ChatPromptTemplate
import json
import mlflow
from config.settings import settings

INTENT_PROMPT = """You are an intent classifier for Databricks platform monitoring.

Analyze the user query and classify it into ONE OR MORE domains:

DOMAINS:
- COST: Billing, spending, DBU usage, budgets, chargeback
- SECURITY: Access control, audit logs, threats, compliance
- PERFORMANCE: Query speed, cluster utilization, latency
- RELIABILITY: Job failures, SLAs, incidents, pipelines
- QUALITY: Data quality, lineage, freshness, governance

Return JSON: {"domains": ["DOMAIN1"], "confidence": 0.XX}"""

class IntentClassifier:
    def __init__(self):
        self.llm = ChatDatabricks(
            endpoint=settings.llm_endpoint,
            temperature=0.1
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_PROMPT),
            ("human", "{query}")
        ])
        self.chain = self.prompt | self.llm
    
    @mlflow.trace(name="classify_intent", span_type="CLASSIFIER")
    def classify(self, query: str) -> dict:
        response = self.chain.invoke({"query": query})
        return json.loads(response.content)
```

### Step 2.2: Create LangGraph State Machine

```python
# src/agents/orchestrator/graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages
import mlflow

class AgentState(TypedDict):
    query: str
    user_id: str
    session_id: Optional[str]
    messages: Annotated[list, add_messages]
    intent: dict
    agent_responses: dict
    utility_results: dict
    synthesized_response: str
    sources: List[str]
    confidence: float

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
    workflow.add_node("synthesize", synthesize_response)
    workflow.add_node("save_context", save_context)
    
    # Define edges
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "classify_intent")
    workflow.add_edge("classify_intent", "route_to_agents")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "route_to_agents",
        determine_agents_to_invoke,
        {
            "cost_only": "cost_agent",
            "security_only": "security_agent",
            "performance_only": "performance_agent",
            "reliability_only": "reliability_agent",
            "quality_only": "quality_agent",
            "multi_agent": "cost_agent"
        }
    )
    
    # All agents lead to collect
    for agent in ["cost_agent", "security_agent", "performance_agent",
                  "reliability_agent", "quality_agent"]:
        workflow.add_edge(agent, "collect_responses")
    
    workflow.add_edge("collect_responses", "synthesize")
    workflow.add_edge("synthesize", "save_context")
    workflow.add_edge("save_context", END)
    
    return workflow.compile()
```

### Step 2.3: Implement Response Synthesizer

```python
# src/agents/orchestrator/synthesizer.py
from langchain_databricks import ChatDatabricks
from langchain.prompts import ChatPromptTemplate
import mlflow

SYNTHESIZER_PROMPT = """Combine responses from domain agents into a unified answer.

DOMAIN RESPONSES:
{agent_responses}

USER QUESTION:
{query}

Guidelines:
1. Start with direct answer
2. Integrate insights from each domain
3. Highlight cross-domain correlations
4. Provide actionable recommendations
5. Cite sources in [brackets]"""

class ResponseSynthesizer:
    def __init__(self):
        self.llm = ChatDatabricks(endpoint="databricks-dbrx-instruct", temperature=0.3)
        self.prompt = ChatPromptTemplate.from_template(SYNTHESIZER_PROMPT)
        self.chain = self.prompt | self.llm
    
    @mlflow.trace(name="synthesize", span_type="LLM")
    def synthesize(self, query: str, responses: dict) -> str:
        formatted = "\n\n".join([
            f"### {domain.upper()}:\n{resp.get('response', 'No data')}"
            for domain, resp in responses.items()
        ])
        
        result = self.chain.invoke({
            "agent_responses": formatted,
            "query": query
        })
        
        return result.content
```

## Phase 3: Worker Agents (1 Week)

### Step 3.1: Create Base Worker Agent

```python
# src/agents/workers/base.py
from abc import ABC, abstractmethod
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
import mlflow

class BaseWorkerAgent(ABC):
    def __init__(self, domain: str, genie_space_id: str):
        self.domain = domain
        self.genie_space_id = genie_space_id
        self.client = WorkspaceClient()
        self.genie = GenieAPI(self.client)
    
    @abstractmethod
    def enhance_query(self, query: str, context: dict) -> str:
        pass
    
    @mlflow.trace(span_type="AGENT")
    def query(self, question: str, context: dict = None) -> dict:
        enhanced = self.enhance_query(question, context or {})
        
        try:
            response = self.genie.start_conversation(
                space_id=self.genie_space_id,
                content=enhanced
            )
            
            # Wait for completion
            result = self._wait_for_completion(response)
            
            return {
                "response": result["content"],
                "sources": result["sources"],
                "confidence": 0.9,
                "domain": self.domain
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "domain": self.domain,
                "error": str(e)
            }
```

### Step 3.2: Implement Domain Agents

```python
# src/agents/workers/cost_agent.py
from .base import BaseWorkerAgent
from config.settings import settings

class CostWorkerAgent(BaseWorkerAgent):
    def __init__(self):
        super().__init__("cost", settings.cost_genie_space_id)
    
    def enhance_query(self, query: str, context: dict) -> str:
        enhanced = query
        if "threshold" in context:
            enhanced += f" Flag costs exceeding ${context['threshold']}"
        if "workspace" in context:
            enhanced += f" Focus on workspace: {context['workspace']}"
        return enhanced

# src/agents/workers/security_agent.py
class SecurityWorkerAgent(BaseWorkerAgent):
    def __init__(self):
        super().__init__("security", settings.security_genie_space_id)
    
    def enhance_query(self, query: str, context: dict) -> str:
        if "sensitive" in query.lower():
            return f"{query} Include data classification tags."
        return query

# Similar for performance, reliability, quality agents...
```

## Phase 4: Utility Tools (3 Days)

### Step 4.1: Web Search Tool

```python
# src/agents/tools/web_search.py
from tavily import TavilyClient
from config.settings import settings
import mlflow

class WebSearchTool:
    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)
        self.trusted_domains = [
            "docs.databricks.com",
            "status.databricks.com"
        ]
    
    @mlflow.trace(name="web_search", span_type="TOOL")
    def search(self, query: str, max_results: int = 5) -> dict:
        response = self.client.search(
            query=query,
            max_results=max_results,
            include_domains=self.trusted_domains
        )
        return {
            "results": response.get("results", []),
            "answer": response.get("answer", "")
        }

web_search = WebSearchTool()
```

### Step 4.2: Dashboard Linker Tool

```python
# src/agents/tools/dashboard_linker.py
from config.settings import settings

class DashboardLinkerTool:
    DASHBOARDS = {
        "cost": {"id": "cost_dashboard_id", "name": "Cost Analysis"},
        "security": {"id": "security_dashboard_id", "name": "Security Posture"},
        "performance": {"id": "perf_dashboard_id", "name": "Query Performance"},
        "reliability": {"id": "jobs_dashboard_id", "name": "Job Operations"},
        "quality": {"id": "quality_dashboard_id", "name": "Data Quality"}
    }
    
    def get_dashboard(self, domains: list) -> dict:
        # Find best matching dashboard
        for domain in domains:
            if domain in self.DASHBOARDS:
                dash = self.DASHBOARDS[domain]
                return {
                    "name": dash["name"],
                    "url": f"{settings.databricks_host}/sql/dashboards/{dash['id']}"
                }
        return {"name": "Platform Overview", "url": f"{settings.databricks_host}/sql/dashboards/overview"}

dashboard_linker = DashboardLinkerTool()
```

## Phase 5: Memory Integration (3 Days)

### Step 5.1: Implement Memory Classes

See [07-Memory Management](07-memory-management.md) for complete implementation.

```python
# src/agents/memory/short_term.py
# src/agents/memory/long_term.py
# Implementation as documented in memory management guide
```

## Phase 6: MLflow Integration (1 Week)

### Step 6.1: Enable Tracing

```python
# src/agents/__init__.py
import mlflow

# Enable autolog at module load
mlflow.langchain.autolog(
    log_models=True,
    log_input_examples=True,
    log_model_signatures=True
)

# Set experiment
mlflow.set_experiment("/Shared/health_monitor/agent_traces")
```

### Step 6.2: Register Prompts

```python
# src/agents/prompts/register.py
import mlflow.genai

def register_all_prompts():
    prompts = {
        "orchestrator": ORCHESTRATOR_PROMPT,
        "intent_classifier": INTENT_PROMPT,
        "synthesizer": SYNTHESIZER_PROMPT
    }
    
    for name, content in prompts.items():
        mlflow.genai.log_prompt(
            prompt=content,
            artifact_path=f"prompts/{name}",
            registered_model_name=f"health_monitor_{name}_prompt"
        )
```

### Step 6.3: Log Agent

```python
# src/agents/logging/log_agent.py
import mlflow

def log_agent(agent, version: str):
    mlflow.models.set_model(agent)
    
    with mlflow.start_run(run_name=f"health_monitor_agent_{version}"):
        mlflow.langchain.log_model(
            lc_model=agent.orchestrator_graph,
            artifact_path="orchestrator",
            registered_model_name="health_monitor_orchestrator",
            pip_requirements=["mlflow>=3.0.0", "langchain>=0.3.0", "langgraph>=0.2.0"]
        )
```

## Phase 7: Evaluation Pipeline (3 Days)

### Step 7.1: Create Evaluation Set

```python
# evaluation_sets/create_eval_set.py
import pandas as pd

eval_data = pd.DataFrame([
    {"query": "Why did costs spike yesterday?", "category": "cost"},
    {"query": "Who accessed sensitive data?", "category": "security"},
    {"query": "What are the slowest queries?", "category": "performance"},
    {"query": "Which jobs failed today?", "category": "reliability"},
    {"query": "Which tables have quality issues?", "category": "quality"},
    {"query": "Are expensive jobs also failing?", "category": "multi_domain"}
])

eval_data.to_parquet("evaluation_sets/health_monitor_eval.parquet")
```

### Step 7.2: Run Evaluation

```python
# src/agents/evaluation/run_eval.py
import mlflow.genai
from mlflow.genai.scorers import Relevance, Safety, Correctness

def run_evaluation(agent, eval_data):
    results = mlflow.genai.evaluate(
        model=agent,
        data=eval_data,
        scorers=[Relevance(), Safety(), Correctness()]
    )
    
    print(f"Relevance: {results.metrics['relevance/mean']:.2%}")
    print(f"Safety: {results.metrics['safety/mean']:.2%}")
    
    return results
```

## Phase 8: Deployment (2 Days)

### Step 8.1: Create Model Serving Endpoint

See [13-Deployment and Monitoring](13-deployment-and-monitoring.md) for complete setup.

### Step 8.2: Deploy Databricks App

```python
# src/frontend_app/app.py
import streamlit as st
from databricks.sdk import WorkspaceClient

st.title("Databricks Health Monitor")

# Initialize client
client = WorkspaceClient()

# Chat interface
if prompt := st.chat_input("Ask about costs, jobs, security..."):
    response = client.serving_endpoints.query(
        name="health_monitor_orchestrator",
        inputs={"messages": [{"role": "user", "content": prompt}]}
    )
    st.write(response["response"])
```

## Validation Checklist

### Phase 1 Completion
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Memory tables created
- [ ] Genie Space access verified

### Phase 2-3 Completion
- [ ] Intent classifier working (>90% accuracy on test set)
- [ ] LangGraph state machine compiles
- [ ] All 5 worker agents querying Genie successfully
- [ ] Response synthesizer producing coherent responses

### Phase 4-5 Completion
- [ ] Web search returning results
- [ ] Dashboard linker generating correct URLs
- [ ] Memory save/retrieve working
- [ ] Context injection into prompts

### Phase 6-7 Completion
- [ ] MLflow traces appearing in UI
- [ ] Prompts registered in registry
- [ ] Agent logged to Model Registry
- [ ] Evaluation metrics >80% relevance

### Phase 8 Completion
- [ ] Model Serving endpoint deployed
- [ ] Endpoint responding to queries
- [ ] Databricks App accessible
- [ ] End-to-end test passing

## Next Steps

- **[13-Deployment and Monitoring](13-deployment-and-monitoring.md)**: Production deployment details

