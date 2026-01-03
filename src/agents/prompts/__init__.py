"""
Prompt Registry Module
======================

Versioned prompts for the Health Monitor agent system.
All prompts are registered to MLflow for tracking and deployment.
"""

from .registry import (
    register_all_prompts,
    load_prompt,
    ORCHESTRATOR_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    SYNTHESIZER_PROMPT,
)

__all__ = [
    "register_all_prompts",
    "load_prompt",
    "ORCHESTRATOR_PROMPT",
    "INTENT_CLASSIFIER_PROMPT",
    "SYNTHESIZER_PROMPT",
]
