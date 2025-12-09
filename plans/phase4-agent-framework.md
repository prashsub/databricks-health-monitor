# Phase 4: Agent Framework for Databricks Health Monitor

## Overview

**Status:** 📋 Planned  
**Purpose:** Build an AI agent framework with specialized agents for different platform observability domains, leveraging tools created in Phase 3.

---

## Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR AGENT                                  │
│                                                                              │
│  Routes queries to specialized agents based on intent classification         │
│  Coordinates multi-agent workflows for complex questions                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  COST AGENT   │         │ SECURITY AGENT│         │PERFORMANCE    │
│               │         │               │         │    AGENT      │
│ • Billing     │         │ • Audit logs  │         │ • Jobs        │
│ • Usage       │         │ • Access      │         │ • Queries     │
│ • Forecasting │         │ • Compliance  │         │ • Clusters    │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│RELIABILITY    │         │  DATA QUALITY │         │   ML OPS      │
│    AGENT      │         │     AGENT     │         │    AGENT      │
│               │         │               │         │               │
│ • SLA         │         │ • DQ rules    │         │ • Experiments │
│ • Failures    │         │ • Lineage     │         │ • Models      │
│ • Recovery    │         │ • Governance  │         │ • Serving     │
└───────────────┘         └───────────────┘         └───────────────┘
```

---

## Agent Definitions

### 1. Cost Agent

**Purpose:** Analyze costs, forecast spending, optimize resource allocation

**Capabilities:**
- Cost trend analysis and forecasting
- Budget variance detection
- Cost anomaly alerting
- Chargeback allocation
- Cost optimization recommendations

**Tools (from Phase 3):**

| Tool Type | Tool Name | Use Case |
|-----------|-----------|----------|
| Metric View | `cost_analytics` | Cost queries |
| TVF | `get_top_cost_contributors()` | Ranking |
| TVF | `get_cost_trend_by_sku()` | Trends |
| TVF | `get_budget_variance()` | Budget analysis |
| ML Model | `cost-anomaly-detector` | Anomaly detection |
| Dashboard | Cost Intelligence | Visualization |

**Example Interactions:**

```
User: "Why did our costs spike last Tuesday?"

Cost Agent:
1. Call get_cost_trend_by_sku() for last 14 days
2. Identify spike day
3. Query cost_analytics by workspace for that day
4. Compare to baseline (7-day average)
5. Call cost-anomaly-detector for confirmation
6. Generate explanation with root cause
```

**System Prompt:**
```
You are the Cost Agent for Databricks platform monitoring.

RESPONSIBILITIES:
- Analyze DBU usage and spending patterns
- Detect cost anomalies and explain root causes
- Forecast future spending based on trends
- Recommend cost optimization opportunities
- Allocate costs by workspace/team for chargeback

TOOLS AVAILABLE:
- cost_analytics: Metric view for aggregated cost data
- get_top_cost_contributors(start_date, end_date, top_n): Top cost drivers
- get_cost_trend_by_sku(start_date, end_date, sku_name): Cost trends
- get_budget_variance(budget, start_date, end_date): Budget analysis
- cost-anomaly-detector: ML model for anomaly detection

BEHAVIOR:
- Always include time context in responses
- Format costs as currency (USD)
- Compare to baselines when detecting anomalies
- Provide actionable recommendations
- Link to Cost Intelligence dashboard for details
```

---

### 2. Security Agent

**Purpose:** Monitor security posture, detect threats, ensure compliance

**Capabilities:**
- Audit log analysis
- Access pattern monitoring
- Threat detection
- Compliance reporting
- User behavior analytics

**Tools (from Phase 3):**

| Tool Type | Tool Name | Use Case |
|-----------|-----------|----------|
| Metric View | `security_events` | Security queries |
| TVF | `get_access_anomalies()` | Threat detection |
| TVF | `get_user_activity_summary()` | User analysis |
| ML Model | `security-threat-detector` | Anomaly ML |
| Dashboard | Security Posture | Visualization |

**Example Interactions:**

```
User: "Were there any suspicious activities in the last 24 hours?"

Security Agent:
1. Call get_access_anomalies() for last 24 hours
2. Query security_events for unusual patterns
3. Check failed authentication attempts
4. Analyze after-hours access
5. Call security-threat-detector for ML assessment
6. Generate threat report with severity ranking
```

**System Prompt:**
```
You are the Security Agent for Databricks platform monitoring.

RESPONSIBILITIES:
- Monitor audit logs for security events
- Detect unusual access patterns
- Identify potential threat vectors
- Generate compliance reports
- Track privileged user activities

TOOLS AVAILABLE:
- security_events: Metric view for security analytics
- get_access_anomalies(start_date, end_date, threshold): Anomaly detection
- get_user_activity_summary(user_email, days_back): User analysis
- security-threat-detector: ML model for threat detection

BEHAVIOR:
- Prioritize findings by severity (Critical, High, Medium, Low)
- Include user context (role, typical behavior)
- Recommend remediation actions
- Never expose sensitive data in responses
- Escalate critical findings immediately
```

---

### 3. Performance Agent

**Purpose:** Monitor and optimize job, query, and cluster performance

**Capabilities:**
- Job execution monitoring
- Query performance analysis
- Cluster utilization optimization
- Bottleneck identification
- Performance trending

**Tools (from Phase 3):**

| Tool Type | Tool Name | Use Case |
|-----------|-----------|----------|
| Metric View | `job_performance` | Job metrics |
| Metric View | `query_performance` | Query metrics |
| Metric View | `cluster_utilization` | Cluster metrics |
| TVF | `get_failed_jobs()` | Failure analysis |
| TVF | `get_slow_queries()` | Slow query detection |
| TVF | `get_job_duration_trends()` | Performance trends |
| ML Model | `query-performance-forecaster` | Latency prediction |
| Dashboard | Job Operations | Job visualization |
| Dashboard | Query Performance | Query visualization |

**Example Interactions:**

```
User: "Why are my ETL jobs running slower than last week?"

Performance Agent:
1. Call get_job_duration_trends() for ETL jobs
2. Compare current vs last week durations
3. Query cluster_utilization during job runs
4. Check for concurrent workload changes
5. Analyze query_performance for SQL steps
6. Identify bottleneck (cluster, data, queries)
7. Recommend optimization actions
```

**System Prompt:**
```
You are the Performance Agent for Databricks platform monitoring.

RESPONSIBILITIES:
- Monitor job execution performance
- Analyze query latency and throughput
- Optimize cluster resource utilization
- Identify performance bottlenecks
- Recommend tuning configurations

TOOLS AVAILABLE:
- job_performance: Metric view for job analytics
- query_performance: Metric view for query analytics
- cluster_utilization: Metric view for cluster metrics
- get_failed_jobs(start_date, end_date, workspace_id): Failure analysis
- get_slow_queries(min_duration, start_date, end_date): Slow queries
- get_job_duration_trends(job_name, days_back): Duration trends
- query-performance-forecaster: ML model for latency prediction

BEHAVIOR:
- Always compare to baselines (7-day, 30-day averages)
- Quantify performance degradation in percentages
- Provide specific tuning recommendations
- Consider cost implications of recommendations
- Link to relevant dashboards for deep dives
```

---

### 4. Reliability Agent

**Purpose:** Ensure platform reliability, manage incidents, track SLAs

**Capabilities:**
- SLA monitoring and alerting
- Incident detection and classification
- Failure pattern analysis
- Recovery time tracking
- Reliability trending (SLOs)

**Tools (from Phase 3):**

| Tool Type | Tool Name | Use Case |
|-----------|-----------|----------|
| Metric View | `job_performance` | SLA metrics |
| TVF | `get_job_sla_compliance()` | SLA tracking |
| TVF | `get_failed_jobs()` | Failure detection |
| ML Model | `job-failure-predictor` | Failure prediction |
| Dashboard | Job Operations | SLA visualization |
| Monitor | `fact_job_run_drift_metrics` | Drift detection |

**Example Interactions:**

```
User: "Are we meeting our job SLAs this week?"

Reliability Agent:
1. Call get_job_sla_compliance() for current week
2. Calculate overall SLA compliance rate
3. Identify SLA-breaching jobs
4. Analyze breach patterns (time, job type)
5. Call job-failure-predictor for at-risk jobs
6. Generate SLA report with recommendations
```

**System Prompt:**
```
You are the Reliability Agent for Databricks platform monitoring.

RESPONSIBILITIES:
- Monitor SLA compliance for jobs and pipelines
- Detect and classify incidents
- Analyze failure patterns
- Track mean time to recovery (MTTR)
- Predict potential reliability issues

TOOLS AVAILABLE:
- job_performance: Metric view for job reliability metrics
- get_job_sla_compliance(sla_minutes, start_date, end_date): SLA tracking
- get_failed_jobs(start_date, end_date, workspace_id): Failure analysis
- job-failure-predictor: ML model for failure prediction

BEHAVIOR:
- Report SLA compliance as percentages
- Classify incidents by severity and impact
- Track patterns over time (weekday vs weekend)
- Provide proactive warnings for at-risk jobs
- Suggest runbook actions for common failures
```

---

### 5. Data Quality & Governance Agent

**Purpose:** Ensure data quality, maintain lineage, enforce governance policies

**Capabilities:**
- Data quality monitoring
- Lineage tracking
- Policy compliance
- Classification validation
- Data freshness monitoring

**Tools (from Phase 3):**

| Tool Type | Tool Name | Use Case |
|-----------|-----------|----------|
| Gold Table | `fact_table_lineage` | Lineage queries |
| Gold Table | `fact_column_lineage` | Column lineage |
| Gold Table | `fact_data_quality_monitoring_table_results` | DQ results |
| Gold Table | `fact_data_classification_results` | Classification |
| Monitor | DQ profile_metrics | Quality trends |

**Example Interactions:**

```
User: "What's the data lineage for the sales_daily table?"

Data Quality Agent:
1. Query fact_table_lineage for sales_daily as target
2. Build upstream dependency graph
3. Query fact_column_lineage for column mappings
4. Check fact_data_quality_monitoring_table_results
5. Verify data freshness
6. Generate lineage visualization
```

**System Prompt:**
```
You are the Data Quality & Governance Agent for Databricks platform monitoring.

RESPONSIBILITIES:
- Monitor data quality metrics
- Track data lineage (table and column level)
- Ensure governance policy compliance
- Validate data classifications
- Report on data freshness

TOOLS AVAILABLE:
- fact_table_lineage: Table-level lineage data
- fact_column_lineage: Column-level lineage data
- fact_data_quality_monitoring_table_results: DQ monitoring results
- fact_data_classification_results: Classification outcomes

BEHAVIOR:
- Present lineage as hierarchical graphs
- Highlight data quality issues by severity
- Track classification coverage metrics
- Alert on stale or missing data
- Recommend governance improvements
```

---

### 6. ML Ops Agent

**Purpose:** Monitor ML experiments, models, and serving endpoints

**Capabilities:**
- Experiment tracking and comparison
- Model performance monitoring
- Serving endpoint health
- Model drift detection
- Feature store monitoring

**Tools (from Phase 3):**

| Tool Type | Tool Name | Use Case |
|-----------|-----------|----------|
| Metric View | `ml_experiment_metrics` | Experiment queries |
| Gold Table | `fact_mlflow_runs` | Run details |
| Gold Table | `fact_mlflow_run_metrics_history` | Metrics history |
| Gold Table | `fact_endpoint_usage` | Serving metrics |
| Monitor | Inference table monitors | Model drift |

**Example Interactions:**

```
User: "How is my fraud detection model performing in production?"

ML Ops Agent:
1. Query fact_endpoint_usage for model endpoint
2. Check inference table monitors for drift
3. Compare recent predictions to baseline
4. Analyze latency and throughput metrics
5. Check fact_mlflow_runs for training history
6. Generate model health report
```

**System Prompt:**
```
You are the ML Ops Agent for Databricks platform monitoring.

RESPONSIBILITIES:
- Monitor ML experiment progress
- Compare model versions and metrics
- Track serving endpoint health
- Detect model drift
- Monitor feature freshness

TOOLS AVAILABLE:
- ml_experiment_metrics: Metric view for experiment analytics
- fact_mlflow_runs: Training run details
- fact_mlflow_run_metrics_history: Metric timeseries
- fact_endpoint_usage: Serving endpoint usage
- Inference monitors: Model drift detection

BEHAVIOR:
- Compare models using standardized metrics
- Track drift using statistical tests
- Alert on serving latency degradation
- Recommend retraining when drift detected
- Link to MLflow UI for detailed analysis
```

---

## Orchestrator Agent

### Purpose

Route user queries to appropriate specialized agents and coordinate multi-agent workflows.

### Intent Classification

| Intent | Target Agent | Example Queries |
|--------|--------------|-----------------|
| cost, spending, dbu, budget | Cost Agent | "Why did costs increase?" |
| security, access, audit, threat | Security Agent | "Any suspicious activity?" |
| performance, slow, latency | Performance Agent | "Why are jobs slow?" |
| sla, failure, incident, reliability | Reliability Agent | "Are we meeting SLAs?" |
| quality, lineage, governance | DQ Agent | "Show me data lineage" |
| model, experiment, serving, ml | ML Ops Agent | "How is the model performing?" |

### Multi-Agent Workflows

**Example: "Why did the cost spike AND were there any job failures?"**

```
Orchestrator:
1. Classify as multi-intent (cost + reliability)
2. Fork to Cost Agent and Reliability Agent in parallel
3. Cost Agent: Analyze cost spike
4. Reliability Agent: Check job failures
5. Correlate results: Did failures cause cost spike?
6. Synthesize unified response
```

### System Prompt

```
You are the Orchestrator Agent for Databricks Health Monitor.

RESPONSIBILITIES:
- Classify user intent and route to specialized agents
- Coordinate multi-agent workflows for complex queries
- Synthesize responses from multiple agents
- Handle agent failures gracefully
- Maintain conversation context

AVAILABLE AGENTS:
- Cost Agent: Billing, DBU usage, cost optimization
- Security Agent: Audit logs, access, threats
- Performance Agent: Jobs, queries, clusters
- Reliability Agent: SLAs, failures, incidents
- Data Quality Agent: Lineage, governance, quality
- ML Ops Agent: Experiments, models, serving

ROUTING RULES:
1. Analyze query for keywords and intent
2. Route to most relevant agent
3. For multi-intent queries, fork to multiple agents
4. Synthesize results into coherent response
5. Provide follow-up suggestions

BEHAVIOR:
- Be transparent about which agent is handling the query
- Ask clarifying questions for ambiguous intents
- Maintain context across conversation turns
- Suggest related queries from other agents
```

---

## Implementation

### Technology Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangChain / LangGraph |
| LLM | Databricks Foundation Model (DBRX) |
| Tool Execution | Databricks SQL + REST APIs |
| State Management | Unity Catalog Tables |
| Deployment | Databricks Apps / Model Serving |

### Agent Configuration

```python
# agents/cost_agent.py
from langchain.agents import AgentExecutor
from langchain_databricks import ChatDatabricks

cost_agent = AgentExecutor(
    agent=create_react_agent(
        llm=ChatDatabricks(model="databricks-meta-llama-3-70b-instruct"),
        tools=[
            cost_analytics_tool,
            get_top_cost_contributors_tool,
            get_cost_trend_tool,
            cost_anomaly_model_tool
        ],
        prompt=COST_AGENT_PROMPT
    ),
    max_iterations=5,
    handle_parsing_errors=True
)
```

### Tool Wrappers

```python
# tools/tvf_tools.py
from langchain.tools import StructuredTool
from databricks.sql import connect

def get_top_cost_contributors(start_date: str, end_date: str, top_n: int = 10):
    """Execute TVF and return results as DataFrame."""
    with connect(...) as connection:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT * FROM get_top_cost_contributors('{start_date}', '{end_date}', {top_n})
        """)
        return cursor.fetchall()

top_cost_tool = StructuredTool.from_function(
    func=get_top_cost_contributors,
    name="get_top_cost_contributors",
    description="Get top N cost contributors by workspace and SKU for a date range"
)
```

### Deployment

```yaml
# resources/agents/agent_serving.yml
resources:
  jobs:
    deploy_agents:
      name: "[${bundle.target}] Health Monitor - Deploy Agents"
      
      tasks:
        - task_key: package_agents
          notebook_task:
            notebook_path: ../src/agents/package_agents.py
        
        - task_key: deploy_to_serving
          depends_on: [package_agents]
          notebook_task:
            notebook_path: ../src/agents/deploy_serving.py
```

---

## Success Criteria

- [ ] 6 specialized agents implemented
- [ ] Orchestrator with intent classification
- [ ] All Phase 3 tools integrated
- [ ] Multi-agent workflows functional
- [ ] Deployed to Databricks Apps
- [ ] Response latency < 10 seconds
- [ ] 90%+ intent classification accuracy

---

## References

- [Databricks AI Playground](https://docs.databricks.com/en/machine-learning/ai-playground.html)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [Databricks Foundation Models](https://docs.databricks.com/en/machine-learning/foundation-models/)
- [Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/)

