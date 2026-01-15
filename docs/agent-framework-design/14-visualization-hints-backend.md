# 14A - Visualization Hints: Backend Implementation

> **📋 Implementation Status**: ✅ IMPLEMENTED (Jan 9, 2026)
> 
> **Purpose**: Enable worker agents to suggest appropriate visualizations for tabular data.
> 
> **Audience**: Backend developers implementing agent system
>
> **Implementation Notes**: Since this agent uses a single-file model (`log_agent_model.py`), 
> the visualization hint functions were added inline to the agent class, rather than in a 
> separate `utils` module. All core functionality is implemented and included in both 
> streaming and non-streaming predict methods.

## Overview

Worker agents will analyze Genie responses containing tabular data and generate visualization hints. These hints tell the frontend what type of chart (bar, line, pie) or table view is most appropriate for the data.

## Architecture

```
┌─────────────┐       ┌─────────────┐       ┌──────────────┐
│   Worker    │──────▶│ Viz Hint    │──────▶│ Orchestrator │
│   Agent     │       │ Generator   │       │    Agent     │
└─────────────┘       └─────────────┘       └──────────────┘
     │                      │                       │
     │ 1. Genie Response    │ 2. Analyze Data       │ 3. Pass Through
     │    with Table        │    Suggest Type       │    custom_outputs
```

### Flow

1. Worker agent queries Genie Space → receives markdown table
2. Worker extracts tabular data from response
3. Visualization hint generator analyzes data + query
4. Worker returns enhanced response with `visualization_hint`
5. Orchestrator passes hints through in `custom_outputs`

---

## Implementation Tasks

### Task 1: Create Visualization Hint Utility Module

**File**: `src/agents/utils/visualization_hints.py` (NEW)

**Purpose**: Pure Python module for analyzing data and suggesting visualizations.

**Implementation**:

```python
"""
Visualization Hint Generator
=============================

Generates visualization recommendations for tabular data returned from Genie queries.
Used by worker agents to suggest appropriate chart types for frontend rendering.
"""

from typing import Dict, List, Any, Optional
import pandas as pd


def suggest_visualization(
    data: List[Dict[str, Any]],
    query: str,
    domain: str
) -> Dict[str, Any]:
    """
    Suggest appropriate visualization for tabular data.
    
    Args:
        data: List of dictionaries representing table rows
        query: Original user query (lowercase for matching)
        domain: Domain name (cost, security, performance, reliability, quality)
    
    Returns:
        Dictionary with visualization hint:
        {
            "type": "bar_chart|line_chart|pie_chart|table|heatmap",
            "x_axis": "column_name",
            "y_axis": ["column1", "column2"],
            "title": "Chart title",
            "reason": "Why this visualization was chosen"
        }
    """
    if not data or len(data) == 0:
        return {"type": "table", "reason": "No data to visualize"}
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(data)
    
    # Analyze column types
    numeric_cols = df.select_dtypes(include=['number', 'int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns.tolist()
    
    # Try to detect datetime columns from string patterns
    for col in categorical_cols:
        if _is_datetime_column(df[col]):
            datetime_cols.append(col)
            categorical_cols.remove(col)
    
    row_count = len(df)
    query_lower = query.lower()
    
    # RULE 1: Time series pattern
    if datetime_cols and numeric_cols:
        return {
            "type": "line_chart",
            "x_axis": datetime_cols[0],
            "y_axis": numeric_cols[:3],  # Up to 3 metrics
            "title": f"{', '.join(numeric_cols[:3])} Over Time",
            "reason": "Time series data with numeric metrics"
        }
    
    # RULE 2: Top N pattern (cost queries, job performance, etc.)
    if categorical_cols and numeric_cols and row_count <= 20:
        if any(word in query_lower for word in ['top', 'highest', 'most', 'expensive', 'slowest', 'worst']):
            return {
                "type": "bar_chart",
                "x_axis": categorical_cols[0],
                "y_axis": numeric_cols[0],
                "title": f"Top {row_count} {categorical_cols[0].replace('_', ' ').title()} by {numeric_cols[0].replace('_', ' ').title()}",
                "reason": "Top N comparison query"
            }
    
    # RULE 3: Distribution pattern (percentages, breakdowns)
    if categorical_cols and numeric_cols and row_count <= 10:
        if any(word in query_lower for word in ['breakdown', 'distribution', 'percentage', 'share', 'split']):
            return {
                "type": "pie_chart",
                "label": categorical_cols[0],
                "value": numeric_cols[0],
                "title": f"Distribution of {numeric_cols[0].replace('_', ' ').title()}",
                "reason": "Distribution/breakdown query"
            }
    
    # RULE 4: Comparison pattern
    if row_count <= 15 and numeric_cols and categorical_cols:
        return {
            "type": "bar_chart",
            "x_axis": categorical_cols[0],
            "y_axis": numeric_cols[0],
            "title": f"{numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}",
            "reason": "Comparison across categories"
        }
    
    # RULE 5: Default to table for complex/large data
    return {
        "type": "table",
        "reason": f"Complex data ({row_count} rows, {len(df.columns)} columns) - table view recommended"
    }


def _is_datetime_column(series: pd.Series) -> bool:
    """Check if a string column contains datetime values."""
    if len(series) == 0:
        return False
    
    # Sample first non-null value
    sample = series.dropna().iloc[0] if len(series.dropna()) > 0 else None
    if not sample:
        return False
    
    # Check for common date patterns
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
    ]
    
    import re
    for pattern in date_patterns:
        if re.match(pattern, str(sample)):
            return True
    
    return False


def get_domain_specific_hints(domain: str, query: str) -> Dict[str, Any]:
    """
    Get domain-specific visualization preferences.
    
    Args:
        domain: Domain name
        query: User query
    
    Returns:
        Dictionary with domain-specific preferences
    """
    query_lower = query.lower()
    
    domain_rules = {
        "cost": {
            "prefer_currency_format": True,
            "color_scheme": "red_amber_green",
            "default_sort": "descending"
        },
        "performance": {
            "highlight_outliers": True,
            "color_scheme": "sequential",
            "default_sort": "descending"
        },
        "security": {
            "highlight_critical": True,
            "color_scheme": "red_amber_green",
            "default_sort": "severity"
        },
        "reliability": {
            "show_thresholds": True,
            "color_scheme": "red_amber_green",
            "default_sort": "descending"
        },
        "quality": {
            "show_percentages": True,
            "color_scheme": "red_amber_green",
            "default_sort": "quality_score"
        }
    }
    
    return domain_rules.get(domain, {})
```

**Validation**:
- [ ] File created at `src/agents/utils/visualization_hints.py`
- [ ] No `# Databricks notebook source` header (pure Python)
- [ ] All functions have docstrings
- [ ] Can be imported: `from src.agents.utils.visualization_hints import suggest_visualization`

---

### Task 2: Add Table Extraction to Worker Base Class

**File**: `src/agents/workers/base.py` (MODIFY)

**Add method to extract tabular data from Genie markdown responses**:

```python
def _extract_tabular_data(self, genie_response: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extract tabular data from Genie response.
    
    Genie typically returns markdown tables like:
    
    | Column1 | Column2 |
    |---------|---------|
    | Value1  | Value2  |
    
    This method parses them into: [{"Column1": "Value1", "Column2": "Value2"}]
    
    Args:
        genie_response: Raw Genie response text
    
    Returns:
        List of dictionaries (one per row) or None if no table detected
    """
    if "|" not in genie_response:
        return None
    
    lines = genie_response.strip().split("\n")
    
    # Find table start (header row with pipes)
    table_start = None
    for i, line in enumerate(lines):
        if "|" in line and i < len(lines) - 1 and "|" in lines[i+1]:
            # Check if next line is separator (contains dashes)
            if "-" in lines[i+1]:
                table_start = i
                break
    
    if table_start is None:
        return None
    
    # Parse header
    header_line = lines[table_start].strip()
    headers = [h.strip() for h in header_line.split("|") if h.strip()]
    
    # Skip separator line
    data_start = table_start + 2
    
    # Parse rows
    data = []
    for line in lines[data_start:]:
        line = line.strip()
        if not line or "|" not in line:
            break
        
        # Stop if we hit another markdown element
        if line.startswith("#") or line.startswith("*"):
            break
        
        values = [v.strip() for v in line.split("|") if v.strip() != ""]
        
        # Only add row if column count matches
        if len(values) == len(headers):
            row = dict(zip(headers, values))
            data.append(row)
    
    return data if data else None
```

**Validation**:
- [ ] Method added to `src/agents/workers/base.py`
- [ ] Can parse markdown tables from Genie responses
- [ ] Returns `None` if no table found
- [ ] Returns list of dicts if table found

---

### Task 3: Modify Worker Agent Query Method

**Files**: All worker agent files in `src/agents/workers/`
- `cost_agent.py`
- `security_agent.py`
- `performance_agent.py`
- `reliability_agent.py`
- `quality_agent.py`

**Modify the `query()` method to generate visualization hints**:

```python
# Add import at top of file
from ..utils.visualization_hints import suggest_visualization, get_domain_specific_hints

# Modify query() method
@mlflow.trace(name="worker_agent_query", span_type="AGENT")
def query(
    self,
    question: str,
    context: Optional[Dict] = None,
    conversation_id: Optional[str] = None
) -> Dict:
    """
    Query worker agent and return response with visualization hints.
    
    Returns:
        {
            "domain": str,
            "response": str,               # Natural language response
            "data": List[Dict],            # ✨ NEW: Tabular data (if present)
            "visualization_hint": Dict,     # ✨ NEW: Visualization recommendation
            "sources": List[str],
            "confidence": float,
            "conversation_id": str,
            "source": "genie|error"
        }
    """
    with mlflow.start_span(name=f"{self.domain}_agent_query") as span:
        try:
            # Query Genie (existing logic)
            if conversation_id:
                genie_response = self.genie.continue_conversation(
                    space_id=self.genie_space_id,
                    conversation_id=conversation_id,
                    content=question
                )
            else:
                genie_response = self.genie.start_conversation(
                    space_id=self.genie_space_id,
                    content=question
                )
            
            # Extract response text
            response_text = genie_response.message.content
            
            # ✨ NEW: Extract tabular data from response
            data = self._extract_tabular_data(response_text)
            
            # ✨ NEW: Generate visualization hint if we have data
            if data:
                viz_hint = suggest_visualization(
                    data=data,
                    query=question,
                    domain=self.domain
                )
                # Add domain-specific preferences
                domain_prefs = get_domain_specific_hints(self.domain, question)
                viz_hint.update(domain_prefs)
                
                # Log to span
                span.set_attributes({
                    "has_tabular_data": True,
                    "row_count": len(data),
                    "visualization_type": viz_hint.get("type"),
                })
            else:
                viz_hint = {"type": "text", "reason": "No tabular data in response"}
                span.set_attributes({"has_tabular_data": False})
            
            return {
                "domain": self.domain,
                "response": response_text,
                "data": data,                          # ✨ NEW
                "visualization_hint": viz_hint,         # ✨ NEW
                "sources": [],  # Extract from genie_response if available
                "confidence": 1.0,
                "conversation_id": genie_response.conversation_id,
                "source": "genie"
            }
            
        except Exception as e:
            span.set_attributes({
                "error": str(e),
                "has_tabular_data": False
            })
            
            return {
                "domain": self.domain,
                "response": f"Error querying {self.domain}: {str(e)}",
                "data": None,
                "visualization_hint": {"type": "error"},
                "sources": [],
                "confidence": 0.0,
                "conversation_id": None,
                "source": "error",
                "error": str(e)
            }
```

**Validation per worker**:
- [ ] Import added: `from ..utils.visualization_hints import suggest_visualization, get_domain_specific_hints`
- [ ] `_extract_tabular_data()` called in query method
- [ ] `suggest_visualization()` called if data exists
- [ ] Response includes `data` and `visualization_hint` fields
- [ ] MLflow span logs `has_tabular_data` and `visualization_type`

---

### Task 4: Modify Orchestrator to Pass Through Hints

**File**: `src/agents/orchestrator/agent.py` (MODIFY)

**In the `predict()` method (around line 180-210)**:

```python
try:
    # Run the orchestrator graph
    with get_checkpoint_saver() as checkpointer:
        graph = create_orchestrator_graph().compile(
            checkpointer=checkpointer
        )
        final_state = graph.invoke(initial_state, checkpoint_config)

    # Extract response
    response_content = final_state.get(
        "synthesized_response",
        "I was unable to process your request."
    )
    sources = final_state.get("sources", [])
    confidence = final_state.get("confidence", 0.0)
    
    # ✨ NEW: Extract visualization hints from agent responses
    agent_responses = final_state.get("agent_responses", {})
    visualization_hints = {}
    response_data = {}
    
    for domain, response_dict in agent_responses.items():
        if "visualization_hint" in response_dict:
            visualization_hints[domain] = response_dict["visualization_hint"]
        if "data" in response_dict:
            response_data[domain] = response_dict["data"]

    return ChatAgentResponse(
        messages=[
            ChatAgentMessage(
                role="assistant",
                content=response_content,
            )
        ],
        custom_outputs={
            "thread_id": thread_id,
            "sources": sources,
            "confidence": confidence,
            "domains": final_state.get("intent", {}).get("domains", []),
            # ✨ NEW: Pass visualization hints to frontend
            "visualization_hints": visualization_hints,
            "data": response_data,
        },
    )

except Exception as e:
    mlflow.log_metric("agent_error", 1)
    return ChatAgentResponse(
        messages=[
            ChatAgentMessage(
                role="assistant",
                content=f"I encountered an error: {str(e)}. Please try again.",
            )
        ],
        custom_outputs={
            "thread_id": thread_id,
            "error": str(e),
            # ✨ NEW: Include empty hints on error
            "visualization_hints": {},
            "data": {},
        },
    )
```

**Validation**:
- [ ] Orchestrator extracts `visualization_hints` from worker responses
- [ ] Orchestrator extracts `data` from worker responses
- [ ] Both passed in `custom_outputs`
- [ ] Error case includes empty dicts (not None)

---

### Task 5: Update Streaming Predict Method

**File**: `src/agents/orchestrator/agent.py` (MODIFY)

**In `predict_stream()` method, add hints to final response**:

```python
# At the end of predict_stream, before final yield
# Around line 380-405

# Get final state data
sources = event.get("sources", [])
confidence = event.get("confidence", 0.0)
final_intent = event.get("intent", {})

# ✨ NEW: Extract visualization hints
agent_responses = event.get("agent_responses", {})
visualization_hints = {}
response_data = {}

for domain, response_dict in agent_responses.items():
    if "visualization_hint" in response_dict:
        visualization_hints[domain] = response_dict["visualization_hint"]
    if "data" in response_dict:
        response_data[domain] = response_dict["data"]

yield ChatAgentResponse(
    messages=[
        ChatAgentMessage(
            role="assistant",
            content=response_content,
        )
    ],
    custom_outputs={
        "thread_id": thread_id,
        "status": "complete",
        "stage": "final",
        "sources": sources,
        "confidence": confidence,
        "domains": final_intent.get("domains", []),
        # ✨ NEW
        "visualization_hints": visualization_hints,
        "data": response_data,
    },
)
```

**Validation**:
- [ ] Streaming responses include visualization hints
- [ ] Both batch and streaming modes return same structure

---

## Testing

### Unit Tests

Create `tests/test_visualization_hints.py`:

```python
"""Test visualization hint generation."""

import pytest
from src.agents.utils.visualization_hints import suggest_visualization, get_domain_specific_hints


def test_time_series_detection():
    """Test detection of time series pattern."""
    data = [
        {"date": "2024-01-01", "total_cost": 1200.50},
        {"date": "2024-01-02", "total_cost": 1350.25},
        {"date": "2024-01-03", "total_cost": 1100.00},
    ]
    
    hint = suggest_visualization(
        data=data,
        query="Show cost trend over time",
        domain="cost"
    )
    
    assert hint["type"] == "line_chart"
    assert hint["x_axis"] == "date"
    assert "total_cost" in hint["y_axis"]
    print("✓ Time series test passed")


def test_top_n_detection():
    """Test detection of top N comparison pattern."""
    data = [
        {"job_name": "ETL Pipeline", "total_cost": 850.00},
        {"job_name": "ML Training", "total_cost": 720.50},
        {"job_name": "Data Validation", "total_cost": 320.00},
    ]
    
    hint = suggest_visualization(
        data=data,
        query="What are the top 10 most expensive jobs?",
        domain="cost"
    )
    
    assert hint["type"] == "bar_chart"
    assert hint["x_axis"] == "job_name"
    assert hint["y_axis"] == "total_cost"
    print("✓ Top N test passed")


def test_distribution_detection():
    """Test detection of distribution/breakdown pattern."""
    data = [
        {"workspace": "WS1", "cost": 1200},
        {"workspace": "WS2", "cost": 800},
        {"workspace": "WS3", "cost": 400},
    ]
    
    hint = suggest_visualization(
        data=data,
        query="Show cost breakdown by workspace",
        domain="cost"
    )
    
    assert hint["type"] == "pie_chart"
    assert hint["label"] == "workspace"
    assert hint["value"] == "cost"
    print("✓ Distribution test passed")


def test_no_data_fallback():
    """Test fallback when no data provided."""
    hint = suggest_visualization(
        data=[],
        query="Some query",
        domain="cost"
    )
    
    assert hint["type"] == "table"
    print("✓ No data fallback test passed")


def test_domain_specific_hints():
    """Test domain-specific preferences."""
    hints = get_domain_specific_hints("cost", "show trends")
    
    assert hints["prefer_currency_format"] == True
    assert hints["color_scheme"] == "red_amber_green"
    print("✓ Domain hints test passed")


if __name__ == "__main__":
    test_time_series_detection()
    test_top_n_detection()
    test_distribution_detection()
    test_no_data_fallback()
    test_domain_specific_hints()
    print("\n✅ All tests passed!")
```

**Run tests**:
```bash
python tests/test_visualization_hints.py
```

### Integration Tests

Create `tests/integration/test_worker_viz_hints.py`:

```python
"""Integration tests for worker visualization hints."""

import pytest
from src.agents.workers.cost_agent import CostWorkerAgent
from databricks.sdk import WorkspaceClient


def test_cost_worker_returns_viz_hint():
    """Test that cost worker returns visualization hint."""
    client = WorkspaceClient()
    worker = CostWorkerAgent(
        genie_space_id="<cost_genie_space_id>",
        workspace_client=client
    )
    
    response = worker.query("What are the top 5 expensive workspaces?")
    
    # Verify structure
    assert "visualization_hint" in response
    assert "data" in response
    
    # Verify hint structure
    if response["data"]:  # Only if Genie returned a table
        hint = response["visualization_hint"]
        assert hint["type"] in ["bar_chart", "line_chart", "pie_chart", "table"]
        assert "reason" in hint
    
    print(f"✓ Cost worker returned: {response['visualization_hint']['type']}")


if __name__ == "__main__":
    test_cost_worker_returns_viz_hint()
    print("\n✅ Integration test passed!")
```

---

## Validation Checklist

After implementation, verify:

### Code Structure
- [ ] `src/agents/utils/visualization_hints.py` created (pure Python, no notebook header)
- [ ] `_extract_tabular_data()` added to worker base class
- [ ] All 5 workers import and use visualization hints
- [ ] Orchestrator passes hints in `custom_outputs`

### Functionality
- [ ] Worker responses include `data` field (list of dicts or None)
- [ ] Worker responses include `visualization_hint` field (dict with type, reason)
- [ ] Orchestrator `custom_outputs` includes `visualization_hints` and `data`
- [ ] Hints generated for bar, line, and pie chart patterns
- [ ] Falls back to table for complex/unknown patterns

### Tracing
- [ ] MLflow spans log `has_tabular_data` attribute
- [ ] MLflow spans log `visualization_type` when data present
- [ ] Can view hint generation in MLflow trace UI

### Testing
- [ ] Unit tests pass for all detection rules
- [ ] Integration tests verify end-to-end flow
- [ ] Tested with real Genie responses from all 5 domains

---

## Example Response Format

After implementation, agent responses will look like:

```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "Here are the top 5 most expensive jobs this month:\n\n| Job Name | Total Cost |\n|----------|------------|\n| ETL Pipeline | $1,250.50 |\n| ML Training | $980.25 |\n| Data Validation | $450.75 |\n| Reporting | $320.00 |\n| Archive | $180.50 |"
    }
  ],
  "custom_outputs": {
    "thread_id": "thread_123",
    "domains": ["cost"],
    "confidence": 0.95,
    "sources": [],
    "visualization_hints": {
      "cost": {
        "type": "bar_chart",
        "x_axis": "Job Name",
        "y_axis": "Total Cost",
        "title": "Top 5 Jobs by Cost",
        "reason": "Top N comparison query",
        "prefer_currency_format": true,
        "color_scheme": "red_amber_green"
      }
    },
    "data": {
      "cost": [
        {"Job Name": "ETL Pipeline", "Total Cost": "1250.50"},
        {"Job Name": "ML Training", "Total Cost": "980.25"},
        {"Job Name": "Data Validation", "Total Cost": "450.75"},
        {"Job Name": "Reporting", "Total Cost": "320.00"},
        {"Job Name": "Archive", "Total Cost": "180.50"}
      ]
    }
  }
}
```

---

## Implementation Estimate

| Task | Time | Complexity |
|------|------|------------|
| Task 1: Viz hint utility | 1-2 hours | Low |
| Task 2: Table extraction | 1 hour | Medium |
| Task 3: Worker modifications (×5) | 2-3 hours | Low |
| Task 4: Orchestrator passthrough | 30 min | Low |
| Task 5: Streaming updates | 30 min | Low |
| Testing | 2 hours | Medium |
| **Total** | **7-9 hours** | **Medium** |

---

## References

- [Worker Agents Design](04-worker-agents.md)
- [Orchestrator Agent Design](03-orchestrator-agent.md)
- [Genie Integration](05-genie-integration.md)
- [MLflow Tracing](08-mlflow-tracing.md)

