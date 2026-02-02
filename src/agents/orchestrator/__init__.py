"""
TRAINING MATERIAL: Orchestrator Module Architecture
====================================================

This module provides the orchestrator agent that coordinates the multi-agent
system. It's the "brain" that decides which domain workers handle a query.

ORCHESTRATOR ARCHITECTURE:
--------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT SYSTEM OVERVIEW                           │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ORCHESTRATOR (HealthMonitorAgent)                                │  │
│  │  ─────────────────────────────────────────────────────────────────│  │
│  │  Entry point for all user queries. Implements mlflow.pyfunc.      │  │
│  │  ChatAgent for deployment to Databricks Model Serving.            │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                               │                                         │
│                               ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  INTENT CLASSIFIER (IntentClassifier)                             │  │
│  │  ─────────────────────────────────────────────────────────────────│  │
│  │  Analyzes query to determine which domain(s) should handle it.    │  │
│  │  Uses LLM with few-shot examples for classification.              │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                               │                                         │
│                               ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  LANGGRAPH STATE MACHINE (create_orchestrator_graph)              │  │
│  │  ─────────────────────────────────────────────────────────────────│  │
│  │  Manages state flow through: classify → route → workers →         │  │
│  │  synthesize → respond. Uses AgentState TypedDict.                 │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                               │                                         │
│                               ▼                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │  COST   │  │SECURITY │  │ PERF    │  │RELIABIL │  │ QUALITY │     │
│  │  AGENT  │  │ AGENT   │  │ AGENT   │  │  AGENT  │  │  AGENT  │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│       ↓            ↓            ↓            ↓            ↓           │
│       └────────────┴────────────┴────────────┴────────────┘           │
│                               │                                         │
│                               ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  RESPONSE SYNTHESIZER                                             │  │
│  │  ─────────────────────────────────────────────────────────────────│  │
│  │  Combines domain responses into unified, coherent answer.         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

MODULE COMPONENTS:
------------------

1. HealthMonitorAgent (agent.py)
   - Main entry point implementing mlflow.pyfunc.ChatAgent
   - Deployed to Databricks Model Serving
   - Handles predict() and predict_stream()

2. IntentClassifier (intent_classifier.py)
   - Classifies user queries into domain categories
   - Supports multi-domain classification
   - Returns confidence scores

3. AgentState (state.py)
   - TypedDict defining state schema for LangGraph
   - Flows through all graph nodes
   - Uses add_messages reducer for conversation history

4. create_orchestrator_graph (graph.py)
   - Factory function building the LangGraph state machine
   - Defines nodes, edges, and conditional routing
   - Integrates with Lakebase checkpointer for memory

LangGraph-based supervisor agent that coordinates domain workers.
"""

from .agent import HealthMonitorAgent
from .intent_classifier import IntentClassifier
from .state import AgentState
from .graph import create_orchestrator_graph

__all__ = [
    "HealthMonitorAgent",
    "IntentClassifier",
    "AgentState",
    "create_orchestrator_graph",
]
