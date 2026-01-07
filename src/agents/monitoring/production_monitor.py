"""
Production Monitoring for Health Monitor Agent

Implements real-time response quality assessment using mlflow.genai.assess()
per MLflow 3.0 production monitoring best practices.

Two complementary monitoring approaches:
1. **Registered Scorers** (see register_scorers.py): Automatically run on sampled traces
2. **On-demand Assessment** (this file): Explicitly called via assess_response()

References:
- https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring
- .cursor/rules/ml/28-mlflow-genai-patterns.mdc
"""

import mlflow
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json
import re

# Import scorer decorator and Score class with fallback
try:
    from mlflow.genai.scorers import scorer
    from mlflow.genai import Score
except ImportError:
    # Fallback for older MLflow versions
    from mlflow.genai import scorer, Score

# Import built-in scorers with fallback
try:
    from mlflow.genai.scorers import Relevance, Safety
    BUILTIN_SCORERS_AVAILABLE = True
except ImportError:
    BUILTIN_SCORERS_AVAILABLE = False
    Relevance = None
    Safety = None

# Note: assess() function may not be available in all MLflow versions
try:
    from mlflow.genai import assess
    ASSESS_AVAILABLE = True
except ImportError:
    assess = None
    ASSESS_AVAILABLE = False


@dataclass
class AssessmentResult:
    """Result of a production assessment."""
    request_id: str
    timestamp: str
    scores: Dict[str, float]
    rationales: Dict[str, str]
    overall_score: float
    needs_review: bool
    alert_triggered: bool


# ===========================================================================
# CUSTOM SCORERS FOR PRODUCTION MONITORING
# ===========================================================================

@scorer
def response_quality_scorer(inputs: Dict, outputs: Dict, expectations: Optional[Dict] = None) -> Score:
    """
    Quick production scorer for response quality.
    Optimized for low latency in production monitoring.
    """
    response = outputs.get("response", "")
    
    # Quick heuristics for production
    score = 1.0
    rationale_parts = []
    
    # Check for error responses
    if "error" in response.lower():
        score -= 0.5
        rationale_parts.append("Contains error indication")
    
    # Check for minimal response
    if len(response) < 50:
        score -= 0.2
        rationale_parts.append("Very short response")
    
    # Check for actionable content
    if any(word in response.lower() for word in ["should", "recommend", "try", "check", "run"]):
        score += 0.1
        rationale_parts.append("Contains actionable language")
    
    score = max(0.0, min(1.0, score))
    
    return Score(
        value=score,
        rationale="; ".join(rationale_parts) if rationale_parts else "Standard response"
    )


@scorer
def domain_routing_scorer(inputs: Dict, outputs: Dict, expectations: Optional[Dict] = None) -> Score:
    """
    Verify that the response addresses the correct domain.
    """
    query = inputs.get("query", "").lower()
    metadata = outputs.get("metadata", {})
    detected_domain = metadata.get("domain", "unknown")
    
    # Domain keyword mapping
    domain_keywords = {
        "cost": ["cost", "spend", "budget", "billing", "dbu"],
        "security": ["security", "access", "permission", "audit", "login"],
        "performance": ["slow", "performance", "latency", "cache", "optimize"],
        "reliability": ["fail", "job", "error", "sla", "pipeline"],
        "quality": ["quality", "freshness", "stale", "schema", "null"],
    }
    
    # Find expected domain from query
    expected_domain = "unified"
    for domain, keywords in domain_keywords.items():
        if any(kw in query for kw in keywords):
            expected_domain = domain
            break
    
    # Check if routing was correct
    if detected_domain == expected_domain:
        return Score(value=1.0, rationale=f"Correctly routed to {expected_domain}")
    elif detected_domain == "unified":
        return Score(value=0.7, rationale=f"Routed to unified (expected {expected_domain})")
    else:
        return Score(value=0.3, rationale=f"Misrouted: {detected_domain} (expected {expected_domain})")


# ===========================================================================
# PRODUCTION MONITOR CLASS
# ===========================================================================

class ProductionMonitor:
    """
    Production monitoring using mlflow.genai.assess().
    
    Two modes of operation:
    1. With mlflow.genai.assess() - Uses built-in scorers (Relevance, Safety)
    2. Fallback mode - Uses custom heuristic scorers when assess() unavailable
    
    Usage:
        monitor = ProductionMonitor()
        
        # After each agent response
        result = monitor.assess_response(
            query="Why did costs spike?",
            response="Based on the analysis...",
            metadata={"domain": "cost", "source": "genie"}
        )
        
        if result.needs_review:
            send_alert(result)
    """
    
    def __init__(
        self,
        relevance_threshold: float = 0.6,
        safety_threshold: float = 0.9,
        alert_threshold: float = 0.5,
    ):
        """
        Initialize production monitor.
        
        Args:
            relevance_threshold: Minimum relevance score
            safety_threshold: Minimum safety score  
            alert_threshold: Score below which to trigger alert
        """
        self.relevance_threshold = relevance_threshold
        self.safety_threshold = safety_threshold
        self.alert_threshold = alert_threshold
        
        # Build scorers list based on availability
        self.scorers = []
        
        # Add built-in scorers if available
        if BUILTIN_SCORERS_AVAILABLE and Relevance is not None:
            self.scorers.append(Relevance())
            self.scorers.append(Safety())
        
        # Always add custom scorers (work regardless of MLflow version)
        self.scorers.extend([
            response_quality_scorer,
            domain_routing_scorer,
        ])
    
    def assess_response(
        self,
        query: str,
        response: str,
        metadata: Optional[Dict] = None,
        request_id: Optional[str] = None,
    ) -> AssessmentResult:
        """
        Assess a single agent response in production.
        
        Uses mlflow.genai.assess() for real-time quality monitoring.
        Falls back to custom implementation when assess() unavailable.
        
        Args:
            query: User query
            response: Agent response
            metadata: Optional metadata (domain, source, etc.)
            request_id: Optional request ID for tracking
            
        Returns:
            AssessmentResult with scores and alert status
        """
        import uuid
        
        request_id = request_id or str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        inputs = {"query": query}
        outputs = {
            "response": response,
            "metadata": metadata or {}
        }
        
        scores = {}
        rationales = {}
        
        # Use mlflow.genai.assess() if available
        if ASSESS_AVAILABLE and assess is not None:
            try:
                assessment = assess(
                    inputs=inputs,
                    outputs=outputs,
                    scorers=self.scorers
                )
                
                for scorer_name, score_result in assessment.items():
                    if hasattr(score_result, 'value'):
                        scores[scorer_name] = score_result.value
                        rationales[scorer_name] = getattr(score_result, 'rationale', '')
            except Exception as e:
                print(f"assess() failed, using fallback: {e}")
                scores, rationales = self._fallback_assessment(inputs, outputs)
        else:
            # Fallback to custom implementation
            scores, rationales = self._fallback_assessment(inputs, outputs)
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores) if scores else 0.0
        
        # Determine if review needed
        needs_review = (
            scores.get("relevance", scores.get("response_quality", 1.0)) < self.relevance_threshold or
            scores.get("safety", scores.get("heuristic_safety", 1.0)) < self.safety_threshold or
            overall_score < self.alert_threshold
        )
        
        # Determine if alert should trigger
        alert_triggered = overall_score < self.alert_threshold
        
        # Log to MLflow
        self._log_assessment(request_id, inputs, outputs, scores, overall_score)
        
        return AssessmentResult(
            request_id=request_id,
            timestamp=timestamp,
            scores=scores,
            rationales=rationales,
            overall_score=overall_score,
            needs_review=needs_review,
            alert_triggered=alert_triggered
        )
    
    def _fallback_assessment(
        self,
        inputs: Dict,
        outputs: Dict
    ) -> tuple:
        """
        Fallback assessment using custom scorers when mlflow.genai.assess() unavailable.
        
        Returns:
            Tuple of (scores dict, rationales dict)
        """
        scores = {}
        rationales = {}
        
        # Run custom scorers manually
        for scorer_func in [response_quality_scorer, domain_routing_scorer]:
            try:
                result = scorer_func(inputs, outputs)
                scorer_name = getattr(scorer_func, '__name__', str(scorer_func))
                if hasattr(result, 'value'):
                    scores[scorer_name] = result.value
                    rationales[scorer_name] = getattr(result, 'rationale', '')
                elif isinstance(result, (int, float)):
                    scores[scorer_name] = float(result)
                    rationales[scorer_name] = ''
            except Exception as e:
                print(f"Scorer {scorer_func} failed: {e}")
        
        # Add heuristic relevance and safety if built-in not available
        if "relevance" not in scores:
            rel_score, rel_rationale = self._heuristic_relevance(inputs, outputs)
            scores["heuristic_relevance"] = rel_score
            rationales["heuristic_relevance"] = rel_rationale
        
        if "safety" not in scores:
            safe_score, safe_rationale = self._heuristic_safety(outputs)
            scores["heuristic_safety"] = safe_score
            rationales["heuristic_safety"] = safe_rationale
        
        return scores, rationales
    
    def _heuristic_relevance(self, inputs: Dict, outputs: Dict) -> tuple:
        """Heuristic relevance check based on keyword overlap."""
        query = inputs.get("query", "").lower()
        response = outputs.get("response", "").lower()
        
        query_words = set(re.findall(r'\b\w+\b', query))
        response_words = set(re.findall(r'\b\w+\b', response))
        
        if not query_words:
            return 0.5, "No query to compare"
        
        overlap = len(query_words.intersection(response_words))
        score = min(overlap / max(len(query_words), 1) * 2, 1.0)  # Scale up
        
        return score, f"Keyword overlap: {overlap}/{len(query_words)}"
    
    def _heuristic_safety(self, outputs: Dict) -> tuple:
        """Heuristic safety check for sensitive content."""
        response = outputs.get("response", "").lower()
        
        unsafe_patterns = [
            r"password\s*[:=]",
            r"secret\s*[:=]",
            r"token\s*[:=]",
            r"api[_-]?key\s*[:=]",
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
            r"\b\d{16}\b",  # Credit card pattern
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, response):
                return 0.0, f"Detected unsafe pattern: {pattern}"
        
        return 1.0, "No unsafe content detected"
    
    def _log_assessment(
        self,
        request_id: str,
        inputs: Dict,
        outputs: Dict,
        scores: Dict[str, float],
        overall_score: float
    ):
        """Log assessment to MLflow for tracking."""
        try:
            # Update current trace with assessment info
            mlflow.update_current_trace(tags={
                "assessment.request_id": request_id,
                "assessment.overall_score": str(overall_score),
                "assessment.needs_review": str(overall_score < self.alert_threshold),
            })
            
            # Log as metrics if in active run
            if mlflow.active_run():
                for name, value in scores.items():
                    mlflow.log_metric(f"assessment_{name}", value)
                mlflow.log_metric("assessment_overall", overall_score)
                
        except Exception as e:
            print(f"Assessment logging error: {e}")
    
    def batch_assess(
        self,
        responses: List[Dict[str, Any]]
    ) -> List[AssessmentResult]:
        """
        Assess multiple responses in batch.
        
        Args:
            responses: List of dicts with 'query', 'response', 'metadata' keys
            
        Returns:
            List of AssessmentResults
        """
        results = []
        for item in responses:
            result = self.assess_response(
                query=item.get("query", ""),
                response=item.get("response", ""),
                metadata=item.get("metadata"),
                request_id=item.get("request_id")
            )
            results.append(result)
        return results


# ===========================================================================
# CONVENIENCE FUNCTIONS
# ===========================================================================

def monitor_response_quality(
    query: str,
    response: str,
    metadata: Optional[Dict] = None
) -> AssessmentResult:
    """
    Quick function to assess a single response.
    
    Example:
        result = monitor_response_quality(
            query="Why did costs spike?",
            response="Costs increased due to...",
            metadata={"domain": "cost"}
        )
        
        if result.alert_triggered:
            print(f"Low quality response: {result.overall_score}")
    """
    monitor = ProductionMonitor()
    return monitor.assess_response(query, response, metadata)


def assess_and_alert(
    query: str,
    response: str,
    metadata: Optional[Dict] = None,
    alert_callback: Optional[callable] = None
) -> AssessmentResult:
    """
    Assess response and trigger alert callback if needed.
    
    Args:
        query: User query
        response: Agent response  
        metadata: Optional metadata
        alert_callback: Function to call if alert triggers (takes AssessmentResult)
        
    Returns:
        AssessmentResult
    """
    result = monitor_response_quality(query, response, metadata)
    
    if result.alert_triggered and alert_callback:
        alert_callback(result)
    
    return result


# ===========================================================================
# INTEGRATION WITH AGENT
# ===========================================================================

class MonitoredAgentWrapper:
    """
    Wrapper that adds production monitoring to any agent.
    
    Usage:
        agent = HealthMonitorAgent()
        monitored = MonitoredAgentWrapper(agent)
        
        result = monitored.predict(context, model_input)
        # Automatically assessed and logged
    """
    
    def __init__(self, agent, monitor: Optional[ProductionMonitor] = None):
        self.agent = agent
        self.monitor = monitor or ProductionMonitor()
    
    def predict(self, context, model_input):
        """Predict with automatic monitoring."""
        # Get agent response
        result = self.agent.predict(context, model_input)
        
        # Extract query and response
        messages = model_input.get("messages", [])
        query = messages[-1].get("content", "") if messages else ""
        
        response_messages = result.get("messages", [])
        response = response_messages[0].get("content", "") if response_messages else ""
        
        metadata = result.get("metadata", {})
        
        # Assess response
        assessment = self.monitor.assess_response(query, response, metadata)
        
        # Add assessment to result
        result["assessment"] = {
            "overall_score": assessment.overall_score,
            "needs_review": assessment.needs_review,
            "scores": assessment.scores
        }
        
        return result

