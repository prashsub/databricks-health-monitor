# 06 - Utility Tools

## Overview

Beyond Genie Spaces for data queries, agents have access to 4 utility tools for actions and external data retrieval. These tools complement Genie's data capabilities with real-time information, dashboard navigation, alerting, and documentation retrieval.

## Tool Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UTILITY TOOLS (4 Total)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. WEB SEARCH TOOL                                                   │   │
│  │    Purpose: Real-time information from the web                       │   │
│  │    • Databricks status page (outages, maintenance)                   │   │
│  │    • Documentation lookups (how-to guides)                           │   │
│  │    • Latest product announcements                                    │   │
│  │    • Community solutions (Stack Overflow, forums)                    │   │
│  │    Implementation: Tavily API / SerpAPI                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. DASHBOARD LINKER TOOL                                             │   │
│  │    Purpose: Generate deep links to AI/BI dashboards                  │   │
│  │    • Cost Analysis Dashboard                                         │   │
│  │    • Job Operations Dashboard                                        │   │
│  │    • Security Posture Dashboard                                      │   │
│  │    • Performance Insights Dashboard                                  │   │
│  │    • 11 dashboards total (from Phase 3.5)                           │   │
│  │    Implementation: Dashboard registry with URL templates             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. ALERT TRIGGER TOOL                                                │   │
│  │    Purpose: Manually trigger SQL alerts based on findings            │   │
│  │    • Trigger cost spike alerts                                       │   │
│  │    • Trigger job failure incidents                                   │   │
│  │    • Notify teams via configured channels                            │   │
│  │    Implementation: Alert Trigger Framework (to be built)             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. RUNBOOK RAG TOOL                                                  │   │
│  │    Purpose: Retrieve remediation steps from documentation            │   │
│  │    • Troubleshooting guides                                          │   │
│  │    • Runbook procedures                                              │   │
│  │    • Best practice recommendations                                   │   │
│  │    Implementation: Vector Search over documentation corpus           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tool 1: Web Search

### Purpose

Retrieve real-time information from the web that isn't available in the data warehouse:
- Databricks status page for outage information
- Product documentation for how-to guides
- Latest announcements and release notes
- Community solutions for common issues

### Implementation

```python
from typing import List, Optional
import mlflow
from tavily import TavilyClient
import os

class WebSearchTool:
    """Tool for searching the web for real-time information."""
    
    def __init__(self):
        self.client = TavilyClient(
            api_key=os.environ.get("TAVILY_API_KEY")
        )
        
        # Predefined search domains for better results
        self.trusted_domains = [
            "docs.databricks.com",
            "status.databricks.com",
            "community.databricks.com",
            "databricks.com/blog",
            "learn.microsoft.com/azure/databricks",
            "stackoverflow.com"
        ]
    
    @mlflow.trace(name="web_search", span_type="TOOL")
    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_domains: List[str] = None
    ) -> dict:
        """
        Search the web for information.
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results
            include_domains: Limit search to specific domains
        
        Returns:
            {
                "results": List[{title, url, content}],
                "answer": str (AI-generated summary),
                "query": str
            }
        """
        with mlflow.start_span(name="tavily_search") as span:
            span.set_attributes({
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results
            })
            
            # Use trusted domains if not specified
            domains = include_domains or self.trusted_domains
            
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=domains
            )
            
            results = {
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content", "")[:500]  # Truncate
                    }
                    for r in response.get("results", [])
                ],
                "answer": response.get("answer", ""),
                "query": query
            }
            
            span.set_attributes({
                "result_count": len(results["results"]),
                "has_answer": bool(results["answer"])
            })
            
            return results
    
    def check_databricks_status(self) -> dict:
        """Check Databricks status page for outages."""
        return self.search(
            query="Databricks service status current incidents",
            include_domains=["status.databricks.com"],
            max_results=3
        )
    
    def search_documentation(self, topic: str) -> dict:
        """Search Databricks documentation."""
        return self.search(
            query=f"Databricks {topic} documentation guide",
            include_domains=["docs.databricks.com", "learn.microsoft.com"],
            max_results=5
        )

# Tool instance
web_search_tool = WebSearchTool()
```

### Example Usage

```python
# Check for outages
status = web_search_tool.check_databricks_status()
print(f"Status: {status['answer']}")

# Search documentation
docs = web_search_tool.search_documentation("Delta Lake MERGE")
for result in docs['results']:
    print(f"- {result['title']}: {result['url']}")
```

## Tool 2: Dashboard Linker

### Purpose

Generate deep links to relevant AI/BI dashboards based on the user's query context. This helps users visualize the data behind the agent's answers.

### Implementation

```python
from typing import List, Optional, Dict
import mlflow
from urllib.parse import urlencode

class DashboardLinkerTool:
    """Tool for generating links to AI/BI dashboards."""
    
    def __init__(self, workspace_url: str):
        self.workspace_url = workspace_url.rstrip("/")
        
        # Dashboard registry from Phase 3.5
        self.dashboard_registry = {
            "cost_analysis": {
                "id": "cost_analysis_dashboard_id",
                "name": "Cost Analysis Dashboard",
                "domains": ["cost"],
                "description": "DBU usage, spending trends, budget tracking",
                "filters": ["workspace", "date_range", "sku"]
            },
            "job_operations": {
                "id": "job_operations_dashboard_id",
                "name": "Job Operations Dashboard",
                "domains": ["reliability"],
                "description": "Job success rates, failures, SLA tracking",
                "filters": ["job_name", "date_range", "status"]
            },
            "security_posture": {
                "id": "security_posture_dashboard_id",
                "name": "Security Posture Dashboard",
                "domains": ["security"],
                "description": "Access events, threats, compliance",
                "filters": ["user", "date_range", "action"]
            },
            "query_performance": {
                "id": "query_performance_dashboard_id",
                "name": "Query Performance Dashboard",
                "domains": ["performance"],
                "description": "Query latency, warehouse efficiency",
                "filters": ["warehouse", "date_range", "user"]
            },
            "data_quality": {
                "id": "data_quality_dashboard_id",
                "name": "Data Quality Dashboard",
                "domains": ["quality"],
                "description": "Quality scores, freshness, anomalies",
                "filters": ["table", "date_range", "catalog"]
            },
            "platform_overview": {
                "id": "platform_overview_dashboard_id",
                "name": "Platform Health Overview",
                "domains": ["cost", "security", "performance", "reliability", "quality"],
                "description": "Cross-domain health metrics",
                "filters": ["date_range"]
            },
            # Additional dashboards from Phase 3.5
            "warehouse_advisor": {
                "id": "warehouse_advisor_dashboard_id",
                "name": "Warehouse Advisor Dashboard",
                "domains": ["performance", "cost"],
                "description": "Warehouse sizing and optimization",
                "filters": ["warehouse", "date_range"]
            },
            "governance_hub": {
                "id": "governance_hub_dashboard_id",
                "name": "Governance Hub Dashboard",
                "domains": ["security", "quality"],
                "description": "Data classification, access control",
                "filters": ["catalog", "schema"]
            },
            "lakeflow_monitoring": {
                "id": "lakeflow_dashboard_id",
                "name": "LakeFlow Monitoring Dashboard",
                "domains": ["reliability"],
                "description": "Pipeline health, DLT monitoring",
                "filters": ["pipeline", "date_range"]
            },
            "serverless_cost": {
                "id": "serverless_cost_dashboard_id",
                "name": "Serverless Cost Observability",
                "domains": ["cost"],
                "description": "Serverless jobs and notebooks cost",
                "filters": ["job_type", "date_range"]
            },
            "workflow_advisor": {
                "id": "workflow_advisor_dashboard_id",
                "name": "Workflow Advisor Dashboard",
                "domains": ["reliability", "performance"],
                "description": "Job optimization recommendations",
                "filters": ["job_name", "date_range"]
            }
        }
    
    @mlflow.trace(name="dashboard_linker", span_type="TOOL")
    def get_relevant_dashboard(
        self,
        domains: List[str],
        filters: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Get the most relevant dashboard for the given domains.
        
        Args:
            domains: List of domains (cost, security, etc.)
            filters: Optional filter values to apply
        
        Returns:
            {
                "dashboard_name": str,
                "dashboard_url": str,
                "description": str,
                "available_filters": List[str]
            }
        """
        with mlflow.start_span(name="find_dashboard") as span:
            span.set_attributes({"domains": domains})
            
            # Find best matching dashboard
            best_match = None
            best_score = 0
            
            for key, dashboard in self.dashboard_registry.items():
                # Calculate match score
                matching_domains = set(domains) & set(dashboard["domains"])
                score = len(matching_domains) / len(domains) if domains else 0
                
                if score > best_score:
                    best_score = score
                    best_match = (key, dashboard)
            
            if not best_match:
                return {
                    "dashboard_name": "Platform Health Overview",
                    "dashboard_url": self._build_url("platform_overview"),
                    "description": "Cross-domain health metrics",
                    "available_filters": ["date_range"]
                }
            
            key, dashboard = best_match
            url = self._build_url(key, filters)
            
            span.set_attributes({
                "selected_dashboard": dashboard["name"],
                "match_score": best_score
            })
            
            return {
                "dashboard_name": dashboard["name"],
                "dashboard_url": url,
                "description": dashboard["description"],
                "available_filters": dashboard["filters"]
            }
    
    def _build_url(
        self,
        dashboard_key: str,
        filters: Optional[Dict[str, str]] = None
    ) -> str:
        """Build dashboard URL with optional filters."""
        dashboard = self.dashboard_registry[dashboard_key]
        base_url = f"{self.workspace_url}/sql/dashboards/{dashboard['id']}"
        
        if filters:
            # Filter only valid parameters
            valid_filters = {
                k: v for k, v in filters.items()
                if k in dashboard["filters"]
            }
            if valid_filters:
                return f"{base_url}?{urlencode(valid_filters)}"
        
        return base_url
    
    def get_all_dashboards(self) -> List[dict]:
        """Get list of all available dashboards."""
        return [
            {
                "name": d["name"],
                "description": d["description"],
                "domains": d["domains"]
            }
            for d in self.dashboard_registry.values()
        ]

# Tool instance
dashboard_linker = DashboardLinkerTool(
    workspace_url=os.environ.get("DATABRICKS_HOST")
)
```

### Example Usage

```python
# Get dashboard for cost queries
link = dashboard_linker.get_relevant_dashboard(
    domains=["cost"],
    filters={"date_range": "last_7_days"}
)
print(f"View details: {link['dashboard_url']}")

# Get dashboard for multi-domain query
link = dashboard_linker.get_relevant_dashboard(
    domains=["cost", "reliability"]
)
print(f"Dashboard: {link['dashboard_name']}")
```

## Tool 3: Alert Trigger

### Purpose

Allow the agent to trigger SQL alerts based on findings. This enables proactive notification when the agent detects issues.

### Implementation

```python
from typing import Optional, Dict, List
import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import AlertsAPI

class AlertTriggerTool:
    """Tool for triggering SQL alerts programmatically."""
    
    def __init__(self, workspace_client: WorkspaceClient = None):
        self.client = workspace_client or WorkspaceClient()
        self.alerts_api = AlertsAPI(self.client)
        
        # Alert registry from Phase 3.7
        self.alert_registry = {
            "cost_spike": {
                "alert_id": "cost_spike_alert_id",
                "name": "Cost Spike Alert",
                "description": "Triggered when daily cost exceeds threshold",
                "channels": ["slack", "email"],
                "severity": "high"
            },
            "job_failure": {
                "alert_id": "job_failure_alert_id",
                "name": "Critical Job Failure Alert",
                "description": "Triggered when critical job fails",
                "channels": ["pagerduty", "slack"],
                "severity": "critical"
            },
            "security_threat": {
                "alert_id": "security_threat_alert_id",
                "name": "Security Threat Alert",
                "description": "Triggered on suspicious access patterns",
                "channels": ["security_team", "slack"],
                "severity": "critical"
            },
            "quality_degradation": {
                "alert_id": "quality_degradation_alert_id",
                "name": "Data Quality Alert",
                "description": "Triggered when quality score drops",
                "channels": ["data_team", "email"],
                "severity": "medium"
            },
            "performance_degradation": {
                "alert_id": "perf_degradation_alert_id",
                "name": "Performance Alert",
                "description": "Triggered when query latency increases",
                "channels": ["platform_team", "slack"],
                "severity": "medium"
            }
        }
    
    @mlflow.trace(name="alert_trigger", span_type="TOOL")
    def trigger_alert(
        self,
        alert_type: str,
        context: Dict[str, str],
        triggered_by: str = "agent"
    ) -> dict:
        """
        Trigger an alert with context.
        
        Args:
            alert_type: Type of alert (cost_spike, job_failure, etc.)
            context: Context data for the alert message
            triggered_by: Who/what triggered the alert
        
        Returns:
            {
                "status": str,
                "alert_name": str,
                "message": str,
                "channels_notified": List[str]
            }
        """
        with mlflow.start_span(name="trigger_alert") as span:
            span.set_attributes({
                "alert_type": alert_type,
                "triggered_by": triggered_by
            })
            
            if alert_type not in self.alert_registry:
                return {
                    "status": "error",
                    "message": f"Unknown alert type: {alert_type}"
                }
            
            alert_config = self.alert_registry[alert_type]
            
            # Build alert message
            message = self._build_alert_message(alert_config, context, triggered_by)
            
            try:
                # Trigger the alert via SQL Alerts API
                # Note: This is a simplified version. Actual implementation
                # would use the SQL Alerts trigger mechanism.
                self._send_alert(alert_config, message)
                
                span.set_attributes({
                    "status": "triggered",
                    "channels": alert_config["channels"]
                })
                
                return {
                    "status": "triggered",
                    "alert_name": alert_config["name"],
                    "message": message,
                    "channels_notified": alert_config["channels"],
                    "severity": alert_config["severity"]
                }
            
            except Exception as e:
                span.set_attributes({"error": str(e)})
                return {
                    "status": "error",
                    "message": f"Failed to trigger alert: {str(e)}"
                }
    
    def _build_alert_message(
        self,
        alert_config: dict,
        context: dict,
        triggered_by: str
    ) -> str:
        """Build alert message with context."""
        message_parts = [
            f"**{alert_config['name']}** ({alert_config['severity'].upper()})",
            f"Triggered by: {triggered_by}",
            "",
            "**Context:**"
        ]
        
        for key, value in context.items():
            message_parts.append(f"- {key}: {value}")
        
        return "\n".join(message_parts)
    
    def _send_alert(self, alert_config: dict, message: str):
        """Send alert to configured channels."""
        # Implementation would integrate with notification systems
        # For now, log the alert
        print(f"ALERT: {alert_config['name']}")
        print(message)
        
        # In production, this would call:
        # - Slack webhook
        # - PagerDuty API
        # - Email service
        # - SQL Alerts trigger
    
    def prepare_alert(
        self,
        query: str,
        agent_responses: Dict[str, dict]
    ) -> dict:
        """
        Analyze agent responses to determine if an alert should be triggered.
        
        Args:
            query: User's original query
            agent_responses: Responses from domain agents
        
        Returns:
            Alert recommendation or None
        """
        recommendations = []
        
        # Check cost responses for spikes
        if "cost" in agent_responses:
            cost_response = agent_responses["cost"].get("response", "")
            if any(kw in cost_response.lower() for kw in ["spike", "increase", "exceeded", "anomaly"]):
                recommendations.append({
                    "alert_type": "cost_spike",
                    "context": {"source": "cost_agent", "finding": cost_response[:200]}
                })
        
        # Check reliability for failures
        if "reliability" in agent_responses:
            rel_response = agent_responses["reliability"].get("response", "")
            if any(kw in rel_response.lower() for kw in ["failed", "failure", "error", "down"]):
                recommendations.append({
                    "alert_type": "job_failure",
                    "context": {"source": "reliability_agent", "finding": rel_response[:200]}
                })
        
        # Check security for threats
        if "security" in agent_responses:
            sec_response = agent_responses["security"].get("response", "")
            if any(kw in sec_response.lower() for kw in ["threat", "unauthorized", "suspicious", "breach"]):
                recommendations.append({
                    "alert_type": "security_threat",
                    "context": {"source": "security_agent", "finding": sec_response[:200]}
                })
        
        return {"recommendations": recommendations}

# Tool instance
alert_trigger = AlertTriggerTool()
```

### Example Usage

```python
# Trigger a cost spike alert
result = alert_trigger.trigger_alert(
    alert_type="cost_spike",
    context={
        "amount": "$15,000",
        "threshold": "$10,000",
        "date": "2025-01-15",
        "workspace": "prod"
    },
    triggered_by="health_monitor_agent"
)
print(f"Alert status: {result['status']}")
```

## Tool 4: Runbook RAG

### Purpose

Retrieve remediation steps and troubleshooting guides from documentation using vector search. This helps the agent provide actionable recommendations.

### Implementation

```python
from typing import List, Optional
import mlflow
from databricks.vector_search.client import VectorSearchClient

class RunbookRAGTool:
    """Tool for retrieving runbook content using vector search."""
    
    def __init__(
        self,
        index_name: str = "health_monitor.runbooks.runbook_index",
        embedding_endpoint: str = "databricks-bge-large-en"
    ):
        self.client = VectorSearchClient()
        self.index_name = index_name
        self.embedding_endpoint = embedding_endpoint
        
        # Get the index
        self.index = self.client.get_index(
            endpoint_name="runbook_vector_endpoint",
            index_name=index_name
        )
    
    @mlflow.trace(name="runbook_search", span_type="TOOL")
    def search(
        self,
        query: str,
        agent_responses: Optional[Dict] = None,
        num_results: int = 5,
        filters: Optional[Dict] = None
    ) -> dict:
        """
        Search runbooks for relevant remediation steps.
        
        Args:
            query: Search query
            agent_responses: Context from agent responses
            num_results: Number of results to return
            filters: Optional metadata filters
        
        Returns:
            {
                "results": List[{title, content, source, relevance}],
                "suggested_actions": List[str]
            }
        """
        with mlflow.start_span(name="vector_search") as span:
            # Enhance query with agent context
            enhanced_query = self._enhance_query(query, agent_responses)
            
            span.set_attributes({
                "original_query": query,
                "enhanced_query": enhanced_query,
                "num_results": num_results
            })
            
            # Perform vector search
            results = self.index.similarity_search(
                query_text=enhanced_query,
                columns=["title", "content", "source", "category", "tags"],
                num_results=num_results,
                filters=filters
            )
            
            # Format results
            formatted_results = []
            for row in results.get("result", {}).get("data_array", []):
                formatted_results.append({
                    "title": row[0],
                    "content": row[1],
                    "source": row[2],
                    "category": row[3],
                    "tags": row[4],
                    "relevance": row[-1]  # Score is typically last
                })
            
            # Extract suggested actions
            suggested_actions = self._extract_actions(formatted_results)
            
            span.set_attributes({
                "result_count": len(formatted_results),
                "action_count": len(suggested_actions)
            })
            
            return {
                "results": formatted_results,
                "suggested_actions": suggested_actions
            }
    
    def _enhance_query(
        self,
        query: str,
        agent_responses: Optional[Dict]
    ) -> str:
        """Enhance search query with context."""
        if not agent_responses:
            return query
        
        # Add error messages from agent responses
        error_context = []
        for domain, response in agent_responses.items():
            if "error" in response.get("response", "").lower():
                # Extract potential error keywords
                error_context.append(domain)
        
        if error_context:
            return f"{query} troubleshoot {' '.join(error_context)}"
        return query
    
    def _extract_actions(self, results: List[dict]) -> List[str]:
        """Extract actionable steps from results."""
        actions = []
        
        for result in results[:3]:  # Top 3 results
            content = result.get("content", "")
            
            # Look for numbered steps or bullet points
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                # Match numbered steps (1., 2., etc.) or bullets (-, *)
                if (line and 
                    (line[0].isdigit() or line[0] in ["-", "*", "•"]) and
                    len(line) > 10):
                    actions.append(line.lstrip("0123456789.-*• "))
        
        return actions[:5]  # Top 5 actions
    
    def get_remediation_steps(
        self,
        issue_type: str,
        context: Dict[str, str]
    ) -> dict:
        """
        Get specific remediation steps for an issue.
        
        Args:
            issue_type: Type of issue (job_failure, cost_spike, etc.)
            context: Issue context (error message, affected resource, etc.)
        
        Returns:
            Remediation steps and relevant documentation
        """
        # Build targeted query
        query_parts = [f"remediate {issue_type}"]
        
        if context.get("error_message"):
            query_parts.append(context["error_message"][:100])
        if context.get("resource"):
            query_parts.append(context["resource"])
        
        query = " ".join(query_parts)
        
        # Search with category filter
        category_map = {
            "job_failure": "reliability",
            "cost_spike": "cost_optimization",
            "slow_query": "performance",
            "security_incident": "security",
            "data_quality": "data_management"
        }
        
        filters = None
        if issue_type in category_map:
            filters = {"category": category_map[issue_type]}
        
        return self.search(query, filters=filters)

# Tool instance
runbook_rag = RunbookRAGTool()
```

### Runbook Index Schema

```sql
-- Table for storing runbook content
CREATE TABLE health_monitor.runbooks.runbook_content (
    id STRING PRIMARY KEY,
    title STRING NOT NULL,
    content STRING NOT NULL,
    source STRING,  -- URL or document path
    category STRING,  -- reliability, cost, security, performance, data
    tags ARRAY<STRING>,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Vector Search Index
CREATE VECTOR SEARCH INDEX runbook_index
ON health_monitor.runbooks.runbook_content (
    content_embedding
)
USING DATABRICKS_VECTOR_SEARCH
WITH (
    endpoint_name = "runbook_vector_endpoint",
    embedding_source_column = "content",
    embedding_model_endpoint_name = "databricks-bge-large-en"
);
```

### Example Usage

```python
# Search for remediation steps
results = runbook_rag.search(
    query="How do I fix job timeout errors?",
    agent_responses={"reliability": {"response": "Job xyz timed out after 2 hours"}}
)

print("Suggested Actions:")
for action in results["suggested_actions"]:
    print(f"  - {action}")
```

## Tool Registry

```python
from typing import Dict, Any

class ToolRegistry:
    """Registry of all utility tools."""
    
    def __init__(self):
        self.tools = {
            "web_search": web_search_tool,
            "dashboard_linker": dashboard_linker,
            "alert_trigger": alert_trigger,
            "runbook_rag": runbook_rag
        }
    
    def get_tool(self, name: str):
        """Get a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        return self.tools[name]
    
    def invoke(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Invoke a tool with parameters."""
        tool = self.get_tool(tool_name)
        
        # Map tool names to methods
        method_map = {
            "web_search": tool.search,
            "dashboard_linker": tool.get_relevant_dashboard,
            "alert_trigger": tool.trigger_alert,
            "runbook_rag": tool.search
        }
        
        return method_map[tool_name](**kwargs)

# Global registry
tool_registry = ToolRegistry()
```

## Next Steps

- **[07-Memory Management](07-memory-management.md)**: Lakebase short/long-term memory
- **[08-MLflow Tracing](08-mlflow-tracing.md)**: Comprehensive tracing setup

