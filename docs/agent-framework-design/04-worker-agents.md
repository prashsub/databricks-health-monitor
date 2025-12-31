# 04 - Worker Agents

## Overview

Worker agents are domain specialists that receive queries from the orchestrator and query their assigned Genie Space. Each worker follows a consistent interface but specializes in a specific domain.

## Worker Agent Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
import mlflow

class WorkerAgent(ABC):
    """Base class for all worker agents."""
    
    def __init__(
        self,
        domain: str,
        genie_space_id: str,
        workspace_client: WorkspaceClient
    ):
        self.domain = domain
        self.genie_space_id = genie_space_id
        self.client = workspace_client
        self.genie = GenieAPI(workspace_client)
    
    @abstractmethod
    def enhance_query(self, query: str, context: Dict) -> str:
        """Enhance the query with domain-specific context."""
        pass
    
    @abstractmethod
    def format_response(self, genie_response: Dict) -> Dict:
        """Format the Genie response for synthesis."""
        pass
    
    @mlflow.trace(span_type="AGENT")
    def query(
        self,
        question: str,
        context: Optional[Dict] = None,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        Query the Genie Space and return structured response.
        
        Args:
            question: User's question
            context: Additional context (user preferences, history)
            conversation_id: Optional conversation ID for continuity
        
        Returns:
            {
                "response": str,
                "sources": List[str],
                "confidence": float,
                "domain": str,
                "raw_data": Optional[dict]
            }
        """
        with mlflow.start_span(name=f"{self.domain}_agent_query") as span:
            # Enhance query with domain context
            enhanced_query = self.enhance_query(question, context or {})
            
            span.set_attributes({
                "original_query": question,
                "enhanced_query": enhanced_query,
                "genie_space_id": self.genie_space_id
            })
            
            # Query Genie
            try:
                if conversation_id:
                    genie_response = self.genie.continue_conversation(
                        space_id=self.genie_space_id,
                        conversation_id=conversation_id,
                        content=enhanced_query
                    )
                else:
                    genie_response = self.genie.start_conversation(
                        space_id=self.genie_space_id,
                        content=enhanced_query
                    )
                
                # Format response
                formatted = self.format_response(genie_response)
                formatted["domain"] = self.domain
                formatted["conversation_id"] = genie_response.conversation_id
                
                span.set_attributes({
                    "response_length": len(formatted.get("response", "")),
                    "source_count": len(formatted.get("sources", [])),
                    "success": True
                })
                
                return formatted
                
            except Exception as e:
                span.set_attributes({"error": str(e), "success": False})
                return {
                    "response": f"Error querying {self.domain} data: {str(e)}",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": self.domain,
                    "error": str(e)
                }
    
    async def query_async(
        self,
        question: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Async version for parallel execution."""
        import asyncio
        return await asyncio.to_thread(self.query, question, context)
```

## Domain-Specific Worker Agents

### Cost Agent

```python
class CostWorkerAgent(WorkerAgent):
    """Worker agent specialized for cost and billing queries."""
    
    def __init__(self, workspace_client: WorkspaceClient):
        super().__init__(
            domain="cost",
            genie_space_id="cost_intelligence_genie_space_id",  # From Phase 3.6
            workspace_client=workspace_client
        )
        
        # Domain-specific knowledge
        self.key_metrics = [
            "total_dbu_cost", "compute_cost", "storage_cost",
            "serverless_spend", "job_cost", "warehouse_cost"
        ]
        self.key_dimensions = [
            "workspace", "sku_name", "usage_date", "owner",
            "tag_team", "tag_project"
        ]
    
    def enhance_query(self, query: str, context: Dict) -> str:
        """Add cost-specific context to the query."""
        enhanced = query
        
        # Add time context if missing
        if not any(kw in query.lower() for kw in ["today", "yesterday", "week", "month", "date"]):
            enhanced += " (for the last 7 days if no time specified)"
        
        # Add workspace filter if user has preference
        if context.get("preferred_workspace"):
            enhanced += f" Focus on workspace: {context['preferred_workspace']}"
        
        # Add cost threshold context
        if context.get("cost_threshold"):
            enhanced += f" Flag costs exceeding ${context['cost_threshold']}"
        
        return enhanced
    
    def format_response(self, genie_response: Dict) -> Dict:
        """Format cost response with currency formatting."""
        response_text = genie_response.result.content
        
        # Extract sources (tables/views queried)
        sources = genie_response.result.sources or []
        
        return {
            "response": response_text,
            "sources": [f"Cost Intelligence: {s}" for s in sources],
            "confidence": 0.9,  # High confidence for Genie responses
            "raw_data": genie_response.result.data if hasattr(genie_response.result, 'data') else None
        }

# Genie Space mapping from Phase 3.6
COST_GENIE_ASSETS = {
    "tvfs": [
        "get_daily_cost_summary",
        "get_top_cost_contributors", 
        "get_cost_anomalies",
        "get_workspace_cost_breakdown",
        "get_sku_cost_analysis",
        "get_tagged_vs_untagged_spend",
        "get_serverless_cost_trend",
        "get_budget_vs_actual",
        "get_cost_forecast",
        "get_chargeback_report",
        "get_idle_resource_cost",
        "get_right_sizing_opportunities",
        "get_commitment_utilization",
        "get_spot_vs_ondemand_analysis",
        "get_cost_per_job"
    ],
    "metric_views": [
        "cost_analytics_metrics",
        "budget_performance_metrics"
    ],
    "ml_models": [
        "cost_anomaly_detector",
        "cost_forecaster",
        "budget_predictor",
        "usage_pattern_classifier",
        "waste_detector",
        "right_sizing_recommender"
    ]
}
```

### Security Agent

```python
class SecurityWorkerAgent(WorkerAgent):
    """Worker agent specialized for security and compliance queries."""
    
    def __init__(self, workspace_client: WorkspaceClient):
        super().__init__(
            domain="security",
            genie_space_id="security_auditor_genie_space_id",
            workspace_client=workspace_client
        )
        
        self.key_metrics = [
            "access_events", "failed_logins", "permission_changes",
            "sensitive_data_access", "api_calls", "threat_score"
        ]
        self.key_dimensions = [
            "user_email", "action_name", "service_name",
            "ip_address", "workspace", "timestamp"
        ]
    
    def enhance_query(self, query: str, context: Dict) -> str:
        """Add security-specific context to the query."""
        enhanced = query
        
        # Add time context for security (default to 24 hours)
        if not any(kw in query.lower() for kw in ["today", "yesterday", "hour", "day"]):
            enhanced += " (in the last 24 hours if no time specified)"
        
        # Add sensitivity context
        if "sensitive" in query.lower() or "pii" in query.lower():
            enhanced += " Include data classification tags in the response."
        
        return enhanced
    
    def format_response(self, genie_response: Dict) -> Dict:
        """Format security response with threat indicators."""
        response_text = genie_response.result.content
        sources = genie_response.result.sources or []
        
        return {
            "response": response_text,
            "sources": [f"Security Auditor: {s}" for s in sources],
            "confidence": 0.92,
            "raw_data": genie_response.result.data if hasattr(genie_response.result, 'data') else None
        }

SECURITY_GENIE_ASSETS = {
    "tvfs": [
        "get_security_events_summary",
        "get_failed_access_attempts",
        "get_sensitive_data_access",
        "get_permission_changes",
        "get_user_activity_report",
        "get_api_access_patterns",
        "get_threat_indicators",
        "get_compliance_violations",
        "get_secret_access_log",
        "get_ip_anomalies"
    ],
    "metric_views": [
        "security_posture_metrics",
        "compliance_metrics"
    ],
    "ml_models": [
        "threat_detector",
        "anomaly_access_detector",
        "insider_threat_scorer",
        "compliance_risk_predictor"
    ]
}
```

### Performance Agent

```python
class PerformanceWorkerAgent(WorkerAgent):
    """Worker agent specialized for performance and optimization queries."""
    
    def __init__(self, workspace_client: WorkspaceClient):
        super().__init__(
            domain="performance",
            genie_space_id="performance_optimizer_genie_space_id",
            workspace_client=workspace_client
        )
        
        self.key_metrics = [
            "query_duration", "cluster_utilization", "spill_bytes",
            "shuffle_bytes", "scan_efficiency", "cache_hit_rate"
        ]
        self.key_dimensions = [
            "query_id", "warehouse_id", "cluster_id",
            "user_email", "query_type", "execution_date"
        ]
    
    def enhance_query(self, query: str, context: Dict) -> str:
        """Add performance-specific context to the query."""
        enhanced = query
        
        # Add threshold context
        if "slow" in query.lower() and not any(c.isdigit() for c in query):
            enhanced += " (consider queries taking >30 seconds as slow)"
        
        # Add warehouse filter if specified
        if context.get("preferred_warehouse"):
            enhanced += f" Focus on warehouse: {context['preferred_warehouse']}"
        
        return enhanced
    
    def format_response(self, genie_response: Dict) -> Dict:
        """Format performance response with timing details."""
        response_text = genie_response.result.content
        sources = genie_response.result.sources or []
        
        return {
            "response": response_text,
            "sources": [f"Performance: {s}" for s in sources],
            "confidence": 0.88,
            "raw_data": genie_response.result.data if hasattr(genie_response.result, 'data') else None
        }

PERFORMANCE_GENIE_ASSETS = {
    "tvfs": [
        "get_slow_queries",
        "get_query_performance_stats",
        "get_cluster_utilization",
        "get_warehouse_efficiency",
        "get_spill_analysis",
        "get_cache_performance",
        "get_concurrent_query_analysis",
        "get_query_queue_times",
        "get_optimization_recommendations",
        "get_index_suggestions",
        "get_partition_efficiency",
        "get_compute_right_sizing",
        "get_autoscale_analysis",
        "get_photon_performance",
        "get_serverless_performance",
        "get_query_comparison"
    ],
    "metric_views": [
        "query_performance_metrics",
        "cluster_efficiency_metrics",
        "warehouse_performance_metrics"
    ],
    "ml_models": [
        "query_runtime_predictor",
        "resource_recommender",
        "autoscale_optimizer",
        "cache_predictor",
        "workload_classifier",
        "bottleneck_detector",
        "performance_anomaly_detector"
    ]
}
```

### Reliability Agent

```python
class ReliabilityWorkerAgent(WorkerAgent):
    """Worker agent specialized for job reliability and SLA queries."""
    
    def __init__(self, workspace_client: WorkspaceClient):
        super().__init__(
            domain="reliability",
            genie_space_id="job_health_monitor_genie_space_id",
            workspace_client=workspace_client
        )
        
        self.key_metrics = [
            "success_rate", "failure_count", "sla_breach_count",
            "mttr", "mtbf", "duration_p95"
        ]
        self.key_dimensions = [
            "job_name", "workspace", "result_state",
            "error_category", "owner", "run_date"
        ]
    
    def enhance_query(self, query: str, context: Dict) -> str:
        """Add reliability-specific context to the query."""
        enhanced = query
        
        # Add failure context
        if "fail" in query.lower():
            enhanced += " Include error messages and failure categories."
        
        # Add SLA context
        if "sla" in query.lower():
            enhanced += " Compare against defined SLA thresholds."
        
        return enhanced
    
    def format_response(self, genie_response: Dict) -> Dict:
        """Format reliability response with status indicators."""
        response_text = genie_response.result.content
        sources = genie_response.result.sources or []
        
        return {
            "response": response_text,
            "sources": [f"Reliability: {s}" for s in sources],
            "confidence": 0.91,
            "raw_data": genie_response.result.data if hasattr(genie_response.result, 'data') else None
        }

RELIABILITY_GENIE_ASSETS = {
    "tvfs": [
        "get_failed_jobs",
        "get_job_success_rate",
        "get_sla_breaches",
        "get_job_run_history",
        "get_pipeline_health",
        "get_error_analysis",
        "get_recovery_time_stats",
        "get_job_dependencies",
        "get_critical_path_analysis",
        "get_retry_analysis",
        "get_timeout_analysis",
        "get_resource_contention"
    ],
    "metric_views": [
        "job_reliability_metrics"
    ],
    "ml_models": [
        "failure_predictor",
        "sla_breach_predictor",
        "recovery_time_estimator",
        "root_cause_classifier",
        "impact_assessor"
    ]
}
```

### Quality Agent

```python
class QualityWorkerAgent(WorkerAgent):
    """Worker agent specialized for data quality and governance queries."""
    
    def __init__(self, workspace_client: WorkspaceClient):
        super().__init__(
            domain="quality",
            genie_space_id="data_quality_monitor_genie_space_id",
            workspace_client=workspace_client
        )
        
        self.key_metrics = [
            "completeness_score", "freshness_score", "accuracy_score",
            "anomaly_count", "schema_drift_count", "lineage_depth"
        ]
        self.key_dimensions = [
            "table_name", "schema", "catalog",
            "column_name", "data_classification", "owner"
        ]
    
    def enhance_query(self, query: str, context: Dict) -> str:
        """Add quality-specific context to the query."""
        enhanced = query
        
        # Add freshness context
        if "fresh" in query.lower() or "stale" in query.lower():
            enhanced += " Include last update timestamps."
        
        # Add lineage context
        if "lineage" in query.lower():
            enhanced += " Show upstream and downstream dependencies."
        
        return enhanced
    
    def format_response(self, genie_response: Dict) -> Dict:
        """Format quality response with quality scores."""
        response_text = genie_response.result.content
        sources = genie_response.result.sources or []
        
        return {
            "response": response_text,
            "sources": [f"Data Quality: {s}" for s in sources],
            "confidence": 0.87,
            "raw_data": genie_response.result.data if hasattr(genie_response.result, 'data') else None
        }

QUALITY_GENIE_ASSETS = {
    "tvfs": [
        "get_table_quality_scores",
        "get_freshness_report",
        "get_schema_drift_analysis",
        "get_anomaly_report",
        "get_data_lineage",
        "get_classification_coverage",
        "get_governance_compliance"
    ],
    "metric_views": [
        "data_quality_metrics",
        "governance_metrics"
    ],
    "ml_models": [
        "quality_predictor",
        "anomaly_detector",
        "drift_classifier"
    ]
}
```

## Worker Agent Registry

```python
from databricks.sdk import WorkspaceClient

class WorkerAgentRegistry:
    """Registry of all worker agents."""
    
    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        self.client = workspace_client or WorkspaceClient()
        
        # Initialize all worker agents
        self.agents = {
            "cost": CostWorkerAgent(self.client),
            "security": SecurityWorkerAgent(self.client),
            "performance": PerformanceWorkerAgent(self.client),
            "reliability": ReliabilityWorkerAgent(self.client),
            "quality": QualityWorkerAgent(self.client)
        }
    
    def get_agent(self, domain: str) -> WorkerAgent:
        """Get a worker agent by domain."""
        domain_lower = domain.lower()
        if domain_lower not in self.agents:
            raise ValueError(f"Unknown domain: {domain}. Valid domains: {list(self.agents.keys())}")
        return self.agents[domain_lower]
    
    async def query_multiple(
        self,
        domains: List[str],
        question: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Dict]:
        """Query multiple agents in parallel."""
        import asyncio
        
        tasks = {}
        for domain in domains:
            agent = self.get_agent(domain)
            tasks[domain] = asyncio.create_task(
                agent.query_async(question, context)
            )
        
        results = {}
        for domain, task in tasks.items():
            try:
                results[domain] = await task
            except Exception as e:
                results[domain] = {
                    "response": f"Error: {str(e)}",
                    "sources": [],
                    "confidence": 0.0,
                    "domain": domain,
                    "error": str(e)
                }
        
        return results

# Global registry instance
worker_registry = WorkerAgentRegistry()
```

## Genie Space ID Configuration

```python
# Genie Space IDs from Phase 3.6 deployment
GENIE_SPACE_CONFIG = {
    "cost": {
        "space_id": "${COST_INTELLIGENCE_GENIE_SPACE_ID}",
        "name": "Cost Intelligence Genie Space",
        "description": "Cost analysis, billing, budgets, chargeback"
    },
    "security": {
        "space_id": "${SECURITY_AUDITOR_GENIE_SPACE_ID}",
        "name": "Security Auditor Genie Space",
        "description": "Security events, access control, compliance"
    },
    "performance": {
        "space_id": "${PERFORMANCE_OPTIMIZER_GENIE_SPACE_ID}",
        "name": "Performance Optimizer Genie Space",
        "description": "Query performance, cluster efficiency, optimization"
    },
    "reliability": {
        "space_id": "${JOB_HEALTH_MONITOR_GENIE_SPACE_ID}",
        "name": "Job Health Monitor Genie Space",
        "description": "Job failures, SLAs, pipeline health"
    },
    "quality": {
        "space_id": "${DATA_QUALITY_MONITOR_GENIE_SPACE_ID}",
        "name": "Data Quality Monitor Genie Space",
        "description": "Data quality, freshness, lineage, governance"
    },
    "unified": {
        "space_id": "${UNIFIED_HEALTH_MONITOR_GENIE_SPACE_ID}",
        "name": "Unified Health Monitor Genie Space",
        "description": "Cross-domain queries, platform overview"
    }
}
```

## Testing Worker Agents

```python
import pytest
from unittest.mock import Mock, patch

class TestCostWorkerAgent:
    """Tests for Cost Worker Agent."""
    
    def setup_method(self):
        self.mock_client = Mock(spec=WorkspaceClient)
        self.agent = CostWorkerAgent(self.mock_client)
    
    def test_enhance_query_adds_time_context(self):
        query = "What are the top cost contributors?"
        enhanced = self.agent.enhance_query(query, {})
        assert "7 days" in enhanced
    
    def test_enhance_query_respects_existing_time(self):
        query = "What were yesterday's costs?"
        enhanced = self.agent.enhance_query(query, {})
        assert "yesterday" in enhanced.lower()
        assert "7 days" not in enhanced
    
    def test_enhance_query_adds_workspace_filter(self):
        query = "Show me costs"
        context = {"preferred_workspace": "prod"}
        enhanced = self.agent.enhance_query(query, context)
        assert "prod" in enhanced
    
    @patch.object(CostWorkerAgent, 'genie')
    def test_query_returns_formatted_response(self, mock_genie):
        # Mock Genie response
        mock_response = Mock()
        mock_response.result.content = "Costs increased by 20%"
        mock_response.result.sources = ["fact_usage"]
        mock_response.conversation_id = "conv_123"
        mock_genie.start_conversation.return_value = mock_response
        
        result = self.agent.query("Why did costs spike?")
        
        assert result["response"] == "Costs increased by 20%"
        assert result["domain"] == "cost"
        assert result["confidence"] == 0.9
        assert len(result["sources"]) == 1

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Next Steps

- **[05-Genie Integration](05-genie-integration.md)**: Detailed Genie API patterns
- **[06-Utility Tools](06-utility-tools.md)**: Web search, dashboard linker, alerts, RAG

